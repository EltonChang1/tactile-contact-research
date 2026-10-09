from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd

from .config import PROTOCOLS, FORBIDDEN, digest, write_json
from .signal import condition_vector


def build_episodes(root, cfg, windows):
    root = Path(root)
    surfaces = pd.read_csv(root/"data/manifests/surfaces.csv").set_index("surface_id")
    supports = windows[windows.role == "support"]
    queries = windows[windows.role == "query"]
    lookup = {(r.surface_id,r.speed_mm_s,r.direction_deg,r.nominal_force_N,r.repeat_id,r.duration_s):r.window_id
              for r in supports.itertuples()}
    if len(lookup) != len(supports):
        raise ValueError("Duplicate support key")
    eligible = []
    cohort = []
    for surface in cfg["train_ids"] + cfg["val_ids"]:
        required = [(surface,*c,d) for p in cfg["protocols"] for c in PROTOCOLS[p] for d in cfg["durations_s"]]
        missing = [key for key in required if key not in lookup]
        eligible.append({"surface_id":surface,"eligible":not missing,"reason":f"{len(missing)} required support windows missing" if missing else ""})
        if not missing:
            cohort.append(surface)
    pd.DataFrame(eligible).to_csv(root/"data/manifests/eligibility.csv",index=False)
    if len(set(cohort) & set(cfg["train_ids"])) < 2 or not set(cohort) & set(cfg["val_ids"]):
        raise ValueError("Need at least two eligible training surfaces and one validation surface")
    # Require every training response repeat for retrieval's linear-power averaging.
    common = None
    for surface in cohort:
        q = queries[queries.surface_id == surface]
        required_repeats = [0,1] if surface in cfg["train_ids"] else [1]
        condition_set = None
        for repeat in required_repeats:
            subset = q[q.repeat_id == repeat]
            found = set(zip(subset.speed_mm_s,subset.direction_deg,subset.nominal_force_N))
            condition_set = found if condition_set is None else condition_set & found
        common = condition_set if common is None else common & condition_set
    if not common:
        raise ValueError("No common eligible query conditions across the cohort")
    if common & FORBIDDEN:
        raise ValueError("A primary query condition was observed by a support protocol")
    rows = []
    for surface in cohort:
        q = queries[queries.surface_id == surface]
        for protocol in cfg["protocols"]:
            for duration in cfg["durations_s"]:
                ids = [lookup[(surface,*c,duration)] for c in PROTOCOLS[protocol]]
                support_records = set(supports[supports.window_id.isin(ids)].recording_id)
                for query in q.itertuples():
                    condition = (query.speed_mm_s,query.direction_deg,query.nominal_force_N)
                    if condition not in common:
                        continue
                    if query.recording_id in support_records:
                        raise ValueError("Support/query recording overlap")
                    row = {"surface_id":surface,"family_group":surfaces.loc[surface,"family_group"],
                           "split":query.split,"protocol":protocol,"duration_s":duration,
                           "support_window_ids":json.dumps(ids),"query_window_id":query.window_id,
                           "query_speed_mm_s":query.speed_mm_s,"query_direction_deg":query.direction_deg,
                           "query_nominal_force_N":query.nominal_force_N,"query_repeat_id":query.repeat_id,
                           "total_support_time_s":len(ids)*duration,
                           "total_support_distance_mm":sum(c[0]*duration for c in PROTOCOLS[protocol]),
                           "config_hash":cfg["config_hash"]}
                    row["episode_id"] = digest({"surface":surface,"protocol":protocol,"duration":duration,"query":query.window_id})[:24]
                    rows.append(row)
    episodes = pd.DataFrame(rows).sort_values(["split","surface_id","protocol","duration_s","query_window_id"])
    episodes.to_csv(root/"data/manifests/episodes.csv",index=False)
    write_json(root/"data/manifests/episode_summary.json",{
        "stage":"development","config_hash":cfg["config_hash"],"common_query_conditions":[list(c) for c in sorted(common)],
        "eligible_train_ids":sorted(set(cohort)&set(cfg["train_ids"])),
        "eligible_val_ids":sorted(set(cohort)&set(cfg["val_ids"])),
        "episode_count":len(episodes),"specimen_groups_reviewed":bool(surfaces.loc[cohort,"grouping_reviewed"].all()),
        "specimen_grouping_scopes":sorted(surfaces.loc[cohort,"grouping_scope"].unique().tolist())})
    return episodes


class FeatureStore:
    """Prediction inputs are built from a whitelist; targets have a separate accessor."""
    def __init__(self, root, windows):
        self.root = Path(root)
        self.windows = windows.set_index("window_id")
        self._cache = {}

    def feature(self, window_id):
        if window_id not in self._cache:
            with np.load(self.root/self.windows.loc[window_id,"feature_path"]) as data:
                self._cache[window_id] = {k:data[k].copy() for k in data.files}
        return self._cache[window_id]

    def fit_scaler(self, train_episodes):
        if not (train_episodes.split == "train").all():
            raise ValueError("Scaler can fit training episodes only")
        ids = sorted({w for encoded in train_episodes.support_window_ids for w in json.loads(encoded)})
        if not all(self.windows.loc[w,"split"] == "train" and self.windows.loc[w,"role"] == "support" for w in ids):
            raise ValueError("Scaler encountered nontraining support")
        values = np.stack([self.feature(w)["log_band_power"].reshape(-1) for w in ids])
        std = values.std(axis=0)
        std[std < 1e-8] = 1.
        scaler = {"mean":values.mean(axis=0),"std":std}
        path = self.root/"data/features/scaler.npz"
        np.savez(path,**scaler)
        write_json(path.with_suffix(".json"),{"fit_window_ids":ids,"fit_surface_ids":sorted(train_episodes.surface_id.unique().tolist())})
        return scaler

    def make_prediction_inputs(self, episode, scaler):
        # Deliberately never read query_window_id, target, material ID or measured query force.
        support = np.zeros((2,101),dtype=np.float32)
        mask = np.zeros(2,dtype=np.float32)
        ids = json.loads(episode["support_window_ids"])
        if not 1 <= len(ids) <= 2:
            raise ValueError("Expected one or two permitted supports")
        for index,window_id in enumerate(ids):
            row = self.windows.loc[window_id]
            if row.role != "support":
                raise ValueError("Query window used as support input")
            powers = self.feature(window_id)["log_band_power"].reshape(-1)
            support[index] = np.r_[(powers-scaler["mean"])/scaler["std"],
                                  condition_vector(row.speed_mm_s,row.direction_deg,row.nominal_force_N),row.duration_s]
            mask[index] = 1
        query = condition_vector(episode["query_speed_mm_s"],episode["query_direction_deg"],episode["query_nominal_force_N"])
        return support,mask,query

    def get_target(self, episode):
        window_id = episode["query_window_id"]
        if self.windows.loc[window_id,"role"] != "query":
            raise ValueError("Target must be a hidden query window")
        return self.feature(window_id)["log_band_power"].reshape(-1).astype(np.float32)

    def batch_inputs(self, episodes, scaler):
        values = [self.make_prediction_inputs(row,scaler) for row in episodes.to_dict("records")]
        return tuple(np.stack([v[i] for v in values]) for i in range(3))

    def targets(self, episodes):
        return np.stack([self.get_target(row) for row in episodes.to_dict("records")])
