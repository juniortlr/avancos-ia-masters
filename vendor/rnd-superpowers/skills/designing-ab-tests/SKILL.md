---
name: designing-ab-tests
description: "Use when: Design or analyze randomized A/B tests with power, randomization units, sample-ratio mismatch, intent-to-treat, guardrails and valid stopping rules."
---

# Designing Ab Tests


## Procedure
1. Define intervention, population, eligibility, assignment and exposure timestamps, randomization unit, outcome window and estimand (normally intent-to-treat). Assess spillover; randomize groups, sites or time blocks if individuals interfere.
2. Pre-specify one primary metric, meaningful absolute effect, baseline rate/variance, alpha, power, allocation, exclusions, guardrails and multiplicity control. Read `preregistering-an-analysis` before outcomes. Use pilot information and uncertainty ranges for power; do not compute observed post-hoc power.
3. Calculate sample and duration requirements accounting for clustering, attrition, outcome delay and seasonality. An independent-proportions approximation is not valid for clustered or repeatedly measured subjects. Low traffic may make the experiment infeasible; report duration rather than promise significance.
4. Validate assignment persistence and instrumentation, preferably with an A/A check. Check sample-ratio mismatch against planned assignment proportions at the randomization unit. Diagnose mismatches before interpreting treatment effects; p above a threshold does not prove instrumentation is sound.
5. Analyze by assignment (ITT), with declared cluster-aware uncertainty. Avoid conditioning on post-treatment attendance, usage or conversion. Report absolute and relative effects, denominators, intervals, attrition and guardrails. Ratios need appropriate ratio inference.
6. Choose fixed-horizon analysis OR a specified sequentially valid method in advance. Repeated ordinary p-value peeking is not a valid stopping rule. Bayesian analysis also needs an explicit loss/stopping policy and sensitivity analysis.
7. Report practical benefit, uncertainty and tradeoffs. Use equivalence/non-inferiority bounds if the question is negligible harm, not p > 0.05. CUPED uses only suitable pre-treatment covariates and preserves the declared estimand.
## Deliver
Write `experiment-protocol.md`, assignment/analysis checks, `experiment-results.csv` and a ship/continue/stop recommendation grounded in predeclared criteria. The user retains rollout authority.
## Stop or hand off
Nonrandom assignment routes to `identifying-causal-effects`. Unresolved assignment bugs block causal interpretation. Small samples may justify a pilot or better instrumentation rather than an efficacy claim.
