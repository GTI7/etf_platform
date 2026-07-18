# REFERENCE H3 — Gate 2 Evidence Discrepancy Analysis

**Status: investigation only. No code, data, scoring, or governance
document has been modified as part of this analysis.** This report
answers a single question: why does `data_inventory_2026-07-19.json`
say BOTZ has 2474 bars while
`data_inventory_2026-07-19_post_extension.json`'s
`before_after_coverage.after.bars_per_etf` says 2476, and does that gap
invalidate the "0 missing dates" verification claim.

## 1. Executive conclusion

The +2 bar discrepancy is real, but it is **not** a defect in the H3
historical extension work, and it is **not** a case of 2474 being the
wrong expected count. Both database queries below confirm 2474 is the
correct number of real XNYS trading days between 2016-09-13 and
2026-07-17.

The database genuinely contains **2 invalid extra `PriceBar` rows per
ETF** (50 rows total: 25 tickers × 2 dates), on **2026-06-19**
(Juneteenth) and **2026-07-03** (the pre-July-4th observed holiday,
since July 4, 2026 falls on a Saturday) — both real NYSE closures,
correctly absent from the `TradingSession` calendar. These rows are
tagged `source='backfill-gap-fill'`, a value that does not appear
anywhere in the current codebase's ingestion paths.

Critically, timestamp evidence shows these 2 bad bars were already in
the database on **2026-07-17, a full day before** the H3 extension ran
(2026-07-18). **Root cause classification: (A)** — the database
contains 2 invalid/extra bars per ETF, pre-existing and unrelated to
the Gate 2 extension. The post-extension verification script's "0
missing dates" claim is accurate on its own narrow terms but incomplete:
it only checks for missing dates, never for surplus/extra dates, which
is why it did not catch this.

## 2. Exact evidence reviewed

- [`research_archive/reference_h3/data_inventory_2026-07-19.json`](../research_archive/reference_h3/data_inventory_2026-07-19.json) — BOTZ `bars: 2474`, `earliest: 2016-09-13`, `latest: 2026-07-17`; also `current_database_backfilled_range.bars_per_etf: 504` for the then-current window (2024-07-17 → 2026-07-17).
- [`research_archive/reference_h3/data_inventory_2026-07-19_post_extension.json`](../research_archive/reference_h3/data_inventory_2026-07-19_post_extension.json) — `before_after_coverage.after.bars_per_etf: 2476`; `post_extension_verification.result`: "0 missing dates of 2474 expected trading days".
- [`research_archive/reference_h3/gate2_independent_review_2026-07-19.md`](../research_archive/reference_h3/gate2_independent_review_2026-07-19.md) — prior reviewer signed off on substance but correctly flagged that independence was unmet; did not catch this discrepancy.
- Direct SQLite queries against the live `experiments_etf_universe.db` (read-only; `sqlite3` module via Python, no CLI available in this environment), covering `TradingSession`, `PriceBar`, and `ETF` tables.
- Ingestion source code: [`core/market_data/ingestion/price_ingestion.py`](../core/market_data/ingestion/price_ingestion.py), [`experiments/backfill_price_history.py`](../experiments/backfill_price_history.py), [`experiments/seed_trading_calendar.py`](../experiments/seed_trading_calendar.py) — read for the daily pipeline's and the extension script's actual insert logic and `source` tagging.

## 3. Database findings

Queried directly (calendar `XNYS`, BOTZ `etf_id = 260b96d1ad0e49809e8a502304ee567d`):

| Query | Result |
|---|---|
| `TradingSession` rows, `2016-09-13`–`2026-07-17`, `is_trading_day=1` | **2474** |
| `TradingSession` rows in same range with `is_trading_day=0` | 0 (table only ever stores `is_trading_day=1`; a non-trading date simply has no row) |
| `PriceBar` rows, BOTZ, same range | **2476** |
| Duplicate `(etf_id, session_date)` pairs, BOTZ | 0 |
| `PriceBar` dates for BOTZ with no matching `is_trading_day=1` `TradingSession` row | **2**: `2026-06-19`, `2026-07-03` |
| Real trading days (`TradingSession`) with no matching `PriceBar` for BOTZ | 0 |

