# Development protocol and intended primary study

Question: How much brief sliding-contact information supports vibration-response prediction on unseen specimens, and does a second direction, speed, or load help more than repeating the contact at the same time budget?

The primary target is 32 log10 spectral band powers on each of three acceleration axes. The starter range is 24–1000 Hz, with 0.125-second Welch segments and 50% overlap. Acceleration is converted from g to SI before estimation. The `log10(power + 1e-10)` floor is numerical and has not been established as a sensor noise floor. Bin-center integration and modeled-band RMS follow the supplied guide.

## Current development experiment

The paragraph below records the initial single-probe pilot. The expanded development experiment uses `configs/expanded_pilot.yaml`, all five protocols, 0.25/0.5/1-second nested support prefixes, the same four query conditions, and the same train/validation IDs. `configs/pilot_groups.csv` records a completed review of available names with scope `metadata_names_only`; manufacturing-family independence is unresolved. The full 76-condition study has not been run.

Source: Cluster mirror revision `b7c2fb70ed2d68219389478660f35c2cd49c69fb`. Training IDs: 0, 38, 49, 65, 74, 79, 82, 87, 102, 103. Provisional validation IDs: 10, 57. No test split is defined or scored. Family IDs are explicitly unreviewed specimen placeholders; these validation specimens were not used to fit model weights or preprocessing statistics.

Support: repeat 0 at 40 mm/s, direction 0 degrees, nominal 0.5 N; a 0.5-second prefix of a retrospectively selected steady interval. Queries: repeat 1 at `(30, 0, 0.5)`, `(50, 0, 0.5)`, `(40, 45, 1.0)`, `(60, 90, 1.0)`. Tuple units are mm/s, degrees, and N. Training response fitting can use both query repetitions. Every method receives the same support budget and query cohort.

The encoder receives 96 training-standardized log powers, four contact-condition features, and duration per observed contact. Query conditioning includes requested speed, periodic direction encoding, and nominal load. Measured query acceleration/force and material identity are excluded from deployable inputs. Force is currently used only in offline QC; the optional support-force variant is not implemented yet.

Time base is provisional: interpolate on a uniform grid at the rounded median logged acceleration rate, then anti-alias/resample to 6000 Hz. No extrapolation beyond the recording is permitted. Logged gaps, invalid values, duplicate timestamps, and resets fail QC. The source's observed delivery rate differs from the documented acquisition rate; absolute frequency interpretation requires further review.

Motion QC uses an 11-point local quadratic fit for clean synthetic fixtures and a 21-point fit for the measured pilot, at native position timestamps. The measured choice came from the training-only comparison in `motion_qc_comparison.json`. Steady speed must lie within `max(2 mm/s, 10% of nominal)` with measured normal force above 0.05 N. Motion fitting and longest-interval selection are retrospective. These budgets exclude approach, stabilization, and repositioning.

Comparators: fixed conditions-only ridge, copied/linear-averaged support power, and nearest training-surface retrieval using protocol-prescribed support fingerprints. The model is the guide's 16-dimensional encoder, mean pooling, explicit mask/count, and small predictor. Training uses balanced surface/cell sampling; initialization seeds 0/1/2; validation-only early stopping. Wrong support uses a deterministic surface derangement.

Expanded comparators add ridge on mean/std of permitted support vectors, probe count, and requested conditions. Its input standardization fits training episodes; declared regularization candidates are 0.01/0.1/1/10/100, selected by equal-cell validation MAE. Full-PSD rescaling uses the guide's angular/speed/canonical-order support rule and the same target-bin integration. Above-floor training powers fit global exponents with ridge candidates 0/0.1/1; exponents are bounded to p∈[-4,8], b∈[-4,4] and validation chooses the candidate. These parameters are predictive approximations, not validated physical laws. Every regression's total sample weight is one per specimen, independent of repeated protocol cells.

The expanded tables compare single 1 second against two 0.5-second contacts, single 0.5 seconds against two 0.25-second contacts, and repeat/direction/speed/load at two 0.5-second contacts. Query identities must match before pairing. Named subsets publish condition lists and counts. The clock sensitivity is training-only and compares the same timestamp-selected raw spans under two interpretations; its index path has a different nominal budget and does not enter model selection. See [expanded report](expanded_pilot_report.md), [timing audit](timing_audit.md), and [specimen audit](specimen_group_audit.md).

Primary development score: raw log-band-power MAE averaged over queries per specimen, then specimens. Save per-axis/modeled-band RMS diagnostics. Bootstrap output on two provisional validation groups is an engineering diagnostic, not a scientific uncertainty claim.

## Full study choices still to lock

The intended primary comparison is encoder versus retrieval with single 0.5-second support on the familiar-condition common grid. The full design has 76 query condition triples after excluding all support conditions, before QC. The main probe contrast is direction versus repetition with two 0.5-second contacts. Other probe contrasts, duration curves, and transfer subsets must be declared and reported.

Before the scientific test: verify specimen families, select and document the spectral time base, audit full-grid coverage, choose a practical effect margin using training/pilot variability, freeze support/query and exclusion rules, declare secondary-comparison interpretation, and lock train/validation/test manifests. A nonsignificant difference will not be called equivalence. A learned-model benefit requires evidence beyond a functioning implementation or attractive example.
