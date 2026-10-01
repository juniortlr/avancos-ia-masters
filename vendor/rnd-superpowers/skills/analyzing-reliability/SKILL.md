---
name: analyzing-reliability
description: "Use when: Analyze time-to-event, remaining useful life, events or failure using survival methods with censoring, competing risks and temporal validation."
---

# Analyzing Reliability


## Procedure
1. Define time origin, event, at-risk population, observation end and time scale. Distinguish right/left/interval censoring and delayed entry. Separate failure, replacement and study exit; replacement can be informative.
2. Report event counts, follow-up and censoring by cohort. Do not label surviving units as never failing or train only on failed units. Define what makes censoring plausibly noninformative conditional on modeled variables.
3. Start with Kaplan–Meier where its assumptions apply, then Cox/AFT or appropriate flexible models. Diagnose proportional hazards before interpreting constant hazard ratios. For competing events, use cumulative incidence rather than interpreting one-minus-KM as event-specific risk.
4. Treat time-varying predictors with risk-set-correct timing. Prevent future information and immortal-time bias. Split by entity/time for deployment claims and compare with a simple baseline.
5. Evaluate calibration at relevant horizons, time-dependent discrimination and censoring-adjusted scores under justified assumptions. Report uncertainty at entity/cluster level and limits at horizons with few at risk.
## Deliver
Write `event-contract.md`, censoring/at-risk tables, survival or incidence curves, horizon metrics and a clearly scoped remaining-life statement.
## Stop or hand off
Too few failures or unknown censoring mechanisms may support only descriptive follow-up. Do not output precise RUL from proxy measurements without a defined failure threshold and validated extrapolation.
