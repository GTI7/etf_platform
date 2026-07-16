# Architecture Decisions

This document records the definitive design decisions made during Phase 0
(`v0.1.0`), Phase 1 (`v0.2.0`), and Phase 2 (`v0.3.0`) of the ETF
Intelligence Platform. It is a record, not a proposal: nothing here changes
existing code or behavior. Decisions are grouped by the phase in which they
were made and numbered (`AD-NNN`) for reference. Where a later phase
revised an earlier decision, the entry says so explicitly rather than
silently superseding it.

---

## Cross-cutting conventions

These apply uniformly across every phase and are referenced by later
entries rather than repeated.

### AD-001: Repository functions never commit internally

**Decision:** every function in a `*/persistence/repository.py` module
executes plain SQL (`conn.execute(...)`) and never wraps itself in `with
conn:` or calls `.commit()`/`.rollback()`. The caller — always an
orchestration function such as `run_pipeline` — owns the transaction
boundary and decides which set of writes must succeed or fail together.

**Rationale:** this is the one rule that makes multi-write operations
(e.g. an `IndicatorValue` insert + `IngestionRun` completion + `PipelineState`
advance) atomic without a `UnitOfWork` abstraction. Phase 0 initially
violated this (see AD-013) and had to be corrected; every repository
written since has followed the rule from the start.

### AD-002: Decimal, never float, for anything numeric that matters

**Decision:** `Money.amount`, `PriceBar` OHLC fields, and `IndicatorValue.value`
are all `decimal.Decimal`. Storage in SQLite is always `TEXT`, populated
with `str(Decimal(...))` and parsed back with `Decimal(text)` — never
`REAL`/`FLOAT` columns, never `Decimal(float)` conversions (which would
bake in binary floating-point noise).

**Rationale:** ETF prices and derived indicator values must round-trip
exactly. `str(Decimal(...))` is lossless and unbounded-precision; a `REAL`
column or a naive `Decimal(0.1)` construction would not be.

### AD-003: Typed IDs via `typing.NewType`, no wrapper classes

**Decision:** entity identifiers are `NewType` aliases over `str`
(`ETFId`, `UniverseId`, `ScoreId`, `PortfolioId`, `HoldingId` in
`core/shared/ids.py`; `IndicatorDefinitionId`, `IndicatorValueId` defined
locally in `core/analytics/domain/models.py` — see AD-028). No dataclass
or value-object wrapper around IDs.

**Rationale:** enough to catch "passed an ETFId where a ScoreId was
expected" at type-check time, without runtime overhead or serialization
complexity. Analytics-only IDs were deliberately *not* added to the
Shared Kernel — see AD-028 for why.

### AD-004: Migration files are additive-only once released

**Decision** (documented in `migrations/README.md`): a migration file may
be edited in place only before any real (non-test) database has been
created from it. The moment a real database exists, that file is frozen
forever; every later schema change ships as a new migration file
(`0002_*.sql`, `0003_*.sql`, ...). A mistake in a released migration is
fixed forward with a new migration, never by editing history.

**Rationale:** `schema_migrations` is only a trustworthy audit log if the
filename-to-SQL mapping it tracks never changes retroactively.

**Application note:** `0001_initial_schema.sql` was in fact edited several
times during Phase 0 development (see AD-008, AD-011) — this was
explicitly permitted under this same rule, because no real database had
been created from it yet at the time. `0002_analytics_indicators.sql`
(Phase 2) was added as a new file rather than folded into `0001`, since by
that point Phase 0/1 had been tagged and treated as released.

### AD-005: No frameworks, no generic abstractions ahead of need

