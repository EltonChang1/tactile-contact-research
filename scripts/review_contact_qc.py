"""Training-only, prespecified motion/heading/load diagnostics; no model fitting."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tactile_contact.audit import CHANNELS, load_record, steady_interval
from tactile_contact.config import load_config, recording_permitted, validate_source, file_hash, write_json
from tactile_contact.qc_review import support_diagnostics, fit_heading_frame, wrap_degrees
from tactile_contact.records import parse_record_name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=Path("configs/qc_review.json"))
    args = parser.parse_args()
    spec = json.loads(args.review.read_text())
    cfg = load_config(spec["source_config"])
    validate_source(Path("."), cfg)
    convention_path = Path("configs/clock_convention.json")
    convention = json.loads(convention_path.read_text())
    if any(cfg[key] != convention[key] for key in ["time_base", "sampling_rate_hz"]) or convention["physical_acquisition_clock_verified"]:
        raise ValueError("Contact review expects the declared uncalibrated logged-coordinate convention")
    raw = Path("data/raw/cluster")
    inventory = {row["path"]: row["sha256"] for row in json.loads(Path("data/raw_inventory.json").read_text())["files"]}
    sensitivity, diagnostics, identities = [], [], []
    for surface in cfg["train_ids"]:
        for speed, direction, force in cfg["conditions"]:
            if not recording_permitted(cfg, surface, speed):
                continue
            for repeat in [0, 1]:
                record = f"{surface}_{direction}_{speed}_{int(force*1000)}_{repeat}"
                row = parse_record_name(record+".parquet")
                for channel in CHANNELS:
                    path = raw/f"sensor_data/{channel}/{surface}/{record}.parquet"
                    sha = file_hash(path)
                    if inventory[path.relative_to(raw).as_posix()] != sha:
                        raise ValueError(f"Raw inventory mismatch: {path}")
                    identities.append(dict(path=path.as_posix(), sha256=sha))
                frames, times, _ = load_record(raw, record)
                for variant in spec["variants"]:
                    rules = dict(cfg["qc"], **variant["overrides"])
                    result = dict(recording_id=record, surface_id=surface, speed_mm_s=speed,
                        direction_deg=direction, nominal_force_N=force, repeat_id=repeat,
                        variant=variant["name"], valid=False, duration_s=0., half_second_available=False,
                        one_second_available=False, exclusion_reason="")
                    try:
                        start, end, _ = steady_interval(frames, times, speed, rules)
                        result.update(valid=True, start_s=start, end_s=end, duration_s=end-start,
                            half_second_available=end-start >= .5, one_second_available=end-start >= 1.)
                        if variant["name"] == "current" and end-start >= spec["diagnostic_support_duration_s"]:
                            features = support_diagnostics(frames, times, start, spec["diagnostic_support_duration_s"], rules["motion_smoothing_samples"])
                            diagnostic = dict(row, start_s=start, duration_s=spec["diagnostic_support_duration_s"], **features)
                            diagnostic["nominal_distance_mm"] = speed*spec["diagnostic_support_duration_s"]
                            diagnostic["travel_to_nominal_ratio"] = features["logged_position_travel_mm"]/diagnostic["nominal_distance_mm"]
                            diagnostic["force_mean_to_nominal_ratio"] = features["force_time_weighted_mean_N"]/force
                            for channel, t in times.items():
                                dt = np.diff(t)
                                diagnostic.update({f"{channel}_mean_logged_rate_hz": 1/dt.mean(), f"{channel}_median_logged_rate_hz": 1/np.median(dt),
                                    f"{channel}_max_gap_s": float(dt.max()), f"{channel}_interval_cv": float(dt.std()/dt.mean())})
                            diagnostics.append(diagnostic)
                    except ValueError as exc:
                        result["exclusion_reason"] = str(exc)
                        # A diagnostic failure must not silently redefine pipeline eligibility.
                        if result["valid"]:
                            raise
                    sensitivity.append(result)
        print("Reviewed training specimen", surface, flush=True)
    detail, variants = pd.DataFrame(diagnostics), pd.DataFrame(sensitivity)
    best, candidates = fit_heading_frame(detail.observed_heading_deg, detail.direction_deg)
    detail["heading_residual_deg"] = wrap_degrees(detail.observed_heading_deg-(best["offset_deg"]+best["sign"]*detail.direction_deg))
    detail["heading_absolute_residual_deg"] = detail.heading_residual_deg.abs()
    summaries = variants.groupby("variant", sort=False).agg(recordings=("recording_id", "size"), valid=("valid", "sum"),
        half_second_available=("half_second_available", "sum"), one_second_available=("one_second_available", "sum"),
        minimum_duration_s=("duration_s", "min"), median_duration_s=("duration_s", "median")).reset_index()
    conditions = detail.groupby(["speed_mm_s", "direction_deg", "nominal_force_N"]).agg(recordings=("recording_id", "size"),
        heading_abs_median_deg=("heading_absolute_residual_deg", "median"), heading_abs_max_deg=("heading_absolute_residual_deg", "max"),
        force_ratio_median=("force_mean_to_nominal_ratio", "median"), force_ratio_min=("force_mean_to_nominal_ratio", "min"),
        force_ratio_max=("force_mean_to_nominal_ratio", "max"), force_trend_abs_median_N=("force_trend_change_N", lambda s: s.abs().median()),
        travel_ratio_median=("travel_to_nominal_ratio", "median"), travel_ratio_min=("travel_to_nominal_ratio", "min"),
        travel_ratio_max=("travel_to_nominal_ratio", "max")).reset_index()
    artifacts = []
    for name, table in [("records", detail), ("sensitivity_records", variants), ("sensitivity", summaries), ("conditions", conditions)]:
        path = Path(f"docs/contact_qc_{name}.csv")
        table.to_csv(path, index=False, lineterminator="\n")
        artifacts.append(dict(path=path.as_posix(), sha256=file_hash(path)))
    make_figure(detail)
    artifacts.append(dict(path="docs/figures/contact_qc_review.png", sha256=file_hash("docs/figures/contact_qc_review.png")))
    write_json("docs/contact_qc_provenance.json", dict(review_id=spec["review_id"], config_hash=cfg["config_hash"],
        convention_id=convention["convention_id"], convention_sha256=file_hash(convention_path),
        review_sha256=file_hash(args.review), source_revision=cfg["revision"],
        source_hashes={Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix(): file_hash(path)
                       for path in [__file__, "src/tactile_contact/qc_review.py", "src/tactile_contact/audit.py"]},
        accessed_raw_files=identities, accessed_surface_ids=cfg["train_ids"], accessed_speeds_mm_s=sorted(detail.speed_mm_s.unique().tolist()),
        selected_heading_frame=best, heading_frame_candidates=candidates, diagnostic_recordings=len(detail),
        requested_recordings=len(variants)/len(spec["variants"]), outputs=artifacts,
        limitations="Training-only 10 conditions, 0/45/90 degrees. Global heading frame is diagnostic, not calibration or a new eligibility filter. Force rows are not independent. Logged time remains uncalibrated. Pipeline QC and model fits unchanged."))
    print(summaries.to_string(index=False), flush=True)
    print(best, flush=True)


def make_figure(detail):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for load, subset in detail.groupby("nominal_force_N"):
        label = f"Nominal {load:g} N"
        axes[0].scatter(subset.direction_deg, subset.heading_residual_deg, s=12, alpha=.5, label=label)
        axes[1].scatter(subset.speed_mm_s, subset.force_mean_to_nominal_ratio, s=12, alpha=.5)
        axes[2].scatter(subset.speed_mm_s, subset.travel_to_nominal_ratio, s=12, alpha=.5)
    axes[0].set(xlabel="Nominal direction (degrees)", ylabel="Global-frame heading residual (degrees)")
    axes[0].axhline(0, color="gray", linewidth=.8); axes[0].legend(fontsize=8)
    axes[1].set(xlabel="Nominal speed (mm/s)", ylabel="Mean recorded force / nominal load")
    axes[2].set(xlabel="Nominal speed (mm/s)", ylabel="Logged-position travel / nominal distance")
    for ax in axes[1:]:
        ax.axhline(1, color="gray", linewidth=.8)
    fig.suptitle("Training-only 0.5 logged-second contacts; diagnostic frame, uncalibrated timing")
    fig.tight_layout()
    Path("docs/figures").mkdir(exist_ok=True)
    fig.savefig("docs/figures/contact_qc_review.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
