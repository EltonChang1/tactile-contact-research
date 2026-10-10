"""Download/audit known-speed training coverage with mandatory reservation preflight."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tactile_contact.audit import CHANNELS, load_record, steady_interval
from tactile_contact.config import digest, file_hash, load_config, validate_source, write_json
from tactile_contact.download import download_cluster
from tactile_contact.qc_review import support_diagnostics, fit_heading_frame, wrap_degrees
from tactile_contact.records import parse_record_name
from tactile_contact.study_design import validate_development_access


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=Path("configs/wider_qc_review.json"))
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    spec = json.loads(args.review.read_text())
    groups, reservation = [pd.read_csv(spec[key]) for key in ["group_manifest", "reservation_manifest"]]
    exposure = json.loads(Path(spec["exposure_snapshot"]).read_text())
    exposed = exposure["training_surface_ids"]+exposure["selection_surface_ids"]
    validate_development_access(spec["surface_ids"], groups, reservation, exposed)
    if not set(spec["surface_ids"]).issubset(exposure["training_surface_ids"]) or spec["allowed_speeds_mm_s"] != [20, 40, 60]:
        raise ValueError("Wider review requires only existing training specimens and known speeds")
    cfg = load_config(spec["source_config"])
    convention = json.loads(Path(spec["clock_convention"]).read_text())
    if any(cfg[key] != convention[key] for key in ["time_base", "sampling_rate_hz"]) or convention["physical_acquisition_clock_verified"]:
        raise ValueError("Wider QC expects declared uncalibrated logged coordinates")
    domains = pd.read_csv(spec["domain_table"])
    selected = domains[domains.support_condition | domains.known_speed_query]
    if len(selected) != 48 or set(selected.speed_mm_s) != {20, 40, 60}:
        raise ValueError("Invalid permitted-speed review domain")
    conditions = list(selected[["speed_mm_s", "direction_deg", "nominal_force_N"]].itertuples(index=False, name=None))
    expected = len(spec["surface_ids"])*len(conditions)*2
    if expected != spec["expected_recording_triplets"]:
        raise ValueError("Review denominator changed")
    variants = json.loads(Path(spec["variants_spec"]).read_text())["variants"]
    if args.download:
        # Use the bounded downloader only, with no validation records requested.
        download_cfg = dict(cfg, train_ids=spec["surface_ids"], val_ids=[], conditions=conditions, data_root=".")
        download_cluster(Path("."), download_cfg)
    validate_source(Path("."), cfg)
    raw = Path("data/raw/cluster")
    inventory = {r["path"]: r["sha256"] for r in json.loads(Path("data/raw_inventory.json").read_text())["files"]}
    sensitivities, details, raw_hashes = [], [], []
    for surface in spec["surface_ids"]:
        for speed, direction, force in conditions:
            for repeat in [0, 1]:
                record = f"{surface}_{direction}_{speed}_{int(force*1000)}_{repeat}"
                info = parse_record_name(record+".parquet")
                for channel in CHANNELS:
                    path = raw/f"sensor_data/{channel}/{surface}/{record}.parquet"
                    sha = file_hash(path)
                    if inventory[path.relative_to(raw).as_posix()] != sha:
                        raise ValueError(f"Raw hash mismatch: {path}")
                    raw_hashes.append(dict(path=path.as_posix(), sha256=sha))
                frames, times, _ = load_record(raw, record)
                for variant in variants:
                    rules = dict(cfg["qc"], **variant["overrides"])
                    row = dict(info, variant=variant["name"], valid=False, duration_s=0., half_second_available=False,
                        one_second_available=False, exclusion_reason="")
                    try:
                        start, end, _ = steady_interval(frames, times, speed, rules)
                        row.update(valid=True, start_s=start, end_s=end, duration_s=end-start,
                            half_second_available=end-start >= .5, one_second_available=end-start >= 1.)
                    except ValueError as exc:
                        row["exclusion_reason"] = str(exc)
                    sensitivities.append(row)
                    if variant["name"] == "current":
                        diagnostic = dict(info, qc_status="valid" if row["valid"] else "excluded", qc_reason=row["exclusion_reason"],
                            usable_duration_s=row["duration_s"], half_second_available=row["half_second_available"],
                            one_second_available=row["one_second_available"])
                        for channel, t in times.items():
                            dt = np.diff(t)
                            diagnostic.update({f"{channel}_mean_logged_rate_hz": 1/dt.mean(), f"{channel}_max_gap_s": dt.max(),
                                               f"{channel}_interval_cv": dt.std()/dt.mean()})
                        if row["half_second_available"]:
                            diagnostic.update(start_s=start, diagnostic_duration_logged_s=spec["diagnostic_duration_logged_s"],
                                **support_diagnostics(frames, times, start, spec["diagnostic_duration_logged_s"], rules["motion_smoothing_samples"]))
                            diagnostic["force_mean_to_nominal_ratio"] = diagnostic["force_time_weighted_mean_N"]/force
                            diagnostic["travel_to_nominal_ratio"] = diagnostic["logged_position_travel_mm"]/(speed*spec["diagnostic_duration_logged_s"])
                        details.append(diagnostic)
        print("Wider review completed training specimen", surface, flush=True)
    detail, sensitivity = pd.DataFrame(details), pd.DataFrame(sensitivities)
    has_heading = detail.observed_heading_deg.notna()
    heading_frame, candidates = fit_heading_frame(detail.loc[has_heading, "observed_heading_deg"], detail.loc[has_heading, "direction_deg"])
    detail["heading_residual_deg"] = wrap_degrees(detail.observed_heading_deg-(heading_frame["offset_deg"]+heading_frame["sign"]*detail.direction_deg))
    detail["heading_absolute_residual_deg"] = detail.heading_residual_deg.abs()
    summary = sensitivity.groupby("variant", sort=False).agg(requested=("recording_id", "size"), valid=("valid", "sum"),
        half_second_available=("half_second_available", "sum"), one_second_available=("one_second_available", "sum")).reset_index()
    conditions_table = detail.groupby(["speed_mm_s", "direction_deg", "nominal_force_N"]).agg(requested=("recording_id", "size"),
        half_second_available=("half_second_available", "sum"), one_second_available=("one_second_available", "sum"),
        force_ratio_median=("force_mean_to_nominal_ratio", "median"), travel_ratio_median=("travel_to_nominal_ratio", "median"),
        heading_abs_max_deg=("heading_absolute_residual_deg", "max")).reset_index()
    surface_table = detail.groupby("surface_id").agg(requested=("recording_id", "size"), half_second_available=("half_second_available", "sum"),
        one_second_available=("one_second_available", "sum"), minimum_duration_s=("usable_duration_s", "min")).reset_index()
    prefix = spec["output_prefix"]
    outputs = []
    for name, table in [("records", detail), ("sensitivity_records", sensitivity), ("sensitivity", summary), ("conditions", conditions_table), ("surfaces", surface_table)]:
        path = Path(f"docs/{prefix}_{name}.csv")
        table.to_csv(path, index=False, lineterminator="\n")
        outputs.append(dict(path=path.as_posix(), sha256=file_hash(path)))
    write_json(f"docs/{prefix}_provenance.json", dict(review_id=spec["review_id"], requested_recordings=expected,
        accessed_surface_ids=spec["surface_ids"], accessed_speeds_mm_s=spec["allowed_speeds_mm_s"],
        source_config_hash=cfg["config_hash"], source_revision=cfg["revision"],
        review_hash=file_hash(args.review), selected_conditions_hash=digest(conditions),
        input_hashes={spec[key]: file_hash(spec[key]) for key in ["domain_table", "group_manifest", "reservation_manifest", "exposure_snapshot", "clock_convention", "variants_spec"]},
        source_hashes={"scripts/review_wider_coverage.py": file_hash(__file__), **{f"src/tactile_contact/{name}.py": file_hash(f"src/tactile_contact/{name}.py") for name in ["audit", "qc_review", "study_design", "download"]}},
        raw_hashes=raw_hashes, outputs=outputs, heading_frame=heading_frame, heading_frame_candidates=candidates,
        scope="960 requested known-speed training records; all requested records in denominators. No validation/reserved/omitted-speed records or predictor errors read. Geometry/loading only on current half-second intervals; retrospective QC, uncalibrated logged coordinates. No setting or model changed."))
    print(summary.to_string(index=False), flush=True)
    print("Heading frame:", heading_frame, flush=True)


if __name__ == "__main__":
    main()
