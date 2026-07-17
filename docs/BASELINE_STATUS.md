# Analytics Engine Baseline Status

This document is a snapshot, not a proposal. It records the state of the
project through v0.17.0 (the CLI research interface expansion release)
plus four further commits not yet folded into a tagged release, why
each pause point was considered complete for its scope, and what would
have to become true before further implementation is justified. See
`docs/ARCHITECTURE_DECISIONS.md` for the detailed rationale behind
individual decisions referenced here, and
`docs/V0_6_0_DESIGN_WRITE_PIPELINE_COMPOSITION.md` for the v0.6.0 design
review that release implemented.

## Version / state

**v0.17.0 is the current tagged baseline.** Architecture remains exactly
as frozen at v0.4.0 (see below); every release from v0.5.0 through
v0.17.0 has added capability strictly within it — no repository,
migration, scoring, or transaction module has changed since v0.4.0 to
deliver any of them. Migrations are still exactly `0001`-`0003`, frozen
since v0.3.0-era; no new migration file has ever shipped since.

Since this document was last updated at v0.17.0, four further commits
shipped, none yet tagged:

- **`ad82395` — trading calendar seed utility**
  (`experiments/seed_trading_calendar.py`). Populates real,
  exchange-accurate `Calendar`/`TradingSession` rows via the
  `exchange_calendars` package, correctly excluding real NYSE holidays
  (verified against Juneteenth and the pre-July-4th half day, both of
  which a since-removed naive weekday heuristic had mismarked as
  trading days). It writes through the existing, unmodified
  `insert_calendar()`/`insert_trading_session()` repository functions
  only — no new repository function, no new domain model. `core/`,
  `adapters/`, and `migrations/` are untouched.
  `exchange_calendars` is a documented, tool-local dependency: nothing
  outside this one file imports it, and `core/`/`adapters/` remain at
  zero third-party runtime dependencies.
- **`cae13e7` — price backfill and scoring signal research tooling**
  (`experiments/backfill_price_history.py`,
  `experiments/validate_scoring_signal.py`). Both are `experiments/`
  tooling, not platform capability: they consume existing
  `DataProvider.fetch_daily_bars()`, `insert_price_bar()`,
  `daily_etf_universe_update.run(session_date=...)`, and
  `generate_ranked_etf_report()` exactly as those already existed, add
  no new repository function, no new domain model, and are not exposed
  through the CLI. See "Scoring signal research" below for the actual
  finding this tooling produced. `core/`, `adapters/`, and
  `migrations/` are untouched.
- **`cebd5b0` / `67d9e90` — indicator integrity fix**
  (`core/analytics/indicator_calculation.py`). This is the one `core/`
  change among the four: `calculate_sma()`, `calculate_rsi()`, and
  `calculate_drawdown()` previously had no `is_trading_day()` guard,
  unlike `calculate_score()` (which already had one). A non-trading
  `session_date` would silently resolve a window ending at the prior
  real trading day and store a duplicate `IndicatorValue` under the
  non-trading date, rather than skipping cleanly. Found by running the
  real daily experiment runner on a Saturday and observing a duplicate
  SMA value dated to that Saturday. Fixed by applying the exact guard
  `calculate_score()` already used, identically, to all three
  functions. No migration, no repository change, no change to window
  resolution, price loading, transaction boundaries, or
  idempotency-on-rerun — all re-proven unchanged by the existing test
  suite. Two new tests added (mirroring
  `test_scoring_pipeline.py`'s existing non-trading-day test for
  `calculate_score()`), plus one more for `calculate_drawdown()`.
  Verified against real data both via the test suite and by direct
  execution: a genuine future Saturday now produces zero
  `IndicatorValue` rows for all three indicators, where the unguarded
  code previously produced one.

None of the four commits changed a migration or introduced a new
domain model. Exactly one (`cebd5b0`/`67d9e90`) changed `core/`
behavior; the other two are `experiments/`-only, following the same
boundary already established for
`experiments/daily_etf_universe_update.py` (commit `0e06fdd`, itself
still untagged and, per its own README, deliberately not a platform
feature).

## Completed phases

