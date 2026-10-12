# Tactile Worlds — A Scientific Pitch

Prepared 12 October 2026. **Exactly 12 slides.** This is a research pitch about the goal, existing capabilities, the proposed gap and the work needed to test it. The [HTML deck](ruihan_gao_partnership_pitch.html) is built from this script. The existing HTML filename is retained so the open presentation can be reloaded.

## Story and pacing

Lead with the world we want to simulate. Make the target concrete before discussing papers. Then show four complementary capability groups: measurement and representations; sensory assets and scenes; contact simulation; predictive world models. Those results motivate a specific research question about reuse and physical validation. Present the proposed system, our actual starting point, the first study, the evidence that would convince us and the path to the room-scale goal.

Spend roughly 30–45 seconds on each opening slide, 45–60 seconds on each literature synthesis, and about a minute on each proposal slide. Paper names are signposts; explain the capability instead of reading the bibliography aloud. References on the slides link to primary sources. The HTML's **Papers / R** drawer includes the complete existing 99-paper catalog and three additional texture/scene references; it is supporting material, not an additional slide. This is a curated research map, not a claim of exhaustive coverage of every tactile paper.

## Slide 1 — Tactile Worlds: A Room We Can Touch

**Purpose:** Establish the ultimate goal immediately.

**Status on slide:** Ultimate goal

**On-slide text:**

**A simulated room where every object has a tactile surface.**

Wood grain, woven fabric, ceramic, rubber and metal become spatial surface assets.

An agent can press, slide or grasp—and predict both what it feels and how the object responds.

**Speaker notes:**

“I want to represent touch as a reusable property of a simulated world. Every object would carry surface information that changes across its regions, and interactions would produce both tactile observations and physical outcomes. The room is the ultimate goal; the research starts with a small, measured set of surfaces and one specified contact probe.”

## Slide 2 — The Same Surface Changes with the Action

**Purpose:** Explain why an interactive tactile world needs more than a texture label.

**Status on slide:** Problem definition

**On-slide text:**

**What happens if this agent touches this location, in this way?**

| Query | What the model must predict |
| --- | --- |
| Slide faster along a woven patch | Speed-dependent vibration and the resulting contact force |
| Press with a specified pad | Contact geometry, sensor response and supported deformation |
| Push a movable object | Slip and the resulting motion over time |

The response depends on the surface, contact partner, local geometry, action and history.

**The target is a consistent prediction of touch and physical state under future actions.**

