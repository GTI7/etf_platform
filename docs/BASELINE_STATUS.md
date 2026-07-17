# Analytics Engine Baseline Status

This document is a snapshot, not a proposal. It records the state of the
project through v0.5.0 (Phase 5's Ranked ETF Report, the v0.4.1 hardening
release, and the v0.5.0 second-indicator capability release), why each
pause point was considered complete for its scope, and what would have to
become true before further implementation is justified. See
`docs/ARCHITECTURE_DECISIONS.md` for the detailed rationale behind
individual decisions referenced here.

## Version / state

**Baseline v0.4.0 — architecture frozen** for its current evidenced scope,
tagged and committed (superseding this document's earlier draft reference
to a `v1.0.0`/`analytics-engine-baseline-v1.0.0` naming that was not, in
the end, how the repository's existing `v0.x.0` tag convention was
followed). **v0.4.1** is a maintenance-only release on top of it: two
hardening fixes (explicit transaction configuration, enforced parameter
canonicalization — see Architectural guarantees below), no architecture
change, no new capability. **v0.5.0** is the current release: the first
capability addition after the v0.4.1 baseline — a second concrete
indicator (RSI), added beside SMA with no changes to persistence,
scoring, or migrations. Architecture remains exactly as frozen at v0.4.0;
v0.5.0 adds capability strictly within it.

## Completed phases

- ✓ Phase 1 — Market Data
- ✓ Phase 2 — Indicators
- ✓ Phase 3 — Scoring Engine
- ✓ Phase 4 — Ranking Engine
- ✓ Phase 5 — Ranked ETF Report
- ✓ v0.5.0 — Second Concrete Indicator

| Phase | Capability |
|---|---|
| 0 | Foundation: Money, Clock, typed IDs, SQLite/WAL, migrations, raw-data immutability, PipelineState |
| 1 | Market data: ETF storage, provider abstraction (Yahoo Finance), TradingCalendar-aware ingestion, immutable PriceBar |
| 2 | Indicators: IndicatorDefinition/IndicatorValue, versioned, immutable, two concrete indicators (SMA, RSI as of v0.5.0) |
| 3 | Scoring: ScoringProfile/Score/DimensionScore, versioned, immutable, deterministic |
| 4 | Ranking: cross-ETF Score retrieval, deterministic ranking, stable tie-break, read-only |
| 5 | Ranked ETF Report: composes Phase 4's pieces into one usable, ETF-identity-resolved report |
| 0.5.0 | Second Concrete Indicator: `rsi()` calculation and `calculate_rsi()` orchestration added beside SMA; the generic `IndicatorDefinition`/`IndicatorValue` architecture validated against two independent concrete implementations; SMA and RSI coexist and are consumed by scoring identically, with zero scoring-layer changes |

## Current capabilities

- **Immutable market history** — price data is ingested once and never altered; corrections are new records, never edits.
- **Versioned indicators** — indicator values are computed deterministically and tied to a specific, immutable `IndicatorDefinition` version.
- **Deterministic scoring** — `Score`/`DimensionScore` are a pure, reproducible function of immutable indicator data and a versioned `ScoringProfile`.
- **ETF ranking** — cross-ETF `Score` retrieval with deterministic ordering and a stable, explicit tie-break.
- **Ranked report generation** — `generate_ranked_etf_report()` composes retrieval, ranking, and ETF-identity resolution into one usable, ETF-identity-resolved report for a given `(scoring_profile_id, session_date)`.

Traced end to end: given a `ScoringProfile` and a `session_date`, the
system returns every ETF with a `Score` for that pair, ranked by
`overall_score` descending, each entry resolved to its ticker and name.
That output is produced from data written by three independent, atomic
write paths (ingest a price → compute an indicator → compute a score),
each callable on its own, each fully tested, but **never chained together
in any single function** — every phase's tests seed the previous stage's
data directly via repository inserts rather than by calling the previous
stage's real function. This is the one honest gap in an otherwise coherent
system: the read side (Phases 4-5) is fully composed into a usable
deliverable; the write side (Phases 1-3, and both indicators as of v0.5.0)
is not composed at all.

