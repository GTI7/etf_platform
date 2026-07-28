# `reference_h2` — Phase 2 Research Proposal — Level 2 Adversarial Review (HEAD `201b8ae`)

**Level 2 — AI-assisted adversarial review.** Procedurally independent
(fresh session, no conversational continuity with the work being
reviewed, adversarial posture, claims independently re-derived from
primary sources — commit hashes, table cells, and quotes were checked
directly against the files, not inspected at face value or taken from
either prior review artifact's narrative). **NOT organizationally
independent** (same underlying model family/vendor as the work being
reviewed; no incentive separation; no accountable, persistent reviewer
role) — per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4, this qualifier is
required and this review must never be described with the unqualified
word "independent."

**Reviewer:** Claude Sonnet 5, fresh session, 2026-07-28.

**Review date:** 2026-07-28.

**Commit reviewed.** `201b8ae5a78086234fb1bc251a0fee862c472b0d`. Verified
directly via `git rev-parse HEAD` and `git branch --show-current`
(`master`) immediately before this review began; `git status
--porcelain=v1` was empty (clean tree) at that time.

**Relationship to prior review artifacts.** This is a new, independent
Level 2 pass — not a re-scoring of, edit to, or replacement for:
- `research_archive/reference_h2/reviewer_reports/2026-07-28_level2_adversarial_review.md`
  ("the original FAIL review," commit `7e7566f`, verdict FAIL) — left
  unmodified, verified by diff.
- `research_archive/reference_h2/reviewer_reports/2026-07-28_level2_review_clarification.md`
  ("the clarification," reclassified the original review's central
  finding from implied disproof to "claim exceeds available evidence,"
  but held the FAIL verdict standing pending a wording correction) — left
  unmodified, verified by diff.

This review answers a different, narrower question than either: does the
proposal **as it exists right now**, at `201b8ae`, clear the Level 2
floor — independent of whether the prior FAIL review's reasoning was
itself airtight.

---

## Repository state verified

- Branch: `master`.
- HEAD: `201b8ae5a78086234fb1bc251a0fee862c472b0d`.
- Working tree: clean (`git status --porcelain=v1` empty).
- `git log --oneline -10` confirms the expected commit sequence ending at
  `201b8ae` ("Remediate unsupported provenance claim in H2 proposal
  Section 1"), preceded by `9a54306` (clarification), `d6d51af`
  (preserve original FAIL review), `7e7566f` (the commit the original
  FAIL review actually reviewed), `8e6fa80`, and earlier proposal-drafting
  commits.
- `git diff --stat 7e7566f 201b8ae` confirms exactly three files changed
  between the commit the original FAIL review evaluated and current HEAD:
  the two new reviewer-report files (301 and 103 lines added,
  respectively — pure additions) and a **2-line diff** (1 insertion, 1
  deletion) in `research_archive/reference_h2/research_proposal.md`. No
  other file in the repository differs between those two commits.

## Evidence reviewed

Read directly, in full, at current HEAD:
`research_archive/reference_h2/research_proposal.md`,
`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`,
`docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`,
`research_archive/reference_h3/decision_log.md` (Entry 1 and surrounding
entries), `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 and §4,
`core/research/lifecycle.py` (`_TRANSITION_AUTHORIZATION_FLOORS`), both
existing reviewer-report artifacts, and (spot-check)
`docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md`. Also ran
`git log`/`git diff`/`git show --stat` directly rather than trusting any
document's narrative account of what changed or when.

## Provenance analysis

Independently confirmed, against the primary documents:

- **V1** (`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`, committed
  `1091a01`, 2026-07-18) scores the same candidate pool against **four**
  named criteria (economic justification, independence from v1/H1, data
  availability, overfitting risk) in its §5 table. Line 158 discloses,
  in its own text, that these are "the four criteria specified for this
  memo, not the fuller 8-dimension evaluation the original strategy
  document used."
- **V2** (`docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`, committed
  `76382b5`, 2026-07-28) scores the same six remaining candidates against
  **five** criteria, the fifth being "Expected research value," in its
  "Ranking summary" table.
- The original 8-dimension framework is confirmed absent from this
  repository: `research_archive/reference_h3/decision_log.md` Entry 1
  states directly, "The original 8-hypothesis document that first ranked
  H3 is not present in this repository as a primary source (known only
  secondhand)."
- **Additional item, independently noticed, not cited by either prior
  review artifact's classification section:** V2's own prose contains an
  internal inconsistency — immediately before listing five criteria, it
  states the candidates are "re-ranked below against **the four
  factors** this memo is scoped to," then lists five. This is a genuine
  textual defect in the *source* document, not in the proposal. It is
  weak, ambiguous evidence (consistent with "four" being a copy-forward
  artifact from v1's four-criteria framing, left unedited when a fifth
  criterion was added) — it does not resolve the provenance question
  either way, but it is a piece of primary-source evidence bearing on it
  that the current proposal's Section 1 does not mention.

**Determination on the three-way question posed:**

(A) Can the repository prove criterion 5 was introduced later? **No.**
(B) Can the repository prove criterion 5 existed before? **No.**
(C) **The historical origin cannot be established from this repository.**
This is the only conclusion the evidence supports, and it is the
conclusion both the original review (in its "In fairness to the
document" paragraph) and the clarification (explicitly) already reached.
Independent re-derivation does not change this.

## Proposal Section 1 assessment

`git diff 7e7566f 201b8ae -- research_archive/reference_h2/research_proposal.md`
shows the entire remediation is a single-sentence replacement. The
**prior** wording (as the original FAIL review correctly evaluated) read:

> "These criteria were stated before the six candidates were scored
> against them and were not reweighted afterward. No criterion here is
> new; none was added, dropped, or adjusted after any candidate's score
> was seen."

This asserted a categorical, checkable fact contradicted by v1's own
four-criteria pass of the same candidates ten days earlier — the
original review's central, correctly-identified finding.

The **current** wording (`201b8ae`) reads:

> "These criteria are fixed for this cycle's own scoring pass in
> `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md` — Section 2's table below
> applies all five uniformly to all six candidates — and were not
> reweighted afterward. Whether criterion 5 ('Expected research value')
> existed in an earlier, unrecorded criteria set or was introduced for
> this cycle cannot be established from the repository: [cites v1 line
> 158 and decision_log Entry 1]."

Checked against the Step 3 rubric:

- **Limits claims to available evidence.** Yes. The claim is now scoped
  to "this cycle's own scoring pass" (v2's application of its five
  criteria uniformly across all six candidates, unreweighted after
  scoring) — a narrower, verifiable claim, not the broader, falsified
  claim that no criterion was ever added relative to any prior pass.
- **Explicitly discloses unresolved provenance.** Yes, in the same
  sentence, with two specific, checkable citations.
- **Distinguishes final-cycle scoring from historical origin.** Yes —
  this is precisely what "fixed for this cycle's own scoring pass...
  Whether criterion 5... existed in an earlier... set... cannot be
  established" does: it separates "was this cycle's own process
  internally consistent" (yes, uniformly applied) from "did a criterion
  get added relative to some earlier point" (unknown, disclosed as
  unknown).
- **Avoids claiming criterion 5 was new.** Confirmed — the sentence
  states this "cannot be established," not that it was new.
- **Avoids claiming criterion 5 always existed.** Confirmed, same
  reasoning.

**Residual observation (not a FAIL condition):** Section 1 does not cite
V2's own "four factors... [lists five]" internal wording inconsistency,
which is additional primary-source evidence touching this exact
question. Its omission does not make any current claim in Section 1
false — the "cannot be established" conclusion holds regardless, since
this piece of evidence is ambiguous rather than resolving — but a
maximally thorough disclosure would have cited it alongside the two
citations already given. This is noted as a forward-improvement item,
not a defect that reintroduces unsupported certainty or hides a
limitation material to the verdict.

**Assessment: PASS.** The current wording accurately limits its claim to
what the repository can support and correctly discloses what it cannot
resolve.

## Research integrity assessment

`git diff 7e7566f 201b8ae -- research_archive/reference_h2/research_proposal.md`
confirms the remediation touched exactly one sentence (1 insertion, 1
deletion) in Section 1. Independently confirmed:

- **Ranking (§2 table):** unchanged — identical to the version the
  original review checked cell-by-cell against V2's table.
- **Scores:** unchanged.
- **Ordering:** unchanged (H2, H6, H7, H4, H5, H8).
- **H2 selection (§3):** unchanged.
- **Rejected alternatives (§4):** unchanged — independently spot-checked
  the H4-sourcing disclosure and the "not on any expectation... it will
  validate" quote directly against
  `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md`: that document
  indeed contains zero occurrences of "H4" (confirming the proposal's
  disclosure that H4 is sourced from the V2 roadmap instead, not from
  this document), and the quote matches verbatim.

This is a wording-only remediation, as the task expected it to be.

## Governance integrity assessment

- The original FAIL review (`2026-07-28_level2_adversarial_review.md`)
  was added once, in commit `d6d51af`, as a pure addition (301 insertions,
  0 deletions), and does not appear in the diff between `d6d51af` and
  `201b8ae` — it remains byte-identical to what was committed and is
  unedited.
- The clarification (`2026-07-28_level2_review_clarification.md`) was
  added once, in commit `9a54306`, as a pure addition (103 insertions, 0
  deletions), and likewise does not appear in any subsequent diff —
  unedited.
- This review evaluates HEAD `201b8ae` directly, verified by
  `git rev-parse HEAD` at the start of this review, not the commit
  (`7e7566f`) the original FAIL review evaluated.
- No lifecycle transition has occurred: `find . -iname
  transition_records.jsonl` returns exactly one file in the repository
  (`research_archive/reference_h4/transition_records.jsonl`); no such
  file exists anywhere under `research_archive/reference_h2/`. No
  `DecisionRecord`, `advance_phase()` call, or `compose_transition()`
  output for `reference_h2` was found, created, or referenced.
- `core/research/lifecycle.py` line 159 confirms the
  `(RESEARCH_PROPOSAL, PRE_VALIDATION)` transition still carries an
  unconditional Level 2 floor (AD-072) — unchanged from what the prior
  review artifacts state.

## Findings

1. **(Resolved)** The categorical, falsified provenance claim identified
   by the original FAIL review ("no criterion... was added... after any
   candidate's score was seen") has been replaced with a claim correctly
   scoped to this cycle's own scoring pass, paired with an explicit
   disclosure that criterion 5's historical origin cannot be established
   from the repository. Independently verified against v1's four-criteria
   table, v2's five-criteria table, and `decision_log.md` Entry 1.
2. **(Confirmed, non-blocking)** V2's own text contains an internal
   "four factors... lists five" inconsistency not cited anywhere in the
   current proposal's Section 1. This is weak, ambiguous evidence on the
   provenance question and does not change the "cannot be established"
   conclusion; noted as a forward-improvement item for a future revision
   of Section 1, not a defect requiring a FAIL verdict here.
3. **(Confirmed)** No ranking, score, ordering, selection, or
   rejected-alternative content changed as part of this remediation —
   the fix is wording-only, exactly as the proposal's own scope
   discipline (Section 5/6) requires of a Phase 2 artifact.
4. **(Confirmed)** No lifecycle transition, transition record, or
   Pre-validation artifact exists for `reference_h2` as of this review.

## Final verdict

**PASS**

The current research proposal at HEAD `201b8ae` satisfies the Level 2
evidence and provenance requirements for Section 1's ranking-criteria
claim. This PASS does **not** mean the historical origin of criterion 5
("Expected research value") has been discovered — it has not, and the
repository does not contain the evidence needed to discover it. It means
the proposal's own claim about that unresolved history is now accurately
scoped and honestly disclosed, rather than asserting a certainty the
record does not support. Combined with the citation-chain, rejected-
alternatives, chronology, scope-discipline, and review-level-honesty
checks — independently spot-checked here and unaffected by the
remediation — the proposal as a whole clears the Level 2 floor for the
Research Proposal artifact.

## Transition status

No lifecycle transition authorized by this review.
