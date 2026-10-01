---
name: reproducing-research
description: "Use when: Reproduce research results and maintain experiment manifests, seeds, environments, data versions and independently rerunnable scientific artifacts."
---

# Reproducing Research


## Procedure
1. Name the claim and acceptance tolerance; distinguish rerunning original code from independent reimplementation and external replication. Reproduction failure may reflect missing inputs, not a false scientific claim.
2. Record input hashes/source versions, extraction query, target/feature definitions, split IDs, code revision, command, package versions, hardware and all random seeds. Keep confidential raw data and credentials outside version control.
3. Separate raw inputs, derived data, configurations and results. A manifest checksum excludes volatile creation timestamps. Validate schema and joins before computation; fail on unexpected changes.
4. Run from a clean process with explicit configuration. Avoid hidden notebook state. Capture stdout/stderr, failures and actual wall time. State hardware-dependent nondeterminism instead of promising bitwise reproducibility.
5. Trace each headline number to a saved result row and each figure to its generation command. Compare reproduction to reference with a predeclared tolerance and explain discrepancies.
6. Preserve superseded runs and claims with status/reason; do not overwrite inconvenient outcomes. Supply a small synthetic smoke test when real data cannot be distributed, clearly labeled synthetic.
## Deliver
Write `run-manifest.json`, environment lock/export, commands, metrics, inspected figures and `reproduction-report.md`. Check that a second process can recreate the claimed artifacts.
## Stop or hand off
If restricted data or unavailable hardware prevents reproduction, report exactly which steps ran and which remain unverified. Do not equate repository structure checks with scientific validation.
