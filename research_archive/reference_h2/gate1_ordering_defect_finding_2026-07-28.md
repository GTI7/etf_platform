# `reference_h2` — Gate 1 Ordering-Defect Finding (Pre-validation Plan §3, Gate 1, "Ordering requirement")

**Status: governance finding and disclosure artifact only.** This document
is **not a gate outcome**. It makes no PASS, no FAIL, and no INCONCLUSIVE
determination, for Gate 1 or for any other gate. It does not interpret the
measured correlation or overlap figures in
[`gate1_independence_analysis_2026-07-28.json`](gate1_independence_analysis_2026-07-28.json),
does not advance `reference_h2`'s lifecycle phase, does not create or modify
[`transition_records.jsonl`](transition_records.jsonl), and does not create a
Methodology Freeze. `reference_h2` remains in **PRE_VALIDATION**.

Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5's naming-and-versioning
convention, this is a new, dated artifact. It edits no existing archived
file. The documents it discusses —
[`prevalidation_plan.md`](prevalidation_plan.md),
[`attempt_001_specification.md`](attempt_001_specification.md),
[`attempt_001_addendum_2026-07-28.md`](attempt_001_addendum_2026-07-28.md) —
are retained unedited as the historical record of what was believed true at
the time.

**Date:** 2026-07-28. **Author level:** Level 1 (self-directed governance
remediation pass; not a review of `reference_h2`'s research substance).
**Basis:** the Level 2 adjudication recorded in §7 below.

---

## 1. The requirement

[`prevalidation_plan.md`](prevalidation_plan.md) §3, Gate 1 ("Signal
independence"), closes with a subsection headed **"Ordering requirement"**,
committed at `a7d0938c66ab86e0bfb46b643698f67229b224a2` on 2026-07-28 at
13:47:49 (+0200). It states, verbatim:

> "Per `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2's 'Required ordering,'
> Gate 3's economic rationale must be frozen for the specific construction
> under test before this check is run against it. This check is a
> confirmatory sanity check on an already-decided construction, not a tool
> for searching across candidate constructions for whichever happens to
> correlate least with MOMENTUM."

The requirement therefore has two components, both of which must hold at the
moment the Gate 1 check is run:

1. **A specific construction must already be decided** — the check is
   confirmatory on a fixed construction, not exploratory across candidates.
2. **Gate 3's economic rationale must already be frozen for that specific
   construction** — the economic reason for the construction must predate the
   number, so that the number cannot shape the reason.

Its purpose is anti-hindsight, and the plan says so directly: running the
check the other way around "would be parameter mining wearing an
independence check's clothing" (the H3 source text the H2 plan adopts by
citation). This is the same protection
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §1 names first among the four failure
modes the standard exists to prevent.

Gate 3's content is fixed by [`prevalidation_plan.md`](prevalidation_plan.md)
§3, Gate 3 ("Economic rationale"): a written statement that the frozen
construction actually implements the mechanism claimed for it, plus three
written distinctness statements (against `reference_v1` MOMENTUM, against
`reference_v2_h1`, and against `reference_h3`).

## 2. Chronology, reconstructed from repository evidence

Every row below is established from committed git metadata, file
modification times, or a cited artifact's own recorded timestamp — not from
narrative recollection. Local times are `+0200`; the Gate 1 artifact records
its own timestamp in UTC and is shown both ways.

| # | Time (local, 2026-07-28) | Event | Evidence |
|---|---|---|---|
| 1 | 00:53:17 | `hypothesis.md` finalized — Phase 1 mechanism statement ("Economic Mechanism", "Novelty Boundary") | file mtime; commits `b7bedba`, `ee802aa` |
| 2 | 13:25:02 | `RESEARCH_PROPOSAL → PRE_VALIDATION` transition recorded, `gate_outcomes: []` | commit `839d000`; `transition_records.jsonl` sequence 1 |
| 3 | 13:45:23 / **13:47:49** | `prevalidation_plan.md` written / **committed** — the ordering requirement enters force | file mtime; commit `a7d0938` (single-file commit) |
| 4 | **13:58:46** (= `2026-07-28T11:58:46Z`) | **Gate 1 evidence run executed**; `h2_gate1_independence_analysis_report.json` produced (483 dates, both components) | `gate1_independence_analysis_2026-07-28.json` field `generated_at`; archived copy's mtime |
| 5 | **14:08:15** | `attempt_001_specification.md` written — the construction is fixed in writing (§2: 252-day formation, 21-day skip, log-return basis, 25-ETF universe, bucket size 5, panel minimum 10, 2024-07-17–2026-07-17 window) | file mtime |
| 6 | 14:52:13 | `attempt_001_specification.md` committed, together with the attestation addendum and its Level 2 confirmation | commit `41ce0fb` |
| 7 | 15:08:54 | `experiments/validate_h2_gate1_independence.py` first committed — in a form modified after the run at row 4 | commit `c771355` |
| 8 | 15:58:53 | Level 2 confirming reproduction report archived (483/483 dates bitwise identical, tolerance 0) | commit `04f83d1` |

**No Gate 3 artifact appears anywhere in this chronology.** Verified
directly: `research_archive/reference_h2/` contains no Gate 3 economic-
rationale document, and `reviewer_reports/` contains no Gate 3 review, at any
point in the cycle to date — not before row 4, and not since. The Gate 3
requirement is referenced in [`prevalidation_plan.md`](prevalidation_plan.md)
§3 and in [`attempt_001_specification.md`](attempt_001_specification.md) §6
as future work; it has never been produced.

`hypothesis.md` (row 1) does state a candidate economic mechanism, and it
does predate the run. It is **not** a Gate 3 discharge and cannot be read as
one: it is a Phase 1 artifact, written before the construction existed, so it
cannot state that the frozen construction implements the mechanism it
describes; and it contains none of the three distinctness statements Gate 3
requires.

### What the chronology establishes

- At row 4, when the Gate 1 check ran, **the construction it was run against
  was not yet fixed in writing** — that happened 9 minutes 29 seconds later,
  at row 5.
- At row 4, **no Gate 3 economic rationale existed** for that construction,
  or for any construction, in any form.
- Both conditions of §1 were therefore unsatisfied at the moment of the run.

### Contrast: the precedent the plan cites

`reference_h3`, whose ordering language this plan adopts by citation, ran the
same sequence in the required order:
`research_archive/reference_h3/decision_log.md` Entry 8 records Gate 3
economic rationale reviewed PASS at 01:48–02:00 on 2026-07-19; Entry 10
records Attempt 1's construction frozen at 10:51; Entry 11 records a Gate 1
readiness review at 12:03; the Gate 1 evidence artifact
(`gate1_independence_analysis_2026-07-19.json`) was produced at 14:38. Gate 3
preceded the freeze, which preceded the run, by roughly nine and twelve
hours respectively. `reference_h2` inverted that sequence.

## 3. The finding

**The Gate 1 ordering requirement stated in
[`prevalidation_plan.md`](prevalidation_plan.md) §3 was violated.**

The violation is not marginal or interpretive. Both limbs of the requirement
failed: the check was run against a construction not yet frozen, and it was
run with no Gate 3 economic rationale in existence. The requirement was in
force at the time — it had been committed 10 minutes 57 seconds earlier
(rows 3→4) — so this is not a case of a control adopted after the fact and
applied retrospectively.

## 4. Three distinct defects, not one

This finding concerns a defect that is **separate from**, and not cured by,
the two governance defects already recorded for this cycle. All three attach
to the same 13:58:46 run, and each survives the other's remediation.

**(a) The attestation defect — already remediated (Entry 6).**
[`attempt_001_specification.md`](attempt_001_specification.md) §3's mandatory
pre-log attestation falsely stated that the script had not been executed and
that no correlation figure existed. That was corrected by
[`attempt_001_addendum_2026-07-28.md`](attempt_001_addendum_2026-07-28.md)
and independently confirmed at Level 2
(`reviewer_reports/2026-07-28_level2_independent_confirmation_attempt_001_addendum.md`).
The defect there is a **false statement about the chronology**. Its remedy is
a truthful restatement, which has been made.

**(b) The ordering defect — this finding, previously unrecorded.** The defect
here is **the chronology itself**, independent of how it was described. Had
the original attestation been perfectly truthful — had it said plainly "the
check has already been run; no Gate 3 rationale exists; the construction is
being fixed now" — the ordering requirement would still have been violated in
exactly the same way and to exactly the same degree. Truthful disclosure of a
prohibited sequence does not convert it into a permitted one. This is why the
addendum's remediation, though sound on its own subject, does not reach this
defect: the addendum corrected what was *said*, and this finding concerns
what was *done*.

**(c) Provenance limitations — separately disclosed (O-2, O-5).**
[`provenance_record_gate1_2026-07-28.json`](provenance_record_gate1_2026-07-28.json)
discloses that the exact producing script version was never committed and no
longer exists (O-5), and that database identity was established post-hoc
rather than contemporaneously (O-2). These concern the **traceability of the
evidence to the code and data that produced it**. They are orthogonal to
ordering: closing them would not cure the ordering defect, and the ordering
defect does not worsen them.

## 5. Impact

**Arithmetic evidence: unaffected.** The measured figures in
[`gate1_independence_analysis_2026-07-28.json`](gate1_independence_analysis_2026-07-28.json)
were independently reproduced from the frozen written specification — not by
re-running the original script — with 483 of 483 dates bitwise identical at
absolute tolerance 0, for both Component 1 (cross-sectional Spearman rank
correlation) and Component 2 (top-5/bottom-5 overlap)
(`reviewer_reports/2026-07-28_level2_gate1_confirming_reproduction.md` §4;
`decision_log.md` Entry 8). Ordering is a governance property of *when* a
calculation was performed relative to other governance acts; it has no
bearing on whether the arithmetic is correct. Nothing in this finding
impugns those numbers, and nothing in the reproduction result mitigates this
finding.

**Anti-hindsight protection: weakened, and not restorable.** The specific
protection the ordering requirement provides is that the economic reason for
a construction cannot have been shaped by the independence figures, because
the reason was frozen first. That protection is gone for Attempt #1's Gate 1
evidence. Concretely, what can no longer be established from the record:

- that the construction fixed at 14:08:15 was not influenced, in any element,
  by figures that had existed for nine and a half minutes when it was
  written;
- that a Gate 3 economic rationale, whenever it is eventually written, is not
  being composed with knowledge of the Gate 1 result it must justify — a risk
  that now attaches permanently to any future Gate 3 document in this cycle,
  and which that document will have to disclose;
- that no candidate-construction search occurred, since the confirmatory-only
  posture the requirement enforces was not in place.

**What this finding does not assert.** It does not assert that hindsight
actually operated. No repository evidence shows any frozen construction
element was selected or adjusted using the pre-existing figures, and
`decision_log.md` Entry 6 records that the construction's principal
parameters were named by convention citation in
`docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` roughly fourteen
hours before the script existed (as narrowed by
[`attempt_001_chronology_correction_2026-07-28.md`](attempt_001_chronology_correction_2026-07-28.md),
which establishes that the 252-day formation window and the existence of a
skip are so attributable, while the exact 21-day integer and the log-return
basis are not). The point of the ordering requirement is that this question
should not have needed answering from circumstantial evidence at all. It is
recorded as **unresolved in either direction**, consistent with Entry 6's
existing disclosure of the same residual risk.

## 6. Not retroactively curable

The ordering requirement is a constraint on the *sequence of events*, and the
events have occurred. No document written after 13:58:46 can place a Gate 3
economic rationale before it. Specifically, none of the following would cure
this defect, and none is offered here as doing so:

- writing the Gate 3 economic rationale now — it would postdate the figures,
  which is the precise condition the requirement forbids;
- re-running the Gate 1 check against the now-frozen construction — the
  result would be produced by an operator who has already seen the first
  result, and Gate 3 would still not predate the original run;
- the exact reproduction recorded in Entry 8 — it confirms arithmetic, not
  sequence, and was itself performed after all of the events above;
- re-numbering or re-freezing Attempt #1 — the plan's attempt machinery
  governs construction revisions, not the ordering of an already-executed
  check.

Under `docs/RESEARCH_GOVERNANCE_STANDARD.md` §8, a control that was not
satisfied and cannot now be satisfied is not thereby waived: it must be
**disclosed and governed through an exception record**, carrying a documented
reason, an impact assessment, an approval record at Level 2 minimum, and a
time-box or remediation commitment. That exception record is recorded in
[`decision_log.md`](decision_log.md) Entry 11, which cites this finding as its
factual basis. This document supplies the finding; it does not itself
constitute the exception, and it grants no permission to use the evidence.

## 7. Adjudication basis

The determination that the ordering requirement was violated, that the
violation is distinct from the attestation defect, and that Attempt #1's
Gate 1 evidence is numerically reproducible, not invalidated, and usable only
under a documented exception, was made by a **Level 2 (AI-assisted
adversarial) adjudication** directing this remediation pass. Its factual
premises — the four timestamps in §2 rows 3–6, the absence of any Gate 3
artifact, and the reproduction result — were each re-verified against
repository evidence by this pass before being recorded above; no premise was
accepted on assertion.

Recorded limitations of that basis, stated rather than assumed away:

- **The adjudication is not archived as a `reviewer_reports/` artifact.** It
  reached this cycle as a governance directive to this remediation pass, not
  as a dated review document under
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5's one-file-per-review-event
  convention. Its Level 2 tier is therefore self-reported here and is not
  independently verifiable from the archive alone. This is a real gap in the
  exception's approval record under §8 item 3, and it is disclosed as such.
- **This document is Level 1.** Recording a finding is not reviewing it. This
  finding has not itself received Level 2 or above review.
- **No Level 3 review exists or is available on this platform**, for this
  finding or for any prior entry in this cycle.
- **The attempt-cap ruling recorded in `decision_log.md` Entry 6 remains
  provisional.** It is valid on the facts as recorded, but was not
  independently confirmed. The remaining attempt budget (two further attempts
  under the three-attempt cap) is to be treated as **provisional until
  confirmed**, and nothing in this finding confirms it.

---

**No Gate 1 outcome is created by this document. No lifecycle transition is
created. No Methodology Freeze is created. `reference_h2` remains in
PRE_VALIDATION, with `transition_records.jsonl` holding exactly one record
and `gate_outcomes: []`.**
