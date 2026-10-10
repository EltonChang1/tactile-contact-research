"""Run guarded matched familiar/omitted development fits and frozen scoring."""
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
from tactile_contact.baselines import ConditionsOnly, CopySpectrum, FixedFeatures, Retrieval, SpeedRescaling
from tactile_contact.config import PROTOCOLS, digest, file_hash, load_config
from tactile_contact.convergence import json_lf
from tactile_contact.evaluation import score_predictions
from tactile_contact.matched import MatchedStore, build_matched_episodes, fit_matched, wrong_support_by_orientation
from tactile_contact.metrics import paired_bootstrap
from tactile_contact.repetition_review import aggregate_scores
from tactile_contact.signal import spectral_features
from tactile_contact.study_design import query_domains, validate_development_access
from tactile_contact.training import model_predictions
from tactile_contact.windows import prepare_acceleration_window


def read(path):
    return json.loads(Path(path).read_text())


def preflight(spec):
    design = read(spec["design"])
    groups, reservation = [pd.read_csv(design[k]) for k in ["group_manifest", "reservation_manifest"]]
    exposure = read(design["exposure_snapshot"])
    validate_development_access(design["train_ids"]+design["selection_and_score_ids"], groups, reservation,
        exposure["training_surface_ids"]+exposure["selection_surface_ids"])
    if design["train_ids"] != exposure["training_surface_ids"] or design["selection_and_score_ids"] != exposure["selection_surface_ids"]:
        raise ValueError("Matched run retains exact exposed cohorts")
    if design["stage"] != "development_only":
        raise ValueError("Matched runner accepts development only, not locked test scoring")
    budgets = design["budgets"]
    if budgets["protocols"] != list(PROTOCOLS) or budgets["support_durations_logged_s"] != [.25, .5, 1.] or budgets["query_duration_logged_s"] != .5:
        raise ValueError("Retain all original matched protocols and durations")
    if budgets["sampling_grid_hz"] != 6000 or budgets["power_floor"] != 1e-10 or budgets["feature_range_logged_frequency"] != [24, 1000] or budgets["spectral_bands_per_axis"] != 32:
        raise ValueError("Retain current grid and spectral features")
    inputs = {}
    for key in ["transfer_training_provenance", "validation_provenance"]:
        proof = read(spec[key])
        for section in ["public_input_hashes", "source_hashes", "shared_input_hashes"]:
            for path, sha in proof[section].items():
                if file_hash(path) != sha:
                    raise ValueError(f"Coverage input changed: {path}")
                inputs[path] = sha
        for row in proof["outputs"]:
            if file_hash(row["path"]) != row["sha256"]:
                raise ValueError("Coverage output changed")
            inputs[row["path"]] = row["sha256"]
        for row in proof["raw_hashes"]:
            path = Path(proof["raw_root"])/row["path"]
            if file_hash(path) != row["sha256"]:
                raise ValueError("Pinned matched raw input changed")
            inputs[path.as_posix()] = row["sha256"]
        inputs[spec[key]] = file_hash(spec[key])
    known_proof = read("docs/wider_contact_qc_provenance.json")
    for row in known_proof["raw_hashes"]:
        if file_hash(row["path"]) != row["sha256"]:
            raise ValueError("Known-speed training raw input changed")
        inputs[row["path"]] = row["sha256"]
    for key in ["training_common_eligibility", "validation_common_eligibility"]:
        eligibility = pd.read_csv(spec[key])
        if not eligibility.common_candidate.all():
            raise ValueError("Complete prespecified common cohort required; review QC attrition before fitting")
    domains = pd.read_csv(design["domain_table"])
    pd.testing.assert_frame_equal(domains.fillna(""), query_domains().fillna(""), check_dtype=False)
    policy = read(design["training_policy"])
    if design["training"]["epochs"] != policy["epoch_cap"] or policy["epoch_cap"] != 120:
        raise ValueError("Matched finite cap changed")
    for k in ["patience", "seeds", "learning_rate", "batch_size", "episodes_per_surface", "latent_dim", "gradient_norm_clip", "optimizer"]:
        if design["training"][k] != policy[k]:
            raise ValueError(f"Matched policy changed: {k}")
    convention = read(design["clock_convention"])
    cfg = load_config("configs/omitted_speed.yaml")
    if convention["physical_acquisition_clock_verified"] or cfg["revision"] != design["source_revision"]:
        raise ValueError("Retain logged coordinates and pinned source")
    for k in ["sampling_rate_hz", "time_base"]:
        if cfg[k] != convention[k]:
            raise ValueError("Clock/grid convention changed")
    for path in [spec["design"], *[design[k] for k in ["group_manifest", "reservation_manifest", "exposure_snapshot", "domain_table", "clock_convention", "training_policy"]],
                 *[spec[k] for k in ["training_transfer_records", "training_known_records", "validation_records"]]]:
        inputs[path] = file_hash(path)
    return design, groups, domains, cfg, inputs