Both anomalous dates are legitimate NYSE closures, correctly absent
from the calendar seeded via `exchange_calendars` (per
`seed_trading_calendar.py`'s explicit design intent — see its docstring
on the earlier "naive weekday heuristic" bug it replaced):
- `2026-06-19` = Friday = Juneteenth National Independence Day.
- `2026-07-03` = Friday = observed Independence Day holiday (July 4,
  2026 is a Saturday; NYSE closes the preceding Friday in that case).

**Scope check across the full universe**: the same 2 dates produce
exactly 50 `PriceBar` rows total (25 ETFs × 2 dates) — every ETF has
identically 2 extra rows, no more, no fewer, and no other anomalous
date exists anywhere in the table (verified by an unrestricted
join across all `PriceBar` rows and all tickers).

Each of the 50 rows has `open = high = low = close` (a single flat
price, not a real OHLC bar) and `volume = 0` — the signature of a
synthetic last-known-price fill, not a genuine market bar.

**Timestamp evidence (decisive for root cause):**

| Batch | `ingested_at` range | Row count |
|---|---|---|
| Pre-existing "before" window (`source='yahoo_finance'`, `2024-07-17`–`2026-07-17`) | 2026-07-17T21:31:40 – 21:31:58 UTC | 12,550 (502/ETF) |
| **Anomalous rows (`source='backfill-gap-fill'`)** | **2026-07-17T21:32:29 – 21:32:30 UTC** | **50 (2/ETF)** |
| H3 extension batch (`source='yahoo_finance'`, `2016-09-13`–`2024-07-16`) | 2026-07-18T22:24:05 – 22:24:13 UTC | 49,300 (1972/ETF) |

The 2 bad bars were inserted **2026-07-17, roughly a full day before**
the H3 extension ran on 2026-07-18. They are part of whatever process
originally populated the pre-existing 504-bar "before" window — indeed
502 (`yahoo_finance`) + 2 (`backfill-gap-fill`) = 504, exactly matching
`data_inventory_2026-07-19.json`'s pre-extension
`current_database_backfilled_range.bars_per_etf: 504`. **The anomaly
predates not just the H3 extension but the original pre-extension
inventory baseline itself** — it was silently already present when
Gate 2 work began.

## 4. Provider-count findings

`data_inventory_2026-07-19.json`'s BOTZ `bars: 2474` figure is
annotated as `"source": "live YahooFinanceProvider.fetch_daily_bars,
read-only, no database write"` — i.e., a live provider query for
BOTZ's own `[earliest, latest]` range, made before any extension work
touched the database.

This number is **correct** and matches the true XNYS calendar count
independently derived from the database's own `TradingSession` table
(2474, per Section 3 above) — two independently-sourced counts (live
provider query, and the `exchange_calendars`-seeded database calendar)
agree exactly. There is no evidence 2474 was a trading-calendar
approximation, a filtered count, or a script error — it reproduces
cleanly against the authoritative calendar source.

The `effective_sample_size_estimation` block's `2479` figure (for
"full common history, all 25 ETFs, 2016-09-13") is a different,
explicitly-labeled approximation (`calendar_days * 252/365.25`) used
only for an illustrative sample-size estimate table, not a data
completeness claim, and is not evidence of any error — the report
itself discloses this formula as approximate.

**Conclusion: the provider availability count (2474) is correct. 2476
is not a corrected or better expected value — it is the actual stored
count, which includes 2 invalid rows.**

## 5. Missing-data verification methodology

`data_inventory_2026-07-19_post_extension.json`'s `method` field states
the check compares "stored PriceBar dates against the full set of real
XNYS trading days" and reports **only**: "0 missing dates of 2474
expected trading days."

This phrasing, and the fact that it did not catch a stored count of
2476 against an expected count of 2474, indicates the check computes
only:

```
missing = expected_dates - stored_dates
```

and never computes or reports:

```
surplus = stored_dates - expected_dates
```

