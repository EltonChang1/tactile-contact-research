from __future__ import annotations

from math import gcd
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import resample_poly

from .audit import load_record
from .config import PROTOCOLS, FORBIDDEN, data_root, recording_permitted
from .signal import spectral_features


PROCESSING_BOUNDARY = "raw_window_v1"


def prepare_acceleration_window(frame, t, start, duration, fs):
    """Crop raw observations first; every signal dependency stays in [start, end).

    The grid rate is estimated from allowed timestamps only. Interpolation holds
    the local first/last sample at grid edges; polyphase line padding also uses
    only local endpoints. Padding is derived data, not extra observed context.
    Logged coordinates remain provisional, and onset/QC is retrospective.
    """
    t = np.asarray(t, dtype=np.float64)
    if t.ndim != 1 or len(t) != len(frame) or len(t) < 3 or not np.isfinite(t).all() or (np.diff(t) <= 0).any():
        raise ValueError("Window preparation requires finite increasing timestamps")
    if not np.isfinite([start, duration, fs]).all() or duration <= 0 or fs <= 0 or int(fs) != fs:
        raise ValueError("Require a finite start, positive duration and integer sampling rate")
    fs = int(fs)
    end = start + duration
    if start < t[0] or end > t[-1]:
        raise ValueError("Declared window lies outside the recorded time span")
    first = int(np.searchsorted(t, start, side="left"))
    stop = int(np.searchsorted(t, end, side="left"))
    local_t = t[first:stop]
    observed = frame.iloc[first:stop][["X", "Y", "Z"]].to_numpy(dtype=np.float64)
    if len(local_t) < 3 or not np.isfinite(observed).all():
        raise ValueError("Insufficient or invalid allowed raw acceleration samples")
    source_rate = max(int(round(1/np.median(np.diff(local_t)))), fs)
    n = round(duration * fs)
    source_count = int(np.ceil(duration * source_rate))
    source_t = start + np.arange(source_count)/source_rate
    # Floating arithmetic can put a nominal final grid point on the open end.
    source_t = source_t[source_t < end]
    source = np.column_stack([np.interp(source_t, local_t, observed[:, axis]) for axis in range(3)])
    factor = gcd(fs, source_rate)
    up, down = fs//factor, source_rate//factor
    values = resample_poly(source, up, down, axis=0, window=("kaiser", 5.0), padtype="line")
    if n < 1 or len(values) < n or start + (n-1)/fs >= end:
        raise ValueError("Local grid cannot provide the declared output sample count")
    provenance = {
        "processing_boundary": PROCESSING_BOUNDARY,
        "raw_start_index": first, "raw_end_index_exclusive": stop,
        "dependency_raw_start_index": first, "dependency_raw_end_index_exclusive": stop,
        "raw_samples": stop-first, "raw_first_time_s": float(local_t[0]),
        "raw_last_time_s": float(local_t[-1]), "observed_context_before_s": 0.,
        "observed_context_after_s": 0., "source_grid_hz": source_rate,
        "source_grid_samples": len(source_t), "output_samples": n,
        "interpolation_padding": "local_endpoint_hold", "resample_padding": "local_line",
        "left_interpolation_padding_s": float(max(0., local_t[0]-source_t[0])),
        "right_interpolation_padding_s": float(max(0., source_t[-1]-local_t[-1])),
        "resample_up": up, "resample_down": down, "filter_window": "kaiser_beta_5",
        "filter_numtaps": 1 if up == down == 1 else 20*max(up, down)+1,
        "source_rate_scope": "allowed_raw_timestamps",
    }
    return values[:n], provenance


def extract_windows(root, cfg, manifest):
    root = Path(root)
    raw = data_root(root,cfg)/"data/raw"/cfg["source_kind"]
    cache = root/"data/features"/cfg["config_hash"]
    cache.mkdir(parents=True,exist_ok=True)
    requested_support = {c for p in cfg["protocols"] for c in PROTOCOLS[p]}
    rows = []
    for record in manifest[manifest.qc_status == "valid"].itertuples():
        if not recording_permitted(cfg,record.surface_id,record.speed_mm_s):
            continue
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
        fs = cfg["sampling_rate_hz"]
        # Preserve the historical canonical output-grid start using timestamps,
        # without reading outside-window acceleration or filtering a recording.
        origin = times["accel"][0]
        start_index = max(0, int(np.ceil((record.steady_start_s-origin)*fs)))
        start = origin + start_index/fs
        if start < record.steady_start_s:
            start_index += 1
            start = origin + start_index/fs
        for role,duration in roles:
            if start+duration > record.steady_end_s:
                continue
            array, dependency = prepare_acceleration_window(frames["accel"],times["accel"],start,duration,fs)
            feature = spectral_features(array,fs=fs,floor=cfg["power_floor"])
            window_id = f"{record.recording_id}_{role}_{duration:g}_{cfg['config_hash'][:12]}"
            path = cache/f"{window_id}.npz"
            np.savez_compressed(path,**feature)
            rows.append({"window_id":window_id,"recording_id":record.recording_id,
                         "surface_id":record.surface_id,"split":split,"role":role,
                         "duration_s":duration,"start_s":start,"end_s":start+duration,
                         "speed_mm_s":record.speed_mm_s,"direction_deg":record.direction_deg,
                         "nominal_force_N":record.nominal_force_N,"repeat_id":record.repeat_id,
                         "feature_path":path.relative_to(root).as_posix(),**dependency,
                         "window_config_hash":cfg["config_hash"],"time_base_id":cfg["time_base"]})
    windows = pd.DataFrame(rows)
    if windows.empty:
        raise ValueError("No full-length windows pass the selected QC rules")
    windows.to_csv(root/"data/manifests/windows.csv",index=False)
    return windows