**Decision:** the entire codebase is Python standard library only —
`sqlite3`, `decimal`, `datetime`, `urllib.request`, `json`, `uuid`,
`typing`. No ORM, no dependency-injection container, no `UnitOfWork`
class, no event bus, no CQRS, no generic repository base class. Where a
transaction needs to span multiple writes, the fix is "draw the `with
conn:` boundary in the right place" (AD-001), not a new abstraction.

**Rationale:** stated as a hard constraint from Phase 0 onward and
re-confirmed explicitly before Phase 2. It also removes an entire class of
reproducibility risk: there are no third-party numerical library versions
that could silently change calculation behavior between releases (see
AD-021).

---

## Phase 0 (`v0.1.0`) — Foundation

### AD-006: `Money` — Decimal-based, explicit currency, no implicit conversion

**Decision:** `Money(amount: Decimal, currency: str)`, frozen dataclass.
Currency must be a 3-letter uppercase code. Arithmetic (`+`, `-`) and
comparison operators raise `CurrencyMismatchError` (a `DomainError`) if the
two operands' currencies differ. No multiplication/division by scalars,
no implicit float coercion — constructing with a non-`Decimal` amount
raises `TypeError`.

**Rationale:** keep the value object minimal but make incompatible-currency
bugs impossible to silently pass through arithmetic.

### AD-007: `Clock` — a plain Protocol, not a DI framework

**Decision:** `Clock` is a `typing.Protocol` with a single `now()` method.
`SystemClock` wraps `datetime.now(timezone.utc)`; `FixedClock` wraps a
fixed, timezone-aware `datetime` (raises `ValueError` if given a naive
one). No global clock singleton, no dependency-injection container —
callers that need a clock take one as a constructor/function argument.

**Rationale:** deterministic tests (`FixedClock`) without building any
general-purpose DI infrastructure.

### AD-008: `Calendar` + `TradingSession`, not a single `TradingCalendar` table

**Decision:** calendar metadata (`Calendar`: id, name, exchange, timezone)
and per-date sessions (`TradingSession`: calendar_id, session_date,
is_trading_day, close_time_utc) are two tables, not one. `ETF.calendar_id`
carries a real SQL foreign key to `Calendar.calendar_id`.

**Rationale:** a single `TradingCalendar(calendar_id, session_date, ...)`
table has a composite primary key, and SQLite cannot express a foreign key
from `ETF` to just the `calendar_id` portion of a composite key. Splitting
the tables was a revision made during Phase 0 (the original single-table
design was corrected before `v0.1.0`) specifically to make that foreign
key real rather than advisory.

**Explicitly out of scope:** this is not a full exchange-calendar engine
and has no holiday-calculation logic. Callers populate the sessions they
need; an unpopulated date is treated as non-trading by `is_trading_day`
(safe default — see AD-024 for why this default became load-bearing in
Phase 2).

### AD-009: Raw market data is insert-only, enforced by SQLite triggers

**Decision:** `PriceBar` rows can never be updated or deleted —
`BEFORE UPDATE`/`BEFORE DELETE` triggers `RAISE(ABORT, ...)`
unconditionally. A price correction is a new row, never an edit. The same
pattern is documented as required for future raw tables (macro
observations, sentiment observations) when they are introduced.

**Rationale:** raw ingested data is the one thing every derived
calculation (Phase 2 onward) ultimately depends on for reproducibility; it
must be tamper-proof at the database level, not just by convention.

### AD-010: `PipelineState` is an explicit table, not a computed watermark

**Decision:** `last_successful_pipeline_date`-equivalent state is stored in
a dedicated `PipelineState(pipeline_name PRIMARY KEY, last_successful_session,
updated_at)` table, updated only when a pipeline run completes
successfully. `IngestionRun` remains the full, untouched execution history
(every attempt, successful or not); `PipelineState` is the derived
"current progress" pointer, not the other way around.

**Revision note:** the original Phase 0 implementation computed this value
as `MAX(pipeline_date) WHERE status='success'` over `IngestionRun`
directly, with no separate table. This was revised before `v0.1.0` because
it becomes ambiguous once multiple pipelines or out-of-order backfills
exist — a `MAX()` alone cannot express "this pipeline's watermark should
never regress" once more than one caller can write to overlapping dates.

### AD-011: Watermark advancement is monotonic only

**Decision:** `advance_pipeline_watermark` upserts with
`last_successful_session = MAX(last_successful_session, excluded.last_successful_session)`.
An out-of-order (e.g. backfill) run for an earlier session never regresses
a watermark that has already advanced past a later one.

### AD-012: Cheap invariants belong in SQLite, not just in Python

**Decision:** `CHECK (volume >= 0)` on `PriceBar.volume`;
`CHECK ((status = 'running') = (completed_at IS NULL))` on `IngestionRun`
(a run is `'running'` if and only if it has no completion timestamp — it
can never be left half-finished). Both were added after an explicit review
identified them as invariants that were previously enforced nowhere at
all.

**Rationale:** a constraint SQLite can check for free should not depend on
every calling code path remembering to check it in Python.

### AD-013: Transaction-boundary bug found and fixed before freeze

**Finding:** the original Phase 0 implementation had every repository
function commit independently (its own `with conn:`), including inside
`run_pipeline`'s success path — meaning `complete_ingestion_run` and
`advance_pipeline_watermark` were two separate transactions. A crash
between them would leave `IngestionRun.status='success'` permanently
committed while the watermark never advanced.

**Fix:** repository functions were rewritten to never commit internally
(AD-001), and `run_pipeline` was rewritten so that `start_ingestion_run`
remains its own committed transaction (a crash during the pipeline body
should leave a visible orphaned `'running'` row), while the completion
path (`complete_ingestion_run` + `advance_pipeline_watermark` on success,
or just `complete_ingestion_run` on failure) is exactly one transaction
per outcome.

**Verification:** a regression test was written, confirmed to fail against
the original two-transaction implementation (by temporarily reintroducing
it), then confirmed to pass against the fix.

---

## Phase 1 (`v0.2.0`) — Market data providers and ingestion

### AD-014: `DataProvider` is a minimal Protocol, mapped at the boundary

**Decision:** `DataProvider` is a `Protocol` with `name: str` and
`fetch_daily_bars(ticker, start_date, end_date) -> list[ProviderPriceBar]`.
`ProviderPriceBar` is a raw, provider-shaped value (session_date, OHLCV,
currency) — it is never persisted directly. Ingestion orchestration maps
each `ProviderPriceBar` into a domain `PriceBar` (assigning `price_bar_id`,
`etf_id`, `source`, `ingested_at`) before calling `insert_price_bar`.

**Rationale:** keeps provider-specific shapes (whatever a given API
happens to return) fully isolated from the immutable domain/storage model.

### AD-015: `ProviderRegistry` is an explicit dict, no auto-discovery

**Decision:** `ProviderRegistry.register(provider)` / `.get(name)` backed
by a plain `dict[str, DataProvider]`. Duplicate registration raises
`ValueError`; an unknown name raises `KeyError`. No plugin scanning, no
entry-point discovery.

### AD-016: `YahooFinanceProvider` — stdlib HTTP, injectable fetch

**Decision:** implemented with `urllib.request` only (no `requests`, no
`yfinance` — see AD-005). The HTTP fetch function is injectable via the
constructor (`YahooFinanceProvider(fetch=...)`), defaulting to a real
`urlopen` call. This lets every test run fully offline against canned JSON
without mocking library internals.

**Numeric-safety decision:** every price value from the parsed JSON goes
through `Decimal(str(x))`, never `Decimal(x)` directly — `x` is a JSON
float, and skipping the `str()` round-trip would bake in binary
floating-point artifacts (AD-002).

### AD-017: One `run_pipeline` call = one `(ETF, session_date)` pair

**Decision:** `ingest_daily_prices` runs one pipeline per ETF per session,
named `f"price_ingestion:{ticker}"` — giving every ETF its own independent
`PipelineState` watermark. TradingCalendar-aware: a non-trading
`session_date` is a no-op success (nothing to ingest), and the watermark
still advances past it.

### AD-018: `is_trading_day` added as a targeted accessor

**Decision:** `is_trading_day(conn, calendar_id, session_date) -> bool`
added alongside the existing `get_trading_days`. An unpopulated date
returns `False` (safe default: skip rather than guess — inherited from
AD-008).

### AD-019: Partial-write rollback bug found and fixed during Phase 1

**Finding:** `run_pipeline`'s failure branch committed the `'failed'`
status without first rolling back whatever the pipeline body had written
before raising. Invisible in Phase 0 (nothing ever wrote inside the
pipeline body there); concrete in Phase 1, where `ingest_daily_prices`
inserts `PriceBar` rows inside that same body — a provider that inserted
one bar and then failed on a second would leave the first bar permanently
committed alongside a `'failed'` run.

**Fix:** `conn.rollback()` added at the top of the `except` branch, before
recording the failure in its own fresh transaction.

**Verification:** reproduced live (regression test failed against the
un-fixed code, passed after the fix), same method as AD-013.

---

## Phase 2 (`v0.3.0`) — Analytics indicators

### AD-020: `IndicatorDefinition` identity is `(name, version, parameters)`

**Decision:** one row per distinct calculation identity. `parameters` is
JSON, always built via `serialize_parameters()`
(`json.dumps(parameters, sort_keys=True)`) — never `json.dumps()` directly
— so the `UNIQUE(name, version, parameters)` constraint cannot be silently
bypassed by two logically-identical dicts serializing differently due to
key order.

### AD-021: Calculation versioning is a plain integer, no environment-tracking concept

**Decision:** `version: int`, monotonically increasing per `name`. A
calculation-logic change is always a new version (new row); an existing
`IndicatorDefinition` is never edited.

**Considered and rejected:** introducing a separate
"CalculationEnvironment" concept to track the runtime/toolchain that
produced a value. Rejected because (a) the codebase has zero external
numerical dependencies whose version could silently change calculation
behavior (AD-005), and (b) the codebase itself is git-tagged at every
phase boundary. `IndicatorDefinition.version` plus git history was judged
sufficient for "reproducible forever"; revisit only if a numeric
dependency with real version-behavior differences is ever introduced.

### AD-022: `IndicatorValue` is insert-only, with idempotent writes

**Decision:** same immutability pattern as `PriceBar` (AD-009):
`BEFORE UPDATE`/`BEFORE DELETE` triggers reject any attempt to modify a
computed value. `UNIQUE(indicator_definition_id, etf_id, session_date)`
plus `INSERT ... ON CONFLICT (...) DO NOTHING` makes a rerun of the same
definition for the same day a silent no-op — never a duplicate row, never
a silent overwrite. A corrected recomputation always means a new
`IndicatorDefinition` version (AD-021), never an `UPDATE` of an existing
value.

### AD-023: Window resolution validates `PriceBar` completeness, not just trading-day count

**Decision:** computing an N-day window resolves the N most recent trading
dates from `TradingSession`, then requires a `PriceBar` row for *every one*
of them — raising `InsufficientPriceHistoryError` if any is missing,
whether that's because the ETF genuinely lacks that much history yet, or
because the `TradingCalendar` itself has a population gap (AD-008's
accepted limitation). The two causes are deliberately not distinguished:
both mean the window cannot be computed correctly.

**Rationale:** a check that only counted `TradingSession` rows marked as
trading days would miss the case where the calendar is fully populated but
price ingestion has a gap — silently producing a shorter, mislabeled
window. This was identified as a silent-corruption risk during the Phase 2
readiness review and folded into the window-resolution logic before
implementation began.

### AD-024: Insufficient history raises, rather than partial window / NULL / silent skip

**Decision:** `InsufficientPriceHistoryError` (a `DomainError`) is raised
and allowed to propagate out of the pipeline body, where `run_pipeline`
records it as a failed `IngestionRun` with the error message attached.

**Alternatives rejected:**
- *Partial window* — would silently redefine what "N-day SMA" means for
  that row, with no signal to any downstream consumer.
- *NULL value* — ambiguous (never-computable vs. not-yet-computed vs.
  bad data) and would require a later mutation to fill in, contradicting
  AD-022.
- *Silent skip (no row, no error)* — throws away the audit trail that
  raising gets for free via the existing `IngestionRun.error_message`
  mechanism.

**Accepted consequence:** for a fixed past `session_date`, a genuine
too-early-history failure fails identically on every retry — the
watermark correctly never advances past a date that can never be
computed.

### AD-025: Pure calculation logic lives in `domain/`, not a new subpackage

**Decision:** `core/analytics/domain/calculations.py` holds side-effect-free
functions only (`sma(prices: list[Decimal]) -> Decimal`, window-size
implicit in `len(prices)`). No `core/analytics/engine/` or
`core/analytics/calculation/` subpackage was introduced — the reserved
Phase 0 structure only specified `domain/` and `persistence/` under
`analytics`, and pure math is exactly what a domain layer holds.

### AD-026: `run_pipeline` is reused unmodified, cross-package

**Decision:** `core/analytics/indicator_calculation.py` imports
`run_pipeline` directly from `core.market_data.ingestion.pipeline_run`
rather than moving, duplicating, or wrapping it.

**Rationale:** `run_pipeline` is generic (parameterized only by
`pipeline_name`/`pipeline_date`) and contains no market-data-specific
logic; relocating it would touch frozen, tagged code for a cosmetic
reason with no functional benefit. Judged not to be an architectural
violation — analogous to how `core.shared.clock.Clock` is imported
everywhere without controversy.

### AD-027: Idempotency and rollback guarantees are re-verified per pipeline family, not assumed

**Decision:** although `calculate_sma` reuses `run_pipeline` unmodified
(AD-026), its own regression tests independently reproduce both failure
modes proven for market-data ingestion in Phase 1 (AD-019): a failure
inside the pipeline body after a successful write, and a failure in
`run_pipeline`'s own completion step. Both are confirmed to roll back the
`IndicatorValue` insert.

**Rationale:** reusing already-correct infrastructure is not the same as
proving a new caller of it is correct — the transaction boundary must be
drawn correctly at each new call site (AD-001), and that was checked
explicitly rather than assumed to follow automatically from Phase 1's
tests.

### AD-028: Analytics-only typed IDs are not added to the Shared Kernel

**Decision:** `IndicatorDefinitionId` and `IndicatorValueId` are defined in
`core/analytics/domain/models.py`, not in `core/shared/ids.py`.

**Rationale:** a hard constraint against new Shared Kernel concepts was in
effect for Phase 2. These IDs have no reuse outside the analytics context,
so adding them to the shared module would have been an unnecessary
extension of it rather than a required one.
