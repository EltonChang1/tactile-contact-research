from __future__ import annotations

import json

import numpy as np
from sklearn.linear_model import Ridge



class ConditionsOnly:
    def fit(self, episodes, store, scaler):
        if not (episodes.split == "train").all():
            raise ValueError("Fit requires training records")
        _,_,q = store.batch_inputs(episodes,scaler)
        # Each surface/protocol/duration cell contributes equal total weight.
        counts = episodes.groupby(["surface_id","protocol","duration_s"]).episode_id.transform("size")
        self.regression = Ridge(alpha=1.).fit(q,store.targets(episodes),sample_weight=1/counts.to_numpy())
        return self

    def predict(self, episodes, store, scaler):
        _,_,q = store.batch_inputs(episodes,scaler)
        return self.regression.predict(q)


class CopySpectrum:
    def predict(self, episodes, store, scaler):
        out = []
        for row in episodes.to_dict("records"):
            ids = json.loads(row["support_window_ids"])
            power = np.mean([store.feature(w)["band_power"] for w in ids],axis=0)
            floor = float(store.feature(ids[0])["floor"])
            out.append(np.log10(power+floor).reshape(-1))
        return np.stack(out)


class Retrieval:
    def fit(self, episodes, store, scaler):
        if not (episodes.split == "train").all():
            raise ValueError("Retrieval library requires training surfaces")
        self.library = {}
        self.responses = {}
        self.library_sources = {}
        self.response_sources = {}
        self.scaler = scaler
        for key, group in episodes.groupby(["protocol","duration_s"]):
            fingerprints,ids = [],[]
            self.library_sources[key] = {}
            for surface, subset in group.groupby("surface_id",sort=True):
                row = subset.iloc[0].to_dict()
                inputs,mask,_ = store.make_prediction_inputs(row,scaler)
                self.library_sources[key][str(surface)] = json.loads(row["support_window_ids"])
                fingerprints.append(inputs[mask.astype(bool),:96].reshape(-1))
                ids.append(int(surface))
                for condition, queries in subset.groupby(["query_speed_mm_s","query_direction_deg","query_nominal_force_N"]):
                    windows = sorted(set(queries.query_window_id))
                    power = np.mean([store.feature(w)["band_power"] for w in windows],axis=0)
                    floor = float(store.feature(windows[0])["floor"])
                    self.responses[(surface,*condition)] = np.log10(power+floor).reshape(-1)
                    self.response_sources[(surface,*condition)] = windows
            self.library[key] = (np.stack(fingerprints),np.array(ids))
        return self

    def predict(self, episodes, store, scaler):
        predictions, retrieved = [],[]
        for row in episodes.to_dict("records"):
            support,mask,_ = store.make_prediction_inputs(row,scaler)
            fingerprint = support[mask.astype(bool),:96].reshape(-1)
            library,ids = self.library[(row["protocol"],row["duration_s"])]
            surface = int(ids[np.argmin(np.square(library-fingerprint).sum(axis=1))])
            key = (surface,row["query_speed_mm_s"],row["query_direction_deg"],row["query_nominal_force_N"])
            predictions.append(self.responses[key]); retrieved.append(surface)
        return np.stack(predictions),np.array(retrieved)
