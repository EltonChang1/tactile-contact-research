"""Repeat context and numerical feature checks; no model selection or sensor calibration."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .records import parse_record_name


KEYS = ["surface_id", "speed_mm_s", "direction_deg", "nominal_force_N"]


def validate_review_records(records, surface_ids, domains):
    """Reject incomplete/duplicate/unapproved cells before any signal is read."""
    permitted = domains[domains.support_condition | domains.known_speed_query]
    conditions = set(permitted[KEYS[1:]].itertuples(index=False, name=None))
    expected = {(s, *c, r) for s in surface_ids for c in conditions for r in [0, 1]}
    keys = records[KEYS+["repeat_id"]]
    actual = set(keys.itertuples(index=False, name=None))
    if keys.duplicated().any() or actual != expected:
        raise ValueError("Diagnostic records must contain every permitted training repeat exactly once")
    if not (records.qc_status == "valid").all() or not records.half_second_available.all():
        raise ValueError("Review requires the complete previously audited half-second cohort")
    if "recording_id" in records:
        for row in records.to_dict("records"):
            identity = parse_record_name(row["recording_id"]+".parquet")
            if any(identity[k] != row[k] for k in KEYS+["repeat_id"]):
                raise ValueError("QC recording identity disagrees with permitted condition columns")


def repeat_metrics(records, powers, floor):
    """One symmetric observation per pair, without treating axes/bands as trials."""
    powers = np.asarray(powers, dtype=float)
    if powers.shape != (len(records), 32, 3) or not np.isfinite(powers).all() or (powers < 0).any():
        raise ValueError("Expected finite nonnegative 32-band three-axis powers")
    if not np.isfinite(floor) or floor <= 0:
        raise ValueError("Require a positive finite floor")
    if records[KEYS+["repeat_id"]].duplicated().any() or not set(records.repeat_id).issubset({0, 1}):
        raise ValueError("Duplicate or invalid repeat labels")
    groups = records.reset_index(drop=True).groupby(KEYS, sort=True).indices
    rows, differences = [], []
    for key, indices in groups.items():
        if len(indices) != 2 or set(records.iloc[indices].repeat_id) != {0, 1}:
            raise ValueError("Every condition requires two distinct repeats")
        ordered = sorted(indices, key=lambda i: records.iloc[i].repeat_id)
        a, b = powers[ordered]
        difference = np.abs(np.log10(a+floor)-np.log10(b+floor))
        rms = np.sqrt(powers[ordered].sum(axis=(1, 2)))
        symmetric = 0. if rms.sum() == 0 else 2*abs(rms[0]-rms[1])/rms.sum()
        row = dict(zip(KEYS, key), repeat_log_mae=float(difference.mean()),
                   repeat_rms_symmetric_relative_difference=float(symmetric))
        for axis, label in enumerate("XYZ"):
            row[f"repeat_log_mae_{label}"] = float(difference[:, axis].mean())
        rows.append(row)
        differences.append(difference)
    return pd.DataFrame(rows), np.stack(differences)


def floor_sensitivity(powers, floors, reference):
    powers = np.asarray(powers, dtype=float)
    if powers.ndim != 3 or powers.shape[1:] != (32, 3) or not np.isfinite(powers).all() or (powers < 0).any():
        raise ValueError("Invalid power array")
    if not np.isfinite([reference, *floors]).all() or min(reference, *floors) <= 0:
        raise ValueError("Require positive finite floors")
    base = np.log10(powers+reference)
    rows = []
    for floor in floors:
        for axis, label in enumerate("XYZ"):
            values = powers[:, :, axis]
            change = np.abs(np.log10(values+floor)-base[:, :, axis])
            rows.append(dict(floor=floor, axis=label, feature_values=values.size,
                at_or_below_floor=int((values <= floor).sum()), below_floor_fraction=float((values <= floor).mean()),
                minimum_power=float(values.min()), p05_power=float(np.quantile(values, .05)),
                median_power=float(np.median(values)), mean_log_change=float(change.mean()), maximum_log_change=float(change.max())))
    return pd.DataFrame(rows)


def history_diagnostic(history, cap, selected_epoch, tail_epochs):
    """Quantify saved equal-cell selection history, without inferring missing primary history."""
    epochs = history.epoch.to_numpy()
    scores = history.validation_equal_cell_mae.to_numpy(dtype=float)
    if len(epochs) < 1 or not np.array_equal(epochs, np.arange(1, len(epochs)+1)) or not np.isfinite(scores).all() or (scores < 0).any():
        raise ValueError("Invalid epoch history")
    if cap < len(epochs) or tail_epochs < 1 or selected_epoch != int(epochs[np.argmin(scores)]):
        raise ValueError("Checkpoint selection/cap disagrees with history")
    cutoff = max(1, len(epochs)-tail_epochs)
    previous = float(scores[:cutoff].min())
    best = float(scores.min())
    return dict(epochs_run=len(epochs), epoch_cap=cap, selected_epoch=selected_epoch,
        reached_cap=len(epochs) == cap, best_equal_cell_mae=best,
        best_before_tail_mae=previous, tail_best_improvement=previous-best,
        tail_relative_improvement=0. if previous == 0 else (previous-best)/previous,
        selected_within_tail=selected_epoch > cutoff,
        primary_history_available="validation_primary_mae" in history.columns)
