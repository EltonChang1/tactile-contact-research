import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tactile_contact.development_diagnostics import (
    floor_sensitivity, history_diagnostic, repeat_metrics, validate_review_records,
)


def paired_records():
    return pd.DataFrame([
        dict(surface_id=7, speed_mm_s=40, direction_deg=45, nominal_force_N=1., repeat_id=1),
        dict(surface_id=7, speed_mm_s=40, direction_deg=45, nominal_force_N=1., repeat_id=0),
    ])


def test_repeat_difference_has_log_units_and_symmetric_rms():
    records = paired_records()
    powers = np.stack([np.full((32, 3), 100.), np.full((32, 3), 10.)])
    pairs, differences = repeat_metrics(records, powers, 1e-10)
    np.testing.assert_allclose(differences, 1., atol=1e-10)
    assert pairs.repeat_log_mae.iloc[0] == pytest.approx(1.)
    assert pairs.repeat_rms_symmetric_relative_difference.iloc[0] == pytest.approx(2*(np.sqrt(10)-1)/(np.sqrt(10)+1))
    swapped, _ = repeat_metrics(records.assign(repeat_id=[0, 1]), powers, 1e-10)
    pd.testing.assert_frame_equal(pairs, swapped)


def test_repeat_pair_requires_distinct_complete_recordings():
    records = paired_records()
    with pytest.raises(ValueError, match="two distinct repeats"):
        repeat_metrics(records.iloc[:1], np.ones((1, 32, 3)), 1e-10)
    with pytest.raises(ValueError, match="Duplicate"):
        repeat_metrics(records.assign(repeat_id=0), np.ones((2, 32, 3)), 1e-10)


def test_zero_power_floor_effect_is_two_decades_and_finite():
    result = floor_sensitivity(np.zeros((2, 32, 3)), [1e-12, 1e-10, 1e-8], 1e-10)
    assert (result.below_floor_fraction == 1).all()
    np.testing.assert_allclose(result[result.floor != 1e-10].mean_log_change, 2.)
    assert (result[result.floor == 1e-10].maximum_log_change == 0).all()
    pairs, _ = repeat_metrics(paired_records(), np.zeros((2, 32, 3)), 1e-10)
    assert pairs.repeat_log_mae.iloc[0] == 0
    assert pairs.repeat_rms_symmetric_relative_difference.iloc[0] == 0


def test_floor_check_rejects_nonphysical_power_and_invalid_floor():
    with pytest.raises(ValueError):
        floor_sensitivity(np.full((2, 32, 3), -1.), [1e-8], 1e-10)
    with pytest.raises(ValueError):
        floor_sensitivity(np.ones((2, 32, 3)), [0.], 1e-10)
    result = floor_sensitivity(np.ones((2, 32, 3)), [1e-8], 1e-10)
    assert (result.below_floor_fraction == 0).all()
    assert result.maximum_log_change.max() < 5e-9


def test_full_training_domain_cannot_be_replaced_or_duplicated():
    records = paired_records().assign(qc_status="valid", half_second_available=True)
    domains = records.iloc[:1].drop(columns=["surface_id", "repeat_id", "qc_status", "half_second_available"]).assign(
        support_condition=False, known_speed_query=True)
    validate_review_records(records, [7], domains)
    for altered in [records.assign(surface_id=8), records.iloc[:1], pd.concat([records, records.iloc[:1]])]:
        with pytest.raises(ValueError, match="every permitted training repeat"):
            validate_review_records(altered, [7], domains)
    forged = records.assign(recording_id=["8_45_40_1000_1", "7_45_40_1000_0"])
    with pytest.raises(ValueError, match="identity disagrees"):
        validate_review_records(forged, [7], domains)


def test_runner_rejects_reserved_selection_before_source_or_signal_access(tmp_path, monkeypatch):
    path = Path("scripts/review_development_diagnostics.py")
    module_spec = importlib.util.spec_from_file_location("review_diagnostics", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    coverage = json.loads(Path("configs/wider_qc_review.json").read_text())
    coverage["surface_ids"] = [5]  # Entirely reserved; no sensor/source read may follow.
    coverage_path = tmp_path/"coverage.json"
    coverage_path.write_text(json.dumps(coverage))
    review = json.loads(Path("configs/development_diagnostics.json").read_text())
    review["coverage_review"] = str(coverage_path)
    review_path = tmp_path/"review.json"
    review_path.write_text(json.dumps(review))
    def forbidden(*args, **kwargs):
        pytest.fail("Source or sensor access occurred before reservation preflight")
    monkeypatch.setattr(module, "load_config", forbidden)
    monkeypatch.setattr(module, "load_record", forbidden)
    with pytest.raises(ValueError, match="reserved test group"):
        module.run(review_path)


def test_history_flags_cap_and_missing_primary_without_claiming_convergence():
    history = pd.DataFrame(dict(epoch=np.arange(1, 61), validation_equal_cell_mae=np.linspace(.8, .2, 60)))
    result = history_diagnostic(history, 60, 60, 10)
    assert result["reached_cap"] and result["selected_within_tail"]
    assert not result["primary_history_available"]
    assert result["tail_best_improvement"] == pytest.approx(history.validation_equal_cell_mae.iloc[49]-.2)
    with pytest.raises(ValueError, match="disagrees"):
        history_diagnostic(history, 60, 59, 10)
    with pytest.raises(ValueError, match="Invalid epoch"):
        history_diagnostic(history.assign(epoch=np.arange(2, 62)), 60, 60, 10)


def test_early_stop_can_be_reported_without_assuming_missing_epochs():
    history = pd.DataFrame(dict(epoch=[1, 2, 3, 4], validation_equal_cell_mae=[.5, .3, .4, .45]))
    result = history_diagnostic(history, 60, 2, 2)
    assert not result["reached_cap"]
    assert result["epochs_run"] == 4 and result["tail_best_improvement"] == 0
