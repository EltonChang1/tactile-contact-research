"""Acquire and audit matched transfer-speed training coverage, without fitting."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tactile_contact.audit import CHANNELS, load_record, steady_interval
from tactile_contact.config import digest, file_hash, validate_source
from tactile_contact.convergence import json_lf
from tactile_contact.coverage_review import canonical_availability, expected_paths, stage_cached_raw
from tactile_contact.transfer_training import preflight, known_current_records, training_eligibility
from tactile_contact.download import download_cluster
from tactile_contact.qc_review import fit_heading_frame, support_diagnostics, wrap_degrees
from tactile_contact.records import parse_record_name


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run(review_path, download=False):
    spec = read(review_path)
    cfg, domains, selected = preflight(spec)
    conditions = list(selected[["speed_mm_s", "direction_deg", "nominal_force_N"]].itertuples(index=False, name=None))
    output = Path(spec["output_root"])
    shared_paths = [Path("data/raw_inventory.json"), Path("data/source.json")]
    shared_hashes = {p.as_posix(): file_hash(p) for p in shared_paths}
    seal = output/"review_seal.json"
    if output.exists():
        if (output/"audit_complete.json").exists() or not seal.exists() or read(seal)["review_hash"] != file_hash(review_path):
            raise ValueError("Preserve completed evidence; use a fresh matching output root")
    else:
        output.mkdir(parents=True)
        for path in shared_paths:
            target = output/"shared_snapshot"/path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
        json_lf(seal, dict(review_hash=file_hash(review_path), review=spec, shared_input_hashes=shared_hashes,
            source_hashes={p.as_posix(): file_hash(p) for p in [Path(__file__).relative_to(Path.cwd()),
                *[Path(f"src/tactile_contact/{n}.py") for n in ["coverage_review", "transfer_training", "audit", "qc_review", "download", "study_design", "config", "records"]]]},
            condition_hash=digest(conditions), requested_recording_triplets=spec["expected_recording_triplets"]))
    sealed = read(seal)
    for path, sha in sealed["source_hashes"].items():
        if file_hash(path) != sha:
            raise ValueError("Audit source changed after acquisition seal")
    for path, sha in sealed["shared_input_hashes"].items():
        if file_hash(path) != sha:
            raise ValueError("Shared historical inventory/source changed")
    copied = stage_cached_raw(output, cfg, spec["surface_ids"], conditions)
    if download:
        download_cfg = dict(cfg, experiment="familiar_conditions", train_ids=spec["surface_ids"], val_ids=[], conditions=conditions, data_root=output.as_posix())
        download_cluster(output, download_cfg)
    raw = output/"data/raw/cluster"
    validate_source(output, dict(cfg, data_root=output.as_posix()))
    inventory_path = output/"data/raw_inventory.json"
    inventory = read(inventory_path)
    paths = expected_paths(spec["surface_ids"], conditions)
    registered = {r["path"]: r for r in inventory["files"]}
    if set(registered) != set(paths):
        raise ValueError("Incomplete/unexpected raw selection; rerun unchanged config with --download")
    for relative in paths:
        if file_hash(raw/relative) != registered[relative]["sha256"]:
            raise ValueError(f"Pinned raw hash mismatch: {relative}")
    variants = read(spec["variants_spec"])["variants"]
    details, sensitivities = [], []
    for surface in spec["surface_ids"]:
        for number, (speed, direction, force) in enumerate(conditions):
            for repeat in [0, 1]:
                record = f"{surface}_{direction}_{speed}_{round(force*1000)}_{repeat}"
                info = parse_record_name(record+".parquet")
                frames, times, error = None, None, ""
                try:
                    frames, times, _ = load_record(raw, record)
                except ValueError as exc:
                    error = str(exc)
                for variant in variants:
                    row = dict(info, variant=variant["name"], valid=False, usable_duration_logged_s=0.,
                        canonical_start_s=np.nan, steady_end_s=np.nan, exclusion_reason=error,
                        **{f"available_{d:g}": False for d in spec["durations_logged_s"]})
                    rules = dict(cfg["qc"], **variant["overrides"])
                    if not error:
                        try:
                            start, end, _ = steady_interval(frames, times, speed, rules)
                            canonical, available = canonical_availability(times["accel"], start, end, cfg["sampling_rate_hz"])
                            row.update(valid=True, steady_start_s=start, canonical_start_s=canonical, steady_end_s=end,
                                usable_duration_logged_s=end-start, canonical_shift_s=canonical-start,
                                **{f"available_{d:g}": v for d, v in available.items()})
                        except ValueError as exc:
                            row["exclusion_reason"] = str(exc)
                    sensitivities.append(row)
                    if variant["name"] == "current":
                        detail = dict(row, condition_role="support" if (speed, direction, force) in
                            set(selected[selected.support_condition][["speed_mm_s", "direction_deg", "nominal_force_N"]].itertuples(index=False, name=None))
                            else "selection" if speed in [20, 40, 60] else "transfer")
                        if frames is not None:
                            for channel, t in times.items():
                                dt = np.diff(t)
                                detail.update({f"{channel}_mean_logged_rate_hz": 1/dt.mean(), f"{channel}_max_gap_s": dt.max(),
                                    f"{channel}_interval_cv": dt.std()/dt.mean()})
                            detail["accel_fraction_at_16g"] = float((frames["accel"][["X", "Y", "Z"]].abs() >= 16).to_numpy().mean())
                        if row["available_0.5"]:
                            diagnostic = support_diagnostics(frames, times, row["canonical_start_s"], .5, rules["motion_smoothing_samples"])
                            detail.update(diagnostic, force_mean_to_nominal_ratio=diagnostic["force_time_weighted_mean_N"]/force,
                                travel_to_nominal_ratio=diagnostic["logged_position_travel_mm"]/(speed*.5))
                        details.append(detail)
            if (number+1) % 10 == 0:
                print(f"Audited specimen {surface}: {number+1}/{len(conditions)} conditions", flush=True)
        print(f"Completed coverage specimen {surface}", flush=True)
    records, sensitivity = pd.DataFrame(details), pd.DataFrame(sensitivities)
    if len(records) != spec["expected_recording_triplets"] or len(sensitivity) != len(records)*len(variants):
        raise ValueError("Every requested record and setting must stay in the denominator")
    eligible_heading = records.observed_heading_deg.notna()
    frame, candidates = fit_heading_frame(records.loc[eligible_heading, "observed_heading_deg"], records.loc[eligible_heading, "direction_deg"])
    records["heading_absolute_residual_deg"] = abs(wrap_degrees(records.observed_heading_deg-(frame["offset_deg"]+frame["sign"]*records.direction_deg)))
    known = known_current_records()
    common = training_eligibility(pd.concat([known, records], ignore_index=True), domains, spec["surface_ids"])
    variant_summary = sensitivity.groupby("variant", sort=False).agg(requested=("recording_id", "size"), valid=("valid", "sum"),
        quarter_second=("available_0.25", "sum"), half_second=("available_0.5", "sum"), one_second=("available_1", "sum")).reset_index()
    intersections = []
    for duration, part in common.groupby("support_duration_logged_s"):
        for domain, selected_rows in [("selection", part[part.known_speed_query]), ("transfer", part[part.transfer_query])]:
            global_counts = selected_rows.groupby(["speed_mm_s", "direction_deg", "nominal_force_N"]).common_candidate.all()
            intersections.append(dict(support_duration_logged_s=duration, query_domain=domain,
                requested_conditions=len(global_counts), conditions_all_specimens=int(global_counts.sum()),
                requested_specimen_query_cells=len(selected_rows), eligible_specimen_query_cells=int(selected_rows.common_candidate.sum())))
    by_condition = records.groupby(["condition_role", "speed_mm_s", "direction_deg", "nominal_force_N"], as_index=False).agg(
        requested=("recording_id", "size"), half_second=("available_0.5", "sum"), one_second=("available_1", "sum"),
        force_ratio_median=("force_mean_to_nominal_ratio", "median"), travel_ratio_median=("travel_to_nominal_ratio", "median"),
        heading_absolute_max_deg=("heading_absolute_residual_deg", "max"))
    by_surface = records.groupby(["surface_id", "condition_role"], as_index=False).agg(requested=("recording_id", "size"),
        half_second=("available_0.5", "sum"), one_second=("available_1", "sum"), minimum_duration_logged_s=("usable_duration_logged_s", "min"))
    outputs = []
    for name, table in [("records", records), ("known_canonical", known), ("sensitivity_records", sensitivity), ("sensitivity", variant_summary),
                        ("common_eligibility", common), ("intersections", pd.DataFrame(intersections)),
                        ("conditions", by_condition), ("surfaces", by_surface)]:
        path = Path(f"docs/{spec['output_prefix']}_{name}.csv")
        table.to_csv(path, index=False, lineterminator="\n")
        outputs.append(dict(path=path.as_posix(), sha256=file_hash(path)))
    summary = dict(requested_recording_triplets=len(records), current_valid=int(records.valid.sum()),
        half_second_available=int(records["available_0.5"].sum()), one_second_available=int(records.available_1.sum()),
        median_force_to_nominal=float(records.force_mean_to_nominal_ratio.median()),
        force_ratio_p05=float(records.force_mean_to_nominal_ratio.quantile(.05)), force_ratio_p95=float(records.force_mean_to_nominal_ratio.quantile(.95)),
        median_travel_to_nominal=float(records.travel_to_nominal_ratio.median()),
        heading_absolute_max_deg=float(records.heading_absolute_residual_deg.max()),
        maximum_canonical_shift_s=float(records.canonical_shift_s.max()),
        all_matched_cells_eligible=bool(common.common_candidate.all()), intersections=intersections)
    summary_path = Path(f"docs/{spec['output_prefix']}_summary.json")
    json_lf(summary_path, summary)
    outputs.append(dict(path=summary_path.as_posix(), sha256=file_hash(summary_path)))
    for path, sha in sealed["shared_input_hashes"].items():
        if file_hash(path) != sha:
            raise ValueError("Shared historical input was modified during review")
    public = {review_path.as_posix(): file_hash(review_path), **{spec[k]: file_hash(spec[k]) for k in
        ["source_config", "domain_table", "group_manifest", "reservation_manifest", "exposure_snapshot", "clock_convention", "variants_spec", "known_training_records", "known_training_provenance"]}}
    json_lf(f"docs/{spec['output_prefix']}_provenance.json", dict(review_id=spec["review_id"], review_date=spec["review_date"],
        public_input_hashes=public, source_hashes=sealed["source_hashes"], shared_input_hashes=sealed["shared_input_hashes"],
        seal=dict(path=seal.as_posix(), sha256=file_hash(seal)), local_inventory=dict(path=inventory_path.as_posix(), sha256=file_hash(inventory_path)),
        raw_root=raw.as_posix(), raw_hashes=inventory["files"], outputs=outputs, accessed_surface_ids=spec["surface_ids"],
        requested_recording_triplets=len(records), variant_rows=len(sensitivity), heading_frame=frame, heading_frame_candidates=candidates,
        reserved_signals_accessed=False, prediction_scores_accessed=False, settings_changed=False,
        scope=spec["scope"], claim_limit="Development coverage only; no calibrated acquisition timing, predictor result, scientific test or manufacturing-family independence."))
    json_lf(output/"audit_complete.json", dict(review_id=spec["review_id"], outputs=outputs, all_matched_cells_eligible=summary["all_matched_cells_eligible"]))
    print(variant_summary.to_string(index=False), flush=True)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=Path("configs/transfer_training_qc_review.json"))
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    run(args.review, args.download)