def window_manifest(design, domains, cfg, output, spec):
    train = pd.concat([pd.read_csv(spec[k], float_precision="round_trip") for k in ["training_known_records", "training_transfer_records"]], ignore_index=True)
    validation = pd.read_csv(spec["validation_records"], float_precision="round_trip")
    records = pd.concat([train.assign(split="train"), validation.assign(split="val")], ignore_index=True)
    if len(records) != 1776 or records.recording_id.duplicated().any():
        raise ValueError("Complete unique 1480 training /296 validation records required")
    supports = {tuple(c) for protocol in PROTOCOLS.values() for c in protocol}
    support_conditions = {c[:3] for c in supports}
    queries = set(domains.loc[domains.matched_familiar_fit_query, ["speed_mm_s", "direction_deg", "nominal_force_N"]].itertuples(index=False, name=None))
    processing_hash = digest(dict(qc=cfg["qc"], time_base=cfg["time_base"], fs=cfg["sampling_rate_hz"], floor=cfg["power_floor"], boundary="raw_window_v1", revision=cfg["revision"]))
    rows = []
    for record in records.itertuples():
        condition = record.speed_mm_s, record.direction_deg, record.nominal_force_N
        key = (*condition, record.repeat_id)
        if condition in support_conditions and (record.split == "val" or key in supports):
            roles = [("support", d) for d in design["budgets"]["support_durations_logged_s"]]
        elif condition in queries:
            roles = [("query", .5)]
        else:
            continue
        source = "data/raw/cluster" if record.split == "train" and record.speed_mm_s in [20, 40, 60] else \
            "runs/transfer_training_coverage/data/raw/cluster" if record.split == "train" else "runs/selection_transfer_coverage/data/raw/cluster"
        for role, duration in roles:
            if record.canonical_start_s+duration > record.steady_end_s:
                raise ValueError("Canonical matched window not available")
            window_id = f"{record.recording_id}_{role}_{duration:g}_{processing_hash[:12]}"
            deferred = record.split == "val" and role == "query" and not (record.speed_mm_s in [20, 40, 60] and record.repeat_id == 1)
            rows.append(dict(window_id=window_id, recording_id=record.recording_id, surface_id=record.surface_id, split=record.split,
                speed_mm_s=record.speed_mm_s, direction_deg=record.direction_deg, nominal_force_N=record.nominal_force_N,
                repeat_id=record.repeat_id, role=role, duration_s=duration, start_s=record.canonical_start_s, end_s=record.canonical_start_s+duration,
                raw_root=source, feature_path=f"features/{window_id}.npz", window_config_hash=processing_hash, deferred_until_selection_seal=deferred))
    return pd.DataFrame(rows).sort_values("window_id").reset_index(drop=True)


def prepare_phase(windows, output, deferred):
    audits = []
    subset = windows[windows.deferred_until_selection_seal == deferred]
    for index, ((raw_root, recording_id), group) in enumerate(subset.groupby(["raw_root", "recording_id"], sort=True)):
        frames, times, _ = load_record(raw_root, recording_id)
        for row in group.itertuples():
            values, dependency = prepare_acceleration_window(frames["accel"], times["accel"], row.start_s, row.duration_s, 6000)
            altered = frames["accel"].copy()
            outside = (times["accel"] < row.start_s) | (times["accel"] >= row.end_s)
            altered.loc[outside, ["X", "Y", "Z"]] = 12345.
            check, _ = prepare_acceleration_window(altered, times["accel"], row.start_s, row.duration_s, 6000)
            if not np.array_equal(values, check):
                raise ValueError("Matched window depends on outside acceleration")
            path = output/row.feature_path
            path.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(path, **spectral_features(values, fs=6000, floor=1e-10))
            audits.append(dict(window_id=row.window_id, phase="post_selection_scoring" if deferred else "fit_selection_preparation",
                feature_sha256=file_hash(path), outside_perturbation_equal=True, **dependency))
        if (index+1) % 100 == 0:
            print(f"Prepared {'scoring' if deferred else 'fit'} features: {index+1} recordings", flush=True)
    return audits


