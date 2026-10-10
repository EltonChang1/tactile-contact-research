# Tactile Research Implementation Guide

## Brief contact probes for predicting texture and sliding contact

Prepared for Elton Chang — original plan dated 7 October 2026; guide updated 10 October 2026 after reviewing the completed 9 October development findings, America/Los_Angeles.

**Purpose:** an implementation guide for the maintained [research plan](research_plan.md), originally supplied as `Tactile_Contact_Research_Plan_2026-10-07.md`. Use the stage gates below to decide which steps are ready to begin. The first completed study uses public data; later milestones add measured contact forces, simulation, and control.

The public study develops the **tactile observation model**: what a robot should sense under a requested contact. The mechanical study develops the **contact law**: forces that influence motion. A useful world model ultimately needs both. Starting with public data lets you test whether brief observations contain transferable information and establish reliable evaluation methods before investing in a force rig. Vibration prediction alone does not identify an intrinsic material law.

**Status as of 10 October 2026:** an executable [public repository](https://github.com/EltonChang1/tactile-contact-research) supports bounded real-data and synthetic development experiments. The initial pilot, expanded five-protocol/three-duration comparison, and separately fitted omitted-speed experiment have completed and were rerun with corrected raw-window preparation. Use the [boundary report](window_boundary_report.md) for current scores; the original [development status](development_status.md), [expanded results](expanded_pilot_report.md), and [omitted-speed results](omitted_speed_report.md) remain historical. The latest executed suite has 78 passing tests. No locked scientific test, force identification, simulator validation, or control experiment has run. This revision changes documentation only.

| Current bounded development result, single 0.5 logged-second support | Retrieval MAE | Fixed-feature MAE | Encoder MAE | Interpretation |
| --- | --- | --- | --- | --- |
| Expanded familiar-condition pilot | **0.1726** | 0.2016 | 0.2513 | Retrieval leads; wrong support worsens encoder MAE to 0.5936 |
| Separately fitted omitted-speed pilot | 0.3300 | **0.3096** | 0.3141 | Fixed features lead MAE; encoder/retrieval difference remains inconclusive on two specimens |

These experiments use different query grids, so their errors do not isolate the effect of omitting speeds. The repeatedly used specimens are development data. The [name-based specimen review](specimen_group_audit.md) does not verify manufacturing-family independence. Current timing sensitivity demonstrates a consequential clock ambiguity, rather than resolving it.

**Boundary correction completed 9 October:** `windows.py` now crops raw acceleration before interpolation/filtering and derives padding only from allowed samples. Nine new checks passed in a 53-test suite, and outside-sample perturbations left all 688 real prepared windows bit-for-bit unchanged. All methods/seeds were rerun in new roots. Expanded retrieval/encoder MAE is now 0.1726/0.2513; omitted fixed-feature/encoder/retrieval MAE is 0.3096/0.3141/0.3300, with the encoder/retrieval difference still inconclusive. See the [boundary report](window_boundary_report.md) for exact dependency provenance, feature changes, before/after scores and limitations. Historical reports remain intact.

**Clock/QC review completed 9 October:** fifteen original CSVs preserve mirror timestamps/signals after declared conversion. Physical acquisition timing remains unverified, so [logged_coordinates_v1](../configs/clock_convention.json) explicitly scopes continued development to logged-time windows and frequency coordinates. Seven prespecified QC settings were reviewed on 200 known-speed training records: current settings retain every half-second interval and 199 one-second intervals; heading/load/travel diagnostics are exported. Settings and models remain unchanged. See the [decision/report](clock_qc_review.md). That milestone passed 62 tests.

**Metadata and wider training coverage completed 9 October:** all 118 specimens are reviewed in 87 conservative groups; twenty metadata-only specimens in fifteen whole groups are reserved. The [960-record known-speed audit](wider_coverage_review.md) retains every half-second interval, all required one-second supports and all 44 common query triples across ten training specimens. Current settings and fitted models are unchanged; 70 tests pass.

**Training diagnostic review completed 9 October:** the [repeat/feature/history report](development_diagnostics_review.md) covers 480 repeat pairs, including 440 known-query pairs, from the same 960 training records. Mean query repeat MAE is 0.172972 with higher variability on specimens 102/103; repeat differences are limited context, not a noise ceiling. Floor/range checks support retaining current features. All six expanded/omitted histories hit the 60-epoch cap while improving; primary-cell histories were not saved. No model or reserved signal changed; 78 tests pass.

Next run a finite controlled convergence extension with primary-cell logging, then repetition reversal, residual/matched-grid development comparisons and a scientific protocol/access freeze. Practical margins and wider selection/transfer coverage remain pending. Numerical defaults already implemented are identified below; proposed additions remain labeled. A baseline winning is a valid scientific outcome.

## Scope and stage gates

The plan is feasible as a staged project. Its first deliverable is a completed public-data study of brief-contact information. The strongest candidate contribution is the matched-budget experiment and its interpretation; the small network implements that experiment. Hardware-dependent stages need separate access, calibration, and evidence.

| Plan stage | Guide steps | Evidence required before the next stage |
| --- | --- | --- |
| A: tactile-response prediction | 1–17, with packaging in 26 | Bounded preprocessing, declared time convention, fresh held-out evaluation, baselines, and a scoped report |
| B: measured sliding mechanics | 18–22 | Independent calibrated force measurements and held-out force predictions |
| C: forward dynamics and engine integration | 23–24 | A dynamically responsive experiment and motion predictions from initial state/actions |
| D: planning or robot learning | 25 | Matched task evaluation after the relevant model has been validated |

Investigate rig capabilities while Stage A runs. Stage B depends on calibrated independent force measurements, not an encoder victory or Stage A publication. Stage A has its own completion point even if hardware remains unavailable. Do Step 26 throughout the project. Static friction, compliance, waveform generation, new sensors, category exclusion, and large policy training are follow-ups whose scope must be justified separately.

## How to use this guide

The first executable pipeline and both bounded comparisons are complete. Use the steps as contracts and checkpoints, not instructions to restart the project.

1. The Step 8 raw boundary and matched reruns, plus Step 6 bounded clock/QC review, are complete. Retain the declared logged-coordinate scope; physical calibration remains unresolved.
2. Retain the completed all-specimen metadata/exposure review, twenty-specimen reservation and wider known-speed training coverage in Steps 5–7; verify future selection/transfer coverage without exposing reserved groups.
3. Retain the completed training repeat/floor/range and saved-history diagnostics in Steps 11–17. Extend unchanged bounded cohorts to a finite 120-epoch cap with primary logging and first-60 reproduction checks before broader fitting; then complete repetition reversal, matched-grid familiar/omitted comparison and a fresh locked test.
4. Investigate Step 18 in parallel. Start measured mechanics only when its calibration and measurement gate is satisfied; Steps 23–25 retain their additional validation gates.
5. Maintain Step 26 throughout. Preserve historical results and label revisions so the original negative and inconclusive findings remain visible.

The 9 October implementation completed raw-window correction, bounded development reruns, clock scope, metadata/reservation, wider known-speed training QC and repeat/floor/range/history diagnostics. This 10 October revision aligns the guide with those findings. The controlled 120-epoch extension, repetition reversal, broader matched fitting and a scientific test remain pending.

## Step 1. Define one primary scientific question

Write this in `docs/protocol.md`:

> How much short sliding-contact data is needed to predict a previously unseen surface's vibration response under another speed, direction, or nominal load? At the same contact-time budget, which second probe provides more information than repeating the first probe?

Define the terms:

| Term | Meaning in this study |
| --- | --- |
| Surface | One specimen ID in the dataset; not necessarily an entire material family |
| Support contact | A short measured contact the model may observe before predicting |
| Query condition | A requested speed, direction, and nominal load |
| Query response | The recorded vibration response hidden from prediction inputs |
| Unseen surface | A surface whose recordings were excluded from training and preprocessing-statistic fitting |
| Representation | A compact vector inferred from permitted support observations |
| Generalization | Prediction on held-out surfaces and explicitly identified held-out conditions |

Your initial target is **vibration spectral power**. Friction and compliance require additional evidence. The proposed encoder is a tool for answering the question, rather than the research contribution by itself.

Write the primary analysis cell explicitly, rather than leaving its budget or subset open to later selection:

| Field | Initial specification to freeze after the training/pilot audit |
| --- | --- |
| Condition experiment | New surfaces, familiar conditions |
| Support protocol and budget | `single`, 0.5 seconds at 40 mm/s, 0 degrees, 0.5 N |
| Query set | Common eligible conditions outside the union of all support conditions; repeat 1 |
| Comparison | Encoder/predictor versus nearest training-surface retrieval with the same held-out support |
| Metric and averaging | Raw log10 band-power MAE; mean over queries per surface, then mean over surfaces |
| Randomness and uncertainty | Average model initialization seeds within surface; paired surface/group bootstrap |

Use the longer durations and other methods as declared secondary analyses. For probe selection, predeclare direction versus repetition at two 0.5-second contacts as the main probe-choice contrast; report speed-versus-repetition and load-versus-repetition as well. The contrast measures prediction benefit from a fixed additional probe. It does not yet demonstrate adaptive probe selection, which would require a policy that chooses the next probe from the first observation and an independent evaluation of that policy.

Set a practical effect margin in log-power MAE units from training/pilot scales and repeat variability before opening test results. Record the scientific reason for that margin. Declare whether secondary comparisons are descriptive or use a specified multiplicity adjustment; isolated unadjusted intervals across many comparisons cannot establish every apparent benefit. Change initial choices only for documented audit findings and freeze them before test evaluation.

**Output:** `docs/protocol.md`, initially about one page.

**Checkpoint:** a reader can identify the observable inputs, hidden response, independent test units, primary comparison, and claim without seeing your code.

## Step 2. Read the closest papers and write the gap

Prioritize Heravi 2020/2024 and the Cluster documentation for Stage A. Read DiffTactile/TacTID before designing Stage B. ExSARN and HaptoFlow inform optional representations/renderers and need not delay the first pipeline. Read for these questions:

| Reference | Read for | Concrete note to produce |
| --- | --- | --- |
| Heravi et al., ICRA 2020 [R1] | Action-conditioned vibration prediction from tactile observations | List inputs, output, held-out setup, and similarities to your study |
| Heravi et al., IEEE Transactions on Haptics 2024 [R2] | Spectral prediction, rendering, and unseen-texture retrieval | Explain why retrieval is a necessary baseline |
| Cluster dataset paper and documentation [R3] | Acquisition, conditions, timing, and available labels | A data dictionary and limitations list |
| ExSARN, IROS 2021 [R4] | Compact tactile representation and sensor adaptation | What representation ideas you can use without assuming calibrated mechanics |
| HaptoFlow, 2026 [R5] | Interaction-conditioned vibrotactile generation | Why waveform generation is a later extension, after the first prediction study |
| DiffTactile, ICLR 2024 [R6] | Contact-parameter calibration and force-supervised simulation | What additional measurements enable the mechanical milestone |
| TacTID, 2024 [R7] | Friction and effective-stiffness inference | Existing mechanical inference methods and assumptions |

Create `docs/related_work.csv` with columns:

```text
paper,input_observations,conditioning,output,unseen_surface_test,
force_ground_truth,probe_budget_study,simulation_validation,
code_available,data_available,overlap_with_project,remaining_question
```

Use `unknown` when you have not verified a field. Record the page or section supporting each important entry. Check cited and citing papers around the closest works before making a novelty claim.

Heravi 2020 presents preliminary new-material embedding evidence; its main quantitative action/image tests use training materials. Heravi 2024 uses a nearest training representation for unseen textures. Your acceleration-support retrieval method adapts that idea to a different observation modality, so it is not an exact reproduction. [R1–R2]

Your candidate gap is a systematic, matched-budget investigation of brief moving probes and their information about response across conditions. A future extension tests whether that information supports calibrated sliding-force prediction. Treat this as a candidate contribution until a focused literature comparison supports it.

**Output:** the comparison table and a 150–250-word gap statement.

**Checkpoint:** you can explain how the experiment differs from action-conditioned rendering and from ordinary material classification, while acknowledging existing work.

## Step 3. Set up a reproducible workspace

The workspace is already implemented. Use Python 3.12, initially on CPU. From the repository directory in PowerShell, a clean installation is:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m tactile_contact --help
```

For Linux/macOS use `python3 -m venv .venv`, then `.venv/bin/python -m pip install -e ".[dev]"`. If a particular CPU/CUDA build is needed, install it with the [official PyTorch selector](https://pytorch.org/get-started/locally/) before installing the package. The existing Windows bootstrap reused numerical packages through `--system-site-packages`; actual run environments are saved in `results/environment.lock.txt` under each output root. Current measured runs used Python 3.12.6, NumPy 1.26.4, SciPy 1.15.1, and PyTorch 2.6.0+cu118 on CPU. A clean install may resolve different versions; record them and check numerical compatibility before comparing results.

| Implemented package module | Responsibility |
| --- | --- |
| `src/tactile_contact/cli.py`, `pipeline.py`, `config.py` | CLI orchestration, configuration validation, provenance/reuse guards |
| `download.py`, `records.py` | Bounded pinned HTTPS downloads, raw hashes, recording keys |
| `audit.py`, `timing.py` | Recording/specimen manifests, retrospective motion QC, clock sensitivity |
| `windows.py`, `signal.py` | Raw-window-bounded preparation, full PSD and spectral bands |
| `episodes.py` | Cohort/episode construction, prediction-input whitelist, train-only scaler |
| `baselines.py`, `models.py`, `training.py` | Five baselines, masked encoder, balanced training and checkpoint selection |
| `evaluation.py`, `metrics.py` | Partitioned scores, paired contrasts, diagnostics and group bootstrap |
| `synthetic.py` | Separate engineering fixtures |
| `scripts/summarize_expanded_pilot.py`, `summarize_omitted_speed.py` | Public aggregate reports and audit exports |

CLI subcommands are `download`, `audit`, `prepare`, `run`, `synth`, `figures`, and `timing`. They operate on existing modules; the old placeholder scripts are no longer implementation contracts. Downloads use Python HTTPS, requiring neither `huggingface_hub` nor Jupyter. Notebooks remain optional for inspection.

**Output:** installable package, declared dependencies in `pyproject.toml`, and per-run environment/provenance.

**Checkpoint:** a clean environment can import the package and reproduce a configuration's recorded workflow.

## Step 4. Download a small, versioned data subset

The current source is the [Cluster Parquet mirror](https://huggingface.co/datasets/tamago117/cluster-haptic-texture-dataset), pinned to revision `b7c2fb70ed2d68219389478660f35c2cd49c69fb`. Filename convention:

```text
sensor_data/accel/<surface_id>/<surface_id>_<direction>_<speed>_<force_mN>_<repeat>.parquet
```

Force and position use corresponding paths. Configuration and source inventory, rather than a fresh latest-revision lookup, define each reproducible selection. Existing configurations are bounded development runs:

| Config | Raw files | Requested recording triplets | Scope |
| --- | --- | --- | --- |
| `configs/pilot.yaml` | 362 | 120 | Single 0.5-second support, four familiar queries |
| `configs/expanded_pilot.yaml` | 578 | 192 | Five protocols, three durations, same four queries |
| `configs/omitted_speed.yaml` | 770 | 256 | Six permitted-speed queries, four omitted-speed queries |

For example, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m tactile_contact download --config configs/expanded_pilot.yaml --root runs/bounded_expanded_pilot --data-root .
.\.venv\Scripts\python.exe -m tactile_contact run --config configs/expanded_pilot.yaml --root runs/bounded_expanded_pilot --data-root .
.\.venv\Scripts\python.exe -m tactile_contact timing --config configs/expanded_pilot.yaml --root runs/bounded_expanded_pilot --data-root .
```

`--root` isolates prepared features, models and results; `--data-root .` shares the pinned measured raw cache. Config paths resolve from the shell's working directory. `run` prepares fresh unless `--reuse` is supplied; reuse verifies configuration and preparation-code hashes. After changing preparation, rebuild and rerun all methods in a new output root, retaining historical results.

The omitted-speed config skips training 30/50 mm/s records even when they are present in the shared cache. Synthetic fixtures use their own root (`runs/synthetic_check`) and are never mixed with measured data. See the [README](../README.md) for all executed command sequences.

**Output:** `data/source.json`, `data/raw_inventory.json`, immutable raw files and hashes at the configured raw-data root.

**Checkpoint:** each selected recording is tied to a fixed source revision and original content hash; downloading more files does not silently change derived runs.

## Step 5. Build the recording and specimen manifests

Filename parsing is implemented in `records.py`; do not encode material IDs as predictor inputs. The measured mirror uses acceleration `time_ns,X,Y,Z` in g, force `time_ns,force` in N, and position `time_ns,X,Y` in mm. [R3]

`data/manifests/recordings.csv` contains the common recording key and paths; nominal conditions/repeat; `qc_status`, `qc_reason`, steady interval and duration; `config_hash`, shared `origin_ns`; each channel's row count, median logged rate, mean rate, maximum gap, interval coefficient of variation and duration; acceleration clipping fraction; and measured-force mean/std over the selected longest steady interval. Duplicate/reset timestamps, invalid values and missing channels are checked during loading. These record-level force summaries are offline audit fields, not statistics of each support-duration window or predictor inputs.

`data/manifests/surfaces.csv` currently contains:

```text
surface_id,name,category,family_group,grouping_reason,grouping_reviewed,split,grouping_scope
```

The [complete metadata review](study_design_review.md) now records all 118 specimens in [87 conservative groups](../configs/all_specimen_groups.csv), with `grouping_scope=metadata_names_only`. Named variants and construction-only cloth uncertainty blocks are explicit; all manufacturing relationships remain unknown. The original 12-specimen grouping file is retained for historical provenance. A specimen-level study can proceed with documented limits; an unseen-manufacturing-family claim requires stronger evidence.

**Completed exposure ledger:** [all 118 rows](specimen_exposure_ledger.csv) distinguish metadata review from direct/group exposure. Six real-run histories yield 72 specimen/run events and a 304-recording union before wider QC. All existing IDs `[0,38,49,65,74,79,82,87,102,103,10,57]` are development-exposed; known/declared group links block 22 specimens from a fresh test. IDs 10 and 57 have repeatedly selected models and their transfer outcomes are known. Twenty metadata-only specimens in fifteen whole groups are reserved before broader signal review; they are not yet a scientifically frozen test.

Verify coverage across 80 condition triples and two repetitions without assuming all files/windows survive. Cluster's specimen friction metadata were measured with another counterface/protocol; they are not synchronized tangential-force labels for these scans. [R3]

**Output:** recording/surface manifests, complete grouping rules/table, historical access evidence, exposure ledger, protected reservation and [condition masks](../configs/query_domains.csv); wider coverage/attrition review follows.

**Checkpoint:** each channel maps to one recording key; group scope and development exposure are explicit rather than inferred from a review flag.

## Step 6. Audit time alignment, contact quality, and usable motion

Keep integer nanosecond timestamps and subtract one joint origin across acceleration, force and position before converting to seconds. Independently zeroing each channel can erase offsets; sorting cannot repair a reset. Audit synchronized plots, gaps, duplicates and interval variation. Acceleration is documented around 6 kHz, position around 100 Hz, and force acquisition at 80 Hz despite faster transmission. Repeated force values do not create independent high-frequency force samples. [R3]

Current measured QC fits a local quadratic to **21 native position samples at their actual timestamps**. It selects the longest interval with speed magnitude within `max(2 mm/s, 10% of nominal)` and measured normal force above 0.05 N; maximum logged gaps are 0.01 s for acceleration and 0.05 s for auxiliary channels. The 21-point choice was the smallest tested setting retaining full 0.5-second intervals on all 100 initial training recordings (11 points retained 80; 21/31 retained 100). This was a coverage decision, not proof of motion accuracy. Smoothing and interval selection are retrospective.

The fixed query duration is now **0.5 seconds** for every method. Support durations are 0.25/0.5/1 seconds. The initial, expanded and omitted runs passed QC for all 120/192/256 requested recording triplets respectively. That success applies to bounded selections, not the whole grid.

The logged acceleration rate averages about 8.63 kHz. The adopted logged-coordinate path interpolates at the rounded median local logged rate and anti-alias resamples to a computational 6 kHz grid. Training-only sensitivity compares timestamp-selected raw spans against contiguous nominal-6-kHz index timing: the omitted run's median nominal-duration ratio is 1.44 and median log-feature difference about 0.3914. Different nominal budgets make this a sensitivity diagnostic, not a matched-budget proof or clock calibration. See [timing audit](timing_audit.md) and the [corrected timing comparison](window_boundary_report.md).

**Completed timing decision:** `scripts/audit_source_clock.py` compared five preselected training records across three channels with original Figshare version-6 CSVs using 18.6 MB of exact bounded ZIP ranges. All fifteen CSVs match rounded nanoseconds and float32 signals. The discrepancy persists in originals; acquisition/transport timing remains unexplained. [logged_coordinates_v1](../configs/clock_convention.json) adopts logged-time windows and inverse-logged-time spectra for a limited empirical study, with physical frequency, physical probe duration and causal online latency uncalibrated. No predictor errors chose the clock. Changing the convention requires a versioned decision and rebuilt features, training statistics, libraries and methods on matched episodes. See [clock/source provenance and limitations](clock_qc_review.md).

**Completed bounded QC review:** `scripts/review_contact_qc.py` uses the [prespecified seven-setting review](../configs/qc_review.json) on 200 known-speed training records, ten conditions, both repeats. Current/11-point/31-point smoothing retains 200/166/200 full half-second and 199/57/200 full one-second intervals. Neighboring gap thresholds change no coverage here. A single global heading frame fits the three logged headings with maximum residual 0.0653 degrees; this is not independently tracked motion. Median time-weighted recorded force is 1.04865 × nominal and logged-position travel is 0.99062 × nominal distance. Retrospective diagnostic smoothing may use neighboring position samples; these quantities never enter predictor inputs. Retain current settings, publish deviations and continue wider category/condition/duration attrition review. No heading/load exclusion or setting selected by model error is introduced.

**Completed wider training QC:** `scripts/review_wider_coverage.py --download` enforces reservation preflight and audits all 48 known-speed conditions, both repeats, on ten already exposed training specimens. Current/11-point/31-point smoothing retains 960/812/960 half-second and 932/266/960 one-second records. Nearby gap limits change no coverage. `scripts/summarize_wider_coverage.py` checks that all fifty required supports retain one second and every one of the 440 known-speed specimen/query cells has both half-second repetitions. Current settings therefore support the intended training budget comparison without switching to the smoother with greater retention. See the [coverage report](wider_coverage_review.md); selection, transfer and reserved-test coverage are not established by this audit.

**Output:** current `audit_summary.json`, `motion_qc_comparison.json`, timing tables and audit plots; [clock/contact review](clock_qc_review.md), hashed source comparisons, [complete metadata/exposure](study_design_review.md), [wider training coverage](wider_coverage_review.md) and [repeat/feature/history diagnostics](development_diagnostics_review.md), with per-record/per-condition decisions and common-pool eligibility. Controlled convergence, repetition reversal and wider selection/transfer coverage remain pending.

**Checkpoint:** the chosen time convention has evidence or an explicit limitation; frozen QC defines valid targets without implying causal onset detection.

## Step 7. Lock material splits and eligible evaluation surfaces

Current model configs use ten training IDs and development validation IDs 10/57, with no scientific test. The [metadata-only reservation](../configs/test_reservation.csv) now protects twenty specimens in fifteen complete groups while coverage/protocol review continues. Existing pilot specimens stay in development; they need not all be reassigned to model training. Approximate 80/18/20 counts remain a capacity target, not a completed allocation or guarantee of 118 eligible surfaces.

Run `scripts/prepare_study_design.py --check-config CONFIG_PATH` before any new measured development selection. The wider-coverage runner enforces this reservation guard before downloads; existing experiment CLI commands require the explicit preflight. Reservation validation rejects split/exposed/forged groups and unknown IDs. Locked scientific access and scoring are still unimplemented; do not present the reservation as a completed held-out test.

The implemented `split_materials.csv` records IDs, group IDs and split. A future frozen split must also retain selection rationale, exposure/grouping scope and split seed. Assert disjoint IDs and known groups across train/validation/test, and split records before windows or fitted statistics. Unknown fabrication relationships limit the claim; do not relabel name-only review as family independence.

For matched durations/protocols, require all declared supports at the longest duration and a common query set, with both training query repeats where retrieval averages them. A full-cohort intersection may remove many conditions; inspect the coverage matrix before freezing a cohort/mask. Predeclare any revised mask or narrower duration comparison using development coverage, report excluded specimens/cells with reasons, and apply it equally to every method. Never choose eligibility by model error.

Keep seeds `[0,1,2]` and declare any additional group-split or reverse-repeat robustness checks prospectively. Selection/transfer targets on 10/57 are now development outcomes and cannot be reopened as a new test.

**Output:** exposure ledger, reviewed split scope, eligibility/condition masks with exclusions, and eventually a frozen fresh-test manifest.

**Checkpoint:** test groups are untouched by fitting, selection and inspected outcomes; every paired comparison uses the same cohort and queries.

## Step 8. Extract support and query windows

Define one start from a retrospectively selected steady interval and nested **raw** support intervals of 0.25/0.5/1 seconds. Query duration is fixed at 0.5 seconds in a different condition recording. Approach, stabilization, repositioning and retrospective start selection are outside the current observation budget. This is an offline steady-contact prediction experiment; online use would require causal detection and charged overhead.

**Historical defect, corrected 9 October:** preparation previously interpolated/filtered a full recording before cropping a processed prefix. Interpolation may bracket with a raw sample outside the allowed interval, and the centered polyphase filter may use neighboring raw acceleration before/after it. The historical raw indices described only the nominal interval. Current manifests additionally record processing-dependency indices, zero observed context before/after, endpoint padding, source-grid scope/count, output count and polyphase factors/filter design. The new tests verify isolation beyond metadata prefix bookkeeping. SciPy documents the [zero-phase FIR and padding behavior](https://docs.scipy.org/doc/scipy-1.15.1/reference/generated/scipy.signal.resample_poly.html). Across 688 matched windows, median per-window mean log-feature change is approximately 0.0038–0.0039 across experiments; this includes both local edges and locally estimated grid rates, rather than isolating outside-context influence.

**Implemented convention:** select raw samples in `[start, start + duration)`, estimate the source rate from allowed timestamps, interpolate a local grid with endpoint holding, and anti-alias resample with local line padding. Each output has exactly `round(duration * fs)` samples. Causal processing is a separate future experiment requiring fully charged history/initialization and latency. Do not silently borrow a bracket sample, filter margin or another repetition. Preserve exactly `round(duration_s * fs)` output samples where the declared local-processing convention supports them, reject insufficient intervals and record the local padding/grid rule. Keep physical amplitude and anti-alias filtering; interpolation alone is not an anti-alias filter.

Nested raw observations are mandatory for duration comparisons. Independently filtered shorter windows may differ at their edges from a longer window's processed prefix. Do not enforce processed-prefix identity if achieving it requires future acceleration.

Verification/artifacts completed for this convention (retain these guards on future changes):

1. Hold the selected interval and motion metadata fixed, perturb raw acceleration outside **each** allowed support interval, and confirm its processed feature vector does not change. Cover the first/last samples and interpolation/filter boundaries at every duration. Test interval selection separately.
2. Save exact allowed raw indices, actual processing dependencies, padding/history/filter margins and time convention. Require every dependency to lie inside the allowed interval or be explicitly charged.
3. Invalidate old caches and rerun scalers, response libraries, baseline selection, every encoder seed and metrics on aligned episodes. Preserve old reports as provisional; report the measured before/after effect without assuming its magnitude.

Current `windows.csv` stores IDs, split/role, duration, `start_s`/`end_s`, nominal conditions/repeat, `feature_path`, `source_grid_hz`, nominal raw indices, `window_config_hash` and `time_base_id`. Processing dependencies are now stored per window. Support-window force summaries remain **unimplemented**. Recording-level force remains offline QC; future force-informed input variants must use only force within the observed support. Hidden query force may define target QC or a labeled oracle analysis, never normal prediction input.

Current training and evaluation use deterministic cached starts; random-start augmentation and centered-window sensitivity are optional, unimplemented additions. Query QC is a frozen offline target definition and does not imply a deployed predictor knows future force/motion validity.

**Output completed:** corrected bounded preparation, dependency provenance, nine boundary tests, a 688-window real audit and regenerated deterministic windows/results in isolated roots.

**Checkpoint:** outside-window acceleration cannot change a support feature except through explicitly budgeted observations; raw-duration nesting and target-input separation both hold.

## Step 9. Implement spectral features with physical amplitude preserved

Spectral extraction is implemented in `src/tactile_contact/signal.py`; use that authoritative helper rather than copying another guide implementation. With Step 8's correction implemented, current settings are 6000 Hz in the declared coordinate system, 0.125-second Hann Welch segments, 50% overlap and 32 linear bands from 24 to 1000 Hz per axis. Absolute physical Hz remains conditional on Step 6's clock evidence.

Convert g to SI with 9.80665, demean each local window and preserve amplitude; do not normalize each contact to unit variance. Cache full PSD, actual frequency grid, band edges and bin counts, linear powers, `log10(power + 1e-10)` and modeled-band RMS. Integrate with rectangular sums of PSD-bin centers times bin width, assigning every modeled bin once and including the final 1000 Hz bin. Use this same convention for targets and rescaled PSDs. Changes require matched regeneration of all methods.

Flatten in band-major X/Y/Z order to 96 features/targets. The numerical floor is not a measured sensor-noise floor. The [training feature audit](development_diagnostics_review.md) checks all 92,160 current values: none are below `1e-8`, and the largest feature change from the current `1e-10` floor is 0.000221326. Retain `1e-10`. The 24–500/1000/1500 inverse logged-time alternatives change band widths/targets; lower repeat differences do not establish better prediction, so retain 24–1000. A dense encoder or a force-summary variant remains optional and unimplemented; the full PSD already supports the rescaling baseline at the same raw-contact budget.

Existing numerical checks verify spectral peaks, amplitude doubling (fourfold power; log10 change about 0.60206), offset removal, duration handling and modeled-band RMS. They verify the spectral helper, not acquisition timing or Step 8's processing boundary.

**Output:** full-PSD/band cache and declared spectral convention, rebuilt after preparation correction.

**Checkpoint:** finite 96-vectors preserve physical amplitude within the declared time convention, with consistent estimator settings across methods and durations.

## Step 10. Fit preprocessing using training surfaces only

Fit a feature scaler on permitted training support windows. Use a declared balanced sample across training surfaces, protocols, and durations; repeated episode references to one cached window must not change its statistical weight. For each spectral feature, save its training mean and standard deviation. Replace a near-zero standard deviation with 1 rather than amplifying a constant feature. Apply the saved scaler unchanged to validation/test support.

For the first model, keep query targets in raw log10 band-power units and train with mean absolute error in those units. This keeps training loss aligned with the primary reported metric. If you later standardize targets, fit that scaler on training targets only and invert it before reporting metrics.

Encode conditions explicitly:

```python
import numpy as np

def condition_vector(speed_mm_s, direction_deg, nominal_force_N):
    theta = np.deg2rad(direction_deg)
    return np.array([
        speed_mm_s / 40.0,
        np.cos(theta),
        np.sin(theta),
        nominal_force_N / 0.5,
    ], dtype=np.float32)
```

The periodic angle encoding avoids an artificial discontinuity between 0 and 315 degrees. It encodes the dataset's direction convention; do not use it to infer a world-coordinate velocity vector without checking that convention against position.

One default support vector contains:

```text
96 standardized log-band powers
4 observed condition features
1 observed duration / 1 second
= 101 input features per support contact
```

The query vector contains four requested condition features. An optional, unimplemented experiment adds two support-window force statistics, changing support dimension to 103. Evaluate that addition separately; the future measured query force remains excluded. The current scaler uses each unique training support-window ID once and records those IDs; omitted-speed fit guards are implemented.

For the globally omitted-speed experiment, rebuild the scaler from allowed training speeds only. A scaler fitted using 30/50 mm/s data would contaminate that experiment even if the neural-network training omitted those speeds.

**Output:** `data/features/scaler.npz`, feature order, and configuration hash.

**Checkpoint:** every transformation has a recorded training-only fit source, and the query target stays outside the model-input builder.

## Step 11. Build support/query episodes explicitly

Use these fixed support protocols, with `r0` denoting repeat 0:

| Protocol | Support conditions `(speed, direction, force, repeat)` |
| --- | --- |
| `single` | `(40, 0, 0.5, r0)` |
| `repeat` | `(40, 0, 0.5, r0)` and `(40, 0, 0.5, r1)` |
| `speed` | `(40, 0, 0.5, r0)` and `(20, 0, 0.5, r0)` |
| `load` | `(40, 0, 0.5, r0)` and `(40, 0, 1.0, r0)` |
| `direction` | `(40, 0, 0.5, r0)` and `(40, 90, 0.5, r0)` |

Exclude the following condition triples from the common query set for **every** protocol:

```python
FORBIDDEN_QUERY_CONDITIONS = {
    (40, 0, 0.5),
    (20, 0, 0.5),
    (40, 0, 1.0),
    (40, 90, 0.5),
}
```

The fully observed condition grid contains 80 triples, so a complete primary query grid has 76 triples before QC exclusions. Use repeat 1 for the fixed validation/test primary query response. Training may sample query repeat 0 or 1 outside the forbidden condition union, giving every fitted method access to the same allowed training response pool. A predeclared reverse-repeat check swaps repeat assignments consistently and is reported separately. The repeat-control protocol observes both reference repeats, but that reference condition is excluded from all queries.

Distinguish **per-contact duration** from **total observed time**. The second-probe comparison uses two contacts of equal duration for every two-probe protocol. To compare one versus two contacts at equal total time, score `single` at 1 second against each two-probe protocol at 0.5 seconds per contact; similarly compare 0.5 seconds against two 0.25-second contacts. Keep the cohort and queries identical. The current `total_support_distance_mm` is **nominal sliding distance**, computed as nominal speed times duration for each support; it is not integrated measured travel. Add measured path length from position before claiming a physical distance budget. Equal time or nominal distance does not imply equal traversed area. Repositioning time is not represented in this dataset, so these are observation-budget comparisons rather than complete robot execution-time comparisons.

Episode schema:

```text
episode_id,surface_id,family_group,experiment,evaluation_partition,split,protocol,duration_s,
support_window_ids,query_window_id,query_speed_mm_s,query_direction_deg,
query_nominal_force_N,query_repeat_id,total_support_time_s,total_support_distance_mm,config_hash
```

For every episode, assert:

- Support and query belong to the same surface within the correct material split.
- All support windows match the allowed protocol and duration.
- No support window or recording ID equals the query's.
- Query condition is outside the union of observed support conditions.
- Declared raw observation time and processing context are accounted for after Step 8 is corrected; no hidden extra repetitions are averaged into a held-out support feature.
- The prediction input includes support measurements, their conditions, and requested query conditions only.

Maintain two access functions: `make_prediction_inputs(episode)` returns support and query-condition tensors; `get_target(episode)` returns the hidden query response for training loss or scoring. This separation makes accidental target access easier to notice.

The implemented sampler balances surfaces and protocol/duration cells with 64 episodes per surface per epoch, using fixed cached support/query starts. Random-start augmentation is optional future work. `evaluation_partition` is `fit`, `selection` or `transfer`; fitting APIs reject transfer episodes and omitted speeds even if a partition label is forged. Transfer targets are accessed only after every method and seed checkpoint is selected. They are now known development outcomes on 10/57.

For validation/test, store a fixed episode list. Use all common eligible queries and identical episode ordering for all methods. Cache targets once rather than letting each predictor rebuild its own favorable evaluation set.

**Output:** train episode rules and fixed validation/test episode manifests.

**Checkpoint:** substituting a prediction implementation cannot change the evaluation samples or reveal query measurements.

## Step 12. Implement the baselines before the encoder

### Baseline A: requested conditions only

Fit a small regression model from the four query-condition features to the 96-dimensional query log spectrum, using training episodes. This estimates the average response of training surfaces. It receives no test surface observation.

The implemented conditions-only method is float64 ridge with alpha 1. A conditions-only MLP is optional, unimplemented work. All fitted regressions give each training specimen total weight one, independent of repeated protocol/duration cells.

### Baseline B: reuse the observed spectrum

For one probe, return its log spectrum. For two probes, average their **linear band powers** and then take the log. Averaging logarithms instead would be a different baseline and should be labeled as such.

This method ignores query conditions. Its purpose is to establish whether prediction improves beyond copying the measurement.

### Baseline C: rescale the observed spectrum by speed

Keep the support's full PSD from Step 9. With speed ratio `s = query_speed / support_speed` and nominal-load ratio `r = query_load / support_load`, use the proposed approximation:

\[
\hat S_q(f)=s^{p-1}r^{b}S_s(f/s).
\]

Here `p` is a power-scaling exponent and `b` is a load-scaling exponent. They are fitted on training pairs and checked on validation surfaces. The factor `1/s` accounts for frequency-axis stretching; a simple geometric acceleration model suggests an illustrative `p=4`, but the apparatus response may not obey that idealization. Do not assume that exponent is empirically correct.

Implement interpolation of `S_s(f/s)`, then integrate over the same target bands. Reject unsupported frequency extrapolation or report it explicitly. With the starter query band up to 1000 Hz and this dataset's speed ratios, retaining the full 6 kHz-sampled support PSD provides the needed source-frequency range, subject to the data audit confirming its validity.

The implementation fits above-floor training log powers with ridge candidates `[0,0.1,1]`, bounds `p` to [-4,8] and `b` to [-4,4], and selects on validation surfaces. Never optimize them on test spectra. Freeze the following rule so the baseline returns predictions for the complete primary grid: choose the support with the smallest circular angular difference to the query, break ties by the smallest absolute log speed ratio, then by its canonical protocol order. Rescale that support PSD and ignore any remaining angular mismatch. Label this the direction-agnostic rescaling baseline; it cannot model directional variation.

Also report a same-direction diagnostic subset, where the selected support and query directions match exactly. Score every compared method on that same subset, and give its condition/specimen count. This subset does not replace the common-grid primary evaluation.

This dense-PSD baseline has access to the same raw support contacts but a less compressed signal representation. Label it accordingly. If it dominates the compact encoder, test whether compression caused the failure before attributing it to learning itself.

### Baseline D: nearest training-surface retrieval

For each training surface, build a fingerprint under each allowed support protocol/duration. Use the same feature definitions as the test support. For the primary retrieval baseline, construct the training fingerprint from exactly the protocol-prescribed support records and duration, in a fixed contact order. Flatten the standardized spectral support features and use Euclidean distance; the common condition/duration fields are fixed within a library and need not affect its distance. In the optional force-summary experiment, append the same permitted force summaries with training-only scaling to retrieval and fixed-feature regression, so additional information is available to each comparison method. The library never uses held-out-surface queries. A repeat-averaged fingerprint is a separately labeled stronger-library check with its additional offline calibration disclosed.

At inference:

1. Compute the unfamiliar surface's fingerprint from its allowed support only.
2. Find the nearest training fingerprint using training-fitted feature scaling.
3. Retrieve that training surface's spectrum at the requested condition. Default to both permitted training repeats: average linear band powers, then take `log10(power + floor)`. Training response records are offline calibration, distinct from the held-out surface's brief-support budget. Make the same training-record pool available to all fitted methods. Save the exact source records and aggregation.

For the globally omitted-speed experiment, **do not retrieve the training surface's recorded 30/50 mm/s response**. Interpolate log powers from same-direction/load 20/40 endpoints for 30 and 40/60 endpoints for 50, with weights 0.5/0.5 after repeat responses are averaged in linear power. This geometric-power approximation is predictive, not a validated physical law. Exact endpoint IDs/weights are saved; missing or forbidden endpoints and extrapolation fail. Step 15 specifies the 26-cell endpoint-safe full-grid scope.

Restrict each library to training surfaces with valid fingerprints and the required response coverage, using fixed QC rules; report its size. Break equal distances by a fixed sorted training ID. Never put validation or test surfaces in the retrieval library. Save the retrieved training ID as a diagnostic, not a prediction input to the learned model.

### Baseline E: measured features plus regression

Implemented fixed-feature ridge uses mean/std of the permitted 101-dimensional support vectors, probe count and requested conditions. Its scaler is fitted on weighted training episodes; alpha candidates `[0.01,0.1,1,10,100]` are selected by equal-cell validation MAE. Support-by-query interactions are optional and unimplemented.

This asks whether a learned bottleneck provides value beyond ordinary spectral features.

### Control: wrong-surface support

Replace a test surface's support with another test surface's support at the same protocol/duration, while keeping requested query conditions and hidden target unchanged. Substitute all support fields together, including any measured support-force summaries. No wrong surface's query measurements are exposed. Use a fixed derangement with no self-matches. Keep this mapping identical across model seeds.

An optional harder control swaps within category when enough held-out specimens exist. Label the eligible subset and report it separately.

**Output:** predictions from every baseline and control, on the same episodes.

**Checkpoint:** each baseline uses only permitted inputs; nearest retrieval never reads omitted-speed labels or a held-out surface's response.

## Step 13. Implement the small encoder and predictor

Use one model trained across the declared one- and two-probe protocols and durations. This holds network capacity constant when comparing probe choices. If you instead train separate models, report that design and match training budgets.

Default tensors:

| Tensor | Shape | Meaning |
| --- | --- | --- |
| `support` | `[batch, 2, 101]` | Up to two support contacts; padded slots are masked |
| `support_mask` | `[batch, 2]` | 1 for an observed contact, 0 for padding |
| `query_condition` | `[batch, 4]` | Requested speed, angle encoding, nominal load |
| `target_log_power` | `[batch, 96]` | Hidden query log10 band powers |
| `z` | `[batch, 16]` | Pooled inferred representation |

Starter code for `src/tactile_contact/models.py`:

```python
import torch
from torch import nn

class ContactPredictor(nn.Module):
    def __init__(self, support_dim=101, output_dim=96, latent_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(support_dim, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, latent_dim),
        )
        self.predictor = nn.Sequential(
            nn.Linear(latent_dim + 4 + 1, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, output_dim),
        )

    def forward(self, support, support_mask, query_condition):
        if support.ndim != 3 or support.shape[-1] != self.encoder[0].in_features:
            raise ValueError("Expected [batch, slots, support_dim]")
        if support_mask.shape != support.shape[:2]:
            raise ValueError("Support mask must match batch and slots")
        if query_condition.shape != (support.shape[0], 4):
            raise ValueError("Expected four query-condition features per episode")
        if not torch.all((support_mask == 0) | (support_mask == 1)):
            raise ValueError("Support mask must contain only zero or one")
        if not torch.isfinite(support).all() or not torch.isfinite(query_condition).all():
            raise ValueError("Inputs must be finite; use finite zero padding")
        mask = support_mask.to(device=support.device, dtype=support.dtype)
        count = mask.sum(dim=1, keepdim=True)
        if torch.any(count <= 0):
            raise ValueError("Every episode needs at least one support contact")
        encoded = self.encoder(support)
        z = (encoded * mask.unsqueeze(-1)).sum(dim=1) / count
        context = torch.cat([z, query_condition, count / 2.0], dim=1)
        return self.predictor(context), z
```

Use finite zero padding; multiplying an encoded NaN by a zero mask would still propagate NaN. Mean pooling makes the support-set representation invariant to probe order. The encoder sees each observation's condition, so speed/load-dependent changes can be interpreted. Probe count is explicit rather than hidden in zero padding.

Implemented training choices: Adam at `1e-3`, batch size 128, at most 60 epochs, gradient-norm clipping at 1, and early stopping after 10 epochs without improved **validation per-surface raw log-power MAE**. Use training-only sampling, the same three initialization seeds, and a fixed validation episode manifest. For checkpoint selection, first average queries per surface in each protocol/duration cell, then average surfaces, then give each declared cell equal weight. The current history saves the equal-cell aggregate only. A large query subset must not dominate selection merely because it has more rows.

Corrected expanded checkpoints select epochs 58/59/60 and corrected omitted-speed checkpoints 59/60/58. The [saved-history review](development_diagnostics_review.md) finds final-ten-epoch best-score improvements of 1.4–3.2% and 5.3–9.4%, respectively. Convergence remains unresolved.

**Proposed next check, not executed:** freshly train unchanged cohorts/seeds with a finite 120-epoch cap and unchanged optimizer/sampler/patience. Preserve each experiment's original fitting and selection domains: expanded familiar selection keeps its four query triples including 30/50 mm/s; omitted selection keeps only its six 20/40/60 triples. Add primary single-0.5 selection history as a diagnostic; keep the equal-cell checkpoint-selection rule. Save best-by-60/120 checkpoints and actual stop reasons, and verify first-60 reproduction. Preserve historical roots and do not resume weights without optimizer/sampler state. If the cap still binds, report it rather than repeatedly increasing it to pursue a victory. Final selections precede any new transfer scoring. The later matched 70/44 comparison uses common known-speed selection and is a separate experiment.

Minimal training-step example:

```python
model.train()
optimizer.zero_grad(set_to_none=True)
prediction, _ = model(support, support_mask, query_condition)
loss = torch.nn.functional.l1_loss(prediction, target_log_power)
loss.backward()
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
optimizer.step()
```

Use `model.eval()` and `torch.no_grad()` for validation/test. Save model weights, feature/scaler configuration, split and episode hashes, initialization seed, optimizer settings, selected epoch, and environment information together.

Before real training, set Python, NumPy, and PyTorch seeds. If using CUDA, document device and deterministic settings; fixed seeds alone do not establish identical results across hardware or library versions. Do not claim more reproducibility than you measured.

**Output:** training script, checkpoint format, and one trained development checkpoint.

**Checkpoint:** the model accepts both one and two masked probes, returns 96 outputs, and has no material-ID or future-query-measurement input.

## Step 14. Perform engineering checks before scientific evaluation

The latest executed source-code verification completed **78 tests** plus compilation. The earlier [implementation checks](implementation_checks.md) remain historical; later [boundary](window_boundary_report.md), [design/coverage](study_design_review.md) and [diagnostic](development_diagnostics_review.md) reports record added guards. Tests cover spectra/units, motion fitting, split/query exclusions, cached prefix bookkeeping, masked/order-invariant inputs, train-only fitting, retrieval aggregation, wrong support, bootstrap guards, checkpoint restoration, tiny-fit optimization, provenance/reuse, omitted-speed isolation, reservation/domain checks and repeat/floor/history diagnostics. Synthetic behavior is an engineering check, not physical contact validation.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src tests scripts
```

**Implemented guards:** whole-group reservation/exposure preflight, complete metadata/domain masks, exact known-speed diagnostic identities/denominators, and Step 8's outside-window checks. New review runners enforce reservation preflight; the original experiment CLI still needs the separate preflight. **Remaining required checks:** convergence-extension history/checkpoint identity, integrated matched fitting/selection/scoring roles and QC intersections, reversal consistency, and a frozen scoring path that cannot select/refit from test labels. Current configuration deliberately rejects `stage: test`; locked scoring is unimplemented. These guards do not certify physical timing, measured distance, force/motion control or manufacturing-family independence.

Keep tiny-fit/debugging results separate from scientific comparisons. Inspect gradient flow, raw loss scale and support variation if mean predictions persist; a functioning model is not evidence it outperforms retrieval.

**Output:** updated implementation checks for each source change and explicit unverified physical/scientific assumptions.

**Checkpoint:** relevant engineering guards pass, and the remaining scientific assumptions are not presented as established by the test count.

## Step 15. Freeze choices using validation data, then run the test

**Current status:** only development is supported. Implement and verify a separate frozen prediction/scoring path before adding scientific test IDs; it must load frozen preprocessing, libraries and checkpoints without fitting or selecting on test targets. All 12 existing specimens remain development data. Keep architecture/feature exploration modest and recorded; do not promote the current winning fixed-feature baseline to a retrospectively chosen primary comparison.

Retain the intended primary cell: **encoder versus retrieval, `single`, 0.5-second support, familiar conditions**. Retain direction versus repetition at two 0.5-second contacts as the main probe-choice contrast. Decide a practical margin from development scales/repeat context and a descriptive or multiplicity-adjusted secondary policy before opening fresh-test results. These decisions are not yet frozen.

Separate condition experiments and their pre-QC candidate domains:

| Experiment | Fit/selection speeds | Candidate query triples | Retrieval-safe scope |
| --- | --- | --- | --- |
| Familiar conditions | 20/30/40/50/60 | 80 minus four support triples = **76** | Same permitted training condition |
| Omitted-speed known-condition selection | 20/40/60 | 48 minus four support triples = **44** | Permitted training endpoints only |
| Omitted-speed transfer | 30/50 | **32** possible triples | **26** same-direction/load bracketable triples |

For each omitted speed, transfer at `(direction,load)=(0,0.5),(0,1.0),(90,0.5)` lacks at least one permitted retrieval endpoint because the endpoint is in the excluded support union. These six cells are excluded from the matched 26-cell comparator domain. Publish exact masks and reasons; do not restore coverage by retrieving excluded support responses or hidden 30/50 labels. An additional six-cell analysis requires a separately predeclared comparator/contract. Further QC may reduce all counts.

Current omitted evidence covers only six fit/selection triples and four transfer triples at 45/90 degrees, 1 N. Its query grid differs from the familiar pilot. Before attributing differences to global speed withholding, run a **matched-grid familiar development comparator** on identical 30/50 direction/load targets, with the additional permitted familiar-speed training responses, identical raw budgets/cohort and declared selection rules. Refit scalers, exponents, libraries and models separately; changing the response pool is the intended treatment. Transfer results on existing specimens stay developmental.

Before test scoring freeze and hash:

```text
source revision, raw inventory and environment
strict support-processing boundary/dependencies, timing convention and claim scope
QC rules, coverage/attrition, nominal versus measured budgets
exposure ledger, known groups, fresh split, eligible cohort and exact condition masks
support/query repetitions, starts, feature/scaler definitions and floor
baseline contracts/fitted choices, model configuration and selected checkpoints
primary comparison, practical effect margin, seed/group aggregation
secondary policy, load/direction subsets, reverse-repeat and other planned robustness
locked prediction/scoring interface and reproducible release artifacts
```

Load transfer is 1 N queries for protocols observing only 0.5 N (`single`, `repeat`, `speed`, `direction`). The `load` protocol observes both loads. Define unobserved directions per protocol and their intersection for matched comparisons. Publish exact masks/counts. Neither two loads nor the available speed range establishes arbitrary extrapolation.

Run the frozen main test once and only predeclared robustness checks afterward. If a genuine software bug is found, record it and rerun every affected method consistently. Do not redesign QC, cohorts or architecture to rescue test scores.

**Output:** frozen bundle and fresh-test raw predictions, after the preceding development gates are met.

**Checkpoint:** fitting/selection cannot read test targets; claims identify exact held-out groups, condition domain and accounted observation budget.

## Step 16. Compute metrics and confidence intervals correctly

Save one row per query:

```text
experiment,model,seed,episode_id,surface_id,family_group,protocol,duration_s,
query_speed_mm_s,query_direction_deg,query_nominal_force_N,
log_power_mae,rms_error_X,rms_error_Y,rms_error_Z,modeled_band_total_rms_error,
retrieved_training_id,config_hash
```

Current `per_query.csv` also carries `evaluation_partition`; checkpoint paths are recorded in the run manifest and can be mapped by seed/configuration, rather than stored in each score row. Per-axis log-power diagnostics can be derived from saved prediction arrays and remain part of the required analysis. Primary error for a query is the mean absolute difference across its 96 log10 band-power entries. First average over query conditions within a surface, then average across surfaces. This prevents surfaces with more valid windows from dominating.

Recover modeled-band amplitude from spectra:

```python
import numpy as np

def rms_from_log_power(log_power, floor=1e-10):
    log_power = np.asarray(log_power, dtype=np.float64).reshape(-1, 32, 3)
    linear_power = np.maximum(np.power(10.0, log_power) - floor, 0.0)
    rms_axes = np.sqrt(linear_power.sum(axis=1))
    rms_total = np.sqrt(linear_power.sum(axis=(1, 2)))
    return rms_axes, rms_total
```

Keep this metric limited to the modeled frequency band. Do not call it total physical acceleration RMS over frequencies you did not predict. Use absolute amplitude errors as primary amplitude diagnostics; relative errors need a documented denominator floor near zero.

Compare methods using paired surface errors, averaging initialization seeds within each surface for the main paired comparison and reporting seed variation separately. Treat specimen families as bootstrap clusters where appropriate. Supply homogeneous, nonmissing group IDs from the frozen manifest. The helper resamples whole families and retains a surface-weighted mean within each draw; large families contain more surfaces and therefore more weight. Use a different, predeclared estimator if the question calls for equal weight per family.

The following bootstrap illustration describes the estimator; the implemented helper in `src/tactile_contact/metrics.py` is authoritative:

```python
import numpy as np

def paired_bootstrap(baseline_error, proposed_error, group_ids=None,
                     draws=10000, seed=7):
    a = np.asarray(baseline_error, dtype=np.float64)
    b = np.asarray(proposed_error, dtype=np.float64)
    if a.ndim != 1 or a.shape != b.shape or len(a) == 0:
        raise ValueError("Need matching nonempty per-surface error arrays")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Nonfinite errors")
    if not isinstance(draws, (int, np.integer)) or draws < 1:
        raise ValueError("draws must be a positive integer")
    groups = (np.arange(len(a), dtype=object) if group_ids is None
              else np.asarray(group_ids, dtype=object))
    if groups.shape != a.shape:
        raise ValueError("Group IDs must align with surfaces")
    def valid_group_id(g):
        if g is None:
            return False
        if isinstance(g, (str, np.str_)):
            return bool(g.strip())
        if isinstance(g, (int, float, np.integer, np.floating)):
            return bool(np.isfinite(g))
        return False
    if not all(valid_group_id(g) for g in groups):
        raise ValueError("Group IDs must be nonmissing scalar strings or numbers")
    string_ids = all(isinstance(g, (str, np.str_)) for g in groups)
    numeric_ids = all(isinstance(g, (int, float, np.integer, np.floating)) for g in groups)
    if not (string_ids or numeric_ids):
        raise ValueError("Use homogeneous string or numeric group IDs")
    unique = np.unique(groups)
    members = [np.flatnonzero(groups == g) for g in unique]
    delta = a - b  # positive means lower error for the proposed method
    rng = np.random.default_rng(seed)
    boot = np.empty(draws)
    for i in range(draws):
        chosen = rng.integers(0, len(members), size=len(members))
        indices = np.concatenate([members[j] for j in chosen])
        boot[i] = delta[indices].mean()
    return {
        "mean_improvement": float(delta.mean()),
        "ci95": np.quantile(boot, [0.025, 0.975]).tolist(),
        "surfaces": len(a),
        "independent_groups": len(unique),
    }
```

An interval spanning zero is inconclusive about the sign of the mean improvement under this analysis: it does not establish equivalence. Claim a practically meaningful improvement only when the interval supports the predeclared positive effect margin. Claim practical equivalence only with a specified equivalence procedure and margin; otherwise report that this evaluation has not demonstrated an advantage. A statistically clear small effect can still fall below the intended use's needs.

Report absolute paired improvement in log10-power MAE units, its interval, and independent group count. Percent error reduction is optional and unstable when baseline error is near zero. A log-power difference describes a ratio of band powers; it is not directly a force or motion improvement. Bootstrap intervals condition on this split and library, and a small number of independent groups limits their precision.

These intervals concern mean method differences. If predictive uncertainty for individual responses is added, fit/calibrate it using training/validation groups and evaluate coverage and interval width on held-out surfaces. Ensemble disagreement alone does not establish calibrated prediction uncertainty.

The [training repeat tables](development_diagnostics_review.md) now provide 480 pairs, including 440 known-query pairs; mean query difference is 0.172972 log-power units and specimens 102/103 vary more. Retain all specimens. These independently recorded windows are not spatially aligned; they give limited variability context, not a noise ceiling. The matched prediction reverse-repeat sensitivity remains pending. The present two-validation-group intervals are descriptive engineering diagnostics even when an individual interval excludes zero. Additional windows from a repetition are correlated observations rather than extra independent specimens.

**Output:** per-query/per-surface tables, paired improvements, bootstrap intervals, and seed variability.

**Checkpoint:** the reported sample size reflects independent surfaces/groups; all methods are compared on aligned samples.

## Step 17. Make figures, interpret failures, and finish the public study

Existing development figures include duration/probe curves, reference audits, [training repeat context and learning curves](development_diagnostics_review.md). Extend them with condition/specimen failures and the eventual frozen-study results; the final report should contain:

1. Paired support/query panels, each with synchronized acceleration, force, and motion channels and the selected window marked.
2. Predicted and measured spectra for successes and failures, using the same selection rule for all models.
3. Error versus support duration.
4. Two-probe error by second-probe type, with the repetition control.
5. Error by query speed, nominal load, and direction.
6. Paired per-surface improvement over retrieval; show the full distribution.
7. Correct-support versus wrong-support performance.
8. Repeated-recording differences as limited repeatability context; the training version is complete, while matched prediction repetition reversal remains pending.

Use plots generated from saved tables, rather than manually selected notebook states. Include specimen counts and confidence-interval units in captions. Example selection should be reproducible, such as median, best, and worst surface by a predeclared metric—not a collection of attractive predictions.

Interpretation rules:

| Observation | Defensible interpretation | Next action |
| --- | --- | --- |
| Wrong support performs similarly | Model has not demonstrated useful surface-specific conditioning | Inspect apparatus/condition signals and inference bottleneck |
| Paired retrieval/model difference is inconclusive | This evaluation has not demonstrated an advantage for the learned embedding; equivalence requires its own margin/test | Report it; examine input compression and probe information |
| Perpendicular probe beats repetition at equal time | The orthogonal contact adds useful observations under this acquisition protocol | Examine anisotropy, spatial path differences, and surface heterogeneity |
| Load probe helps while one-load transfer fails | One observed load does not adequately constrain loading response | Audit actual load variation; measure more loads later |
| Spectra improve but amplitudes remain wrong | Shape similarity is insufficient for physically scaled response | Inspect normalization, floors, and force dependence |
| All methods are poor and repeats disagree strongly | Target variability or measurement limits may dominate | Revisit the prediction target and need for more independent trials |

Direction changes can alter the scanned path and surface patch as well as heading. Equal declared time and nominal speed-times-duration distance do not isolate intrinsic anisotropy; use position metadata to characterize coverage and preserve these alternatives in the conclusion.

Write a short report with: question, related work, data/protocol, baselines/method, results, ablations/failures, limitations, and mechanical extension. A 6–8-page main report plus appendix is a practical target, not an admissions requirement.

Use an accurate title, initially **Brief Contact Probes for Predicting Texture Responses Across Interaction Conditions**. Describe the completed work as an independent tactile-response study. Include mechanical identification and robot learning as future work until those experiments are completed.

**Stage A completion gate:** correct/verify bounded preparation; justify the clock or explicitly narrow to a logged-coordinate study; complete exposure/coverage review and fresh locked evaluation; save the primary paired comparison, declared duration/probe contrasts, wrong-support and load/direction results, separately fitted omitted-speed analysis, exclusions, repeatability and convergence context. Package the report and reproducible artifacts. A logged-coordinate completion answers an empirical feature-prediction question; calibrated physical frequency/duration claims remain open. If coverage prevents a contrast, explain the limitation and narrow the answered question. A simple baseline winning is a valid completed result.

**Output:** report, figures, configurations, code, and a concise completed-work description.

**Checkpoint:** you can answer what was learned, which alternative explanations were tested, and what remains unresolved, even if a simple method won.

## Step 18. Decide whether the mechanical milestone is currently feasible

While completing the public study, draft a capability inquiry for a potential mentor or partner, supported by the protocol and provisional figures. Sending an inquiry requires separate user authorization. Identify actual calibrated rig capabilities rather than assuming a tactile kit includes independent force ground truth. Stage B can proceed with suitable measurements even if retrieval wins Stage A; an encoder advantage is not its gate. No rig access or mechanical dataset adequacy is currently confirmed. Steps 19–25 below remain future-work specifications and illustrative mechanics code.

Required measurements/capabilities:

| Requirement | Why it is needed |
| --- | --- |
| Normal force independent of the tactile estimator | Loading ground truth and force-ratio calibration |
| Tangential force independent of the tactile estimator | Sliding resistance ground truth |
| Known probe geometry and counterface | Defines the physical contact being identified |
| Controlled relative motion | Separates material/contact effects from changing actions |
| Position and velocity measurements | Motion alignment and confirmation of sliding |
| Tactile signal or probe acceleration | Observation input and connection to Stage A |
| Repeatable mounting and timestamps | Calibration and repeatability |

A linear stage or repeatable planar fixture can be enough. A robotic hand is not necessary. Choose hardware only after defining the required force range, sensitivity, timing, and fixture arrangement.

If using a public force dataset, verify downloadable raw force/motion channels, timestamps, probe geometry, condition variation, and sufficient independent surface specimens. DiffTactile's paper and code are relevant, but described real recordings should not be treated as available until access is verified. Two surfaces can support a calibration demonstration, not a broad unseen-material claim.

If access remains unavailable, complete the public report and describe mechanics as the next experimental milestone. A simulation-only identification study can be added and labeled as simulation-only; it does not replace real validation.

**Output:** `docs/mechanics_access.md` with available measurements, missing capabilities, and the chosen scope.

**Checkpoint:** you can identify which device produces each ground-truth quantity and which measurements are actually obtainable.

## Step 19. Calibrate the force-and-motion measurement chain

Start with rigid flat surfaces and a fixed probe. Keep geometry, mounting, and orientation unchanged during the pilot. Record the probe material and dimensions.

Perform these engineering measurements before collecting research trials:

1. Zero force readings with no contact and estimate offset drift.
2. Apply known normal loads across the intended range and fit/check the calibration.
3. Apply known tangential loads and check calibration and normal/tangential cross-axis coupling.
4. Verify force signs and coordinate transforms with known directional motion.
5. Measure fixture/guide drag independently where it can influence tangential force.
6. Verify encoder scale and actual motion against an independent length reference if needed.
7. Check temporal offsets using an event observable in both motion/tactile and force channels.
8. Repeat a reference contact before and after sessions to measure drift.

Choose operating loads that produce sliding forces clearly above effective measurement uncertainty. If a predicted improvement is smaller than calibration error or repeat variability, the rig cannot convincingly establish it.

Store `configs/calibration.json` with units, coefficients, uncertainties, signs, transforms, offsets, date, instrument IDs, probe ID, and mounting/session IDs. Raw readings remain unchanged; calibrated data are a derived product.

For compliance later, also characterize deformation in the probe, fixture, and mounting. Force divided by actuator travel is not automatically the surface's stiffness.

**Output:** calibration report, reference trials, and a documented operating range.

**Checkpoint:** the measured force differences of interest exceed the instrument/fixture uncertainty and calibration is repeatable across sessions.

## Step 20. Collect a small randomized sliding-contact pilot

Starting proposal: 8–12 distinct surface specimens, three usable speeds, three nominal loads, and five independent repetitions per condition. At ten surfaces this is 450 trials. Repeated windows from a single trial do not count as those repetitions.

Select speeds and loads within the calibrated rig's operating range. Keep initial sliding direction fixed. This first mechanical question concerns speed/load dependence; add directional friction in a later expansion.

Distribute repetitions across at least two sessions when feasible. Randomize trial order within practical blocks, record cleaning/replacement procedures, and include reference trials to distinguish surface effects from drift or wear.

Each trial should include approach, contact establishment, steady sliding, and release. Record enough steady contact for permitted support intervals and separate query trials. Identify continuous sliding from measured relative motion; do not infer kinetic friction from arbitrary sticking contacts.

Save one synchronized derived table per trial:

```text
time_s,position_x_m,position_z_m,velocity_x_m_s,
commanded_velocity_x_m_s,commanded_normal_force_N,
measured_normal_force_N,measured_tangential_force_N,
accel_X_m_s2,accel_Y_m_s2,accel_Z_m_s2,
contact_state,surface_id,probe_id,session_id,trial_id,calibration_id
```

If the rig controls height rather than force, call the input a height command and record the resulting normal force. Do not describe it as a perfectly controlled normal-load experiment. A later forward model will need a normal contact relation or another justified way to compute the reaction force.

Save metadata separately: geometry, counterface, material specimen, mounting, trial conditions, raw paths, and QC flags. Define valid sliding intervals using calibrated motion/contact criteria before scoring model errors.

Before collection, write `configs/mechanics_protocol.yaml` with the reference speed/load, supported observation durations, input interface, specimen/session split, trial reservations, query conditions, primary metric, and exclusion rules. A concrete five-repeat starting contract is:

| Trial role | Permitted use |
| --- | --- |
| Repeat 0 at the reference speed/load | Brief support; initially the first 0.5 seconds of valid steady sliding, with nested durations if feasible |
| Repeats 0–2 at all conditions | Reserved richer calibration pool; disclosed higher-data reference only |
| Repeats 3–4 at nonreference conditions | Common query trials for every method; no fitting or test-surface calibration |

These role restrictions govern calibration and prediction for a held-out surface. Global coefficients, shared parameters, and tactile regressions may be fitted from all allowed training-surface records; in each inner validation fold, apply the same brief-support/query separation to its held-out surfaces and hide their query targets during fitting. The brief support trial is within the richer pool, but only its prescribed prefix is visible to brief methods. In the main cross-condition result, exclude the reference speed/load from queries. Evaluate all remaining valid speed/load cells with separate query trials and identical per-surface aggregation for every method. Save trial IDs and exact intervals; invalid trials follow frozen replacement/exclusion rules.

Balance collection order so reserved query repeats are not automatically later in time; repeat labels designate independent trials, not a chronological block. Distribute each role across sessions when feasible and disclose the session assignments. A same-session result and a deliberately held-out-session result answer different questions. Report extra calibration time/travel for the richer reference. If the rig cannot supply this contract, revise it before examining held-out outcomes.

**Output:** a versioned force/tactile/motion pilot dataset, mechanical episode manifest, and collection notes.

**Checkpoint:** independent trials and sessions are identifiable, and each target force has a synchronized action and motion context.

## Step 21. Fit the simplest sliding-friction model first

For confirmed one-dimensional sliding, the starter law is:

\[
F_t=-\mu_k F_n\operatorname{sign}(v).
\]

Fit the effective coefficient using only allowed support intervals. The measured normal/tangential support forces are legitimate inputs for this **force-informed** calibration.

Put the following numerical helper in `src/tactile_contact/friction.py`:

```python
import numpy as np

def fit_sliding_mu(normal_force, tangential_force, velocity,
                   min_normal=0.05, min_speed=0.001):
    """Fit a nonnegative Coulomb coefficient from confirmed sliding support.

    SI units; velocity is signed. Thresholds must be calibrated for the rig.
    The measured tangential force is the contact force on the moving body.
    """
    if (not np.isfinite(min_normal) or min_normal <= 0
            or not np.isfinite(min_speed) or min_speed < 0):
        raise ValueError("Invalid sliding thresholds")
    fn = np.asarray(normal_force, dtype=np.float64)
    ft = np.asarray(tangential_force, dtype=np.float64)
    v = np.asarray(velocity, dtype=np.float64)
    if fn.shape != ft.shape or fn.shape != v.shape or fn.ndim != 1:
        raise ValueError("Expected aligned one-dimensional arrays")
    valid = (np.isfinite(fn) & np.isfinite(ft) & np.isfinite(v)
             & (fn > min_normal) & (np.abs(v) > min_speed))
    if valid.sum() < 3:
        raise ValueError("Insufficient valid sliding samples")
    resistance = -ft[valid] * np.sign(v[valid])
    denominator = np.dot(fn[valid], fn[valid])
    numerator = np.dot(fn[valid], resistance)
    if not np.isfinite(denominator) or denominator <= 0 or not np.isfinite(numerator):
        raise ValueError("Invalid force-regression scale")
    mu = max(0.0, numerator / denominator)
    return float(mu)
```

Pass only the support interval to this function, not the full trial if that exceeds the observation budget. Validate that `min_normal` is finite and positive and `min_speed` is finite and nonnegative before applying rig-specific thresholds. Flag systematic negative resistance as a possible sign/calibration problem rather than accepting the nonnegative clamp as evidence of zero friction. Temporally correlated samples support the fit but do not provide that many independent repeats for uncertainty estimates.

Check sign convention with a known synthetic or physical direction before using this helper. If the force instrument reports the reaction on the fixture rather than the moving body, transform the sign explicitly.

Compare four methods:

1. One global coefficient fitted from training surfaces.
2. A per-surface Coulomb fit from the permitted brief support.
3. A modest speed-dependent law or learned prior using the same support budget.
4. Richer per-surface calibration using many contacts, disclosed as a higher-data reference.

An initial speed-dependent extension can use `mu(v) = max(0, mu_support + beta * log(abs(v)/v_support))` in the calibrated nonzero-speed range. Fit the shared coefficient `beta` from training surfaces. Do not assume the relation holds outside that range or near zero speed. Add load or history dependence only if the data support identifying it.

The direct support-force fit may already work well. If it wins, use it in the simulator and report the limited benefit of learning. That outcome still answers a useful research question.

**Output:** fitted contact parameters, force predictions, and same-budget mechanical baselines.

**Checkpoint:** a fitted coefficient produces forces with the correct units and direction, and no target/query interval was used to fit a test surface.

## Step 22. Test whether tactile observations add useful mechanical information

Separate two inference interfaces:

| Interface | Permitted support inputs | Claim being tested |
| --- | --- | --- |
| Force-informed | Short measured normal/tangential forces, motion, and optionally tactile signals | Efficient calibration and prediction from measured probing |
| Tactile-informed | Tactile/acceleration support and known commands/conditions; independent support-force labels hidden from inference | Whether tactile evidence can predict contact behavior without direct force calibration at deployment |

Use independent force measurements as training supervision and test ground truth in both cases. If you expose support force to the model, do not call that model tactile-only.

Start with simple regression from support features to effective friction behavior, trained on the mechanical training surfaces. With only 8–12 specimens, a large neural model is unlikely to be well justified. Compare known conditions alone, tactile features plus conditions, and the force-informed fit where applicable.

A public-data encoder trained with another probe or apparatus is an optional transfer experiment. Test it against newly fitted simple features and report the domain change. Do not assume ExSARN or the Cluster encoder transfers unchanged to a different sensor or mounting.

For the small pilot, use grouped leave-one-surface-out evaluation. For each held-out surface, choose hyperparameters using only the remaining surfaces or inner validation groups. Allow only its brief prescribed support during inference. Its query trials remain hidden until scoring.

Primary targets: measured tangential-force error in newtons and dependence on requested speed/load. Aggregate within trial, then condition, then held-out surface; bootstrap surfaces/groups rather than force samples. Keep brief support and richer calibration separate from the reserved query trials in Step 20. For a deployable prescribed-load prediction, use commanded load and commanded motion as inputs. A separate analysis using future measured query normal force can diagnose the conditional force law, but must be labeled as an oracle diagnostic. In a forward simulator, the normal force must instead come from the solver or a justified known-loading setup.

Test parameter ambiguity: refit with different support subsets and inspect whether similar support errors imply divergent held-out predictions. Large variation can indicate insufficient excitation, noise, or an overparameterized law.

**Output:** mechanical comparison tables, input-interface descriptions, and parameter-stability analysis.

**Checkpoint:** you can distinguish inference benefits from additional force information, and every held-out prediction uses an explicitly documented deployment interface.

## Step 23. Validate a simple forward motion model

First validate a very restricted physical situation: a known-mass body coasting under sliding friction on the same counterface and geometry, with no applied tangential force after release. This requires a fixture or free degree of freedom that actually permits the body to respond dynamically.

A servo-controlled scan can validate reaction forces, but matching its commanded position is not a free-motion prediction. Keep this distinction explicit.

The following numerical helper is an exact within-step update for constant Coulomb deceleration in an **unforced coasting** experiment. It is not a general sticking/sliding engine:

```python
import numpy as np

def simulate_coast(v0, mass, mu, normal_load, dt=0.001, steps=1000):
    """Return columns time, position, velocity for unforced planar coasting.

    SI units. Constant known normal load; no tangential applied force.
    Velocity is clamped at the stopping event and remains zero thereafter.
    """
    values = np.array([v0, mass, mu, normal_load, dt], dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Parameters must be finite")
    if mass <= 0 or mu < 0 or normal_load < 0 or dt <= 0:
        raise ValueError("Invalid physical parameter")
    if not isinstance(steps, (int, np.integer)) or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    out = np.zeros((steps + 1, 3), dtype=np.float64)
    v = float(v0)
    x = 0.0
    deceleration = mu * normal_load / mass
    out[0] = [0.0, x, v]
    for i in range(steps):
        if deceleration > 0 and v != 0:
            direction = np.sign(v)
            moving_time = min(dt, abs(v) / deceleration)
            x += v * moving_time - 0.5 * direction * deceleration * moving_time**2
            v = direction * max(0.0, abs(v) - deceleration * dt)
        else:
            x += v * dt
        out[i + 1] = [(i + 1) * dt, x, v]
    return out
```

Verify it before using real parameters. For positive initial speed and nonzero friction:

\[
t_{\mathrm{stop}}=\frac{m v_0}{\mu N},\qquad
d_{\mathrm{stop}}=\frac{m v_0^2}{2\mu N}.
\]

The implementation should match this result, never reverse velocity because of friction, and preserve constant velocity when `mu=0`. Check both signs of initial velocity. These numerical checks validate the implementation, not its realism on textured materials.

For real validation, keep contact geometry and probe/surface pairing consistent with the fitted law, know the moving mass and normal loading, and characterize additional guide drag. Use only initial state and known loading in prediction. Future measured velocity or force cannot be supplied to rescue the rollout.

Use initial speeds and loads inside the calibrated range. The helper's analytical examples are numerical checks, not proposed hardware settings. Inspect the low-speed stopping regime separately; a law fitted during steady sliding may miss real behavior near a stop.

Compare global/default friction, brief-contact calibration, and the richer calibration reference on held-out surfaces. Score velocity error, position error, and stopping distance when the experiment supports that metric. Include measured uncertainty in initial speed, mass, and loading when interpreting errors.

**Output:** numerical simulator verification and, when hardware permits, real held-out motion comparisons.

**Checkpoint:** the contact parameters influence predicted motion and are evaluated against measurements the simulator did not consume as future inputs.

## Step 24. Integrate the validated contact model into an existing engine

After a restricted force/motion validation, use an existing physics engine for known-geometry bodies. Start with native contact parameters rather than combining a custom learned force with an already active friction model.

For a MuJoCo experiment, an explicit contact pair makes the coefficient assignment clear. Example configuration fragment, assuming these geoms exist:

```xml
<contact>
  <pair name="probe_surface" geom1="probe_geom" geom2="surface_geom"
        condim="3" friction="0.5 0.5 0 0 0"/>
</contact>
```

Illustrative coefficient assignment after loading a model:

```python
import mujoco

pair_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_PAIR, "probe_surface")
if pair_id < 0:
    raise ValueError("Expected contact pair is missing")
model.pair_friction[pair_id, :2] = mu_hat
```

Validate signs, normal forces, timestep sensitivity, and energy dissipation with a simple slider before adding a robot. Native parameter semantics and the solver's contact approximation must be understood; an effective fit is specific to the experiment and engine setup.

The coefficient assignment above implements a constant Coulomb parameter. It does not implement the speed-dependent extension from Step 21. Start with the constant law. If a variable law has verified benefits, integrating it requires a separately validated implementation that replaces the relevant native resistance rather than adding a second friction force.

Attach a separate tactile observation module that predicts spectral features from permitted simulated contact conditions. The public model is trained on steady-window spectra and two nominal loads. Its first integration should therefore use compatible steady-contact conditions and feature observations. Do not claim instantaneous transient waveforms or arbitrary continuous-load rendering from that benchmark.

If you later generate waveforms, study phase reconstruction or a generative renderer such as HaptoFlow only after validating spectral/amplitude prediction. Keep renderer quality and mechanical fidelity as separate measurements.

**Output:** an engine scene, parameter-inference interface, contact-force checks, and a clearly scoped tactile observation interface.

**Checkpoint:** changing the inferred friction parameter changes mechanical response, while tactile output is generated by a separately evaluated observation model.

## Step 25. Test usefulness for planning or robot learning

Choose one task after validating force and motion: for example, move a known object to a target while respecting a force limit. Begin with a controller or planner before a large reinforcement-learning experiment.

Compare fixed global/default contact parameters, brief-contact-calibrated parameters, and a learned contact model only if it has demonstrated predictive value.

Hold controller/policy architecture, training budget, action limits, real-data budget, task distribution, and test surfaces constant. Measure task success, position error, force-limit violations, probing time, and adaptation cost.

If testing tactile observation quality, vary that factor separately from dynamics. Otherwise an improved result cannot establish whether it came from better forces, richer observations, or additional training data.

A planning/control result establishes decision-making usefulness. Claims about robot learning or sim-to-real transfer require the corresponding matched training and real evaluation. You can keep these as follow-up milestones rather than delaying the first completed study indefinitely.

**Output:** one matched downstream task evaluation, or an explicit future-work specification.

**Checkpoint:** an improvement has a traceable cause and was measured on held-out surfaces/tasks appropriate to the claim.

## Step 26. Package the research so another person can assess it

Create a top-level `README.md` explaining the question, supported claims, dataset revision, environment, data preparation, experiment configurations, figure regeneration, and limitations. Include the actual package CLI and report commands. The current public repository contains source/configs/tests, documentation and aggregate reports; downloaded raw data, feature caches, checkpoints and full per-query outputs are ignored by Git. Public aggregates alone are not the complete reproducibility package. Before scientific release, choose an allowed artifact distribution or verified reconstruction recipe, preserving data revision, environment, manifests, hashes and all outputs needed to reproduce principal tables. Historical report hashes refer to their recorded source commits, not necessarily the current checkout.

The research record should contain:

- Protocol and related-work comparison.
- Data/QC manifests, specimen groups, split files, and window/episode definitions.
- Training-only fitted preprocessing and baseline parameters.
- Model checkpoints and configuration hashes.
- Per-query and per-surface numerical results.
- Figures generated from those results.
- Report and appendix.
- A contribution statement identifying your work, guidance, reused code, and verified results.

Keep a weekly log: question, attempted experiment, reason, outcome, interpretation, and next decision. Record failed approaches when they clarify a methodological choice. Distinguish exploratory tuning from locked evaluation.

For a PhD application, describe completed evidence accurately. Example structure:

> I investigated whether brief sliding contacts support prediction on held-out surfaces. I designed matched-budget probe comparisons, implemented retrieval and physical-rescaling baselines, and evaluated response prediction across interaction conditions. The study found [verified result], which motivated [specific next experiment].

Fill brackets only with actual results. Label an unpublished report as a technical report or preprint, a submitted paper as submitted, and acceptance only after acceptance. A short conversation with a researcher does not establish supervision or a recommendation commitment.

The credible evidence is your scientific question, experimental ownership, validation, and interpretation. Publication suitability depends on novelty and results; admissions outcomes also depend on the rest of the application.

**Output:** a complete, reviewable research package and an accurate completed-work description.

**Checkpoint:** someone can reproduce the principal tables and understand your contribution without reading this conversation.

## Recommended execution order from the current milestone

| Next gate | Concrete action | Exit evidence |
| --- | --- | --- |
| Completed 9 October: strict acceleration boundary | Raw-window-first preparation, outside-sample tests/audit, every method rerun in new roots | 53 passing tests, 688 invariant real windows, [aligned before/after report](window_boundary_report.md) |
| Completed 9 October: logged-coordinate and QC scope | Original/mirror evidence, motion/heading/load and seven-setting sensitivity | [Clock/QC decision](clock_qc_review.md); physical timing remains uncalibrated |
| Completed 9 October: exposure, reservation and wider training coverage | Complete metadata groups/domain masks; protected twenty-specimen reservation; 960-record training audit | [Design](study_design_review.md) and [coverage](wider_coverage_review.md); all required supports and 44 query triples survive |
| Completed 9 October: training repeat/feature/history review | 480 repeat pairs, floor/range sensitivity and nine saved histories | [Diagnostics](development_diagnostics_review.md); keep current features/QC and all specimens; 78 passing tests; convergence unresolved |
| Next: controlled convergence | Fresh unchanged bounded cohorts/seeds, finite 120-epoch cap, original selection domains, unchanged patience, primary/equal-cell logging | First-60 reproduction, best-by-60/120 checkpoints and actual stop reasons; no repeated cap chase |
| Then: remaining diagnostics and matched development | Repetition reversal, residuals, wider selection/transfer coverage and integrated 70/44 fitting with common known-speed selection /26 scoring | Aligned model/probe comparisons and documented practical-effect rationale |
| Fresh-test freeze | Protect existing reserved groups, implement frozen scoring, set primary margin/secondary policy and planned robustness | Versioned freeze bundle and test-interface checks |
| Complete Stage A | Score frozen models, run declared checks, produce failure figures and scoped report | Honest completed study and reproducible release |
| Parallel: Stage B access | Prepare capability inquiry and verify actual available measurements | Calibrated independent force/motion gate; outreach only when authorized |
| Later stages | Measured mechanics, responsive motion validation, engine integration, matched control | The distinct gates in Steps 18–25 |

These are dependency gates, not a restart of completed download/training work or a calendar promise. Clock uncertainty can limit a completed empirical report; it cannot be erased by a sensitivity curve. Hardware delays need not keep Stage A indefinitely unfinished.

## Stage A experiment matrix and conditional extensions

| Experiment | Required methods | Required outcome |
| --- | --- | --- |
| New surfaces, familiar conditions | Conditions-only, copy, retrieval, fixed-feature regression, encoder, direction-agnostic rescaling; same-direction diagnostic for all | Per-surface spectral/amplitude errors |
| Probe duration | Same methods at 0.25/0.5/1 s on matched cohort | Error versus observed time |
| One versus two probes at equal total time | Single 1 s versus two 0.5 s; single 0.5 s versus two 0.25 s | Benefit of probe diversity beyond additional observation time |
| Second-probe choice | Repetition/speed/load/direction, fixed 0.5-second contact duration for the main contrast; other durations secondary | Same-budget comparison; count time and distance |
| Wrong-support control | Proposed predictor with correct and substituted support | Evidence of surface-specific conditioning |
| Globally omitted speeds | Refit all relevant methods with 20/40/60 only; add matched-grid familiar comparator | 44 known-speed /26 endpoint-safe transfer triples before QC; current development covers 6/4 |
| Mechanical pilot, when feasible | Global coefficient, brief-force fit, modest extension, richer calibration | Held-out force error and parameter stability |
| Restricted real dynamics, when feasible | Global, brief-contact, richer calibration | Motion error without future-state inputs |

The development slice and bounded expanded/omitted matrix have now been rerun with verified raw-window preparation. Keep historical versions visible and preserve current dependency guards. Logged-coordinate scope, complete metadata/reservation, wider known-speed training QC and training repeat/floor/range diagnostics are recorded. Controlled convergence, repetition reversal, wider selection/transfer coverage, matched fitting and a fresh locked test remain gates. Category exclusion and globally omitted directions are optional exploratory stress tests. Adaptive next-probe selection, waveform synthesis, compliance, and sensor transfer need separately scoped experiments after the planned study is complete.

## Troubleshooting guide

| Symptom | Check first | Avoid concluding prematurely |
| --- | --- | --- |
| All test errors are exceptionally small | Material splits, same-record overlap, query labels, retrieval omitted-speed access | Universal material representation |
| All amplitude errors are large | g-to-SI conversion, per-record normalization, PSD density integration, log inversion | Insufficient network size |
| Frequency shifts look wrong | Sampling/time base, speed units, interpolation scaling factor | Material physics is unpredictable |
| More contact always helps enormously | Outside-window preprocessing context, hidden query observations, unmatched time/nominal distance, cohort changes | A special information-theoretic benefit |
| Wrong surface performs equally well | Support ignored, query-condition dominance, machine signal | Surface identification |
| Force model fits support but fails elsewhere | Confirmed sliding, load control, calibration drift, parameter ambiguity | Intrinsic friction has been recovered |
| Simulation matches a scan exactly | Whether measured future motion was replayed | Forward dynamics accuracy |
| Controller improves with new model | Data/training budget and observation/dynamics changes | Sim-to-real or robot-learning improvement |

## References and official implementation resources

- **[R1] Heravi et al. Learning an Action-Conditional Model for Haptic Texture Generation. ICRA 2020.** [Paper](https://arxiv.org/abs/1909.13025).
- **[R2] Heravi et al. Development and Evaluation of a Learning-based Model for Real-time Haptic Texture Rendering. IEEE Transactions on Haptics, 2024.** [Paper](https://arxiv.org/abs/2212.13332).
- **[R3] Eguchi et al. Cluster Haptic Texture Dataset: Haptic Texture Dataset with Varied Velocity–Direction Sliding Contacts. Scientific Data 13, 756 (2026).** [Published article](https://www.nature.com/articles/s41597-026-06760-z), [author manuscript](https://arxiv.org/html/2407.16206v4), [data mirror and schema](https://huggingface.co/datasets/tamago117/cluster-haptic-texture-dataset), [author code](https://github.com/cluster-lab/Cluster-Haptic-Texture-Dataset), [collection/file documentation](https://github.com/cluster-lab/Cluster-Haptic-Texture-Dataset/blob/main/documents/dataset_details.md).
- **[R4] Gao et al. On Explainability and Sensor-Adaptability of a Robot Tactile Texture Representation Using a Two-Stage Recurrent Networks. IROS 2021 — ExSARN.** [Final publication](https://ieeexplore.ieee.org/document/9636380), [author code/data](https://github.com/dexrob/ExSARN).
- **[R5] Eguchi et al. HaptoFlow: High-Fidelity Real-Time Vibrotactile Generation via Flow Matching for Virtual Reality. 2026 arXiv manuscript; arXiv reports acceptance to IEEE ISMAR 2026.** [Paper](https://arxiv.org/abs/2608.01974).
- **[R6] Si et al. DiffTactile: A Physics-based Differentiable Tactile Simulator for Contact-rich Robotic Manipulation. ICLR 2024.** [Paper](https://arxiv.org/abs/2403.08716), [project](https://difftactile.github.io/), [code](https://github.com/Genesis-Embodied-AI/DiffTactile).
- **[R7] TacTID: High-Performance Visuo-Tactile Sensor-Based Terrain Identification for Legged Robots. IEEE Sensors Journal, 2024.** [Author-hosted paper](https://charon-bo.github.io/assets/PDF/TacTID.pdf).
- **[R8] Gao et al. Tactile DreamFusion: Exploiting Tactile Sensing for 3D Generation. NeurIPS 2024.** [Paper](https://arxiv.org/abs/2412.06785). Useful for a later 3D texture-generation direction, rather than a dependency of this first benchmark.
- **SciPy polyphase resampling and boundary behavior.** [Version 1.15.1 documentation](https://docs.scipy.org/doc/scipy-1.15.1/reference/generated/scipy.signal.resample_poly.html). Relevant to the strict-window correction; the repository uses Python HTTPS rather than the Hugging Face Hub client.
- **SciPy Welch estimation.** [Official documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html).
- **PyTorch installation.** [Official selector](https://pytorch.org/get-started/locally/).
- **MuJoCo contact model.** [Official computation documentation](https://mujoco.readthedocs.io/en/stable/computation/index.html), [XML contact-pair reference](https://mujoco.readthedocs.io/en/stable/XMLreference.html#contact-pair).
- **CMU research-statement guidance.** [Jonathan Aldrich's faculty guidance](https://www.cs.cmu.edu/~aldrich/essay-advice.html).

## Refinement and validation record

The initial 8 October refinement checked source acquisition/schema statements, prior retrieval work, illustrative numerical/model/mechanics behavior, the 76-condition grid and 26 guide steps. Those syntax/synthetic checks were guide verification, not research findings. The implemented repository subsequently completed the initial, expanded and omitted-speed development runs; the 8 October source-code suite passed 44 tests and compilation. Actual historical runtimes/results are recorded in [implementation checks](implementation_checks.md) and the three milestone reports.

The maintained guide uses executed CLI/module contracts, the fixed 0.5-second query specification, nominal-distance terminology and exact 76/44/26 domains. Raw boundaries, logged-coordinate scope, metadata/reservation, known-speed training coverage and repeat/floor/range/history diagnostics are complete. Controlled convergence, repetition reversal, wider selection/transfer coverage, matched fitting, practical/secondary policies and locked scientific scoring remain pending. Negative/inconclusive comparisons are preserved. Mechanical/calibration stages remain future work and do not depend on a learned-model victory.

The 8 October inspection identified whole-record interpolation/filtering dependence. On 9 October, raw-window-first processing and dependency metadata were implemented, nine targeted tests passed within a 53-test suite, and all three development pipelines were refitted in separate roots. The real audit verifies 688 invariant windows and unchanged raw intervals/episode inputs. Local preparation changes are measured in the boundary report; historical run provenance remains preserved. Clock calibration, fresh-test evaluation and mechanics remain uncompleted. Documentation structure, CLI references, local links and example syntax are checked before publication.

The 10 October documentation revision promotes corrected scores to the current-result tables, separates completed diagnostics from pending experiments, clarifies each convergence run's original selection domain, and retains current features/QC and difficult specimens. It adds no fits or response exposures. Updated portable plan/guide copies are saved separately from the original supplied documents and earlier revisions.
