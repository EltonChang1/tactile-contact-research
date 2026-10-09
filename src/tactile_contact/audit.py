from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import write_json, data_root, validate_source, recording_permitted
from .records import parse_record_name


CHANNELS = {"accel": ["X", "Y", "Z"], "force": ["force"], "position": ["X", "Y"]}


def load_record(raw, recording_id):
    surface = recording_id.split("_")[0]
    frames = {m: pd.read_parquet(Path(raw)/"sensor_data"/m/surface/f"{recording_id}.parquet") for m in CHANNELS}
    for name, frame in frames.items():
        if not set(["time_ns"] + CHANNELS[name]).issubset(frame.columns):
            raise ValueError(f"Missing {name} columns")
        if not pd.api.types.is_integer_dtype(frame.time_ns):
            raise ValueError(f"{name} timestamps must remain integer nanoseconds")
        if len(frame) < 3 or not np.isfinite(frame[["time_ns"] + CHANNELS[name]].to_numpy()).all():
            raise ValueError(f"Invalid {name} samples")
        if (np.diff(frame.time_ns.to_numpy()) <= 0).any():
            raise ValueError(f"Nonmonotonic/duplicate {name} timestamps; no automatic sorting")
    origin = min(int(f.time_ns.min()) for f in frames.values())
    times = {m: (f.time_ns.to_numpy() - origin)/1e9 for m, f in frames.items()}
    return frames, times, origin


def motion_speed(position, t, smoothing_samples=11):
    values = position[["X", "Y"]].to_numpy(dtype=float)
    # Fit against actual native timestamps. Differentiating at each jittery interval
    # creates artificial speed spikes even after index-based position smoothing.
    window = min(smoothing_samples, len(values))
    half = window//2
    velocity = np.empty_like(values)
    for i in range(len(t)):
        start = max(0,min(i-half,len(t)-window))
        selected = slice(start,start+window)
        coefficients = np.polynomial.polynomial.polyfit(t[selected]-t[i],values[selected],2)
        velocity[i] = coefficients[1]
    return np.linalg.norm(velocity, axis=1)


def steady_interval(frames, times, nominal_speed, rules):
    for channel, t in times.items():
        threshold = rules["max_accel_gap_s"] if channel == "accel" else rules["max_aux_gap_s"]
        if np.diff(t).max() > threshold:
            raise ValueError(f"{channel} gap exceeds frozen development threshold")
    t = times["position"]
    speed = motion_speed(frames["position"], t, rules.get("motion_smoothing_samples",11))
    force = np.interp(t, times["force"], frames["force"].force, left=np.nan, right=np.nan)
    tolerance = max(rules["speed_absolute_tolerance_mm_s"], rules["speed_relative_tolerance"]*nominal_speed)
    valid = ((np.abs(speed-nominal_speed) <= tolerance) & (force > rules["min_normal_force_N"])
             & (t >= times["accel"][0]) & (t <= times["accel"][-1]))
    edges = np.diff(np.r_[False, valid, False].astype(int))
    spans = [(t[start], t[end-1]) for start, end in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))]
    if not spans:
        raise ValueError("No valid steady contact interval")
    start, end = max(spans, key=lambda pair: pair[1]-pair[0])
    return float(start), float(end), speed


def build_manifest(root, cfg):
    root = Path(root)
    validate_source(root,cfg)
    raw = data_root(root,cfg)/"data/raw"/cfg["source_kind"]
    requested = set(cfg["train_ids"] + cfg["val_ids"])
    conditions = {tuple(c) for c in cfg["conditions"]}
    rows = []
    for path in sorted(raw.glob("sensor_data/accel/*/*.parquet")):
        row = parse_record_name(path)
        if row["surface_id"] not in requested or (row["speed_mm_s"], row["direction_deg"], row["nominal_force_N"]) not in conditions:
            continue
        if not recording_permitted(cfg,row["surface_id"],row["speed_mm_s"]):
            continue
        for channel in CHANNELS:
            row[f"{channel}_path"] = (raw/"sensor_data"/channel/str(row["surface_id"])/path.name).resolve().as_posix()
        row.update(qc_status="excluded", qc_reason="", steady_start_s=np.nan, steady_end_s=np.nan,
                   usable_duration_s=0., config_hash=cfg["config_hash"])
        try:
            frames, times, origin = load_record(raw, row["recording_id"])
            row["origin_ns"] = origin
            for channel, t in times.items():
                dt = np.diff(t)
                row.update({f"{channel}_rows": len(t), f"{channel}_logged_rate_hz": 1/np.median(dt),
                            f"{channel}_mean_rate_hz": 1/np.mean(dt), f"{channel}_max_gap_s": dt.max(),
                            f"{channel}_interval_cv": dt.std()/dt.mean(), f"{channel}_duration_s": t[-1]-t[0]})
            row["accel_fraction_at_16g"] = float((np.abs(frames["accel"][["X","Y","Z"]].to_numpy()) >= 15.99).mean())
            start, end, _ = steady_interval(frames, times, row["speed_mm_s"], cfg["qc"])
            row.update(steady_start_s=start, steady_end_s=end, usable_duration_s=end-start, qc_status="valid")
            mask = (times["force"] >= start) & (times["force"] <= end)
            row["measured_force_mean_N"] = float(frames["force"].force.to_numpy()[mask].mean())
            row["measured_force_std_N"] = float(frames["force"].force.to_numpy()[mask].std())
        except (ValueError, FileNotFoundError) as exc:
            row["qc_reason"] = str(exc)
        rows.append(row)
    manifest = pd.DataFrame(rows)
    if manifest.empty:
        raise ValueError("No requested acceleration recordings found; download or synthesize data first")
    target = root/"data/manifests"
    target.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(target/"recordings.csv", index=False)
    expected = sum(2 for surface in requested for speed,_,_ in conditions if recording_permitted(cfg,surface,speed))
    summary = {"source_kind": cfg["source_kind"], "config_hash": cfg["config_hash"],
               "expected_recordings": expected, "found_recordings": len(rows),
               "qc_valid": int((manifest.qc_status == "valid").sum()),
               "qc_excluded": int((manifest.qc_status != "valid").sum()),
               "timestamp_warning": "Logged intervals do not establish sensor acquisition rate. Time-base choice is provisional."}
    write_json(target/"audit_summary.json", summary)
    make_surfaces(root, cfg, raw)
    make_audit_figures(root, manifest, raw, cfg)
    print(summary, flush=True)
    return manifest


