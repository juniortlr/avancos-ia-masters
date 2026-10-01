---
name: budgeting-automl
description: "Use when: Run bounded AutoML and hyperparameter optimization with FLAML, Optuna or AutoGluon, fair compute comparisons and protected test evaluation."
---

# Budgeting Automl


## Procedure
1. Read `training-classical-ml`; complete its target, split, baseline and metric contract before search. AutoML automates fitting, not identification or experimental design.
2. Choose one engine initially: FLAML for a budgeted tabular search; Optuna for explicit/custom objectives, including physics losses; AutoGluon for tabular ensembles when memory and inference cost permit. Check installed-version APIs in official documentation.
3. Record wall-clock, CPU cores, GPU/device hours, memory, trial count, disk, API spend (if any), seeds and inference limits. Include preprocessing, ensemble fitting and refitting in the measured budget. A framework timeout can be soft; use an external process deadline for a strict cap and record interruptions.
4. Feed only development data into search. Verify the engine honors supplied group/time folds at every level, including bagging, stacking, early stopping and calibration. If it cannot, disable those features or use a custom objective; never fall back silently to random folds.
5. Persist trial configuration, validation score, duration, failures and pruning decisions. Count adaptive trials as selection effort; do not treat the winning validation score as unbiased evidence.
6. Compare against baseline under the same data, hardware/resource allocation and measured budget. Lock the selected pipeline and threshold before final evaluation. A failed or over-budget run belongs in the report.
7. Measure latency, memory, serialization and dependencies. Prefer a simpler eligible pipeline when gains do not justify operating cost. Use outer evaluation or the untouched final test for claims.
## Deliver
Write `search-budget.json`, `trials.csv`, `selection-record.md` and a resource/performance table. Report requested and actual runtime separately.
## Stop or hand off
If budget or fold constraints cannot be enforced, return the baseline and an explicit limitation. Do not launch paid resources without authorization. Default to a bounded CPU pilot only when resources are available.
