from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import yaml

PROTOCOLS = {
    "single": [(40, 0, 0.5, 0)],
    "repeat": [(40, 0, 0.5, 0), (40, 0, 0.5, 1)],
    "speed": [(40, 0, 0.5, 0), (20, 0, 0.5, 0)],
    "load": [(40, 0, 0.5, 0), (40, 0, 1.0, 0)],
    "direction": [(40, 0, 0.5, 0), (40, 90, 0.5, 0)],
}
FORBIDDEN = {c[:3] for conditions in PROTOCOLS.values() for c in conditions}


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def data_root(root, cfg):
    """Raw downloads may be shared; derived artifacts always use the run root."""
    return Path(cfg.get("data_root", root))


def validate_source(root, cfg):
    path = data_root(root,cfg)/"data/source.json"
    source = json.loads(path.read_text(encoding="utf-8"))
    if source.get("source_kind") != cfg["source_kind"]:
        raise ValueError("Raw-data source kind does not match configuration")
    if cfg["source_kind"] == "cluster" and any(source.get(key) != cfg[key] for key in ["revision","repo_id"]):
        raise ValueError("Raw-data revision/repository does not match configuration")
    return source


def load_config(path):
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if cfg.get("stage") != "development":
        raise ValueError("Only development runs are implemented; locked test evaluation is not enabled")
    train, val = set(cfg["train_ids"]), set(cfg["val_ids"])
    if not train or not val or train & val:
        raise ValueError("Need nonempty disjoint training/validation surfaces")
    if len(train) != len(cfg["train_ids"]) or len(val) != len(cfg["val_ids"]):
        raise ValueError("Duplicate surface IDs")
    for speed,direction,force in cfg["conditions"]:
        if speed not in [20,30,40,50,60] or direction not in range(0,360,45) or force not in [.5,1.]:
            raise ValueError("Condition is outside the Cluster grid")
    if any(p not in PROTOCOLS for p in cfg["protocols"]):
        raise ValueError("Unknown support protocol")
    if min(cfg["durations_s"]) < 0.25 or cfg["query_duration_s"] < 0.25:
        raise ValueError("Welch starter requires at least 0.25 seconds")
    if cfg["time_base"] != "timestamp_resample":
        raise ValueError("Choose and audit timestamp_resample for this development implementation")
    if not isinstance(cfg["sampling_rate_hz"],int) or cfg["sampling_rate_hz"] <= 2000:
        raise ValueError("Require integer sampling rate with 1000 Hz below Nyquist")
    if not math.isfinite(cfg["power_floor"]) or cfg["power_floor"] <= 0:
        raise ValueError("Invalid spectral power floor")
    review_path = None
    if cfg.get("specimen_groups_path"):
        review_path = (Path(path).resolve().parent/cfg["specimen_groups_path"]).resolve()
        cfg["specimen_groups_hash"] = file_hash(review_path)
    cfg["config_hash"] = digest(cfg)
    if review_path:
        cfg["specimen_groups_path"] = str(review_path)
    return cfg
