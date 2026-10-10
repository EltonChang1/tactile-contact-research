# Brief Contact Probes for Predicting Texture and Sliding Contact

Prepared for Elton Chang — original plan 7 October 2026; revised after implementation review 8 October and boundary/clock/QC review 9 October 2026, America/Los_Angeles

**Status:** A public [development repository](https://github.com/EltonChang1/tactile-contact-research) and three bounded real-data experiments are complete. These establish implementation behavior and provisional comparisons. No locked scientific test, calibrated mechanical identification, real motion validation, or control experiment has been completed. Hardware access, novelty, and publication acceptance remain unestablished. This revision separates observed evidence from proposed work and preserves the original long-term objective.

## 1. Objective and research scope

Long-term objective: develop contact models and tactile observation models that improve physics simulation and robot learning.

First scientific question: **How much brief contact data is needed to predict a previously unseen surface's response under other motions and loads, and which additional probe provides useful information?**

The initial public-data study predicts vibration spectra. The mechanical extension predicts sliding forces and identifies friction behavior for a fixed probe–surface contact. These are separate milestones with separate evidence requirements.

The main candidate contribution is a careful study of contact information, generalization, and probe selection. An encoder and decoder alone are not the contribution. Any claim of novelty requires checking the closest prior work and obtaining expert feedback.

The first mechanical scope is **sliding friction with a fixed contact geometry**. Add compliance after measuring indentation and calibrating fixture and probe deformation. A complete engine, full-body touch, universal material properties, and large world-model training are longer-term objectives.

The immediate deliverable is a defensible study of information in brief contacts, including a result in which retrieval or fixed-feature regression wins. Keep the primary method comparison as encoder versus retrieval with one 0.5-second support, and the primary probe comparison as direction versus repetition with two 0.5-second contacts. Duration labels refer to logged-time extent under the declared [logged-coordinate convention](../configs/clock_convention.json); physical duration and frequency remain uncalibrated. Do not redefine the primary cell around a favorable development result.

## 2. Why the previous idea needs refinement

Vibration prediction establishes a tactile observation model. A physical simulator also requires a force law that changes the simulated state. Matching tactile spectra cannot independently establish accurate friction, stiffness, slip onset, or object motion.

Existing work already connects tactile observations and actions to texture vibrations. Heravi et al. use GelSight observations and interaction conditions in action-conditioned generation; their later system handles unseen textures through a nearest-neighbor representation. DiffTactile already identifies sensor and contact parameters using measured interactions. TacTID estimates friction and effective stiffness. [1–4]

This makes the following questions more defensible:

- Does one brief moving contact contain enough information for a particular prediction target?
- At the same observation budget, is an extra direction, load, or speed more useful than repeating the same contact?
- How much of the apparent generalization can simple retrieval or speed rescaling explain?
- When measured force data become available, does inferred contact behavior improve force predictions and eventually motion rollouts?

Both positive and negative results are useful when they answer these questions convincingly. A failure to outperform a strong baseline should change the claim rather than trigger an arbitrary search for a larger network.

## 3. The intended simulation architecture

Keep three interfaces explicit:

1. **Inference:** observed probe contacts and their conditions produce a contact representation and, where supported by measurements, effective contact parameters.
2. **Dynamics:** a physical solver uses contact parameters, current state, and actions to compute forces and update motion.
3. **Observation:** a sensor model uses the simulated contact state to predict tactile readings or texture spectra.

Conceptually:

\[
z,\hat\theta = E(D_{\mathrm{probe}}),\qquad
s_{t+1}=F_{\mathrm{solver}}(s_t,a_t;\hat\theta),\qquad
\hat o_{t+1}=G(s_{t+1},z,\hat\theta).
\]

The public study initially establishes part of E and G. Measured sliding-force experiments establish a restricted part of the parameter inference and force law. The project does not assume that an acceleration encoder will transfer unchanged to an optical or magnetic tactile sensor.

Contact parameters describe a specified probe, surface, mounting, and operating range. Sensor deformation, object deformation, contact geometry, and loading can be confounded. Hold these factors fixed initially and expand the claim only after appropriate calibration and experiments.

## 4. Stage A: public-data study

### 4.0 Current evidence and remaining scientific gates

The development implementation includes pinned downloads and hashes, recording/QC manifests, spectral features, matched episodes, five baselines, a small encoder/predictor, wrong-support controls, three initialization seeds, and result provenance. The initial single-probe pilot is retained in [development_status.md](development_status.md). Subsequent experiments are summarized below; episode counts do not represent independent specimens.

| Development experiment | Coverage | Observed primary-cell behavior | Interpretation |
| --- | --- | --- | --- |
| [Expanded familiar-condition pilot](expanded_pilot_report.md) | Ten training/two validation specimens; five protocols; three durations; four common query triples; 1,320 episodes | Single 0.5-second log-power MAE: retrieval 0.1724, fixed features 0.2006, encoder 0.2492; wrong support 0.5837 | Retrieval leads; the encoder uses specimen-dependent information within this development cohort. No learned-model advantage or preferred probe is established. |
| [Separately fitted omitted-speed experiment](omitted_speed_report.md) | Same twelve specimens; fit/select on 20/40/60 mm/s; score 30/50 mm/s; two query directions/one load; 2,100 episodes | Transfer MAE: fixed features 0.3098, encoder 0.3158, interpolated retrieval 0.3298; wrong support 0.4975. Retrieval has lower transfer RMS error than the encoder. | Different metrics favor different methods. The paired retrieval-minus-encoder MAE difference is 0.0140 with a two-group diagnostic interval spanning zero. This remains exploratory development evidence. |

The two experiments use different query grids and cannot isolate the effect of speed withholding by comparing their scores. Add a familiar-condition comparator on the identical grid, support/query definitions, specimens, and budgets before attributing a change to omitted-speed training.

The review identified three limits. The acceleration-boundary correction and bounded clock investigation are complete; physical timing and scientific evaluation remain unresolved:

1. **Strict acceleration information budget, corrected 9 October:** raw samples are now cropped before interpolation/filtering, with locally derived padding and rate estimates. Nine new checks pass in a 53-test suite; all 688 real windows are invariant to outside-acceleration perturbations. All methods/seeds were refitted in separate roots with matched raw intervals and episode inputs. Median mean log-feature changes are approximately 0.0038–0.0039 and include local-rate/edge effects. The [boundary report](window_boundary_report.md) preserves before/after results: retrieval still leads the expanded familiar pilot, and fixed features still lead omitted-speed MAE. This closes the acceleration-input boundary with retrospective QC held fixed, not physical clock or causal onset validation.
2. **Clock interpretation, scoped 9 October:** fifteen original CSVs match the mirror exactly after nanosecond rounding and float32 conversion. Their original acceleration/force rows still average roughly 8.6 kHz against documented roughly 6 kHz acquisition/transmission. Acquisition timing remains unverified. Use `logged_coordinates_v1` for the limited observational study: logged-time windows and inverse-logged-time frequency coordinates, without calibrated physical-duration/frequency claims. A training-only 200-record contact review reports heading, force, travel and smoothing/gap sensitivity; it changes no QC/model setting. See the [clock/QC decision](clock_qc_review.md) and preserved [timing sensitivity](timing_audit.md).
3. **Scope and exposure:** all twelve current specimens are development-exposed. The complete 118-specimen review has scope `metadata_names_only`; fabrication-family independence is unknown. Twenty metadata-only specimens in fifteen groups are reserved before wider signal review, with scientific freeze/scoring still pending. No full-grid model comparison or fresh scientific test has run.

Retain the verified budget guards and declared logged-coordinate scope; complete wider coverage, exposure, repeatability and feature/convergence review before locking scientific evaluation. A negative result against strong baselines can complete Stage A; a functioning pipeline alone cannot.

### 4.1 Dataset and access

Use the Cluster Haptic Texture Dataset. It offers 118 surfaces, five speeds (20–60 mm/s), eight scan directions, two nominal loads (0.5 and 1 N), and two repetitions. Sliding recordings include acceleration, normal force, and in-plane position. [5]

- [Author paper](https://arxiv.org/html/2407.16206v4)
- [Convenient Parquet mirror](https://huggingface.co/datasets/tamago117/cluster-haptic-texture-dataset)
- [Author repository](https://github.com/cluster-lab/Cluster-Haptic-Texture-Dataset)
- [Collection and file documentation](https://github.com/cluster-lab/Cluster-Haptic-Texture-Dataset/blob/main/documents/dataset_details.md)

Begin with acceleration, force, position, and material metadata. Images and audio are optional follow-up modalities, not dependencies for the first result.

The normal-load setting is obtained by selecting a contact height; it should not be treated as perfect continuous force control. Friction metadata were measured separately under a different protocol. Those coefficients are not synchronized tangential-force trajectories for each scan. The dataset also lacks the indentation data required for this project's compliance identification. Force transmission is 6 kHz, while the force acquisition updates at 80 Hz. [5]

### 4.2 Data audit before training

Create an inventory with material ID, category, specimen/family notes, speed, direction, nominal load, repeat ID, duration, sampling intervals, and missing or unusable channels.

The original ten-surface audit and two-specimen development validation are complete for bounded selections. Expand synchronized acceleration/force/position review and condition coverage using development specimens. Check steady sliding, actual loading variation, timestamps, clipping, differences between repetitions, and specimen-level failures. Record exclusions using a rule defined without looking at scientific test errors.

Determine the number of usable windows per condition after removing approach, acceleration, and stopping phases. Keep track of observations that cannot provide a full requested duration. Do not silently shorten long probes or fabricate extra independent trials.

Document possible machine vibration and sensor resonances. Wrong-material and action-only controls help detect whether performance is dominated by the apparatus, but a single apparatus cannot establish sensor transfer.

The current longest steady interval is selected retrospectively using motion and force over a recording. This is an offline benchmark selection rule, not an online detector that knows when a usable probe has begun. Keep query force confined to offline QC and hidden from prediction inputs. Audit how QC changes coverage by specimen, speed, direction, load, and duration; publish the intended and retained denominators rather than reporting only successful windows.

The acceleration-budget correction now selects each raw support/query interval before local interpolation, anti-aliasing and spectra. Manifests record allowed/dependency indices, local timestamps/grid/padding, zero extra observed context and output counts. Targeted perturbation checks plus the 688-window measured audit hold starts/QC fixed and confirm unchanged processed inputs; prediction-input guards then keep query labels separate. All caches, scalers, libraries, baselines and model seeds were rebuilt in isolated roots. Retain this convention and the historical results. A future causal variant must explicitly charge its observed history and detection/initialization overhead.

The bounded acquisition/delivery investigation now adopts [logged_coordinates_v1](../configs/clock_convention.json) without using predictor errors. Original-CSV agreement establishes preservation on five training records; available documentation does not calibrate acquisition timestamps. Continue a limited report on logged-coordinate windows and spectra with assumptions and sensitivity disclosed. Absolute physical frequency and physical contact-time labels remain uncalibrated. New authoritative transport/acquisition evidence requires a versioned decision and fresh matched preparation/comparisons; preserve the present results. This scope supports a limited observational study rather than proving the original physical-duration question.

The [200-training-record QC review](clock_qc_review.md) retains all 0.5-second intervals and 199/200 one-second intervals at current settings. Eleven-point smoothing retains only 166 and 57 respectively; 31 points retain all, without proving higher accuracy. Tighter/doubled gap limits leave this bounded selection unchanged. Logged headings agree under a single global frame; median time-weighted force is 1.04865 times nominal. Keep settings and nominal input labels, disclose deviations, and audit wider intended/retained denominators before freezing scientific QC. Do not turn diagnostic heading/load results into post-hoc exclusions or predictor inputs.

The [wider known-speed training audit](wider_coverage_review.md) now covers all 48 permitted-speed conditions on ten training specimens, both repeats: 960 requested records, all valid for half a second and 932 for one second. Every required one-second support survives, and all 44 known-speed query triples have both half-second repetitions across all ten specimens (440 candidate cells). Keep current settings. Median force/nominal ratio is 1.02909 over the broader grid. Reserved, validation and training omitted-speed records are excluded from this new audit; their future coverage remains to be verified under the appropriate access rules.

### 4.3 Split and test protocol

Use approximately 80 training, 18 validation, and 20 test specimens as a planning target, adjusted after conservative grouping and prespecified coverage/QC rules. These are not locked counts. Balance category coverage where feasible; keep known related variants together rather than splitting them to meet exact numbers. Review the complete metadata list, record unknown fabrication relationships, and distinguish name-based grouping from verified manufacturing-family independence. If additional provenance is unavailable, retain an explicitly specimen-level claim rather than indefinitely requiring proof of unknown families.

All twelve current specimens are development-exposed: training IDs 0, 38, 49, 65, 74, 79, 82, 87, 102, 103; development validation IDs 10 and 57. None may become a fresh scientific test. IDs 10 and 57 have repeatedly supported model selection and exploratory evaluation even though their records did not fit model weights. The [complete metadata/exposure review](study_design_review.md) now records all 118 specimens in 87 conservative name/uncertainty groups. Direct exposure propagates to 22 specimens blocked from fresh test groups. Manufacturing relationships remain unknown.

Twenty metadata-only specimens in fifteen complete groups are [reserved](../configs/test_reservation.csv) before wider signal review, using a fixed seed and category quotas without response/QC/score selection. Keep the reservation protected while final coverage, grouping scope, features, comparisons and practical margins are reviewed. The [exposure ledger](specimen_exposure_ledger.csv) distinguishes metadata from direct/group response exposure; a reservation is not yet a locked scientific evaluation. Only obsidian remains fresh in the Glass category, limiting future category claims.

All recordings from a held-out surface remain outside model training and preprocessing-statistic fitting. Material IDs are used to pair records and construct splits, never as encoder or predictor inputs. Split records before creating windows.

Publish the fixed split manifest and evaluation configuration. Use development/training/validation specimens for architecture, feature, and stopping decisions. Freeze timing, budget handling, groups, exclusions, features, methods, margins, and analyses before scientific test scoring. Use three model initialization seeds; additional group splits are a predeclared robustness check, not an opportunity to choose the best result. The existing CLI enforces development runs; locked-test creation, access control, and scoring still require implementation and review. A configuration labeled test is not sufficient evidence of an untouched evaluation.

A test surface is observed through a limited support set at evaluation time. This is adaptation from brief contact, not prediction with zero observations. The query recordings remain hidden until scoring. Model weights stay frozen unless a separately labeled adaptation baseline specifies otherwise.

### 4.4 Probe conditions and budgets

The implemented reference contact is 40 mm/s, direction 0 degrees, nominal load 0.5 N. Compare observed durations of 0.25, 0.5, and 1 second after the strict information-budget and timing/claim decisions. Keep the query target duration fixed at 0.5 seconds so that support-duration comparisons change observation information rather than target-estimation duration. The current five protocols and three durations have run on a bounded grid; full-grid coverage remains proposed.

Then compare these two-probe protocols, using the same duration per contact:

| Protocol | Second probe | Question |
| --- | --- | --- |
| Repetition | Same condition, other recorded repetition | Does averaging repeated contact explain the gain? |
| Speed | 20 mm/s, 0 degrees, 0.5 N | Does varying speed improve prediction? |
| Load | 40 mm/s, 0 degrees, 1 N | Does observing another load reduce loading uncertainty? |
| Direction | 40 mm/s, 90 degrees, 0.5 N | Does an orthogonal contact reveal directional behavior? |

Compare second-probe alternatives at the same total observation duration and number of contacts. Retain the primary direction-versus-repetition contrast at two 0.5-second contacts; report speed/load contrasts as declared secondary analyses. Also compare a single 1-second contact with two 0.5-second contacts, and a single 0.5-second contact with two 0.25-second contacts. Report total selected observation time and nominal distance (requested speed multiplied by duration) separately. Nominal distance is not measured travel; calculate measured displacement from synchronized position if that quantity is reported. These budgets exclude approach, stabilization, and repositioning.

Select nested raw prefixes from one canonical steady interval per recording. Raw-prefix nesting does not require a shorter independently filtered array to equal the prefix of a longer filtered array: valid boundary treatments can differ. Verify nesting from raw sample provenance and verify the absence of outside-budget influence separately. Do not use full-record filtering merely to make processed arrays nest exactly.

Score all protocols on a common query set that excludes the union of support conditions. This prevents a protocol from receiving credit for having directly observed its evaluation condition. A condition's other repetition should not serve as a query for that same observed condition in the primary cross-condition result.

The intended familiar-condition grid has 80 speed/direction/load triples minus the four support-condition triples: **76 queries before QC**. Use a cohort and query intersection matched across methods, protocols, and durations; report lost conditions and specimens with reasons. The four-query development pilot does not establish behavior over this full grid.

Use a fixed support repetition and the other repetition for query evaluation where possible, then reverse the assignment as a sensitivity check. Both repetitions may be used as support for the repetition-control protocol, so queries for that protocol must come from other conditions. The dataset contains only two repetitions; do not invent a three-repeat control.

### 4.5 Features and prediction targets

Begin with three-axis acceleration, preserving amplitude in consistent units. Remove the constant offset and extract spectra from steady contact. If resampling is necessary, check timestamps and use appropriate filtering. Compute summary statistics only from training data.

Use Welch power spectral density estimates and integrated power in fixed frequency bands. A workable starting configuration is 32 bands over a validated acceleration frequency range, per axis, with a log transform and a documented numerical floor. Choose the band range and window settings from the audit; exclude empty or unreliable bins. Keep the spectral-estimation procedure consistent across durations.

The implemented encoder receives observed spectral features, observed contact conditions, duration, and probe mask/count. The predictor receives the inferred representation and the **requested speed, direction, and nominal load** for the query. Measured normal force is currently used only for offline QC. A support-force variant is optional future work: declare it separately, give every comparator the same permitted information, and retain a tactile-only comparison if tactile-only inference is claimed.

Never use query acceleration, query material identity, or future measured query force as deployable prediction inputs. Any optional future-force-conditioned analysis must be labeled as an oracle diagnostic and reported separately.

The primary target is log spectral band power. A secondary target is vibration amplitude, computed from consistently band-limited data. This avoids requiring an exact phase-aligned waveform from a short contact on a heterogeneous surface.

Current development features use 32 linear bands from 24–1000 Hz on each of three axes, 0.125-second Welch segments with 50% overlap, SI acceleration, and `log10(power + 1e-10)`. The floor is numerical, not a calibrated sensor noise floor. Confirm bin integration, repeat variability, above-floor coverage, and floor sensitivity on development/training data before freezing the scientific features. Absolute frequency labels remain conditional on the clock decision.

### 4.6 Models and baselines

Start with a small MLP encoder and predictor; a 16-dimensional representation is a reasonable initial choice. Train from same-surface support/query pairs with balanced sampling across surfaces and conditions. Use prediction loss rather than requiring material classification as the main objective.

| Method/control | What it tests |
| --- | --- |
| Conditions-only predictor | How much can motion and loading alone explain? |
| Copy support spectrum | Does prediction improve beyond reusing an observation? |
| Speed-rescaled support spectrum, with amplitude scaling fitted on training data | Can a simple motion transformation explain the result? |
| Nearest training-surface retrieval, using the same allowed support features | Is continuous representation learning needed beyond retrieval? |
| Fixed feature vector plus condition-dependent regression | Is a learned bottleneck better than ordinary measured features? |
| Proposed encoder plus predictor | Does learned representation improve held-out response prediction? |
| Wrong-surface support substitution | Does the predictor actually use surface-specific evidence? |

Use the same observable inputs and observation budgets for compared methods. Heravi-style models are related work; changing their sensor modality or training protocol creates an adapted baseline, not an exact reproduction of published results.

All listed comparators are implemented for the bounded development runs. Fixed-feature regression and speed/load rescaling select declared regularization candidates on permitted validation conditions; their scalers, coefficients, exponents, and retrieval response libraries fit only training data. Rescaling exponents are empirical predictive approximations, not identified material laws. The omitted-speed retrieval baseline uses permitted same-direction/load endpoint responses, rather than hidden omitted-speed labels.

Before any architecture expansion, inspect per-condition/per-specimen residuals, feature conditioning, repeat disagreement, retrieval identity stability across budgets, and optimization histories. Several latest encoder checkpoints lie near the 60-epoch development limit; inspect convergence under a declared development-only training policy before locking it. Preserve failed approaches and all required baseline comparisons. The current results do not justify replacing strong simple methods with a larger preferred model.

### 4.7 Generalization experiments

Separate the following claims rather than averaging them into one score:

1. **New surfaces, familiar conditions:** training includes the condition grid but not test surfaces.
2. **New surfaces and speed interpolation:** separately refit every relevant method using only 20, 40, and 60 mm/s for fitting and validation selection; score 30 and 50 mm/s after all choices are frozen. Omitted speeds are not support conditions. The bounded development experiment already implements these partitions and retrieval endpoint provenance; scientific expansion remains proposed.
3. **Load transfer:** a one-load support contact predicts the other available nominal load. A two-load support protocol answers a different question: the value of observing both loads.
4. **Direction transfer:** evaluate held-out directions relative to the support set; optionally add a separate model with globally omitted directions.

Category exclusion is an exploratory stress test. Holding out a specimen does not establish transfer to an entirely new material family. Two load levels do not establish arbitrary-load extrapolation. A single probe and apparatus do not establish sensor-independent material properties.

For the intended full-grid omitted-speed design, the permitted-speed response grid has 48 triples minus the same four support triples: **44 fit/selection queries before QC**. The two omitted speeds provide 32 potential transfer triples. Under the current same-direction/load interpolation contract, necessary endpoints are excluded at 0 degrees/0.5 N, 0 degrees/1 N, and 90 degrees/0.5 N. Their six omitted-speed triples are therefore outside the matched retrieval domain, leaving **26 endpoint-safe transfer triples before QC**. Publish these denominators and condition lists before scoring; do not silently admit observed support-condition responses into the retrieval library. Other transfer domains require a separately declared prediction rule and aligned comparators.

Fit a familiar-condition comparator on the identical transfer grid and specimen/budget definitions before attributing a change to withholding speeds. Keep omitted-speed models, features, tuning, and outputs separately versioned. Familiar-condition selection scores and transfer scores answer different questions and must not be pooled.

### 4.8 Metrics, uncertainty, and interpretation

Primary metric: mean absolute error of predicted log band power, averaged over query conditions within each surface and then over surfaces. Use a fixed log floor and report its sensitivity when relevant.

Secondary metrics: amplitude error, per-axis spectral error, category-level error, and error as a function of probe duration and second-probe type.

Report paired differences between methods on the same held-out surfaces, confidence intervals obtained by resampling surfaces or specimen groups, and variation across initialization seeds. Thousands of windows are not thousands of independent materials. Compare errors with differences between the two repeated recordings as context, while acknowledging that two repeats provide a limited estimate of variability.

Current intervals based on two development validation groups are engineering diagnostics, not scientific uncertainty estimates. Average seeds within each specimen for the primary paired comparison; preserve seed variation separately. Complete repeatability, support/query repetition reversal, convergence, and numerical-floor checks before choosing a practical effect margin. Keep every required method and declared cell in the final tables.

If uncertainty is added, evaluate interval coverage and width on held-out surfaces. Ensemble disagreement alone is not evidence of calibrated uncertainty.

Predeclare interpretation rules:

- If wrong-surface support does not worsen predictions, do not claim useful surface conditioning. If it does worsen predictions, this supports dependence on specimen-specific observations within the tested cohort, not intrinsic material identification.
- If retrieval is competitive or uncertainty does not resolve an advantage, report that a continuous learned representation has not demonstrated an advantage. A nonsignificant difference does not establish equivalence.
- If a second direction improves prediction more than repeated contact at the same verified budget, this supports direction-specific predictive information under the tested apparatus. It does not independently establish intrinsic anisotropy or an adaptive probe-selection policy.
- If speed transfer works while load transfer fails, investigate loading variation and whether the support data constrain load dependence.
- If all methods fail, inspect repeat variability, apparatus signals, and observability before expanding network size.

Do not select a desired percentage improvement in advance and call it a scientific success criterion. Choose a practically meaningful effect after auditing signal scales and repeat variability, before opening the test results.

Declare whether secondary comparisons are descriptive or use a specified multiplicity procedure. Isolated unadjusted intervals over many protocols, durations, metrics, and subsets cannot establish every apparent benefit. A complete negative or inconclusive comparison with sound budgets and a bounded claim is a valid study outcome.

## 5. Stage B: measured contact mechanics

### 5.1 First target and hardware dependency

First mechanical target: **sliding tangential force under different normal loads and speeds for a fixed probe–surface pair**.

Required capabilities: independently calibrated normal and tangential force measurements, controlled relative motion, known probe geometry, synchronized position and velocity, and a repeatable tactile or acceleration measurement. A calibrated linear stage and fixture can be sufficient; a dexterous hand is not a requirement.

Hardware access is unconfirmed. Seek a mentor or existing rig while completing Stage A. Reuse an existing dataset only after checking that it exposes the required forces, motion, independent records, and surface variation. A paper describing collection does not guarantee those recordings are downloadable. DiffTactile's code is available, but access and adequacy of its real system-identification recordings must be checked. Its paper's two real surfaces would not alone support a broad unseen-material benchmark. [3]

The mechanical gate is suitable calibrated measurements and a declared force experiment, not an encoder victory in Stage A. A completed observation-model result favoring retrieval can coexist with a justified mechanical pilot. Prepare a capability checklist and any outreach draft in parallel; sending messages requires separate user authorization. No mechanical data collection or hardware calibration is established by the existing repository.

### 5.2 Calibration and collection

Begin with known geometry and rigid flat surfaces to reduce deformation confounds. Keep probe construction and mounting fixed. Calibrate force axes, zero offsets, cross-axis sensitivity, sensor delay, fixture drag, and probe/fixture deformation as needed. Record reference contacts before and after sessions.

A pilot design is 8–12 distinct surface specimens, three usable speeds, three normal-load levels, and at least five independent repetitions per condition, collected across more than one session where feasible. Exact ranges depend on sensor resolution and rig capabilities. This is a small pilot, not a universal material study. Distinct specimens and groups—not windows—determine the strength of generalization evidence.

Use independently initiated contacts/trials rather than treating crops of one scan as extra repetitions. Report actual measurement update rates and synchronized timing, not transmission frequency as an independent force sample rate. Record collection session, specimen provenance, calibration checks, and repeated-contact ordering so drift and wear can be inspected.

Record approach, contact establishment, steady sliding, and release. Preserve raw timestamps and calibration information. Use independent force measurements as labels. Define whether the inference inputs contain measured support forces or only tactile signals and actions. If support forces are used, describe the method as force-informed contact inference; evaluate tactile-only inference separately if claimed.

Identify motion and contact state independently where possible. A static contact's tangential-to-normal force ratio does not generally identify kinetic friction. Estimate sliding friction only from confirmed sliding intervals; static friction or slip onset needs a separate controlled ramp or comparable experiment.

### 5.3 Minimal mechanical model

First fit a simple Coulomb sliding-friction baseline from permitted support contacts:

\[
\mathbf F_t=-\mu_k F_n\frac{\mathbf v_t}{\|\mathbf v_t\|}
\quad\text{during sliding}.
\]

Use nonnegative coefficients and specify behavior near zero velocity. The initial evaluation can remain in continuous sliding to avoid overclaiming static-friction modeling.

Then test whether a constrained speed-dependent friction law, or a learned prior fitted from training surfaces and adapted from short probes, improves held-out forces. Begin with very few parameters; a small dataset may not identify a complicated load-, direction-, and history-dependent law.

Keep the direct support-force fit as a strong baseline. Learning is useful only if it improves limited-data prediction, uncertainty, or adaptation relative to this fit. Separate inference quality from solver accuracy. Check whether several parameter settings explain the same support data but predict different query forces.

Assess normal contact compliance only after measuring indentation and calibrating deformation in the sensor and fixture. Initially report an effective force–indentation relation for this contact geometry, not an intrinsic Young's modulus without a justified constitutive model.

### 5.4 Force evaluation

Hold out entire surfaces when evaluating generalization, with a limited support protocol for each new surface. For a small pilot, grouped leave-one-surface-out evaluation can use data more efficiently than a tiny fixed test set; select hyperparameters using inner training/validation data, never the held-out query.

Report tangential-force error in newtons, relative error with a sensible floor near zero, error versus speed/load, and support-budget curves. Compare against a global friction coefficient, per-surface coefficients fitted from the same brief support, a constrained model, and a fuller per-surface calibration reference with its larger data budget disclosed.

For deployable queries, use commanded inputs and solver-computed states or contact forces. Future measured normal forces can diagnose conditional prediction but cannot silently replace the forward model's own force computation.

## 6. Stage C: simulation validation

Start with a known-geometry slider or dragging task. Use a simple one- or two-dimensional contact simulator to test the identified law, or map effective parameters into an existing engine. MuJoCo already provides frictional contact dynamics; its native coefficients are a useful first integration point. [8]

Two different validations must be distinguished:

1. **Prescribed-motion force prediction:** given a motion command, predict its measured reaction force. This is a valid contact-model test.
2. **Forward motion prediction:** given an initial state and applied actions/forces, predict subsequent position and velocity. This requires the body or relevant degree of freedom to respond dynamically; replaying a prescribed trajectory is insufficient.

For a motion experiment, keep the counterface, geometry, mounting, and known mass consistent with calibration. Measure or characterize additional carriage/fixture drag. A free-body validation is an additional hardware capability, not something assumed from a servo-controlled scan.

Compare global/default parameters, brief-contact calibration, learned inference if useful, and a richer per-surface calibration reference. Score multi-step velocity/position error and force error on unseen surfaces and withheld actions. Unforced Coulomb coasting can include stopping distance under the restricted no-reversal law in the guide. Slip onset, sticking under applied forces, or more general contact-transition metrics require a separately defined and validated static/transition model.

Keep texture observations and mechanics separate in the implementation. A spectrum renderer can generate tactile observations, while a validated friction law affects dynamics. Attaching vibration noise to an engine does not validate a texture-dependent contact force law. Avoid double-counting friction if adding a custom force term to an engine that already computes friction.

## 7. Stage D: robot-learning evaluation

After force and motion validation, choose one task, such as dragging a known object to a target while respecting a force limit. Compare policies or planners using a fixed global contact model, brief-contact-calibrated parameters, and the learned contact model if it has demonstrated predictive value.

Hold task distribution, policy architecture, real-data budget, training steps, and evaluation surfaces constant. If testing tactile observation fidelity, vary that factor separately from the dynamics model. Report success, force-limit violations, and adaptation cost.

A planning/control experiment establishes usefulness for decision-making. A claim of improved robot learning or sim-to-real transfer requires the corresponding matched training and real evaluation. Large-scale reinforcement learning is not required for the first research milestone.

## 8. What makes this credible research for PhD applications

A defensible independent project should provide:

- A precise scientific question and a comparison with the closest papers.
- A written protocol with observable inputs, targets, support budgets, and held-out groups.
- Meaningful baselines and controls that could invalidate the preferred explanation.
- Completed quantitative experiments, failure analysis, and appropriately limited conclusions.
- Reproducible code, fixed manifests, configurations, raw result tables, and environment information.
- A clear account of Elton's original contribution and any external guidance or reused code.

Suggested output: a concise technical report of roughly 6–8 pages plus an appendix, code, and experiment configurations. Length is a practical suggestion, not an admissions requirement. A repository and report can document completed independent research before peer review; publication acceptance must be described separately.

CMU faculty guidance emphasizes explaining the research problem, its importance and difficulty, the relation to prior work, the technical approach, and validation. These are the qualities to demonstrate in the report and statement of purpose. [9]

Seek regular feedback from someone who can examine protocols, figures, and code. A recommendation based on observed research work is a different kind of evidence from a brief networking conversation. Do not assume any contacted researcher will advise the project or write a letter.

Use the title matching completed evidence. If only Stage A is complete, describe the work as tactile-response prediction and a study of probe information. Add force modeling, simulator calibration, or robot learning to the claim only after completing those evaluations. In-progress items belong in a clearly labeled future-work section.

No project design can guarantee publication or admission. The achievable goal is evidence of research judgment, ownership, and careful execution.

## 9. Schedule, milestones, and decisions

The initial setup and bounded development milestones are complete. Continue from the gates below rather than restarting the original week-by-week schedule. The order reflects dependencies; dates depend on available acquisition information, retained coverage, and hardware access. Do not let an unavailable manufacturing history or rig indefinitely prevent an explicitly limited public-data report.

| Next gate | Work | Concrete output or decision |
| --- | --- | --- |
| Completed 9 October: strict acceleration budget | Raw-window-first processing, dependency provenance, perturbation checks and matched reruns | 53 passing tests; 688 invariant real windows; preserved historical results and [boundary report](window_boundary_report.md) |
| Completed 9 October: bounded timing/claim and contact review | Original-CSV comparison, declared logged-coordinate convention, training-only heading/loading/travel and seven-setting sensitivity | Fifteen preserved CSVs; 200 reviewed records; [decision/report](clock_qc_review.md); physical calibration deferred; 62 current tests |
| Completed 9 October: metadata/exposure and domain design | Complete name/category review, historical access snapshot, whole-group reservation and query masks | 118 specimens, 87 conservative groups, 22 blocked from fresh test, 20 reserved in 15 groups; [design review](study_design_review.md); matched 70/44 fitting and 26 scoring domains |
| Completed 9 October: wider known-speed training coverage | Mandatory reservation preflight, 960 requested records, seven settings and common support/query eligibility | All half-second records and fifty required one-second supports retained; 44 common triples / 440 cells; [coverage report](wider_coverage_review.md); 70 tests |
| Error review and matched development | Inspect repeatability, convergence, floor sensitivity, residuals and wider selection coverage; implement matched domains | Practical-effect rationale, revised feature/QC scope if justified, and matched-grid familiar/omitted results |
| Scientific protocol freeze | Reserve fresh test groups; freeze features, QC, budgets, methods, tuning, comparisons, margins, and access rules; implement locked evaluation support | Immutable manifests and executable preflight; current twelve specimens remain development-exposed |
| Locked evaluation and report | Run frozen models on reserved queries; report the full method/probe matrix, uncertainty, limitations, and reproducibility | Completed Stage A report, including negative/inconclusive results; clearly bounded claims |
| Parallel hardware capability review | Verify normal/tangential force, synchronized motion, geometry, calibration, and independent-trial access; draft any outreach | Stage B go/no-go based on measurements, independent of the Stage A baseline winner; no messages sent without authorization |
| Hardware-dependent mechanics | If the rig or suitable recordings pass the gate, collect/analyze the force pilot and minimal law | Held-out force results and parameter-ambiguity analysis; otherwise explicitly deferred Stage B |
| Later dynamics and control | Verify a dynamically responsive experiment, integrate the validated law, then one matched task | Separate evidence for forward motion and decision-making; robot-learning claims only if that evaluation is actually completed |

Immediate next actions:

1. Retain the completed raw-boundary guards and matched reruns; use the new bounded roots for development and preserve historical pilots.
2. Retain the completed clock evidence and explicitly limited logged-coordinate scope; reopen through versioned comparisons only if new authoritative timing evidence appears.
3. Retain the completed metadata/exposure ledger, twenty-specimen reservation and 960-record training coverage audit. Inspect repeat variability, floor sensitivity, convergence and specimen/condition errors before changing the model; wider selection/transfer coverage remains pending.
4. Use the explicit 76/44/26 masks and matched 70-versus-44 fitting design; implement matched model/selection/scoring roles only after coverage and diagnostics, with prespecified QC intersections.
5. Protect the already reserved fresh groups while freezing the scientific protocol and implementing locked access/scoring. Prepare the technical report and hardware capability/outreach drafts in parallel; do not imply that outreach has been authorized or sent.

## 10. Software and resources

Suggested stack: Python; pandas and PyArrow for Parquet; NumPy and SciPy for timestamps, filtering, and spectra; scikit-learn for regression/retrieval baselines; PyTorch for the small encoder/predictor; Matplotlib for figures. A laptop can support initial feature extraction and small baselines. A GPU is optional for this initial model.

Useful documentation:

- [SciPy Welch spectral estimation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html)
- [Cluster data mirror and schema](https://huggingface.co/datasets/tamago117/cluster-haptic-texture-dataset)
- [ExSARN author code and data](https://github.com/dexrob/ExSARN)
- [DiffTactile project](https://difftactile.github.io/)
- [DiffTactile code](https://github.com/Genesis-Embodied-AI/DiffTactile)
- [MuJoCo computation and contact model](https://mujoco.readthedocs.io/en/stable/computation/index.html)

## 11. References and their roles

1. **Heravi, Yuan, Okamura, and Bohg. Learning an Action-Conditional Model for Haptic Texture Generation. ICRA 2020.** [Paper](https://arxiv.org/abs/1909.13025). Closest foundational precedent for tactile observation plus actions predicting texture acceleration.
2. **Heravi, Culbertson, Okamura, and Bohg. Development and Evaluation of a Learning-based Model for Real-time Haptic Texture Rendering. IEEE Transactions on Haptics, 2024.** [Paper](https://arxiv.org/abs/2212.13332). Relevant unseen-texture and nearest-neighbor conditioning precedent; spectral prediction is already established in this line of work.
3. **Si et al. DiffTactile: A Physics-based Differentiable Tactile Simulator for Contact-rich Robotic Manipulation. ICLR 2024.** [Paper](https://arxiv.org/abs/2403.08716). Contact-model calibration, measured-force supervision, and separation of mechanics and tactile rendering.
4. **TacTID: High-Performance Visuo-Tactile Sensor-Based Terrain Identification for Legged Robots. IEEE Sensors Journal, 2024.** [Author-hosted paper](https://charon-bo.github.io/assets/PDF/TacTID.pdf). Direct precedent for friction and effective-stiffness estimation; important for avoiding a broad first-of-its-kind claim.
5. **Eguchi et al. Cluster Haptic Texture Dataset: Haptic Texture Dataset with Varied Velocity–Direction Sliding Contacts.** [Current paper](https://arxiv.org/html/2407.16206v4). Main data and collection-protocol reference; publication also appears in Scientific Data in 2026.
6. **Gao, Tian, Lin, and Wu. On Explainability and Sensor-Adaptability of a Robot Tactile Texture Representation Using a Two-Stage Recurrent Networks. IROS 2021 — ExSARN.** [Final publication](https://ieeexplore.ieee.org/document/9636380). Representation-learning reference; a classification/attribute representation is not automatically a calibrated mechanics model.
7. **Eguchi, Hiroi, and Hiraki. HaptoFlow: High-Fidelity Real-Time Vibrotactile Generation via Flow Matching for Virtual Reality. 2026 preprint.** [Paper](https://arxiv.org/abs/2608.01974). Interaction-conditioned waveform generation reference; its current material-label interface is restricted to training materials. Flow matching can be a later renderer choice after the first predictive study.
8. **MuJoCo official computation documentation.** [Documentation](https://mujoco.readthedocs.io/en/stable/computation/index.html). Existing frictional dynamics and solver integration, rather than starting with a new whole engine.
9. **Jonathan Aldrich. Advice on writing a Ph.D. statement of purpose for CMU.** [Faculty guidance](https://www.cs.cmu.edu/~aldrich/essay-advice.html). Research communication and evidence relevant to applications.
10. **Gao et al. Tactile DreamFusion: Exploiting Tactile Sensing for 3D Generation. NeurIPS 2024.** [Paper](https://arxiv.org/abs/2412.06785). Longer-term link to tactile surface detail in 3D generation; not a prerequisite for the first sliding-contact experiment.

Source statements above are brief summaries. Reported development outcomes link to the completed experiment records; remaining protocol choices, budget corrections, full-grid evaluations, and hardware stages are proposed work. The public repository does not establish physical calibration, novel material identification, publication acceptance, or robot-learning benefit.
