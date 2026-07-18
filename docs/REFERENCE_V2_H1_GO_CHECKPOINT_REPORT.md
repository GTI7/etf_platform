# REFERENCE v2 H1 — GO Checkpoint Report

Data suitability verification only, executed against the frozen
[`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md`](REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md)
(Parts 5 and 9). No forward return, no risk-adjusted return, no H1-A/
H1-B statistic, no permutation test, and no bootstrap was computed at
any point. No data was repaired, filled, or interpolated. `core/`,
`experiments/`, the scoring engine, and existing validation scripts
were not modified — this check ran a standalone, ad hoc, read-only
script against the existing `experiments_etf_universe.db`, using only
existing, unmodified repository functions (`get_trading_days`,
`get_etf_by_ticker`, `get_price_bars`) to read data.

## Methodology

- **Universe:** the same 25-ticker `ETF_UNIVERSE` defined in
  `experiments/daily_etf_universe_update.py`.
- **Calendar:** `XNYS` trading days as populated in the database's
  `Calendar`/`TradingSession` tables.
- **Score (60-day lookback), exactly per spec Part 3:** for a ranking
  date to have a computable score, 61 consecutive trading-day close
  prices must be resolvable — the ranking date itself plus the 60
  trading days immediately before it — producing exactly 60
  close-to-close log returns. Realized volatility = sample standard
  deviation (N−1) of those 60 log returns, not annualized. This
  61-price/60-return convention is the standard construction implied
  by "60 trading-day lookback, 60 returns" and is stated explicitly
  here as the operational definition used for this verification — it
  does not alter or extend the frozen specification.
- **Missing data rule, exactly per spec:** no forward-fill, no
  interpolation, no partial windows. A date/ETF pair is excluded from
  scoring entirely if any single day in its 61-price window is
  unresolvable.
- **Forward existence check (not a return calculation):** for the
  panel-feasibility check only, an ETF-date pair is checked for whether
  a close price *exists* 20 trading days later — no return value is
  computed from it.
- **Dispersion checkpoint sampling, exactly per spec Part 5:** one
  ranking date per calendar quarter, the first valid ranking date in
  each quarter, drawn from dates where both the 60-day lookback and the
  20-day-forward existence check are satisfiable (i.e., genuinely
  usable ranking dates — see the calendar/data mismatch note below for
  why this matters).
- **Dispersion metric, exactly per spec:** CV = cross-sectional
  standard deviation(realized volatility) ÷ mean(realized volatility)
  across whichever ETFs have a computable score on that date. No
  outcome variable is touched by this calculation.

---

## 1. Historical data availability

All 25 ETFs in `ETF_UNIVERSE` have a registered `ETF` row and price
history. Every ETF has an **identical** data range:

| Ticker | Earliest date | Latest date | Bar count |
|---|---|---|---|
| VT, ACWI, SPY, VTI, QQQ, IWM, EFA, VGK, EWJ, EEM, XLK, XLF, XLE, XLV, ARKK, ICLN, SKYY, HACK, BOTZ, GLD, TLT, BND, VNQ, USMV, SCHD | 2024-07-17 | 2026-07-17 | 504 |

**Finding — trading calendar extends beyond ingested price data.** The
`XNYS` calendar table contains 752 trading days, spanning 2024-07-17 to
**2027-07-16** — roughly a year further into the future than any ETF
has price data for (data stops at 2026-07-17). This is a real, worth-
noting artifact: the calendar was seeded (`seed_trading_calendar.py`)
further ahead than `daily_etf_universe_update.py`/`backfill_price_history.py`
ever ingested prices for. It does not itself block H1 — the calendar
does not need to match the data range — but it does mean that any
"first/last usable ranking date" figure must be **bounded by the
actual data range**, not by the calendar alone, or it will
systematically overstate usable coverage by counting dates that have
no price data at all. Both bounds are reported below for transparency.

| | Calendar-only bound | **Data-bound (correct for actual use)** |
|---|---|---|
| First usable ranking date | 2024-10-10 | **2024-10-10** |
| Last usable ranking date | 2027-06-16 | **2026-06-17** |
| Candidate ranking dates | 672 | **422** |

