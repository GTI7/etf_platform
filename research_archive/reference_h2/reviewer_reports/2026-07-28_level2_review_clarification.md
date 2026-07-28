# `reference_h2` — Level 2 Review Clarification

**Date:** 2026-07-28.
**Relates to:** `research_archive/reference_h2/reviewer_reports/2026-07-28_level2_adversarial_review.md`
("the original review"), which reviewed
`research_archive/reference_h2/research_proposal.md` at commit
`7e7566f272819b441ed7d036ae3f952ea4c12a3f` and returned a verdict of
**FAIL**.

**Purpose.** This document refines the original review's finding. It
does not replace, edit, or soften the original review, which remains
available unchanged at the path above and continues to state its own
conclusions in its own words. This clarification addresses only the
evidentiary strength of one specific finding within that review — the
Ranking-criteria discipline check (§2 of the original review) — and
does not reopen, re-run, or re-score any other part of it.

## What the original review got right

The original review correctly identified a real provenance weakness:
`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` (v1, committed `1091a015`,
2026-07-18) scored these candidates against four named criteria, while
`docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md` (v2, committed `76382b59`,
2026-07-28) scores the same candidate pool against five, the fifth
being "Expected research value." The research proposal's Section 1
statement — "No criterion here is new; none was added, dropped, or
adjusted after any candidate's score was seen" — is a categorical,
unqualified claim that this discrepancy puts in question. Flagging this
was correct and the discrepancy is real.

## Where the original review's verdict language overstated the evidence

The original review's verdict (§7) states the proposal's claim "is
false on the plainest reading of the committed record" and its §2
header reads "FAILS as stated" — language asserting the claim is
disproven. The repository does not support that strength of
conclusion.

`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` line 158 discloses, in its
own text, that its four criteria are "the four criteria specified for
this memo, not the fuller 8-dimension evaluation the original strategy
document used." `research_archive/reference_h3/decision_log.md`, Entry
1, independently confirms that this original, broader source document
"is not present in this repository as a primary source (known only
secondhand)."

This means v1's four-criteria pass is a disclosed subset of an
unrecovered, larger framework, not a complete enumeration of every
criterion available at that time. The absence of "Expected research
value" from v1's stated four is therefore consistent with either of two
possibilities, and the repository does not contain evidence that
distinguishes between them:

- criterion 5 was newly introduced when v2 was written, or
- criterion 5 was part of the earlier, unrecovered framework and simply
  was not selected into v1's four-item subset.

Neither of the above is asserted by this clarification as the correct
account. Both remain open. The repository proves only that it cannot
settle the question — not which answer is right.

## Corrected classification

The finding is reclassified from an implied disproof to:

**"Claim exceeds available evidence; unsupported as written."**

This is not a downgrade of the finding's importance and it does not
convert the verdict to PASS. An unqualified categorical claim that the
repository cannot verify is, on its own, a valid basis for a Level 2
finding, independent of whether the underlying historical fact turns
out to be true.

## Effect on the Level 2 verdict

**The Level 2 FAIL stands.** `core/research/lifecycle.py`'s
`_TRANSITION_AUTHORIZATION_FLOORS` sets an unconditional Level 2 floor
on the `RESEARCH_PROPOSAL → PRE_VALIDATION` transition (AD-072). A
Level 2 review that identifies an unsupported categorical claim in the
reviewed artifact has not certified that artifact, regardless of
whether the claim is corrected to "false," "unsupported," or anything
else — the floor is not cleared until the proposal's wording is
corrected and a fresh Level 2 review passes it.

This clarification does not authorize `PRE_VALIDATION`. No lifecycle
transition has been authorized by the original review, by this
clarification, or by any other artifact as of this date. No entry
exists in any `transition_records.jsonl` file for `reference_h2`
(verified directly against the repository at the time of writing).

## What this clarification does not claim

For the avoidance of doubt, this document does not assert:

- that criterion 5 ("Expected research value") was newly introduced in
  v2;
- that criterion 5 existed prior to v1's scoring pass;
- that H2's ranking, selection, or the rejected-alternatives reasoning
  in `research_proposal.md` §2–§4 is invalid.

Those questions are either unresolved (the first two) or unaffected by
this finding (the third), and this document takes no position on them
beyond what is stated above.
