# Automatic research intake, evidence retrieval and parallel agents

Status: proposed implementation plan. No new runtime behavior is implemented by this document.
Date: 2026-09-28. Baseline: the current domain-neutral 22-skill framework.

## 1. Problem and diagnosis

The current agent has the right skills but weak execution dependencies:

- `using-research-superpowers` sends prediction directly from framing/data contracts to ML. EDA can be omitted unless the user explicitly requests exploration.
- Literature review is a separate intent route. Thesis analysis can proceed without retrieving related methods, comparable findings or contrary evidence.
- The agent file describes one general researcher. It has no specialist dispatch protocol, capability negotiation, task state, result contract or join/review stage.
- Static Markdown validation verifies structure, not whether EDA, retrieval or parallel execution actually happened.

Change the control flow and artifact dependencies, not just the trigger descriptions. Keep the framework domain-neutral and proportional to the task.

## 2. Proposed default workflow

Intake → capability/data inventory → parallel discovery → synthesis → study plan → execution → result comparison → review/report.

After minimal intake, run three independent workstreams where useful:

1. **Data investigator:** provenance, schema and initial EDA on permitted data.
2. **Literature investigator:** related questions, methods, datasets, findings and contrary evidence.
3. **Context investigator:** supplied thesis proposal, existing notes, prior protocols, terminology and project constraints.

The coordinator combines them into an evidence-based plan. A methodology reviewer checks the proposed design after this join. Modeling or confirmatory analysis requires the relevant readiness checks; unrelated useful work continues while a branch is blocked.

### Applicability

| Request | Initial data exploration | Context/literature discovery |
|---|---|---|
| New empirical thesis/study | Required when data is accessible | Required before substantive method/novelty claims |
| Model training or statistical analysis | Required or verified current EDA reused | Required for a research contribution; bounded method lookup for routine operational work |
| New dataset or materially changed extract | Re-run affected EDA | Refresh if population, measurement or question changes |
| Theory, qualitative or literature-only thesis | Method-appropriate source/corpus inspection; tabular EDA may be not applicable | Required, with discipline-appropriate sources |
| Existing study with valid artifacts | Verify fingerprints/scope; reuse | Verify relevance and currency; update gaps only |
| Tiny code/format fix | Not applicable unless analysis assumptions change | Not applicable unless scientific claims change |

A user instruction to avoid browsing, inaccessible data, missing tools or restricted permissions must be respected and recorded. Do not manufacture completion. An exploratory local task may proceed with a limited context record, but a literature-grounded novelty claim cannot.

## 3. Make initial EDA an explicit dependency

### Two-stage exploration protects evaluation data

**Stage A: structural inspection.** Inventory accessible datasets, schema, formats, measurement definitions, entity/time fields, file sizes, source versions and existing split metadata. Use this to establish a defensible split. Record any prior outcome exposure; do not assert that an already inspected target is unseen.

**Stage B: substantive EDA.** Inspect the development portion once evaluation boundaries are defined. Include:

- Row count and independent units, group sizes and coverage.
- Missingness/sentinels, duplicate keys, unexpected cardinality and suspicious values.
- Variable distributions, units, target quality and relevant associations.
- Temporal patterns or group structure where applicable.
- Potential leakage, censoring, selection and representativeness limits.
- Inspected figures and a short explanation of their consequences for the study.
- A hypothesis queue, clearly exploratory, and recommended method changes.

Schema-only profiling does not satisfy substantive EDA. Loading data or printing `head()` is not completion. For large inputs, use bounded scans and reproducible samples; declare coverage and do not certify the full dataset from a sample.

Keep sealed test outcomes outside EDA, literature workers, reviewers and tuning. Access enforcement requires separate views/mounts or a tool wrapper where supported; a prompt instruction alone is a soft control. Do not require train/test splitting for purely descriptive research that has no predictive/confirmatory holdout claim.

### Proposed artifacts

- `research/intake/data-inventory.json`
- `research/eda/eda-report.md`
- `research/eda/quality-summary.csv`
- `research/eda/figures/`
- `research/eda/eda-manifest.json`

The manifest records data fingerprint, scope/query, row/entity coverage, split fingerprint, inspected fields, sampling settings, script/command, outputs and unresolved limitations. Figure inspection needs a recorded finding, not just an image path.

**Readiness rule:** substantive analysis can begin when required checks are complete or explicitly not applicable; unresolved critical measurement/split issues block only affected claims. A cached report is usable only if its data, target, population and split scope match.

## 4. Retrieve research context automatically

### Local context first, public literature alongside it

Read supplied proposals, research questions, protocols, references and prior reports. Produce a source-grounded context summary and distinguish current documents from stale drafts. Do not silently replace the user's research question with a similar paper's question.

Use the question plus measurement/task vocabulary to search available scholarly sources. Search by:

