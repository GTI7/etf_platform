# REFERENCE H3 — Data Sufficiency Report (Pre-Validation Phase 1)

Executes Section 3 ("Historical data sufficiency verification") of the
frozen [`docs/REFERENCE_H3_PREVALIDATION_PLAN.md`](REFERENCE_H3_PREVALIDATION_PLAN.md).
No H3 signal, benchmark, peer group, lookback window, or scoring logic
is defined anywhere in this report. No IC, p-value, forward return, or
predictive performance metric was computed. Raw evidence is archived
at [`research_archive/reference_h3/data_inventory_2026-07-19.json`](../research_archive/reference_h3/data_inventory_2026-07-19.json)
(pre-extension inventory) and
[`research_archive/reference_h3/data_inventory_2026-07-19_post_extension.json`](../research_archive/reference_h3/data_inventory_2026-07-19_post_extension.json)
(the executed extension and its verification).

**Status: Option B has been approved, executed, and verified clean.
Gate 2 is not yet marked satisfied — independent reviewer confirmation
is still outstanding.** See "Final Gate 2 status" at the end of this
report.

## 1. ETF universe history inventory

Queried the live data provider directly (read-only, no database write)
for full available history per ticker, and separately inspected the
currently backfilled database range.

**Provider-level availability** (what actually exists, independent of
what's currently backfilled): 8 of the 25 ETFs have data back to
2000–2003 (`SPY`, `QQQ`, `EWJ`, `XLK`, `XLF`, `XLE`, `XLV` to
2000-01-03; `VTI`, `EFA` to 2001; `TLT` to 2002; `EEM` to 2003). Most
of the remainder go back to 2004–2011. The youngest three are `BOTZ`
(2016-09-13), `HACK` (2014-11-12), and `ARKK` (2014-10-31).

**Currently backfilled database range:** all 25 ETFs identically cover
only 2024-07-17 to 2026-07-17 (504 bars each) — a small fraction of
what the provider actually has available.

**Universe-wide common start** (the date after which all 25 ETFs have
simultaneous data): **2016-09-13**, bound entirely by `BOTZ`.

**Survivorship / availability constraint tickers**, in order of how
much they constrain a full-universe extension:

| Ticker | Earliest available | Years before the universe-binding date |
|---|---|---|
| BOTZ | 2016-09-13 | binds the common start |
| HACK | 2014-11-12 | 1.8y earlier |
| ARKK | 2014-10-31 | 1.9y earlier |
| USMV / SCHD | 2011-10-20 | 4.9y earlier |
| SKYY | 2011-07-06 | 5.2y earlier |

The remaining 19 ETFs all have data back to 2008 or earlier, several
to 2000.

## 2. Effective sample size assessment

Structural date-count calculation only (approx. trading days ÷ 20-day
reference horizon — reused as a structural convention from REFERENCE
v1/H1, not a commitment to any H3-specific horizon, which remains
completely unspecified). No predictive performance was tested or
optimized for.

| Candidate window | Start | ~Trading days | ~Effective independent windows |
|---|---|---|---|
| Current (as backfilled) | 2024-07-17 | 503 | **~25** |
| +1 year | 2023-07-17 | 756 | ~37 |
| +3 years | 2021-07-17 | 1,259 | ~62 |
| +5 years | 2019-07-17 | 1,764 | ~88 |
| Full common history, all 25 ETFs | 2016-09-13 | 2,479 | **~123** |

Extending to the full common-availability start (2016-09-13) — using
the *current, unchanged* 25-ETF universe, no composition change needed
— is a **~5x increase** in effective independent windows over the
current window (~25 → ~123). This is a material improvement, not a
marginal one.

## 3. Regime coverage inventory (descriptive only)

Annual realized volatility and max intra-year drawdown of a
broad-market proxy (`SPY`), computed over its full available history
(2000–2026). Purely descriptive of the price history itself — not
related to any score or forward return.

| Period | Character |
|---|---|
| 2000–2002 | Dot-com bust: vol 22–26%, drawdowns to −34% |
| 2003–2007 | Recovery / low-vol expansion: vol 10–16%, drawdowns ≤ −14% |
| 2008 | Global Financial Crisis: **vol 41.2%, drawdown −47.9%** — the most extreme year on record here |
| 2009–2011 | Recovery and European debt-crisis volatility: vol 18–27% |
| 2012–2019 | Extended low-volatility bull regime: vol as low as **6.7% (2017)**, drawdowns mostly ≤ −12% |
| 2020 | COVID crash: **vol 33.8%, drawdown −34.1%** |
| 2021 | Calm: vol 13.1%, drawdown −5.4% |
| 2022 | Rate-hike bear market: vol 24.3%, drawdown −25.4% |
| 2023–2026 (current backfilled window starts mid-2024) | vol 12.6–19.4%, drawdowns −8.4% to −19.0% |

**The currently backfilled window (2024-07-17 to 2026-07-17) contains
none of the 2008 or 2020 crisis regimes, and none of the extended
2012–2019 low-volatility regime.** It sits entirely within a
moderate-to-elevated volatility band (12.6–19.4%) that is itself only
a slice of the full range this dataset has actually experienced
(6.7% to 41.2%).

## 4. Post-extension verification (executed)

Option B was approved and executed using only existing, unmodified
mechanisms — no new script, no schema change, no core/ change.

**Commands run:**
1. `experiments.seed_trading_calendar.run(start_date=2016-09-13)` —
   seeded 1,973 new real `TradingSession` rows (752 already present
   from the prior range); 2,725 real `XNYS` sessions now cover
   2016-09-13 to 2027-07-19.
2. `experiments.backfill_price_history.run(start_date=2016-09-13, end_date=2024-07-16)`
   — backfilled exactly the gap before the previously-existing window.

**Backfill result:** all 25 ETFs — **1,972 bars inserted each, 0
skipped, 0 missing ETF rows, 49,300 bars total inserted.**

**Before / after coverage:**

| | Start | End | Bars per ETF |
|---|---|---|---|
| Before | 2024-07-17 | 2026-07-17 | 504 |
| After | **2016-09-13** | 2026-07-17 | **2,476** |

**Post-extension missing-data check:** for each of the 25 ETFs,
compared stored bars against every real `XNYS` trading day within that
ETF's own `[earliest, latest]` range.

**Result: ALL CLEAN.** Every one of the 25 ETFs — **0 missing dates of
2,474 expected trading days (0.000% missing)**, identical range
(2016-09-13 to 2026-07-17) across the entire universe.

**Universe check:** confirmed the same 25 tickers as before, in the
same order — no ETF was added or removed as part of this extension.

## Limitations

- Effective-sample-size figures in Section 2 remain approximate
  (calendar-day-based estimates for the candidate-window comparison
  table), and use the 20-day reference horizon inherited from
  REFERENCE v1/H1 purely as a structural yardstick — H3's own eventual
  forecast horizon is unspecified and out of scope for this report.
  The *post-extension* coverage figures above, by contrast, are exact
  (computed directly from real `TradingSession` and `PriceBar` rows,
  not estimated).
- Regime description (Section 3) uses a single broad-market proxy
  (`SPY`); it does not characterize regime behavior separately for
  sector, thematic, or defensive-asset ETFs within the universe, which
  may have diverged from the broad market at times this report does
  not capture.
- Provider-reported and now-ingested dates reflect this platform's
  existing Yahoo Finance integration only; they are not independently
  cross-checked against a second source or against each fund's actual
  prospectus-listed inception date.
- The missing-data check above verifies internal completeness (no gaps
  within each ETF's own stored range) but does not independently
  verify the *correctness* of the ingested price values themselves
  (e.g., against a second data source) — this platform has no existing
  mechanism for that, and building one is out of scope here.

## A/B/C recommendation

**Recommended: B — extend historical data to the full common-availability
start (2016-09-13), using the current, unchanged 25-ETF universe.**

Justification against the plan's own decision criteria:

- **Why not A (continue with current history):** the effective sample
  size gain from extension is not small — it is a ~5x improvement — and
  extension to 2016-09-13 is safe for the entire current universe with
  no composition change, so neither of A's indicating conditions
  ("gain is small" / "extension can't be done safely") holds.
- **Why B over C (change universe composition):** the full-universe
  extension already delivers a material improvement without dropping
  any ticker. Going further back (e.g., to 2008 or 2000) would require
  dropping `BOTZ`, `HACK`, and `ARKK` — the platform's youngest, most
  distinctly thematic ETFs — which the pre-validation plan's own
  Section 5 already flags as a real universe-selection-bias risk, and
  would also change the universe's economic character (removing
  precisely the kind of thematic, rotation-prone names a
  relative-strength hypothesis is most likely to be interested in).
  Option C is not indicated here because Option B already clears the
  "material improvement" bar without that cost.
- **Regime coverage reinforces B, not just the sample-size count:**
  extending to 2016 adds the 2020 COVID crash and most of the
  2017–2019 low-volatility period the current window entirely lacks —
  addressing the qualitative regime-diversity concern, not only the
  quantitative window count.

This recommendation is data-supported, not assumed in advance, per the
plan's own instruction not to presuppose the answer.

## Final Gate 2 status

**Gate 2 is NOT YET marked satisfied.** Per
`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` Section 4, Gate 2 requires:

1. Section 3's inventory completed — **done** (this report, Sections
   1–3).
2. An A/B/C decision made and documented, with reasoning — **done**
   (Option B, justified above).
3. If B or C was chosen, the resulting dataset change executed and
   re-checked for missing data and survivorship risk — **done**
   (Section 4 above: extension executed, 0.000% missing data, universe
   unchanged).
4. Independent confirmation, per Section 4's duties (a reviewer who did
   not perform this work must review the complete evidence, confirm no
   outcome data was used, confirm no prior-cycle results influenced any
   decision, and record that confirmation in the archive) — **not yet
   done.** This step cannot be self-certified by the process that
   performed items 1–3.

Gate 2 will be satisfied once an independent reviewer completes and
records item 4. Gates 1, 3, and 4 remain entirely unaddressed and are
out of scope for this report — no H3 construction, benchmark, peer
group, or lookback window may be chosen until all four gates are
independently confirmed.
