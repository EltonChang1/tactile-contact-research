from __future__ import annotations

from math import gcd
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import resample_poly

from .audit import load_record
from .config import PROTOCOLS, FORBIDDEN, data_root
from .signal import spectral_features


def uniform_acceleration(frame, t, fs):
    """Provisional delivery-clock grid, followed by anti-aliased rate conversion.

    Never interpolate across a gap larger than the upstream frozen QC threshold.
    The source grid uses rounded median logged rate; this is not acquisition proof.
    """
    source_rate = max(int(round(1/np.median(np.diff(t)))), int(fs))
    count = int(np.floor((t[-1]-t[0])*source_rate)) + 1
    source_t = t[0] + np.arange(count)/source_rate
    source = np.column_stack([np.interp(source_t,t,frame[axis]) for axis in ["X","Y","Z"]])
    factor = gcd(int(fs),source_rate)
    values = resample_poly(source,int(fs)//factor,source_rate//factor,axis=0,padtype="line")
    output_t = t[0] + np.arange(len(values))/fs
    valid = output_t <= t[-1]
    return values[valid], output_t[valid], source_rate


def extract_windows(root, cfg, manifest):
    root = Path(root)
    raw = data_root(root,cfg)/"data/raw"/cfg["source_kind"]
    cache = root/"data/features"/cfg["config_hash"]
    cache.mkdir(parents=True,exist_ok=True)
    requested_support = {c for p in cfg["protocols"] for c in PROTOCOLS[p]}
    rows = []
    for record in manifest[manifest.qc_status == "valid"].itertuples():
        condition = (record.speed_mm_s,record.direction_deg,record.nominal_force_N)
        key = condition + (record.repeat_id,)
        split = "train" if record.surface_id in cfg["train_ids"] else "val"
        if key in requested_support:
            roles = [("support",d) for d in cfg["durations_s"]]
        elif condition not in FORBIDDEN and (split == "train" or record.repeat_id == 1):
            roles = [("query",cfg["query_duration_s"])]
        else:
            continue
        frames,times,_ = load_record(raw,record.recording_id)
        array,t_grid,source_rate = uniform_acceleration(frames["accel"],times["accel"],cfg["sampling_rate_hz"])
        start_index = int(np.searchsorted(t_grid,record.steady_start_s))
        for role,duration in roles:
            n = round(duration*cfg["sampling_rate_hz"])
            end_index = start_index+n
            if end_index > len(array) or t_grid[start_index]+duration > record.steady_end_s:
                continue
            feature = spectral_features(array[start_index:end_index],fs=cfg["sampling_rate_hz"],floor=cfg["power_floor"])
            window_id = f"{record.recording_id}_{role}_{duration:g}_{cfg['config_hash'][:12]}"
            path = cache/f"{window_id}.npz"
            np.savez_compressed(path,**feature)
            rows.append({"window_id":window_id,"recording_id":record.recording_id,
                         "surface_id":record.surface_id,"split":split,"role":role,
                         "duration_s":duration,"start_s":t_grid[start_index],"end_s":t_grid[start_index]+duration,
                         "speed_mm_s":record.speed_mm_s,"direction_deg":record.direction_deg,
                         "nominal_force_N":record.nominal_force_N,"repeat_id":record.repeat_id,
                         "feature_path":path.relative_to(root).as_posix(),"source_grid_hz":source_rate,
                         "raw_start_index":int(np.searchsorted(times["accel"],t_grid[start_index])),
                         "raw_end_index_exclusive":int(np.searchsorted(times["accel"],t_grid[start_index]+duration)),
                         "window_config_hash":cfg["config_hash"],"time_base_id":cfg["time_base"]})
    windows = pd.DataFrame(rows)
    if windows.empty:
        raise ValueError("No full-length windows pass the selected QC rules")
    windows.to_csv(root/"data/manifests/windows.csv",index=False)
    return windows
