# Tactile Worlds — Research Introduction

Historical 11-slide version. The HTML now uses the [12-slide scientific pitch](tactile_worlds_research_pitch_12_slides.md).

Prepared 12 October 2026. **Exactly 11 slides**, including the opening and closing slides. This presentation explains the intended system, current evidence, relevant references and the proposed implementation sequence.

The HTML is rebuilt at the existing [presentation path](ruihan_gao_partnership_pitch.html) so the already-open file can be reloaded. Its filename is retained for compatibility; its content is a research introduction. The earlier partnership script is historical and no longer supplies the HTML.

Copy each title, status and on-slide text onto its slide. Reference footers and illustration captions stay visible. Speaker notes elaborate the content. Proposed architecture and experiments are distinguished from existing repository results and reported prior work.

## Slide 1 — Tactile Worlds: A Room We Can Touch

**Purpose:** Introduce the intended system and its initial scope.

**Status on slide:** Long-term research vision

**On-slide text:**

**A simulated room whose objects have spatially varying tactile properties.**

The goal is to predict what an embodied agent would feel and how objects would physically respond when it presses, slides or grasps.

**Starting scope:** measured surface patches, known rigid geometry, one probe and bounded interactions.

**Speaker notes:**

“I want tactile properties to become reusable scene assets alongside geometry and visual appearance. The intended system combines physical interaction with the sensory response of a specified probe. The room is the long-term goal, while the first implementation focuses on a small set of measured surfaces and controlled interactions.”

## Slide 2 — What Tactile Simulation Must Predict

**Purpose:** Define separate targets and their dependencies.

**Status on slide:** System requirements

**On-slide text:**

| Target | Required prediction |
| --- | --- |
| Tactile observation | Vibration, pressure or optical sensor response |
| Contact mechanics | Forces, deformation and slip |
| Object motion | Position and velocity under the action |

Responses depend on surface location, the contacting pad/tool, load, relative motion and relevant history.

**Sensor realism, physical accuracy and computational cost require separate tests.**

**Speaker notes:**

“Texture is experienced through an interaction, so a static material label is only a starting descriptor. Contact mechanics depend on the material pair, geometry and conditions, and the sensor adds its own mechanics and readout. I will assess tactile observations, forces and resulting motion separately rather than treating one convincing output as evidence for all three.”

## Slide 3 — Existing Building Blocks

**Purpose:** Establish what related research has demonstrated for assets and scenes.

**Status on slide:** Reported results in cited settings

**On-slide text:**

| Research | Relevant demonstrated component |
| --- | --- |
| Tactile DreamFusion | Spatial 3D texture fields and regional texture assignment |
| Visual-Tactile Synthesis | Joint visual/tactile content and haptic rendering |
| ObjectFolder 2.0 | Queryable multisensory object assets and perception transfer |
| PAT3D | Physics-assisted, simulation-ready scene arrangement |

**These are foundations for the representation and scene pipeline. Accurate temporal contact prediction remains a separate validation target.**

