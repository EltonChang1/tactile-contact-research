# Running and reproducing the experiments

This is the technical companion to the [plain-language project overview](../README.md). Run every command below from the repository root, even though this document is under `docs/`.

The commands cover the preserved development experiments and later matched comparison. Earlier reports and test counts are dated milestones. The [latest matched report](matched_development_review.md) and [independent validation](matched_validation_review.md) describe the current findings. Verification requires the saved local recordings, fitted models and their recorded sources/environment; raw data and models are ignored by Git. Completed audit/fit roots reject overwrite.

## Install

Python 3.12. In PowerShell, from the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

For a particular CPU/CUDA PyTorch build, install it in that environment using the [official selector](https://pytorch.org/get-started/locally/) before installing the package. The local bootstrap reused installed numerical packages through `--system-site-packages`; the run's `results/environment.lock.txt` records that actual environment. A clean environment can use the commands above. Downloads use Python's HTTPS client and require no Hugging Face credentials.

## Run the bounded real pilot

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

## Run the bounded omitted-speed experiment

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

The source comparison fetches selected original archive members with validated HTTP ranges under a 32 MiB cap. Contact diagnostics use only cached known-speed training records, with a [prespecified sensitivity review](../configs/qc_review.json). Both export derived tables/provenance in `docs/`; original CSVs stay ignored under `runs/clock_qc_review/source`. See the report for scope, rates, global heading frame, load/travel diagnostics and limitations.

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

The runner checks reservation, complete recording identities, audited QC and raw hashes before signal use. It exports repeat pairs, floor/range sensitivity, saved learning curves, figures and provenance under `docs/development_diagnostics_*`. It fits no model and reads no reserved, selection or training omitted-speed signals. See the [review](development_diagnostics_review.md) for interpretation and the controlled convergence follow-up.

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

**Frozen repetition reversal completed 10 October:** the [review](repetition_review_report.md) restores all five baseline fits and six 120-budget checkpoints without refitting. All 22 forward prediction arrays reproduce exactly; 88 complementary windows pass outside-sample checks and all cells remain included. Familiar encoder MAE changes 0.2049 → 0.2500, omitted transfer 0.3245 → 0.3912, while encoder RMS improves. Direction-versus-repeat encoder contrasts change sign in all three domains; no stable direction benefit is established. Specimen 10 shows greater deterioration; retrieval identities are stable in 29/30 specimen/protocol/duration cells per experiment. Both orientations change support and target recordings, so effects are not attributable solely to supports. That milestone passed **92 tests**. Keep current models/QC/features and all specimens; the subsequent coverage reviews and matched fitting are complete; scientific freeze and locked scoring remain pending. Reserved specimens remain untouched.

Run the frozen diagnostic with `.venv/Scripts/python.exe scripts/review_repetition.py`, then verify it with `.venv/Scripts/python.exe scripts/validate_repetition_review.py`. It requires the preserved bounded roots and completed convergence checkpoints; it rejects an existing output root. All fits remain frozen, and raw data/full predictions stay ignored.

**Matched selection/transfer coverage completed 10 October:** the [audit](selection_transfer_coverage_review.md) reviews 296 triplets on development specimens 10/57, both repetitions, in an isolated raw root that preserves historical inventory/source hashes. All half-second queries and all sixteen one-second supports survive; all 44 selection and 26 transfer triples remain common at every support duration, yielding 420 eligible specimen/query/duration cells. Ten query records lack one second but meet their half-second target budget. Retain current QC; no predictions or models changed. That coverage milestone passed **100 tests**. The [matched 70/44 specification](../configs/matched_development_review.json) is prepared with the 120-cap policy. The subsequent training audit and guarded matched execution are complete, as reported below. Reserved-test scoring has not run.

**Matched training coverage and 70/44 fitting completed 10 October:** the [training audit](transfer_training_coverage_review.md) retains all 520 safe transfer-speed half-second queries and every common training cell. The [matched comparison](matched_development_review.md) separately fits familiar 70 versus omitted 44 queries with identical known-speed selection and 26 transfer targets, retaining both validation orientations. Single-0.5 forward transfer MAE is retrieval **0.1494 → 0.3119**, fixed features **0.2987 → 0.3188**, encoder **0.3517 → 0.3550**; reverse is 0.1462 → 0.3089, 0.3004 → 0.3178 and 0.3658 → 0.3953. The encoder does not lead, and transfer direction/repeat contrasts change sign. Two of six new trajectories hit the finite 120 cap. All ten baseline and six encoder selections precede preparation of 192 deferred validation targets; all 1,878 windows pass outside-acceleration invariance. **110 tests pass.** Reserved specimens remain untouched. Practical/secondary policy, scientific cohort/full-76 coverage and guarded locked scoring remain gates.

Reproduce the coverage audit with `.venv/Scripts/python.exe scripts/review_selection_transfer_coverage.py --download`, then `.venv/Scripts/python.exe scripts/validate_selection_transfer_coverage.py`. The completed audit root is protected. Public QC tables are under `docs/selection_transfer_qc_*`; raw data remains ignored.

## Reproduce the matched development comparison

After both coverage audits and the wider known-speed audit:

```powershell
.venv/Scripts/python.exe scripts/review_transfer_training_coverage.py --download
.venv/Scripts/python.exe scripts/run_matched_development.py
.venv/Scripts/python.exe scripts/validate_matched_review.py
```

The [execution configuration](../configs/matched_fit_review.json) references the preserved prepared role/budget specification and audited recordings. Completed roots reject overwrite; reconstruction requires explicit new roots and recorded sources/environment. Full predictions, fitted artifacts and raw data stay ignored. See the [matched report](matched_development_review.md) for all methods, both orientations, finite histories, access guards and residuals.

## Verify the saved matched results

With the completed matched run and its prerequisites preserved:

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe scripts/validate_matched_review.py --staged
.venv/Scripts/python.exe scripts/verify_matched_results.py
.venv/Scripts/python.exe scripts/verify_matched_raw_features.py
```

The replay verifier checks every saved prediction, score, summary, residual and contrast. The raw verifier reconstructs every feature window and checks that acceleration outside the allowed interval cannot affect it. These commands fit no new model and access no reserved specimen. See the [validation report](matched_validation_review.md) for exact counts, source hashes and environment checks.
