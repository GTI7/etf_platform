# `reference_h2` — Phase 2 Research Proposal — Level 2 Adversarial Review

**Level 2 — AI-assisted adversarial review.** Procedurally independent
(fresh session, no conversational continuity with the work being
reviewed, adversarial posture, claims independently re-derived from
primary sources rather than inspected at face value). **NOT
organizationally independent** (same underlying model family/vendor as
the work being reviewed; no incentive separation; no accountable,
persistent reviewer role) — per `docs/RESEARCH_GOVERNANCE_STANDARD.md`
§4, this qualifier is required and this review must never be described
with the unqualified word "independent."

**Reviewer:** Claude Sonnet 5, fresh session, 2026-07-28. This session has
no memory of, and no conversational connection to, whatever session(s)
produced `research_proposal.md`, `hypothesis.md`, or the two Phase 5
memos cited below. That claim is self-reported and not independently
verifiable by a third party, exactly as §4 states of every Level 2
review.

**Commit reviewed.** `7e7566f272819b441ed7d036ae3f952ea4c12a3f`. Confirmed
via `git log -1 --format="%H"` immediately before this review began;
`git status --porcelain` was empty (clean tree) at that time. All
findings below are checked against the files at this exact commit.

**Scope reviewed.** `research_archive/reference_h2/research_proposal.md`
(primary subject), read together with
`research_archive/reference_h2/hypothesis.md`,
`docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`,
`docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md`, and
`docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md`, plus (as
citation-chain verification requires) `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`
(v1), `docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md`, `core/research/lifecycle.py`,
and `git log` on all of the above. No file was modified. Nothing was
committed by this review.

---

## 1. Citation chain integrity

Checked every attributed claim, quote, and table cell in
`research_proposal.md` against its cited source.

**Holds up:**
- The six-candidate ranking order (H2, H6, H7, H4, H5, H8) in §2 matches
  `REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`'s "Ranking summary" table
  exactly, in the same order.
- Every cell of the proposal's §2 table (Economic rationale, Overlap,
  Data readiness, DoF risk, Expected value, all six candidates) was
  checked cell-by-cell against the V2 roadmap's ranking summary table.
  All match, some lightly paraphrased but never strengthened or
  weakened in meaning.
- All four rejected-alternative paragraphs (H5, H6, H7, H8) in §4 match
  `PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` §4 essentially
  verbatim, with no added or dropped substance.
- The H4 sourcing disclosure in §2 and §4 is accurate: I independently
  confirmed `PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` frames the
  field as a five-candidate shortlist (§1, §3, §4 all discuss only H2,
  H5, H6, H7, H8) and never mentions H4. The proposal's decision to
  source H4's row from the V2 roadmap instead, and to say so explicitly,
  is correct and is exactly the kind of disclosure a citation check
  should reward.
- The quote "not on any expectation, stated or implied, that it will
  validate" (§3) matches `PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md`
  §1 verbatim.
- The quote "ranked H1 first and H3 second, prior to H1's own testing"
  (§3) matches `REFERENCE_RESEARCH_ROADMAP_NEXT.md`'s opening framing
  (line 10-11) in substance and near-verbatim wording.
- The quote "No use of REFERENCE v1's results to select or tune v2's
  parameters" (§3) matches `REFERENCE_V1_RESEARCH_CLOSEOUT.md` line 307
  verbatim (item heading, across a line wrap).
- The quote "No parameter tuning of v1 (or H1)" (§3), attributed to
  `REFERENCE_RESEARCH_ROADMAP_NEXT.md` §4 item 3, matches verbatim, and I
  confirmed that §4 is in fact the entry-requirements section that
  governed the candidate that became `reference_h3` (the same document's
  §5 recommends H3 explicitly).
- §6's claim about `core/research/lifecycle.py`'s
  `_TRANSITION_AUTHORIZATION_FLOORS` setting a Level 2 floor on
  `(RESEARCH_PROPOSAL, PRE_VALIDATION)` is correct — I read the table
  directly at line 159: `(LifecyclePhase.RESEARCH_PROPOSAL,
  LifecyclePhase.PRE_VALIDATION): 2`.

**Does not hold up — flagged in detail under §2 below:** §1's claim "No
criterion here is new; none was added, dropped, or adjusted after any
candidate's score was seen" is not supported by the record and is
contradicted by it once you look one document further back than the
proposal's own citation list.

## 2. Ranking-criteria discipline — FAILS as stated

This is the review's central finding.

`docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`'s "Remaining Candidates"
section scores the same six candidates (H2, H4, H5, H6, H7, H8) against
five criteria: economic rationale, overlap with closed tests, data
requirements, degrees-of-freedom risk, and **expected research value**.

`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` (v1, committed `1091a015`,
2026-07-18 — ten days before v2) already scored these same candidates
once, in its own §5 "Ranked candidate directions" table, against **four**
criteria: economic justification, independence from v1/H1, data
availability, overfitting risk. There is no fifth column. "Expected
research value" does not appear anywhere in v1's scoring pass of these
candidates.

