---
name: validating-physics-informed-models
description: "Use when developing or evaluating physics-informed, mechanistic or hybrid models in any quantitative research domain, with dimensional checks, physical baselines and controlled ablations."
---

# Validating Physics-Informed Models

## Procedure
1. Define physical state, observable target, units, measurement process and uncertainty. Distinguish latent quantities from instrument estimates and model-derived labels.
2. Write governing equations, initial/boundary conditions, parameter assumptions and domain of validity. Check dimensional consistency and identifiability. Classify constraints as hard, soft or empirical; justify their applicability and numerical scales.
3. Compare simple predictive, unconstrained statistical, mechanistic-only and hybrid baselines on identical outcomes and evaluation units. Select architectures from the research question rather than assuming a particular model family.
4. Hold out independent entities, periods or environments according to the intended generalization. Prevent leakage in derived features, preprocessing and simulation calibration. Evidence at one scale does not establish validity at another.
5. Ablate model components, constraints, loss weights and simulated pretraining under comparable tuning budgets. Measure prediction error, constraint violations, uncertainty, computational cost and failure modes.
6. For simulations, record equations, solvers, tolerances, parameter sets and calibration inputs. Shared simulation assumptions can produce apparent agreement; validate against independent empirical observations when making real-world claims.
7. Distinguish reversible observed variation from constrained latent dynamics. Do not force monotonicity, conservation or bounds onto quantities for which they are unjustified.

## Deliver
Write `physics-contract.md`, an evaluation/ablation matrix, constraint diagnostics and a scoped generalization statement. Link every substantive claim to reproducible evidence.

## Stop or hand off
Unvalidated measurements, unidentified parameters or unsupported constraints restrict the claim. Modeling an instrument's output is not automatically estimating the underlying physical state.
