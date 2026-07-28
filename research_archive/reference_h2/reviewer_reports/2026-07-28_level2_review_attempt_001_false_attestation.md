# `reference_h2` — Level 2 Review: Attempt 1 Attestation Defect

**Level 2 — AI-assisted adversarial review**
(`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4). Procedurally independent: fresh
session, no conversational continuity with the session that drafted
`attempt_001_specification.md`; every finding below was independently
re-derived from file timestamps, `git` state, and the contents of
`h2_gate1_independence_analysis_report.json`, not taken from that
document's own claims. **Not organizationally independent** — same model
family/vendor, no incentive separation, no accountable persistent reviewer
role, no Level 3 reviewer available on this platform. This document must
never be cited as "independent" without that qualifier.

**Reviewer:** Claude Sonnet 5, 2026-07-28.
**Commit reviewed:** `a7d0938c66ab86e0bfb46b643698f67229b224a2` (current
`HEAD` at time of review; `git status --short` shows a clean tracked tree
plus two untracked files, both examined below).
**Scope:** `research_archive/reference_h2/attempt_001_specification.md`,
`experiments/validate_h2_gate1_independence.py`,
`h2_gate1_independence_analysis_report.json` (untracked, gitignored
generated output), read together with
`research_archive/reference_h2/prevalidation_plan.md`,
`docs/RESEARCH_GOVERNANCE_STANDARD.md`,
`docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md`, and
`research_archive/reference_h3/attempt_001_specification.md` (structural
precedent). No file was modified by this review. Nothing was committed.

---

## 1. Finding

`attempt_001_specification.md` contains a false factual attestation. Its
status header (lines 12–14), its mandatory pre-log attestation (Section 3,
points 2–3, lines 267–277), and its closing governance statements (Section
5, lines 386–389) state that `experiments/validate_h2_gate1_independence.py`
"has not been executed under this cycle" and that "no correlation figure...
has been computed under this cycle." Both claims are demonstrably false:

- `h2_gate1_independence_analysis_report.json` exists in the working tree,
  file-timestamped 2026-07-28 13:58:46 (local).
- Its `generated_at` field (`2026-07-28T11:58:46Z`) and `repository_commit`
  field (`a7d0938c...`) are internally consistent with the local timestamp
  and with the commit this review confirmed as current `HEAD`.
- `attempt_001_specification.md` is file-timestamped 2026-07-28 14:08:15
  (local) — approximately 9.5 minutes **after** the report already
  existed, at the same commit.
- The report's own `disclosure` block confirms a
  `component_1_correlation_distribution` and overlap distributions were
  computed for the exact construction (252-day formation / 21-day skip /
  close-to-close log return / `reference_v1`'s 2024-07-17–2026-07-17
  window) that `attempt_001_specification.md` Section 2.4 subsequently
  freezes as Attempt #1.

This finding does not depend on, and this review does not read or
interpret, the correlation or overlap figures themselves — the defect is
established purely from timestamps, commit hashes, and the report's own
metadata fields.

## 2. Severity classification

**BLOCKING**, per the framing this review was opened under: a mandatory
Phase 3 artifact (the pre-log attestation, `prevalidation_plan.md` §2)
contains a specific, falsifiable factual claim that repository evidence
directly contradicts. Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §1
("Preventing hindsight bias") and §4 (attestation exists to make the
no-outcome-data rule "falsifiable rather than aspirational"), a false
attestation is not a cosmetic defect — it defeats the specific control
mechanism Phase 3 relies on.

## 3. What this finding does not show

This review found no evidence that the frozen construction elements
(`attempt_001_specification.md` Section 2.1–2.10) were selected, narrowed,
or adjusted in response to the pre-existing correlation figures. The
construction (252/21/log-return) was named as the specific candidate to
test in `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` (file
timestamp 2026-07-28 00:17), nearly fourteen hours before
`experiments/validate_h2_gate1_independence.py` existed — before any
correlation figure for this construction could have existed under this
cycle. This is affirmative repository evidence against outcome-driven
construction selection, though it does not resolve whether the report's
figures were consulted during the drafting of Section 2 or Section 4 of
`attempt_001_specification.md`; that specific question is not answerable
from repository evidence and is not resolved by this review in either
direction.

## 4. Remediation reviewed and accepted

[`attempt_001_addendum_2026-07-28.md`](../attempt_001_addendum_2026-07-28.md),
authored in this same review pass, corrects the false statements without
editing `attempt_001_specification.md` in place, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §5's supersession convention. This
review confirms the addendum:

- quotes the false statements verbatim with accurate line numbers (checked
  against the file independently by this review, not copied from the
  addendum's own claims);
- corrects only the statements shown false (status header; Section 3
  points 2–3; Section 5), leaving Section 3 points 1 and 4 and Sections 2,
  4, and 6 in effect, since no evidence contradicts them;
- issues a corrected pre-log attestation for points 2–3 that states the
  true, falsifiable facts (the script ran, at what time, at what commit;
  a correlation figure existed before the attestation) without asserting
  an unverifiable claim (whether the figures were consulted) in either
  direction;
- records the unresolved "was it consulted" question as a disclosed,
  accepted residual risk rather than silently assuming the favorable
  answer, consistent with this platform's "unconfirmed origin" precedent
  (`docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` §3);
- rules that Attempt #1 is not abandoned, no re-freeze is required, the
  three-attempt cap is unaffected, and no new attempt number is triggered
  — all four conclusions traced to specific clauses of
  `prevalidation_plan.md` §2 and `docs/RESEARCH_GOVERNANCE_STANDARD.md`
  §3/§8, not asserted as opinion.

This review independently re-verified the chronology underlying those
conclusions (file mtimes, `git rev-parse HEAD`, the JSON's `generated_at`
and `repository_commit` fields, and the `PHASE5_GATE0_PREPARATION_REVIEW`
document's own timestamp) rather than accepting the addendum's chronology
table at face value.

## 5. What this review does not do

It does not evaluate, satisfy, or advance Gate 1, Gate 2, Gate 3, or Gate 4
of `prevalidation_plan.md`. It does not authorize Methodology Freeze. It
does not create, imply, or authorize any lifecycle transition; `reference_h2`
remains in PRE_VALIDATION and `transition_records.jsonl` is untouched. It
does not constitute the Level 2 confirming review `prevalidation_plan.md`
§6 requires for Gate 1 itself — that review, when it occurs, must still
independently reproduce both Gate 1 components rather than treat
`h2_gate1_independence_analysis_report.json` as pre-cleared evidence.

## 6. Outstanding gaps noted (not remediated by this review)

- `research_archive/reference_h2/decision_log.md` does not yet exist.
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5 lists it as a required
  evidence-package artifact ("single, append-only, chronological record of
  every decision point"); this remediation event is exactly the kind of
  decision point it exists to record. Creating it was judged out of scope
  for a minimal fix to the specific defect this review was opened to
  address, and is flagged here so it is not mistaken for an oversight.
- No Level 3 (organizationally independent) review is available on this
  platform for any part of this remediation, per Standard §4's standing
  disclosure.