**Reference footer:** [Tactile DreamFusion, NeurIPS 2024](https://arxiv.org/abs/2412.06785); [Controllable Visual-Tactile Synthesis, ICCV 2023](https://arxiv.org/abs/2305.03051); [ObjectFolder 2.0, CVPR 2022](https://arxiv.org/abs/2204.02389); [PAT3D](https://arxiv.org/abs/2511.21978).

**Speaker notes:**

“Spatial tactile fields and regional texture assignment already exist in Tactile DreamFusion. Visual-Tactile Synthesis and ObjectFolder supply complementary content and sensory-asset precedents, while PAT3D contributes physically arranged scenes. The proposed direction builds on these results and tests the additional interface needed for interaction-dependent observations and independently measured physical outcomes.”

## Slide 4 — Proposed Representation: A Surface Atlas

**Purpose:** Explain what an object asset contains and what needs calibration.

**Status on slide:** Proposed representation

**On-slide text:**

**Store surface information in object coordinates.**

| At each surface region | Stored information |
| --- | --- |
| Surface structure | Local geometry, texture descriptor and directionality |
| Response descriptors | Sensory model and supported mechanical descriptors |
| Validity | Measured or inferred status, uncertainty and calibrated conditions |

One object can contain several materials. Contact laws depend on the material pair; sensor readout is calibrated separately.

**Reference footer:** Representation precedents: [Tactile DreamFusion](https://arxiv.org/abs/2412.06785); [ObjectFolder 2.0](https://arxiv.org/abs/2204.02389). Vibration-response precedent: [Heravi et al., ToH 2024](https://arxiv.org/abs/2212.13332).

**Speaker notes:**

“The atlas follows the object when it moves and lets different regions have different properties. I would start with explicit material patches before testing a continuous learned field. A texture feature or generated normal map is not automatically a friction or compliance measurement; physical descriptors enter the asset only where acquisition and excitation support them.”

## Slide 5 — What the Current Repository Provides

**Purpose:** State current implementation and evidence without implying a completed simulator.

**Status on slide:** Implemented observation study; development evidence

**On-slide text:**

- **Input:** brief acceleration supports plus speed, direction and nominal load.
- **Output:** 96 log-band-power values describing vibration energy.
- **Methods:** retrieval, fixed-feature and encoder baselines.
- **Current result:** retrieval is stronger than the encoder in the matched development comparison.

**Missing:** spatial maps, calibrated contact laws, engine coupling and motion rollouts.

**Reference footer:** [Repository audit](repository_research_audit.md); [matched development, 10 October 2026](matched_development_review.md). Ten training specimens and two repeatedly exposed development specimens. Physical timing remains unverified.

**Speaker notes:**

“The current code predicts another contact's vibration spectrum from brief support observations and requested conditions. It supplies an observation-model starting point, baselines and reproducible evaluation machinery. Retrieval currently performs better than the encoder in this restricted development setting; the result does not establish broad generalization or physical identification. Registered surface acquisition and mechanics validation are proposed next steps.”

## Slide 6 — Connecting Physics and Sensor Simulation

**Purpose:** Define the contact-simulation interfaces.

**Status on slide:** Proposed architecture

**On-slide text:**

| Component | Responsibility |
| --- | --- |
| Scene state and action | Specify geometry, mass, pose, velocity and actuator/controller input |
| Local contact model | Query surface properties and the contacting pad/tool mechanics |
| Physics engine | Compute contact forces and next physical state |
| Sensor renderer | Generate tactile observations from predicted contact conditions |

**Use an existing engine. Initially fix the probe and model only supported channels.**

**Reference footer:** [TACTO](https://arxiv.org/abs/2012.08456); [Taxim](https://arxiv.org/abs/2109.04027); [DiffTactile](https://arxiv.org/abs/2403.08716). These approaches provide different rendering and contact-modeling precedents.

**Speaker notes:**

“The engine evolves the physical state, and the renderer predicts what a chosen sensor observes from that contact. The pad's geometry and compliance affect mechanics even when its optical or electrical readout is modeled separately. Requested velocity or load may be controller setpoints; actual contact velocity and force must follow from the dynamics. Vibration or thermal channels require their own models and calibration.”

## Slide 7 — First Acquisition and Calibration Pilot

**Purpose:** Describe the practical first experiment and its required measurements.

**Status on slide:** Proposed experiment; rig access unresolved

**On-slide text:**

**Setup:** a registered flat panel with several material patches and one known probe.

- Record acceleration, independent normal/tangential force, position and a verified acquisition clock.
- Vary speed, load and direction within a bounded sliding range.
- Hold out interaction conditions and acquisition sessions.
- Fit a tactile response model and minimal calibrated friction baseline.

**First deliverable:** a measured patch asset with independent tactile and force tests.

**Speaker notes:**

“This pilot extends the existing acceleration study with registered locations and independent mechanical measurements. The first feasibility step is confirming the rig, timing, force calibration and synchronization. Prescribed sliding can validate tactile and force response. A later known-mass, independently responding body is required to evaluate motion predictions.”

## Slide 8 — An Action-Conditioned Contact World Model

**Purpose:** Explain sequential prediction and distinguish it from a conditional renderer.

**Status on slide:** Proposed predictive interface

**On-slide text:**

**Predict contact outcomes under a specified future action sequence.**

| Interface | Content |
| --- | --- |
| Inputs | Current state/belief, tactile history, surface assets, contact partner and candidate actions |
| Outputs | Future object/contact states, forces and tactile observations |
| First implementation | Physics-engine rollouts with calibrated sensor rendering |
| Later option | Learned surrogate trained on synchronized actions and outcomes |

**Future contact velocity and load must come from predicted dynamics.**

**Reference footer:** Predictive precedents: [RoboPack, RSS 2024](https://arxiv.org/abs/2407.01418); [SPOTS](https://arxiv.org/abs/2304.11193); [Visuo-Tactile World Models](https://arxiv.org/abs/2602.06001).

**Speaker notes:**

“An observation renderer predicts touch when contact conditions are supplied. A full world-model rollout instead predicts those conditions and future motion from a candidate action sequence. I would first establish the engine-based transition and sensor interface, then test a learned surrogate for efficient prediction or planning. The current spectral dataset does not provide the complete synchronized state/action/outcome trajectories needed for that sequential model.”

## Slide 9 — Validation: Touch, Forces, Motion and Reuse

**Purpose:** Define independent evaluation questions and comparisons.

**Status on slide:** Proposed evaluation

**On-slide text:**

| Target | Evidence required |
| --- | --- |
| Tactile fidelity | Held-out spectra, waveforms or sensor images for the chosen modality |
| Force accuracy | Independently measured force trajectories |
| Motion accuracy | Freely responding position, velocity and stopping outcomes |
| Asset reuse | Held-out locations and geometry; new-material transfer tested separately |
| Practicality | Runtime, memory and full acquisition/probing cost |

**Controls:** conditions-only, retrieval, patch-specific, shared-surface and calibrated-physics baselines.

**Speaker notes:**

“Each target needs its own measurement and holdout. For physical inference, force-only versus force-plus-tactile comparisons help identify the additional information supplied by touch. Reusing familiar material patches on a new object tests composition and geometry transfer; unfamiliar material inference needs another test. Practical margins and the final protocol should be fixed before the final evaluation.”

## Slide 10 — Implementation Roadmap

**Purpose:** Show the sequence from the initial measurements to the room-scale goal.

**Status on slide:** Proposed staged implementation

**On-slide text:**

| Stage | Milestone |
| --- | --- |
| 1. Calibrated patches | Registered data and held-out tactile/force tests |
| 2. Heterogeneous objects | Validated assets on known geometry and distinct regions |
| 3. Asset library | Reusable schema, validity ranges and sensor calibration |
| 4. Room scenes | Composed objects with measured contact accuracy and runtime |
| 5. Predictive use | Multi-step rollouts and one planning benchmark |

**Scaling proposal:** scene-level body dynamics with detailed modeling near active contacts.

**Accuracy and runtime of this approximation remain to be tested.**

**Speaker notes:**

“The sequence builds evidence before expanding scope. I would first validate a small material library, then attach those assets to heterogeneous objects and compose scenes. Detailed local contact computation may make the room practical, but that is an architectural assumption requiring benchmarks. Additional sensors, bulk deformation and whole-body touch remain later extensions.”

## Slide 11 — Open Questions and First Target Outcome

**Purpose:** End with the immediate technical objective and the questions that determine its success.

**Status on slide:** Open research questions

**On-slide text:**

**First target: one measured heterogeneous surface asset with documented queries and independent tests.**

- How much measurement is needed to identify useful descriptors?
- Which descriptors transfer across locations, geometry and contact partners?
- How should sensory texture and physical calibration share a representation?
- What accuracy, acquisition cost and runtime tradeoffs are acceptable?

**Long-term outcome:** reusable tactile assets for action-conditioned simulation and prediction in room-scale worlds.

**Speaker notes:**

“The immediate objective is a measured asset and interface whose limitations and valid conditions are documented. The major open questions concern observability, reuse and the balance between accuracy and acquisition cost. The room-scale world becomes credible as those interfaces pass independent tests and compose into larger scenes. This is the research and implementation direction I am planning to pursue.”

---

# Presenter Preparation — Not Additional Slides

## Scope and evidence

The presentation introduces a research direction. No roles, founding invitation, partnership ask or commercial demand claim forms part of the slide content or speaker notes. The examples explain existing methods and the planned implementation.

Spatial texture fields already exist in prior work. Generated normals, calibrated force laws and time-dependent tactile observations require different evidence. The contacting pad/tool affects mechanics; sensor readout can be separated only with its calibration and mechanical effects accounted for.

The current repository is a developmental spectral observation study. It has no force/motion or room-simulation result, and physical timing remains unresolved. A conditional renderer evaluated with measured contact conditions must not be reported as a full action-conditioned physical rollout.

Reuse of familiar assets, new-material adaptation and transfer to another sensor are separate tests. Rig feasibility and synchronized mechanical acquisition must be resolved before fixing a prototype schedule.

## Practical reference groups

- **Assets and scenes:** Tactile DreamFusion, Controllable Visual-Tactile Synthesis, ObjectFolder 2.0 and PAT3D.
- **Tactile observations and contact:** Heravi's texture rendering, TACTO, Taxim and DiffTactile.
- **Predictive interfaces:** RoboPack, SPOTS and Visuo-Tactile World Models.
- **Current evidence:** [repository audit](repository_research_audit.md) and [matched development report](matched_development_review.md).

Source figures and original concept illustrations are retained in [presentation_assets](presentation_assets/README.md). All generated illustrations are labeled as concepts, and primary figures retain their credits.