- ✓ Phase 1 — Market Data
- ✓ Phase 2 — Indicators
- ✓ Phase 3 — Scoring Engine
- ✓ Phase 4 — Ranking Engine
- ✓ Phase 5 — Ranked ETF Report
- ✓ v0.5.0 — Second Concrete Indicator
- ✓ v0.6.0 — Write-side Pipeline Composition
- ✓ v0.7.0 — Multi-ETF Write Execution + Dimension Breakdown
- ✓ v0.8.0 — Risk Intelligence Layer (MAX_DRAWDOWN)
- ✓ v0.9.0 — Single-ETF Analysis Report
- ✓ v0.10.0 — ETF Screening
- ✓ v0.11.0 — Bounded Screening Shortlist
- ✓ v0.12.0 — ETF Comparison
- ✓ v0.13.0 — Historical Score Evolution
- ✓ v0.14.0 — First CLI Command (`etf analyze`)
- ✓ v0.15.0 — CLI Subcommand Dispatcher + `etf update`
- ✓ v0.15.1 / v0.15.2 — Yahoo Finance Provider Hardening
- ✓ v0.16.0 — Pipeline Run Visibility (`etf status`)
- ✓ v0.17.0 — CLI Research Interface Expansion (`etf rank` / `etf compare` / `etf history`)
- (untagged) `ad82395` — Trading Calendar Seed Utility
- (untagged) `cae13e7` — Price Backfill + Scoring Signal Research Tooling
- (untagged, see Versioning assessment below) `cebd5b0`/`67d9e90` — Indicator Integrity Fix (non-trading-day guard for SMA/RSI/MAX_DRAWDOWN)

| Phase | Capability |
|---|---|
| 0 | Foundation: Money, Clock, typed IDs, SQLite/WAL, migrations, raw-data immutability, PipelineState |
| 1 | Market data: ETF storage, provider abstraction (Yahoo Finance), TradingCalendar-aware ingestion, immutable PriceBar |
| 2 | Indicators: IndicatorDefinition/IndicatorValue, versioned, immutable, two concrete indicators (SMA, RSI as of v0.5.0) |
| 3 | Scoring: ScoringProfile/Score/DimensionScore, versioned, immutable, deterministic |
| 4 | Ranking: cross-ETF Score retrieval, deterministic ranking, stable tie-break, read-only |
| 5 | Ranked ETF Report: composes Phase 4's pieces into one usable, ETF-identity-resolved report |
| 0.5.0 | Second Concrete Indicator: `rsi()` calculation and `calculate_rsi()` orchestration added beside SMA; the generic `IndicatorDefinition`/`IndicatorValue` architecture validated against two independent concrete implementations; SMA and RSI coexist and are consumed by scoring identically, with zero scoring-layer changes |
| 0.6.0 | Write-side Pipeline Composition: `run_write_pipeline()` (new `core/analytics/write_pipeline.py`) composes `ingest_daily_prices()` → `calculate_sma()` → `calculate_rsi()` → `calculate_score()` for one ETF/session; ingestion idempotency on the composed path is a direct `PriceBar` existence check (not a pipeline watermark, which cannot distinguish an already-ingested session from an earlier, never-ingested backfill session); SMA and RSI are called explicitly, by name, with no dispatch mechanism; `run_pipeline` remains the sole transaction owner, with each stage still committing in its own, separate transaction |
| 0.7.0 | Multi-ETF Write Execution + Dimension Breakdown: `run_write_pipeline_for_etfs()` runs `run_write_pipeline()` sequentially over an explicit list of ETFs for one session, with isolated per-ETF failure handling (`dict[ETFId, WritePipelineResult \| Exception]`) — one ETF's failure never blocks or rolls back another's; `run_write_pipeline()` itself unmodified. `RankedETFReportEntry.dimension_scores` exposes the per-dimension breakdown `overall_score` was already computed from |
| 0.8.0 | Risk Intelligence Layer: `max_drawdown()`/`calculate_drawdown()` — a third concrete indicator, same shape as SMA/RSI, deliberately not wired into `run_write_pipeline()` and remaining independently callable; `RankedETFReportEntry.max_drawdown` and `generate_ranked_etf_report(..., risk_definition_id=None)` expose it as an optional comparison metric only — not a scoring dimension, no `Dimension.RISK` |
| 0.9.0 | Single-ETF Analysis Report: `generate_etf_analysis_report()` — one ETF's identity, overall_score, dimension breakdown, optional max_drawdown, and rank/peer_count among peers for one `(scoring_profile_id, session_date)`; raises `MissingScoreError` when no Score exists (a required precondition, unlike max_drawdown) |
| 0.10.0 | ETF Screening: `screen_etfs()` + `ETFScreeningCriteria` (min_overall_score, min_dimension_scores, max_drawdown) — independent AND filtering over metrics already exposed by `RankedETFReportEntry`, not composite scoring; fail-closed per candidate; raises `InvalidScreeningCriteriaError` for a structurally impossible request before any database work |
| 0.11.0 | Bounded Screening Shortlist: `get_top_candidates()` — the first `limit` entries of `screen_etfs()`'s result, `limit` required with no default; no new ranking or scoring |
| 0.12.0 | ETF Comparison: `compare_etfs()` — a named candidate view delegating entirely to `screen_etfs()` with the caller's ETF set as `candidate_etf_ids`; no new ranking, scoring, or comparison logic |
| 0.13.0 | Historical Score Evolution: `get_scores_for_etf()` (repository) + `get_score_history()`/`ScoreHistoryEntry` — read-only exposure of already-computed Score/DimensionScore history for one ETF/profile, optionally date-range-restricted; no recalculation, no historical ranking, no trend analysis, no forecasting |
| 0.14.0 | First CLI Command: `adapters/cli/main.py`, `etf analyze` — the platform's first entry point outside the test suite |
| 0.15.0 | CLI Subcommand Dispatcher + `etf update`: restructured into `etf analyze \| etf update`; `update` orchestrates the existing, unmodified write pipeline only, with every identifier required, no defaults, no "latest" behavior |
| 0.15.1 / 0.15.2 | Yahoo Finance Provider Hardening: transport/parse failures translated into the existing `ProviderError` (0.15.1); explicit `User-Agent` header added after a real HTTP 429 was traced to Yahoo Finance rejecting the default `urllib` User-Agent (0.15.2) — both confined entirely to `core/market_data/providers/yahoo_finance.py`, found and re-verified via real smoke tests |
| 0.16.0 | Pipeline Run Visibility: `etf status` — the first way to read back the `IngestionRun` audit trail `run_pipeline()` has written since Phase 0; `get_latest_ingestion_run()` (repository) plus pipeline-name construction extracted into `core/shared/pipeline_names.py` so the write-side and read-side can never drift apart |
| 0.17.0 | CLI Research Interface Expansion: `etf rank`, `etf compare`, `etf history` — thin CLI wrappers over `generate_ranked_etf_report()`, `compare_etfs()`, and `get_score_history()` (all pre-existing since v0.7.0-v0.13.0); zero SQL, zero calculation, zero ranking logic in the CLI layer; empty results render as an explicit factual message, never silent output |
| (untagged) | Trading calendar seed utility, price backfill + scoring signal research tooling, and an indicator integrity fix — see Version/state above for detail on each |

