"""Metadata-only grouping, reservation and query-domain preflight.

This does not load sensor values or implement scientific test scoring.
"""
import hashlib
from itertools import product

import pandas as pd

from .config import FORBIDDEN, OMITTED_SPEEDS, speed_bracket


def reviewed_groups(metadata, rules):
    if metadata.surface_id.duplicated().any():
        raise ValueError("Metadata contains duplicate specimen IDs")
    ids = set(metadata.surface_id)
    assigned = {}
    names = set()
    for group in rules["groups"]:
        if not group["name"] or group["name"] in names:
            raise ValueError("Review needs unique nonempty group names")
        names.add(group["name"])
        if not group["ids"] or not set(group["ids"]).issubset(ids):
            raise ValueError("Review group has unknown or missing specimens")
        for surface in group["ids"]:
            if surface in assigned:
                raise ValueError("Specimen assigned to multiple groups")
            assigned[surface] = group
    rows = []
    for row in metadata.to_dict("records"):
        surface = row["surface_id"]
        group = assigned.get(surface)
        rows.append(dict(row, family_group=group["name"] if group else f"specimen_{surface}",
            grouping_reason=group["reason"] if group else rules["default_reason"],
            grouping_reviewed=True, grouping_scope=rules["grouping_scope"],
            manufacturing_relationships="unknown", review_note=rules.get("notes", {}).get(str(surface), "")))
    return pd.DataFrame(rows)


def reserve_groups(groups, exposed_ids, targets, seed):
    """Select complete groups with exact metadata-category quotas, never scores."""
    if not set(exposed_ids).issubset(set(groups.surface_id)):
        raise ValueError("Exposure ledger contains unknown specimens")
    categories = list(targets)
    target = tuple(targets[c] for c in categories)
    exposed_groups = set(groups.loc[groups.surface_id.isin(exposed_ids), "family_group"])
    candidates = [(name, frame) for name, frame in groups.groupby("family_group") if name not in exposed_groups]
    candidates.sort(key=lambda pair: hashlib.sha256(f"{seed}|{pair[0]}".encode()).hexdigest())
    states = {(0,)*len(categories): ()}
    for name, frame in candidates:
        if not set(frame.category).issubset(categories):
            raise ValueError("Reservation quota omits a candidate category")
        count = tuple(int((frame.category == c).sum()) for c in categories)
        if any(n > cap for n, cap in zip(count, target)):
            continue
        additions = {}
        for state, selection in states.items():
            following = tuple(a+b for a, b in zip(state, count))
            if any(n > cap for n, cap in zip(following, target)):
                continue
            if following not in states and following not in additions:
                additions[following] = selection+(name,)
        states.update(additions)
        if target in states:
            selected = groups[groups.family_group.isin(states[target])].copy()
            return selected.sort_values("surface_id").reset_index(drop=True)
    raise ValueError("Cannot meet exact category targets without breaking groups/exposure rules")


def validate_reservation(groups, reservation, exposed_ids):
    if not set(exposed_ids).issubset(set(groups.surface_id)):
        raise ValueError("Exposure ledger contains unknown specimens")
    if reservation.empty or reservation.surface_id.duplicated().any():
        raise ValueError("Reservation needs unique nonempty specimens")
    if not set(reservation.surface_id).issubset(set(groups.surface_id)):
        raise ValueError("Reservation includes unknown specimens")
    actual = groups[groups.surface_id.isin(reservation.surface_id)]
    expected = groups[groups.family_group.isin(actual.family_group)]
    if set(expected.surface_id) != set(reservation.surface_id):
        raise ValueError("Reservation splits a reviewed group")
    exposed_groups = set(groups.loc[groups.surface_id.isin(exposed_ids), "family_group"])
    if set(actual.family_group) & exposed_groups:
        raise ValueError("Reservation contains a development-exposed group")
    labels = actual.set_index("surface_id").family_group
    if any(row.family_group != labels.loc[row.surface_id] for row in reservation.itertuples()):
        raise ValueError("Reservation group labels disagree with reviewed metadata")


def validate_development_access(surface_ids, groups, reservation, exposed_ids):
    validate_reservation(groups, reservation, exposed_ids)
    requested = set(surface_ids)
    if not requested.issubset(set(groups.surface_id)):
        raise ValueError("Development selection includes unreviewed specimens")
    reserved_groups = set(reservation.family_group)
    requested_groups = set(groups.loc[groups.surface_id.isin(requested), "family_group"])
    if requested_groups & reserved_groups:
        raise ValueError("Development selection would expose a reserved test group")


def query_domains():
    rows = []
    for speed, direction, force in product([20, 30, 40, 50, 60], range(0, 360, 45), [.5, 1.]):
        condition = (speed, direction, force)
        support = condition in FORBIDDEN
        omitted = speed in OMITTED_SPEEDS
        endpoints = speed_bracket(speed) if omitted else ()
        blocked = [endpoint for endpoint in endpoints if (endpoint, direction, force) in FORBIDDEN]
        transfer = omitted and not blocked
        known_query = not omitted and not support
        rows.append(dict(speed_mm_s=speed, direction_deg=direction, nominal_force_N=force,
            support_condition=support, familiar_query=not support, known_speed_query=known_query,
            omitted_candidate=omitted, omitted_transfer=transfer,
            matched_familiar_fit_query=known_query or transfer,
            matched_comparison_query=transfer, lower_endpoint_mm_s=endpoints[0] if endpoints else 0,
            upper_endpoint_mm_s=endpoints[1] if endpoints else 0,
            omitted_exclusion_reason="endpoint is an excluded support condition" if blocked else "",
            blocked_endpoints_mm_s="|".join(map(str, blocked))))
    return pd.DataFrame(rows)
