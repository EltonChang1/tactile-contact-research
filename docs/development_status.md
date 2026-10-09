# First implementation milestone — 8 October 2026

Completed: installable Python package and CLI; bounded pinned downloads with hash checking; recording/specimen manifests; synchronized audit figures; retrospective motion QC; anti-aliased acceleration preparation; PSD and band-power caching; deterministic prefix windows; matched episodes; training-only scaling; conditions/copy/retrieval baselines; masked encoder training; per-query/per-surface scoring; wrong-support control; checkpoint and result provenance.

The source numerical helpers came from the user-provided refined guide. The surrounding I/O, preparation, evaluation, CLI, and checks were implemented for this project. Original plan and guide copies are stored in `docs/`.

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
