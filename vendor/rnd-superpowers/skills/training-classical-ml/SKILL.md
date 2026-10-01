---
name: training-classical-ml
description: "Use when: Train and evaluate classical classification or regression models with leakage-safe pipelines, grouped or temporal validation, calibration and interpretable baselines."
---

# Training Classical Ml


## Procedure
1. Fix target definition, prediction time, horizon, population, observation unit and loss. Name the deployment generalization: new entities, future observations on known entities, or both.
2. Freeze a split manifest at the proper unit. Use grouped splits for unseen entities and chronological splits for forecasting. For both, enforce group isolation AND time ordering explicitly; neither ordinary GroupKFold nor TimeSeriesSplit alone guarantees both. Purge training labels whose outcome windows overlap validation.
3. Start with dummy/mean/majority or persistence predictions, then regularized linear/logistic models and a tree ensemble. Use SVM or nearest neighbors when representation, data size and scaling justify them.
4. Fit imputers, scalers, encoders, resampling, feature selection and target encodings inside each training fold. Fit probability calibration and decision thresholds on training/validation only. Never balance the test sample to improve metrics.
5. Tune with inner folds and estimate performance on untouched outer folds, or use a fixed development/validation/test design. Refit on permitted development data only after selection. Report which evaluation protocol was used and the search budget.
6. For regression, report MAE/RMSE in domain units and residual slices. For rare classification, report PR-AUC plus prevalence, recall/precision at the action budget, calibration and confusion counts. Metric choice follows the decision cost, not the best score.
7. Estimate paired improvement over baseline using the correct resampling unit. Report entity counts and repeated measurements; folds/seeds are not independent subjects. Inspect residuals, subgroup performance and plausible extrapolation failures.
8. Use held-out permutation importance or SHAP for model behavior, explicitly non-causal. Correlated predictors can exchange importance. Save environment, seeds, split IDs and model configuration.
## Deliver
Write `model-card.md`, `metrics.csv`, `split-manifest.csv`, inspected diagnostic figures and rerunnable training/evaluation commands. Follow `reproducing-research` for release.
## Stop or hand off
If labels leak, meaning is unresolved, or split constraints fail, block the performance claim and repair the protocol. Use `budgeting-automl` for larger searches.
