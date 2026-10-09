import json

import numpy as np
import pandas as pd
import pytest
import torch

from tactile_contact.audit import motion_speed,load_record
from tactile_contact.config import FORBIDDEN,load_config
from tactile_contact.baselines import ConditionsOnly,CopySpectrum,Retrieval
from tactile_contact.metrics import paired_bootstrap
from tactile_contact.models import ContactPredictor
from tactile_contact.signal import spectral_features,rms_from_log_power
from tactile_contact.training import fit_model,model_predictions,validation_objective
from tactile_contact.evaluation import wrong_support


@pytest.mark.parametrize("duration",[.25,.5,1.])
def test_spectrum_preserves_physical_power(duration):
    t = np.arange(round(duration*6000))/6000
    a = .02*np.sin(2*np.pi*160*t)[:,None]*np.array([[1,.5,.2]])
    result = spectral_features(a)
    np.testing.assert_allclose(spectral_features(2*a)["band_power"],4*result["band_power"],rtol=1e-10,atol=1e-20)
    np.testing.assert_allclose(spectral_features(a+1)["band_power"],result["band_power"],rtol=1e-8,atol=1e-20)
    axes,total = rms_from_log_power(result["log_band_power"].reshape(1,-1))
    np.testing.assert_allclose(axes[0],.02*9.80665/np.sqrt(2)*np.array([1,.5,.2]),rtol=1e-8)
    assert total[0] == pytest.approx(np.linalg.norm(axes[0]))


def test_actual_time_motion_fit_handles_delivery_jitter():
    rng = np.random.default_rng(0)
    t = np.r_[0,np.cumsum(rng.uniform(.007,.013,99))]
    positions = pd.DataFrame({"X":32*t,"Y":24*t})
    np.testing.assert_allclose(motion_speed(positions,t,21),40,rtol=1e-10)


def test_episode_split_and_query_exclusions(prepared):
    _,_,windows,episodes,_,_,train,val = prepared
    assert set(train.surface_id).isdisjoint(val.surface_id)
    assert not set(zip(episodes.query_speed_mm_s,episodes.query_direction_deg,episodes.query_nominal_force_N)) & FORBIDDEN
    assert set(train.query_repeat_id) == {0,1} and set(val.query_repeat_id) == {1}
    lookup = windows.set_index("window_id")
    for row in episodes.itertuples():
        supports = lookup.loc[json.loads(row.support_window_ids)]
        query = lookup.loc[row.query_window_id]
        assert (supports.surface_id == query.surface_id).all()
        assert query.recording_id not in set(supports.recording_id)
        assert row.total_support_time_s == len(supports)*row.duration_s


def test_duration_windows_are_prefixes(prepared):
    _,_,windows,*_ = prepared
    for _, group in windows[windows.role == "support"].groupby("recording_id"):
        assert group.start_s.nunique() == 1
        np.testing.assert_allclose(group.end_s-group.start_s,group.duration_s)


def test_query_fields_cannot_change_prediction_inputs(prepared):
    _,_,_,_,store,scaler,_,val = prepared
    episode = val.iloc[0].to_dict()
    before = store.make_prediction_inputs(episode,scaler)
    episode.update(query_window_id="unreadable-future-target",surface_id=999999,
                   measured_query_force_N=999,target_log_power=np.full(96,np.nan))
    after = store.make_prediction_inputs(episode,scaler)
    for a,b in zip(before,after):
        np.testing.assert_array_equal(a,b)


def test_preprocessing_and_retrieval_exclude_validation(prepared):
    _,_,_,_,store,scaler,train,val = prepared
    with pytest.raises(ValueError):
        store.fit_scaler(val)
    with pytest.raises(ValueError):
        Retrieval().fit(val,store,scaler)
    baseline = Retrieval().fit(train,store,scaler)
    prediction,ids = baseline.predict(val,store,scaler)
    assert prediction.shape == (len(val),96)
    assert set(ids).issubset(set(train.surface_id))
    assert not set(ids) & set(val.surface_id)


def test_retrieval_averages_training_linear_power(prepared):
    _,_,_,_,store,scaler,train,_ = prepared
    baseline = Retrieval().fit(train,store,scaler)
    group = train[(train.protocol == "single") & (train.duration_s == .5) & (train.surface_id == 0)]
    selected = group[(group.query_speed_mm_s == 30) & (group.query_nominal_force_N == .5)]
    powers = np.mean([store.feature(w)["band_power"] for w in selected.query_window_id],axis=0)
    expected = np.log10(powers+1e-10).reshape(-1)
    np.testing.assert_allclose(baseline.responses[(0,30,0,.5)],expected)


def test_all_baselines_predict_identical_episode_set(prepared):
    _,_,_,_,store,scaler,train,val = prepared
    for baseline in [ConditionsOnly().fit(train,store,scaler),CopySpectrum(),Retrieval().fit(train,store,scaler)]:
        output = baseline.predict(val,store,scaler)
        prediction = output[0] if isinstance(output,tuple) else output
        assert prediction.shape == (len(val),96) and np.isfinite(prediction).all()


