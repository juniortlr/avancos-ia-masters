# Problem definition, review and communication

## Roles
| Skill | Primary question | Output |
|---|---|---|
| defining-problem-statements | What exactly is the problem, evidence gap and intended contribution? | Versioned problem/question/objective/evidence map |
| conducting-self-review | Is my own work consistent, complete and supported? | Internal audit and corrections |
| conducting-peer-review-round | Does the argument survive structured independent critique? | Reviews, synthesis, author responses and revision verification |
| conducting-tutor-review | Is the study coherent, feasible and understood by its author? | Formative feedback and next learning/revision milestone |
| conducting-outsider-review | Can a non-specialist understand the claim without being misled? | Plain-language restatement and clarity risks |
| writing-executive-summaries | What does the audience need to know or decide? | Concise evidence-based brief |

## Relationship to the research loop

The canonical loop is **problem → baseline → hypothesis → experiment → ablation → review → problem**. Review ends with an evidence-backed decision to retain, refine, split, reject or close the problem, with a new version when necessary. A favorable review is not the only valid endpoint. See [loop controls](research-loop.md).

## Sequence
Define a provisional problem → inspect relevant data and literature → refine the statement/version → plan and execute → self-review → selected peer/tutor/outsider reviews → author response and revision verification → executive summary.

Reviews also apply to proposals and intermediate chapters, with criteria appropriate to their stage. A preliminary executive summary can precede full review if its status and unresolved issues are clear. The three review perspectives need not be mandatory for every task.

## Shared review record
Record `review_id`, `round_id`, `review_type`, `reviewer_type`, artifact version/hash, inspected inputs, access limitations and overall recommendation. Each issue records ID, locator, severity (blocking/major/minor/question), finding, evidence, consequence, proposed action and acceptance check. Each response records agreement/disagreement with rationale, changed artifact version, verification evidence and status (open/addressed/verified/disputed/deferred).

A critique cannot be closed just because text changed. Verify the relevant evidence or argument, preserve disagreements and recheck affected downstream claims. File names alone do not prove quality; honest insufficiency is preferable to a fabricated verdict.

## Peer round mechanics
Freeze a packet; collect complementary independent critiques when actual host agents are available; synthesize by evidence; record author responses; make authorized revisions; verify. Default to one bounded round and add another only for a concrete unresolved material risk. Sequential passes remain useful but must not be presented as native parallelism or independent human review.

Tutor review emphasizes learning and study coherence; outsider review emphasizes comprehension; peer review emphasizes scientific validity and contribution; self-review is explicitly non-independent. None grants official academic or publication approval. The native coordinator, runtime readiness gates and automatic intake described in the separate plan remain proposed, not implemented by these six skill files.

## Validation scenarios for future behavioral evaluation
- A proposal without results must receive a proposal review/summary, not fabricated findings.
- An unsupported novelty claim triggers source verification and limited wording.
- A reviewer requests an outcome-driven hypothesis change: preserve protocol/deviation history.
- Two reviewers disagree: retain the issue and investigate primary evidence, not majority vote.
- Native agents unavailable: label sequential review without fabricated reviewer identities.
- A technically correct but opaque manuscript routes to outsider review without claiming technical invalidity.
- Tutor feedback identifies a learning gap without inventing a university rubric or official grade.
- An executive summary retains a material limitation and matches the current result version.

These are acceptance scenarios, not completed empirical tests. Structural checks and existing helper tests do not establish scientific review accuracy.
