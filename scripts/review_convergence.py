"""Run a finite bounded convergence extension, selecting every trajectory before scoring."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from tactile_contact.config import file_hash, validate_fit_pool
from tactile_contact.convergence import SelectionStore, fit_convergence, json_lf
from tactile_contact.evaluation import score_predictions, wrong_support
from tactile_contact.metrics import paired_bootstrap
from tactile_contact.models import ContactPredictor
from tactile_contact.study_design import validate_development_access
from tactile_contact.training import model_predictions


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def preflight(spec):
    groups, reserved = [pd.read_csv(spec[k]) for k in ["group_manifest", "reservation_manifest"]]
    exposure = read(spec["exposure_snapshot"])
    convention = read(spec["clock_convention"])
    if spec["epoch_cap"] != 120 or spec["reference_horizon"] != 60 or spec["seeds"] != [0, 1, 2]:
        raise ValueError("Only the prescribed finite 60/120, three-seed review is supported")
    if spec["history_absolute_tolerance"] != 0 or not spec["require_reference_checkpoint_tensor_equality"]:
        raise ValueError("Reference histories and checkpoint tensors must reproduce exactly")
    if [e["name"] for e in spec["experiments"]] != ["expanded", "omitted"]:
        raise ValueError("Require both unchanged historical development experiments")
    contexts = []
    for experiment in spec["experiments"]:
        root = Path(experiment["historical_root"])
        manifest = read(root/"results/run_manifest.json")
        cfg = manifest["config"]
        validate_development_access(cfg["train_ids"]+cfg["val_ids"], groups, reserved,
            exposure["training_surface_ids"]+exposure["selection_surface_ids"])
        if set(cfg["train_ids"]) != set(exposure["training_surface_ids"]) or set(cfg["val_ids"]) != set(exposure["selection_surface_ids"]):
            raise ValueError("Convergence must use the unchanged exposed cohorts")
        if cfg["training"]["epochs"] != 60 or cfg["training"]["seeds"] != spec["seeds"]:
            raise ValueError("Historical training horizon/seeds changed")
        if any(cfg[k] != convention[k] for k in ["time_base", "sampling_rate_hz"]) or convention["physical_acquisition_clock_verified"]:
            raise ValueError("Convergence retains declared uncalibrated logged coordinates")
        if manifest["processing_boundary"] != "raw_window_v1":
            raise ValueError("Only corrected bounded histories may be extended")
        inputs = {str(root/"results/run_manifest.json"): file_hash(root/"results/run_manifest.json")}
        for name, sha in manifest["manifest_hashes"].items():
            path = root/"data/manifests"/name
            if file_hash(path) != sha:
                raise ValueError(f"Historical manifest changed: {path}")
            inputs[str(path)] = sha
        for name, sha in manifest["software_hashes"].items():
            if file_hash(Path("src/tactile_contact")/name) != sha:
                raise ValueError(f"Historical source changed: {name}")
        preparation = read(root/"data/manifests/preparation.json")
        if preparation["config_hash"] != cfg["config_hash"] or preparation["processing_boundary"] != "raw_window_v1":
            raise ValueError("Historical preparation identity mismatch")
        windows = pd.read_csv(root/"data/manifests/windows.csv")
        episodes = pd.read_csv(root/"data/manifests/episodes.csv")
        if not set(windows.surface_id).issubset(cfg["train_ids"]+cfg["val_ids"]) or set(windows.window_config_hash) != {cfg["config_hash"]}:
            raise ValueError("Unexpected specimens/configuration in window manifest")
        if episodes.episode_id.duplicated().any() or set(episodes.config_hash) != {cfg["config_hash"]}:
            raise ValueError("Episode identities changed")
        train = episodes[episodes.split == "train"].reset_index(drop=True)
        val = episodes[episodes.split == "val"].reset_index(drop=True)
        selection = val[val.evaluation_partition == "selection"].reset_index(drop=True)
        validate_fit_pool(train, "train"); validate_fit_pool(selection, "val")
        triples = selection[["query_speed_mm_s", "query_direction_deg", "query_nominal_force_N"]].drop_duplicates()
        if sorted(selection.query_speed_mm_s.unique()) != experiment["selection_speeds"] or len(triples) != experiment["selection_triples"]:
            raise ValueError("Original experiment-specific selection domain changed")
        expected_experiment = "omitted_speed" if experiment["name"] == "omitted" else "familiar_conditions"
        if set(episodes.experiment) != {expected_experiment}:
            raise ValueError("Experiment labels changed")
        store = SelectionStore(root, windows, train, selection)
        # Hash only permitted feature files here; transfer cache files remain unread.
        feature_hashes = {}
        for window_id in sorted(store.allowed):
            path = root/store.windows.loc[window_id, "feature_path"]
            feature_hashes[str(path)] = file_hash(path)
        scaler_path = root/"data/features/scaler.npz"
        with np.load(scaler_path) as data:
            scaler = {k: data[k].copy() for k in ["mean", "std"]}
        support_ids = sorted({w for encoded in train.support_window_ids for w in json.loads(encoded)})
        values = np.stack([store.feature(w)["log_band_power"].reshape(-1) for w in support_ids])
        std = values.std(axis=0); std[std < 1e-8] = 1.
        if not np.array_equal(values.mean(axis=0), scaler["mean"]) or not np.array_equal(std, scaler["std"]):
            raise ValueError("Saved scaler does not match unchanged training-only fitting")
        for path in [scaler_path, root/"data/features/scaler.json", root/"data/manifests/preparation.json", root/"results/environment.lock.txt"]:
            inputs[str(path)] = file_hash(path)
        references = {}
        for seed in spec["seeds"]:
            checkpoint_path = root/f"runs/{cfg['config_hash']}/seed_{seed}/model.pt"
            history_path = checkpoint_path.with_name("history.csv")
            checkpoint = torch.load(checkpoint_path, weights_only=True, map_location="cpu")
            if checkpoint["seed"] != seed or checkpoint["config_hash"] != cfg["config_hash"]:
                raise ValueError("Historical checkpoint identity changed")
            references[seed] = (pd.read_csv(history_path, float_precision="round_trip"), checkpoint)
            for path in [checkpoint_path, history_path]:
                inputs[str(path)] = file_hash(path)
        contexts.append(dict(experiment=experiment, root=root, cfg=cfg, train=train, val=val, selection=selection,
            store=store, scaler=scaler, references=references, inputs=inputs, fit_feature_hashes=feature_hashes))
    return contexts


def run(review_path):
    spec = read(review_path)
    contexts = preflight(spec)
    output = Path(spec["output_root"])
    historical = [c["root"].resolve() for c in contexts]
    if output.exists() or any(output.resolve() == r or r in output.resolve().parents for r in historical):
        raise ValueError("Use a new output root outside the preserved historical runs")
    output.mkdir(parents=True)
    json_lf(output/"review.json", spec)
    curves, selections, jobs = [], [], []
    total = len(contexts)*len(spec["seeds"])
    for context in contexts:
        name = context["experiment"]["name"]
        for seed in spec["seeds"]:
            reference_history, reference_checkpoint = context["references"][seed]
            trajectory = output/name/f"seed_{seed}"
            history, metadata = fit_convergence(trajectory, context["cfg"], context["train"], context["selection"],
                context["store"], context["scaler"], seed, spec["epoch_cap"], spec["reference_horizon"],
                reference_history, reference_checkpoint, spec["history_absolute_tolerance"])
            curves.append(history.assign(experiment=name, seed=seed))
            cutoff = max(1, metadata["epochs_run"]-spec["tail_epochs"])
            earlier = float(history.loc[history.epoch <= cutoff, "validation_equal_cell_mae"].min())
            best = float(history.validation_equal_cell_mae.min())
            selections.append(dict(experiment=name, seed=seed, epochs_run=metadata["epochs_run"], stop_reason=metadata["stop_reason"],
                selected_by_60=metadata["checkpoints"]["60"]["selected_epoch"], selected_by_120=metadata["checkpoints"]["120"]["selected_epoch"],
                equal_cell_by_60=metadata["checkpoints"]["60"]["selection_equal_cell_mae"], equal_cell_by_120=best,
                primary_selection_by_60=metadata["checkpoints"]["60"]["selection_primary_mae"],
                primary_selection_by_120=metadata["checkpoints"]["120"]["selection_primary_mae"],
                tail_best_improvement=earlier-best, first_60_history_max_change=metadata["first_reference_history_max_change"],
                reference_checkpoint_tensor_match=metadata["reference_checkpoint_tensor_match"]))
            jobs.append(dict(experiment=name, seed=seed, trajectory=trajectory.as_posix(),
                checkpoints={str(b): file_hash(trajectory/f"best_by_{b}.pt") for b in [60, 120]}))
    # Persist the complete selection seal BEFORE historical arrays or transfer targets.
    seal = output/"selection_complete.json"
    json_lf(seal, dict(review_id=spec["review_id"], selected_trajectories=len(jobs), expected_trajectories=total,
        all_first_60_histories_exact=all(s["first_60_history_max_change"] == 0 for s in selections),
        all_reference_checkpoints_exact=all(s["reference_checkpoint_tensor_match"] for s in selections), jobs=jobs))
    scores, scoring_hashes = [], {}
    for context in contexts:
        name, store, val, cfg = context["experiment"]["name"], context["store"], context["val"], context["cfg"]
        store.unlock_scoring(val, selected_trajectories=len(jobs), expected_trajectories=total)
        targets = store.targets(val)
        historical_predictions = context["root"]/"results/tables/predictions.npz"
        original_scores = context["root"]/"results/tables/per_query.csv"
        scoring_hashes[str(historical_predictions)] = file_hash(historical_predictions)
        scoring_hashes[str(original_scores)] = file_hash(original_scores)
        old = pd.read_csv(original_scores)
        old["model"] = old.model.replace({"encoder": "encoder_original_60", "encoder_wrong_support": "encoder_wrong_original_60"})
        scores.append(old.assign(experiment_name=name))
        predictions = {}
        with np.load(historical_predictions) as saved:
            if not np.array_equal(saved["episode_ids"], val.episode_id.to_numpy(dtype=str)) or not np.array_equal(saved["targets"], targets):
                raise ValueError("Historical scoring identities/targets changed")
            for seed in spec["seeds"]:
                for budget in [60, 120]:
                    checkpoint = torch.load(output/name/f"seed_{seed}/best_by_{budget}.pt", weights_only=True, map_location="cpu")
                    model = ContactPredictor(latent_dim=cfg["training"]["latent_dim"])
                    model.load_state_dict(checkpoint["state_dict"])
                    prediction = model_predictions(model, val, store, context["scaler"])
                    if budget == 60 and not np.array_equal(prediction, saved[f"encoder_{seed}"]):
                        raise ValueError("Reproduced reference checkpoint predictions changed")
                    wrong = model_predictions(model, wrong_support(val), store, context["scaler"])
                    predictions[f"encoder_by_{budget}_{seed}"] = prediction
                    predictions[f"encoder_wrong_by_{budget}_{seed}"] = wrong
                    for method, values in [(f"encoder_by_{budget}", prediction), (f"encoder_wrong_by_{budget}", wrong)]:
                        scores.append(score_predictions(val, values, targets, method, seed, cfg["power_floor"]).assign(experiment_name=name))
        np.savez_compressed(output/name/"predictions.npz", episode_ids=val.episode_id.to_numpy(dtype=str), targets=targets, **predictions)
        for window_id in sorted(set(val.query_window_id)):
            path = context["root"]/store.windows.loc[window_id, "feature_path"]
            scoring_hashes[str(path)] = file_hash(path)
    all_scores = pd.concat(scores, ignore_index=True)
    all_scores.to_csv(output/"per_query.csv", index=False, lineterminator="\n")
    metrics = ["log_power_mae", "modeled_band_total_rms_error"]
    keys = ["experiment_name", "evaluation_partition", "model", "protocol", "duration_s", "surface_id", "family_group"]
    by_seed = all_scores.groupby(keys+["seed"], as_index=False)[metrics].mean()
    per_surface = by_seed.groupby(keys, as_index=False)[metrics].mean()
    summary = per_surface.groupby(keys[:-2], as_index=False).agg(log_power_mae=("log_power_mae", "mean"),
        modeled_band_total_rms_error=("modeled_band_total_rms_error", "mean"), surfaces=("surface_id", "nunique"))
    comparisons = []
    for labels, frame in per_surface.groupby(["experiment_name", "evaluation_partition", "protocol", "duration_s"]):
        pivot = frame.pivot(index=["surface_id", "family_group"], columns="model", values="log_power_mae")
        for a, b in [("encoder_by_60", "encoder_by_120"), ("retrieval", "encoder_by_120"), ("fixed_features", "encoder_by_120")]:
            paired = paired_bootstrap(pivot[a].to_numpy(), pivot[b].to_numpy(), pivot.index.get_level_values("family_group").to_numpy(), draws=2000)
            comparisons.append(dict(zip(["experiment", "partition", "protocol", "duration_s"], labels), method_a=a, method_b=b,
                mean_improvement_b=paired["mean_improvement"], ci95_low=paired["ci95"][0], ci95_high=paired["ci95"][1],
                groups=paired["independent_groups"]))
    prefix = spec["output_prefix"]
    exported = []
    for name, table in [("histories", pd.concat(curves, ignore_index=True)), ("selections", pd.DataFrame(selections)),
                        ("summary", summary), ("per_surface", per_surface), ("paired", pd.DataFrame(comparisons))]:
        path = Path(f"docs/{prefix}_{name}.csv")
        table.to_csv(path, index=False, lineterminator="\n")
        exported.append(dict(path=path.as_posix(), sha256=file_hash(path)))
    curve = pd.concat(curves, ignore_index=True)
    figure, axes = plt.subplots(2, 2, figsize=(10, 7))
    for column, name in enumerate(["expanded", "omitted"]):
        for seed in spec["seeds"]:
            history = curve[(curve.experiment == name) & (curve.seed == seed)]
            for row, metric in enumerate(["validation_equal_cell_mae", "validation_primary_mae"]):
                later = history[history.epoch >= 40]
                axes[row, column].plot(later.epoch, later[metric], label=f"Seed {seed}")
                axes[row, column].axvline(60, color="gray", ls="--", lw=.8)
        axes[0, column].set(title=f"{name}: equal-cell selection", ylabel="MAE (log10 power)")
        axes[1, column].set(title=f"{name}: single-0.5 selection diagnostic", ylabel="MAE (log10 power)", xlabel="Epoch")
        axes[0, column].legend(fontsize=8)
    figure.suptitle("Controlled development extension; dashed line = original cap")
    figure.tight_layout()
    path = Path(f"docs/{prefix}_curves.png")
    figure.savefig(path, dpi=160); plt.close(figure)
    exported.append(dict(path=path.as_posix(), sha256=file_hash(path)))
    environment = dict(python=platform.python_version(), platform=platform.platform(), device="cpu",
        packages={p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scipy", "torch", "matplotlib"]})
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True)
    (output/"environment.lock.txt").write_text(freeze.stdout, encoding="utf-8", newline="\n")
    sources = [Path(__file__).relative_to(Path.cwd()), *Path("src/tactile_contact").glob("*.py")]
    public_inputs = {str(review_path): file_hash(review_path), **{spec[k]: file_hash(spec[k]) for k in
        ["group_manifest", "reservation_manifest", "exposure_snapshot", "clock_convention"]}}
    json_lf(f"docs/{prefix}_provenance.json", dict(review_id=spec["review_id"], review_date=spec["review_date"],
        public_input_hashes=public_inputs, source_hashes={p.as_posix(): file_hash(p) for p in sources},
        historical_input_hashes={k: v for c in contexts for k, v in c["inputs"].items()},
        permitted_fit_feature_hashes={k: v for c in contexts for k, v in c["fit_feature_hashes"].items()},
        scoring_input_hashes=scoring_hashes, selection_seal=dict(path=seal.as_posix(), sha256=file_hash(seal)),
        selections=selections, jobs=jobs, environment=environment, outputs=exported,
        feature_accesses=[dict(experiment=c["experiment"]["name"], phase=phase, window_id=w) for c in contexts for phase, w in sorted(c["store"].accesses)],
        reserved_signals_accessed=False, scope=spec["scope"],
        claim_limit="Two development validation groups; no fresh test, no calibrated clock, no model or QC/floor/range/selection change beyond finite cap."))
    print(pd.DataFrame(selections).to_string(index=False), flush=True)
    print(summary[(summary.protocol == "single") & (summary.duration_s == .5)].to_string(index=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=Path("configs/convergence_review.json"))
    run(parser.parse_args().review)
