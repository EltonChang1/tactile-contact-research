import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tactile_contact.episodes import FeatureStore
from tactile_contact.matched import MatchedStore, build_matched_episodes, fit_matched, wrong_support_by_orientation
from tactile_contact.study_design import query_domains
from tactile_contact.transfer_training import training_eligibility, preflight as training_preflight


def identity_fixture():
    domains = query_domains()
    rows = []
    for surface in [0, 1, 10, 57]:
        for query in domains[domains.support_condition | domains.matched_familiar_fit_query].itertuples():
            role = "support" if query.support_condition else "query"
            for repeat in [0, 1]:
                for duration in [.25, .5, 1.] if role == "support" else [.5]:
                    rows.append(dict(surface_id=surface, speed_mm_s=query.speed_mm_s, direction_deg=query.direction_deg,
                        nominal_force_N=query.nominal_force_N, repeat_id=repeat, role=role, duration_s=duration,
                        split="train" if surface in [0, 1] else "val", window_id=f"{surface}_{query.speed_mm_s}_{query.direction_deg}_{query.nominal_force_N}_{repeat}_{role}_{duration}"))
    groups = pd.DataFrame(dict(surface_id=[0, 1, 10, 57], family_group=["a", "b", "c", "d"]))
    design = dict(train_ids=[0, 1], selection_and_score_ids=[10, 57],
        budgets=dict(protocols=["single", "repeat", "speed", "load", "direction"], support_durations_logged_s=[.25, .5, 1.]))
    return pd.DataFrame(rows), groups, design, domains


def test_matched_roles_keep_identical_selection_and_score_identities():
    windows, groups, design, domains = identity_fixture()
    familiar = build_matched_episodes(windows, groups, design, domains, "familiar", "a")
    omitted = build_matched_episodes(windows, groups, design, domains, "omitted", "b")
    assert len(familiar[familiar.split == "train"]) == 4200
    assert len(omitted[omitted.split == "train"]) == 2640
    assert set(omitted[omitted.split == "train"].query_speed_mm_s) == {20, 40, 60}
    keys = ["surface_id", "orientation", "protocol", "duration_s", "query_window_id", "support_window_ids", "evaluation_partition"]
    pd.testing.assert_frame_equal(familiar[familiar.split == "val"][keys].reset_index(drop=True), omitted[omitted.split == "val"][keys].reset_index(drop=True))
    for rows in [familiar, omitted]:
        assert len(rows[(rows.split == "val") & (rows.orientation == "forward") & (rows.evaluation_partition == "selection")]) == 1320
        assert len(rows[(rows.split == "val") & (rows.orientation == "reverse") & (rows.evaluation_partition == "transfer")]) == 780


def test_matched_builder_aborts_missing_complements_and_duplicate_keys():
    windows, groups, design, domains = identity_fixture()
    with pytest.raises(ValueError, match="Missing matched"):
        build_matched_episodes(windows.iloc[:-1], groups, design, domains, "familiar", "a")
    with pytest.raises(ValueError, match="Ambiguous"):
        build_matched_episodes(pd.concat([windows, windows.iloc[[0]]]), groups, design, domains, "familiar", "a")


def test_matched_guard_blocks_cached_transfer_and_unfinished_seal(tmp_path, monkeypatch):
    windows, groups, design, domains = identity_fixture()
    episodes = build_matched_episodes(windows, groups, design, domains, "omitted", "a")
    train = episodes[episodes.split == "train"]
    selection = episodes[(episodes.evaluation_partition == "selection") & (episodes.orientation == "forward")]
    val = episodes[episodes.split == "val"]
    store = MatchedStore(tmp_path, windows, train, selection)
    hidden = val[val.evaluation_partition == "transfer"].query_window_id.iloc[0]
    store._cache[hidden] = dict(log_band_power=np.zeros(96))
    monkeypatch.setattr(FeatureStore, "feature", lambda *args: pytest.fail("Hidden target reached cache/loader"))
    with pytest.raises(ValueError, match="whitelist"):
        store.feature(hidden)
    path = tmp_path/"seal.json"
    path.write_text(json.dumps(dict(completed_experiments=["familiar"], encoder_selections=3, baseline_selections=5)))
    with pytest.raises(ValueError, match="All matched selections"):
        store.unlock_scoring(val, path)
    assert store.phase == "fit_selection"


def test_scoring_unlock_never_exposes_omitted_training_transfer(tmp_path):
    windows, groups, design, domains = identity_fixture()
    episodes = build_matched_episodes(windows, groups, design, domains, "omitted", "a")
    train = episodes[episodes.split == "train"]
    selection = episodes[(episodes.evaluation_partition == "selection") & (episodes.orientation == "forward")]
    store = MatchedStore(tmp_path, windows, train, selection)
    path = tmp_path/"seal.json"
    path.write_text(json.dumps(dict(completed_experiments=["familiar", "omitted"], encoder_selections=6, baseline_selections=10)))
    with pytest.raises(ValueError, match="omitted training targets"):
        store.unlock_scoring(train, path)
    store.unlock_scoring(episodes[episodes.split == "val"], path)
    forbidden = windows[(windows.split == "train") & (windows.role == "query") & windows.speed_mm_s.isin([30, 50])]
    assert not set(forbidden.window_id) & store.allowed


