# First implementation milestone — 8 October 2026

**Latest assessment:** the milestone sections below preserve their original development decisions and scores. The current [plan](research_plan.md) and [guide](implementation_guide.md) replace their next-work lists. First correct whole-record interpolation/filtering before support cropping, verify outside-window isolation, and regenerate aligned comparisons. The strict support-context effect is unquantified. Resolve or explicitly limit the clock, label existing distance as nominal, and complete coverage/exposure/repeatability/convergence review. All 12 used specimens remain development; fresh test scoring is not implemented. Candidate full-grid counts are 76 familiar, 44 permitted-speed and 26 endpoint-safe omitted-speed triples before QC. A matched-grid familiar comparator is still needed. No mechanical stage has begun.

This section retains the initial pilot record. The subsequent expanded comparison is documented below and in [expanded_pilot_report.md](expanded_pilot_report.md).

Completed: installable Python package and CLI; bounded pinned downloads with hash checking; recording/specimen manifests; synchronized audit figures; retrospective motion QC; anti-aliased acceleration preparation; PSD and band-power caching; deterministic prefix windows; matched episodes; training-only scaling; conditions/copy/retrieval baselines; masked encoder training; per-query/per-surface scoring; wrong-support control; checkpoint and result provenance.

The source numerical helpers came from the user-provided refined guide. The surrounding I/O, preparation, evaluation, CLI, and checks were implemented for this project. The maintained plan and guide are stored in `docs/`; the original supplied documents remain in Downloads.

## Real pilot coverage

Downloaded 362 files, about 34.9 MB: 120 recordings with three modalities plus metadata/README. All 120 have usable channels under the current development rules. The final selected cohort contains all ten training and two provisional validation specimens, with four shared query conditions.

Prepared 100 windows: 12 supports, 80 training-query windows, and 8 validation-query windows. There are 88 episodes. Support and query duration are both 0.5 seconds. The remaining protocols/durations are exercised by synthetic fixtures, which produced 176 windows and 840 episodes across six training and two synthetic validation surfaces.

## Audit decisions and unresolved issues

The real recordings' mean logged acceleration rate is about 8.63 kHz, rather than the approximately 6 kHz acquisition rate in the source description. Position is logged near 100 Hz. This mismatch does not establish which time base gives the physically correct spectrum. The current timestamp-resampling path is a provisional engineering implementation; acquisition-index timing and delivery delays need a focused comparison.

Direct differentiation after index-based smoothing fragmented steady intervals because of timestamp jitter. A local quadratic fit against actual position timestamps removes those derivative spikes. On the 100 training recordings, 11 native samples yielded 80 full half-second intervals; 21 and 31 samples both yielded 100. The smallest tested successful setting, 21, was selected before running real-model validation. The threshold stayed at 10%/2 mm/s. See `motion_qc_comparison.json` and `scripts/compare_motion_qc.py`.

All initial family groups remain explicitly unreviewed. IDs 10 and 57 are development validation candidates, not a frozen scientific test. Changing the time-base/feature rules later requires rebuilding every affected cache and rerunning all methods on aligned episodes.

## Initial validation behavior

The three model runs selected epoch 9. Averaged over seeds and the two validation surfaces, the initial model's log-power MAE was approximately 0.791, compared with 0.172 for retrieval, 0.323 for conditions-only regression, and 0.461 for copying the spectrum. Wrong support scored approximately 0.776. These values describe a tiny, provisional development set. They establish neither useful learned surface conditioning nor a generalization advantage.

Retain these results rather than selecting a favorable subset or changing the test definition to improve the network's score. A synthetic tiny-fit check confirms basic gradient/optimization capability; next debugging should examine feature conditioning, observed support variability, and the richer retrieval calibration before considering model changes.

## Checks and next work

