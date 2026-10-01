---
name: validating-time-series
description: "Use when: Forecast and analyze temporal signals, degradation trajectories, change points or demand using rolling backtests, horizon-aware features and dependence-aware uncertainty."
---

# Validating Time Series


## Procedure
1. Define forecast origin, horizon, label window, sampling frequency, latency and entity. Distinguish forecasting known units from extrapolating to new units. Check clocks, duplicate timestamps, irregular spacing and stateful resampling.
2. Freeze chronological backtests and an untouched latest period; add entity holdouts for unseen-unit claims. Purge overlap in training label windows. Choose gaps from information overlap and operational latency, not a magic constant.
3. Construct trailing features using only information available at each origin. Centered smoothers, full-history normalization and future interpolation leak. Distinguish truly known future covariates from forecasts that must themselves be evaluated.
4. Compare persistence, seasonal naive and simple trend/state-space baselines before tree or neural models. Score identical targets and horizons; report performance by horizon, unit and regime.
5. For anomaly/change-point work, separate retrospective segmentation from online detection. Report delay, false alarms per exposure and event-level recall when labels exist; backdated detection is not early warning.
6. Estimate uncertainty preserving serial/entity dependence. For block methods state block length and sensitivity; a bootstrap distribution estimates uncertainty, not automatically a no-trend null. Validate interval coverage on backtests and identify distribution-shift limits.
7. Inspect residual autocorrelation, seasonal errors and drift. Predefine retraining/monitoring criteria without repeatedly retuning against the sealed evaluation period.
## Deliver
Write `backtest-plan.md`, origin/horizon split manifest, baseline comparison, residual plots and interval coverage by horizon.
## Stop or hand off
Sparse seasonal history limits seasonal claims. Censoring and instrument or estimator changes can distort observed trajectories. Route measurement failures back to provenance.
