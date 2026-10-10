# Independent validation of matched development — 10 October 2026

The [matched 70/44 development result](matched_development_review.md) survives code review, frozen-fit replay and independent numerical reconstruction. No prediction, numerical or scientific-reporting error was found. The encoder remains behind the stronger baselines, transfer-speed withholding changes retrieval markedly, and no stable transfer direction-probe benefit is established. This validates the recorded development result; it does not establish a fresh scientific test, calibrated physical timing or population inference.

| Verification | Observed result |
| --- | --- |
| Full suite and compilation | **110 tests pass**; all source/scripts/tests compile |
| Frozen fitted-artifact replay | All **22** prediction arrays reproduce bit-for-bit: ten baseline, six encoder and six wrong-support arrays |
| Prediction access boundary | Every query feature is denied during replay inference; only supports are accessible until all predictions finish |
| Direct score reconstruction | **92,400** rows and **462,000** scalar metric checks agree, covering log-power MAE, total modeled-band RMS and all three axis RMS errors |
| Independent aggregation | All **840** summary rows, **1,680** specimen rows and **11,760** primary residual rows agree |
| Independent paired contrasts | All **476** means/signs and interval bounds agree; with two singleton groups, the bootstrap bounds coincide with the minimum/maximum group differences |
| Episode and treatment contracts | All **42,600** training/selection/scoring episodes retain prescribed roles, repeats and budgets; both fits score the same **4,200** episode inputs and byte-identical targets |
| Checkpoint and baseline decisions | All six checkpoints select the first equal-cell history minimum; epoch/patience metadata agrees; both fits' ridge/rescaling choices minimize their recorded known-speed candidate scores |
| Scaler and retrieval treatment | Both scalers exactly reconstruct from the same **150** training-support windows; retained retrieval responses/fingerprints agree, and familiar fitting adds **260** response arrays |
| Raw reconstruction | All **1,878** windows from **1,746** used recordings reconstruct exactly, including **15,024** spectral arrays and dependency records; maximum feature discrepancy is **zero** |
| Outside-interval perturbation | Altering every outside acceleration sample leaves all 1,878 prepared windows and their dependencies unchanged |
| Manifest and provenance | The private window manifest regenerates exactly from frozen QC/configuration; **5,328** pinned raw files and **28** frozen execution source files verify |
| Historical evidence | Earlier reversal, selection/transfer coverage, boundary and diagnostic release checks still pass; execution artifacts and sources remain preserved |
| Environment | `pip check` passes after a local packaging repair; all numerical package versions remain unchanged |

The [frozen replay proof](matched_validation_provenance.json), [raw reconstruction proof](matched_raw_validation_provenance.json) and [current verification environment](matched_validation_environment.json) are distinct from the original execution provenance. The added verifiers fit no model, choose no new checkpoint, download no data and access no reserved specimen. Their hashes identify the executed verification sources. Existing reports with differing contents are preserved.

Run these from the repository root with the preserved local development roots:

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe scripts/validate_matched_review.py --staged
.venv/Scripts/python.exe scripts/verify_matched_results.py
.venv/Scripts/python.exe scripts/verify_matched_raw_features.py
.venv/Scripts/python.exe scripts/validate_repetition_review.py
.venv/Scripts/python.exe scripts/validate_selection_transfer_coverage.py
.venv/Scripts/python.exe -m pip check
```

The [replay verifier](../scripts/verify_matched_results.py) reconstructs predictions under a support-only feature store, then independently calculates errors, history decisions and contrasts. The [raw verifier](../scripts/verify_matched_raw_features.py) reconstructs the manifest and every spectral bundle from pinned raw recordings and repeats outside-window perturbations. Both default to verification; report writes require an explicit option. A clean clone needs the earlier coverage/run prerequisites and their recorded sources/environment because raw files and fitted artifacts are intentionally ignored.

The environment audit initially found inherited `twine 5.1.1` requiring `pkginfo <1.11` while inherited `poetry 2.1.3` requires `pkginfo >=1.12`. Installing `twine 6.2.0` and `id 1.6.1` with `--no-deps` only inside this project's `.venv` resolves the conflict. Global installations, numerical packages, declared project dependencies and recorded training environment locks remain unchanged. These publishing utilities do not enter the research computation.

Documentation review corrected stale references to the bounded 6/4 grid, a historically current 62-test suite and pending matched implementation. The maintained plan/guide and 10 October portable exports reflect completed 44/26 coverage and verified 70/44 fits; original supplied documents and earlier dated revisions remain preserved.

The remaining gates are unchanged: justify practical/secondary policy, freeze the scientific cohort and broader 76-query familiar coverage, and implement independently verified scoring with frozen fits before opening reserved signals. Two exposed validation groups, unequal training condition counts, seed variation, cap-limited fitting and the unresolved physical clock remain material limits. Reverse scoring changes support and query repetition together. All twenty reserved specimens remain untouched.
