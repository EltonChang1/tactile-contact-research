"""Deterministic fixtures that exercise I/O and split logic, not contact physics."""
from pathlib import Path
import numpy as np
import pandas as pd

from .config import write_json


def generate(root,cfg):
    root = Path(root)
    if cfg["source_kind"] != "synthetic":
        raise ValueError("Fixture generator requires synthetic configuration")
    source_path = root/"data/source.json"
    if source_path.exists():
        import json
        if json.loads(source_path.read_text()).get("source_kind") != "synthetic":
            raise ValueError("This root already contains measured data; use a separate --root for fixtures")
    raw = root/"data/raw/synthetic"
    for surface in cfg["train_ids"] + cfg["val_ids"]:
        rng = np.random.default_rng(surface)
        frequency = 120+16*surface
        amplitude = 0.006+0.002*surface
        for speed,direction,force in cfg["conditions"]:
            for repeat in [0,1]:
                t = np.arange(12000)/6000
                theta = np.deg2rad(direction)
                wave = np.sin(2*np.pi*frequency*(speed/40)*t)
                values = amplitude*(force/.5)*wave[:,None]*np.array([[1.,.7,.5]])
                values += rng.normal(0,0.0005,values.shape)
                values[:,2] -= 1.
                position_t = np.arange(200)/100
                force_t = np.arange(160)/80
                frames = {
                    "accel":pd.DataFrame({"time_ns":np.rint(t*1e9).astype(np.int64),"X":values[:,0],"Y":values[:,1],"Z":values[:,2]}),
                    "force":pd.DataFrame({"time_ns":np.rint(force_t*1e9).astype(np.int64),"force":np.full(len(force_t),force)}),
                    "position":pd.DataFrame({"time_ns":np.rint(position_t*1e9).astype(np.int64),"X":speed*np.cos(theta)*position_t,"Y":speed*np.sin(theta)*position_t}),
                }
                filename = f"{surface}_{direction}_{speed}_{round(force*1000)}_{repeat}.parquet"
                for modality,frame in frames.items():
                    path = raw/"sensor_data"/modality/str(surface)/filename
                    path.parent.mkdir(parents=True,exist_ok=True); frame.to_parquet(path,index=False)
    write_json(root/"data/source.json",{"source_kind":"synthetic","generator_seed":"surface_id","config_hash":cfg["config_hash"]})
    print("Synthetic fixtures generated; these are engineering inputs, not physical measurements.",flush=True)
