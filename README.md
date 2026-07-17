# ETF Intelligence Platform

A transparent ETF research and analytics tool. It analyzes and screens ETFs
against explicit, caller-supplied criteria. It never recommends what to buy
or sell, never optimizes a portfolio, and never applies a hidden default
investment preference -- every scoring profile, criterion, and identifier
used by any command must be supplied explicitly.

## Setup

The platform reads and writes a single SQLite database file. There is no
installer: pick a path for that file (e.g. `etf.db`) and pass it explicitly
to every command via `--db-path`/`db_path`. The database schema is created
automatically the first time a command opens the file.

Before any command can produce output, the database needs at least:

- a `Calendar` and its `TradingSession` rows for the exchange(s) you track
- one `ETF` row per ticker you want to analyze
- an `IndicatorDefinition` for SMA and one for RSI (the parameters the
  write pipeline computes on each update)
- a `ScoringProfile` describing which indicator feeds which scoring
  dimension

This one-time setup is not yet exposed through the CLI; it is done via the
repository functions in `core/analytics/persistence/repository.py` and
`core/market_data/persistence/repository.py` (see `tests/test_write_pipeline.py`
for a complete, working example of everything above being created).

## Running analysis

```
python -m adapters.cli.main analyze <ticker> <profile_name> <profile_version> <session_date> <db_path>
```

Prints a single-ETF analysis report (identity, overall score, per-dimension
breakdown, rank among peers) for one ticker, scoring profile, and session
date. Every argument is required -- there are no defaults.

## Running an update

```
python -m adapters.cli.main update \
  --ticker <ticker> \
  --sma-name <name> --sma-version <version> \
  --rsi-name <name> --rsi-version <version> \
  --profile-name <name> --profile-version <version> \
  --session-date <date> \
  --db-path <db_path>
```

Ingests today's price for one ETF, computes SMA and RSI, and computes a
score for one session date -- using the existing write pipeline. Re-running
it for a date that's already been processed is safe (each stage is
idempotent). Every identifier is required -- there are no defaults, no
"latest" behavior, and no automatic selection.
