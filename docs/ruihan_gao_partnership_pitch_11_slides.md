# Tactile Worlds — Partnership Pitch for Ruihan Gao

Prepared 11 October 2026. **Exactly 11 slides**, including the opening and closing slides. Suggested speaking time: 15–20 minutes, followed by discussion.

Audience: **Ruihan Gao**, the tactile generation and haptic-rendering researcher whose [official research page](https://ruihangao.github.io/) lists Controllable Visual-Tactile Synthesis, Tactile DreamFusion and PAT3D. ObjectFolder is related work by **Ruohan Gao and collaborators**; it is not attributed to Ruihan in this pitch.

The meeting objective is to explore building this together: propose a concrete research partnership, state the cofounder ambition clearly, and agree on the next joint working step. The commercial case remains a hypothesis.

Copy each slide's **title**, **status**, and **on-slide text** into the presentation. Keep its reference footer with that slide. Read the speaker notes as preparation, not as slide copy. Everything after Slide 11 is presenter preparation and is **not an additional slide**.

Your confirmed contribution: **time, a computer science and data science background**, and the existing repository as a starting asset. Proposed responsibilities below are invitations to agree a division of work; they do not imply committed hours, funding, hardware access or customer traction.

Visual assets and source figures: [slide-by-slide visual guide](presentation_assets/README.md), including three original concept illustrations, the saved development chart and primary-source paper figures.

Presentation: [standalone HTML slides](ruihan_gao_partnership_pitch.html). Open in a browser; arrows navigate, N opens notes, F requests fullscreen, and O opens the overview. Images are embedded for offline presentation.

## Slide 1 — Tactile Worlds: A Proposal to Build Together

**Purpose:** Make the ambition and the partnership intention clear immediately.

**Status on slide:** Long-term vision and partnership proposal

**On-slide text:**

**A simulated room whose objects have measurable, reusable tactile properties.**

An embodied agent could predict what it would feel and what would physically happen when it presses, slides or grasps.

**My goal:** build this with you, beginning with a focused joint study and exploring a cofounder partnership.

**Speaker notes:**

“I want to explore building a tactile layer for simulated worlds, where objects carry reusable surface representations and interactions produce meaningful sensory and physical outcomes. I am approaching this with a company ambition, and I want the first step to be a research problem we can define and test together. My reason for speaking with you is that your work directly connects tactile content, 3D generation and physical scenes.”

## Slide 2 — Why I Want to Build This with You

**Purpose:** Connect the invitation to Ruihan's actual work, with a specific candidate extension.

**Status on slide:** Your published work and a proposed connection

**On-slide text:**

| Your work | Foundation for this proposal |
| --- | --- |
| Controllable Visual-Tactile Synthesis | Joint visual/tactile content and haptic rendering |
| Tactile DreamFusion | Spatial 3D texture fields and different textures across regions |
| PAT3D, as a coauthor | Physics-assisted, simulation-ready scene generation |

**The question I would like us to investigate:** can these tactile assets support accurate sensory and physical predictions under specified interactions?

**Reference footer:** [Controllable Visual-Tactile Synthesis, ICCV 2023](https://arxiv.org/abs/2305.03051); [Tactile DreamFusion, NeurIPS 2024](https://arxiv.org/abs/2412.06785); [PAT3D, ICLR 2026](https://arxiv.org/abs/2511.21978). Venue information is also listed on Ruihan's [official research page](https://ruihangao.github.io/).

**Speaker notes:**

“Tactile DreamFusion already gives us spatial texture fields and regional texture assignment, so I would treat that as a foundation. Your visual-tactile synthesis work connects content to haptic rendering, and PAT3D connects generated content to physical scene arrangement. I would like us to investigate what additional measurements and modeling make those assets reliable during temporal interactions. I want you to help shape that research question and the eventual product direction.”

## Slide 3 — The Research Question I Want Us to Answer

**Purpose:** Define an assessable contribution beyond displaying tactile-looking geometry.

**Status on slide:** Proposed research question

**On-slide text:**

**Can a reusable surface asset predict both touch and physical response under new interactions?**

| Question | Testable output |
| --- | --- |
| What would the sensor feel? | Action-dependent tactile observations |
| What would the contact do? | Independently validated forces and motion |
| What can we reuse? | Transfer across locations and known object geometries |

**Candidate contribution:** an experimentally validated interface between tactile assets and contact dynamics.

**Speaker notes:**

“The core question is whether a reusable asset supports predictions under interactions we did not use to fit it. We would evaluate sensory response, physical behavior and asset reuse separately. A spatial texture field is an existing idea; our proposed study concerns its interface with measured interaction dynamics and the conditions under which reuse works. A literature review and the first experiment would determine the eventual novelty claim.”

## Slide 4 — Existing Results Make the Direction Credible

**Purpose:** Establish feasibility through complementary demonstrations without claiming the complete system exists.

**Status on slide:** Reported results in specific research settings

**On-slide text:**

| Precedent | What it demonstrates |
| --- | --- |
| ObjectFolder 2.0 | Queryable multisensory object assets and perception transfer |
| Heravi et al. | Interaction-conditioned tactile vibration rendering |
| TACTO / DiffTactile | Sensor rendering / differentiable contact simulation |
| RoboPack | Tactile-informed dynamics prediction and manipulation |

**Evidence for the ingredients. Our proposed integration still needs validation.**

**Reference footer:** [ObjectFolder 2.0, CVPR 2022](https://arxiv.org/abs/2204.02389); [Heravi et al., ToH 2024](https://arxiv.org/abs/2212.13332); [TACTO, RA-L 2022](https://arxiv.org/abs/2012.08456); [DiffTactile, 2024](https://arxiv.org/abs/2403.08716); [RoboPack, RSS 2024](https://arxiv.org/abs/2407.01418).

**Speaker notes:**

“These papers provide evidence that the main components are feasible in their reported settings. ObjectFolder gives object-centric sensory assets, Heravi gives interaction-conditioned vibration, and the simulation papers provide rendering or contact mechanics. RoboPack shows that tactile information can be useful for predicting motion and planning. We can build on these components while testing our own consistency, transfer and runtime claims.”

## Slide 5 — What I Bring Today

**Purpose:** Show concrete starting assets and your contribution without overstating progress.

**Status on slide:** Confirmed background and current repository

**On-slide text:**

- **Time and a computer science / data science background.**
- Existing brief-touch spectral prediction pipeline and probe protocols.
- Retrieval, fixed-feature and encoder baselines with reproducible evaluation.
- A curated tactile research map and a documented mechanics study proposal.

**Current finding:** retrieval is stronger than the encoder in the matched development comparison.

**Next capability:** registered surface measurements and calibrated physical prediction.

**Reference footer:** [Repository audit](repository_research_audit.md); [matched development, 10 October 2026](matched_development_review.md). Ten training specimens, two repeatedly exposed development specimens; physical timing remains unverified.

**Speaker notes:**

“I can commit time and bring my computer science and data science background to implementation and evaluation. The repository already contains an observation-prediction pipeline and strong controls, giving us a concrete starting point. Its development results favor retrieval, and we have no calibrated force, motion or room-simulation result to claim. I propose to lead software implementation, data processing and reproducible experiments while we jointly define the representation and validation.”

## Slide 6 — The System We Could Build Together

**Purpose:** Describe the initial shared technical contract and show how it can grow into a world model.

**Status on slide:** Proposed architecture

**On-slide text:**

| Layer | Responsibility |
| --- | --- |
| Surface asset | Geometry, spatial texture descriptors, supported mechanical descriptors and uncertainty |
| Contact dynamics | Use local properties and the contacting pad/tool to predict forces and next state |
| Sensor readout | Convert predicted contact conditions into calibrated tactile observations |
| Learned world model | Predict future states and touch under candidate actions |

**Build on an existing physics engine. Start with one known probe and bounded conditions.**

**Speaker notes:**

“We should jointly choose an asset and contact interface that an existing engine can use. The contacting pad or tool has geometry and compliance that affect mechanics, while its optical or electrical readout can be modeled separately. During a full rollout, contact speed and force must come from predicted dynamics, rather than future measurements. The learned world model becomes a later consumer or surrogate of a validated simulation interface.”

## Slide 7 — First Joint Study: A Reusable Surface Asset

**Purpose:** Offer a small research project with concrete deliverables and a path to the room vision.

**Status on slide:** Proposed experiment; acquisition feasibility to resolve

**On-slide text:**

**Question:** can measured surface patches retain useful predictions when reused on known rigid objects?

**Start:** one fixed probe, registered patches, known geometry and mass, measured normal load and bounded sliding conditions.

**Deliverables**

- Registered tactile and independent-force measurements.
- A surface-asset format and one engine integration.
- Held-out prediction results, baselines and documented failure cases.

**Then:** reuse familiar patches on a second geometry and compose a small scene.

**Speaker notes:**

“The first study would make a small set of measured patches queryable at known locations and interaction conditions. We would select the sensor and confirm acquisition feasibility together before fixing a schedule. A second geometry tests reuse, and assembling objects into a scene tests composition; unfamiliar materials remain a separate question. A room demonstration would grow from this interface once the measurements support it.”

## Slide 8 — Evidence That Would Make Us Continue

**Purpose:** Make the collaboration credible through clear decision gates.

**Status on slide:** Proposed evaluation gates

**On-slide text:**

| Gate | Evidence required |
| --- | --- |
| Reliable acquisition | Verified timing, contact registration and independent forces |
| Useful surface model | Held-out tactile and force predictions against strong baselines |
| Physical transfer | Freely responding motion and reuse on a second geometry |
| Practical integration | Measured latency, memory and acquisition cost |

**Controls:** retrieval, object-specific models, shared surface models and minimal calibrated mechanics.

**Agree practical accuracy targets before final testing.**

**Speaker notes:**

“We need a result that survives strong baselines and independent measurements, including condition-only and force-only versus force-plus-tactile comparisons. An accurate simple model would be a useful outcome; additional learning should address an observed limitation. Prescribed sliding can validate forces, while motion validation requires an independently responding body with known mass, initial state and actuation. We should agree the necessary accuracy and cost from the intended use, then freeze the final evaluation.”

## Slide 9 — A Product Thesis Worth Testing

**Purpose:** Explain the possible company without inventing market validation.

**Status on slide:** Commercial hypothesis, not demonstrated demand

**On-slide text:**

**Hypothesis:** robotics and simulation teams may value reusable tactile assets that reduce their calibration and data-collection work.

**First candidate offering:** a measured material library and calibrated integration for one engine and one sensor.

**Potential compounding value:** validated measurements, reusable calibration and reliable integrations.

**Validation needed:** target users, required accuracy, time saved and willingness to pay.

**Speaker notes:**

“The first candidate product is a usable asset library and integration supported by measurement, with a narrow sensor and engine scope. Whether that saves enough work to support a company is still a hypothesis. Alongside the research prototype, I propose learning from potential users about the interactions they cannot currently simulate and the accuracy they need. A positive technical result and real demand would justify expanding toward room-scale assets and additional embodiments.”

## Slide 10 — How We Could Work Together

**Purpose:** Make the proposed complementarity and decision process concrete.

**Status on slide:** Proposed roles, to agree together

**On-slide text:**

| Partner | Proposed responsibility |
| --- | --- |
| Me | Software implementation, data pipelines, experiment execution and reproducibility |
| Ruihan | Co-lead representation, tactile generation and research/evaluation design |
| Together | Choose the first study, resolve acquisition feasibility and evaluate product value |

**Start with a bounded joint study and a shared decision gate.**

**Explore cofounder roles as we establish technical evidence and working fit.**

**Speaker notes:**

“I would like to take responsibility for the implementation and evaluation work, drawing on my computer science and data science background. Your work makes representation and tactile generation a natural area to co-lead, but I want the division of work and research agenda to reflect your interests. We would agree scope, responsibilities, available time and an achievable milestone together. That gives us a concrete way to evaluate a research partnership and explore building a company.”

## Slide 11 — An Invitation to Build Together

**Purpose:** Ask directly for partnership and end with a concrete next action.

**Status on slide:** Partnership invitation

**On-slide text:**

**I want to explore building this company with you.**

If a research partnership is the right starting point, I want to begin there.

**Today's ask**

- Co-shape the first research question and surface representation.
- Define the acquisition setup, roles and evaluation gate.
- Agree a next working session and a first concrete deliverable.

**Long-term ambition:** reusable tactile assets for physically interactive simulated worlds.

**Speaker notes:**

“I am interested in you as a potential cofounder because this direction connects closely with your work, and I want you to help define what it becomes. I would also welcome a research partnership as the first step. If the direction interests you, I would like us to choose one small study and set a working session to specify its representation, measurements and responsibilities. That would give us a concrete basis for deciding how to build together.”

---

# Presenter Preparation — Not Additional Slides

## What changed for this meeting

The narrative now gives the audience a reason to build with you: a specific connection to Ruihan's work, your confirmed contribution, a bounded joint study and an explicit founding invitation. The room remains the vision, with whole-body somatosensation as a later extension. The initial product and commercial value are labeled hypotheses.

## Claims to keep precise

- **Ruihan and Ruohan are different researchers.** Ruihan's work anchors Slide 2. ObjectFolder belongs to the related-work evidence in Slide 4.
- **Spatial tactile fields are existing work.** Tactile DreamFusion already includes a 3D texture field and different textures across regions. The proposed contribution concerns experimentally validated interaction prediction, calibration and reuse.
- **Generated surface detail is not a calibrated force law.** Optical normals, acceleration spectra and independently measured forces are different signals. Aligning these channels needs acquisition and validation.
- **Sensor readout can be modular; contact mechanics must represent the contacting tool.** Pad geometry and compliance can change contact behavior. Friction is contact-pair-dependent; vibration also depends on the probe, object and fixture.
- **A differentiable model can support fitting, without guaranteeing identification.** The first study should estimate only descriptors supported by its measurements and excitation.
- **Rendering and full prediction have different input contracts.** A renderer can be tested with measured contact conditions. A full action-conditioned rollout must predict those future conditions.
- **Reuse and new-material generalization are separate claims.** A new scene assembled from familiar assets demonstrates composition. Additional holdouts are required for unfamiliar surfaces.
- **Current evidence is developmental.** The existing predictor outputs 96 log-band-power values. Retrieval is stronger in the matched development comparison, physical timing remains unresolved, and force/motion/room results remain future work. See the [repository audit](repository_research_audit.md) and [matched report](matched_development_review.md).
- **The room-scale computation strategy is a proposal.** Detailed local rendering around active contacts may help runtime, but its accuracy and scaling need measurement.
- **Commercial value is unverified.** No customer demand, revenue, funding, proprietary dataset ownership, special hardware access or commercial advantage is asserted by this deck.

## Questions to be ready for

**“What is new relative to Tactile DreamFusion?”**

“The spatial field is an existing foundation. I propose studying the additional representation, paired measurements and contact interface needed for sensory trajectories and physical predictions under held-out interactions. We would determine the novelty claim together through focused related-work review and results.”

**“What can you contribute personally?”**

“Time and a computer science and data science background. I propose to lead software implementation, data processing and reproducible experiments, starting with the repository's existing pipeline and baselines. We should agree the actual time commitment and first milestone together.”

**“Do you have the required rig and measurements?”**

“The current work uses acceleration recordings for spectral prediction. A registered, synchronized acquisition setup with independent force measurements remains to be established. Confirming that setup is the first feasibility gate.”

**“Why build a company around this?”**

“The candidate value is reducing the work required to create and calibrate tactile assets for simulation. We need evidence that target users have that problem and would adopt or pay for a solution. I want to test that alongside the technical prototype.”

**“What if retrieval or simple mechanics wins?”**

“We should keep the simpler method if it meets accuracy and cost requirements. The research outcome can identify what transfers and what requires calibration. Reusable, validated assets can be useful even when their best predictor is simple.”

**“Why start with one probe?”**

“It lets us control contact geometry and sensor mechanics while testing the asset interface. Cross-sensor transfer becomes a separate experiment after that interface works; optical surface normals and vibration spectra alone do not establish arbitrary sensor transfer.”

**“How does this become a room or a world model?”**

“Validated assets can be placed on known objects and composed into scenes, with local tactile computation activated at contact. A learned model can then predict candidate-action outcomes using simulated and real interactions. Both room runtime and predictive accuracy require their own tests.”

**“What would agreeing today mean?”**

“Agreement to a next working session that chooses the first question, measurements, responsibilities and decision gate. The founding ambition is explicit, and the working collaboration gives us evidence for deciding how far to take it.”

## How the pasted overview was used

The supplied overview contributed the long-term vision of a material representation, tactile simulation layer and somatosensory world model. Its broad stack is a roadmap. This pitch uses verified primary sources for selected evidence and omits unsupported absence-of-prior-work claims, universal physical/sensor transfer, whole-body capability, speculative sensor costs and commercial certainty.

## Presentation emphasis

Spend the most time on Slides 2, 3, 7 and 10–11: the personal research connection, the question, the first joint study and the invitation. Keep the external literature concise; Ruihan should have space to reshape the proposal. The immediate outcome to seek is a shared research direction and a next working session.
