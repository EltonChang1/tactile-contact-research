# Brief Contact Research

A working development pipeline for the public-data stage of the [research plan](docs/research_plan.md) and [refined guide](docs/implementation_guide.md). It predicts vibration band power from brief observed contacts and requested interaction conditions.

The implementation downloads bounded, revision-pinned Cluster subsets, audits synchronized channels, extracts nested support prefixes, constructs matched episodes, fits five baselines and a small masked encoder, and saves validation predictions and provenance. The expanded pilot covers five probe protocols and three durations. Continued development uses declared logged coordinates; physical timing calibration, manufacturing-family relationships and a fresh scientific test remain unresolved.

## Current result

The expanded real pilot uses ten training surfaces, two provisional validation surfaces, five protocols, 0.25/0.5/1-second supports, and the original four common query conditions. Three model seeds completed. Retrieval remains ahead of fixed-feature regression and the encoder; wrong support now substantially worsens the encoder's predictions. See the [expanded pilot report](docs/expanded_pilot_report.md), [timing audit](docs/timing_audit.md), and [specimen review](docs/specimen_group_audit.md).

The separately fitted [omitted-speed experiment](docs/omitted_speed_report.md) now evaluates 30/50 mm/s after fitting and selecting only on 20/40/60 mm/s. In its single 0.5-second cell, fixed-feature regression scores 0.310 MAE, encoder 0.316, and interpolated retrieval 0.330. The encoder/retrieval difference is inconclusive on two specimens. This experiment uses different query conditions from the earlier pilot; its raw MAE is not a direct before/after comparison.

The [boundary correction](docs/window_boundary_report.md) now crops raw acceleration before interpolation/filtering, with local padding and dependency provenance. At that milestone, 53 tests passed and outside-sample perturbations left all 688 measured prepared windows bit-for-bit unchanged. Three fresh reruns preserve the original cohorts/episodes. Expanded retrieval/encoder MAE is 0.1726/0.2513; omitted fixed features/encoder/retrieval is 0.3096/0.3141/0.3300. The main findings are unchanged. Physical timing remains unverified; all 12 specimens stay development-exposed.

Synthetic fixtures also exercise all five probe protocols and 0.25/0.5/1-second supports. They check engineering behavior, not physical accuracy. Locked test evaluation, mechanics, and simulation are later milestones.

The [clock/QC review](docs/clock_qc_review.md) compared 15 original CSVs with the mirror: rounded timestamps and float32 signals match exactly. The acquisition-rate discrepancy persists, so [logged_coordinates_v1](configs/clock_convention.json) explicitly limits duration/frequency claims. Across its 200 training records, current QC retains every half-second and 199 one-second intervals; mean force is typically about 5% above nominal. That milestone passed 62 tests. No model or eligibility rule changed.

The [complete metadata/exposure review](docs/study_design_review.md) now covers all 118 specimens in 87 conservative groups. Twelve direct exposures block 22 specimens from a fresh test; twenty metadata-only specimens in fifteen groups are reserved before wider sensor review. [Condition masks](configs/query_domains.csv) define the 76/44/26 domains and a 70-condition familiar fitting pool for the matched omitted-speed contrast. Manufacturing independence and locked test evaluation remain unestablished.

The [wider known-speed audit](docs/wider_coverage_review.md) now covers 960 training records across all eight directions. Every record retains half a second; all required one-second supports and 44 common query triples survive on all ten training specimens. Median recorded force is 2.9% above nominal. Current QC remains unchanged. **70 tests pass.** No reserved signals or new model fits are part of this milestone.

The [training diagnostic review](docs/development_diagnostics_review.md) now checks 480 repeat pairs, including 440 known-query pairs. Mean query repeat difference is **0.173 log-power units**, with much higher variability on specimens 102/103. The numerical floor has negligible influence; retain current features and QC. All six expanded/omitted model histories reach 60 epochs while still improving, and primary-cell histories were not saved. That 9 October milestone passed **78 tests** and motivated the finite extension completed below; reserved signals remained untouched.

