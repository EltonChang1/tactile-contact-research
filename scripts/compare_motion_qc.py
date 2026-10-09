"""Compare native-rate motion smoothers using training recordings only."""
from pathlib import Path
import json
import pandas as pd

from tactile_contact.audit import load_record,steady_interval
from tactile_contact.config import load_config

cfg = load_config("configs/pilot.yaml")
manifest = pd.read_csv("data/manifests/recordings.csv")
train = manifest[manifest.surface_id.isin(cfg["train_ids"])]
rows = []
for n in [11,21,31]:
    rules = dict(cfg["qc"],motion_smoothing_samples=n)
    spans = []
    for row in train.itertuples():
        frames,times,_ = load_record(Path("data/raw/cluster"),row.recording_id)
        start,end,_ = steady_interval(frames,times,row.speed_mm_s,rules)
        spans.append(end-start)
    result = {"native_position_samples":n,"full_half_second_windows":sum(d >= .5 for d in spans),
              "training_recordings":len(spans),"minimum_duration_s":min(spans)}
    rows.append(result)
    print(result,flush=True)
Path("docs/motion_qc_comparison.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
