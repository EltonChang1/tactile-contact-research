# Brief Contact Probes for Predicting Texture and Sliding Contact

Prepared for Elton Chang — 7 October 2026, America/Los_Angeles

**Status:** Proposed independent research. No experiments, results, hardware access, novelty claim, or publication acceptance are implied by this plan. Numerical choices below are starting specifications to finalize after a data audit and mentor review.

## 1. Objective and research scope

Long-term objective: develop contact models and tactile observation models that improve physics simulation and robot learning.

First scientific question: **How much brief contact data is needed to predict a previously unseen surface's response under other motions and loads, and which additional probe provides useful information?**

The initial public-data study predicts vibration spectra. The mechanical extension predicts sliding forces and identifies friction behavior for a fixed probe–surface contact. These are separate milestones with separate evidence requirements.

The main candidate contribution is a careful study of contact information, generalization, and probe selection. An encoder and decoder alone are not the contribution. Any claim of novelty requires checking the closest prior work and obtaining expert feedback.

The first mechanical scope is **sliding friction with a fixed contact geometry**. Add compliance after measuring indentation and calibrating fixture and probe deformation. A complete engine, full-body touch, universal material properties, and large world-model training are longer-term objectives.

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

For ten pilot surfaces, plot acceleration, normal force, and position together. Check steady sliding, actual loading variation, timestamps, clipping, and differences between repetitions. Record exclusions using a rule defined without looking at model test errors.

Determine the number of usable windows per condition after removing approach, acceleration, and stopping phases. Keep track of observations that cannot provide a full requested duration. Do not silently shorten long probes or fabricate extra independent trials.

Document possible machine vibration and sensor resonances. Wrong-material and action-only controls help detect whether performance is dominated by the apparatus, but a single apparatus cannot establish sensor transfer.

### 4.3 Split and test protocol

Use approximately 80 training surfaces, 18 validation surfaces, and 20 test surfaces, adjusted after grouping closely related specimens. Balance category coverage where feasible; group related variants rather than splitting them merely to meet exact counts.

All recordings from a held-out surface remain outside model training and preprocessing-statistic fitting. Material IDs are used to pair records and construct splits, never as encoder or predictor inputs. Split records before creating windows.

Publish the fixed split manifest and evaluation configuration. Use validation surfaces for architecture, feature, and stopping decisions. Run the locked test after these choices. Use three model initialization seeds; additional group splits are a predeclared robustness check, not an opportunity to choose the best result.

A test surface is observed through a limited support set at evaluation time. This is adaptation from brief contact, not prediction with zero observations. The query recordings remain hidden until scoring. Model weights stay frozen unless a separately labeled adaptation baseline specifies otherwise.

### 4.4 Probe conditions and budgets

Start with a reference contact: 40 mm/s, direction 0 degrees, nominal load 0.5 N. Compare observed durations of 0.25, 0.5, and 1 second, subject to the audit confirming usable windows.

Then compare these two-probe protocols, using the same duration per contact:

| Protocol | Second probe | Question |
| --- | --- | --- |
| Repetition | Same condition, other recorded repetition | Does averaging repeated contact explain the gain? |
| Speed | 20 mm/s, 0 degrees, 0.5 N | Does varying speed improve prediction? |
| Load | 40 mm/s, 0 degrees, 1 N | Does observing another load reduce loading uncertainty? |
| Direction | 40 mm/s, 90 degrees, 0.5 N | Does an orthogonal contact reveal directional behavior? |

Compare second-probe alternatives at the same total observation duration and number of contacts. Report total time and travel distance separately; different speeds imply different scanned distances.

Score all protocols on a common query set that excludes the union of support conditions. This prevents a protocol from receiving credit for having directly observed its evaluation condition. A condition's other repetition should not serve as a query for that same observed condition in the primary cross-condition result.

Use a fixed support repetition and the other repetition for query evaluation where possible, then reverse the assignment as a sensitivity check. Both repetitions may be used as support for the repetition-control protocol, so queries for that protocol must come from other conditions. The dataset contains only two repetitions; do not invent a three-repeat control.

### 4.5 Features and prediction targets

Begin with three-axis acceleration, preserving amplitude in consistent units. Remove the constant offset and extract spectra from steady contact. If resampling is necessary, check timestamps and use appropriate filtering. Compute summary statistics only from training data.

Use Welch power spectral density estimates and integrated power in fixed frequency bands. A workable starting configuration is 32 bands over a validated acceleration frequency range, per axis, with a log transform and a documented numerical floor. Choose the band range and window settings from the audit; exclude empty or unreliable bins. Keep the spectral-estimation procedure consistent across durations.

The encoder receives the observed spectral features and observed contact conditions. It can also receive measured normal-force summaries from the support contact, with an ablation that removes them. The predictor receives the inferred representation and the **requested speed, direction, and nominal load** for the query.

Never use query acceleration, query material identity, or future measured query force as deployable prediction inputs. Any optional future-force-conditioned analysis must be labeled as an oracle diagnostic and reported separately.

The primary target is log spectral band power. A secondary target is vibration amplitude, computed from consistently band-limited data. This avoids requiring an exact phase-aligned waveform from a short contact on a heterogeneous surface.

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

### 4.7 Generalization experiments

Separate the following claims rather than averaging them into one score:

