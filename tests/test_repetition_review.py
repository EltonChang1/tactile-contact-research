import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tactile_contact.episodes import FeatureStore
from tactile_contact.repetition_review import (FrozenScoringStore, aggregate_scores,
    build_reversed_episodes, restore_baselines, reversed_requests)


def test_reversal_preserves_matched_conditions_and_canonical_repeat_control(prepared):
    _, _, windows, _, _, _, _, val = prepared
    original = val.copy(deep=True)
    requests, plans = reversed_requests(val, windows)
    lookup = {key: f"new-{index}" for index, key in enumerate(requests)}
    reversed_rows = build_reversed_episodes(val, plans, lookup)
    pd.testing.assert_frame_equal(val, original)
    assert len(reversed_rows) == len(val)
    assert (reversed_rows.query_repeat_id == 0).all()
    assert np.array_equal(reversed_rows.matched_forward_episode_id, val.episode_id)
    assert (reversed_rows.episode_id != val.episode_id).all()
    for row, (supports, query) in zip(val.itertuples(), plans):
        assert query[0] == row.surface_id and query[4:6] == (0, "query")
        assert query[1:4] == (row.query_speed_mm_s, row.query_direction_deg, row.query_nominal_force_N)
        assert [key[4] for key in supports] == ([0, 1] if row.protocol == "repeat" else [1]*len(supports))
        assert all(key[-1] == row.duration_s for key in supports)


def test_incomplete_complementary_cohort_aborts_without_dropping_queries(prepared):
    _, _, windows, _, _, _, _, val = prepared
    requests, plans = reversed_requests(val, windows)
    lookup = {key: str(index) for index, key in enumerate(requests)}
    del lookup[plans[0][1]]
    with pytest.raises(ValueError, match="never silently drop"):
        build_reversed_episodes(val, plans, lookup)


def test_reversal_rejects_changed_target_repetition_and_query_as_support(prepared):
    _, _, windows, _, _, _, _, val = prepared
    with pytest.raises(ValueError, match="repeat-1 queries"):
        reversed_requests(val.assign(query_repeat_id=0), windows)
    altered = val.copy()
    altered.loc[0, "support_window_ids"] = json.dumps([val.query_window_id.iloc[0]])
    with pytest.raises(ValueError, match="Support role"):
        reversed_requests(altered, windows)


def test_prediction_target_guard_precedes_underlying_cached_loader(prepared, monkeypatch):
    root, _, windows, _, _, _, _, val = prepared
    store = FrozenScoringStore(root, windows, val)
    hidden = val.query_window_id.iloc[0]
    store._cache[hidden] = {"hidden": "already cached"}
    def forbidden(*args, **kwargs):
        pytest.fail("Hidden target reached loader or cache")
    monkeypatch.setattr(FeatureStore, "feature", forbidden)
    with pytest.raises(ValueError, match="before frozen predictions"):
        store.feature(hidden)
    store.unlock_targets()
    assert hidden in store.allowed and store.phase == "scoring"


def test_residual_aggregation_gives_equal_specimen_and_seed_weight():
    rows = []
    for surface, seed, errors in [(1, 0, [0., 0., 0.]), (1, 1, [2.]), (2, 0, [3.])]:
        for error in errors:
            rows.append(dict(experiment="expanded", evaluation_partition="selection", orientation="reverse",
                model="encoder", protocol="single", duration_s=.5, surface_id=surface, family_group=str(surface),
                seed=seed, log_power_mae=error, modeled_band_total_rms_error=error,
                query_speed_mm_s=30, query_direction_deg=45, query_nominal_force_N=.5))
    per_surface, summary, residuals = aggregate_scores(pd.DataFrame(rows))
    assert summary.log_power_mae.iloc[0] == 2.
    assert summary.surfaces.iloc[0] == 2
    assert per_surface.log_power_mae.tolist() == [1., 3.]
    assert residuals.log_power_mae.tolist() == [1., 3.]


def test_restore_frozen_baselines_preserves_coefficients_and_interpolation(tmp_path):
    coef = np.arange(8).reshape(2, 4)
    np.savez(tmp_path/"conditions_only_fit.npz", coefficient=coef, intercept=np.array([1., 2.]))
    np.savez(tmp_path/"fixed_features_fit.npz", coefficient=coef, intercept=np.array([3., 4.]),
        feature_mean=np.arange(4), feature_std=np.ones(4))
    (tmp_path/"speed_rescaling_fit.json").write_text(json.dumps(dict(p=1.2, b=-.3)))
    (tmp_path/"retrieval_sources.json").write_text(json.dumps(dict(library={"single_0.5": {"1": ["s"]}},
        responses={"1_20_45_0.5": ["q20"], "1_40_45_0.5": ["q40"]})))
    np.savez(tmp_path/"retrieval_fit.npz", fingerprints_single_0_ignored=np.zeros(1),
        **{"fingerprints_single_0.5": np.ones((1, 96)), "training_ids_single_0.5": np.array([1]),
           "response_1_20_45_0.5": np.array([2., 4.]), "response_1_40_45_0.5": np.array([4., 8.])})
    models = restore_baselines(tmp_path, interpolate_speeds=True)
    assert np.array_equal(models["conditions_only"].regression.coef_, coef)
    assert np.array_equal(models["fixed_features"].mean, np.arange(4))
    assert np.array_equal(models["speed_rescaling"].exponents, [1.2, -.3])
    values, keys, weights = models["retrieval"].response(1, 30, 45, .5)
    assert np.array_equal(values, [3., 6.]) and weights == [.5, .5]
    assert keys == [(1, 20, 45, .5), (1, 40, 45, .5)]
    with pytest.raises(ValueError, match="extrapolation"):
        models["retrieval"].response(1, 60, 45, .5)


def test_repetition_reservation_guard_precedes_parameters_and_raw(tmp_path, monkeypatch):
    module_spec = importlib.util.spec_from_file_location("repetition_runner", Path("scripts/review_repetition.py"))
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    spec = json.loads(Path("configs/repetition_review.json").read_text())
    root = tmp_path/"reserved_history"
    (root/"results").mkdir(parents=True)
    (root/"results/run_manifest.json").write_text(json.dumps({"config": {"train_ids": [5], "val_ids": [10]}}))
    spec["experiments"][0]["historical_root"] = str(root)
    def forbidden(*args, **kwargs):
        pytest.fail("Reserved cohort reached numerical values")
    monkeypatch.setattr(module.np, "load", forbidden)
    monkeypatch.setattr(module, "load_record", forbidden)
    with pytest.raises(ValueError, match="reserved test group"):
        module.preflight(spec)
