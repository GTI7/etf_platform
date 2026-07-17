# experiments/

Scripts in this directory are **experiment runners**, not production
code:

- They are **not** part of the `etf` CLI (`etf update`, `etf status`,
  `etf analyze`) and are not installed, scheduled, or shipped as part
  of the platform.
- They do not modify `core/`, `adapters/`, database models, migrations,
  or scoring logic. They only call existing application services
  (e.g. `core.analytics.write_pipeline.run_write_pipeline_for_etfs`)
  exactly as those services already exist.
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
`CALENDAR_ID` before running this script. How you do that is outside
this script's scope -- this directory does not add a platform seeding
mechanism, since none currently exists.

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