The data-bound window (422 candidate dates, 2024-10-10 to 2026-06-17)
is the one used for every subsequent check in this report. It already
satisfies the spec's requirement of ≥60 valid trading days before the
first ranking date and ≥20 valid trading days after the last ranking
date, since it is constructed to guarantee exactly that for every date
in it.

---

## 2. Missing data suitability

Measured across the data-bound window only (422 candidate dates × 25
ETFs = 10,550 possible ETF-date observations), applying the frozen
rule exactly (60-day lookback required, no fill, no interpolation, no
partial windows):

| Metric | Value |
|---|---|
| Total possible ETF-date observations | 10,550 |
| Excluded (incomplete 60-day lookback) | **0 (0.00%)** |
| ETFs with systematic gaps | **None** |

Every one of the 25 ETFs has a complete, gap-free daily bar for every
trading day in its 2024-07-17–2026-07-17 range (504 bars each, matching
the 504 trading days the `XNYS` calendar defines for that span exactly)
— there is no internal missing-data problem within the ingested
history. The only "missing data," in the sense of item 1's calendar
mismatch above, is the un-ingested future period beyond 2026-07-17,
which is excluded from this and all subsequent checks by construction
(the data-bound window), not patched or assumed.

---

## 3. Cross-sectional volatility dispersion GO checkpoint

Sampled dates: one per calendar quarter, first valid date in each
quarter, within the data-bound window (7 quarters covered, 2024-07-17
to 2026-07-17 of history yields quarters 2024-Q4 through 2026-Q2).

| Sampled date | ETF count | CV |
|---|---|---|
| 2024-10-10 | 25 | 0.3857 |
| 2025-01-02 | 25 | 0.4045 |
| 2025-04-01 | 25 | 0.4433 |
| 2025-07-01 | 25 | 0.3087 |
| 2025-10-01 | 25 | 0.3976 |
| 2026-01-02 | 25 | 0.4465 |
| 2026-04-01 | 25 | 0.4332 |

- **Median CV: 0.4045**
- **Threshold: ≥ 0.20**
- **Result: GO** — median CV clears the threshold by more than a
  factor of two, and every individual sampled date (not just the
  median) independently exceeds 0.20, so this is not a borderline or
  single-date-driven result.

No forward return, risk-adjusted return, IC, or p-value was computed
at any point in this check — only the score (realized volatility)
across the full 25-ETF cross-section on each sampled date.

---

## 4. Panel feasibility

Without computing any IC: for each of the 422 data-bound candidate
ranking dates, counted how many ETFs simultaneously have (a) a
computable score (complete 60-day lookback) and (b) a resolvable
forward close price 20 trading days later (existence only, no return
value computed).

| Metric | Value |
|---|---|
| Candidate ranking dates | 422 |
| Feasible (≥ 10 ETFs) | **422 (100.00%)** |
| Infeasible (< 10 ETFs) | 0 |
| Min ETF count across all candidate dates | 25 |
| Max ETF count across all candidate dates | 25 |

Every candidate ranking date in the data-bound window has the full
25-ETF universe available, well above the minimum panel size of 10
established in the frozen specification (Part 6). No date needs to be
excluded from the eventual H1-A/H1-B panel on data-availability
grounds.

---

## Final recommendation

**GO: implementation may begin.**

- Data availability: confirmed, once correctly bounded by the actual
  ingested price range rather than the (longer) trading calendar — a
  distinction worth carrying forward, not a blocker.
- Missing data: none, within the data-bound window (0.00% exclusion,
  no systematic gaps on any ETF).
- Dispersion checkpoint: GO, with a wide margin (median CV 0.4045 vs.
  a 0.20 threshold) and no single-date dependency.
- Panel feasibility: 100% of candidate ranking dates support the full
  25-ETF universe, well above the required minimum of 10.

No specification review is required. This report verifies data
suitability only — it does not test, imply, or anticipate any H1-A or
H1-B result.
