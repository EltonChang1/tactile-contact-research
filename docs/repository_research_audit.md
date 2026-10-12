# Repository research audit

Reviewed **11 October 2026**. This audit reads source code, configurations and saved documentation. It does not inspect raw signals or reserved specimen records, download data, refit methods, rerun experiments, change scientific settings or independently rerun the saved validation. Numerical statements below are attributed to the existing reports.

## Contents

1. [Current research object](#current-research-object)
2. [Implemented capabilities](#implemented-capabilities)
3. [Strongest current evidence](#strongest-current-evidence)
4. [Evidence limits and protected data](#evidence-limits-and-protected-data)
5. [Gap to a contact physics world model](#gap-to-a-contact-physics-world-model)
6. [Existing documents and next decisions](#existing-documents-and-next-decisions)

## Current research object

The completed software studies **brief-support-conditioned vibration-response prediction**. It receives short sliding-contact observations from a specimen plus a requested speed, direction and nominal pressing load, and predicts the acceleration power spectrum of another recorded contact. This is a potential tactile **observation-model component** of a future physical world model.

The current learned latent is a compact representation of support spectra. It is not established as friction, compliance, contact geometry or a sufficient physical state. The repository has no implemented action-conditioned state-transition model, contact-force law, rigid/deformable-body solver, optical tactile renderer, forward-motion benchmark or robot-control experiment. The mechanical study under [experiments/brief-touch-mechanics](../experiments/brief-touch-mechanics/README.md) is a proposed design; its maintained successor lives in the separately linked [brief-touch-mechanics repository](https://github.com/EltonChang1/brief-touch-mechanics). That repository's public README, checked on 11 October 2026, explicitly reports a proposed study with no force or motion results. It states that implementation and data collection come next, with data/rig access and force calibration still unconfirmed. This is a separate proposed research scope, not a completed mechanics capability of the vibration predictor.

The measurement interface matters. Recorded pressing force and probe position support retrospective eligibility/QC; predictor query inputs encode **nominal** load and declared motion conditions. There are no synchronized per-scan tangential-force targets in the current study. Separately measured metadata friction attributes are not substitute force trajectories or predictor inputs. See the [mechanical methods review](../experiments/brief-touch-mechanics/METHODS.md) and [protocol](protocol.md).

## Implemented capabilities

| Layer | What exists | Main implementation/evidence |
| --- | --- | --- |
| Data provenance | Pinned bounded downloads, hashes, recording identities, specimen manifests, measured/synthetic separation and preserved source versions | [download.py](../src/tactile_contact/download.py), [source_archive.py](../src/tactile_contact/source_archive.py), [records.py](../src/tactile_contact/records.py) |
| Timing and motion QC | Native timestamp motion estimation; retrospective steady windows; logged-coordinate convention; documented timing sensitivity | [windows.py](../src/tactile_contact/windows.py), [clock review](clock_qc_review.md), [clock convention](../configs/clock_convention.json) |
| Strict support boundary | Raw allowed acceleration is cropped before local interpolation/filtering; local endpoint padding and dependency provenance; outside-window perturbation checks | [boundary report](window_boundary_report.md), [pipeline.py](../src/tactile_contact/pipeline.py) |
| Sensor target | Welch PSD and 32 log10 band powers per acceleration axis: **96 output values**, 24–1000 inverse logged-time coordinates; acceleration converted from g before estimation | [signal.py](../src/tactile_contact/signal.py) |
| Support/query design | Five protocols: single, repeat, second speed, second load, second direction; support durations **0.25/0.5/1 logged seconds**, fixed **0.5 logged-second** query | [config.py](../src/tactile_contact/config.py), [episode construction](../src/tactile_contact/episodes.py), [study design](study_design_review.md) |
| Learned predictor | MLP encodes each 101-dimensional support; masked mean produces a **16-dimensional** latent; query condition has four normalized speed/heading/load values plus support count; decoder returns 96 powers | [models.py](../src/tactile_contact/models.py), [training.py](../src/tactile_contact/training.py) |
| Baselines | Conditions-only regression, spectrum copy, nearest-support retrieval, fixed-feature ridge, full-PSD speed/load rescaling; omitted-speed retrieval uses permitted endpoints | [baselines.py](../src/tactile_contact/baselines.py) |
| Evaluation | Per-query/per-specimen errors; equal-specimen aggregation; seed averaging; paired group comparisons; wrong-support control; forward/reverse repetitions; saved residuals | [metrics.py](../src/tactile_contact/metrics.py), [evaluation.py](../src/tactile_contact/evaluation.py), [matched.py](../src/tactile_contact/matched.py) |
| Access and selection | Separate fit, selection and scoring roles; guarded matched feature store; all-selection seal; reservation preflight in newer review runners | [matched implementation](../src/tactile_contact/matched.py), [study_design.py](../src/tactile_contact/study_design.py), [matched validation](matched_validation_review.md) |
| Reproducibility | Hash provenance, immutable completed output roots, selected histories/artifacts, independent replay and raw-feature verification scripts, synthetic fixtures and tests | [validation report](matched_validation_review.md), [reproduction instructions](reproducing_experiments.md) |

[pyproject.toml](../pyproject.toml) defines an installable Python 3.12+ package and `tactile-contact` CLI. Commands cover download, audit, prepare, run, synthetic fixtures, figures and timing. Its listed numerical stack is NumPy/SciPy/pandas/PyArrow/scikit-learn/PyTorch/Matplotlib; no physics-engine dependency is declared. `load_config` rejects stages other than development, explicitly leaving locked scientific test evaluation disabled.

The spectral target describes energy by frequency. It discards waveform phase and does not predict a time-resolved acceleration trajectory, evolving contact patch, force, pose or velocity. Query condition dependence is useful, but it differs from rolling out state under a sequence of commanded actions.

## Strongest current evidence

The authoritative current comparison is [matched familiar / omitted-speed development, 10 October 2026](matched_development_review.md). Both experiments use the same ten training specimens and two exposed selection/scoring specimens, the same support scaler and shared evaluation domains. Familiar fitting includes **70 query triples** (44 known-speed plus 26 safe transfer-speed); omitted fitting includes **44 known-speed triples**. Both select on the same 44 known-speed domain and then score the same 26 transfer-speed triples. Six transfer triples lacking permitted retrieval endpoints are excluded. This is a restricted development contrast; the broader 76-query familiar study remains unfinished.

The primary single-touch cell uses a 0.5 logged-second support. Values below are saved raw log10 band-power MAE, averaging queries within specimen, seeds within specimen and specimens equally. Lower is better.

| Scoring domain | Orientation | Familiar retrieval | Omitted retrieval | Familiar fixed features | Omitted fixed features | Familiar encoder | Omitted encoder |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Known-speed 44 | Forward | 0.157480 | 0.157480 | 0.316785 | 0.312214 | 0.358985 | 0.345186 |
| Known-speed 44 | Reverse | 0.153866 | 0.153866 | 0.311432 | 0.306780 | 0.382472 | 0.394519 |
| Transfer-speed 26 | Forward | **0.149374** | **0.311900** | 0.298727 | 0.318800 | 0.351728 | 0.354996 |
| Transfer-speed 26 | Reverse | **0.146161** | **0.308938** | 0.300449 | 0.317804 | 0.365812 | 0.395250 |

Removing transfer-speed responses increases retrieval transfer MAE by **0.162526 forward / 0.162777 reverse**. This treatment also reduces the training condition/sample count; it does not isolate speed coverage at an equal training-data budget. Retrieval and fixed features remain stronger than the encoder on these transfer cells. Wrong-support degradation indicates support dependence within the setup, without establishing a learned-model advantage or identifiable physical properties. The direction-versus-repeat transfer contrast changes sign with orientation; no reliable direction advantage is established. Reverse scoring changes both support and query repetition.

Training counts are **21,000 familiar / 13,200 omitted episodes**, with **1,320** shared forward known-speed selection episodes per experiment. Both score identical **4,200** episode inputs across two orientations. These episode counts reuse conditions/budgets and are not independent specimen counts. Two of six selected encoder trajectories remain cap-limited under the finite 120-epoch policy; the run does not establish optimization convergence.

The [saved independent validation](matched_validation_review.md) reports **110 passing tests**, **22** bit-for-bit reproduced prediction arrays, **92,400** score rows, **462,000** scalar metric checks, **840** summary rows, **1,680** specimen rows and **11,760** primary residual rows. It reports exact reconstruction of **1,878** windows from **1,746** recordings, with zero maximum feature discrepancy and invariance to outside-interval acceleration. These are strong implementation checks for the saved development computation. They do not create fresh scientific evidence. This research audit has not rerun those checks.

Saved supporting findings include equal-specimen query-repeat MAE **0.172972** and mean modeled-band symmetric RMS difference **10.779%** across the training repeat review. Those two unaligned scans do not establish an irreducible noise ceiling. See [training diagnostics](development_diagnostics_review.md), [finite convergence](convergence_review_report.md) and [frozen repetition reversal](repetition_review_report.md). Earlier pilot scores are historical and should not replace the matched table above.

## Evidence limits and protected data

1. **Physical clock remains uncalibrated.** `logged_coordinates_v1` explicitly defines durations as logged-time extents and frequencies as inverse logged-time coordinates. The 6000 Hz processing grid is computational. Documented acquisition rates and observed timestamp row rates disagree. The clock review completes a bounded claim decision, not physical calibration.
2. **Scientific confirmation is pending.** The same ten training and two selection/scoring specimens have been repeatedly used. Saved development results cannot support a population significance claim, manufacturing-family generalization or a locked test result.
3. **Twenty specimens in fifteen whole groups are reserved.** The [design review](study_design_review.md) records 118 metadata-reviewed specimens, 87 conservative groups and 22 specimens blocked from fresh testing through exposure propagation. Manufacturing relationships remain uncertain. Existing reports say the twenty reserved specimens remain untouched; this audit preserves that boundary.
4. **Access guards have a scope.** Newer coverage/matched runners perform reservation preflight and separate fitting from scoring access. Historical CLI experiment commands do not automatically apply every newer guard. A locked scientific evaluation interface is not implemented; documentation-only research does not authorize opening reserved signals.
5. **Contact acquisition is retrospective.** Offline motion/QC does not establish causal online onset detection or a deployable observation budget including approach, settling, travel and active probe selection.
6. **Mechanics remain unmeasured here.** No calibrated tangential-force/compliance labels, independently verified slip states, synchronized free-response motion experiment or validated engine-contact pairing exists in this checkout.

## Gap to a contact physics world model

The following decomposition is an architectural assessment, not an implemented result:

| Needed component | Current foothold | Missing evidence/implementation |
| --- | --- | --- |
| Observation inference: touch/history → contact state and uncertain physical parameters | Brief support spectra → compact latent | Geometry, normal/tangential traction, stick/slip, deformation and identifiable parameter estimates; uncertainty; sensor calibration and cross-sensor adaptation |
| Action-conditioned dynamics: current state + action + contact parameters → next state/force | Static query speed/direction/nominal-load conditioning | Sequential transition model; mass/inertia/geometry; force/contact constraints; friction/compliance law; integration; multi-step pose/velocity/force ground truth |
| Tactile observation generation: physical contact state → sensor reading | Predicted acceleration band powers | Time-domain waveform or optical image/deformation renderer; sensor transfer function; phase/transients; latency, drift and measurement noise |
| Engine integration and identification | Proposed Stage B/C design | Fit effective contact laws from aligned independent-force labels; check parameter ambiguity; map law into a solver; avoid double-counting engine friction |
| Planning/control usefulness | Fixed protocol/probe comparisons | Validated forward rollouts under unseen actions; planner/policy ablations; matched real task/control evaluation |
| Trustworthy generalization | Provenance, support boundaries, group reservation and strong baselines | Frozen practical margin/secondary policy; broader familiar coverage; independently verified locked scoring before reserved signal access |

A short spectrum can carry specimen-specific information without uniquely identifying mechanics. A sensor's own compliant body also shapes its observations. Geometry, load, speed, sensor material and contact history must be represented or controlled before interpreting a learned latent as material physics. Sensor papers in the accompanying dictionary are therefore primarily **enabling**: they make physical state observable, but force estimation or contact reconstruction alone does not establish action-conditioned forward dynamics.

The closest concrete extension already described by the repository is a calibrated prescribed-sliding **force** pilot with a minimal friction baseline, followed by an independently moving-body **motion** test and then one control task. A sophisticated renderer can be developed separately, but sensor realism and mechanics accuracy need separate measurements and ablations.

## Existing documents and next decisions

| Purpose | Current artifact |
| --- | --- |
| Maintained goals, gates and closest prior work | [Research plan](research_plan.md) |
| Executable numerical/measurement implementation guidance | [Implementation guide](implementation_guide.md) |
| Input/target and study contract | [Protocol](protocol.md) |
| Current results and all-cell links | [Matched development](matched_development_review.md) |
| Strongest saved computational validation | [Matched validation](matched_validation_review.md), [replay verifier](../scripts/verify_matched_results.py), [raw-feature verifier](../scripts/verify_matched_raw_features.py) |
| Exposure, whole-group reservation and domains | [Study design](study_design_review.md), [study-design config](../configs/study_design.json) |
| Time coordinate and claim boundaries | [Clock/contact QC review](clock_qc_review.md), [clock convention](../configs/clock_convention.json) |
| Reliability and finite optimization limits | [Diagnostics](development_diagnostics_review.md), [convergence](convergence_review_report.md), [repetition reversal](repetition_review_report.md) |
| Run prerequisites and historical preservation | [Reproduction instructions](reproducing_experiments.md) |
| Proposed mechanical acquisition and evaluation | [Brief-touch mechanics methods](../experiments/brief-touch-mechanics/METHODS.md) |

The next scientific decision is to justify the practical-effect margin and secondary-analysis policy, freeze cohort/coverage/features/methods/budgets and implement locked scoring. Hardware feasibility and calibrated channel review can proceed independently. The literature review should guide those decisions while preserving the current negative and inconclusive findings.
