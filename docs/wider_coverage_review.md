# Wider known-speed training coverage

Completed 9 October 2026, after the [metadata-only reservation](study_design_review.md). **All 960 requested training records retain a half-second interval under current QC.** The full 44-condition known-speed query pool is available for all ten training specimens, with both query repetitions and every protocol-required one-second support. Settings and fitted models are unchanged.

## Scope and access

The [prespecified review](../configs/wider_qc_review.json) expands from ten conditions to **all 48 known-speed conditions**: 20/40/60 mm/s × eight headings × two nominal loads, both repetitions, on the same ten already exposed training specimens. The bounded downloader verifies 2,882 selected files, **343.6 MB in total including cached files**; new raw files remain ignored by Git. The review verifies all 2,880 sensor-file hashes before use.

The runner validates the whole-group reservation and exposure ledger **before** source loading or downloading. It reads no reserved specimens, selection IDs 10/57, or training 30/50 mm/s records in this review. Previously familiar development did use training 30/50 responses; this review does not make them project-wide untouched conditions. No new specimen becomes response-exposed here, no predictor error selects QC, and no model is fitted. The twenty reserved specimens remain metadata-only in the audited project history.

This is the complete known-speed grid on ten development specimens, not the 76-condition familiar grid on 118 surfaces or a scientific test. Geometry/loading use the first 0.5 logged seconds of each current steady interval, before acceleration-grid quantization, with retrospective position smoothing. Physical duration, frequency and distance remain uncalibrated under [logged_coordinates_v1](../configs/clock_convention.json).

## Coverage and sensitivity

The same [seven settings](../configs/qc_review.json) are reviewed one at a time, giving **6,720 recording/setting decisions**. Every requested recording enters the denominators.

| Setting | Valid / requested | Full 0.5 logged-second interval | Full 1 logged-second interval |
| --- | --- | --- | --- |
| Current: 21 native position samples | 960 / 960 | 960 | 932 |
| 11 samples | 960 / 960 | 812 | 266 |
| 31 samples | 960 / 960 | 960 | 960 |
| Acceleration gap 0.005 or 0.02 s | 960 / 960 each | 960 each | 932 each |
| Auxiliary gap 0.025 or 0.1 s | 960 / 960 each | 960 each | 932 each |

The 28 records shorter than one second are not automatically unusable queries: the target duration is fixed at half a second. For a prospective common training pool, the [eligibility check](wider_contact_qc_common_eligibility.csv) separately requires all five protocol-prescribed support recordings to retain one second and both query repetitions to retain half a second. **All fifty required support recordings and all 440 specimen/query-condition cells pass; all 44 query triples are common across ten training specimens.** This supports keeping the current settings while further diagnostics proceed. Increased retention under 31-point smoothing does not establish better motion accuracy.

This common-pool result is prospective training coverage, not a frozen evaluation cohort. It does not establish validation/test coverage or the 26 omitted-speed score-grid intersection. Future model preparation must still preserve exact raw windows, exclusions, retrieval endpoints and matched method budgets.

## Contact diagnostics

- **Heading:** a single equal-record-weight global frame gives `observed atan2(Y velocity, X velocity) ≈ −89.999732° − nominal heading`. Absolute residual is at most **0.06601°**, with 95th percentile **0.02854°**. This extends logged-position agreement to all eight headings; it is not independent motion tracking or physical calibration.
- **Loading:** median time-weighted recorded force / nominal load is **1.02909**; the 5th–95th percentile range is **0.94195–1.12488**, and the full range **0.83011–1.33484**. The earlier ten-condition selection had median 1.04865; broader conditions change the descriptive distribution. Do not treat nominal input labels as exact measured force or discard deviations to improve scores. Dense transmitted force rows are not independent acquisition measurements.
- **Travel:** integrated smoothed logged-position speed / nominal distance has median **0.99164**, 5th–95th percentile **0.97817–1.00523**. Endpoint displacement is exported separately. These are retrospective logged-coordinate diagnostics; nominal distance remains the prediction-budget field.
- **Timing:** acceleration mean logged row rates span **8,494.8–8,737.8 Hz**, with median **8,639.2 Hz**; position averages around 100 Hz. The wider sample confirms persistence of the documented/logged-rate discrepancy without resolving acquisition timing.

## Evidence and reproduction

Exports: [960 records](wider_contact_qc_records.csv), [48 conditions](wider_contact_qc_conditions.csv), [ten specimens](wider_contact_qc_surfaces.csv), [setting totals](wider_contact_qc_sensitivity.csv), [6,720 decisions](wider_contact_qc_sensitivity_records.csv), [common training eligibility](wider_contact_qc_common_eligibility.csv), [compact summary](wider_contact_qc_summary.json), [raw/source/input/output provenance](wider_contact_qc_provenance.json) and [summary provenance](wider_contact_qc_summary_provenance.json).

From the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_study_design.py
.\.venv\Scripts\python.exe scripts/review_wider_coverage.py --download
.\.venv\Scripts\python.exe scripts/summarize_wider_coverage.py
.\.venv\Scripts\python.exe -m pytest -q
```

Omit `--download` to review an already complete cache. Missing/hash-mismatched raw files fail rather than silently reducing coverage. Invalid steady intervals are recorded as exclusions. New grouping/reservation/domain/preflight/common-eligibility checks bring the suite to **70 passing tests**; historical boundary reports and fitted experiments remain preserved.

Next review repeat variability, primary-cell/aggregate convergence, feature floor/range sensitivity and practical-effect margins on development data. Then implement the matched 70-versus-44 fitting and shared-selection/26-score interfaces, verify wider selection coverage, and freeze scientific access/scoring. Keep reserved responses protected through those decisions. No larger model or new scientific claim is justified solely by this coverage result.
