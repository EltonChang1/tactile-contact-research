"""Verify training coverage and the matched selection/scoring release."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from tactile_contact.config import file_hash
from tactile_contact.repetition_review import aggregate_scores
from tactile_contact.study_design import validate_development_access
from tactile_contact.transfer_training import training_eligibility


def read(path):
    return json.loads(Path(path).read_text())


def hashes(mapping):
    for path, sha in mapping.items():
        assert file_hash(path) == sha, path


def validate_coverage():
    spec = read("configs/transfer_training_qc_review.json")
    proof = read("docs/transfer_training_qc_provenance.json")
    for key in ["public_input_hashes", "source_hashes", "shared_input_hashes"]:
        hashes(proof[key])
    for entry in proof["outputs"]:
        hashes({entry["path"]: entry["sha256"]})
    for entry in proof["raw_hashes"]:
        hashes({str(Path(proof["raw_root"])/entry["path"]): entry["sha256"]})
    for key in ["seal", "local_inventory"]:
        hashes({proof[key]["path"]: proof[key]["sha256"]})
    records = pd.read_csv("docs/transfer_training_qc_records.csv", float_precision="round_trip")
    known = pd.read_csv("docs/transfer_training_qc_known_canonical.csv", float_precision="round_trip")
    sensitivity = pd.read_csv("docs/transfer_training_qc_sensitivity_records.csv", float_precision="round_trip")
    assert len(records) == 520 and len(known) == 960 and len(sensitivity) == 3640
    assert records["available_0.5"].all() and known["available_0.5"].all()
    assert set(records.speed_mm_s) == {30, 50} and set(known.speed_mm_s) == {20, 40, 60}
    assert records.groupby("surface_id").size().eq(52).all()
    for _, part in sensitivity.groupby("variant"):
        assert set(part.recording_id) == set(records.recording_id)
        for duration in [.25, .5, 1.]:
            expected = part.valid & (part.canonical_start_s+duration <= part.steady_end_s)
            assert expected.equals(part[f"available_{duration:g}"])
    domains = pd.read_csv(spec["domain_table"])
    expected = training_eligibility(pd.concat([known, records], ignore_index=True), domains, spec["surface_ids"]).fillna("")
    actual = pd.read_csv("docs/transfer_training_qc_common_eligibility.csv", float_precision="round_trip").fillna("")
    pd.testing.assert_frame_equal(actual, expected)
    assert len(actual) == 2100 and actual.common_candidate.all()
    exposure = read(spec["exposure_snapshot"])
    validate_development_access(spec["surface_ids"], pd.read_csv(spec["group_manifest"]), pd.read_csv(spec["reservation_manifest"]),
        exposure["training_surface_ids"]+exposure["selection_surface_ids"])
    assert not any(proof[k] for k in ["reserved_signals_accessed", "prediction_scores_accessed", "settings_changed"])
    return proof


def validate_matched():
    proof = read("docs/matched_review_provenance.json")
    for key in ["input_hashes", "source_hashes", "selected_artifact_hashes", "scoring_artifact_hashes"]:
        hashes(proof[key])
    for entry in proof["outputs"]:
        hashes({entry["path"]: entry["sha256"]})
    for key in ["execution_seal", "selection_seal"]:
        hashes({proof[key]["path"]: proof[key]["sha256"]})
    output = Path(proof["output_root"])
    seal = read(proof["selection_seal"]["path"])
    assert seal["completed_experiments"] == ["familiar", "omitted"] and seal["encoder_selections"] == 6 and seal["baseline_selections"] == 10
    assert not seal["deferred_targets_prepared"] and not seal["reverse_used_for_selection"]
    assert proof["shared_scaler_exact"] and not proof["reserved_signals_accessed"]
    windows = pd.read_csv(output/"windows.csv", float_precision="round_trip").set_index("window_id")
    audit = pd.read_csv("docs/matched_review_windows.csv", float_precision="round_trip").set_index("window_id")
    assert len(windows) == len(audit) == proof["windows"] == 1878
    assert windows.deferred_until_selection_seal.sum() == 192
    assert audit.outside_perturbation_equal.all()
    assert (audit.raw_start_index == audit.dependency_raw_start_index).all()
    assert (audit.raw_end_index_exclusive == audit.dependency_raw_end_index_exclusive).all()
    for window_id, row in windows.iterrows():
        assert file_hash(output/row.feature_path) == audit.loc[window_id, "feature_sha256"]
        assert audit.loc[window_id, "raw_first_time_s"] >= row.start_s
        assert audit.loc[window_id, "raw_last_time_s"] < row.end_s
        assert audit.loc[window_id, "phase"] == ("post_selection_scoring" if row.deferred_until_selection_seal else "fit_selection_preparation")
    contexts = {}
    for name, expected_count in [("familiar", 21000), ("omitted", 13200)]:
        episodes = pd.read_csv(output/name/"episodes.csv")
        train = episodes[episodes.split == "train"]
        selection = episodes[(episodes.evaluation_partition == "selection") & (episodes.orientation == "forward")]
        val = episodes[episodes.split == "val"]
        assert len(train) == expected_count and len(selection) == 1320 and len(val) == 4200
        assert episodes.episode_id.is_unique
        if name == "omitted":
            assert set(train.query_speed_mm_s) == {20, 40, 60}
        contexts[name] = val
        with np.load(output/name/"predictions.npz") as values:
            assert np.array_equal(values["episode_ids"], val.episode_id.to_numpy(dtype=str))
            targets = []
            for row in val.itertuples():
                with np.load(output/windows.loc[row.query_window_id, "feature_path"]) as feature:
                    targets.append(feature["log_band_power"].reshape(-1).astype(np.float32))
            assert np.array_equal(values["targets"], np.stack(targets))
        for access in [row for row in proof["feature_accesses"] if row["experiment"] == name and row["phase"] == "fit_selection"]:
            window = windows.loc[access["window_id"]]
            assert not window.deferred_until_selection_seal
            if name == "omitted" and window.split == "train" and window.role == "query":
                assert window.speed_mm_s in [20, 40, 60]
    keys = ["surface_id", "orientation", "protocol", "duration_s", "support_window_ids", "query_window_id", "evaluation_partition"]
    pd.testing.assert_frame_equal(contexts["familiar"][keys].reset_index(drop=True), contexts["omitted"][keys].reset_index(drop=True))
    with np.load(output/"familiar/scaler.npz") as a, np.load(output/"omitted/scaler.npz") as b:
        assert all(np.array_equal(a[k], b[k]) for k in ["mean", "std"])
    scores = pd.read_csv(output/"per_query.csv", float_precision="round_trip")
    assert len(scores) == 92400
    per_surface, summary, residuals = aggregate_scores(scores)
    for suffix, expected in [("per_surface", per_surface), ("summary", summary),
        ("primary_residuals", residuals[(residuals.duration_s == .5) & residuals.protocol.isin(["single", "repeat", "direction"])])]:
        actual = pd.read_csv(f"docs/matched_review_{suffix}.csv", float_precision="round_trip")
        pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected.reset_index(drop=True), check_exact=False, atol=1e-14, rtol=0)
    return proof


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-only", action="store_true")
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    proofs = [validate_coverage()]
    if not args.coverage_only:
        proofs.append(validate_matched())
    if args.staged:
        for proof in proofs:
            mapping = {**proof.get("public_input_hashes", {}), **proof["source_hashes"],
                **{row["path"]: row["sha256"] for row in proof["outputs"]}}
            # Matched input hashes include ignored private raw/selection files.
            if "input_hashes" in proof:
                mapping.update({k: v for k, v in proof["input_hashes"].items() if k.startswith(("configs/", "docs/"))})
            for path, sha in mapping.items():
                content = subprocess.run(["git", "show", f":{path.replace(chr(92), '/')}"], capture_output=True, check=True).stdout
                assert hashlib.sha256(content).hexdigest() == sha, path
    print("Verified complete transfer training coverage"+ (" and matched role identities, all-selection seal, target isolation, 1878 bounded windows and 92400 score rows." if not args.coverage_only else "."))
