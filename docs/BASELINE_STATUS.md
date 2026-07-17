# Analytics Engine Baseline Status

This document is a snapshot, not a proposal. It records the state of the
project through v0.6.0 (Phase 5's Ranked ETF Report, the v0.4.1 hardening
release, the v0.5.0 second-indicator capability release, and the v0.6.0
write-side pipeline composition release), why each pause point was
considered complete for its scope, and what would have to become true
before further implementation is justified. See
`docs/ARCHITECTURE_DECISIONS.md` for the detailed rationale behind
individual decisions referenced here, and
`docs/V0_6_0_DESIGN_WRITE_PIPELINE_COMPOSITION.md` for the v0.6.0 design
review this release implements.

## Version / state

**Baseline v0.4.0 — architecture frozen** for its current evidenced scope,
tagged and committed (superseding this document's earlier draft reference
to a `v1.0.0`/`analytics-engine-baseline-v1.0.0` naming that was not, in
the end, how the repository's existing `v0.x.0` tag convention was
followed). **v0.4.1** is a maintenance-only release on top of it: two
hardening fixes (explicit transaction configuration, enforced parameter
canonicalization — see Architectural guarantees below), no architecture
change, no new capability. **v0.5.0** is a capability addition after the
v0.4.1 baseline — a second concrete indicator (RSI), added beside SMA
with no changes to persistence, scoring, or migrations. **v0.6.0 is the
current stable development baseline** — the first capability addition on
the write side since v0.4.0: a single orchestration entry point,
`run_write_pipeline()`, composing the existing ingest → SMA → RSI →
score stages for one ETF and one trading session. Architecture remains
exactly as frozen at v0.4.0; v0.5.0 and v0.6.0 each add capability
strictly within it — no repository, migration, scoring, or transaction
module changed to deliver v0.6.0.

## Completed phases

- ✓ Phase 1 — Market Data
- ✓ Phase 2 — Indicators
- ✓ Phase 3 — Scoring Engine
- ✓ Phase 4 — Ranking Engine
- ✓ Phase 5 — Ranked ETF Report
- ✓ v0.5.0 — Second Concrete Indicator
- ✓ v0.6.0 — Write-side Pipeline Composition

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

## Current capabilities

The system now supports: price ingestion, multiple indicators (SMA +
RSI), generic scoring, ranking, and composed write-side execution.

- **Immutable market history** — price data is ingested once and never altered; corrections are new records, never edits.
- **Versioned indicators** — indicator values are computed deterministically and tied to a specific, immutable `IndicatorDefinition` version.
- **Deterministic scoring** — `Score`/`DimensionScore` are a pure, reproducible function of immutable indicator data and a versioned `ScoringProfile`.
- **ETF ranking** — cross-ETF `Score` retrieval with deterministic ordering and a stable, explicit tie-break.
- **Ranked report generation** — `generate_ranked_etf_report()` composes retrieval, ranking, and ETF-identity resolution into one usable, ETF-identity-resolved report for a given `(scoring_profile_id, session_date)`.
- **Composed write-side execution (v0.6.0)** — `run_write_pipeline()` composes `ingest_daily_prices()` → `calculate_sma()` → `calculate_rsi()` → `calculate_score()` into one orchestration entry point for a single ETF and trading session, closing the one gap this document previously flagged (below).

Traced end to end: given a `ScoringProfile` and a `session_date`, the
system returns every ETF with a `Score` for that pair, ranked by
`overall_score` descending, each entry resolved to its ticker and name.
That output can now be produced by a single composed call —
`run_write_pipeline()` — chaining ingest → SMA → RSI → score for one
ETF/session, in addition to each of the four underlying stages remaining
independently callable and independently tested exactly as before. As of
v0.5.0 this was described as "the one honest gap in an otherwise coherent
system": the write side was never chained together in any single
function, unlike the fully-composed read side (Phases 4-5). **v0.6.0
closes that gap** — orchestration only, no business logic moved between
layers, and no existing stage function was modified to do it.

**Multiple concrete indicators are supported.** As of v0.5.0, two
indicators exist side by side as separate, explicit orchestration
functions — `calculate_sma()` and `calculate_rsi()` — each computing its
own `IndicatorDefinition`/`IndicatorValue` pair. Scoring consumes both
identically: `_resolve_dimension_values()` resolves whichever indicator
name a `ScoringProfile` references generically, with no branching on
which indicator it is. `run_write_pipeline()` (v0.6.0) calls both
explicitly by name — `calculate_sma()` then `calculate_rsi()` — with no
indicator-name dispatch mechanism; two concrete indicators remain
judged-insufficient evidence to build one (see Abstraction discipline
below).

