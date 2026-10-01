# Iterative research process

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

## Stage-to-skill mapping

| Stage | Supporting skills |
|---|---|
| Problem | defining-problem-statements, framing-a-research-question, provenance, exploring-data, reviewing-scientific-literature |
| Baseline | relevant statistical, theoretical, predictive or domain method; reproducing-research |
| Hypothesis | framing-a-research-question, preregistering-an-analysis where appropriate |
| Experiment | designing-scientific-experiments and the selected method skill |
| Ablation | designing-scientific-experiments, analysis-with-a-null-model where applicable, uncertainty estimation |
| Review | conducting-self-review, red-teaming-a-result, selected peer/tutor/outsider review, evidence ledger |
| Return to problem | defining-problem-statements and a versioned cycle decision |

An executive summary may be prepared at a checkpoint, with the cycle's status and limitations intact. The loop is a procedural addition to the current 28-skill framework, not another numerical model or a newly implemented orchestration runtime.

## Method adaptation

For theoretical work, baseline can be the current theorem/argument; hypothesis a proposition; experiment a proof attempt or counterexample search; ablation an examination of necessary assumptions. For qualitative work, use an explicit interpretive framework, evidence collection/analysis and defensible alternative interpretations or negative cases. Do not force statistical nulls, numerical superiority or component removal when they are methodologically inappropriate.