def make_surfaces(root, cfg, raw):
    metadata_path = raw/"texture_list.xlsx"
    metadata = pd.read_excel(metadata_path).set_index("Texture_id") if metadata_path.exists() else None
    path = root/"data/manifests/surfaces.csv"
    old = pd.read_csv(path).set_index("surface_id") if path.exists() else None
    review_path = cfg.get("specimen_groups_path")
    reviewed = pd.read_csv(review_path).set_index("surface_id") if review_path else None
    if reviewed is not None and (reviewed.index.duplicated().any() or not set(cfg["train_ids"]+cfg["val_ids"]).issubset(reviewed.index)):
        raise ValueError("Specimen review needs unique entries for every requested surface")
    rows = []
    for surface in cfg["train_ids"] + cfg["val_ids"]:
        row = {"surface_id": surface, "name": f"synthetic_{surface}" if cfg["source_kind"] == "synthetic" else "unknown",
               "category": "synthetic" if metadata is None else str(metadata.loc[surface,"Category"]).replace("\\n"," ").strip(),
               "family_group": f"specimen_{surface}", "grouping_reason": "unreviewed specimen placeholder",
               "grouping_reviewed": cfg["source_kind"] == "synthetic",
               "split": "train" if surface in cfg["train_ids"] else "val"}
        if metadata is not None:
            row["name"] = str(metadata.loc[surface,"Texture_Name (en)"])
        if old is not None and surface in old.index:
            for field in ["family_group", "grouping_reason", "grouping_reviewed"]:
                row[field] = old.loc[surface, field]
        if reviewed is not None:
            for field in ["family_group", "grouping_reason", "grouping_reviewed"]:
                row[field] = reviewed.loc[surface,field]
            row["grouping_scope"] = reviewed.loc[surface,"grouping_scope"]
        if not isinstance(row["grouping_reviewed"],(bool,np.bool_)):
            raise ValueError("Grouping review flag must be a Boolean")
        row.setdefault("grouping_scope","synthetic_fixture" if cfg["source_kind"] == "synthetic" else "unreviewed")
        rows.append(row)
    surfaces = pd.DataFrame(rows)
    if surfaces.family_group.isna().any() or (surfaces.family_group.str.strip() == "").any():
        raise ValueError("Missing family groups")
    if (surfaces.groupby("family_group").split.nunique() > 1).any():
        raise ValueError("Specimen family crosses training/validation split")
    surfaces.to_csv(path,index=False)
    surfaces[["surface_id","family_group","split","grouping_reviewed"]].to_csv(path.with_name("split_materials.csv"),index=False)


def make_audit_figures(root, manifest, raw, cfg):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    target = root/"results/figures/audit"
    target.mkdir(parents=True,exist_ok=True)
    for surface in cfg["train_ids"] + cfg["val_ids"]:
        subset = manifest[(manifest.surface_id == surface) & (manifest.qc_status == "valid")]
        if subset.empty:
            continue
        reference = subset[(subset.speed_mm_s == 40) & (subset.direction_deg == 0) & (subset.nominal_force_N == .5)]
        row = (reference if not reference.empty else subset).iloc[0]
        frames, times, _ = load_record(raw, row.recording_id)
        fig, axes = plt.subplots(3,1,sharex=True,figsize=(9,6))
        axes[0].plot(times["accel"],frames["accel"][["X","Y","Z"]]); axes[0].set_ylabel("Acceleration (g)")
        axes[1].plot(times["force"],frames["force"].force); axes[1].axhline(row.nominal_force_N,color="gray",ls="--"); axes[1].set_ylabel("Normal force (N)")
        axes[2].plot(times["position"],motion_speed(frames["position"],times["position"],cfg["qc"].get("motion_smoothing_samples",11))); axes[2].axhline(row.speed_mm_s,color="gray",ls="--"); axes[2].set_ylabel("Speed (mm/s)"); axes[2].set_xlabel("Joint-origin logged time (s)")
        for ax in axes:
            ax.axvspan(row.steady_start_s,row.steady_end_s,color="green",alpha=.1)
            ax.axvspan(row.steady_start_s,row.steady_start_s+.5,color="orange",alpha=.15)
        fig.suptitle(f"{row.recording_id} — retrospective QC; timing provisional")
        fig.tight_layout(); fig.savefig(target/f"surface_{surface}.png",dpi=120); plt.close(fig)
