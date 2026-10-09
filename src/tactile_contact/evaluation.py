from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .metrics import paired_bootstrap
from .signal import rms_from_log_power
from .config import write_json


def score_predictions(episodes, prediction, target, method, seed, floor, retrieved=None):
    if prediction.shape != target.shape or not np.isfinite(prediction).all():
        raise ValueError("Predictor returned invalid response shape/values")
    out = episodes.copy()
    out["model"] = method; out["seed"] = seed
    out["log_power_mae"] = np.abs(prediction-target).mean(axis=1)
    axes,total = rms_from_log_power(prediction,floor)
    true_axes,true_total = rms_from_log_power(target,floor)
    for index,name in enumerate(["X","Y","Z"]):
        out[f"rms_error_{name}"] = np.abs(axes[:,index]-true_axes[:,index])
    out["modeled_band_total_rms_error"] = np.abs(total-true_total)
    out["retrieved_training_id"] = retrieved if retrieved is not None else np.nan
    return out


def summarize(root,cfg,scores):
    root = Path(root)
    destination = root/"results/tables"
    destination.mkdir(parents=True,exist_ok=True)
    scores.to_csv(destination/"per_query.csv",index=False)
    metrics = ["log_power_mae","modeled_band_total_rms_error"]
    per_surface = scores.groupby(["model","seed","protocol","duration_s","surface_id","family_group"],as_index=False)[metrics].mean()
    per_surface.to_csv(destination/"per_surface.csv",index=False)
    # Collapse seeds within each surface before any surface-level aggregation.
    seed_mean = per_surface.groupby(["model","protocol","duration_s","surface_id","family_group"],as_index=False)[metrics].mean()
    table = seed_mean.groupby(["model","protocol","duration_s"],as_index=False)[metrics].mean()
    counts = seed_mean.groupby(["model","protocol","duration_s"]).surface_id.nunique().rename("surfaces")
    table = table.merge(counts.reset_index(),on=["model","protocol","duration_s"])
    table.to_csv(destination/"summary.csv",index=False)
    comparison = []
    for (protocol,duration),part in seed_mean.groupby(["protocol","duration_s"]):
        pivot = part.pivot(index=["surface_id","family_group"],columns="model",values="log_power_mae")
        if "encoder" in pivot and "retrieval" in pivot:
            pair = pivot[["retrieval","encoder"]].dropna()
            result = paired_bootstrap(pair.retrieval.to_numpy(),pair.encoder.to_numpy(),pair.index.get_level_values("family_group").to_numpy(),draws=2000)
            comparison.append({"protocol":protocol,"duration_s":duration,**result})
    write_json(destination/"paired_comparisons.json",{"stage":"development","config_hash":cfg["config_hash"],"comparisons":comparison,
        "interpretation":"Small provisional validation cohort; intervals are debugging output, not scientific evidence or test results."})
    make_figures(root,cfg,table)
    return table


def make_figures(root,cfg,summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    destination = root/"results/figures"
    fig,ax = plt.subplots(figsize=(9,5))
    for method,rows in summary.groupby("model"):
        single = rows[rows.protocol == "single"].sort_values("duration_s")
        if not single.empty:
            ax.plot(single.duration_s,single.log_power_mae,marker="o",label=method)
    ax.set_xlabel("Observed steady-contact time (s)"); ax.set_ylabel("Per-surface log10 band-power MAE")
    ax.set_title(f"{cfg['source_kind']} development validation — no scientific claims")
    ax.legend(); fig.tight_layout(); fig.savefig(destination/"validation_errors.png",dpi=130); plt.close(fig)


def wrong_support(episodes):
    surfaces = sorted(episodes.surface_id.unique())
    if len(surfaces) < 2:
        raise ValueError("Wrong-support control requires two eligible validation surfaces")
    mapping = dict(zip(surfaces,surfaces[1:]+surfaces[:1]))
    supports = {(r.surface_id,r.protocol,r.duration_s):r.support_window_ids for r in episodes.itertuples()}
    result = episodes.copy()
    for i,row in result.iterrows():
        result.loc[i,"support_window_ids"] = supports[(mapping[row.surface_id],row.protocol,row.duration_s)]
    return result
