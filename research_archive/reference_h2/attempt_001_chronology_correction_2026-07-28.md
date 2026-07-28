# `reference_h2` — Attempt 1 Chronology Correction: O-3 (Gate 0 Documentary Support, Narrowed)

**Status: correction-and-disclosure artifact only.** This document does not
edit, delete, or silently supersede
[`attempt_001_addendum_2026-07-28.md`](attempt_001_addendum_2026-07-28.md) or
[`attempt_001_specification.md`](attempt_001_specification.md) — both files
are retained, unedited, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §5's naming-and-versioning convention
("A correction is a new, dated file, cross-referenced from the file it
supersedes — the superseded file is retained, unedited"). This correction
narrows one supporting sentence in the addendum's corrected attestation. It
does not touch `transition_records.jsonl`, create any lifecycle transition,
or make any Gate 1 determination.

**Date:** 2026-07-28. **Scope:** correction of finding O-3 from
[`reviewer_reports/2026-07-28_level2_gate1_confirming_reproduction.md`](reviewer_reports/2026-07-28_level2_gate1_confirming_reproduction.md),
§6.

---

## 1. Purpose

`attempt_001_addendum_2026-07-28.md` §9 point 3, in the course of correcting
a different, more serious false statement (O-5's subject matter is
unrelated; the addendum's own subject was the false claim that the script
had not been executed), makes a supporting factual claim about what
`docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` named. The Level 2
confirming reviewer verified that claim against the source document and
found it partially overstated (O-3). This artifact records the correction
so the overstatement does not stand unaddressed.

## 2. What the original addendum claimed

`attempt_001_addendum_2026-07-28.md` §9 point 3 states, verbatim:

> "What repository evidence *does* support: the construction parameters
> (252-day formation, 21-day skip, log return) were named as the specific
> candidate to test in `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md`,
> nearly fourteen hours before the script existed..."

This asserts that all three of the following were named in the Gate 0
preparation review:
1. 252-day formation window
2. 21-trading-day skip
3. log return basis

## 3. What was actually verified

Per O-3 (confirming reviewer report §6): checked against
`docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` directly —

- **252 trading days is named.** ✅
- **The existence of a skip is named** (described there as a 1-month skip,
  not as an exact trading-day count). ✅
- **The exact integer 21** (as in "21 trading days" / "21-trading-day
  skip") **does not appear anywhere in that document** (case-insensitive
  string search: zero occurrences of "21 trading" or "21-trading"). ❌
- **The phrase or concept "log return"** (as distinct from simple return)
  **does not appear anywhere in that document** (case-insensitive search:
  zero occurrences of "log return"). ❌

So two of the three cited parameters — the formation window and the fact
that some skip exists — are correctly attributed to the Gate 0 preparation
review. The other two specifics — the skip's exact integer value and the
log-return basis — are not.

## 4. Correct provenance

The exact 21-trading-day skip and the log-return basis were first fixed in
`attempt_001_specification.md` §2.4, after
`docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` already existed.
Both are justified there on disclosed convention-reuse grounds, not as
things the Gate 0 review itself specified:

- the skip's integer value (21) follows the platform's standing
  21-trading-day-month convention;
- the log-return basis follows the log-return convention already used by
  `REFERENCE_V2_H1` and `reference_h3`.

This is a **defensible provenance** for both parameters — but it is a
**different** provenance from the one `attempt_001_addendum_2026-07-28.md`
§9 point 3 claims. The addendum's core correction (that the script had, in
fact, been executed before the specification was drafted) is unaffected and
remains sound. This correction concerns only the supporting sentence's
overreach about what the Gate 0 document itself named.

**This is a provenance correction, not a claim that the frozen construction
parameters are invalid.** The 252-day formation, 21-day skip, and
log-return basis remain the frozen Attempt #1 construction, unchanged, and
are not reopened, questioned, or subject to re-freezing by this document.

## 5. Governance impact

- **Narrows a documentary-support claim.** `attempt_001_addendum_2026-07-28.md`
  §9 point 3's supporting sentence is now understood to cover only the
  formation window and the existence of a skip, not the skip's exact
  integer or the return basis.
- **Does not invalidate Attempt #1.** No frozen construction element
  changed; §7's original chronology analysis (script executed before
  specification drafted, construction named in advance) is unaffected by
  this narrower attribution.
- **Does not change the attempt count.** Attempt #1 remains the only
  validly logged attempt; the three-attempt cap is unaffected.
- **Does not change the Gate 1 reproduction result.** The independent
  reproduction recorded in
  `reviewer_reports/2026-07-28_level2_gate1_confirming_reproduction.md` §4
  (483/483 dates bitwise identical for both components, tolerance 0)
  derives from the frozen specification, not from the Gate 0 preparation
  review's wording, and is untouched by this correction.
- **Does not create a gate outcome.** No PASS/FAIL/INCONCLUSIVE
  determination is made here or implied. `reference_h2` remains in
  PRE_VALIDATION; `transition_records.jsonl` is not modified.

## 6. Cross-reference handling

Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5, corrections are new, dated,
cross-referenced files, and nothing archived is edited or silently
superseded in place. Consistent with that convention:

- `attempt_001_addendum_2026-07-28.md` is **not edited**. Its §9 point 3
  remains on record as originally written; this document narrows, but does
  not alter, its text.
- The relationship between the overstated claim (§9 point 3 of the
  addendum) and this correction is **not** recorded by modifying either
  existing file. It is recorded here, and is indexed from
  [`decision_log.md`](decision_log.md) Entry 9 — the cycle's chronological
  narrative artifact spanning Phases 2 through 8, per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5's seven-item evidence-package
  structure. The chronological index is the correct location for recording
  *that* a correction exists and *which* prior claim it narrows; this
  document is the correct location for the correction's substance.

---

**No lifecycle transition, `DecisionRecord`, or edit to
`transition_records.jsonl` occurs here. `reference_h2` remains in
PRE_VALIDATION. No Gate 1 determination is made or implied.**
