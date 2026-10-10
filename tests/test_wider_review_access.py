import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd
import pytest


def test_wider_review_rejects_reserved_group_before_download_or_source_loading(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1]/"scripts/review_wider_coverage.py"
    spec = importlib.util.spec_from_file_location("wider_review_for_test", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    groups = pd.DataFrame({"surface_id": [0, 1, 2], "family_group": ["development", "reserved", "reserved"]})
    group_path, reservation_path, exposure_path, review_path = [tmp_path/name for name in ["groups.csv", "reserved.csv", "exposure.json", "review.json"]]
    groups.to_csv(group_path, index=False)
    groups.iloc[[1, 2]].to_csv(reservation_path, index=False)
    exposure_path.write_text(json.dumps({"training_surface_ids": [0], "selection_surface_ids": []}))
    review_path.write_text(json.dumps({"group_manifest": str(group_path), "reservation_manifest": str(reservation_path),
        "exposure_snapshot": str(exposure_path), "surface_ids": [0, 2]}))
    def prohibited(*args, **kwargs):
        raise AssertionError("Reserved request must fail before source loading or network download")
    monkeypatch.setattr(module, "download_cluster", prohibited)
    monkeypatch.setattr(module, "load_config", prohibited)
    monkeypatch.setattr(sys, "argv", [str(script), "--review", str(review_path), "--download"])
    with pytest.raises(ValueError, match="reserved"):
        module.main()


def test_common_coverage_requires_all_long_supports_and_both_query_repeats():
    script = Path(__file__).resolve().parents[1]/"scripts/summarize_wider_coverage.py"
    spec = importlib.util.spec_from_file_location("wider_summary_for_test", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from tactile_contact.config import PROTOCOLS
    rows = []
    for speed, direction, force, repeat in {tuple(c) for protocol in PROTOCOLS.values() for c in protocol}:
        rows.append(dict(surface_id=0, speed_mm_s=speed, direction_deg=direction, nominal_force_N=force,
            repeat_id=repeat, half_second_available=True, one_second_available=True))
    rows += [dict(surface_id=0, speed_mm_s=60, direction_deg=45, nominal_force_N=1., repeat_id=repeat,
                  half_second_available=True, one_second_available=False) for repeat in [0, 1]]
    domains = pd.DataFrame([dict(speed_mm_s=60, direction_deg=45, nominal_force_N=1., known_speed_query=True)])
    good = pd.DataFrame(rows)
    assert module.common_known_eligibility(good, domains).common_candidate.all()
    missing_repeat = good.iloc[:-1]
    assert not module.common_known_eligibility(missing_repeat, domains).common_candidate.any()
    short_support = good.copy()
    short_support.loc[0, "one_second_available"] = False
    result = module.common_known_eligibility(short_support, domains)
    assert not result.common_candidate.any() and result.both_query_repeats_half_second.all()
