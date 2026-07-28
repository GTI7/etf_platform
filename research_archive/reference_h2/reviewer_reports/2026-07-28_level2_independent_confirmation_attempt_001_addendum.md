# `reference_h2` — Level 2 Independent Confirmation of the Attempt 1 Addendum

**Level 2 — AI-assisted adversarial review**
(`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4). Procedurally independent: fresh
session, no conversational continuity with the session that drafted
`attempt_001_specification.md`, `attempt_001_addendum_2026-07-28.md`, or
`2026-07-28_level2_review_attempt_001_false_attestation.md`. This review did
not author, and was not involved in producing, any of those three
documents. Every factual claim below was independently re-derived from
`git` state, filesystem timestamps, and the contents of
`h2_gate1_independence_analysis_report.json`, and cross-checked against —
not copied from — the addendum's own chronology table. **Not
organizationally independent** — same model family/vendor, no incentive
separation, no accountable persistent reviewer role, no Level 3 reviewer
available on this platform, per Standard §4. This document must never be
cited as "independent" without that qualifier.

**Reviewer:** Claude Sonnet 5, 2026-07-28.
**Commit reviewed:** `a7d0938c66ab86e0bfb46b643698f67229b224a2` (confirmed
current `HEAD` at time of this review via `git rev-parse HEAD`).
**Scope:** this review only. It re-examines
[`attempt_001_addendum_2026-07-28.md`](../attempt_001_addendum_2026-07-28.md)
and
[`2026-07-28_level2_review_attempt_001_false_attestation.md`](2026-07-28_level2_review_attempt_001_false_attestation.md)
against repository evidence, and rules on one narrow governance question
(Section 4, below). It does not re-examine
`attempt_001_specification.md` Sections 1, 2, 4, or 6, or Section 3 points
1 and 4, which the addendum already left standing and which no evidence
found here contradicts.

---

## 1. Purpose

The prior reviewer report,
`2026-07-28_level2_review_attempt_001_false_attestation.md`, discloses in
its own Section 4 that the addendum it reviews and accepts was "authored
in this same review pass" — i.e., the same session that wrote the
correction also wrote the review confirming that correction, without a
second, separate reviewing pass. That is a genuine governance gap: it
means the addendum's acceptance rests on self-confirmation, not on a
distinct reviewing party, even though the document is labeled "Level 2."
This is consistent with — and does not reopen — the substance of that
review's own finding; the gap is procedural (who confirmed the
correction), not substantive (whether the correction is correct).

This document supplies that missing second pass: an independent
(procedurally, not organizationally) re-derivation of the chronology and
an independent confirmation of the addendum's conclusions, by a session
that did not write the addendum and had no part in writing the review that
first accepted it.

## 2. Independent chronology reconstruction

Reconstructed directly from repository state by this review, not taken
from the addendum's table:

| Evidence checked | Result |
|---|---|
| `git rev-parse HEAD` | `a7d0938c66ab86e0bfb46b643698f67229b224a2` |
| `git log --oneline -10` | confirms `a7d0938` = "Add reference_h2 Phase 3 pre-validation plan," the most recent commit; no commit postdates it |
| `git status --short` | four untracked (`??`) files: `experiments/validate_h2_gate1_independence.py`, `attempt_001_specification.md`, `attempt_001_addendum_2026-07-28.md`, `2026-07-28_level2_review_attempt_001_false_attestation.md` — none of the four has ever been committed |
| `git check-ignore -v h2_gate1_independence_analysis_report.json` | matched by `.gitignore:34`; confirmed gitignored generated output, not a tracked artifact |
| filesystem mtime, `experiments/validate_h2_gate1_independence.py` | 2026-07-28 13:58:38 |
| filesystem mtime, `h2_gate1_independence_analysis_report.json` | 2026-07-28 13:58:46 |
| `h2_gate1_independence_analysis_report.json` → `generated_at` | `2026-07-28T11:58:46Z` (UTC; consistent with the local mtime at UTC+2) |
| `h2_gate1_independence_analysis_report.json` → `repository_commit` | `a7d0938c66ab86e0bfb46b643698f67229b224a2` — matches confirmed current `HEAD` |
| `h2_gate1_independence_analysis_report.json` → `disclosure` block | `logged_construction_attempt: false`, `pre_log_attestation_written: false`, `gate_1_satisfied: false`; explicit note that the run "does not, by itself, satisfy Gate 1" and "is not counted against the plan's attempt cap" |
| `h2_gate1_independence_analysis_report.json` → `config` | `h2_formation_trading_days: 252`, `h2_skip_trading_days: 21`, `h2_return_basis: "close-to-close log return"`, `period_start/end: 2024-07-17`/`2026-07-17` — identical to the construction `attempt_001_specification.md` Section 2.4 and Section 2.10 subsequently freezes |
| filesystem mtime, `attempt_001_specification.md` | 2026-07-28 14:08:15 — **~9.5 minutes after** the report already existed, at the same commit |
| filesystem mtime, `attempt_001_addendum_2026-07-28.md` | 2026-07-28 14:25:40 |
| filesystem mtime, `2026-07-28_level2_review_attempt_001_false_attestation.md` | 2026-07-28 14:26:11 — **~31 seconds after** the addendum, confirming the two were produced in the same short pass, as the review's own Section 4 already discloses |

This independently reproduces every factual claim in the addendum's
Section 2 chronology table and in the prior review's Section 1 finding. No
discrepancy was found. This review therefore treats the underlying factual
finding — that `attempt_001_specification.md`'s status header and Section
3 points 2–3 falsely stated the script had not been run and no
correlation figure existed — as independently confirmed, not merely
inspected.

## 3. Independent confirmation of the addendum's conclusions

Checked against the frozen text of
[`prevalidation_plan.md`](../prevalidation_plan.md) Section 2 and
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §3 directly, not against the
addendum's own restatement of those sections:

- **Attempt #1 remains Attempt #1.** `prevalidation_plan.md` §2's "exact
  definition of an attempt" ties attempt-numbering to a change in one of
  the ten enumerated construction elements (formation window, skip
  length, return basis, dividend treatment, ranking methodology, tie
  handling, minimum panel size, or other construction logic). The false
  attestation is not on that list, and no element in
  `attempt_001_specification.md` Section 2.1–2.10 differs between the
  original filing and the addendum's corrected attestation. Confirmed:
  no new attempt number is triggered.
- **No abandonment.** Abandonment would require evidence that the frozen
  construction was itself a product of the false attestation's underlying
  conduct — i.e., that the correlation figures actually shaped a
  construction choice. `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md`
  independently predates `experiments/validate_h2_gate1_independence.py`
  by close to fourteen hours (file evidence, not re-derived from that
  document's internal date claim alone — this review relied on the
  script's own mtime relative to the referenced document's mtime) and
  already names the identical 252/21/log-return construction. No
  repository evidence supports outcome-driven selection. Confirmed: no
  abandonment.
- **No re-freeze.** Re-freezing under `docs/RESEARCH_GOVERNANCE_STANDARD.md`
  §3 is triggered only by a change to one of the eight frozen elements
  listed there. `reference_h2` has not yet reached Methodology Freeze
  (Phase 4) at all — it remains in Pre-validation (Phase 3) — so there is
  no freeze in effect to reopen, and the addendum's own construction
  (Section 2 of `attempt_001_specification.md`) is unchanged. Confirmed:
  no re-freeze.
- **No additional attempt consumed.** The three-attempt cap
  (`prevalidation_plan.md` §2) is unaffected: the originally filed,
  falsely-attested document did not validly satisfy the pre-log
  attestation requirement and so was never a validly logged attempt in
  the first place; the corrected attestation (addendum §9) is what makes
  Attempt #1 validly logged. Zero attempts have been consumed against the
  cap of three by this sequence of events. Confirmed.
- **PRE_VALIDATION unchanged.** `transition_records.jsonl` was read by
  this review and contains exactly one entry (`sequence_number: 1`,
  `from_phase: "Research Proposal"`, `to_phase: "Pre-validation"`,
  `recorded_at: 2026-07-28T11:09:00Z`, `commit_hash: 4030d86e...`). No
  second entry exists. Neither `attempt_001_specification.md`, nor the
  addendum, nor the prior review, nor this review appends to that file.
  Confirmed: `reference_h2` remains in PRE_VALIDATION.

## 4. Resolution of the self-confirmation defect

The narrow defect this review was opened to address — that
`2026-07-28_level2_review_attempt_001_false_attestation.md` confirmed an
addendum authored in the same pass as the review itself, leaving the
addendum's acceptance procedurally self-confirmed rather than confirmed by
a distinct reviewing party — is **resolved by this document**. This
review:

- did not author `attempt_001_addendum_2026-07-28.md`,
  `attempt_001_specification.md`, or the prior false-attestation review;
- independently reconstructed the chronology from repository evidence
  (Section 2, above) rather than accepting the addendum's or the prior
  review's chronology table at face value;
- independently confirmed the addendum's five governance conclusions
  (Section 3, above), tracing each to the specific clause of
  `prevalidation_plan.md` §2 or `docs/RESEARCH_GOVERNANCE_STANDARD.md` §3
  it rests on, rather than accepting the addendum's rulings as given.

This supplies the distinct reviewing pass that was missing. It does not
reopen the underlying factual finding (Section 1 of the prior review),
which this document independently reproduces and finds accurate, and it
does not disturb any of that review's other conclusions (Section 6's
outstanding-gaps disclosure, for instance, remains outstanding and is not
addressed here, as it is out of scope for this narrow confirmation).

## 5. What this review does not do

It does not evaluate, satisfy, or advance Gate 1, Gate 2, Gate 3, or Gate 4
of `prevalidation_plan.md`. **Gate 1 (signal independence) itself remains
OPEN and UNSATISFIED**: no confirming reviewer has yet performed
`prevalidation_plan.md` §6 point 4's independent reproduction of both Gate
1 components (the rank-correlation calculation and the ranking-extreme
overlap analysis) as an act of evaluating the construction against
`reference_v1`'s MOMENTUM score — this review confirms the *chronology and
attestation* were corrected honestly, which is a precondition for Gate 1
review, not a substitute for it. It does not authorize Methodology Freeze.
It does not create, imply, or authorize any lifecycle transition;
`reference_h2` remains in PRE_VALIDATION and `transition_records.jsonl` is
untouched by this review. It does not edit, replace, or supersede
`attempt_001_specification.md` or `attempt_001_addendum_2026-07-28.md` —
both remain exactly as written. It does not create
`research_archive/reference_h2/decision_log.md`, which the prior review's
Section 6 already flagged as an outstanding, separately-scoped gap.

## 6. Outstanding gaps (unchanged from the prior review)

- `research_archive/reference_h2/decision_log.md` still does not exist.
  Not remediated here; out of scope for this confirmation.
- No Level 3 (organizationally independent) review is available on this
  platform for any part of this cycle, per Standard §4's standing
  disclosure.
- The unverifiable question of whether the pre-existing correlation
  figures were consulted while Section 2 or Section 4 of
  `attempt_001_specification.md` were drafted remains an accepted,
  disclosed, unresolved residual risk (addendum §10), not resolved by this
  review in either direction.