def save_baselines(destination, models):
    destination.mkdir(parents=True)
    for name in ["conditions_only", "fixed_features"]:
        model = models[name]
        arrays = dict(coefficient=model.regression.coef_, intercept=model.regression.intercept_)
        if name == "fixed_features":
            arrays.update(feature_mean=model.mean, feature_std=model.std, alpha=np.array(model.alpha))
            json_lf(destination/"fixed_features_selection.json", model.candidates)
        np.savez_compressed(destination/f"{name}_fit.npz", **arrays)
    speed = models["speed_rescaling"]
    json_lf(destination/"speed_rescaling_fit.json", dict(p=float(speed.exponents[0]), b=float(speed.exponents[1]), selected_alpha=speed.alpha, candidates=speed.candidates))
    retrieval = models["retrieval"]
    arrays, sources = {}, dict(library={}, responses={})
    for (protocol, duration), (fingerprints, ids) in retrieval.library.items():
        label = f"{protocol}_{duration:g}"
        arrays[f"fingerprints_{label}"], arrays[f"training_ids_{label}"] = fingerprints, ids
        sources["library"][label] = retrieval.library_sources[(protocol, duration)]
    for key, values in retrieval.responses.items():
        label = "_".join(map(str, key))
        arrays[f"response_{label}"] = values; sources["responses"][label] = retrieval.response_sources[key]
    np.savez_compressed(destination/"retrieval_fit.npz", **arrays)
    json_lf(destination/"retrieval_sources.json", sources)


