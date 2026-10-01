# Research Superpowers

A method-driven research agent for research across disciplines, general thesis work and reproducible papers. This upgrade expands the supplied eight-skill framework to **28 skills**: eight core workflow skills, fourteen method skills and six problem-definition, review and summary skills.

The host provides code execution, data access and search. These instructions do not constitute a standalone autonomous research service; installing skills does not install scientific packages or validate a model.

## Core loop

**problem → baseline → hypothesis → experiment → ablation → review → problem**

Each cycle establishes a reference, tests a specific claim, isolates its contribution and uses review to update or close the problem. Preserve previous cycles and evidence. See the [loop specification](docs/research-loop.md) and [cycle record](templates/research-cycle.md).

## Start here

- [Problem statements, review rounds and executive summaries](docs/review-and-communication-workflow.md)

- [Proposed automatic EDA, context retrieval and parallel-agent changes](docs/research-intake-and-parallelism-plan.md)

- [Audit, research and upgrade roadmap](docs/upgrade-research-plan.md)
- [Method catalog](docs/method-catalog.md)
- [General research workflows](docs/research-workflows.md)
- [Validation and limitations](docs/validation.md)
- [Sources and adoption decisions](docs/sources.md)

| Layer | Contents |
|---|---|
| Core | Framing, preregistration, provenance, null models, red teaming, evidence ledger, reporting, routing |
| Data/prediction | EDA, mining, classical ML, budgeted AutoML, temporal validation |
| Inference | A/B tests, causal identification, uncertainty/Bayesian methods, experimental design, reliability |
| Publication | Physics-informed validation, literature review, reproducibility, paper writing |

Read `skills/using-research-superpowers/SKILL.md` to route a task. Keep organization-specific data and rules in the downstream analysis project.

## Existing Copilot installation

From this directory on Windows with PowerShell 7:

```powershell
pwsh -NoProfile -File .\install.ps1
```

The supplied installer copies agent files to `%APPDATA%\Code\User\prompts` and skills to `~\.copilot\skills`. It overwrites matching files; review or export local customizations first. Destination arguments remain configurable. Its Windows behavior was preserved; this upgrade did not run or verify it in VS Code.

```powershell
pwsh -NoProfile -File .\install.ps1 -Export
```

Export copies this project's named installed agents/skills back into the checkout. Review the diff before accepting changes; it can overwrite the checkout and does not remove stale files.

## Other hosts

Skills use standard name/description YAML frontmatter. A host capable of reading repository files can be directed to the router and relevant sibling skills. Root `AGENTS.md` provides repository-local guidance. Automatic discovery and paths differ by host/version: verify using the host's current documented mechanism. The `.agent.md` adapter is for Copilot; no Codex/Claude/Antigravity adapter was integration-tested. No personal skills were installed while preparing this upgrade.

## Validation and helpers

Python 3.10+; only the static validator requires PyYAML. Research libraries are task-specific.

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate_project.py
python -m unittest discover -s tests -v
python scripts/audit_split.py examples/split-manifest.csv --disjoint-entities
python scripts/plan_ab.py --baseline .5 --effect .1 --units-per-period 100
```

The split auditor checks one manifest for label/time overlap, future feature availability and optional entity separation. It cannot inspect feature lineage or hidden AutoML folds; run it per fold. The A/B helper is an independent binary-outcome fixed-horizon approximation, not a clustered/sequential inference engine. Examples are synthetic or illustrative.

Use `templates/study-protocol.md` and `templates/run-manifest.json` in downstream research projects with their own dependency lockfiles.

## Principles

Preserve evidence discipline; permit honest exploration; protect evaluation outcomes; identify causal effects before estimating them; compare simple baselines; log material choices and proceed with authorized reversible work; preserve uncertainty and superseded findings.

External projects were researched, not bulk-vendored. No blanket license is assigned to the original uploaded project. Establish ownership/license before public redistribution; review per-file licenses before importing third-party components.

## Validation evidence

- [30-task synthetic pilot](validation/synthetic/research-agent-pilot-report.md): 180 structured attempts; ceiling effect limits discrimination.
- [Dota 2 real-data validation](validation/dota/REPORT.md): bounded profiling of 83 Kaggle listings plus UCI/two Zenodo sources, four modeling families, independent internal reviews and concrete next-step acceptance requirements.

These evaluations do not establish general superiority or runtime enforcement. The Dota study found initial EDA inspection remained unreliable.
