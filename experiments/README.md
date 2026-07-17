# experiments/

This directory holds two different kinds of scripts, neither of them
production code:

- **Research runners** (e.g. `daily_etf_universe_update.py`) -- collect
  real ETF scoring history over time. Safe to run daily/on a schedule.
  Produce a factual research summary as output.
- **Setup utilities** (e.g. `seed_trading_calendar.py`) -- populate
  one-time or occasionally-refreshed prerequisite data (data the
  research runners and the platform's write pipeline require to exist,
  but do not themselves generate) and then are done. Never scheduled,
  never collect research history, produce a factual setup summary as
  output. `seed_trading_calendar.py` belongs here rather than in a new
  top-level directory because it exists for exactly one reason -- to
  satisfy `daily_etf_universe_update.py`'s own documented trading-
  calendar prerequisite below -- and because as of this writing it is
  the only script of its kind; a dedicated directory for "setup
  utilities" would be structure built ahead of a second concrete need,
  the same abstraction this project consistently declines to build
  early elsewhere (see `docs/ARCHITECTURE_DECISIONS.md` and
  `docs/BASELINE_STATUS.md`'s "Abstraction discipline").

Both kinds of script share the same boundary rules:

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
