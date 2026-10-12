# Tactile Contact Research

We study how a robot can learn about a new contact after a few short touches, then use that information to predict forces, movement and tactile readings. The long-term goal is an **action-conditioned contact world model connected to a physics engine**.

**Current status — 11 October 2026:** this repository implements brief-touch **vibration-spectrum prediction** and checked development comparisons. Force identification, physical motion simulation and robot control are later milestones.

## Contents

- [Research map and paper dictionary](#research-map-and-paper-dictionary)
- [What we currently have](#what-we-currently-have)
- [Current findings and limits](#current-findings-and-limits)
- [Path to a physics world model](#path-to-a-physics-world-model)
- [Explore and reproduce](#explore-and-reproduce)
- [Maintain the literature catalog](#maintain-the-literature-catalog)

## Research map and paper dictionary

Start with the **[99-paper dictionary and table of contents](docs/paper_dictionary.md)**. Each entry records the problem, inputs/actions, outputs, reported evidence, potential contribution to a world model, limitations, repository connection and primary-source links. It distinguishes direct contributions from enabling methods and adjacent ideas, and records publication status and reading depth.

- **[Research synthesis and recommended next steps](docs/tactile_world_model_review.md):** how the literature fits together, closest prior work, dataset readiness and implementation order.
- **[Repository research audit](docs/repository_research_audit.md):** what the code and saved results establish, with links to the evidence.
- **[Canonical JSON dictionary](docs/paper_dictionary.json)** and **[filterable CSV](docs/paper_dictionary.csv):** searchable versions of the same catalog.
- **[12-slide scientific pitch](docs/ruihan_gao_partnership_pitch.html)** and **[speaker script](docs/tactile_worlds_research_pitch_12_slides.md):** the room-scale tactile vision, existing capabilities, research gap and proposed studies. The HTML includes a paper-library drawer.

| Literature branch | Papers | Role in the goal |
| --- | ---: | --- |
| [Sensor foundations and observability](docs/paper_dictionary.md#foundations-sensors) | 21 | Make geometry, deformation, pressure and contact observable |
| [Contact state, force and parameter identification](docs/paper_dictionary.md#force-state-identification) | 6 | Infer slip, force, pose and effective mechanics |
| [Texture datasets and vibration models](docs/paper_dictionary.md#datasets-texture-rendering) | 11 | Predict tactile observations under different motions and loads |
| [Tactile representations and multisensory data](docs/paper_dictionary.md#representations-multimodal) | 14 | Build transferable perception and inference features |
| [Predictive dynamics and world models](docs/paper_dictionary.md#predictive-world-models) | 12 | Predict outcomes under future actions |
| [Active exploration and tactile control](docs/paper_dictionary.md#active-touch-control) | 7 | Select useful probes and test task benefit |
| [Tactile simulation and calibration](docs/paper_dictionary.md#tactile-simulation) | 16 | Model sensor deformation and generate tactile readings |
| [Physics and learned simulation foundations](docs/paper_dictionary.md#physics-foundations) | 12 | Compute contact forces and evolve physical state |

The catalog covers foundational work and recent papers through **11 October 2026**. It is a curated map for this goal; broader entries receive abstract/metadata review, while the closest papers receive targeted full-text review. A complete [reading path](docs/paper_dictionary.md#recommended-reading-path) starts with Cluster, Heravi, classical texture models, brief friction fitting, TacTID, DiffTactile and RoboPack.

## What we currently have

Each method receives a short sample from a recorded sliding touch and predicts the vibration spectrum of another touch under a requested speed, direction and nominal pressing load. The observations come from the [Cluster Haptic Texture Dataset](https://arxiv.org/html/2407.16206v4).

The working software includes recording provenance, contact eligibility/QC, strict acceleration input windows, matched support/query protocols, five simple baselines, a small encoder, wrong-support controls and reproducible result artifacts. The target is **96 log-band-power values**, rather than a sequence of physical states.

| Component | Current evidence |
| --- | --- |
| Brief-contact inference and vibration observation prediction | Implemented; development comparisons and saved independent computational validation |
| Friction/compliance inference and contact-force prediction | Proposed experiment; no force results |
| Forward physical dynamics and engine integration | Planned; no motion rollout validation |
| Active robot probing and task control | Planned; current probe comparisons use recorded contacts |

The [saved validation report, dated 10 October 2026](docs/matched_validation_review.md), reports **110 passing tests** and exact reproduction of the frozen predictions and raw-derived features. The literature/documentation review did not rerun these experiments.

## Current findings and limits

In the latest [matched development comparison](docs/matched_development_review.md):

- **Retrieval beats the current encoder.** Similar recorded examples yield lower prediction error for the main brief-touch comparison.
- **Available motion conditions matter.** With transfer-speed responses omitted, forward single-touch retrieval raw log10 band-power MAE rises **0.1494 → 0.3119**; encoder MAE changes **0.3517 → 0.3550**. Lower is better. The omission also reduces training data, so this is not an equal-data-budget isolation of speed coverage.
- **A second direction has no reliable advantage yet.** Its benefit relative to repeating a touch changes across repetition orientations.

These are development findings from **ten training specimens and two repeatedly exposed evaluation specimens**. The first scientific study remains unfinished. **Twenty specimens remain reserved and untouched according to the saved study-design reports.**

The recordings' acquisition timing still needs confirmation. Current touch durations and frequency coordinates use the declared [logged-coordinate convention](docs/clock_qc_review.md). The data used here do not provide synchronized per-scan tangential-force or indentation targets. Good vibration predictions alone do not establish accurate friction, stiffness or object motion.

## Path to a physics world model

Keep the model interfaces explicit:

1. **Inference:** observed touches and their conditions produce a contact belief and supported effective parameters.
2. **Dynamics:** current state, action and contact law produce forces and the next physical state.
3. **Observation:** physical contact state produces predicted tactile readings.
4. **Planning:** predicted outcomes and uncertainty guide the next probe or task action.

The current prototype supplies part of inference and observation. The immediate research direction is a calibrated **fixed-pad sliding-force study**, followed by an independently moving-body test and one control task. Compare action-only, force-only, retrieval and simple mechanics with tactile-assisted inference at matched observation budgets.

The maintained **[brief-touch-mechanics repository](https://github.com/EltonChang1/brief-touch-mechanics)** contains that proposed study. Its public README still reports no force or motion results; dataset/rig feasibility and calibration are the next gates. The [research synthesis](docs/tactile_world_model_review.md#recommended-implementation-sequence) explains the implementation sequence and which papers inform each step.

## Explore and reproduce

| Need | Document |
| --- | --- |
| Goals, staged milestones and scientific gates | [Research plan](docs/research_plan.md) |
| Input/target and comparison contract | [Protocol](docs/protocol.md) |
| Technical implementation | [Implementation guide](docs/implementation_guide.md) |
| Current development evidence | [Matched results](docs/matched_development_review.md) and [validation](docs/matched_validation_review.md) |
| Exposure, reservation and test design | [Study design](docs/study_design_review.md) |
| Timing and contact-quality limits | [Clock/QC review](docs/clock_qc_review.md) |
| Installation and experiment commands | [Reproduction guide](docs/reproducing_experiments.md) |
| Preserved original mechanics design | [Experiment README](experiments/brief-touch-mechanics/README.md) and [methods](experiments/brief-touch-mechanics/METHODS.md) |

Code lives in [src/tactile_contact](src/tactile_contact), review/reproduction utilities in [scripts](scripts), and implementation checks in [tests](tests). The [reproduction guide](docs/reproducing_experiments.md) specifies prerequisites and commands for the existing development experiments.

## Maintain the literature catalog

Edit `docs/paper_dictionary.json`, verify additions against primary sources, and regenerate its Markdown and CSV views:

```powershell
python scripts/build_paper_dictionary.py
python scripts/build_paper_dictionary.py --check
```

The generator validates stable IDs, required fields, categories, source links and the reading path. The original [six-entry related-work matrix](docs/related_work.csv) remains a historical comparison for the brief-contact study; the broader dictionary is the current literature index.
