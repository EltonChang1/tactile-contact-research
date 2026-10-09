# Brief Contact Research

A working development pipeline for the public-data stage of the [research plan](docs/research_plan.md) and [refined guide](docs/implementation_guide.md). It predicts vibration band power from brief observed contacts and requested interaction conditions.

The first implementation downloads a bounded, revision-pinned Cluster subset, audits synchronized channels, extracts nested support prefixes, constructs matched support/query episodes, fits three baselines and a small masked encoder, and saves validation predictions and provenance. This is an implemented development milestone. Specimen families and sensor timing still require review before a scientific evaluation.

## Current result

The real pilot uses ten training surfaces, two provisional validation surfaces, 0.5-second support/query windows, and four common query conditions. All three initialization seeds ran successfully. Retrieval outperformed the initial network on this development set; no learned-model advantage is established. See [development status](docs/development_status.md) for the audit decisions and limitations.

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
| `results/tables/` | Query/surface scores, raw predictions, baseline fits, retrieval provenance, wrong-support assignment, development bootstrap |
| `results/figures/` | Synchronized pilot plots and validation error figure |
| `results/run_manifest.json`, `environment.lock.txt` | Configuration, data/software hashes, seeds/checkpoints, runtime |

Run `python -m tactile_contact figures --config configs/pilot.yaml` with the environment interpreter to regenerate the validation figure from the saved summary table. Generated data, models, and results are ignored by Git; the source, configurations, protocol, and tests are versionable.

## Evaluation contract

- Surface IDs and family groups construct splits and pair records; they never enter predictor tensors.
- Prediction inputs contain permitted support spectra/conditions/duration and requested query conditions. Query measurements are retrieved through a separate target accessor.
- Every protocol excludes the union of all support conditions from primary queries. A different repetition of an observed condition is also excluded.
- Training may use both query repetitions; fixed validation queries use repeat 1. Retrieval averages the training responses in linear power before logging.
- All methods use the same eligible cohort and common query set. Checkpoint selection averages within surface and then equally across protocol/duration cells.
- Metrics average queries within surface, then surfaces; model seeds are averaged within surface for the paired retrieval comparison. Family-group bootstrap supports reviewed groups, but the current Cluster groups are placeholders.

## Next implementation milestone

Review specimen relationships and the acquisition/delivery clock, expand the bounded pilot to the planned condition grid, and add fixed-feature regression and speed rescaling. Then run matched duration and second-probe comparisons with a separately fitted omitted-speed experiment. The scientific protocol must be finalized before adding a locked test split. Force rigs, friction identification, engine integration, and control remain subsequent stages.
