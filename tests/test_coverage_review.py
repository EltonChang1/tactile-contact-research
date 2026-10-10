import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tactile_contact import coverage_review
from tactile_contact.config import file_hash
from tactile_contact.coverage_review import canonical_availability, common_eligibility, preflight, stage_cached_raw


def coverage_fixture():
    rows = []
    for speed, direction, force in [(40, 0, .5), (20, 0, .5), (40, 0, 1.), (40, 90, .5), (60, 45, 1.)]:
        for repeat in [0, 1]:
            rows.append(dict(surface_id=10, speed_mm_s=speed, direction_deg=direction, nominal_force_N=force,
                repeat_id=repeat, **{f"available_{d:g}": True for d in [.25, .5, 1.]}))
    domains = pd.DataFrame([dict(speed_mm_s=60, direction_deg=45, nominal_force_N=1., known_speed_query=True, omitted_transfer=False)])
    return pd.DataFrame(rows), domains


def test_canonical_availability_does_not_overcredit_interval_length():
    start, available = canonical_availability(np.array([0., .0001, .0002]), .0001, .5001, 6000)
    assert start == 1/6000
    assert available[.25] and not available[.5]
    _, available = canonical_availability(np.array([0., .0001, .0002]), .0001, start+.5, 6000)
    assert available[.5] and not available[1.]


def test_complete_common_coverage_retains_all_three_budgets():
    records, domains = coverage_fixture()
    common = common_eligibility(records, domains, [10])
    assert len(common) == 3 and common.common_candidate.all()
    assert common.support_duration_logged_s.tolist() == [.25, .5, 1.]


def test_short_reversed_support_blocks_only_long_budget():
    records, domains = coverage_fixture()
    row = (records.speed_mm_s == 20) & (records.direction_deg == 0) & (records.repeat_id == 1)
    records.loc[row, "available_1"] = False
    common = common_eligibility(records, domains, [10])
    assert common.common_candidate.tolist() == [True, True, False]
    assert common.both_query_repeats_available.all()
    assert "20:0:0.5:1" in common.missing_supports.iloc[-1]


def test_missing_query_repeat_stays_in_denominator_and_duplicates_fail():
    records, domains = coverage_fixture()
    common = common_eligibility(records.iloc[:-1], domains, [10])
    assert len(common) == 3 and not common.common_candidate.any()
    assert common.missing_query_repeats.eq("1").all()
    with pytest.raises(ValueError, match="Duplicate"):
        common_eligibility(pd.concat([records, records.iloc[[0]]]), domains, [10])


def test_reservation_guard_precedes_configuration_or_signal_access(tmp_path, monkeypatch):
    groups = pd.DataFrame(dict(surface_id=[0, 1, 2], family_group=["development", "reserved", "reserved"]))
    groups.to_csv(tmp_path/"groups.csv", index=False)
    groups.iloc[1:].to_csv(tmp_path/"reservation.csv", index=False)
    (tmp_path/"exposure.json").write_text(json.dumps(dict(training_surface_ids=[0], selection_surface_ids=[])))
    spec = dict(group_manifest=str(tmp_path/"groups.csv"), reservation_manifest=str(tmp_path/"reservation.csv"),
        exposure_snapshot=str(tmp_path/"exposure.json"), surface_ids=[2], source_config="must-not-open")
    def forbidden(*args):
        pytest.fail("Reserved request reached configuration/raw preparation")
    monkeypatch.setattr(coverage_review, "load_config", forbidden)
    with pytest.raises(ValueError, match="reserved test group"):
        preflight(spec)


def make_cache(tmp_path):
    shared = tmp_path/"shared"
    (shared/"data").mkdir(parents=True)
    cfg = dict(source_kind="cluster", revision="b"*40, repo_id="example/pinned")
    (shared/"data/source.json").write_text(json.dumps(dict(cfg, selected_surface_ids=[10, 99])))
    files = []
    for surface in [10, 99]:
        relative = f"sensor_data/accel/{surface}/{surface}_0_40_500_0.parquet"
        path = shared/"data/raw/cluster"/relative
        path.parent.mkdir(parents=True)
        path.write_bytes(b"approved" if surface == 10 else b"unrequested")
        files.append(dict(path=relative, bytes=path.stat().st_size, sha256=file_hash(path)))
    (shared/"data/raw_inventory.json").write_text(json.dumps(dict(revision=cfg["revision"], files=files)))
    return shared, cfg


def test_isolated_staging_copies_only_approved_files_and_preserves_shared_bytes(tmp_path):
    shared, cfg = make_cache(tmp_path)
    before = {p: p.read_bytes() for p in [shared/"data/source.json", shared/"data/raw_inventory.json"]}
    output = tmp_path/"output"
    assert stage_cached_raw(output, cfg, [10], [(40, 0, .5)], shared) == 1
    copied = list((output/"data/raw/cluster").rglob("*.parquet"))
    assert len(copied) == 1 and copied[0].read_bytes() == b"approved"
    assert all(p.read_bytes() == values for p, values in before.items())
    assert stage_cached_raw(output, cfg, [10], [(40, 0, .5)], shared) == 0


def test_staging_rejects_changed_pinned_cache(tmp_path):
    shared, cfg = make_cache(tmp_path)
    path = shared/"data/raw/cluster/sensor_data/accel/10/10_0_40_500_0.parquet"
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Shared pinned cache changed"):
        stage_cached_raw(tmp_path/"output", cfg, [10], [(40, 0, .5)], shared)


def test_review_rejects_changed_denominator_or_unsafe_domain(tmp_path):
    spec = json.loads(Path("configs/selection_transfer_qc_review.json").read_text())
    with pytest.raises(ValueError, match="denominator"):
        preflight(dict(spec, expected_recording_triplets=300))
    domains = pd.read_csv(spec["domain_table"])
    forbidden = (domains.speed_mm_s == 30) & (domains.direction_deg == 0) & (domains.nominal_force_N == .5)
    domains.loc[forbidden, "omitted_transfer"] = True
    altered = tmp_path/"unsafe.csv"
    domains.to_csv(altered, index=False)
    with pytest.raises(AssertionError):
        preflight(dict(spec, domain_table=str(altered)))