Automated checks cover spectral amplitude/units; native-time motion derivatives; specimen/query exclusions; nested windows; target-input separation; preprocessing/library split restrictions; linear-power retrieval aggregation; grouped bootstrap IDs; mask invariance; wrong-support derangement; checkpoint restoration; tiny-fit optimization; fresh-run artifacts; immutable download hashes; and measured/synthetic source separation.

Next: inspect the pilot audit figures and specimen relationships, resolve the clock interpretation, then expand the real condition grid and add fixed-feature regression/speed rescaling. Only after those development decisions should the full scientific split, practical-effect margin, and test protocol be locked. Mechanical measurements and simulator evaluation have not started.

## Expanded implementation milestone — 8 October 2026

Added fixed-feature ridge, full-PSD speed/load rescaling, validation-selected baseline regularization, matched total-time/second-probe contrasts, named directional/load subsets, a training-only clock sensitivity command, and metadata-scoped specimen review. Shared raw-data roots preserve the initial pilot's derived outputs. Preparation reuse checks source-code hashes, and source/revision mismatch is rejected. Download progress and partial inventories support resumable bounded selections.

The expanded real run verified 578 files (62.5 MB), audited all 192 recordings successfully, and produced 268 windows/1,320 episodes across the same ten training/two validation specimens. All five protocols and all three durations retain the same four query conditions. Three encoder seeds selected epochs 55, 59, and 60. In the single 0.5-second cell, retrieval MAE is 0.1724, fixed features 0.2006, encoder 0.2492, conditions-only 0.3225, copy 0.4607, and rescaling 0.4787. Wrong support raises encoder error to 0.5837. Aggregate tables and a reproducible report are versioned in `docs/`.

The same raw spans correspond to a median 1.4388 times greater nominal duration when interpreted as contiguous 6 kHz samples; median log-power difference between clock paths is 0.3526 over 230 training windows. Timing is consequential and remains unresolved. The specimen review confirms available names and records its limited scope; fabrication relationships remain unknown. These outcomes justify continued development, not a learned-model advantage or a preferred scientific probe.

Remaining: justify the acquisition clock; extend specimen review and the common query grid; inspect model error/feature conditioning while preserving the negative retrieval comparison; implement a separately fitted omitted-speed experiment; then freeze a scientific split, practical effect margin, and locked evaluation protocol. Stage B mechanics, simulation, and control remain later work.

## Separately fitted omitted-speed milestone — 8 October 2026

The next implementation refits all methods using 20/40/60 mm/s responses and selects hyperparameters/checkpoints on those permitted speeds. Globally omitted 30/50 mm/s targets are scored only after fitting finishes. The recording/feature loader excludes training omitted-speed records, including shared-cache leftovers; API guards reject transfer episodes during fitting or selection. Retrieval uses same-direction/load endpoint interpolation in log power and saves endpoint IDs/weights. Selection and transfer analyses are separate.

All 256 requested recordings passed QC. Preparation produced 320 windows and 2,100 episodes: 1,800 fitting, 180 selection, and 120 transfer. All ten training/two validation specimens remain eligible. The three seeds selected epochs 59, 60, and 58 using permitted-speed validation. In the single 0.5-second transfer cell, fixed-feature MAE is 0.3099, encoder 0.3158, interpolated retrieval 0.3298; wrong support scores 0.4975. Retrieval-minus-encoder improvement is 0.0140 with a two-group diagnostic interval spanning zero. This does not establish a learned-model advantage.

The report/export audit verified all 120 transfer retrieval predictions use only allowed endpoints with 0.5/0.5 weights. The training-only timing comparison now covers 270 windows, with median index/logged duration ratio 1.44 and median log-power difference 0.3915. Timing and manufacturing-family independence remain unresolved. The six fitting/query endpoint cells and four transfer cells use 45/90 degrees at nominal 1 N, so scores cannot be compared directly to the earlier pilot's condition grid.

See [omitted_speed_report.md](omitted_speed_report.md). Remaining work is to justify timing, complete family review, broaden the common query grid, inspect errors, and then lock the scientific protocol. Mechanics, simulation, and control have not begun.
