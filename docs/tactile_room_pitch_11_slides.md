# Tactile Worlds: A Room We Can Touch

Exactly 11 slides, including the title and closing slide. Prepared 11 October 2026 from the current repository review and cited primary research. Suggested duration: 15–20 minutes. Copy the title, status and on-slide text onto each slide; use the speaker notes orally. Reference footers belong on their associated slide and do not require an additional references slide. All proposed demonstrations remain future work.

## Slide 1 — Tactile Worlds: A Room We Can Touch

**Status on slide:** Long-term research vision

**On-slide text:**

**Spatial texture representations for physics simulation and action-conditioned world models**

Goal: build a simulated room where every object's surfaces produce tactile observations and physical responses appropriate to the contact and action.

Examples: sliding across a table, pressing a cushion, grasping a cup.

**Speaker notes:**

“We want tactile properties to become reusable scene assets alongside geometry and visual appearance. An agent should be able to ask what it would feel, and what would physically happen, if it interacted with a surface. The room is our long-term goal; this presentation proposes the representation and experiments needed to work toward it.”

## Slide 2 — What Does It Mean to Simulate Touch?

**Status on slide:** Targets for the proposed system

**On-slide text:**

| Target | What the simulator should predict |
| --- | --- |
| Tactile observation | Vibration, pressure or optical sensor response |
| Contact mechanics | Forces, deformation and slip |
| Physical outcome | Object motion under the chosen action |

Responses depend on surface location, contacting tool or sensor, load, motion and relevant history.

Each target requires its own validation.

**Speaker notes:**

“A tactile texture describes how a surface responds during an interaction. The measured signal depends on the sensor, and friction depends on the contacting material pair and conditions. We need separate evidence for realistic observations, accurate forces and accurate motion; success on one target does not establish the others.”

## Slide 3 — Existing Research Demonstrates the Ingredients

**Status on slide:** Reported demonstrations in cited research

**On-slide text:**

| Research | Demonstrated ingredient |
| --- | --- |
| ObjectFolder 2.0 | Queryable multisensory object assets and perception transfer |
| Heravi et al. | Interaction-conditioned texture vibration rendering |
| TACTO | Optical tactile rendering using external physics |
| DiffTactile | Differentiable contact and tactile sensor simulation |
| RoboPack | Tactile-informed dynamics prediction and manipulation |

These results support the components. Their integration and room-scale tactile fidelity remain to be tested in our proposed system.

