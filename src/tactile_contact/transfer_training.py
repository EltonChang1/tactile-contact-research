"""Training-only transfer coverage and forward-support common eligibility."""
import json
from pathlib import Path

import pandas as pd

from .audit import load_record
from .config import PROTOCOLS, file_hash, load_config
from .coverage_review import canonical_availability
from .study_design import query_domains, validate_development_access


def preflight(spec):
    groups, reservation = [pd.read_csv(spec[k]) for k in ["group_manifest", "reservation_manifest"]]
    exposure = json.loads(Path(spec["exposure_snapshot"]).read_text())
    validate_development_access(spec["surface_ids"], groups, reservation,
        exposure["training_surface_ids"]+exposure["selection_surface_ids"])
    if spec["surface_ids"] != exposure["training_surface_ids"]:
        raise ValueError("Only the exact exposed training cohort may enter this audit")
    cfg = load_config(spec["source_config"])
    convention = json.loads(Path(spec["clock_convention"]).read_text())
    if any(cfg[k] != convention[k] for k in ["time_base", "sampling_rate_hz"]) or convention["physical_acquisition_clock_verified"]:
        raise ValueError("Retain declared logged coordinates")
    domains = pd.read_csv(spec["domain_table"])
    pd.testing.assert_frame_equal(domains.fillna(""), query_domains().fillna(""), check_dtype=False)
    selected = domains[domains.omitted_transfer]
    if len(selected) != 26 or spec["expected_recording_triplets"] != len(selected)*len(spec["surface_ids"])*2:
        raise ValueError("Training transfer denominator/domain changed")
    if spec["repeats"] != [0, 1] or spec["durations_logged_s"] != [.25, .5, 1.] or spec["query_duration_logged_s"] != .5:
        raise ValueError("Training repeats/budgets changed")
    return cfg, domains, selected


def known_current_records():
    provenance = json.loads(Path("docs/wider_contact_qc_provenance.json").read_text())
    for entry in provenance["outputs"]:
        if file_hash(entry["path"]) != entry["sha256"]:
            raise ValueError("Known training QC output changed")
    for path, sha in provenance["source_hashes"].items():
        if file_hash(path) != sha:
            raise ValueError("Known training QC source changed")
    for entry in provenance["raw_hashes"]:
        if file_hash(entry["path"]) != entry["sha256"]:
            raise ValueError("Known training raw file changed")
    records = pd.read_csv("docs/wider_contact_qc_records.csv", float_precision="round_trip")
    rows = []
    for row in records.itertuples():
        _, times, _ = load_record(Path("data/raw/cluster"), row.recording_id)
        end = row.start_s+row.usable_duration_s
        start, availability = canonical_availability(times["accel"], row.start_s, end, 6000)
        rows.append(dict(surface_id=row.surface_id, speed_mm_s=row.speed_mm_s, direction_deg=row.direction_deg,
            nominal_force_N=row.nominal_force_N, repeat_id=row.repeat_id, recording_id=row.recording_id,
            valid=row.qc_status == "valid", steady_start_s=row.start_s, steady_end_s=end, canonical_start_s=start,
            **{f"available_{d:g}": v and row.qc_status == "valid" for d, v in availability.items()}))
    return pd.DataFrame(rows)


def training_eligibility(records, domains, surface_ids, durations=(.25, .5, 1.)):
    keys = ["surface_id", "speed_mm_s", "direction_deg", "nominal_force_N", "repeat_id"]
    if records.duplicated(keys).any():
        raise ValueError("Duplicate training coverage identity")
    lookup = records.set_index(keys)
    supports = sorted({tuple(c) for protocol in PROTOCOLS.values() for c in protocol})
    rows = []
    for surface in surface_ids:
        for duration in durations:
            missing_supports = [str(c) for c in supports if (surface, *c) not in lookup.index or
                not lookup.loc[(surface, *c), f"available_{duration:g}"]]
            for query in domains[domains.matched_familiar_fit_query].itertuples():
                missing_queries = [str(repeat) for repeat in [0, 1] if
                    (surface, query.speed_mm_s, query.direction_deg, query.nominal_force_N, repeat) not in lookup.index or
                    not lookup.loc[(surface, query.speed_mm_s, query.direction_deg, query.nominal_force_N, repeat), "available_0.5"]]
                rows.append(dict(surface_id=surface, speed_mm_s=query.speed_mm_s, direction_deg=query.direction_deg,
                    nominal_force_N=query.nominal_force_N, support_duration_logged_s=duration,
                    known_speed_query=query.known_speed_query, transfer_query=query.omitted_transfer,
                    all_protocols_forward_support_available=not missing_supports, both_query_repeats_available=not missing_queries,
                    common_candidate=not (missing_supports or missing_queries), missing_supports="|".join(missing_supports),
                    missing_query_repeats="|".join(missing_queries)))
    return pd.DataFrame(rows)
