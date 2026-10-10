"""Review frozen prediction repetition reversal and condition/specimen residuals."""
import argparse
import json
from pathlib import Path
import platform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from tactile_contact.audit import load_record
from tactile_contact.config import data_root, file_hash, omitted_speed
from tactile_contact.convergence import json_lf
from tactile_contact.evaluation import score_predictions, wrong_support
from tactile_contact.metrics import paired_bootstrap
from tactile_contact.models import ContactPredictor
from tactile_contact.repetition_review import (FrozenScoringStore, aggregate_scores,
    build_reversed_episodes, restore_baselines, reversed_requests)
from tactile_contact.signal import spectral_features
from tactile_contact.study_design import validate_development_access
from tactile_contact.training import model_predictions
from tactile_contact.windows import prepare_acceleration_window


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_hashes(mapping):
    for path, expected in mapping.items():
        if file_hash(path) != expected:
            raise ValueError(f"Preserved artifact changed: {path}")


def preflight(spec):
    if spec["checkpoint_budget"] != 120 or spec["seeds"] != [0, 1, 2]:
        raise ValueError("Only the frozen 120-budget three-seed review is supported")
    if [e["name"] for e in spec["experiments"]] != ["expanded", "omitted"]:
        raise ValueError("Both historical experiments are required")
    groups, reserved = [pd.read_csv(spec[k]) for k in ["group_manifest", "reservation_manifest"]]
    exposure = read(spec["exposure_snapshot"])
    contexts = []
    for experiment in spec["experiments"]:
        root = Path(experiment["historical_root"])
        manifest = read(root/"results/run_manifest.json")
        cfg = manifest["config"]
        # Identity access guard precedes raw signals, feature arrays or checkpoints.
        validate_development_access(cfg["train_ids"]+cfg["val_ids"], groups, reserved,
            exposure["training_surface_ids"]+exposure["selection_surface_ids"])
        if set(cfg["train_ids"]) != set(exposure["training_surface_ids"]) or set(cfg["val_ids"]) != set(exposure["selection_surface_ids"]):
            raise ValueError("Only unchanged exposed specimens may enter this review")
        check_hashes({str(root/"data/manifests"/k): v for k, v in manifest["manifest_hashes"].items()})
        check_hashes({str(Path("src/tactile_contact")/k): v for k, v in manifest["software_hashes"].items()})
        windows = pd.read_csv(root/"data/manifests/windows.csv", float_precision="round_trip")
        val = pd.read_csv(root/"data/manifests/episodes.csv")
        val = val[val.split == "val"].reset_index(drop=True)
        if set(val.surface_id) != set(cfg["val_ids"]) or val.episode_id.duplicated().any():
            raise ValueError("Unexpected validation cohort")
        contexts.append(dict(name=experiment["name"], root=root, cfg=cfg, windows=windows, val=val))
    convergence = read(spec["convergence_provenance"])
    for key in ["public_input_hashes", "source_hashes", "historical_input_hashes", "permitted_fit_feature_hashes", "scoring_input_hashes"]:
        check_hashes(convergence[key])
    check_hashes({convergence["selection_seal"]["path"]: convergence["selection_seal"]["sha256"]})
    seal = read(convergence["selection_seal"]["path"])
    if seal["selected_trajectories"] != 6 or not seal["all_first_60_histories_exact"] or not seal["all_reference_checkpoints_exact"]:
        raise ValueError("Incomplete controlled convergence evidence")
    inputs = {spec["convergence_provenance"]: file_hash(spec["convergence_provenance"])}
    for context in contexts:
        root, name, cfg = context["root"], context["name"], context["cfg"]
        for path in [root/"results/run_manifest.json", *[root/"data/manifests"/p for p in ["recordings.csv", "windows.csv", "episodes.csv"]]]:
            inputs[path.as_posix()] = file_hash(path)
        scaler_path = root/"data/features/scaler.npz"
        inputs[scaler_path.as_posix()] = file_hash(scaler_path)
        with np.load(scaler_path) as values:
            context["scaler"] = {k: values[k].copy() for k in ["mean", "std"]}
        context["baselines"] = restore_baselines(root/"results/tables", omitted_speed(cfg))
        for filename in ["conditions_only_fit.npz", "fixed_features_fit.npz", "speed_rescaling_fit.json", "retrieval_fit.npz", "retrieval_sources.json"]:
            path = root/"results/tables"/filename
            inputs[path.as_posix()] = file_hash(path)
        context["models"] = {}
        for seed in spec["seeds"]:
            path = Path(spec["convergence_root"])/name/f"seed_{seed}/best_by_120.pt"
            job = next(j for j in seal["jobs"] if j["experiment"] == name and j["seed"] == seed)
            if file_hash(path) != job["checkpoints"]["120"]:
                raise ValueError("Frozen checkpoint hash mismatch")
            checkpoint = torch.load(path, weights_only=True, map_location="cpu")
            if checkpoint["config_hash"] != cfg["config_hash"] or checkpoint["seed"] != seed or checkpoint["available_by_epoch"] != 120:
                raise ValueError("Checkpoint identity mismatch")
            if not all(np.array_equal(checkpoint[f"scaler_{k}"].numpy(), context["scaler"][k]) for k in ["mean", "std"]):
                raise ValueError("Frozen scaler differs from checkpoint")
            model = ContactPredictor(latent_dim=checkpoint["latent_dim"])
            model.load_state_dict(checkpoint["state_dict"]); model.eval()
            context["models"][seed] = model
            inputs[path.as_posix()] = file_hash(path)
    return contexts, inputs