**Reference footer:** [ObjectFolder 2.0, CVPR 2022](https://arxiv.org/abs/2204.02389); [Heravi et al., IEEE Transactions on Haptics 2024](https://arxiv.org/abs/2212.13332); [TACTO, RA-L 2022](https://arxiv.org/abs/2012.08456); [DiffTactile, 2024](https://arxiv.org/abs/2403.08716); [RoboPack, RSS 2024](https://arxiv.org/abs/2407.01418).

**Speaker notes:**

“ObjectFolder provides a direct precedent for storing tactile information with an object, while Heravi's work shows interaction-conditioned vibration rendering. TACTO and DiffTactile contribute sensor simulation and contact modeling, and RoboPack shows that tactile information can support future-state prediction and manipulation. These demonstrations make the direction credible, but each has its own tested scope and none constitutes validation of our proposed architecture.”

## Slide 4 — Our Current Starting Point

**Status on slide:** Implemented here, with development evidence

**On-slide text:**

- Input: brief acceleration support spectra plus requested speed, direction and nominal load.
- Output: 96 log-band-power values describing vibration energy.
- Implemented: retrieval, fixed-feature and encoder baselines, with reproducible evaluation machinery.
- Current development results favor retrieval over the encoder.
- Still needed: spatial surface maps, calibrated mechanics, engine coupling and motion rollouts.

**Reference footer:** Current repository audit and matched development report, 10 October 2026. Ten training specimens and two repeatedly exposed development specimens. Physical timing remains unverified.

**Speaker notes:**

“Our existing work studies how brief observations predict another contact's vibration spectrum. It provides an observation-model starting point and strong baselines, rather than a finished surface asset or physical simulator. Retrieval currently outperforms the encoder in the matched development comparison, and the two exposed evaluation specimens do not establish broad generalization. We have no force or motion results to claim today.”

**Source links:** [Repository audit](repository_research_audit.md); [matched development report](matched_development_review.md).

## Slide 5 — Proposed Representation: A Tactile Surface Atlas

**Status on slide:** Proposed representation

**On-slide text:**

Store surface information in object coordinates.

| At each surface region | Representation |
| --- | --- |
| Local surface structure | Geometry, texture descriptor and directionality |
| Mechanical behavior | Calibrated descriptors where measurements support them |
| Confidence | Measured or inferred status, uncertainty and valid conditions |

Example: one mug with smooth sides, a rough base and a rubber grip.

Sensor calibration stays separate. Contact mechanics depend on both contacting materials.

**Speaker notes:**

“A spatial atlas lets different parts of one object produce different responses, and its coordinates follow the object as it moves. We can begin with a simple patch map before testing a continuous learned field. Texture descriptors and mechanical parameters have different meanings, so we should include friction or compliance estimates only where measurements justify them.”

## Slide 6 — Acquiring Surface Assets from Real Objects

**Status on slide:** Proposed acquisition pipeline

**On-slide text:**

1. Obtain object geometry and register contact locations.
2. Record tactile signals with synchronized motion, load and timing.
3. Fit surface descriptors from measured contact patches.
4. Use shared material models or interpolation for unmeasured regions, with uncertainty.

Independent force measurements are required to calibrate mechanics.

Open question: how much measurement does a reusable asset require?

**Speaker notes:**

“We propose combining known geometry with registered tactile samples, rather than assuming every surface point has already been measured. Shared material models may reduce acquisition, but inferred regions must remain distinguishable from measured ones. Acquisition coverage, calibration and hardware access are feasibility questions we still need to resolve.”

## Slide 7 — Connecting the Surface Atlas, Physics and World Model

**Status on slide:** Proposed architecture

**On-slide text:**

| Component | Inputs | Outputs |
| --- | --- | --- |
| Physics engine | Scene state, actuator command and local contact properties | Contact conditions, forces and next state |
| Tactile renderer | Predicted contact conditions, surface atlas and sensor calibration | Predicted tactile observations |
| Learned world model | Scene representation, surface assets and candidate actions | Predicted future states and touch |

Observation query: predict touch given contact conditions.

Full rollout: predict contact conditions, motion and touch from an action.

**Speaker notes:**

“The physics engine evolves the scene and provides the contact state used by the tactile renderer. A learned world model could approximate these outcomes for efficient planning, using simulated and real interactions for training and validation. During a full rollout, actual contact velocity and force must come from predicted dynamics; using future measured conditions would conceal dynamics errors.”

## Slide 8 — Proposed Strategy for Room-Scale Simulation

**Status on slide:** Untested design assumption

**On-slide text:**

- Room: body dynamics and collision geometry.
- Object: spatial surface assets in local coordinates.
- Active contact: detailed tactile rendering and selected deformation modeling.
- Shared surface models: reuse measured assets across objects and scenes.

Assumption: selective local detail can make room-scale simulation practical.

Unknown: accuracy, latency and memory as active contacts increase.

**Speaker notes:**

“Our proposed scaling strategy concentrates tactile detail around contact patches while retaining scene-level dynamics. Reusable surface assets could populate several objects without fitting every object independently. This is an architectural assumption, so we must benchmark total runtime and check whether the local approximation preserves the interactions we care about.”

## Slide 9 — What Remains Unproven

**Status on slide:** Research hypotheses and current limits

**On-slide text:**

- Sparse touches provide enough information for unfamiliar surfaces and actions.
- Spatial descriptors transfer across locations and object geometries.
- One asset supports consistent tactile observations and physical behavior.
- The combined system remains practical in multi-object scenes.

Current limits: physical clock calibration, new spatial/mechanical measurements and independent held-out evaluation.

**Speaker notes:**

“These are the claims we need to test, rather than results we already have. A room assembled from familiar assets demonstrates composition; unfamiliar materials require a separate generalization test. We also need to resolve measurement timing and collect the force and motion data missing from the current study before making physical-accuracy claims.”

## Slide 10 — First Validation: One Object with Several Textures

**Status on slide:** Proposed experiment

**On-slide text:**

**Setup:** one known rigid geometry, three measured surface patches, one probe and bounded sliding conditions.

| Test | Required evidence |
| --- | --- |
| Tactile prediction | Held-out locations, speeds, loads and directions |
| Spatial representation | Patch-boundary continuity and transfer to another geometry |
| Contact mechanics | Independently measured forces and freely responding motion |

Baselines: retrieval, one descriptor per object, spatial atlas and unconditioned rendering.

Keep training and test specimens/sessions separate.

**Speaker notes:**

“The first experiment tests the interface that a room would reuse, with a small measured surface library. We compare the atlas with simpler models and evaluate both familiar-material transfer and independently held-out contacts. Prescribed sliding can validate force response; motion validation needs an object that responds to known actuation, with no future state corrections. Existing spectral data supports the observation study, while spatial and mechanical validation require additional measurements.”

## Slide 11 — Proposed Contribution and Next Step

**Status on slide:** Research proposal

**On-slide text:**

**Contribution to test:** reusable spatial surface models with consistent tactile and physical predictions.

**Milestones**

1. Validate measured surface patches.
2. Demonstrate heterogeneous objects and transfer.
3. Assemble and benchmark a tactile room.
4. Evaluate action-conditioned prediction and planning.

**Immediate collaboration:** representation design, acquisition/calibration and physics-engine integration.

**Speaker notes:**

“The long-term outcome is a room assembled from reusable tactile assets that an agent can interact with and predict. The immediate proposal is a surface representation, an acquisition strategy and a first validation experiment grounded in existing research. I would like feedback on the representation and support in identifying a calibrated setup for that experiment.”
