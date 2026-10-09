from pathlib import Path

import pytest

from tactile_contact.config import load_config,digest
from tactile_contact.synthetic import generate
from tactile_contact.pipeline import prepare
from tactile_contact.episodes import FeatureStore


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    root = tmp_path_factory.mktemp("contact-fixtures")
    project = Path(__file__).resolve().parents[1]
    cfg = load_config(project/"configs/synthetic.yaml")
    cfg.update(train_ids=[0,1],val_ids=[2,3])
    cfg["training"] = dict(cfg["training"],epochs=2,patience=2,episodes_per_surface=8)
    cfg.pop("config_hash")
    cfg["config_hash"] = digest(cfg)
    generate(root,cfg)
    windows,episodes = prepare(root,cfg)
    store = FeatureStore(root,windows)
    train = episodes[episodes.split == "train"].reset_index(drop=True)
    val = episodes[episodes.split == "val"].reset_index(drop=True)
    scaler = store.fit_scaler(train)
    return root,cfg,windows,episodes,store,scaler,train,val