**Multiple concrete indicators are supported.** As of v0.5.0, two
indicators exist side by side as separate, explicit orchestration
functions — `calculate_sma()` and `calculate_rsi()` — each computing its
own `IndicatorDefinition`/`IndicatorValue` pair. Scoring consumes both
identically: `_resolve_dimension_values()` resolves whichever indicator
name a `ScoringProfile` references generically, with no branching on
which indicator it is. This is proof, not assumption, that the generic
`IndicatorDefinition`/`IndicatorValue` design and scoring's name-based
resolution both generalize correctly — no indicator-name dispatch
mechanism and no write-side pipeline composer have been built to get
here, and neither remains blocked on "can't generalize from one case"
now that two exist; both simply remain undemonstrated as needed.

Nothing outside the test suite can currently invoke any of this. There is
no entry point, CLI, API, or scheduler anywhere in the repository.

## Architectural guarantees

**Domain purity.** Calculation modules (`calculations.py`, `score_calculation.py`, `ranking.py`) have no database access, no `Clock` dependency, no randomness. Output is a deterministic function of their inputs alone.

**Repository responsibility.** Repositories execute SQL and nothing else — they do not commit, and they do not contain business rules (sorting, ranking, or validation logic stays in the domain/orchestration layers). Transaction ownership belongs to orchestration layers (`run_pipeline` and its callers), never to the repository functions themselves.

**Explicit transaction configuration (v0.4.1).** Every connection is opened with `isolation_level=""` explicitly (`core/market_data/persistence/database.py`) — behaviorally identical to sqlite3's own default, but now a stated, tested requirement rather than an implicit one. All of the above transactional guarantees are load-bearing on this specific mode; it is no longer possible to lose track of that dependency by reading the code alone.

**Versioning discipline.** A change to a calculation's logic or parameters creates a new `IndicatorDefinition` version or a new `ScoringProfile` version. Historical meaning is never mutated — an existing version's data always means what it meant when it was computed. Since v0.4.1, `IndicatorDefinition.parameters` and `ScoringProfile.parameters` are validated at construction (`__post_init__`) to be exactly the canonical, sort-keys form `serialize_parameters()` produces — not just built that way by convention. Malformed JSON or a non-canonical (but validly parseable) serialization is rejected immediately with `ValueError`, the same pattern `Money` already used for its own invariants.

**Immutable history.** `PriceBar`, `IndicatorValue`, `Score`, and `DimensionScore` are insert-only. This is enforced by SQLite `BEFORE UPDATE`/`BEFORE DELETE` triggers, not just by convention or code discipline.

**Interface stability.** Repository interfaces are considered stable once proven. New functionality should preferably be added alongside existing interfaces (a new function) rather than by modifying an established one, unless a concrete requirement demonstrates that modification is necessary. Every repository extension across Phases 1-5 has followed this: existing functions were never altered, only new ones added beside them.

**Migration discipline.** As of this release, migrations are additive only: `0001`-`0003` are frozen, and every schema change since the first has shipped as a new file. Existing migrations are never rewritten.

**Abstraction discipline.** New abstractions require a second concrete use case, not a plausible first one. Examples already respected: a second concrete indicator (RSI, v0.5.0) was added *without* introducing an indicator registry or dispatch mechanism — two working implementations were judged insufficient evidence on their own, since `calculate_sma`/`calculate_rsi` simply coexist as explicit functions; no Universe concept was built before a subset-ranking requirement existed; no Portfolio domain was built before a portfolio requirement existed.

## Deferred capabilities

Not implemented, and why each is deferred rather than simply forgotten:

