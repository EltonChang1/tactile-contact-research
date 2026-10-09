"""Training-only clock sensitivity; neither path proves acquisition timing."""
from pathlib import Path

import numpy as np
import pandas as pd

from .audit import load_record
from .config import data_root, write_json
from .signal import spectral_features


def compare_raw_span(frame, times, start, end, timestamp_feature, fs, floor):
    first = int(np.searchsorted(times,start))
    stop = int(np.searchsorted(times,end))
    values = frame[["X","Y","Z"]].to_numpy()[first:stop]
    indexed = spectral_features(values,fs=fs,floor=floor)
    def peak(feature):
        selected = (feature["frequency_hz"] >= 24) & (feature["frequency_hz"] <= 1000)
        return float(feature["frequency_hz"][selected][np.argmax(feature["psd"][selected].sum(axis=1))])
    return {
        "raw_start_index":first,"raw_end_index_exclusive":stop,"raw_samples":len(values),
        "logged_span_s":float(end-start),"index_duration_at_reported_rate_s":len(values)/fs,
        "mean_logged_rate_in_span_hz":float((len(values)-1)/(times[stop-1]-times[first])),
        "timestamp_peak_hz":peak(timestamp_feature),"reported_rate_index_peak_hz":peak(indexed),
        "log_power_mae_between_paths":float(np.abs(indexed["log_band_power"]-timestamp_feature["log_band_power"]).mean()),
    }


def timing_sensitivity(root,cfg):
    root = Path(root)
    windows = pd.read_csv(root/"data/manifests/windows.csv")
    if set(windows.window_config_hash) != {cfg["config_hash"]}:
        raise ValueError("Timing sensitivity requires matching prepared windows")
    # Do not tune the clock convention from held-out response errors.
    windows = windows[windows.split == "train"]
    raw = data_root(root,cfg)/"data/raw"/cfg["source_kind"]
    rows = []
    for recording,part in windows.groupby("recording_id"):
        frames,times,_ = load_record(raw,recording)
        for row in part.itertuples():
            with np.load(root/row.feature_path) as feature:
                result = compare_raw_span(frames["accel"],times["accel"],row.start_s,row.end_s,
                                          feature,cfg["sampling_rate_hz"],cfg["power_floor"])
            rows.append({"window_id":row.window_id,"surface_id":row.surface_id,"role":row.role,
                         "duration_s":row.duration_s,**result})
    table = pd.DataFrame(rows)
    target = root/"results/tables"
    target.mkdir(parents=True,exist_ok=True)
    table.to_csv(target/"timing_sensitivity.csv",index=False)
    summary = {"config_hash":cfg["config_hash"],"training_windows":len(table),
        "surfaces":int(table.surface_id.nunique()),
        "median_index_to_logged_duration_ratio":float((table.index_duration_at_reported_rate_s/table.logged_span_s).median()),
        "median_log_power_mae_between_paths":float(table.log_power_mae_between_paths.median()),
        "comparison":"Same raw timestamp-selected span: delivery-clock resampling versus contiguous samples interpreted at reported 6000 Hz.",
        "limitation":"Sample-index windows contain more nominal acquisition time and different frequency coordinates; this is sensitivity, not matched-budget evaluation or clock verification."}
    write_json(target/"timing_sensitivity.json",summary)
    print(summary,flush=True)
    return table
