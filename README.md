# Brief Contact Research

We want to help a robot understand a surface after a few short touches, then use that understanding to predict contact and make robot simulations more realistic.

Imagine a robot sliding a finger across a surface. Could one short slide tell it what to expect when it moves faster, changes direction or presses harder? That is the first question we are studying.

## What we are doing now

We use existing recordings of real surfaces. Each prediction method receives a short sample from a sliding touch and tries to predict the vibrations of another touch under different conditions.

For now, we predict how strong the vibrations are at different frequencies. Predicting contact forces, building a physical simulator and controlling a real robot are later steps in the [research plan](docs/research_plan.md).

## Why we are doing this

We want to find out how much touching is necessary and whether a different kind of second touch provides more useful information than repeating the first.

We compare AI with simpler methods, including looking up similar recorded examples and making simple mathematical predictions. This tells us which methods actually help and where more work is worthwhile.

## What we have built

This repository contains working software that processes the recordings, makes fair comparisons, trains prediction methods and saves results that can be checked again.

As of **10 October 2026**, all **110 tests pass**. Independent checks reproduce the saved predictions and calculations exactly. See the [validation report](docs/matched_validation_review.md).

## What we found

In the latest development comparison:

- **Similar recorded examples beat our current AI model.** For the main comparison using one brief touch, looking up similar examples gives lower prediction error.
- **The available examples matter.** Removing examples at the tested speeds roughly doubles that lookup method's error. That experiment also gives the method fewer examples to use.
- **A different direction has no reliable advantage yet.** A second touch in another direction has not consistently helped more than repeating the same direction.

**Simple methods are strong. Our current AI model has not yet shown an advantage.**

These findings come from ten surfaces used for training and two repeatedly used evaluation surfaces. They are early development results. The [full result report](docs/matched_development_review.md) explains the comparison and its limits.

## Where we are in the plan

The working prototype and these development comparisons are complete. The first scientific study is still unfinished.

Next, we need to decide the test rules in advance, complete the planned range of speeds, directions and pressing forces, then test on surfaces kept out of development. **Twenty surfaces remain set aside and untouched.**

The recordings' timing still needs confirmation before we can make precise claims about touch duration or vibration frequency. Force prediction, physical simulation and robot control come later.

## Explore or run the project

- [Research plan](docs/research_plan.md): the goals and stages of the project.
- [Implementation guide](docs/implementation_guide.md): how each stage is carried out.
- [Latest results](docs/matched_development_review.md): the measurements behind the findings above.
- [Validation report](docs/matched_validation_review.md): how we checked the results.
- [Installation and experiment commands](docs/reproducing_experiments.md): technical instructions for running the software and reproducing the work.
