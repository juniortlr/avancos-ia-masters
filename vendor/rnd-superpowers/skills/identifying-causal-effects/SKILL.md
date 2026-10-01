---
name: identifying-causal-effects
description: "Use when: Answer causal questions using DAGs, target trials, adjustment, matching, weighting, DiD, RDD, IV or heterogeneous treatment effects with explicit identification and sensitivity."
---

# Identifying Causal Effects


## Procedure
1. Specify a target trial: eligible population, treatment versions, comparator, assignment time, follow-up, outcome, causal contrast and analysis. Align time zero to prevent immortal-time bias.
2. Draw a DAG including plausible unmeasured causes and selection. Classify pre-treatment confounders, mediators and colliders. Do not adjust for every column or use predictive feature importance to choose adjustment variables.
3. Write the identification argument BEFORE the estimator. For adjustment: consistency, conditional exchangeability and positivity. For DiD: plausible parallel untreated trends, no anticipation, composition/spillover checks; staggered adoption requires an estimator appropriate to heterogeneous timing effects. For RDD: continuity and manipulation/bandwidth checks. For IV: relevance, exclusion, independence and, for LATE, monotonicity.
4. If not identified, say so and provide descriptive estimates or a data/design proposal. A graph-learning algorithm, simulator or historical replay alone does not identify a real-world intervention effect.
5. Choose estimation appropriate to the argument: regression/g-computation, matching, weighting or doubly robust estimation. For flexible nuisance models use cross-fitting. If time-varying confounders are affected by prior treatment, consider longitudinal g-methods rather than ordinary adjustment. Report overlap, weight distribution, effective sample size and balance; matching alone does not remove hidden confounding.
6. DoWhy can structure model→identify→estimate→refute; EconML can estimate effect heterogeneity. Verify APIs and assumptions. Refutation checks can reveal failures but cannot prove that unmeasured confounding is absent.
7. Use negative controls/placebos, sensitivity to hidden confounding, alternate defensible DAGs, trimming sensitivity and dependence-aware uncertainty. Pre-specify heterogeneity or label it exploratory with multiplicity control.
## Deliver
Write `causal-design.md`, DAG, identification assumptions, diagnostics, effect table, sensitivity results and a claim scoped to the population/estimand.
## Stop or hand off
Poor overlap, aliased treatments, collider selection or unjustified assumptions block the corresponding causal claim. Do not repair positivity by extrapolation without changing and reporting the target population.
