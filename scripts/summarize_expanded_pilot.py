"""Publish compact derived development tables; raw measurements stay outside Git."""
import argparse
import json
from pathlib import Path
import shutil

import pandas as pd

from tactile_contact.config import file_hash, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root",default="runs/expanded_pilot")
    parser.add_argument("--output",default="docs")
    args = parser.parse_args()
    root,destination = Path(args.root),Path(args.output)
    tables = root/"results/tables"
    destination.mkdir(parents=True,exist_ok=True)
    manifest = json.loads((root/"results/run_manifest.json").read_text())
    episode = json.loads((root/"data/manifests/episode_summary.json").read_text())
    timing = json.loads((tables/"timing_sensitivity.json").read_text())
    fixed = json.loads((tables/"fixed_features_selection.json").read_text())
    rescaling = json.loads((tables/"speed_rescaling_fit.json").read_text())
    if timing["config_hash"] != manifest["config"]["config_hash"]:
        raise ValueError("Clock sensitivity and model runs have different configurations")
    summary = pd.read_csv(tables/"summary.csv")
    primary = summary[(summary.protocol == "single") & (summary.duration_s == .5)].sort_values("log_power_mae")
    required = {"conditions_only","copy","retrieval","fixed_features","speed_rescaling","encoder","encoder_wrong_support"}
    if set(primary.model) != required:
        raise ValueError("Incomplete method comparison")
    for name in ["summary.csv","budget_contrasts.csv","diagnostic_subsets.csv"]:
        (destination/f"expanded_pilot_{name}").write_bytes((tables/name).read_text(encoding="utf-8").encode("utf-8"))
    (destination/"expanded_pilot_diagnostic_conditions.json").write_bytes(
        (tables/"diagnostic_conditions.json").read_text(encoding="utf-8").encode("utf-8"))
    figures = destination/"figures"; figures.mkdir(exist_ok=True)
    shutil.copyfile(root/"results/figures/probe_budget_errors.png",figures/"expanded_probe_budget.png")
    lines = ["# Expanded development pilot — 8 October 2026", "",
        "The expanded pipeline completed five support protocols and 0.25/0.5/1-second observations on the original ten training and two development validation specimens. All 192 recordings passed QC. Preparation produced 268 windows and 1,320 episodes (1,200 training, 120 validation). Four distinct query conditions per specimen remain fixed across every method and protocol; validation uses repeat 1. These are development results, with no locked test evaluated.", "",
        "## Primary development cell", "",
        "Single 0.5-second support; per-query error averaged within each specimen and then across the two specimens. Encoder rows average the three initialization seeds within specimen. Lower values are better.", "",
        "| Method | Log10 band-power MAE | Modeled-band RMS error (m/s²) |", "| --- | ---: | ---: |"]
    for row in primary.itertuples():
        lines.append(f"| {row.model} | {row.log_power_mae:.4f} | {row.modeled_band_total_rms_error:.4f} |")
    lines += ["", "The encoder improves on the initial pilot's approximately 0.791 MAE, but retrieval and fixed-feature regression remain stronger. Expanded training samples cover multiple cells and early stopping selects later epochs, so this change does not isolate the effect of any single probe. Wrong-surface support now increases encoder error substantially. That is evidence of surface dependence within this tiny development cohort; it does not establish a generalization advantage.", "",
        "## Matched budgets and probe choice", "",
        "The exports compare single 1-second contact against two 0.5-second contacts, single 0.5-second contact against two 0.25-second contacts, and repetition against alternative second probes at 0.5 seconds per contact. Query identities are checked before pairing. Total observed time and sliding distance are recorded; setup and repositioning are excluded.", "",
        "| Method | Repeat 2×0.5 s | Direction 2×0.5 s | Speed 2×0.5 s | Load 2×0.5 s |", "| --- | ---: | ---: | ---: | ---: |"]
    for model in ["retrieval","fixed_features","encoder"]:
        values = summary[(summary.model == model) & (summary.duration_s == .5)].set_index("protocol").log_power_mae
        lines.append(f"| {model} | {values['repeat']:.4f} | {values['direction']:.4f} | {values['speed']:.4f} | {values['load']:.4f} |")
    lines += ["", "Retrieval selects the same training specimen for each held-out specimen across all tested budgets, producing the same response predictions. The encoder favors direction over repetition in this pilot, while fixed-feature regression shows little change. Two specimens and four query conditions cannot establish a preferred probe scientifically. Longer support does not consistently lower every method's error. All contrasts and bootstrap intervals are retained as provisional diagnostics rather than equivalence or significance claims.", "",
        "![Matched protocol and duration curves](figures/expanded_probe_budget.png)", "",
        "## Fitting and diagnostic limits", "",
        f"Fixed-feature regression uses mean/std of permitted support vectors, count, and requested conditions; five declared ridge candidates select alpha {fixed['selected_alpha']:g} on development validation. Both support-feature scaling and regression-feature scaling fit training observations only. Regression sample weights total one per specimen, so duplicating query labels across cells does not change regularization strength.", "",
        f"Direction-agnostic rescaling uses the full support PSD and `s^(p-1) r^b S(f/s)`. Above-floor training band powers fit global speed/load exponents; three ridge candidates select alpha {rescaling['selected_alpha']:g}, p={rescaling['p']:.4f}, b={rescaling['b']:.4f} on validation. These are empirical development parameters, not verified material laws. Source-frequency extrapolation is rejected. The support-selection rule prioritizes angle, speed ratio, then protocol order; unused contacts do not automatically improve this baseline.", "",
        "Named diagnostics score every method on same-direction queries, protocol-specific unobserved directions/loads, and the common unobserved-direction intersection. Condition lists and sample counts are saved. These are familiar-condition experiments; 30/50 mm/s labels were used in fitting, so they are not an omitted-speed test.", "",
        f"The training-only clock sensitivity covers {timing['training_windows']} windows: median nominal index/logged duration ratio {timing['median_index_to_logged_duration_ratio']:.4f}, median feature MAE {timing['median_log_power_mae_between_paths']:.4f}. See the [timing audit](timing_audit.md). The [specimen review](specimen_group_audit.md) covers available names; fabrication-family independence remains unresolved.", "",
        "## Reproduction and next work", "",
        "Commands and isolated output roots are in the [README](../README.md). Versioned aggregate exports: [full method matrix](expanded_pilot_summary.csv), [budget contrasts](expanded_pilot_budget_contrasts.csv), [named subsets](expanded_pilot_diagnostic_subsets.csv), and [run provenance](expanded_pilot_provenance.json). Raw predictions, per-specimen errors, checkpoints, raw-file hashes, and environment lock remain in the local run directory.", "",
        "Next: establish timing, complete the family review, broaden the common query grid, then refit a separate globally omitted-speed experiment. Preserve these pilot outcomes while investigating the encoder gap. Mechanical identification, simulation, and control have not begun.", ""]
    (destination/"expanded_pilot_report.md").write_text("\n".join(lines),encoding="utf-8")
    write_json(destination/"expanded_pilot_provenance.json",{
        "stage":manifest["stage"],"source":manifest["source"],"config_hash":manifest["config"]["config_hash"],
        "manifest_hashes":manifest["manifest_hashes"],"software_hashes":manifest["software_hashes"],
        "specimen_groups_hash":manifest["config"]["specimen_groups_hash"],"episode_summary":episode,
        "training_seeds":manifest["config"]["training"]["seeds"],"timing_sensitivity":timing,
        "exported_table_hashes":{f"expanded_pilot_{name}":file_hash(destination/f"expanded_pilot_{name}")
                                  for name in ["summary.csv","budget_contrasts.csv","diagnostic_subsets.csv"]},
        "claim_limit":manifest["claim_limit"]})
    print(primary.to_string(index=False))
    print(f"Saved derived pilot report and aggregate tables under {destination.resolve()}")


if __name__ == "__main__":
    main()