## Current capabilities

The system now supports: price ingestion, three indicators (SMA, RSI,
MAX_DRAWDOWN — now consistently non-trading-day-aware, see below),
generic scoring, ranking, screening, comparison, historical score
retrieval, composed single- and multi-ETF write execution, a
six-command CLI exposing most of the read-side capability, and
`experiments/`-level tooling for trading-calendar seeding, historical
price backfill, and scoring signal research.

- **Immutable market history** — price data is ingested once and never altered; corrections are new records, never edits.
- **Versioned indicators** — indicator values are computed deterministically and tied to a specific, immutable `IndicatorDefinition` version. Three concrete indicators now exist (SMA, RSI, MAX_DRAWDOWN), each its own explicit orchestration function — see Abstraction discipline below for why this still hasn't triggered a dispatch mechanism.
- **Non-trading-day-aware indicator calculation** — `calculate_sma()`, `calculate_rsi()`, and `calculate_drawdown()` now all guard against a non-trading `session_date` via `is_trading_day()`, matching `calculate_score()`'s existing behavior exactly (commits `cebd5b0`/`67d9e90`). Previously only `calculate_score()` had this guard; the other three would silently compute and store a duplicate value under a non-trading date instead of skipping cleanly.
- **Deterministic scoring** — `Score`/`DimensionScore` are a pure, reproducible function of immutable indicator data and a versioned `ScoringProfile`.
- **ETF ranking** — cross-ETF `Score` retrieval with deterministic ordering and a stable, explicit tie-break.
- **Ranked report generation** — `generate_ranked_etf_report()` composes retrieval, ranking, and ETF-identity resolution into one usable report for a given `(scoring_profile_id, session_date)`, with an optional `max_drawdown` comparison metric (v0.8.0). Already fully correct for historical dates with no change needed — confirmed directly by the scoring signal research tooling below.
- **Single-ETF analysis** — `generate_etf_analysis_report()` (v0.9.0): one ETF's full report plus its rank/peer_count among the same profile/session's peers.
- **Screening and shortlisting** — `screen_etfs()`/`get_top_candidates()` (v0.10.0/v0.11.0): explicit, caller-supplied criteria only, never a built-in default; ranks are always local and gapless among survivors.
- **Named comparison** — `compare_etfs()` (v0.12.0): a specific caller-supplied set of ETFs, ranked locally among just themselves.
- **Historical score retrieval** — `get_score_history()` (v0.13.0): one ETF's own Score history over time, read-only, no recalculation.
- **Composed write-side execution** — `run_write_pipeline()` (v0.6.0) for one ETF/session, and `run_write_pipeline_for_etfs()` (v0.7.0) for a list of ETFs in one session with isolated per-ETF failure handling.
- **A CLI** (v0.14.0-v0.17.0) — `etf analyze`, `etf update`, `etf status`, `etf rank`, `etf compare`, `etf history`. Every command is orchestration-only: resolve required identifiers via existing repository lookups, call exactly one existing core function, format, print. No SQL, no calculation, no ranking logic anywhere in `adapters/cli/`. Every identifier is required on every command — no default scoring profile, no "latest" date, no automatic selection, on any of the six.
- **Trading calendar seeding** (`experiments/seed_trading_calendar.py`) — a one-time/occasional setup utility, not a CLI command and not a `core/` capability; populates real `Calendar`/`TradingSession` data via `exchange_calendars`.
- **Historical price backfill and scoring signal research** (`experiments/backfill_price_history.py`, `experiments/validate_scoring_signal.py`) — `experiments/`-only tooling; see "Scoring signal research" below for the actual finding.