- **API** — no external consumer has ever been named or discovered.
- **CLI** — same reason; nothing exists yet that would call it.
- **Dashboard consumer** — no consumer requirement exists.
- **Scheduler** — no demonstrated need for automated execution, and it would have nothing coherent to schedule until the write-side composition below exists.
- **Workflow runner** (write-side ingest→indicator→score composition) — not built. Two concrete indicators exist since v0.5.0 (SMA, RSI), so this is no longer blocked on lacking evidence for how multiple indicators would be selected — but no concrete requirement for an automated, composed write pipeline has been demonstrated, so it remains deferred rather than built speculatively.
- **Portfolio domain** — `PortfolioId`/`HoldingId` have been reserved in `core/shared/ids.py` since Phase 0 but are still unused anywhere; no portfolio requirement has been demonstrated.
- **Universe filtering** — `UniverseId` has been reserved since Phase 0 but is still unused; no requirement to rank within a named subset has been demonstrated.
- **Ranking persistence** — rankings are recomputed on demand from immutable `Score` rows; no measured latency or scale problem justifies caching them.
- **Indicator registry/dispatch** — two concrete indicators exist since v0.5.0 (SMA, RSI), each its own explicit orchestration function (`calculate_sma`, `calculate_rsi`); no caller has needed to select between them dynamically at runtime, so a name→function dispatch mechanism remains unbuilt. Not built speculatively now — the concrete trigger to watch for is a third indicator or an actual dynamic-selection requirement.
- **Configuration system** — `config/` remains an empty package; nothing yet needs runtime configuration beyond a database path.

## Activation triggers

What would justify resuming implementation, and what it would justify —
not before, and not more than the trigger warrants:

| Trigger | Justified consequence |
|---|---|
| ~~A second real indicator (e.g. SMA + RSI) with an actual calculation requirement~~ — **fired at v0.5.0** (SMA + RSI both exist) | Not, on its own, an indicator name→function dispatch mechanism — two concrete cases were judged insufficient evidence to build one. See below for what would still justify it. |
| A third real indicator, or a concrete need to select between indicators dynamically at runtime | An indicator name→function dispatch mechanism (e.g. `IndicatorCalculatorRegistry`) |
| A concrete requirement for automated, composed execution of ingest→indicator→score | A write-side pipeline composer chaining ingest→indicator(s)→score for one ETF/day — no longer blocked on indicator-generalization evidence (two indicators exist since v0.5.0), but still not demonstrated as needed |
| A named external consumer (API, dashboard, another service) requesting this data | An application-service or API boundary shaped around that consumer's actual needs |
| A concrete need to score holdings or allocations, not just standalone ETFs | A Portfolio domain, using the already-reserved `PortfolioId`/`HoldingId` |
| A concrete need to rank within a named subset of ETFs rather than all of them | A Universe concept, using the already-reserved `UniverseId` |
| A demonstrated need for automated daily execution | A workflow runner/scheduler — only after the write-side composition above already exists to schedule |
| A demonstrated latency/scale problem with on-demand ranking | Persisted/cached derived data — only with a measured problem, not a hypothetical one |

## Known limitations

- Two pre-existing Phase 0 guard clauses remain uncovered by any test: `insert_price_bar`'s OHLC-currency-mismatch check and `complete_ingestion_run`'s terminal-status check (`core/market_data/persistence/repository.py:105,193`). Neither is a defect; both are defensive code paths no test has exercised.
- `Money.__le__`/`__gt__` are implemented but not directly exercised by any test (`core/shared/money.py:48-53`) — `__lt__`/`__ge__`/`__eq__` are, and all four comparisons share one implementation pattern, but this is an honest gap, not an assumption.
- `migrations.py`'s already-applied-migration skip branch is never exercised, since every test starts from a fresh, unmigrated database.
- Overall coverage (as of v0.5.0): 145/145 tests passing, with every line in every Phase 1-5 module added or extended during this project, plus both v0.4.1 hardening changes and the v0.5.0 RSI addition, at 100%.
- None of the above are introduced by, or specific to, Phase 0-5 of this project — all predate or are orthogonal to this baseline's scope, and none are hidden here.

## Recommended next action

None. Wait for one of the activation triggers above to occur for real, then scope the next phase around that specific trigger — not around the original roadmap's assumed continuation.
