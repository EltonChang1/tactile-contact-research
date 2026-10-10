# Complete metadata, exposure and wider study design

9 October 2026. All **118 specimen names/categories** are reviewed; **87 conservative groups** are recorded; **20 specimens in 15 complete groups** are reserved before wider sensor review. Grouping is based on names and declared uncertainty, with manufacturing relationships unknown. Scientific coverage/protocol freeze and locked scoring remain pending.

## Metadata and grouping

The pinned `texture_list.xlsx` hash is `6cd7dfc06e61852d49a2256d7fe8d44d222f3619f48fe9a4031f677d1b0eb4ff`. The [author documentation](https://github.com/cluster-lab/Cluster-Haptic-Texture-Dataset/blob/e05d6b022d127e24f73583146f0aa229c6934449/documents/dataset_details.md) describes this workbook and the recording keys. This review inspects ID, English name, category and subcategory, preserving ambiguous source labels. The workbook also contains separately measured friction attributes; they are not vibration targets or predictor inputs. The full workbook was parsed previously, so the ledger distinguishes metadata availability from sensor-response exposure.

[Review rules](../configs/specimen_review_rules.json) declare fifteen multi-specimen blocks: oak, ash, cherry, Hinoki, cedar, pine, polyethylene, phenol, steel, glass finishes, porcelain, cotton/linen textiles, wool textiles, cow-named materials, and an uncertainty block for construction-only cloth names. Duplicate white ash and frosted-glass names remain different specimen IDs in the same group. Cotton/linen and wool blocks cross raw metadata categories. These are conservative analyst blocks, not verified manufacturing families or taxonomic claims. Supplier, lot, composition and fabrication relationships remain unknown throughout.

`North pipe`, `Ppolylactic acid`, and `Silicon` are retained with ambiguity notes rather than silently corrected. Construction-only cloth labels (including exposed velvet/corduroy) are grouped together because fibers/suppliers are unspecified. Singletons mean no declared connection was identified in this metadata; they do not prove independence. The existing pilot grouping file and all historical results remain intact; [complete grouping](../configs/all_specimen_groups.csv) is prospective.

## Exposure and fresh reservation

The [exposure snapshot](../configs/development_exposure.json) permanently marks training IDs `0,38,49,65,74,79,82,87,102,103` and selection/scoring IDs `10,57` as development-exposed. A local audit verifies six historical real-run manifests, **72 specimen/run events** and a **304-recording-triplet union**. Repeated model seeds, crops, episodes and reruns do not create additional independent specimens. The pre-expansion cache held 24 triplets per training specimen and 32 per selection specimen.

Published evidence: [run events and manifest hashes](development_exposure_events.csv), [record-access union](development_record_access.csv), [local snapshot hashes](local_exposure_snapshot.json), and [118-row exposure ledger](specimen_exposure_ledger.csv). The snapshot describes exposure through the clock/QC milestone; subsequent wider QC accesses only the same ten training IDs and is recorded separately in its provenance. It is not a claim about external access by other people.

Twelve direct exposures propagate to **22 specimens blocked from a fresh test**, through the polyethylene, steel, manufactured-glass and uncertain-cloth blocks. The ten additionally blocked IDs are `50,66,75,76,77,107,108,109,110,111`. That leaves **96 metadata-only fresh-group candidates before reservation**. All 118 have metadata reviewed; fresh here means no sensor response/model-score exposure in the audited project history, not ignorance of specimen identity.

The [reservation](../configs/test_reservation.csv) is deterministic: seed `20261009`, SHA256 ordering of eligible whole groups, exact category quotas and no signal/QC/score selection. It reserves IDs **`5,8,13,21,34,46,48,59,60,72,73,78,80,81,83,86,93,94,113,114`**. All four ash specimens, both phenol specimens and both porcelain specimens stay together. The selection cannot silently change on regeneration; a changed reservation requires an explicit versioned review. No reserved signal is downloaded or read in this milestone.

| Metadata category | All specimens | Directly exposed | Group-blocked from fresh test | Reserved |
| --- | --- | --- | --- | --- |
| Wood | 38 | 2 | 2 | 5 |
| Stones | 11 | 1 | 1 | 2 |
| Polymers | 16 | 2 | 3 | 2 |
| Metals | 9 | 1 | 2 | 2 |
| Glass | 5 | 1 | 4 | 1 |
| Composites | 3 | 1 | 1 | 2 |
| Ceramics | 5 | 1 | 1 | 2 |
| Biodegradable | 15 | 1 | 1 | 2 |
| Cloths | 16 | 2 | 7 | 2 |
| **Total** | **118** | **12** | **22** | **20** |

The raw metadata category labels are retained. Only obsidian remains an eligible Glass specimen after manufactured glass is blocked, so Glass receives one reserved specimen and Wood five; the other categories receive two each. This limits future category-level conclusions, especially manufactured-glass generalization. The remaining 98 specimens are not reserved; their training/selection allocation is still pending coverage/group review. [Category table](specimen_category_review.csv) counts group intersections within categories; cross-category groups mean those group counts must not be summed as globally independent groups.

## Access guard and condition domains

The reservation validator rejects incomplete groups, exposed groups, forged labels and unknown specimens. The development preflight rejects reserved group members. **The new wider-coverage runner invokes this guard before source loading/downloads.** Existing experiment CLI commands do not automatically invoke this new preflight; any new development selection must run it explicitly. These checks are tested, but do not implement a locked scientific scoring interface or prevent external access to public data.

[All eighty triples and masks](../configs/query_domains.csv) make the domains executable:

| Domain before QC | Triples |
| --- | --- |
| Union of support conditions | 4 |
| Full familiar queries | 76 |
| Known-speed 20/40/60 fitting/selection queries | 44 |
| Candidate 30/50 transfer queries | 32 |
| Endpoint-safe transfer queries | 26 |
| Matched familiar fitting queries: known 44 + safe transfer 26 | 70 |

The six blocked omitted-speed triples are both speeds at `(direction, nominal load)=(0°,0.5 N),(0°,1 N),(90°,0.5 N)`. Each retained transfer triple has both retrieval endpoints in the permitted non-support response domain. Primary familiar evaluation still uses the 76-query design.

The [matched-comparator design](../configs/study_design.json) specifies a separate contrast: identical specimens, support/query windows, QC intersection, methods and tuning; select both models only on the same 44 known-speed validation triples; score the same 26 transfer triples after selections finish. Omitted fitting uses 44 known-speed triples; familiar fitting adds only the 26 safe transfer-speed response triples, giving 70. This isolates that added response domain instead of comparing mismatched historical grids. These are domain/role contracts; fitting this comparator and locking scientific scores require further implementation.

Training 30/50 mm/s data were excluded within the omitted experiment, but earlier familiar development used them. The project cannot call those conditions globally untouched. Reserved fresh specimens remain the route to a later independent test.

## Reproduction

From the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_study_design.py
.\.venv\Scripts\python.exe scripts/prepare_study_design.py --check-config configs/omitted_speed.yaml
.\.venv\Scripts\python.exe scripts/review_wider_coverage.py --download
.\.venv\Scripts\python.exe -m pytest -q
```

The design script reads the pinned metadata or downloads only the 19 KB workbook under a 1 MiB cap. A clean clone reuses the committed historical access snapshot. `--audit-local` additionally requires the six historical run roots to recapture their manifest/cache-name evidence; it reads no sensor values. Source/input/output hashes are in [design provenance](study_design_provenance.json). The wider runner requires the committed reservation, exposure ledger and domains, and requests only known-speed records for ten already exposed training specimens. Downloaded raw data remain ignored by Git.

The reservation is made before wider QC. After that review, retain it while checking repeat variability, convergence, feature floor/range sensitivity and practical margins. Reserve/test access must stay separate from those decisions; neither a 20-row reservation nor a successful preflight is evidence of a completed scientific test.

The subsequent [wider known-speed review](wider_coverage_review.md) is now complete: all 960 training records retain half a second, all required one-second supports survive, and all 44 known-speed query triples are common across ten training specimens. Seven-setting sensitivity retains current QC. The suite has 70 passing tests. The historical exposure snapshot/reservation remains preserved; wider access touches only the same ten already exposed training IDs.
