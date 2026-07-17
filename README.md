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

## Ranking, comparing, and history

These three commands expose existing read-only research capabilities from
`core/analytics/ranked_report.py` -- they perform no calculation, ranking,
or scoring of their own; they only retrieve and format what has already
been computed. Like every other command, every identifier is required --
there is no default scoring profile and no "latest date" selection.

### Ranked report

```
python -m adapters.cli.main rank \
  --date <session_date> \
  --profile-name <name> --profile-version <version> \
  --db-path <db_path> \
  [--risk-name <name> --risk-version <version>]
```

Prints every ETF with a Score for one scoring profile and session date,
ranked, using the existing `generate_ranked_etf_report()`. `--risk-name`/
`--risk-version` are optional and only enable `max_drawdown` display in
the output; omitting them omits `max_drawdown`, exactly as the underlying
function already does.

### Comparison

```
python -m adapters.cli.main compare <ticker> [<ticker> ...] \
  --date <session_date> \
  --profile-name <name> --profile-version <version> \
  --db-path <db_path> \
  [--risk-name <name> --risk-version <version>]
```

Prints the given tickers, ranked locally among just themselves, using the
existing `compare_etfs()`. Zero or one ticker is a valid comparison, the
same as `compare_etfs()` itself -- neither is rejected.

### Score history

```
python -m adapters.cli.main history \
  --ticker <ticker> \
  --profile-name <name> --profile-version <version> \
  --db-path <db_path> \
  [--start-date <date>] [--end-date <date>]
```

Prints one ETF's own Score history under one scoring profile, using the
existing `get_score_history()`. `--start-date`/`--end-date` are optional;
omitting either omits that bound, exactly as the underlying function
already does.

These commands are research and analysis tools only: they never rank,
screen, or compare toward a recommendation, and their output never states
what is "best," "worst," or should be bought or sold -- the same
no-investment-advice boundary every other command in this platform
already holds.
