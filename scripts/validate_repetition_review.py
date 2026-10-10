"""Verify the recorded frozen repetition review without refitting or downloading."""
import argparse
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from tactile_contact.config import file_hash
from tactile_contact.repetition_review import aggregate_scores
from tactile_contact.study_design import validate_development_access


def run(staged=False):
    provenance = json.loads(Path("docs/repetition_review_provenance.json").read_text())
    spec = json.loads(Path("configs/repetition_review.json").read_text())
    for section in ["public_input_hashes", "source_hashes", "input_hashes"]:
        for path, sha in provenance[section].items():
            assert file_hash(path) == sha, path
    for row in provenance["outputs"]:
        assert file_hash(row["path"]) == row["sha256"], row["path"]
    seal = provenance["frozen_seal"]
    assert file_hash(seal["path"]) == seal["sha256"]
    frozen = json.loads(Path(seal["path"]).read_text())
    assert frozen["no_refit"] and not frozen["complementary_signals_accessed"]
    assert frozen["encoder_checkpoints"] == 6
    assert len(provenance["reproduction"]) == 22
    assert all(row["exact_prediction_reproduction"] for row in provenance["reproduction"])
    assert not provenance["reserved_signals_accessed"] and provenance["no_new_download"]
    assert provenance["episodes_per_orientation"] == {"expanded": 120, "omitted": 300}
    windows = pd.read_csv("docs/repetition_review_windows.csv", float_precision="round_trip")
    assert len(windows) == provenance["windows"] == 88
    assert windows.outside_perturbation_equal.all()
    assert (windows.end_s <= windows.steady_end_s).all()
    assert (windows.raw_first_time_s >= windows.start_s).all()
    assert (windows.raw_last_time_s < windows.end_s).all()
    assert (windows.observed_context_before_s == 0).all() and (windows.observed_context_after_s == 0).all()
    assert (windows.raw_start_index == windows.dependency_raw_start_index).all()
    assert (windows.raw_end_index_exclusive == windows.dependency_raw_end_index_exclusive).all()
    scores = pd.read_csv(Path(spec["output_root"])/"per_query.csv", float_precision="round_trip")
    assert len(scores) == 9240
    for name, count in provenance["episodes_per_orientation"].items():
        for orientation in ["forward", "reverse"]:
            part = scores[(scores.experiment == name) & (scores.orientation == orientation)]
            assert part.groupby(["model", "seed"]).size().eq(count).all()
            assert part.query_repeat_id.eq(1 if orientation == "forward" else 0).all()
    for suffix, expected in zip(["per_surface", "summary", "residuals"], aggregate_scores(scores)):
        actual = pd.read_csv(f"docs/repetition_review_{suffix}.csv", float_precision="round_trip")
        pd.testing.assert_frame_equal(actual, expected, check_exact=False, atol=1e-14, rtol=0)
    for experiment in spec["experiments"]:
        name, root = experiment["name"], Path(experiment["historical_root"])
        original = pd.read_csv(root/"data/manifests/windows.csv").set_index("window_id")
        destination = Path(spec["output_root"])/name
        new = pd.read_csv(destination/"windows.csv").set_index("window_id")
        for window_id, row in new.iterrows():
            with np.load(row.feature_path) as values:
                audit = windows[(windows.experiment == name) & (windows.window_id == window_id)].iloc[0]
                assert file_hash(row.feature_path) == audit.feature_sha256
                if window_id in original.index:
                    with np.load(root/original.loc[window_id, "feature_path"]) as old:
                        assert set(values.files) == set(old.files)
                        assert all(np.array_equal(values[k], old[k]) for k in values.files)
        for access in [r for r in provenance["feature_accesses"] if r["experiment"] == name]:
            manifest = original if access["orientation"] == "forward" else new
            if access["phase"] == "prediction":
                assert manifest.loc[access["window_id"], "role"] == "support"
        reverse = pd.read_csv(destination/"episodes.csv")
        forward = scores[(scores.experiment == name) & (scores.orientation == "forward") & (scores.model == "copy")]
        assert set(reverse.matched_forward_episode_id) == set(forward.episode_id)
        assert reverse.episode_id.nunique() == len(reverse)
        for row in reverse[reverse.protocol == "repeat"].itertuples():
            ids = json.loads(row.support_window_ids)
            assert new.loc[ids].repeat_id.tolist() == [0, 1]
        with np.load(destination/"targets.npz") as targets:
            # Every reverse target derives from its declared, bounded query feature.
            recomputed = []
            for row in reverse.itertuples():
                with np.load(new.loc[row.query_window_id, "feature_path"]) as feature:
                    recomputed.append(feature["log_band_power"].reshape(-1).astype(np.float32))
            assert np.array_equal(targets["reverse"], np.stack(recomputed))
    inventory = json.loads(Path("data/raw_inventory.json").read_text())
    raw_ids = sorted({int(f["path"].split("/")[2]) for f in inventory["files"] if f["path"].startswith("sensor_data/")})
    exposure = json.loads(Path(spec["exposure_snapshot"]).read_text())
    validate_development_access(raw_ids, pd.read_csv(spec["group_manifest"]), pd.read_csv(spec["reservation_manifest"]),
        exposure["training_surface_ids"]+exposure["selection_surface_ids"])
    if staged:
        import hashlib
        mapping = {**provenance["public_input_hashes"], **provenance["source_hashes"],
            **{row["path"]: row["sha256"] for row in provenance["outputs"]}}
        for path, sha in mapping.items():
            content = subprocess.run(["git", "show", f":{path.replace(chr(92), '/')}"], capture_output=True, check=True).stdout
            assert hashlib.sha256(content).hexdigest() == sha, path
    print("Validated frozen inputs/checkpoints, 22 exact reproductions, 88 bounded windows, 9240 scoring rows, matched aggregation, target derivation and untouched reservation."+ (" Staged public hashes match." if staged else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true")
    run(parser.parse_args().staged)