**Reference footer:** Action-dependent texture: [Culbertson et al.](https://pubmed.ncbi.nlm.nih.gov/25248220/); [Heravi et al.](https://arxiv.org/abs/1909.13025). Future-state prediction: [RoboPack](https://arxiv.org/abs/2407.01418).

**Speaker notes:**

“The same material produces different measurements when the motion, load or contacting tool changes. A world model must answer a future-action query, including the contact conditions and motion caused by that action. That is why I separate sensory response, contact mechanics and state evolution, while requiring them to agree on the same interaction.”

## Slide 3 — We Can Already Measure and Represent Touch

**Purpose:** Summarize the measurement, data and inference tools available in the field.

**Status on slide:** Existing capabilities · results reported in specific settings

**On-slide text:**

| Available capability | Relevant papers and resources |
| --- | --- |
| Contact geometry, force and slip | GelSight; GelSlim 3.0 / 4.0; DIGIT; ReSkin; Digit 360 |
| Force and material inference | GelSlim inverse FEM; Tac3D; TacTID; GelSight hardness estimation |
| Measured texture and motion data | Penn HaTT; LMT; Cluster; MIT planar pushing |
| Transferable tactile features | Touch and Go; Sparsh / TacBench; T3; UniTouch; AnyTouch / AnyTouch 2 / ToucHD |

**Contribution:** measurement interfaces, data and reusable inference features.

Each modality has its own calibration; these resources provide different parts of the required evidence.

**Reference footer:** [GelSight](https://pmc.ncbi.nlm.nih.gov/articles/PMC5751610/); [GelSlim 3.0](https://arxiv.org/abs/2103.12269); [inverse FEM](https://arxiv.org/abs/1810.04621); [Tac3D](https://arxiv.org/abs/2202.06211); [TacTID](https://charon-bo.github.io/assets/PDF/TacTID.pdf); [Sparsh](https://arxiv.org/abs/2410.24090); [AnyTouch 2](https://arxiv.org/abs/2602.09617). Full titles and sources: Papers / R.

**Speaker notes:**

“There is already substantial infrastructure for acquiring and interpreting touch. Sensors recover local shape, deformation, force or slip, while datasets and encoders offer a starting point for sensory modeling. The important distinction is that estimating force or hardness from observed touch is different from predicting the response to a new action. The reviewed resources also provide different channels: I have not verified a single corpus containing registered brief probes, independently calibrated forces and freely responding motion for the same contact pairs.”

## Slide 4 — Tactile Assets and 3D Scenes Already Have Precedents

**Purpose:** Connect the room-scale ambition to existing representation and generation work.

**Status on slide:** Existing capabilities · sensory assets and scene construction

**On-slide text:**

**Spatial texture:** Tactile DreamFusion; Controllable Visual-Tactile Synthesis.

**Multisensory objects:** ObjectFolder; ObjectFolder 2.0; ObjectFolder Benchmark.

**Physics-assisted scenes:** PAT3D.

**Contribution:** tactile-guided geometry, queryable sensory assets and simulation-ready scene arrangements.

The next question is how an asset preserves measured contact response when reused in a new interaction.

**Reference footer:** [Tactile DreamFusion](https://arxiv.org/abs/2412.06785); [Visual-Tactile Synthesis](https://arxiv.org/abs/2305.03051); [ObjectFolder](https://arxiv.org/abs/2109.07991); [ObjectFolder 2.0](https://arxiv.org/abs/2204.02389); [ObjectFolder Benchmark](https://openaccess.thecvf.com/content/CVPR2023/papers/Gao_The_ObjectFolder_Benchmark_Multisensory_Learning_With_Neural_and_Real_Objects_CVPR_2023_paper.pdf); [PAT3D](https://arxiv.org/abs/2511.21978).

**Speaker notes:**

“Tactile DreamFusion already represents regional tactile textures on 3D objects, so spatial texture fields themselves are prior art. Visual-Tactile Synthesis connects generated content with haptic rendering. The ObjectFolder family supplies sensory object assets and task benchmarks, including traversal and dynamics work; PAT3D contributes physically arranged scenes. These results motivate building an asset pipeline, while leaving the measured force, temporal touch and motion behavior of our proposed assets to be tested.”

## Slide 5 — Contact Simulation and Texture Rendering Are Available

**Purpose:** Show that the proposed system can build on established numerical and sensory models.

**Status on slide:** Existing capabilities · simulation infrastructure

**On-slide text:**

| Building block | Relevant papers |
| --- | --- |
| Vibration from interaction conditions | Culbertson texture models; Heravi action-conditional / real-time rendering; HaptoFlow |
| Optical tactile rendering | TACTO; Taxim; FOTS |
| Contact and deformable sensor mechanics | DiffTactile; Efficient Tactile Simulation; TacIPC; Tacchi / Tacchi 2.0; TaCauchy |
| Simulator integration and throughput | TacSL; TacEx; Taccel |
| Numerical physics foundations | MuJoCo; SAP compliant contact; IPC; MLS-MPM; DiffTaichi; DiffPD |

**Contribution:** existing solvers, calibrated sensor models and routes to faster simulation.

Accuracy and validity still depend on the contact model, measurements and simulator settings.

**Reference footer:** [Heravi rendering](https://arxiv.org/abs/2212.13332); [TACTO](https://arxiv.org/abs/2012.08456); [DiffTactile](https://arxiv.org/abs/2403.08716); [Efficient Tactile Simulation](https://proceedings.mlr.press/v205/xu23b.html); [TacSL](https://arxiv.org/abs/2408.06506); [SAP](https://arxiv.org/abs/2110.10107). Full titles and sources: Papers / R.

**Speaker notes:**

“We can use existing infrastructure for both the physical solver and the sensor model. These approaches have different responsibilities: TACTO primarily renders optical observations with external mechanics, while DiffTactile and FEM-based methods model deformable contact more explicitly. Classical and learned vibration models address another sensory channel. The proposed work is to select a supported combination, calibrate its surface assets and test it independently; replacing every solver with a new neural model is unnecessary.”

## Slide 6 — World Models Already Use Touch to Predict Outcomes

**Purpose:** Establish the closest predictive prior work and clarify the proposed distinction.

**Status on slide:** Existing capabilities · prediction and planning

**On-slide text:**

| Research direction | Relevant papers |
| --- | --- |
| Action-conditioned tactile and visual prediction | Manipulation by Feel; SPOTS; Visuo-Tactile World Models; DexTouch-WM |
| Physical-state prediction and representation | RoboPack; ContactWorld; Compact Visuotactile World Models for Lifting |
| Exploration and action generation | Predictive Interactive Perception; OmniVTA; Dream-Tac; VT-WAM; TACO |

**Contribution:** touch can support future-state prediction, contact reasoning and task control.

**Our target:** reusable spatial surface assets with independently tested tactile, force and motion predictions.

**Reference footer:** [SPOTS](https://arxiv.org/abs/2304.11193); [RoboPack](https://arxiv.org/abs/2407.01418); [VT-WM](https://arxiv.org/abs/2602.06001); [ContactWorld](https://arxiv.org/abs/2606.13877); [DexTouch-WM](https://arxiv.org/abs/2609.20649). Recent work includes preprints; publication status and sources: Papers / R.

**Speaker notes:**

“Tactile world models already exist, and several papers demonstrate predictive or planning benefits in their tested tasks. RoboPack models physical outcomes using tactile information; SPOTS and VT-WM predict sensory futures under actions; ContactWorld studies representation choices; DexTouch-WM investigates human-to-robot contact data. The models in the action-generation group expose different interfaces, so I would inspect their conditioning before using them for counterfactual rollouts. My proposed target centers on reusable material regions, calibration and agreement between touch and physical outcomes.”

## Slide 7 — The Research Gap: Validated Reuse Across Interactions

**Purpose:** State a defensible gap that follows from the preceding capability map.

**Status on slide:** Proposed research target · synthesis of reviewed work

**On-slide text:**

**Can a measured surface asset predict touch and physical response across new interactions and known geometries?**

| What the field provides | What this project would need to establish |
| --- | --- |
| Spatial textures and sensory assets | Response preserved across held-out locations and known geometries |
| Calibrated contact and sensor models | Agreement with independent forces and freely responding motion |
| Predictive tactile models | Multi-step outcomes under specified future actions |
| Encoders and exploration methods | Useful adaptation with a measured acquisition budget |

**Research goal:** validated, action-dependent asset reuse with a specified contact partner.

**Reference footer:** Gap assessment from the [research synthesis](tactile_world_model_review.md) and [paper dictionary](paper_dictionary.md). Integration and world-model precedents exist; this is a proposed empirical target, not an established novelty claim.

**Speaker notes:**

“The gap I want to test is the reusable interface between a surface asset, a contact model and a predictive world. Each ingredient has prior work, and several systems already integrate touch with physics or planning. What remains to establish for this project is whether a measured asset retains useful sensory and physical accuracy across changed interactions and geometry, with a manageable calibration budget. Transfer to a different material or contact partner is a further experiment, rather than something implied by successful reuse.”

## Slide 8 — Surface Assets Drive Physics and Touch

**Purpose:** Make the proposal concrete and separate asset representation from transition and readout.

**Status on slide:** Proposed system

**On-slide text:**

**Surface → contact → physics → touch**

| Component | Proposed role |
| --- | --- |
| Surface atlas | Texture, local geometry, response descriptors and validity |
| Contact model | Couple surface, specified pad/tool and contact history |
| Physics engine | Predict states and forces under candidate actions |
| Sensor model | Predict readings from the evolving contact |

**First implementation:** engine rollouts. Test a learned surrogate later.

**Reference footer:** Representation: [Tactile DreamFusion](https://arxiv.org/abs/2412.06785), [ObjectFolder 2.0](https://arxiv.org/abs/2204.02389). Contact/readout: [DiffTactile](https://arxiv.org/abs/2403.08716), [TACTO](https://arxiv.org/abs/2012.08456). Prediction: [RoboPack](https://arxiv.org/abs/2407.01418).

**Speaker notes:**

“The atlas follows the object in object coordinates and lets different regions carry different properties. The physical law is conditioned on the contact pair; the sensor's mechanics and readout also require calibration. Geometry, mass, pose, velocity and controller inputs initialize an engine rollout, which predicts the contact conditions used by the sensor model. Generated normals are not automatically friction coefficients. Learned inference or a faster surrogate can be added once synchronized action/outcome data and independent tests support them.”

## Slide 9 — Our Starting Point Is a Tactile Observation Model

**Purpose:** Ground the proposal in actual repository work without overstating readiness.

**Status on slide:** Implemented starting point · development evidence

**On-slide text:**

**Brief acceleration observations + requested contact conditions → vibration spectrum**

- Predicts **96 log-band-power values**.
- Includes retrieval, fixed-feature and encoder comparisons.
- Retrieval currently outperforms the encoder in the matched development comparison.

**Next bridge:** registered surface locations and independent mechanical measurements.

**Reference footer:** [Repository audit](repository_research_audit.md); [matched development](matched_development_review.md). Ten training specimens; two repeatedly exposed development specimens. Timing remains unverified; no force or motion result.

**Speaker notes:**

“This repository gives us an implemented observation task and an evaluation foundation. It takes brief acceleration supports and a requested speed, direction and nominal load, then predicts a vibration spectrum. The saved development comparison favors retrieval, which is a reason to keep strong simple methods in the next study. This is an early component: spatial assets, calibrated mechanics, temporal rollouts and engine coupling are still proposed.”

## Slide 10 — First Study: Build One Measured Surface Asset

**Purpose:** Turn the gap into an executable acquisition and calibration study.

**Status on slide:** Proposed first study

**On-slide text:**

**One registered panel. Several material regions. One known probe.**

- Measure acceleration, independent normal/tangential force, position and synchronized time.
- Sweep bounded speeds, loads and directions; hold out conditions and sessions.
- Fit a sensory model and a minimal friction model; compare with retrieval and direct force fitting.
- Attach the measured regions to known geometry and test what transfers.

**Deliverable:** a queryable surface asset with documented calibration and uncertainty.

**Reference footer:** Acquisition: [Cluster](https://arxiv.org/html/2407.16206v4), [Penn HaTT](https://is.mpg.de/hi/publications/culbertson14-hs-texture). Calibration budget: [How Much Haptic Surface Data Is Enough?](https://www.cs.utexas.edu/~jsinapov/AAAI-SSS-2017/paper/Burka_AAAI_SSS_2017.pdf). Rig access and feasibility remain unresolved.

**Speaker notes:**

“The first study produces a measured asset, rather than attempting the entire room at once. I would confirm the rig, force calibration and clock, then register measurements to the surface and vary controlled interactions. The initial law stays simple enough to identify from the available excitation, with longer calibration costed separately. Prescribed sliding establishes tactile and force evidence; an independently responding body is added for motion validation. Curved geometry and new contact partners need their own tests.”

## Slide 11 — The Evidence That Would Make the Idea Convincing

**Purpose:** Define success and failure in terms of independent tests.

**Status on slide:** Proposed evaluation

**On-slide text:**

**Test the same calibrated asset across sensory and physical outcomes.**

| Claim | Required test |
| --- | --- |
| Predicts touch | Held-out sensory responses for the chosen modality |
| Predicts mechanics | Independent force trajectories and freely responding motion |
| Is reusable | Held-out locations and known geometries; new materials tested separately |
| Uses touch effectively | Force-only vs force-plus-tactile at matched acquisition cost |
| Supports a practical world | Multi-step rollout error, runtime and one planning task |

**Baselines:** retrieval, conditions-only, patch-specific models and calibrated physics.

**Reference footer:** [ContactWorld](https://arxiv.org/abs/2606.13877) motivates controlled representation comparisons; [RoboPack](https://arxiv.org/abs/2407.01418) motivates physical outcome evaluation. Test protocol and practical margins must be frozen before final scoring.

**Speaker notes:**

“A convincing demonstration needs agreement across several independent tests. A realistic tactile image or accurate spectrum would validate one output, while force and free motion require separate measurements. The tactile contribution is demonstrated only if it improves the relevant prediction over force-only and simple calibrated models at the same cost. If it does not, that tells us which component or acquisition strategy should change before expanding the system.”

## Slide 12 — From One Validated Surface to a Tactile World

**Purpose:** Close with the research path and the ultimate contribution.

**Status on slide:** Proposed roadmap

**On-slide text:**

**Make tactile behavior a reusable part of a simulated world.**

| Step | Evidence before expansion |
| --- | --- |
| Patches → heterogeneous object | Tactile and force fidelity, then independent motion |
| Objects → asset library | Transfer across locations and known geometries |
| Library → room scenes | Contact accuracy and measured runtime at scene scale |
| Scenes → predictive interaction | Multi-step action rollouts and one planning benchmark |

**Scaling hypothesis:** detailed computation near active contacts, with scene-level body dynamics.

**First milestone:** one measured asset. **Ultimate goal:** a room of objects with predictable tactile behavior.

**Reference footer:** Scaling and generalization of this architecture remain research questions. Paper library: Papers / R.

**Speaker notes:**

“The intended contribution is a validated path from measured tactile surfaces to reusable simulated objects and eventually a room. Each expansion has an evidence requirement, so the representation becomes more ambitious only when the sensory and physical tests support it. Computing local detail near active contacts is a plausible scaling strategy that must be benchmarked. The first concrete result is one asset that predicts touch and physical response; the longer-term goal is a world in which those assets compose.”

---

# Presenter Preparation — Supporting Material, Not Extra Slides

## Why this story works

Slides 1–2 establish the ambition and the query the system must answer. Slides 3–6 show why the proposal is plausible: the field has measurement tools, asset representations, simulation methods and predictive models. Slide 7 identifies the proposed contribution without claiming the ingredients are new. Slide 8 makes the architecture understandable; Slide 9 gives an honest starting point. Slides 10–11 describe the first study and how to judge it. Slide 12 connects those tests back to the room-scale ambition.

The key statement to repeat is: **“A reusable surface asset should predict what an agent feels and what physically happens under a specified action.”**

## Evidence boundaries to preserve in discussion

- Spatial texture fields and tactile world models already exist. The proposed novelty is not their existence; reuse, calibration, joint outcome validation and acquisition efficiency are candidate contributions requiring further comparison.
- Sensory descriptors, generated geometry and mechanical coefficients have different meanings. Contact laws depend on the material pair, geometry, state and excitation; the sensor affects both mechanics and readout.
- Current repository findings use two repeatedly exposed development specimens. Physical timing is unresolved, and no calibrated force, independent motion or engine result exists.
- Prescribed trajectories validate force and observation response. Freely responding motion needs a known initial state, geometry, mass, actuator/controller and independent motion measurement.
- Reusing familiar materials on a new object, adapting to new materials and transferring to another sensor or tool are separate experiments.
- Future-action-conditioned rollouts and joint action-generation models have different interfaces. A renderer supplied with measured future force or velocity is not a complete action-conditioned physical rollout.

## Reference coverage

The slide names select the closest and most useful exemplars from all branches of the current research map. The HTML embeds the full existing [99-paper catalog](paper_dictionary.md), including sensor foundations, contact-state inference, texture models, representations, dynamics, active touch, tactile simulation and numerical physics. Three additional references cover texture generation and scene construction:

- [Tactile DreamFusion: Exploiting Tactile Sensing for 3D Generation](https://arxiv.org/abs/2412.06785).
- [Controllable Visual-Tactile Synthesis](https://arxiv.org/abs/2305.03051).
- [PAT3D: Physics-Augmented Text-to-3D Scene Generation](https://arxiv.org/abs/2511.21978).

The canonical catalog records publication status and review depth. A reported result is evidence in the paper's tested setting; this documentation work has not reproduced it. The catalog is curated and includes enabling and adjacent work. The three added asset/scene papers were checked against their primary manuscripts and author resources in preparing these slides.

## Visuals and controls

Reuse the room concept on Slide 1, DreamFusion/PAT3D figures on Slide 4, the surface-atlas concept on Slide 8, the saved development chart on Slide 9 and the proposed rig on Slide 10. Original illustrations remain labeled as AI-generated concepts; primary figures keep credits. Arrow keys navigate, N opens notes, O opens the overview, R opens the paper library and F requests fullscreen.