This means a criterion was added to the scoring framework, for the same
set of candidates, in the second of two scoring passes conducted ten
days apart — and the proposal's own text ("no criterion... was added...
after any candidate's score was seen") asserts the opposite of what the
committed record shows. I checked this directly against `git log
--date=iso-strict` on both files; the dates and hashes are not in
dispute.

Two aggravating details:

- `REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md` itself states, immediately
  before listing the five criteria, that the candidates are "re-ranked
  below against **the four factors** this memo is scoped to" — then
  lists five. This internal contradiction in the source document is not
  noticed, flagged, or resolved anywhere in `research_proposal.md`,
  which cites this exact passage as the source of "criteria fixed before
  any candidate was scored."
- The un-disclosed fifth criterion is not incidental to the outcome: it
  is the one axis on which H2 is rated strictly higher ("High,
  conditional on clearing the overlap gate") than every other
  High-economic-rationale, stronger-independence candidate (H5, H8 both
  rated "Medium" or "Low" here) — i.e., it is doing real work in keeping
  H2 ranked first ahead of candidates that score better than H2 on
  independence from closed cycles. A criterion introduced at the exact
  point a specific candidate is being re-evaluated, that happens to be
  the deciding factor in that candidate's favor, is precisely the
  scenario Phase 2's "fixed before scoring" rule exists to prevent —
  whether or not that is what actually happened here.

**In fairness to the document:** the origin of this fifth criterion is
genuinely unverifiable, not provably fabricated. `REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`
itself notes the candidate pool traces to "REFERENCE v2's 8-candidate
shortlist, itself never persisted as a standalone file" (a gap already
disclosed independently in `research_archive/reference_h3/decision_log.md`
Entry 1 and reiterated in the reference_h4 Level 2 review at
`research_archive/reference_h4/reviewer_reports/2026-07-25_level2_adversarial_review.md`).
It is possible "expected research value" was one of the original eight
dimensions, simply unused in v1's four-of-eight subset and restored in
v2. That would make its reappearance legitimate. But nothing in
`research_proposal.md`, `REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`, or
`PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` says this, argues it,
or even acknowledges that a discrepancy with v1's four-criteria pass
exists. The proposal's Section 1 asserts a categorical, checkable fact
("none was added... after any candidate's score was seen") that turns
out to be false on the narrowest reading of the record available to me,
and is at best unverifiable — never merely true — on the most generous
reading available to me.

**Everything else under this check passes.** I did not find any instance
of H2 being scored more favorably than a rejected alternative on a given
criterion without a stated reason; every differential rating I checked
(data readiness across H2/H4/H5/H6/H8; DoF risk across H2/H5/H6) traces
to an explicit, substantive distinction stated in the roadmap text (e.g.
H4's volume-contamination problem is explicitly distinguished from H2's
purely calendar-depth-driven constraint in the "Historical Depth
Decision" section).

## 3. Rejected-alternatives completeness — passes

All five non-H2 candidates (H4, H5, H6, H7, H8) have specific, checkable,
non-generic rejection reasons in §4:

- H4 — a named measurement-validity defect (creation/redemption
  contamination) that does not improve with more data, plus an explicit
  disclosure that this entry is sourced differently from the other four.
- H5 — a named, concrete infrastructure gap (no yield field in the
  current schema; new external source and new provenance obligations
  required).
- H6 — two independently stated grounds: overlap with `reference_h3`'s
  own significant reversal result, and a specific window-count
  degradation claim (as few as 4-8 independent windows).
- H7 — a specific, named freeze-discipline problem (no a priori
  direction; committing to a sign would introduce an undisclosed
  degree of freedom), not a data or independence complaint.
- H8 — two named requirements (new macro data source, new statistical
  infrastructure beyond the platform's reused `mean_ic` /
  `permutation_null` / `holm_bonferroni` / `bootstrap_ci` stack) plus an
  explicit degrees-of-freedom ranking.

None of the five reads as boilerplate "lower priority" language, and
none is a rewritten or softened version of what the cited sources
actually say — each traces to the same specific reasoning recorded in
the Phase 5 documents.

## 4. Chronology addendum (§7) — independently re-derived, holds up

I re-ran the chronology claims from primary `git log` data rather than
trusting the addendum's narrative:

```
76382b59d43be6ecbbc4af974ad16fed85516aa2  2026-07-28T00:03:57+02:00  docs: add Phase 5 research roadmap reassessment and hypothesis selection review
97961d4f94666b6e3505d2f610867c17ff1c4549  2026-07-28T00:19:00+02:00  docs: add Phase 5 Gate 0 preparation review for H2
c0d5a18b96fa0d596766ae6aafab94a8db97e78f  2026-07-28T01:17:31+02:00  Add H2 Phase 2 research proposal artifact
```

All three hashes exist, are reachable from the reviewed commit's
history, and touch the files the addendum says they touch
(`REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md` +
`PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` in `76382b5`;
`PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` in `97961d4`; the
proposal itself in `c0d5a18`). The stated ordering (`76382b5` <
`97961d4` < `c0d5a18`) is correct. The stated interval — Gate 0 review
predates the proposal's original drafting "by 58 minutes" — checks out
exactly: `01:17:31 − 00:19:00 = 0:58:31`. This is exactly the kind of
claim a Level 2 review should re-derive rather than trust, and it
survives re-derivation cleanly.

The addendum's substantive point — that the Gate 0 review's database
finding (extended history already present, so H2's depth requirement is
already largely met) existed in the repository *before* the proposal's
original Section 2 table was drafted, and was therefore an omission at
authorship time rather than new evidence arriving later — is consistent
with the commit timestamps above.

## 5. Scope discipline — passes

Section 5's "Deferred Decisions Boundary" (formation period, skip
interval, return basis, ranking method, tie handling, forecast horizon,
evaluation metrics, rejection/promotion criteria) and Section 6's
approval-state disclaimer are not contradicted anywhere later in the
document, including the Section 7 addendum. The addendum repeatedly and
explicitly declines to let the Gate 0 finding retroactively change the
Section 2 table, the Section 3 selection, or the Section 4 rejections,
and closes with an explicit list of the same undecided items restated
from Section 5. I looked specifically for a case where the "stale, not
yet corrected" data-readiness rating for H2 was quietly used to make H2
look better than it should — it is not: leaving H2's rating at "Needs
depth extension" rather than updating it to reflect the Gate 0 finding
is, if anything, conservative against H2's own interest, not
self-serving.

