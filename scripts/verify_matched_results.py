"""Replay frozen matched predictions and independently reconstruct their metrics.

No fitting, checkpoint selection, downloads or reserved-signal access occurs.
The original execution sources and artifacts remain unchanged.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from tactile_contact.config import file_hash
from tactile_contact.matched import wrong_support_by_orientation
from tactile_contact.models import ContactPredictor
from tactile_contact.repetition_review import FrozenScoringStore, restore_baselines
from tactile_contact.study_design import validate_development_access
from tactile_contact.training import model_predictions
from validate_matched_review import validate_coverage, validate_matched


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def independent_metrics(prediction, target):
    if prediction.shape != target.shape or prediction.shape[1] != 96:
        raise ValueError("Prediction/target dimensions changed")
    if not np.isfinite(prediction).all() or not np.isfinite(target).all():
        raise ValueError("Nonfinite saved prediction/target")
    def rms(value):
        power = np.maximum(10. ** value.astype(np.float64).reshape(-1, 32, 3)-1e-10, 0.)
        return np.sqrt(power.sum(axis=1)), np.sqrt(power.sum(axis=(1, 2)))
    axes, total = rms(prediction)
    true_axes, true_total = rms(target)
    return dict(log_power_mae=np.abs(prediction-target).mean(axis=1),
        modeled_band_total_rms_error=np.abs(total-true_total),
        **{f"rms_error_{axis}": np.abs(axes[:, i]-true_axes[:, i]) for i, axis in enumerate("XYZ")})


def objective(episodes, error, primary=False):
    values = episodes[["surface_id", "protocol", "duration_s"]].copy()
    values["error"] = error
    if primary:
        values = values[(values.protocol == "single") & (values.duration_s == .5)]
    return float(values.groupby(["protocol", "duration_s", "surface_id"]).error.mean().groupby(level=[0, 1]).mean().mean())


def verify_histories(root, name, selections, public_histories):
    for seed in [0, 1, 2]:
        destination = root/name/f"seed_{seed}"
        history = pd.read_csv(destination/"history.csv", float_precision="round_trip")
        selection = read(destination/"selection.json")
        assert history.epoch.tolist() == list(range(1, len(history)+1))
        assert 1 <= len(history) <= 120
        best, chosen, stale = np.inf, 0, 0
        for row in history.itertuples():
            assert np.isfinite([row.train_loss, row.validation_equal_cell_mae, row.validation_primary_mae]).all()
            if row.validation_equal_cell_mae < best:
                best, chosen, stale = row.validation_equal_cell_mae, row.epoch, 0
            else:
                stale += 1
            assert (row.best_equal_cell_mae, row.selected_epoch, row.stale_epochs) == (best, chosen, stale)
            assert stale < 10 or row.epoch == len(history)
        assert selection["selected_epoch"] == chosen and selection["epochs_run"] == len(history)
        assert selection["selection_equal_cell_mae"] == best
        assert selection["selection_primary_mae"] == history.iloc[chosen-1].validation_primary_mae
        assert selection["stop_reason"] == ("patience" if stale == 10 else "epoch_cap")
        assert stale == 10 or len(history) == 120
        row = selections[(selections.experiment == name) & (selections.seed == seed)].iloc[0]
        for key, value in selection.items():
            assert row[key] == value
        public = public_histories[(public_histories.experiment == name) & (public_histories.seed == seed)].drop(columns=["experiment", "seed"])
        pd.testing.assert_frame_equal(history, public.reset_index(drop=True), check_exact=True)


def verify(write_report=False):
    torch.set_num_threads(1)
    design = read("configs/matched_development_review.json")
    exposure = read(design["exposure_snapshot"])
    validate_development_access(design["train_ids"]+design["selection_and_score_ids"],
        pd.read_csv(design["group_manifest"]), pd.read_csv(design["reservation_manifest"]),
        exposure["training_surface_ids"]+exposure["selection_surface_ids"])
    coverage, proof = validate_coverage(), validate_matched()
    root = Path(proof["output_root"])
    windows = pd.read_csv(root/"windows.csv", float_precision="round_trip")
    scores = pd.read_csv(root/"per_query.csv", float_precision="round_trip")
    selections = pd.read_csv("docs/matched_review_selections.csv", float_precision="round_trip")
    histories = pd.read_csv("docs/matched_review_histories.csv", float_precision="round_trip")
    replay, reconstructed = [], []
    for name in ["familiar", "omitted"]:
        episodes = pd.read_csv(root/name/"episodes.csv")
        val = episodes[episodes.split == "val"].reset_index(drop=True)
        select = (val.evaluation_partition == "selection") & (val.orientation == "forward")
        verify_histories(root, name, selections, histories)
        with np.load(root/name/"scaler.npz") as data:
            scaler = {k: data[k].copy() for k in ["mean", "std"]}
        models = restore_baselines(root/name/"baselines", interpolate_speeds=name == "omitted")
        store = FrozenScoringStore(root, windows, val)
        outputs = []
        for method, model in models.items():
            value = model.predict(val, store, scaler)
            prediction, ids = value if isinstance(value, tuple) else (value, None)
            outputs.append((method, -1, prediction, ids))
        for seed in [0, 1, 2]:
            checkpoint = torch.load(root/name/f"seed_{seed}/model.pt", weights_only=True, map_location="cpu")
            selection = read(root/name/f"seed_{seed}/selection.json")
            assert checkpoint["seed"] == seed and not checkpoint["resumable"]
            assert checkpoint["selected_epoch"] == selection["selected_epoch"]
            assert checkpoint["actual_epochs_run"] == selection["epochs_run"]
            assert set(episodes.config_hash) == {checkpoint["config_hash"]}
            assert all(np.array_equal(checkpoint[f"scaler_{k}"].numpy(), scaler[k]) for k in scaler)
            model = ContactPredictor(latent_dim=checkpoint["latent_dim"])
            model.load_state_dict(checkpoint["state_dict"]); model.eval()
            for method, rows in [("encoder", val), ("encoder_wrong_support", wrong_support_by_orientation(val))]:
                outputs.append((method, seed, model_predictions(model, rows, store, scaler), None))
        # All predictors complete under a store that denies every query feature.
        assert store.phase == "prediction" and all(w in store.supports for _, w in store.accesses)
        store.unlock_targets()
        target = store.targets(val)
        with np.load(root/name/"predictions.npz") as saved:
            assert np.array_equal(target, saved["targets"])
            expected_keys = {"targets", "episode_ids"}
            for method, seed, prediction, ids in outputs:
                key = method if seed == -1 else f"{method}_{seed}"
                expected_keys.add(key)
                assert np.array_equal(prediction, saved[key]), f"Frozen replay changed: {name}/{key}"
                metrics = independent_metrics(prediction, target)
                table = scores[(scores.experiment == name) & (scores.model == method) & (scores.seed == seed)]
                assert np.array_equal(table.episode_id.to_numpy(), val.episode_id.to_numpy())
                for column, value in metrics.items():
                    np.testing.assert_allclose(table[column].to_numpy(), value, rtol=0, atol=1e-14)
                if ids is not None:
                    assert np.array_equal(table.retrieved_training_id.to_numpy(dtype=int), np.asarray(ids, dtype=int))
                else:
                    assert table.retrieved_training_id.isna().all()
                if method == "encoder":
                    selection = read(root/name/f"seed_{seed}/selection.json")
                    # Replaying a different batch shape can alter float32 GEMM reductions.
                    for primary, field in [(False, "selection_equal_cell_mae"), (True, "selection_primary_mae")]:
                        assert abs(objective(val[select], metrics["log_power_mae"][select], primary)-selection[field]) <= 1e-6
                if method in ["fixed_features", "speed_rescaling"]:
                    base = root/name/"baselines"
                    if method == "fixed_features":
                        candidates = read(base/"fixed_features_selection.json")
                        with np.load(base/"fixed_features_fit.npz") as data:
                            alpha = float(data["alpha"])
                    else:
                        fit = read(base/"speed_rescaling_fit.json")
                        candidates, alpha = fit["candidates"], fit["selected_alpha"]
                    chosen = min(candidates, key=lambda item: item["validation_mae"])
                    assert chosen["alpha"] == alpha
                    assert abs(objective(val[select], metrics["log_power_mae"][select])-chosen["validation_mae"]) <= 1e-6
                frame = val.copy()
                frame["experiment"], frame["model"], frame["seed"] = name, method, seed
                for column, value in metrics.items():
                    frame[column] = value
                reconstructed.append(frame)
                replay.append(dict(experiment=name, prediction=key, rows=len(val), bit_exact=True))
        assert set(saved.files) == expected_keys
        print(f"Replayed {name}: 11 exact prediction arrays; selected fits and all query metrics verified.", flush=True)
    result = pd.concat(reconstructed, ignore_index=True)
    keys = ["experiment", "evaluation_partition", "orientation", "model", "protocol", "duration_s", "surface_id", "family_group"]
    columns = ["log_power_mae", "modeled_band_total_rms_error"]
    surfaces = result.groupby(keys+["seed"])[columns].mean().groupby(level=keys).mean().reset_index()
    actual = pd.read_csv("docs/matched_review_per_surface.csv", float_precision="round_trip")
    pd.testing.assert_frame_equal(surfaces, actual, check_exact=False, rtol=0, atol=1e-14)
    summary = surfaces.groupby(keys[:-2])[columns].mean().reset_index()
    summary["surfaces"] = surfaces.groupby(keys[:-2]).surface_id.nunique().to_numpy()
    actual_summary = pd.read_csv("docs/matched_review_summary.csv", float_precision="round_trip")
    pd.testing.assert_frame_equal(summary, actual_summary, check_exact=False, rtol=0, atol=1e-14)
    conditions = ["query_speed_mm_s", "query_direction_deg", "query_nominal_force_N"]
    residual_keys = keys+conditions
    residuals = result.groupby(residual_keys+["seed"])[columns].mean().groupby(level=residual_keys).mean().reset_index()
    primary_residuals = residuals[(residuals.duration_s == .5) & residuals.protocol.isin(["single", "repeat", "direction"])].reset_index(drop=True)
    actual_residuals = pd.read_csv("docs/matched_review_primary_residuals.csv", float_precision="round_trip")
    pd.testing.assert_frame_equal(primary_residuals, actual_residuals, check_exact=False, rtol=0, atol=1e-14)
    contrasts = pd.read_csv("docs/matched_review_contrasts.csv", float_precision="round_trip")
    for row in contrasts.itertuples():
        part = surfaces[(surfaces.evaluation_partition == row.partition) & (surfaces.orientation == row.orientation) &
            (surfaces.model == row.model) & (surfaces.duration_s == row.duration_s)]
        if row.contrast == "omitted_minus_familiar":
            part = part[part.protocol == row.protocol]
            pivot = part.pivot(index="surface_id", columns="experiment", values="log_power_mae")
            delta = pivot.omitted-pivot.familiar
        else:
            assert row.contrast == "repeat_minus_direction"
            part = part[part.experiment == row.experiment]
            pivot = part.pivot(index="surface_id", columns="protocol", values="log_power_mae")
            delta = pivot["repeat"]-pivot.direction
        assert len(delta) == row.groups == 2
        assert abs(delta.mean()-row.mean_difference) <= 1e-14
        # With two independent singleton groups, the bootstrap has only three
        # attainable means; both extreme values occur in the 2.5/97.5 tails.
        assert abs(delta.min()-row.ci95_low) <= 1e-14
        assert abs(delta.max()-row.ci95_high) <= 1e-14
    report = dict(review_id="matched_frozen_replay_validation_v2", review_date="2026-10-10",
        original_execution_provenance=dict(path="docs/matched_review_provenance.json", sha256=file_hash("docs/matched_review_provenance.json")),
        source_sha256=file_hash(__file__), replay=replay, per_query_rows=len(result), scalar_metric_checks=len(result)*5,
        independently_reconstructed_summary_rows=len(summary), independently_reconstructed_specimen_rows=len(surfaces),
        independently_reconstructed_primary_residual_rows=len(primary_residuals),
        selection_histories=6, baseline_selections_checked=4, contrasts_checked=len(contrasts),
        query_features_denied_during_prediction=True, refitting=False, reserved_signals_accessed=False,
        limits="Frozen artifact replay and independent numerical validation; not fresh scientific testing, physical calibration or population inference.")
    if write_report:
        path = Path("docs/matched_validation_provenance.json")
        serialized = json.dumps(report, indent=2)+"\n"
        if path.exists() and path.read_text(encoding="utf-8") != serialized:
            raise ValueError("Preserve prior verification evidence; use a distinct report before changing verification sources")
        path.write_text(serialized, encoding="utf-8", newline="\n")
    print(f"Verified 22 exact frozen arrays, {len(result)} score rows, six histories and {len(contrasts)} independently derived contrasts.", flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    verify(parser.parse_args().write_report)
