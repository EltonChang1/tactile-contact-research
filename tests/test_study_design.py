import pandas as pd
import pytest

from tactile_contact.config import FORBIDDEN
from tactile_contact.study_design import (reviewed_groups, reserve_groups, validate_reservation,
                                          validate_development_access, query_domains)


def fixture_groups():
    return pd.DataFrame({"surface_id": [0, 1, 2, 3, 4, 5], "category": ["A", "A", "A", "B", "A", "B"],
                         "family_group": ["exposed", "exposed", "cross_category", "cross_category", "fresh_A", "fresh_B"]})


def test_reservation_is_deterministic_complete_group_and_exposure_aware():
    groups = fixture_groups()
    first = reserve_groups(groups, [0], {"A": 2, "B": 1}, 42)
    second = reserve_groups(groups.iloc[::-1], [0], {"A": 2, "B": 1}, 42)
    assert first.surface_id.tolist() == second.surface_id.tolist() == [2, 3, 4]
    validate_reservation(groups, first, [0])


def test_impossible_quotas_do_not_split_a_group_or_promote_exposed_relative():
    groups = fixture_groups().iloc[:4]
    with pytest.raises(ValueError, match="Cannot meet"):
        reserve_groups(groups, [0], {"A": 1, "B": 0}, 42)
    with pytest.raises(ValueError, match="exposed group"):
        validate_reservation(fixture_groups(), fixture_groups().iloc[:2], [0])
    with pytest.raises(ValueError, match="splits"):
        validate_reservation(fixture_groups(), fixture_groups().iloc[[2]], [0])


def test_development_preflight_rejects_reserved_and_unknown_specimens():
    groups = fixture_groups()
    reservation = groups.iloc[[2, 3]]
    validate_development_access([0, 1, 4], groups, reservation, [0])
    with pytest.raises(ValueError, match="reserved"):
        validate_development_access([0, 3], groups, reservation, [0])
    with pytest.raises(ValueError, match="unreviewed"):
        validate_development_access([99], groups, reservation, [0])
    with pytest.raises(ValueError, match="Exposure ledger"):
        validate_reservation(groups, reservation, [99])


def test_reservation_cannot_forge_group_labels():
    groups = fixture_groups()
    forged = groups.iloc[[2, 3]].copy()
    forged["family_group"] = "fake"
    with pytest.raises(ValueError, match="labels disagree"):
        validate_reservation(groups, forged, [0])


def test_metadata_review_does_not_silently_merge_or_repeat_assignments():
    metadata = pd.DataFrame({"surface_id": [0, 1, 2], "name": ["foo", "bar", "baz"], "category": ["A"]*3})
    rules = {"groups": [{"name": "paired", "ids": [0, 1], "reason": "declared"}],
             "default_reason": "unknown", "grouping_scope": "metadata_names_only"}
    result = reviewed_groups(metadata, rules)
    assert result.family_group.tolist() == ["paired", "paired", "specimen_2"]
    assert set(result.manufacturing_relationships) == {"unknown"}
    with pytest.raises(ValueError, match="multiple"):
        reviewed_groups(metadata, dict(rules, groups=rules["groups"]+[{"name": "other", "ids": [1], "reason": "bad"}]))
    with pytest.raises(ValueError, match="unique"):
        reviewed_groups(metadata, dict(rules, groups=rules["groups"]+[{"name": "paired", "ids": [2], "reason": "bad"}]))


def test_domain_masks_and_matched_comparator_exclude_observed_endpoints():
    domains = query_domains()
    assert len(domains) == 80
    assert domains.support_condition.sum() == 4
    assert domains.familiar_query.sum() == 76
    assert domains.known_speed_query.sum() == 44
    assert domains.omitted_candidate.sum() == 32
    assert domains.omitted_transfer.sum() == 26
    assert domains.matched_familiar_fit_query.sum() == 70
    assert ((domains.known_speed_query | domains.omitted_transfer) == domains.matched_familiar_fit_query).all()
    known = set(domains.loc[domains.known_speed_query, ["speed_mm_s", "direction_deg", "nominal_force_N"]].itertuples(index=False, name=None))
    transfer = domains[domains.omitted_transfer]
    for row in transfer.itertuples():
        assert (row.lower_endpoint_mm_s, row.direction_deg, row.nominal_force_N) in known
        assert (row.upper_endpoint_mm_s, row.direction_deg, row.nominal_force_N) in known
        assert (row.speed_mm_s, row.direction_deg, row.nominal_force_N) not in FORBIDDEN
    blocked = domains[domains.omitted_candidate & ~domains.omitted_transfer]
    assert len(blocked) == 6
    assert set(zip(blocked.direction_deg, blocked.nominal_force_N)) == {(0, .5), (0, 1.), (90, .5)}
