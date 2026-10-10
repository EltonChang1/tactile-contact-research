"""Verify prospective coverage, immutable history and staged public hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from tactile_contact.config import file_hash
from tactile_contact.coverage_review import canonical_availability, common_eligibility, expected_paths, preflight


def read(path):
    return json.loads(Path(path).read_text())


def run(staged=False):
    spec = read("configs/selection_transfer_qc_review.json")
    cfg, domains, selected = preflight(spec)
    prefix = f"docs/{spec['output_prefix']}"
    provenance = read(prefix+"_provenance.json")
    for section in ["public_input_hashes", "source_hashes", "shared_input_hashes"]:
        for path, sha in provenance[section].items():
            assert file_hash(path) == sha, path
    for entry in provenance["outputs"]:
        assert file_hash(entry["path"]) == entry["sha256"], entry["path"]
    for key in ["seal", "local_inventory"]:
        assert file_hash(provenance[key]["path"]) == provenance[key]["sha256"]
    conditions = list(selected[["speed_mm_s", "direction_deg", "nominal_force_N"]].itertuples(index=False, name=None))
    assert set(r["path"] for r in provenance["raw_hashes"]) == set(expected_paths(spec["surface_ids"], conditions))
    raw = Path(provenance["raw_root"])
    for entry in provenance["raw_hashes"]:
        assert file_hash(raw/entry["path"]) == entry["sha256"], entry["path"]
    for path, sha in provenance["shared_input_hashes"].items():
        snapshot = Path(spec["output_root"])/"shared_snapshot"/Path(path).name
        assert file_hash(snapshot) == sha, snapshot
    assert provenance["accessed_surface_ids"] == spec["surface_ids"] == [10, 57]
    assert not any(provenance[k] for k in ["reserved_signals_accessed", "prediction_scores_accessed", "settings_changed"])
    records = pd.read_csv(prefix+"_records.csv", float_precision="round_trip")
    sensitivity = pd.read_csv(prefix+"_sensitivity_records.csv", float_precision="round_trip")
    assert len(records) == 296 and len(sensitivity) == 2072
    keys = ["surface_id", "speed_mm_s", "direction_deg", "nominal_force_N", "repeat_id"]
    assert not records.duplicated(keys).any() and not sensitivity.duplicated(keys+["variant"]).any()
    assert records.groupby("surface_id").size().eq(148).all()
    for _, part in sensitivity.groupby("variant"):
        assert set(part.recording_id) == set(records.recording_id)
    for row in records[records.valid].itertuples():
        modality_first = []
        for channel in ["accel", "force", "position"]:
            path = raw/f"sensor_data/{channel}/{row.surface_id}/{row.recording_id}.parquet"
            times = pd.read_parquet(path, columns=["time_ns"]).time_ns
            modality_first.append(int(times.iloc[0]))
        accel_origin = (modality_first[0]-min(modality_first))/1e9
        start, _ = canonical_availability([accel_origin], row.steady_start_s, row.steady_end_s, cfg["sampling_rate_hz"])
        assert start == row.canonical_start_s
    for duration in spec["durations_logged_s"]:
        expected = sensitivity.valid & (sensitivity.canonical_start_s+duration <= sensitivity.steady_end_s)
        assert expected.equals(sensitivity[f"available_{duration:g}"])
    common = pd.read_csv(prefix+"_common_eligibility.csv", float_precision="round_trip").fillna("")
    expected = common_eligibility(records, domains, spec["surface_ids"]).fillna("")
    pd.testing.assert_frame_equal(common, expected)
    assert len(common) == 420
    summary = read(prefix+"_summary.json")
    assert summary["current_valid"] == int(records.valid.sum())
    assert summary["half_second_available"] == int(records["available_0.5"].sum())
    assert summary["one_second_available"] == int(records.available_1.sum())
    assert summary["all_matched_cells_eligible"] == bool(common.common_candidate.all())
    prepared = read("configs/matched_development_review.json")
    policy = read(prepared["training_policy"])
    assert prepared["train_ids"] == cfg["train_ids"]
    assert prepared["selection_and_score_ids"] == spec["surface_ids"]
    for key in ["patience", "seeds", "optimizer", "learning_rate", "batch_size", "episodes_per_surface", "latent_dim", "gradient_norm_clip"]:
        assert prepared["training"][key] == policy[key], key
    assert prepared["training"]["epochs"] == policy["epoch_cap"] == 120
    for domain, mask in [("familiar_fit", "matched_familiar_fit_query"), ("omitted_fit", "known_speed_query"),
                         ("shared_selection", "known_speed_query"), ("shared_scoring", "omitted_transfer")]:
        assert prepared["conditions"][domain+"_mask"] == mask
        assert prepared["conditions"][domain+"_query_triples"] == int(domains[mask].sum())
    assert prepared["coverage"]["remaining_transfer_training_triplets"] == 26*2*len(cfg["train_ids"]) == 520
    assert prepared["prospective_episode_counts_before_qc"] == dict(familiar_train=21000, omitted_train=13200,
        shared_known_speed_selection_per_experiment=1320, shared_transfer_scoring_per_orientation_per_experiment=780)
    if staged:
        mapping = {**provenance["public_input_hashes"], **provenance["source_hashes"],
            **{entry["path"]: entry["sha256"] for entry in provenance["outputs"]}}
        for path, sha in mapping.items():
            content = subprocess.run(["git", "show", f":{path.replace(chr(92), '/')}"], capture_output=True, check=True).stdout
            assert hashlib.sha256(content).hexdigest() == sha, path
    print("Validated 296 complete record identities, 2072 sensitivity rows, exact grid starts, 420 matched eligibility cells, pinned raw hashes and preserved shared history."+ (" Staged hashes match." if staged else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true")
    run(parser.parse_args().staged)
