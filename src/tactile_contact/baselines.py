from __future__ import annotations

import json

import numpy as np
from sklearn.linear_model import Ridge

from .signal import integrate_bands
from .config import validate_fit_pool, OMITTED_SPEEDS, speed_bracket


def cell_weights(episodes):
    counts = episodes.groupby(["surface_id","protocol","duration_s"]).episode_id.transform("size")
    cells = episodes[["surface_id","protocol","duration_s"]].drop_duplicates().groupby("surface_id").size()
    # Total weight per specimen is one, independent of how many cells repeat its labels.
    return 1/counts.to_numpy()/episodes.surface_id.map(cells).to_numpy()


def validation_mae(episodes, prediction, target):
    error = episodes[["surface_id","protocol","duration_s"]].copy()
    error["error"] = np.abs(prediction-target).mean(axis=1)
    return float(error.groupby(["surface_id","protocol","duration_s"]).error.mean()
                 .groupby(["protocol","duration_s"]).mean().mean())


class FixedFeatures:
    """Ridge on mean/std of permitted vectors; all scalers fit training only."""
    alphas = (0.01,0.1,1.,10.,100.)

    def features(self, episodes, store, scaler):
        support,mask,query = store.batch_inputs(episodes,scaler)
        count = mask.sum(axis=1,keepdims=True)
        mean = (support*mask[:,:,None]).sum(axis=1)/count
        variance = (np.square(support-mean[:,None,:])*mask[:,:,None]).sum(axis=1)/count
        return np.column_stack([mean,np.sqrt(variance),count,query])

    def fit(self, train, val, store, scaler):
        validate_fit_pool(train,"train"); validate_fit_pool(val,"val")
        features = self.features(train,store,scaler)
        weights = cell_weights(train)
        self.mean = np.average(features,axis=0,weights=weights)
        self.std = np.sqrt(np.average(np.square(features-self.mean),axis=0,weights=weights))
        self.std[self.std < 1e-8] = 1.
        x = (features-self.mean)/self.std
        y = store.targets(train)
        validation = (self.features(val,store,scaler)-self.mean)/self.std
        target = store.targets(val)
        self.candidates = []
        best = np.inf
        for alpha in self.alphas:
            model = Ridge(alpha=alpha).fit(x,y,sample_weight=weights)
            loss = validation_mae(val,model.predict(validation),target)
            self.candidates.append({"alpha":alpha,"validation_mae":loss})
            if loss < best:
                best = loss; self.regression = model; self.alpha = alpha
        self.fit_surface_ids = sorted(train.surface_id.unique().tolist())
        return self

    def predict(self, episodes, store, scaler):
        return self.regression.predict((self.features(episodes,store,scaler)-self.mean)/self.std)


def select_support(episode, store):
    ids = json.loads(episode["support_window_ids"])
    query_angle = episode["query_direction_deg"]
    query_speed = episode["query_speed_mm_s"]
    def rank(index):
        row = store.windows.loc[ids[index]]
        if row.role != "support":
            raise ValueError("Rescaling requires permitted support")
        angular = abs((row.direction_deg-query_angle+180)%360-180)
        return angular,abs(np.log(query_speed/row.speed_mm_s)),index
    return ids[min(range(len(ids)),key=rank)]


def warp_band_power(feature, speed_ratio, load_ratio=1., p=0., b=0.):
    """s^(p-1) r^b S(f/s), integrated on the target's bin grid."""
    if speed_ratio <= 0 or load_ratio <= 0:
        raise ValueError("Positive speed and load ratios required")
    frequency = feature["frequency_hz"]
    wanted = frequency/speed_ratio
    # Only modeled-band bins need source coverage; high output bins are unused.
    modeled = (frequency >= 24) & (frequency <= 1000)
    if wanted[modeled].min() < frequency[0] or wanted[modeled].max() > frequency[-1]:
        raise ValueError("Speed rescaling would extrapolate the modeled frequency range")
    warped = np.column_stack([np.interp(wanted,frequency,feature["psd"][:,i],left=0.,right=0.) for i in range(3)])
    power,_ = integrate_bands(frequency,warped*speed_ratio**(p-1)*load_ratio**b,feature["band_edges_hz"])
    return power.reshape(-1)


