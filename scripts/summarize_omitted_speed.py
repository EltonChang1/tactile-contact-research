"""Export an audited development report without publishing raw recordings."""
import argparse
import json
from pathlib import Path
import shutil

import pandas as pd

from tactile_contact.config import file_hash, write_json, speed_bracket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root",default="runs/omitted_speed")
    parser.add_argument("--output",default="docs")
    args = parser.parse_args()
    root,output = Path(args.root),Path(args.output)
    tables = root/"results/tables"
    output.mkdir(parents=True,exist_ok=True)
    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))
    manifest = read(root/"results/run_manifest.json")
    if manifest.get("processing_boundary"):
        raise ValueError("This exporter preserves the historical pilot; use summarize_window_boundary.py for corrected runs")
    episodes = read(root/"data/manifests/episode_summary.json")
    audit = read(root/"data/manifests/audit_summary.json")
    fit = read(tables/"fit_selection_manifest.json")
    timing = read(tables/"timing_sensitivity.json")
    cfg = manifest["config"]
    if cfg.get("experiment") != "omitted_speed" or manifest["stage"] != "development":
        raise ValueError("Report requires the separately fitted development experiment")
    if fit["fit_speeds_mm_s"] != [20,40,60] or fit["selection_speeds_mm_s"] != [20,40,60]:
        raise ValueError("Fitting/selection included an omitted speed")
    if timing["config_hash"] != cfg["config_hash"]:
        raise ValueError("Timing and model configurations differ")
    rows = read(tables/"retrieval_prediction_sources.json")["predictions"]
    lookup = pd.read_csv(root/"data/manifests/episodes.csv").set_index("episode_id")
    transfer_count = 0
    for row in rows:
        episode = lookup.loc[row["episode_id"]]
        speeds = [key[1] for key in row["response_keys"]]
        if not set(speeds).issubset({20,40,60}):
            raise ValueError("Retrieval used omitted-speed responses")
        if episode.evaluation_partition == "transfer":
            if speeds != list(speed_bracket(episode.query_speed_mm_s)) or row["weights"] != [.5,.5]:
                raise ValueError("Transfer retrieval does not use the declared bracketing rule")
            transfer_count += 1
    if transfer_count != episodes["partition_episode_counts"]["transfer"]:
        raise ValueError("Incomplete transfer retrieval provenance")
    summary = pd.read_csv(tables/"summary.csv")
    primary = summary[(summary.protocol == "single") & (summary.duration_s == .5)]
    for partition in ["selection","transfer"]:
        if primary[primary.evaluation_partition == partition].model.nunique() != 7:
            raise ValueError("Incomplete primary method comparison")
    exports = {"omitted_speed_summary.csv":tables/"summary.csv"}
    for partition in ["selection","transfer"]:
        for name in ["budget_contrasts.csv","diagnostic_subsets.csv","diagnostic_conditions.json","paired_comparisons.json"]:
            exports[f"omitted_speed_{partition}_{name}"] = tables/partition/name
    for name,source in exports.items():
        (output/name).write_bytes(source.read_text(encoding="utf-8").encode("utf-8"))
    figures = output/"figures"; figures.mkdir(exist_ok=True)
    shutil.copyfile(root/"results/figures/transfer/probe_budget_errors.png",figures/"omitted_speed_transfer.png")
    comparison = read(tables/"transfer/paired_comparisons.json")
    paired = next(r for r in comparison["comparisons"] if r["protocol"] == "single" and r["duration_s"] == .5)
    values = primary.pivot(index="model",columns="evaluation_partition",values="log_power_mae")
    rms = primary[primary.evaluation_partition == "transfer"].set_index("model").modeled_band_total_rms_error
    lines = ["# Globally omitted-speed development experiment — 8 October 2026", "",
        "This experiment refits every learned comparator using 20/40/60 mm/s responses only. Those same permitted speeds select regularization and encoder checkpoints on development validation specimens. The 30/50 mm/s targets are read for scoring only after all methods and all three checkpoints are selected. This is a new-condition development evaluation on the existing validation specimens, not a locked scientific test.", "",
        "## Coverage and data separation", "",
        f"The bounded selection verified 770 raw files (91.9 MB). All {audit['found_recordings']} requested recordings passed the current QC rules. Preparation produced 320 windows and {episodes['episode_count']:,} episodes: {episodes['partition_episode_counts']['fit']:,} fitting, {episodes['partition_episode_counts']['selection']} selection, and {episodes['partition_episode_counts']['transfer']} transfer. All ten training and two validation specimens remain eligible across five protocols and three durations.", "",
        "Permitted response conditions are 20/40/60 mm/s × 45/90 degrees × nominal 1 N. Transfer conditions are 30/50 mm/s × those same directions/load. Support protocols are unchanged. The angular/load cells supply permitted bracketing responses outside the union of excluded support conditions; the earlier pilot's 0-degree/0.5 N query cells would need excluded response endpoints under this contract. Results therefore cannot be compared directly with the earlier pilot's four-condition MAE as though only speed withholding changed.", "",
        "The downloader, audit, and extractor exclude omitted-speed training records, including any such files left in a shared raw cache. Scalers, conditions-only fitting, fixed-feature fitting, exponent fitting, retrieval libraries, and checkpoint selection reject transfer episodes. Episode manifests label `fit`, `selection`, and `transfer` explicitly. Selection and transfer metrics/budget contrasts are exported separately.", "",
        "## Primary development result", "",
        "Single 0.5-second support. Errors average within specimen, then across specimens; encoder errors average the three seeds within specimen. Selection conditions and transfer conditions differ, and selection scores were used in tuning.", "",
        "| Method | Permitted-speed selection MAE | Omitted-speed transfer MAE | Transfer RMS error (m/s²) |",
        "| --- | ---: | ---: | ---: |"]
    for model in values.sort_values("transfer").index:
        lines.append(f"| {model} | {values.loc[model,'selection']:.4f} | {values.loc[model,'transfer']:.4f} | {rms.loc[model]:.4f} |")
    lines += ["", "Fixed-feature regression has the lowest transfer log-power MAE in this cell. The encoder narrowly beats interpolated retrieval on that metric, while retrieval has lower transfer RMS error. Neither supports a general learned-model advantage from this development cohort.", "",
        f"The paired retrieval-minus-encoder log-power difference is {paired['mean_improvement']:.4f}; the two-group bootstrap interval is [{paired['ci95'][0]:.4f}, {paired['ci95'][1]:.4f}]. It includes zero and is retained as a small-cohort diagnostic. Wrong support increases encoder transfer MAE, consistent with surface-dependent predictions within these specimens.", "",
        "## Retrieval and matched budgets", "",
        f"For each of the {transfer_count} transfer episodes, retrieval selects a training specimen from permitted support, then interpolates its log band powers between 20/40 mm/s for a 30 mm/s query or 40/60 mm/s for a 50 mm/s query. Both endpoints use the same direction and nominal load; both training response repeats are averaged in linear power before taking logs. Each interpolation weight is 0.5. No omitted-speed response is stored or read by the retrieval fit. Prediction provenance retains exact endpoint window IDs and weights.", "",
        "All protocols and durations use the same eligible specimens and query conditions within each partition. Equal-time comparisons and repeat/direction/speed/load contrasts are reported in the exported tables. The full matrix remains necessary when interpreting probe choice; the primary cell is not selected from favorable budgets.", "",
        "![Omitted-speed probe and duration comparisons](figures/omitted_speed_transfer.png)", "",
        "## Remaining limitations and reproduction", "",
        f"Timing remains provisional. The training-only comparison of {timing['training_windows']} windows gives a median acquisition-index/logged duration ratio of {timing['median_index_to_logged_duration_ratio']:.4f}, and median band-log-power difference {timing['median_log_power_mae_between_paths']:.4f}. Available names have been reviewed, but manufacturing-family independence is unresolved. Nominal 1 N and two query directions are a limited development grid.", "",
        "The original pilot and expanded familiar-condition results remain preserved. Reproduction commands are in the [README](../README.md). Versioned outputs include the [full matrix](omitted_speed_summary.csv), [transfer budget contrasts](omitted_speed_transfer_budget_contrasts.csv), [transfer conditions](omitted_speed_transfer_diagnostic_conditions.json), and [fitting/provenance audit](omitted_speed_provenance.json). Full raw predictions and checkpoint histories remain under the local run root.", "",
        "Next: justify the clock convention and complete fabrication-family review before freezing a scientific split; broaden the query grid and inspect condition/surface-level errors. No mechanical identification, simulator evaluation, or control experiment was run.", ""]
    (output/"omitted_speed_report.md").write_bytes("\n".join(lines).encode("utf-8"))
    provenance = {"stage":manifest["stage"],"experiment":"omitted_speed","source":manifest["source"],
        "config_hash":cfg["config_hash"],"software_hashes":manifest["software_hashes"],
        "manifest_hashes":manifest["manifest_hashes"],"episode_summary":episodes,"fit_selection_manifest":fit,
        "retrieval_transfer_interpolation_rows_verified":transfer_count,"timing_sensitivity":timing,
        "exported_table_hashes":{name:file_hash(output/name) for name in exports},"claim_limit":manifest["claim_limit"]}
    write_json(output/"omitted_speed_provenance.json",provenance)
    print(primary[primary.evaluation_partition == "transfer"].to_string(index=False))
    print(f"Verified {transfer_count} interpolations; exported report under {output.resolve()}")


if __name__ == "__main__":
    main()
