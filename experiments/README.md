# experiments/

This directory holds three different kinds of scripts, none of them
production code:

- **Research runners** (e.g. `daily_etf_universe_update.py`) -- *produce*
  real ETF scoring history over time. Safe to run daily/on a schedule.
  Produce a factual research summary as output.
- **Setup utilities** (e.g. `seed_trading_calendar.py`,
  `backfill_price_history.py`) -- populate one-time or occasionally-
  refreshed prerequisite data (data the research runners and the
  platform's write pipeline require to exist, but do not themselves
  generate) and then are done. Never scheduled, never collect or
  interpret research history, produce a factual setup summary as
  output.
- **Research analysis scripts** (e.g. `validate_scoring_signal.py`) --
  *consume* history the research runners already produced and ask
  whether it means anything (e.g. does a ranking correlate with
  subsequent returns). Produce a factual research finding, explicitly
  disclosing its own sample size and limitations -- never a
  recommendation, never a claim of proof.

None of these three categories gets its own top-level directory or
dedicated subdirectory. Each new script that doesn't fit the existing
two categories has, so far, been exactly one script -- a dedicated
directory or module per category would be structure built ahead of a
second concrete need, the same abstraction this project consistently
declines to build early elsewhere (see `docs/ARCHITECTURE_DECISIONS.md`
and `docs/BASELINE_STATUS.md`'s "Abstraction discipline"). The same
reasoning applies to `core/`: none of the price-acquisition or
signal-research logic in this directory was added to `core/` either --
see each script's own module docstring for why, but in short: every
function these scripts need (`DataProvider.fetch_daily_bars()` with a
real date range, `insert_price_bar()`, `generate_ranked_etf_report()`
for a past date, `daily_etf_universe_update.run(session_date=...)`)
already existed, unmodified, before either script was written. Nothing
new was needed in `core/` to build them.

All three kinds of script share the same boundary rules:

- Neither is part of the `etf` CLI (`etf update`, `etf status`, `etf
  analyze`, `etf rank`, `etf compare`, `etf history`) and neither is
  installed, scheduled, or shipped as part of the platform.
- Neither modifies `core/`, `adapters/`, database models, migrations,
  or scoring logic. Both only call existing application/repository
  functions (e.g. `core.analytics.write_pipeline.run_write_pipeline_for_etfs`,
  `core.market_data.persistence.repository.insert_trading_session`)
  exactly as those functions already exist.
- No new CLI commands, config framework, scheduler, or UI are added by
  anything in this directory.

## daily_etf_universe_update.py

Runs the platform's existing write pipeline (price ingestion -> SMA ->
RSI -> score) once per ETF across a fixed, editable ~25-ticker research
universe spanning global equity, US equity, regional equity, sectors,
themes, and defensive assets.

Purpose: collect real, daily ETF scoring history across a broad,
realistic universe so there is actual data to look at before any
future decisions are made about a UI, dashboard, or additional
platform features. It exists to generate evidence, not to make
recommendations -- the script prints a factual success/failure summary
only (no ranking, no "buy this", no investment advice).

Run it with:

```
python experiments/daily_etf_universe_update.py
```

It uses its own database file (`experiments_etf_universe.db` at the
repo root, gitignored-equivalent scratch data) so it never touches the
database used by the production CLI. The ETF list, database path,
SMA/RSI definitions, and scoring profile are all plain constants at
the top of the file -- edit them directly, no config framework
involved.

Each run is idempotent (same guarantee the platform's own pipeline
provides) and continues past a single ETF's failure rather than
aborting the whole batch, so it is safe to run daily via whatever
external scheduler you prefer -- this directory does not install or
manage one.

### Prerequisite: a valid trading calendar must already exist

This script bootstraps `ETF`, `IndicatorDefinition`, and
`ScoringProfile` rows on first run, but it does **not** create a
`Calendar` or `TradingSession` rows, and it will not run against a
database that has neither. If no trading days are found for
`CALENDAR_ID` ("XNYS"), it prints a factual error and exits (status 1)
instead of guessing.

This is intentional, not an oversight. An earlier version of this
script generated `TradingSession` rows itself using a weekday-based
heuristic (every Mon-Fri marked a trading day). That is market-data
domain logic -- deciding which dates are real trading sessions -- and
it belongs to the platform, not to an experiment script:

- `core.market_data.persistence.repository.is_trading_day()` is
  explicitly documented to treat an unpopulated date as non-trading
  ("safe default: skip rather than guess"). The weekday heuristic did
  the opposite -- it guessed and wrote the guess to the database.
- `core.analytics.indicator_calculation` derives the SMA/RSI window
  directly from `get_trading_days()`, so calendar content is a direct
  input to whether a computed indicator value is correct -- on the
  same footing as price data, not incidental setup.
- In practice, the weekday heuristic silently mismarked real NYSE
  closures (e.g. Juneteenth, the pre-July-4th half day) as trading
  days, which produced incorrect SMA/RSI windows until manually
  corrected.

So: populate a real `Calendar` and its `TradingSession` rows for
`CALENDAR_ID` before running this script. `seed_trading_calendar.py`,
also in this directory, does exactly that -- see below.

