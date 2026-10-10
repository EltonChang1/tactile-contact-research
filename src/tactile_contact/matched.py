"""Matched fit/selection/scoring identities and access enforcement."""
from copy import deepcopy
import json
from pathlib import Path
import random

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler

from .config import PROTOCOLS, FORBIDDEN, digest, validate_fit_pool
from .convergence import json_lf, primary_objective
from .episodes import FeatureStore
from .models import ContactPredictor
from .training import validation_objective


def wrong_support_by_orientation(episodes):
    from .evaluation import wrong_support
    return pd.concat([wrong_support(part) for _, part in episodes.groupby("orientation", sort=False)]).sort_index()


def build_matched_episodes(windows, groups, design, domains, experiment, config_hash):
    if experiment not in ["familiar", "omitted"]:
        raise ValueError("Unknown matched experiment")
    keys = ["surface_id", "speed_mm_s", "direction_deg", "nominal_force_N", "repeat_id", "role", "duration_s"]
    if windows.duplicated(keys).any():
        raise ValueError("Ambiguous matched window identity")
    lookup = windows.set_index(keys).window_id.to_dict()
    group_lookup = groups.set_index("surface_id").family_group
    known = set(domains.loc[domains.known_speed_query, ["speed_mm_s", "direction_deg", "nominal_force_N"]].itertuples(index=False, name=None))
    transfer = set(domains.loc[domains.omitted_transfer, ["speed_mm_s", "direction_deg", "nominal_force_N"]].itertuples(index=False, name=None))
    if (known | transfer) & FORBIDDEN or known & transfer:
        raise ValueError("Matched query domains overlap supports or each other")
    rows = []
    for surface in design["train_ids"]+design["selection_and_score_ids"]:
        training = surface in design["train_ids"]
        conditions = known | transfer if experiment == "familiar" or not training else known
        for orientation in ["forward"] if training else ["forward", "reverse"]:
            repeats = [0, 1] if training else [1 if orientation == "forward" else 0]
            for protocol in design["budgets"]["protocols"]:
                for duration in design["budgets"]["support_durations_logged_s"]:
                    support_conditions = [(v, a, f, repeat if orientation == "forward" or protocol == "repeat" else 1-repeat)
                        for v, a, f, repeat in PROTOCOLS[protocol]]
                    support_keys = [(surface, *c, "support", duration) for c in support_conditions]
                    if any(k not in lookup for k in support_keys):
                        raise ValueError("Missing matched support; do not silently drop a cohort")
                    support_ids = [lookup[k] for k in support_keys]
                    for speed, direction, force in sorted(conditions):
                        for repeat in repeats:
                            key = (surface, speed, direction, force, repeat, "query", .5)
                            if key not in lookup:
                                raise ValueError("Missing matched query; do not silently drop a cell")
                            query_id = lookup[key]
                            row = dict(surface_id=surface, family_group=group_lookup.loc[surface],
                                experiment="familiar_conditions" if experiment == "familiar" else "omitted_speed",
                                evaluation_partition="fit" if training else "selection" if (speed, direction, force) in known else "transfer",
                                split="train" if training else "val", orientation=orientation, protocol=protocol, duration_s=duration,
                                support_window_ids=json.dumps(support_ids), query_window_id=query_id,
                                query_speed_mm_s=speed, query_direction_deg=direction, query_nominal_force_N=force, query_repeat_id=repeat,
                                total_support_time_s=len(support_ids)*duration,
                                total_support_distance_mm=sum(c[0]*duration for c in support_conditions), config_hash=config_hash)
                            row["episode_id"] = digest([experiment, surface, protocol, duration, query_id, orientation])[:24]
                            rows.append(row)
    return pd.DataFrame(rows).sort_values(["split", "surface_id", "protocol", "duration_s", "query_window_id", "orientation"]).reset_index(drop=True)


