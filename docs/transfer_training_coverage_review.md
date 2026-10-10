# Safe transfer-speed training coverage — 10 October 2026

The final training-coverage gate passes without changing QC. All **520** requested transfer-speed recordings retain the required half-second query interval. Together with the 960 known-speed records, the complete 70-query familiar and 44-query omitted training pools remain eligible at every declared support budget. This is development coverage, without prediction scores or reserved-test access.

The [configuration](../configs/transfer_training_qc_review.json) requests 26 endpoint-safe speed/direction/load triples × two repetitions × ten already exposed training specimens. Acquisition explicitly uses familiar-condition permission for 30/50 mm/s; these responses must remain inaccessible to omitted model fitting. A separate ignored root, `runs/transfer_training_coverage`, preserves the shared historical raw inventory/source. Its 1,562 pinned files, including dataset metadata, total 169.8 MB.

| QC setting | Requested / valid | Quarter-second | Half-second | One-second |
| --- | ---: | ---: | ---: | ---: |
| Current 21-sample smoother | 520 / 520 | 520 | **520** | 497 |
| 11-sample smoother | 520 / 520 | 519 | 453 | 136 |
| 31-sample smoother | 520 / 520 | 520 | 520 | 520 |
| Acceleration gap half / double | 520 / 520 each | 520 each | 520 each | 497 each |
| Auxiliary gap half / double | 520 / 520 each | 520 each | 520 each | 497 each |

The 23 recordings without a full second are query recordings with a fixed half-second target budget. They do not remove any required cell. Retain current settings; greater one-second retention under a different smoother is unnecessary for this comparison. No setting or exclusion is selected by predictor error.

The [known canonical table](transfer_training_qc_known_canonical.csv) rechecks output-grid starts against the preserved current-QC intervals and hashed raw timestamps for all 960 known records. It does not rerun or alter their motion QC. All five prescribed original support recordings per training specimen retain the longest budget: **50 one-second supports**. Training uses original support assignments; reversed training supports are not required for the frozen validation sensitivity.

The [common eligibility](transfer_training_qc_common_eligibility.csv) combines known and transfer records: all **440 known** and **260 safe transfer** specimen/query cells survive at each of 0.25, 0.5 and 1-second support, yielding **2,100 eligible rows**. Both query repetitions are required, including for retrieval's linear-power averaging. The CSV intersection label `selection` names the shared known-speed condition domain; its records here are training specimens, not held-out selection data.

Median recorded force is **1.019765 × nominal**, with 5th–95th percentiles **0.930244–1.114408**. Median logged travel is **0.993509 × nominal speed-times-duration distance**; maximum global-frame heading residual is **0.045485°**. The largest canonical alignment shift is 0.000166401 logged seconds. These are retrospective logged-coordinate diagnostics, without independently calibrated force/motion or new predictor inputs.

The matched runner now has complete prospective training and [validation coverage](selection_transfer_coverage_review.md). Its [execution specification](../configs/matched_fit_review.json) retains the prepared [70/44 role/budget design](../configs/matched_development_review.json), known-speed selection on 44 triples, common transfer scoring on 26, and the finite 120 training policy. The [matched report](matched_development_review.md) records execution outcomes separately from this coverage evidence. The restricted matched domain does not replace the broader 76-query familiar primary study or a fresh locked scientific test.

**110 tests pass**, including ten new matched-role/access/history checks. The coverage release audit verifies all 520 identities, 3,640 sensitivity rows, canonical availability, combined common pools, pinned raw hashes, preserved historical inputs and reservation preflight. Run `.venv/Scripts/python.exe scripts/review_transfer_training_coverage.py --download`, then `.venv/Scripts/python.exe scripts/validate_matched_review.py --coverage-only`. Completed roots are protected; a new execution requires a new declared root.

Evidence: [runner](../scripts/review_transfer_training_coverage.py), [training eligibility helpers](../src/tactile_contact/transfer_training.py), [provenance](transfer_training_qc_provenance.json), [summary](transfer_training_qc_summary.json), [records](transfer_training_qc_records.csv), [sensitivity](transfer_training_qc_sensitivity.csv), [all setting/record rows](transfer_training_qc_sensitivity_records.csv), [intersections](transfer_training_qc_intersections.csv), [condition diagnostics](transfer_training_qc_conditions.csv), [specimen diagnostics](transfer_training_qc_surfaces.csv), and [tests](../tests/test_matched.py). Raw data remains ignored. The twenty reserved specimens remain untouched.
