"""Review training repeat/floor/range context and saved development convergence."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from tactile_contact.audit import CHANNELS, load_record
from tactile_contact.config import file_hash, load_config, validate_source
from tactile_contact.development_diagnostics import (
    KEYS, validate_review_records, repeat_metrics, floor_sensitivity, history_diagnostic,
)
from tactile_contact.signal import integrate_bands, spectral_features
from tactile_contact.study_design import validate_development_access
from tactile_contact.windows import prepare_acceleration_window


def write_json_lf(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8", newline="\n")


def run(review_path):
    spec = json.loads(review_path.read_text())
    coverage = json.loads(Path(spec["coverage_review"]).read_text())
    groups, reservation = [pd.read_csv(coverage[key]) for key in ["group_manifest", "reservation_manifest"]]
    exposure = json.loads(Path(coverage["exposure_snapshot"]).read_text())
    validate_development_access(coverage["surface_ids"], groups, reservation,
                                exposure["training_surface_ids"]+exposure["selection_surface_ids"])
    if set(coverage["surface_ids"]) != set(exposure["training_surface_ids"]) or coverage["allowed_speeds_mm_s"] != [20, 40, 60]:
        raise ValueError("Diagnostic signals are restricted to the existing known-speed training cohort")
    if spec["duration_logged_s"] != .5:
        raise ValueError("This diagnostic contract requires half-second windows")
    cfg = load_config(coverage["source_config"])
    validate_source(Path("."), cfg)
    convention = json.loads(Path(coverage["clock_convention"]).read_text())
    if any(cfg[k] != convention[k] for k in ["time_base", "sampling_rate_hz"]) or convention["physical_acquisition_clock_verified"]:
        raise ValueError("Expected the declared uncalibrated logged-coordinate convention")
    qc_provenance = json.loads(Path(spec["qc_provenance"]).read_text())
    if cfg["config_hash"] != qc_provenance["source_config_hash"]:
        raise ValueError("Source/QC configuration differs from the audited coverage")
    output_hashes = {r["path"]: r["sha256"] for r in qc_provenance["outputs"]}
    if file_hash(spec["qc_records"]) != output_hashes[spec["qc_records"]]:
        raise ValueError("QC report changed after its coverage audit")
    if file_hash(spec["coverage_review"]) != qc_provenance["review_hash"]:
        raise ValueError("Coverage review settings changed")
    for path, sha in qc_provenance["input_hashes"].items():
        if file_hash(path) != sha:
            raise ValueError(f"QC input changed: {path}")
    domains = pd.read_csv(coverage["domain_table"])
    records = pd.read_csv(spec["qc_records"]).sort_values(KEYS+["repeat_id"]).reset_index(drop=True)
    validate_review_records(records, coverage["surface_ids"], domains)
    if len(records) != coverage["expected_recording_triplets"]:
        raise ValueError("Diagnostic denominator changed")
    input_paths = [review_path.as_posix(), spec["coverage_review"], spec["qc_records"], spec["qc_provenance"],
                   coverage["source_config"], *[coverage[k] for k in ["domain_table", "group_manifest", "reservation_manifest", "exposure_snapshot", "clock_convention"]]]
    input_hashes = {p: file_hash(p) for p in input_paths}
    raw = Path("data/raw/cluster")
    verified = {r["path"]: r["sha256"] for r in qc_provenance["raw_hashes"]}
    range_powers = {r["name"]: [] for r in spec["ranges"]}
    fractions = {r["name"]: [] for r in spec["ranges"]}
    windows, raw_hashes = [], []
    for row in records.itertuples():
        for channel in CHANNELS:
            path = raw/f"sensor_data/{channel}/{row.surface_id}/{row.recording_id}.parquet"
            sha = file_hash(path)
            if verified.get(path.as_posix()) != sha:
                raise ValueError(f"Raw file differs from audited QC input: {path}")
            raw_hashes.append(dict(path=path.as_posix(), sha256=sha))
        frames, times, _ = load_record(raw, row.recording_id)
        fs = cfg["sampling_rate_hz"]
        origin = times["accel"][0]
        index = max(0, int(np.ceil((row.start_s-origin)*fs)))
        start = origin+index/fs
        if start < row.start_s:
            index += 1
            start = origin+index/fs
        if start+spec["duration_logged_s"] > row.start_s+row.usable_duration_s:
            raise ValueError("Canonical raw window exceeds audited steady interval")
        acceleration, dependency = prepare_acceleration_window(frames["accel"], times["accel"], start, spec["duration_logged_s"], fs)
        feature = spectral_features(acceleration, fs=fs, floor=spec["reference_floor"])
        total, _ = integrate_bands(feature["frequency_hz"], feature["psd"], [24., fs/2])
        total_power = total.sum()
        for setting in spec["ranges"]:
            if setting["bands"] != 32 or not 0 < setting["lower"] < setting["upper"] < fs/2:
                raise ValueError("Expected 32 diagnostic bands strictly inside Nyquist")
            powers, _ = integrate_bands(feature["frequency_hz"], feature["psd"],
                                       np.linspace(setting["lower"], setting["upper"], setting["bands"]+1))
            range_powers[setting["name"]].append(powers)
            fractions[setting["name"]].append(0. if total_power == 0 else powers.sum()/total_power)
        windows.append(dict(recording_id=row.recording_id, surface_id=row.surface_id, start_s=start,
                            end_s=start+spec["duration_logged_s"], **dependency))
        if row.repeat_id == 1 and row.direction_deg == 315 and row.speed_mm_s == 60 and row.nominal_force_N == 1.:
            print("Feature review completed training specimen", row.surface_id, flush=True)
    range_powers = {k: np.stack(v) for k, v in range_powers.items()}
    current = range_powers["current"]
    current_setting = next(r for r in spec["ranges"] if r["name"] == "current")
    if (current_setting["lower"], current_setting["upper"], spec["reference_floor"]) != (24, 1000, cfg["power_floor"]):
        raise ValueError("Current diagnostic must match the frozen starter feature definition")
    repeat_tables, range_rows, band_rows = [], [], []
    support = set(domains.loc[domains.support_condition, KEYS[1:]].itertuples(index=False, name=None))
    for setting in spec["ranges"]:
        name = setting["name"]
        table, differences = repeat_metrics(records, range_powers[name], spec["reference_floor"])
        table["range"] = name
        table["known_query"] = [tuple(r) not in support for r in table[KEYS[1:]].itertuples(index=False, name=None)]
        repeat_tables.append(table)
        query = table[table.known_query]
        range_rows.append(dict(**setting, recordings=len(records), all_pairs=len(table), query_pairs=len(query),
            query_repeat_equal_surface_mae=float(query.groupby("surface_id").repeat_log_mae.mean().mean()),
            query_pair_p05=float(query.repeat_log_mae.quantile(.05)), query_pair_median=float(query.repeat_log_mae.median()),
            query_pair_p95=float(query.repeat_log_mae.quantile(.95)),
            query_rms_symmetric_mean=float(query.groupby("surface_id").repeat_rms_symmetric_relative_difference.mean().mean()),
            power_fraction_24_to_nyquist_median=float(np.median(fractions[name])),
            power_fraction_24_to_nyquist_p05=float(np.quantile(fractions[name], .05))))
        if name == "current":
            edges = np.linspace(24, 1000, 33)
            for band in range(32):
                for axis, label in enumerate("XYZ"):
                    values = current[:, band, axis]
                    delta = differences[table.known_query.to_numpy(), band, axis]
                    band_rows.append(dict(band=band, lower=edges[band], upper=edges[band+1], axis=label,
                        minimum_power=float(values.min()), p05_power=float(np.quantile(values, .05)),
                        median_power=float(np.median(values)), query_repeat_mean_log_difference=float(delta.mean())))
    pairs = pd.concat(repeat_tables, ignore_index=True)
    floor_table = floor_sensitivity(current, spec["floors"], spec["reference_floor"])
    current_pairs = pairs[(pairs.range == "current") & pairs.known_query]
    surfaces = current_pairs.groupby("surface_id").agg(query_pairs=("repeat_log_mae", "size"),
        repeat_log_mae=("repeat_log_mae", "mean"), repeat_rms_symmetric_relative_difference=("repeat_rms_symmetric_relative_difference", "mean")).reset_index()
    conditions = current_pairs.groupby(KEYS[1:]).agg(specimens=("surface_id", "size"),
        repeat_log_mae=("repeat_log_mae", "mean"), repeat_log_mae_max=("repeat_log_mae", "max")).reset_index()
    histories, history_rows, history_inputs = [], [], {}
    for root_text in spec["history_roots"]:
        root = Path(root_text)
        manifest_path = root/"results/run_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        historical_cfg = manifest["config"]
        validate_development_access(historical_cfg["train_ids"]+historical_cfg["val_ids"], groups, reservation,
                                    exposure["training_surface_ids"]+exposure["selection_surface_ids"])
        if set(historical_cfg["train_ids"]) != set(exposure["training_surface_ids"]) or set(historical_cfg["val_ids"]) != set(exposure["selection_surface_ids"]):
            raise ValueError("History root contains a different development cohort")
        if manifest["processing_boundary"] != "raw_window_v1":
            raise ValueError("Only corrected histories belong in this review")
        history_inputs[manifest_path.as_posix()] = file_hash(manifest_path)
        for checkpoint_text in manifest["checkpoints"]:
            checkpoint_path = root/checkpoint_text
            checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
            history_path = checkpoint_path.with_name("history.csv")
            history = pd.read_csv(history_path)
            if checkpoint["config_hash"] != historical_cfg["config_hash"]:
                raise ValueError("History checkpoint configuration disagrees with manifest")
            row = dict(run=root.name, seed=checkpoint["seed"],
                **history_diagnostic(history, historical_cfg["training"]["epochs"], checkpoint["selected_epoch"], spec["history_tail_epochs"]))
            history_rows.append(row)
            history["run"], history["seed"] = root.name, checkpoint["seed"]
            histories.append(history)
            for path in [history_path, checkpoint_path]:
                history_inputs[path.as_posix()] = file_hash(path)
    history_table, curves = pd.DataFrame(history_rows), pd.concat(histories, ignore_index=True)
    prefix = spec["output_prefix"]
    outputs = []
    for name, table in [("windows", pd.DataFrame(windows)), ("repeat_pairs", pairs), ("repeat_surfaces", surfaces),
                        ("repeat_conditions", conditions), ("floor", floor_table), ("range", pd.DataFrame(range_rows)),
                        ("bands", pd.DataFrame(band_rows)), ("history", history_table), ("learning_curves", curves)]:
        path = Path(f"docs/{prefix}_{name}.csv")
        table.to_csv(path, index=False, lineterminator="\n")
        outputs.append(dict(path=path.as_posix(), sha256=file_hash(path)))
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    axes[0].bar(surfaces.surface_id.astype(str), surfaces.repeat_log_mae, color="#4778a8")
    axes[0].set(xlabel="Training specimen ID", ylabel="Mean repeat difference (log10 power)", title="44 known query pairs per specimen")
    axes[0].tick_params(axis="x", rotation=45)
    band_table = pd.DataFrame(band_rows)
    for label in "XYZ":
        subset = band_table[band_table.axis == label]
        axes[1].plot((subset.lower+subset.upper)/2, subset.query_repeat_mean_log_difference, label=label)
    axes[1].set(xlabel="Inverse logged-time frequency coordinate", ylabel="Mean absolute repeat difference", title="Current 24–1000 coordinate range")
    axes[1].legend(title="Axis")
    figure.suptitle("Development repeat context: two recordings, retrospective windows")
    figure.tight_layout()
    figure_path = Path(f"docs/{prefix}_repeats.png")
    figure.savefig(figure_path, dpi=160)
    plt.close(figure)
    outputs.append(dict(path=figure_path.as_posix(), sha256=file_hash(figure_path)))
    figure, axes = plt.subplots(2, len(spec["history_roots"]), figsize=(12, 6.5))
    for axis in axes[0, 1:]:
        axis.sharey(axes[0, 0])
    for column, (name, frame) in enumerate(curves.groupby("run", sort=False)):
        for seed, history in frame.groupby("seed"):
            axes[0, column].plot(history.epoch, history.validation_equal_cell_mae, label=f"Seed {seed}")
            tail = history[history.epoch > history.epoch.max()-spec["history_tail_epochs"]]
            axes[1, column].plot(tail.epoch, tail.validation_equal_cell_mae, label=f"Seed {seed}")
        axes[0, column].set(title=name.removeprefix("bounded_"), xlabel="Epoch")
        axes[0, column].legend(fontsize=8)
        axes[1, column].set(title="Last ten saved epochs", xlabel="Epoch")
    axes[0, 0].set_ylabel("Selection equal-cell MAE")
    axes[1, 0].set_ylabel("Selection equal-cell MAE")
    figure.suptitle("Saved corrected development histories; primary-cell history unavailable")
    figure.tight_layout()
    figure_path = Path(f"docs/{prefix}_convergence.png")
    figure.savefig(figure_path, dpi=160)
    plt.close(figure)
    outputs.append(dict(path=figure_path.as_posix(), sha256=file_hash(figure_path)))
    summary = dict(review_id=spec["review_id"], recordings=len(records), repeat_pairs=len(records)//2,
        known_query_pairs=len(current_pairs), query_equal_surface_repeat_mae=float(surfaces.repeat_log_mae.mean()),
        query_pair_median=float(current_pairs.repeat_log_mae.median()),
        query_rms_symmetric_relative_difference=float(surfaces.repeat_rms_symmetric_relative_difference.mean()),
        current_floor_values_below=int(floor_table.loc[floor_table.floor == spec["reference_floor"], "at_or_below_floor"].sum()),
        largest_alternative_floor_log_change=float(floor_table.maximum_log_change.max()),
        histories_reaching_cap=int(history_table.reached_cap.sum()), histories_reviewed=len(history_table),
        histories_selected_within_tail=int(history_table.selected_within_tail.sum()),
        primary_history_available=bool(history_table.primary_history_available.all()),
        feature_qc_model_changed=False, scientific_practical_margin_frozen=False,
        scope=spec["scope"])
    path = Path(f"docs/{prefix}_summary.json")
    write_json_lf(path, summary)
    outputs.append(dict(path=path.as_posix(), sha256=file_hash(path)))
    source_paths = [Path("scripts/review_development_diagnostics.py"), *[Path(f"src/tactile_contact/{name}.py") for name in
        ["development_diagnostics", "audit", "windows", "signal", "study_design", "records", "config"]]]
    write_json_lf(f"docs/{prefix}_provenance.json", dict(review_id=spec["review_id"],
        source_revision=cfg["revision"], accessed_training_surface_ids=coverage["surface_ids"],
        accessed_signal_speeds_mm_s=[20, 40, 60], reserved_signals_accessed=False,
        input_hashes=input_hashes, history_input_hashes=history_inputs,
        source_hashes={p.as_posix(): file_hash(p) for p in source_paths}, raw_hashes=raw_hashes, outputs=outputs,
        scope=spec["scope"]))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=Path("configs/development_diagnostics.json"))
    run(parser.parse_args().review)