def predictions(context, episodes, store):
    outputs = []
    for name, model in context["baselines"].items():
        output = model.predict(episodes, store, context["scaler"])
        values, ids = output if isinstance(output, tuple) else (output, None)
        outputs.append((name, -1, values, ids))
    for seed, model in context["models"].items():
        for name, rows in [("encoder", episodes), ("encoder_wrong_support", wrong_support(episodes))]:
            outputs.append((name, seed, model_predictions(model, rows, store, context["scaler"]), None))
    return outputs


def prepare_complement(context, destination, input_hashes):
    requests, plans = reversed_requests(context["val"], context["windows"])
    records = pd.read_csv(context["root"]/"data/manifests/recordings.csv", float_precision="round_trip")
    indexed = records.set_index(["surface_id", "speed_mm_s", "direction_deg", "nominal_force_N", "repeat_id"])
    if indexed.index.duplicated().any():
        raise ValueError("Ambiguous recording identity")
    raw = data_root(context["root"], context["cfg"])/"data/raw"/context["cfg"]["source_kind"]
    inventory_path = data_root(context["root"], context["cfg"])/"data/raw_inventory.json"
    inventory = read(inventory_path)
    if inventory["revision"] != context["cfg"]["revision"]:
        raise ValueError("Raw inventory revision mismatch")
    indexed_hashes = {f["path"]: f["sha256"] for f in inventory["files"]}
    input_hashes[inventory_path.as_posix()] = file_hash(inventory_path)
    loaded, rows, lookup, audits = {}, [], {}, []
    cache = destination/"features"
    cache.mkdir(parents=True)
    for key in requests:
        identity, role, duration = key[:5], key[5], key[6]
        if identity not in indexed.index:
            raise ValueError(f"Missing complementary recording: {identity}")
        record = indexed.loc[identity]
        if record.qc_status != "valid":
            raise ValueError(f"Complementary record failed frozen QC: {identity}")
        recording_id = record.recording_id
        if recording_id not in loaded:
            for channel in ["accel", "force", "position"]:
                relative = f"sensor_data/{channel}/{identity[0]}/{recording_id}.parquet"
                path = raw/relative
                if relative not in indexed_hashes or file_hash(path) != indexed_hashes[relative]:
                    raise ValueError(f"Missing/changed pinned raw file: {relative}")
                input_hashes[path.as_posix()] = indexed_hashes[relative]
            loaded[recording_id] = load_record(raw, recording_id)
        frames, times, _ = loaded[recording_id]
        fs = context["cfg"]["sampling_rate_hz"]
        origin = times["accel"][0]
        start_index = max(0, int(np.ceil((record.steady_start_s-origin)*fs)))
        start = origin+start_index/fs
        if start < record.steady_start_s:
            start_index += 1; start = origin+start_index/fs
        if start+duration > record.steady_end_s:
            raise ValueError(f"Complementary window unavailable; complete-cohort policy: {key}")
        array, dependency = prepare_acceleration_window(frames["accel"], times["accel"], start, duration, fs)
        altered = frames["accel"].copy()
        outside = (times["accel"] < start) | (times["accel"] >= start+duration)
        altered.loc[outside, ["X", "Y", "Z"]] = 12345.
        check, _ = prepare_acceleration_window(altered, times["accel"], start, duration, fs)
        if not np.array_equal(array, check):
            raise ValueError("Outside-window perturbation changed a complementary window")
        feature = spectral_features(array, fs=fs, floor=context["cfg"]["power_floor"])
        window_id = f"{recording_id}_{role}_{duration:g}_{context['cfg']['config_hash'][:12]}"
        path = cache/f"{window_id}.npz"
        np.savez_compressed(path, **feature)
        lookup[key] = window_id
        rows.append(dict(window_id=window_id, recording_id=recording_id, surface_id=key[0],
            speed_mm_s=key[1], direction_deg=key[2], nominal_force_N=key[3], repeat_id=key[4],
            role=role, duration_s=duration, split="val", start_s=start, end_s=start+duration,
            feature_path=path.resolve().as_posix(), window_config_hash=context["cfg"]["config_hash"], **dependency))
        audits.append(dict(experiment=context["name"], window_id=window_id, recording_id=recording_id,
            surface_id=key[0], role=role, duration_s=duration, start_s=start, end_s=start+duration,
            steady_end_s=record.steady_end_s, outside_perturbation_equal=True,
            feature_sha256=file_hash(path), **dependency))
    windows = pd.DataFrame(rows)
    reverse = build_reversed_episodes(context["val"], plans, lookup)
    windows.to_csv(destination/"windows.csv", index=False, lineterminator="\n")
    reverse.to_csv(destination/"episodes.csv", index=False, lineterminator="\n")
    return windows, reverse, audits


