import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from tactile_contact.baselines import ConditionsOnly, FixedFeatures, Retrieval, SpeedRescaling
from tactile_contact.config import digest, load_config, validate_fit_pool
from tactile_contact.episodes import FeatureStore
from tactile_contact.pipeline import prepare, run
from tactile_contact.synthetic import generate


@pytest.fixture(scope="module")
def omitted(tmp_path_factory):
    root = tmp_path_factory.mktemp("omitted-speed")
    cfg = load_config(Path(__file__).resolve().parents[1]/"configs/omitted_speed.yaml")
    cfg.update(source_kind="synthetic",train_ids=[0,1],val_ids=[2,3])
    for key in ["specimen_groups_path","specimen_groups_hash","config_hash"]:
        cfg.pop(key)
    cfg["training"] = dict(cfg["training"],seeds=[0,1],epochs=2,patience=2,episodes_per_surface=8)
    cfg["qc"]["motion_smoothing_samples"] = 11
    cfg["config_hash"] = digest(cfg)
    generate(root,cfg)
    # An unrelated shared cache may contain omitted training files. They must never be opened.
    (root/"data/raw/synthetic/sensor_data/accel/0/0_45_30_1000_0.parquet").write_bytes(b"unreadable hidden training record")
    windows,episodes = prepare(root,cfg)
    store = FeatureStore(root,windows)
    train = episodes[episodes.split == "train"].reset_index(drop=True)
    selection = episodes[episodes.evaluation_partition == "selection"].reset_index(drop=True)
    transfer = episodes[episodes.evaluation_partition == "transfer"].reset_index(drop=True)
    scaler = store.fit_scaler(train)
    return root,cfg,windows,episodes,store,scaler,train,selection,transfer


def test_omitted_records_never_enter_audit_features_or_fit_partitions(omitted):
    root,_,windows,episodes,_,_,train,selection,transfer = omitted
    recordings = pd.read_csv(root/"data/manifests/recordings.csv")
    assert not ((recordings.surface_id.isin([0,1])) & recordings.speed_mm_s.isin([30,50])).any()
    assert not ((windows.split == "train") & windows.speed_mm_s.isin([30,50])).any()
    assert set(train.query_speed_mm_s) == {20,40,60}
    assert set(selection.query_speed_mm_s) == {20,40,60}
    assert set(transfer.query_speed_mm_s) == {30,50}
    assert set(episodes.evaluation_partition) == {"fit","selection","transfer"}
    assert set(train.query_repeat_id) == {0,1}
    assert set(selection.query_repeat_id) == set(transfer.query_repeat_id) == {1}


@pytest.mark.parametrize("method",["conditions","fixed","rescaling","retrieval","scaler"])
def test_fit_apis_reject_transfer_labels(omitted,method):
    _,_,_,_,store,scaler,train,selection,transfer = omitted
    calls = {
        "conditions":lambda:ConditionsOnly().fit(transfer,store,scaler),
        "fixed":lambda:FixedFeatures().fit(train,transfer,store,scaler),
        "rescaling":lambda:SpeedRescaling().fit(train,transfer,store,scaler),
        "retrieval":lambda:Retrieval(interpolate_speeds=True).fit(transfer,store,scaler),
        "scaler":lambda:store.fit_scaler(transfer),
    }
    with pytest.raises(ValueError,match="roles"):
        calls[method]()
    forged = transfer.copy(); forged["split"] = "train"; forged["evaluation_partition"] = "fit"
    with pytest.raises(ValueError,match="Omitted-speed labels"):
        validate_fit_pool(forged,"train")


def test_retrieval_interpolates_log_power_without_using_direct_omitted_labels(omitted):
    _,_,_,_,store,scaler,train,_,transfer = omitted
    model = Retrieval(interpolate_speeds=True).fit(train,store,scaler)
    expected = .5*(model.responses[(0,20,45,1.)]+model.responses[(0,40,45,1.)])
    model.responses[(0,30,45,1.)] = np.full(96,999.)
    prediction,keys,weights = model.response(0,30,45,1.)
    np.testing.assert_allclose(prediction,expected)
    assert keys == [(0,20,45,1.),(0,40,45,1.)] and weights == [.5,.5]
    assert model.predict(transfer,store,scaler)[0].shape == (len(transfer),96)
    assert all(key[1] in [20,40,60] for row in model.prediction_sources for key in row["response_keys"])
    with pytest.raises(ValueError,match="extrapolation"):
        model.response(0,70,45,1.)
    model.responses.pop((0,60,45,1.))
    with pytest.raises(ValueError,match="endpoints"):
        model.response(0,50,45,1.)


def test_transfer_targets_stay_unread_during_fitting_and_checkpoint_selection(omitted,monkeypatch):
    root,cfg,_,_,_,_,_,_,_ = omitted
    import tactile_contact.training as training
    original_fit = training.fit_model
    original_target = FeatureStore.get_target
    state = {"selected":0,"transfer_reads":0}
    def fit(*args,**kwargs):
        result = original_fit(*args,**kwargs)
        state["selected"] += 1
        return result
    def target(self,episode):
        if episode["evaluation_partition"] == "transfer":
            assert state["selected"] == len(cfg["training"]["seeds"])
            state["transfer_reads"] += 1
        return original_target(self,episode)
    monkeypatch.setattr(training,"fit_model",fit)
    monkeypatch.setattr(FeatureStore,"get_target",target)
    summary = run(root,cfg,reuse=True)
    assert state["transfer_reads"] == 120
    assert set(summary.evaluation_partition) == {"selection","transfer"}
    assert (root/"results/tables/selection/budget_contrasts.csv").exists()
    assert (root/"results/tables/transfer/budget_contrasts.csv").exists()
    fit_manifest = json.loads((root/"results/tables/fit_selection_manifest.json").read_text())
    assert fit_manifest["fit_speeds_mm_s"] == fit_manifest["selection_speeds_mm_s"] == [20,40,60]
    with np.load(root/"results/tables/predictions.npz") as values:
        assert set(values["evaluation_partitions"]) == {"selection","transfer"}
        assert len(values["targets"]) == 300


def test_config_rejects_interpolation_endpoints_that_are_support_conditions(tmp_path):
    cfg = yaml.safe_load((Path(__file__).resolve().parents[1]/"configs/omitted_speed.yaml").read_text())
    cfg.pop("specimen_groups_path")
    cfg["conditions"] += [[30,0,.5],[50,0,.5]]
    path = tmp_path/"bad.yaml"; path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError,match="non-support response endpoints"):
        load_config(path)


def test_download_omits_training_transfer_records(tmp_path,monkeypatch):
    from tactile_contact.download import download_cluster
    calls = []
    def fetch(request,timeout):
        calls.append(request.full_url)
        return io.BytesIO(b"fixture bytes")
    monkeypatch.setattr("urllib.request.urlopen",fetch)
    cfg = {"experiment":"omitted_speed","repo_id":"example/fixture","revision":"a"*40,
           "train_ids":[0],"val_ids":[1],"conditions":[[speed,45,1.] for speed in [20,30,40,50,60]]}
    download_cluster(tmp_path,cfg)
    assert len(calls) == 50
    assert not any("/0/0_45_30_" in url or "/0/0_45_50_" in url for url in calls)
    assert any("/1/1_45_30_" in url for url in calls)
