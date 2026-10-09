import json

import numpy as np
import pandas as pd
import pytest

from tactile_contact.baselines import FixedFeatures, SpeedRescaling, cell_weights, select_support, warp_band_power
from tactile_contact.signal import spectral_features
from tactile_contact.timing import compare_raw_span


def test_speed_warp_identity_and_power_stretch():
    t = np.arange(6000)/6000
    feature = spectral_features(.02*np.sin(2*np.pi*160*t)[:,None]*np.ones((1,3)))
    np.testing.assert_allclose(warp_band_power(feature,1.,p=4),feature["band_power"].reshape(-1),rtol=1e-12)
    doubled = warp_band_power(feature,2.,p=4).reshape(32,3)
    np.testing.assert_allclose(doubled.sum(axis=0),16*feature["band_power"].sum(axis=0),rtol=1e-8)
    peak_band = np.argmax(doubled[:,0])
    assert feature["band_edges_hz"][peak_band] <= 320 <= feature["band_edges_hz"][peak_band+1]
    with pytest.raises(ValueError,match="extrapolate"):
        warp_band_power(feature,.2)
    assert feature["band_bin_counts"].sum() == 123


def test_fixed_features_statistics_are_training_only_and_queries_remain_hidden(prepared):
    _,_,_,_,store,scaler,train,val = prepared
    model = FixedFeatures().fit(train,val,store,scaler)
    features = model.features(train,store,scaler)
    np.testing.assert_allclose(model.mean,np.average(features,axis=0,weights=cell_weights(train)))
    assert set(model.fit_surface_ids) == set(train.surface_id)
    corrupted = val.copy(); corrupted["query_window_id"] = "future-is-hidden"; corrupted["surface_id"] = 999
    np.testing.assert_allclose(model.predict(val,store,scaler),model.predict(corrupted,store,scaler))
    with pytest.raises(ValueError,match="roles"):
        FixedFeatures().fit(val,val,store,scaler)


def test_repeated_protocol_cells_do_not_change_conditions_only_regularization(prepared):
    _,_,_,_,store,scaler,train,val = prepared
    from tactile_contact.baselines import ConditionsOnly
    reference = train[(train.protocol == "single") & (train.duration_s == .5)]
    full = ConditionsOnly().fit(train,store,scaler)
    single = ConditionsOnly().fit(reference,store,scaler)
    np.testing.assert_allclose(full.predict(val,store,scaler),single.predict(val,store,scaler),atol=1e-6)
    weights = pd.Series(cell_weights(train),index=train.index)
    np.testing.assert_allclose(weights.groupby(train.surface_id).sum(),1.)


def test_rescaling_fits_train_only_and_selects_the_nearest_permitted_direction(prepared):
    _,_,_,_,store,scaler,train,val = prepared
    model = SpeedRescaling().fit(train,val,store,scaler)
    assert set(model.fit_query_window_ids).isdisjoint(val.query_window_id)
    row = val[(val.protocol == "direction") & (val.duration_s == .5)].iloc[0].to_dict()
    row["query_direction_deg"] = 90
    selected = store.windows.loc[select_support(row,store)]
    assert selected.direction_deg == 90
    row["query_direction_deg"] = 45
    assert select_support(row,store) == json.loads(row["support_window_ids"])[0]
    corrupted = val.copy(); corrupted["query_window_id"] = "future-is-hidden"; corrupted["surface_id"] = 999
    np.testing.assert_allclose(model.predict(val,store,scaler),model.predict(corrupted,store,scaler))
    with pytest.raises(ValueError,match="roles"):
        SpeedRescaling().fit(val,val,store,scaler)


def test_clock_sensitivity_exposes_changed_frequency_and_nominal_budget():
    times = np.arange(9000)/9000
    frame = pd.DataFrame({axis:.02*np.sin(2*np.pi*160*times) for axis in ["X","Y","Z"]})
    grid = np.arange(3000)/6000
    timestamp = spectral_features(.02*np.sin(2*np.pi*160*grid)[:,None]*np.ones((1,3)))
    result = compare_raw_span(frame,times,0.,.5,timestamp,6000,1e-10)
    assert result["raw_samples"] == 4500
    assert result["index_duration_at_reported_rate_s"] == .75
    assert result["timestamp_peak_hz"] == 160
    assert result["reported_rate_index_peak_hz"] == pytest.approx(160*6000/9000,abs=4)
    assert result["log_power_mae_between_paths"] > 0


def test_explicit_family_review_rejects_a_cross_split_family(prepared,tmp_path):
    root,cfg,*_ = prepared
    from tactile_contact.audit import make_surfaces
    review = pd.DataFrame({"surface_id":[0,1,2,3],"family_group":["shared","b","shared","d"],
        "grouping_reason":["fixture"]*4,"grouping_reviewed":[True]*4,"grouping_scope":["fixture"]*4})
    path = tmp_path/"groups.csv"; review.to_csv(path,index=False)
    output = tmp_path/"run"; (output/"data/manifests").mkdir(parents=True)
    with pytest.raises(ValueError,match="crosses"):
        make_surfaces(output,dict(cfg,specimen_groups_path=str(path)),root/"data/raw/synthetic")


def test_preparation_reuse_rejects_changed_software(prepared,monkeypatch):
    root,cfg,*_ = prepared
    from tactile_contact.pipeline import run
    monkeypatch.setattr("tactile_contact.pipeline.preparation_hashes",lambda:{"changed":True})
    with pytest.raises(ValueError,match="code changed"):
        run(root,cfg,reuse=True)


def test_budget_contrast_rejects_changed_query_identity(prepared,tmp_path):
    _,_,_,episodes,*_ = prepared
    from tactile_contact.evaluation import budget_contrasts
    scores = episodes[episodes.split == "val"].copy()
    scores["model"] = "fixture"; scores["log_power_mae"] = 1.
    per_surface = scores.groupby(["model","surface_id","family_group","protocol","duration_s"],as_index=False).log_power_mae.mean()
    scores.loc[(scores.protocol == "repeat") & (scores.duration_s == .5),"query_window_id"] = "changed"
    with pytest.raises(ValueError,match="query identities"):
        budget_contrasts(tmp_path,per_surface,scores)
