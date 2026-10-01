---
name: preregistering-an-analysis
description: "Use when: about to run a statistical test, comparison, correlation, regression, A/B test or model evaluation, when designing an experiment or choosing a metric, when deciding how many arms or variants to compare, when someone asks 'is this significant', or when you need to fix the estimand, clustering unit, null model, multiplicity budget, minimum detectable effect and stopping rule before looking at the outcome"
---

# Preregistering an Analysis

Use prospective protocols for confirmatory work. Record what outcomes were already seen; exploratory plans are not retrospective preregistrations.

## Protocol fields
1. Question, estimand, population and contrast.
2. Sampling and independent inference unit, dependence structure and planned sample size.
3. Outcome/measurement definitions, timing, eligibility, exclusions, missingness and censoring.
4. Primary analysis, hypotheses, baseline/null, assumptions and identification or evaluation design.
5. Primary metric and practical threshold; prospective power/MDE or precision analysis with assumptions.
6. Multiplicity family and control, sensitivity analyses and exploratory work distinguished from primary tests.
7. Stopping rules, resource budget, model-selection procedure, split definitions and seeds.
8. Evidence that would change the conclusion, reporting commitments and reproducibility artifacts.

## Small samples
Compute attainable p-value resolution for the actual test. For independent nonzero untied paired differences under an exact two-sided signed-rank test, the extreme minimum is 2/2^n. Ties, zeros and approximation choices matter; this is not a universal bound for other tests. Check the actual multiplicity procedure and family prospectively.

## Amendments
Timestamp the protocol and preserve versions. Identify post-outcome changes as deviations or a new exploratory analysis; retain the original. Do not reduce a test family or change an outcome to rescue significance.

## Deliver
Write `study-protocol.md` with protocol status, prior outcome exposure and amendment history. Report effect intervals and practical bounds; observed post-hoc power is not evidence for an absence claim.
