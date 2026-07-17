# Analytics Engine Baseline Status

This document is a snapshot, not a proposal. It records the state of the
project through v0.17.0 (the CLI research interface expansion release),
why each pause point was considered complete for its scope, and what
would have to become true before further implementation is justified.
See `docs/ARCHITECTURE_DECISIONS.md` for the detailed rationale behind
individual decisions referenced here, and
`docs/V0_6_0_DESIGN_WRITE_PIPELINE_COMPOSITION.md` for the v0.6.0 design
review that release implemented.

## Version / state

**v0.17.0 is the current stable baseline.** Architecture remains exactly
as frozen at v0.4.0 (see below); every release from v0.5.0 through
v0.17.0 has added capability strictly within it — no repository,
migration, scoring, or transaction module has changed since v0.4.0 to
deliver any of them. Migrations are still exactly `0001`-`0003`, frozen
since v0.3.0-era; no new migration file has ever shipped since.

Since this document was last updated at v0.6.0, eleven further releases
shipped, in three groups:

- **v0.7.0-v0.13.0 — read-side analytics capability**, entirely inside
  `core/analytics/ranked_report.py`: batch write-side execution across a
  list of ETFs (`run_write_pipeline_for_etfs()`, v0.7.0), a risk
  comparison metric (`max_drawdown()`/`calculate_drawdown()`, v0.8.0), a
  single-ETF analysis report (`generate_etf_analysis_report()`, v0.9.0),
  explicit-criteria screening (`screen_etfs()`, v0.10.0), a bounded
  shortlist over screening (`get_top_candidates()`, v0.11.0), named
  comparison (`compare_etfs()`, v0.12.0), and historical score retrieval
  (`get_score_history()`, v0.13.0). None of these changed a migration, a
  repository's SQL, the scoring methodology, or the `Dimension` enum;
  each is either new orchestration over existing repository queries or a
  thin composition over the read-side function immediately before it
  (`get_top_candidates()` over `screen_etfs()`; `compare_etfs()` over
  `screen_etfs()`).
- **v0.14.0-v0.16.0 — the first CLI**, `adapters/cli/main.py`: `etf
  analyze` (v0.14.0, one command), then a subcommand dispatcher plus `etf
  update` (v0.15.0), then `etf status` (v0.16.0). v0.15.1/v0.15.2 were
  two production-incident fixes confined entirely to
  `core/market_data/providers/yahoo_finance.py` (Yahoo Finance rejecting
  the default `urllib` User-Agent, and translating transport/parse
  failures into the existing `ProviderError`), found via real smoke
  tests against real Yahoo Finance data, not simulated.
- **v0.17.0 — CLI exposure of the read-side analytics capability** built
  in v0.7.0-v0.13.0: three new commands, `etf rank`, `etf compare`, `etf
  history`, wrapping `generate_ranked_etf_report()`, `compare_etfs()`,
  and `get_score_history()` respectively. No change to
  `core/analytics/ranked_report.py` or any other core module.

Separately, an **external, untagged experiment runner**
(`experiments/daily_etf_universe_update.py`, commit `0e06fdd`) was added
between v0.16.0 and v0.17.0. It is explicitly not a platform feature: it
lives outside `core/`/`adapters/`, is not part of the CLI, and its own
`experiments/README.md` documents why it deliberately does not generate
its own trading calendar (calendar/`TradingSession` content is treated
as market-data domain truth, not experiment-owned configuration). It is
the first real, external, non-test caller of `run_write_pipeline_for_etfs()`
(v0.7.0) against real Yahoo Finance data across a 25-ETF universe.

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

## Current capabilities

The system now supports: price ingestion, three indicators (SMA, RSI,
MAX_DRAWDOWN), generic scoring, ranking, screening, comparison,
historical score retrieval, composed single- and multi-ETF write
execution, and a six-command CLI exposing most of the read-side
capability.