Nothing outside the test suite can currently invoke any of this. There is
still no entry point, CLI, API, or scheduler anywhere in the repository
— `run_write_pipeline()` is a plain function, callable directly, not
exposed through any of those.

## Architectural guarantees

**Domain purity.** Calculation modules (`calculations.py`, `score_calculation.py`, `ranking.py`) have no database access, no `Clock` dependency, no randomness. Output is a deterministic function of their inputs alone.

**Repository responsibility.** Repositories execute SQL and nothing else — they do not commit, and they do not contain business rules (sorting, ranking, or validation logic stays in the domain/orchestration layers). Transaction ownership belongs to orchestration layers (`run_pipeline` and its callers), never to the repository functions themselves.

**Explicit transaction configuration (v0.4.1).** Every connection is opened with `isolation_level=""` explicitly (`core/market_data/persistence/database.py`) — behaviorally identical to sqlite3's own default, but now a stated, tested requirement rather than an implicit one. All of the above transactional guarantees are load-bearing on this specific mode; it is no longer possible to lose track of that dependency by reading the code alone.

**Versioning discipline.** A change to a calculation's logic or parameters creates a new `IndicatorDefinition` version or a new `ScoringProfile` version. Historical meaning is never mutated — an existing version's data always means what it meant when it was computed. Since v0.4.1, `IndicatorDefinition.parameters` and `ScoringProfile.parameters` are validated at construction (`__post_init__`) to be exactly the canonical, sort-keys form `serialize_parameters()` produces — not just built that way by convention. Malformed JSON or a non-canonical (but validly parseable) serialization is rejected immediately with `ValueError`, the same pattern `Money` already used for its own invariants.

**Immutable history.** `PriceBar`, `IndicatorValue`, `Score`, and `DimensionScore` are insert-only. This is enforced by SQLite `BEFORE UPDATE`/`BEFORE DELETE` triggers, not just by convention or code discipline.

**Interface stability.** Repository interfaces are considered stable once proven. New functionality should preferably be added alongside existing interfaces (a new function) rather than by modifying an established one, unless a concrete requirement demonstrates that modification is necessary. Every repository extension across Phases 1-5 has followed this: existing functions were never altered, only new ones added beside them.

**Migration discipline.** As of this release, migrations are additive only: `0001`-`0003` are frozen, and every schema change since the first has shipped as a new file. Existing migrations are never rewritten.

**Abstraction discipline.** New abstractions require a second concrete use case, not a plausible first one. Examples already respected: a second concrete indicator (RSI, v0.5.0) was added *without* introducing an indicator registry or dispatch mechanism — two working implementations were judged insufficient evidence on their own, since `calculate_sma`/`calculate_rsi` simply coexist as explicit functions; the v0.6.0 write-pipeline composer calls both explicitly by name for the same reason, introducing no dispatch mechanism and no `ProviderRegistry` activation (it takes a `DataProvider` directly, exactly as `ingest_daily_prices()` already did); no Universe concept was built before a subset-ranking requirement existed; no Portfolio domain was built before a portfolio requirement existed.

## Deferred capabilities

Not implemented, and why each is deferred rather than simply forgotten:

- **API** — no external consumer has ever been named or discovered.
- **CLI** — same reason; nothing exists yet that would call it.
- **Dashboard consumer** — no consumer requirement exists.
- **Scheduler** — ~~no demonstrated need for automated execution, and it would have nothing coherent to schedule until the write-side composition below exists~~ — the write-side composition it would schedule now exists (`run_write_pipeline()`, v0.6.0), but no demonstrated need for *automated* (recurring/cron-style) execution has appeared; still deferred on that basis alone.
- **Portfolio domain** — `PortfolioId`/`HoldingId` have been reserved in `core/shared/ids.py` since Phase 0 but are still unused anywhere; no portfolio requirement has been demonstrated.
- **Universe filtering** — `UniverseId` has been reserved since Phase 0 but is still unused; no requirement to rank within a named subset has been demonstrated.
- **Ranking persistence** — rankings are recomputed on demand from immutable `Score` rows; no measured latency or scale problem justifies caching them.
- **Indicator registry/dispatch** — two concrete indicators exist since v0.5.0 (SMA, RSI), each its own explicit orchestration function (`calculate_sma`, `calculate_rsi`); no caller has needed to select between them dynamically at runtime, so a name→function dispatch mechanism remains unbuilt. The v0.6.0 write-pipeline composer reaffirms this rather than reopening it — it calls both explicitly by name, same as any other caller. Not built speculatively now — the concrete trigger to watch for is a third indicator or an actual dynamic-selection requirement.
- **`ProviderRegistry` activation** — `ProviderRegistry` (Phase 1) remains an explicit, unused-by-any-orchestration-function dict-backed registry; `ingest_daily_prices()` and `run_write_pipeline()` (v0.6.0) both take a `DataProvider` directly, never a registry lookup. No concrete need to select a provider dynamically at runtime has been demonstrated.
- **Configuration system** — `config/` remains an empty package; nothing yet needs runtime configuration beyond a database path.

