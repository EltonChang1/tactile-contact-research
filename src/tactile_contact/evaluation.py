from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .metrics import paired_bootstrap
from .signal import rms_from_log_power
from .config import write_json, PROTOCOLS


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


def summarize(root,cfg,scores,partition=None):
    root = Path(root)
    destination = root/"results/tables"
    if partition is None and "evaluation_partition" in scores and scores.evaluation_partition.nunique() > 1:
        destination.mkdir(parents=True,exist_ok=True)
        scores.to_csv(destination/"per_query.csv",index=False)
        tables,surfaces = [],[]
        for name,part in scores.groupby("evaluation_partition",sort=True):
            tables.append(summarize(root,cfg,part,partition=name).assign(evaluation_partition=name))
            surfaces.append(pd.read_csv(destination/name/"per_surface.csv").assign(evaluation_partition=name))
        table = pd.concat(tables,ignore_index=True)
        table.to_csv(destination/"summary.csv",index=False)
        pd.concat(surfaces,ignore_index=True).to_csv(destination/"per_surface.csv",index=False)
        return table
    if partition:
        destination = destination/partition
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
    diagnostic_tables(destination,cfg,scores)
    budget_contrasts(destination,seed_mean,scores)
    make_figures(root,cfg,table,partition)
    return table


def diagnostic_tables(destination,cfg,scores):
    """Each named subset applies to every method and publishes its condition list."""
    subsets = {
        "same_direction":pd.Series(False,index=scores.index),
        "unobserved_load":(scores.protocol != "load") & (scores.query_nominal_force_N == 1.),
        "load_observed_both":(scores.protocol == "load") & (scores.query_nominal_force_N == 1.),
        "unobserved_direction":pd.Series(False,index=scores.index),
    }
    observed_angles = {c[1] for p in cfg["protocols"] for c in PROTOCOLS[p]}
    subsets["matched_unobserved_direction"] = ~scores.query_direction_deg.isin(observed_angles)
    for protocol in cfg["protocols"]:
        angles = {c[1] for c in PROTOCOLS[protocol]}
        selected = scores.protocol == protocol
        subsets["same_direction"] |= selected & scores.query_direction_deg.isin(angles)
        subsets["unobserved_direction"] |= selected & ~scores.query_direction_deg.isin(angles)
    rows,conditions = [],{}
    for name,selected in subsets.items():
        part = scores[selected]
        if part.empty:
            continue
        per_surface = part.groupby(["model","protocol","duration_s","surface_id"],as_index=False)[
            ["log_power_mae","modeled_band_total_rms_error"]].mean()
        summary = per_surface.groupby(["model","protocol","duration_s"],as_index=False).agg(
            log_power_mae=("log_power_mae","mean"),modeled_band_total_rms_error=("modeled_band_total_rms_error","mean"),
            surfaces=("surface_id","nunique"))
        counts = part.groupby(["model","protocol","duration_s"]).query_window_id.nunique().rename("query_windows")
        summary = summary.merge(counts.reset_index(),on=["model","protocol","duration_s"])
        summary["subset"] = name; rows.append(summary)
        conditions[name] = {protocol:group[["query_speed_mm_s","query_direction_deg","query_nominal_force_N"]]
                            .drop_duplicates().sort_values(["query_speed_mm_s","query_direction_deg","query_nominal_force_N"])
                            .to_numpy().tolist() for protocol,group in part.groupby("protocol")}
    if rows:
        pd.concat(rows,ignore_index=True).to_csv(destination/"diagnostic_subsets.csv",index=False)
    write_json(destination/"diagnostic_conditions.json",conditions)


