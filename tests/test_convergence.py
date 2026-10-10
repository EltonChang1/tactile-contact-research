import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from tactile_contact.convergence import SelectionStore, fit_convergence, primary_objective, verify_reference_history
from tactile_contact.episodes import FeatureStore
from tactile_contact.training import fit_model


def test_primary_diagnostic_averages_specimens_and_ignores_other_cells():
    episodes = pd.DataFrame(dict(surface_id=[1, 1, 2, 1], protocol=["single", "single", "single", "repeat"], duration_s=[.5]*4))
    predicted = np.repeat(np.array([[1.], [1.], [3.], [100.]]), 96, axis=1)
    assert primary_objective(episodes, predicted, np.zeros_like(predicted)) == 2.
    with pytest.raises(ValueError, match="missing"):
        primary_objective(episodes.assign(protocol="repeat"), predicted, np.zeros_like(predicted))


def test_reference_trajectory_rejects_drift_missing_epochs_and_false_horizon():
    history = pd.DataFrame(dict(epoch=[1, 2, 3], train_loss=[.5, .3, .2], validation_equal_cell_mae=[.6, .4, .3]))
    assert verify_reference_history(history, history.iloc[:2], 2) == 0.
    changed = history.copy(); changed.loc[1, "train_loss"] += 1e-8
    with pytest.raises(ValueError, match="did not reproduce"):
        verify_reference_history(changed, history.iloc[:2], 2)
    with pytest.raises(ValueError, match="incomplete"):
        verify_reference_history(history.iloc[[0, 2]], history.iloc[:2], 2)


def test_unselected_query_feature_fails_before_cache_access(prepared, monkeypatch):
    root, cfg, windows, episodes, original, scaler, train, val = prepared
    chosen = val[val.query_window_id != val.query_window_id.iloc[0]]
    store = SelectionStore(root, windows, train, chosen)
    hidden = val.query_window_id.iloc[0]
    def forbidden(*args, **kwargs):
        pytest.fail("Forbidden target reached underlying feature loader/cache")
    monkeypatch.setattr(FeatureStore, "feature", forbidden)
    with pytest.raises(ValueError, match="whitelist"):
        store.feature(hidden)
    with pytest.raises(ValueError, match="Every trajectory"):
        store.unlock_scoring(val, selected_trajectories=1, expected_trajectories=2)
    assert store.phase == "selection"
    with pytest.raises(ValueError, match="whitelist"):
        store.feature(hidden)


def test_transfer_role_cannot_enter_selection(prepared):
    root, cfg, windows, episodes, original, scaler, train, val = prepared
    with pytest.raises(ValueError, match="exclude transfer"):
        SelectionStore(root, windows, train, val.assign(evaluation_partition="transfer"))


def test_extension_reproduces_legacy_sampler_history_and_checkpoint(prepared, tmp_path):
    root, cfg, windows, episodes, original, scaler, train, val = prepared
    _, checkpoint_path = fit_model(tmp_path/"legacy", cfg, train, val, original, scaler, 0)
    reference = torch.load(checkpoint_path, weights_only=True, map_location="cpu")
    historical = pd.read_csv(checkpoint_path.with_name("history.csv"), float_precision="round_trip")
    store = SelectionStore(root, windows, train, val)
    history, metadata = fit_convergence(tmp_path/"extension", cfg, train, val, store, scaler, 0, 4, 2, historical, reference)
    assert metadata["first_reference_history_max_change"] == 0.
    assert metadata["reference_checkpoint_tensor_match"]
    assert len(history) >= 2 and history.validation_primary_mae.notna().all()
    saved = torch.load(tmp_path/"extension/best_by_2.pt", weights_only=True)
    assert all(torch.equal(value, reference["state_dict"][key]) for key, value in saved["state_dict"].items())
    assert not saved["resumable"]
    with pytest.raises(ValueError, match="fresh output root"):
        fit_convergence(tmp_path/"extension", cfg, train, val, store, scaler, 0, 4, 2)


def test_extension_rejects_transfer_before_training_or_output(prepared, tmp_path):
    root, cfg, windows, episodes, original, scaler, train, val = prepared
    with pytest.raises(ValueError, match="exclude transfer"):
        fit_convergence(tmp_path/"forbidden", cfg, train, val.assign(evaluation_partition="transfer"), original, scaler, 0, 4, 2)
    assert not (tmp_path/"forbidden").exists()


def test_runner_reservation_preflight_precedes_feature_values(tmp_path, monkeypatch):
    module_spec = importlib.util.spec_from_file_location("convergence_runner", Path("scripts/review_convergence.py"))
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    spec = json.loads(Path("configs/convergence_review.json").read_text())
    root = tmp_path/"reserved_history"
    (root/"results").mkdir(parents=True)
    (root/"results/run_manifest.json").write_text(json.dumps({"config": {"train_ids": [5], "val_ids": [10]}}))
    spec["experiments"][0]["historical_root"] = str(root)
    def forbidden(*args, **kwargs):
        pytest.fail("Reserved cohort reached feature values before preflight")
    monkeypatch.setattr(module.np, "load", forbidden)
    with pytest.raises(ValueError, match="reserved test group"):
        module.preflight(spec)
