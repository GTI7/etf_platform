# `reference_h2` — Attempt 1 Addendum: Attestation Correction

**Status: correction-and-disclosure artifact only. This document does not
edit, delete, or silently supersede
[`attempt_001_specification.md`](attempt_001_specification.md) — that file
is retained, unedited, as the historical record of what was believed (and
incorrectly stated) true at the time it was written, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §5's naming-and-versioning
convention ("A correction is a new, dated file, cross-referenced from the
file it supersedes — the superseded file is retained, unedited"). This
addendum does not run, interpret, or report any Gate 1 result. It performs
no experiment and does not modify
`experiments/validate_h2_gate1_independence.py`. It does not touch
`research_archive/reference_h2/transition_records.jsonl`, create any
lifecycle transition, or open Methodology Freeze.**

**Date:** 2026-07-28. **Author:** Claude Sonnet 5, fresh session — Level 2
per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4 (procedurally independent of
the session that drafted `attempt_001_specification.md`; every claim below
was independently re-derived from file timestamps, git state, and JSON
content rather than taken from that document's own text). **Not
organizationally independent** — same model family/vendor, no incentive
separation, no Level 3 reviewer available on this platform, per Standard §4.

---

## 1. Purpose

`attempt_001_specification.md`, in its status header (lines 12–14) and in
its mandatory pre-log attestation (Section 3, points 2 and 3, lines
267–277), states that `experiments/validate_h2_gate1_independence.py` has
not been executed under this cycle and that no correlation figure for the
frozen construction has been computed under this cycle. Both statements are
false. This addendum records the correct chronology, explains the
governance significance of the false statements, rules on the consequences
for Attempt #1, and issues a corrected pre-log attestation.

## 2. Chronology (repository evidence only)

| Time (local, UTC+2) | Event | Evidence |
|---|---|---|
| 2026-07-28 00:17 | `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` committed/written, naming "the cross-sectional correlation between `reference_v1`'s `SMA(20)` rank and a trailing-12-1-month-return rank... across the same 25-ETF universe and a shared date range" as the specific Gate 1 evidence check to run — **before** the script existed | file mtime; §1 item 2 of that document |
| 2026-07-28 13:58:38 | `experiments/validate_h2_gate1_independence.py` created on disk | `ls -la` mtime |
| 2026-07-28 13:58:46 | Script executed; `h2_gate1_independence_analysis_report.json` written, `generated_at: 2026-07-28T11:58:46Z`, `repository_commit: a7d0938c...` | JSON content; file mtime |
| — | `a7d0938c` confirmed as **current** repository HEAD (unchanged since) | `git rev-parse HEAD` |
| 2026-07-28 14:08:15 | `research_archive/reference_h2/attempt_001_specification.md` created on disk — **~9.5 minutes after** the report existed, at the same HEAD | `ls -la` mtime |

Both `experiments/validate_h2_gate1_independence.py` and
`attempt_001_specification.md` are untracked (`git status --short`: `??`
for both) — neither has ever been committed. This addendum does not treat
that as mitigating: the Standard's disclosure discipline applies to the
working record, not only to committed history.

The construction the script evaluates (252-trading-day formation, 21-
trading-day skip, close-to-close log return, `reference_v1`'s own
2024-07-17–2026-07-17 window) is the **identical** construction
`attempt_001_specification.md` Section 2.4 subsequently freezes as Attempt
#1. This is not a coincidence requiring investigation — both documents cite
the same source, `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md`
§1 item 2, which named this exact construction hours before the script was
written.

## 3. The false statements (verbatim, with line numbers)

**Status header, lines 12–14:**
> "This document does not execute
> `experiments/validate_h2_gate1_independence.py`, does not interpret any
> prior run of it (none has occurred)..."

**Section 3, attestation point 2, lines 267–270:**
> "No output of `experiments/validate_h2_gate1_independence.py` was read,
> generated, or consulted in the drafting of this document; that script has
> not been executed under this cycle."

**Section 3, attestation point 3, lines 275–277:**
> "No correlation figure of any kind — for this construction or any
> alternative — has been computed under this cycle at the time of this
> attestation."

**Section 5, lines 386–389:**
> "No figure, statistic, distribution, or output from
> `experiments/validate_h2_gate1_independence.py` or any other
> evidence-generation code... That script has not been executed as part of
> producing this document."

## 4. Why these statements are false

`h2_gate1_independence_analysis_report.json` exists on disk, was generated
at the current repository HEAD (`a7d0938c`), and its own `disclosure` block
(`logged_construction_attempt: false`, `pre_log_attestation_written: false`,
`gate_1_satisfied: false`) confirms the script ran and produced a
`component_1_correlation_distribution` and two overlap distributions for
the exact frozen Attempt #1 construction, roughly 9.5 minutes before
`attempt_001_specification.md` was written, in the same working tree, at
the same commit. "That script has not been executed under this cycle" and
"no correlation figure... has been computed under this cycle" are therefore
factually incorrect, independent of any question about whether the
resulting figures were actually consulted while drafting Section 2 or
Section 4.

This addendum does not read, quote, or interpret the correlation or overlap
figures themselves anywhere above or below — doing so is out of scope for
this correction and is not necessary to establish that the quoted claims
are false.

## 5. Governing requirements

- `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2, Phase 3: a "pre-log
  attestation for every attempt" is a *required artifact* of Pre-validation,
  not an optional courtesy. `prevalidation_plan.md` §2 states the same
  attestation "exists specifically to make this rule falsifiable rather
  than aspirational."
- Standard §1, "Preventing hindsight bias": "A hypothesis, a construction,
  or an acceptance threshold chosen — or quietly adjusted — with knowledge
  of how it or something similar performed is not evidence of anything
  except that adjustment." The attestation exists to make a violation of
  this principle detectable; an attestation that is itself false defeats
  that purpose regardless of whether an actual violation occurred.
- Standard §5, evidence-package naming convention: corrections are new,
  dated, cross-referenced files; nothing archived is silently overwritten.
  This addendum follows that convention.
- Standard §4, Level 2 limits: "the claim of 'no conversational memory' is
  self-reported and not verifiable by a third party from outside the
  session." The same limitation applies here in reverse — this addendum
  cannot verify, any more than it can falsify, whether the drafting session
  actually read the report's figures. Only the objectively checkable claims
  (was the script executed; does a correlation figure exist) are ruled on
  below as facts; the unverifiable claim (was it *consulted*) is treated as
  an open, disclosed residual risk, not resolved either way.

## 6. Repository precedent

- `docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` and
  `docs/REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md` §7 establish this
  platform's standing discipline: a discovered defect is corrected by a
  dated addendum that discloses the defect and its evidence in full, never
  by editing the affected document in place.
- `docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md` §0 states the
  governing rule for when a defect invalidates a result: "the trigger for
  invalidating a cycle is a change to a frozen element; no frozen element
  changed" — applied there to hold a PASS decision valid despite disclosed
  control gaps. The analogous question here is whether the false
  attestation changed any frozen construction element (Section 2 of
  `attempt_001_specification.md`). It did not — see §7 below.
- `docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` §3's "unconfirmed origin"
  convention (also restated at Standard §8, "Incomplete provenance" worked
  example): where a fact cannot be conclusively established, the correct
  response is to proceed with an explicit, disclosed "unconfirmed" status,
  not to either assume the best case silently or to treat the
  unconfirmed status as equivalent to a proven violation.

## 7. Governance analysis

**Does execution before attestation invalidate Attempt #1?** The *original*
logging of Attempt #1 — the specific document-plus-attestation submitted at
14:08:15 — is invalid, because a mandatory artifact (a truthful pre-log
attestation) was not actually produced; a document containing the false
claims quoted in §3 does not satisfy `prevalidation_plan.md` §2's
attestation requirement merely because it is labeled as satisfying it. This
is a **procedural invalidation of the attestation**, not a substantive
invalidation of the construction: nothing in the repository evidence shows
the frozen construction elements (Section 2.1–2.10 of
`attempt_001_specification.md`) were selected, adjusted, or influenced by
the pre-existing correlation figures. The construction was already
specifically named, by ticker-level convention citation, in
`docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` (00:17, nearly
fourteen hours before the script ran) — it was not searched for or narrowed
down after the report existed.

**Does it merely require disclosure?** No — disclosure alone is necessary
but not sufficient. A false, falsifiable factual claim in a mandatory
attestation cannot be cured by *adding* a correction elsewhere while the
false claim continues to stand, uncorrected, as part of the "logged"
attempt. The false claims must be superseded by true ones (§9 below), in
addition to being disclosed.

**Must Attempt #1 be abandoned?** No. Abandonment would be the correct
response only if the construction itself were shown to be a product of the
false attestation's underlying failure (i.e., if outcome-adjacent evidence
had actually driven a construction choice). No repository evidence supports
that; the affirmative evidence (§2's chronology) points the other way. Per
Standard §8's stricter-reading-by-default principle, this addendum does not
resolve the unverifiable "was it consulted" question in H2's favor by
assumption — but that unresolved question is a disclosed residual risk
(§9), not grounds for abandonment absent evidence.

**Does the construction need to be re-frozen?** No. Re-freezing is required
only when a frozen *construction element* (Section 2 of the prevalidation
plan's attempt-definition list: formation window, skip length, return
basis, dividend treatment, ranking methodology, tie handling, minimum panel
size, or other construction logic) changes. None has changed. The
correction here is confined to the attestation text.

**Does the three-attempt cap change?** No. The cap remains 3. The invalid
original logging is not counted as a consumed attempt, because it was never
validly logged in the first place (§ above); the corrected re-submission
(§9) becomes the first validly logged attempt. Two further attempts remain
available under the cap if a future Gate 1 evaluation does not clear.

**Is a new attempt number required?** No. `prevalidation_plan.md` §2's
"Exact definition of an attempt" ties attempt-numbering to changes in the
enumerated construction elements. Correcting a false procedural claim in
the attestation is not on that list and does not trigger a new attempt
number. The corrected artifact below remains Attempt #1.

## 8. Remediation chosen: Option A (addendum), not full replacement

`attempt_001_specification.md` Sections 2 (frozen construction), 4
(alternatives considered), and 6 (traceability) are not contradicted by any
repository evidence and are not restated here. Only the status header and
Section 3, points 2–3, are false. A full replacement document (Option B)
would duplicate ~350 lines of unaffected content for no auditability
benefit; a dated, cross-referenced addendum that supersedes only the false
passages, per Standard §5's own convention, is the smaller and more
transparent change.

## 9. Corrected pre-log attestation for Attempt #1

This supersedes `attempt_001_specification.md` Section 3 points 2 and 3,
and the status-header claims at lines 12–14 and 386–389, **only**. Points 1
and 4 of that document's Section 3 are not contradicted by any evidence
found here and remain in effect, unmodified, incorporated by reference.

1. *(unchanged — see `attempt_001_specification.md` Section 3, point 1)*
2. **No forward/outcome data used for selection — corrected.**
   `experiments/validate_h2_gate1_independence.py` **was executed** under
   this cycle, at 2026-07-28 13:58:46 (local), at repository HEAD
   `a7d0938c`, approximately 9.5 minutes before
   `attempt_001_specification.md` was drafted; its output,
   `h2_gate1_independence_analysis_report.json`, exists in the working
   tree. No forward return, risk-adjusted return, Information Coefficient,
   p-value, or other outcome variable appears anywhere in that script or
   its output — both are limited to same-date, score-to-score comparisons,
   per the script's own disclosure block. This point of the original
   attestation is corrected to state accurately that the script ran; it is
   **not** corrected to claim the resulting correlation/overlap figures
   were, or were not, read or consulted while Section 2 and Section 4 of
   `attempt_001_specification.md` were drafted — that specific question is
   not resolvable from repository evidence and is recorded as an open,
   disclosed residual risk in §10, below, not asserted either way.
3. **No selection based on correlation outcome — corrected.** A
   correlation figure for this exact construction **had** been computed
   under this cycle, at the time `attempt_001_specification.md` was
   written (§2, above). The claim that none had been computed is false and
   is withdrawn. What repository evidence *does* support: the construction
   parameters (252-day formation, 21-day skip, log return) were named as
   the specific candidate to test in
   `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md`, nearly fourteen
   hours before the script existed — i.e., before any correlation figure
   for this or any alternative construction could have existed under this
   cycle. This is affirmative evidence against outcome-driven selection of
   the construction's parameters, though it does not, by itself,
   conclusively rule out consultation during drafting (§10).
4. *(unchanged — see `attempt_001_specification.md` Section 4, "Alternatives
   considered")*

## 10. Residual risk (disclosed, not resolved)

Whether the correlation/overlap figures in
`h2_gate1_independence_analysis_report.json` were read or otherwise
influenced the drafting of `attempt_001_specification.md` Section 2 or
Section 4 cannot be established from repository evidence and is not
resolved by this addendum in either direction. This is recorded, following
the H3 "unconfirmed origin" convention (`docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md`
§3; Standard §8), as an accepted, disclosed, unconfirmed-status residual
risk attached permanently to Attempt #1, not as a resolved finding. Any
future Gate 1 confirming reviewer (`prevalidation_plan.md` §6, point 4)
must independently reproduce both Gate 1 components rather than treating
`h2_gate1_independence_analysis_report.json` as pre-cleared evidence, and
should weigh this disclosed gap when assessing Attempt #1's overall
evidentiary strength.

## 11. Effect on `attempt_001_specification.md`

`attempt_001_specification.md` is **not edited**. Its status header (lines
12–14), Section 3 points 2–3 (lines 264–277), and Section 5 (lines
386–389) are **superseded by this addendum** as of 2026-07-28 and must not
be relied upon as accurate without reading this document alongside it. Its
Sections 1, 2, 4, and 6, and Section 3 points 1 and 4, remain in effect
unmodified. `reference_h2` remains in PRE_VALIDATION; no lifecycle
transition occurs as a result of this addendum.