class SpeedRescaling:
    """Dense-PSD direction-agnostic baseline, with global train-fitted exponents."""
    alphas = (0.,0.1,1.)

    def components(self, episodes, store):
        powers,ratios,floors,selected = [],[],[],[]
        for row in episodes.to_dict("records"):
            window = select_support(row,store)
            condition = store.windows.loc[window]
            s = row["query_speed_mm_s"]/condition.speed_mm_s
            r = row["query_nominal_force_N"]/condition.nominal_force_N
            feature = store.feature(window)
            powers.append(warp_band_power(feature,s)); ratios.append([np.log10(s),np.log10(r)])
            floors.append(float(feature["floor"])); selected.append(window)
        return np.stack(powers),np.array(ratios),np.array(floors),selected

    @staticmethod
    def reconstruct(power, ratios, floors, exponents):
        return np.log10(power*np.power(10.,ratios@exponents)[:,None]+floors[:,None])

    def fit(self, train, val, store, scaler):
        validate_fit_pool(train,"train"); validate_fit_pool(val,"val")
        power,ratios,floors,selected = self.components(train,store)
        targets = store.targets(train).astype(float)
        target_power = np.maximum(10**targets-floors[:,None],0.)
        valid = (power > 100*floors[:,None]) & (target_power > 100*floors[:,None])
        if not valid.any():
            raise ValueError("No training bands above the numerical floor for exponent fitting")
        # Above-floor bands obey log Pq - log Pwarp = p log s + b log r.
        difference = np.log10(np.maximum(target_power,np.finfo(float).tiny))-np.log10(np.maximum(power,np.finfo(float).tiny))
        x = np.broadcast_to(ratios[:,None,:],(*power.shape,2))[valid]
        y = difference[valid]
        counts = valid.sum(axis=1)
        weights = np.broadcast_to((cell_weights(train)/np.maximum(counts,1))[:,None],power.shape)[valid]
        validation = self.components(val,store)
        target = store.targets(val)
        self.candidates = []; best = np.inf
        for alpha in self.alphas:
            regression = Ridge(alpha=alpha,fit_intercept=False).fit(x,y,sample_weight=weights)
            # Declare finite bounds to avoid poorly identified extreme extrapolation.
            exponents = np.clip(regression.coef_,[-4.,-4.],[8.,4.])
            loss = validation_mae(val,self.reconstruct(*validation[:3],exponents),target)
            self.candidates.append({"alpha":alpha,"p":float(exponents[0]),"b":float(exponents[1]),"validation_mae":loss})
            if loss < best:
                best = loss; self.exponents = exponents; self.alpha = alpha
        self.fit_surface_ids = sorted(train.surface_id.unique().tolist())
        self.fit_support_window_ids = sorted(set(selected))
        self.fit_query_window_ids = sorted(set(train.query_window_id))
        return self

    def predict(self, episodes, store, scaler):
        power,ratios,floors,_ = self.components(episodes,store)
        return self.reconstruct(power,ratios,floors,self.exponents)



class ConditionsOnly:
    def fit(self, episodes, store, scaler):
        validate_fit_pool(episodes,"train")
        _,_,q = store.batch_inputs(episodes,scaler)
        # Each surface/protocol/duration cell contributes equal total weight.
        self.regression = Ridge(alpha=1.).fit(q.astype(float),store.targets(episodes).astype(float),sample_weight=cell_weights(episodes))
        return self

    def predict(self, episodes, store, scaler):
        _,_,q = store.batch_inputs(episodes,scaler)
        return self.regression.predict(q.astype(float))


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
    def __init__(self, interpolate_speeds=False):
        self.interpolate_speeds = interpolate_speeds

    def fit(self, episodes, store, scaler):
        validate_fit_pool(episodes,"train")
        is_transfer = "experiment" in episodes and (episodes.experiment == "omitted_speed").any()
        if is_transfer != self.interpolate_speeds:
            raise ValueError("Retrieval interpolation mode must match the experiment")
        if self.interpolate_speeds and episodes.query_speed_mm_s.isin(OMITTED_SPEEDS).any():
            raise ValueError("Omitted-speed responses cannot enter retrieval")
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

    def response(self, surface, speed, direction, force):
        key = (surface,speed,direction,force)
        if self.interpolate_speeds and speed in OMITTED_SPEEDS:
            lower,upper = speed_bracket(speed)
            keys = [(surface,lower,direction,force),(surface,upper,direction,force)]
            if any(k not in self.responses for k in keys):
                raise ValueError("Retrieval needs both permitted interpolation endpoints")
            fraction = (speed-lower)/(upper-lower)
            weights = [1-fraction,fraction]
            return sum(weight*self.responses[k] for weight,k in zip(weights,keys)),keys,weights
        if key not in self.responses:
            raise ValueError("No permitted retrieval response; extrapolation is disabled")
        return self.responses[key],[key],[1.]

    def predict(self, episodes, store, scaler):
        predictions, retrieved = [],[]
        self.prediction_sources = []
        for row in episodes.to_dict("records"):
            support,mask,_ = store.make_prediction_inputs(row,scaler)
            fingerprint = support[mask.astype(bool),:96].reshape(-1)
            library,ids = self.library[(row["protocol"],row["duration_s"])]
            surface = int(ids[np.argmin(np.square(library-fingerprint).sum(axis=1))])
            prediction,keys,weights = self.response(surface,row["query_speed_mm_s"],row["query_direction_deg"],row["query_nominal_force_N"])
            predictions.append(prediction); retrieved.append(surface)
            self.prediction_sources.append({"episode_id":row["episode_id"],"retrieved_training_id":surface,
                "response_keys":[list(k) for k in keys],"weights":weights,
                "source_window_ids":[self.response_sources[k] for k in keys]})
        return np.stack(predictions),np.array(retrieved)