### Cold-start history requirement

Even with a valid calendar in place, SMA20/RSI14 cannot be computed
until enough real trading days have actually been ingested: the
platform's write pipeline ingests one session-day per run (by design,
not as a limitation -- see `ingest_daily_prices`), and `SMA` with a
20-day window needs 20 real trading days of `PriceBar` history to
exist before it can be calculated at all. Concretely, running this
script daily from a fresh database will report `Failed` for every
ticker (with `InsufficientPriceHistoryError`) for roughly the first 20
trading days, and start reporting `Successful` once enough history has
accumulated. This is expected, factual, fail-loud behavior, not a bug
in this script.

### Not part of the production CLI

To restate plainly: this script is not `etf update`, `etf status`, or
`etf analyze`, is not installed or registered anywhere, and nothing in
`core/` or `adapters/` depends on it or is changed by it. It exists
solely to run the platform's existing pipeline over a realistic ETF
universe and collect real operational history for future review.

## seed_trading_calendar.py

A **setup utility**, not a research runner: it populates real,
exchange-accurate `Calendar`/`TradingSession` rows -- the prerequisite
`daily_etf_universe_update.py` above documents and refuses to invent
itself -- and produces no ETF scoring history of its own.

Run it once before the first research run against a fresh database, or
occasionally afterward to extend calendar coverage further into the
future:

```
python experiments/seed_trading_calendar.py
```

It requires the `exchange_calendars` package, which is **not**
installed by any part of this platform:

```
pip install exchange_calendars
```

This is a documented, tool-local dependency only. `core/` and
`adapters/` have zero third-party runtime dependencies, and installing
this package does not change that -- nothing outside this one file
imports it, and it is never added to any project-wide dependency
declaration. If you never run this script, you never need it installed.

Idempotent, same discipline as every other script in this directory:
re-running it (to extend coverage, or against an already-seeded
database) never fails on "already exists" and never duplicates rows.
It uses the same `experiments_etf_universe.db` file at the repo root
that `daily_etf_universe_update.py` uses by default, so a normal
first-time sequence is:

```
python experiments/seed_trading_calendar.py
python experiments/daily_etf_universe_update.py
```

## backfill_price_history.py

A **setup utility**, not a research runner and not the daily
production pipeline. `daily_etf_universe_update.py`'s own pipeline
ingests one session-day per run, by design -- correct for daily
production use, far too slow (one HTTP request per ETF per day) to
build up months or years of history without risking the kind of
provider rate-limiting this project has already hit for real (see
`core/market_data/providers/yahoo_finance.py`'s v0.15.1/v0.15.2 fixes).

This script solves that with zero new machinery: it calls the
platform's existing `DataProvider.fetch_daily_bars(ticker, start, end)`
directly with a real date range -- one request per ETF for the whole
range -- and inserts each bar via the existing `insert_price_bar()`
repository function. Single responsibility: price bars only. It does
not calculate indicators or scores, does not seed a calendar, and does
not modify ingestion logic or introduce a provider abstraction.

Requires ETF rows to already exist (run `daily_etf_universe_update.py`
at least once first) -- this script does not register ETFs; a ticker
with no ETF row is reported as skipped, not created.

Run it with:

```
python experiments/backfill_price_history.py
```

Idempotent: existing `PriceBar` rows are read once per ETF before
fetching, and only genuinely new dates from the provider response are
inserted. No new dependency -- it uses the same `YahooFinanceProvider`
the rest of the platform already uses.

## validate_scoring_signal.py

A **research analysis script**, explicitly not called backtesting, a
validation framework, or a signal engine -- see its own module
docstring for why "backtesting" is the wrong word here (it would imply
trade simulation, which this platform has never had and doesn't gain
now). It asks exactly one question:

> Over this historical period, did higher-ranked ETFs have different
> subsequent returns than lower-ranked ETFs?

It reuses `daily_etf_universe_update.run(session_date=...)` and
`generate_ranked_etf_report()` unmodified -- both already work
correctly for historical dates, with no change needed. The only new
code is a private `forward_return()` calculation (pure, `Decimal`, no
database access, same discipline as
`core.analytics.domain.calculations.max_drawdown()`) and the
loop/aggregation logic that composes the above into one factual
report. Nothing here is published as a reusable interface.

Deliberately minimal scope: one scoring profile, one ETF universe, one
fixed forward-return horizon, a top-k vs. bottom-k bucket comparison.
No benchmark comparison, no multiple horizons, no parameter sweep, no
persistence of results, no CLI command -- all explicitly out of scope
for this first version.

Requires `backfill_price_history.py` (above) to have already provided
real price depth covering the requested period plus the forward-return
horizon beyond it; without that, most or all historical dates will
have no Score yet and this script will factually report very few or
zero observed ranking dates.

Run it with:

```
python experiments/validate_scoring_signal.py
```

The report always discloses its own sample size and limitations
(observations are not independent, one historical regime only,
survivorship bias in the ETF universe) and ends with an explicit
disclaimer that it does not confirm, validate, or prove predictive
value -- no recommendation, no ranking judgment, no investment advice.
No new dependency.