1. Same or closely related research question and constructs.
2. Alternative methods addressing that question.
3. Comparable datasets, populations and evaluation protocols.
4. Similar findings, null results, disagreements and failed replications.
5. Foundational work and relevant newer work.

Do not search only for evidence agreeing with a preliminary result. Treat related findings as comparison evidence, not as the answer the analysis must reproduce.

### Two retrieval passes

**Before analysis:** establish methods, baselines, known limitations and plausible contribution. Start with a bounded targeted scan rather than automatically claiming a systematic review. Proposed pilot budget: up to six query families, 20 screened records and five to eight deeply examined relevant sources if available; budgets are adjustable, not minimum quality guarantees.

**After EDA:** refine terminology and search once more if the actual measurement, population or task differs from the initial description. Record why the question changed.

**After results:** add a bounded comparison pass covering agreement, disagreement and plausible reasons. Preserve the pre-analysis protocol; new literature does not license unreported outcome-driven changes.

Stop when the bounded scan has covered the key question/method/contrary-evidence slots or the allocated budget is exhausted. Report remaining gaps; never pad a bibliography to meet a count.

### Evidence and comparison schema

Store source ID, verified bibliographic fields, stable locator/version, retrieval date, access level, question, data/population, independent sample, measurements, study/split design, baseline, reported result, uncertainty, units, limitations and exact page/table/section locator. Use `not reported` or `unavailable` instead of inventing values.

Classify each comparison as `directly comparable`, `partly comparable` or `context only`, with reasons. Different outcomes, scales, populations or splits should not share a leaderboard without qualification. For theoretical/qualitative work substitute relevant propositions, constructs, corpus and methodological context.

Proposed artifacts: `research/context/context-brief.md`, `search-log.csv`, `evidence-matrix.csv`, `references.bib`, `related-results.md`. Capture abstracts as abstract-only evidence; full-method claims require inspected full text. Verify citations against primary sources and deduplicate preprint/published versions.

## 5. Native parallel-agent support

### Native first; explicit fallback

The framework should provide a coordinator, specialist definitions and a tested adapter for each supported host. It must not claim that a Markdown role file creates concurrency.

For the first adapter, target the project's existing VS Code/Copilot environment. Current official documentation distinguishes harnesses: Local uses `agent/runSubagent`, and delegation/context behavior and discovery locations differ by harness. The existing installer uses a legacy profile prompts path, so installation must resolve the active harness and verify discovery instead of assuming one universal destination.

At session start record support for spawning, actual concurrent execution, tool permissions, file access/isolation, lifecycle results, cancellation, continuation and resource limits. Verify required tools. Do not infer support from an agent name or a previous session.

If only sequential subagents are supported, use them sequentially with the same contracts. If no subagents exist, use one agent with explicit workstream artifacts and disclose sequential execution. If a strict concurrency requirement cannot be met, say so. Do not simulate worker identities in prose and claim native execution.

### Roles and scheduling

| Role | Inputs | Outputs | Ownership |
|---|---|---|---|
| Coordinator | User request, state, capabilities | Tasks, integrated plan, final report | Canonical state and synthesis |
| Data investigator | Approved data view, question, split policy | EDA/quality artifacts | Own task directory |
| Literature investigator | Question and approved non-sensitive terms | Search/evidence/results matrix | Own task directory |
| Context investigator | Approved project documents | Context brief and unresolved constraints | Own task directory |
| Methodology reviewer | Frozen discovery outputs and proposed design | Assumption/design critique | Review output only |
| Analysis worker(s) | Frozen protocol, permitted data, budget | Method results and run records | Isolated method/run directory |
| Evidence reviewer | Claims plus primary artifacts | Verification and discrepancy report | Review output only |

Use one coordinator plus at most three workers concurrently as an initial configurable default; respect lower host limits. For small tasks, combine roles or avoid delegation. No recursive worker spawning by default. Reserve part of the total budget for review/synthesis; maximum concurrency is not a target.

Only independent work runs in parallel. The design waits for relevant discovery outputs; modeling waits for required EDA/split readiness; result comparison and review wait for actual results. Parallel model runs must have explicit CPU/GPU/memory allocations so competition does not corrupt timing comparisons.

### Task/result contract

Each task includes `task_id`, role, question, input artifact hashes, dependency IDs, allowed reads, output directory, tool allowances, budget, deadline, acceptance criteria and expected schema. Send enough context explicitly; do not assume workers inherit the full conversation.

Each result includes status, input versions, artifact paths/hashes, verified findings, source locators, unresolved assumptions, warnings, measured resources and blocking errors. A narrative summary without its required artifacts is incomplete.

Workers write only their own outputs. The coordinator alone updates canonical state and integrates results atomically. Conflicting findings create an explicit discrepancy record; majority agreement among agents is not scientific verification. Reviewers receive the question, primary artifacts and necessary assumptions, without being instructed to endorse the intended result.