- **Immutable market history** — price data is ingested once and never altered; corrections are new records, never edits.
- **Versioned indicators** — indicator values are computed deterministically and tied to a specific, immutable `IndicatorDefinition` version. Three concrete indicators now exist (SMA, RSI, MAX_DRAWDOWN), each its own explicit orchestration function — see Abstraction discipline below for why this still hasn't triggered a dispatch mechanism.
- **Deterministic scoring** — `Score`/`DimensionScore` are a pure, reproducible function of immutable indicator data and a versioned `ScoringProfile`.
- **ETF ranking** — cross-ETF `Score` retrieval with deterministic ordering and a stable, explicit tie-break.
- **Ranked report generation** — `generate_ranked_etf_report()` composes retrieval, ranking, and ETF-identity resolution into one usable report for a given `(scoring_profile_id, session_date)`, with an optional `max_drawdown` comparison metric (v0.8.0).
- **Single-ETF analysis** — `generate_etf_analysis_report()` (v0.9.0): one ETF's full report plus its rank/peer_count among the same profile/session's peers.
- **Screening and shortlisting** — `screen_etfs()`/`get_top_candidates()` (v0.10.0/v0.11.0): explicit, caller-supplied criteria only, never a built-in default; ranks are always local and gapless among survivors.
- **Named comparison** — `compare_etfs()` (v0.12.0): a specific caller-supplied set of ETFs, ranked locally among just themselves.
- **Historical score retrieval** — `get_score_history()` (v0.13.0): one ETF's own Score history over time, read-only, no recalculation.
- **Composed write-side execution** — `run_write_pipeline()` (v0.6.0) for one ETF/session, and `run_write_pipeline_for_etfs()` (v0.7.0) for a list of ETFs in one session with isolated per-ETF failure handling.
- **A CLI** (v0.14.0-v0.17.0) — `etf analyze`, `etf update`, `etf status`, `etf rank`, `etf compare`, `etf history`. Every command is orchestration-only: resolve required identifiers via existing repository lookups, call exactly one existing core function, format, print. No SQL, no calculation, no ranking logic anywhere in `adapters/cli/`. Every identifier is required on every command — no default scoring profile, no "latest" date, no automatic selection, on any of the six.

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

## Architectural guarantees

**Domain purity.** Calculation modules (`calculations.py`, `score_calculation.py`, `ranking.py`) have no database access, no `Clock` dependency, no randomness. Output is a deterministic function of their inputs alone.

**Repository responsibility.** Repositories execute SQL and nothing else — they do not commit, and they do not contain business rules (sorting, ranking, or validation logic stays in the domain/orchestration layers). Transaction ownership belongs to orchestration layers (`run_pipeline` and its callers), never to the repository functions themselves. The CLI (v0.14.0-v0.17.0) does not weaken this: `adapters/cli/main.py` contains zero SQL and zero `conn.execute()` calls — every command resolves identifiers via existing repository/core functions only.

**Explicit transaction configuration (v0.4.1).** Every connection is opened with `isolation_level=""` explicitly (`core/market_data/persistence/database.py`) — behaviorally identical to sqlite3's own default, but now a stated, tested requirement rather than an implicit one. All of the above transactional guarantees are load-bearing on this specific mode; it is no longer possible to lose track of that dependency by reading the code alone.

**Versioning discipline.** A change to a calculation's logic or parameters creates a new `IndicatorDefinition` version or a new `ScoringProfile` version. Historical meaning is never mutated — an existing version's data always means what it meant when it was computed. Since v0.4.1, `IndicatorDefinition.parameters` and `ScoringProfile.parameters` are validated at construction (`__post_init__`) to be exactly the canonical, sort-keys form `serialize_parameters()` produces — not just built that way by convention. Malformed JSON or a non-canonical (but validly parseable) serialization is rejected immediately with `ValueError`, the same pattern `Money` already used for its own invariants.

**Immutable history.** `PriceBar`, `IndicatorValue`, `Score`, and `DimensionScore` are insert-only. This is enforced by SQLite `BEFORE UPDATE`/`BEFORE DELETE` triggers, not just by convention or code discipline.