class MatchedStore(FeatureStore):
    def __init__(self, root, windows, train, selection):
        validate_fit_pool(train, "train"); validate_fit_pool(selection, "val")
        if not (selection.orientation == "forward").all():
            raise ValueError("Reverse targets cannot enter checkpoint selection")
        super().__init__(root, windows)
        permitted = pd.concat([train, selection], ignore_index=True)
        self.allowed = {w for encoded in permitted.support_window_ids for w in json.loads(encoded)} | set(permitted.query_window_id)
        self.phase, self.accesses = "fit_selection", set()

    def feature(self, window_id):
        if window_id not in self.allowed:
            raise ValueError("Matched feature outside the current target/support whitelist")
        self.accesses.add((self.phase, window_id))
        return super().feature(window_id)

    def unlock_scoring(self, episodes, seal_path):
        seal = json.loads(Path(seal_path).read_text())
        if seal["completed_experiments"] != ["familiar", "omitted"] or seal["encoder_selections"] != 6 or seal["baseline_selections"] != 10:
            raise ValueError("All matched selections must finish before scoring")
        if not (episodes.split == "val").all():
            raise ValueError("Scoring unlock cannot expose omitted training targets")
        self.allowed |= {w for encoded in episodes.support_window_ids for w in json.loads(encoded)} | set(episodes.query_window_id)
        self.phase = "scoring"


def fit_matched(root, cfg, train, selection, store, scaler, seed):
    validate_fit_pool(train, "train"); validate_fit_pool(selection, "val")
    root = Path(root)
    if root.exists():
        raise ValueError("Never overwrite a matched training trajectory")
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.set_num_threads(1)
    settings = cfg["training"]
    if settings["epochs"] != 120 or settings["patience"] != 10:
        raise ValueError("Use the declared finite matched training policy")
    model = ContactPredictor(latent_dim=settings["latent_dim"])
    optimizer = torch.optim.Adam(model.parameters(), lr=settings["learning_rate"])
    arrays = store.batch_inputs(train, scaler)
    dataset = TensorDataset(*(torch.from_numpy(a) for a in arrays), torch.from_numpy(store.targets(train)))
    counts = train.groupby(["surface_id", "protocol", "duration_s"]).episode_id.transform("size")
    sampler = WeightedRandomSampler(torch.as_tensor(1/counts.to_numpy(), dtype=torch.double),
        settings["episodes_per_surface"]*train.surface_id.nunique(), replacement=True, generator=torch.Generator().manual_seed(seed))
    loader = DataLoader(dataset, batch_size=settings["batch_size"], sampler=sampler)
    inputs = tuple(torch.from_numpy(a) for a in store.batch_inputs(selection, scaler))
    target = store.targets(selection)
    best, stale, history = np.inf, 0, []
    for epoch in range(1, settings["epochs"]+1):
        model.train(); losses = []
        for support, mask, query, y in loader:
            optimizer.zero_grad(set_to_none=True)
            prediction, _ = model(support, mask, query)
            loss = torch.nn.functional.l1_loss(prediction, y)
            loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
            optimizer.step(); losses.append(float(loss.detach()))
        model.eval()
        with torch.no_grad():
            prediction = model(*inputs)[0].numpy()
        score = validation_objective(selection, prediction, target)
        primary = primary_objective(selection, prediction, target)
        if score < best:
            best, selected_epoch, stale = score, epoch, 0
            state, selected_primary = deepcopy(model.state_dict()), primary
        else:
            stale += 1
        history.append(dict(epoch=epoch, train_loss=float(np.mean(losses)), validation_equal_cell_mae=score,
            validation_primary_mae=primary, best_equal_cell_mae=best, selected_epoch=selected_epoch, stale_epochs=stale))
        if stale >= settings["patience"]:
            break
    model.load_state_dict(state); model.eval(); root.mkdir(parents=True)
    torch.save(dict(state_dict=state, seed=seed, config_hash=cfg["config_hash"], selected_epoch=selected_epoch,
        actual_epochs_run=epoch, latent_dim=settings["latent_dim"], scaler_mean=torch.from_numpy(scaler["mean"]),
        scaler_std=torch.from_numpy(scaler["std"]), resumable=False), root/"model.pt")
    metadata = dict(seed=seed, epochs_run=epoch, selected_epoch=selected_epoch,
        stop_reason="patience" if stale >= settings["patience"] else "epoch_cap",
        selection_equal_cell_mae=best, selection_primary_mae=selected_primary)
    pd.DataFrame(history).to_csv(root/"history.csv", index=False, lineterminator="\n")
    json_lf(root/"selection.json", metadata)
    print(f"Matched seed {seed}: {epoch} epochs ({metadata['stop_reason']}), selected {selected_epoch}, selection {best:.6f}", flush=True)
    return model, metadata