def test_wrong_support_preserves_orientation_and_query_ids():
    windows, groups, design, domains = identity_fixture()
    episodes = build_matched_episodes(windows, groups, design, domains, "familiar", "a")
    val = episodes[episodes.split == "val"]
    wrong = wrong_support_by_orientation(val)
    pd.testing.assert_series_equal(wrong.query_window_id, val.query_window_id)
    lookup = windows.set_index("window_id")
    for row in wrong[wrong.protocol == "single"].itertuples():
        support = lookup.loc[json.loads(row.support_window_ids)[0]]
        assert support.surface_id != row.surface_id
        assert support.repeat_id == (0 if row.orientation == "forward" else 1)


def test_reverse_targets_cannot_enter_matched_selection(tmp_path):
    windows, groups, design, domains = identity_fixture()
    episodes = build_matched_episodes(windows, groups, design, domains, "familiar", "a")
    with pytest.raises(ValueError, match="Reverse targets"):
        MatchedStore(tmp_path, windows, episodes[episodes.split == "train"],
            episodes[(episodes.evaluation_partition == "selection") & (episodes.orientation == "reverse")])


def test_training_coverage_does_not_require_unused_reversed_training_supports():
    windows, groups, design, domains = identity_fixture()
    rows = windows[(windows.surface_id == 0) & ((windows.role == "query") | (windows.duration_s == 1.))].copy()
    rows = rows.drop_duplicates(["surface_id", "speed_mm_s", "direction_deg", "nominal_force_N", "repeat_id"])
    rows["available_0.25"] = rows["available_0.5"] = rows["available_1"] = True
    short_unused = (rows.speed_mm_s == 20) & (rows.direction_deg == 0) & (rows.nominal_force_N == .5) & (rows.repeat_id == 1)
    rows.loc[short_unused, "available_1"] = False
    assert training_eligibility(rows, domains, [0]).common_candidate.all()
    rows = rows[~((rows.speed_mm_s == 30) & (rows.direction_deg == 45) & (rows.nominal_force_N == .5) & (rows.repeat_id == 1))]
    result = training_eligibility(rows, domains, [0])
    assert int((~result.common_candidate).sum()) == 3


def test_training_reservation_guard_precedes_source_loading(tmp_path, monkeypatch):
    from tactile_contact import transfer_training
    spec = json.loads(Path("configs/transfer_training_qc_review.json").read_text())
    spec["surface_ids"] = [5]
    monkeypatch.setattr(transfer_training, "load_config", lambda *args: pytest.fail("Reserved request reached source config"))
    with pytest.raises(ValueError, match="reserved test group"):
        training_preflight(spec)


def test_matched_reservation_guard_precedes_coverage_and_feature_access(tmp_path, monkeypatch):
    module_spec = importlib.util.spec_from_file_location("matched_runner", Path("scripts/run_matched_development.py"))
    module = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(module)
    spec = json.loads(Path("configs/matched_fit_review.json").read_text())
    design = json.loads(Path(spec["design"]).read_text()); design["train_ids"] = [5]
    path = tmp_path/"design.json"; path.write_text(json.dumps(design)); spec["design"] = str(path)
    monkeypatch.setattr(module.np, "load", lambda *args: pytest.fail("Reserved request reached feature arrays"))
    with pytest.raises(ValueError, match="reserved test group"):
        module.preflight(spec)


def test_matched_finite_training_saves_both_selection_histories(prepared, tmp_path, monkeypatch):
    from tactile_contact import matched
    root, cfg, windows, episodes, original, scaler, train, val = prepared
    cfg = dict(cfg, training=dict(cfg["training"], epochs=120, patience=10))
    train, val = train.assign(orientation="forward"), val.assign(orientation="forward")
    store = MatchedStore(root, windows, train, val)
    monkeypatch.setattr(matched, "validation_objective", lambda *args: 1.)
    _, selection = fit_matched(tmp_path/"fit", cfg, train, val, store, scaler, 0)
    assert selection["epochs_run"] == 11 and selection["selected_epoch"] == 1
    history = pd.read_csv(tmp_path/"fit/history.csv")
    assert history.validation_primary_mae.notna().all() and history.validation_equal_cell_mae.eq(1).all()
    with pytest.raises(ValueError, match="overwrite"):
        fit_matched(tmp_path/"fit", cfg, train, val, store, scaler, 0)
