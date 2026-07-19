# Acceptance Criteria — [project name]

**Status: frozen at Phase 4 (Methodology Freeze).** Every element below
must be filled in with an explicit value or an explicit `UNRESOLVED`
before this document is committed as the freeze — an unresolved item is
disclosed, never left blank or implied.
`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 3 requires all eight
elements to be fixed in writing, immutably, before Phase 5
(Implementation) may begin. Once committed, no element on this page may
change for any reason without invalidating the cycle to date (Standard
Section 3, "How changes are handled after freeze").

## 1. Universe

[The exact set of instruments under study, named explicitly — not "the
current universe" by reference.]

## 2. Dataset version

[The exact data snapshot: source, date range, and content hash.]

## 3. Evaluation period

[The exact date range, or the exact same-date comparison basis for an
outcome-free phase.]

## 4. Benchmark

[The exact comparison construct, named and versioned if it is itself a
derived score.]

## 5. Metrics

[The exact statistics to be computed, and how they will be aggregated.]

## 6. Scoring rules

[The exact formula, including every input, weight, lookback, and
missing-data handling rule.]

## 7. Parameters

[Every numeric constant the scoring rules depend on, each with a stated
justification that does not reference any outcome figure.]

## 8. Acceptance criteria

[The exact PASS/FAIL/INCONCLUSIVE decision rule, fixed before
Validation is run, including how near-threshold or statistically
ambiguous results will be resolved.]

---

**Freeze record.** This document is not effective as a freeze until it
is committed to version control and its commit hash is recorded in
`decision_log.md` — a document's own prose claim to be "frozen" is not
freeze evidence (Standard Section 3, "How freeze is recorded").

- **Freeze commit hash:** [fill in after commit]
- **Confirmed complete against all eight elements above by:** [reviewer
  identity and level, Standard Section 4]
