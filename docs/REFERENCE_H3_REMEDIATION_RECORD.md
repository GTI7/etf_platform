# REFERENCE H3 — Gate 2 Database Remediation Record

**Status: remediation executed and validated. Gate 2 remains HOLD
pending independent reviewer confirmation.** This document is a
forward-pointing addendum: it records what was done, does not rewrite
[`REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md`](REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md)
(which remains the authoritative account of how the discrepancy was
found), and implements exactly the approach selected in
[`REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md`](REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md)
(Option F: export-then-delete, Option D's invariant as the predicate).

## 1. What was done

Per the remediation plan's Section 4, executed as a single, reviewed,
versioned, one-off script —
[`maintenance/remediate_h3_invalid_pricebar_rows.py`](../maintenance/remediate_h3_invalid_pricebar_rows.py)
— never run interactively/ad hoc:

1. **Dry run.** The delete predicate (any `PriceBar` row whose
   `(etf_id, session_date)` has no matching `is_trading_day=1`
   `TradingSession` row for that ETF's calendar — Option D, not a
   `source` tag match) was run read-only first. It matched exactly 50
   rows: 25 ETFs x 2 dates (`2026-06-19`, `2026-07-03`), all tagged
   `source='backfill-gap-fill'`, all flat-OHLC, all zero-volume —
   an exact match to the investigation's enumerated set. A different
   count, or any deviation from that shape, was a hard stop condition
   the script enforces before any write.
2. **Export.** The full 50 matched rows (every column, plus each row's
   ticker/calendar for readability) were written to
   [`research_archive/reference_h3/removed_backfill_gap_fill_rows_2026-07-19.json`](../research_archive/reference_h3/removed_backfill_gap_fill_rows_2026-07-19.json),
   then re-read from disk and verified to contain exactly the same 50
   `price_bar_id` values as the live dry run, before any delete was
   permitted to proceed.
3. **Delete, inside a transaction.** `PriceBar` carries a `BEFORE
   DELETE` trigger (`trg_pricebar_no_delete`) enforcing this table's
   general append-only design — it unconditionally raises `ABORT`.
   This is not addressed in the remediation plan, which predates
   discovery of the trigger. To execute the approved, audited delete,
   the script drops the trigger, deletes exactly the 50 row IDs
   captured in the export (not a re-evaluation of the predicate at
   delete time, so the exported and deleted sets are provably
   identical), recreates the trigger verbatim (byte-identical to
   [`migrations/0001_initial_schema.sql`](../migrations/0001_initial_schema.sql),
   with a script-level self-check against drift), and re-runs the
   predicate once more inside the same transaction to confirm zero
   rows remain before committing. If anything fails before `COMMIT`,
   SQLite rolls back the `DROP` along with everything else, so the
   immutability guarantee is never left weakened. This was manually
   re-verified after commit: the trigger still blocks deletion of a
   real row.
4. **Post-remediation validation** (Section 6 of the remediation plan)
   ran automatically in the same script invocation and all six checks
   passed — see
   [`research_archive/reference_h3/post_remediation_validation_2026-07-19.json`](../research_archive/reference_h3/post_remediation_validation_2026-07-19.json)
   for the full machine-readable record, and
   [`research_archive/reference_h3/data_inventory_2026-07-19_post_remediation.json`](../research_archive/reference_h3/data_inventory_2026-07-19_post_remediation.json)
   for the human-readable successor to the post-extension inventory.

## 2. Commands executed

```
python maintenance/remediate_h3_invalid_pricebar_rows.py --dry-run
python maintenance/remediate_h3_invalid_pricebar_rows.py --execute
```

A raw file-level copy of `experiments_etf_universe.db` was also taken
immediately before `--execute` as a belt-and-suspenders safety net,
beyond the plan's required row-level export (the database file is
gitignored and not part of this commit; the row-level export is the
plan's actual, permanent undo mechanism).

## 3. Result summary

| Check | Result |
|---|---|
| Rows exported | 50 (byte-verified against live dry run before delete) |
| Rows deleted | 50 (exact match to exported IDs; `DELETE` rowcount asserted) |
| Row count reconciliation | 61,900 → 61,850 (−50, exact) |
| Two-directional coverage | 0 missing, 0 surplus, of 2474 expected trading days — all 25 ETFs |
| Source-tag audit | Only `source='yahoo_finance'` remains (61,850 rows); 0 `backfill-gap-fill` or other unrecognized values |
| Universe/date-range integrity | 25 tickers, unchanged; range 2016-09-13 to 2026-07-17 for all ETFs |
| Export/backup integrity | On-disk export row count and `price_bar_id` set match the live matched set exactly |
| Recurrence check | 0 rows match the predicate immediately post-delete; 0 rows inserted since the H3 extension batch other than its own clean batch |

## 4. Origin precondition (Section 5)

[`REFERENCE_H3_BACKFILL_GAP_FILL_ORIGIN_REPORT.md`](REFERENCE_H3_BACKFILL_GAP_FILL_ORIGIN_REPORT.md)
already performed the required best-effort origin investigation before
this remediation began: full Git history/blob scan (162/162 blobs,
clean), all current and past committed `PriceBar`-writing code paths
exonerated, and no `IngestionRun` row referencing anything resembling
this incident. Its conclusion — **unknown, leaning no, not provably
closed** — was treated as satisfying the remediation plan's Section 5
precondition ("if the origin cannot be confidently ruled out, the
delete can still proceed... but Gate 2's re-verification must then
explicitly check for recurrence"), which is why the recurrence check
above is present in validation. A direct query at remediation time
additionally confirmed no `PriceBar` row has been inserted since the
H3 extension's own batch (2026-07-18T22:24:13 UTC) other than that
batch itself, and no `IngestionRun` row anywhere mentions backfill or
gap-fill.

## 5. Remaining limitations

- **Gate 2 is not satisfied by this remediation alone.** Per the
  remediation plan's Section 8, a genuinely independent reviewer — one
  who did not author or execute the delete script — must separately
  re-query the live database, reproduce these figures, confirm the
  export accounts for the row-count delta, confirm no unrecognized
  `source` values remain, and re-confirm the standing no-outcome-data
  duties, recording that confirmation as its own archived document
  (`gate2_independent_review_<date>_post_remediation.md`). That review
  was intentionally **not** produced as part of this remediation, since
  the executor of the delete cannot self-certify independence.
- **The origin of the 50 rows remains unconfirmed**, per Section 4
  above — reconstructed with high confidence as a manual, un-versioned
  action, but not a recovered artifact. No structural guard (schema
  constraint, trigger, or write-time check) currently prevents a
  similar ad hoc write to `PriceBar` in the future beyond the shape of
  the code paths that happen to write it today. The origin report's
  Section 8 suggestion — a lightweight write-time or periodic-audit
  guard tying `PriceBar` inserts to `TradingSession` — remains an
  unauthorized, unimplemented future option, not part of this change.
- **Verification-methodology changes are out of scope here**, per the
  remediation plan's Section 4, point 5: the two-directional check
  used in this validation was implemented inside the one-off
  remediation script for this specific re-verification, not landed as
  a permanent change to any existing verification tooling/pipeline.
  Making the two-directional check a permanent part of Gate 2
  verification methodology (as the discrepancy analysis's Section 9
  recommends) is a separate, separately-reviewable change.
- **No H3 work, scoring, experiment, or research methodology was
  touched.** This remediation is strictly a raw-data hygiene action on
  `PriceBar`, upstream of any H3 construction work, none of which has
  started.

---

**This record does not move Gate 2 off HOLD.** Gate 2 remains HOLD
until an independent reviewer completes the confirmation described in
Section 5 above and the remediation plan's Section 8.
