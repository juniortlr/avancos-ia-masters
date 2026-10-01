---
name: estimating-uncertainty
description: "Use when: Perform statistical estimation, Bayesian or hierarchical modeling, bootstrap inference, equivalence analysis and uncertainty calibration for small or dependent samples."
---

# Estimating Uncertainty


## Procedure
1. State estimand, likelihood/sampling model, dependence and measurement assumptions. Report observations AND independent units; effective information also depends on intracluster correlation and design.
2. Select a justified frequentist or Bayesian analysis. Use multilevel models for repeated units when pooling assumptions are defensible. Bayesian partial pooling does not manufacture independent evidence.
3. For resampling, resample the inferential unit and preserve pairing/dependence. Define row-weighted versus equally weighted cluster estimands; they differ with unequal cluster sizes. Few clusters can make asymptotic and bootstrap intervals unreliable; report that limitation or use defensible design-based/small-sample methods.
4. For Bayesian models, run prior predictive checks, justify priors in domain units, inspect chains/R-hat/ESS/divergences and posterior predictive checks. Perform prior/model sensitivity. Do not report an unconverged chain as a result.
5. Distinguish confidence, credible and predictive intervals. For predictive/conformal intervals, state exchangeability assumptions and evaluate empirical coverage; ordinary conformal guarantees do not automatically survive temporal or domain shift.
6. Report effect magnitude and practical bounds with uncertainty. A non-significant test does not establish equivalence. Separate parameter uncertainty, measurement error, model misspecification and between-unit variability.
7. For discrete small-sample tests, compute attainable resolution for the actual design; ties/zeros and approximation choice matter. Record multiplicity and Monte Carlo error, including the number of permutations.
## Deliver
Write `uncertainty-report.md` with assumptions, diagnostics, interval method, sensitivity and reproducible settings. Suggested tools: SciPy/statsmodels for classical inference; PyMC/ArviZ for Bayesian workflows, after checking installed-version documentation.
## Stop or hand off
Nonidentifiability, failed convergence or invalid resampling blocks the associated interval claim. Report descriptive estimates with limitations rather than manufacturing precision.