**Interface stability.** Repository interfaces are considered stable once proven. New functionality should preferably be added alongside existing interfaces (a new function) rather than by modifying an established one, unless a concrete requirement demonstrates that modification is necessary. Every repository extension across Phases 1-5 and every v0.5.0-v0.17.0 release has followed this: existing functions were never altered, only new ones added beside them. The one internal refactor (v0.9.0 extracted `generate_ranked_etf_report()`'s per-ETF resolution logic into shared private helpers) changed no public interface's behavior, proven by every pre-existing test for it passing unmodified.

**Migration discipline.** Migrations remain additive only: `0001`-`0003` are frozen, and no new migration file has shipped since v0.3.0-era — every capability added from v0.5.0 through v0.17.0 (nine indicator/analytics releases, a CLI, and an external experiment runner) was delivered without a single schema change. Existing migrations are never rewritten.

**Abstraction discipline.** New abstractions require a second concrete use case, not a plausible first one, and are still held to that bar even once a third case exists. Examples: a second concrete indicator (RSI, v0.5.0) was added *without* introducing an indicator registry or dispatch mechanism; a third (MAX_DRAWDOWN, v0.8.0) still hasn't triggered one — `calculate_sma`/`calculate_rsi`/`calculate_drawdown` simply coexist as explicit functions, because no caller has ever needed to select between them dynamically at runtime (see Activation triggers). Screening/comparison (v0.10.0-v0.12.0) let a caller pass an ad hoc `candidate_etf_ids` list to rank within a subset — satisfying every observed "rank within a subset" need so far without ever needing the reserved, still-unused `UniverseId`/named-Universe concept; the v0.6.0 write-pipeline composer calls both original indicators explicitly by name for the same reason, introducing no dispatch mechanism and no `ProviderRegistry` activation (it takes a `DataProvider` directly, exactly as `ingest_daily_prices()` already did); the CLI (v0.14.0-v0.17.0) added exactly six commands across four releases and no config framework, no bootstrap/init/seed command, and no batch command — `experiments/daily_etf_universe_update.py`'s own bootstrap for ETF/IndicatorDefinition/ScoringProfile records stayed external to the platform for the same reason; no Portfolio domain was built before a portfolio requirement existed.

## Deferred capabilities

Not implemented, and why each is deferred rather than simply forgotten:

- **API** — no external consumer has ever been named or discovered. A CLI exists (below); an API is still a different, undemonstrated thing.
- ~~**CLI**~~ — **built, v0.14.0-v0.17.0.** Six commands: `analyze`, `update`, `status`, `rank`, `compare`, `history`. See Current capabilities above.
- **Bootstrap/init/seed CLI command** — creating a `Calendar`/`TradingSession`/`ETF`/`IndicatorDefinition`/`ScoringProfile` from the CLI remains unbuilt; the README still documents this as done "via the repository functions," same as before v0.14.0. `experiments/daily_etf_universe_update.py` does its own ETF/IndicatorDefinition/ScoringProfile bootstrap, but deliberately not a Calendar/TradingSession one (see that directory's README for why), and that script is explicitly not a platform feature.
- **CLI exposure of `screen_etfs()`/`get_top_candidates()`** — criteria-based screening (v0.10.0/v0.11.0) has no CLI command as of v0.17.0; only `rank` (no filtering) and `compare` (an explicit caller-supplied set, no criteria) are exposed. No evidence of a recurring, CLI-blocked filtering need has been demonstrated yet, as distinct from the visibility gap `rank`/`compare` closed.
- **Dashboard consumer** — no consumer requirement exists.
- **Scheduler** — no demonstrated need for automated (recurring/cron-style) execution; `experiments/daily_etf_universe_update.py` is explicitly documented as safe to run under an external scheduler (cron, Windows Task Scheduler) without the platform installing or managing one itself.
- **Portfolio domain** — `PortfolioId`/`HoldingId` have been reserved in `core/shared/ids.py` since Phase 0 and remain unused anywhere in `core/`, `adapters/`, or `experiments/`; no portfolio requirement has been demonstrated.
- **Universe filtering** — `UniverseId` has been reserved since Phase 0 and remains unused anywhere in `core/`, `adapters/`, or `experiments/`. Ad hoc `candidate_etf_ids` lists (`screen_etfs()`/`compare_etfs()`, v0.10.0/v0.12.0) already satisfy every "rank within a subset" need observed so far without a persisted, named grouping — no requirement for one has been demonstrated.
- **Ranking persistence** — rankings are recomputed on demand from immutable `Score` rows on every `rank`/`compare`/`analyze` call; no measured latency or scale problem justifies caching them.
- **Indicator registry/dispatch** — three concrete indicators now exist (SMA, RSI, MAX_DRAWDOWN as of v0.8.0), each its own explicit orchestration function (`calculate_sma`, `calculate_rsi`, `calculate_drawdown`); no caller has needed to select between them dynamically at runtime, so a name→function dispatch mechanism remains unbuilt. See Activation triggers — the letter of the "third indicator" trigger has fired, but its consequence was judged not yet warranted, the same call made at the second indicator.
- **`ProviderRegistry` activation** — `ProviderRegistry` (Phase 1) remains an explicit, unused-by-any-orchestration-function dict-backed registry (it has its own isolated unit tests, but no caller); `ingest_daily_prices()`, `run_write_pipeline()`, `run_write_pipeline_for_etfs()`, and the CLI's `update` command all take/construct a `DataProvider` directly, never a registry lookup. No concrete need to select a provider dynamically at runtime has been demonstrated.
- **Configuration system** — `config/` remains an empty package; nothing yet needs runtime configuration beyond a database path. `experiments/daily_etf_universe_update.py` reinforced this by deliberately declining to introduce one, using plain Python constants instead.

## Activation triggers

What would justify resuming implementation, and what it would justify —
not before, and not more than the trigger warrants:

| Trigger | Justified consequence |
|---|---|
| ~~A second real indicator (e.g. SMA + RSI) with an actual calculation requirement~~ — **fired at v0.5.0** (SMA + RSI both exist) | Not, on its own, an indicator name→function dispatch mechanism — two concrete cases were judged insufficient evidence to build one. See below for what would still justify it. |
| ~~A third real indicator, or a concrete need to select between indicators dynamically at runtime~~ — **fired at v0.8.0** (SMA + RSI + MAX_DRAWDOWN all exist) | Not, on its own, a dispatch mechanism — three concrete cases are still judged insufficient evidence; no caller has ever needed dynamic selection. A dispatch mechanism now requires a demonstrated dynamic-selection need specifically, not merely a further indicator count. |
| ~~A concrete requirement for automated, composed execution of ingest→indicator→score~~ — **fired at v0.6.0** (`run_write_pipeline()` exists) | Not, on its own, a scheduler, an API/CLI, or dynamic dispatch — orchestration composition alone was judged sufficient scope for v0.6.0. See below for what would still justify each of those. |
| ~~A named external consumer (API, dashboard, another service) requesting this data~~ — **partially fired at v0.14.0-v0.17.0**: the consumer that appeared was a CLI operator, not an API/dashboard/service consumer | A CLI, shaped around exactly what an interactive operator needs (six commands, every identifier required, no defaults) — not, on its own, an API boundary, a dashboard, or a bootstrap/config/batch surface. A distinct API/dashboard/service consumer would still need to appear to justify those specifically. |
| A concrete need to score holdings or allocations, not just standalone ETFs | A Portfolio domain, using the already-reserved `PortfolioId`/`HoldingId` |
| A concrete need to persist a named, reusable subset of ETFs, beyond what an ad hoc `candidate_etf_ids` list (v0.10.0-v0.12.0) already provides per call | A Universe concept, using the already-reserved `UniverseId` |
| A demonstrated need for automated (recurring/cron-style) daily execution | A scheduler — the write-side composition it would schedule already exists (`run_write_pipeline()`/`run_write_pipeline_for_etfs()`), and an external, schedulable caller already exists (`experiments/daily_etf_universe_update.py`), but automated triggering itself remains undemonstrated |
| A demonstrated latency/scale problem with on-demand ranking | Persisted/cached derived data — only with a measured problem, not a hypothetical one |
| A concrete need to select a `DataProvider` dynamically at runtime rather than passing one directly | `ProviderRegistry` activation inside `ingest_daily_prices()`/`run_write_pipeline()`/the CLI's `update` command — the registry itself has existed, unused by orchestration, since Phase 1 |
| A recurring, demonstrated need to filter/screen ETFs from the CLI, distinct from the visibility gap `rank`/`compare` (v0.17.0) already closed | CLI exposure of `screen_etfs()`/`get_top_candidates()`, most likely requiring new argument-parsing work for `ETFScreeningCriteria` (a `dict[Dimension, Decimal]` field has no existing CLI-argument precedent in this codebase) |
| A concrete, demonstrated need to create a Calendar/ETF/IndicatorDefinition/ScoringProfile without writing Python, beyond what `experiments/daily_etf_universe_update.py`'s own internal bootstrap already covers for its fixed universe | A bootstrap/init/seed capability — scope (CLI command vs. standalone tool, and where trading-calendar truth should come from) still an open question, not decided by this document |

## Known limitations

- Two pre-existing Phase 0 guard clauses remain uncovered by any test: `insert_price_bar`'s OHLC-currency-mismatch check and `complete_ingestion_run`'s terminal-status check (`core/market_data/persistence/repository.py:124,212`). Neither is a defect; both are defensive code paths no test has exercised.
- `Money.__le__`/`__gt__` are implemented but not directly exercised by any test (`core/shared/money.py:48-49,52-53`) — `__lt__`/`__ge__`/`__eq__` are, and all four comparisons share one implementation pattern, but this is an honest gap, not an assumption.
- `migrations.py`'s already-applied-migration skip branch is never exercised, since every test starts from a fresh, unmigrated database.
- `adapters/cli/main.py` has two new uncovered lines as of v0.17.0: the success-path return of `_resolve_optional_risk_definition_id()` (line 463 — a valid `--risk-name`/`--risk-version` pair that actually resolves to an existing `IndicatorDefinition`, exercised for `rank` and `compare` manually but not by an automated test) and `etf compare`'s risk-error branch (lines 523-524 — `compare`'s equivalent of a test that does exist for `rank`). Neither is a defect: both paths are exercised by `rank`'s equivalent tests and by manual verification before release, but the automated suite doesn't cover them for every command that shares the helper. The two pre-existing lines at the bottom of the file (the argparse-unreachable `AssertionError`, and the `if __name__ == "__main__":` guard) are the same gap that has existed since v0.15.0, just shifted by new code above them.
- Overall coverage (as of v0.17.0): 311/311 tests passing, 1078/1089 statements covered (99%) across `core/` and `adapters/`. Every line in every Phase 1-5 module, every v0.4.1-v0.13.0 change, and `adapters/cli/formatting.py` is at 100%. `adapters/cli/main.py` is at 98% (the four lines above); `core/market_data/persistence/repository.py` and `core/shared/money.py` carry the two pre-existing gaps noted above, both predating this baseline. `experiments/daily_etf_universe_update.py` is deliberately outside this coverage measurement — it is explicitly not part of the platform (see its own README), and per its original scope was verified by direct execution against real Yahoo Finance data rather than by an added test suite.
- None of the above are introduced by, or specific to, Phase 0-5 of this project — all predate or are orthogonal to the original baseline's scope; the two new v0.17.0 lines are the only gaps genuinely introduced since v0.6.0, and neither is hidden here.

## Recommended next action

None. v0.17.0 closed the CLI-visibility gap for `generate_ranked_etf_report()`, `compare_etfs()`, and `get_score_history()` with CLI wiring only — no repository, migration, scoring, transaction, or `core/analytics` change, and no dispatch/`ProviderRegistry`/API/bootstrap/screening-CLI/portfolio/universe/scheduler work bundled in. Wait for one of the activation triggers above to occur for real, then scope the next phase around that specific trigger — not around the original roadmap's assumed continuation.