def run(review_path):
    torch.set_num_threads(1)
    spec = read(review_path)
    design, groups, domains, original_cfg, inputs = preflight(spec)
    output = Path(spec["output_root"])
    if output.exists():
        raise ValueError("Preserve matched evidence; use a fresh output root")
    output.mkdir(parents=True)
    source_paths = [Path(__file__).relative_to(Path.cwd()), *Path("src/tactile_contact").glob("*.py")]
    source_hashes = {p.as_posix(): file_hash(p) for p in source_paths}
    inputs[review_path.as_posix()] = file_hash(review_path)
    json_lf(output/"execution_seal.json", dict(review=spec, design=design, inputs=inputs, source_hashes=source_hashes))
    windows = window_manifest(design, domains, original_cfg, output, spec)
    if len(windows) != 1878 or int(windows.deferred_until_selection_seal.sum()) != 192:
        raise ValueError("Matched preparation denominator changed")
    windows.to_csv(output/"windows.csv", index=False, lineterminator="\n")
    audits = prepare_phase(windows, output, False)
    contexts, histories, selections, baseline_selections, selected_artifacts = [], [], [], [], {}
    for name in ["familiar", "omitted"]:
        cfg = dict(original_cfg, experiment="familiar_conditions" if name == "familiar" else "omitted_speed",
            training={k: design["training"][k] for k in ["epochs", "patience", "seeds", "learning_rate", "batch_size", "episodes_per_surface", "latent_dim"]})
        cfg["config_hash"] = digest(dict(review=spec["review_id"], name=name, design=design, processing=windows.window_config_hash.iloc[0]))
        episodes = build_matched_episodes(windows, groups, design, domains, name, cfg["config_hash"])
        train = episodes[episodes.split == "train"].reset_index(drop=True)
        selection = episodes[(episodes.split == "val") & (episodes.evaluation_partition == "selection") & (episodes.orientation == "forward")].reset_index(drop=True)
        val = episodes[episodes.split == "val"].reset_index(drop=True)
        if len(train) != (21000 if name == "familiar" else 13200) or len(selection) != 1320 or len(val) != 4200:
            raise ValueError("Matched role counts changed")
        destination = output/name
        destination.mkdir()
        episodes.to_csv(destination/"episodes.csv", index=False, lineterminator="\n")
        store = MatchedStore(output, windows, train, selection)
        support_ids = sorted({w for encoded in train.support_window_ids for w in json.loads(encoded)})
        values = np.stack([store.feature(w)["log_band_power"].reshape(-1) for w in support_ids])
        std = values.std(axis=0); std[std < 1e-8] = 1.
        scaler = dict(mean=values.mean(axis=0), std=std)
        if contexts and not all(np.array_equal(scaler[k], contexts[0]["scaler"][k]) for k in scaler):
            raise ValueError("Matched training-support scalers differ")
        np.savez_compressed(destination/"scaler.npz", **scaler)
        print(f"Fitting {name}: {len(train)} train and {len(selection)} selection episodes", flush=True)
        models = dict(conditions_only=ConditionsOnly().fit(train, store, scaler), copy=CopySpectrum(),
            retrieval=Retrieval(interpolate_speeds=name == "omitted").fit(train, store, scaler),
            fixed_features=FixedFeatures().fit(train, selection, store, scaler),
            speed_rescaling=SpeedRescaling().fit(train, selection, store, scaler))
        save_baselines(destination/"baselines", models)
        baseline_selections.extend(dict(experiment=name, model=method) for method in models)
        encoders = {}
        for seed in design["training"]["seeds"]:
            model, metadata = fit_matched(destination/f"seed_{seed}", cfg, train, selection, store, scaler, seed)
            encoders[seed] = model
            selections.append(dict(experiment=name, **metadata))
            histories.append(pd.read_csv(destination/f"seed_{seed}/history.csv", float_precision="round_trip").assign(experiment=name, seed=seed))
        for path in destination.rglob("*"):
            if path.is_file() and path.suffix in [".npz", ".pt", ".json", ".csv"]:
                selected_artifacts[path.as_posix()] = file_hash(path)
        contexts.append(dict(name=name, cfg=cfg, episodes=episodes, train=train, selection=selection, val=val,
            store=store, scaler=scaler, models=models, encoders=encoders))
    seal_path = output/"selection_complete.json"
    json_lf(seal_path, dict(completed_experiments=["familiar", "omitted"], encoder_selections=len(selections),
        baseline_selections=len(baseline_selections), selected_artifact_hashes=selected_artifacts,
        deferred_targets_prepared=False, reverse_used_for_selection=False))
    audits.extend(prepare_phase(windows, output, True))
    scores, scoring_artifacts, retrieval_sources = [], {}, []
    for context in contexts:
        val, store, name = context["val"], context["store"], context["name"]
        store.unlock_scoring(val, seal_path)
        predictions, outputs = {}, []
        for method, model in context["models"].items():
            result = model.predict(val, store, context["scaler"])
            prediction, ids = result if isinstance(result, tuple) else (result, None)
            outputs.append((method, -1, prediction, ids)); predictions[method] = prediction
            if method == "retrieval":
                retrieval_sources.extend(dict(experiment=name, **row) for row in model.prediction_sources)
        for seed, model in context["encoders"].items():
            for method, rows in [("encoder", val), ("encoder_wrong_support", wrong_support_by_orientation(val))]:
                prediction = model_predictions(model, rows, store, context["scaler"])
                outputs.append((method, seed, prediction, None)); predictions[f"{method}_{seed}"] = prediction
        target = store.targets(val)
        path = output/name/"predictions.npz"
        np.savez_compressed(path, episode_ids=val.episode_id.to_numpy(dtype=str), targets=target, **predictions)
        scoring_artifacts[path.as_posix()] = file_hash(path)
        for method, seed, prediction, ids in outputs:
            table = score_predictions(val, prediction, target, method, seed, 1e-10, ids)
            table["experiment"] = name; scores.append(table)
    result = pd.concat(scores, ignore_index=True)
    result.to_csv(output/"per_query.csv", index=False, lineterminator="\n")
    scoring_artifacts[(output/"per_query.csv").as_posix()] = file_hash(output/"per_query.csv")
    json_lf(output/"retrieval_prediction_sources.json", retrieval_sources)
    per_surface, summary, residuals = aggregate_scores(result)
    comparisons = []
    for labels, frame in per_surface.groupby(["evaluation_partition", "orientation", "model", "protocol", "duration_s"]):
        pivot = frame.pivot(index=["surface_id", "family_group"], columns="experiment", values="log_power_mae")
        comparison = paired_bootstrap(pivot.omitted.to_numpy(), pivot.familiar.to_numpy(), pivot.index.get_level_values("family_group").to_numpy(), draws=2000)
        comparisons.append(dict(zip(["partition", "orientation", "model", "protocol", "duration_s"], labels), contrast="omitted_minus_familiar",
            mean_difference=comparison["mean_improvement"], ci95_low=comparison["ci95"][0], ci95_high=comparison["ci95"][1], groups=2))
    for labels, frame in per_surface[per_surface.duration_s == .5].groupby(["experiment", "evaluation_partition", "orientation", "model"]):
        pivot = frame.pivot(index=["surface_id", "family_group"], columns="protocol", values="log_power_mae")
        comparison = paired_bootstrap(pivot["repeat"].to_numpy(), pivot.direction.to_numpy(), pivot.index.get_level_values("family_group").to_numpy(), draws=2000)
        comparisons.append(dict(zip(["experiment", "partition", "orientation", "model"], labels), duration_s=.5, contrast="repeat_minus_direction",
            mean_difference=comparison["mean_improvement"], ci95_low=comparison["ci95"][0], ci95_high=comparison["ci95"][1], groups=2))
    public_outputs = []
    for suffix, table in [("summary", summary), ("per_surface", per_surface), ("contrasts", pd.DataFrame(comparisons)),
        ("selections", pd.DataFrame(selections)), ("histories", pd.concat(histories, ignore_index=True)), ("windows", pd.DataFrame(audits)),
        ("primary_residuals", residuals[(residuals.duration_s == .5) & residuals.protocol.isin(["single", "repeat", "direction"])])]:
        path = Path(f"docs/matched_review_{suffix}.csv")
        table.to_csv(path, index=False, lineterminator="\n")
        public_outputs.append(dict(path=path.as_posix(), sha256=file_hash(path)))
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for axis, orientation in zip(axes, ["forward", "reverse"]):
        table = summary[(summary.evaluation_partition == "transfer") & (summary.orientation == orientation) &
            (summary.protocol == "single") & (summary.duration_s == .5) & summary.model.isin(["retrieval", "fixed_features", "encoder"])]
        table.pivot(index="model", columns="experiment", values="log_power_mae").reindex(["retrieval", "fixed_features", "encoder"]).plot.bar(ax=axis, rot=15)
        axis.set(title=f"Matched transfer: {orientation}", ylabel="Mean log10-power MAE", xlabel="")
    fig.suptitle("Same 26 query triples; two development specimens; frozen scoring")
    fig.tight_layout(); path = Path("docs/matched_review_primary.png")
    fig.savefig(path, dpi=160); plt.close(fig)
    public_outputs.append(dict(path=path.as_posix(), sha256=file_hash(path)))
    for path, sha in source_hashes.items():
        if file_hash(path) != sha:
            raise ValueError("Matched execution source changed during run")
    json_lf("docs/matched_review_provenance.json", dict(review_id=spec["review_id"], review_date=spec["review_date"], input_hashes=inputs,
        source_hashes=source_hashes, output_root=output.as_posix(), execution_seal=dict(path=(output/"execution_seal.json").as_posix(), sha256=file_hash(output/"execution_seal.json")),
        selection_seal=dict(path=seal_path.as_posix(), sha256=file_hash(seal_path)), selected_artifact_hashes=selected_artifacts,
        scoring_artifact_hashes=scoring_artifacts, outputs=public_outputs, windows=len(windows), deferred_target_windows=192,
        selections=selections, feature_accesses=[dict(experiment=c["name"], phase=p, window_id=w) for c in contexts for p, w in sorted(c["store"].accesses)],
        shared_scaler_exact=True, all_windows_outside_perturbation_invariant=True, reserved_signals_accessed=False,
        environment=dict(python=platform.python_version(), torch=torch.__version__, device="cpu"), scope=spec["scope"],
        claim_limit="Matched development comparison on two exposed groups, not the broader 76-query primary scientific study or locked test. Physical acquisition clock unverified."))
    print(summary[(summary.protocol == "single") & (summary.duration_s == .5)].to_string(index=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=Path("configs/matched_fit_review.json"))
    run(parser.parse_args().review)
