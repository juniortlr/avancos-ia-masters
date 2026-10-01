# Sources and adoption decisions

Checked 2026-09-28. Live pages and search indexes can differ; recheck versions before implementation. No external skill text/code was copied. New procedures are original synthesis; popularity is not evidence of correctness.

| Primary source | Inspection and relevance | Decision |
|---|---|---|
| [K-Dense Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills) | Repository overview inspected; broad science collection | Strongest inspected specialist candidate; adopt selectively |
| [K-Dense scikit-learn skill](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scikit-learn/SKILL.md) | Body inspected: supervised/unsupervised learning, pipelines, fold-local preprocessing; declares BSD-3-Clause | Optional implementation reference; preserve our group/time contracts |
| [K-Dense catalog](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/docs/skills.md) | Indexed catalog confirms EDA and experiment/statistics workflows; some direct bodies unavailable | EDA, statistics, literature review and DOE candidates require individual review before adoption |
| [Anthropic skills](https://github.com/anthropics/skills) | Primary repository retrieved; general skill/artifact reference | Packaging reference, not scientific method replacement; check per-skill terms |
| [VoltAgent data analyst](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/main/categories/05-data-ai/data-analyst.md) | Primary search result describes role prompt; full data-scientist body unavailable | Lower-priority role reference, not a validated scientific workflow |
| [scikit-learn pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) and [cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) | Official preprocessing/leakage page inspected; CV indexed | Training-fold-only transformations; deployment-relevant splitting |
| [FLAML](https://microsoft.github.io/FLAML/docs/Use-Cases/Task-Oriented-AutoML/) | Official AutoML page retrieved | Candidate bounded tabular engine; verify installed API and folds |
| [Optuna Study API](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.study.Study.html) | Official indexed API includes n_trials and timeout | Custom objective candidate; verify hard resource caps separately |
| [AutoGluon tabular](https://auto.gluon.ai/stable/tutorials/tabular/tabular-essentials.html) | Official indexed time limits/presets | Optional ensemble benchmark; verify memory and internal folds |
| [DoWhy example](https://www.pywhy.org/dowhy/main/example_notebooks/dowhy_simple_example.html) and [refutation](https://www.pywhy.org/dowhy/main/user_guide/refuting_causal_estimates/refuting_effect_estimates/index.html) | Official indexed identification/estimation/refutation workflows | Useful causal structure; refuters do not prove hidden confounding absent |
| [Microsoft SRM research](https://www.microsoft.com/en-us/research/publication/diagnosing-sample-ratio-mismatch-in-online-controlled-experiments-a-taxonomy-and-rules-of-thumb-for-practitioners/) | Primary publication indexed | Assignment/instrumentation diagnostics for A/B tests |
| [NIST design selection](https://www.itl.nist.gov/div898/handbook/pri/section3/pri33.htm) | Official handbook indexed | Select DOE by scientific objective and factor structure |
| [SciPy Wilcoxon](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html) | Body inspected: assumptions, exact methods, ties/zeros | Correct original universal small-sample bound |
| [PRISMA checklist](https://www.prisma-statement.org/prisma-2020-checklist) and [scoping](https://www.prisma-statement.org/scoping) | Official reporting resources indexed | Apply to appropriate review type; not a study-quality certificate |

Before importing: inspect complete skill/scripts, dependency/network behavior, current revision and per-file license; preserve notices, resolve instruction conflicts, run a small task and pin the reviewed revision. A collection-level MIT label does not override distinct bundled licenses. Unretrieved bodies remain candidates.

PyMC/ArviZ, statsmodels, EconML and reliability libraries are optional method choices, not installed/API-tested integrations. Consult their current official docs during execution. No compatibility claim is made here.
