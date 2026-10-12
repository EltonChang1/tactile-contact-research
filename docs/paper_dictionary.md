# Tactile Paper Dictionary

Reviewed **2026-10-11** (America/Los_Angeles). **99 papers**.

A curated map of tactile research relevant to a contact physics engine and an action-conditioned world model. Read the [research synthesis](tactile_world_model_review.md) and [repository audit](repository_research_audit.md) for decisions and current evidence.

[Canonical JSON](paper_dictionary.json) · [Filterable CSV](paper_dictionary.csv)

## Table of contents

- [Scope and field definitions](#scope-and-field-definitions)
- [Recommended reading path](#recommended-reading-path)
- [Sensor foundations and physical observability (21)](#foundations-sensors)
- [Contact state, force and parameter identification (6)](#force-state-identification)
- [Texture datasets and vibration observation models (11)](#datasets-texture-rendering)
- [Tactile representations and multisensory datasets (14)](#representations-multimodal)
- [Predictive tactile dynamics and world models (12)](#predictive-world-models)
- [Active exploration and tactile control (7)](#active-touch-control)
- [Tactile simulators and sensor calibration (16)](#tactile-simulation)
- [Physics solvers, contact mechanics and learned simulation (12)](#physics-foundations)

<a id="scope-and-field-definitions"></a>
## Scope and field definitions

Curated primary-source research map for tactile contact state/parameter inference, action-conditioned physical dynamics, sensor observation modeling and planning. Coverage includes foundational sensors, classical vibration modeling, datasets, tactile representations, contact simulation and recent work through 11 October 2026. It is not an exhaustive systematic review or a claim that any single paper supplies a general physics world model.

**Direct** means the paper addresses a contact-state, parameter, dynamics, observation or planning interface. **Enabling** supplies sensors, data or numerical methods. **Adjacent** offers transferable ideas with a different objective.

**P0**: closest prior work or immediate baseline. **P1**: useful implementation or next-stage reading. **P2**: later extension. Priorities and world-model contributions are our assessments, not reported paper results.

**Year** is the earliest manuscript/publication year independently verified in this review; the publication field records venue dates separately. It does not guarantee the earliest online submission. **Full-text-sections** means the listed sections were inspected, not that every experiment was reproduced. **Abstract-and-metadata** means broader triage. Resource links identify verified author releases/pages; null means not verified, not unavailable. A linked release does not imply its files, license, calibration or runnable dependencies were tested.

Evidence describes the paper's reported results. Limitations and repository connections also include our assessment of transfer to this project. Entry sources are listed next to each paper; publication status is not inferred from a conference name in search results.

<a id="recommended-reading-path"></a>
## Recommended reading path

| Order | Paper | Read for |
| --- | --- | --- |
| 1 | [Cluster Haptic Texture Dataset: Haptic Texture Dataset with Varied Velocity-Direction Sliding Contacts](#cluster-haptic-texture-2024) | Understand the current measurements and their mechanics/timing limits. |
| 2 | [Learning an Action-Conditional Model for Haptic Texture Generation](#heravi-action-conditional-texture) | Closest action-conditioned tactile-to-vibration precedent. |
| 3 | [Development and Evaluation of a Learning-based Model for Real-time Haptic Texture Rendering](#heravi-real-time-texture) | Understand unseen-texture retrieval and the prior art around nearest representations. |
| 4 | [Modeling and Rendering Realistic Textures from Unconstrained Tool-Surface Interactions](#culbertson-ar-textures-2014) | Build a transparent force/speed-conditioned observation baseline. |
| 5 | [How Much Haptic Surface Data Is Enough?](#how-much-haptic-data-2017) | Study simple force-law fitting and data-budget stopping. |
| 6 | [TacTID: High-Performance Visuo-Tactile Sensor-Based Terrain Identification for Legged Robots](#tactid-2024) | Design calibrated friction/effective-stiffness inference and contact-state checks. |
| 7 | [Dense Tactile Force Distribution Estimation using GelSlim and inverse FEM](#gelslim-inverse-fem-2018) | Separate sensor deformation from independent force validation. |
| 8 | [DiffTactile: A Physics-based Differentiable Tactile Simulator for Contact-rich Robotic Manipulation](#difftactile) | Study contact/sensor calibration and explicit mechanics assumptions. |
| 9 | [Efficient Tactile Simulation with Differentiability for Robotic Manipulation](#efficient-tactile-simulation) | Connect deformable tactile simulation, dynamics gradients and control. |
| 10 | [RoboPack: Learning Tactile-Informed Dynamics Models for Dense Packing](#robopack) | Separate tactile latent physics inference from future object-state dynamics. |
| 11 | [Multi-Modal World Model for Physical Robot Interactions: Simultaneous Visual and Tactile Predictions for Enhanced Accuracy](#spots) | Study planned-action-conditioned joint visual/taxel prediction and its force-calibration limit. |
| 12 | [Visuo-Tactile World Models](#visuo-tactile-world-models) | Compare tactile-aware prediction/planning and its generalization limits. |
| 13 | [ContactWorld: What Representations Matter for Vision-Tactile Latent World Models in Contact-Rich Manipulation](#contactworld) | Choose physical-state/predictive representations using controlled comparisons. |
| 14 | [DexTouch-WM: Learning Action-Conditioned Tactile World Models from Human Touch for Dexterous Robot Manipulation](#dextouch-wm) | Inspect a recent explicit future-action-conditioned pressure model. |
| 15 | [Predictive Visuo-Tactile Interactive Perception Framework for Object Properties Inference](#predictive-interactive-perception-2024) | Represent belief and choose informative physical probes. |
| 16 | [MuJoCo: A physics engine for model-based control](#mujoco) | Use an established solver for a restricted, validated mechanical model. |
| 17 | [An Unconstrained Convex Formulation of Compliant Contact](#sap-compliant-contact) | Understand compliance/friction solver assumptions and optimization. |
| 18 | [Sparsh: Self-supervised touch representations for vision-based tactile sensing](#sparsh-tacbench) | Evaluate reusable touch features and task-specific force supervision. |

<a id="foundations-sensors"></a>
## Sensor foundations and physical observability

Hardware and surveys that determine what contact variables can be measured. Sensor geometry, compliance, bandwidth and calibration constrain every later model.

| Paper | Year | Priority / relevance | Output |
| --- | --- | --- | --- |
| [GelSight: High-Resolution Robot Tactile Sensors for Estimating Geometry and Force](#gelsight-geometry-force-2017) | 2017 | P0 / enabling | Geometry, force/shear cues and slip information. |
| [A Review of Tactile Information: Perception and Action Through Touch](#tactile-information-review-2020) | 2020 | P0 / enabling | Raw/contact/object/action information hierarchy. |
| [GelSlim3.0: High-Resolution Measurement of Shape, Force and Slip in a Compact Tactile-Sensing Finger](#gelslim3-2021) | 2021 | P0 / enabling | Shape, contact 3D force distribution and incipient slip. |
| [Evaluation of a Vision-based Tactile Sensor](#gelforce-2004) | 2004 | P1 / enabling | Contact force-vector distribution. |
| [Biomimetic Tactile Sensor Array](#biotac-2008) | 2008 | P1 / enabling | Spatial transduction responses containing force/contact information. |
| [Retrographic sensing for the measurement of surface texture and shape](#retrographic-gelsight-2009) | 2009 | P1 / enabling | Contacted surface normals and a 2.5D height reconstruction. |
| [Improved GelSight Tactile Sensor for Measuring Geometry and Slip](#improved-gelsight-2017) | 2017 | P1 / enabling | Surface normals, height maps, translational/rotational slip detection. |
| [GelSlim: A High-Resolution, Compact, Robust, and Calibrated Tactile-sensing Finger](#gelslim-2018) | 2018 | P1 / enabling | High-resolution tactile images with improved integration and durability. |
| [The TacTip Family: Soft Optical Tactile Sensors with 3D-Printed Biomimetic Morphologies](#tactip-family-2018) | 2018 | P1 / enabling | Local contact/location estimates across several sensor designs. |
| [Soft-bubble: A highly compliant dense geometry tactile sensor for robot manipulation](#soft-bubble-2019) | 2019 | P1 / enabling | Deformation geometry; object classification, pose estimation/tracking. |
| [DIGIT: A Novel Design for a Low-Cost Compact High-Resolution Tactile Sensor with Application to In-Hand Manipulation](#digit-2020) | 2020 | P1 / enabling | Tactile feedback enabling marble manipulation. |
| [OmniTact: A Multi-Directional High Resolution Touch Sensor](#omnitact-2020) | 2020 | P1 / enabling | Contact-angle estimates and touch-only insertion control. |
| [In-Hand Object Localization Using a Novel High-Resolution Visuotactile Sensor](#gelstereo-2021) | 2021 | P1 / enabling | Contact point clouds and in-hand object pose. |
| [A soft thumb-sized vision-based sensor with accurate all-round force perception](#insight-2021) | 2021 | P1 / enabling | Spatial normal/shear force distribution. |
| [ReSkin: versatile, replaceable, lasting tactile skins](#reskin-2021) | 2021 | P1 / enabling | Contact/force-related measurements robust across sensor variation. |
| [DenseTact: Optical Tactile Sensor for Dense Shape Reconstruction](#densetact-2022) | 2022 | P1 / enabling | Dense 3D sensor-surface reconstruction. |
| [DenseTact 2.0: Optical Tactile Sensor for Shape and Force Reconstruction](#densetact2-2022) | 2022 | P1 / enabling | Surface shape and six-axis wrench. |
| [Tac3D: A Novel Vision-based Tactile Sensor for Measuring Forces Distribution and Estimating Friction Coefficient Distribution](#tac3d-2022) | 2022 | P1 / enabling | Shape, force distribution and friction-coefficient maps. |
| [Digitizing Touch with an Artificial Multimodal Fingertip](#digit360-2024) | 2024 | P1 / enabling | Multimodal tactile readings and sensing features. |
| [GelSlim 4.0: Focusing on Touch and Reproducibility](#gelslim4-2024) | 2024 | P1 / enabling | Depth and shear estimates; manufacturing/perception resources. |
| [GelTip: A Finger-shaped Optical Tactile Sensor for Robotic Manipulation](#geltip-2020) | 2020 | P2 / enabling | Contact localization across the sensing surface. |

<a id="gelsight-geometry-force-2017"></a>
### GelSight: High-Resolution Robot Tactile Sensors for Estimating Geometry and Force

**Wenzhen Yuan et al. · 2017 · P0 · enabling**  
Sensors 17(12):2762, 2017

[Paper / primary source](https://pmc.ncbi.nlm.nih.gov/articles/PMC5751610/)

- **Problem:** Explain optical tactile sensing principles and useful robot contact information.
- **Inputs:** Illuminated elastomer images and lateral marker deformation. **Conditioning:** Optical calibration, sensor construction and contact deformation.
- **Output:** Geometry, force/shear cues and slip information.
- **World-model contribution (assessment):** Core reference for separating sensor deformation, inferred contact state and object properties.
- **Reported evidence:** Reviews designs and algorithms with geometry/force evaluations and manipulation applications.
- **Limits / transfer assessment:** Primarily a sensor/principles review; inference and task examples do not establish a universal dynamics model.
- **Repository connection:** Guides future measurement interfaces and the observation-model side of Stage B/C.

Review: `full-text-sections`; Abstract; Section 3 sensing principle; Sections 6–7 applications and conclusions Verified 2026-10-11.

<a id="tactile-information-review-2020"></a>
### A Review of Tactile Information: Perception and Action Through Touch

**Qiang Li et al. · 2020 · P0 · enabling**  
IEEE Transactions on Robotics 36(6):1619–1634, 2020

[Paper / primary source](https://xplorestaging.ieee.org/document/9136877)

- **Problem:** Organize tactile information and its uses beyond raw sensor signals.
- **Inputs:** Survey of robot tactile signals, contact states, object properties and actions. **Conditioning:** Varies across reviewed perception/control methods.
- **Output:** Raw/contact/object/action information hierarchy.
- **World-model contribution (assessment):** A conceptual checklist for separating observation encoding, physical-state inference and action-level reasoning.
- **Reported evidence:** Reviews information types and robotics applications at four levels.
- **Limits / transfer assessment:** Survey taxonomy is not new experimental evidence for any one world-model architecture.
- **Repository connection:** Useful structure for defining missing contact/object/action outputs beyond the current spectral target.

Review: `full-text-sections`; Abstract; Sections I–III sensing/contact hierarchy; publisher metadata Verified 2026-10-11.

<a id="gelslim3-2021"></a>
### GelSlim3.0: High-Resolution Measurement of Shape, Force and Slip in a Compact Tactile-Sensing Finger

**Ian Taylor et al. · 2021 · P0 · enabling**  
ArXiv manuscript 2021; ICRA 2022

[Paper / primary source](https://arxiv.org/abs/2103.12269) · [Author project](https://mcubelab.github.io/gelslim/) · [Code](https://github.com/mcubelab/gelslim)

- **Problem:** Integrate geometry, distributed force and slip sensing in a compact finger.
- **Inputs:** Photometric geometry and tracked gel deformation. **Conditioning:** Calibrated optical/analytic measurement models.
- **Output:** Shape, contact 3D force distribution and incipient slip.
- **World-model contribution (assessment):** A practical measurement interface for physically interpretable contact state.
- **Reported evidence:** Presents real-time analytic measurement capabilities and reproducible sensor design/software.
- **Limits / transfer assessment:** Present-state reconstruction requires sensor calibration and does not predict future object motion.
- **Repository connection:** Strong candidate reference for collecting the missing geometry/force/slip information in Stage B.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="gelforce-2004"></a>
### Evaluation of a Vision-based Tactile Sensor

**Kazuto Kamiyama et al. · 2004 · P1 · enabling**  
ICRA 2004, pp. 1542–1547

[Paper / primary source](https://files.tachilab.org/publications/intconf2000/Kamiyama200408ICRA.pdf) · [Author project](https://tachilab.org/old/modules/projects/gelforce.html)

- **Problem:** Recover distributed force direction as well as magnitude.
- **Inputs:** Camera-tracked red/blue markers at two elastomer depths. **Conditioning:** Calibrated elastic response; uniform linear half-space assumptions.
- **Output:** Contact force-vector distribution.
- **World-model contribution (assessment):** An interpretable observation-to-traction bridge and early baseline for inverse sensor mechanics.
- **Reported evidence:** Evaluates marker localization, force magnitude/direction, spatial resolution and calculation timing.
- **Limits / transfer assessment:** Elastic reconstruction assumptions restrict transfer; no learned action-conditioned object dynamics.
- **Repository connection:** Future force-state sensing and sensor-response calibration; current acceleration spectra provide no comparable traction map.

Review: `full-text-sections`; Abstract; Section II force reconstruction and elastic assumptions Verified 2026-10-11.

<a id="biotac-2008"></a>
### Biomimetic Tactile Sensor Array

**Nicholas Wettels et al. · 2008 · P1 · enabling**  
Advanced Robotics 22(8):829–849, 2008

[Paper / primary source](https://viterbi.usc.edu/pdfs/gloeb/62200.pdf)

- **Problem:** Robust fingertip sensing with compliant contact and distributed receptors.
- **Inputs:** Impedance changes at electrodes beneath a fluid-filled silicone skin. **Conditioning:** Skin geometry, material and electrode configuration.
- **Output:** Spatial transduction responses containing force/contact information.
- **World-model contribution (assessment):** A complementary non-optical observation family; emphasizes modeling the sensor body as part of contact mechanics.
- **Reported evidence:** Characterizes dynamic range and preliminary spatial/temporal response after skin texturing.
- **Limits / transfer assessment:** This early paper is not the full later BioTac multimodal capability suite or a physical world model.
- **Repository connection:** Useful calibration and modality comparison for a future tactile-plus-force acquisition design.

Review: `full-text-sections`; Abstract; Sections 1 and 2.1 design concept Verified 2026-10-11.

<a id="retrographic-gelsight-2009"></a>
### Retrographic sensing for the measurement of surface texture and shape

**Micah K. Johnson and Edward H. Adelson · 2009 · P1 · enabling**  
CVPR 2009

[Paper / primary source](https://people.csail.mit.edu/kimo/publications/retrographic/sensor.pdf)

- **Problem:** Capture contact microgeometry across varying object reflectance.
- **Inputs:** RGB image of an illuminated reflective elastomer skin. **Conditioning:** Known lighting and calibrated photometric response.
- **Output:** Contacted surface normals and a 2.5D height reconstruction.
- **World-model contribution (assessment):** Foundational tactile geometry observation model and basis for optical sensor rendering.
- **Reported evidence:** Demonstrates single-frame surface reconstruction and changing contact deformation.
- **Limits / transfer assessment:** Contact-constrained height maps are not a complete 3D scene or action-conditioned motion prediction.
- **Repository connection:** Offers a geometry sensing route missing from the current vibration-only predictor.

Review: `full-text-sections`; Abstract; Section 1 sensor principle and scope Verified 2026-10-11.

<a id="improved-gelsight-2017"></a>
### Improved GelSight Tactile Sensor for Measuring Geometry and Slip

**Siyuan Dong et al. · 2017 · P1 · enabling**  
IROS 2017

[Paper / primary source](https://arxiv.org/abs/1708.00922)

- **Problem:** Improve geometric accuracy and slip sensing in a compact robot finger.
- **Inputs:** Lambertian membrane images, relative motion and shear distortion. **Conditioning:** Illumination and photometric stereo calibration.
- **Output:** Surface normals, height maps, translational/rotational slip detection.
- **World-model contribution (assessment):** More reliable geometry and contact-mode observations for state estimation.
- **Reported evidence:** Tests slip sensing with 37 everyday objects and grasp stabilization.
- **Limits / transfer assessment:** Sensor reconstruction/control demonstrations do not validate predictive forces or body-state rollouts.
- **Repository connection:** Candidate optical sensing design for adding state cues absent from current acceleration band powers.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="gelslim-2018"></a>
### GelSlim: A High-Resolution, Compact, Robust, and Calibrated Tactile-sensing Finger

**Elliott Donlon et al. · 2018 · P1 · enabling**  
IROS 2018

[Paper / primary source](https://arxiv.org/abs/1803.00628)

- **Problem:** Compact, durable and consistently calibrated optical touch for grasping.
- **Inputs:** Images of reflective gel through a redesigned optical path. **Conditioning:** Optics, illumination and material/fabrication calibration.
- **Output:** High-resolution tactile images with improved integration and durability.
- **World-model contribution (assessment):** Reproducible sensing infrastructure can reduce sensor-specific observation variation.
- **Reported evidence:** Evaluates signal-quality durability through more than 3,000 grasping experiments.
- **Limits / transfer assessment:** Hardware robustness is not calibrated friction identification or action-conditioned dynamics.
- **Repository connection:** Useful acquisition platform for future contact experiments; not a replacement for current spectral baselines.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="tactip-family-2018"></a>
### The TacTip Family: Soft Optical Tactile Sensors with 3D-Printed Biomimetic Morphologies

**Benjamin Ward-Cherrier et al. · 2018 · P1 · enabling**  
Soft Robotics 5(2):216–227, 2018

[Paper / primary source](https://pmc.ncbi.nlm.nih.gov/articles/PMC5905869/) · [Author project](https://softroboticstoolkit.com/tactip)

- **Problem:** Adapt compliant tactile sensing to different robot morphologies.
- **Inputs:** Camera-tracked internal pins displaced by skin deformation. **Conditioning:** Sensor morphology and learned localization calibration.
- **Output:** Local contact/location estimates across several sensor designs.
- **World-model contribution (assessment):** Demonstrates why embodiment and sensor morphology belong in observation calibration.
- **Reported evidence:** Four sensor morphologies attain submillimeter localization on a rolling-cylinder task.
- **Limits / transfer assessment:** Morphology-dependent contact localization does not identify object mechanics or forward dynamics.
- **Repository connection:** Alternative to photometric sensors for future contact-state sensing and embodiment-transfer controls.

Review: `full-text-sections`; Abstract; design/fabrication; Discussion and Conclusion Verified 2026-10-11.

<a id="soft-bubble-2019"></a>
### Soft-bubble: A highly compliant dense geometry tactile sensor for robot manipulation

**Alex Alspach et al. · 2019 · P1 · enabling**  
RoboSoft 2019 (presentation recorded in author arXiv metadata)

[Paper / primary source](https://arxiv.org/abs/1904.02252)

- **Problem:** Combine high compliance with dense geometry sensing.
- **Inputs:** Internal depth images of an inflated latex membrane. **Conditioning:** Known sensor/end-effector geometry and physical contact.
- **Output:** Deformation geometry; object classification, pose estimation/tracking.
- **World-model contribution (assessment):** Direct depth observations can constrain contact patches and compliant sensor states.
- **Reported evidence:** Demonstrates classification, pose/tracking and nonprehensile manipulation examples.
- **Limits / transfer assessment:** A compliant depth sensor and manipulation demonstration do not provide a learned physics engine.
- **Repository connection:** Candidate geometry channel if future experiments involve soft contact; mechanically different from the existing probe.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="digit-2020"></a>
### DIGIT: A Novel Design for a Low-Cost Compact High-Resolution Tactile Sensor with Application to In-Hand Manipulation

**Mike Lambeta et al. · 2020 · P1 · enabling**  
IEEE Robotics and Automation Letters 5(3):3838–3845, 2020

[Paper / primary source](https://arxiv.org/abs/2005.14679) · [Author project](https://digit.ml/digit.html) · [Code](https://github.com/facebookresearch/digit-interface)

- **Problem:** Affordable, compact and repeatably manufactured touch for multi-finger hands.
- **Inputs:** High-resolution optical images of gel deformation. **Conditioning:** Sensor observations in learned model-based manipulation controllers.
- **Output:** Tactile feedback enabling marble manipulation.
- **World-model contribution (assessment):** Widely reusable optical acquisition substrate and an early tactile model-based control demonstration.
- **Reported evidence:** Tests neural model-based controllers manipulating glass marbles in-hand.
- **Limits / transfer assessment:** Hardware/control evidence does not establish identifiable material parameters or broad forward physics generalization.
- **Repository connection:** Potential platform for extending the current spectral support/query framework to image observations.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="omnitact-2020"></a>
### OmniTact: A Multi-Directional High Resolution Touch Sensor

**Akhil Padmanabha et al. · 2020 · P1 · enabling**  
ICRA 2020 (acceptance recorded in author arXiv metadata)

[Paper / primary source](https://arxiv.org/abs/2003.06965) · [Author project](https://sites.google.com/berkeley.edu/omnitact) · [Code](https://github.com/s-tian/bench-press)

- **Problem:** Sense high-resolution contacts around a finger rather than only a flat tip.
- **Inputs:** Multiple micro-camera images of a gel-based skin. **Conditioning:** Learned image processing of multidirectional fingertip contacts.
- **Output:** Contact-angle estimates and touch-only insertion control.
- **World-model contribution (assessment):** Broadens the observable contact state for manipulation with side contacts.
- **Reported evidence:** Compares sensor designs in curved-finger angle estimation and electrical connector insertion.
- **Limits / transfer assessment:** State estimation and successful insertion are not a calibrated contact-state transition model.
- **Repository connection:** Useful for future geometry-aware embodiments; current texture data cannot emulate these multidirectional images.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="gelstereo-2021"></a>
### In-Hand Object Localization Using a Novel High-Resolution Visuotactile Sensor

**Shaowei Cui et al. · 2021 · P1 · enabling**  
IEEE Transactions on Industrial Electronics 69(6):6015–6025, 2022; online June 2021

[Paper / primary source](https://ieeexplore.ieee.org/document/9464700/)

- **Problem:** Recover contact geometry for accurate in-hand localization.
- **Inputs:** Stereo tactile images of the GelStereo elastomer. **Conditioning:** Stereo calibration, object geometry and probabilistic point-set registration.
- **Output:** Contact point clouds and in-hand object pose.
- **World-model contribution (assessment):** Supplies measurable geometry/state constraints and an alternative optical observation model.
- **Reported evidence:** Evaluates tactile point clouds, localization and insertion of small parts.
- **Limits / transfer assessment:** Geometry/localization is not force-law identification or sequential world dynamics.
- **Repository connection:** Possible geometry observation channel absent from current acceleration-based support latent.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="insight-2021"></a>
### A soft thumb-sized vision-based sensor with accurate all-round force perception

**Huanbo Sun et al. · 2021 · P1 · enabling**  
ArXiv manuscript 2021; Nature Machine Intelligence 4:135–145, 2022

[Paper / primary source](https://arxiv.org/abs/2111.05934)

- **Problem:** Accurate distributed force sensing around a compliant thumb.
- **Inputs:** Monocular images of an over-molded soft shell and structured lighting. **Conditioning:** Supervised calibration with independent force/torque and known contact locations.
- **Output:** Spatial normal/shear force distribution.
- **World-model contribution (assessment):** A force-state observation model with an explicit ground-truth measurement interface.
- **Reported evidence:** Tests force/location inference; reports qualitative multiple-contact results.
- **Limits / transfer assessment:** Distribution labels use a spatial approximation; fast motion can introduce inertial deformation artifacts; no forward world dynamics.
- **Repository connection:** Highlights independent-force supervision and sensor-body dynamics missing from the existing spectral latent.

Review: `full-text-sections`; Abstract; Nature methods/calibration, performance and discussion Verified 2026-10-11.

<a id="reskin-2021"></a>
### ReSkin: versatile, replaceable, lasting tactile skins

**Raunaq Bhirangi et al. · 2021 · P1 · enabling**  
CoRL 2021; proceedings published as PMLR 164:587–597 in 2022

[Paper / primary source](https://proceedings.mlr.press/v164/bhirangi22a.html) · [Author project](https://reskin.dev/) · [Code](https://github.com/raunaqbhirangi/reskin_sensor)

- **Problem:** Soft sensor replacement, wear and cross-sample calibration variation.
- **Inputs:** Magnetic-field measurements beneath replaceable magnetic elastomer. **Conditioning:** Learned sensor-response calibration and self-supervised adaptation.
- **Output:** Contact/force-related measurements robust across sensor variation.
- **World-model contribution (assessment):** Provides an inexpensive non-optical modality and a concrete sensor-transfer calibration strategy.
- **Reported evidence:** Develops response models addressing fabrication/time variation and small-data adaptation.
- **Limits / transfer assessment:** A learned magnetic response map is not an action-conditioned object dynamics model.
- **Repository connection:** Alternative acquisition modality; informs replacement/drift controls for future brief-touch experiments.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="densetact-2022"></a>
### DenseTact: Optical Tactile Sensor for Dense Shape Reconstruction

**Won Kyung Do and Monroe Kennedy III · 2022 · P1 · enabling**  
ArXiv manuscript 2022; ICRA 2022 author citation

[Paper / primary source](https://arxiv.org/abs/2201.01367) · [Author project](https://github.com/armlabstanford/DenseTact) · [Data / release](https://github.com/armlabstanford/DenseTact)

- **Problem:** Compact high-resolution reconstruction of a curved soft fingertip.
- **Inputs:** Internal fisheye-camera image. **Conditioning:** Supervised neural calibration of surface deformation.
- **Output:** Dense 3D sensor-surface reconstruction.
- **World-model contribution (assessment):** A data-driven observation-to-geometry route for curved contacts.
- **Reported evidence:** Demonstrates real-time neural deformation estimation.
- **Limits / transfer assessment:** Reconstruction fidelity does not validate a material law or action-conditioned dynamics.
- **Repository connection:** Extends potential support observations to dense geometry; needs a new dataset and calibrated sensor.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="densetact2-2022"></a>
### DenseTact 2.0: Optical Tactile Sensor for Shape and Force Reconstruction

**Won Kyung Do et al. · 2022 · P1 · enabling**  
ArXiv manuscript 2022; ICRA 2023, pp. 12549–12555

[Paper / primary source](https://arxiv.org/abs/2209.10122)

- **Problem:** Calibrated shape and force sensing in a soft fingertip.
- **Inputs:** Images of deformed sensor surface. **Conditioning:** Neural reconstruction and transfer calibration across fingers.
- **Output:** Surface shape and six-axis wrench.
- **World-model contribution (assessment):** Calibrated wrench/geometry observations can supervise contact-state inference and sensor transfer.
- **Reported evidence:** Evaluates shape/wrench reconstruction and reduced-data transfer calibration.
- **Limits / transfer assessment:** Net wrench does not determine every local traction field; no action-conditioned physical rollout is established.
- **Repository connection:** Potential force-label acquisition reference for a new mechanical dataset.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="tac3d-2022"></a>
### Tac3D: A Novel Vision-based Tactile Sensor for Measuring Forces Distribution and Estimating Friction Coefficient Distribution

**Lunwei Zhang et al. · 2022 · P1 · enabling**  
ArXiv preprint, February 2022; no later venue verified

[Paper / primary source](https://arxiv.org/abs/2202.06211)

- **Problem:** Measure 3D geometry/forces and spatial friction information.
- **Inputs:** Virtual-binocular tactile images of contact deformation. **Conditioning:** Contact surface/force reconstruction plus global sensor pose.
- **Output:** Shape, force distribution and friction-coefficient maps.
- **World-model contribution (assessment):** Connects tactile state estimates with spatially varying contact parameters.
- **Reported evidence:** Reconstructs object shape with friction distribution in reported experiments.
- **Limits / transfer assessment:** Estimated friction maps do not establish a general transient friction law or predictive multi-step dynamics.
- **Repository connection:** Relevant mechanical-state precedent; the current repository has no equivalent per-scan tangential-force identification.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="digit360-2024"></a>
### Digitizing Touch with an Artificial Multimodal Fingertip

**Mike Lambeta et al. · 2024 · P1 · enabling**  
ArXiv preprint, November 2024; official repository cites arXiv

[Paper / primary source](https://arxiv.org/abs/2411.02479) · [Author project](https://digit.ml/) · [Code](https://github.com/facebookresearch/digit360)

- **Problem:** Digitize rich touch through a compliant hemispherical fingertip.
- **Inputs:** Optical deformation plus vibration, force-related, thermal and chemical channels. **Conditioning:** Calibrated sensor platform and on-device learned processing.
- **Output:** Multimodal tactile readings and sensing features.
- **World-model contribution (assessment):** Potentially combines geometry and high-frequency vibration observations in one embodiment.
- **Reported evidence:** Characterizes spatial/force/vibration sensing and multimodal capabilities.
- **Limits / transfer assessment:** Reported sensor resolutions are not physical-world-model prediction accuracy; substantial calibration/hardware requirements remain.
- **Repository connection:** Especially relevant to connecting the current vibration study with future optical and force channels.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="gelslim4-2024"></a>
### GelSlim 4.0: Focusing on Touch and Reproducibility

**Andrea Sipos et al. · 2024 · P1 · enabling**  
ArXiv preprint 2024; author page says submitted to ICRA 2025, acceptance not verified

[Paper / primary source](https://arxiv.org/abs/2409.19770) · [Author project](https://www.mmintlab.com/research/gelslim-4-0/) · [Code](https://github.com/MMintLab/gelslim_depth)

- **Problem:** Make optical touch hardware easier to reproduce and repair.
- **Inputs:** RGB images and deformation/shear fields. **Conditioning:** Simplified manufacturing, optical design and perception calibration.
- **Output:** Depth and shear estimates; manufacturing/perception resources.
- **World-model contribution (assessment):** Helps control hardware variation in reproducible mechanics and sensor-renderer experiments.
- **Reported evidence:** Evaluates reproducibility through human usability testing.
- **Limits / transfer assessment:** Usability and depth/shear estimation do not establish calibrated forces or predictive dynamics.
- **Repository connection:** Practical successor sensor candidate for a future synchronized collection setup.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="geltip-2020"></a>
### GelTip: A Finger-shaped Optical Tactile Sensor for Robotic Manipulation

**Daniel Fernandes Gomes et al. · 2020 · P2 · enabling**  
IROS 2020; author-hosted IROS manuscript

[Paper / primary source](https://arxiv.org/abs/2008.05404) · [Author project](https://danfergo.github.io/geltip/)

- **Problem:** Observe contacts anywhere along a finger-shaped surface.
- **Inputs:** Optical images of opaque elastomer deformation over a transparent rigid body. **Conditioning:** Finger geometry and contact location calibration.
- **Output:** Contact localization across the sensing surface.
- **World-model contribution (assessment):** Provides observations of otherwise unobserved side contacts in clutter.
- **Reported evidence:** Evaluates localization at different locations on the finger.
- **Limits / transfer assessment:** Localization evidence does not establish force calibration or forward dynamics.
- **Repository connection:** Embodiment option for future contact-state work, less immediately relevant to flat sliding vibration prediction.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="force-state-identification"></a>
## Contact state, force and parameter identification

Inference of force, slip, object pose or effective contact properties. These components connect tactile readings to the physical state needed by a solver.

| Paper | Year | Priority / relevance | Output |
| --- | --- | --- | --- |
| [Measurement of Shear and Slip with a GelSight Tactile Sensor](#gelsight-shear-slip-2015) | 2015 | P0 / direct | Contact-state and incipient-slip estimates. |
| [Dense Tactile Force Distribution Estimation using GelSlim and inverse FEM](#gelslim-inverse-fem-2018) | 2018 | P0 / direct | Dense contact-force distribution. |
| [TacTID: High-Performance Visuo-Tactile Sensor-Based Terrain Identification for Legged Robots](#tactid-2024) | 2024 | P0 / direct | Sliding friction coefficient and effective stiffness estimates. |
| [Shape-independent Hardness Estimation Using Deep Learning and a GelSight Tactile Sensor](#gelsight-hardness-2017) | 2017 | P1 / direct | Shore 00 hardness estimates. |
| [Learning Tactile Models for Factor Graph-based Estimation](#tactile-factor-graph-2020) | 2020 | P1 / direct | Relative sensor pose and object-state estimates. |
| [Learning Dynamics Models of Contacts from Tactile Sensors](#contact-inverse-dynamics-2015) | 2015 | P2 / direct | Joint torques including external-contact effects. |

<a id="gelsight-shear-slip-2015"></a>
### Measurement of Shear and Slip with a GelSight Tactile Sensor

**Wenzhen Yuan et al. · 2015 · P0 · direct**  
ICRA 2015.

[Paper / primary source](https://people.csail.mit.edu/yuan_wz/GelSight1/ICRA15_2740_FI.pdf)

- **Problem:** Observing tangential contact and incipient slip.
- **Inputs:** Sequences of GelSight elastomer/marker images. **Conditioning:** Applied normal, shear and torsional loading.
- **Output:** Contact-state and incipient-slip estimates.
- **World-model contribution (assessment):** Motivates an explicit stick/partial-slip/sliding state rather than a single friction scalar.
- **Reported evidence:** Gripper-like experiments detect stable contact and incipient slip from deformation.
- **Limits / transfer assessment:** Slip recognition is not a universal calibrated force law; gel response, contact patch and image rate constrain inference.
- **Repository connection:** Confirm actual sliding before using tangential/normal force ratios as kinetic-friction labels.

Review: `full-text-sections`; Abstract; contact-deformation and incipient-slip methods Verified 2026-10-11.

<a id="gelslim-inverse-fem-2018"></a>
### Dense Tactile Force Distribution Estimation using GelSlim and inverse FEM

**Daolin Ma et al. · 2018 · P0 · direct**  
First arXiv 2018; ICRA 2019 venue title: Dense Tactile Force Estimation using GelSlim and inverse FEM.

[Paper / primary source](https://arxiv.org/abs/1810.04621) · [Author project](https://mcube.mit.edu/research/gelslim.html)

- **Problem:** Recovering contact force from optical deformation.
- **Inputs:** GelSlim marker displacement fields. **Conditioning:** Calibrated gel finite-element model.
- **Output:** Dense contact-force distribution.
- **World-model contribution (assessment):** Supplies a mechanics-aware tactile-to-force observation/inference bridge.
- **Reported evidence:** Inverse FEM reconstructs spatial forces; real experiments compare reconstructed resultant force against a force/torque sensor.
- **Limits / transfer assessment:** Dense force ground truth is difficult; resultant-force agreement does not independently validate every local force. Gel constitutive parameters and boundary assumptions must transfer.
- **Repository connection:** Choose independent force supervision for any future optical-sensor version.

Review: `abstract-and-metadata`; Abstract; author project publication listing Verified 2026-10-11.

<a id="tactid-2024"></a>
### TacTID: High-Performance Visuo-Tactile Sensor-Based Terrain Identification for Legged Robots

**Ziwu Song et al. · 2024 · P0 · direct**  
IEEE Sensors Journal 24(16), 2024; DOI 10.1109/JSEN.2024.3417514.

[Paper / primary source](https://charon-bo.github.io/assets/PDF/TacTID.pdf)

- **Problem:** Inferring terrain friction and effective stiffness.
- **Inputs:** Embedded optical marker deformation and calibrated contact-force estimates. **Conditioning:** Sliding/terrain contact and deformation geometry.
- **Output:** Sliding friction coefficient and effective stiffness estimates.
- **World-model contribution (assessment):** Direct precedent for a mechanical parameter inference interface.
- **Reported evidence:** Independent force-sensor comparison, silicone stiffness experiments and quadruped terrain identification.
- **Limits / transfer assessment:** Sensor-specific calibration and friction-cone sampling assumptions matter. Effective stiffness mixes contacting bodies; results do not establish half-second acceleration-only inference or validated motion rollouts.
- **Repository connection:** Design force-ground-truth and slip-confirmation checks before making friction claims.

Review: `full-text-sections`; Sections II-III: force calibration and terrain identification; Section IV experiments Verified 2026-10-11.

<a id="gelsight-hardness-2017"></a>
### Shape-independent Hardness Estimation Using Deep Learning and a GelSight Tactile Sensor

**Wenzhen Yuan et al. · 2017 · P1 · direct**  
ICRA 2017.

[Paper / primary source](https://arxiv.org/abs/1704.03955)

- **Problem:** Hardness inference despite varying contact shape.
- **Inputs:** GelSight deformation images during pressing. **Conditioning:** Loosely controlled manual/robotic contact.
- **Output:** Shore 00 hardness estimates.
- **World-model contribution (assessment):** Shows tactile deformation can identify a material-related quantity for parameter inference.
- **Reported evidence:** Learning estimates hardness across differently shaped objects under uneven, unknown force/trajectory conditions.
- **Limits / transfer assessment:** Hardness scale is not an identified stiffness/damping law or Young's modulus. Sensor and object deformation can be confounded.
- **Repository connection:** Add compliance only with indentation and fixture/sensor calibration.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="tactile-factor-graph-2020"></a>
### Learning Tactile Models for Factor Graph-based Estimation

**Paloma Sodhi et al. · 2020 · P1 · direct**  
First arXiv 2020; accepted ICRA 2021.

[Paper / primary source](https://arxiv.org/abs/2012.03768)

- **Problem:** Estimating occluded object pose during pushing.
- **Inputs:** Pairs/history of optical tactile images. **Conditioning:** Physics and geometric factors in a factor graph.
- **Output:** Relative sensor pose and object-state estimates.
- **World-model contribution (assessment):** Separates learned observation likelihoods from physical state constraints.
- **Reported evidence:** Real planar-pushing tracking across three shapes using tactile feedback.
- **Limits / transfer assessment:** State estimation uses contact history and supervised relative-pose data; it does not identify a new surface's friction law.
- **Repository connection:** Add belief/state inference when extending spectral prediction to object motion.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="contact-inverse-dynamics-2015"></a>
### Learning Dynamics Models of Contacts from Tactile Sensors

**Roberto Calandra et al. · 2015 · P2 · direct**  
ICRA 2015 Get in touch! tactile/force workshop paper; main-track conference acceptance not claimed.

[Paper / primary source](https://www.ias.informatik.tu-darmstadt.de/uploads/Workshops/ICRA2015TactileForce/12_icra_ws_tactileforce.pdf) · [Author project](https://www.ias.informatik.tu-darmstadt.de/Workshops/ICRA2015TactileForce)

- **Problem:** Predict robot inverse dynamics in the presence of external contacts.
- **Inputs:** Raw tactile/force-torque data and joint position, velocity and acceleration. **Conditioning:** Current robot kinematic state and contact sensor readings.
- **Output:** Joint torques including external-contact effects.
- **World-model contribution (assessment):** An early whole-body contact-learning precedent using Gaussian-process mixtures of experts.
- **Reported evidence:** The workshop paper reports iCub contact experiments and comparisons with force/torque-based dynamics models.
- **Limits / transfer assessment:** Inverse torque prediction is different from forward action-conditioned rollouts. Current measured contact input does not establish brief new-surface calibration or an identifiable material force law.
- **Repository connection:** A later extension beyond fingertip spectra; maintain explicit observation/inverse/forward interfaces.

Review: `full-text-sections`; Abstract; inverse-dynamics problem formulation and contact-learning approach. Verified 2026-10-11.

<a id="datasets-texture-rendering"></a>
## Texture datasets and vibration observation models

Closest to the current acceleration-spectrum task: measured sensory response, action conditioning, classical texture models and generation. The pushing dataset supplies separate motion/force evidence.

| Paper | Year | Priority / relevance | Output |
| --- | --- | --- | --- |
| [Modeling and Rendering Realistic Textures from Unconstrained Tool-Surface Interactions](#culbertson-ar-textures-2014) | 2014 | P0 / direct | Piecewise autoregressive models and generated vibrations. |
| [One Hundred Data-Driven Haptic Texture Models and Open-Source Methods for Rendering on 3D Objects](#hatt-2014) | 2014 | P0 / direct | 100 texture/friction models and rendering methods. |
| [More than a Million Ways to Be Pushed: A High-Fidelity Experimental Dataset of Planar Pushing](#planar-pushing-dataset-2016) | 2016 | P0 / enabling | Experimental motion/force trajectories and friction-variability analysis. |
| [Learning an Action-Conditional Model for Haptic Texture Generation](#heravi-action-conditional-texture) | 2019 | P0 / direct | Next short-window acceleration Fourier magnitudes; reconstructed vibration. |
| [Development and Evaluation of a Learning-based Model for Real-time Haptic Texture Rendering](#heravi-real-time-texture) | 2022 | P0 / direct | Acceleration spectrum followed by causal waveform reconstruction. |
| [Cluster Haptic Texture Dataset: Haptic Texture Dataset with Varied Velocity-Direction Sliding Contacts](#cluster-haptic-texture-2024) | 2024 | P0 / direct | A dataset and texture/motion classification demonstrations. |
| [HaptoFlow: High-Fidelity Real-Time Vibrotactile Generation via Flow Matching for Virtual Reality](#haptoflow) | 2026 | P0 / direct | Autoregressive waveform segments through flow matching in an audio-codec latent space. |
| [Creating Realistic Virtual Textures from Contact Acceleration Data](#romano-texture-2012) | 2012 | P1 / direct | Frequency-domain texture models and stylus vibrations. |
| [A Haptic Texture Database for Tool-mediated Texture Recognition and Classification](#lmt-texture-database-2014) | 2014 | P1 / enabling | A texture database and recognition/classification setting. |
| [Should Haptic Texture Vibrations Respond to User Force and Speed?](#force-speed-perception-2015) | 2015 | P1 / adjacent | Perceived realism comparisons. |
| [Handling Scan-time Parameters in Haptic Surface Classification](#scan-time-features-2017) | 2017 | P1 / enabling | Surface classification and feature-condition correlations. |

<a id="culbertson-ar-textures-2014"></a>
### Modeling and Rendering Realistic Textures from Unconstrained Tool-Surface Interactions

**Heather Culbertson et al. · 2014 · P0 · direct**  
IEEE Transactions on Haptics 7(3), 2014.

[Paper / primary source](https://pubmed.ncbi.nlm.nih.gov/25248220/) · [Author project](https://mlgh.net/publication/culbertson-2014-apr/)

- **Problem:** Speed/load-responsive texture rendering from freehand data.
- **Inputs:** Tool acceleration with measured speed and normal force. **Conditioning:** Force and speed indexed through interpolation.
- **Output:** Piecewise autoregressive models and generated vibrations.
- **World-model contribution (assessment):** A transparent action-conditioned observation baseline with explicit interpolation.
- **Reported evidence:** TexturePad human evaluation supports roughness reproduction; the abstract reports hardness and slipperiness require additional modeling.
- **Limits / transfer assessment:** One model set per recorded texture; no brief unseen-surface identification or validated mechanical rollout.
- **Repository connection:** Compare retrieval and speed rescaling with force/speed-conditioned AR modeling.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="hatt-2014"></a>
### One Hundred Data-Driven Haptic Texture Models and Open-Source Methods for Rendering on 3D Objects

**Heather Culbertson et al. · 2014 · P0 · direct**  
IEEE Haptics Symposium 2014; HaTT manual released 12 February 2014.

[Paper / primary source](https://is.mpg.de/hi/publications/culbertson14-hs-texture) · [Author project](https://heatherculbertson.wixsite.com/home/research) · [Data / release](https://repository.upenn.edu/bitstreams/960863b6-df14-4770-9068-b1b2bf6a50f1/download)

- **Problem:** Reusable measurement-based texture rendering.
- **Inputs:** Recorded tool acceleration, force, position and texture images. **Conditioning:** Measured scanning speed and applied force.
- **Output:** 100 texture/friction models and rendering methods.
- **World-model contribution (assessment):** Provides a paired-channel candidate and strong classical observation-model baseline.
- **Reported evidence:** HaTT packages recorded interactions, texture models and rendering resources; manual specifies model force/speed coordinates.
- **Limits / transfer assessment:** Freehand steel-tip contact differs from Cluster's urethane probe. Controlled query coverage, sensor calibration, access and archive/license contents need inspection before use. Perceptual rendering does not validate free-body motion.
- **Repository connection:** Prioritize feasibility checking for the proposed force study.

Review: `abstract-and-metadata`; Author publication record; indexed HaTT manual abstract and model-file tables Verified 2026-10-11.

<a id="planar-pushing-dataset-2016"></a>
### More than a Million Ways to Be Pushed: A High-Fidelity Experimental Dataset of Planar Pushing

**Kuan-Ting Yu et al. · 2016 · P0 · enabling**  
IROS 2016; first arXiv April 2016.

[Paper / primary source](https://arxiv.org/abs/1604.04038) · [Author project](https://web.mit.edu/mcube/push-dataset/) · [Data / release](https://web.mit.edu/mcube/push-dataset/)

- **Problem:** Testing assumptions in frictional pushing models.
- **Inputs:** Pusher/object poses and planar force/torque. **Conditioning:** Surface, object shape, contact, direction, speed and acceleration.
- **Output:** Experimental motion/force trajectories and friction-variability analysis.
- **World-model contribution (assessment):** A separate benchmark for forward physical dynamics and residual error.
- **Reported evidence:** Varied pushing experiments and repeated trials expose variability in common frictional assumptions.
- **Limits / transfer assessment:** No paired high-frequency texture touch. Author release explicitly notes unsynchronized measurement streams; resampling requires alignment checks.
- **Repository connection:** Validate a mechanics module separately; do not treat it as paired Cluster force targets.

Review: `full-text-sections`; Paper abstract; author release measurement schema and synchronization warning Verified 2026-10-11.

<a id="heravi-action-conditional-texture"></a>
### Learning an Action-Conditional Model for Haptic Texture Generation

**Negin Heravi et al. · 2019 · P0 · direct**  
ICRA 2020; first arXiv manuscript September 2019; revised October 2020.

[Paper / primary source](https://arxiv.org/html/1909.13025) · [Author project](https://sites.google.com/stanford.edu/haptic-texture-generation) · [Data / release](https://sites.google.com/stanford.edu/haptic-texture-generation)

- **Problem:** Predict texture vibrations across varying interaction conditions.
- **Inputs:** GelSight image of a pressed surface; measured acceleration for supervision. **Conditioning:** Recent applied-force and stroking-speed history.
- **Output:** Next short-window acceleration Fourier magnitudes; reconstructed vibration.
- **World-model contribution (assessment):** Direct precedent for the sensor renderer G; separates surface representation from interaction inputs.
- **Reported evidence:** Quantitative tests vary images and force/speed on training materials; unseen-material latent placement is qualitative.
- **Limits / transfer assessment:** Predicts vibration, not object motion or contact forces. Unknown-material waveform accuracy is not established; probe/grip mechanics remain confounds.
- **Repository connection:** Closest architecture to the current Cluster spectrum task; retain retrieval and held-condition baselines.

Review: `full-text-sections`; Sections III and V-C through V-F; arXiv submission history. Verified 2026-10-11.

<a id="heravi-real-time-texture"></a>
### Development and Evaluation of a Learning-based Model for Real-time Haptic Texture Rendering

**Negin Heravi et al. · 2022 · P0 · direct**  
IEEE Transactions on Haptics 17(4), 705–716, 2024; DOI 10.1109/TOH.2024.3382258; first arXiv December 2022.

[Paper / primary source](https://arxiv.org/html/2212.13332)

- **Problem:** Generate causal, responsive tactile texture vibrations.
- **Inputs:** GelSight surface image; measured texture acceleration. **Conditioning:** Applied force and sliding speed.
- **Output:** Acceleration spectrum followed by causal waveform reconstruction.
- **World-model contribution (assessment):** Practical real-time G architecture and explicit retrieval fallback for unfamiliar surfaces.
- **Reported evidence:** Technical and perceptual rendering evaluation; unfamiliar materials use nearest training-surface representations because raw extrapolation is unstable.
- **Limits / transfer assessment:** Does not identify calibrated friction, compliance, or motion dynamics. Unseen-material rendering depends on substitution.
- **Repository connection:** Supports retaining nearest-neighbor baselines and distinguishing unseen-surface inference from renderer generalization.

Review: `full-text-sections`; Sections III-A/B, IV-B4, V4, VI; arXiv and publisher metadata. Verified 2026-10-11.

<a id="cluster-haptic-texture-2024"></a>
### Cluster Haptic Texture Dataset: Haptic Texture Dataset with Varied Velocity-Direction Sliding Contacts

**Michikuni Eguchi et al. · 2024 · P0 · direct**  
arXiv manuscript, first 2024; reviewed v4 (2025).

[Paper / primary source](https://arxiv.org/html/2407.16206v4) · [Author project](https://github.com/cluster-lab/Cluster-Haptic-Texture-Dataset) · [Code](https://github.com/cluster-lab/Cluster-Haptic-Texture-Dataset) · [Data / release](https://github.com/cluster-lab/Cluster-Haptic-Texture-Dataset)

- **Problem:** Controlled variation of sliding texture observations.
- **Inputs:** Acceleration, normal load, position, audio and surface images. **Conditioning:** Speed, direction, nominal load and repetition.
- **Output:** A dataset and texture/motion classification demonstrations.
- **World-model contribution (assessment):** Supports action-conditioned sensor prediction and condition-held-out evaluation.
- **Reported evidence:** 118 surfaces with machine-controlled sliding across five speeds and eight directions.
- **Limits / transfer assessment:** No synchronized per-scan tangential-force or indentation targets for this project's mechanics milestone. Host timestamps require independent acquisition-clock verification; nominal load is not continuous force control.
- **Repository connection:** The current dataset; retain logged-coordinate scope and specimen reservation.

Review: `full-text-sections`; Methods: hardware, acquisition, measurement procedure and friction measurement Verified 2026-10-11.

<a id="haptoflow"></a>
### HaptoFlow: High-Fidelity Real-Time Vibrotactile Generation via Flow Matching for Virtual Reality

**Michikuni Eguchi et al. · 2026 · P0 · direct**  
arXiv:2608.01974, August 2026 preprint.

[Paper / primary source](https://arxiv.org/html/2608.01974v1) · [Author project](https://tamago117.github.io/HaptoFlow/) · [Data / release](https://huggingface.co/datasets/tamago117/cluster-haptic-texture-dataset)

- **Problem:** Generate low-latency texture vibration waveforms.
- **Inputs:** Cluster acceleration waveforms; previous generated segment. **Conditioning:** Material label, stroking velocity, and applied force.
- **Output:** Autoregressive waveform segments through flow matching in an audio-codec latent space.
- **World-model contribution (assessment):** Modern G alternative to spectrum prediction; useful causal waveform and actuator evaluation design.
- **Reported evidence:** Technical reproduction/latency and VR perceptual experiments on a selected subset of Cluster materials.
- **Limits / transfer assessment:** Discrete training-material conditioning does not infer unfamiliar material physics; actuator bandwidth/compliance and material-dependent perceptual errors remain.
- **Repository connection:** Direct comparison candidate after matching Cluster splits, materials, sensor axes, and interaction coverage.

Review: `full-text-sections`; Sections 2.2, 5.2, and 7; official model card. Verified 2026-10-11.

<a id="romano-texture-2012"></a>
### Creating Realistic Virtual Textures from Contact Acceleration Data

**Joseph M. Romano and Katherine J. Kuchenbecker · 2012 · P1 · direct**  
IEEE Transactions on Haptics 5(2), 2012; DOI 10.1109/TOH.2011.38. Earlier online date not independently established here.

[Paper / primary source](https://pubmed.ncbi.nlm.nih.gov/26964067/)

- **Problem:** Reconstructing fine texture feedback from recorded interactions.
- **Inputs:** Three-axis tool acceleration, position and force. **Conditioning:** Recorded interaction conditions and rendering motion.
- **Output:** Frequency-domain texture models and stylus vibrations.
- **World-model contribution (assessment):** Motivates a separate spectral/waveform observation model.
- **Reported evidence:** Linear predictive coding and dimensional reduction support real-time vibration rendering evaluated with human subjects.
- **Limits / transfer assessment:** Perceptual realism is different from force accuracy or dynamic consistency; tool and actuator response are part of the signal.
- **Repository connection:** Add a classical autoregressive texture baseline before scaling the encoder.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="lmt-texture-database-2014"></a>
### A Haptic Texture Database for Tool-mediated Texture Recognition and Classification

**Matti Strese et al. · 2014 · P1 · enabling**  
IEEE HAVE 2014.

[Paper / primary source](https://www.ce.cit.tum.de/en/lmt/forschung/datensaetze/texture-database/) · [Author project](https://zeus.lkn.ei.tum.de/downloads/texture/) · [Data / release](https://zeus.lkn.ei.tum.de/downloads/texture/)

- **Problem:** Texture features robust to scan conditions.
- **Inputs:** Tool acceleration from controlled scans and human exploration. **Conditioning:** Scan force and speed variation.
- **Output:** A texture database and recognition/classification setting.
- **World-model contribution (assessment):** Offers a sensor-domain shift and feature-invariance benchmark.
- **Reported evidence:** The author dataset page describes 69 textures and controlled plus freehand exploration; later releases contain other material counts/modalities.
- **Limits / transfer assessment:** Different releases have different schemas. Verify force calibration, motion availability and timestamps in the specific archive; labels/classification do not establish mechanics.
- **Repository connection:** Use for external observation-model validation after Cluster's study is locked.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="force-speed-perception-2015"></a>
### Should Haptic Texture Vibrations Respond to User Force and Speed?

**Heather Culbertson and Katherine J. Kuchenbecker · 2015 · P1 · adjacent**  
IEEE World Haptics Conference 2015.

[Paper / primary source](https://is.mpg.de/hi/publications/culbertson15-whc-vibrations)

- **Problem:** Which interaction variables improve rendered texture realism?
- **Inputs:** Recorded texture vibration signals and human judgments. **Conditioning:** Speed-responsive, force-responsive and ablated rendering.
- **Output:** Perceived realism comparisons.
- **World-model contribution (assessment):** Guides sensor-renderer ablations and separates perceptual objectives from mechanics.
- **Reported evidence:** The authors' abstract reports reduced realism without speed responsiveness; removing force responsiveness did not significantly reduce realism in their study.
- **Limits / transfer assessment:** This perceptual result cannot justify removing normal load from a physical friction law.
- **Repository connection:** Use as motivation for action-conditioning ablations; retain force variables for mechanics.

Review: `abstract-and-metadata`; Author publication metadata; original abstract indexed by publisher/search Verified 2026-10-11.

<a id="scan-time-features-2017"></a>
### Handling Scan-time Parameters in Haptic Surface Classification

**Alex Burka and Katherine J. Kuchenbecker · 2017 · P1 · enabling**  
IEEE World Haptics Conference 2017.

[Paper / primary source](https://www.alexburka.com/penn/proton/whc2017.pdf)

- **Problem:** Separating material identity from exploration conditions.
- **Inputs:** Measured surface force/vibration and scan parameters. **Conditioning:** Scan-dependent versus scan-free feature representations.
- **Output:** Surface classification and feature-condition correlations.
- **World-model contribution (assessment):** Helps design a latent representation separating identity from the actions needed for prediction.
- **Reported evidence:** Compares features on the 69-surface LMT set and new Proton Pack recordings.
- **Limits / transfer assessment:** Classification benefits from invariance; predicting action-dependent signals requires retaining conditions. This paper does not learn a dynamics law.
- **Repository connection:** Audit whether features remove useful action information or retain apparatus shortcuts.

Review: `full-text-sections`; Abstract; introduction on scan-time conditioning Verified 2026-10-11.

<a id="representations-multimodal"></a>
## Tactile representations and multisensory datasets

Transferable encoders, sensory assets and benchmarks. Useful inference priors do not automatically identify a contact law or predict action-conditioned physical evolution.

| Paper | Year | Priority / relevance | Output |
| --- | --- | --- | --- |
| [Sparsh: Self-supervised touch representations for vision-based tactile sensing](#sparsh-tacbench) | 2024 | P0 / enabling | Embeddings; force, slip, pose, grasp, textile, and manipulation outputs. |
| [AnyTouch 2: General Optical Tactile Representation Learning For Dynamic Tactile Perception](#anytouch-2) | 2025 | P0 / enabling | Representations; force and temporal-force estimates; manipulation features. |
| [Making Sense of Vision and Touch: Self-Supervised Learning of Multimodal Representations for Contact-Rich Tasks](#making-sense-vision-touch) | 2018 | P1 / enabling | Optical flow, next-cycle contact occurrence, and modality concurrency; features for reinforcement learning. |
| [On Explainability and Sensor-Adaptability of a Robot Tactile Texture Representation Using a Two-Stage Recurrent Networks](#exsarn) | 2021 | P1 / enabling | Recurrent texture representations and classification. |
| [ObjectFolder 2.0: A Multisensory Object Dataset for Sim2Real Transfer](#objectfolder-2) | 2022 | P1 / enabling | Multisensory renderings; scale, contact-location, and shape estimates. |
| [Touch and Go: Learning from Human-Collected Vision and Touch](#touch-and-go) | 2022 | P1 / enabling | Cross-modal embeddings, tactile-driven image stylization, and tactile prediction. |
| [The ObjectFolder Benchmark: Multisensory Learning with Neural and Real Objects](#objectfolder-benchmark) | 2023 | P1 / direct | Perception outputs and learned forward predictions for multisensory MPC. |
| [Transferable Tactile Transformers for Representation Learning Across Diverse Sensors and Tasks](#t3) | 2024 | P1 / enabling | Reusable tactile embeddings and supervised task outputs. |
| [AnyTouch: Learning Unified Static-Dynamic Representation across Multiple Visuo-tactile Sensors](#anytouch) | 2025 | P1 / enabling | Sensor-agnostic features, reconstructed videos, and auxiliary next-frame prediction. |
| [Tactile Beyond Pixels: Multisensory Touch Representations for Robot Manipulation](#sparsh-x) | 2025 | P1 / enabling | Touch embeddings for physical perception and manipulation. |
| [Learning the signatures of the human grasp using a scalable tactile glove](#stag) | 2019 | P2 / enabling | Object identity, weight estimates, and grasp/hand-pressure structure. |
| [Connecting Touch and Vision via Cross-Modal Prediction](#visgel) | 2019 | P2 / enabling | Generated touch from vision and vision from touch. |
| [ObjectFolder: A Dataset of Objects with Implicit Visual, Auditory, and Tactile Representations](#objectfolder) | 2021 | P2 / enabling | Rendered modalities and representations for object tasks. |
| [Binding Touch to Everything: Learning Unified Multimodal Tactile Representations](#unitouch) | 2024 | P2 / enabling | Unified semantic embeddings and cross-modal downstream outputs. |

<a id="sparsh-tacbench"></a>
### Sparsh: Self-supervised touch representations for vision-based tactile sensing

**Carolina Higuera et al. · 2024 · P0 · enabling**  
CoRL 2024; proceedings PMLR 270 (2025); arXiv:2410.24090. TacBench is its evaluation suite.

[Paper / primary source](https://arxiv.org/html/2410.24090v1) · [Author project](https://sparsh-ssl.github.io/) · [Code](https://github.com/facebookresearch/sparsh) · [Data / release](https://huggingface.co/collections/facebook/sparsh)

- **Problem:** Learn transferable optical touch features with limited labels.
- **Inputs:** Optical tactile images across sensors; force/pose/slip labels for downstream heads. **Conditioning:** Self-supervised pretraining and task-specific supervision.
- **Output:** Embeddings; force, slip, pose, grasp, textile, and manipulation outputs.
- **World-model contribution (assessment):** Strong E baseline and force-estimation benchmark before learning physical transitions.
- **Reported evidence:** TacBench evaluates six tasks; force tests vary contact geometries. Slip labels use a friction-cone criterion.
- **Limits / transfer assessment:** Force regression is observational, not a contact law. Dense force visualizations and derived slip labels require careful calibration interpretation.
- **Repository connection:** Add optical-force baselines with geometry/sensor splits; retain separate acceleration-spectrum validation.

Review: `full-text-sections`; Sections 3–5 and appendices D.3–D.5; official resources. Verified 2026-10-11.

<a id="anytouch-2"></a>
### AnyTouch 2: General Optical Tactile Representation Learning For Dynamic Tactile Perception

**Ruoxuan Feng et al. · 2025 · P0 · enabling**  
ICLR 2026; anonymous OpenReview manuscript publicly indexed in 2025; arXiv:2602.09617 February 2026.

[Paper / primary source](https://arxiv.org/abs/2602.09617) · [Author project](https://gewu-lab.github.io/AnyTouch2/) · [Code](https://github.com/GeWu-Lab/AnyTouch2) · [Data / release](https://huggingface.co/collections/BAAI/touchd)

- **Problem:** Learn force-aware temporal touch features.
- **Inputs:** ToucHD synthetic actions, real manipulation, and optical touch paired with measured force. **Conditioning:** Video/frame-difference reconstruction, action alignment, and force supervision.
- **Output:** Representations; force and temporal-force estimates; manipulation features.
- **World-model contribution (assessment):** Promising E and force-supervision resource bridging optical perception and dynamics.
- **Reported evidence:** Force/force-change tests, unseen indenters, multisensor benchmarks, and real manipulation.
- **Limits / transfer assessment:** Estimating force from observed windows does not establish arbitrary-action force rollouts or calibrated material coefficients.
- **Repository connection:** Prioritize its touch-force pairs for future force heads; modality differs from Cluster.

Review: `full-text-sections`; Final-paper force experiment section 5.2; official dataset structure; abstract/history. Verified 2026-10-11.

<a id="making-sense-vision-touch"></a>
### Making Sense of Vision and Touch: Self-Supervised Learning of Multimodal Representations for Contact-Rich Tasks

**Michelle A. Lee et al. · 2018 · P1 · enabling**  
ICRA 2019; first arXiv October 2018 (1810.10191); later expanded T-RO article has a separate manuscript.

[Paper / primary source](https://arxiv.org/html/1810.10191v2)

- **Problem:** Fuse heterogeneous observations for contact-rich control.
- **Inputs:** RGB, wrist six-axis force/torque history, and proprioception. **Conditioning:** Current fused state and next end-effector action for auxiliary predictions.
- **Output:** Optical flow, next-cycle contact occurrence, and modality concurrency; features for reinforcement learning.
- **World-model contribution (assessment):** Foundational action-informed E pretraining with actual force/torque feedback.
- **Reported evidence:** Simulated and real peg insertion; modality ablations, geometry/clearance variation, and perturbations.
- **Limits / transfer assessment:** Auxiliary one-step prediction and policy success do not establish full force/motion rollouts or calibrated material identification.
- **Repository connection:** Compare predictive versus purely reconstructive encoder objectives when adding measured force and robot state.

Review: `full-text-sections`; Sections IV-A/B and VI; arXiv venue/history. Verified 2026-10-11.

<a id="exsarn"></a>
### On Explainability and Sensor-Adaptability of a Robot Tactile Texture Representation Using a Two-Stage Recurrent Networks

**Ruihan Gao et al. · 2021 · P1 · enabling**  
IROS 2021; verified official author repository and citation.

[Paper / primary source](https://github.com/dexrob/ExSARN) · [Code](https://github.com/dexrob/ExSARN) · [Data / release](https://github.com/dexrob/ExSARN)

- **Problem:** Represent textures across heterogeneous tactile sensors.
- **Inputs:** BioTac/iCub tactile sequences and material descriptions. **Conditioning:** Sensor input and supervised texture classes.
- **Output:** Recurrent texture representations and classification.
- **World-model contribution (assessment):** Texture E baseline and sensor-adaptation reference.
- **Reported evidence:** Official release supplies texture-class datasets and implementation for representation/classification research.
- **Limits / transfer assessment:** Classification labels do not calibrate friction/compliance or establish action-conditioned acceleration/force generation; detailed paper metrics were not reviewed.
- **Repository connection:** Existing related-work dataset; useful retrieval/representation baseline, with sensor differences made explicit.

Review: `abstract-and-metadata`; Author README dataset description and paper citation; full paper not reviewed. Verified 2026-10-11.

<a id="objectfolder-2"></a>
### ObjectFolder 2.0: A Multisensory Object Dataset for Sim2Real Transfer

**Ruohan Gao et al. · 2022 · P1 · enabling**  
CVPR 2022; arXiv:2204.02389.

[Paper / primary source](https://arxiv.org/abs/2204.02389) · [Code](https://github.com/rhgao/ObjectFolder) · [Data / release](https://github.com/rhgao/ObjectFolder)

- **Problem:** Improve multisensory rendering scale and transfer to real objects.
- **Inputs:** Implicit visual, impact-audio, and tactile object assets. **Conditioning:** Object identity and modality-specific spatial/contact queries.
- **Output:** Multisensory renderings; scale, contact-location, and shape estimates.
- **World-model contribution (assessment):** Provides scalable G assets and checks on observation transfer.
- **Reported evidence:** Sim-to-real object-scale estimation, contact localization, and shape reconstruction.
- **Limits / transfer assessment:** Transfer of these perception tasks does not validate friction, calibrated forces, or long-horizon dynamics.
- **Repository connection:** Potential synthetic optical pretraining; require a separate mechanics and calibration evaluation.

Review: `abstract-and-metadata`; Abstract, CVPR paper metadata, and official repository. Verified 2026-10-11.

<a id="touch-and-go"></a>
### Touch and Go: Learning from Human-Collected Vision and Touch

**Fengyu Yang et al. · 2022 · P1 · enabling**  
NeurIPS 2022 Datasets and Benchmarks; arXiv:2211.12498.

[Paper / primary source](https://papers.neurips.cc/paper_files/paper/2022/hash/354892587fe39b17c2b727af02abff4a-Abstract-Datasets_and_Benchmarks.html)

- **Problem:** Learn visual/tactile features from diverse everyday contacts.
- **Inputs:** Human-collected scene video and GelSight contacts. **Conditioning:** Paired modalities and temporal context.
- **Output:** Cross-modal embeddings, tactile-driven image stylization, and tactile prediction.
- **World-model contribution (assessment):** Broad pretraining source for E and cross-modal observation priors.
- **Reported evidence:** Dataset and representation/generation benchmarks on natural contacts.
- **Limits / transfer assessment:** Human collection lacks standardized robot action, force, and state trajectories needed for calibrated transition learning.
- **Repository connection:** Useful optical encoder pretraining; not a drop-in source of acceleration-spectrum or contact-law supervision.

Review: `abstract-and-metadata`; Proceedings abstract and metadata; dataset description. Verified 2026-10-11.

<a id="objectfolder-benchmark"></a>
### The ObjectFolder Benchmark: Multisensory Learning with Neural and Real Objects

**Ruohan Gao et al. · 2023 · P1 · direct**  
CVPR 2023; arXiv:2306.00956.

[Paper / primary source](https://openaccess.thecvf.com/content/CVPR2023/papers/Gao_The_ObjectFolder_Benchmark_Multisensory_Learning_With_Neural_and_Real_Objects_CVPR_2023_paper.pdf) · [Author project](https://objectfolder.stanford.edu) · [Data / release](https://objectfolder.stanford.edu/objectfolder-real)

- **Problem:** Evaluate multisensory object learning and manipulation.
- **Inputs:** Neural assets and real-object video, impact sounds, and localized GelSight measurements. **Conditioning:** Object/task context; initial observations and candidate controls in manipulation tasks.
- **Output:** Perception outputs and learned forward predictions for multisensory MPC.
- **World-model contribution (assessment):** A task suite linking object representations, adaptation, and action-conditioned planning.
- **Reported evidence:** Benchmarks include surface traversal and dynamic pushing; context-conditioned forward models support manipulation.
- **Limits / transfer assessment:** These task results do not identify transferable calibrated contact laws or universal material coefficients.
- **Repository connection:** Use task-level rollout and adaptation evaluations beyond current spectrum errors.

Review: `full-text-sections`; Sections 4.9 and 4.10; ObjectFolder Real author page. Verified 2026-10-11.

<a id="t3"></a>
### Transferable Tactile Transformers for Representation Learning Across Diverse Sensors and Tasks

**Jialiang Zhao et al. · 2024 · P1 · enabling**  
CoRL 2024; arXiv:2406.13640.

[Paper / primary source](https://arxiv.org/abs/2406.13640) · [Author project](https://t3.alanz.info/) · [Code](https://github.com/alanzjl/t3) · [Data / release](https://huggingface.co/datasets/alanz-mit/FoundationTactile)

- **Problem:** Transfer representations across sensor hardware and tasks.
- **Inputs:** FoTa tactile data spanning diverse sensors and tasks. **Conditioning:** Sensor-specific encoders, a shared transformer, and task decoders.
- **Output:** Reusable tactile embeddings and supervised task outputs.
- **World-model contribution (assessment):** Candidate modular E design; sensor adapters prevent treating every tactile modality identically.
- **Reported evidence:** Novel sensor/task pairings, few-shot transfer, and behavior-cloning insertion demonstrations.
- **Limits / transfer assessment:** Representation and policy transfer do not demonstrate action-conditioned physical rollouts or parameter identification.
- **Repository connection:** Relevant when adding optical sensors; cannot assume transfer to Cluster probe acceleration.

Review: `full-text-sections`; Architecture section and official project/data overview; arXiv metadata. Verified 2026-10-11.

<a id="anytouch"></a>
### AnyTouch: Learning Unified Static-Dynamic Representation across Multiple Visuo-tactile Sensors

**Ruoxuan Feng et al. · 2025 · P1 · enabling**  
ICLR 2025; first dated arXiv February 2025 (2502.12191); earlier OpenReview submission date not independently recovered.

[Paper / primary source](https://arxiv.org/abs/2502.12191) · [Author project](https://gewu-lab.github.io/AnyTouch/) · [Code](https://github.com/GeWu-Lab/AnyTouch) · [Data / release](https://huggingface.co/datasets/xxuan01/TacQuad)

- **Problem:** Align heterogeneous sensors while retaining temporal contact detail.
- **Inputs:** Tactile images/videos; TacQuad aligned contacts, vision, and text. **Conditioning:** Masked modeling, multimodal alignment, and cross-sensor matching.
- **Output:** Sensor-agnostic features, reconstructed videos, and auxiliary next-frame prediction.
- **World-model contribution (assessment):** Temporal/multisensor E pretraining and paired sensor calibration data.
- **Reported evidence:** Static/dynamic perception transfer and real tactile-guided pouring.
- **Limits / transfer assessment:** Unconditioned temporal representation learning is not candidate-action physics prediction; sensor alignment does not calibrate forces.
- **Repository connection:** Useful encoder comparison after collecting optical sequences and synchronized action data.

Review: `abstract-and-metadata`; Abstract; author project model, dataset, and experiment sections. Verified 2026-10-11.

<a id="sparsh-x"></a>
### Tactile Beyond Pixels: Multisensory Touch Representations for Robot Manipulation

**Carolina Higuera et al. · 2025 · P1 · enabling**  
CoRL 2025; arXiv:2506.14754; model Sparsh-X.

[Paper / primary source](https://arxiv.org/abs/2506.14754)

- **Problem:** Retain tactile information beyond optical appearance.
- **Inputs:** DIGIT 360 images, audio, inertial motion, and pressure. **Conditioning:** Multimodal self-supervised pretraining and downstream supervision.
- **Output:** Touch embeddings for physical perception and manipulation.
- **World-model contribution (assessment):** E design combining visual contact with vibration/motion channels; used by VT-WM.
- **Reported evidence:** Physical-property/force perception and imitation/control transfer evaluations reported.
- **Limits / transfer assessment:** Multisensory encoding alone is not an intervention model; hardware-specific signals require calibration and transfer checks.
- **Repository connection:** Closest foundation-encoder direction to combining Cluster acceleration with future optical/force sensing.

Review: `abstract-and-metadata`; Abstract, arXiv metadata, and primary author publication listing. Verified 2026-10-11.

<a id="stag"></a>
### Learning the signatures of the human grasp using a scalable tactile glove

**Subramanian Sundaram et al. · 2019 · P2 · enabling**  
Nature 569, 698–702, 2019; DOI 10.1038/s41586-019-1234-z.

[Paper / primary source](https://stag.csail.mit.edu/) · [Author project](https://stag.csail.mit.edu/) · [Code](https://github.com/Erkil1452/touch) · [Data / release](https://stag.csail.mit.edu/)

- **Problem:** Record and interpret distributed human grasp pressures.
- **Inputs:** Full-hand piezoresistive pressure maps and accompanying images. **Conditioning:** Human grasps of objects; supervised object/weight tasks.
- **Output:** Object identity, weight estimates, and grasp/hand-pressure structure.
- **World-model contribution (assessment):** Distributed-contact E/data precedent distinct from fingertip optical textures.
- **Reported evidence:** Human grasp classification and weight estimation; official release includes pressure-only datasets.
- **Limits / transfer assessment:** Human observations lack robot action-conditioned dynamics and calibrated contact-law identification; noncommercial dataset terms require review.
- **Repository connection:** Data-diversity reference; complements texture vibration but does not replace synchronized mechanics trajectories.

Review: `abstract-and-metadata`; Official paper abstract, citation, and dataset descriptions. Verified 2026-10-11.

<a id="visgel"></a>
### Connecting Touch and Vision via Cross-Modal Prediction

**Yunzhu Li et al. · 2019 · P2 · enabling**  
CVPR 2019; arXiv:1906.06322; dataset VisGel.

[Paper / primary source](https://arxiv.org/abs/1906.06322) · [Author project](http://visgel.csail.mit.edu) · [Data / release](http://visgel.csail.mit.edu)

- **Problem:** Learn correspondence between visual appearance and touch.
- **Inputs:** Paired robot-camera and GelSight contact sequences. **Conditioning:** Cross-modal images and contact location/scale context.
- **Output:** Generated touch from vision and vision from touch.
- **World-model contribution (assessment):** Foundational G/E cross-modal prediction baseline.
- **Reported evidence:** Paired dataset, prediction benchmarks, and perceptual realism evaluations.
- **Limits / transfer assessment:** Observation translation lacks candidate controls, calibrated contact-force targets, and dynamical state transitions.
- **Repository connection:** Establishes why plausible tactile images need additional physical validation.

Review: `abstract-and-metadata`; Abstract, author paper introduction, and arXiv metadata. Verified 2026-10-11.

<a id="objectfolder"></a>
### ObjectFolder: A Dataset of Objects with Implicit Visual, Auditory, and Tactile Representations

**Ruohan Gao et al. · 2021 · P2 · enabling**  
CoRL 2021; arXiv:2109.07991.

[Paper / primary source](https://arxiv.org/abs/2109.07991) · [Code](https://github.com/rhgao/ObjectFolder) · [Data / release](https://github.com/rhgao/ObjectFolder)

- **Problem:** Provide reusable multisensory object assets.
- **Inputs:** Synthetic visual, impact-audio, and tactile responses. **Conditioning:** Queries to object-specific implicit representations.
- **Output:** Rendered modalities and representations for object tasks.
- **World-model contribution (assessment):** Object-centric observation renderer/assets for G and multimodal E.
- **Reported evidence:** Recognition, retrieval, reconstruction, and grasping examples using virtual objects.
- **Limits / transfer assessment:** An implicit sensory asset does not establish action-dependent rigid/deformable mechanics or measured force laws.
- **Repository connection:** Useful simulation-side observation source after a physical solver; distinct from material identification.

Review: `abstract-and-metadata`; Abstract, arXiv metadata, and official repository description. Verified 2026-10-11.

<a id="unitouch"></a>
### Binding Touch to Everything: Learning Unified Multimodal Tactile Representations

**Fengyu Yang et al. · 2024 · P2 · enabling**  
CVPR 2024; arXiv:2401.18084; model name UniTouch.

[Paper / primary source](https://openaccess.thecvf.com/content/CVPR2024/papers/Yang_Binding_Touch_to_Everything_Learning_Unified_Multimodal_Tactile_Representations_CVPR_2024_paper.pdf) · [Author project](https://cfeng16.github.io/UniTouch/) · [Code](https://github.com/cfeng16/UniTouch)

- **Problem:** Connect tactile data with other semantic modalities.
- **Inputs:** Optical tactile images paired with visual information. **Conditioning:** Pretrained ImageBind space and sensor-specific tokens.
- **Output:** Unified semantic embeddings and cross-modal downstream outputs.
- **World-model contribution (assessment):** Possible semantic prior for E and retrieval; supports multimodal alignment.
- **Reported evidence:** Zero-shot material/grasp-related tasks and touch-conditioned multimodal generation.
- **Limits / transfer assessment:** Semantic alignment does not identify mechanics or predict interventions; generated appearance is not calibrated force evidence.
- **Repository connection:** Secondary material-retrieval baseline if optical observations are added.

Review: `abstract-and-metadata`; Abstract and official method/project overview. Verified 2026-10-11.

<a id="predictive-world-models"></a>
## Predictive tactile dynamics and world models

Sequential prediction, latent state transitions and world/action models. Inspect future-action inputs, feedback availability and tested rollout/generalization scope for each entry.

| Paper | Year | Priority / relevance | Output |
| --- | --- | --- | --- |
| [Manipulation by Feel: Touch-Based Control with Deep Predictive Models](#manipulation-by-feel) | 2019 | P0 / direct | Future tactile observations used in model predictive control. |
| [Multi-Modal World Model for Physical Robot Interactions: Simultaneous Visual and Tactile Predictions for Enhanced Accuracy](#spots) | 2023 | P0 / direct | Joint future video and tactile vectors through coupled modality-specific recurrent predictors. |
| [RoboPack: Learning Tactile-Informed Dynamics Models for Dense Packing](#robopack) | 2024 | P0 / direct | Latent object physics and future object-particle states used by MPPI. |
| [Visuo-Tactile World Models](#visuo-tactile-world-models) | 2025 | P0 / direct | Future visual and tactile latents; CEM goal planning. |
| [ContactWorld: What Representations Matter for Vision-Tactile Latent World Models in Contact-Rich Manipulation](#contactworld) | 2026 | P0 / direct | Latent transitions and manipulation plans. |
| [Learning Latent Space Dynamics for Tactile Servoing](#latent-tactile-servoing) | 2018 | P1 / direct | Latent tactile dynamics and goal-directed tactile servoing. |
| [Compact Visuotactile World Models for Lifting: Prediction, Reward Alignment, and Force Constraints](#compact-lifting-world-model) | 2026 | P1 / direct | Future states/reward/contact-force estimates and model-based policy feedback. |
| [DexTouch-WM: Learning Action-Conditioned Tactile World Models from Human Touch for Dexterous Robot Manipulation](#dextouch-wm) | 2026 | P1 / direct | Joint future RGB and pressure maps. |
| [Dream-Tac: A Unified Tactile World Action Model for Contact-Rich Robot Manipulation](#dream-tac) | 2026 | P1 / direct | Action predictions and future visual/tactile sequences. |
| [OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](#omnivta) | 2026 | P1 / direct | Short-horizon contact evolution, actions, and tactile-error corrections. |
| [TACO: TActile World Model as a Self-COrrector for Scalable Robot Policy Post-Training](#taco) | 2026 | P1 / direct | Corrected video/force trajectories, action labels, and post-trained policies. |
| [VT-WAM: Visual-Tactile World Action Model for Contact-Rich Manipulation](#vt-wam) | 2026 | P1 / direct | Future tactile/visual sequences and action chunks. |

<a id="manipulation-by-feel"></a>
### Manipulation by Feel: Touch-Based Control with Deep Predictive Models

**Stephen Tian et al. · 2019 · P0 · direct**  
ICRA 2019; arXiv:1903.04128; DOI 10.1109/ICRA.2019.8794219.

[Paper / primary source](https://arxiv.org/abs/1903.04128) · [Author project](https://sites.google.com/view/deeptactilempc)

- **Problem:** Plan manipulation from high-dimensional tactile feedback.
- **Inputs:** Raw optical tactile images from autonomous interactions. **Conditioning:** Tactile history and candidate action sequences.
- **Output:** Future tactile observations used in model predictive control.
- **World-model contribution (assessment):** Foundational tactile forward-model/MPC precedent.
- **Reported evidence:** Touch-goal control of a ball, analog joystick, and die.
- **Limits / transfer assessment:** Task-specific sensory prediction is not calibrated object/contact mechanics or evidence of unseen-material identification.
- **Repository connection:** Motivates action-shuffle, persistence, multi-step, and closed-loop checks beyond spectrum loss.

Review: `abstract-and-metadata`; Abstract and author PDF introduction; arXiv/publisher metadata. Verified 2026-10-11.

<a id="spots"></a>
### Multi-Modal World Model for Physical Robot Interactions: Simultaneous Visual and Tactile Predictions for Enhanced Accuracy

**Willow Mandil et al. · 2023 · P0 · direct**  
Robotics and Autonomous Systems 204, 105512, 2026; journal title adds (SPOTS). First arXiv April 2023; reviewed v2 May 2026.

[Paper / primary source](https://arxiv.org/html/2304.11193v2) · [Author project](https://sites.google.com/view/spots-research) · [Code](https://github.com/imanlab/WM-4-PRI) · [Data / release](https://github.com/imanlab/WM-4-PRI)

- **Problem:** Predict hidden contact-dependent outcomes of pushing.
- **Inputs:** Scene RGB and Xela uSkin normal/shear taxel vectors. **Conditioning:** Sensory history, past robot state, and planned future actions.
- **Output:** Joint future video and tactile vectors through coupled modality-specific recurrent predictors.
- **World-model contribution (assessment):** Direct action-conditioned F/G precedent and physically ambiguous comparison protocol.
- **Reported evidence:** Household-cluster and visually identical hidden-friction-location pushing tests; extended-horizon and sensory-removal analyses.
- **Limits / transfer assessment:** Paper explicitly describes uncalibrated taxel forces. Prediction evidence does not identify contact-law parameters; straight-line pushing constrains action coverage.
- **Repository connection:** Promising paired robot/action/touch benchmark after checking timestamps and force calibration.

Review: `full-text-sections`; Sections 2.1, 3, 4.3, 5.1, and 6.4; publisher metadata. Verified 2026-10-11.

<a id="robopack"></a>
### RoboPack: Learning Tactile-Informed Dynamics Models for Dense Packing

**Bo Ai et al. · 2024 · P0 · direct**  
Robotics: Science and Systems 2024; arXiv:2407.01418.

[Paper / primary source](https://arxiv.org/html/2407.01418v1) · [Author project](https://robo-pack.github.io) · [Code](https://github.com/BoAi01/robopack)

- **Problem:** Infer hidden object physics for nonprehensile packing.
- **Inputs:** RGB-D object particles and SoftBubble deformation/flow-derived tactile force proxies. **Conditioning:** Interaction history for physics estimation; candidate actions for forward dynamics.
- **Output:** Latent object physics and future object-particle states used by MPPI.
- **World-model contribution (assessment):** Closest E(probes)→latent-physics→F(state,action) structural precedent.
- **Reported evidence:** Real pushing/packing, unseen objects/mass distributions, and dynamics/physics-baseline comparisons.
- **Limits / transfer assessment:** Physics latents are unsupervised and not calibrated coefficients; deformation-derived force proxies are not direct force-law measurements. Future tactile is excluded from forward prediction.
- **Repository connection:** Prioritize architectural study; add object state/action supervision before extending Cluster to physical rollouts.

Review: `full-text-sections`; Sections III-C/D, IV-A, and V-B through V-D. Verified 2026-10-11.

<a id="visuo-tactile-world-models"></a>
### Visuo-Tactile World Models

**Carolina Higuera et al. · 2025 · P0 · direct**  
First public OpenReview September 19, 2025, ICLR 2026 submission; arXiv:2602.06001 February 2026 preprint. Acceptance not independently verified.

[Paper / primary source](https://arxiv.org/html/2602.06001v1)

- **Problem:** Predict joint visual/contact evolution for planning.
- **Inputs:** Scene RGB and DIGIT 360 multimodal finger touch encoded with Sparsh-X. **Conditioning:** Observation context and candidate wrist/gripper actions.
- **Output:** Future visual and tactile latents; CEM goal planning.
- **World-model contribution (assessment):** Close learned E/F precedent integrating tactile information in latent transition dynamics.
- **Reported evidence:** Multi-step prediction, tracking-based plausibility checks, and real goal-conditioned manipulation.
- **Limits / transfer assessment:** Evaluation remains scene/object/hardware constrained; plausibility checks do not prove calibrated forces or conservation.
- **Repository connection:** Candidate architecture after acquiring synchronized robot state/actions and force/contact ground truth.

Review: `full-text-sections`; Sections 3–4 and appendix E; primary author OpenReview publication listing. Verified 2026-10-11.

<a id="contactworld"></a>
### ContactWorld: What Representations Matter for Vision-Tactile Latent World Models in Contact-Rich Manipulation

**Zhiyuan Zhang et al. · 2026 · P0 · direct**  
arXiv:2606.13877; first June 2026; latest reviewed v3 September 24, 2026.

[Paper / primary source](https://arxiv.org/html/2606.13877v3) · [Author project](https://contact-world.github.io/) · [Code](https://github.com/PokuangZhou/ContactWorld)

- **Problem:** Identify useful visual/tactile structures for latent world models.
- **Inputs:** RGB or point clouds; tactile RGB, arrays, or force-field representations. **Conditioning:** Action history/candidates and multimodal context in learned planning.
- **Output:** Latent transitions and manipulation plans.
- **World-model contribution (assessment):** Representation ablations directly inform physically structured E/F inputs.
- **Reported evidence:** Controlled simulation comparisons and real manipulation across platforms/sensors; tactile benefits vary by task.
- **Limits / transfer assessment:** Some real array/force-field comparisons use different hardware and separately trained models; not zero-shot sensor transfer or calibrated material identification.
- **Repository connection:** Evaluate force/geometry structure against learned features under matched protocols.

Review: `full-text-sections`; Sections V-D, V-E, and VI; latest arXiv metadata. Verified 2026-10-11.

<a id="latent-tactile-servoing"></a>
### Learning Latent Space Dynamics for Tactile Servoing

**Giovanni Sutanto et al. · 2018 · P1 · direct**  
ICRA 2019; first arXiv November 2018 (1811.03704).

[Paper / primary source](https://arxiv.org/abs/1811.03704)

- **Problem:** Control contact using a compact tactile state.
- **Inputs:** BioTac measurements and robot demonstrations. **Conditioning:** Current latent touch and control actions.
- **Output:** Latent tactile dynamics and goal-directed tactile servoing.
- **World-model contribution (assessment):** Early E-plus-transition-model example for tactile-state control.
- **Reported evidence:** Learned low-dimensional tactile manifold and contact servoing demonstrations.
- **Limits / transfer assessment:** Local/task-specific dynamics do not establish broad material or embodiment transfer, calibrated friction, or compliance.
- **Repository connection:** Useful small-model baseline before adopting large generative world models.

Review: `abstract-and-metadata`; Abstract and arXiv venue/submission metadata. Verified 2026-10-11.

<a id="compact-lifting-world-model"></a>
### Compact Visuotactile World Models for Lifting: Prediction, Reward Alignment, and Force Constraints

**Qinzhen Ma · 2026 · P1 · direct**  
arXiv:2609.09597; September 2026 preprint; latest reviewed v2.

[Paper / primary source](https://arxiv.org/html/2609.09597v2)

- **Problem:** Test whether compact prediction models improve force-constrained control.
- **Inputs:** Simulated lifting state and tactile/contact observations. **Conditioning:** Candidate actions and compact learned state.
- **Output:** Future states/reward/contact-force estimates and model-based policy feedback.
- **World-model contribution (assessment):** Particularly useful falsification protocol: strong reactive baselines, action-effect checks, and fresh environments.
- **Reported evidence:** MuJoCo geometry/physics shifts; model feedback, behavior-cloning, reactive IQL, and imagined-RL comparisons.
- **Limits / transfer assessment:** Imagined RL underperforms reactive IQL; pooled control benefit is uncertain. Separate public tactile-force perturbation analysis does not demonstrate optical sim-to-real deployment.
- **Repository connection:** Adopt its evaluation discipline before interpreting spectral prediction as physical/control progress.

Review: `full-text-sections`; Sections V-C, V-D, and VI; arXiv latest-author metadata. Verified 2026-10-11.

<a id="dextouch-wm"></a>
### DexTouch-WM: Learning Action-Conditioned Tactile World Models from Human Touch for Dexterous Robot Manipulation

**Yan Qin et al. · 2026 · P1 · direct**  
arXiv:2609.20649, September 2026; accepted IROS 2026 RoBoWoMo workshop lightning talk, not main-conference acceptance.

[Paper / primary source](https://arxiv.org/html/2609.20649v2)

- **Problem:** Scale robot contact prediction with aligned human interaction data.
- **Inputs:** RGB and bilateral full-hand pressure maps. **Conditioning:** Initial observations, instruction, and retargeted future hand/wrist/camera poses.
- **Output:** Joint future RGB and pressure maps.
- **World-model contribution (assessment):** Explicit action-conditioned sensory rollout with anatomy-aware contact tokens.
- **Reported evidence:** Human-data scaling with fixed robot supervision; robot-domain prediction, policy evaluation, and synthetic-data uses.
- **Limits / transfer assessment:** Requires shared sensing layout/action alignment; does not identify calibrated material constants or guarantee physical consistency.
- **Repository connection:** Guides future collection of synchronized contact/action trajectories; current Cluster lacks articulated state.

Review: `full-text-sections`; Sections III-A through III-D and IV-A; arXiv workshop status. Verified 2026-10-11.

<a id="dream-tac"></a>
### Dream-Tac: A Unified Tactile World Action Model for Contact-Rich Robot Manipulation

**Yunfan Lou et al. · 2026 · P1 · direct**  
arXiv:2606.08737, June 2026 preprint.

[Paper / primary source](https://arxiv.org/abs/2606.08737) · [Code](https://github.com/LYFCLOUDFAN/Dream-Tac)

- **Problem:** Couple action generation with predicted tactile/visual evolution.
- **Inputs:** Visual and tactile observations. **Conditioning:** Current multimodal context and joint action/future-observation generation.
- **Output:** Action predictions and future visual/tactile sequences.
- **World-model contribution (assessment):** Joint world/action modeling with contact-gated fusion and efficient inference.
- **Reported evidence:** Six contact-rich tasks report improved action accuracy; abstract claims should not be read as force-calibration evidence.
- **Limits / transfer assessment:** Action accuracy and generated sensory dynamics do not establish calibrated force rollouts or a reusable physical engine.
- **Repository connection:** Policy-oriented comparison after collecting action-conditioned robot trajectories.

Review: `abstract-and-metadata`; Abstract and official code README; arXiv history. Verified 2026-10-11.

<a id="omnivta"></a>
### OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation

**Yuhang Zheng et al. · 2026 · P1 · direct**  
arXiv:2603.19201; first March 2026; latest v3 August 2026.

[Paper / primary source](https://arxiv.org/abs/2603.19201) · [Author project](https://mrsecant.github.io/OmniVTA/)

- **Problem:** Combine predicted contacts with rapid feedback for manipulation.
- **Inputs:** OmniViTac synchronized visual/tactile robot trajectories. **Conditioning:** Task/interaction context within a world-model, policy, and reflex-control pipeline.
- **Output:** Short-horizon contact evolution, actions, and tactile-error corrections.
- **World-model contribution (assessment):** Reference for combining predictive F with feedback when rollout errors accumulate.
- **Reported evidence:** Real manipulation across interaction categories and unseen objects/geometries reported.
- **Limits / transfer assessment:** Broad task results do not establish calibrated material coefficients; release availability must be checked separately.
- **Repository connection:** Future control architecture; requires robot actions and contact geometry absent from present texture pipeline.

Review: `abstract-and-metadata`; Latest abstract, submission history, and official project overview. Verified 2026-10-11.

<a id="taco"></a>
### TACO: TActile World Model as a Self-COrrector for Scalable Robot Policy Post-Training

**Shengbang Liu et al. · 2026 · P1 · direct**  
arXiv:2607.02840; first July 2026; latest reviewed v2 September 2026.

[Paper / primary source](https://arxiv.org/html/2607.02840v2) · [Author project](https://taco-wm.github.io/)

- **Problem:** Generate local corrective demonstrations for policy improvement.
- **Inputs:** RGB video and bilateral measured six-axis force/torque streams. **Conditioning:** Failure-adjacent anchor observations and task instructions; inverse-dynamics/action labeling stages.
- **Output:** Corrected video/force trajectories, action labels, and post-trained policies.
- **World-model contribution (assessment):** Actual force/torque modality and explicit corrective-data validation pipeline.
- **Reported evidence:** Real policy post-training experiments with trajectory filtering and compositional model ablations.
- **Limits / transfer assessment:** Correction generation is not necessarily arbitrary-action forward simulation; no calibrated material-parameter inference or conservation proof.
- **Repository connection:** Relevant future force/torque data format and synthetic-data filtering reference.

Review: `full-text-sections`; World-model/correction method and appendix A data collection. Verified 2026-10-11.

<a id="vt-wam"></a>
### VT-WAM: Visual-Tactile World Action Model for Contact-Rich Manipulation

**Shuai Tian et al. · 2026 · P1 · direct**  
arXiv:2607.02503, July 2026 preprint.

[Paper / primary source](https://arxiv.org/html/2607.02503v1) · [Author project](https://vt-wam.github.io/)

- **Problem:** Use sparse contact evolution to improve action generation.
- **Inputs:** Wrist RGB and bilateral three-dimensional tactile deformation fields. **Conditioning:** Initial observations, proprioception, and language; jointly denoised tactile/action sequences.
- **Output:** Future tactile/visual sequences and action chunks.
- **World-model contribution (assessment):** Useful joint observation/action-generation architecture with contact-gated attention.
- **Reported evidence:** Real surface-interaction/insertion tasks, deformation prediction, and attention/model ablations.
- **Limits / transfer assessment:** The tactile expert masks action keys; joint generation is not demonstrated arbitrary-candidate-action force prediction. Deformation is not calibrated friction/compliance.
- **Repository connection:** Separate policy gains from forward-physics accuracy when comparing to future E/F/G.

Review: `full-text-sections`; Sections III-A/B and IV-B/C; attention masks explicitly inspected. Verified 2026-10-11.

<a id="active-touch-control"></a>
## Active exploration and tactile control

Probe selection, stopping rules and task feedback. Informative actions must be evaluated at matched measurement and execution costs.

| Paper | Year | Priority / relevance | Output |
| --- | --- | --- | --- |
| [How Much Haptic Surface Data Is Enough?](#how-much-haptic-data-2017) | 2017 | P0 / direct | Coulomb-plus-viscous fit and stopping criterion. |
| [Predictive Visuo-Tactile Interactive Perception Framework for Object Properties Inference](#predictive-interactive-perception-2024) | 2024 | P0 / direct | Object/property beliefs, contact predictions and task actions. |
| [Use of tactile feedback to control exploratory movements to characterize object compliance](#active-compliance-2012) | 2012 | P1 / direct | Exploratory contact control and compliance characterization. |
| [Bayesian Exploration for Intelligent Identification of Textures](#bayesian-texture-exploration-2012) | 2012 | P1 / enabling | Texture posterior and next exploration choice. |
| [Cable Manipulation with a Tactile-Reactive Gripper](#tactile-cable-gripper) | 2019 | P1 / direct | Local linear sliding dynamics and reactive/LQR control. |
| [SwingBot: Learning Physical Features from In-hand Tactile Exploration for Dynamic Swing-up Manipulation](#swingbot-2020) | 2020 | P1 / direct | Physical-feature embedding and achieved swing angle. |
| [More Than a Feeling: Learning to Grasp and Regrasp using Vision and Touch](#more-than-a-feeling) | 2018 | P2 / adjacent | Predicted grasp outcome; iterative regrasp selection. |

<a id="how-much-haptic-data-2017"></a>
### How Much Haptic Surface Data Is Enough?

**Alex Burka and Katherine J. Kuchenbecker · 2017 · P0 · direct**  
AAAI Spring Symposium 2017.

[Paper / primary source](https://www.cs.utexas.edu/~jsinapov/AAAI-SSS-2017/paper/Burka_AAAI_SSS_2017.pdf)

- **Problem:** When to stop collecting friction-calibration data.
- **Inputs:** Proton Pack tangential/normal force, speed and vibration. **Conditioning:** Incremental freehand sliding.
- **Output:** Coulomb-plus-viscous fit and stopping criterion.
- **World-model contribution (assessment):** The closest classical baseline for observation-budget mechanics.
- **Reported evidence:** Online fitting on one vinyl surface; reports a 55.4-second stopping point in a 120-second recording.
- **Limits / transfer assessment:** Single surface and setup-specific criterion; no evidence that half a second identifies unseen surfaces or separates all speed-law parameters.
- **Repository connection:** Match total probing cost and compare simple force-based adaptation with learned inference.

Review: `full-text-sections`; Friction Modeling; online stopping criterion; results and discussion Verified 2026-10-11.

<a id="predictive-interactive-perception-2024"></a>
### Predictive Visuo-Tactile Interactive Perception Framework for Object Properties Inference

**Anirvan Dutta et al. · 2024 · P0 · direct**  
arXiv first November 2024; venue acceptance not independently confirmed in this review.

[Paper / primary source](https://arxiv.org/html/2411.09020v1)

- **Problem:** Active inference of hidden object properties.
- **Inputs:** Vision, tactile/contact force and pose history. **Conditioning:** Exploratory pushing/pulling and information-gain action selection.
- **Output:** Object/property beliefs, contact predictions and task actions.
- **World-model contribution (assessment):** A concrete belief/dynamics architecture with active mechanical exploration.
- **Reported evidence:** Dual differentiable filtering with graph networks is evaluated on configurable planar objects, tracking and goal tasks.
- **Limits / transfer assessment:** Repeated five-second interactions at 15 Hz and largely quasi-static action design; differs from half-second surface calibration and unrestricted dynamic friction.
- **Repository connection:** Prioritize its inference/action-selection interfaces after a restricted force law is validated.

Review: `full-text-sections`; Sections III-D to III-F; IV-B2 learning setup; evaluation Verified 2026-10-11.

<a id="active-compliance-2012"></a>
### Use of tactile feedback to control exploratory movements to characterize object compliance

**Zhe Su et al. · 2012 · P1 · direct**  
Frontiers in Neurorobotics 6:7, 2012.

[Paper / primary source](https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2012.00007/full)

- **Problem:** Controlled exploration for compliance discrimination.
- **Inputs:** BioTac electrodes and pressure with robot displacement. **Conditioning:** Feedback-controlled orientation and pressing.
- **Output:** Exploratory contact control and compliance characterization.
- **World-model contribution (assessment):** Demonstrates that contact geometry/control is part of a useful mechanical measurement.
- **Reported evidence:** Flat-material experiments combine multimodal tactile feedback with exploratory movement control.
- **Limits / transfer assessment:** Restricted material/contact setting; not a general deformation solver or cross-sensor mechanical model.
- **Repository connection:** Charge settling and orientation time to the probe budget; calibrate the combined contact.

Review: `full-text-sections`; Materials and methods; BioTac setup and exploratory movement control Verified 2026-10-11.

<a id="bayesian-texture-exploration-2012"></a>
### Bayesian Exploration for Intelligent Identification of Textures

**Jeremy A. Fishel and Gerald E. Loeb · 2012 · P1 · enabling**  
Frontiers in Neurorobotics 6:4, 2012.

[Paper / primary source](https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2012.00004/full)

- **Problem:** Choosing informative tactile exploration movements.
- **Inputs:** BioTac multimodal texture measurements. **Conditioning:** Candidate motion/load and current class belief.
- **Output:** Texture posterior and next exploration choice.
- **World-model contribution (assessment):** Provides a Bayesian action-selection template for reducing contact uncertainty.
- **Reported evidence:** Adaptive movement/signal selection discriminates textures in a known texture database.
- **Limits / transfer assessment:** Closed-set discrimination differs from predicting new surfaces' force responses; classification confidence is not physical-parameter uncertainty.
- **Repository connection:** Evaluate direction/load/speed probes at matched cost with continuous target uncertainty.

Review: `full-text-sections`; Classification Theory and Strategy; experimental overview; abstract Verified 2026-10-11.

<a id="tactile-cable-gripper"></a>
### Cable Manipulation with a Tactile-Reactive Gripper

**Yu She et al. · 2019 · P1 · direct**  
RSS 2020; first arXiv October 2019 (1910.02860); IJRR extension 2021.

[Paper / primary source](https://arxiv.org/abs/1910.02860) · [Author project](https://gelsight.csail.mit.edu/cable/)

- **Problem:** Follow and manipulate flexible cables while regulating contact.
- **Inputs:** GelSight cable geometry and tactile force estimates. **Conditioning:** Robot motion, grip command, and observed cable state.
- **Output:** Local linear sliding dynamics and reactive/LQR control.
- **World-model contribution (assessment):** Shows geometry, force feedback, and learned dynamics can be separate control components.
- **Reported evidence:** Real following across cable variants and headphone-jack insertion.
- **Limits / transfer assessment:** Local cable/sliding models do not recover general deformable-object mechanics or material laws.
- **Repository connection:** Reference for geometry/force instrumentation and a compact controlled-contact demonstrator.

Review: `full-text-sections`; IJRR extension sections 3, 4, and 7; RSS/arXiv metadata. Verified 2026-10-11.

<a id="swingbot-2020"></a>
### SwingBot: Learning Physical Features from In-hand Tactile Exploration for Dynamic Swing-up Manipulation

**Chen Wang et al. · 2020 · P1 · direct**  
IROS 2020; arXiv deposit January 2021.

[Paper / primary source](https://arxiv.org/abs/2101.11812)

- **Problem:** Adapting dynamic manipulation to unknown objects.
- **Inputs:** Tactile exploration while holding objects. **Conditioning:** Tilting/shaking probes and swing-up control parameters.
- **Output:** Physical-feature embedding and achieved swing angle.
- **World-model contribution (assessment):** Links inferred latent contact/object properties to action outcomes and control.
- **Reported evidence:** Predicts swing-up angles and selects controls for previously unseen objects.
- **Limits / transfer assessment:** Learned embeddings are not automatically calibrated mass/friction parameters; probe sequence and held-object dynamics differ from short flat slides.
- **Repository connection:** Use outcome prediction and unseen-object controls as later-stage evaluation precedents.

Review: `abstract-and-metadata`; Abstract; bibliographic metadata Verified 2026-10-11.

<a id="more-than-a-feeling"></a>
### More Than a Feeling: Learning to Grasp and Regrasp using Vision and Touch

**Roberto Calandra et al. · 2018 · P2 · adjacent**  
IEEE Robotics and Automation Letters 3(4), 2018; DOI 10.1109/LRA.2018.2852779.

[Paper / primary source](https://arxiv.org/abs/1805.11085) · [Author project](https://sites.google.com/view/more-than-a-feeling)

- **Problem:** Select tactile-informed grasp corrections.
- **Inputs:** Vision and two-finger GelSight images. **Conditioning:** Candidate grasp adjustment.
- **Output:** Predicted grasp outcome; iterative regrasp selection.
- **World-model contribution (assessment):** Action-conditional outcome critic and useful control baseline.
- **Reported evidence:** Real grasp trials evaluate outcome prediction, efficient regrasping, and finger-force reduction.
- **Limits / transfer assessment:** Predicts success rather than full state transitions; deliberately avoids analytical contact-force calibration.
- **Repository connection:** Benchmark a simple outcome model before claiming that full world-model rollouts add control value.

Review: `abstract-and-metadata`; Abstract, publication DOI, and author project. Verified 2026-10-11.

<a id="tactile-simulation"></a>
## Tactile simulators and sensor calibration

Optical rendering, elastomer mechanics and simulated tactile interfaces. Image quality, force calibration, simulation speed and real motion accuracy are separate targets.

| Paper | Year | Priority / relevance | Output |
| --- | --- | --- | --- |
| [Efficient Tactile Simulation with Differentiability for Robotic Manipulation](#efficient-tactile-simulation) | 2022 | P0 / direct | Dense tactile normal/shear force fields and analytic gradients. |
| [DiffTactile: A Physics-based Differentiable Tactile Simulator for Contact-rich Robotic Manipulation](#difftactile) | 2024 | P0 / direct | Forces, gel deformation, markers, optical images and dynamics gradients. |
| [TACTO: A Fast, Flexible, and Open-source Simulator for High-Resolution Vision-based Tactile Sensors](#tacto) | 2020 | P1 / direct | High-resolution synthetic tactile images. |
| [Sim-to-Real for Robotic Tactile Sensing via Physics-Based Simulation and Learned Latent Projections](#biotac-sim-latent) | 2021 | P1 / direct | Electrical sensor signals and contact patches. |
| [Taxim: An Example-based Simulation Model for GelSight Tactile Sensors](#taxim) | 2021 | P1 / direct | RGB tactile images and marker displacement fields. |
| [Tacchi: A Pluggable and Low Computational Cost Elastomer Deformation Simulator for Optical Tactile Sensors](#tacchi) | 2023 | P1 / direct | Deformed elastomer surfaces and tactile images. |
| [TacIPC: Intersection- and Inversion-free FEM-based Elastomer Simulation For Optical Tactile Sensors](#tacipc) | 2023 | P1 / direct | Deformed geometry, pseudo-images and marker motion. |
| [FOTS: A Fast Optical Tactile Simulator for Sim2Real Learning of Tactile-motor Robot Manipulation Skills](#fots) | 2024 | P1 / direct | RGB images, masks and marker-flow fields. |
| [TacEx: GelSight Tactile Simulation in Isaac Sim -- Combining Soft-Body and Visuotactile Simulators](#tacex) | 2024 | P1 / direct | GelSight observations and RL rollouts. |
| [TacSL: A Library for Visuotactile Sensor Simulation and Learning](#tacsl) | 2024 | P1 / direct | Synthetic touch observations and trained multimodal policies. |
| [Taccel: Scaling Up Vision-based Tactile Robotics via High-performance GPU Simulation](#taccel) | 2025 | P1 / direct | Coupled physical trajectories and optical touch. |
| [Tacchi 2.0: A Low Computational Cost and Comprehensive Dynamic Contact Simulator for Vision-based Tactile Sensors](#tacchi-2) | 2025 | P1 / direct | Tactile, marker-motion and joint image sequences. |
| [TaCauchy: An Extensible FEM Framework for Vision-Based Tactile Simulation](#tacauchy) | 2026 | P1 / direct | Cauchy stress, surface traction, pressure and tactile images. |
| [Simulation of Vision-based Tactile Sensors using Physics based Rendering](#optical-physics-rendering) | 2020 | P2 / direct | Rendered GelSight contact images. |
| [SimTac: A Physics-Based Simulator for Vision-Based Tactile Sensing with Biomorphic Structures](#simtac) | 2025 | P2 / direct | Optical responses and neural mechanical-response fields. |
| [Reduced-order Neural Modeling with Differentiable Simulation for High-Detail Tactile Perception](#reduced-order-tactile-simulation) | 2026 | P2 / direct | Fine displacement/deformation fields, tactile rendering and differentiable latent reconstruction. |

<a id="efficient-tactile-simulation"></a>
### Efficient Tactile Simulation with Differentiability for Robotic Manipulation

**Jie Xu et al. · 2022 · P0 · direct**  
CoRL 2022; proceedings published as PMLR 205 in 2023.

[Paper / primary source](https://proceedings.mlr.press/v205/xu23b.html) · [Author project](https://tactilesim.csail.mit.edu/) · [Code](https://github.com/eanswer/TactileSimulation)

- **Problem:** Compute dense normal/shear tactile fields and derivatives efficiently.
- **Inputs:** Rigid-body simulation state; real GelSlim marker flow for transfer. **Conditioning:** Actions, contact geometry, penalty contact parameters and taxel layout.
- **Output:** Dense tactile normal/shear force fields and analytic gradients.
- **World-model contribution (assessment):** A compact differentiable force observation interface for planning.
- **Reported evidence:** Simulation comparisons and zero-shot real high-precision peg insertion.
- **Limits / transfer assessment:** Reduced-coordinate rigid/penalty approximation; normalized force/marker correspondence is not universal absolute-force calibration.
- **Repository connection:** A force-field interface is a later Stage C/control extension after the fixed-contact force pilot.

Review: `full-text-sections`; Abstract; supplementary Appendix A penalty dynamics and derivatives. Verified 2026-10-11.

<a id="difftactile"></a>
### DiffTactile: A Physics-based Differentiable Tactile Simulator for Contact-rich Robotic Manipulation

**Zilin Si et al. · 2024 · P0 · direct**  
ICLR 2024; verified author project and proceedings.

[Paper / primary source](https://arxiv.org/abs/2403.08716) · [Author project](https://difftactile.github.io/) · [Code](https://github.com/Genesis-Embodied-AI/DiffTactile)

- **Problem:** Calibrate and optimize contact-rich dynamics with dense touch.
- **Inputs:** Real six-axis forces, optical markers; simulated FEM and particle states. **Conditioning:** Sensor pose/velocity; sensor elasticity; friction, damping and contact stiffness.
- **Output:** Forces, gel deformation, markers, optical images and dynamics gradients.
- **World-model contribution (assessment):** Closest mechanics-calibration precedent: fit contact parameters, then use a separate sensor renderer.
- **Reported evidence:** Press-slide fitting on acrylic/tape, tested on slide and two twists; simulated manipulation and real grasping demonstrations.
- **Limits / transfer assessment:** Two calibration surfaces; parameter uniqueness and unseen-surface brief-probe generalization are unproven. Penalty contact and randomized object parameters restrict claims.
- **Repository connection:** Stage B needs measured tangential forces; current vibration spectra cannot replace this supervision.

Review: `full-text-sections`; Sections 3.2–3.5, 4.3; Appendix A.2. Verified 2026-10-11.

<a id="tacto"></a>
### TACTO: A Fast, Flexible, and Open-source Simulator for High-Resolution Vision-based Tactile Sensors

**Shaoxiong Wang et al. · 2020 · P1 · direct**  
IEEE Robotics and Automation Letters 2022; verified official code citation.

[Paper / primary source](https://arxiv.org/abs/2012.08456) · [Code](https://github.com/facebookresearch/tacto)

- **Problem:** Generate optical touch observations efficiently in robot simulation.
- **Inputs:** Simulated contact geometry and sensor/object poses. **Conditioning:** External physics engine; optical sensor configuration and geometry.
- **Output:** High-resolution synthetic tactile images.
- **World-model contribution (assessment):** A modular observation model and renderer baseline.
- **Reported evidence:** Million-grasp stability learning, marble manipulation and a sim-to-real proof of concept.
- **Limits / transfer assessment:** Official README explicitly delegates dynamics and does not claim physically accurate deformation or friction. Image realism cannot validate a force law.
- **Repository connection:** Keep the current vibration observation predictor separate from Stage C dynamics in the same way.

Review: `abstract-and-metadata`; Abstract; official README physics disclaimer and citation. Verified 2026-10-11.

<a id="biotac-sim-latent"></a>
### Sim-to-Real for Robotic Tactile Sensing via Physics-Based Simulation and Learned Latent Projections

**Yashraj Narang et al. · 2021 · P1 · direct**  
ICRA 2021; verified official BioTac simulation repository.

[Paper / primary source](https://arxiv.org/abs/2103.16747) · [Code](https://github.com/NVlabs/biotac_sim)

- **Problem:** Connect a deformable sensor simulator to non-optical electrical touch.
- **Inputs:** Simulated BioTac FEM deformation and real electrical output. **Conditioning:** Indenter contact; learned mappings between simulated/real latent spaces.
- **Output:** Electrical sensor signals and contact patches.
- **World-model contribution (assessment):** A mechanics-to-observation bridge across modalities without assuming identical sensor outputs.
- **Reported evidence:** FEM comparison to an experimentally validated CPU model; electrical synthesis and patch estimation for unseen interactions.
- **Limits / transfer assessment:** Sensor-specific calibration and paired supervision; CPU-model agreement is distinct from new real motion validation.
- **Repository connection:** Acceleration-to-optical transfer requires a validated observation mapping, as this work demonstrates for BioTac.

Review: `abstract-and-metadata`; Abstract; official repository scope and ICRA metadata. Verified 2026-10-11.

<a id="taxim"></a>
### Taxim: An Example-based Simulation Model for GelSight Tactile Sensors

**Zilin Si and Wenzhen Yuan · 2021 · P1 · direct**  
IEEE Robotics and Automation Letters 2022; verified primary DiffTactile bibliography.

[Paper / primary source](https://arxiv.org/abs/2109.04027) · [Code](https://github.com/Robo-Touch/Taxim)

- **Problem:** Calibrate realistic GelSight optics and marker deformation cheaply.
- **Inputs:** Real calibration indentations; deformed geometry or point cloud. **Conditioning:** Sensor-specific lighting calibration; normal/shear displacement.
- **Output:** RGB tactile images and marker displacement fields.
- **World-model contribution (assessment):** Example-calibrated observation layer; linear elastic superposition is a useful mechanics baseline.
- **Reported evidence:** Optical image comparisons and CPU rendering; fewer than 100 real calibration examples.
- **Limits / transfer assessment:** Approximate deformation/linear superposition; sensor calibration is required. No general dynamic friction identification or long-horizon world-model demonstration.
- **Repository connection:** Use comparable simple calibrated observation baselines before increasing network complexity.

Review: `abstract-and-metadata`; Abstract; official README calibration and marker simulation. Verified 2026-10-11.

<a id="tacchi"></a>
### Tacchi: A Pluggable and Low Computational Cost Elastomer Deformation Simulator for Optical Tactile Sensors

**Zixi Chen et al. · 2023 · P1 · direct**  
IEEE Robotics and Automation Letters 2023; verified author repository.

[Paper / primary source](https://arxiv.org/abs/2301.08343) · [Code](https://github.com/zixichen007115/Tacchi)

- **Problem:** Simulate optical sensor elastomer deformation without costly FEM.
- **Inputs:** Object geometry and simulated elastomer particles. **Conditioning:** Indentation, sensor shape and elastomer properties.
- **Output:** Deformed elastomer surfaces and tactile images.
- **World-model contribution (assessment):** Particle mechanics layer linking local contact geometry to touch.
- **Reported evidence:** Image similarity and sim-to-real classification comparisons; MuJoCo/Gazebo integration.
- **Limits / transfer assessment:** Perception/image evidence does not establish contact-force identification; original paper does not demonstrate end-to-end differentiable contact calibration.
- **Repository connection:** Useful future soft-sensor comparison; current fixed-probe sliding law can remain simpler.

Review: `abstract-and-metadata`; Abstract; author repository citation; DiffTactile related-work comparison. Verified 2026-10-11.

<a id="tacipc"></a>
### TacIPC: Intersection- and Inversion-free FEM-based Elastomer Simulation For Optical Tactile Sensors

**Wenxin Du et al. · 2023 · P1 · direct**  
IEEE Robotics and Automation Letters 2024; verified author publication page.

[Paper / primary source](https://arxiv.org/abs/2311.05843) · [Author project](https://sites.google.com/view/tac-ipc) · [Code](https://github.com/Ailon-Island/TacIPC)

- **Problem:** Prevent penetration and mesh inversion in optical sensor elastomer simulation.
- **Inputs:** FEM geometry; real tactile images and markers. **Conditioning:** Object shape, indentation/shear/rotation, elastic parameters and friction.
- **Output:** Deformed geometry, pseudo-images and marker motion.
- **World-model contribution (assessment):** Robust compliant-contact backend connecting contact to sensor deformation.
- **Reported evidence:** Image, depth and marker tests; simulated-training slip-rotation estimation tested on real wooden stick/pen.
- **Limits / transfer assessment:** Author project reports slow CPU linear solve and force prediction as future work. Depth split includes training objects, limiting unseen-object claims.
- **Repository connection:** Use it to distinguish robust deformation from validated sliding-force prediction.

Review: `abstract-and-metadata`; Abstract; author project results, dataset split, time analysis and sensitivity range. Verified 2026-10-11.

<a id="fots"></a>
### FOTS: A Fast Optical Tactile Simulator for Sim2Real Learning of Tactile-motor Robot Manipulation Skills

**Yongqiang Zhao et al. · 2024 · P1 · direct**  
IEEE Robotics and Automation Letters 2024; verified official code citation.

[Paper / primary source](https://arxiv.org/abs/2404.19217) · [Code](https://github.com/Rancho-zhao/FOTS)

- **Problem:** Render optical touch and markers quickly under different loads.
- **Inputs:** Contact geometry; real optical and marker calibration. **Conditioning:** Normal/shear/twist loads and sensor calibration.
- **Output:** RGB images, masks and marker-flow fields.
- **World-model contribution (assessment):** Fast approximate observation model integrated with a dynamics engine.
- **Reported evidence:** CPU speed/image comparisons; MuJoCo peg-in-hole policy with zero-shot sim-to-real.
- **Limits / transfer assessment:** Marker distributions approximate deformation; calibration and task transfer do not establish general material identification.
- **Repository connection:** Supports a later engine-plus-renderer architecture; compare approximate observations separately from force-law accuracy.

Review: `abstract-and-metadata`; Abstract; official README calibration and publication status. Verified 2026-10-11.

<a id="tacex"></a>
### TacEx: GelSight Tactile Simulation in Isaac Sim -- Combining Soft-Body and Visuotactile Simulators

**Duc Huy Nguyen et al. · 2024 · P1 · direct**  
CoRL 2024 Learning Robot Fine and Dexterous Manipulation workshop; verified paper/workshop attribution, not main-track CoRL.

[Paper / primary source](https://arxiv.org/abs/2411.04776) · [Author project](https://sites.google.com/view/tacex) · [Code](https://github.com/DH-Ng/TacEx)

- **Problem:** Integrate contact mechanics and tactile observations in Isaac Sim/Lab.
- **Inputs:** PhysX/GIPC state, gel deformation and rendered RGB/markers. **Conditioning:** Actions; rigid-compliant or soft gel model; optical/marker calibration.
- **Output:** GelSight observations and RL rollouts.
- **World-model contribution (assessment):** Modular physics/optics/marker pipeline; exposes backend tradeoffs.
- **Reported evidence:** Stable pushing, lifting and pole-balancing simulation and policy training.
- **Limits / transfer assessment:** Paper primarily establishes simulation usability. Built-in soft-body friction caused grasp slip; expensive GIPC limits parallelism. Broad real transfer remains unproven.
- **Repository connection:** Example for organizing eventual solver and observation modules; not evidence for current Stage A mechanics.

Review: `full-text-sections`; Abstract; Appendix B backend choice; Appendix C integration. Verified 2026-10-11.

<a id="tacsl"></a>
### TacSL: A Library for Visuotactile Sensor Simulation and Learning

**Iretiayo Akinola et al. · 2024 · P1 · direct**  
IEEE Transactions on Robotics 2025; verified NVIDIA Research publication page.

[Paper / primary source](https://arxiv.org/abs/2408.06506) · [Author project](https://iakinola23.github.io/tacsl/) · [Code](https://github.com/isaac-sim/IsaacGymEnvs/tree/tacsl)

- **Problem:** Scale visuotactile simulation and policy training on GPUs.
- **Inputs:** Simulator contacts, tactile RGB and normal/shear force fields. **Conditioning:** Robot actions, sensor models and contact-intensive task configuration.
- **Output:** Synthetic touch observations and trained multimodal policies.
- **World-model contribution (assessment):** Scalable observation/dynamics integration and policy evaluation toolkit.
- **Reported evidence:** Simulation speed benchmarks, multimodal/distillation comparisons and real peg placement/insertion transfer.
- **Limits / transfer assessment:** Fast approximate contact model; benchmark throughput and task success do not prove arbitrary-surface force fidelity.
- **Repository connection:** Relevant after mechanics and dynamics validation, when a matched tactile control experiment becomes justified.

Review: `abstract-and-metadata`; Abstract; project task descriptions; NVIDIA publication metadata. Verified 2026-10-11.

<a id="taccel"></a>
### Taccel: Scaling Up Vision-based Tactile Robotics via High-performance GPU Simulation

**Yuyang Li et al. · 2025 · P1 · direct**  
2025 arXiv manuscript; current official citation remains preprint (peer-reviewed venue not verified).

[Paper / primary source](https://arxiv.org/abs/2504.12908) · [Author project](https://taccel-simulator.github.io/) · [Code](https://github.com/Taccel-Simulator/Taccel)

- **Problem:** Scale coupled robot, gel and object contact simulation.
- **Inputs:** IPC/FEM gel state; affine robot/object state; tactile rendering. **Conditioning:** Robot-sensor geometry, material/contact parameters and actions.
- **Output:** Coupled physical trajectories and optical touch.
- **World-model contribution (assessment):** High-throughput compliant contact backend for later large-scale experiments.
- **Reported evidence:** GPU parallel benchmarks and object-recognition, grasping and articulated-manipulation sim-to-real demonstrations.
- **Limits / transfer assessment:** Hardware/configuration-specific speed; calibrated materials remain necessary. General brief-probe material inference is not established.
- **Repository connection:** Potential later backend after a restricted force law is validated; scaling alone cannot resolve Stage A clock/calibration gaps.

Review: `abstract-and-metadata`; Abstract; official project concepts, examples and citation. Verified 2026-10-11.

<a id="tacchi-2"></a>
### Tacchi 2.0: A Low Computational Cost and Comprehensive Dynamic Contact Simulator for Vision-based Tactile Sensors

**Yuhao Sun et al. · 2025 · P1 · direct**  
2025 first arXiv manuscript; revised Sensors and Actuators A: Physical article 117856, 2026, with changed author list; publisher verified.

[Paper / primary source](https://arxiv.org/abs/2503.09100)

- **Problem:** Extend low-cost MPM sensor simulation to dynamic marker images.
- **Inputs:** Elastomer particle motion and optical camera projection. **Conditioning:** Pressing, sliding and rotation; camera/sensor calibration.
- **Output:** Tactile, marker-motion and joint image sequences.
- **World-model contribution (assessment):** Time-varying observation layer for shear/slip rather than static indentation alone.
- **Reported evidence:** 2026 journal revision reports simulated-training dynamic/slip recognition evaluated on real data.
- **Limits / transfer assessment:** Recognition transfer demonstrates observation utility, not absolute force accuracy or contact-parameter uniqueness. Camera calibration is required.
- **Repository connection:** Later optical sensing extension; current acceleration probes require separate cross-sensor validation.

Review: `abstract-and-metadata`; First-manuscript abstract/metadata; publisher 2026 abstract and highlights (doi:10.1016/j.sna.2026.117856). Verified 2026-10-11.

<a id="tacauchy"></a>
### TaCauchy: An Extensible FEM Framework for Vision-Based Tactile Simulation

**Hengfei Zhao et al. · 2026 · P1 · direct**  
Accepted IROS 2026 according to arXiv/official code; proceedings publication not independently verified.

[Paper / primary source](https://arxiv.org/abs/2606.20426) · [Code](https://github.com/figsama/TaCauchy)

- **Problem:** Expose stress, pressure and tangential traction in Isaac tactile simulation.
- **Inputs:** UIPC FEM deformation; real normal-force/image pairs. **Conditioning:** Sensor geometry, hyperelastic parameters, contact and optical calibration.
- **Output:** Cauchy stress, surface traction, pressure and tactile images.
- **World-model contribution (assessment):** Useful explicit mechanical supervision interface; 'ground truth' is model-computed, not automatically real-world truth.
- **Reported evidence:** Six real pressing trials; simulated indentation adjusted to match measured force, followed by image comparison; multi-sensor simulations.
- **Limits / transfer assessment:** Force matching is an input to image validation, not independent unknown-force prediction. Real tangential-force/rollout validation is unestablished.
- **Repository connection:** Adopt explicit forces as later outputs; retain held-out force tests instead of using image SSIM as mechanics validation.

Review: `full-text-sections`; Sections III-C, IV-A–IV-D; especially IV-B force-matching protocol. Verified 2026-10-11.

<a id="optical-physics-rendering"></a>
### Simulation of Vision-based Tactile Sensors using Physics based Rendering

**Arpit Agarwal et al. · 2020 · P2 · direct**  
ICRA 2021; verified Carnegie Mellon publication page.

[Paper / primary source](https://arxiv.org/abs/2012.13184) · [Author project](https://labs.ri.cmu.edu/robotouch/tactile-optical-simulation/) · [Code](https://github.com/Robo-Touch/tactile_optical_simulation)

- **Problem:** Model GelSight optical image formation from first-principles light transport.
- **Inputs:** Sensor/object meshes and deformation geometry. **Conditioning:** Illumination, optics, reflective coating and contact geometry.
- **Output:** Rendered GelSight contact images.
- **World-model contribution (assessment):** Separates photometric sensor fidelity from mechanical dynamics.
- **Reported evidence:** Real-versus-rendered image similarity evaluation and component analysis.
- **Limits / transfer assessment:** Accurate optical parameters are needed; rendering comparisons establish observation fidelity, not force-law accuracy or mechanics identification.
- **Repository connection:** A physics-inspired renderer may complement future mechanics; Stage A spectra alone do not establish dynamics.

Review: `abstract-and-metadata`; Abstract; Carnegie Mellon publication metadata and official code README. Verified 2026-10-11.

<a id="simtac"></a>
### SimTac: A Physics-Based Simulator for Vision-Based Tactile Sensing with Biomorphic Structures

**Xuyang Zhang et al. · 2025 · P2 · direct**  
Cyborg and Bionic Systems 2026, article 0510; verified arXiv journal reference and author project citation.

[Paper / primary source](https://arxiv.org/abs/2511.11456) · [Author project](https://xuyangzhang0223.github.io/SimTac/)

- **Problem:** Simulate curved, biomorphic tactile sensor shapes.
- **Inputs:** MPM deformation, FEM training targets, real images/markers. **Conditioning:** Shape, optical system, elastomer properties and contact geometry.
- **Output:** Optical responses and neural mechanical-response fields.
- **World-model contribution (assessment):** Morphology-aware mechanics/observation bridge beyond planar gels.
- **Reported evidence:** FEM-reference force/deformation tests, real marker/image comparisons, prototypes and perception sim-to-real tasks.
- **Limits / transfer assessment:** Mechanical network targets are primarily FEM reference, distinct from independently measured real force fields. New materials require fine-tuning; code marked to release.
- **Repository connection:** Future sensor-geometry expansion after fixed-contact calibration; no automatic acceleration-to-curved-optical transfer.

Review: `abstract-and-metadata`; Abstract; author project simulation principles, performance and material fine-tuning. Verified 2026-10-11.

<a id="reduced-order-tactile-simulation"></a>
### Reduced-order Neural Modeling with Differentiable Simulation for High-Detail Tactile Perception

**Yuhu Guo et al. · 2026 · P2 · direct**  
2026 arXiv manuscript; author metadata lists IEEE RoboSoft 2026 (proceedings not independently verified).

[Paper / primary source](https://arxiv.org/abs/2605.05053)

- **Problem:** Recover fine tactile geometry without full-resolution simulation.
- **Inputs:** Paired coarse/fine MPM states; real GelSight indentation images. **Conditioning:** Fixed constitutive settings and low-speed indentation.
- **Output:** Fine displacement/deformation fields, tactile rendering and differentiable latent reconstruction.
- **World-model contribution (assessment):** Reduced-order surrogate can accelerate a validated mechanics observation model.
- **Reported evidence:** Eight-object real image benchmark; simulated depth reconstruction and runtime/ablation comparisons.
- **Limits / transfer assessment:** Paper explicitly restricts contact to quasi-static/low-speed indentation, fixed materials/lighting and geometry; absolute forces and rapid sliding are outside demonstrated scope.
- **Repository connection:** Potential later renderer/surrogate; unsuitable evidence for the current sliding-friction or long-horizon dynamics claims.

Review: `full-text-sections`; Sections IV-A–IV-F; V limitations. Verified 2026-10-11.

<a id="physics-foundations"></a>
## Physics solvers, contact mechanics and learned simulation

Numerical infrastructure and contact/constitutive assumptions for state evolution. These are enabling physics papers rather than tactile sensing results.

| Paper | Year | Priority / relevance | Output |
| --- | --- | --- | --- |
| [MuJoCo: A physics engine for model-based control](#mujoco) | 2012 | P0 / enabling | Forces and next physical states. |
| [An Unconstrained Convex Formulation of Compliant Contact](#sap-compliant-contact) | 2021 | P0 / enabling | Contact impulses/forces and motion using an unconstrained convex solve. |
| [A New Model for Control of Systems with Friction](#lugre-friction-1995) | 1995 | P1 / enabling | Dynamic friction force. |
| [A Moving Least Squares Material Point Method with Displacement Discontinuity and Two-Way Rigid Body Coupling](#mls-mpm) | 2018 | P1 / enabling | Particle/grid evolution, deformation and coupled body motion. |
| [DiffTaichi: Differentiable Programming for Physical Simulation](#difftaichi) | 2019 | P1 / enabling | Rollouts, parameter gradients and optimized controllers. |
| [Learning to Simulate Complex Physics with Graph Networks](#graph-network-simulator) | 2020 | P1 / enabling | Particle accelerations and autoregressive trajectories. |
| [Incremental Potential Contact: Intersection- and Inversion-free, Large-Deformation Dynamics](#incremental-potential-contact) | 2020 | P1 / enabling | Stable implicitly integrated deformation and contact forces. |
| [DiffPD: Differentiable Projective Dynamics](#diffpd) | 2021 | P1 / enabling | Deformable trajectories and gradients using projective dynamics. |
| [No Free Slide: Spurious Contact Forces in Incremental Potential Contact](#no-free-slide) | 2023 | P1 / enabling | Contact-force behavior with reduced irregularities. |
| [ChainQueen: A Real-Time Differentiable Physical Simulator for Soft Robotics](#chainqueen) | 2018 | P2 / enabling | Soft-body rollouts and gradients. |
| [Learning Mesh-Based Simulation with Graph Networks](#meshgraphnets) | 2020 | P2 / enabling | Next mesh states and adaptive simulation rollouts. |
| [PlasticineLab: A Soft-Body Manipulation Benchmark with Differentiable Physics](#plasticinelab) | 2021 | P2 / enabling | Deformation rollouts and trajectory-optimization gradients. |

<a id="mujoco"></a>
### MuJoCo: A physics engine for model-based control

**Emanuel Todorov et al. · 2012 · P0 · enabling**  
IROS 2012; verified IEEE publisher and official repository citation.

[Paper / primary source](https://ieeexplore.ieee.org/document/6386109/) · [Author project](https://mujoco.org/) · [Code](https://github.com/google-deepmind/mujoco)

- **Problem:** Efficient articulated forward/inverse dynamics with contact.
- **Inputs:** Known state, geometry, masses and mechanical parameters. **Conditioning:** Controls, generalized coordinates and contact constraints.
- **Output:** Forces and next physical states.
- **World-model contribution (assessment):** An existing solver for validating inferred contact parameters before creating a new engine.
- **Reported evidence:** Dynamics throughput and model-based-control examples; forward/inverse contact formulation.
- **Limits / transfer assessment:** Engine contact parameters approximate a specified contact. Default friction is not validated for the repository's surfaces; texture spectra are not force parameters.
- **Repository connection:** First Stage C integration candidate; compare prescribed-motion force and independently responsive motion separately.

Review: `abstract-and-metadata`; Publisher abstract/metadata; official repository; Drake contact-model discussion. Verified 2026-10-11.

<a id="sap-compliant-contact"></a>
### An Unconstrained Convex Formulation of Compliant Contact

**Alejandro Castro et al. · 2021 · P0 · enabling**  
IEEE Transactions on Robotics, online 2022; volume 39(2), 2023. Issue verified by IEEE RAS contents.

[Paper / primary source](https://arxiv.org/abs/2110.10107) · [Author project](https://drake.mit.edu/doxygen_cxx/group__drake__contacts.html) · [Code](https://github.com/RobotLocomotion/drake)

- **Problem:** Robustly resolve compliant friction, stiction and contact transitions.
- **Inputs:** Mechanical state, geometry and compliant-contact parameters. **Conditioning:** Applied forces/actions and time-step/contact model.
- **Output:** Contact impulses/forces and motion using an unconstrained convex solve.
- **World-model contribution (assessment):** Transparent force model and robust solver alternative for calibrated contact.
- **Reported evidence:** Accuracy/convergence benchmarks and interactive robotic manipulation simulations.
- **Limits / transfer assessment:** Convex approximations must be characterized; numerical convergence does not establish real material identification or sensor calibration.
- **Repository connection:** Stage C alternative when compliance/stiction matters; initially validate simpler continuous sliding mechanics.

Review: `abstract-and-metadata`; Abstract; official Drake contact discussion and references. Verified 2026-10-11.

<a id="lugre-friction-1995"></a>
### A New Model for Control of Systems with Friction

**Carlos Canudas de Wit et al. · 1995 · P1 · enabling**  
IEEE Transactions on Automatic Control 40(3), 1995.

[Paper / primary source](https://www.lunduniversity.lu.se/publication/0c411ed4-a01c-41e2-852c-6586fa9295e7)

- **Problem:** Modeling friction with internal contact memory.
- **Inputs:** Relative motion; contact internal state is modeled rather than directly sensed. **Conditioning:** Velocity and identified friction parameters.
- **Output:** Dynamic friction force.
- **World-model contribution (assessment):** Offers an interpretable alternative when constant Coulomb friction cannot explain presliding/hysteresis.
- **Reported evidence:** Analysis and simulations capture Stribeck behavior, stiction and friction-observer/control properties.
- **Limits / transfer assessment:** Not tactile learning; requires adequate excitation and parameter identification. A single constant-speed probe cannot identify the whole law.
- **Repository connection:** Begin with simpler Coulomb/viscous baselines and add this model only for measured residual structure.

Review: `abstract-and-metadata`; Original abstract and publisher-PDF indexed text; author institutional publication metadata Verified 2026-10-11.

<a id="mls-mpm"></a>
### A Moving Least Squares Material Point Method with Displacement Discontinuity and Two-Way Rigid Body Coupling

**Yuanming Hu et al. · 2018 · P1 · enabling**  
ACM Transactions on Graphics / SIGGRAPH 2018; verified author page and code.

[Paper / primary source](https://yzhu.io/publication/mpmmls2018siggraph/paper.pdf) · [Author project](https://yzhu.io/publication/mpmmls2018siggraph/) · [Code](https://github.com/yuanming-hu/taichi_mpm)

- **Problem:** Efficiently simulate varied materials and rigid/deformable coupling.
- **Inputs:** Particle state, deformation and grid state. **Conditioning:** Constitutive models, boundaries and rigid-body interactions.
- **Output:** Particle/grid evolution, deformation and coupled body motion.
- **World-model contribution (assessment):** Mechanical foundation for Tacchi, DiffTactile and differentiable material simulators.
- **Reported evidence:** Cutting, discontinuities and two-way coupling simulations; faster stress-discretization formulation.
- **Limits / transfer assessment:** Requires constitutive/contact parameters and resolution choices; no tactile measurement or brief-probe material inference demonstration.
- **Repository connection:** Longer-term soft-object expansion after fixed-geometry force validation.

Review: `abstract-and-metadata`; Author project abstract, metadata and code link. Verified 2026-10-11.

<a id="difftaichi"></a>
### DiffTaichi: Differentiable Programming for Physical Simulation

**Yuanming Hu et al. · 2019 · P1 · enabling**  
ICLR 2020; verified author publication page and official repository.

[Paper / primary source](https://arxiv.org/abs/1910.00935) · [Author project](https://yuanming.taichi.graphics/publication/2020-difftaichi/) · [Code](https://github.com/taichi-dev/difftaichi)

- **Problem:** Implement efficient differentiable physical simulators.
- **Inputs:** Programmed simulator state and parameterized controllers. **Conditioning:** Physical laws, actions and differentiable model parameters.
- **Output:** Rollouts, parameter gradients and optimized controllers.
- **World-model contribution (assessment):** Implementation substrate for mechanics inference rather than a learned tactile model itself.
- **Reported evidence:** Ten simulator examples with speed/productivity and gradient-based control experiments.
- **Limits / transfer assessment:** Autodifferentiation does not resolve non-identifiability, sensor calibration or inaccurate contact assumptions.
- **Repository connection:** Useful for a small differentiable contact-law prototype after obtaining force/motion data.

Review: `abstract-and-metadata`; Abstract; author venue metadata; official examples README. Verified 2026-10-11.

<a id="graph-network-simulator"></a>
### Learning to Simulate Complex Physics with Graph Networks

**Alvaro Sanchez-Gonzalez et al. · 2020 · P1 · enabling**  
ICML 2020, PMLR 119; verified author paper and publication page.

[Paper / primary source](https://arxiv.org/abs/2002.09405) · [Author project](https://sites.google.com/view/learning-to-simulate) · [Code](https://github.com/deepmind/deepmind-research/tree/master/learning_to_simulate) · [Data / release](https://github.com/deepmind/deepmind-research/tree/master/learning_to_simulate)

- **Problem:** Learn particle dynamics across interacting material systems.
- **Inputs:** Recent particle states and particle/material information. **Conditioning:** Physical state, boundaries and global context.
- **Output:** Particle accelerations and autoregressive trajectories.
- **World-model contribution (assessment):** A learned dynamics architecture with rollout evaluation, beyond tactile observation generation.
- **Reported evidence:** Fluid/rigid/deformable simulations; long rollouts and larger particle counts than training.
- **Limits / transfer assessment:** Training uses simulator trajectories, not sparse touch. Official project shows long-rollout solid deformation and spurious wall sticking; new real contact laws need validation.
- **Repository connection:** Potential residual/surrogate dynamics after force/motion data; current spectra do not observe complete physical state.

Review: `abstract-and-metadata`; Abstract; author ICML paper metadata; official project generalization and failure examples; supplementary runtime excerpts. Verified 2026-10-11.

<a id="incremental-potential-contact"></a>
### Incremental Potential Contact: Intersection- and Inversion-free, Large-Deformation Dynamics

**Minchen Li et al. · 2020 · P1 · enabling**  
ACM Transactions on Graphics / SIGGRAPH 2020; verified author project and paper.

[Paper / primary source](https://ipc-sim.github.io/file/IPC-paper-fullRes.pdf) · [Author project](https://ipc-sim.github.io/) · [Code](https://github.com/ipc-sim/IPC)

- **Problem:** Prevent intersections/inversions in frictional deformable contact.
- **Inputs:** Finite-element positions/velocities and collision geometry. **Conditioning:** Constitutive law, material parameters, boundary conditions and friction.
- **Output:** Stable implicitly integrated deformation and contact forces.
- **World-model contribution (assessment):** Core compliant-contact backend underlying TacIPC and Taccel.
- **Reported evidence:** Large-contact stress tests, accuracy/convergence comparisons and a physical impact example.
- **Limits / transfer assessment:** Robust geometry guarantees concern the discretized model, not real force fidelity. Barrier/discretization artifacts can matter for sliding.
- **Repository connection:** Needed when calibrated gel/object deformation warrants FEM; check tangential artifacts before learning friction.

Review: `full-text-sections`; Abstract; Sections 2 and 5 contact/friction; author project benchmarks. Verified 2026-10-11.

<a id="diffpd"></a>
### DiffPD: Differentiable Projective Dynamics

**Tao Du et al. · 2021 · P1 · enabling**  
ACM Transactions on Graphics 41(2), 2022; first manuscript 2021; verified author project.

[Paper / primary source](https://arxiv.org/abs/2101.05917) · [Author project](https://diffpd.csail.mit.edu/) · [Code](https://github.com/mit-gfx/diff_pd_public)

- **Problem:** Accelerate implicit differentiable soft-body simulation.
- **Inputs:** Soft-body state and real-scene data for identification. **Conditioning:** Material/contact parameters, actions and boundary constraints.
- **Output:** Deformable trajectories and gradients using projective dynamics.
- **World-model contribution (assessment):** Efficient inverse-mechanics/calibration alternative when compliance is central.
- **Reported evidence:** System identification, design, trajectory/control benchmarks and real-to-sim contact/collision example.
- **Limits / transfer assessment:** Contact approximation and constitutive/model choices remain relevant; no brief tactile support benchmark or universal material identification.
- **Repository connection:** A Stage B/C compliance option after indentation and fixture calibration are measured.

Review: `abstract-and-metadata`; Abstract; official publication/code metadata. Verified 2026-10-11.

<a id="no-free-slide"></a>
### No Free Slide: Spurious Contact Forces in Incremental Potential Contact

**Yinwei Du et al. · 2023 · P1 · enabling**  
2023 arXiv manuscript verified; publication venue not independently verified.

[Paper / primary source](https://arxiv.org/abs/2308.01696)

- **Problem:** Discretized surfaces can create artificial tangential contact resistance.
- **Inputs:** Contact meshes and forward/inverse test cases. **Conditioning:** Surface discretization and smooth surface/contact representations.
- **Output:** Contact-force behavior with reduced irregularities.
- **World-model contribution (assessment):** Critical warning: inferred friction may absorb solver artifacts rather than material behavior.
- **Reported evidence:** Forward/inverse benchmarks demonstrate tangential-force irregularities and advantages of smooth contacting surfaces.
- **Limits / transfer assessment:** Numerical examples concern particular representations; material calibration and real tactile measurements remain separate.
- **Repository connection:** Add mesh/time-step and frictionless sliding sanity checks to Stage C before attributing resistance to a surface.

Review: `full-text-sections`; Abstract; Section 4.3 available author-paper excerpts. Verified 2026-10-11.

<a id="chainqueen"></a>
### ChainQueen: A Real-Time Differentiable Physical Simulator for Soft Robotics

**Yuanming Hu et al. · 2018 · P2 · enabling**  
ICRA 2019; verified author page and official repository.

[Paper / primary source](https://arxiv.org/abs/1810.01054) · [Author project](https://www.andrewspielberg.com/chainqueen-a-real-time-differentiable-physical-simulator-for-soft-robotics) · [Code](https://github.com/yuanming-hu/ChainQueen)

- **Problem:** Differentiate deformable-body simulation for inference/control/design.
- **Inputs:** MLS-MPM particle state and model parameters. **Conditioning:** Forces, controls and physical/design parameters.
- **Output:** Soft-body rollouts and gradients.
- **World-model contribution (assessment):** Early foundation for fitting mechanics and optimizing actions through simulation.
- **Reported evidence:** Forward/gradient precision tests and soft-robot control with many decision variables.
- **Limits / transfer assessment:** Soft-robot simulations do not establish tactile identification; released repository is explicitly legacy and directs users toward DiffTaichi.
- **Repository connection:** Conceptual gradient-based calibration precedent; not the preferred immediate code dependency.

Review: `abstract-and-metadata`; Abstract; author publication metadata; repository legacy warning. Verified 2026-10-11.

<a id="meshgraphnets"></a>
### Learning Mesh-Based Simulation with Graph Networks

**Tobias Pfaff et al. · 2020 · P2 · enabling**  
ICLR 2021; verified official author project.

[Paper / primary source](https://arxiv.org/abs/2010.03409) · [Author project](https://sites.google.com/view/meshgraphnets) · [Code](https://github.com/deepmind/deepmind-research/tree/master/meshgraphnets) · [Data / release](https://github.com/deepmind/deepmind-research/tree/master/meshgraphnets)

- **Problem:** Learn mesh-based mechanics with adaptive discretization.
- **Inputs:** Mesh graph, physical node states and boundary conditions. **Conditioning:** Geometry, connectivity and physical state.
- **Output:** Next mesh states and adaptive simulation rollouts.
- **World-model contribution (assessment):** A surrogate for calibrated gel/object deformation at varying resolution.
- **Reported evidence:** Aerodynamics, structural-mechanics and cloth simulation benchmarks; larger/altered geometries and speed comparisons.
- **Limits / transfer assessment:** Simulator-trained surrogate; detailed friction, real tactile inference and unknown material identifiability are not established.
- **Repository connection:** Later soft-body surrogate; begin with an interpretable restricted sliding law instead.

Review: `abstract-and-metadata`; Abstract; official project experiment and code/dataset links. Verified 2026-10-11.

<a id="plasticinelab"></a>
### PlasticineLab: A Soft-Body Manipulation Benchmark with Differentiable Physics

**Zhiao Huang et al. · 2021 · P2 · enabling**  
ICLR 2021 spotlight; verified arXiv author metadata.

[Paper / primary source](https://arxiv.org/abs/2104.03311) · [Author project](https://plasticinelab.csail.mit.edu/) · [Code](https://github.com/hzaskywalker/PlasticineLab)

- **Problem:** Benchmark manipulation of elastic/plastic deformable materials.
- **Inputs:** Simulator states and goal configurations. **Conditioning:** Manipulator actions and differentiable material dynamics.
- **Output:** Deformation rollouts and trajectory-optimization gradients.
- **World-model contribution (assessment):** Tests downstream usefulness of a deformable dynamics model.
- **Reported evidence:** RL versus gradient-based task comparisons; gradients solve many tasks quickly but struggle with multistage planning.
- **Limits / transfer assessment:** Simulation-only benchmark; deformable manipulation success cannot replace real tactile/contact calibration.
- **Repository connection:** Later Stage D task ideas if soft-material mechanics become validated; unnecessary for the first slider experiment.

Review: `abstract-and-metadata`; Abstract; official benchmark tasks and metadata. Verified 2026-10-11.

## Maintaining this dictionary

Edit the canonical JSON, retain stable paper IDs, verify new claims against primary sources, and regenerate the two views:

```powershell
python scripts/build_paper_dictionary.py
python scripts/build_paper_dictionary.py --check
```

The original six-entry [related-work comparison](related_work.csv) remains a historical snapshot of the brief-contact study. This dictionary is the current broader literature index.
