"""Frozen-model repetition sensitivity; no fitting or checkpoint selection."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from .baselines import ConditionsOnly, CopySpectrum, FixedFeatures, Retrieval, SpeedRescaling
from .config import digest
from .episodes import FeatureStore


def response_key(label):
    surface, speed, direction, force = label.split("_")
    return int(surface), int(speed), int(direction), float(force)


def restore_baselines(root, interpolate_speeds=False):
    """Restore persisted coefficients and library; never access training targets."""
    root = Path(root)
    methods = {"conditions_only": ConditionsOnly(), "copy": CopySpectrum(),
               "fixed_features": FixedFeatures(), "speed_rescaling": SpeedRescaling(),
               "retrieval": Retrieval(interpolate_speeds=interpolate_speeds)}
    for name in ["conditions_only", "fixed_features"]:
        with np.load(root/f"{name}_fit.npz") as data:
            model = methods[name]
            model.regression = Ridge()
            model.regression.coef_ = data["coefficient"].copy()
            model.regression.intercept_ = data["intercept"].copy()
            model.regression.n_features_in_ = model.regression.coef_.shape[1]
            if name == "fixed_features":
                model.mean, model.std = data["feature_mean"].copy(), data["feature_std"].copy()
    values = json.loads((root/"speed_rescaling_fit.json").read_text())
    methods["speed_rescaling"].exponents = np.array([values["p"], values["b"]])
    retrieval = methods["retrieval"]
    sources = json.loads((root/"retrieval_sources.json").read_text())
    retrieval.library, retrieval.library_sources = {}, {}
    retrieval.responses, retrieval.response_sources = {}, {}
    with np.load(root/"retrieval_fit.npz") as data:
        for label, provenance in sources["library"].items():
            protocol, duration = label.rsplit("_", 1)
            key = protocol, float(duration)
            retrieval.library[key] = data[f"fingerprints_{label}"].copy(), data[f"training_ids_{label}"].copy()
            retrieval.library_sources[key] = provenance
        for label, provenance in sources["responses"].items():
            key = response_key(label)
            retrieval.responses[key] = data[f"response_{label}"].copy()
            retrieval.response_sources[key] = provenance
    return methods


def reversed_requests(episodes, windows):
    """Specify complementary recordings without signal/target access.

    Repeat control keeps its two existing supports in canonical order. Other
    protocols swap support repeat 0 to 1; every query swaps repeat 1 to 0.
    """
    indexed = windows.set_index("window_id")
    requests, plans = {}, []
    for row in episodes.itertuples():
        if row.split != "val" or row.query_repeat_id != 1:
            raise ValueError("Reversal requires unchanged validation repeat-1 queries")
        support_keys = []
        for window_id in json.loads(row.support_window_ids):
            window = indexed.loc[window_id]
            if window.role != "support" or window.surface_id != row.surface_id:
                raise ValueError("Support role/specimen mismatch")
            repeat = int(window.repeat_id) if row.protocol == "repeat" else 1-int(window.repeat_id)
            key = (int(window.surface_id), int(window.speed_mm_s), int(window.direction_deg),
                   float(window.nominal_force_N), repeat, "support", float(window.duration_s))
            requests[key] = key
            support_keys.append(key)
        query = indexed.loc[row.query_window_id]
        if query.role != "query" or query.surface_id != row.surface_id or query.repeat_id != 1:
            raise ValueError("Query role/specimen/repetition mismatch")
        key = (int(query.surface_id), int(query.speed_mm_s), int(query.direction_deg),
               float(query.nominal_force_N), 0, "query", float(query.duration_s))
        requests[key] = key
        plans.append((support_keys, key))
    return sorted(requests), plans


def build_reversed_episodes(episodes, plans, window_lookup):
    if len(episodes) != len(plans):
        raise ValueError("Incomplete matched repetition plans")
    reverse = episodes.copy()
    for index, (supports, query) in zip(reverse.index, plans):
        if any(k not in window_lookup for k in supports+[query]):
            raise ValueError("Missing complementary window; never silently drop a cell")
        support_ids = [window_lookup[k] for k in supports]
        query_id = window_lookup[query]
        reverse.at[index, "support_window_ids"] = json.dumps(support_ids)
        reverse.at[index, "query_window_id"] = query_id
        reverse.at[index, "query_repeat_id"] = 0
        reverse.at[index, "episode_id"] = digest(["reversed", episodes.at[index, "episode_id"], support_ids, query_id])[:20]
    reverse["matched_forward_episode_id"] = episodes.episode_id.to_numpy()
    return reverse


class FrozenScoringStore(FeatureStore):
    """During prediction, reject query features even when already cached."""
    def __init__(self, root, windows, episodes):
        super().__init__(root, windows)
        self.supports = {w for encoded in episodes.support_window_ids for w in json.loads(encoded)}
        self.query_ids = set(episodes.query_window_id)
        if any(self.windows.loc[w, "role"] != "support" for w in self.supports):
            raise ValueError("Only support windows may enter predictor inputs")
        if any(self.windows.loc[w, "role"] != "query" for w in self.query_ids):
            raise ValueError("Only query windows may provide scoring targets")
        self.allowed = set(self.supports)
        self.phase = "prediction"
        self.accesses = set()

    def feature(self, window_id):
        if window_id not in self.allowed:
            raise ValueError("Query target access before frozen predictions are complete")
        self.accesses.add((self.phase, window_id))
        return super().feature(window_id)

    def unlock_targets(self):
        self.allowed |= self.query_ids
        self.phase = "scoring"


def aggregate_scores(scores):
    metrics = ["log_power_mae", "modeled_band_total_rms_error"]
    keys = ["experiment", "evaluation_partition", "orientation", "model", "protocol", "duration_s",
            "surface_id", "family_group"]
    # Average queries within seed/specimen first, then seeds, then specimens.
    by_seed = scores.groupby(keys+["seed"], as_index=False)[metrics].mean()
    per_surface = by_seed.groupby(keys, as_index=False)[metrics].mean()
    summary = per_surface.groupby(keys[:-2], as_index=False)[metrics].mean()
    summary["surfaces"] = per_surface.groupby(keys[:-2]).surface_id.nunique().to_numpy()
    conditions = ["query_speed_mm_s", "query_direction_deg", "query_nominal_force_N"]
    residuals = scores.groupby(keys+conditions+["seed"], as_index=False)[metrics].mean()
    residuals = residuals.groupby(keys+conditions, as_index=False)[metrics].mean()
    return per_surface, summary, residuals
