"""Prospective matched validation coverage, independent of predictor errors."""
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from .config import PROTOCOLS, file_hash, load_config, validate_source
from .convergence import json_lf
from .study_design import query_domains, validate_development_access


def preflight(spec):
    groups, reservation = [pd.read_csv(spec[k]) for k in ["group_manifest", "reservation_manifest"]]
    exposure = json.loads(Path(spec["exposure_snapshot"]).read_text())
    validate_development_access(spec["surface_ids"], groups, reservation,
        exposure["training_surface_ids"]+exposure["selection_surface_ids"])
    if sorted(spec["surface_ids"]) != sorted(exposure["selection_surface_ids"]):
        raise ValueError("Review must retain exactly the existing development selection cohort")
    cfg = load_config(spec["source_config"])
    convention = json.loads(Path(spec["clock_convention"]).read_text())
    if any(cfg[k] != convention[k] for k in ["time_base", "sampling_rate_hz"]) or convention["physical_acquisition_clock_verified"]:
        raise ValueError("Retain the declared uncalibrated logged-coordinate convention")
    domains = pd.read_csv(spec["domain_table"])
    pd.testing.assert_frame_equal(domains.fillna(""), query_domains().fillna(""), check_dtype=False)
    selected = domains[domains.support_condition | domains.known_speed_query | domains.omitted_transfer]
    if len(selected) != 74 or int(domains.known_speed_query.sum()) != 44 or int(domains.omitted_transfer.sum()) != 26:
        raise ValueError("Matched condition masks changed")
    if spec["repeats"] != [0, 1] or spec["durations_logged_s"] != [.25, .5, 1.] or spec["query_duration_logged_s"] != .5:
        raise ValueError("Retain both repetitions and the declared contact budgets")
    if len(selected)*len(spec["surface_ids"])*2 != spec["expected_recording_triplets"]:
        raise ValueError("Requested recording denominator changed")
    return cfg, domains, selected


def expected_paths(surface_ids, conditions):
    paths = ["README.md", "texture_list.xlsx"]
    for surface in surface_ids:
        for speed, direction, force in conditions:
            for repeat in [0, 1]:
                record = f"{surface}_{direction}_{speed}_{round(force*1000)}_{repeat}"
                paths.extend(f"sensor_data/{channel}/{surface}/{record}.parquet" for channel in ["accel", "force", "position"])
    return sorted(set(paths))


def stage_cached_raw(output, cfg, surface_ids, conditions, shared=Path(".")):
    """Copy only approved cached files; preserve the shared inventory/source bytes."""
    output, shared = Path(output), Path(shared)
    source = validate_source(shared, cfg)
    inventory_path = shared/"data/raw_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    if inventory["revision"] != cfg["revision"]:
        raise ValueError("Shared raw inventory revision mismatch")
    previous = {row["path"]: row for row in inventory["files"]}
    local_inventory_path = output/"data/raw_inventory.json"
    local = {}
    if local_inventory_path.exists():
        local_inventory = json.loads(local_inventory_path.read_text())
        if local_inventory["revision"] != cfg["revision"]:
            raise ValueError("Local raw inventory revision mismatch")
        local = {row["path"]: row for row in local_inventory["files"]}
    cached_triplets = 0
    for relative in expected_paths(surface_ids, conditions):
        path = output/"data/raw/cluster"/relative
        if relative in local:
            if file_hash(path) != local[relative]["sha256"]:
                raise ValueError("Local pinned cache changed")
            continue
        if relative not in previous:
            continue
        original = shared/"data/raw/cluster"/relative
        if file_hash(original) != previous[relative]["sha256"]:
            raise ValueError("Shared pinned cache changed")
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, path)
        local[relative] = previous[relative]
        cached_triplets += int(relative.startswith("sensor_data/accel/"))
    json_lf(local_inventory_path, dict(revision=cfg["revision"], files=[local[k] for k in sorted(local)]))
    json_lf(output/"data/source.json", dict(source, selected_surface_ids=surface_ids))
    return cached_triplets


def canonical_availability(accel_times, steady_start, steady_end, fs, durations=(.25, .5, 1.)):
    """Use the exact preparation grid start, not only the steady interval length."""
    origin = float(accel_times[0])
    index = max(0, int(np.ceil((steady_start-origin)*fs)))
    start = origin+index/fs
    if start < steady_start:
        index += 1; start = origin+index/fs
    return start, {duration: start+duration <= steady_end for duration in durations}


def common_eligibility(records, domains, surface_ids, durations=(.25, .5, 1.)):
    keys = ["surface_id", "speed_mm_s", "direction_deg", "nominal_force_N", "repeat_id"]
    if records.duplicated(keys).any():
        raise ValueError("Duplicate recording identities in coverage")
    lookup = records.set_index(keys)
    # Union over all protocols AND both prediction orientations: eight supports.
    support_conditions = {tuple(c[:3]) for protocol in PROTOCOLS.values() for c in protocol}
    supports = sorted((*condition, repeat) for condition in support_conditions for repeat in [0, 1])
    queries = domains[domains.known_speed_query | domains.omitted_transfer]
    rows = []
    for surface in surface_ids:
        for duration in durations:
            field = f"available_{duration:g}"
            missing_supports = []
            for support in supports:
                key = (surface, *support)
                if key not in lookup.index or not lookup.loc[key, field]:
                    missing_supports.append(":".join(map(str, support)))
            for query in queries.itertuples():
                missing_queries = []
                for repeat in [0, 1]:
                    key = (surface, query.speed_mm_s, query.direction_deg, query.nominal_force_N, repeat)
                    if key not in lookup.index or not lookup.loc[key, "available_0.5"]:
                        missing_queries.append(str(repeat))
                rows.append(dict(surface_id=surface, speed_mm_s=query.speed_mm_s, direction_deg=query.direction_deg,
                    nominal_force_N=query.nominal_force_N, support_duration_logged_s=duration,
                    known_speed_query=query.known_speed_query, transfer_query=query.omitted_transfer,
                    all_protocols_both_orientations_support_available=not missing_supports,
                    both_query_repeats_available=not missing_queries,
                    common_candidate=not (missing_supports or missing_queries),
                    missing_supports="|".join(missing_supports), missing_query_repeats="|".join(missing_queries)))
    return pd.DataFrame(rows)
