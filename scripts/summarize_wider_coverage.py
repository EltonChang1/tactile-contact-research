"""Summarize the completed wider QC and prospective common known-speed pool."""
import json
from pathlib import Path

import pandas as pd

from tactile_contact.config import PROTOCOLS, file_hash, write_json


def common_known_eligibility(records, domains):
    keys = ["surface_id", "speed_mm_s", "direction_deg", "nominal_force_N", "repeat_id"]
    if records.duplicated(keys).any():
        raise ValueError("Duplicate recording keys in coverage")
    lookup = records.set_index(keys)
    supports = {tuple(item) for conditions in PROTOCOLS.values() for item in conditions}
    queries = domains[domains.known_speed_query]
    rows = []
    for surface in sorted(records.surface_id.unique()):
        missing_supports = []
        for speed, direction, force, repeat in sorted(supports):
            key = (surface, speed, direction, force, repeat)
            if key not in lookup.index or not lookup.loc[key, "one_second_available"]:
                missing_supports.append(f"{direction}:{speed}:{force:g}:{repeat}")
        for query in queries.itertuples():
            missing_queries = []
            for repeat in [0, 1]:
                key = (surface, query.speed_mm_s, query.direction_deg, query.nominal_force_N, repeat)
                if key not in lookup.index or not lookup.loc[key, "half_second_available"]:
                    missing_queries.append(str(repeat))
            rows.append(dict(surface_id=int(surface), speed_mm_s=query.speed_mm_s, direction_deg=query.direction_deg,
                nominal_force_N=query.nominal_force_N, all_protocol_supports_one_second=not missing_supports,
                both_query_repeats_half_second=not missing_queries, common_candidate=not (missing_supports or missing_queries),
                missing_supports="|".join(missing_supports), missing_query_repeats="|".join(missing_queries)))
    return pd.DataFrame(rows)


def main():
    prefix = "docs/wider_contact_qc"
    records = pd.read_csv(prefix+"_records.csv")
    variants = pd.read_csv(prefix+"_sensitivity.csv")
    provenance_path = Path(prefix+"_provenance.json")
    # Make the input's byte hash portable under the repository's LF policy.
    provenance_path.write_text(provenance_path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    provenance = json.loads(provenance_path.read_text())
    for entry in provenance["outputs"]:
        if file_hash(entry["path"]) != entry["sha256"]:
            raise ValueError("Wider QC output hash mismatch")
    domains = pd.read_csv("configs/query_domains.csv")
    common = common_known_eligibility(records, domains)
    common_path = Path(prefix+"_common_eligibility.csv")
    common.to_csv(common_path, index=False, lineterminator="\n")
    summary = dict(requested_records=len(records), current_valid=int((records.qc_status == "valid").sum()),
        half_second_records=int(records.half_second_available.sum()), one_second_records=int(records.one_second_available.sum()),
        half_second_diagnostic_records=int(records.observed_heading_deg.notna().sum()),
        support_eligible_surfaces=int(common[common.all_protocol_supports_one_second].surface_id.nunique()),
        common_candidate_cells=int(common.common_candidate.sum()), requested_known_query_cells=len(common),
        common_query_conditions_all_surfaces=int(common.groupby(["speed_mm_s", "direction_deg", "nominal_force_N"]).common_candidate.all().sum()),
        median_force_to_nominal=float(records.force_mean_to_nominal_ratio.median()),
        force_ratio_p05=float(records.force_mean_to_nominal_ratio.quantile(.05)), force_ratio_p95=float(records.force_mean_to_nominal_ratio.quantile(.95)),
        median_travel_to_nominal=float(records.travel_to_nominal_ratio.median()),
        heading_absolute_p95_deg=float(records.heading_absolute_residual_deg.quantile(.95)),
        heading_absolute_max_deg=float(records.heading_absolute_residual_deg.max()), variants=variants.to_dict("records"))
    write_json(prefix+"_summary.json", summary)
    summary_path = Path(prefix+"_summary.json")
    summary_path.write_text(summary_path.read_text(), encoding="utf-8", newline="\n")
    write_json(prefix+"_summary_provenance.json", dict(script_sha256=file_hash(__file__),
        input_hashes={path: file_hash(path) for path in [prefix+"_records.csv", prefix+"_sensitivity.csv", provenance_path.as_posix(), "configs/query_domains.csv", "src/tactile_contact/config.py"]},
        output_hashes={path.as_posix(): file_hash(path) for path in [common_path, summary_path]},
        scope="Prospective known-speed training eligibility only. Five protocol-prescribed support recordings must all retain 1 logged second; both query repeats need 0.5. This does not freeze a scientific cohort, cover validation/test/omitted grids, or score predictions."))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
