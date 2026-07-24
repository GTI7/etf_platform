# ETF Intelligence Platform

A transparent ETF research and analytics tool. It analyzes and screens ETFs
against explicit, caller-supplied criteria. It never recommends what to buy
or sell, never optimizes a portfolio, and never applies a hidden default
investment preference -- every scoring profile, criterion, and identifier
used by any command must be supplied explicitly.

## What this repository contains

This repository holds two kinds of material, governed differently.

**Software.** `core/` and `adapters/` contain the platform's executable
code, running the commands documented below. `migrations/` contains
database schema changes. `config/` and `portfolio/` are reserved layout
packages, currently empty. `tools/` and `maintenance/` are repository
tooling (import-boundary checks, one-off data remediation), not part of
the CLI.

**Research material.** `experiments/`, `research_archive/`, and `docs/`
are not the platform. `experiments/` holds research runners, setup
utilities, and analysis scripts that are not registered as CLI commands,
are not installed or scheduled by anything here, and do not modify
`core/` or `adapters/` (see `experiments/README.md`). The one deliberate
exception is governance reproduction tooling: `core/governance/
reproduction_runner.py` intentionally loads and executes a pinned
commit's own copy of an experiment script as part of a governed
reproduction attempt (see that module's docstring) -- an explicit,
narrow carve-out, not a general rule that `core/` runs `experiments/`
code. `research_archive/` holds research evidence records, at different
lifecycle stages: a dated, closed-out snapshot for some cycles, and only
the evidence produced so far for others still open. Normal analytical
commands (`analyze`, `update`, `rank`, `compare`, `history`) never read
`research_archive/` to compute a score, rank, or report; governance
tooling (again, `core/governance/reproduction_runner.py`) may
intentionally inspect specific archive artifacts as part of a
reproduction attempt (see `research_archive/README.md`). `docs/` holds
the narrative for those cycles and the process they were conducted
under (`docs/RESEARCH_GOVERNANCE_STANDARD.md`).

The boundary matters in one direction in particular: a finding recorded
in `research_archive/` or `docs/` is a statement about the specific
sample and code revision it was produced from. It does not describe the
software in `core/`, and installing or running the platform neither
carries that finding forward nor re-establishes it.

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

## Reproducibility limitations

This section states what the repository does and does not let you
regenerate. It makes no claim that any figure recorded in
`research_archive/` or `docs/` can be reproduced today.

- **The database is caller-supplied and mutable.** Every command takes
  `--db-path`, and the prerequisite rows are created through repository
  functions rather than a CLI command (see Setup above). Two databases
  built by different hands can differ, and nothing in a report states
  which one produced it.
- **Price data comes from a live third-party provider.** A fetch made
  today may return values that differ from the ones a past run stored,
  and the platform does not snapshot provider responses.
- **Indicator values depend on the trading calendar.** SMA/RSI windows
  are derived from `TradingSession` rows, so a database seeded with a
  different or incomplete calendar produces different indicator values
  from the same prices (see `experiments/README.md`).
- **Analysis-script output at the repo root is overwritten.** The
  `*_significance_report.json` files are gitignored working output,
  regenerated by every run; the copy a past conclusion was drawn from
  is not necessarily the copy on disk.
- **Archive contents vary by cycle status and are not uniformly
  complete.** `research_archive/` holds records from cycles at
  different lifecycle stages -- some contain a dated, closed-out
  snapshot; others contain only the partial or current records
  accumulated so far. Cycles also differ in shape: earlier ones predate
  the evidence-package structure in `docs/RESEARCH_GOVERNANCE_STANDARD.md`
  Section 5 and the `archive_manifest.json` convention, which is not
  applied retroactively (`docs/RESEARCH_ARCHIVE_MANIFEST.md`). Inspect
  each cycle's own `README.md` or `archive_manifest.json`, where
  available, for what it actually contains.
- **Manually re-running an analysis script is a fresh execution, not a
  reproduction.** It produces a new result from whatever data is present
  at that moment, under whatever code is checked out. Governed
  reproduction -- verifying that a past result still holds against its
  originally frozen commit and dataset -- is a separate, controlled
  mechanism (`core/governance/reproduction_runner.py`); the two are not
  interchangeable.

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

These commands, and every other command in this platform, are research
and analysis tools only. They never rank, screen, or compare toward a
recommendation, and their output never states what is "best," "worst,"
or should be bought or sold. No output of this platform is investment
advice, a solicitation, or a suitability assessment: it is not
personalized to any holder's circumstances, does not account for
transaction costs, taxes, or liquidity, and must not be treated as a
basis for allocating capital. Scores, ranks, and comparisons describe
only what the configured scoring profile computed from the data present
in the database for the requested dates -- past-period figures carry no
claim about future results.