def budget_contrasts(destination,per_surface,scores):
    """Match query identities before comparing probe choice or total contact time."""
    comparisons = []
    for protocol in ["repeat","speed","load","direction"]:
        comparisons.extend([("equal_total_time","single",1.,protocol,.5),
                            ("equal_total_time","single",.5,protocol,.25)])
        if protocol != "repeat":
            comparisons.append(("second_probe_choice","repeat",.5,protocol,.5))
    rows = []
    for label,a,da,b,db in comparisons:
        left = per_surface[(per_surface.protocol == a) & (per_surface.duration_s == da)]
        right = per_surface[(per_surface.protocol == b) & (per_surface.duration_s == db)]
        if left.empty or right.empty:
            continue
        query_sets = []
        for protocol,duration in [(a,da),(b,db)]:
            part = scores[(scores.protocol == protocol) & (scores.duration_s == duration)]
            query_sets.append(set(zip(part.surface_id,part.query_window_id)))
        if query_sets[0] != query_sets[1]:
            raise ValueError("Budget contrast has unmatched query identities")
        paired = left.merge(right,on=["model","surface_id","family_group"],suffixes=("_a","_b"),validate="one_to_one")
        if len(paired) != len(left) or len(paired) != len(right):
            raise ValueError("Budget contrast has unmatched methods/surfaces")
        for model,part in paired.groupby("model"):
            result = paired_bootstrap(part.log_power_mae_a.to_numpy(),part.log_power_mae_b.to_numpy(),
                                      part.family_group.to_numpy(),draws=2000)
            rows.append({"contrast":label,"model":model,"protocol_a":a,"duration_a_s":da,
                "protocol_b":b,"duration_b_s":db,"total_time_a_s":len(PROTOCOLS[a])*da,
                "total_time_b_s":len(PROTOCOLS[b])*db,
                "distance_a_mm":sum(c[0]*da for c in PROTOCOLS[a]),
                "distance_b_mm":sum(c[0]*db for c in PROTOCOLS[b]),
                "mean_mae_a":float(part.log_power_mae_a.mean()),"mean_mae_b":float(part.log_power_mae_b.mean()),
                "mean_improvement_b":result["mean_improvement"],"ci95_low":result["ci95"][0],
                "ci95_high":result["ci95"][1],"surfaces":result["surfaces"],"independent_groups":result["independent_groups"]})
    if rows:
        pd.DataFrame(rows).to_csv(destination/"budget_contrasts.csv",index=False)


def make_figures(root,cfg,summary,partition=None):
    if partition is None and "evaluation_partition" in summary:
        for name,part in summary.groupby("evaluation_partition",sort=True):
            make_figures(root,cfg,part,partition=name)
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    destination = root/"results/figures"
    if partition:
        destination = destination/partition
    destination.mkdir(parents=True,exist_ok=True)
    fig,ax = plt.subplots(figsize=(9,5))
    for method,rows in summary.groupby("model"):
        single = rows[rows.protocol == "single"].sort_values("duration_s")
        if not single.empty:
            ax.plot(single.duration_s,single.log_power_mae,marker="o",label=method)
    ax.set_xlabel("Observed steady-contact time (s)"); ax.set_ylabel("Per-surface log10 band-power MAE")
    ax.set_title(f"{cfg['source_kind']} development {partition or 'validation'} — no scientific claims")
    ax.legend(); fig.tight_layout(); fig.savefig(destination/"validation_errors.png",dpi=130); plt.close(fig)
    fig,axes = plt.subplots(1,len(cfg["protocols"]),figsize=(4*len(cfg["protocols"]),4),sharey=True,squeeze=False)
    for ax,protocol in zip(axes[0],cfg["protocols"]):
        for method,rows in summary[summary.protocol == protocol].groupby("model"):
            rows = rows.sort_values("duration_s")
            ax.plot(rows.duration_s*len(PROTOCOLS[protocol]),rows.log_power_mae,marker="o",label=method)
        ax.set_title(protocol); ax.set_xlabel("Total observed contact time (s)")
    axes[0,0].set_ylabel("Per-surface log10 band-power MAE")
    handles,labels = axes[0,-1].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",ncol=4,fontsize=8)
    fig.suptitle(f"Matched development {partition or 'cohort'}; observed contact excludes setup time")
    fig.tight_layout(rect=(0,.12,1,1)); fig.savefig(destination/"probe_budget_errors.png",dpi=130); plt.close(fig)


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
