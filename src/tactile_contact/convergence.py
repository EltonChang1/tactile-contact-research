"""Controlled finite training extension preserving the original optimizer trajectory."""
from copy import deepcopy
import json
from pathlib import Path
import random

import numpy as np
import pandas as pd
import torch
from torch.utils.data import TensorDataset, DataLoader, WeightedRandomSampler

from .config import validate_fit_pool
from .episodes import FeatureStore
from .models import ContactPredictor
from .training import validation_objective


def json_lf(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")


class SelectionStore(FeatureStore):
    """A feature whitelist rejects transfer targets before file/cache access."""
    def __init__(self, root, windows, train, selection):
        validate_fit_pool(train, "train")
        validate_fit_pool(selection, "val")
        super().__init__(root, windows)
        inputs = pd.concat([train, selection], ignore_index=True)
        supports = {w for encoded in inputs.support_window_ids for w in json.loads(encoded)}
        targets = set(inputs.query_window_id)
        self.allowed = supports | targets
        self.selection_target_ids = targets
        self.phase = "selection"
        self.accesses = set()
        if not self.allowed.issubset(set(self.windows.index)):
            raise ValueError("Fit/selection window identities absent from manifest")
        if any(self.windows.loc[w, "role"] != "support" for w in supports):
            raise ValueError("Query window cannot serve as an observed support")
        if any(self.windows.loc[w, "role"] != "query" for w in targets):
            raise ValueError("Only query windows can provide training/selection targets")

    def feature(self, window_id):
        if window_id not in self.allowed:
            raise ValueError("Feature access is outside the current fit/selection whitelist")
        self.accesses.add((self.phase, window_id))
        return super().feature(window_id)

    def unlock_scoring(self, episodes, *, selected_trajectories, expected_trajectories):
        if expected_trajectories < 1 or selected_trajectories != expected_trajectories:
            raise ValueError("Every trajectory must be selected before scoring access")
        if not (episodes.split == "val").all() or not set(episodes.query_window_id).issubset(set(self.windows.index)):
            raise ValueError("Scoring must use the approved validation window manifest")
        self.allowed |= set(episodes.query_window_id)
        self.phase = "scoring"


def primary_objective(episodes, predictions, targets):
    mask = (episodes.protocol == "single") & (episodes.duration_s == .5)
    if not mask.any():
        raise ValueError("Primary single-0.5 selection cell is missing")
    return validation_objective(episodes.loc[mask], predictions[mask], targets[mask])


def verify_reference_history(current, historical, horizon, tolerance=0.):
    fields = ["train_loss", "validation_equal_cell_mae"]
    reference = historical[historical.epoch <= horizon]
    prefix = current[current.epoch <= horizon]
    if not np.array_equal(prefix.epoch, reference.epoch) or len(reference) != horizon:
        raise ValueError("Original epoch trajectory is incomplete or mismatched")
    difference = np.abs(prefix[fields].to_numpy()-reference[fields].to_numpy())
    if not np.isfinite(difference).all() or difference.max() > tolerance:
        raise ValueError(f"First-{horizon} trajectory did not reproduce: maximum difference {difference.max()}")
    return float(difference.max())


def fit_convergence(root, cfg, train, selection, store, scaler, seed, cap, horizon,
                    reference_history=None, reference_checkpoint=None, tolerance=0.):
    validate_fit_pool(train, "train")
    validate_fit_pool(selection, "val")
    if not 0 < horizon < cap or horizon != cfg["training"]["epochs"]:
        raise ValueError("Require the original horizon and a finite larger cap")
    root = Path(root)
    if root.exists():
        raise ValueError("Use a fresh output root; never overwrite a training trajectory")
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.set_num_threads(1)
    settings = cfg["training"]
    model = ContactPredictor(latent_dim=settings["latent_dim"])
    optimizer = torch.optim.Adam(model.parameters(), lr=settings["learning_rate"])
    arrays = store.batch_inputs(train, scaler)
    target = store.targets(train)
    dataset = TensorDataset(*(torch.from_numpy(a) for a in arrays), torch.from_numpy(target))
    counts = train.groupby(["surface_id", "protocol", "duration_s"]).episode_id.transform("size")
    generator = torch.Generator().manual_seed(seed)
    samples = settings["episodes_per_surface"]*train.surface_id.nunique()
    sampler = WeightedRandomSampler(torch.as_tensor(1/counts.to_numpy(), dtype=torch.double), samples,
                                   replacement=True, generator=generator)
    loader = DataLoader(dataset, batch_size=settings["batch_size"], sampler=sampler)
    val_inputs = tuple(torch.from_numpy(a) for a in store.batch_inputs(selection, scaler))
    val_target = store.targets(selection)
    # No new model construction, stochastic evaluation, or RNG draws in this loop.
    best, stale, best_epoch = np.inf, 0, 0
    history, snapshots = [], {}
    reference_difference, tensor_match = None, None
    for epoch in range(1, cap+1):
        model.train(); losses = []
        for support, mask, q, y in loader:
            optimizer.zero_grad(set_to_none=True)
            prediction, _ = model(support, mask, q)
            loss = torch.nn.functional.l1_loss(prediction, y)
            loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
            optimizer.step(); losses.append(float(loss.detach()))
        model.eval()
        with torch.no_grad():
            predictions = model(*val_inputs)[0].numpy()
        score = validation_objective(selection, predictions, val_target)
        primary = primary_objective(selection, predictions, val_target)
        if score < best:
            best, best_epoch, stale = score, epoch, 0
            state = deepcopy(model.state_dict())
            selected_primary = primary
        else:
            stale += 1
        history.append(dict(epoch=epoch, train_loss=float(np.mean(losses)), validation_equal_cell_mae=score,
            validation_primary_mae=primary, best_equal_cell_mae=best, selected_epoch=best_epoch, stale_epochs=stale))
        if epoch == horizon:
            snapshots[horizon] = dict(state_dict=deepcopy(state), selected_epoch=best_epoch,
                selection_equal_cell_mae=best, selection_primary_mae=selected_primary)
            if reference_history is not None:
                reference_difference = verify_reference_history(pd.DataFrame(history), reference_history, horizon, tolerance)
            if reference_checkpoint is not None:
                tensor_match = (reference_checkpoint["selected_epoch"] == best_epoch and
                    set(state) == set(reference_checkpoint["state_dict"]) and
                    all(torch.equal(value, reference_checkpoint["state_dict"][key]) for key, value in state.items()))
                if not tensor_match:
                    raise ValueError("Best-by-reference checkpoint tensors did not reproduce")
        if stale >= settings["patience"]:
            break
    if horizon not in snapshots:
        if reference_history is not None:
            raise ValueError("Extension stopped before reproducing the original horizon")
        snapshots[horizon] = dict(state_dict=deepcopy(state), selected_epoch=best_epoch,
            selection_equal_cell_mae=best, selection_primary_mae=selected_primary)
    snapshots[cap] = dict(state_dict=state, selected_epoch=best_epoch,
        selection_equal_cell_mae=best, selection_primary_mae=selected_primary)
    root.mkdir(parents=True)
    for budget, snapshot in snapshots.items():
        torch.save(dict(**snapshot, seed=seed, config_hash=cfg["config_hash"], available_by_epoch=budget,
            actual_epochs_run=min(epoch, budget), support_dim=101, output_dim=96, latent_dim=settings["latent_dim"],
            scaler_mean=torch.from_numpy(scaler["mean"]), scaler_std=torch.from_numpy(scaler["std"]),
            resumable=False), root/f"best_by_{budget}.pt")
    history = pd.DataFrame(history)
    history.to_csv(root/"history.csv", index=False, lineterminator="\n")
    metadata = dict(seed=seed, epochs_run=epoch, epoch_cap=cap, reference_horizon=horizon,
        stop_reason="patience" if stale >= settings["patience"] else "epoch_cap",
        first_reference_history_max_change=reference_difference, reference_checkpoint_tensor_match=tensor_match,
        original_training=settings, original_config_hash=cfg["config_hash"], selection_rule="unchanged_equal_cell",
        primary_history_is_diagnostic=True, checkpoints={str(k): {x: v for x, v in value.items() if x != "state_dict"} for k, value in snapshots.items()})
    json_lf(root/"selection.json", metadata)
    print(f"Seed {seed}: {epoch} epochs, {metadata['stop_reason']}; selected {best_epoch}; equal-cell {best:.6f}", flush=True)
    return history, metadata