Traced end to end: given a `ScoringProfile` and a `session_date`, the
system returns every ETF with a `Score` for that pair, ranked by
`overall_score` descending, each entry resolved to its ticker and
name — reachable now via `etf rank` directly, not only via a Python
call. That output can also be produced by a single composed write-side
call — `run_write_pipeline()` / `run_write_pipeline_for_etfs()` —
chaining ingest → SMA → RSI → score for one or many ETFs, reachable via
`etf update` for one ETF, or via the external, untagged
`experiments/daily_etf_universe_update.py` for a fixed multi-ETF
universe.

**A CLI now exists.** As of v0.14.0 this was the first entry point
outside the test suite; as of v0.17.0 it exposes six commands covering
every read-side analytics function built through v0.13.0 except
`screen_etfs()`/`get_top_candidates()` (criteria-based screening remains
CLI-unexposed — see Deferred capabilities). This closes the gap this
document previously described as "Nothing outside the test suite can
currently invoke any of this."

**Multiple concrete indicators are supported.** As of v0.8.0, three
indicators exist side by side as separate, explicit orchestration
functions — `calculate_sma()`, `calculate_rsi()`, and
`calculate_drawdown()` — each computing its own
`IndicatorDefinition`/`IndicatorValue` pair. Scoring consumes SMA/RSI
identically via `_resolve_dimension_values()`, with no branching on
which indicator it is; `calculate_drawdown()` is deliberately not wired
into scoring at all (max_drawdown is a comparison metric, never a
`Dimension`). `run_write_pipeline()` still calls SMA and RSI explicitly
by name; no indicator-name dispatch mechanism has been built despite
three concrete cases now existing (see Activation triggers below — this
trigger's literal condition has fired, but no caller has ever needed
dynamic selection).

## Scoring signal research

Run once, so far, using
`experiments/validate_scoring_signal.py` (commit `cae13e7`) against
real Yahoo Finance data:

| Parameter | Value |
|---|---|
| Scoring profile | REFERENCE v1 |
| ETF universe | 25 |
| Period | 2024-07-17 to 2026-07-17 |
| Forward return horizon | 20 trading days |
| Ranking dates observed | 463 |
| Top bucket | top 5 ranked ETFs per date |
| Bottom bucket | bottom 5 ranked ETFs per date |
| Top bucket average forward return | ~+1.717% |
| Bottom bucket average forward return | ~+1.486% |
| Difference (top − bottom) | **+0.00231054291724640766004162231 (~+0.231%)** |

This is an observed measurement over a limited historical sample. It
does not confirm, validate, or prove predictive value, and this
document does not describe it as such. Disclosed limitations, carried
from the tooling's own output:

- Observations are not independent — rankings move slowly and forward
  windows overlap, so the effective sample size behind 463 observed
  dates is materially smaller than 463.
- This represents one historical regime only (2024-2026); the result
  does not generalize beyond it.
- The 25-ETF universe was selected from currently existing,
  currently-liquid ETFs, so the result carries survivorship bias.

**Why this matters for this document specifically:** a weak,
inconclusive measurement is not, on its own, evidence that further
scoring-methodology work (a v2 profile, a richer factor taxonomy, or
promoting `validate_scoring_signal.py`'s logic into a `core/`
capability) is justified. Per this document's own Abstraction
discipline and Activation triggers below, a materially different
result — not merely a repeat run — would be the kind of concrete
second data point that could justify revisiting this question. See
Recommended next action.

## Architectural guarantees

**Domain purity.** Calculation modules (`calculations.py`, `score_calculation.py`, `ranking.py`) have no database access, no `Clock` dependency, no randomness. Output is a deterministic function of their inputs alone.

**Repository responsibility.** Repositories execute SQL and nothing else — they do not commit, and they do not contain business rules (sorting, ranking, or validation logic stays in the domain/orchestration layers). Transaction ownership belongs to orchestration layers (`run_pipeline` and its callers), never to the repository functions themselves. The CLI (v0.14.0-v0.17.0) does not weaken this: `adapters/cli/main.py` contains zero SQL and zero `conn.execute()` calls — every command resolves identifiers via existing repository/core functions only. Neither does the `experiments/` tooling added since v0.17.0: `seed_trading_calendar.py`, `backfill_price_history.py`, and `validate_scoring_signal.py` all call only existing, unmodified repository/core functions.

