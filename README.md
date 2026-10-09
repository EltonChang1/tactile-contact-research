# Brief Contact Research

A working development pipeline for the public-data stage of the [research plan](docs/research_plan.md) and [refined guide](docs/implementation_guide.md). It predicts vibration band power from brief observed contacts and requested interaction conditions.

The implementation downloads bounded, revision-pinned Cluster subsets, audits synchronized channels, extracts nested support prefixes, constructs matched episodes, fits five baselines and a small masked encoder, and saves validation predictions and provenance. The expanded pilot covers five probe protocols and three durations. Sensor timing and manufacturing-family relationships still require review before a scientific evaluation.

## Current result

The expanded real pilot uses ten training surfaces, two provisional validation surfaces, five protocols, 0.25/0.5/1-second supports, and the original four common query conditions. Three model seeds completed. Retrieval remains ahead of fixed-feature regression and the encoder; wrong support now substantially worsens the encoder's predictions. See the [expanded pilot report](docs/expanded_pilot_report.md), [timing audit](docs/timing_audit.md), and [specimen review](docs/specimen_group_audit.md).

The separately fitted [omitted-speed experiment](docs/omitted_speed_report.md) now evaluates 30/50 mm/s after fitting and selecting only on 20/40/60 mm/s. In its single 0.5-second cell, fixed-feature regression scores 0.310 MAE, encoder 0.316, and interpolated retrieval 0.330. The encoder/retrieval difference is inconclusive on two specimens. This experiment uses different query conditions from the earlier pilot; its raw MAE is not a direct before/after comparison.

Synthetic fixtures also exercise all five probe protocols and 0.25/0.5/1-second supports. They check engineering behavior, not physical accuracy. Locked test evaluation, mechanics, and simulation are later milestones.

## Install

Python 3.12. In PowerShell, from this directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

