---
name: exploring-data
description: "Use when: Explore an unfamiliar dataset with bounded EDA, missingness, distributions, outliers, coverage, leakage checks and hypothesis generation."
---

# Exploring Data


## Procedure
1. Read `data-provenance-and-contracts`. Record grain, entity IDs, time coverage, units, data origin and available sample. Profile schema before full scans; estimate memory and select a reproducible, stratified sample when necessary.
2. Declare this work exploratory. If prediction is intended, reserve evaluation entities/time before target-aware exploration. Keep final test outcomes sealed; record prior exposure if already inspected.
3. Report rows, unique entities, cluster sizes, duplicates at the declared key, nulls and sentinels per field. Compare missingness and coverage by time, cohort and target availability. Do not infer MAR or MCAR from a non-significant diagnostic.
4. Plot distributions and per-entity trajectories on development data. Check units, quantization, outliers, censoring, asynchronous sampling and drift. Preserve raw values; flag suspicious observations rather than deleting by a generic rule.
5. Examine associations using appropriate scales, strata and dependence-aware uncertainty. Separate within-entity and between-entity effects. Treat correlations and plots as descriptive, not causal.
6. Produce a small ranked hypothesis queue: proposed mechanism, rival explanation, required data and validation design. Count searched features/subgroups; label any exploratory p-values as such and address multiplicity.
## Deliver
Write `eda-report.md`, `quality-summary.csv`, inspected figures and `hypotheses.csv`. Record sampling seed, sample coverage and inspected columns. Export aggregates rather than raw sensitive records.
## Stop or hand off
Unresolved target meaning goes to the data-contract skill. Descriptive summaries can stand as scoped observations; hypotheses require a fresh confirmatory sample or a valid selection-aware procedure. Do not call the entire dataset clean from a sample.
