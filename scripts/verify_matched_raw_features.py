"""Reconstruct frozen matched features from raw recordings without refitting.

Run from the repository root. Verification is read-only unless --write-report
is explicitly provided. Existing reports with different contents are preserved.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from tactile_contact.audit import load_record
from tactile_contact.config import file_hash, load_config
from tactile_contact.signal import spectral_features
from tactile_contact.study_design import validate_development_access
from tactile_contact.windows import prepare_acceleration_window


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify(provenance_path):
    proof = read(provenance_path)
    output = Path(proof["output_root"])
    execution = read(proof["execution_seal"]["path"])
    spec, design = execution["review"], execution["design"]
    require(design["stage"] == "development_only", "Only frozen development evidence may be verified")
    windows_path = output/"windows.csv"
    windows = pd.read_csv(windows_path, float_precision="round_trip")
    groups = pd.read_csv(design["group_manifest"])
    reservation = pd.read_csv(design["reservation_manifest"])
    exposure = read(design["exposure_snapshot"])
    exposed = exposure["training_surface_ids"]+exposure["selection_surface_ids"]
    require(design["train_ids"] == exposure["training_surface_ids"] and
        design["selection_and_score_ids"] == exposure["selection_surface_ids"], "Exposed cohorts changed")
    expected_cohort = set(design["train_ids"]+design["selection_and_score_ids"])
    require(len(windows) == 1878 and set(windows.surface_id) == expected_cohort, "Matched window denominator/cohort changed")
    validate_development_access(windows.surface_id.unique().tolist(), groups, reservation, exposed)
    # Preflight every raw path before hashing or reading sensor bytes.
    raw_paths = {p: sha for p, sha in proof["input_hashes"].items() if p.endswith(".parquet")}
    raw_cohort = {int(Path(p).stem.split("_")[0]) for p in raw_paths}
    require(raw_cohort == expected_cohort, "Pinned raw cohort differs from the exposed matched cohort")
    validate_development_access(sorted(raw_cohort), groups, reservation, exposed)
    require(len(raw_paths) == 5328, "Pinned matched raw-file denominator changed")
    for section in ["input_hashes", "source_hashes"]:
        for path, expected in proof[section].items():
            require(file_hash(path) == expected, f"Frozen {section} file changed: {path}")
    for key in ["execution_seal", "selection_seal"]:
        require(file_hash(proof[key]["path"]) == proof[key]["sha256"], f"Frozen {key} changed")
    for entry in proof["outputs"]:
        require(file_hash(entry["path"]) == entry["sha256"], f"Frozen public output changed: {entry['path']}")
    require(read(spec["design"]) == design, "Current design differs from execution seal")
    runner_path = Path("scripts/run_matched_development.py")
    runner_spec = importlib.util.spec_from_file_location("frozen_matched_runner_for_verification", runner_path)
    runner = importlib.util.module_from_spec(runner_spec)
    runner_spec.loader.exec_module(runner)
    expected_windows = runner.window_manifest(design, pd.read_csv(design["domain_table"]),
        load_config("configs/omitted_speed.yaml"), output, spec)
    pd.testing.assert_frame_equal(windows, expected_windows, check_exact=True)
    audit_path = Path("docs/matched_review_windows.csv")
    audit = pd.read_csv(audit_path, float_precision="round_trip").set_index("window_id")
    require(windows.window_id.is_unique and audit.index.is_unique and set(windows.window_id) == set(audit.index),
        "Window/audit identities are ambiguous or different")
    started = time.monotonic()
    checked, recordings, array_checks = 0, 0, 0
    key_counts = {}
    maximum_discrepancy = 0.
    for (raw_root, recording_id), part in windows.groupby(["raw_root", "recording_id"], sort=True):
        frames, times, _ = load_record(raw_root, recording_id)
        for row in part.itertuples():
            feature_path = output/row.feature_path
            require(file_hash(feature_path) == audit.loc[row.window_id, "feature_sha256"],
                f"Cached feature changed: {row.window_id}")
            values, dependency = prepare_acceleration_window(frames["accel"], times["accel"],
                row.start_s, row.duration_s, 6000)
            altered = frames["accel"].copy()
            outside = (times["accel"] < row.start_s) | (times["accel"] >= row.end_s)
            altered.loc[outside, ["X", "Y", "Z"]] = 12345.
            changed, changed_dependency = prepare_acceleration_window(altered, times["accel"],
                row.start_s, row.duration_s, 6000)
            require(np.array_equal(values, changed) and dependency == changed_dependency,
                f"Outside-interval raw values influence window: {row.window_id}")
            regenerated = spectral_features(values, fs=6000, floor=1e-10)
            with np.load(feature_path) as saved:
                require(set(saved.files) == set(regenerated), f"Cached spectral fields differ: {row.window_id}")
                for key, value in regenerated.items():
                    current, previous = np.asarray(value), saved[key]
                    require(current.shape == previous.shape, f"Spectral shape differs: {row.window_id}/{key}")
                    discrepancy = float(np.max(np.abs(current-previous)))
                    maximum_discrepancy = max(maximum_discrepancy, discrepancy)
                    require(np.array_equal(current, previous), f"Spectral values differ: {row.window_id}/{key}")
                    array_checks += 1
                    key_counts[key] = key_counts.get(key, 0)+1
            for key, value in dependency.items():
                require(value == audit.loc[row.window_id, key], f"Raw dependency differs: {row.window_id}/{key}")
            checked += 1
        recordings += 1
        if recordings % 100 == 0:
            print(f"Verified raw features: {recordings} recordings / {checked} windows; "
                f"all arrays and boundaries exact; elapsed {time.monotonic()-started:.1f}s", flush=True)
    require(checked == 1878 and recordings == 1746 and array_checks == 15024, "Reconstruction denominator changed")
    # Confirm frozen inputs remained unchanged throughout the reconstruction.
    for section in ["input_hashes", "source_hashes"]:
        for path, expected in proof[section].items():
            require(file_hash(path) == expected, f"Frozen input/source changed during verification: {path}")
    return dict(schema_version=1, review_id="matched_raw_feature_validation_v1", success=True,
        matched_provenance=dict(path=provenance_path.as_posix(), sha256=file_hash(provenance_path)),
        verifier_source=dict(path=Path(__file__).resolve().relative_to(Path.cwd()).as_posix(), sha256=file_hash(__file__)),
        window_manifest=dict(path=windows_path.as_posix(), sha256=file_hash(windows_path), regenerated_exact=True),
        feature_audit=dict(path=audit_path.as_posix(), sha256=file_hash(audit_path)),
        windows=checked, recordings=recordings, feature_array_checks=array_checks, key_counts=key_counts,
        maximum_absolute_feature_discrepancy=maximum_discrepancy, dependency_records_exact=True,
        all_outside_interval_raw_value_perturbations_invariant=True,
        frozen_source_files_verified=len(proof["source_hashes"]), pinned_raw_files_verified=len(raw_paths),
        cohort_ids=sorted(int(x) for x in expected_cohort), reserved_signals_accessed=False,
        scope="Read-only reconstruction of frozen development features; no fitting, downloading, reserved signals or physical-clock calibration.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provenance", type=Path, default=Path("docs/matched_review_provenance.json"))
    parser.add_argument("--write-report", type=Path, help="Explicitly write a new deterministic report; preserve mismatched existing reports")
    args = parser.parse_args()
    report = verify(args.provenance)
    if args.write_report:
        if args.write_report.exists():
            require(read(args.write_report) == report, "Existing verification report differs; preserve it and choose a new report path")
            print(f"Existing report verified without overwrite: {args.write_report}", flush=True)
        else:
            args.write_report.parent.mkdir(parents=True, exist_ok=True)
            with args.write_report.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(report, indent=2, allow_nan=False)+"\n")
            print(f"Verification report: {args.write_report}", flush=True)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
