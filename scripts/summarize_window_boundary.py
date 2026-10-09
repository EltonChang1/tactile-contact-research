"""Audit raw-window preparation and preserve before/after development evidence."""
import argparse
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from tactile_contact.audit import load_record
from tactile_contact.config import data_root, file_hash, write_json, speed_bracket
from tactile_contact.signal import spectral_features
from tactile_contact.windows import prepare_acceleration_window, PROCESSING_BOUNDARY


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def csv(path):
    return pd.read_csv(path, float_precision="round_trip")


def audit_pair(name, before, after):
    old, new = read(before/"results/run_manifest.json"), read(after/"results/run_manifest.json")
    cfg = new["config"]
    if old["config"]["config_hash"] != cfg["config_hash"] or new["processing_boundary"] != PROCESSING_BOUNDARY:
        raise ValueError("Require matching scientific configs and corrected boundary provenance")
    for root, manifest in [(before, old), (after, new)]:
        for filename, expected in manifest["manifest_hashes"].items():
            if file_hash(root/"data/manifests"/filename) != expected:
                raise ValueError(f"Changed historical/current manifest: {root}/{filename}")
    previous = csv(before/"data/manifests/windows.csv").set_index("window_id")
    current = csv(after/"data/manifests/windows.csv")
    if set(previous.index) != set(current.window_id):
        raise ValueError("Window cohort changed")
    old_episodes = csv(before/"data/manifests/episodes.csv").set_index("episode_id").sort_index()
    new_episodes = csv(after/"data/manifests/episodes.csv").set_index("episode_id").sort_index()
    shared = ["surface_id", "split", "protocol", "duration_s", "support_window_ids", "query_window_id",
              "query_speed_mm_s", "query_direction_deg", "query_nominal_force_N"]
    pd.testing.assert_frame_equal(old_episodes[shared], new_episodes[shared])
    raw = data_root(after, cfg)/"data/raw"/cfg["source_kind"]
    inventory = read(data_root(after, cfg)/"data/raw_inventory.json")
    hashes = {row["path"]:row["sha256"] for row in inventory["files"]}
    verified_raw = {}
    rows = []
    for recording, windows in current.groupby("recording_id"):
        for channel in ["accel", "force", "position"]:
            relative = f"sensor_data/{channel}/{recording.split('_')[0]}/{recording}.parquet"
            actual = file_hash(raw/relative)
            if actual != hashes.get(relative):
                raise ValueError("Raw recording hash changed or is absent from inventory")
            verified_raw[relative] = actual
        frames, times, _ = load_record(raw, recording)
        for row in windows.itertuples():
            prior = previous.loc[row.window_id]
            if not np.allclose([prior.start_s, prior.end_s], [row.start_s, row.end_s], rtol=0, atol=1e-12):
                raise ValueError("Canonical window coordinates changed")
            historical_indices = (int(np.searchsorted(times["accel"], prior.start_s)),
                                  int(np.searchsorted(times["accel"], prior.end_s)))
            if "raw_start_index" in prior:
                historical_indices = (prior.raw_start_index, prior.raw_end_index_exclusive)
            if historical_indices != (row.raw_start_index, row.raw_end_index_exclusive):
                raise ValueError("Selected raw sample interval changed")
            original, provenance = prepare_acceleration_window(frames["accel"], times["accel"],
                                                              row.start_s, row.duration_s, cfg["sampling_rate_hz"])
            outside = (times["accel"] < row.start_s) | (times["accel"] >= row.end_s)
            changed = frames["accel"].astype({axis:np.float64 for axis in ["X", "Y", "Z"]})
            changed.loc[outside, ["X", "Y", "Z"]] = np.arange(outside.sum())[:, None]*np.array([[1e5, -3e5, 7e5]])
            attacked, attacked_provenance = prepare_acceleration_window(changed, times["accel"],
                                                                       row.start_s, row.duration_s, cfg["sampling_rate_hz"])
            np.testing.assert_array_equal(original, attacked)
            if attacked_provenance != provenance:
                raise ValueError("Outside acceleration changed processing dependencies")
            feature = spectral_features(original, fs=cfg["sampling_rate_hz"], floor=cfg["power_floor"])
            with np.load(after/row.feature_path) as actual, np.load(before/prior.feature_path) as historical:
                np.testing.assert_array_equal(actual["log_band_power"], feature["log_band_power"])
                difference = np.abs(actual["log_band_power"]-historical["log_band_power"])
            for key, value in provenance.items():
                if getattr(row, key) != value:
                    raise ValueError(f"Recorded processing dependency mismatch: {key}")
            rows.append({"run":name, "window_id":row.window_id, "surface_id":row.surface_id,
                         "split":row.split, "role":row.role, "duration_s":row.duration_s,
                         "start_s":row.start_s, "end_s":row.end_s, **provenance,
                         "outside_perturbation_max_processed_change":float(np.abs(original-attacked).max()),
                         "before_after_mean_log_feature_change":float(difference.mean()),
                         "before_after_max_log_feature_change":float(difference.max())})
    for _, part in current[current.role == "support"].groupby("recording_id"):
        ordered = part.sort_values("duration_s")
        if ordered.start_s.nunique() != 1 or ordered.raw_start_index.nunique() != 1 or (np.diff(ordered.raw_end_index_exclusive) <= 0).any():
            raise ValueError("Raw observation intervals do not nest")
    changed_software = sorted(key for key, value in new["software_hashes"].items() if old["software_hashes"].get(key) != value)
    primary = []
    for label, root in [("historical", before), ("bounded", after)]:
        summary = csv(root/"results/tables/summary.csv")
        if "evaluation_partition" not in summary:
            summary["evaluation_partition"] = "selection"
        chosen = summary[(summary.protocol == "single") & (summary.duration_s == .5)]
        primary.append(chosen.assign(run=name, preparation=label))
    if name == "omitted":
        fit = read(after/"results/tables/fit_selection_manifest.json")
        if fit["fit_speeds_mm_s"] != [20,40,60] or fit["selection_speeds_mm_s"] != [20,40,60]:
            raise ValueError("Omitted-speed separation changed")
        transfer_count = 0
        lookup = new_episodes
        for row in read(after/"results/tables/retrieval_prediction_sources.json")["predictions"]:
            episode = lookup.loc[row["episode_id"]]
            if not {key[1] for key in row["response_keys"]}.issubset({20,40,60}):
                raise ValueError("Retrieval used an omitted-speed label")
            if episode.evaluation_partition == "transfer":
                if [key[1] for key in row["response_keys"]] != list(speed_bracket(episode.query_speed_mm_s)) or row["weights"] != [.5,.5]:
                    raise ValueError("Transfer interpolation changed")
                transfer_count += 1
        if transfer_count != int((new_episodes.evaluation_partition == "transfer").sum()):
            raise ValueError("Incomplete transfer provenance")
    record = {"before_root":before.as_posix(), "after_root":after.as_posix(),
              "config_hash":cfg["config_hash"], "windows":len(current), "episodes":len(new_episodes),
              "support_windows":int((current.role == "support").sum()),
              "historical_raw_indices_recorded":"raw_start_index" in previous.columns,
              "changed_software_modules":changed_software, "raw_hashes_verified":verified_raw,
              "before_manifest_hash":file_hash(before/"results/run_manifest.json"),
              "after_manifest_hash":file_hash(after/"results/run_manifest.json"),
              "after_run_manifest":new}
    return pd.DataFrame(rows), pd.concat(primary, ignore_index=True), record