The [controlled extension](docs/convergence_review_report.md) is now complete: all six runs exactly reproduce their first-60 histories, checkpoint tensors and predictions, then continue under a finite 120 cap. Familiar encoder MAE improves **0.2513 → 0.2049**, with retrieval still leading at **0.1726**. Omitted transfer encoder MAE becomes **0.3245** (previously 0.3141), while RMS error improves; fixed features still lead MAE at 0.3096. Four runs hit the cap, two stop through patience. Adopt the [finite development policy](configs/development_training_policy.json) without a cap chase. **85 tests pass.** Reserved specimens remain untouched; no scientific test has run.

## Install

Python 3.12. In PowerShell, from this directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

For a particular CPU/CUDA PyTorch build, install it in that environment using the [official selector](https://pytorch.org/get-started/locally/) before installing the package. The local bootstrap reused installed numerical packages through `--system-site-packages`; the run's `results/environment.lock.txt` records that actual environment. A clean environment can use the commands above. Downloads use Python's HTTPS client and require no Hugging Face credentials.

## Run the current bounded real pilot

```powershell
.\.venv\Scripts\python.exe -m tactile_contact download --config configs/pilot.yaml --root runs/bounded_pilot --data-root .
.\.venv\Scripts\python.exe -m tactile_contact prepare --config configs/pilot.yaml --root runs/bounded_pilot --data-root .
.\.venv\Scripts\python.exe -m tactile_contact run --config configs/pilot.yaml --root runs/bounded_pilot --data-root . --reuse
```

`run` without `--reuse` regenerates preparation first. `--reuse` requires matching configuration hashes. After changing preparation or feature code, run `prepare` again rather than reusing older caches. Raw downloads are immutable; hashes are checked on subsequent downloads. The default selection is 362 files, approximately 35 MB, rather than the full dataset.

## Run the expanded comparison

```powershell
.\.venv\Scripts\python.exe -m tactile_contact download --config configs/expanded_pilot.yaml --root runs/bounded_expanded_pilot --data-root .
.\.venv\Scripts\python.exe -m tactile_contact run --config configs/expanded_pilot.yaml --root runs/bounded_expanded_pilot --data-root .
.\.venv\Scripts\python.exe -m tactile_contact timing --config configs/expanded_pilot.yaml --root runs/bounded_expanded_pilot --data-root .
```

The expanded selection has 578 files, approximately 62.5 MB. `--data-root .` shares pinned raw downloads with the initial pilot; preparation, fitted models, and results stay under `runs/bounded_expanded_pilot`. Reuse now also checks preparation source-code hashes. The four query conditions remain fixed while three additional support conditions enable the other protocols. This is a bounded development expansion; the full 76-condition scientific grid is still pending.

## Run the globally omitted-speed experiment

```powershell
.\.venv\Scripts\python.exe -m tactile_contact download --config configs/omitted_speed.yaml --root runs/bounded_omitted_speed --data-root .
.\.venv\Scripts\python.exe -m tactile_contact run --config configs/omitted_speed.yaml --root runs/bounded_omitted_speed --data-root .
.\.venv\Scripts\python.exe -m tactile_contact timing --config configs/omitted_speed.yaml --root runs/bounded_omitted_speed --data-root .
```

This selection verifies 770 files (91.9 MB). Training 30/50 mm/s recordings are skipped even if present in a shared cache. Known-speed responses select models; omitted-speed targets are read only after all methods and checkpoints are selected. The 2,100 episodes are labeled `fit` (1,800), `selection` (180), and `transfer` (120). Endpoint queries use 45/90 degrees and nominal 1 N so they stay outside the excluded support conditions.

Selection and transfer each have their own tables/figures under `results/tables/<partition>/` and `results/figures/<partition>/`. The combined summary and raw prediction arrays retain partition labels. Retrieval interpolates log band power from 20/40 or 40/60 mm/s using same-direction/load training endpoints, with exact source IDs and weights saved in `retrieval_prediction_sources.json`.

## Regenerate the boundary audit/report

After the three corrected runs and the two timing commands above:

```powershell
.\.venv\Scripts\python.exe scripts/summarize_window_boundary.py
```

This comparison also requires the retained historical local roots: the project root for the initial run, `runs/expanded_pilot`, and `runs/omitted_speed`. A clean clone can reproduce corrected runs, but before/after auditing requires historical runs reconstructed with their recorded code/environment. Historical report exporters reject corrected runs to prevent mixing versions. Current outputs use `runs/bounded_*`; previous outputs and aggregate reports remain intact. The new report exports all method matrices, paired contrasts, a 688-window dependency/perturbation audit, feature changes and provenance.

## Run the synthetic check separately

```powershell
.\.venv\Scripts\python.exe -m tactile_contact synth --config configs/synthetic.yaml --root runs/synthetic_check
.\.venv\Scripts\python.exe -m tactile_contact run --config configs/synthetic.yaml --root runs/synthetic_check
.\.venv\Scripts\python.exe -m pytest -q
```

Synthetic data must use their own output root when measured data already exist. Configuration paths are relative to the shell's current directory; `--root` selects where data and outputs live.

## Reproduce clock and contact review

After the omitted-speed download above, from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/audit_source_clock.py
.\.venv\Scripts\python.exe scripts/review_contact_qc.py
```

The source comparison fetches selected original archive members with validated HTTP ranges under a 32 MiB cap. Contact diagnostics use only cached known-speed training records, with a [prespecified sensitivity review](configs/qc_review.json). Both export derived tables/provenance in `docs/`; original CSVs stay ignored under `runs/clock_qc_review/source`. See the report for scope, rates, global heading frame, load/travel diagnostics and limitations.

## Reproduce metadata/reservation and wider coverage

```powershell
.\.venv\Scripts\python.exe scripts/prepare_study_design.py
.\.venv\Scripts\python.exe scripts/prepare_study_design.py --check-config configs/omitted_speed.yaml
.\.venv\Scripts\python.exe scripts/review_wider_coverage.py --download
.\.venv\Scripts\python.exe scripts/summarize_wider_coverage.py
```

The design script reviews pinned metadata and uses the committed historical exposure snapshot on a clean clone. `--audit-local` additionally audits six historical run roots/cache names. The wider runner enforces the whole-group reservation before downloads and accesses only the ten existing training specimens at 20/40/60 mm/s. New selections through the original experiment CLI need the explicit reservation preflight; locked test access/scoring is still future work. Outputs are derived tables/hash provenance, with raw files ignored.

## Reproduce training diagnostics

After the wider QC audit and the three corrected bounded runs:

```powershell
.\.venv\Scripts\python.exe scripts/review_development_diagnostics.py
```

The runner checks reservation, complete recording identities, audited QC and raw hashes before signal use. It exports repeat pairs, floor/range sensitivity, saved learning curves, figures and provenance under `docs/development_diagnostics_*`. It fits no model and reads no reserved, selection or training omitted-speed signals. See the [review](docs/development_diagnostics_review.md) for interpretation and the controlled convergence follow-up.

## Reproduce the controlled convergence extension

After the corrected expanded/omitted runs exist with their recorded histories, checkpoints and environment:

```powershell
.\.venv\Scripts\python.exe scripts/review_convergence.py
```

The new default root `runs/convergence_120` must not exist. The runner rejects overwrite, checks exact first-60 reproduction, saves primary/equal-cell histories and both checkpoint budgets, and seals every selection before reading transfer targets or historical score arrays. Baseline fits remain unchanged. Public tables and a figure are under `docs/convergence_review_*`; full predictions/checkpoints stay ignored. A repeated reconstruction requires an explicit copied review config with a new `output_root`. See the report for limitations and source/input hashes.

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

Run `python -m tactile_contact figures --config configs/pilot.yaml --root runs/bounded_pilot` with the environment interpreter to regenerate the validation figure from the saved summary table. Generated data, models, and results are ignored by Git; the source, configurations, protocol, and tests are versionable.

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

The raw acceleration boundary, logged-coordinate scope, metadata/exposure/reservation, training coverage, repeat/feature diagnostics and finite convergence check are complete. Four trajectories remain cap-limited; the finite 120 policy does not claim asymptotic convergence. Next complete repetition reversal, residual analysis, wider selection/transfer coverage and matched-grid familiar/omitted fitting. Protect reserved groups while freezing scientific margins, protocol/access/scoring. Mechanics requires independently calibrated force measurements; an encoder victory is not its gate.