A one-directional missing-only check is consistent with everything
observed: it would correctly report 0 missing (all 2474 real trading
days are indeed present among BOTZ's 2476 stored bars) while remaining
silent on the fact that 2 stored dates fall **outside** the expected
set entirely. This is a real, if narrow, methodology gap — not a
fabrication of the "ALL CLEAN" result, since on the specific claim it
makes (no missing dates), it is accurate.

## 6. Root cause

**(A) The database contains 2 invalid/extra bars per ETF.**

Specifically: 2 synthetic, flat-price, zero-volume `PriceBar` rows per
ETF (50 total across the 25-ETF universe) on 2026-06-19 and
2026-07-03 — both real NYSE holidays, correctly excluded from the
`XNYS` `TradingSession` calendar — tagged with `source =
'backfill-gap-fill'`, a value not produced by any ingestion mechanism
present in the current codebase (`ingest_daily_prices` gates all
inserts on `is_trading_day()` and would not have created these even
historically; `backfill_price_history.run` tags everything
`provider.name` = `'yahoo_finance'`). Timestamp evidence places these
rows' insertion before the H3 extension ran, as part of whatever
process originally populated the database's pre-existing 2-year
window. Ruled out: **(B)** — 2474 is independently confirmed correct
by two sources (live provider query and the database's own seeded
calendar), not wrong. **(C)** — the database itself, not just the
archive documentation, is where the extra rows physically live; this
is not a documentation-only error.

## 7. Whether Gate 2 evidence needs correction

Yes, narrowly. `data_inventory_2026-07-19_post_extension.json`'s
`post_extension_verification.result` string ("0 missing dates of 2474
expected trading days... ALL CLEAN") is technically true but
materially incomplete: it does not disclose that `before_after_coverage
.after.bars_per_etf` (2476) exceeds the expected count (2474) by 2, nor
does it identify or explain those 2 extra rows. A corrected version of
this evidence file should state the surplus explicitly and identify
the 2 dates and their `backfill-gap-fill` source, rather than
presenting "ALL CLEAN" without that context. Per this task's scope,
no such correction has been made yet — this is a recommendation only.

## 8. Whether database correction is required

Yes, in principle — the 2 rows are not genuine market data (flat
price, zero volume, on non-trading dates, from an unidentified/orphaned
source) and their presence inflates every BOTZ-anchored bar count by 2
for any future H3 work built on this universe's common-start window.
However, **no database change has been made under this task's scope**
(Phase 1 is investigation-only, per instructions). Correction requires
its own decision: whether to delete the 2 rows, and whether their
presence indicates a broader latent issue in whatever process created
them (its origin is still unidentified — see Section 9).

## 9. Recommended next action

1. Treat this report, not the existing `post_extension_verification`
   text, as the authoritative account of the +2 discrepancy.
2. Before any deletion: identify the actual origin of
   `source='backfill-gap-fill'` rows — this string does not exist in
   the current codebase, meaning either (a) a since-removed or
   never-committed script produced them, or (b) they were inserted
   manually/ad hoc outside the platform's normal tooling. This matters
   because if such a mechanism still runs anywhere (e.g., a scheduled
   job not visible in this repository), it could reintroduce the same
   defect after cleanup.
3. Once origin is understood, the fix is narrow: remove the 2 rows per
   ETF (or the general class: any `PriceBar` row whose `session_date`
   has no matching `is_trading_day=1` `TradingSession` row) and re-run
   the post-extension verification with a two-directional check
   (missing **and** surplus) so future evidence cannot silently
   pass "ALL CLEAN" with a surplus present.
4. This surplus check should become a permanent part of the Gate 2
   verification methodology, not a one-time fix, given it already
   masked a real defect once.
5. Gate 2 should remain in **HOLD** until (a) the correction in #3 is
   made and re-verified, and (b) genuine independent-reviewer
   confirmation (per the governance plan's Section 4, still open per
   `gate2_independent_review_2026-07-19.md`) occurs. Neither this
   report nor the prior self-review satisfies that independence
   requirement.

No H3 hypothesis, benchmark, peer group, scoring logic, lookback
window, IC, p-value, or forward return was considered, computed, or
referenced anywhere in this investigation.

---

**STOP — awaiting approval before any code, data, or document change.**
