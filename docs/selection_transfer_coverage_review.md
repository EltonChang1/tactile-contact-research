# Matched selection/transfer coverage — 10 October 2026

Current QC supports the complete planned matched validation grid on development specimens **10 and 57**, in both prediction orientations. Retain the existing 21-sample motion smoother, gap rules, spectral features and finite training policy. This is coverage evidence; no new prediction result or scientific test is produced.

## Prespecified acquisition and review

The [review configuration](../configs/selection_transfer_qc_review.json) requests four support conditions, 44 known-speed selection triples and 26 endpoint-safe omitted-speed transfer triples, each on two specimens and two repetitions: **296 recording triplets**. The six omitted-speed triples whose interpolation endpoints are forbidden support conditions remain outside this matched comparison. This review therefore does not cover the broader 76-query familiar primary grid or reserved test specimens.

Mandatory metadata/reservation preflight runs before source loading or downloads. A separate ignored root, `runs/selection_transfer_coverage`, copies 56 approved cached triplets and acquires 240 additional triplets, preserving the shared raw inventory and source metadata byte-for-byte. Its 890 files, including dataset metadata, total 102.2 MB. The raw revision remains `b7c2fb70ed2d68219389478660f35c2cd49c69fb`. Every local raw file is inventoried and hashed. Interrupted acquisition may resume only with the identical sealed configuration and source hashes; completed audit roots cannot be overwritten.

All 296 requested records remain in the denominator for each of the same seven QC settings used in earlier reviews. Current half-second geometry/loading diagnostics use the canonical output-grid start. Availability rounds the steady start onto the exact 6000-point computational grid used by feature preparation and checks the requested end against the steady interval; it does not merely compare interval length with duration. The largest alignment shift is 0.000164302 logged seconds. Feature extraction and model fitting are not part of this audit.

## Availability and common pools

| QC variant | Requested / valid | Quarter-second available | Half-second available | One-second available |
| --- | ---: | ---: | ---: | ---: |
| Current, 21-sample smoother | 296 / 296 | 296 | 296 | 286 |
| 11-sample smoother | 296 / 296 | 296 | 258 | 92 |
| 31-sample smoother | 296 / 296 | 296 | 296 | 296 |
| Acceleration gap half / double | 296 / 296 each | 296 each | 296 each | 286 each |
| Auxiliary gap half / double | 296 / 296 each | 296 each | 296 each | 286 each |

Keep current settings. Greater one-second retention under the 31-sample smoother is unnecessary for the declared experiment and does not establish better physical contact quality. No prediction score selects a setting or an exclusion.

The required support union contains **eight recordings per specimen**: four conditions × two repetitions. All **16** retain the longest one-second support budget, covering all five protocols and both prediction orientations. Query windows remain fixed at half a logged second, regardless of support duration.

| Prospective common pool, each of 0.25 / 0.5 / 1-second support | Requested triples | Triples retained across both specimens | Specimen/query cells retained |
| --- | ---: | ---: | ---: |
| Known-speed selection | 44 | **44** | **88 / 88** |
| Endpoint-safe transfer | 26 | **26** | **52 / 52** |

Every cell has both half-second query repetitions and every protocol's supports in both scoring orientations. All **420** specimen/query/duration eligibility rows survive. This verifies prospective budgets and a common grid, without manufacturing extra independent specimens or repetitions.

Ten query recordings lack one second: six selection and four transfer. None is a required support, and every one retains the required half-second query duration. The [record table](selection_transfer_qc_records.csv) retains their exact identities and intervals; no query or specimen is dropped. The shortest support interval is 1.04056 logged seconds on specimen 10; specimen 57's shortest support interval is 1.909104.

## Geometry, loading and historical consistency

The fitted global heading frame has maximum residual **0.066209°** against logged position. Median time-weighted normal force is **1.01900 × nominal**, with 5th–95th percentiles **0.94234–1.17407**. Median logged travel is **0.992259 × nominal speed-times-duration distance**. No ±16 g clipping appears in the reviewed acceleration rows. These are retrospective diagnostics, not independent calibrated motion/force validation or new predictor inputs.

All **56** records shared with the corrected omitted-speed historical manifest reproduce steady starts and ends exactly. The previous [repetition release verifier](../scripts/validate_repetition_review.py) still passes because its shared inventory and historical feature/checkpoint inputs remain unchanged.

## Matched fit preparation and next gate

The [prepared role/budget specification](../configs/matched_development_review.json) records the retained finite **120-epoch cap**, patience 10, seeds `[0,1,2]`, original optimizer/sampler/model and all required methods. It specifies familiar training on 70 query triples, omitted training on 44, common known-speed selection on 44, and identical scoring on 26. Original forward query repeat 1 remains the primary development assignment; reverse repeat 0 is retained as a separate frozen-model sensitivity, with repeat-control supports in canonical `[0,1]` order.

Before QC, those domains imply 21,000 familiar or 13,200 omitted training episodes, 1,320 known-speed selection episodes per experiment, and 780 transfer scoring episodes per experiment/orientation. Counts enumerate windows/protocol cells and are not independent sample sizes. This restricted matched comparison does not replace the broader familiar-condition primary study.

**No matched fit has run.** Next acquire and audit **520 transfer-speed training triplets**: the 26 safe query triples × two repetitions × ten already exposed training specimens. The known-speed training audit already covers the other 960 records. Then implement the guarded matched fitting runner: original training supports and both query repetitions; a training-only shared support scaler; separate 70/44 target whitelists; identical known-speed selection; all baseline and six encoder selections sealed before either transfer score pool opens; both scoring orientations; full cell/specimen/condition reporting. Use the same QC intersection for both experiments and every method. Do not change the model or choose favorable transfer results.

Reserved specimens remain untouched. Locked scientific scoring, practical/secondary policy, physical timing, calibrated mechanics and manufacturing-family independence remain separate gates.

## Verification and reproduction

**100 tests pass**, with eight new checks for canonical availability, complete pools, reverse-support attrition, missing query repetitions, duplicate identities, reservation-before-source access, restricted immutable cache staging, pinned-file changes and domain/denominator integrity. Compilation and the [release audit](../scripts/validate_selection_transfer_coverage.py) pass. The original document files and historical experiment roots remain intact.

From the repository root, run `.venv/Scripts/python.exe scripts/review_selection_transfer_coverage.py --download`, followed by `.venv/Scripts/python.exe scripts/validate_selection_transfer_coverage.py`. The completed output root is rejected; a new execution needs a copied configuration with a new root. Public evidence includes the [provenance](selection_transfer_qc_provenance.json), [summary](selection_transfer_qc_summary.json), [setting sensitivity](selection_transfer_qc_sensitivity.csv), [all setting/record rows](selection_transfer_qc_sensitivity_records.csv), [common eligibility](selection_transfer_qc_common_eligibility.csv), [intersections](selection_transfer_qc_intersections.csv), [condition diagnostics](selection_transfer_qc_conditions.csv), [specimen diagnostics](selection_transfer_qc_surfaces.csv), [coverage helpers](../src/tactile_contact/coverage_review.py), [runner](../scripts/review_selection_transfer_coverage.py), and [tests](../tests/test_coverage_review.py). Raw files remain ignored.
