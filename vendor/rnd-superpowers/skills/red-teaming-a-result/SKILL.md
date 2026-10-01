---
name: red-teaming-a-result
description: "Use when: an analysis has produced a number and you are about to report it, before closing a gate or signing off a finding, when reviewing someone else's result or dashboard claim, when a correlation looks surprisingly clean, when asked 'can we trust this', or when a result needs to be attacked for confounding, Simpson's paradox, selection bias, subset instability or restricted range before publication"
---

# Red-Teaming a Result

Review the claim before publication or substantive decisions. Mark each applicable check pass, fail or untestable with evidence; explain nonapplicability rather than manufacturing a test.

1. **Question alignment:** Does the result address the stated quantity, proposition or phenomenon?
2. **Measurement and provenance:** Are constructs, units, sources and transformations valid and traceable?
3. **Identification:** Are required causal, sampling, model or interpretive assumptions justified? Aliased factors cannot be separated by assertion.
4. **Selection:** What determines inclusion and observation? Could conditioning induce bias? For causal work, do not automatically adjust for mediators, colliders or post-treatment variables.
5. **Heterogeneity:** Inspect relevant groups and uncertainty. Distinguish within-group and between-group claims. Label broad subgroup searches exploratory.
6. **Robustness:** Evaluate defensible alternative definitions, sources, specifications and sensitivity to influential units; preserve exclusions and their reasons.
7. **Leakage:** Check feature availability, overlapping outcome windows, preprocessing inside folds and independent-entity separation when required.
8. **Uncertainty:** Distinguish inconclusive estimates, equivalence and lack of power. Report test resolution for discrete small-sample designs where relevant.
9. **Interpretability:** Translate quantitative effects to meaningful units or explain theoretical/qualitative implications without extending beyond evidence.
10. **Reproducibility and reporting:** Trace results to artifacts, record deviations and preserve contradictory findings.

## Deliver
A check/verdict/evidence table plus the supported scope and unresolved limitations. Severity is claim-specific: invalid identification or leakage blocks affected claims; scoped descriptive findings may remain reportable. A later precise estimate need not contradict an earlier inconclusive one. Withdraw overclaims explicitly without deleting historical evidence.
