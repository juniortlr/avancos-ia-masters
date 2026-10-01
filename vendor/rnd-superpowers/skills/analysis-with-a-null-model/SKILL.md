---
name: analysis-with-a-null-model
description: "Use when: computing a correlation, effect size, enrichment, coincidence or alignment between two things, running a permutation or bootstrap, detecting steps changepoints or anomalies, testing whether events cluster near other events, choosing a window lag or threshold, estimating a slope or trend, or whenever about to report a statistic and you need to know whether it is bigger than chance"
---

# Analysis with a Null Model

## Procedure
1. State the inferential claim, observed statistic, comparison/null and what evidence would challenge the claim. Purely descriptive summaries need no manufactured null test.
2. Choose a null that preserves relevant dependence and respects the design. Permute assignment at the randomization/exchangeability unit within design strata. Paired sign flips need their own symmetry or randomization justification.
3. For temporal data, justify stationarity, exposure windows and boundary behavior before circular shifts. Resampling raw blocks does not impose a no-trend null; reconstruct under an explicit null with suitable residual dependence.
4. For predictive claims, compare baselines on identical held-out data. Target permutations require justified exchangeability and leakage-safe fitting.
5. Record random seeds, resampling count and Monte Carlo precision. Use valid finite-sample permutation p-values, such as (b+1)/(B+1) where appropriate; do not report zero from finite random draws.
6. Report observed quantity, reference distribution, contrast and uncertainty. Statistical excess alone is not causal attribution. Non-significance means evidence is inconclusive unless a valid equivalence design supports a stronger claim.
7. Pre-specify primary settings and justified sensitivity checks. Exploratory sweeps involve selection/multiplicity even when the whole curve is shown. Validate selected patterns independently or use a justified selection-aware procedure.
8. Resample at the inference unit, preserving pairing and dependence. Report rows and independent entities separately. Few-cluster intervals can be unreliable; do not present a naive interval as equally valid evidence.
9. Check measurement meaning, units, resolution, noise, plausibility and subset stability. Aggregated statistics can resolve changes below individual measurement increments under suitable assumptions. Sign reversal can reflect selection, heterogeneity or noise; it is not proof of a nonexistent mechanism.

## Deliver
Save the observed/reference results, assumptions, computation, inspected figure and uncertainty method. Route substantive findings through `red-teaming-a-result` and `reporting-a-finding`.
