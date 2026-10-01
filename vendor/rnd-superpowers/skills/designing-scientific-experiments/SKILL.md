---
name: designing-scientific-experiments
description: "Use when: Plan factorial experiments, screening, response surfaces, ablations, simulation studies and sequential scientific experiments with randomization, blocking and power."
---

# Designing Scientific Experiments


## Procedure
1. Define scientific question, response, experimental unit, factors, feasible ranges and practical effect. Separate biological/physical replicates from repeated readings or repeated software seeds.
2. Select comparative, screening, full/fractional factorial or response-surface design according to objective and budget. Document confounding/alias structure and which interactions are estimable. One-factor-at-a-time designs can miss interactions.
3. Randomize run order and block nuisance variation (batch, instrument, day); include replication and center points when appropriate. Respect hard-to-change factors through a split-plot design and its analysis.
4. Estimate power or expected precision at the true experimental unit. Pre-specify exclusions, failed runs, outcome windows, analysis and stopping. Synthetic replication is not additional real-world evidence.
5. For algorithm ablations, hold data, target, split, compute and tuning opportunity comparable. Remove components individually and assess key interactions where affordable. Record failures and all seeds; seeds are not independent datasets.
6. For simulation studies, vary known mechanisms, noise, confounding, missingness and distribution shift. Measure bias, RMSE, interval coverage, type-I error and power over replications, with Monte Carlo uncertainty.
## Deliver
Write `design-matrix.csv`, `experiment-plan.md`, budget, randomization seed and analysis specification; log deviations before interpreting results.
## Stop or hand off
Aliased factors restrict the claim; collect additional runs instead of inventing separability. For live conversion tests use `designing-ab-tests`.