## Activation triggers

What would justify resuming implementation, and what it would justify —
not before, and not more than the trigger warrants:

| Trigger | Justified consequence |
|---|---|
| ~~A second real indicator (e.g. SMA + RSI) with an actual calculation requirement~~ — **fired at v0.5.0** (SMA + RSI both exist) | Not, on its own, an indicator name→function dispatch mechanism — two concrete cases were judged insufficient evidence to build one. See below for what would still justify it. |
| A third real indicator, or a concrete need to select between indicators dynamically at runtime | An indicator name→function dispatch mechanism (e.g. `IndicatorCalculatorRegistry`) |
| ~~A concrete requirement for automated, composed execution of ingest→indicator→score~~ — **fired at v0.6.0** (`run_write_pipeline()` exists) | Not, on its own, a scheduler, an API/CLI, or dynamic dispatch — orchestration composition alone was judged sufficient scope for v0.6.0. See below for what would still justify each of those. |
| A named external consumer (API, dashboard, another service) requesting this data | An application-service or API boundary shaped around that consumer's actual needs |
| A concrete need to score holdings or allocations, not just standalone ETFs | A Portfolio domain, using the already-reserved `PortfolioId`/`HoldingId` |
| A concrete need to rank within a named subset of ETFs rather than all of them | A Universe concept, using the already-reserved `UniverseId` |
| A demonstrated need for automated (recurring/cron-style) daily execution | A scheduler — the write-side composition it would schedule already exists as of v0.6.0, but automated triggering itself remains undemonstrated |
| A demonstrated latency/scale problem with on-demand ranking | Persisted/cached derived data — only with a measured problem, not a hypothetical one |
| A concrete need to select a `DataProvider` dynamically at runtime rather than passing one directly | `ProviderRegistry` activation inside `ingest_daily_prices()`/`run_write_pipeline()` — the registry itself has existed, unused by orchestration, since Phase 1 |

## Known limitations

- Two pre-existing Phase 0 guard clauses remain uncovered by any test: `insert_price_bar`'s OHLC-currency-mismatch check and `complete_ingestion_run`'s terminal-status check (`core/market_data/persistence/repository.py:105,193`). Neither is a defect; both are defensive code paths no test has exercised.
- `Money.__le__`/`__gt__` are implemented but not directly exercised by any test (`core/shared/money.py:48-53`) — `__lt__`/`__ge__`/`__eq__` are, and all four comparisons share one implementation pattern, but this is an honest gap, not an assumption.
- `migrations.py`'s already-applied-migration skip branch is never exercised, since every test starts from a fresh, unmigrated database.
- Overall coverage (as of v0.6.0): 154/154 tests passing. Every line in every Phase 1-5 module, both v0.4.1 hardening changes, the v0.5.0 RSI addition, and the new v0.6.0 `core/analytics/write_pipeline.py` (25/25 statements) is at 100%. The pre-existing gaps above are the only lines in the whole codebase not at 100%, and none of them are touched by v0.6.0.
- None of the above are introduced by, or specific to, Phase 0-5 or v0.6.0 of this project — all predate or are orthogonal to this baseline's scope, and none are hidden here.

## Recommended next action

None. v0.6.0 fired the write-side composition trigger and closed it with orchestration only — no repository, migration, scoring, or transaction-module change, and no dispatch/`ProviderRegistry`/API/CLI/portfolio/universe work bundled in. Wait for one of the activation triggers above to occur for real, then scope the next phase around that specific trigger — not around the original roadmap's assumed continuation.
