# H3 Acceptance Criteria — Freeze Record

**Role.** Institutional Quant Research Freeze Custodian. This record
does not evaluate, tune, or modify H3's methodology or acceptance
criteria. It exists solely to establish tamper-evident provenance for
[`docs/H3_ACCEPTANCE_CRITERIA.md`](../../docs/H3_ACCEPTANCE_CRITERIA.md)
before Phase 6 (Validation) reads any H3 outcome figure, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §3 ("A commit hash is freeze
evidence; a document's own claim to be 'frozen' is not.").

---

## 1. Pre-freeze verification

Reviewed against `docs/H3_ACCEPTANCE_CRITERIA.md` as committed:

- **No outcome data used.** The document's own opening statement (§0,
  lines 3–12) disclaims reading, computing, or referencing any forward
  return, Information Coefficient, p-value, Sharpe ratio, drawdown, or
  other outcome/performance figure for H3, and cites
  `docs/H3_ECONOMIC_EVIDENCE_VALIDATION_REPORT.md` §1 as confirming none
  exists anywhere in the platform's archive. That report was read in
  full for this freeze: its Executive Summary and §3 evidence table
  independently confirm no forward return, rank persistence, portfolio
  outcome, IC/p-value, Sharpe ratio, or drawdown has ever been computed
  or referenced for H3. The two documents are consistent; no
  contradiction was found.
- **No performance results influenced criteria.** Every design choice in
  the acceptance criteria document (holding horizons, benchmark
  comparisons, statistical machinery, decision table) is justified on
  economic-mechanism, procedural, or platform-consistency grounds
  citing pre-existing frozen sources (`attempt_001_specification.md`,
  Gate 1/Gate 4 reports, `REFERENCE_H3_PREVALIDATION_PLAN.md`,
  `REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md`) — never on an
  expectation of what result would make H3 look favorable. No such
  justification was found to depend on an outcome figure.
- **Unresolved items explicitly marked.** §7 of the acceptance criteria
  document consolidates three items left open rather than filled with
  an invented number (reproduced in Section 3 below). No other
  criterion in the document is left open.

This freeze record performs no independent recomputation of these
claims beyond reading the cited sources; it is a Level 2 (procedurally
independent, not organizationally independent) check, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4.

---

## 2. Provenance

| Field | Value |
|---|---|
| Frozen document | `docs/H3_ACCEPTANCE_CRITERIA.md` |
| Document hash (SHA-256) | `a5c1821439d4a60039f1c5630d2be4a1692f7b13c71689c8a8ce3f000efd3925` |
| Repository state immediately prior to this freeze | `798f05274459bed203171e8b3094faf79869b852` ("Archive H3 Gate 1 and Gate 4 determinations") |
| Branch | `master` |
| Repository | `D:\Claude\etf_platform` |
| Freeze date | 2026-07-19 |

**Freeze commit hash — known limitation.** This record is committed in
the same commit that first brings `docs/H3_ACCEPTANCE_CRITERIA.md`
under version control (`Freeze H3 acceptance criteria before
validation`). A commit cannot cite its own hash at authoring time, so
that hash is not fabricated here. It is retrievable immediately after
this commit lands via:

```
git log -1 --format=%H -- docs/H3_ACCEPTANCE_CRITERIA.md
```

and should be copied into the **Freeze commit of this document in
effect** field of `docs/H3_ACCEPTANCE_CRITERIA.md` §8's decision-record
template when that template is completed at Phase 6 close-out — not
before, and not by editing this record in place (Section 5 below).

---

## 3. Unresolved items carried forward (not resolved by this record)

Reproduced from `docs/H3_ACCEPTANCE_CRITERIA.md` §7, unchanged:

| # | Item | Why unresolved |
|---|---|---|
| 1 | Net-of-implementation-cost minimum excess return | No transaction-cost, turnover, borrowing-cost, or capacity model exists anywhere on this platform; any basis-point hurdle set now would be arbitrary. |
| 2 | Maximum-drawdown acceptance threshold | Only ≈8 independent 60-day windows of single-regime history exist; a numeric ceiling would be calibrated against a distribution never observed at this horizon. |
| 3 | Volatility ceiling on the H3-B spread | Same reasoning as #2. |

This freeze record does not resolve, estimate, or default any of the
above. They remain open pending the separately-scoped work each item's
"What would resolve it" column in §7 describes.

---

## 4. Immutability statement

**The acceptance criteria frozen by this record cannot change after
Phase 6 (Validation) begins.** Per `docs/H3_ACCEPTANCE_CRITERIA.md` §6
and `docs/RESEARCH_GOVERNANCE_STANDARD.md` §3: any change to any element
of `docs/H3_ACCEPTANCE_CRITERIA.md` — both holding horizons, the
evaluation window, the primary/secondary statistics, the benchmark
comparisons, the bucket and minimum-panel sizes, the statistical
machinery, or the decision table and terminal conditions — made after
this freeze, for any reason, including a reason discovered while
reviewing a Phase 6 result, is not a revision. It is a new methodology
requiring a new freeze commit and, unless still within the
pre-validation attempt cap, a new cycle from Phase 1. Any such change
must be logged in `research_archive/reference_h3/decision_log.md`,
stating which element changed, why, and which prior freeze (this one)
it supersedes. Silence about such a change is itself a governance
violation, independent of whether the change was substantively
justified.

---

## 5. What this record does not do

This record does not evaluate, approve, or modify H3's acceptance
criteria, methodology, or any threshold. It does not authorize Phase 5
(Implementation) or Phase 6 (Validation) to begin — per
`docs/H3_ACCEPTANCE_CRITERIA.md` §6, a separate Level 2 confirmation
that the freeze document is complete against the eight-element
checklist is required first. It resolves none of Section 3's
unresolved items. It is never edited in place after being committed; a
correction is added as a new, dated freeze record cross-referencing
this one, following `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5's
supersession convention.
