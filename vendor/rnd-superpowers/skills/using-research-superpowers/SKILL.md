---
name: using-research-superpowers
description: "Use when starting research or data science, selecting EDA, mining, ML, AutoML, A/B testing, causal inference, forecasting, scientific experiments or paper-writing workflows."
---

# Using Research Superpowers

Read only the skill(s) needed for the next task. Skill folders are siblings of this folder; resolve them within the installed skills root. The host supplies tools; this framework supplies procedures.

## Core research loop

**problem → baseline → hypothesis → experiment → ablation → review → problem**

Use this as the default cycle for substantive research. Start a versioned cycle record; resume completed stages only when their inputs and scope remain valid. Do not force the full cycle onto a small edit.

1. **Problem:** use `defining-problem-statements` to state the question, gap, scope and meaningful outcome. Inspect relevant supplied context, data provenance/initial EDA and related literature before selecting a baseline. Record unavailable inputs and prior outcome exposure.
2. **Baseline:** establish the simplest defensible reference or current state of knowledge, with appropriate measurements, uncertainty and evaluation protocol. Execute or verify it when feasible. A proposed but unrun baseline remains explicitly unverified.
3. **Hypothesis:** state a testable explanation, improvement or proposition relative to that baseline, its assumptions and what would challenge it. Record which baseline/EDA outcomes informed it. Pre-specify confirmatory evaluation before inspecting its outcomes; never call an outcome-informed hypothesis preregistered retroactively.
4. **Experiment:** run the appropriate study or analysis under the defined protocol, using comparable evidence, resource budgets and meaningful controls. Save results, deviations and failed runs. Use design-appropriate validation for theoretical or qualitative studies rather than manufacturing a statistical experiment.
5. **Ablation:** isolate which components, assumptions or choices account for the result through controlled removals/replacements, sensitivity or counterexample analysis. Use comparable targets and fair tuning budgets. One-factor removal alone may miss interactions. Pre-specify confirmatory ablations; label new post-result ablations exploratory.
6. **Review:** conduct self-review and appropriate peer, tutor or outsider review. Assess evidence against the original problem and similar or conflicting research. Record responses, verify revisions and preserve disagreement; do not treat reviewer agreement as proof.
7. **Return to problem:** state what was learned and whether to retain, refine, split, reject or close the problem. Create a new problem/cycle version when changing scope or hypotheses; preserve previous evidence and decisions. Do not rewrite the prior protocol to match the result.

Each stage records artifacts, status and unresolved limitations. Mark genuinely inapplicable stages with a method-specific reason, not a silent skip. Initial exploration and literature retrieval support the problem/baseline stages; missing access must remain visible. These instructions do not create an enforced runtime gate or native parallel scheduler.

## Iteration controls

- Set a cycle/time/compute budget before substantive execution. Default to one completed cycle and a proposed next problem; continue automatically only within an already authorized ongoing scope/budget.
- At review, choose continue, revise, pivot, conclude or blocked. Stop when the question is adequately answered, a futility/feasibility criterion applies, required evidence is unavailable or the budget is exhausted. Do not loop until a positive or publishable result appears.
- Do not repeatedly tune against an exposed final test set. New outcome-informed hypotheses require fresh confirmation evidence or a justified selection-aware design; label otherwise exploratory.
- Reuse artifacts only when data, question, outcome and evaluation versions match. Invalidate affected downstream stages after a material change; do not rerun unrelated valid work.
- Run independent activities within a stage in parallel only when actual host support exists. Preserve dependencies: experimental results precede their ablation assessment and review; independent ablation arms may share a frozen protocol and run concurrently where justified.

## Select a route

| Intent | Route |
|---|---|
| Understand data | provenance → exploring-data → scoped descriptive report |
| Discover segments/rules | exploring-data → mining-patterns → validate discovery |
| Predict a target | frame → data contract → training-classical-ml → red team |
| Search models | ML evaluation contract → budgeting-automl → final evaluation |
| Forecast/detect temporal events | validating-time-series → baseline/backtests → report |
| Estimate intervention effect | designing-ab-tests if randomized; identifying-causal-effects otherwise |
| Plan engineering/lab/algorithm comparisons | designing-scientific-experiments → preregistration → execution |
| Quantify uncertainty | estimating-uncertainty + the relevant method |
| Failure and remaining life | analyzing-reliability + temporal validation |
| Hybrid physical/neural models | validating-physics-informed-models + ML/time-series validation |
| Survey literature or write a paper | reviewing-scientific-literature → evidence ledger → writing-research-papers |
| Reproduce a claim | reproducing-research → evidence ledger → reporting-a-finding |

Use `framing-a-research-question` for unclear scope; `preregistering-an-analysis` for confirmatory choices; `data-provenance-and-contracts` before data work; `analysis-with-a-null-model` for inferential contrasts; `red-teaming-a-result`, `evidence-ledger-and-gates` and `reporting-a-finding` for substantive claims.

Exploration may precede hypothesis selection. Preserve its status and record prior outcome exposure. Never label a hypothesis preregistered after seeing the relevant outcomes. Schema inspection and descriptive results do not require a fabricated null test.

## Problem definition, review and decision communication

Use `defining-problem-statements` to create the explicit problem/gap/question/objective specification; `framing-a-research-question` then classifies and operationalizes it. Neither replaces data inspection or literature retrieval.

| Intent | Skill |
|---|---|
| Define the problem and objectives | `defining-problem-statements` |
| Check one's own draft or analysis | `conducting-self-review` |
| Independent critiques and revision cycle | `conducting-peer-review-round` |
| Formative thesis/supervisor perspective | `conducting-tutor-review` |
| Cross-disciplinary/non-specialist comprehension | `conducting-outsider-review` |
| Concise evidence-based decision brief | `writing-executive-summaries` |

For substantive work, use self-review before external-facing delivery. At relevant milestones, select peer, tutor and/or outsider review according to purpose; do not force every review on small tasks. Review roles may run concurrently only when the host actually supports it and each receives the same frozen artifact. Resolve findings and verify revisions before final summaries. Preserve the review type and limits: AI-assisted review is not real human endorsement.

## Proportional effort

- Quick: scoped question, local data checks, one useful output, clear limitations.
- Standard: protocol, method skill, baseline, valid split/inference, result and run record.
- Publication: full evidence/search ledger, sensitivity/ablations, reproducibility and manuscript checks.

Choose from the request; do not block on selecting a mode. Announce active skills once. Log material choices and proceed on reversible authorized work. Ask only when an unresolved input materially changes validity or an irreversible commitment needs authorization.

## Decision record

Append to `specs/decision-log.md` or root `decision-log.md`: date, question, options, chosen option/reason, reversal cost and evidence. Preserve contrary findings and withdrawals.

## Available skill names

- `analysis-with-a-null-model`
- `analyzing-reliability`
- `budgeting-automl`
- `data-provenance-and-contracts`
- `designing-ab-tests`
- `designing-scientific-experiments`
- `estimating-uncertainty`
- `evidence-ledger-and-gates`
- `exploring-data`
- `framing-a-research-question`
- `identifying-causal-effects`
- `mining-patterns`
- `preregistering-an-analysis`
- `red-teaming-a-result`
- `reporting-a-finding`
- `reproducing-research`
- `reviewing-scientific-literature`
- `training-classical-ml`
- `validating-physics-informed-models`
- `validating-time-series`
- `writing-research-papers`

- `defining-problem-statements`
- `conducting-self-review`
- `conducting-peer-review-round`
- `conducting-tutor-review`
- `conducting-outsider-review`
- `writing-executive-summaries`