**Explicit transaction configuration (v0.4.1).** Every connection is opened with `isolation_level=""` explicitly (`core/market_data/persistence/database.py`) — behaviorally identical to sqlite3's own default, but now a stated, tested requirement rather than an implicit one. All of the above transactional guarantees are load-bearing on this specific mode; it is no longer possible to lose track of that dependency by reading the code alone.

**Versioning discipline.** A change to a calculation's logic or parameters creates a new `IndicatorDefinition` version or a new `ScoringProfile` version. Historical meaning is never mutated — an existing version's data always means what it meant when it was computed. Since v0.4.1, `IndicatorDefinition.parameters` and `ScoringProfile.parameters` are validated at construction (`__post_init__`) to be exactly the canonical, sort-keys form `serialize_parameters()` produces — not just built that way by convention. Malformed JSON or a non-canonical (but validly parseable) serialization is rejected immediately with `ValueError`, the same pattern `Money` already used for its own invariants. The indicator integrity fix (`cebd5b0`/`67d9e90`) is consistent with this: it changed *when* a value is computed (never for a non-trading date), not *what* an already-computed, already-stored historical value means — no existing `IndicatorValue` row's meaning was altered.

**Immutable history.** `PriceBar`, `IndicatorValue`, `Score`, and `DimensionScore` are insert-only. This is enforced by SQLite `BEFORE UPDATE`/`BEFORE DELETE` triggers, not just by convention or code discipline. One concrete consequence surfaced by the indicator integrity fix: the `IndicatorValue` rows already written for non-trading dates before the fix (e.g. an SMA value dated to a Saturday, duplicating the prior real trading day's value) cannot be deleted or corrected — insert-only means exactly that. They are harmless (no `Score` was ever computed from them, since `calculate_score()` already had the guard) and will simply age out of relevance as real trading days accumulate around them, but they are a permanent, if inert, record of the pre-fix behavior.

**Interface stability.** Repository interfaces are considered stable once proven. New functionality should preferably be added alongside existing interfaces (a new function) rather than by modifying an established one, unless a concrete requirement demonstrates that modification is necessary. Every repository extension across Phases 1-5 and every v0.5.0-v0.17.0 release has followed this: existing functions were never altered, only new ones added beside them. The one internal refactor (v0.9.0 extracted `generate_ranked_etf_report()`'s per-ETF resolution logic into shared private helpers) changed no public interface's behavior, proven by every pre-existing test for it passing unmodified. The indicator integrity fix is the first *behavior* change (not interface change) to an established function since this baseline was frozen at v0.4.0 — `calculate_sma()`/`calculate_rsi()`/`calculate_drawdown()`'s signatures are unchanged; what changed is that a case (`session_date` not a trading day) that previously produced an incorrect side effect now correctly no-ops, matching the sibling function (`calculate_score()`) that already handled it correctly.

**Migration discipline.** Migrations remain additive only: `0001`-`0003` are frozen, and no new migration file has shipped since v0.3.0-era — every capability added from v0.5.0 through v0.17.0, plus all four commits since, was delivered without a single schema change. Existing migrations are never rewritten.

**Abstraction discipline.** New abstractions require a second concrete use case, not a plausible first one, and are still held to that bar even once a third case exists. Examples: a second concrete indicator (RSI, v0.5.0) was added *without* introducing an indicator registry or dispatch mechanism; a third (MAX_DRAWDOWN, v0.8.0) still hasn't triggered one — `calculate_sma`/`calculate_rsi`/`calculate_drawdown` simply coexist as explicit functions, because no caller has ever needed to select between them dynamically at runtime (see Activation triggers). Screening/comparison (v0.10.0-v0.12.0) let a caller pass an ad hoc `candidate_etf_ids` list to rank within a subset — satisfying every observed "rank within a subset" need so far without ever needing the reserved, still-unused `UniverseId`/named-Universe concept; the v0.6.0 write-pipeline composer calls both original indicators explicitly by name for the same reason, introducing no dispatch mechanism and no `ProviderRegistry` activation (it takes a `DataProvider` directly, exactly as `ingest_daily_prices()` already did); the CLI (v0.14.0-v0.17.0) added exactly six commands across four releases and no config framework, no bootstrap/init/seed command, and no batch command — `experiments/daily_etf_universe_update.py`'s own bootstrap for ETF/IndicatorDefinition/ScoringProfile records stayed external to the platform for the same reason; no Portfolio domain was built before a portfolio requirement existed. The same discipline held for the calendar-correctness and historical-research problems solved since v0.17.0: both were solved as `experiments/` tooling, not as new `core/` abstractions, because in each case the only demonstrated consumer was a research need, not a production one — see the earlier `tools/` vs. `experiments/` architecture review that established this precedent explicitly.

## Deferred capabilities

Not implemented, and why each is deferred rather than simply forgotten:

- **API** — no external consumer has ever been named or discovered. A CLI exists (below); an API is still a different, undemonstrated thing.
- ~~**CLI**~~ — **built, v0.14.0-v0.17.0.** Six commands: `analyze`, `update`, `status`, `rank`, `compare`, `history`. See Current capabilities above.
- **Bootstrap/init/seed CLI command** — creating a `Calendar`/`TradingSession`/`ETF`/`IndicatorDefinition`/`ScoringProfile` from the CLI remains unbuilt; the README still documents this as done "via the repository functions," same as before v0.14.0. `experiments/daily_etf_universe_update.py` does its own ETF/IndicatorDefinition/ScoringProfile bootstrap, but deliberately not a Calendar/TradingSession one. As of `ad82395`, calendar seeding specifically now has a real answer — `experiments/seed_trading_calendar.py` — but it is tooling, not a CLI command; the underlying trigger (a demonstrated need to do this without writing Python, from the CLI itself) has still not fired.
- **CLI exposure of `screen_etfs()`/`get_top_candidates()`** — criteria-based screening (v0.10.0/v0.11.0) has no CLI command as of v0.17.0; only `rank` (no filtering) and `compare` (an explicit caller-supplied set, no criteria) are exposed. No evidence of a recurring, CLI-blocked filtering need has been demonstrated yet, as distinct from the visibility gap `rank`/`compare` closed.
- **Dashboard consumer** — no consumer requirement exists.
- **Scheduler** — no demonstrated need for automated (recurring/cron-style) execution; `experiments/daily_etf_universe_update.py` is explicitly documented as safe to run under an external scheduler (cron, Windows Task Scheduler) without the platform installing or managing one itself.
- **Portfolio domain** — `PortfolioId`/`HoldingId` have been reserved in `core/shared/ids.py` since Phase 0 and remain unused anywhere in `core/`, `adapters/`, or `experiments/`; no portfolio requirement has been demonstrated.
- **Universe filtering** — `UniverseId` has been reserved since Phase 0 and remains unused anywhere in `core/`, `adapters/`, or `experiments/`. Ad hoc `candidate_etf_ids` lists (`screen_etfs()`/`compare_etfs()`, v0.10.0/v0.12.0) already satisfy every "rank within a subset" need observed so far without a persisted, named grouping — no requirement for one has been demonstrated.
- **Ranking persistence** — rankings are recomputed on demand from immutable `Score` rows on every `rank`/`compare`/`analyze` call (and, as of `cae13e7`, on every historical date the scoring signal research tooling replays); no measured latency or scale problem justifies caching them.
- **Indicator registry/dispatch** — three concrete indicators now exist (SMA, RSI, MAX_DRAWDOWN as of v0.8.0), each its own explicit orchestration function (`calculate_sma`, `calculate_rsi`, `calculate_drawdown`); no caller has needed to select between them dynamically at runtime, so a name→function dispatch mechanism remains unbuilt. See Activation triggers — the letter of the "third indicator" trigger has fired, but its consequence was judged not yet warranted, the same call made at the second indicator.
- **`ProviderRegistry` activation** — `ProviderRegistry` (Phase 1) remains an explicit, unused-by-any-orchestration-function dict-backed registry (it has its own isolated unit tests, but no caller); `ingest_daily_prices()`, `run_write_pipeline()`, `run_write_pipeline_for_etfs()`, and the CLI's `update` command all take/construct a `DataProvider` directly, never a registry lookup. No concrete need to select a provider dynamically at runtime has been demonstrated. `backfill_price_history.py` (`cae13e7`) reinforces this: it also constructs `YahooFinanceProvider` directly.
- **Configuration system** — `config/` remains an empty package; nothing yet needs runtime configuration beyond a database path. `experiments/daily_etf_universe_update.py` reinforced this by deliberately declining to introduce one, using plain Python constants instead; every script added since (`seed_trading_calendar.py`, `backfill_price_history.py`, `validate_scoring_signal.py`) has followed the same pattern.
- **A validated, actionable scoring signal** — the first scoring signal research measurement (`cae13e7`, see above) was weak and inconclusive, not a demonstrated predictive signal. This is not deferred the way an unbuilt feature is deferred — it is an open empirical question this document does not resolve and does not claim to have resolved.

## Activation triggers

What would justify resuming implementation, and what it would justify —
not before, and not more than the trigger warrants:

| Trigger | Justified consequence |
|---|---|
| ~~A second real indicator (e.g. SMA + RSI) with an actual calculation requirement~~ — **fired at v0.5.0** (SMA + RSI both exist) | Not, on its own, an indicator name→function dispatch mechanism — two concrete cases were judged insufficient evidence to build one. See below for what would still justify it. |
| ~~A third real indicator, or a concrete need to select between indicators dynamically at runtime~~ — **fired at v0.8.0** (SMA + RSI + MAX_DRAWDOWN all exist) | Not, on its own, a dispatch mechanism — three concrete cases are still judged insufficient evidence; no caller has ever needed dynamic selection. A dispatch mechanism now requires a demonstrated dynamic-selection need specifically, not merely a further indicator count. |
| ~~A concrete requirement for automated, composed execution of ingest→indicator→score~~ — **fired at v0.6.0** (`run_write_pipeline()` exists) | Not, on its own, a scheduler, an API/CLI, or dynamic dispatch — orchestration composition alone was judged sufficient scope for v0.6.0. See below for what would still justify each of those. |
| ~~A named external consumer (API, dashboard, another service) requesting this data~~ — **partially fired at v0.14.0-v0.17.0**: the consumer that appeared was a CLI operator, not an API/dashboard/service consumer | A CLI, shaped around exactly what an interactive operator needs (six commands, every identifier required, no defaults) — not, on its own, an API boundary, a dashboard, or a bootstrap/config/batch surface. A distinct API/dashboard/service consumer would still need to appear to justify those specifically. |
| ~~A demonstrated correctness gap in trading-calendar handling~~ — **fired via real evidence** (the naive weekday heuristic mismarked Juneteenth and the pre-July-4th half day as trading days, and separately, the unguarded SMA/RSI/MAX_DRAWDOWN functions produced a duplicate value for a real Saturday) | Not a `core/` `CalendarProvider` abstraction and not a CLI bootstrap command — the calendar gap was closed as `experiments/` tooling (`ad82395`), and the indicator gap was closed as a narrow, existing-pattern `core/` bug fix (`cebd5b0`/`67d9e90`), matching the smallest fix that addressed the actual, demonstrated defect in each case. |
| A concrete need to score holdings or allocations, not just standalone ETFs | A Portfolio domain, using the already-reserved `PortfolioId`/`HoldingId` |
| A concrete need to persist a named, reusable subset of ETFs, beyond what an ad hoc `candidate_etf_ids` list (v0.10.0-v0.12.0) already provides per call | A Universe concept, using the already-reserved `UniverseId` |
| A demonstrated need for automated (recurring/cron-style) daily execution | A scheduler — the write-side composition it would schedule already exists (`run_write_pipeline()`/`run_write_pipeline_for_etfs()`), and an external, schedulable caller already exists (`experiments/daily_etf_universe_update.py`), but automated triggering itself remains undemonstrated |
| A demonstrated latency/scale problem with on-demand ranking | Persisted/cached derived data — only with a measured problem, not a hypothetical one |
| A concrete need to select a `DataProvider` dynamically at runtime rather than passing one directly | `ProviderRegistry` activation inside `ingest_daily_prices()`/`run_write_pipeline()`/the CLI's `update` command — the registry itself has existed, unused by orchestration, since Phase 1 |
| A recurring, demonstrated need to filter/screen ETFs from the CLI, distinct from the visibility gap `rank`/`compare` (v0.17.0) already closed | CLI exposure of `screen_etfs()`/`get_top_candidates()`, most likely requiring new argument-parsing work for `ETFScreeningCriteria` (a `dict[Dimension, Decimal]` field has no existing CLI-argument precedent in this codebase) |
| A concrete, demonstrated need to create a Calendar/ETF/IndicatorDefinition/ScoringProfile without writing Python, beyond what `experiments/daily_etf_universe_update.py`'s own internal bootstrap and `experiments/seed_trading_calendar.py`'s tooling already cover | A bootstrap/init/seed capability — scope (CLI command vs. standalone tool) still an open question, not decided by this document |
| A materially different scoring signal research result — not merely a repeat run of the same measurement, but a different scoring profile, a longer/different historical window, or a result whose magnitude clears its own overlapping-observation and single-regime caveats | The kind of second concrete data point that could justify revisiting whether `validate_scoring_signal.py`'s logic belongs in `core/`, or whether a new scoring methodology is worth building — not justified by the first, weak, inconclusive measurement alone |

## Known limitations

- Two pre-existing Phase 0 guard clauses remain uncovered by any test: `insert_price_bar`'s OHLC-currency-mismatch check and `complete_ingestion_run`'s terminal-status check (`core/market_data/persistence/repository.py:124,212`). Neither is a defect; both are defensive code paths no test has exercised.
- `Money.__le__`/`__gt__` are implemented but not directly exercised by any test (`core/shared/money.py:48-49,52-53`) — `__lt__`/`__ge__`/`__eq__` are, and all four comparisons share one implementation pattern, but this is an honest gap, not an assumption.
- `migrations.py`'s already-applied-migration skip branch is never exercised, since every test starts from a fresh, unmigrated database.
- `adapters/cli/main.py` has four uncovered lines, unchanged since v0.17.0 (none of the four commits since touched `adapters/`): the success-path return of `_resolve_optional_risk_definition_id()` (line 463), `etf compare`'s risk-error branch (lines 523-524), the argparse-unreachable `AssertionError` (line 586), and the `if __name__ == "__main__":` guard (line 590). None are defects; all are exercised manually or by a sibling command's equivalent test, just not by an automated test for every command that shares the helper.
- `core/analytics/indicator_calculation.py` is at 100% coverage including the three new non-trading-day guards (`cebd5b0`/`67d9e90`) — no new gap introduced by the fix.
- Overall coverage (current): 314/314 tests passing, 1084/1095 statements covered (99%) across `core/` and `adapters/`. Every line in every Phase 1-5 module, every v0.4.1-v0.13.0 change, `adapters/cli/formatting.py`, and `core/analytics/indicator_calculation.py` (including the new guards) is at 100%. `adapters/cli/main.py` is at 98% (the four lines above, unchanged since v0.17.0); `core/market_data/persistence/repository.py` and `core/shared/money.py` carry the two pre-existing gaps noted above, both predating this baseline. `experiments/` scripts (`daily_etf_universe_update.py`, `seed_trading_calendar.py`, `backfill_price_history.py`, `validate_scoring_signal.py`) are deliberately outside this coverage measurement — none are part of the platform (see `experiments/README.md`), and each was verified by direct execution against real data rather than by an added test suite, per that directory's established convention.
- None of the above are introduced by, or specific to, Phase 0-5 of this project — all predate or are orthogonal to the original baseline's scope; the `adapters/cli/main.py` gaps are the only ones genuinely introduced since v0.6.0, unchanged by anything since v0.17.0, and none are hidden here.

## Versioning assessment

Not yet decided: whether `cebd5b0`/`67d9e90` (the indicator integrity
fix) should be tagged as `v0.17.1`, following the `v0.15.1`/`v0.15.2`
precedent (bug-fix-only patch releases confined to one file family,
found via real execution, each re-verified against real data). No tag
has been created.

**Recommendation: yes, `v0.17.1` is appropriate**, for the same reasons
`v0.15.1`/`v0.15.2` were tagged and the two `experiments/`-only commits
(`ad82395`, `cae13e7`) were not:

- It changes `core/` behavior (`calculate_sma()`, `calculate_rsi()`,
  `calculate_drawdown()`), unlike the calendar and research-tooling
  commits, which are `experiments/`-only and correctly stay untagged,
  matching how `experiments/daily_etf_universe_update.py` itself
  (`0e06fdd`) was never tagged either.
- It is a genuine correctness fix to already-shipped behavior, not a
  new capability — the same shape as `v0.15.1`/`v0.15.2`
  (transport/parse error translation, User-Agent fix), not the shape
  of a `v0.X.0` capability release.
- It was found via real execution against real data (running the
  actual daily runner on a real Saturday), re-verified the same way
  after the fix — matching `v0.15.1`/`v0.15.2`'s own discovery and
  verification method exactly, not a hypothetical or theoretical
  concern.
- Suggested release title: **`v0.17.1 — Indicator Non-Trading-Day
  Guard Fix`**.

Not recommended: tagging `ad82395` or `cae13e7`. Both are
`experiments/`-only, add no `core/`/`adapters/` capability, and follow
the same precedent that already left `daily_etf_universe_update.py`
untagged — tagging them would be inconsistent with that precedent, not
consistent with it.

This section records the recommendation only; creating the tag is a
separate, deliberate action for whoever maintains the release history,
not performed by this document.

## Recommended next action

None, in the sense of new capability work. The four commits since
v0.17.0 closed two real, evidenced gaps (trading-calendar correctness,
now solved as tooling; an indicator correctness bug, now fixed in
`core/`) and produced the platform's first scoring signal research
measurement — which came back weak and inconclusive, not as
confirmation that further scoring-methodology investment is justified.
Per this document's own Abstraction discipline, a weak result is not,
on its own, a trigger for a v2 scoring profile, a richer factor
taxonomy, or promoting research logic into `core/`. Wait for one of
the activation triggers above to occur for real — including a
materially different scoring signal research result — then scope the
next phase around that specific trigger, not around the assumption
that more research automatically calls for more building. Separately,
apply (or explicitly decline) the `v0.17.1` tag recommendation above
so the tagged release history matches the repository's actual state.