On a stateless host, resume with a fresh invocation and explicit artifacts. Deduplicate retries by task/input version; allow one bounded retry for a transient failure, then record the failure and continue independent work. Never silently restart completed expensive work. Record actual overlapping lifecycle intervals before claiming parallel execution.

## 6. State and enforceable checks

Proposed `research/state.json` tracks:

- Question and protocol versions; data/split fingerprints.
- Host capabilities and execution mode (`native-parallel`, `native-sequential`, `single-agent`).
- EDA, context, protocol and review statuses: `pending`, `running`, `complete`, `blocked`, `not_applicable`, `stale`.
- Task IDs, dependencies, input/output hashes, attempts, errors and measured budgets.
- Limitations, permitted downstream actions and reasons for exceptions.

A changed dataset invalidates affected EDA/results; a changed split invalidates dependent features/evaluations; a changed question refreshes literature relevance and protocol assumptions. A session restart reads validated state instead of blindly rerunning everything. Never upgrade blocked/unknown to complete after timeout.

Implement an executable readiness validator checking schemas, fingerprints, outputs and required statuses. However, file existence is not evidence of quality, and a standalone validator cannot prevent an agent bypassing it. In hosts supporting an execution hook/tool wrapper, guard the training/confirmatory entrypoint with the validator. Else label the control prompt-enforced and test compliance; do not market it as a hard runtime guarantee.

## 7. Concrete implementation backlog

| Priority | Files/components | Acceptance |
|---|---|---|
| P0 | Update main agent, router, EDA and literature skills | Thesis/model requests trigger discovery without explicit EDA/review wording |
| P0 | Add `starting-a-research-study` skill and state/EDA/context schemas | Applicability, prior exposure, current artifacts and blocked paths explicit |
| P0 | Add readiness validator and invalidation logic | Missing/stale discovery cannot be marked ready; valid reuse works |
| P1 | Add `coordinating-research-agents` skill and specialist agent definitions | Structured dispatch, ownership, join, retry and evidence contracts |
| P1 | Add capability adapter and revise installer | Active host/tool/discovery checks; native/sequential modes correctly reported |
| P1 | Add related-results template and retrieval refresh rules | Comparable/contrary evidence included with verified locators and limits |
| P2 | Add lifecycle logging, resume and host-supported execution guard | Measured concurrency, bounded failures, state recovery and no write collisions |
| P2 | Add behavioral/integration evaluation suite | Demonstrated behavior across fresh, cached, restricted and failed cases |

Implement P0 before broad parallelism: parallel workers should accelerate a correct workflow, not multiply skipped prerequisites. One tested native adapter is preferable to unsupported compatibility claims across many hosts. Add further adapters only with documented mappings and actual integration tests.

## 8. Required behavioral tests

1. “Train a model on this dataset”: EDA executes before fitting, with substantive plots/findings.
2. “Help with this thesis”: supplied context is read and related/contrary research is retrieved without a separate literature request.
3. Protected holdout: neither EDA nor workers receive test outcomes; prior exposure is recorded.
4. Fresh dataset revision: cached EDA becomes stale; unchanged artifacts are reused.
5. Unsupported/corrupt dataset: profiling failure is explicit; no fabricated report or training-ready state.
6. No internet or user forbids browsing: local work proceeds as appropriate; external gaps and unsupported novelty claims remain explicit.
7. Abstract-only source or incompatible published metric: no invented methods and no misleading numeric ranking.
8. No empirical dataset: tabular EDA is not applicable; theory/qualitative/source inspection uses appropriate criteria.
9. Three independent tasks on a supported host: lifecycle traces show actual overlap and correctly joined outputs.
10. Worker timeout/conflicting output: bounded retry/discrepancy resolution; no overwritten canonical state.
11. Native delegation unavailable: honest sequential mode with equivalent evidence requirements.
12. Resume after interruption: verified completed tasks reused, unfinished tasks resumed within budget.
13. Trivial edit: no unnecessary EDA or literature scan.
14. Prompt-bypass attempt: execution guard blocks missing readiness when supported; soft-only hosts are reported as such.

Measure prerequisite completion, scientific/citation validity, task success, latency, resource cost and unnecessary interruptions. Compare serial versus parallel workflows under equal total budgets. Unit tests alone cannot establish automatic routing, actual retrieval or host concurrency.

## 9. Primary integration references

Checked 2026-09-28; verify actual installed versions during implementation:

- https://code.visualstudio.com/docs/agents/run/subagents — native delegation and harness-specific behavior.
- https://code.visualstudio.com/docs/agent-customization/custom-agents — role definitions and invocation controls.
- https://code.visualstudio.com/docs/agents/concepts/agent-host — runtime/discovery distinctions.

These document host capabilities, not proof that the user's installed host exposes them. This proposal leaves the current 22 skills' runtime behavior unchanged until implemented and integration-tested.