@pytest.mark.parametrize("ids",[["a",np.nan],[None,"a"],["","a"],np.array(["a",1],dtype=object)])
def test_bootstrap_rejects_missing_or_mixed_groups(ids):
    with pytest.raises(ValueError):
        paired_bootstrap([1.,2.],[.5,1.5],ids,draws=20)


def test_bootstrap_pairs_and_resamples_whole_families():
    result = paired_bootstrap([1.,2.,3.],[.5,1.5,2.5],["a","a","b"],draws=100)
    assert result["independent_groups"] == 2 and result["surfaces"] == 3
    np.testing.assert_allclose(result["ci95"],[.5,.5])


def test_model_masks_padding_and_preserves_set_order():
    torch.manual_seed(0)
    model = ContactPredictor().eval()
    support = torch.randn(2,2,101); mask = torch.tensor([[1.,0.],[1.,1.]]); q = torch.randn(2,4)
    with torch.no_grad():
        expected = model(support,mask,q)[0]
        changed = support.clone(); changed[0,1] = 10000
        torch.testing.assert_close(model(changed,mask,q)[0],expected)
        torch.testing.assert_close(model(support[:,[1,0]],mask[:,[1,0]],q)[0],expected)
    changed[0,1] = float("nan")
    with pytest.raises(ValueError):
        model(changed,mask,q)


def test_wrong_support_mapping_has_no_self_matches(prepared):
    _,_,_,_,_,_,_,val = prepared
    substituted = wrong_support(val)
    assert (val.support_window_ids != substituted.support_window_ids).all()
    pd.testing.assert_series_equal(val.query_window_id,substituted.query_window_id)
    pd.testing.assert_series_equal(substituted.support_window_ids,wrong_support(val).support_window_ids)


def test_training_checkpoint_and_scoring_contract(prepared):
    root,cfg,_,_,store,scaler,train,val = prepared
    model,path = fit_model(root,cfg,train,val,store,scaler,0)
    saved = torch.load(path,weights_only=True)
    restored = ContactPredictor(latent_dim=cfg["training"]["latent_dim"])
    restored.load_state_dict(saved["state_dict"])
    predicted = model_predictions(model,val,store,scaler)
    np.testing.assert_allclose(model_predictions(restored,val,store,scaler),predicted)
    assert predicted.shape == (len(val),96) and np.isfinite(predicted).all()
    assert np.isfinite(validation_objective(val,predicted,store.targets(val)))
    assert saved["config_hash"] == cfg["config_hash"]


def test_duplicate_raw_timestamps_are_rejected(prepared,tmp_path):
    root,*_ = prepared
    raw = root/"data/raw/synthetic"
    target = tmp_path/"raw"
    for channel in ["accel","force","position"]:
        destination = target/"sensor_data"/channel/"0"
        destination.mkdir(parents=True)
        original = raw/"sensor_data"/channel/"0/0_0_40_500_0.parquet"
        frame = pd.read_parquet(original)
        if channel == "accel":
            frame.loc[1,"time_ns"] = frame.loc[0,"time_ns"]
        frame.to_parquet(destination/original.name,index=False)
    with pytest.raises(ValueError,match="Nonmonotonic"):
        load_record(target,"0_0_40_500_0")


def test_locked_test_stage_is_not_accidentally_enabled(tmp_path):
    path = tmp_path/"test.yaml"
    path.write_text("stage: test",encoding="utf-8")
    with pytest.raises(ValueError,match="locked test"):
        load_config(path)


def test_fresh_pipeline_saves_predictions_baselines_and_provenance(prepared):
    root,cfg,*_ = prepared
    from tactile_contact.pipeline import run
    result = run(root,cfg,reuse=True)
    assert set(result.model) == {"conditions_only","copy","retrieval","encoder","encoder_wrong_support"}
    for name in ["predictions.npz","conditions_only_fit.npz","retrieval_fit.npz",
                 "retrieval_sources.json","wrong_support_assignments.csv","per_query.csv","per_surface.csv"]:
        assert (root/"results/tables"/name).is_file()
    manifest = json.loads((root/"results/run_manifest.json").read_text())
    assert manifest["stage"] == "development" and manifest["software_hashes"]
    with np.load(root/"results/tables/predictions.npz") as values:
        assert values["encoder_0"].shape == values["targets"].shape
        assert values["encoder_wrong_support_0"].shape == values["targets"].shape


def test_tiny_training_can_fit_a_known_input_response_mapping():
    torch.manual_seed(0); torch.set_num_threads(1)
    support = torch.randn(8,2,101); mask = torch.ones(8,2); q = torch.randn(8,4)
    target = (support[:,0,0:1]+q[:,0:1]).repeat(1,96)
    model = ContactPredictor()
    optimizer = torch.optim.Adam(model.parameters(),lr=.001)
    initial = float(torch.nn.functional.l1_loss(model(support,mask,q)[0],target).detach())
    for _ in range(250):
        optimizer.zero_grad(set_to_none=True)
        loss = torch.nn.functional.l1_loss(model(support,mask,q)[0],target)
        loss.backward(); optimizer.step()
    assert float(loss.detach()) < .05*initial
