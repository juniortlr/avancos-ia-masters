---
name: evidence-ledger-and-gates
description: "Use when: recording a claim or its source, deciding whether a phase or milestone can close, auditing which assertions in a spec are actually supported, tracking provenance of facts taken from wikis tickets papers or colleagues, resolving a contradiction between a document and the data, withdrawing a superseded finding, or asking 'do we actually know this or did someone say it'"
---

# Evidence Ledger and Gates

Track sources, claims and acceptance criteria separately. Provenance is not a ranking of scientific validity.

## Source categories
- E1: primary local artifact or computation; record inputs, code and access requirements.
- E2: source summary; link to the original and preserve scope and retrieval/version information.
- E3: external system record; identify the record, access conditions and retrieval date.
- E4: published research, standard or dataset; verify version, locator and methodological quality.
- E5: personal communication; identify it as such. It cannot establish an independently verified empirical claim by itself.

Qualitative testimony and interview material may be primary study data when collected and analyzed under an appropriate method. Do not confuse that with an unverified informal assertion.

## Registers
Claims: `claim_id, claim, scope, source_id, verdict, assumptions, limitations, status`.
Sources: `source_id, title, type, locator, version, retrieved_on, access, quality_notes`.
Verdicts: `SUPPORTED`, `CONTRADICTED`, `UNSUPPORTED`, `UNVERIFIED-EXT`, `OPEN`, `ASSUMPTION`.
A supported verdict means evidence supports the scoped claim under stated assumptions, not that it is proved beyond revision.

## Gates
Define criteria and acceptance checks appropriate to the research method. Quantitative criteria need computed evidence; source verification, proof review or a documented qualitative audit can satisfy other criteria. A number is not mandatory for every valid research contribution.

Record PASS, PARTIAL, AMBER, RED or OPEN with criterion-level evidence and permitted next steps. Treat assumptions explicitly rather than reclassifying source categories as verdicts. Run authorized reversible checks automatically; seek scientific sign-off or release approval only when required and not already authorized.

## Changes and withdrawals
Preserve prior versions and append the changed claim, new evidence, reason, affected scope and surviving conclusions. Revisit dependent claims when a source changes. Never erase inconvenient results.

## Deliver
Updated source/claim registers and criterion-level acceptance records. Keep confidential source material within its authorized access boundary; summaries do not bypass those restrictions.