def run(review_path):
    torch.set_num_threads(1)
    spec = read(review_path)
    output = Path(spec["output_root"])
    if output.exists():
        raise ValueError("Use a new review root; preserve executed evidence")
    contexts, inputs = preflight(spec)
    output.mkdir(parents=True)
    # All parameters/libraries/checkpoints fixed before complementary raw access.
    seal = output/"frozen_models.json"
    json_lf(seal, dict(review_id=spec["review_id"], inputs=inputs, models=5, encoder_checkpoints=6,
        no_refit=True, policy=spec, complementary_signals_accessed=False))
    scores, all_audits, reproduction, access, retrieval_sources = [], [], [], [], []
    for context in contexts:
        name, val, root = context["name"], context["val"], context["root"]
        forward_store = FrozenScoringStore(root, context["windows"], val)
        forward = predictions(context, val, forward_store)
        paths = [root/"results/tables/predictions.npz", Path(spec["convergence_root"])/name/"predictions.npz"]
        for path in paths:
            inputs[path.as_posix()] = file_hash(path)
        with np.load(paths[0]) as old, np.load(paths[1]) as current:
            if not all(np.array_equal(saved["episode_ids"], val.episode_id.to_numpy(dtype=str)) for saved in [old, current]):
                raise ValueError("Forward prediction episode identity mismatch")
            for method, seed, values, _ in forward:
                source = old if seed == -1 else current
                label = method if seed == -1 else f"{'encoder_wrong' if method == 'encoder_wrong_support' else 'encoder'}_by_120_{seed}"
                if not np.array_equal(values, source[label]):
                    raise ValueError(f"Frozen forward predictions changed: {name}/{method}/{seed}")
                reproduction.append(dict(experiment=name, model=method, seed=seed, exact_prediction_reproduction=True))
        retrieval_sources.extend(dict(experiment=name, orientation="forward", **r) for r in context["baselines"]["retrieval"].prediction_sources)
        forward_store.unlock_targets()
        forward_targets = forward_store.targets(val)
        destination = output/name
        reverse_windows, reverse, audits = prepare_complement(context, destination, inputs)
        all_audits.extend(audits)
        reverse_store = FrozenScoringStore(destination, reverse_windows, reverse)
        reversed_values = predictions(context, reverse, reverse_store)
        retrieval_sources.extend(dict(experiment=name, orientation="reverse", **r) for r in context["baselines"]["retrieval"].prediction_sources)
        # Save all predictor outputs before permitting target reads by the scorer.
        np.savez_compressed(destination/"frozen_predictions.npz", episode_ids=reverse.episode_id.to_numpy(dtype=str),
            **{f"{m}_{s}": p for m, s, p, _ in reversed_values})
        reverse_store.unlock_targets()
        reverse_targets = reverse_store.targets(reverse)
        np.savez_compressed(destination/"targets.npz", forward=forward_targets, reverse=reverse_targets)
        for orientation, episodes, values, targets in [("forward", val, forward, forward_targets),
                                                       ("reverse", reverse, reversed_values, reverse_targets)]:
            for method, seed, prediction, ids in values:
                table = score_predictions(episodes, prediction, targets, method, seed, context["cfg"]["power_floor"], ids)
                # Use short review experiment labels, preserving partition identities.
                table["experiment"] = name
                scores.append(table.assign(orientation=orientation))
        for orientation, store in [("forward", forward_store), ("reverse", reverse_store)]:
            access.extend(dict(experiment=name, orientation=orientation, phase=p, window_id=w) for p, w in sorted(store.accesses))
        for window_id in sorted(forward_store.supports | forward_store.query_ids):
            path = root/forward_store.windows.loc[window_id, "feature_path"]
            inputs[path.as_posix()] = file_hash(path)
    all_scores = pd.concat(scores, ignore_index=True)
    all_scores.to_csv(output/"per_query.csv", index=False, lineterminator="\n")
    json_lf(output/"retrieval_sources.json", retrieval_sources)
    per_surface, summary, residuals = aggregate_scores(all_scores)
    contrasts = []
    for labels, frame in per_surface.groupby(["experiment", "evaluation_partition", "model", "protocol", "duration_s"]):
        pivot = frame.pivot(index=["surface_id", "family_group"], columns="orientation", values="log_power_mae")
        comparison = paired_bootstrap(pivot.forward.to_numpy(), pivot.reverse.to_numpy(), pivot.index.get_level_values("family_group").to_numpy(), draws=2000)
        contrasts.append(dict(zip(["experiment", "partition", "model", "protocol", "duration_s"], labels),
            contrast="forward_minus_reverse", mean_difference=comparison["mean_improvement"],
            ci95_low=comparison["ci95"][0], ci95_high=comparison["ci95"][1], groups=comparison["independent_groups"]))
    for labels, frame in per_surface[per_surface.duration_s == .5].groupby(["experiment", "evaluation_partition", "orientation", "model"]):
        pivot = frame.pivot(index=["surface_id", "family_group"], columns="protocol", values="log_power_mae")
        comparison = paired_bootstrap(pivot["repeat"].to_numpy(), pivot.direction.to_numpy(), pivot.index.get_level_values("family_group").to_numpy(), draws=2000)
        contrasts.append(dict(zip(["experiment", "partition", "orientation", "model"], labels),
            duration_s=.5, contrast="repeat_minus_direction", mean_difference=comparison["mean_improvement"],
            ci95_low=comparison["ci95"][0], ci95_high=comparison["ci95"][1], groups=comparison["independent_groups"]))
    retrieval = all_scores[all_scores.model == "retrieval"]
    keys = ["experiment", "evaluation_partition", "protocol", "duration_s", "surface_id", "query_speed_mm_s", "query_direction_deg", "query_nominal_force_N"]
    identities = retrieval.pivot(index=keys, columns="orientation", values="retrieved_training_id").reset_index()
    identities["identity_changed"] = identities.forward != identities.reverse
    outputs = []
    for suffix, table in [("summary", summary), ("per_surface", per_surface), ("residuals", residuals),
                          ("contrasts", pd.DataFrame(contrasts)), ("retrieval_identity", identities),
                          ("windows", pd.DataFrame(all_audits)), ("reproduction", pd.DataFrame(reproduction))]:
        path = Path(f"docs/repetition_review_{suffix}.csv")
        table.to_csv(path, index=False, lineterminator="\n")
        outputs.append(dict(path=path.as_posix(), sha256=file_hash(path)))
    figure, axes = plt.subplots(1, 3, figsize=(11, 4), sharey=True)
    for ax, (name, partition) in zip(axes, [("expanded", "selection"), ("omitted", "selection"), ("omitted", "transfer")]):
        part = summary[(summary.experiment == name) & (summary.evaluation_partition == partition) &
            (summary.protocol == "single") & (summary.duration_s == .5) & summary.model.isin(["retrieval", "fixed_features", "encoder"])]
        pivot = part.pivot(index="model", columns="orientation", values="log_power_mae").reindex(["retrieval", "fixed_features", "encoder"])
        pivot.plot.bar(ax=ax, rot=20)
        ax.set(title=f"{name}: {partition}", xlabel="", ylabel="Mean log10-power MAE")
        ax.legend(fontsize=8)
    figure.suptitle("Frozen-model repetition sensitivity: two development specimens")
    figure.tight_layout()
    path = Path("docs/repetition_review_primary.png")
    figure.savefig(path, dpi=160); plt.close(figure)
    outputs.append(dict(path=path.as_posix(), sha256=file_hash(path)))
    public = {review_path.as_posix(): file_hash(review_path), **{spec[k]: file_hash(spec[k]) for k in
        ["group_manifest", "reservation_manifest", "exposure_snapshot", "convergence_provenance"]}}
    source_paths = [Path(__file__).relative_to(Path.cwd()), *Path("src/tactile_contact").glob("*.py")]
    json_lf("docs/repetition_review_provenance.json", dict(review_id=spec["review_id"], review_date=spec["review_date"],
        public_input_hashes=public, source_hashes={p.as_posix(): file_hash(p) for p in source_paths},
        input_hashes=inputs, frozen_seal=dict(path=seal.as_posix(), sha256=file_hash(seal)),
        outputs=outputs, reproduction=reproduction, windows=len(all_audits), episodes_per_orientation={c["name"]: len(c["val"]) for c in contexts},
        feature_accesses=access, all_complementary_windows_perturbation_invariant=True,
        no_refit=True, no_new_download=True, reserved_signals_accessed=False,
        environment=dict(python=platform.python_version(), torch=torch.__version__, device="cpu"),
        scope=spec["scope"], claim_limit="Two repeatedly examined development groups; unverified physical clock. No locked scientific test or independent material-family evidence."))
    print(summary[(summary.protocol == "single") & (summary.duration_s == .5)].to_string(index=False), flush=True)
    print(f"Prepared {len(all_audits)} complementary bounded windows; reproduced {len(reproduction)} prediction arrays exactly.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=Path("configs/repetition_review.json"))
    run(parser.parse_args().review)