def main():
    parser = argparse.ArgumentParser()
    for label, before, after in [("initial", ".", "runs/bounded_pilot"),
                                 ("expanded", "runs/expanded_pilot", "runs/bounded_expanded_pilot"),
                                 ("omitted", "runs/omitted_speed", "runs/bounded_omitted_speed")]:
        parser.add_argument(f"--before-{label}", default=before)
        parser.add_argument(f"--after-{label}", default=after)
    parser.add_argument("--output", default="docs")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    windows, primary, runs = [], [], {}
    for label in ["initial", "expanded", "omitted"]:
        before, after = Path(getattr(args, f"before_{label}")), Path(getattr(args, f"after_{label}"))
        table, scores, runs[label] = audit_pair(label, before, after)
        windows.append(table); primary.append(scores)
        summary = csv(after/"results/tables/summary.csv")
        summary.to_csv(output/f"bounded_{label}_summary.csv", index=False, lineterminator="\n")
        print(f"Audited {label}: {len(table)} raw windows; unchanged episodes and raw intervals", flush=True)
    windows = pd.concat(windows, ignore_index=True)
    primary = pd.concat(primary, ignore_index=True)
    windows.to_csv(output/"window_boundary_audit.csv", index=False, lineterminator="\n")
    primary.to_csv(output/"window_boundary_primary.csv", index=False, lineterminator="\n")
    changes = windows.groupby(["run", "split", "role", "duration_s"], as_index=False).agg(
        windows=("window_id", "size"),
        median_mean_log_feature_change=("before_after_mean_log_feature_change", "median"),
        max_mean_log_feature_change=("before_after_mean_log_feature_change", "max"),
        max_single_log_feature_change=("before_after_max_log_feature_change", "max"),
        max_outside_processed_change=("outside_perturbation_max_processed_change", "max"))
    changes.to_csv(output/"window_boundary_feature_changes.csv", index=False, lineterminator="\n")
    for label in ["expanded", "omitted"]:
        after = Path(getattr(args, f"after_{label}"))
        tables = after/"results/tables"
        if label == "expanded":
            exports = [tables/"budget_contrasts.csv", tables/"diagnostic_subsets.csv", tables/"paired_comparisons.json"]
        else:
            exports = [tables/part/name for part in ["selection", "transfer"] for name in
                       ["budget_contrasts.csv", "diagnostic_subsets.csv", "paired_comparisons.json"]]
        for source in exports:
            partition = f"{source.parent.name}_" if source.parent != tables else ""
            (output/f"bounded_{label}_{partition}{source.name}").write_bytes(source.read_text(encoding="utf-8").encode("utf-8"))
        runs[label]["timing_sensitivity"] = read(tables/"timing_sensitivity.json")
        figures = output/"figures"; figures.mkdir(exist_ok=True)
        source = after/"results/figures"/("transfer/probe_budget_errors.png" if label == "omitted" else "probe_budget_errors.png")
        shutil.copyfile(source, figures/f"bounded_{label}_probe_budget.png")
    lines = ["# Raw-window boundary correction — 9 October 2026", "",
             "Acceleration is now cropped to the declared half-open raw interval before interpolation and anti-alias filtering. The local grid rate uses only allowed timestamps. Interpolation holds local endpoints and polyphase filtering extends a line derived from those local endpoints; no observed signal context is borrowed. Raw prefixes nest, while independently processed edges may differ. This fixes the acceleration information boundary with retrospective starts/QC held fixed; it does not establish causal onset detection or a calibrated acquisition clock.", "",
             f"The source suite passed 53 tests, including nine new boundary checks, and compilation. The audit perturbed outside acceleration in all **{len(windows)}** prepared windows (support and query) across three real reruns. Every processed array was bit-for-bit invariant; recomputed features matched their caches. Exact processing dependencies, padding, rate factors and counts are saved in [window audit](window_boundary_audit.csv). Window IDs, raw intervals, canonical coordinates, episode inputs and scientific configurations match historical runs, and original recording hashes were verified.", "",
             "All five baselines, three encoder seeds and wrong-support predictions were freshly generated in isolated output roots. Historical outputs remain intact. Before/after feature changes include both local edge treatment and estimating the interpolation rate locally; they do not isolate either mechanism. Refitted score changes also include altered query targets and checkpoint selection. Historical initial/expanded code versions differ in additional modules, and the initial rerun adds two later baselines; see changed modules in provenance. The omitted-speed package differs only in window preparation and its pipeline/timing provenance. Do not attribute every score change solely to previously borrowed acceleration.", "",
             "## Primary development comparison", "",
             "Single 0.5-second support; seed means within specimen, then equal specimen means. Omitted rows use transfer; the other rows use selection. Grids differ between experiments and still involve only two development validation specimens.", "",
             "| Experiment | Method | Historical MAE | Bounded MAE |", "| --- | --- | ---: | ---: |"]
    for label in ["initial", "expanded", "omitted"]:
        part = primary[(primary.run == label) & (primary.evaluation_partition == ("transfer" if label == "omitted" else "selection"))]
        for model in ["retrieval", "fixed_features", "encoder", "encoder_wrong_support"]:
            values = part[part.model == model].set_index("preparation").log_power_mae
            historical = f"{values['historical']:.4f}" if "historical" in values else "Not previously fitted"
            lines.append(f"| {label} | {model} | {historical} | {values['bounded']:.4f} |")
    paired = next(row for row in read(output/"bounded_omitted_transfer_paired_comparisons.json")["comparisons"]
                  if row["protocol"] == "single" and row["duration_s"] == .5)
    lines += ["", f"Retrieval still leads the expanded familiar-condition pilot; fixed-feature regression still has the lowest omitted-speed log-power MAE. Retrieval retains the lowest omitted-speed modeled-band RMS error among these three methods. Retrieval-minus-encoder transfer MAE is {paired['mean_improvement']:.4f}, with a two-group diagnostic interval [{paired['ci95'][0]:.4f}, {paired['ci95'][1]:.4f}]; it spans zero. No learned-model superiority, preferred scientific probe or fresh-test result is established.", "",
              "## Feature and clock effects", "", "| Run | Median per-window mean log-feature change | Maximum per-window mean change |", "| --- | ---: | ---: |"]
    for label, part in windows.groupby("run", sort=False):
        lines.append(f"| {label} | {part.before_after_mean_log_feature_change.median():.6f} | {part.before_after_mean_log_feature_change.max():.6f} |")
    lines += ["", "These are log10 band-power feature differences, not force errors or calibrated physical time. Duration/role/split breakdowns are in [feature changes](window_boundary_feature_changes.csv). Timing remains consequential: the bounded expanded and omitted runs retain median nominal-index/logged-duration ratios of 1.4388 and 1.44; corresponding median log-feature clock differences are 0.3523 and 0.3914. The paths assign different nominal durations and frequency coordinates, so sensitivity does not choose the correct clock.", "",
              "![Bounded familiar-condition duration/probe curves](figures/bounded_expanded_probe_budget.png)", "",
              "![Bounded omitted-speed duration/probe curves](figures/bounded_omitted_probe_budget.png)", "",
              "## Reproduction and remaining gates", "",
              "Run the commands in the [README](../README.md), then `python scripts/summarize_window_boundary.py` with the environment interpreter from the repository root. The before/after audit requires the three retained historical local roots as well as their corrected reruns; a clean clone can reproduce corrected runs but needs reconstructed historical runs to regenerate this comparison. The report audits matching manifests, raw-file hashes, interval dependencies, cache reconstruction, raw nesting and all 120 omitted-speed retrieval endpoint/weight records. The initial historical manifest lacked raw indices, which this audit derives from its preserved window coordinates and the verified original timestamps. Transfer labels remain excluded until every method/checkpoint is selected.", "",
              "Aggregate matrices: [initial](bounded_initial_summary.csv), [expanded](bounded_expanded_summary.csv), [omitted](bounded_omitted_summary.csv); [primary before/after scores](window_boundary_primary.csv); [run and audit provenance](window_boundary_provenance.json). Raw data, full predictions and checkpoints remain local/ignored; release reconstruction still needs the documented dataset and environment.", "",
              "Next: investigate clock evidence or freeze an explicit logged-coordinate claim, review motion/heading/load and coverage, maintain the exposure ledger, quantify repeatability/convergence and run a matched-grid familiar/omitted development comparator. All twelve current specimens remain development-exposed. A fresh locked scientific test is unimplemented, and mechanics requires independently calibrated force measurements.", ""]
    (output/"window_boundary_report.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    exported = {p.name:file_hash(p) for p in output.glob("window_boundary_*.csv")}
    exported.update({p.name:file_hash(p) for p in output.glob("bounded_*.csv")})
    write_json(output/"window_boundary_provenance.json", {"stage":"development", "processing_boundary":PROCESSING_BOUNDARY,
               "windows_audited":len(windows), "zero_outside_processed_change":bool((windows.outside_perturbation_max_processed_change == 0).all()),
               "runs":runs, "exported_table_hashes":exported, "script_hash":file_hash(__file__)})
    print(f"Saved boundary correction report; {len(windows)} real windows invariant to outside acceleration", flush=True)


if __name__ == "__main__":
    main()