For a particular CPU/CUDA PyTorch build, install it in that environment using the [official selector](https://pytorch.org/get-started/locally/) before installing the package. The local bootstrap reused installed numerical packages through `--system-site-packages`; the run's `results/environment.lock.txt` records that actual environment. A clean environment can use the commands above. Downloads use Python's HTTPS client and require no Hugging Face credentials.

## Run the bounded real pilot

```powershell
.\.venv\Scripts\python.exe -m tactile_contact download --config configs/pilot.yaml
.\.venv\Scripts\python.exe -m tactile_contact audit --config configs/pilot.yaml
.\.venv\Scripts\python.exe -m tactile_contact prepare --config configs/pilot.yaml
.\.venv\Scripts\python.exe -m tactile_contact run --config configs/pilot.yaml --reuse
```

`run` without `--reuse` regenerates preparation first. `--reuse` requires matching configuration hashes. After changing preparation or feature code, run `prepare` again rather than reusing older caches. Raw downloads are immutable; hashes are checked on subsequent downloads. The default selection is 362 files, approximately 35 MB, rather than the full dataset.

## Run the expanded comparison

```powershell
.\.venv\Scripts\python.exe -m tactile_contact download --config configs/expanded_pilot.yaml --root runs/expanded_pilot --data-root .
.\.venv\Scripts\python.exe -m tactile_contact run --config configs/expanded_pilot.yaml --root runs/expanded_pilot --data-root .
.\.venv\Scripts\python.exe -m tactile_contact timing --config configs/expanded_pilot.yaml --root runs/expanded_pilot --data-root .
.\.venv\Scripts\python.exe scripts/summarize_expanded_pilot.py --root runs/expanded_pilot
```

The expanded selection has 578 files, approximately 62.5 MB. `--data-root .` shares pinned raw downloads with the initial pilot; preparation, fitted models, and results stay under `runs/expanded_pilot`. Reuse now also checks preparation source-code hashes. The four query conditions remain fixed while three additional support conditions enable the other protocols. This is a bounded development expansion; the full 76-condition scientific grid is still pending.

## Run the globally omitted-speed experiment

```powershell
.\.venv\Scripts\python.exe -m tactile_contact download --config configs/omitted_speed.yaml --root runs/omitted_speed --data-root .
.\.venv\Scripts\python.exe -m tactile_contact run --config configs/omitted_speed.yaml --root runs/omitted_speed --data-root .
.\.venv\Scripts\python.exe -m tactile_contact timing --config configs/omitted_speed.yaml --root runs/omitted_speed --data-root .
.\.venv\Scripts\python.exe scripts/summarize_omitted_speed.py --root runs/omitted_speed
```

This selection verifies 770 files (91.9 MB). Training 30/50 mm/s recordings are skipped even if present in a shared cache. Known-speed responses select models; omitted-speed targets are read only after all methods and checkpoints are selected. The 2,100 episodes are labeled `fit` (1,800), `selection` (180), and `transfer` (120). Endpoint queries use 45/90 degrees and nominal 1 N so they stay outside the excluded support conditions.

Selection and transfer each have their own tables/figures under `results/tables/<partition>/` and `results/figures/<partition>/`. The combined summary and raw prediction arrays retain partition labels. Retrieval interpolates log band power from 20/40 or 40/60 mm/s using same-direction/load training endpoints, with exact source IDs and weights saved in `retrieval_prediction_sources.json`.

## Run the synthetic check separately

```powershell
.\.venv\Scripts\python.exe -m tactile_contact synth --config configs/synthetic.yaml --root runs/synthetic_check
.\.venv\Scripts\python.exe -m tactile_contact run --config configs/synthetic.yaml --root runs/synthetic_check
.\.venv\Scripts\python.exe -m pytest -q
```

Synthetic data must use their own output root when measured data already exist. Configuration paths are relative to the shell's current directory; `--root` selects where data and outputs live.

## Outputs

| Location | Contents |
| --- | --- |
| `data/source.json`, `data/raw_inventory.json` | Pinned source, selected specimens, original file hashes |
| `data/manifests/recordings.csv` | Channel timing, loading, retrospective steady intervals, QC/exclusions |
| `data/manifests/surfaces.csv`, `split_materials.csv` | Names, categories, editable family groups, review flags, splits |
| `data/manifests/windows.csv`, `episodes.csv`, `eligibility.csv` | Exact windows, budgets, common queries, missing supports |
| `data/features/` | Full PSDs, band powers, train-only scaler, scaler fit-window IDs |
| `runs/<configuration hash>/seed_*/` | Selected checkpoints, training histories, configurations |
| `results/tables/` | Query/surface scores, raw predictions, baseline fits/selection, retrieval provenance, wrong-support assignment, paired budget contrasts, named subsets, clock sensitivity |
| `results/figures/` | Synchronized pilot plots and validation error figure |
| `results/run_manifest.json`, `environment.lock.txt` | Configuration, data/software hashes, seeds/checkpoints, runtime |

Run `python -m tactile_contact figures --config configs/pilot.yaml` with the environment interpreter to regenerate the validation figure from the saved summary table. Generated data, models, and results are ignored by Git; the source, configurations, protocol, and tests are versionable.

## Evaluation contract

- Surface IDs and family groups construct splits and pair records; they never enter predictor tensors.
- Prediction inputs contain permitted support spectra/conditions/duration and requested query conditions. Query measurements are retrieved through a separate target accessor.
- Every protocol excludes the union of all support conditions from primary queries. A different repetition of an observed condition is also excluded.
- Training may use both query repetitions; fixed validation queries use repeat 1. Retrieval averages the training responses in linear power before logging.
- All methods use the same eligible cohort and common query set. Checkpoint selection averages within surface and then equally across protocol/duration cells.
- Metrics average queries within surface, then surfaces; model seeds are averaged within surface before paired comparisons. The expanded specimen review covers available names; manufacturing-family independence remains unresolved.
- Fixed-feature ridge uses mean/std of permitted support vectors, count, and query conditions, with training-only scaling and validation-selected regularization. Rescaling uses the full support PSD, train-fitted speed/load exponents, and validation selection; its angular rule ignores residual direction mismatch.
- Regression weights total one per training specimen so repeating query labels across protocol/duration cells does not silently change ridge regularization.
- Globally omitted speeds have a separately fitted configuration and library. Fitting/selection APIs reject transfer episodes; transfer targets stay unread until every checkpoint is selected.

## Next implementation milestone

Resolve acquisition/delivery timing and complete family review, then extend the common condition grid and inspect condition/surface-level errors. Preserve both familiar-condition and omitted-speed outcomes when choosing the next development decisions. The scientific protocol must be finalized before adding a locked test split. Force rigs, friction identification, engine integration, and control remain subsequent stages.
