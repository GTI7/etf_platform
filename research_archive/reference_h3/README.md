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

No H3 signal, score, benchmark, peer group, lookback window, IC,
p-value, or forward return appears anywhere in any of these files —
all are data availability, remediation execution, and re-verification
only.

## Status

Gate 2 (historical data adequacy) is **not yet satisfied**. The
inventory, the A/B/C decision, the data extension, its post-extension
re-verification, the discovery of a +2-per-ETF surplus defect, and that
defect's remediation (export-then-delete, re-verified two-directionally
clean: 0 missing, 0 surplus, of 2474 expected trading days per ETF
across all 25 ETFs) are all now complete. What remains is a
**genuinely independent reviewer** confirmation per the governance
plan's Section 4 duties and the remediation plan's Section 8 — someone
who did not author or execute the delete script, re-querying the live
database and producing a new
`gate2_independent_review_<date>_post_remediation.md`. This cannot be
self-certified by the same process that performed the remediation, and
does not yet exist. No H3 construction, benchmark, peer group, or
lookback window may be chosen until all four gates are satisfied.
