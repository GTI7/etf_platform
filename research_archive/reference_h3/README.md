# reference_h3/

Incremental, frozen evidence for the REFERENCE H3 pre-validation
phase, preserved as it is produced per
`docs/REFERENCE_H3_PREVALIDATION_PLAN.md`'s archive discipline
(Section 6) — this cycle is still in progress, so this directory will
gain further contents (independence analysis, construction attempt
log, gate decisions, final determination) as later phases execute.

## Contents

- **`data_inventory_2026-07-19.json`** — the complete Phase 1 /
  Section 3 historical data sufficiency evidence, pre-extension:
  provider-level historical availability per ETF (live, read-only
  query), the then-current backfilled database range, the
  survivorship-constraint ranking of tickers, the effective-sample-size
  estimation under candidate extension lengths, and the descriptive
  regime-coverage inventory (SPY, annual realized volatility and
  drawdown).
- **`data_inventory_2026-07-19_post_extension.json`** — the executed
  data extension (Option B, approved) and its post-extension
  verification: exact commands run, before/after coverage, and a
  per-ETF missing-data check across the full extended range. Its
  `post_extension_verification.result` string was later found to be
  technically accurate but incomplete (missing-only, no surplus check)
  — see `docs/REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md` and the
  remediation artifacts below. Left unedited as the historical record.
- **`gate2_independent_review_2026-07-19.md`** — the prior (non-independent)
  Gate 2 review record. Left unedited; it already discloses its own
  independence gap and remains an accurate record of that review's
  findings at the time.
- **`removed_backfill_gap_fill_rows_2026-07-19.json`** — the permanent,
  unedited pre-delete export of the 50 invalid `PriceBar` rows (25 ETFs
  x 2 non-trading dates, `source='backfill-gap-fill'`) identified in
  `docs/REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md`, removed per
  `docs/REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md`'s Option F. Includes
  the remediation execution record (predicate used, dry-run count,
  script path/hash, governing docs).
- **`post_remediation_validation_2026-07-19.json`** — the full,
  machine-generated output of the six-point post-remediation validation
  (row count reconciliation, two-directional per-ETF coverage,
  source-tag audit, universe/date-range integrity, export/backup
  integrity, recurrence check), produced by
  `maintenance/remediate_h3_invalid_pricebar_rows.py`.
- **`data_inventory_2026-07-19_post_remediation.json`** — the
  human-readable successor to the post-extension inventory: root cause
  recap, remediation performed, before/after coverage, and the
  two-directional re-verification result, referencing the validation
  file above.
- **`gate2_independent_review_2026-07-19_post_remediation.md`** — the
  Level 2 (AI-assisted adversarial) Gate 2 review required by the
  remediation plan's Section 8: produced by a reviewer with no memory of,
  and no participation in, the remediation (a separately-scoped session
  that did not author or execute
  `maintenance/remediate_h3_invalid_pricebar_rows.py` or its commit
  `af239c2`). Procedurally independent, not organizationally independent
  — see the file's Section 0 for the full limitations statement, per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4. Independently re-queried the
  live database from scratch (row counts, per-ETF two-directional
  coverage, universe integrity, source-tag audit, trigger/schema
  inspection, governance compliance) and reproduced every figure in the
  post-remediation evidence above exactly. Concludes Gate 2 **PASS**, with
  three SHOULD-FIX and two OPTIONAL recommendations (none blocking) — see
  the file for detail, including the one check it explicitly did not
  perform (runtime trigger testing, to avoid any write attempt against the
  live database).
- **`gate3_independent_review_2026-07-19.md`** — the Level 2 (AI-assisted
  adversarial) Gate 3 review required by the pre-validation plan's Section
  4: produced by a reviewer with no memory of, and no participation in,
  drafting `docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`. Procedurally
  independent, not organizationally independent — see the file's Section 0.
  Checked the rationale
  document against the pre-validation plan on five points (economic
  mechanism validity, literature reasoning, falsification criteria, data
  mining risk, prior-result leakage), independently corroborated the
  ordering claim via `git log` (no H3 construction/scoring commit exists)
  and the directory listing (no construction attempt log exists yet).
  Concludes Gate 3 **PASS**, with no blocking or should-fix findings — see
  the file for detail.

No H3 signal, score, benchmark, peer group, lookback window, IC,
p-value, or forward return appears anywhere in any of these files —
all are data availability, remediation execution, and re-verification
only.

## Status

**Gate 2 (historical data adequacy) is satisfied — PASS**, as of
`gate2_independent_review_2026-07-19_post_remediation.md`. The
inventory, the A/B/C decision, the data extension, its post-extension
re-verification, the discovery of a +2-per-ETF surplus defect, that
defect's remediation (export-then-delete, re-verified two-directionally
clean: 0 missing, 0 surplus, of 2474 expected trading days per ETF
across all 25 ETFs), and now a Level 2 (AI-assisted adversarial, not
organizationally independent) reviewer's from-scratch reproduction of
every post-remediation figure are all complete.

**Gate 3 (economic rationale) is satisfied — PASS**, as of
`gate3_independent_review_2026-07-19.md`. The rationale
(`docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`) — a literature-grounded
mechanism for H3, slow mandate-driven institutional reallocation between
market segments and flow-chasing capital into recently favored
sector/theme ETFs, documented as economically distinct from REFERENCE v1
MOMENTUM's own-history, underreaction-based claim, and written before any
H3 construction was frozen or any independence check run — has now been
independently confirmed per Section 4 of the Prevalidation Plan: a
reviewer with no memory of, and no participation in, drafting the
rationale checked economic mechanism validity, literature reasoning,
falsification criteria, data mining risk, and prior-result leakage, and
independently corroborated (via `git log` and the directory listing) that
no H3 construction or attempt log preceded it.

**Construction Attempt 1 is frozen** —
[`attempt_001_specification.md`](attempt_001_specification.md) — fixing
the universe, peer-segment grouping, score formula/lookback, ranking
convention, and missing-data handling. No Gate 1 correlation, overlap, or
other outcome figure has been computed for it.

**Gate 1 governance readiness is confirmed — PASS**, as of
[`gate1_governance_readiness_review_2026-07-19.md`](gate1_governance_readiness_review_2026-07-19.md),
a Level 2 (AI-assisted adversarial, not organizationally independent)
review confirming: all Gate-1-relevant construction degrees
of freedom are frozen; the construction's recent algebraic clarification
(Section 4 of the attempt specification) documents an implication of the
frozen construction only and does not modify it; no new benchmark,
parameter, grouping, ranking method, lookback, normalization, weighting,
or implementation choice has been introduced; no outcome data has been
used anywhere in the process; and Attempt 1 remains Attempt 1 under the
Prevalidation Plan's attempt cap. That review also logged one non-blocking
SHOULD FIX (committing the currently-untracked archive files to version
control for provenance) that does not block Gate 1 from proceeding.

**Gate 1 (candidate signal independence) itself has not yet been run** —
the rank-correlation and score-overlap methodology of Prevalidation Plan
Section 2 has not yet been executed against the frozen construction. Gate
4 (no unresolved degrees of freedom for a full specification) likewise
remains open. Gate 1 quantitative testing may now begin per the
governance readiness review above.