One residual scope concern, short of a violation: Section 2's ranking
table is now known (by the document's own admission in §7) to rest on a
stale premise for one of its five criteria (H2's data readiness), and
the document declines to re-run or re-check the comparative ranking
under the corrected premise, deferring that to Phase 3. That is a
defensible reading of "Phase 2 ranks against fixed criteria, it does not
re-verify factual premises," but it does mean the Section 2 table
currently on record is known-outdated in one cell, publicly, and remains
uncorrected specifically in this artifact — worth a forward reference in
a future revision, not itself a scope-discipline breach.

## 6. Honesty about own review level — passes

The document states "Level 1 self-review" in its header, restates the
Phase 2 approval-state requirement (Level 1 minimum, Level 2 required
before Pre-validation) twice (§0 preamble and §6), and explicitly
declines to adopt `reference_h4`'s prior (and, per this proposal's own
correct reading, incorrect) claim that "Level 2 is not required to
progress into Pre-validation." I found no place in the document where it
overclaims independence, completeness, or review level. This is
handled correctly and is a genuine strength of the artifact.

## 7. Verdict

**PASS/FAIL on Level 2 review: FAIL.**

Five of six checks (citation-chain accuracy elsewhere in the document,
rejected-alternatives completeness, chronology-addendum accuracy,
scope discipline, and honesty about review level) hold up under
adversarial, independently-re-derived scrutiny. But Section 1's
categorical claim that the five ranking criteria were fixed once, never
added to, dropped, or adjusted after any candidate's score was seen is
false on the plainest reading of the committed record (v1's
four-criterion scoring pass of the same candidates, ten days before v2's
five-criterion pass introduced "expected research value" without
comment), and at best unverifiable on the most generous available
reading. A Level 2 review's job is to catch exactly this kind of
checkable-but-unchecked claim, and it does not survive being checked.
This is not a cosmetic defect: the added criterion is the specific axis
that keeps H2 ranked ahead of candidates with stronger independence from
closed cycles (H5, H8), so the discipline violation, if it is one, bears
directly on the legitimacy of the Selection in §3, not merely on
Section 1's prose.

**Transition eligibility (RESEARCH_PROPOSAL → PRE_VALIDATION): NOT
AUTHORIZED to proceed as currently written.**

`core/research/lifecycle.py`'s `_TRANSITION_AUTHORIZATION_FLOORS` (line
159) sets an unconditional Level 2 floor on this transition, per AD-072.
This review is a genuine Level 2 pass, but it does not certify the
artifact — it identifies a specific, unresolved defect in the Ranking-
criteria discipline check. Under this standard's own logic (a Level 2
review exists to be actionable, not decorative), a FAIL verdict from the
review required to clear this floor means the floor is not cleared. This
is a governance-floor conclusion about process compliance, not a
statement about whether H2's underlying hypothesis is scientifically
sound — the hypothesis may well be a reasonable candidate; the specific
defect is that the document's own compliance claim about how it got
ranked does not hold up, and that must be corrected (either by
justifying the fifth criterion's provenance, or by removing/qualifying
the "no criterion was added" claim and explicitly disclosing the v1→v2
discrepancy) before a Level 2 sign-off can be honestly recorded.

No lifecycle transition record, prevalidation_plan.md, experiment, or
implementation code was created, run, or referenced in the course of
this review, consistent with this review's scope.