1. **New surfaces, familiar conditions:** training includes the condition grid but not test surfaces.
2. **New surfaces and speed interpolation:** a separate model uses only 20, 40, and 60 mm/s for training and validation; evaluation includes 30 and 50 mm/s. These omitted speeds are not support conditions for this experiment.
3. **Load transfer:** a one-load support contact predicts the other available nominal load. A two-load support protocol answers a different question: the value of observing both loads.
4. **Direction transfer:** evaluate held-out directions relative to the support set; optionally add a separate model with globally omitted directions.

Category exclusion is an exploratory stress test. Holding out a specimen does not establish transfer to an entirely new material family. Two load levels do not establish arbitrary-load extrapolation. A single probe and apparatus do not establish sensor-independent material properties.

### 4.8 Metrics, uncertainty, and interpretation

Primary metric: mean absolute error of predicted log band power, averaged over query conditions within each surface and then over surfaces. Use a fixed log floor and report its sensitivity when relevant.

Secondary metrics: amplitude error, per-axis spectral error, category-level error, and error as a function of probe duration and second-probe type.

Report paired differences between methods on the same held-out surfaces, confidence intervals obtained by resampling surfaces or specimen groups, and variation across initialization seeds. Thousands of windows are not thousands of independent materials. Compare errors with differences between the two repeated recordings as context, while acknowledging that two repeats provide a limited estimate of variability.

If uncertainty is added, evaluate interval coverage and width on held-out surfaces. Ensemble disagreement alone is not evidence of calibrated uncertainty.

Predeclare interpretation rules:

- If wrong-surface support does not worsen predictions, do not claim useful surface identification.
- If retrieval performs equally well, report that a continuous learned representation has not demonstrated an advantage.
- If a second direction improves prediction more than repeated contact at the same budget, this supports direction-specific information in probing.
- If speed transfer works while load transfer fails, investigate loading variation and whether the support data constrain load dependence.
- If all methods fail, inspect repeat variability, apparatus signals, and observability before expanding network size.

Do not select a desired percentage improvement in advance and call it a scientific success criterion. Choose a practically meaningful effect after auditing signal scales and repeat variability, before opening the test results.

## 5. Stage B: measured contact mechanics

### 5.1 First target and hardware dependency

First mechanical target: **sliding tangential force under different normal loads and speeds for a fixed probe–surface pair**.

Required capabilities: independently calibrated normal and tangential force measurements, controlled relative motion, known probe geometry, synchronized position and velocity, and a repeatable tactile or acceleration measurement. A calibrated linear stage and fixture can be sufficient; a dexterous hand is not a requirement.

Hardware access is unconfirmed. Seek a mentor or existing rig while completing Stage A. Reuse an existing dataset only after checking that it exposes the required forces, motion, independent records, and surface variation. A paper describing collection does not guarantee those recordings are downloadable. DiffTactile's code is available, but access and adequacy of its real system-identification recordings must be checked. Its paper's two real surfaces would not alone support a broad unseen-material benchmark. [3]

### 5.2 Calibration and collection

Begin with known geometry and rigid flat surfaces to reduce deformation confounds. Keep probe construction and mounting fixed. Calibrate force axes, zero offsets, cross-axis sensitivity, sensor delay, fixture drag, and probe/fixture deformation as needed. Record reference contacts before and after sessions.

A pilot design is 8–12 distinct surface specimens, three usable speeds, three normal-load levels, and at least five independent repetitions per condition, collected across more than one session where feasible. Exact ranges depend on sensor resolution and rig capabilities. This is a small pilot, not a universal material study. Distinct specimens and groups—not windows—determine the strength of generalization evidence.

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

Compare global/default parameters, brief-contact calibration, learned inference if useful, and a richer per-surface calibration reference. Score multi-step velocity/position error and force error on unseen surfaces and withheld actions. Include stopping or slip metrics only after defining the necessary static/contact-transition model.

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

The following is a six-to-eight-week first-project target, assuming concentrated work. Hardware-dependent stages may take longer and should not delay completing an honest public-data report.

| Period | Work | Concrete output or decision |
| --- | --- | --- |
| Week 1 | Read closest papers, audit ten surfaces, review scope with a researcher if available | Related-work matrix, data audit, draft protocol; investigate rig access |
| Week 2 | Finalize groups, features, support/query definitions, and baselines | Locked manifests and a reproducible baseline pipeline |
| Weeks 3–4 | Train the small model; evaluate duration, second-probe choice, and transfer | Main quantitative tables, material-level uncertainty, interpretation of failures |
| Week 5 | Complete required robustness checks; write the first report | Completed Stage A report and code; mechanical extension decision |
| Weeks 6–8 | If a calibrated rig is available, collect the force pilot and test a minimal friction model; otherwise pursue a focused public-data extension or verify reuse of suitable recordings | Measured force results when feasible; otherwise an explicitly limited completed public-data study |
| Later | Validate simulator motion, then one control/learning task | Evidence for stronger physical-simulation and robot-learning claims |

Immediate next actions:

1. Write a one-page protocol with the primary question, probe budgets, observable inputs, and paired comparison to retrieval.
2. Read Heravi 2020/2024 and DiffTactile before claiming a gap; include TacTID in the mechanical comparison.
3. Download ten Cluster surfaces and make synchronized signal plots and cross-condition spectral plots.
4. Identify which calibration and force-measurement capabilities a mentor or partner can actually provide.
5. Finalize the scope based on the audit and access; complete the public study regardless of the hardware decision.

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

Source statements above are brief summaries; the experimental protocol, architecture choices, budgets, milestones, and interpretation rules are recommendations for this proposed project.
