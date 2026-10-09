import io
import json

import pytest

from tactile_contact.download import download_cluster
from tactile_contact.synthetic import generate


def test_pinned_download_cache_checks_original_hashes(tmp_path,monkeypatch):
    calls = []
    def fake_download(request,timeout):
        calls.append(request.full_url)
        return io.BytesIO(b"downloaded fixture bytes")
    monkeypatch.setattr("urllib.request.urlopen",fake_download)
    cfg = {"repo_id":"example/fixture","revision":"a"*40,"train_ids":[0],"val_ids":[1],"conditions":[[40,0,.5]]}
    download_cluster(tmp_path,cfg)
    assert len(calls) == 14 and all("/resolve/"+"a"*40+"/" in u for u in calls)
    download_cluster(tmp_path,cfg)
    assert len(calls) == 14
    (tmp_path/"data/raw/cluster/README.md").write_bytes(b"modified")
    with pytest.raises(ValueError,match="hash mismatch"):
        download_cluster(tmp_path,cfg)


def test_synthetic_generation_cannot_replace_measured_source(tmp_path):
    (tmp_path/"data").mkdir()
    source = tmp_path/"data/source.json"
    source.write_text(json.dumps({"source_kind":"cluster"}),encoding="utf-8")
    with pytest.raises(ValueError,match="separate --root"):
        generate(tmp_path,{"source_kind":"synthetic"})
    assert json.loads(source.read_text())["source_kind"] == "cluster"


def test_separate_run_reuses_shared_pinned_downloads(tmp_path,monkeypatch):
    calls = []
    def fake_download(request,timeout):
        calls.append(request.full_url)
        return io.BytesIO(b"fixture")
    monkeypatch.setattr("urllib.request.urlopen",fake_download)
    cfg = {"repo_id":"example/fixture","revision":"a"*40,"train_ids":[0],"val_ids":[1],"conditions":[[40,0,.5]]}
    download_cluster(tmp_path,cfg)
    second = tmp_path/"second-run"
    download_cluster(second,dict(cfg,data_root=str(tmp_path)))
    assert len(calls) == 14
    assert not (second/"data/raw").exists()


def test_audit_rejects_another_shared_raw_revision(tmp_path):
    from tactile_contact.config import validate_source
    (tmp_path/"data").mkdir()
    (tmp_path/"data/source.json").write_text(json.dumps({"source_kind":"cluster","repo_id":"example/fixture","revision":"a"*40}))
    cfg = {"source_kind":"cluster","repo_id":"example/fixture","revision":"b"*40,"data_root":str(tmp_path)}
    with pytest.raises(ValueError,match="revision/repository"):
        validate_source(tmp_path/"other-run",cfg)
