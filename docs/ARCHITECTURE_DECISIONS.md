# Architecture Decisions

This document records the definitive design decisions made during Phase 0
(`v0.1.0`), Phase 1 (`v0.2.0`), Phase 2 (`v0.3.0`) of the ETF Intelligence
Platform, and the Platform Migration Phase 0 / Phase 1A (`v0.4.0`) that
began converting the repository into the reusable research platform
described in `docs/PLATFORM_ARCHITECTURE_V1.md`. It is a record, not a
proposal: nothing here changes existing code or behavior. Decisions are
grouped by the phase in which they were made and numbered (`AD-NNN`) for
reference. Where a later phase revised an earlier decision, the entry says
so explicitly rather than silently superseding it.

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

---

## Platform Migration Phase 0 / Phase 1A (`v0.4.0`) — Statistics domain extraction

Decisions made while executing
`docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md` Steps 1–2, against the
target shape fixed by `docs/PLATFORM_ARCHITECTURE_V1.md`. Unlike Phases
0–2 above, which designed the ETF platform's own data/analytics model,
this phase begins converting the repository into the reusable research
platform described there; it is additive scaffolding, not a redesign
of anything Phases 0–2 already decided.

### AD-029: Statistics domain extraction is a copy, not a move, with compatibility tests kept permanently

**Decision:** `core/statistics/significance.py` duplicates the
significance-testing helpers (`_spearman`, `_pearson`,
`_rank_average_ties`, `_percentile`, `daily_ic_series`, `mean_ic`,
`top_bottom_spread`, `permutation_null`, `empirical_p_value`,
`bootstrap_ci`, `holm_bonferroni`) that have lived inside
`experiments/validate_reference_v1_significance.py` since REFERENCE v1.
The four `experiments/validate_*.py` scripts that use these functions
keep their own existing implementation untouched — none were rewired to
import from `core.statistics.significance`. The tests proving the
extraction is faithful (`tests/compatibility/test_statistics_reference_v1_compatibility.py`)
are retained permanently as migration evidence, not deleted once Phase
1A review completed.

**Rationale:** REFERENCE v1's published result depends on the exact
behavior of the inlined implementation that produced it; rewiring that
script to call a new module would change what "reproduce REFERENCE v1"
means for a closed cycle, which
`docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md` Sections 5–6 rule out.
The compatibility tests were originally scoped (Migration Plan Section
7) as temporary proof of a correct extraction, deletable once reviewed.
Phase 1A review concluded that framing undersold their value: they are
not just an extraction check, they are standing, re-runnable evidence
that `core/statistics/significance.py` — the module every future
Validation gate will call — remains numerically identical to the
implementation REFERENCE v1 was actually validated against. That
evidence has no expiry date, so the tests do not either. See
`docs/STATISTICS_DOMAIN.md` ("Compatibility tests") for the same
statement made from the domain's side.

**Explicitly not decided here:** whether the drift-regression pattern
should be applied to REFERENCE v2 H1's or H3's own inlined copies. No
second extraction has happened yet (`core/statistics/ranking.py`
remains deferred per `docs/STATISTICS_DOMAIN.md` "Not extracted in
Phase 1A"); this AD covers only what Phase 1A actually built.

### AD-030: Archive manifest is an early preservation guard, not `ArchiveVerifier`

**Decision:** `tools/archive_manifest.py` and
`docs/RESEARCH_ARCHIVE_MANIFEST.md` were introduced in Phase 0, ahead
of any `core/governance/` business logic, as a narrow, purely additive
integrity guard: `build_manifest()` constructs a small
`archive_manifest.json` for a *new* project's archive directory, and
`write_manifest()` refuses outright to write into any of the three
legacy archive directories (`reference_v1`, `reference_v2_h1`,
`reference_h3`) or to overwrite an existing manifest file.

**Rationale:** the retrospective identified archive-completeness
checking as a real gap (Tier 2), but the full check — validating a
directory against the complete Standard Section 5 evidence-package
shape — is `ArchiveVerifier`'s job (`docs/PLATFORM_ARCHITECTURE_V1.md`
Section 4.4), which requires `core/governance/` to exist first. Rather
than wait, Phase 0 shipped the one piece of that problem answerable
immediately and safely: a manifest schema plus write-side guards that
make it structurally impossible for the earliest platform tooling to
touch a closed, historical archive. This is deliberately a fraction of
the eventual system, not a first draft of the whole thing.

**Scope, stated explicitly so it is not mistaken for completion:**
`tools/archive_manifest.py` does not read or interpret an existing
manifest, does not check for the presence of `hypothesis.md`,
`methodology.md`, `dataset_hashes/`, or any other Standard Section 5
artifact, and does not implement `ArchiveVerifier.verify_archive()`. It
has written zero manifests into any real project archive as of this
decision (H4 has not opened). A future `ArchiveVerifier` implementation
is expected to build on this manifest as its input contract — reading
`schema_version` and `lifecycle_version` to decide what shape of check
to run — rather than replacing it.

### AD-031: `ProjectId` / `ArtifactRef` are reserved on the Shared Kernel ahead of any caller

**Decision:** `ProjectId` and `ArtifactRef` (`typing.NewType` over
`str`, following AD-003's existing convention) were added to
`core/shared/ids.py` in Phase 0, with no code anywhere in the
repository constructing or consuming either one yet, and no existing
identifier migrated to use them.

**Rationale:** `docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.1 and 4.4
name `ProjectId` (Research domain, the Project Registry's key) and
`ArtifactRef` (Research's `advance_phase()`, Governance's
`verify_archive()`/`reproduce()`) as identifiers every future domain
converges on. Reserving the names now, on the same Shared Kernel module
every domain already imports from for `ETFId`/`UniverseId`/etc., means
`core/research/` and `core/governance/` have a stable type to import
when they are actually implemented, instead of each domain inventing
its own ad hoc string-id type at that point and requiring a later
rename across every caller.

**Scope, stated explicitly:** this is a name and a type reservation,
nothing more. No registry, no persistence, no multi-tenancy, and no
`TenantId`-style concept exists in this codebase or was introduced by
this decision — `docs/PLATFORM_ARCHITECTURE_V1.md`'s "commercial-ready"
design principle (Section 2) notes only that domain boundaries would
*not preclude* a future multi-tenant deployment, which is a claim about
the shape of the domain graph, not a reservation of any tenant-scoped
identifier. Introducing an actual tenant concept would be a real,
separate architectural decision, made when a concrete second-tenant
requirement exists — not implied by, or bundled into, this AD.

**Considered and rejected:** not reserving the names, and letting
`core/research/`'s eventual implementation introduce `ProjectId` at
that point instead. Rejected because `core/shared/ids.py` is Phase 0/1
proven low-risk ground for this pattern (AD-003), and a reservation
that turns out to be unnecessary costs two unused `NewType` lines,
while retrofitting a shared identifier after several domains have each
already grown their own would be the more expensive path.

---

## Platform Migration Phase 1B (`v0.5.0`) — Price coverage check extraction

Executes `docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md` Section 3, Step
3, the migration step directly after Phase 1A's Statistics extraction:
"Copy the two-directional missing/surplus check out of
`maintenance/remediate_h3_invalid_pricebar_rows.py` into a new
`maintenance/verify_price_coverage.py`, callable standalone or from a
test." Like Phase 1A, this is additive: a new file, extracted logic,
zero edits to the historical script it comes from.

### AD-032: Price coverage check is extracted as structured dataclasses, not the original's plain dicts

**Decision:** `maintenance/verify_price_coverage.py`'s
`check_etf_coverage()` / `verify_price_coverage()` copy the two-directional
(missing + invalid) per-ETF coverage logic from
`remediate_h3_invalid_pricebar_rows.py`'s `per_etf_coverage_check()`
unchanged in substance — same predicate (expected trading days between
an ETF's own earliest and latest stored `PriceBar.session_date`,
compared against stored dates in both directions) — but returns a
frozen `CoverageReport` dataclass per ETF instead of the original's
plain `dict`. The original script is untouched; it keeps its own inlined
dict-returning version, exactly as Phase 1A left the four
`experiments/validate_*.py` scripts' inlined statistics helpers
untouched (AD-029).

**Rationale:** `docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.4 names a
`DatasetIntegrityChecker`-shaped check as this exact gap's eventual
Governance-domain owner, and Section 4.2 established `GateResult` as a
"plain record" contract other domains consume. A dataclass is that same
shape today, one step ahead of Governance actually existing, at zero
behavioral cost — `dataclasses.asdict()` produces the identical
plain-dict/JSON shape the original script already prints, so nothing
about the tool's CLI output changes. This is consistent with AD-003's
existing "enough structure to catch mistakes, no framework" discipline.

**Terminology note — "invalid," not "surplus."** The original script's
field name `surplus_dates` is renamed `invalid_dates` here: "surplus"
described the specific H3 remediation case (rows that shouldn't exist at
all), but the same predicate also fires on a completely unpopulated
calendar date (AD-023's calendar-gap case), which is not "surplus" in
any meaningful sense — both are simply stored rows whose date does not
resolve to a recognized trading day. `invalid_dates` names the actual
invariant being checked, independent of which of the two underlying
causes produced it (see AD-023's own "deliberately not distinguished").
No behavior differs from the original; only the field name is clearer
in the new module.

**Explicitly out of scope.** This AD does not introduce a
`core/governance/` `DatasetIntegrityChecker` implementation — that
remains future work per the migration plan's own sequencing (Governance
Tier 1 items come first, per Step 4). It does not change
`remediate_h3_invalid_pricebar_rows.py`'s `PREDICATE_SQL`, delete logic,
or export format in any way, and it does not touch
`research_archive/reference_h3/` or any other historical artifact.

---

## Platform Migration Phase 1C — Governance Tier 1

**No version tag.** Phase 1A and 1B were labeled `v0.4.0`/`v0.5.0`
above; those already collide with `docs/BASELINE_STATUS.md`'s
unrelated main release track (`v0.4.0` "Foundation frozen", `v0.5.0`
"Second Concrete Indicator"), which predates this migration and is not
being renumbered here. Phase 1C is left deliberately untagged rather
than continuing that collision into `v0.6.0`, which is not just a
numbering coincidence but a real, already-shipped, already-documented
release (`docs/RELEASE_NOTES_v0.6.0.md`, "Write-side Pipeline
Composition") — reusing it here would misidentify this change as part
of that release.

Executes `docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md` Section 3, Step
4 (first half): `IndependenceLabelLinter` and `FreezeVerifier`, the two
Governance Tier 1 automations
`docs/RESEARCH_PLATFORM_RETROSPECTIVE.md` Section 3 ranked highest —
pure functions over text/git state, needing no schema and no dependency
on Research, Validation, or Reporting. Additive: two new modules, two
new test files, no edit to any existing file's behavior other than
`core/governance/__init__.py`'s own docstring (updated to stop
describing the package as empty).

### AD-033: `FreezeVerifier.verify_freeze` takes a raw commit ref, not a `FreezeId`

**Decision:** `core/governance/freeze_verifier.py`'s `verify_freeze(commit_ref:
str, covered_paths: Iterable[Path | str]) -> VerificationResult` diverges
from `docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.4's sketch —
`FreezeVerifier.verify_freeze(self, freeze_id: FreezeId) ->
VerificationResult` — by taking a plain git commit reference and an
explicit list of covered file paths instead of a `FreezeId`.

**Rationale:** `FreezeId` is a Research-domain concept, backed by the
project registry `docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md` Step 5
has not built yet (`core/research/` remains an empty stub;
`ProjectId`/`ArtifactRef` are reserved names only per AD-031, not a
working registry). Building freeze-record persistence here, ahead of
Research existing to own it, would be a new abstraction ahead of any
concrete second consumer — exactly what this repository's stated
discipline (`docs/ARCHITECTURE_DECISIONS.md`'s cross-cutting AD-005)
rules out. The raw-commit-ref signature instead takes exactly what every
existing frozen document already states in prose today (see e.g.
`docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`'s own freeze-commit
table: a hash plus a list of files it covers).

**This is a temporary interface, stated explicitly so it is not mistaken
for the final one.** When `core/research/` is eventually built with a
real `FreezeId`-keyed registry, the expected path is a thin wrapper that
resolves a `FreezeId` to `(commit_ref, covered_paths)` and calls this
function unchanged — not a rewrite of `verify_freeze`'s own logic. This
mirrors AD-030's treatment of the archive manifest as an early,
intentionally partial guard ahead of `ArchiveVerifier`.

**Verification semantics, stated explicitly.** A `VERIFIED` result
proves the covered files are byte-identical to their content at the
claimed commit, with no committed or uncommitted drift since — i.e. the
freeze is *reproducible*. It proves nothing about whether the frozen
methodology was itself correct, adequate, or reviewed, and it does not
constitute approval of any research decision; it answers only "is this
document's own freeze claim actually true of the repository right now."
The result is one of three states (`VERIFIED` / `DRIFTED` /
`UNVERIFIABLE`), deliberately not a boolean — an unresolvable commit
ref or a covered path that never existed at that commit is a different
failure mode than a real, completed drift finding, and collapsing the
two into one `bool` would lose that distinction.

**Explicitly out of scope.** No `FreezeId` type, no persistence, no
Research-domain dependency, no CLI beyond what its own test suite needs.
Read-only: every git invocation is a read-only plumbing command
(`rev-parse`, `cat-file -e`, `diff`, `status --porcelain`); nothing
writes, commits, checks out, or resets. `research_archive/`, every
`experiments/validate_*.py` script, and `maintenance/remediate_h3_invalid_pricebar_rows.py`
are untouched by this AD.

**Smoke test evidence (Days 6-12, read-only).** Run against the two
real, already-documented H3 freeze claims: the methodology freeze
(`docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`, commit `07f0da3`,
covering `attempt_001_specification.md`,
`REFERENCE_H3_PREVALIDATION_PLAN.md`,
`REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`,
`RESEARCH_GOVERNANCE_STANDARD.md`) and the acceptance-criteria freeze
(`research_archive/reference_h3/decision_log.md` Entry 15, commit
`a643993`, covering `H3_ACCEPTANCE_CRITERIA.md`). Both resolved to their
documented full hashes and returned `VERIFIED`, with no drifted files
and no errors — reproducing, by independent recomputation rather than
by re-reading the prior human audit's conclusion, exactly what
`H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`'s own freeze-commit table
already claimed. No repository file was modified by this run.

### AD-034: `IndependenceLabelLinter` is a local, line-adjacent lexical check, not a semantic one

**Decision:** `core/governance/independence_linter.py`'s `lint()` flags a
line containing "independent"/"independently" unless a `Level 2` or
`Level 3` qualifier appears on that same line or the immediately
preceding line. It does not attempt to determine whether "independent"
is being used in a review-independence sense at all, and it does not
scan an entire document for "does a Level 2/3 qualifier appear
anywhere" — both were considered and rejected.

**Rationale — why not whole-document.** A whole-file "does this
document mention Level 2/3 anywhere" check would flag almost nothing:
most H3 documents mention a Level qualifier somewhere while still
containing individual unqualified sentences, which is the actual defect
`docs/RESEARCH_PLATFORM_RETROSPECTIVE.md` Section 2 describes (three
specific mislabeled review documents, not whole documents missing any
qualifier at all). The check has to be local to be the check the
retrospective actually asked for.

**Rationale — why not semantic.** Distinguishing a review-independence
claim from an unrelated use of the word (e.g. "independent variable")
would require sentence-level natural language understanding, which is
out of scope for a Tier 1 automation meant to be "the cheapest possible
automation on this list" (retrospective Section 3 item 2's own framing).
`lint()` therefore also flags non-review uses of "independent" as a
known, accepted false positive — findings are candidates for human
triage (consistent with `docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.4:
Governance flags, it does not fix or auto-reject), not an automatic
pass/fail gate, so an occasional false positive costs a reviewer one
glance, not a wrongly blocked action.

**Explicitly out of scope.** No configuration for additional qualifier
patterns, no per-document allowlist, no CLI beyond what its own test
suite needs. Read-only: only reads the given file paths.

**Calibration finding (Days 6-12 smoke test, read-only).** Run against
every `.md` file under `docs/` and `research_archive/` (50 files): 403
findings, no repository file modified. This is far more than "the three
mislabeled H3 review documents" the retrospective named, and inspection
confirms why — real documents typically state a Level 2/3 qualifier
once per section, then use bare "independent"/"independently" several
more times in the same section, still referring to that one
already-qualified claim; the one-line lookback this AD deliberately
chose does not reach those later, section-scoped repeats. This is
evidence of the documented "not semantic" tradeoff above showing up
concretely, not a new defect: `lint()` is a **candidate-discovery tool**
that finds every lexically unqualified occurrence, not a validator that
determines whether each occurrence is unqualified *in its section's
context*. Consistent with this AD's own "findings are candidates for
human triage, not an automatic gate" framing, the 403 findings are
disclosed here as a calibration signal for a future decision, not acted
on now — **the matching rule (same-line/previous-line window) is
unchanged by this finding**; widening it (e.g. to paragraph/section
scope) remains open for later, once Governance has a real consumer to
evaluate precision against, and should not be done speculatively ahead
of that need.

---

## Platform Migration Phase 1D — Research project identity and metadata

No version tag, for the same reason Phase 1C has none (see above — the
`v0.4.0`/`v0.5.0`-style labels collide with `docs/BASELINE_STATUS.md`'s
unrelated real release track, and `v0.6.0`/`v0.7.0` are both real,
already-shipped releases with their own release notes).

Executes `docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md` Section 3, Step
5, narrowed to identity and metadata ownership only: `ProjectId`
construction, the `Project` record, the `ResearchProjectRepository`
storage boundary, `ProjectRegistry`, and backfilling the three closed
historical cycles. `FreezeManager`, `ExperimentOrchestrator`, and any
lifecycle-transition behavior (`advance_phase`) are explicitly deferred
— nothing here calls into Governance, Data, Statistics, or Validation.
Additive: five new modules under `core/research/`, two new test files,
no edit to any existing file's behavior other than
`core/research/__init__.py`'s own docstring and the same
`tests/test_domain_packages_import.py` carve-out pattern Phase 1A and
1C already established.

### AD-035: `ProjectId` stays a `NewType`; validation lives in a constructor function, not a wrapper class

**Decision:** `core/research/project_id.py`'s `create_project_id(raw:
str) -> ProjectId` validates format (`^[a-z][a-z0-9_]*$`) and returns
the existing `core.shared.ids.ProjectId` — the `NewType("ProjectId",
str)` reserved by AD-031. No new `ProjectId` type is defined anywhere;
`core/research/` imports and reuses the Shared Kernel one exactly as
AD-031 anticipated it would.

**Rationale.** AD-003 is an explicit, cross-cutting rule: "Typed IDs via
`typing.NewType`, no wrapper classes." A validated value object (a
frozen dataclass wrapping a string, raising on construction) is the
natural shape for "immutable, validated, no accidental free-form
strings," but would be exactly the wrapper class AD-003 rules out, and
would leave two competing `ProjectId` concepts in the codebase (the
Shared Kernel one AD-031 already reserved, and a new one for Research to
use instead). `create_project_id` resolves this the same way
`serialize_parameters()` already resolves an analogous problem for
`IndicatorDefinition.parameters` (AD-020): the type itself stays a bare
`NewType`, and a single constructor function is the enforced gate every
caller is expected to go through. This is a convention, not a runtime
guarantee — nothing prevents `ProjectId("bad id")` directly, the same
limitation AD-003 already accepts for every other typed id in this
codebase.

### AD-036: `ProjectRegistry`'s v0.1 interface is narrower than the architecture doc's own sketch

**Decision:** `core/research/project_registry.py`'s `ProjectRegistry`
implements exactly `register_project(project: Project) -> None`,
`get_project(project_id: ProjectId) -> Project`, and `list_projects() ->
list[Project]`. This differs from `docs/PLATFORM_ARCHITECTURE_V1.md`
Section 4.1's own sketch in two ways: the sketch's
`register_project(name, asset_class, mechanism) -> ProjectId` has the
registry mint the id and construct the record; this implementation has
the caller construct a complete `Project` (id included) and hand it to
the registry. The sketch's `list_projects(*, phase=None, status=None)`
filters; this implementation does not.

**Rationale.** Same pattern as AD-033's `FreezeVerifier` divergence last
phase: build the narrowest slice that satisfies the current concrete
need (identity + metadata ownership, per this step's explicit scope)
rather than the full future interface ahead of a caller that would
exercise the rest of it. Filtering and id-minting can be added later
without breaking this signature — `list_projects()` gains optional
keyword filters, `register_project` could gain a factory-style
convenience wrapper — neither requires revisiting `Project`,
`ResearchProjectRepository`, or the historical backfill built against
today's interface.

**Two-layer design (`ProjectRegistry` over `ResearchProjectRepository`),
stated explicitly.** Unlike `ProviderRegistry` (AD-015), which is a flat
dict with no separate storage interface, `ProjectRegistry` delegates
storage to an injected `ResearchProjectRepository`. This is a deliberate
exception to "no abstraction ahead of need," not an oversight: today's
only implementation (`InMemoryResearchProjectRepository`) is exactly as
simple as `ProviderRegistry`'s internal dict, but the Migration Plan
Step 5 explicitly names YAML and SQLite as expected future
implementations. The seam costs one `ABC` and one constructor
parameter today, in exchange for never having to revisit
`ProjectRegistry`'s own logic (duplicate-id checking, lookup semantics)
when a real persistence mechanism is chosen later.

**`lifecycle_state` vs. `research_outcome`, stated explicitly.**
`Project.lifecycle_state` (`ACTIVE`/`FROZEN`/`ARCHIVED`) is a closed,
registry-controlled vocabulary describing where a project is in the
governance process. `Project.research_outcome` is free text (`None`
until concluded) describing what was found — deliberately not an enum,
because the real vocabulary the three historical cycles already used is
not one closed set: `docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md` and
`docs/REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md` both record `"ARCHIVE"`,
while `docs/REFERENCE_H3_RESEARCH_CLOSEOUT.md` records
`"EVIDENCE AGAINST"` — a `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section
7 FAIL-discipline classification, not the same three-category framework
the other two use. Coding a single enum now would mean guessing at a
taxonomy real research history hasn't settled on, ahead of any second
concrete need to structure it — the same discipline AD-005 already
applies everywhere else in this codebase.

**`origin_date`, not `created_at`, stated explicitly.** No file anywhere
in the repository records when any of the three historical cycles
actually *started*. `Project.origin_date` deliberately does not claim
to answer that question — it names the earliest already-recorded
evidence date for that project (a dated report filename, or a freeze
commit's author date; see `core/research/historical_backfill.py` for
the exact source per project), sourced via `FixedClock`-style historical
fact recording (AD-007's pattern, applied to a past fact rather than a
test), never `SystemClock.now()`. Inventing a "created" timestamp that
isn't backed by any real artifact would be exactly the kind of
undisclosed retroactive record-keeping
`docs/RESEARCH_PLATFORM_RETROSPECTIVE.md` Section 2 already identified
as a defect in H3's own process (`decision_log.md` Entry 15's
retroactively-written freeze-commit entry).

**Explicitly out of scope.** No `FreezeManager`, no
`ExperimentOrchestrator`, no `advance_phase`-shaped lifecycle-transition
method — `Project.lifecycle_state` is set once at construction by the
caller; nothing in this AD's code ever mutates an already-registered
project. No YAML/SQLite-backed `ResearchProjectRepository`
implementation. `research_archive/` is read only to source the
historical backfill's evidence citations (commit hashes, filenames,
dates already present in existing frozen files) — no file under
`research_archive/`, `experiments/`, or `maintenance/` is modified by
this AD.

### AD-037: Historical backfill points to existing evidence; it does not duplicate it

**Decision:** `core/research/historical_backfill.py`'s three `Project`
records carry only pointers into already-existing evidence
(`metadata["closeout_doc"]`, `metadata["freeze"]`) — commit hashes and
document paths copied verbatim from `research_archive/reference_v1/COMMIT.txt`,
`research_archive/reference_v2_h1/COMMIT.txt`,
`research_archive/reference_h3/FREEZE_RECORD.md`, and each cycle's
close-out report. No figure, verdict narrative, or methodology detail
from any closeout document is copied or restated beyond the single
`research_outcome` label each document's own headline verdict already
uses verbatim (`"ARCHIVE"`, `"ARCHIVE"`, `"EVIDENCE AGAINST"`).

**`reference_h3`'s two-commit freeze shape vs. the other two's
single-commit shape, stated explicitly.** `reference_v1` and
`reference_v2_h1` each have one freeze commit (`metadata["freeze"]["commit"]`)
because each was archived directly from one significance-report
snapshot with no separate methodology-freeze-then-acceptance-criteria-freeze
phases. `reference_h3` has two
(`metadata["freeze"]["construction_commit"]`,
`metadata["freeze"]["acceptance_commit"]`) because H3's own governance
process actually froze construction and acceptance criteria as two
distinct, separately-logged events (`decision_log.md` Entries 10 and
15) — the metadata shape reflects a real difference in how each cycle
was actually governed, not an arbitrary inconsistency.

### AD-038: Archive Manifest Scaffold Generator creates evidence directories, not evidence files

**Decision:** `tools/archive_manifest.py`'s `scaffold_project_archive()`
creates a new project's `archive_manifest.json` (via the existing
`build_manifest()`/`write_manifest()`) and the three empty evidence
subdirectories `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 5 expects
— `dataset_hashes/`, `experiment_results/`, `reviewer_reports/` — each
with a `.gitkeep` file so git tracks the empty directory. It does not
create `hypothesis.md`, `methodology.md`, `dataset_manifest.json`, or
`decision_log.md`, and it introduces no new manifest schema —
`schema_version` stays `1`.

**Rationale.** Those four files are authored content: a hypothesis, a
methodology, a dataset manifest, and a decision log are things a human
writes as a project's evidence actually takes shape, not boilerplate a
generator can stub out. Scaffolding them empty would create a file that
*looks* like recorded evidence at a glance — same filename a reviewer
or a future `ArchiveVerifier` would look for — while containing
nothing, which is a worse trap than the file simply not existing yet.
Directories carry no such ambiguity: an empty `dataset_hashes/` reads
unambiguously as "not populated yet," which is the truth. This mirrors
AD-030's framing of the manifest concept itself as an early
preservation guard, not the complete evidence system — the scaffold
generator extends *structure*, never substitutes for the human
judgment Standard Section 5's content requirements exist to capture.

### AD-039: Archive manifest tooling remains in `tools/` until `ArchiveVerifier` provides a concrete governance consumer

**Decision:** `scaffold_project_archive()` is added to
`tools/archive_manifest.py` alongside `build_manifest()` and
`write_manifest()`, not moved or duplicated into `core/governance/`.

**Rationale.** `core/governance/` remains intentionally empty in Phase
0 (per this module's own docstring and AD-030) because there is no
concrete consumer of manifest data yet — `ArchiveVerifier`
(`docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.4) is still a forward
reference, not a package with behavior to slot this into. Moving
scaffold generation into `core/governance/` now would be exactly the
kind of speculative, consumer-less abstraction this platform's Phase 0
discipline (AD-025, AD-028) has consistently deferred elsewhere:
premature scoping decisions harden ahead of the first real usage
telling us what shape they should take. `tools/` is where
`archive_manifest.py` already lives, already tested, already the
reference implementation this doc's own text points to; extending it
in place keeps one file with one purpose instead of splitting related
logic across a package boundary that has nothing on the other side yet.
The move happens later, when `ArchiveVerifier` exists and needs it as
an input contract — not preemptively.

### AD-040: Step 7 ships `GateResult`/`GateStatus`/`DecisionMetadata` only, not the full Validation apparatus

**Decision:** `core/validation/gate_result.py` adds three frozen types
— `GateStatus` (a three-way `PASS`/`FAIL`/`AMBIGUOUS` enum, not a
boolean), `DecisionMetadata` (reviewer, review level, date —
attribution only), and `GateResult` (gate name, status, summary,
`evidence_refs`, decision) — plus two concrete gate functions,
`core.validation.gates.signal_independence` and
`.economic_rationale`. The `Gate` Protocol, `GateRunner`,
`ValidationRegistry`, and `GateContext` that
`docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.2 sketches alongside
`GateResult` are not built. Neither is a `LifecyclePhase` enum or any
workflow-state concept, and no historical gate review is backfilled
into a `GateResult` (see AD-044).

**Rationale.** `GateResult` is the one piece of Section 4.2's sketch
every gate review to date already needed in substance —
`GateStatus` mirrors the PASS/FAIL/ambiguous shape
`phase6_economic_validation_2026-07-19.json` and
`core.governance.freeze_verifier.FreezeStatus` already use. The
runner/registry/protocol machinery around it exists in the sketch to
support *pluggable, registered* gates dispatched by phase; today there
are exactly two gates and one caller shape (a script invoking a
function directly), which is precisely the "consumer-less
abstraction" AD-005, AD-025, AD-028, and AD-039 have each already
ruled out in this repository for the same reason: building a registry
ahead of a second concrete way of calling gates would harden a shape
before anything tells us what it should be. `GateResult` moves first
because it is a plain, dependency-free record type with a real
consumer as of this increment (the two gate functions themselves, and
Reporting later); the protocol/runner/registry layer waits for a
second calling pattern the way AD-033's `FreezeVerifier` and AD-036's
`ProjectRegistry` each waited for a second concrete need before
widening their own interfaces.

### AD-041: Gate functions evaluate already-produced statistics; they never compute one

**Decision:** `signal_independence.evaluate_signal_independence_gate`
and `economic_rationale.evaluate_economic_rationale_gate` each take an
already-computed statistic as a plain input parameter
(`measured_overlap`, `measured_value`) and compare it to a
caller-supplied frozen threshold. Neither function imports
`core.statistics`, calls a correlation/IC/permutation/significance
routine, or performs any calculation beyond the single mechanical
comparison against the frozen criterion.

**Rationale.** `docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.2 already
states this boundary in prose — Validation "Owns... Gate/phase
definitions and their results (not the underlying statistics — those
are computed by Statistics and merely *carried* by Validation's result
objects)" — but the boundary was not previously load-bearing in any
committed Validation code, since no Validation code existed. Making
Statistics the sole owner of every IC, correlation, permutation-test,
and significance calculation (as Section 4.3 already assigns) and
Validation a pure consumer of the result keeps the dependency graph
one-directional and the two domains independently testable:
`core.statistics` functions are exercised with plain numeric fixtures
with no frozen-criteria or freeze-verification concept in scope at
all, and `core.validation.gates` functions are exercised with
synthetic already-computed values with no correlation math in scope
at all. A gate that both computed and evaluated a statistic would
blur exactly the seam Section 4.2 draws, and would make Statistics'
`core.statistics.significance` module ambiguous about whether it or
Validation owns a given calculation going forward.

### AD-042: `GateResult.evidence_refs` are references to immutable evidence locations, not scoped to archive-manifest directories

**Decision:** `GateResult.evidence_refs` is a `tuple[str, ...]` of
references to immutable evidence locations. GateResult stores
references to immutable evidence locations. It does not own,
duplicate, or mutate evidence.

**Rationale.** An earlier draft of this field scoped it specifically
to archive-manifest evidence subdirectories (AD-038's
`dataset_hashes/`, `experiment_results/`, `reviewer_reports/`). That
scoping is too narrow for what a real gate result cites in practice —
`phase6_economic_validation_2026-07-19.json` and the Gate 1 report
both cite a mix of frozen source documents, commit hashes, and JSON
result files, not exclusively archive-manifest paths, and a future
gate has no reason to be restricted to that one evidence layout. The
field's actual invariant is narrower and more durable than any one
directory convention: whatever a reference names must already be
immutable and already exist independently of this record. Both gate
functions in this increment honor that invariant identically —
`evidence_refs` is accepted from the caller and passed through into
the returned `GateResult` completely unmodified (see
`signal_independence.py` and `economic_rationale.py`); neither
function reads, writes, hashes, or validates whatever a reference
points to. `GateResult` is a citation list, never a copy.

### AD-043: A missing frozen acceptance criterion (or a failed freeze) is a governance failure, not a statistical judgment call

**Decision:** Both gate functions render `GateStatus.AMBIGUOUS` in two
distinct situations, each with its own fixed rationale text rather
than an ad hoc one: (1) `verify_freeze()` does not return `VERIFIED`
for the caller-supplied `freeze_commit_ref`/`freeze_covered_paths`, or
(2) `frozen_threshold`/`threshold_direction` is `None`, for which the
rationale is always exactly "Acceptance criterion was not frozen
before validation." Neither function ever substitutes a threshold of
its own to force a `PASS`/`FAIL` in either case.

**Rationale.** `experiments/validate_h3_gate1_independence.py`
documents the real historical instance of case (2): Gate 1's frozen
plan specifies a comparison to run but never froze a numeric
overlap threshold, so the script "does not write a PASS/FAIL
determination" and requires human interpretation instead. Framing
that outcome as *statistical* ambiguity — as if the measured overlap
value itself were borderline — would misattribute the cause: the
measurement can be perfectly clean and unambiguous while the process
around it is incomplete (no criterion was ever frozen to compare it
against). Treating both a missing criterion and a failed freeze
verification as the same `AMBIGUOUS` status, with the same "gate
cannot mechanically decide" semantics, keeps that distinction correct:
`AMBIGUOUS` means the gate lacks a trustworthy frozen basis to render
a verdict at all, never that a comparison came out close. `PASS`/
`FAIL` are reserved exclusively for the case where both a verified
freeze and an explicit frozen threshold exist and the comparison is
purely mechanical — consistent with `docs/RESEARCH_GOVERNANCE_STANDARD.md`
Section 7's "render PASS, FAIL, or INCONCLUSIVE against pre-registered
criteria only," never criteria invented after the fact.

### AD-044: Gate functions take explicit typed parameters, not a `GateContext`

**Decision:** `evaluate_signal_independence_gate` and
`evaluate_economic_rationale_gate` each take a flat set of explicit
keyword-only parameters (the measured value, the frozen threshold and
its comparison direction, the freeze commit ref and covered paths,
evidence refs, and a `DecisionMetadata`) rather than a single
`GateContext` object bundling a frozen dataset reference and frozen
methodology parameters, as `docs/PLATFORM_ARCHITECTURE_V1.md` Section
4.2 sketches. No `GateContext` type is defined anywhere in this
increment.

**Rationale.** Same pattern as AD-033's `FreezeVerifier.verify_freeze`,
which takes a raw `commit_ref: str` instead of the sketch's `FreezeId`
because no registry backing `FreezeId` exists yet: `GateContext` in
the architecture sketch exists to serve a `Gate` Protocol and
`GateRunner` that call gates generically, without knowing which
concrete gate they are invoking. Neither exists yet (AD-040), and with
exactly two gates called directly by name, a generic context object
would be pure indirection — every field on it would still need to be
supplied by the same caller that would otherwise pass explicit
parameters, with an extra layer of attribute access and no consumer
that benefits from the genericity. When a second calling pattern
(a `GateRunner` dispatching by name, for instance) actually needs to
pass the same bundle of frozen inputs to gates it does not know the
concrete signature of, `GateContext` is the natural type to introduce
then — not before.

### AD-045: `DecisionLogger` superseded by template-based decision log discipline

**Decision:** `core/governance/decision_logger.py` — named in
`docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md`'s Step 4 file list and
sketched as a `DecisionLogger` Protocol in
`docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.4 — will not be
implemented. No code, abstraction, or stub is introduced by this AD;
it is a state-alignment record only, closing out a Migration Plan line
item that a pre-implementation architecture checkpoint found to already
be satisfied by a different, already-existing mechanism.

**Original intent.** `docs/PLATFORM_ARCHITECTURE_V1.md`'s own
retrospective-mapping table (Section 8-ish, the "Retrospective item →
Owning domain → Interface" table) states the job plainly: "Decision-log
entry scaffolding | Governance | `DecisionLogger.log()`, invoked
automatically by Research at every `advance_phase()` call rather than
authored by hand." The Protocol itself (`class DecisionLogger(Protocol):
def log(self, project_id: ProjectId, entry: DecisionLogEntry) -> None:
...`) was designed to replace `docs/RESEARCH_GOVERNANCE_STANDARD.md`
Section 5's hand-authored `decision_log.md` convention with an
automated, structurally-enforced append-only record, directly targeting
`docs/RESEARCH_PLATFORM_RETROSPECTIVE.md` Section 2's finding that
`reference_h3/decision_log.md` Entry 15 was itself "written
retroactively" against its own freeze commit.

**Why the assumption changed.** Two things this AD did not invent, both
already committed, jointly close the gap `DecisionLogger` was designed
to fill:

1. **AD-038 already chose hand-authorship over structural scaffolding
   for this exact artifact**, for reasons that apply identically to an
   automated `.log()` call. `scaffold_project_archive()` deliberately
   does not create `decision_log.md` — "a hypothesis, a methodology, a
   dataset manifest, and a decision log are things a human writes as a
   project's evidence actually takes shape... Scaffolding them empty
   would create a file that looks like recorded evidence at a glance...
   while containing nothing, which is a worse trap than the file simply
   not existing yet." A mechanically-generated log entry at a phase
   transition is the same trap in a different shape: it would satisfy
   "an entry exists" while omitting the actual content
   `docs/templates/decision_log_template.md` requires — "which
   candidate was ranked where and why," "known limitations" — fields
   that are, and can only be, human judgment. AD-038 already decided
   this platform treats decision-log content as authored evidence, not
   generated boilerplate, and that decision was never scoped to just
   the archive scaffold generator.
2. **AD-036 already deferred `DecisionLogger`'s own trigger.**
   `DecisionLogger.log()` was designed to be invoked *by*
   `advance_phase()`, not called standalone — the architecture doc is
   explicit that automation, not hand-authorship, is the point. AD-036
   confirms `ProjectRegistry` v0.1 has "no `advance_phase`-shaped
   lifecycle-transition method," and no other module implements one
   either (verified by repository-wide search: zero `advance_phase`
   definitions anywhere in `core/`). Building `DecisionLogger` today
   would mean building a module with zero real callers — the exact
   "consumer-less abstraction" pattern AD-005, AD-025, AD-028, AD-039,
   AD-040, and AD-044 have each already refused in this repository, for
   the same reason each time: a shape hardens before anything tells it
   what it should be.

**What already does the job, verified against the current repository,
not the plan.** `docs/templates/decision_log_template.md` is the
scaffolding piece that *was* built — a structured, append-only entry
format (Decision / Evidence references / Governance status / Reviewer
level / Known limitations) that already exists and is already
production-proven: `research_archive/reference_h3/decision_log.md`
carries 18 entries in this exact shape, and
`docs/RESEARCH_PLATFORM_RETROSPECTIVE.md` Section 1 names the
"archive discipline (supersession, never silent edit)" — the same
discipline the template encodes — as one of the platform's genuine
strengths, "followed consistently, including during an active
incident." No code gap remains between what `DecisionLogger` would have
provided and what the template-plus-hand-authorship pattern already
provides; the difference is automation of a step this platform has
independently decided (AD-038) should stay manual.

**Final decision.** No `DecisionLogger` implementation is planned.
`core/governance/` is not expanded by this AD. If a future concrete
need re-opens automated decision logging — for instance, once
`advance_phase()` exists and a real caller wants a *mechanical* entry
(phase, timestamp, commit hash) alongside, not instead of, the
human-authored narrative — that is a new decision to make at that time,
against that concrete need, not a resumption of this one.

**Migration/status.** `research_archive/reference_h3/decision_log.md`
and `docs/templates/decision_log_template.md` remain the canonical
decision-log mechanism, unchanged by this AD. `docs/PLATFORM_ARCHITECTURE_V1.md`
Section 4.4's `DecisionLogger` Protocol and
`docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md`'s references to it are
left as-written, per this repository's established convention that
ADRs record divergence from those two documents rather than editing
them retroactively (the same convention AD-036 and AD-040 already
follow for `ProjectRegistry` and the `Gate` Protocol respectively) —
this AD is the authoritative record that the divergence is permanent,
not an oversight.

### AD-046: Reporting input boundary — `ReportBuilder` accepts `GateResult` directly, not `project_id`/`report_type`

**Decision:** Step 8 v0.1's `ReportBuilder.build()` takes a `GateResult`
(from `core/validation/gate_result.py`) directly as its input, not the
`(project_id: ProjectId, report_type: ReportType)` signature
`docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.5 sketches. This is a
pre-implementation record, written before `core/reporting/` exists —
unlike AD-033/AD-036/AD-040, which documented a narrower interface
already built, this AD fixes the narrower interface *as* the target
before any code is written, so Step 8 does not start from the sketch's
signature and discover the gap mid-implementation.

**Why the sketch's signature cannot be implemented today.** Section
4.5's own sketch requires resolving "the `GateResult`s belonging to
`project_id`." No such lookup exists. Verified directly, not inferred:

- `GateResult` (`core/validation/gate_result.py`) has exactly five
  fields — `gate_name`, `status`, `summary`, `evidence_refs`,
  `decision: DecisionMetadata` — and `DecisionMetadata` carries only
  `reviewer`, `review_level`, `decided_at`. Neither type has a
  `project_id` field or anything resembling one.
- Every `GateResult(...)` construction site in the repository
  (`core/validation/gates/signal_independence.py`,
  `core/validation/gates/economic_rationale.py`) confirms this — none
  passes or references a `ProjectId`.
- `ProjectRegistry` (`core/research/project_registry.py`, added under
  AD-036) resolves identity and metadata only — `register_project`,
  `get_project`, `list_projects` — and `Project`
  (`core/research/project.py`) has no field holding gate results or any
  other reference back to Validation-domain output.

There is, as of this AD, no code path from a `ProjectId` to the
`GateResult`s associated with it in either direction. Building
`ReportBuilder.build(project_id, report_type)` against that gap would
mean either fabricating a lookup Reporting has no business owning, or
shipping a signature with no real implementation behind its first
parameter.

**Rationale.**

- **Avoids implicit Research→Validation ownership.** A Reporting-owned
  `project_id → GateResult[]` lookup would make Reporting the de facto
  join point between two domains it only consumes from — exactly the
  kind of cross-domain orchestration §3's dependency rules reserve for
  Research, not Reporting (`docs/PLATFORM_ARCHITECTURE_V1.md` Section 3:
  Reporting is "a true leaf; no domain's correctness can ever depend on
  Reporting having run"). If a `ProjectId → GateResult` association is
  ever needed, that is Research's or Validation's decision to expose,
  not Reporting's to invent as a side effect of wanting a build-time
  parameter.
- **Follows the established narrower-interface pattern.** Same
  discipline as AD-033 (`FreezeVerifier` takes a raw `commit_ref`, not a
  `FreezeId` backed by a registry that didn't exist yet), AD-036
  (`ProjectRegistry` implements exactly identity + metadata, not the
  sketch's filtering or id-minting), and AD-040 (`GateResult`/
  `GateStatus`/`DecisionMetadata` only, not the full `Gate`/
  `GateRunner`/`ValidationRegistry` apparatus). In each case the
  narrower slice was recorded explicitly rather than left as a silent
  gap between the architecture doc and the code.
- **Avoids a Validation-domain schema change as an implementation side
  effect.** Adding `project_id` to `GateResult` would modify a frozen,
  tested, already-shipped Validation-domain type (Step 7, committed at
  `5c42422`) to satisfy a Reporting-domain convenience. That is a
  cross-domain decision belonging to Validation as the owning domain
  with Reporting as the requesting consumer — not something this AD
  authorizes, and not something `ReportBuilder`'s implementation should
  decide unilaterally by needing it.

**Boundary rules for `ReportBuilder`/`Renderer`, stated explicitly so
Step 8 does not have to rediscover them mid-implementation:**

- Reporting renders; it never validates. It does not compute a
  PASS/FAIL/AMBIGUOUS outcome or any other judgment — it displays
  `GateResult.status` as given.
- Reporting displays; it never interprets. `summary` is reprinted
  verbatim; a renderer does not parse it back into numbers to reformat,
  round, or re-derive a conclusion from it.
- Reporting does not resolve evidence references. `evidence_refs`
  (AD-042: opaque references to immutable evidence locations) are
  displayed as citations only — never dereferenced, fetched, or
  validated. That is `ArchiveVerifier`/`ReproducibilityChecker`
  territory, neither of which exists and neither of which this domain
  is.
- Reporting does not compute statistics. Any renderer needing a
  differently-formatted number than `GateResult` already carries is a
  new, explicit Validation/Statistics-domain question, not something
  `Renderer` derives itself.

**Minimal Step 8 v0.1 implementation scope, per this AD:**

- `ReportBuilder.build(gate_result: GateResult) -> ReportModel`.
- One JSON `Renderer` — closest to `dataclasses.asdict()`, built first
  as the lowest-risk validation of `ReportBuilder`'s shape.
- One Markdown `Renderer` — the actual Step 8 deliverable per
  `docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md`.
- No `ReportRegistry` — same "no registry before a second consumer"
  discipline AD-040 already applies to `GateRunner`/
  `ValidationRegistry`.
- No historical rendering — applies only to `GateResult`s produced
  going forward, per the Migration Plan's own Step 8 scope.

**What this AD does not decide.** Whether `GateResult` should ever gain
a `project_id` field, and whether a `ProjectId → GateResult` lookup
should exist anywhere, are left open — to be raised, if a concrete need
arises, as a Validation- or Research-domain decision, not resolved here
as a precondition Reporting imposes on those domains. Section 3's
already-flagged gaps (raw statistics not structured past `summary`;
`VerificationResult` detail not carried into `GateResult`) remain
separately deferred, per `docs/REPORTING_ARCHITECTURE_PROPOSAL.md`
Section 3, to be resolved against a real second need rather than
pre-solved here.

**Status.** No code is introduced by this AD. `core/reporting/` remains
unbuilt; this record fixes the input boundary Step 8 must build
against.

---

### AD-051: An empty `covered_paths` set is `UNVERIFIABLE`, not `VERIFIED`

**Numbering.** The accepted ceiling was AD-046. AD-047–050 are left
reserved for `docs/PHASE_4_STEP9_DRAFT_ADRS.md`, which provisionally
claims them and is already cross-referenced by those numbers; this
increment takes AD-051 rather than renumber settled cross-references.
The two ADs' content does not conflict either way.

**Decision.** `core/governance/freeze_verifier.py`'s `verify_freeze`
returns `FreezeStatus.UNVERIFIABLE` when `covered_paths` is empty. No new
enum member is introduced; the existing three-way contract (AD-033) is
unchanged.

**Why.** Before this change, `errors` and `drifted` were populated
exclusively inside the per-path loop, so an empty `covered_paths` meant
the loop body never ran, both lists stayed empty, and execution fell
through to `VERIFIED`. A caller could claim a freeze was verified while
supplying zero evidence, and the function would agree.

This was load-bearing, not cosmetic. AD-043 makes both Validation gates
(`signal_independence`, `economic_rationale`) render `AMBIGUOUS` whenever
`verify_freeze` does not return `VERIFIED`. A gate called with
`freeze_covered_paths=[]` sailed past that safeguard and was free to
render `PASS`/`FAIL` on zero freeze coverage — defeating the one
invariant that exists to keep a gate from evaluating against an
untrustworthy basis. The hole was live and real, but no archived
governance record is known to have been produced by an empty-coverage
call; nothing had exercised it with real data.

**Why `UNVERIFIABLE` and not a new status.** `FreezeStatus`'s own
docstring already frames `UNVERIFIABLE` as a run that fails to complete —
categorically distinct from a completed run that finds drift. A run given
zero paths has nothing to complete; it fits that category without
straining it. Both gate call sites branch on `is not VERIFIED`, never on
a specific status, so reuse requires zero changes to either gate. A
distinct `EMPTY`/`NO_COVERAGE` value would let a future caller
pattern-match on it — but no such caller exists or is proposed, and
inventing the distinction without a consumer is the premature
abstraction AD-005/AD-025/AD-028 already rule out.

**Mechanism.** One additive early return between two pieces of unmodified
logic: after commit resolution (so the unresolvable-ref branch still
returns first, still with `resolved_hash=None`) and before the per-path
loop (whose branches are untouched). The guard performs no git
invocation — it is a length check on an already-materialized list, so the
module's read-only posture is preserved. `resolved_hash` is deliberately
carried into the empty-coverage result so that `resolved_hash is None`
continues to mean exactly "the commit ref itself did not resolve", never
anything else.

**What this AD does not claim to fix.** It closes exactly one hole:
zero-evidence verification can no longer be mistaken for success. It
checks *cardinality*, not *relevance*, and the following remain
unaddressed — by design, and disclosed here so no future document can
cite this AD as more than it is:

- **Meaningless coverage.** `covered_paths=["README.md"]` passes the
  non-empty check and is verified faithfully against that one file —
  a true answer to a question nobody meaning "was the methodology
  frozen?" intended to ask.
- **Incomplete coverage.** `verify_freeze` has no independent source of
  truth for what the complete frozen set should have been;
  `covered_paths` is caller-supplied and there is no `FreezeId`-backed
  registry to check it against (AD-033).
- **Drift outside declared coverage.** A file that drifted but was never
  named is invisible to `verify_freeze`, before and after this change.
- **Commit-reference authentication.** `verify_freeze` verifies fidelity
  to whatever `commit_ref` it is given; it cannot confirm that ref is the
  one originally claimed as the freeze point. That is a provenance
  problem one layer up.

Coverage *adequacy* remains a human review judgment with no mechanism
behind it anywhere in this codebase. A `VERIFIED` result proves the
*named paths* were frozen — never that the *methodology* was.

**Scope.** `signal_independence.py`, `economic_rationale.py`,
`GateResult`, `GateStatus`, `DecisionMetadata`, `VerificationResult`'s
shape, and every function signature are unchanged. Both gates inherit the
fix with no code of their own, demonstrated by a propagation test in each
gate's suite. Four tests were added, none modified. The AD-047 (draft)
re-disclosure obligation — a dated governance deviation record stating
that `verify_freeze(commit_ref, [])` *returned* `VERIFIED` — is
independent of this AD and is **not** discharged by it: that disclosure
records the hole's historical existence, this AD closes it going forward.
Both are needed.

---

### AD-047: Freeze verification is scope-bounded; the empty-covered-paths hole at baseline `2c7fb2c` was disclosed, and is guarded in new code

**Numbering.** AD-047-050 were reserved for this document when AD-051 was
accepted (`4c7ca8d`): AD-051 took the next available number instead of
AD-047 specifically so as not to renumber cross-references already made
to AD-047-050 in `docs/PHASE_4_STEP9_DRAFT_ADRS.md` (see AD-051's own
"Numbering" paragraph, above). AD-047-050 are accepted here, in this
reserved sequence, in the order `docs/PHASE_4_STEP9_DRAFT_ADRS.md`'s
"Adoption condition" paragraph fixes: AD-047 - carrying prerequisite
A-1's disclosure content - before AD-048, AD-049, and AD-050.
**Accepting AD-047 does not itself close prerequisite A-1**; see the
limb-by-limb disclosure accounting immediately below.

**Historical framing, stated first.** This AD was drafted at `8a91d35`
against baseline **`2c7fb2c`** (tag `phase4-final-before-h4-20260722`).
Every statement below about `freeze_verifier.py`'s behaviour describes
the repository **as it stood at that baseline** — not as it stands at
current `HEAD`. The defect described was subsequently closed by AD-051
(commit `4c7ca8d`). What this AD contributes is unchanged by that fix:
the historical disclosure, the guard in new Validation code, and the
claim bound all still stand.

**Relationship to AD-051: coexisting; neither supersedes the other.**
AD-051 is **not superseded, not amended, and not renumbered by this
AD**, and nothing here modifies its accepted meaning. The two sit at
different layers and both remain in force:

- **AD-047 (this AD)** documents the **historical architectural
  disclosure** — that the hole existed at `2c7fb2c`, what it made
  vacuously satisfiable, and what a `VerificationResult` produced under
  it is and is not worth — and places a guard in **new Validation
  code**, before any gate runs.
- **AD-051** records the **implemented remediation** inside
  `core/governance/freeze_verifier.py` itself: an empty `covered_paths`
  returns `FreezeStatus.UNVERIFIABLE`.

AD-047 does not supersede AD-051, and AD-051 does not discharge
AD-047's disclosure obligation — AD-051's own "Scope" paragraph states
that in terms. Both are needed.

**Decision.** Three parts, and the first was not conditional on the
other two.

1. **Disclosure.** A dated governance deviation record was required to
   be re-issued, stating that at baseline `2c7fb2c`
   `core/governance/freeze_verifier.py`'s
   `verify_freeze(commit_ref, [])` *returned* `FreezeStatus.VERIFIED`,
   that this behaviour was live at that baseline with no guard and no
   test in either direction, that the original remediation record
   (`docs/PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md`) was
   destroyed **as a committed object** in the 2026-07-21 incident — **no
   reachable git ref contains it**, while byte-identical copies of its
   content survive off-repository as untracked files in non-canonical
   working trees, so that its content is recoverable and its commit
   provenance is not — and that **every `VerificationResult` in the
   archive is only as strong as the covered-path set it was called
   with.** This obligation stood whether or not Step 9 proceeded, and it
   is **not weakened, narrowed, or retired by having been met.**

   **What has been filed against this obligation, limb by limb.**
   Prerequisite A-1 of
   [`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
   §4.1 is two-limbed on its face — done when "The disclosure exists in
   `docs/`" **and** "the PR0 ruling is closed or confirmed obsolete".
   The two limbs stand in different states and are stated separately
   here rather than summed.

   - **Limb 1 — the disclosure — is discharged.** It was closed by
     [`PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md`](PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md)
     (`8bd8f8a`), the dated record in `docs/` this part required.
     [`PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md`](PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md)
     §6 records limb 1 as "**Closed** at `8bd8f8a`", and its §5 states
     that ruling "does not discharge A-1 limb 1. That limb was closed by
     `8bd8f8a` and is not re-decided here."
   - **Limb 2 — the ruling — remains conditional, exactly as the accepted
     A-1 ruling states it.**
     [`PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md`](PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md)
     (`aca36fb`) disposes of both items of the 2026-07-21 ruling request
     — item 1 determined as a statement of fact (§2.1), item 2 VOID for
     failure of its own stated condition (§2.2) — and its §6 records
     limb 2 as "**Closed if this ruling is accepted.** On acceptance,
     limb 2's condition is met by §2 of this record." That condition is
     restated here without alteration and is **not** read as satisfied
     by this AD.

   **Consequently, A-1 as a whole is not stated here as discharged.**
   The accepted ruling's own closing statement governs and is adopted
   verbatim: "Until that acceptance, limb 2 stays open, A-1 stays
   undischarged, and Step 9 stays blocked — exactly as it stood at
   `8bd8f8a`." Resolution §4.1's rule that "Step 9 does not start until
   every item below is closed **in writing**" is unchanged by this AD,
   and A-2 … A-9 remain open on their own terms regardless of A-1's
   disposition.

   The destroyed-record wording above is stated as those records state
   it (re-disclosure record §1.4 and §1.5 rows 3–4), which corrected
   this AD's original, broader "exists in no reachable git ref" phrasing
   on evidence.
2. **Guard, in new code only.** `GateContext` construction rejects an
   empty `freeze_covered_paths`, and `GateRunner` refuses the run before
   any gate executes. `GateRunRecord` stores the **full covered-path
   list**, not a count. `freeze_verifier.py` is **not modified by this
   AD** — the guard lives in new Validation code, so the baseline stays
   untouched by Step 9 and INV-12 holds. That is not asserted here; it is
   [`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
   §3's decision D-2 — "`verify_freeze` is **not modified** by Step 9.
   New Validation code refuses an empty covered-path set; the full path
   list is recorded; the permitted claim is the narrow one (§2.3)" —
   which that decision table binds on AD-047 by name, and which this
   part restates rather than extends.

   **Why this guard is still required after AD-051: the two act at
   different layers.** AD-051 prevents empty coverage from being
   mistaken for success **inside freeze verification** — `verify_freeze`
   itself now returns `UNVERIFIABLE`. This AD prevents a run with empty
   coverage from **executing at all**: `GateRunner` refuses **before any
   gate runs**, rather than letting every gate execute and render
   `AMBIGUOUS` downstream of an `UNVERIFIABLE` verification.
   `GateRunRecord`'s full-path-list requirement is a third thing again —
   an **evidence-recording** obligation that no change to
   `verify_freeze` can satisfy, because a status value cannot carry its
   own coverage set (restated INV-3, below). Neither requirement is
   redundant with AD-051 and neither is weakened by it.
3. **Claim bound.** A `VERIFIED` result licenses exactly one statement:
   *these named paths were byte-identical to their content at the
   claimed commit, with no committed or uncommitted drift since.* No
   Step 9 artifact may render it as "the methodology was frozen."

**Rationale.** The mechanism was verified by reading
`freeze_verifier.py:154-170` **at baseline `2c7fb2c`**
(`git show 2c7fb2c:core/governance/freeze_verifier.py`): `errors` and
`drifted` were populated only inside `for path in paths`; an empty
iterable left both empty and the function fell through to
`else: status = VERIFIED`. **That line range is a citation into the
baseline, not into current `HEAD`** — at `HEAD` the same file carries
AD-051's early return at lines 155-168 and the block cited above has
moved to 170-186, so reading that line range against `HEAD` would not
reproduce the finding. This was load-bearing rather than cosmetic
because AD-043 makes a gate render `AMBIGUOUS` when verification is not
`VERIFIED` — so at that baseline a gate with **zero freeze coverage**
was free to render `PASS`, and any invariant of the form "no gate
executes against an unverified freeze" was **vacuously satisfiable**. A
pre/post freeze bracket over an empty set agrees with itself perfectly
while proving nothing.

**Why the guard is not the whole answer.** Non-emptiness is necessary
and not sufficient. A path set containing only `README.md` satisfies the
guard and verifies exactly as vacuously as the empty set. That is why
part 3 exists and why the full path list — not a count — is recorded:
adequacy of coverage is a **human review judgment**, disclosed as such,
and Step 9 does not mechanize it. Storing a count and calling the
verification non-vacuous would reproduce, inside the correction, the
claim-stronger-than-mechanism failure this AD exists to close.

**Why the baseline is not fixed here.** *(Title retained verbatim.
[`PHASE_4_PR0_REMEDIATION_PROPOSAL.md`](PHASE_4_PR0_REMEDIATION_PROPOSAL.md)'s
"Relationship to Step 9" cites this section by that title — "AD-047,
'why the baseline is not fixed here'" — and that citation must keep
resolving. "Here" has always meant **this AD and Step 9**, which is the
sense
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
§2.5 uses when it rejects "fixing `freeze_verifier.py` inside Step 9";
it has never meant "nowhere, ever". The body below records what has
since happened elsewhere.)*

A guard inside `verify_freeze` itself was identified here as the right
long-term answer, and was deliberately left out of Step 9: it is a
baseline modification, it required its own governance ruling, and
folding it into Step 9 would have repeated the exact scope violation PR0
was returned for. It was named as a separate increment with its own AD —
and that is exactly what it became.

**That increment was subsequently completed.** Its proposal landed at
`ced8636`, its implementation at `4c7ca8d`, and the decision is recorded
as **AD-051**; the split is determined as a matter of fact in
[`PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md`](PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md)
§2.1. What survives from this AD is the **architectural disclosure** —
the scope-bounded reading of freeze verification, the claim bound, and
the record of what the baseline did — none of which the fix discharges.
**AD-047 does not supersede AD-051.**

**Invariant restated.** *No gate executes against a freeze verification
whose covered-path set is empty, unresolved, or drifted, and no
`VERIFIED` result is admitted as evidence without its covered-path list
recorded alongside it.*

**Migration/status.** `freeze_verifier.py` **was modified by AD-051**
(commit `4c7ca8d`, one additive early return plus four additive tests);
**AD-047 introduces no further modification of it.** That modification
landed as its own increment outside Step 9, under its own proposal and
its own AD.

**That it is therefore not a Step 9 baseline change is read from the
Resolution, not asserted here.** INV-12 is a Step 9 invariant, and the
Resolution fixes its scope in two places, both of which put this
increment outside it:
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
§2.5 rejects "fixing `freeze_verifier.py` inside Step 9" and rules that
"The baseline fix is a separate increment with its own AD"; §4.1 then
lists that fix under "**Not a prerequisite, and explicitly deferred:**
the `freeze_verifier` baseline fix (§2.5), which is its own later
increment with its own ruling." `4c7ca8d` is that increment — the
disposition §2.5 ruled for, arrived at as
[`PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md`](PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md)
§2.1 determines as a matter of fact. What INV-12 constrains — Step 9's
own work — is untouched. This AD claims nothing beyond that reading, and
in particular does not rule on how INV-12 would apply to any other
modification of a baseline file.

Everything this AD requires still lives entirely in new Validation code
(`GateContext`, `GateRunner`, `GateRunRecord`). No existing
`VerificationResult` is invalidated by this AD; they are re-scoped by the
disclosure, which states what they did and did not prove — and, as the
re-disclosure record §4.2 states, no historical result is retroactively
improved by the fix either.

---

### AD-048: `DecisionRecorder` — mechanical transition records under AD-045's own re-opening condition

**Relationship to AD-045: clarifying, not superseding.** AD-045 is
**not superseded, not amended, and remains in force in full.** Its
decision — *"No `DecisionLogger` implementation is planned;
`core/governance/` is not expanded by this AD"* — remains **literally
true** after this AD: no `DecisionLogger` is built, no code writes
`decision_log.md`, and hand-authored narrative remains the canonical
record of judgment. This AD is the "new decision, against that concrete
need" that AD-045's final paragraph explicitly reserved — made now that
`advance_phase()` gives it a real caller. AD-045 closed with *"not a
resumption of this one"*, which instructs a new decision rather than an
overturned one. **No supersession marker may appear against AD-045 in
the AD index**: a future component wanting to write a judgment field
would cite it as precedent that the no-automated-decision-logging
decision no longer binds, which is precisely the erosion this AD guards
against.

**What AD-045 got right, and still constrains this AD.**

1. **AD-038's authored-evidence principle.** A mechanically generated
   entry would satisfy "an entry exists" while omitting "which candidate
   was ranked where and why" and "known limitations" — fields that are,
   and can only be, human judgment. This AD does not weaken that. It
   authorizes recording **only** facts that are mechanically derivable
   and independently checkable.
2. **The consumer-less-abstraction objection.** AD-045 refused to build
   a component whose only designed trigger did not exist. That objection
   is answered **only** by `advance_phase()` being built first. **This
   AD is void if `DecisionRecorder` is implemented before
   `ProjectRegistry.advance_phase()` has a real caller.** Ordering is a
   condition of this decision, not an implementation detail.

**Decision.** `core/governance/decision_recorder.py` provides an
append-only, hash-chained, externally-anchored store of **mechanical**
phase-transition records.

- **Records, exclusively:** `project_id`, `sequence_number`,
  `from_phase`, `to_phase`, injected UTC timestamp, code commit hash,
  freeze commit ref with its verification outcome **and its full
  covered-path list** (AD-047), gate names with their statuses as plain
  strings, the authorization record (AD-050), evidence refs as opaque
  strings (AD-042), the `ReproductionRecord` reference establishing
  measurement provenance where one exists, and the SHA-256 of the
  predecessor record's canonical serialization.
- **Never records:** rationale, interpretation, narrative, ranking,
  known limitations, or any free-text field capable of carrying them.
  The record is a frozen dataclass with a **closed field set**, and a
  test pins the **exact** serialized key set — so adding any field fails
  a test and forces a new AD rather than a commit. Prose whitelists were
  the mechanism the review found insufficient; this is the same
  discipline `GateStatus` gets.
- **Never writes** `decision_log.md`, nor any file the human authors.
- **Never commits, checks out, or resets anything** (see anchoring
  below).
- **Expressed in primitives and kernel types only.** Governance cannot
  import Validation (`ALLOWED_DEPENDENCIES["governance"] == {"data"}`,
  asserted by `test_detects_forbidden_governance_to_validation_import`).
  The recorder therefore never sees a `GateResult`. Research projects
  gate outcomes down to strings and passes them (AD-049).
- **Storage:** `core.governance.canonical_jsonl`, whose rules (UTF-8 no
  BOM, LF only, single trailing newline, sorted keys) already exist and
  are already tested. `write_canonical_jsonl` rewrites the whole file
  via `path.write_bytes`, so appends are read-append-rewrite with the
  prior prefix verified byte-identical, written atomically (temp +
  replace). **"Atomically" is disambiguated at A9-C6: temp-plus-replace
  makes the *replacement* atomic and leaves the *read-modify-write* not
  atomic.** The known Windows CRLF fragility in this module is inherited
  and must be covered by an explicit fixture, never assumed away.

**Transcription, not certification.** `PLATFORM_ARCHITECTURE_V1.md`
§4.4: Governance "certifies nothing it did not independently re-derive."
The recorder **cannot** re-derive a gate outcome — the forbidden
Governance → Validation edge is exactly what makes it auditable. It
therefore certifies one thing only: that the retained records were not
altered or reordered since they were written. It asserts nothing about
whether a transcribed gate status is true. **The artifact states this in
its own header**, so an auditor cannot read Governance as vouching for
Validation's conclusions.

**Tamper-evidence, at its true strength.** The chain proves no
**retained** record was altered, reordered, or interior-deleted. It
**cannot** prove no record was removed from the tail: truncating after
record *N* leaves a perfectly valid chain, and so does replacing the
file with a fresh genesis chain. **A self-contained chain cannot prove
its own length**, and the operator who would author retroactively is the
same actor who can truncate.

Anchoring is therefore external, and deliberately **not** by
auto-committing. The three parts below have three different roles, and
**only the second of them is the anchor** (A5-C1):

- **Ordering, not anchoring.** every record carries a monotonic
  `sequence_number`;
- **The anchor.** the hand-authored `decision_log.md` entry — written
  anyway under AD-038 — **cites the chain head hash and sequence
  number** at time of writing, giving a human-witnessed anchor at zero
  new machinery;
- **Retention, not anchoring.** the anchoring **commit is performed by a
  human, outside any gate sequence**, under the existing archive
  discipline.

**Why the recorder must not commit.** Two verified reasons. First, the
Governance domain's read-only posture is explicit and load-bearing:
`freeze_verifier.py:41-43` states "nothing in this module ever writes,
commits, checks out, or resets anything" — a committing recorder breaks
that property in the component whose entire value is being trustworthy.
Second, `verify_freeze` derives drift from `git status --porcelain` on
the **working tree** (`freeze_verifier.py:122-126`); an append that
commits mid-run mutates exactly that state, and could flip a pre/post
freeze bracket or mask real drift by committing it. **An anchoring
mechanism capable of altering the evidence is not an anchor.**

**No inherited precedent.** Earlier drafts justified the chain as
inheriting tamper-evidence "the Phase 4 dataset chain already has."
**No such chain exists** — verified: no `prev_hash`/`previous_hash`/
`chain` construct appears anywhere in `core/governance/`.
`ReproductionRecord` binds a hash *set* within a single record; nothing
links record *N* to *N−1*. The chain here is **novel work** and is
justified on its own merits. Overclaim-by-borrowed-authority is the
failure that returned PR0.

---

**Requirements transcribed from the Phase A ruling records — prefixed,
never merged.** Three accepted ruling records place requirements on this
AD, and all three number their consequence lists from `C-1`.
[`PHASE_4_A9_SINGLE_WRITER_RULING_2026-07-22.md`](PHASE_4_A9_SINGLE_WRITER_RULING_2026-07-22.md)
§9 discloses that collision as its F-25 and directs that A-2 "carry all
three sets under distinguishing prefixes", applying the same treatment
retroactively to A-5's and A-8's lists. That direction is followed here.
The three sets are **disjoint in content and colliding in label only**.
Each item below carries its prefix, its source ruling, and the ruling
section it is drawn from; **no item is merged with another, and no item
is restated inside a second block.**

| Prefix | Source ruling record | Consequence list | Items |
|---|---|---|---|
| **A5-C#** | [A-5 — chain anchoring](PHASE_4_A5_CHAIN_ANCHORING_RULING_2026-07-22.md) | §7 | C-1 … C-13 |
| **A8-C#** | [A-8 — machine-artifact location](PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md) | §6 | C-1 … C-11, plus **A8-C12** (2026-07-26 amendment, AD-074, not in the original ruling) |
| **A9-C#** | [A-9 — single writer](PHASE_4_A9_SINGLE_WRITER_RULING_2026-07-22.md) | §9 | A9-C1 … A9-C10 |

Two items from those lists are **not** carried here, because their own
rulings place them elsewhere: A-5 §7's closing paragraph places its C-9
decomposition of *"verified intact and anchored"* on **AD-050**, where it
is recorded as **A5-C9 (AD-050 limb)**; and A-8 §6's closing paragraph
places its R-5 (`GateRunRecord` location) on **AD-049**. Neither is
restated in this AD, and neither is discharged by it.

**None of the three rulings adds a field to the record.** A-5 §7 (F-2),
A-8 §6, and A-9 §9 (F-23) each state this in terms. The closed field set
above stands exactly as written, and the key-set test that pins it is
unchanged.

#### A-5 — chain anchoring (A5-C1 … A5-C13)

**A5-C1 — the anchor is the external human citation, and nothing inside
the chain is** *(A-5 R-1, §4.1)*. `sequence_number`, the predecessor
hash, and the commit are respectively ordering, interior integrity, and
retention. **None of the three is the anchor.**

| Part | Role | The anchor? |
|---|---|---|
| `sequence_number` | Ordering and interior completeness; the short value an anchor names | **No** |
| predecessor hash | Interior integrity: binds record *N* to *N−1* | **No** |
| the citation `(chain, sequence_number, head hash)` in the cycle's `decision_log.md` | External witness, authored by a human in a different artifact under a different discipline | **Yes** |
| the human-performed commit | Retention and co-visibility: divergence becomes a diff on tracked files | **No** |

No wording in this AD may read as though the chain or the commit anchors
itself. The commit is explicitly demoted on stated grounds: this
repository's git history has already failed to be durable — the PR0
remediation record was destroyed and exists in no reachable ref — so a
mechanism whose durability assumption the repository's own history has
falsified cannot be what the provenance claim rests on. The commit
remains **required** by A8-C8, as retention, not as anchor.

**A5-C2 — anchor content and hash domain** *(A-5 R-2, §4.2)*. An anchor
citation consists of exactly three elements: the **chain identity** (the
repository-relative path `research_archive/<cycle_name>/transition_records.jsonl`,
written in full so a reader holding only the citation can find the file);
the **sequence number** of the record being witnessed; and the **head
hash**, rendered `sha256:<64 lowercase hex>` per the repository's single
existing hash-citation convention and computed over **the UTF-8 bytes of
that record's canonical JSON serialization — the exact line
`write_canonical_jsonl` emits for it, excluding the terminating LF**. The
head hash is therefore **byte-identical to the predecessor-hash field
stored in record *N+1***, so verifying an old citation compares it
against a value the file already carries; only the current head requires
hashing a line.

**A5-C3 — rejected hash domains, recorded as closed** *(A-5 R-2, §4.2)*.
A **whole-file hash** is rejected on the decisive ground that a cited
value must remain checkable after further appends: a file hash cited at
sequence 3 is invalidated by the write of sequence 4, immediately and
permanently. A **Merkle root or hash-of-hashes** is rejected (no
consumer; the length problem is unchanged). A **separate running
"chain hash" field** distinct from the predecessor hash is rejected as a
second representation of one fact — the defect Resolution §2.1 rejected
`Project.current_phase` for. Any digest other than SHA-256 is rejected;
the repository has exactly one convention.

**A5-C4 — numbering origin, per-cycle scope, contiguity** *(A-5 R-3.1 –
R-3.3, §4.3)*. Origin is **1**: the first transition record of a cycle
carries `sequence_number = 1`, so **the head's sequence number is
identical to the record count** and a cited `N` is directly a claim that
the chain contained `N` records. Numbering is **per-file and restarts per
cycle**; sequence numbers are not global and do not order transitions
across cycles, which is why A5-C2's chain-identity element is mandatory
rather than inferred. Sequence numbers are **contiguous ascending
integers `1 … N`, with no gaps and no duplicates**; a gap or a duplicate
is a **chain-invalid** condition — verification refuses, and it is not
repaired, not renumbered, and not reported as a warning.

**A5-C5 — the genesis record** *(A-5 R-3.4, §4.3)*. The genesis record's
predecessor-hash **key is present with the JSON value `null`**. Never an
omitted key (the serialized key set is closed and pinned by test, so
omission changes the key set and fails that test), never an empty string,
and never a sentinel such as `"sha256:0000…"` or the SHA-256 of the empty
string — each of which is a value that could be computed and therefore
forged into an interior position, whereas `null` at any sequence other
than 1 is a structural error a verifier detects trivially. **A `null`
predecessor at any sequence other than 1 is a structural error.**

**A5-C6 — a zero-byte chain file is a valid empty chain** *(A-5 R-3.5,
§4.3)*. `read_canonical_jsonl` returns `[]` for a zero-byte file without
error, and that behaviour is adopted rather than guarded against. The
consequence is recorded because it is the sharpest statement of why the
external anchor is not optional: **a chain emptied to zero bytes is
indistinguishable, from the file alone, from a cycle that has never
transitioned.** Only the external witness distinguishes them.

**A5-C7 — the citation grammar, and the slot that carries it** *(A-5
R-4.1 – R-4.2, §4.4)*. The grammar is defined normatively here, in
exactly one place, as a **single self-locating line** in this fixed
order:

```
**Machine chain anchor.** `research_archive/<cycle_name>/transition_records.jsonl` — seq `<N>`, head `sha256:<64 lowercase hex>`
```

Ruled properties: **one line, found by its bold label alone**, without
the surrounding entry conforming to any particular shape — both decision
logs that exist already diverge from the template's entry shape, so a
carrier defined by position within an entry would be unsatisfiable by two
of two real files. **No version token**, because a version token implies
a parser with a version switch and no parser exists or is authorized
(A5-C9); a change to this grammar is a new AD, and existing citations are
never rewritten. **`Not applicable` is an explicit, valid value**, per
the template's own field discipline, and is the correct value for every
entry that records no phase transition and for every cycle that has no
chain.

The slot is **`docs/templates/decision_log_template.md`**, which gains
one new **required** entry field, `**Machine chain anchor.**`, placed
**after `**Evidence references.**` and before `**Governance status.**`** —
it is a citation, of the same class as evidence references, and must not
be confused with a judgment field. That amendment is a
documentation-only change **bound to the same increment that accepts this
AD**, so that the format and its carrier land together and both land
before Phase C can produce anything to cite. **A format with no slot is
the defect A-5 was raised to close; a slot with no format is
unverifiable.**

**A5-C8 — ordering, cardinality, and the one-to-one rule** *(A-5 R-4.3,
§4.4)*. **One citation per entry, in every entry**; entries recording no
transition carry `Not applicable`, so a reader can always distinguish *no
anchor because no transition* from *anchor omitted*. **A transition entry
cites its own record** — `N` is the `sequence_number` of the record that
the transition described by that entry produced, not the chain head at
some later time and not the predecessor — which yields a **one-to-one
correspondence between transition entries and cited sequence numbers**.
**Ordering is fixed:** human authorization → the mechanical append → the
human authors the entry citing the resulting record → the human commits
both files together under existing archive discipline. **A citation can
never name the commit that contains it** — that hash does not exist when
the line is written — and this AD does not require it to; the anchoring
commit is identified after the fact by git, from the tracked file's
history. **Nothing is retrofitted:** existing entries in
`reference_h3/decision_log.md` and
`positive_control_phase3/decision_log.md` are never edited, and the three
legacy archives, which never receive a chain, never receive a citation.

**A5-C9 — the verification procedure splits, and the split is between
machine and human** *(A-5 R-5, §4.5)*. **Internal verification is
mechanical**: recompute each record's canonical serialization and its
hash; check that record *N*'s stored predecessor hash equals record
*N−1*'s computed hash; check contiguity from 1 with no gaps or
duplicates (A5-C4); check that a `null` predecessor appears at sequence 1
and nowhere else (A5-C5). This detects mutation, reorder, insertion,
interior deletion and a forged predecessor — and it detects **nothing**
about the tail. **Anchored verification takes the anchor as an
argument**: the verifier accepts an expected `(sequence_number,
head_hash)` pair **supplied by the caller**, a human reading the citation
from `decision_log.md`, and confirms that the chain retains a record at
that sequence number whose hash is that value. This is how Phase C's
*"tail truncation detectable via the anchor"* criterion is satisfied and
it is the **only** way it is satisfied. **No code reads, parses, or
writes `decision_log.md`.** The verifier never locates an anchor for
itself; INV-10 is strengthened rather than strained, since the human
artifact is not merely un-written-to but un-read-from, so no code path
can develop a dependency on its formatting. Any future proposal to parse
`decision_log.md` is a new AD. **The corresponding decomposition of
AD-050's *"verified intact and anchored"* precondition is recorded in
AD-050, not here.**

**A5-C10 — anchor lag is inherent, disclosed, and not designed away**
*(A-5 R-6, §4.6)*. At any moment, **every record above the last cited
sequence number is unanchored, and during normal operation that is at
least the newest record**, because the citation is authored after the
append. This is not a defect to be closed and no mechanism is introduced
to close it: closing it would require the writer to anchor its own write,
which is A5-C1's rejected self-witnessing, or an automatic commit, which
is rejected at A5-C13. Consequently **no text in this AD, and no artifact
header, describes a chain as "anchored" without qualification.** The
precise property is **anchored through sequence `N`**, where `N` is the
last externally cited value. The window is bounded by discipline, not by
mechanism — the human writes the entry and commits both files in the same
act — and **nothing enforces that.**

**A5-C11 — the provenance claims, at their true strength** *(A-5 §6.1)*.
These are the **maximum** this AD asserts, and each names what it needs.
They are read together with A9-C8, which makes all of them conditional on
the A9-C4 assumption.

> **Claim 1 — chain alone.** *The records retained in this file form an
> unbroken chain from sequence 1 to sequence M: no retained record was
> altered, reordered, or interior-deleted, and no record was inserted
> between two retained records, without breaking a hash link or a
> sequence contiguity check.* Needs the file. Proves nothing about
> records that are not there.
>
> **Claim 2 — chain plus a citation.** *If the record at sequence `N`
> hashes to the cited `H`, then this file still retains, unaltered, the
> entire prefix of the chain that existed when that entry was authored.
> Removal of any record at or below `N` is detectable by a human
> comparing the citation to the file.* Needs the file and an intact
> `decision_log.md` entry. Answers "a self-contained chain cannot prove
> its own length" **only up to `N`**, never above.
>
> **Claim 2a — the entry-by-entry strengthening.** Because every
> transition entry cites its own record (A5-C8), *the number of
> transition entries in `decision_log.md` and the number of records in
> the chain must agree, and each entry's cited sequence number must match
> its position in that ordering.* A disagreement is an audit finding on
> its face, without any judgment about which artifact is wrong.
>
> **Claim 3 — chain plus citation plus commit.** *The chain and its
> witness were co-present in a committed repository state; a subsequent
> change to either is visible as a diff on a tracked file.* Needs an
> intact git history, which is why it is stated last and weakest.

**The honest summary, carried in these terms:**

> Anchoring converts silent, single-file tampering into tampering that
> requires a coordinated and mutually consistent edit to a
> human-authored, append-only, review-disciplined artifact. **It does not
> prevent tampering. It makes one specific class of it visible to a human
> who looks.**

**A5-C12 — what anchoring explicitly does NOT claim** *(A-5 §6.2)*.

| Not claimed | Because |
|---|---|
| **Automatic commit** | Nothing commits anything; the recorder never invokes git in any mode. The anchoring commit is a human act outside any run, and if the human does not perform it, no commit occurs and nothing reports that fact |
| **Automatic immutability** | A JSONL file on disk is fully writable. No filesystem permission is set, no attribute changed, no git hook installed, no CI check added, no lock file written. "Append-only" describes the **discipline**, not a property of the medium |
| **Immutability conferred by committing** | A commit records a state; it does not freeze a file. History can be rewritten, and in this repository history has already been destroyed once with permanent loss |
| **Writer enforcement** | A9-C2's, and it is a stated assumption. A-5 assumes a well-formed chain and specifies what a malformed one looks like; it prevents nothing |
| **Runtime guarantees** | No daemon, monitor, scheduled verification, CI job, or startup check. Verification runs when a human runs it; a chain can sit tampered and unexamined indefinitely |
| **Proof of time** | Record timestamps are injected and self-asserted. There is no trusted clock and no notarization; a timestamp is a claim by the writer, not evidence |
| **Completeness above the last cited `N`** | Structural, not incidental (A5-C10) |
| **That the transcribed content is true** | Unchanged from this AD's transcription-not-certification ruling: Governance cannot re-derive a gate outcome, so the chain attests to bytes, never to whether a transcribed gate status is correct |
| **That a `decision_log.md` citation is itself protected** | The witness is a text file the same actor can edit. Claim 2 is conditional on the entry being intact and says so. The protection is review discipline and visibility, not enforcement |
| **Anything about the three legacy archives** | They have no transition records and never will. Their absence of a chain is the true state, not a gap |

**A5-C13 — re-affirmed rejections, each closed rather than deferred**
*(A-5 R-7, §4.7)*. **Automatic commit on append remains rejected**, on
Resolution §2.2's two grounds re-verified in A-5: the Governance domain's
read-only posture, and the fact that a mid-run commit mutates the
working-tree state `verify_freeze` reads. Not reopened, not softened, not
made configurable. **The git commit is not the anchor** (A5-C1). **No
external timestamping, notary, blockchain, or third-party attestation
service** — no such dependency exists, it would put a network call inside
the domain that exists to be auditable, and no claim in A5-C11 requires
it. **No filesystem-level immutability, no read-only permissions, no git
hook, no CI check.** Each requires a new AD to reopen; none may be
treated as an obvious extension of this one.

#### A-8 — machine-artifact location (A8-C1 … A8-C11, plus A8-C12 amendment)

**A8-C1 — the partition rule, and no platform-level machine artifact**
*(A-8 R-1, §4.1)*. An artifact whose subject is a **single cycle** lives
inside that cycle's evidence package, `research_archive/<cycle_name>/`;
an artifact whose subject **spans cycles and outlives any one of them**
is platform-level and lives in `docs/`. The rule is adopted from
`RESEARCH_LINEAGE_REGISTER.md`'s own scope paragraph, not invented. Under
it, **every governance machine artifact is per-cycle**; the platform-level
tier is human prose and stays that way, and **Step 9 introduces no
platform-level machine artifact.** No record of this AD is ever written
to `docs/`.

**A8-C2 — the canonical path** *(A-8 R-2, §4.2)*. The transition chain is
**one file per cycle**, at

```
<archive_root>/<cycle_name>/transition_records.jsonl
```

where `<archive_root>` is `research_archive/` in this repository and is
**supplied as an injected parameter, never a module-level constant** —
the discipline `scaffold_project_archive` already follows. Never one
global chain, never one per lineage, never one per attempt. The file sits
at the **cycle directory root**, sibling of `decision_log.md`, not inside
`dataset_hashes/`, `experiment_results/`, or `reviewer_reports/`, each of
which has a defined meaning under Standard §5 that a governance chain is
not; `reproduction_record.json` is the existing precedent for a
fixed-name machine artifact at the cycle root. The filename is
`transition_records.jsonl` rather than `decision_records.jsonl` or
`decision_chain.jsonl` because a name reading as a sibling of
`decision_log.md` invites the conflation AD-045 and this AD exist to
guard against.

**A8-C3 — the filename is undated, and a dated file per append is
rejected** *(A-8 R-2, §4.2)*. Standard §5 requires each file to be dated
*"in its own content **or** filename"*; every record carries an injected
UTC timestamp, so the file is dated in its content, per record, which is
the stronger limb. **A dated file per append is affirmatively rejected:**
it would make every append its own genesis chain, and a chain that cannot
reference its predecessor file proves nothing — the naming convention
would destroy the mechanism it was meant to protect. The file is the
machine counterpart of `decision_log.md`, the one file Standard §5
already recognizes as literally append-only rather than
superseded-by-new-file, and it inherits that discipline. **This is a
reading of §5, not an amendment to it.**

**A8-C4 — the recorder never creates a directory** *(A-8 R-3.1, §4.3)*.
`write_canonical_jsonl` silently `mkdir`s its parent. Left unguarded, a
mistyped or unregistered `cycle_name` would **manufacture an archive
directory with no `archive_manifest.json`** — precisely the
archive↔registry divergence class A-6 R-2 ruled on and declined to
mechanize. **The cycle directory's existence is a precondition of the
first record, never a consequence of it.**

**A8-C5 — the write precondition** *(A-8 R-3.2, §4.3)*. A chain is
written **only into a directory that already contains
`archive_manifest.json`**. This single condition **excludes the three
legacy archives by construction** — they have no manifest and will never
be given one — with **no hardcoded name list**, and therefore without
`core/governance/` needing anything from `tools/archive_manifest.py`. It
is consistent with AD-050's position that the three historical projects
have no transition records at all.

**A8-C6 — identity is checked; completeness is not** *(A-8 R-3.3, §4.3)*.
The manifest is read for exactly one purpose: confirming that
`manifest.project_id`, the directory name, and the record's `project_id`
are **byte-identical**. `lifecycle_version` is **deliberately not
consulted** — interpreting it is `ArchiveVerifier`'s job, and
`ArchiveVerifier` is on Step 9's may-not-implement list. Disclosed: this
makes the recorder the **first component in the repository to read an
existing manifest**, which `RESEARCH_ARCHIVE_MANIFEST.md` anticipated
only for a future `ArchiveVerifier`. It is a three-way identity check,
not a completeness check, and **it must not grow into one.**

**A8-C7 — `RESEARCH_ARCHIVE_MANIFEST.md` is unamended and its
`schema_version` unchanged** *(A-8 R-3.4, §4.3)*. The manifest is a
four-field index that does not enumerate its directory's contents, so a
new file beside it changes nothing the manifest asserts. **The chain sits
inside the directory the manifest indexes, and outside the manifest's
schema.**

**A8-C8 — no new top-level directory, and nothing outside the
repository** *(A-8 R-3.5, §4.3)*. No `governance_records/`, no
`.governance/`, no untracked or out-of-repository store. The retention
half of anchoring requires a **human-performed commit** of the artifact
under existing archive discipline, and **an artifact that git does not
track cannot be anchored that way at all.** A5-C1's demotion of the
commit from anchor to retention does **not** relax this: co-visibility in
a tracked state is still required.

**A8-C9 — the identity relation** *(A-8 R-4, §4.4)*. `cycle_name` is the
**partition key** — the one path segment between the archive root and the
filename — and it is the same identity phase attaches to, so the file is
one-to-one with it. `project_id` is **not a second key**: it is
byte-identical to `cycle_name` and appears in the path exactly once, as
that segment; **the `project_id` field nevertheless stays in the record**,
because the field set is closed and pinned by test, removing a field is a
new AD, and the redundancy keeps a record self-describing if it is ever
quoted outside its file. **`lineage_id` never appears** — not in the
path, not in the filename, not in the record — because a lineage spans
cycles that were in different phases, and a lineage-partitioned chain
would interleave transitions from which no cycle's current phase could be
derived; **the lineage view is obtained by joining in the Register, never
by partitioning the machine artifact.** **`attempt_number` never
appears**, because an attempt does not advance the governance process.

**A8-C10 — `sequence_number` is scoped to the per-cycle file** *(A-8
R-4, §4.4)*. A cycle's sequence numbers are monotonic **within that
cycle**; they are not global and do not order transitions across cycles.
A-8 recorded that the numbering **origin** and the anchor's **format**
remained A-5's to decide; they have since been decided and are carried
here at **A5-C4** (origin 1, contiguity) and **A5-C7** (the citation
grammar). A8-C10 is not merged into those items: it fixes the *scope* of
the numbering, and A5-C4/A5-C7 fix its *origin* and its *citation form*.

**A8-C11 — `Project.repository_path` is a second stored representation,
and nothing binds it** *(A-8 R-4, §4.4)*. Governance may import only
`data`, so the recorder never sees a `Project` and **cannot consult
`repository_path`**; the path is computed from the injected archive root
and the `cycle_name` string. Disclosed: `repository_path` stores the same
location, it agrees with this rule for all three backfilled entries,
**nothing enforces that agreement, and no invariant binding them is
created** — consistent with A-6 R-2's refusal to mechanize the
archive↔registry relation. The only place the two could ever be
reconciled is `core/research/lifecycle.py`.

**A8-C12 — amendment (AD-074, 2026-07-26): the Archive Seal Register is
the first allowed platform-level governance machine artifact.** A8-C1's
partition rule states, without exception, that "every governance machine
artifact is per-cycle." The Archive Seal Register
(`docs/archive_seal_register.jsonl`, `AD_074_ARCHIVE_SEAL_DESIGN_REVIEW.md`
§5.5/§C) is a machine artifact — append-only, machine-written,
machine-read — whose subject spans cycles: it names one sealing commit
per closed archive, and no single cycle's directory can hold it. This is
not a stylistic choice; `AD_074_ARCHIVE_SEAL_DESIGN_REVIEW.md` §3 S-1
proves it is structurally required: the sealing commit is the commit
that *first contains the complete closed archive*, so the record naming
that commit cannot be written before that commit exists, and therefore
cannot live inside `research_archive/<cycle_name>/` without the record
being either absent from the very tree it seals or added by a second,
later commit that mutates a directory Phase G's remediation decision §8
already holds immutable. A per-cycle location is not merely
inconvenient here; S-1 shows it is impossible.

A8-C8 independently forecloses the seemingly obvious alternative — a new
top-level location, e.g. `governance_records/` or `.governance/`: "No new
top-level directory, and nothing outside the repository." Between a rule
that forbids a platform-level machine artifact (A8-C1) and a rule that
forbids inventing a new location for one (A8-C8), the only location
consistent with both is the existing platform-level tier itself —
`docs/`, where A8-C1 already places human-authored, cross-cycle prose.
The Archive Seal Register is machine-written and machine-read, not
prose: the first artifact of that kind ever placed there, and an
exception to A8-C1's own rule, not an application of it.

**This is a narrow, named exception, not a repeal of A8-C1.** It applies
only to the Archive Seal Register, for the one structural reason given
above (S-1), and does not license any other platform-level machine
artifact by analogy: a future proposal for a second one must
independently satisfy A8-C1 or argue its own S-1-shaped impossibility,
not cite this exception as precedent. A8-C1 stands unamended for every
other governance machine artifact, including `transition_records.jsonl`
itself (A8-C2), which remains strictly per-cycle.

#### A-9 — single-writer enforcement (A9-C1 … A9-C10)

**A9-C1 — "single writer" is never printed undifferentiated** *(A-9 R-1,
§4.1)*. The phrase conflates three separable properties, and answering
them with one word would produce a claim stronger than its mechanism.
Every sentence in this AD that uses it says which one it means.

| Property | Question it asks | Answer | Mechanism? |
|---|---|---|---|
| **Authority** | Which code path may append to a transition chain? | Exactly one module, reachable through exactly one caller (A9-C3) | **Yes** — a design property, statically checkable and pinnable by test |
| **Exclusivity in time** | Can two appends to one chain file interleave? | Assumed not to; **nothing prevents it** (A9-C4) | **No** — a runtime property, unenforced, knowingly |
| **Ownership / accountability** | Who is answerable for a record having been written? | The single human operator who authorized that transition, never the module | **Partly** — the authorization record is stored; the identity claim in it is self-asserted |

Exclusivity may not borrow the credibility of authority. A reader
encountering an undifferentiated "single writer" will take it to mean the
strongest of the three, which is precisely the one that is not true.

**A9-C2 — the ruling is stated assumption, not mechanical lock, and the
lock is closed rather than deferred** *(A-9 R-2, §4.2)*. Resolution §4.1
posed A-9 as a binary; the answer is **stated assumption**. **No lock is
introduced, in Step 9 or by this decision.** Five grounds, the fourth
decisive:

1. **No lock primitive exists to adopt.** Nothing in `core/` or `tools/`
   imports `fcntl`, `msvcrt`, `flock`, `filelock` or `portalocker`, and
   nothing performs an `os.replace`. A lock is new machinery, with a new
   dependency or new platform-conditional code, in the domain that exists
   to be audited.
2. **A lock is a write, in the domain whose value is not writing.** An
   advisory lock file placed at the cycle root is an undeclared item in
   an evidence package; placed outside the repository it is untracked,
   and an untracked artifact can neither be shown to have been held nor
   be shown to have been absent — the appearance of discipline with none
   of the evidence.
3. **The contention it defends against does not occur.** The platform
   runs with a single human operator directing all sessions, the chain is
   per-cycle so distinct cycles do not contend at all (A8-C2), and no
   transition happens without explicit authorization. Building it would
   be a component whose only designed trigger does not exist — **AD-045's
   surviving objection, applied to the very AD that had to answer it.**
4. **A lock cannot deliver the property the chain needs.** The threat
   model is that *the actor who would author retroactively is the same
   actor who can truncate*. A lock acquired by that actor's own process
   constrains that actor not at all. A lock defends against *accidental*
   interleaving by *cooperating* writers, and the chain's adversary is
   neither. **A mechanism that raises the apparent strength of a claim
   without raising its actual strength is worse than no mechanism.**
5. **A lock here would be untestable in the environment that has it.** A
   single-operator platform cannot exercise real contention, so it would
   ship as load-bearing-looking code covered only by simulated tests.

Reopening requires a new AD arguing against those five grounds on their
merits. **"Stated assumption" is not permitted to mean *unstated*:**
A9-C4 fixes the words, A9-C5 fixes what happens when the assumption is
false.

**A9-C3 — the authority model binds the design, not the filesystem**
*(A-9 R-3, §4.3)*. Exactly **one module**,
`core/governance/decision_recorder.py`, may write a
`transition_records.jsonl`; no other module in any domain reads-modifies
or writes that file, and Phase C pins this by test. That module is
reachable **only through `core/research/lifecycle.py`**, which is already
the only module permitted to import Validation and Governance together
and therefore the only legal binding point that exists at all — this is
the existing import boundary doing the work, not a new restriction.
**Every append carries one explicit human authorization** (AD-050): there
is no writer without an authorizer, and a record with no authorization
record is not a record this system can produce. **The human operator, not
the module, owns the chain; the module is an instrument.** This
constrains what this system does, **not what can happen to the file**.

**A9-C4 — the assumption, in the words it must be stated in** *(A-9 R-4,
§4.4)*. Carried substantively unchanged, and carried in the artifact
header beside the chain's narrow tamper-evidence claim:

> **Single-writer assumption.** At most one process appends to any one
> `transition_records.jsonl` at any one time, and it does so on behalf of
> the single human operator who authorized that transition. **Nothing
> enforces this.** There is no lock, no advisory file, no process
> registry, and no runtime check. A violation is not prevented. It is
> either detected after the fact by chain verification, or — in the case
> named in A9-C7 — it is not detected at all.

Its scope is **one chain file**, not global: two cycles advancing
concurrently do not violate it, because they touch different files
(A8-C2). This is a real narrowing and is claimed as one. It is an
assumption about the **system's own writers** and says nothing about a
human editing the file by hand. It **names the operator, not a process
identity** — no field records which process wrote a line — so it is a
property of practice, not a checkable property of a record.

**A9-C5 — enforcement is detection, not prevention, and the detection is
A-5's** *(A-9 R-5 and R-6.1, §4.5 – §4.6)*. **A-9 introduces no new
detection mechanism.** What serves it is A5-C4's contiguity rule, ruled
for a different reason and covering two of the three concurrency failure
shapes:

| Concurrency failure shape | Detected by | Disposition |
|---|---|---|
| Two writers assign the **same** `sequence_number` and both records land | A5-C4 duplicate check | **Chain-invalid.** Verification refuses |
| A write is lost such that a number is **skipped** | A5-C4 gap check | **Chain-invalid.** Verification refuses |
| Two writers assign the same `sequence_number` and the **second rewrite discards the first record** | **Nothing** | **Undetectable** — A9-C7 |

**The actual enforcement is that an invalid chain blocks further
advancement**, via AD-050's precondition that the chain be verified
intact before any append, and **it is deliberately after the fact**.

**A9-C6 — "written atomically" is disambiguated** *(A-9 R-5, §4.5)*. The
storage clause above requires the append to be *"written atomically
(temp + replace)"*. **Temp-plus-replace makes the *replacement* atomic —
a reader never sees a half-written file. It does not make the
*read-modify-write* atomic, and it therefore does nothing about
last-writer-wins.** A reader who takes "atomic" as "concurrency-safe"
would be wrong. Phase C's docstrings and test names say *"atomic
replacement"*, never *"atomic append"* and never *"concurrency-safe"*.

**A9-C7 — the one failure that is invisible, stated as a non-claim**
*(A-9 §6.3)*. Carried in substantially these terms and not softened:

> If two authorized appends to the same chain interleave such that the
> second rewrite is computed from a prefix that does not include the
> first, the first record is lost and the resulting file is contiguous,
> correctly chained, and internally valid. **No mechanical check in this
> design detects that.** The anchor cannot cover it either, because the
> lost record is by definition the newest and the newest record is always
> unanchored (A5-C10). The only thing standing between this design and
> that outcome is the A9-C4 assumption, and the assumption is not
> enforced.

This is a **non-claim, not a risk with a mitigation.** A risk invites a
mitigation and a residual-risk rating; a non-claim states that the system
does not know, which is the true position. **No mitigation is built, and
this AD may not convert it into a risk.**

**A9-C8 — the whole of A5-C11 is conditional on the A9-C4 assumption**
*(A-9 R-7.5, §8)*. A-5 §9 pre-committed that if A-9 ruled "stated
assumption", A-5 §6.1's claims become conditional on that assumption **and
this AD must say so in those words**. A-9 rules stated assumption, so the
branch fires. **Claim 1, Claim 2, Claim 2a, Claim 3, and the honest
summary — all of A5-C11, none omitted — are conditional on the
single-writer assumption stated at A9-C4.** A-5's trigger names *"§6.1's
claims"* without qualification and is discharged without qualification:
**the condition may not be carried on a subset**, because an A5-C11 claim
printed unconditionally beside conditional ones will be read as the one
that survived the assumption.

One correction A-9 owes A-5 and states rather than elides: A-5 §9's row
describing a lost interleaved write as appearing "as a gap" holds **only
where the two writers assigned different sequence numbers.** In the
last-writer-wins shape both assign the same number and the survivor
leaves **no gap at all** (A9-C7). This corrects the *coverage
description* of a detection mechanism — not the mechanism, not A5-C4, and
not any A5-C11 claim.

**A9-C9 — what writer discipline explicitly does NOT claim** *(A-9 §7.2)*.

| Not claimed | Because |
|---|---|
| **OS-level locking** | No `fcntl`, `msvcrt`, `flock`, `filelock` or `portalocker` appears anywhere in `core/` or `tools/`, and A9-C2 introduces none. No advisory lock, mandatory lock, lock file, PID file, or sentinel |
| **Database locking** | There is no database on this path. Project storage is a plain in-memory dict; the chain is a flat file rewritten by `path.write_bytes`. No transaction, no row lock, no isolation level |
| **Runtime prevention** | No mutex, semaphore, queue, single-instance guard, process registry, daemon, or supervisor. Nothing runs between operator sessions to prevent anything |
| **Automatic enforcement** | Nothing checks the assumption at write time. `advance_phase()` verifies the chain is *intact* before appending; it cannot verify that no one else is appending *concurrently*, and it does not try |
| **Atomicity of the read-modify-write** | A9-C6. The lost-update window is unaffected by temp-plus-replace |
| **Detection of a lost update** | Structural, not incidental (A9-C7). The surviving file is valid on every check the design has |
| **Any claim about who wrote a record** | No writer-identity field exists and none is added. **The chain attests that bytes were not altered since they were written; it never attests who wrote them.** A record's `project_id`, timestamp and authorization record are claims made by whatever produced the line |
| **That the declared authorizer is who they claim** | Standard §4 stores the declared reviewer level verbatim and does not validate the independence claim. Authorization is recorded, never adjudicated |
| **Protection against a hand edit** | A JSONL file on disk is writable by any process with filesystem access. A9-C3 binds this system's design, not the operating system |
| **That an invalid chain can be made valid** | It cannot, and no tool is provided that would try (A9-C10) |
| **Anything about the three legacy archives** | They have no transition records and never will; they have no writer to be single |

**A9-C10 — conflict handling** *(A-9 R-6, §4.6)*. Governing principle:
**an invalid chain is evidence of a governance event, and evidence is not
repaired — it is disclosed.** Editing a chain to make verification pass
destroys the only record that the violation occurred, by the same act
that would conceal it. Therefore:

1. **Duplicates and gaps are chain-invalid and verification refuses**
   (A5-C4, adopted unchanged and not softened).
2. **Not repaired.** No renumbering, no deduplication, no
   "keep the one with the correct predecessor hash", no
   truncate-to-last-valid, no `--force`. None is built, and building one
   later is a new AD.
3. **The invalid chain is retained exactly as it is** — not deleted, not
   truncated, not moved aside. It is the artifact of record.
4. **The response is a governance act:** a dated disclosure under
   Standard §5's correction-is-a-new-file discipline, plus a
   `decision_log.md` entry recording that the chain went invalid, when it
   was noticed, and what is consequently unknown — stating what cannot be
   reconstructed as unreconstructable rather than supplying a
   reconstruction.
5. **The cycle stops advancing**, via AD-050's intact-chain precondition.
6. **The derived phase becomes unknown, and unknown is correct.** Phase
   is derived, not stored, and the failure direction under-claims by
   design; a cycle whose chain is invalid has no provable current phase.
7. **An unauthorized writer is not reached by A9-C3 at all.** A hand
   edit, an ad-hoc script, or any process with filesystem access is
   caught only by what catches tampering generally — and a **well-formed
   record appended by hand is caught by none of it.**
8. **Ambiguity is never tiebroken.** A citation naming a duplicated
   sequence number is ambiguous and verification refuses rather than
   picking a record. **No tiebreak by timestamp** (that trusts exactly
   the field a compromised writer controls); **no tiebreak by "the one
   whose hash matches the citation"** (circular — it makes the citation
   define which record is real, when its entire evidentiary value is
   being an independent witness of a record that already was); **no
   tiebreak by file order, longest valid prefix, or plausibility** (each
   invents a fact). Resolution is a human governance act whose
   permissible outcomes include *"the true state cannot be
   reconstructed"*. **An ambiguous anchor does not invalidate the
   citation:** the `decision_log.md` entry stands as written and is never
   edited; what is recorded is that the chain can no longer be matched
   against it.

---

**Migration Plan §10 item 4 is NOT satisfied by this AD.** Item 4
requires transitions logged "not hand-authored into a `decision_log.md`
after the fact." This AD **rejects that clause on governance grounds**,
per AD-038 and AD-045: hand-authorship of judgment is correct and is
retained. Item 4 is therefore **partially met — mechanical record
present, replacement of hand-authorship deliberately declined** — and
Step 10's retrospective must record it that way. Rounding it up to "met"
is the violation the Migration Plan §10 itself names.

**Migration/status.** `docs/templates/decision_log_template.md` and the
per-project `decision_log.md` files remain the canonical decision-log
mechanism. **One amendment to the template is required by A5-C7 and is
the only change to it:** it gains one required entry field,
`**Machine chain anchor.**`, carrying the citation grammar defined at
A5-C7, in the increment that accepts this AD. The template is otherwise
unchanged, no `decision_log.md` is edited or retrofitted (A5-C8), and no
code writes or reads either file (INV-10, A5-C9).
`PLATFORM_ARCHITECTURE_V1.md` §4.4's
`DecisionLogger` Protocol and the Migration Plan's references to it are
left as-written, per the convention that ADs record divergence rather
than editing those two documents (AD-036, AD-040, AD-044, AD-045).

---

### AD-049: Validation orchestration — `GateRunner` is built, the §5 table governs, and Validation never aggregates

**Decision, five parts.**

**1. `GateRunner` is built.** AD-040 deferred it because "today there
are exactly two gates and one caller shape"; AD-044 named the trigger
verbatim: *"When a second calling pattern (a `GateRunner` dispatching by
name, for instance) actually needs to pass the same bundle of frozen
inputs to gates it does not know the concrete signature of,
`GateContext` is the natural type to introduce then."* Migration Plan
§10 item 3 requires H4's gates to run "through `core/validation/`'s
`GateRunner` against a registered `Gate`, not a bespoke
`experiments/validate_h4_*.py` script." That is the second calling
pattern, as a hard acceptance criterion. Building it now is consistent
with AD-040/AD-044 on their own stated terms, not a violation of them.

**2. `PLATFORM_ARCHITECTURE_V1.md` §5's table governs over its
contradicting same-section prose.** The table (`:505-509`) marks
Validation → Governance ✅. The same section (`:537-539`) states
"Validation and Governance, both Layer 1, never call each other." Both
verified; they cannot both hold. **The table wins**, on three
independent facts: the linter implements the table
(`ALLOWED_DEPENDENCIES["validation"]` includes `"governance"`);
`test_allows_validation_to_import_statistics_and_governance` asserts it;
and AD-043's existing gates depend on it by calling `verify_freeze`. The
prose is an over-general gloss on the acyclicity argument, and it is
*harmlessly* wrong — a single Validation → Governance edge with no
return edge creates no cycle. Recording this is not bookkeeping: left
unrecorded, an auditor can cite the prose to argue that **every gate in
the repository violates the layering**.

**3. Validation never aggregates gate outcomes.**
`PLATFORM_ARCHITECTURE_V1.md:245-247` assigns cycle-level aggregation to
Research by name: a gate reports whether *its own* criteria were met;
"only Research aggregates gate outcomes into" a terminal decision.
Therefore:

- `GateRunRecord` stores the **ordered per-gate statuses only**, with
  **no aggregate field**;
- the aggregation rule — unchanged, `PASS` only if every gate passed,
  `FAIL` if any failed, otherwise `AMBIGUOUS`, with **FAIL dominating
  AMBIGUOUS** — becomes a pure function in `core/research/`,
  unit-testable against a truth table;
- the result is named `sequence_status`, **never** `verdict`, and is
  distinct from the Standard §7 determination (AD-050).

This also strengthens the audit story: "was the verdict derived, not
asserted?" is answered by the auditor recomputing from stored primitives
under a documented rule, rather than by trusting a stored aggregate.

**4. Scope limits on the runner.** `GateRunner` **never imports
`core.governance.pinned_worktree`** — that component creates worktrees
and executes subprocesses, and wiring it into the runner would turn a
comparison engine into a code-execution engine while contradicting the
runner's own purity claim. Re-running a gate under a pinned worktree is
a Research- or tools-level reproduction concern, out of Step 9 scope.
**`ReviewLevel` is not introduced**: it appears exactly once in the
repository, in a sketch (`PLATFORM_ARCHITECTURE_V1.md:210`), while
`DecisionMetadata.review_level` is a plain `str`. An enum with one
consumer, creating a dual vocabulary against a frozen baseline type and
placing a Standard §4 governance concept under Validation's ownership,
is the abstraction AD-005/AD-040/AD-044 already refuse. Review level
stays `str`. `GateResult`, `GateStatus`, `build_report` and the two gate
functions are **unmodified**; `GateStatus` remains exactly three-valued
and a gate crash is an **envelope error, never a status** (a fourth
member would silently change `build_report`'s contract, AD-046).

**5. The import linter is tightened on three counts before any Step 9
domain code lands.** The shared kernel is exempt as an import *source*,
not merely as a target — `_domain_of_file` returns `None` for
`core/shared/` and `check_repository` `continue`s on `None`, while
`test_shared_kernel_imports_are_exempt` only exercises the target
direction. The mechanism is broader than the kernel: `_domain_of_file`
resolves through `DOMAIN_OF_TOPLEVEL.get(...)`, so **any unmapped
top-level package** under `core/` is silently exempt in both directions;
and `_imported_core_modules` collects only `node.level == 0` imports, so
a **relative** import inside Governance is invisible to the checker.
Required, before `LifecyclePhase` or any new domain module lands:

- the shared kernel may import **nothing** from any `core` domain;
- an **unmapped** top-level package under `core/` is an **error**, not
  an exemption;
- relative imports are resolved or rejected.

All three are `tools/` changes, touch no baseline domain code, and are
strict tightenings that cannot make a currently-passing check fail
(verified: no kernel module imports any domain, and no relative imports
exist under `core/` today). **Ordering is part of this decision** —
adding lifecycle vocabulary to the kernel first and the guard second
leaves a window in which the escape hatch is both open and attractive.

**Invariant restated.** INV-11 as originally drafted — "identical inputs
produce a byte-identical `GateRunRecord` serialization" — is **false**:
the record contains freeze verification outcomes, which `verify_freeze`
derives from the working tree, not from the `GateContext` at all, and
the timestamp varies by design. Correct form: *given identical
`GateContext` inputs, identical freeze verification outcomes, and a
fixed clock, serialization is byte-identical.* An invariant that fails
its own test gets the test weakened to make it pass, which is worse than
having no invariant.

**Migration/status.** The two existing gate functions keep their
explicit-parameter contract (AD-044's rationale survives for direct
callers); the runner reaches them through thin per-gate adapters, and an
equivalence test proves dispatching through the runner returns exactly
what calling the function directly returns. `PLATFORM_ARCHITECTURE_V1.md`
§5's prose and §4.2's sketches are left as-written, per the recording
convention.

**Requirement transcribed from the A-8 ruling record — A-8 R-5, carried
here rather than on AD-048.**
[`PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md`](PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md)
§4.5 (R-5) and its §6 closing paragraph place one consequence on
**AD-049**, not AD-048, because `GateRunRecord` is this AD's object. It is
transcribed here verbatim in effect, under the same
prefix-and-source convention the other transcriptions use, as **A8-R5**:

**A8-R5 — a persisted `GateRunRecord` takes the same per-cycle partition
as every other archive artifact** *(A-8 R-5, §4.5)*. *If* a
`GateRunRecord` is persisted to disk at all, its location is per-cycle,
at `research_archive/<cycle_name>/experiment_results/`, with a **dated
filename**. Standard §5 already assigns `experiment_results/` this exact
meaning — "raw, unmodified Validation output (Phase 6), append-only" — and
a gate run record is raw Validation output, so **no new location is
introduced**. The filename **is** dated (unlike the transition chain of
A8-C2/A8-C3, which is undated because it is a chain): each run record is a
discrete artifact superseded file-by-file under §5's convention, matching
the existing dated result JSONs under `reference_h3`.

This item is a **location/disclosure rule only**, and its scope is
expressly narrow:

- **Whether a `GateRunRecord` is persisted at all is a Phase D question
  and is *not* decided here.** A8-R5 fixes only *where* such a record
  goes *if* it is written, so that Phase D does not make a second, ad-hoc
  location choice.
- It asserts **no enforcement**: nothing in this AD makes the recorder,
  the runner, or any check reject a record written elsewhere; the rule
  records the correct location, it does not police it.
- It asserts **no automatic creation**: the `experiment_results/`
  directory is not created by this item, and this AD does not direct any
  component to create it.
- It confers **no path authority** on `GateRunner` or on Validation over
  the archive layout; the partition it names is Standard §5's, restated,
  not one this AD originates.
- It adds **no invariant** to `GateRunRecord` or to the record's field
  set — the closed field set and the INV-11 restatement above stand
  exactly as written.

---

### AD-050: Research cycle identity, derived phase state, and human-authorized transitions

**Decision, four parts.**

**1. The identity model names three things, not one.**
`core/research/project.py:3` claims `Project` "gives every research
cycle -- past or future -- one stable record." That claim is not true
today: `reference_v1` and `reference_v2_h1` are two `Project`s that are
successive **cycles of one research lineage**, and `reference_h3` ran
multiple internal **attempts** (`attempt_001_specification.md`). One
identifier is doing the work of **lineage**, **cycle**, and **attempt**.
Before any phase state is attached, the three are named and it is
recorded that **phase belongs to the cycle** — not to the lineage
(which spans cycles that were in different phases) and not to the
attempt (which does not advance the governance process on its own).

The registry and the archive are also already divergent:
`research_archive/` holds four project directories and three are
registered — `positive_control_phase3` exists on disk with no `Project`
record, no invariant binds the two, and nothing detects it. This AD
rules on that divergence before H4 adds a fifth directory.

**H4 must be registered** before Step 9 §10 item 1 can be met, under a
naming convention reconciled with the existing three — none of which use
bare H-numbering.

**Requirements transcribed from the A-6 ruling record — prefixed, never
merged.** The identity content of part 1 above is decided by
[`PHASE_4_A6_RESEARCH_IDENTITY_RULING_2026-07-22.md`](PHASE_4_A6_RESEARCH_IDENTITY_RULING_2026-07-22.md)
§6, whose consequence list numbers from `C-1` and therefore collides in
label with A-5's and A-8's lists on AD-048. Under the same prefix
convention A-9 §9 directs for those (see AD-048), A-6's items are carried
here as **A6-C1 … A6-C8**, each naming the ruling section it is drawn
from. **No item is merged with another.** A-6 §6 also mandates three
textual changes to this draft; they are applied below as **A-6 textual
change 1 – 3**, each quoting the draft sentence it governs so the change
is deliberate rather than silent. One further item, **A5-C9 (AD-050
limb)**, arrives from the A-5 ruling and is recorded with the evidence
preconditions at the end of this AD rather than here.

**A6-C1 — the canonical identity vocabulary is the Register's three
fields** *(A-6 R-3, §4.3)*. `lineage_id`, `cycle_name` and
`attempt_number` — already defined in `RESEARCH_LINEAGE_REGISTER.md`'s
Schema — are adopted verbatim, with their existing definitions, and **no
others are defined**. `cycle_name` is canonical with the strongest anchor
of the three: it originates in Standard §5, which outranks the Register
and predates it. This AD's terms map exactly onto them:

| Term used in this AD | Canonical field | Governing definition |
|---|---|---|
| "lineage" | `lineage_id` | The Register's: a **mechanism / target-function space** under a Phase 3 attempt cap, *"chosen to identify the mechanism being corrected, not the cycle or document that first defined it"* |
| "cycle" | `cycle_name` | Standard §5's: the research cycle whose evidence package is `research_archive/<cycle_name>/` |
| "attempt" | `attempt_number` | The Register's: an ordered attempt within a `lineage_id`, carrying `counted_against_cap` |

Two precisions attach. **`ProjectId` / `project_id` is a type and a key,
not a fourth identity concept:** where a cycle is registered, both carry
a string **byte-identical to its `cycle_name`**, the same identity in a
typed and a serialized position. **Attempt numbering outside a registered
lineage is cycle-local and caps nothing across cycles:** only attempts
recorded under a `lineage_id`, with `counted_against_cap`, consume a
cross-cycle cap, so `reference_h3`'s "attempt 1 of a maximum three" is a
real governance artifact but is not a Register entry and must not be
cited as though a lineage cap governed it.

**A6-C2 — no second identity vocabulary is created** *(A-6 R-3, §4.3)*.
This AD introduces **no** new identity field, type, enum, dataclass,
registry, or synonym for `lineage_id`, `cycle_name`, or
`attempt_number`. `Project` is unmodified and `ProjectRegistry`'s three
methods are unmodified. `LifecyclePhase` (part 2) is **phase**
vocabulary transcribed from Standard §2 and is orthogonal to identity —
it names *where a cycle is*, never *which cycle it is* — and nothing
here extends or constrains it beyond that boundary.

**A6-C3 — phase attaches to the `cycle_name`** *(A-6 R-3, §4.3;
Resolution D-15)*. D-15 — *phase belongs to the cycle* — is affirmed
unchanged and stated in canonical terms: phase attaches to a
`cycle_name`, **not** to a `lineage_id` (which spans cycles that were in
different phases) and **not** to an `attempt_number` (which does not
advance the governance process on its own).

**A6-C4 — H4's identifier is `reference_h4`** *(A-6 R-1, §4.1)*. The
form is `reference_<hypothesis-label>`, lowercase, satisfying
`^[a-z][a-z0-9_]*$`, following the most recent precedent `reference_h3`
and dropping the profile-version segment, which was already dropped and
did not return. **One string, four places:** the same literal
`reference_h4` is the `research_archive/` directory name, the
`cycle_name`, the `ProjectId` string, and `archive_manifest.json`'s
`project_id` field — **byte-identical**, never four independently-chosen
names. **Bare `h4` is rejected**: it matches none of the three existing
directory names and would be the sole exception to a format rule whose
own docstring records that no exception exists for any project. The
`"project_id": "h4"` in `RESEARCH_ARCHIVE_MANIFEST.md`'s schema example
is an illustrative field value inside a schema example, **not a naming
decision**, and that document is not edited; the divergence is disclosed
rather than corrected in place.

**A6-C5 — the identifier fixes the string, not the hypothesis** *(A-6
R-1 limitation, §4.1)*. The H-number tracks the **hypothesis label**, not
the ordinal — `reference_v2_h1` was the second cycle and carries `h1`.
Roadmap H4 is a specific hypothesis, volume / flow acceleration, which
was **rejected at H3's selection review on data-reliability grounds** and
has never had a Phase 1 artifact or a Phase 2 approval of its own.
Therefore: registering `reference_h4` **asserts nothing** about
hypothesis content, data adequacy, or Phase 2 selection; and
**`reference_h4` is not a generic label for "the fourth cycle"** — if the
next cycle's Phase 2 selects a different candidate, that cycle takes
`reference_h<n>` for *its own* hypothesis label and `reference_h4` is not
reused. **The identifier follows the hypothesis; it never follows the
ordinal.**

**A6-C6 — `positive_control_phase3` is an open cycle, recorded as a
`cycle_name`, unregistered, and deferred** *(A-6 R-2, §4.2)*. The three
registers genuinely disagree, and each is answered in its own terms:

| Register | Status of `positive_control_phase3` |
|---|---|
| `research_archive/` | **An open cycle's live evidence package — not a historical archive directory.** Its manifest declares `lifecycle_version: "v1"`, and that document defines "legacy" as exactly the three predating directories; its own README states it is not a Methodology Freeze, and the cycle has not reached Phase 4 |
| `RESEARCH_LINEAGE_REGISTER.md` | **A recorded `cycle_name`** — of both recorded attempts under the `active` lineage `gate2_score_acf_target_fn`. It is recorded *as a `cycle_name`*; it is **not** a `lineage_id` and must never be cited as one |
| `ProjectRegistry` | **Unregistered, and a future migration target — explicitly deferred** |

Registration is **deferred rather than performed**, on three grounds in
order of decisiveness: Phase A forbids it (documents only, zero code);
**no registration path for an open cycle exists**, since
`backfill_historical_projects()` is the only path, is deliberately
non-idempotent, and is scoped by its own docstring to closed historical
cycles; and — stated rather than borrowed — **it is not blocked on
representability**, because `Project` can already represent an open cycle
(`lifecycle_state=ACTIVE` with `research_outcome=None`) and `origin_date`
would be taken from `archive_manifest.json`'s `created_at`, an
already-recorded evidence date. The deferral rests on the first two
grounds, which are sufficient, and not on a claimed impossibility that
does not exist.

**A6-C7 — no archive↔registry invariant is created** *(A-6 R-2, §4.2)*.
What is absent is an **invariant binding the two**. No such invariant
exists, nothing detects the divergence, and **Step 9 creates none** —
creating one is a mechanism, and mechanisms are not Phase A work.
**`ProjectRegistry`'s contents mean *the set of projects that have been
registered*, and make no claim about the contents of
`research_archive/`.** A reader must not infer archive completeness from
the registry, or registry completeness from the archive.

**A6-C8 — the stale `historical_backfill.py` docstring is disclosed, not
fixed** *(A-6 R-2, §4.2)*. That module's *"the complete set; no fourth
candidate exists in `research_archive/`"* was **true when written and is
stale now**: the module landed 2026-07-19 and
`research_archive/positive_control_phase3/` landed 2026-07-20, one day
later. Correcting it is a code edit and belongs to the increment that
adds a registration path for a non-historical cycle; the correction is a
docstring edit accompanied by an AD or a dated note, **never a silent
rewrite**, because the record should say when the sentence stopped being
true.

**A-6 textual change 1 — the "one research lineage" sentence is not a
`lineage_id` claim** *(A-6 §6 item 1, R-3 precision 1)*. Part 1 above
states that `reference_v1` and `reference_v2_h1` are *"two `Project`s
that are successive **cycles of one research lineage**"*. That sentence
is retained as the observation it is, and is **not** written as a
`lineage_id` claim: **no `lineage_id` exists for that succession, and
none may be opened for it retroactively.** The Register is append-only
and is written to only when a Phase 3 attempt cap opens, so back-filling
one now would record a retroactive fact of exactly the class
`project.py:32-41` already refuses for `origin_date`. **The succession is
expressed as two `cycle_name`s related by the narrative already in the
closeout documents** — never as a shared `lineage_id`, and never with a
second, wider sense of the word "lineage" defined alongside the
Register's.

**A-6 textual change 2 — "H4 must be registered" stands, and its
identifier is now fixed** *(A-6 §6 item 2)*. The sentence *"**H4 must be
registered** before Step 9 §10 item 1 can be met"* stands as a statement
of Step 9's dependency. The identifier it must be registered under is
**`reference_h4`** (A6-C4), which discharges "under a naming convention
reconciled with the existing three". **The registration itself remains
Phase B work and is not authorized by this AD.**

**A-6 textual change 3 — "rules on that divergence" means disclosed and
bounded, not eliminated** *(A-6 §6 item 3)*. The sentence *"This AD rules
on that divergence before H4 adds a fifth directory"* is satisfied by
**A6-C6 and A6-C7** — a ruling that the divergence is **disclosed,
bounded, and unmechanized**, **not** that it is eliminated. The archive
holds four cycles, the registry holds three, the fourth is a live cycle
whose registration is deferred on stated grounds, and Step 9 may proceed
on that basis without either silently reconciling the two or treating the
divergence as an unknown.

**2. `LifecyclePhase` lives in `core/shared/`.** The eight phases of
`RESEARCH_GOVERNANCE_STANDARD.md` §2 (Hypothesis, Research Proposal,
Pre-validation, Methodology Freeze, Implementation, Validation,
Decision, Archive) are genuinely shared vocabulary: Research advances
through them, Validation maps gates to them, Governance records
transitions in them. A closed `str` enum with no behavior and no imports
beyond `enum` — the same profile as `ProjectId`, which is why the kernel
is where it belongs and why Research is not (Validation → Research is
forbidden, so Validation could not map phases to gates at all).

The values are **transcribed exactly from the Standard at freeze time**
and pinned by a test against §2's table. An invented or approximated
phase vocabulary hardcoded into the kernel would be a governance defect
of the kind the retrospective catalogs. **Gated on AD-049 part 5's
linter tightening landing first.**

**`ProjectLifecycleState` is not `LifecyclePhase`.** ACTIVE / FROZEN /
ARCHIVED is a *storage posture*; the eight phases are the *research
process*. Two orthogonal axes: a project can be ACTIVE in Phase 3 or
ACTIVE in Phase 6, and FROZEN says nothing about which phase produced
it. Collapsing them would rebuild exactly the semantic collapse
`project.py:11-13` already warns against for
`lifecycle_state`/`research_outcome`. **`advance_phase()` never
silently mutates `lifecycle_state`.**

**3. Current phase is DERIVED from the transition record chain, not
stored on `Project`.** `Project` is **not modified**, and **no INV-12
exception is created** by Step 9. Four grounds:

- **Two writable representations of one fact, with no reconciling
  invariant, is the defect part 1 already catches** between the archive
  and the registry. Step 9 must not introduce a second instance of the
  problem it is fixing.
- **The failure directions are asymmetric.** With a damaged or
  truncated chain, a derived phase **under-claims** — it regresses to
  the last provable transition. A stored field **over-claims** — it
  asserts Phase 7 with the supporting evidence gone. Only one of those
  is a safe failure.
- **The three historical projects have no transition records at all.** A
  stored field forces a value for them and any value is invented — the
  same retroactive-fact violation `project.py:32-41` already refuses for
  `origin_date` ("inventing one would be a governance violation"). A
  derived phase returns *unknown*, which is the true answer.
- **It keeps INV-12 intact** through the whole of Step 9.

Stated cost: reading current phase requires Research to read
Governance's artifact (a legal edge, already required by the transition
flow) at O(chain length). With four projects and fewer than twenty
transitions that cost is not real; if it later becomes real, a cache is
a derived-value optimization with its own AD, not grounds to duplicate
the source of truth now.

**4. No transition is ever automatic, at any gate status.**
`advance_phase()` requires an explicit human authorization argument
every time. Gate status determines *what kind* of authorization is
required and *what must be disclosed* — never whether a machine may
proceed unattended.

| `sequence_status` | Automatic | Authorization required | Recorded as |
|---|---|---|---|
| PASS | Never | Explicit authorization at the Standard §2 level for the target phase | normal record |
| AMBIGUOUS | Never | Explicit authorization **plus** a written `decision_log.md` rationale naming each AMBIGUOUS gate and why advancing is justified | `authorized_with_ambiguity`, ambiguous gate names stored |
| FAIL | Never | Explicit **override**, Level 2 minimum, plus a decision-log entry stating the failed criterion and the grounds for overriding | `override`, stored distinctly — never silently equivalent to a pass |

*Why not auto-advance on PASS.* A runner's PASS means only "the frozen
criteria compared favourably." Standard §2 assigns every transition a
reviewer-independence level, which is a human obligation. Advancing on
PASS satisfies the comparison while skipping the review — AD-038's trap
in a new location.

*Why AMBIGUOUS is permitted-with-disclosure rather than blocking.*
AD-043 establishes that AMBIGUOUS means the gate lacked a trustworthy
frozen basis to decide — a **process** gap, not evidence against the
hypothesis. H3 advanced with documented AMBIGUOUS gates. Blocking would
retroactively invalidate that run and would pressure operators to invent
a threshold to clear the block, which AD-043 forbids. The control is
disclosure, not prohibition.

*Why FAIL blocks harder.* FAIL means a real frozen criterion was
evaluated and not met. Advancing is legitimate only as a disclosed
override with a named accountable reviewer. Recording `override`
distinctly from `authorized_with_ambiguity` is what stops a future
reader from seeing "advanced" and assuming the criteria were met.

**Vocabulary boundary.** `GateStatus` is PASS/FAIL/**AMBIGUOUS**;
Standard §7's cycle determination is PASS/FAIL/**INCONCLUSIVE**. These
are different vocabularies at different levels and no mapping exists
anywhere in the repository. The sequence aggregate keeps **gate**
vocabulary and is named `sequence_status`; the Phase 7 determination is
a separate, **human-authored** Standard §7 value; and **no code derives
the latter from the former.** Recording an aggregate as "AMBIGUOUS"
where Phase 7 requires "INCONCLUSIVE" would put a determination in the
archive in a vocabulary the Standard does not define.

**Authorization is recorded, never adjudicated.** Per Standard §4 the
platform stores the declared reviewer level verbatim and does not
validate the independence claim. No record may describe a Level 2 review
as "independent" unqualified.

**Evidence preconditions for any advance.** A `GateRunRecord` for
**every** gate the target phase requires (a missing gate is a refusal,
not an AMBIGUOUS); freeze `VERIFIED` at both bracket ends with a
non-empty covered-path set and the full list recorded (AD-047);
`measurement_provenance` present or its absence explicitly recorded as
an audit finding; and the decision chain verified intact and anchored
**before** the append, so a transition is never written onto a broken
chain.

**A5-C9 (AD-050 limb) — "verified intact and anchored" decomposes into a
machine half and a human half** *(A-5 R-5 and §7 C-9)*. The A-5 ruling
places exactly one requirement on this AD rather than on AD-048, and it
is this: the precondition immediately above is **two conditions, not
one**, and the word "anchored" must not be read as something the machine
did.

- ***Verified intact* is mechanical and automatic.** Recompute each
  record's canonical serialization and hash; check that record *N*'s
  stored predecessor hash equals record *N−1*'s computed hash; check
  `sequence_number` contiguity from 1 with no gaps or duplicates; check
  that a `null` predecessor appears at sequence 1 and nowhere else. This
  detects mutation, reorder, insertion, interior deletion and a forged
  predecessor — and **nothing about the tail**.
- ***Anchored* is a human act.** The verifier takes the expected
  `(sequence_number, head_hash)` pair **as an argument supplied by the
  operator**, read by hand from the previous transition entry's
  `**Machine chain anchor.**` line in the cycle's `decision_log.md`. If
  the pair is supplied, the verifier additionally confirms that the chain
  retains a record at that sequence number whose hash is that value.
  **No code reads, parses, or writes `decision_log.md`**, so the verifier
  never locates an anchor for itself; INV-10 holds on the read side as
  well as the write side.

Two consequences follow and are stated rather than left to be inferred.
**An advance whose operator supplies no expected pair has satisfied
*verified intact* and has not satisfied *anchored***, and must not be
recorded as though it had. And because the newest record is always
unanchored until its entry is written (AD-048's A5-C10), the chain a
transition is appended to is **anchored through the last cited sequence
number**, never "anchored" unqualified.

**Migration/status.** `Project`, `ProjectLifecycleState`, and
`ProjectRegistry`'s existing three methods are unchanged.
`core/research/lifecycle.py` is the only module permitted to import
Validation and Governance together, and is therefore the only legal
binding point between gate outcomes and decision records — because
Governance cannot import Validation, no other layer can perform that
binding at all. Deliberately **not** built: any `Phase` class hierarchy,
transition-table object, event bus, phase-entry/exit hooks, or
`LifecycleEngine` — the same discipline AD-033/AD-036/AD-040/AD-044
applied.

---

## Phase 4 / Step 9 — Phase E decisions (accepted 2026-07-24)

Phase D is complete and frozen (HEAD `c6b9682`, tag
`phase4-phase-d-complete`). Phase E composes the frozen Validation
apparatus (`GateRunner`, `GateRunRecord`) with the frozen Governance
apparatus (`DecisionRecorder`) at the single legal binding point
`core/research/lifecycle.py` (AD-050 Migration/status). The four ADRs
below are accepted here, in this reserved sequence, before any Phase E
code is written. The governing principle for all four is stated once and
applies to each: **the system must never record a claim stronger than
the mechanism that produced the evidence.**

### AD numbering — AD-052 … AD-055 are retired, not available

**Decision.** AD-052, AD-053, AD-054, and AD-055 are **reserved and
retired**; no ADR is ever created under those numbers. They were draft
numbers in `docs/STEP_9_ARCHITECTURE_RECONCILIATION_REVIEW.md` §6.2 and
`docs/STEP_9_VALIDATION_ORCHESTRATION_PROPOSAL.md` §14 that collided with
the reserved AD-047 … AD-050 block (AD-047's "Numbering" paragraph) once
AD-051 was accepted at `4c7ca8d` and AD-047 … AD-050 were accepted into
this log. The accepted ceiling before Phase E is **AD-051**; Phase E
therefore takes **AD-056 … AD-059** and steps over the retired block
rather than reusing a number whose draft meaning already lives, in
amended form, inside an accepted AD. New ADRs number from AD-056.

**AD-052 citation correction (dated governance note, 2026-07-24).** Every
reference to "AD-052" — including the ones still present in the frozen
Phase D files `core/validation/gate_context.py`,
`core/validation/__init__.py`, and `tests/test_gate_context.py` — is to
be read as **AD-047 part 2**. Draft AD-052 ("freeze-stability bracket / a
bracket over an empty covered-path set proves nothing") was subsumed,
amended, into AD-047 part 2 (the empty-covered-paths hole and its
non-emptiness precondition) when AD-047 was accepted. History is **not
rewritten**: the retired number is disclosed and mapped, not deleted from
the record. The literal in-code citation strings are **not corrected in
place** here, because those files are frozen for Phase E; correcting the
strings is a separate, non-Phase-E change (see this section's
"Governance risks carried forward").

**AD-055 citation correction (dated governance note, 2026-07-24).** Every
reference to "AD-055" — including the ones still present in the frozen
Phase D files `core/validation/gate.py` and
`core/validation/__init__.py` — is to be read as **AD-049 part 4**. Draft
AD-055 ("`ReviewLevel` is not introduced; review level stays `str`") was
subsumed, unchanged, into AD-049 part 4 (the runner's scope limits,
which include "`ReviewLevel` is not introduced … `review_level` stays
`str`") when AD-049 was accepted. Same disclosure discipline as AD-052:
mapped, not deleted; strings not rewritten in the frozen files.

### AD-056: A crashed `GateExecutionOutcome` is inadmissible evidence, not `AMBIGUOUS`

**Decision.** A crashed gate — a `GateExecutionOutcome` whose `error`
field is set and whose `result` is `None` (`core/validation/
gate_run_record.py`) — is **not** a `GateStatus`. It must never be
mapped, coerced, or "converted" to `PASS`, `FAIL`, `AMBIGUOUS`, or any
fourth governance status. A crash means the mechanism **failed to
produce a verdict** for that gate, which is categorically different from
the gate mechanically concluding one (INV-4, restated for the
composition layer; AD-043's "AMBIGUOUS is a process gap, not evidence"
does **not** extend to a crash — a crash produced no evidence at all).

**Consequences.**

- A crash in any outcome of the `GateRunRecord` being composed **blocks
  the transition**: `core/research/lifecycle.py` raises and returns no
  value.
- **No `DecisionRecord` is written.** The refusal happens strictly before
  the single `DecisionRecorder.append()` call, so the chain is left
  byte-for-byte unchanged — a crashed run leaves no trace in the
  governance chain, exactly as it should.
- The crash is rejected **before aggregation**. `aggregate_sequence_
  status()` takes `GateStatus` values only and never sees an envelope
  error; a crash cannot influence an aggregate because it is refused one
  layer earlier.

### AD-057: Governance `GateOutcome.status` is a closed transcription vocabulary

**Decision.** The persisted `core.governance.decision_recorder.
GateOutcome.status` string is drawn from a **closed three-value
vocabulary — exactly `"pass"`, `"fail"`, `"ambiguous"`** (the wire values
of `GateStatus`). No fourth value is ever transcribed; in particular a
crash never reaches this field (AD-056), and there is no `"crashed"`,
`"error"`, `"unknown"`, or `"inconclusive"` status here. Governance
cannot import Validation (`ALLOWED_DEPENDENCIES["governance"] ==
{"data"}`), so it stores the **string** rather than the enum; the closed
vocabulary is therefore an obligation on the **only writer**,
`core/research/lifecycle.py`, which transcribes each admitted gate's
`GateStatus.value` and nothing else.

**Consequences.**

- The composition layer never invents a status string; it reads
  `GateResult.status.value` for each admitted (non-crashed) gate.
- This is transcription, not certification (AD-048): the recorder cannot
  re-derive whether a transcribed status is true, so the correctness of
  the closed vocabulary rests entirely on this single writer honouring
  it. Widening the set would require reopening this AD.

### AD-058: Genesis `from_phase` is an explicit human assertion; an empty chain derives `UNKNOWN`

**Decision.** Current phase is **derived** from the transition-record
chain, never stored on `Project` (AD-050 part 3; D-14). An **empty
decision chain derives to `UNKNOWN`** — not to `Hypothesis`, not to any
other phase. Registering a cycle (e.g. `reference_h4`) **does not imply
`Hypothesis`** or any phase (AD-050 A6-C5). There is **no hidden phase
default** anywhere: no `Project.current_phase` field, and no fallback
that substitutes a phase the operator did not supply.

- `UNKNOWN` is a **research-domain derived-state value, not a ninth
  `LifecyclePhase`.** `core/shared/lifecycle_phase.py` remains exactly the
  eight phases transcribed from `RESEARCH_GOVERNANCE_STANDARD.md` §2 and
  pinned by test; adding `UNKNOWN` to that enum would corrupt the
  transcription invariant, so `UNKNOWN` lives outside it as a typed
  sentinel.
- **The first transition requires an explicit `from_phase` argument.**
  Because an empty chain derives `UNKNOWN`, the machine cannot derive a
  genesis `from_phase`; the operator asserts it, and the primitive
  `advance_phase(from_phase, …)` (AD-050 part 4) already takes it as a
  required parameter. Genesis is therefore a human assertion of the
  starting phase, recorded as supplied.
- **Non-genesis transitions must not contradict the chain.** When the
  chain is non-empty, the derived current phase is authoritative and the
  supplied `from_phase` must equal it, or the transition is refused —
  this is what stops a stored/supplied phase from over-claiming past what
  the chain proves.
- **Failure direction is safe by construction** (AD-050 part 3): a
  damaged or truncated chain under-claims (regresses toward `UNKNOWN` or
  the last provable phase), never over-claims. `INV-12` is preserved:
  `Project` is not modified and no INV-12 exception is created.

### AD-059: The research lifecycle is the sole Validation + Governance composition boundary

**Decision.** `core/research/lifecycle.py` is the **only** module that
imports Validation and Governance together and is therefore the **only**
legal place a gate-outcome run (`GateRunRecord`) is bound to a governance
record (`DecisionRecord`) (AD-050 Migration/status; the import table
makes any other binding point impossible, since Governance cannot import
Validation). Phase E adds this composition **without modifying** any
frozen Phase D module — `decision_recorder.py`, `gate_runner.py`,
`gate.py`, `gate_result.py`, `gate_context.py`, `freeze_verifier.py`,
the `Project` model, and the import-boundary rules are all untouched.

The composition performs, in order, and refuses (writing no
`DecisionRecord`) at the first failure:

1. **Gate completeness** — a `GateRunRecord` result exists for **every**
   gate the target phase requires; a missing required gate is a refusal,
   never an `AMBIGUOUS` (AD-050 evidence preconditions). What a phase
   requires is `ValidationRegistry`'s to state, not the lifecycle's to
   invent.
2. **Crash rejection** — any crashed outcome refuses the transition
   (AD-056), before aggregation.
3. **Bracket rejection** — `GateRunRecord.bracket_invalidated is True`
   refuses the transition.
4. **Freeze projection from stored artifacts only** — the freeze status
   is projected from the **stored** `pre_freeze_verification` and
   `post_freeze_verification` on the `GateRunRecord`. `verify_freeze` is
   **never called again** during composition. The projected
   `freeze_verification_status` is `"verified"` **only** when both stored
   verifications are `VERIFIED` and their `resolved_hash` values are
   equal; otherwise the transition is refused. There is **no** conversion
   of a non-verified bracket to `AMBIGUOUS`.
5. **Aggregation** — `aggregate_sequence_status()` (pure: `GateStatus`
   inputs only, no IO, no git, no clock, deterministic) computes the
   sequence status: `PASS` iff every gate passed, `FAIL` if any gate
   failed (**FAIL dominates AMBIGUOUS**), `AMBIGUOUS` otherwise. It
   **refuses an empty input** rather than returning a vacuous `PASS`,
   mirroring AD-047/AD-051's refusal of vacuous verification — an empty
   sequence is never permitted to reach it in any case, because
   completeness (step 1) is checked first.
6. **Authorization** — the pure `advance_phase()` primitive (AD-050 part
   4) decides legality and record kind from the aggregate and the
   recorded human `Authorization`; an unauthorized status raises.
7. **Provenance pass-through** — `DecisionRecord.evidence_refs` are
   **pass-through only**: collected from the admitted gate results in
   requested-gate order, **stably deduplicated**, with **no generated
   strings**. `reproduction_record_ref` is **exactly**
   `GateRunRecord.measurement_provenance` (which may be `None`; its
   absence is recorded as-is, an audit finding per AD-050, never
   invented).
8. **Append** — the chain is verified intact, and (for a non-genesis
   transition) anchored against the operator-supplied `(sequence_number,
   head_hash)` pair (AD-050 A5-C9), **before** the single
   `DecisionRecorder.append()` call. Genesis (empty chain) has nothing to
   anchor and its `predecessor_hash` is `None` by the recorder's own
   construction.

**Aggregation lives in Research, never Validation** (AD-049 part 3):
`GateRunRecord` still carries no aggregate field, and the aggregate is
recomputed under this documented rule rather than stored — mirroring
`DecisionRecord`, which also stores per-gate outcomes only.

### Governance risks carried forward (2026-07-24)

- **Stale in-code AD citations.** `core/validation/gate.py`,
  `core/validation/gate_context.py`, `core/validation/__init__.py`, and
  `tests/test_gate_context.py` still cite the retired numbers AD-052 /
  AD-055. The mapping above (→ AD-047 part 2 / AD-049 part 4) is the
  governing correction; the literal strings are left in place because
  those files are frozen for Phase E. Correcting them is a separate,
  disclosed, non-Phase-E change.

### AD-060: `VerificationResult.covered_paths` closes the Phase E freeze covered-path binding gap (accepted 2026-07-24, Remedy A)

**Finding.** A governance audit of the Phase E composition
(`compose_transition()`) found that `DecisionRecord.freeze_covered_paths`
was populated directly from the caller-supplied `GateContext`, guarded
only by a `freeze_commit_ref` equality check. `VerificationResult` (the
type stored on `GateRunRecord.pre_freeze_verification` /
`post_freeze_verification`) never recorded which paths a given
`verify_freeze()` call actually covered, and `GateRunner._context_digest`
deliberately excludes the freeze basis from its hash (its docstring's
premise -- that the freeze basis is "recorded on the envelope in its own
field already" -- holds for `freeze_commit_ref` but not for
`freeze_covered_paths`). The result: a `GateContext` sharing the run
record's commit ref but naming different, wider, or entirely unverified
paths would be recorded as though those paths had passed freeze
verification, with nothing to catch it. This violates this log's
governing principle for Phase E (stated where AD-056 … AD-059 were
accepted): **the system must never record a claim stronger than the
mechanism that produced the evidence.**

**Decision (Remedy A — the approved remedy; no alternative remedy is
implemented).** `core.governance.freeze_verifier.VerificationResult`
gains one additive field, `covered_paths: tuple[str, ...]`, set by
`verify_freeze()` to the exact `covered_paths` it was called with (not
deduplicated, not sorted, recorded even when the result is `DRIFTED` or
`UNVERIFIABLE`). This is a scoped, disclosed amendment to AD-059's
frozen-file list for `freeze_verifier.py` — the addition is the sole
Phase E change to that file, and it does not touch `verify_freeze`'s
verification logic, `FreezeStatus`, or any existing field's meaning.
`GateStatus`, `DecisionRecord`'s field set, and AD-047 … AD-059's own
text are unchanged.

`core/research/lifecycle.py`'s `compose_transition()` uses the new field
to close the gap in two ways:

1. **Guard, before trusting `context`.** In addition to the existing
   `freeze_commit_ref` check, `context.freeze_covered_paths` (as a set)
   must equal *both* `run_record.pre_freeze_verification.covered_paths`
   and `run_record.post_freeze_verification.covered_paths` (as sets), or
   `ContextRunRecordMismatch` refuses the transition before any
   `DecisionRecord` is written. Checking both bracket ends catches a
   hand-built run record whose two ends disagree, not just a
   context/run-record mismatch.
2. **Source of truth for the persisted field.** `DecisionRecord.
   freeze_covered_paths` is written from
   `run_record.pre_freeze_verification.covered_paths` — the run record's
   own verified evidence — never from `context.freeze_covered_paths`
   directly. Once the guard above holds, the two sets are equal, but the
   value actually persisted is mechanically the verified one.

**Consequences.** A context claiming coverage broader than, narrower
than, or merely different from what was actually run through
`verify_freeze()` now refuses the transition instead of being recorded
as verified. Matching coverage continues to pass unchanged, and the
persisted path list may differ in *order* from `context`'s (it reflects
the verified evidence's own order), which is expected and covered by
regression tests. This closes the gap without reopening `GateStatus`,
`DecisionRecord`'s schema, or any accepted AD's semantics.

### AD numbering — AD-061 … AD-067 are reserved to Phase F, and a reservation is discoverable only here

**Decision.** AD-061, AD-062, AD-063, AD-064, AD-065, AD-066, and AD-067
are **reserved** to the Phase 4 Phase F Research Execution Engine. The
reservation is recorded at
`docs/PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` §5 ("Required AD
content, as resolved"), which fixes the required content of all seven and
states that the accepted ceiling is AD-060 and that this file "contains
**no occurrence** of AD-061 … AD-067." That statement is true and this
block exists to keep it true. New ADRs therefore number from **AD-068**.

**The reservation is live but unaccepted, and those are different
things.** None of the seven is accepted: acceptance is Phase F's F-0,
which `PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` §1.2 and §7 record as
**blocked** for want of an independent review that does not exist as a
repository artifact. A reservation nevertheless binds from the moment it
is recorded. Whether Phase F is accepted bears on Phase F's *decisions*;
it does not bear on Phase F's *claim to the numbers*. Reserved numbers
are released **only by a recorded decision in this file** — never by a
later change observing that the numbers are unoccupied and taking them.

**The general rule, which is the actual repair.** A number is reserved
from the moment any governance document claims it, and
`docs/ARCHITECTURE_DECISIONS.md` is the **single place a reservation is
discoverable**. Any document that claims a range must have that claim
mirrored here, in a block like this one, in the same commit that makes
the claim. This block is written because that rule was not in force: the
Phase F reservation lived only inside an unaccepted proposal document,
invisible to a reader of this file, and boundary-hardening step 2 was
consequently drafted as "AD-061" and cited under that number from six
files before the collision was found. Nothing but this rule prevents the
next one.

**Precedent.** This is the same instrument as the AD-052 … AD-055
retirement block above, applied to a reservation rather than a
retirement: the number is disclosed and fenced, not silently skipped.
The two blocks differ in one respect worth stating — AD-052 … AD-055 are
retired *permanently* and no ADR will ever be created under them, while
AD-061 … AD-067 are held *for a named owner* and would be written under
those numbers if F-0 were ever accepted.

> **Amendment — 2026-07-24: the next-free-number sentence is stale;
> nothing else in this block changes.** *"New ADRs therefore number from
> **AD-068**"* was true when written and is false now — AD-068 (`:3139`
> below) and AD-069 (`:3274` below) are both accepted since. **The next
> free number is AD-070.** This corrects only that one status sentence.
> Every decision sentence above — the reservation of AD-061 … AD-067 to
> Phase F, the release condition, and the general rule — is unchanged and
> is not superseded by this note. The reservation block's other stale
> sentence, describing F-0 as blocked "for want of an independent review
> that does not exist as a repository artifact," is **not** corrected
> here: that correction records that F-0's blocker is discharged, which
> is true only once AD-061 … AD-067 are actually written and accepted,
> and neither has happened as of this note. It is superseded in the same
> commit that performs that acceptance, not before.

> **Amendment — 2026-07-24: F-0 performed; the "independent review"
> sentence is superseded.** The reservation block's other stale sentence
> — describing F-0 as blocked "for want of an independent review that
> does not exist as a repository artifact" — is superseded here, in the
> leveled terms `RESEARCH_GOVERNANCE_STANDARD.md` §4 requires and
> `docs/PHASE_F_ACCEPTANCE_CONDITIONS.md` F-C4 §4.3 item 4 binds: F-0's
> blocker is **discharged, not waived**, and not by the discovery of an
> independent review — none exists and none can be produced on this
> platform (Standard §4). It is discharged by
> `docs/PHASE_F_ARCHITECTURE_ACCEPTANCE.md`, a **Level 2 AI-assisted
> adversarial architecture review**, having been read and its conditions
> (C-1 … C-12, extended by `docs/PHASE_F_ACCEPTANCE_CONDITIONS.md`'s
> F-C1 … F-C4 and by `docs/PHASE_F_IMPLEMENTATION_READINESS_REVIEW.md`'s
> R-16 … R-23, disposed of by
> `docs/PHASE_F_PRE_IMPLEMENTATION_AMENDMENT_PLAN.md`) folded into
> AD-061 … AD-067 below, with **Level 3 review's unavailability on this
> platform disclosed** rather than papered over.
> `docs/PHASE_F_ARCHITECTURE_ACCEPTANCE.md` must never be cited as "the
> independent architecture review." AD-061 … AD-067 are accepted below.
> Combined with the already-accepted AD-068 and AD-069, every number
> from AD-047 through AD-069 is now either accepted or permanently
> retired (AD-052 … AD-055); no reserved-and-unaccepted number remains,
> and the next free number for any future ADR is **AD-070**, as the
> prior amendment note already established.

### AD-068: ETF is a domain distinct from Data, identified by symbol until it is identified by path (accepted 2026-07-24)

**Review basis.** `docs/PHASE_4_STORE_EXTRACTION_GOVERNANCE_RESOLUTION_2026-07-24.md`,
findings GR-04, GR-05, GR-08, GR-09, GR-11, and test T-1. That document
is **Level 1** — one reader with repository access — and discharges no
independent-review requirement. It must never be cited as an independent
review of this decision, and this AD is accepted on that understanding.

**Context.** `docs/PLATFORM_ARCHITECTURE_V1.md` Section 1 states the
platform's goal directly: "adding a new asset class (equities, crypto,
bonds) never requires touching Research, Validation, Statistics,
Governance, or Reporting — only a new Data-domain provider". Section 3
requires Statistics to have "no knowledge that 'ETF' or 'H3' exist".
Both statements are only meaningful if **ETF names something distinct
from generic market data** — and until this decision, nothing in the
repository made that distinction. The import checker mapped
`core.analytics` (ETF scoring and ranking) to the `data` domain, and the
ETF-specific types living inside `core.market_data` were
indistinguishable from the asset-class-neutral ones beside them. Every
platform domain could reach ETF concepts through an edge the Section 5
table blesses as "→ Data", and the coupling was invisible to the only
mechanism that could have reported it.

Five decisions are recorded here. None is derivable from any accepted AD.

**Decision 1 — ETF is a domain, and Section 5 gains a row and a column.**
`core.analytics` maps to `etf`, not to `data`. Per
`docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md` Section 1, only
`core.analytics.persistence` was ever formally Data-domain code; the rest
is "not yet a domain; stays product logic". Under an ETF/Data split that
persistence layer is *ETF-scoring* persistence, so the package moves
whole. ETF may depend on Data and Statistics (and on the kernel, like
every domain).

**Decision 2 — no domain may depend on ETF.** An asset class is a
plug-in *above* the platform, never something the platform reaches down
into. `etf` therefore appears in no other domain's allowed set,
including Data's. This is a **novel rule with no Section 5 precedent** —
that document's forbidden list contains no "nothing may depend on X"
entry — which is why it needs recording rather than assuming. It is the
executable form of Section 1's asset-class-neutrality goal: if a new
asset class must never require touching Research, Validation,
Statistics, Governance, or Reporting, then an edge from any of them into
ETF is a violation by construction.

**Decision 3 — domain attribution by imported symbol, not by module
path.** `ETF_SYMBOLS_BY_MODULE` names the ETF-specific symbols that
physically live in asset-class-neutral modules — `ETFId` in
`core.shared.ids`, `ETF` in `core.market_data.domain.models`, and the
`insert_etf` / `get_etf` / `get_etf_by_ticker` repository functions. An
import is attributed to `etf` by the **name it binds**, not by the module
that currently hosts the definition, so the checker can report
`governance -> etf` for a line whose module path reads
`core.market_data`.

This is a **deliberate departure from Section 5's Enforcement clause**,
which states the check is "a matter of scanning `import` statements by
top-level package name, **no AST-level cleverness required**." The
justification is that step 1 **does not move files** — a path-only
checker cannot see a domain that has no package of its own, so the
choice is symbol attribution or no visibility at all. The alternative,
relocating the symbols first, would make the boundary change and the
file moves one indivisible diff with no intermediate state in which the
coupling is measurable.

**The departure has a termination condition, and it is recorded so the
mechanism does not outlive its reason:** symbol attribution is permitted
**only for domains not yet separated by package path**, and this use of
it ends when `ETF_SYMBOLS_BY_MODULE` empties — at which point ETF is
identified by path like every other domain and the per-alias attribution
becomes dead code to be deleted. Section 5's Enforcement clause is
amended in the same commit as this AD to say exactly that. Nothing here
licenses AST analysis for any other purpose.

**Decision 4 — the pre-existing coupling is inventoried, not
discharged, and the inventory ships as an `xfail(strict=True)` marker.**
Step 1's whole thesis is that inventory is not repair. Five
`data -> etf` and related violations exist in the tree today; this
decision makes them *named and countable* (`format_inventory` groups
them by domain edge) and deliberately does **not** fix them. That is
step 3's work.

The posture is recorded in the test suite by
`tests/test_import_boundaries.py::test_real_repository_has_no_boundary_violations`
carrying `@pytest.mark.xfail(strict=True)`. The earlier draft of this
work shipped the test simply failing. That was rejected: this repository
has **no CI**, so `pytest` is the only gate, and a permanently red suite
destroys that gate for every unrelated test, hides the next real
regression at the summary line, and trains the sole human gate to ignore
red output. `skip` was also rejected — it removes the assertion, so the
coupling stops being checked and nothing detects the day it is
discharged. `strict=True` is what makes the marker better than a red
test rather than weaker: an **unexpected pass is a failure**, so the day
the last coupling is discharged the suite forces the marker's removal.

Conditions on this, all binding: `strict=True` is mandatory; the
`reason` must name the discharging step; the paired green inventory test
`test_known_etf_coupling_inventory_is_exactly_as_documented` is retained
(the marker records the aspiration, the inventory test records the exact
current state, and neither substitutes for the other); the marker is
scoped to **exactly one test** and is **not** precedent for deferring any
other failure. AD-005 is unaffected — `pytest` is already the runner and
no framework is added.

**This is the first `xfail` in the repository.** There is no prior use of
any test-outcome marker here, so the convention is introduced by this
decision and is stated rather than left to be inferred.

**Decision 5 — `ETF_SYMBOLS_BY_MODULE` is a hand-maintained shrink
inventory.** It is not an allow-list and nothing is exempted by
appearing in it; each entry is a generic module that still declares an
asset-class-specific name, and the mapping shrinks to empty when the
split is real. Its accuracy is guaranteed by **no mechanism** — a rename
or relocation of a listed symbol would silently stop matching,
violations would drop toward zero, and the `xfail` would pass
unexpectedly. Under `strict=True` that unexpected pass fails the suite
loudly, which is the intended interaction, but it reports "split
complete" for the wrong reason. `test_every_etf_symbol_resolves_in_its_named_module`
(T-1) closes this by asserting every listed symbol actually exists where
the mapping says it does. That test guards a **false-success** mode and
is the highest-value test in this change; if it ever fails it must be
investigated, never adjusted to pass.

**Consequences.** Section 5's dependency table gains an ETF row and
column and a "nothing may depend on ETF" forbidden entry; its
Enforcement clause is amended to permit symbol attribution for domains
not yet separated by package path, with the termination condition above.
Both amendments ship in the same commit as this AD, so this AD's claim
to amend Section 5 is true by construction rather than by intention.
`core.analytics` is no longer Data-domain code for checker purposes,
which makes previously-blessed edges into it visible as violations —
that visibility is the deliverable. This AD does **not** discharge those
violations, does **not** move any file, and makes no claim about the
`adapters/` tree, which `check_repository` does not scan.

### AD-069: Storage primitives live in `core.store`, a substrate below Data that Data and Governance may reach (accepted 2026-07-24)

**Review basis.** `docs/PHASE_4_STORE_EXTRACTION_GOVERNANCE_RESOLUTION_2026-07-24.md`,
findings GR-02, GR-03, GR-04, GR-06, GR-07, GR-08, GR-18, GR-19, §5, §6
and §7. That document is **Level 1** — one reader with repository access
— and discharges no independent-review requirement. It must never be
cited as an independent review of this decision.

**Context.** `connect()` and `run_migrations()` sat in
`core/market_data/persistence/`. Neither has ever had any market-data
content: `connect()` sets three sqlite3 options, and `run_migrations()`
applies whatever `*.sql` files it is handed against a `schema_migrations`
ledger it owns. They lived in the Data domain only because `market_data`
was the first package that needed a database.

AD-068 made the cost visible. `core.market_data` is **not**
asset-class-neutral — the checker now reports `data -> etf` violations
inside it — yet Governance, the CLI, the tests, and every experiment
script had to import that package merely to open a connection. The
allowed `governance -> data` edge was therefore carrying two unrelated
things at once: a legitimate need for the storage substrate, and a
dependency on an ETF-contaminated package. Neither could be tightened
without hurting the other.

**Decision.**

1. `connect()` moves to `core/store/connection.py` and
   `run_migrations()` to `core/store/migrations.py`, **verbatim**. This
   is a relocation, not a rewrite: the transaction-mode contract
   documented on `connect()` — `isolation_level=""`, on which every
   rollback guarantee in this project depends — is unchanged.
2. `core.store` is a **domain in its own right**, added to the Section 5
   dependency table. It is **Layer −1**: substrate, below Data and
   Statistics. Its own allowed set is **empty** — the substrate reaches
   nothing.
3. `core.store` is **not** folded into the shared kernel, despite the
   kernel's "every domain may import it" exemption looking like a free
   fit. The kernel is a pure value vocabulary (`Money`, `Clock`, ids)
   with no I/O. Mapping a package that opens files and executes SQL to
   `"kernel"` would make `kernel -> store` a same-domain import and thus
   permanently unflaggable, letting `core.shared` acquire sqlite3
   unnoticed. Keeping them distinct preserves that check
   (`tests/test_import_boundaries.py::test_shared_kernel_may_not_depend_on_store`).
4. **Scope is the two primitives and nothing else.** Repository
   functions know table names and stay in their owning domain —
   `core.market_data.persistence.repository` for market data,
   `core.analytics.persistence.repository` for ETF scoring. No dataset
   abstraction is introduced, and none is reserved for.
   `tests/test_store_extraction.py::test_store_holds_only_the_two_primitives`
   fails if a third module appears, so widening the substrate requires a
   new decision rather than a quiet commit.

**Permission ledger — exactly what this decision changes in Section 5.**
An earlier draft of this ADR closed with the sentence *"amends
docs/PLATFORM_ARCHITECTURE_V1.md Section 5's dependency table by
addition only; no existing edge changes direction or permission."* That
sentence was **false in both clauses** and is deleted rather than
softened: adding a column that some existing row is granted *is* a
permission change to that row, and "addition only" was true of the
table's shape while false of its content. In a repository with no CI,
where ADRs are the governing artifact and the reader is a human auditor,
an ADR that misstates its own effect on the normative table is the
highest-consequence defect available — it is what a future reader trusts
*instead of* re-deriving the diff. The replacement is an explicit ledger:

| Row | Before | After | Change |
|---|---|---|---|
| Data → Store | ✕ | **✅** | **Loosened.** Demanded by the two shims. |
| Governance → Store | ✕ | **✅** | **Loosened.** Demanded by `reconstruction_loader` and `reproduction_runner`. |
| Statistics → Store | ✕ | ✕ | **Unchanged.** |
| ETF, Validation, Research, Reporting → Store | ✕ | ✕ | **Unchanged.** No importer. |
| Kernel → Store | ✕ | ✕ | **Unchanged**, and structurally load-bearing (clause 3). |
| Store → anything | — | ✕ | New row, empty set. |
| Every pre-existing non-Store edge | — | — | **Unchanged.** No edge changes direction. |

**Two rows are loosened, and no more.** An earlier draft granted `store`
to **all seven** non-kernel domains. That is rejected. The demonstrated
demand under `core/` is four import sites in three files across two
domains; five domains would have received a storage edge no code uses.
Worse, the broad grant **refuted this ADR's own clause 3 inside the same
change**: clause 3 argues at length that `store` must stay outside the
kernel because "the kernel is a pure value vocabulary and must not
acquire I/O", and the broad grant then handed that exact I/O edge to
`statistics`, which §4.3 defines by the identical purity property.

**The growth rule is demand-driven.** A domain is added to the grant
list when a real importer appears, by recorded decision, **in the commit
that introduces the importer**. Adding a grant later is a one-line
reviewed change; a granted-but-unused edge is invisible drift that a
future module can occupy silently. Under a broad grant, a future
`core/statistics` module opening a database would be architecturally
legal and would pass the checker — which would contaminate the purity
claim that this project's reproducibility arguments rest on. This is the
same shrink-inventory discipline already applied to
`ETF_SYMBOLS_BY_MODULE` and to the shims.

**The two denials are refused on different grounds, and the distinction
is recorded so it is not re-litigated:**

- **`data -> store` is not an upward edge.** Section 5 forbids "Data →
  anything" on the stated rationale that "the foundation never calls
  upward." Store sits **below** Data — it is substrate, Layer −1 — so
  the edge is consistent with that rationale while violating its literal
  wording. The wording was over-broad, and Section 5's entry is reworded
  to *"Data → anything **above it**"* with its rationale preserved
  exactly.
- **`statistics -> store` is denied on purity, not layering.** §4.3
  defines Statistics as a pure computational library; it is refused I/O
  for the same reason the kernel is. That is the ground to record
  because it is the ground that survives future layer changes.
  **Section 5's "Statistics → anything" entry — the single hard rule —
  is left textually untouched by this decision**, which is stated
  explicitly here because the earlier draft did touch it.

**The shims are permanent, and the reason usually given is the secondary
one.** `core/market_data/persistence/database.py` and `migrations.py`
survive as re-export shims. The earlier draft gave exactly one reason:
nine hash-protected Phase-0 `.py` files
(`tests/fixtures/protected_file_hashes.json`,
`tests/test_repository_integrity_snapshot.py`) import a legacy path and
may not be edited, nor may the fixture be regenerated to permit an edit.
That reason is factually correct but it is **not the binding one**, and
the inversion matters because the stated reason could in principle
expire while the real one cannot.

> **PRIMARY — pinned-commit module resolution.**
> `core/governance/reproduction_runner.py` reproduces archived research
> cycles by prepending a pinned worktree to `sys.path` and
> `exec_module`-ing the pinned experiment script. But `sys.modules['core']`
> is **already populated with HEAD's package** — the runner *is*
> `core.governance.reproduction_runner`. Python therefore resolves
> `core.market_data.persistence.database` through **HEAD's**
> `core.__path__`, not through `sys.path`, so a pinned script's legacy
> import binds **HEAD's shim** and never the worktree's own copy. There
> is no `sys.modules` isolation anywhere in `core/`. This is live, not
> theoretical: all three archived cycles pin resolvable commits
> (`07f0da3`, `19771d4`, `8831d54`), and all three pin
> `daily_etf_universe_update.py`, which imports **both** legacy paths.
>
> **SECONDARY — hash-protected evidence**, as above.

**The failure mode, as this decision was accepted: a crash, not a
governed status.** *This paragraph describes the behaviour of
`reproduction_runner.py` as it stood when AD-069 was accepted. Commit
`91634c8` (2026-07-24) changed that classification; the paragraph is
retained unedited because it is the reasoning the decision was accepted
on, and is superseded on the facts by the amendment immediately below.*
If the shims
were deleted, the resulting `ImportError` would not degrade a
reproduction to `UNVERIFIABLE` or `DRIFTED`. In
`reproduction_runner.py`, `_load_expected_tickers_from_worktree` wraps
the load in `except OSError` only, its caller catches
`ReproductionRunnerError` only, `ImportError` is in neither and is not
in `_DRIFT_ERRORS`, and it is raised **before** the
`reconstruct_database` block whose broad `except Exception` maps
failures to `DRIFTED`. A missing shim therefore propagates out of
`run_reproduction` as an **uncaught exception**: no governed status, no
evidence record, nothing auditable. This is what makes the retirement
condition below a hard prohibition rather than a caution. Widening the
runner's exception mapping to govern `ImportError` changes that module's
status semantics and is **out of scope** here; it is recorded as an open
item.

> **Amendment — 2026-07-24, commit `91634c8`: the classification
> changed; the decision does not.** That open item is now discharged.
> `_load_expected_tickers_from_worktree` catches `(OSError, ImportError)`
> and raises `ReproductionRunnerError`, which its caller maps to
> `UNVERIFIABLE`; the reconstruction phase catches `ImportError` ahead of
> the `DRIFTED` backstop and maps it to `UNVERIFIABLE` as well. A missing
> shim is therefore an **unresolvable pinned artifact** with a governed
> status and an evidence record, not an uncaught exception. Concretely,
> for the three archived cycles the preload runs first —
> `experiment_module_relative_path == UNIVERSE_MODULE_RELATIVE_PATH ==
> "experiments/daily_etf_universe_update.py"` for all three — so a
> deleted shim returns `UNVERIFIABLE` before reconstruction is reached.
> The execution phase is deliberately unchanged: an `ImportError` out of
> the pinned module's own load-and-run remains `REPRODUCTION_FAILED`.
> **The retirement prohibition below therefore no longer rests on
> "uncaught crash / no audit trail"; the surviving rationale is stated
> there.** No shim is deleted, no permission is changed, and clauses 1–4
> of the Decision stand.

**Retirement condition — binding.** The shims may be deleted only when
**both** hold:

> **(a)** no file in the working tree imports either legacy path; **and**
> **(b)** **no reproducible commit imports either legacy path** — that
> is, for every cycle under `research_archive/*/` with a `COMMIT.txt`,
> the pinned commit's own tree contains no import of
> `core.market_data.persistence.database` or
> `core.market_data.persistence.migrations`.

Condition (b) is **strictly stronger** than (a) and is the binding one.
Satisfying (a) alone and deleting the shims is a **prohibited act**:
even with governed `UNVERIFIABLE` status, removing the shim permanently
prevents reconstruction of archived cycles and therefore destroys the
ability to reproduce validated research states. It does so silently,
**with a fully green test suite**. The earlier draft's shrink message
instructed exactly that,
deriving the deletion premise from the current tree alone; that message
is corrected, and `test_legacy_shim_importers_are_exactly_the_frozen_files`
is strengthened to read `research_archive/*/COMMIT.txt` and refuse the
deletion premise while any pin imports a legacy path (T-3). **Currently
(a) is satisfied for all non-frozen files and (b) is not satisfied and
cannot be**, because those three commits are immutable and all three
import both paths. **The shims are therefore permanent for the
foreseeable life of the repository, and must not be described as a
transitional alias.** If (b) ever becomes satisfiable, retirement is a
governance act requiring a new ADR recording which archived cycles were
re-verified after deletion and by whom; a green suite is necessary and
**not sufficient** evidence.

> **Amendment — 2026-07-24: the evidence reference above names the wrong
> test; the T-3 predicate, condition (b), and the decision are
> unchanged.** The paragraph above cites
> `test_legacy_shim_importers_are_exactly_the_frozen_files` as the test
> "strengthened to read `research_archive/*/COMMIT.txt` and refuse the
> deletion premise while any pin imports a legacy path (T-3)." The
> T-number is right and the predicate is described correctly; the **test
> identity** is wrong.
>
> T-3 is **`test_pinned_commits_still_require_the_shims`**
> (`tests/test_store_extraction.py:307`). It landed in `6f81bf2`, the
> same commit as this ADR, as a **separate, new** test — not as a
> strengthening of an existing one. Its own docstring reads *"T-3.
> Retirement condition (b) of AD-069, made mechanical,"* and the T-3 row
> of `docs/PHASE_4_STORE_EXTRACTION_GOVERNANCE_RESOLUTION_2026-07-24.md`
> states the same predicate against the same commit.
>
> The test actually named was **not** strengthened to read `COMMIT.txt`
> and does not implement condition (b). Its predicate runs over
> `tests/fixtures/protected_file_hashes.json` — which files at HEAD may
> still import a legacy path — which is condition **(a)**'s territory.
> The two predicates are disjoint in code: `_archived_commit_pins()`
> reads `COMMIT.txt` and is called only by the T-3 test, while
> `_frozen_python_files()` reads the hash fixture and is called only by
> the named one. What GR-07 changed in the named test was its assertion
> **message**, which now directs a reader to the T-3 test for the binding
> condition.
>
> **The evidence chain is therefore: condition (b) → T-3 →
> `test_pinned_commits_still_require_the_shims`.**
>
> Nothing above is rewritten. Condition (b) stands as written, it remains
> unsatisfiable while the three archived pins are immutable, the shims
> remain permanent, and clauses 1–4 of the Decision stand. Only the
> pointer to the mechanism is corrected. The same drift reached
> `reproduction_runner.py`'s docstring, where it had additionally been
> attached to the `sys.modules` claim that T-2 pins; that copy was
> corrected at `e5b3e96`.

**Carried-forward inaccuracy, disclosed not repaired.**
`reproduction_runner`'s own docstring claims pinned code comes "never
from `repo_root`'s current HEAD copy." That is accurate for the
experiment script, which is loaded by file path, and **inaccurate for
the `core.*` modules it imports**, per the mechanism above. This is a
**pre-existing** defect, not introduced here — but this decision makes
the repository *depend* on it, which converts a latent inaccuracy into a
load-bearing one. Repairing it is out of scope and is recorded as an
open item.

> **Amendment — 2026-07-24, commit `91634c8`.** That open item is
> discharged too: the docstring now states that the worktree isolation
> covers the pinned script's *own source* only, and that its `core.*`
> imports resolve through HEAD's `core.__path__`. The **mechanism** is
> unchanged and remains load-bearing — only its disclosure moved from
> this ADR alone into the module itself.

**Consequences.** `governance -> data` now means only what it says; the
storage need has its own edge. `core.store` importing anything this
repository defines — kernel included — is a test failure
(`test_store_imports_nothing_from_core`), which is stricter than the
allowed-dependency table can express, since the kernel is an exempt
target for every domain. Section 5 gains a Store column granted to Data
and Governance only, and its "Data → anything" entry is reworded to
"Data → anything above it"; both amendments ship in the same commit as
this ADR. The five known ETF violations are untouched — AD-068 exposed
them and neither decision discharges them. This decision does **not**
modify `reproduction_runner.py`.

---

## Phase 4 / Phase F — Research Execution Engine, F-0 (accepted 2026-07-24)

Accepts the seven ADs reserved above, per
[`docs/PHASE_4_PHASE_F_RESEARCH_EXECUTION_ENGINE_PROPOSAL.md`](PHASE_4_PHASE_F_RESEARCH_EXECUTION_ENGINE_PROPOSAL.md)
(the "Proposal"), as amended by
[`docs/PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md`](PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md)
(the "Resolution", findings R-1 … R-7), reviewed and conditioned by
[`docs/PHASE_F_ARCHITECTURE_ACCEPTANCE.md`](PHASE_F_ARCHITECTURE_ACCEPTANCE.md)
(conditions C-1 … C-12) and
[`docs/PHASE_F_ACCEPTANCE_CONDITIONS.md`](PHASE_F_ACCEPTANCE_CONDITIONS.md)
(conditions F-C1 … F-C4), and closed out for implementation readiness by
[`docs/PHASE_F_IMPLEMENTATION_READINESS_REVIEW.md`](PHASE_F_IMPLEMENTATION_READINESS_REVIEW.md)
(findings R-16 … R-23), disposed of by
[`docs/PHASE_F_PRE_IMPLEMENTATION_AMENDMENT_PLAN.md`](PHASE_F_PRE_IMPLEMENTATION_AMENDMENT_PLAN.md).
**This is F-0. Docs only — zero production code, zero tests.** Phase F's
own code (F-1 … F-10) unblocks the instant this section lands; none of it
is written here.

**Review basis, common to all seven ADs below, stated once rather than
repeated verbatim seven times.** `docs/PHASE_F_ARCHITECTURE_ACCEPTANCE.md`
is a **Level 2 AI-assisted adversarial architecture review**
(`RESEARCH_GOVERNANCE_STANDARD.md` §4): a separate pass over the material
with every load-bearing claim re-derived from the repository rather than
read out of the Proposal or the Resolution, but **not organizationally
independent under any definition §4 recognizes** — same model family and
vendor, no incentive separation, no accountable persistent reviewer
identity. It is amended by `docs/PHASE_F_ACCEPTANCE_CONDITIONS.md`
(F-C1 … F-C4) at the reviewing architect's own authority, and continued —
at the same Level 2 — by `docs/PHASE_F_IMPLEMENTATION_READINESS_REVIEW.md`
(R-16 … R-23), whose disposition
`docs/PHASE_F_PRE_IMPLEMENTATION_AMENDMENT_PLAN.md` records. **Level 3
review is unavailable on this platform** (Standard §4) and has never been
performed here. None of these five documents, and no AD below, may ever
be cited as "the independent architecture review."

**Census dating.** Every repository census below is re-derived and dated
to **HEAD `74e1693`** — the commit immediately preceding this one, and
the last commit before F-0's own text was written — superseding every
earlier dating in the Proposal (`58908fe`), the Resolution (`58908fe`),
and the Acceptance Review (`befa486`). No code under `core/`, `adapters/`,
or `tools/` changed between `58908fe` and `74e1693` in any way this AD's
censuses depend on; the module counts, export surfaces, and import facts
recorded here were independently re-verified against `74e1693`, not
carried forward.

### AD-061: Phase F — `ResearchRunner` is an orchestrator with no decision authority (accepted 2026-07-24)

**Review basis.** As stated above this section; Level 2, Level 3
unavailable, never cited as independent.

**Decision.** `core/research/execution/research_runner.py`'s
`ResearchRunner` executes one candidate phase transition for one cycle
and holds no decision authority of its own. It reads the clock once and
freezes that instant for the run; asks `ValidationRegistry` which gates
the target phase requires; runs the injected `Experiment` and receives a
`MeasurementBundle`; assembles a `GateContext` from the bundle plus the
operator-supplied frozen criteria and archives the bundle; runs
`GateRunner.run_sequence()` and archives the resulting `GateRunRecord` —
**before** any governance call; and invokes the injected
`TransitionComposer` exactly once. Every governance decision —
completeness, crash rejection, bracket validity, freeze projection,
aggregation, legality, authorization, anchoring, chain append — remains
inside `core.research.lifecycle.compose_transition()`, reached through
one call with the arguments it already accepts. `ResearchRunner` never
inspects a gate's status and never branches on outcome except to catch a
declared refusal; holds no state between calls; and never invents a
value — every string, threshold, path, hash, and timestamp comes from a
caller, from an artifact, or does not exist. The one string it composes
is an archive filename, from the frozen instant and a fixed template.

**The persisted measurement artifact carries a closed field set,
including a code revision reference and a provenance reference (F-C2).**
The `measurements_<timestamp>.jsonl` artifact `ArchiveWriter` writes is,
at minimum: `experiment_name`, the frozen `as_of`, `parameters`,
`measurements`, `evidence_refs`, `dataset_refs`, `provenance_ref`, and a
**code revision reference**. The set is closed and pinned by test at F-1;
adding a field fails a test and forces a new AD rather than a commit.
`parameters` is serialized alongside the measurements it produced — the
field exists, per `ExperimentSpec`, so an operator can pin a run's inputs,
and an artifact omitting it would leave that purpose unmet by the design
that declares it. Persisting the code revision and provenance/environment
references is **evidence retention**, governed by AD-064's `retention ≠
reproducibility` terminology: it does not assert the run can be
re-executed, does not bind Phase F to `core.governance.reproduction_runner`,
and creates no reproducibility contract. Where any identity element is
unavailable, it is persisted as an explicit absence — `None` or empty —
never omitted, never inferred, and never derived by the runner itself (no
`git rev-parse` inside `ResearchRunner`, no environment sniffing, no
inference from the archive path). The caller supplies identity, or the
record says it was not supplied.

**The gate evidence-ref propagation contract (F-C3).** The one ref
`ResearchRunner` mints — the measurement artifact's own path, appended to
`GateContext.evidence_refs` after `bundle.evidence_refs` — reaches
`DecisionRecord.evidence_refs` **only** through the required gates' own
`GateResult.evidence_refs`; `compose_transition()` builds the record's
refs from the admitted gates' own results, not from the context directly
(`core/research/lifecycle.py:384-388`). A gate admitted to a Phase F
sequence **is required to propagate `context.evidence_refs`** into its
own result. Both shipped gate adapters do this today
(`core/validation/gates/economic_rationale_adapter.py:49`,
`core/validation/gates/signal_independence_adapter.py:44`), but the
`Gate` Protocol is structural and does not require it, and Phase F cannot
make it require it — `Gate` lives in frozen Validation and AD-063
forbids Phase F holding authority there. `ResearchRunner` cannot verify
the propagation without reaching into adapter internals, for the same
reason it cannot verify that a gate's private measurement key is present
in the bundle — a disclosed, unmitigated limitation, not a mechanism.
The accountable holder of this contract is the
human act of registering a gate to a phase (AD-066); its
non-detectability is disclosed under the same discipline as AD-067's
amendment triggers.

**An empty gate list is legal and reachable, not an oversight (R-5).**
`ValidationRegistry.register_phase_gates(phase, [])` is legal — no
non-empty check exists at `core/validation/validation_registry.py:32`. A
registered-but-empty phase runs zero gates, archives both the measurement
and the run-record artifacts, and is refused at composition by
`EmptyGateSequence` from `aggregate_sequence_status`. Phase F adds no
second non-empty check at the registry, the runner, or
`build_gate_context` — the refusal already exists at the correct
altitude, and a duplicated check upstream could drift from the one that
governs.

**The injected clock must be timezone-aware (R-7).** `FixedClock` raises
`ValueError` on a naive `datetime` (`core/shared/clock.py:19`). A naive
instant is refused at step 1, before the experiment runs, rather than
discovered later after a wasted execution.

**No dependency on `core.store` is acquired by Phase F's own modules; it
is not inherited by an `Experiment` (R-14, C-5).** The full transitive
first-party import closure of everything Phase F reaches —
`core.research.lifecycle`, `core.validation.gate_runner`/
`validation_registry`, `core.governance.canonical_jsonl`/
`decision_recorder`/`freeze_verifier`, `core.shared.clock`/
`lifecycle_phase` — contains no `core.store` module, consistent with
`ALLOWED_DEPENDENCIES["research"] == {"data", "statistics", "governance",
"validation"}` (`tools/check_import_boundaries.py:176`, re-verified at
HEAD `74e1693`), which carries no `store` grant. This is a property of
**Phase F's own modules**, and must be recorded as exactly that — never
as a property an `Experiment` implementation inherits: a future
`Experiment` written under `core/research/` that reads the database
acquires that dependency, and a direct `core.store` import is a boundary
violation requiring its own recorded decision in the same commit, while
an import of the permanent `core.market_data.persistence.{database,migrations}`
shims (AD-069) is `research → data`, already granted, and reaches
`core.store` invisibly to the direct-import checker. That is inherent to
the mechanism, not a defect in Phase F, and no dependency grant is added
or altered by this AD.

**No ETF `Experiment` implementation that reads ETF data may live under
`core/research/` (R-16).** `core.analytics` is the `etf` domain
(`tools/check_import_boundaries.py:109`, `DOMAIN_OF_TOPLEVEL`);
`ALLOWED_DEPENDENCIES["research"]` holds no `etf` grant (`:176`); and
AD-068 decision 2 makes that grant **unavailable rather than merely
absent** — no domain may depend on `etf`, by construction, because an
asset class is a plug-in above the platform. AD-068 decision 3 closes the
remaining route: `ETF_SYMBOLS_BY_MODULE` attributes `ETFId`, `ETF`, and
the `insert_etf` / `get_etf` / `get_etf_by_ticker` repository functions to
the `etf` domain **by the name bound, not by the module that hosts it**,
so reaching ETF data through the *granted* `research → data` edge is a
violation too. An ETF `Experiment` therefore lives **outside `core/`**.
No grant is added by this AD, no file is moved, and no checker changes;
this is a structural consequence of AD-068, recorded here because it is
where a future author would otherwise discover it the hard way.

**§8 non-claims.** Phase F does not claim: that an archived Phase F run
is reproducible — nothing requires a provenance or code-revision
reference to be supplied, and nothing validates one that is; that a
`DecisionRecord` cites the measurement artifact — it does so only if the
phase's required gates propagate `context.evidence_refs`, which no
mechanism requires; that the single-writer assumption is enforced, or
that a lost update is detectable (A-9, unchanged); that Phase F's own
no-`core.store` property is inherited by any future `Experiment`.

---

### AD-062: Archive write authority — a second writer of a different artifact class, never a second writer of any artifact (accepted 2026-07-24)

**Review basis.** As stated above this section; Level 2, Level 3
unavailable, never cited as independent.

**Decision.** `ArchiveWriter` (`core/research/execution/archive_writer.py`)
is a second writer *of a different artifact class* —
`experiment_results/measurements_*.jsonl` and
`experiment_results/gate_run_*.jsonl` — never a second writer of any
artifact `DecisionRecorder` already owns. It can never name
`transition_records.jsonl`, `decision_log.md`, or `archive_manifest.json`,
checked by name and by the fact that it writes only inside
`<archive_root>/<project_id>/experiment_results/`. This extends A-9
R-3.1's single-writer-per-artifact rule **by analogy, not by amendment** —
this AD may not be cited as reopening that rule.

**`ArchiveWriter` remains domain-blind (F-C2).** It takes a
`Mapping[str, Any]` payload and a filename; it knows nothing about gates,
measurements, phases, or research. AD-061's closed measurement-artifact
field set does not widen this: serialization of the bundle belongs beside
the bundle, in `core/research/execution/`, never inside `ArchiveWriter`
itself.

**Preconditions, checked in this order, each a refusal (R-6):**

0. `filename` is a single path component — no separator, no `..`, no
   absolute path, no drive letter — refused, never normalized. This is
   precondition **0**, not a prohibition listed elsewhere: precondition
   3's guarantee is a statement about the target path's *immediate
   parent*, and is void unless this check has already established that
   the parent is `experiment_results/`.
1. `<archive_root>/<project_id>/` exists — never created. A cycle
   directory's existence is a precondition of evidence, never a
   consequence of writing it.
2. `archive_manifest.json` exists in it, and `manifest.project_id ==
   directory name == project_id`, byte-identical — a deliberately
   duplicated guard, not duplicated state: importing `DecisionRecorder`'s
   private check would put a Governance import into `ArchiveWriter` and
   violate AD-063's boundary for no benefit.
3. `experiment_results/` exists — never created.
4. The target file does not exist.

**Collision is a refusal, never a suffix, and is reachable by automation
(R-15).** If the target path exists, `ArchiveWriter` raises — it never
appends `_2`, overwrites, or increments, mirroring `write_manifest()`'s
existing `ManifestAlreadyExistsError` precedent. Filenames are dated to
the second; two runs of one project inside one second refuse. This was
previously unreachable at human speed and is reachable by an automated
caller, including F-10 and any future loop. A collision at the
**run-record** write (step 7, after the experiment and the gates have
already run) leaves an orphan `experiment_results/` measurement artifact
with no chain record — the same disclosed orphan-retention outcome an
archive-write failure produces, reached by a new route. Phase F adds no
suffixing, no retry, and no sub-second timestamp — each would trade an
observed property for an invented one.

**Atomicity wording is fixed, per A-9 C-6.** If the implementation writes
via temp-file-plus-`os.replace`, its docstring and test names say
**"atomic replacement"** — never "atomic append", never
"concurrency-safe". Temp-plus-replace makes the *replacement* atomic and
the read-check-write **not** atomic, and does nothing about
last-writer-wins.

**Disclosed reduction in standing enforcement (R-2).** The sole
`TransitionComposer` implementation is the single most
governance-sensitive module Phase F adds, and its own coverage is F-9's
AST test alone — narrower than `tools/check_import_boundaries.py`, which
does not scan `adapters/`. `ArchiveWriter`'s own permitted
`core.governance.canonical_jsonl` import (AD-063 enumeration (b)) is the
only Governance-adjacent surface this module carries, and it is
**asserted, not merely tolerated**, as not an authority crossing.

**Disclosed residual: automating execution does not create the
single-writer risk, it makes it easier to reach by accident.** The
unenforced single-writer assumption (A-9 R-2) is unchanged in strength by
Phase F; a runner that executes transitions faster than a human could
does not change whether the assumption is true, only how easily it is
violated without anyone noticing. Phase F adds no lock, no
writer-identity field, no repair path, no retry, and no orphan cleanup.

---

### AD-063: Composition-boundary preservation — no Phase F module holds Decision Chain authority (accepted 2026-07-24)

**Review basis.** As stated above this section; Level 2, Level 3
unavailable, never cited as independent.

**Decision.** This AD governs **Decision Chain authority only** — who may
bind a `GateRunRecord` to a `DecisionRecord` and who may append to
`transition_records.jsonl` — never import *direction* at package
granularity, which `tools/check_import_boundaries.py` already governs
over the §5 domain table. A rule written in package paths cannot answer
the authority question; **package boundaries are not authority
boundaries**. The rule is two literal enumerations over declared
surfaces:

> **(a)** No Phase F module names any symbol exported by
> `core.governance.decision_recorder`. The containment is
> **module-scoped over that module's entire export surface** — every
> public name it exports, whatever their number, present and future —
> never a recital of selected names. A symbol added to `decision_recorder`
> tomorrow is inside the rule the day it is added, with no edit to (a).
>
> **(b)** The only `core.governance` module a Phase F module may import is
> `core.governance.canonical_jsonl`. `archive_writer.py` does, under
> AD-062, and that import is **not** an authority crossing:
> `canonical_jsonl` imports nothing from this repository, holds no path,
> reads no chain, and names no record type.

Pinned by one new AST test, scoped by name to `core/research/execution/`
and `adapters/research/` (F-9). No classifier, no registry, no runtime
policy check — the enumerations are the only mechanism, and building
anything beyond them is the authority framework the Proposal §7.1
forbids.

**These enumerations are exhaustive only over their declared surfaces,
never over authority.** Enumeration (a) is exhaustive over
`decision_recorder`'s export surface; (b) is exhaustive over
`core.governance`'s module surface as reached by direct module-path
import. Anything holding Decision Chain authority without appearing on
one of those two declared surfaces is outside both enumerations and
outside what F-9's AST test can see; a passing test says nothing about
it. Authority reachability can change without either enumeration
changing — through relocation, re-export, or a new access path — and
AD-067's amendment triggers name the occasions on which this must be
re-derived.

**Current repository census, re-derived and dated to HEAD `74e1693`,
superseding every earlier dating (C-4):**

- `core/governance/` holds **thirteen** modules besides `__init__.py`:
  `calendar_definitions`, `canonical_jsonl`, `dataset_manifest`,
  `dataset_snapshots`, `decision_recorder`, `freeze_verifier`,
  `identity_verification`, `independence_linter`, `network_guard`,
  `pinned_worktree`, `reconstruction_loader`, `reproduction_record`,
  `reproduction_runner`. Exactly **one**, `decision_recorder.py`, can
  write `transition_records.jsonl`.
- `decision_recorder` declares no `__all__`; its public module-level
  export surface is **fourteen names**: `TRANSITION_RECORDS_FILENAME`,
  `ARCHIVE_MANIFEST_FILENAME`, `MissingArchiveManifestError`,
  `ProjectIdentityMismatchError`, `ChainInvalidError`,
  `ChainPrefixMismatchError`, `AuthorizationRecord`, `GateOutcome`,
  `DecisionRecord`, `hash_record`, `read_chain`, `verify_chain_intact`,
  `verify_chain_anchored`, `DecisionRecorder`.
- `core/governance/__init__.py` re-exports nothing — prose only, no
  `import`, no `__all__`.
- `canonical_jsonl.py` imports nothing from this repository — `hashlib`,
  `json`, `pathlib.Path`, `typing.Any` only
  (`core/governance/canonical_jsonl.py:16-21`) — and exposes five
  module-level functions; it is already imported by frozen Validation
  (`core/validation/gate_runner.py:39`).
- No `core.research.execution` package and no `adapters/research`
  package exist yet at HEAD `74e1693`; F-9's AST test scope names them in
  advance of their creation.

This census is a **count at a commit**, not a structural invariant;
AD-067 discloses the four occasions on which it must be re-derived.

**`core/research/lifecycle.py`'s frozen composition boundary is
preserved, not reinterpreted.** It remains the only module in `core/`
naming both a Validation type and a `core.governance.decision_recorder`
symbol, and the only place a `GateRunRecord` is bound to a
`DecisionRecord` (AD-059). Phase F narrows the callers of
`compose_transition()` from "anyone" to exactly one **non-test** module,
pinned by a test that excludes `tests/` by a stated rule rather than an
incidental path filter.

**Phase F modules reach `core.governance` transitively, and this rule
does not hide that.** `Authorization` is defined at
`core/research/lifecycle.py:87`, inside the one module that imports
`decision_recorder` at module scope (`core/research/lifecycle.py:46`).
This rule prevents a Phase F module from **naming** any symbol
`decision_recorder` exports; it does not keep the Governance package out
of the process, and must never be cited as if it did.

---

### AD-064: Measurement and criterion have different producers, structurally (accepted 2026-07-24)

**Review basis.** As stated above this section; Level 2, Level 3
unavailable, never cited as independent.

**Decision.** `MeasurementBundle`'s field set is closed at five fields —
`experiment_name`, `measurements`, `evidence_refs`, `dataset_refs`,
`provenance_ref` — and the absences are the design: no `status`,
`verdict`, or `passed` (a measurer that could also conclude would
collapse measurement into judgment); no `threshold`, `criterion`, or
`direction` (the yardstick comes from the operator's frozen methodology,
never from the thing being measured); no `summary`, `notes`, or
`rationale` (AD-045's prohibition on narrative in a mechanical record is
not reopened at a new altitude). An `Experiment` cannot return a status,
threshold, criterion, verdict, or narrative — only measured values and
references to where they came from. An experiment crash produces **no
bundle and no artifact**; no partial measurement is ever constructed.

**Evidence retention is not a reproducibility contract (F-C1).** Phase F
genuinely delivers evidence retention: every run's raw measurement bundle
and raw `GateRunRecord` are archived, content-hashed, dated, before
anything is composed, and never deleted, overwritten, or repaired —
including for refused transitions. It does **not** deliver
reproducibility. The two terms are not interchangeable in any Phase F
document from this AD forward: *evidence retention* is the archive
property Phase F delivers; a *reproducibility contract* is a commitment
that a run can be re-executed to the same result. Phase F holds the first
and makes no instance of the second.

**`provenance_ref`'s absence semantics.** `MeasurementBundle.provenance_ref`
may be `None`, and `None` is recorded as `None` — never backfilled with
the archive path the runner just wrote, which would invent a
reproduction reference that does not exist. Its absence is an audit
finding, disclosed, never filled in.

**`reproduction_record_ref`'s absence semantics — the path and its
endpoint, stated in full.** `provenance_ref` flows, unchanged, through
`GateContext.measurement_provenance` → `GateRunRecord.measurement_provenance`
(`core/validation/gate_run_record.py:72`) →
`DecisionRecord.reproduction_record_ref`
(`core/research/lifecycle.py:389`, `run_record.measurement_provenance`),
which is `str | None`, defaulted to `None`
(`core/governance/decision_recorder.py:139,277`). **Nothing refuses a
`None`, and nothing checks that a non-`None` value resolves to
anything.** A fully compliant Phase F transition may therefore be
recorded — permanently, immutably, hash-chained — with no reproduction
path at all, and no mechanism in Phase F or below will say so at the time
it happens. This is a disclosure obligation, not a mechanism obligation:
a non-`None` guard would duplicate a rule that belongs in
`compose_transition()`, which is frozen, and Phase F adds none — not in
`ResearchRunner`, not in `ArchiveWriter`, not in `compose_transition()`
itself.

**No bridge to `core.governance.reproduction_runner` (R-11, R-18).**
Phase F builds no bridge between an `Experiment` implementation and
`core.governance.reproduction_runner.run_reproduction`. Phase F makes no
reproduction claim: `experiment_name` is a caller-chosen label, not an
identity, and nothing in Phase F asserts that code reproduced under
`reproduction_runner` is the same code that ran under `ResearchRunner`.
The two models remain structurally separate — neither references the
other, and Phase F is not authorized to connect them. This is
deliberately silent on *how*, or *whether*, an operator might later
achieve identity between the two: no adapter, no composition-root
inhabitant, no `run()`-entrypoint convention, and no placement decision
is stated here. Any such route is an implementation choice for a later
increment, made — if at all — when that increment is actually written;
it is not a claim this AD gets to make about code that does not yet
exist. A `ReproducibilityChecker` or any bridge object remains on the
Proposal §7.1 forbidden list; wiring `ResearchRunner` into
`reproduction_runner` remains deferred; and no `ReproductionRecord`
producer is authorized by this AD — writing the `(commit_hash,
dataset_content_hashes, result_report_hash)` triple for any real run is a
human act against the existing frozen dataclass, not a component.

**`experiment_name` is only a label, never an identity.**
`reproduction_runner.run_reproduction` reproduces a cycle by loading an
experiment **script by relative path out of a pinned worktree**, with a
commit pin and a hash. Phase F's `Experiment` is a **live object injected
by the caller**, fully constructed with whatever database handle and
configuration it needs — it has no path, no commit pin, and no hash. The
only identity that survives into the archive is `experiment_name: str`, a
caller-chosen string that nothing validates. Phase F archives what was
measured; absent an explicitly supplied code revision and provenance
reference (AD-061), it does not record what code measured it, and
`experiment_name` must never be read as answering that question.

**Dataset-reference non-claim (R-21).** `MeasurementBundle.dataset_refs`
is `tuple[str, ...]` of opaque references by accepted decision (AD-042).
Phase F does not validate that a `dataset_ref` identifies a dataset, and
nothing should: a runner-side resolver would be a duplicated rule at the
wrong altitude from wherever dataset identity is ever actually
established. Opaque refs are evidence retention; dataset identity, where
it exists, is a separate concern this AD does not resolve.

**Current census — the reproduction stack has itself never been run
against a real cycle (R-23), dated to HEAD `74e1693`.** The reproduction
model Phase F does not connect to — `reproduction_runner`,
`reconstruction_loader`, `dataset_snapshots`, `dataset_manifest`,
`identity_verification`, `pinned_worktree`, `network_guard` — is fully
built and tested against fixtures only. **No `dataset_manifest.json` and
no dataset snapshot for any real cycle exists in the repository**
(`find . -name dataset_manifest.json` returns nothing, re-verified at
HEAD `74e1693`) **at the commit at which this AD is accepted.** It is a
mechanism with no production instance. This prevents a later reader from
treating any future reproduction attempt as a reuse when it would be a
first.

---

### AD-065: The anchor receipt is a convenience transcription, not a machine-verified anchor (accepted 2026-07-24)

**Review basis.** As stated above this section; Level 2, Level 3
unavailable, never cited as independent.

**Decision.** `TransitionReceipt.record_hash` exists to be
**hand-copied** by the operator into `decision_log.md`, as the citation
the *next* transition's anchor is verified against. Emitting it is a
convenience transcription; it does **not** make the anchor
machine-verified, and must never be read as one.

- The machine never writes `decision_log.md` (INV-10). The operator
  copies the citation by hand, and its evidentiary value comes from being
  committed to a separate hand-authored artifact at a known time — not
  from who computed the hash.
- The receipt is never auto-carried into a subsequent `execute()` call.
  `expected_anchor` is always operator-supplied, read from
  `decision_log.md`, exactly as AD-050 A5-C9 requires. `ResearchRunner`
  holds no state between calls, so it cannot carry it, and this is why.
- Anchor lag is unchanged (A-5 R-6): the newest record is always
  unanchored. Phase F narrows that window not at all.

**`record_hash` is operator-recomputable, and that is what makes it a
transcription rather than a dependency (Q2).** The value is recomputable
by the operator from the appended row via `hash_record` — the same
function `decision_recorder.py` already exports. A receipt the operator
*could not* independently reproduce would be a claim about the chain that
only the machine could make; one they can reproduce is a transcription.
This is the whole of this AD's defensibility, stated explicitly rather
than left implicit.

---

### AD-066: Gate registration is a governance act, and two-registry agreement is unenforced (accepted 2026-07-24)

**Review basis.** As stated above this section; Level 2, Level 3
unavailable, never cited as independent.

**Decision.** There are **two** registries, and Phase F populates
neither. `ValidationRegistry` maps phase → ordered gate **names**, and
ships deliberately empty; `gates_for_phase` raises `KeyError` for any
unregistered phase (`core/validation/validation_registry.py:38`).
`GateRunner` holds its own name → `Gate` **instance** registry;
`run_sequence` resolves every required name against it in an atomic
preflight before any gate executes. `ResearchRunner` reads both
registries and populates neither. **Populating `ValidationRegistry` and
`GateRunner` for a real cycle is the human operator's act, at the
composition root, per cycle** — a governance act, not configuration,
because it decides what evidence a phase requires.

**Nothing checks that the two registries agree.** A required gate name
with no matching `Gate` instance surfaces as `run_sequence`'s atomic
preflight `KeyError`, before any gate executes — breakage, not a
governed refusal, and no partial evidence set is produced. Phase F ships
**no** registry-consistency check: such a check would have to name gates,
and Phase F is not authorized to determine what any phase requires.

**Registering a phase → gate assignment for a real cycle carries the same
standing as producing the repository's first real
`transition_records.jsonl`: it requires a `decision_log.md` entry and a
named human.** A fixture experiment's registration (F-10) is exempt only
because it registers gates in test fixture code, against a fixture phase;
Phase F's own completion must never be recorded as having determined what
any real phase requires.

**Gate registration carries the propagation attestation (F-C3).**
Registering a gate to a phase is already the governance act, with its own
`decision_log.md` entry and named human (above). That act now
additionally **asserts that the registered gate propagates
`context.evidence_refs`** into its own `GateResult` — the only route by
which the measurement-artifact reference AD-061 mints can ever reach a
`DecisionRecord`. This is where the propagation contract acquires an
accountable holder: the `Gate` Protocol itself cannot be made to require
the behavior (AD-063 forbids Phase F holding authority over frozen
Validation), and `ResearchRunner` cannot verify it mechanically, so the
attestation is what makes a silent breakage of the contract discoverable
— by the record of who registered the gate — rather than invisible.
Making propagation a `Gate` **Protocol** requirement is a
Validation-owned decision for a later increment; Phase F does not make it
and this AD does not authorize it.

---

### AD-067: Policy authority composition — package boundaries are not authority boundaries, and the authority enumeration is hand-maintained (accepted 2026-07-24)

**Review basis.** As stated above this section; Level 2, Level 3
unavailable, never cited as independent.

**Decision.** The repository holds **two different kinds of boundary**.
*Import-direction* boundaries are enforced by
`tools/check_import_boundaries.py` over the §5 domain table, at
**package** granularity, mechanically derived from a path. *Authority*
boundaries — who may bind a `GateRunRecord` to a `DecisionRecord`, who
may append to `transition_records.jsonl`, who may decide — are held by
**named symbols** and by **construction and call**, never by location.
`adapters/research/lifecycle_composer.py` (once it exists) holds Decision
Chain authority because it constructs `DecisionRecorder` and calls
`compose_transition()`, not because of where it sits — and it sits
outside `core/`, where the package checker does not reach. Conversely
`archive_writer.py` imports a `core.governance` module (`canonical_jsonl`,
AD-063 enumeration (b)) and holds **no** authority whatever.

**The disclosure proper.** AD-063's containment is **module-scoped over
`decision_recorder`'s export surface** — exhaustive **within** that
surface without maintenance, and **derived from nothing outside it**.
Enumeration (b) is an allow-list of one, so a *new* `core.governance`
module is excluded by default — the safe direction. But **neither
enumeration follows authority**: reachability can change through
relocation, re-export, or a new access path while both remain textually
correct. A chain-writing or chain-reading symbol defined outside
`core.governance.decision_recorder`, a `decision_recorder` symbol
re-exported under another path, or a `canonical_jsonl` that acquires a
chain path would each leave F-9's AST test **passing** with the boundary
unprotected and nothing to say so.

**The four amendment triggers, on each of which AD-063's enumerations and
this disclosure must be re-derived and amended before F-9's test is cited
as evidence of containment:**

1. **A new module is added under `core/governance/`.** Enumeration (b)
   excludes it by default — the safe direction — but the census below is
   stale from that commit, and if the new module carries chain authority,
   (a) does not reach it.
2. **A chain-authority symbol is relocated** out of
   `core.governance.decision_recorder` — anything that writes, reads,
   hashes, or verifies `transition_records.jsonl`. Enumeration (a) binds
   to the module, so relocation moves the symbol out of the rule while
   the rule's text is unchanged and the AST test still passes.
3. **Any `__init__.py` re-export appears** that makes a
   `decision_recorder` symbol reachable under a different path. At the
   commit this AD is dated to, `core/governance/__init__.py` re-exports
   nothing, which is the condition (a) is written against.
4. **`canonical_jsonl`'s access is widened** — it acquires a chain path,
   a chain-path constant, a default path, chain-awareness, or any
   repository import. Enumeration (b) permits it *because* it holds no
   path and imports nothing from this repository; widening it turns the
   one permitted import into an authority crossing while (b) still reads
   as correct.

**These are amendment obligations on the text of AD-063 and this AD,
discharged by a human reader.** Phase F ships nothing that detects them,
and this AD authorizes nothing that would: no watcher, no CI check, no
registry, no runtime policy framework. A trigger that fires unnoticed is
exactly the failure this AD discloses; naming the occasions narrows it
without closing it.

**Current census, re-derived and dated to HEAD `74e1693`, superseding
every earlier dating (C-4):** `core/governance/` holds **thirteen**
modules besides `__init__.py`, and exactly **one**, `decision_recorder.py`,
can write the chain; `core/governance/__init__.py` re-exports **nothing**
— prose only, no `import`, no `__all__`; `canonical_jsonl.py` imports
nothing from this repository, exposes five module-level functions, and is
already imported by the frozen Validation module
`core/validation/gate_runner.py:39`. This is a count at a commit, not a
structural invariant, and holds no claim about any later HEAD.

**No mechanism is authorized by this AD.** No authority registry, no
`core/governance/authority.py`, no classifier deriving which symbols
carry authority, no runtime policy check, no decorator or metadata
scheme. This AD confers authority on nothing, adds no code and no runtime
component, amends no accepted AD, and must never be cited as a policy
framework or as evidence that authority is mechanically governed.

---

### AD-072: Lifecycle Authorization Floors and Transition Authority Semantics (accepted 2026-07-25)

**Review basis.** Level 2 (AI-assisted adversarial review, conducted
across sequential drafting, refinement, and acceptance passes, each
re-verified against `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2,
`research_archive/reference_h4/transition_records.jsonl`, and this AD's
own citation set); Level 3 unavailable; never cited as independent
(Standard §4).

**Acceptance basis.** Drafted and accepted per
[`REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md`](REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md)
§10, remediation item **R-1** (closes G-1, D-1…D-4): *"an ADR: where the
Standard §2 phase → minimum-review-level table lives and what refuses a
transition that does not meet it."* This AD is that instrument.
Implementation — the mechanical refusal itself, in
`core/research/lifecycle.py` — is separate, future work, gated on this
acceptance but not performed by it.

**Numbering.** AD-070 and AD-071 are not consumed here. Per
`docs/PHASE_F_PRE_IMPLEMENTATION_AMENDMENT_PLAN.md` §8, those two numbers
remain the named (not formally reserved) candidates Track C's own commit
C0 may claim, "if still required," for Golden Run 001. This AD numbers
itself AD-072 to avoid any collision with that track's own numbering act,
intentionally leaving AD-070/071 unconsumed rather than claiming the
literal next-free number.

**Context.** `core/research/lifecycle.py`'s `Authorization` and
`core/governance/decision_recorder.py`'s `AuthorizationRecord` both hold,
as deliberate prior design, that `reviewer_level` is "recorded, never
adjudicated" — stored, never parsed, compared, or checked against a
hierarchy. `advance_phase()` therefore accepts `"Level 1 (self-review)"`
at any transition without objection, because nothing on the platform
holds the Standard §2 phase → minimum-review-level table. The Phase G
remediation decision (G-1, **High**) names this the direct structural
cause of `reference_h4`'s D-1 through D-4, and R-1 requires this
instrument, gating the next cycle's Phase 2 → Pre-validation transition.

A companion ambiguity (referred to in review as **E-6**) sits one layer
below G-1: even once a floor table exists, `authorization.reviewer_level`
on a `DecisionRecord` is not self-evidently *which* thing it asserts —
the level that authorized this transition record, or the highest level
any review reached anywhere during the phase's lifetime. `reference_h4`'s
D-1 shows why the difference is load-bearing: a genuine Level 2 review of
the freeze exists, but it was authored after Phase 6 Validation had
already run against that freeze. A floor check satisfied by a review
that arrived later than the transition it purports to authorize would
validate the exact ordering failure D-1 discloses, not catch it.

**Decision.** The platform adopts a mechanical lifecycle authorization
floor, held beside `advance_phase()` in `core/research/lifecycle.py` —
the module R-1 names as the natural site, since it already holds
transition-legality authority (`IllegalPhaseTransition`,
`UnauthorizedTransition`) and is the one non-test module permitted to
name `core.governance.decision_recorder` symbols (AD-063 enumeration
(a)). The floor's scope is deliberately narrow:

> **The lifecycle engine enforces unconditional approval floors only.
> Conditional governance requirements dependent on external facts remain
> human governance obligations.**

An "unconditional floor" is a minimum `reviewer_level` for a given
transition-authorization event, fixed by the Standard, requiring no
external fact to evaluate. The engine performs mechanical evaluation of
the recorded reviewer level against that floor — implementation may
normalize the recorded string into a comparable representation, but the
evaluation reaches no further than the value already on the record. The
engine does not evaluate reviewer identity, reviewer availability, any
authority hierarchy among reviewers, or the substance of what was
reviewed.

**Mechanical enforcement boundary.**

| Phase / event | Floor | Kind | Mechanically enforced? |
|---|---|---|---|
| 2 — Research Proposal, artifact creation | Level 1 minimum | Artifact-creation floor, not a transition | No — out of scope for this AD. No `advance_phase()` call corresponds to authoring the proposal. |
| 2 — Research Proposal → Pre-validation | Level 2 required | Transition-authorization floor | Yes — Level 2 |
| 3 — Pre-validation → Methodology Freeze | Level 2 minimum, per individual gate | Transition-authorization floor | Yes — Level 2 |
| | Level 3 where available, before platform implementation effort | Conditional clause | No — human governance obligation |
| 4 — Methodology Freeze → Implementation | Level 2 minimum | Transition-authorization floor | Yes — Level 2 |
| 5 — Implementation → Validation | Level 1 minimum (Standard code review) | Transition-authorization floor | Yes — Level 1 |
| | Level 2 conformance check | Recommendation only | No — not mechanically enforced |
| 6 — Validation → Decision | Level 2 minimum | Transition-authorization floor | Yes — Level 2 |
| | Level 3 before capital allocation | Conditional clause | No — human governance obligation |
| 7 — Decision → Archive | Level 2 minimum | Transition-authorization floor | Yes — Level 2 |
| | Level 3 target maturity; Level 2 exception where genuinely unavailable | Conditional clause | No — availability assessment and disclosure remain human governance obligations |
| 8 — Archive, completeness check | Level 1 sufficient | In-phase completeness check, not a transition (Archive is terminal — no outbound transition record exists) | No — out of scope for this AD, same structural reason as Phase 2's artifact-creation floor |

Every enforced row above is a transition-authorization floor, attached to
the specific `DecisionRecord` whose `from_phase`/`to_phase` pair names
that transition. Several phases additionally carry a second component of
a different kind — an artifact-creation floor (Phase 2), a recommendation
(Phase 5), a conditional escalation (Phases 3, 6, 7), or an in-phase
completeness check with no corresponding transition (Phase 8) — and each
is marked accordingly rather than folded into the enforced floor.

**Policy boundary.** The lifecycle floor table is transition policy only.
It is not a reviewer authority registry, not a permissions system, not a
policy engine, and not a replacement for human governance judgement — it
is a deterministic, per-transition floor: one fixed minimum value per
transition-authorization event, evaluated mechanically against the
recorded reviewer level, consulted at exactly one point
(`advance_phase()`), and authorizing nothing beyond refusing a transition
whose floor is unmet.

**Authorization semantics.** `authorization.reviewer_level` means: the
reviewer authority level that authorized *this specific transition
record* — the value the human recorded, at the time they recorded it, as
the basis for making *this* transition. It is evaluated against the floor
table at the moment `advance_phase()` composes the record, using only
what that record itself carries.

It does not mean: the highest reviewer level any review reached anywhere
during the phase's lifetime. A later, higher-level review — however
genuine and thorough — does not retroactively change what a prior
transition record asserted about itself. The Standard's ordering
requirement exists to guarantee that the confirming reviewer had not yet
seen the outcome; that property is a fact about *when* the review
happened relative to the transition, not merely *whether* a sufficiently
high review exists somewhere in the archive. Collapsing the two concepts
would convert the floor check into a mechanism that actively launders the
exact ordering failure it exists to catch.

A future evidence field, named but not implemented here:
`phase_evidence.highest_review_level_attained`. This would record,
separately from any authorization, the highest review level a phase's
evidence ever received — including reviews that arrived late. It would be
disclosure data, read by no mechanical floor check, never substitutable
for `authorization.reviewer_level` at any transition. This AD does not
define its schema, producer, or storage location.

**Reference H4 compliance implications.** No rewriting of history.
`research_archive/reference_h4/` remains immutable per the Phase G
decision's §8 determination, and nothing here revisits
`decision_record.md`'s **PASS**.

`reference_h4` contains substantive Level 2 review evidence —
`reviewer_reports/2026-07-25_level2_adversarial_review.md`, a genuine
bit-for-bit re-derivation, and the Level 2 arithmetic check at Validation.
That evidence remains visible and is not disputed by what follows.

The lifecycle transition **authorization records** that would be
evaluated under AD-072 are `seq 2` (Research Proposal → Pre-validation),
`seq 3` (Pre-validation → Methodology Freeze), `seq 4` (Methodology
Freeze → Implementation), `seq 6` (Validation → Decision), and `seq 7`
(Decision → Archive) — all five carry `authorization.reviewer_level =
"Level 1 (self-review)"`. Under AD-072's floors — Phase 2's transition
floor Level 2, Phase 3 Level 2, Phase 4 Level 2, Phase 6 Level 2, and
Phase 7 Level 2 — none of these five would satisfy the required floor.
`advance_phase()` would have refused all five at composition, including
the very first Pre-validation entry (`seq 2`), which matches D-2's own
finding that this transition was taken without the Level 2 the Standard
requires. `seq 5` (Implementation → Validation) is not among them: its
recorded Level 1 satisfies Phase 5's Level 1 minimum.

This is not a defect to paper over. It is exactly the discrepancy R-1
exists to surface: a real governance cycle produced real evidence that a
real mechanical floor would have caught what disclosure alone did not,
until this decision was written after the fact. That discrepancy stays
visible in this register and in the Phase G decision's own D-1…D-4, not
resolved by this AD, only made mechanically preventable for the next
cycle.

**Compatibility with existing decisions.**

*AD-063.* Governs Decision Chain *authority* — who may name
`decision_recorder` symbols, who may bind a `GateRunRecord` to a
`DecisionRecord` — at module/symbol granularity, and states that "package
boundaries are not authority boundaries." AD-072 adds no new caller and no
new authority crossing: the floor check runs inside
`core/research/lifecycle.py`, the one non-test module AD-063 already
permits to hold this reach. Enumerations (a) and (b) are untouched.

*AD-065.* Concerns `TransitionReceipt.record_hash` and the
chain-anchoring citation — a distinct precondition from authorization
level. AD-072 does not touch anchoring and introduces no dependency
between the two checks.

*AD-067.* Forbids "no authority registry, no
`core/governance/authority.py`, no classifier deriving which symbols
carry authority, no runtime policy check" for *who may call or construct*
chain-writing code. AD-072's floor is not that: it is a data-validation
check over the value already present in an existing recorded field, of
the same kind the platform already accepts in `ValidationRegistry`
(AD-066's "phase → ordered gate names" registry) — a sibling of that
accepted pattern, not a new authority-registry concept, restated
explicitly as this AD's own policy-boundary statement above.

*AD-050 A5-C9.* Decomposes "verified intact and anchored" into a
mechanical half (hash chain, contiguity, anchoring citation) and a human
half (the substance of what was reviewed). AD-072 preserves that
discipline by construction: its floor check is a mechanical evaluation of
the recorded reviewer-level value against a fixed table — it verifies
that a sufficient level was recorded, never that a review was
substantively adequate, and never anything about reviewer identity,
availability, or hierarchy beyond the recorded value itself. It adds a
new, independent precondition to `advance_phase()` alongside A5-C9's
chain-integrity precondition; it does not modify A5-C9's own split.

No existing invariant is weakened by this AD.

**Consequences.** `advance_phase()` gains a new refusal ground;
`UnauthorizedTransition` is raised for a floor violation in addition to
its existing grounds — implementation, not performed by this AD. The
`Authorization` / `AuthorizationRecord` docstrings ("recorded, never
adjudicated") become stale on acceptance and must be updated at
implementation time. The next research cycle's Phase 2 → Pre-validation
transition is gated on this ADR's acceptance and implementation, per
R-1's stated blocking condition. `phase_evidence.highest_review_level_attained`
remains named-but-unimplemented; a future ADR must define its schema, or
explicitly decline to, before it is cited as available.

**Rejected alternatives.**

- *Enforce every Standard §2 clause mechanically, including "where
  available" language.* Rejected: the engine cannot observe reviewer
  availability; mechanizing that judgment would fabricate an answer
  rather than enforce a requirement.
- *Define `authorization.reviewer_level` as the highest level attained
  anywhere in the phase.* Rejected: demonstrated to retroactively
  validate `reference_h4`'s own ordering failure (D-1).
- *Implement `phase_evidence.highest_review_level_attained` now,
  alongside the floor.* Rejected: out of scope by explicit constraint,
  and premature — naming it without designing it risks the "named in
  three places, implemented in none" failure mode G-3 already documents
  for `ArchiveVerifier`.
- *Locate the floor table in `core/governance/decision_recorder.py`
  instead of `core/research/lifecycle.py`.* Rejected:
  `decision_recorder` explicitly disclaims adjudicating `reviewer_level`
  as a matter of scope discipline (AD-063's authority split); `lifecycle.py`
  already owns transition legality.

**Adversarial self-review.**

*What assumption could still be wrong?* That the Standard's per-phase
clauses decompose cleanly into an enforced transition floor plus a
separate non-enforced component (artifact floor, recommendation, or
conditional escalation) has now been checked against the Standard's
actual text for every phase in this table, not assumed by analogy from
Phase 2 alone. The residual risk is narrower: a future Standard revision
could restructure a phase's approval state in a way this table does not
anticipate, and nothing here detects that drift automatically.

*What future implementation mistake could this ADR accidentally allow?*
Reading "unconditional floor" too liberally — e.g., an implementer
deciding that Phase 6's or Phase 7's "Level 3 before/at" language is
"basically unconditional most of the time" and quietly mechanizing it
anyway. That would smuggle a conditional, fact-dependent judgment into
the engine through the back door this AD explicitly closes.

*Does this ADR create any hidden authority registry?* No, by construction
and by comparison to AD-066's already-accepted `ValidationRegistry`
pattern — it is a value-floor table over an already-recorded field, never
a registry of who may call or construct chain-writing code, which is the
one thing AD-067 reserves and this AD does not touch.

---

### AD-073: Archive Integrity Verification Architecture (accepted 2026-07-25)

**Review basis.** Level 2 (AI-assisted adversarial review, conducted
across sequential drafting, refinement, and acceptance passes, each
re-verified against `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 Phase 8 and
§5, `docs/PLATFORM_ARCHITECTURE_V1.md` §4.4,
`docs/RESEARCH_ARCHIVE_MANIFEST.md`,
`docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md` §§4/9/10,
`docs/POST_RELEASE_V0_18_0_GOVERNANCE_BASELINE_REVIEW.md` §§3/6/7, and
this AD's own citation set); Level 3 unavailable; never cited as
independent (Standard §4).

**Acceptance basis.** Drafted and accepted against Phase G remediation
item **R-3** (closes G-3, D-8): *"Implement `ArchiveVerifier` per
`PLATFORM_ARCHITECTURE_V1.md` §4.4, **or** record its deferral as a
time-boxed §8 exception. Named-but-absent is not an allowed third
option."* R-3 names an implementation, not a design, and the design it
presupposes does not exist anywhere in this repository: §4.4 gives
`ArchiveVerifier` a one-line protocol sketch, and the proposed Archive
Seal — reviewed in architecture but never recorded as a decision —
raises the prior question of whether it *is* `ArchiveVerifier` or sits
underneath it. This AD answers that prior question and nothing beyond
it. Implementation is separate, future work, gated on this acceptance
but not performed by it.

**This AD does not close R-3, and does not close R-4.** R-3 closes on
implementation (or on a recorded §8 deferral); R-4 closes on a
re-protection mechanism this AD deliberately does not design. What this
AD removes is the architectural ambiguity that blocked both.

**Numbering.** AD-070 and AD-071 remain unconsumed, for the reason
AD-072 records: per `docs/PHASE_F_PRE_IMPLEMENTATION_AMENDMENT_PLAN.md`
§8 they are the named (not formally reserved) candidates Track C's own
commit C0 may claim for Golden Run 001. This AD takes AD-073, the next
number after AD-072, and claims neither.

**Correction basis.** A second adversarial pass, conducted the same day
against this AD's own text (no new source document), found five
contradictions internal to the acceptance below and none in the
architecture it describes:

- **F-1** — the Archive Seal's coverage and Decision part 8's
  one-authoritative-record rule named only one pre-existing hash
  mechanism (`protected_file_hashes.json`) when a second already exists
  and already covers archived bytes: `dataset_manifest.json`'s per-entry
  `content_hash`, which already names every file under `dataset_hashes/`
  by `snapshot_path` (confirmed at
  `research_archive/reference_h4/dataset_manifest.json`) and is
  `DatasetIntegrityChecker`'s input contract under this AD's own
  Non-goals item 5.
- **F-2** — the freeze-claim bullet asserted "no archive artifact defines
  that structured claim today." False: `core/governance/
  decision_recorder.py` already writes `freeze_commit_ref` into every
  record of `transition_records.jsonl`, already present in every v1
  archive (confirmed at `research_archive/reference_h4/
  transition_records.jsonl`). No selection rule was given for which
  record's claim governs.
- **F-3** — the applicability bullet's prose said "for exactly those
  three [named legacy archives]," but **AC-14**, the criterion an
  implementer actually builds to, said "no `archive_manifest.json`
  present" unqualified — a rule under which any future archive that
  simply failed to receive a manifest would be silently exempted as
  legacy rather than reported incomplete.
- **F-4** — applicability was keyed only to `lifecycle_version` (`"v1"`
  vs. `"legacy"` vs. absent), with no signal for whether a `"v1"`
  archive's cycle has actually *closed*. `RESEARCH_ARCHIVE_MANIFEST.md`
  writes the manifest once, at archive-directory scaffolding, which
  precedes Phase 8 by construction — so an open v1 archive and a closed
  one were indistinguishable to the rule as written, and Problem
  statement P1/P2's own premise ("a closed cycle's evidence package") was
  silently unenforced.
- **F-5** — the Architecture overview correctly states that the Archive
  Seal and `FreezeVerifier` verify different subjects (archived bytes vs.
  live repository state), but never states what a reader should do when
  both branches report on paths that name the same underlying file. No
  composition rule existed for that case.

None of these findings changes what `ArchiveVerifier`, the Archive Seal,
or `FreezeVerifier` *are*, what they may write, or how they compose
(Decision parts 1–7 are unaffected). Each is a boundary, source, or scope
that this AD's original text left implicit, contradictory, or
unqualified. The fixes below tighten existing language; none introduces
a component, and none adds a manifest schema field — both prior gaps
(F-1, F-2) turned out to already have a governing mechanism on disk that
the original text overlooked.

---

**Status.** **Accepted, 2026-07-25.** Documentation only: no code, test,
fixture, archive, or architecture document is changed by this
acceptance, and no implementation exists at the moment it is recorded.
`ArchiveVerifier` remains unimplemented; the Archive Seal remains
unimplemented.

Acceptance carries one forward condition, taken directly from R-3's own
terms: this AD is the *design* half of R-3, and R-3's gating condition
(*before the next cycle's Phase 8*) is unchanged by it. If implementation
has not landed by that point, R-3's second branch — a time-boxed §8
exception recording the deferral — becomes mandatory. Accepting a design
is not a third option any more than naming a component was; this AD's own
existence must not be cited as partial closure of R-3.

**Corrected, 2026-07-25** (same day), against the Correction basis above
(F-1…F-5). The correction is documentation-only, like the acceptance it
amends: no code, test, fixture, or archive changes, and R-3's gating
condition and forward-condition wording are untouched by it.

**Amended, 2026-07-26** (AD-074 acceptance-with-conditions remediation).
`docs/AD_074_ARCHIVE_SEAL_DESIGN_REVIEW.md` was reviewed the same day and
received **Accept with conditions**; four of those conditions are narrow
amendments to this AD's own text, applied inline below and listed here so
that "amended" is never a claim this document makes about itself without
saying where. Like the correction above, this amendment is
documentation-only — no code, test, fixture, or archive changes — and
R-3's and R-4's gating conditions are untouched by it.

1. **Responsibilities — the Archive Seal's git-access bar was over-broad
   relative to its own stated rationale.** "does not … verify any commit,
   resolve any git reference, or observe repository state" is replaced
   below with a bar scoped to *freeze-claim verification* and
   *time-varying repository state*, not to git access as such. The
   Archive Seal may now read git objects at a commit fixed at archive
   close — a read, not a commit verification — while `FreezeVerifier`
   remains the only component that verifies a freeze claim, a live,
   time-varying fact. Neither component's responsibility grows into the
   other's: the Archive Seal still never calls `verify_freeze()`, and
   `FreezeVerifier` still never reads `research_archive/`.
2. **Decision part 5 — "the Archive Seal never verifies a commit" is
   replaced with the same narrower bar.** `AD_074_ARCHIVE_SEAL_DESIGN_REVIEW.md`
   §3 S-5 shows the old sentence was never load-bearing against a
   *fixed-commit, archive-local* comparison — only against a *live,
   time-varying* one, which is what this AD's own rationale (the
   Architecture overview's "third row") actually argues against.
3. **Status vocabulary and the Architecture overview table —
   "sealed manifest" is replaced with "the sealing commit tree identified
   by an Archive Seal Register record."** AD-074 §5 resolves what this AD
   left as Non-goals item 1: the Seal's expected value is not an authored
   manifest but a git tree, named by one record in the Archive Seal
   Register (AD-074 §5.5). Every other use of "sealed manifest" in this
   AD's text below — Non-goals item 1, Migration items 2 and 5, Future
   work's R-4 line, the Worked example, and AC-11 — describes the
   undecided state *at this AD's original 2026-07-25 acceptance* and is
   superseded by AD-074, not rewritten here; a reader encountering
   "sealed manifest" elsewhere in this AD should read it as historical.
4. **A8-C1 — the Archive Seal Register is the first allowed
   platform-level governance machine artifact.** Recorded at **A8-C12**,
   in the A-8 section below, not here, because A8-C1 is owned by that
   section's transcription discipline, not by this AD. This AD's own
   Decision and Non-goals sections are otherwise unaffected: seal
   issuance's format is now decided by AD-074, but *where* AD-073 itself
   grants write authority (Decision part 7, AD-062) is unchanged — AD-074
   grants none beyond what Non-goals item 1 already contemplated.
5. **Nothing else in this AD's text changes.** Decision parts 1, 2, 3, 4,
   6, 7, 8 stand as corrected 2026-07-25; the aggregation rule, AC-1,
   AC-2, and AC-4…AC-17 stand; AC-11 is satisfied more strongly than
   before (`AD_074_ARCHIVE_SEAL_DESIGN_REVIEW.md` §2 O-3). This
   enumeration — items 1–4 above — is exhaustive of this amendment; it is
   not a general loosening, and no future reader may cite it to justify
   an edit beyond the four sentences it actually changes.
6. **This amendment is recorded here, in the owning decision document,
   not only in AD-074's own text.** AD-074 §7 cross-references this block
   rather than restating it as the authority; where the two documents'
   prose differs, this block, being the amendment to the accepted AD,
   governs.

**Further amended, 2026-07-26** (AD-074 Increment 2 governance hardening
pass — the second adversarial audit of the shipped
`core/governance/archive_seal.py`, whose remediation *is* a code change,
unlike the two documentation-only passes above). One further amendment to
this AD's own text is required, and it is item 5's first exception:

7. **AC-15 — lifecycle closure is the completeness branch's question,
   not the Archive Seal's.** AC-15 as accepted reads "Completeness and
   the Archive Seal **both** read `transition_records.jsonl`'s terminal
   record before running," and requires an unclosed `lifecycle_version:
   "v1"` archive to report *both* branches `UNVERIFIABLE`. The Seal
   branch does not do this and, on the reasoning below, must not. The
   clause is amended to:

   > **AC-15 (amended 2026-07-26).** The completeness branch reads
   > `transition_records.jsonl`'s terminal record before running. A
   > `lifecycle_version: "v1"` archive whose terminal `to_phase` is not
   > `Archive` — including an absent or empty `transition_records.jsonl`
   > — reports the completeness branch `UNVERIFIABLE`, never failing and
   > never exempt, and therefore reports `OverallStatus.UNVERIFIABLE`
   > for the archive under the aggregation rule. The Archive Seal branch
   > makes no closure judgement of its own; it answers only whether the
   > archive's tree matches the sealing commit named by the Register.

   **Why the code was not changed to match the accepted text instead.**
   This was a genuine fork, and the deciding argument is the same one
   that drove the rest of this hardening pass. `transition_records.jsonl`
   is read from the **working tree**. Making the Seal's answer depend on
   it would have added a live, post-seal-editable input to a comparison
   whose every other input this pass just finished pinning to the sealing
   commit — the exact defect class the pass exists to remove, reintroduced
   by an acceptance criterion. Three further points, none of them alone
   decisive:

   - AC-15's *user-visible* guarantee is unchanged. `overall_status` is
     derived, and an unclosed cycle already reports `UNVERIFIABLE`
     through the completeness branch, so no report changes shape.
   - Under AD-074 the Seal has a **stronger** structural guard than a
     closure read: an unclosed cycle has no Register record, because
     issuance happens after the Decision → Archive record is committed
     (AD-074 §5.3). Absence of a record is already `UNVERIFIABLE`.
   - Were a record somehow issued for an unclosed cycle, that is an
     *issuance* error. The Seal's answer — "this tree matches the commit
     you named" — remains true and correctly scoped; suppressing it
     would make the Seal report on a question it did not ask.

   AC-15's original phrasing predates AD-074: it was written when the
   Seal's expected value was an unspecified "sealed manifest" with no
   issuance discipline, and a closure read was the only available guard.
   AD-074 §5.3 supplied a better one.

8. **Nothing else changes, again.** Item 5's enumeration stands as
   amended by item 7 and by nothing else. AC-1…AC-14, AC-16 and AC-17 are
   untouched, and AC-15's amendment narrows one branch's responsibility
   rather than relaxing any check: no archive reports `SOUND` under the
   amended text that would have reported otherwise under the original.

**Further amended, 2026-07-26** (AD-074 Increment 2 **acceptance audit**
remediation — the independent audit of the hardening pass above, which
found the architecture correct and withheld acceptance on two blocking
findings). This block records the corrected trust model here, in the
owning register, so that no reader has to reach
`AD_074_ARCHIVE_SEAL_DESIGN_REVIEW.md` to find out that the previous
block's claim was too strong.

9. **RF-1 — the Git attribute *source* stack was not fully pinned, and
   the claim that it was is withdrawn.** The hardening pass above
   described the attribute inputs to the Seal comparison as **"four
   stacked sources"**, all pinned. That enumeration was complete for git
   <2.40 and stopped being complete when git 2.40 added `attr.tree`
   (config) and `GIT_ATTR_SOURCE` (environment). The correct statement is
   **five possible attribute influences, including `attr.tree` /
   `GIT_ATTR_SOURCE` attribute-source selection.**

   Neither adds an attribute rule; both redirect attribute lookup to an
   arbitrary tree, which makes the fourth source's blob-for-blob
   verification *vacuous* — that check confirms the working-tree
   `.gitattributes` matches the sealing commit, not that git consulted
   it. Verified end to end: with either set to a tree containing no
   `.gitattributes`, a `-text` (byte-exact) archive artifact tampered to
   CRLF hashed back to its sealed blob and the archive reported
   **`MATCHED`** instead of `MISMATCH`. That is a tampered archive
   certified sound by an input outside the sealing commit, which is
   exactly what AC-74-5a forbids.

   Seal verification now explicitly neutralises **all five**: system
   attributes (`GIT_ATTR_NOSYSTEM=1`), global attributes
   (`-c core.attributesFile=`), `$GIT_COMMON_DIR/info/attributes`
   (refused outright — `UNVERIFIABLE`, since git offers no way to
   disable it), working-tree `.gitattributes` (verified blob-for-blob
   against the sealing commit), and `attr.tree` / `GIT_ATTR_SOURCE`
   selection (`-c attr.tree=` on every invocation **and**
   `GIT_ATTR_SOURCE` removed from the environment — the environment
   variable overrides the config setting, so the config pin alone does
   not close it).

   **AC-74-5a is amended to read:** *"No input outside the sealing commit
   may change a `MATCHED` result, including Git attribute source
   selection."*

10. **RF-2 — a regression test was a false positive; no production code
    was wrong.** The round-trip identity check on `sealed_commit` (D11)
    was justified by, and tested through, a *ref whose name is 40 hex
    characters* impersonating an object id. That case is **not
    reachable**: git deliberately ignores refs whose names end in 40 hex
    characters when resolving a 40-hex revision, so the decoy never
    resolved and the record failed earlier, as an unreadable commit. The
    test asserted only that *some* reason was returned, so it passed
    whether or not the round-trip check existed — confirmed by deleting
    the check and watching it still pass.

    The check itself is correct and is retained unchanged. Its
    **reachable** case is an **annotated tag**: a tag object's id is a
    full-length lowercase hexadecimal string, so it clears the syntactic
    fixed-id check, and `^{commit}` then peels it to a *different*
    object. The test is replaced with that case and asserts the identity
    failure specifically; it fails when the check is removed. D11's
    rationale is corrected accordingly, and the 40-hex-refname claim is
    withdrawn from it.

11. **The working-tree reparse-point refusal (D8) had a Windows-shaped
    hole.** *(Recorded here 2026-07-26; previously documented only in
    `AD_074_ARCHIVE_SEAL_DESIGN_REVIEW.md`, §7B, under the label
    **F-3** — not renumbered here to avoid colliding with this same
    document's own, unrelated **F-3** a few hundred lines above (the
    AD-073 correction pass's applicability-prose finding); the two are
    different findings from different audit passes that happen to share
    a label only in the design review.)* D8's refusal was implemented
    with `Path.is_symlink()`,
    which reports **False** for a Windows NTFS **junction** — a reparse
    point that redirects a directory without being a symlink by that
    test. `os.walk(followlinks=False)` does not close the gap either: it
    suppresses descent into *symlinked* directories only. So on Windows
    the archive walk descended into a junction and reported the target
    directory's files as the archive's own — the identical defect D8
    closed for symlinks, left open on the platform where it is **more**
    reachable, since creating a junction needs no privilege while
    creating a symlink needs Developer Mode or elevation.

    **[verified]** before the fix, a junction planted inside a sealed
    archive produced `MISMATCH` with an `unexpected` finding naming a
    file outside the archive entirely; after it, `UNVERIFIABLE`.
    Detection is now "symlink **or** reparse point"
    (`os.path.isjunction`, with an `st_file_attributes` /
    `FILE_ATTRIBUTE_REPARSE_POINT` fallback for interpreters predating
    it). Existing symlink behaviour is unchanged — the symlink test runs
    first — and the change only ever *adds* refusals, so it can convert
    a wrong `MATCHED`/`MISMATCH` into `UNVERIFIABLE` and never the
    reverse. Like items 9 and 10, this is a tightening: no archive
    reports `SOUND` under it that would not have reported `SOUND`
    before.

12. **Nothing else changes.** Items 9, 10, and 11 are exhaustive of this
    amendment. All three are *tightenings*: item 9 only ever converts a
    wrongly-`MATCHED` archive into `MISMATCH` or `UNVERIFIABLE`, item 10
    changes no production behaviour at all, and item 11 only ever
    converts a wrongly-`MATCHED`/`MISMATCH` archive into `UNVERIFIABLE`.
    No archive reports `SOUND` under this amendment that would not have
    reported `SOUND` before, and the AD-073 acceptance criteria are
    otherwise untouched.

**Further amended, 2026-07-26** (post-AD-075 governance hardening pass —
`core/governance/dataset_integrity.py` implemented, and
`core/governance/archive_seal.py` hardened a second time; remediation of a
merge-blocking acceptance review, not a new source document). Five further
amendments to this AD's own text:

13. **AC-3 / Decision part 5 — "observes no time-varying repository state"
    is narrowed to admit two bounded admissibility gates.** The Seal's
    second hardening pass (`archive_seal.py`'s `_committed_register_text`
    and `_unreachable_commit_error`) now reads `HEAD` for exactly two
    purposes, neither the comparison AC-3 and Decision part 5 describe:
    whether the Archive Seal Register record naming the sealing commit is
    itself *committed*, never a working-tree read; and whether the sealing
    commit is *reachable* from `HEAD`, not merely resolvable. AD-074 §7A
    B-1's reversal (recorded in AD-074's own text, not restated here) is
    the detailed reasoning for the second gate; both gates share the same
    bound, stated once here rather than twice: each can only ever move a
    result toward `UNVERIFIABLE`, never toward a `MATCHED` or `MISMATCH`
    the comparison would not otherwise have reached, so the comparison
    itself remains a pure function of the sealing commit and the archive
    bytes. AC-3 and Decision part 5's "observes no time-varying repository
    state" is narrowed to mean exactly that: no time-varying fact may
    change a `MATCHED`/`MISMATCH` verdict or move a result between them —
    the guarantee already carried, restated to admit an admissibility gate
    that only ever narrows toward `UNVERIFIABLE`. This is not a new
    exception to AC-3 in the sense Decision part 5's amendment item 1
    (git-object reads at a fixed commit) already is not one: neither turns
    the Seal into a second `FreezeVerifier`, and neither makes the
    comparison's *result* a function of anything but the sealing commit
    and the bytes.
14. **The dataset-integrity branch is built, and the *Future work* choice
    it required is made: orchestration.** *Future work* named
    "`DatasetIntegrityChecker` and `ReproducibilityChecker` as possible
    further branches, each requiring its own decision about whether
    orchestration or independence serves the auditor better." For
    `DatasetIntegrityChecker`, that decision is now made: **orchestration**,
    exactly as `ArchiveVerifier` already orchestrates the Seal.
    `core/governance/dataset_integrity.py`'s `verify_dataset_integrity()`
    recomputes each `dataset_hashes/*.jsonl` snapshot's SHA-256 and row
    count against `dataset_manifest.json` read at the sealing commit —
    resolved once, by `archive_seal.resolve_sealing_commit()`, and reused
    rather than re-derived, so the Seal and the dataset branch can never
    name two different sealing commits for the same archive (the
    duplicate-source-of-truth failure Decision part 8 exists to prevent,
    one level up). It is invoked unconditionally, alongside Completeness
    and the Seal, never caller-elected the way the freeze branch is
    (*Architecture overview*'s "third row"): its subject is archive-local
    bytes against a value fixed at archive close, the Seal's own stability
    property, not the freeze branch's. **`ReproducibilityChecker` is
    untouched by this item** and remains exactly what *Future work* and
    Non-goals item 5 already said it was — a separate §4.4 component,
    undesigned, unimplemented, and not folded into this architecture by
    this or any amendment to date.
15. **Four branches, not three.** *Status vocabulary*'s "Three branches,
    three independent vocabularies" becomes four: the dataset-integrity
    branch owns its own three-valued vocabulary (`VERIFIED` / `DRIFTED` /
    `FAILED`, `DatasetIntegrityStatus`), deliberately not merged with
    `CompletenessStatus`, `SealStatus`, or `FreezeStatus` — the same
    discipline this AD's original text already applied to the first
    three. `FAILED` names the same fact `UNVERIFIABLE` names elsewhere
    ("could not reach a verdict"); it is not folded into that shared name
    because the branch was specified with its own vocabulary, not because
    the fact it denotes differs. The *Architecture overview* diagram and
    table gain a fourth line/row, **Dataset Integrity**, positioned
    between the Archive Seal and Freeze binding: subject
    `dataset_hashes/*.jsonl` snapshot bytes against `dataset_manifest.json`
    read at the sealing commit; stable once the archive closes (yes — both
    sides are archive-local, the Seal's own property); owner
    `core.governance.dataset_integrity`. The **Overall status aggregation
    rule**'s "exactly one branch can be absent, and for exactly one
    reason" is unchanged in what it protects — the freeze branch remains
    the only caller-elected one — but the rule's fixed precedence gains the
    dataset branch's two non-good values *within* the existing three
    steps, not as a new step: step 1 (`UNSOUND`) gains
    `DatasetIntegrityStatus.DRIFTED` alongside Completeness `INCOMPLETE`,
    Seal `MISMATCH`, and Freeze `DRIFTED`; step 2 (`UNVERIFIABLE`) gains
    `DatasetIntegrityStatus.FAILED` alongside the other three branches'
    `UNVERIFIABLE`; step 3 (`SOUND`) additionally requires
    `DatasetIntegrityStatus.VERIFIED`. No fourth outcome, weighting, or
    partial-credit case is introduced — the rule itself is unchanged; only
    the set of always-invoked branches feeding it grows from two
    (Completeness, Seal) to three (Completeness, Seal, Dataset Integrity),
    with Freeze remaining the one caller-elected branch. AC-4 and AC-5's
    "three branches" read as four accordingly and are not separately
    rewritten here.
16. **Non-goals item 5 — discharged for dataset integrity only.** Item 5
    read: *"Reproduction (`ReproducibilityChecker`, `run_reproduction()`)
    and dataset integrity (`DatasetIntegrityChecker`,
    `dataset_manifest.json` content verification). Both remain separate
    §4.4 components; neither is folded into this architecture."* The
    dataset-integrity half is discharged by item 14 above:
    `DatasetIntegrityChecker` now exists, is orchestrated by
    `ArchiveVerifier` as its fourth branch, and *is* folded into this
    architecture. The reproduction half is untouched and remains a
    non-goal exactly as written: `ReproducibilityChecker` and
    `run_reproduction()` are not implemented, not designed, and not
    folded into this architecture by this or any amendment to date.
17. **Nothing else changes.** Items 13–16 are exhaustive of this
    amendment. Item 13 is a tightening in the same sense items 9–11
    already are: it converts no `UNVERIFIABLE`/`MISMATCH` archive into
    `MATCHED`, and no archive reports `SOUND` under it that would not have
    reported `SOUND` before. Items 14–16 add one always-invoked branch and
    its vocabulary; they do not relax Completeness, the Seal, or Freeze,
    and they do not change AC-1, AC-2, AC-6 through AC-10, AC-12 through
    AC-17, the Non-goals other than item 5, or any Migration item.

---

**Context.**

Four facts, each independently verified at commit `a1a0aa8`:

1. **`ArchiveVerifier` is named in three places and implemented in
   none** (G-3, R-3, **Medium**): `core/governance/__init__.py`'s module
   docstring, `tools/archive_manifest.py`'s header, and
   `docs/PLATFORM_ARCHITECTURE_V1.md` §4.4. `grep -rn "class
   ArchiveVerifier" core/ tools/` returns nothing. Standard §2 Phase 8
   requires an archive-completeness check; on this platform that check
   has only ever been performed by hand — most recently by the Phase G
   remediation decision itself, which is also the document that recorded
   the gap.
2. **No artifact asserts that a closed cycle's evidence package is
   complete** (D-8). `research_archive/reference_h4/` was inspected
   manually for that decision; nothing in the repository re-asserts the
   result, and nothing would detect a later divergence.
3. **A closed cycle's archived bytes are protected by nothing
   automated** (D-9/G-5/R-4, **High**, live at this commit).
   `tests/test_repository_integrity_snapshot.py`:100–106 still excludes
   `research_archive/reference_h4/`, and `tests/fixtures/protected_file_hashes.json`
   — a one-time snapshot taken *before* Phase 0 touched the repository,
   immutable by its own docstring's terms — holds zero `reference_h4`
   entries. The exclusion clause has expired by its own wording.
4. **The existing integrity components each answer a different
   question, and none answers these two.**
   `core/governance/freeze_verifier.py` answers a question about the
   *repository* ("is this document's freeze claim true of the repository
   right now?", AD-033). `core/governance/decision_recorder.py`'s
   `verify_chain_intact()` / `verify_chain_anchored()` answer a question
   about *record linkage* in one file. `run_reproduction()` answers a
   question about *re-execution*. `tools/archive_manifest.py` is a
   write-side guard only — by AD-030's explicit scope statement it "does
   not read or interpret an existing manifest" and "does not implement
   `ArchiveVerifier`."

An architecture review of a proposed **Archive Seal** design was
conducted ahead of this AD and reached six conclusions, taken here as
review input rather than as decisions in their own right: the Archive
Seal is a valuable integrity primitive; it should *not* replace
`ArchiveVerifier`; `ArchiveVerifier` should become a thin orchestration
layer; integrity and completeness are separate responsibilities;
`FreezeVerifier` remains responsible for commit binding; and every
existing documentation reference to `ArchiveVerifier` should remain
valid. This AD records those conclusions as an architectural decision,
with their consequences and their boundaries stated explicitly.

---

**Problem statement.**

Archive verification is not one question. It is at least four, and the
platform currently conflates them under one unimplemented name:

| # | Question | Subject of the claim | Answered today by |
|---|---|---|---|
| Q1 | Does this evidence package contain everything Standard §5 requires? | The package's *shape* | Nothing (manual inspection only) |
| Q2 | Are the archived files still the bytes that were archived? | The package's *content* | Nothing (D-9, live gap) |
| Q3 | Is the freeze commit this archive claims real, resolvable, and undrifted? | The *repository's current state* | `FreezeVerifier` (invoked by hand) |
| Q4 | Was the conclusion correct? | The *research* | Human review; never mechanical (Standard §4) |

**P1 — completeness is unverified.** Q1 has no mechanical answer, so
Phase 8 completeness is asserted by whoever performs it and re-derivable
by nobody.

**P2 — content integrity is unverified.** Q2 has no mechanical answer for
a *closed* cycle. The one repository-wide mechanism that exists
(`protected_file_hashes.json`) is a pre-Phase-0 snapshot with no path for
a cycle that closes after it was taken — G-5, stated exactly: a closed
cycle has no path back into protected status.

**P3 — the naming risk.** Introducing an Archive Seal as a *peer* of
`ArchiveVerifier` would create a second public answer to "is this archive
sound," invalidate three existing references, and leave callers to decide
which component is authoritative. That is the duplicate-source-of-truth
failure this platform has refused elsewhere (AD-049 part 3; AD-062's
single-writer-per-artifact rule; AD-066's two-registry disclosure). P3 is
a real problem created by the proposed solution to P1/P2, and it is the
reason this AD exists at all rather than an implementation ticket.

---

**Decision.**

Eight parts. Each is architectural; none prescribes an algorithm, a
signature, a file format, a module split below the two named components,
or a hash function.

**1. `ArchiveVerifier` is retained as the single archive-verification
abstraction.** It is the one name a governance caller uses to ask "is
this archive sound." Every existing reference to it — in
`core/governance/__init__.py`, `tools/archive_manifest.py`, and
`PLATFORM_ARCHITECTURE_V1.md` §4.4 — remains valid and correct in
meaning after this AD, and remains valid after implementation. Nothing
here renames it, deprecates it, or narrows what §4.4 says it does.

**2. `ArchiveVerifier` becomes a thin orchestration layer.** It owns
composition and reporting; it owns no integrity algorithm of its own. It
determines *which* checks apply to an archive, invokes them, and
assembles their findings. It computes no hash, parses no evidence
content, and re-implements no check another component already owns.

**3. The Archive Seal is an implementation primitive beneath
`ArchiveVerifier`, not a peer abstraction.** It is the mechanism by
which Q2 is answered. It is invoked by `ArchiveVerifier`; it is not a
second public entry point for archive verification, and no governance
caller is expected to reach it directly to ask the archive-soundness
question. Whether it is one module, one function, or several is an
implementation matter this AD does not decide.

**4. Completeness and integrity are separate responsibilities, with
separately attributed results.** Standard §5 completeness (Q1) and seal
content integrity (Q2) are evaluated independently and reported
independently. Neither may mask, satisfy, or substitute for the other,
in either direction.

**5. `FreezeVerifier` is invoked, never reimplemented, and never
modified by this AD.** Commit binding (Q3) remains entirely
`core/governance/freeze_verifier.py`'s responsibility, with its existing
semantics (AD-033), its existing three-valued outcome (AD-047, AD-051),
and its existing `covered_paths` field (AD-060) unchanged. *(Amended
2026-07-26 — see Status, item 2.)* The Archive Seal performs no
freeze-claim verification and observes no time-varying repository state;
it may read git objects at a commit recorded at archive close, where both
sides of any comparison are archive-local and fixed, without replacing or
duplicating any part of `FreezeVerifier`'s responsibility.
`ArchiveVerifier` itself still never verifies a commit — that remains
exclusively `FreezeVerifier`'s act, invoked, not reimplemented.

**6. `ArchiveVerifier` produces exactly one report, composed of
separately attributed component findings.** One call, one report — but
the report preserves per-component results. Any overall status it
carries is a **derived** projection over the component statuses under a
documented rule, recomputable by a reader from the components, never a
stored aggregate that erases them. This follows AD-049 part 3's stated
discipline verbatim: *"was the verdict derived, not asserted?" is
answered by the auditor recomputing from stored primitives under a
documented rule.*

**7. Every component named here is read-only, and this AD grants no
write authority.** `ArchiveVerifier` and the Archive Seal read
artifacts; neither writes, creates, repairs, normalizes, or mutates
anything under `research_archive/`, exactly as `FreezeVerifier` is
read-only over git. Seal **issuance** — who produces a sealed manifest,
when, where it is stored, and under what write authority — is out of
scope (see *Non-goals*) and is constrained by AD-062: nothing in this AD
authorizes a new writer of any artifact under
`research_archive/<project>/`.

**8. One authoritative content-hash record per archived file, and the
sealed manifest's coverage is bounded by what other mechanisms already
own.** Two mechanisms already assign an expected hash to specific
archived bytes, and the sealed manifest never extends to either's files:
the Phase-0 `tests/fixtures/protected_file_hashes.json` snapshot, and
`dataset_manifest.json`'s per-entry `content_hash` field — already
`DatasetIntegrityChecker`'s input contract (Non-goals item 5), and
already naming every file under `dataset_hashes/` by `snapshot_path`.
Where either mechanism already covers a file, the sealed manifest does
not cover it, and the reverse holds equally. Two mechanisms recording an
expected hash for the same bytes is the duplicate source of truth this
architecture exists to avoid, and it is forbidden regardless of which
mechanism is written first or which pre-exists the other.

---

**Architecture overview.**

```
ArchiveVerifier                     (orchestration; owns composition + the report)
    |
    ├── Completeness verification   (Standard §5 evidence-package shape)
    ├── Archive Seal verification   (archived content integrity)
    ├── Dataset Integrity check     (dataset_hashes/*.jsonl vs. sealed manifest) *(added — Status, item 14)*
    └── FreezeVerifier integration  (commit binding — invoked, not owned)
```

The split is not a convenience decomposition. Each branch verifies a
different *subject*, and the subjects have different stability
properties:

| Branch | Subject of verification | Stable once the archive closes? | Owner |
|---|---|---|---|
| Completeness | The evidence package's structure, against Standard §5's seven required items | Yes — the required shape is fixed by the Standard, and the package is immutable | `ArchiveVerifier`'s own layer |
| Archive Seal | The archived files' bytes, against the sealing commit tree identified by an Archive Seal Register record *(amended 2026-07-26)* | Yes — both sides of the comparison are archive-local | Archive Seal primitive |
| Dataset Integrity *(added — Status, item 14)* | `dataset_hashes/*.jsonl` snapshot bytes and row counts, against `dataset_manifest.json` read at the sealing commit resolved by the Seal | Yes — both sides are archive-local, the Seal's own stability property | `core.governance.dataset_integrity` |
| Freeze binding | The **repository's current state**, against a commit reference the archive claims | **No** — the answer can legitimately change after the archive closes | `FreezeVerifier` |

The third row is the load-bearing one. A freeze-verification result is a
statement about the repository at the moment of the call, not about the
archive: a covered path edited in `docs/` a year later legitimately turns
a `VERIFIED` freeze into `DRIFTED` without any archived byte changing.
Folding commit binding into a content seal would produce a seal whose
result varies with facts outside the sealed set — a seal that fails for
reasons that are not integrity failures. That is why `FreezeVerifier` is
*integrated* rather than absorbed, and why its invocation is
caller-elected rather than unconditional. **"Where appropriate," wherever
this AD uses it of the freeze branch, means exactly one thing: the caller
requested freeze verification.** That request is the only condition on
whether the branch exists. It is never a condition about what the archive
contains — an archive that states no freeze claim still produces a freeze
branch whenever the caller asked for one, reporting `UNVERIFIABLE`
(*Responsibilities*, `ArchiveVerifier` — does).

**Composition rule for overlapping paths.** `FreezeVerifier`'s
`covered_paths` (AD-060) and the Archive Seal's sealed file set can name
what looks like the same file — a source file the freeze claim covers in
the live repository, mirrored into the archive under the seal. The two
branches are never merged, never deduplicated, and never given
precedence over each other: each is reported exactly as Decision part 6
already requires, attributed to its own branch, and the composed
report's derived overall status (Decision part 6, AC-5) treats them as
independent inputs, not as two votes on one question. A Seal `MATCHED`
alongside a `FreezeStatus.DRIFTED` for what appears to be the same
filename is not a contradiction to resolve — the Seal answers "does the
*archived* copy match what was sealed," a question about bytes fixed at
archive time; `FreezeVerifier` answers "does the *live repository* path
still match the frozen commit right now," a question that can legitimately
change afterward (this section's own point, above). `ArchiveVerifier`
does not attempt to reconcile the two into a single "is this file
trustworthy" verdict; a reader who needs that judgment reads both
attributed findings, exactly as AC-4 already requires for any pair of
branch results.

**Status vocabulary.** Four branches *(amended 2026-07-26 — see Status,
item 15; three at this AD's original acceptance)*, four independent
vocabularies, deliberately not merged into one enum — so that a
confirmed problem in one branch is never mistaken for the same fact in
another:

- **Freeze branch** — `FreezeStatus`, exactly as
  `core/governance/freeze_verifier.py` already defines it (AD-047,
  AD-051): `VERIFIED`, `DRIFTED`, `UNVERIFIABLE`. Unmodified, unextended,
  never assigned to either other branch.
- **Completeness branch** — a distinct, `ArchiveVerifier`-owned
  vocabulary: `COMPLETE` (every required item — Standard §5's seven,
  plus `archive_manifest.json` — present and of the correct kind, with
  content unexamined and emptiness no bar), `INCOMPLETE`
  (at least one required item missing or the wrong kind), `EXEMPT` (a
  legacy archive, AC-14, the v1 layout check waived), `UNVERIFIABLE`
  (the cycle has not closed, AC-15). These four belong to this branch
  alone.
- **Archive Seal branch** — a distinct, seal-owned vocabulary
  *(amended 2026-07-26 — see Status, item 3)*: `MATCHED` (the sealing
  commit tree identified by an Archive Seal Register record exists and
  every covered file's bytes match it), `MISMATCH` (a Register record
  exists and at least one covered file is modified, missing, or
  unexpected — AC-7's three finding kinds are preserved in the attributed
  findings and never collapsed; `MISMATCH` is the branch-level summary of
  "one or more occurred," not a replacement for them), `UNVERIFIABLE` (no
  Archive Seal Register record identifies a sealing commit tree to
  compare against for this archive — including, at this AD's original
  acceptance, every archive, since seal issuance's format was then
  undecided; AD-074 resolves the format and leaves the per-archive rule
  unchanged).
- **Dataset Integrity branch** *(added 2026-07-26 — see Status, item
  15)* — a distinct, `core.governance.dataset_integrity`-owned
  vocabulary, `DatasetIntegrityStatus`: `VERIFIED` (a manifest was read
  at the sealing commit and every entry's snapshot is present, hashes
  to its declared `content_hash`, and holds its declared `row_count`),
  `DRIFTED` (at least one entry is confirmed wrong — a hash mismatch, a
  row-count mismatch, or a missing snapshot), `FAILED` (the question
  could not be answered — no sealing commit, no manifest at the sealing
  commit, an unparsable manifest, a snapshot that cannot be read). Named
  `FAILED` rather than `UNVERIFIABLE` because that is the vocabulary
  this branch was specified with; the fact it denotes is the same one
  `UNVERIFIABLE` denotes elsewhere.

`UNVERIFIABLE` is the one value name shared across the other three
vocabularies (Completeness, Archive Seal, Freeze), and it means the same
fact in each: this branch could not reach a verdict; the Dataset
Integrity branch's `FAILED` denotes the identical fact under its own
branch's name. That is the sole intentional overlap; no other value
is shared, and none is folded into `GateStatus`, `GateOutcome`, or the
Decision-outcome vocabulary (`PASS`/`FAIL`/`INCONCLUSIVE`, Standard §4)
— an archive report answers none of those questions (this AD's own
"does not" lists).

**Overall status aggregation rule.** The derived value Decision part 6
and AC-5 require — never stored, always recomputable from the branch
values above — is drawn from its own three-valued vocabulary: `SOUND`,
`UNSOUND`, `UNVERIFIABLE`. The rule considers only branches that were
actually invoked. **Exactly one branch can be absent, and for exactly
one reason:** a freeze branch the caller did not request (the "where
appropriate" clause, defined above as the caller's request and nothing
else) is absent from the report and takes no part in this computation.
Completeness, the Seal, and Dataset Integrity always run *(the third
added 2026-07-26 — see Status, items 14–15)*; a requested freeze branch
always runs, and a requested freeze branch that finds no freeze claim
reports `UNVERIFIABLE` and is counted like any other invoked branch. An
absent branch is not the same fact as an invoked branch reporting
`UNVERIFIABLE`, and a reader must never conflate the two. Fixed
precedence, evaluated top to bottom, first match wins:

1. **`UNSOUND`** — at least one invoked branch reports its confirmed-
   problem value: Completeness `INCOMPLETE`, Seal `MISMATCH`, Dataset
   Integrity `DRIFTED` *(added 2026-07-26)*, or Freeze `DRIFTED`.
2. **`UNVERIFIABLE`** — no invoked branch reports a confirmed problem,
   and at least one invoked branch reports `UNVERIFIABLE` (Dataset
   Integrity's `FAILED` counts as this branch's spelling of the same
   fact, *added 2026-07-26*).
3. **`SOUND`** — every invoked branch reports its confirmed-good value:
   Completeness `COMPLETE` or `EXEMPT`, Seal `MATCHED`, Dataset
   Integrity `VERIFIED` *(added 2026-07-26)*, Freeze `VERIFIED`.

This is the entire rule. No implementation may add a fourth outcome, a
weighting, or a partial-credit case. It applies AD-051's own precedence
— confirmed problem outranks unverifiable outranks confirmed good —
across branches instead of within one. Dataset Integrity's two non-good
values slot into the existing three steps; they do not add a step, a
weighting, or a partial-credit case, per Status item 15.

**Worked example: a non-legacy, closed archive with no
`archive_manifest.json`.** Completeness and the Seal each depend on a
different artifact, and this case is where an implementer could
otherwise conflate them:

- **Completeness: `INCOMPLETE`.** `archive_manifest.json` is a required
  item for this branch (the completeness bullet above); its absence is
  reported exactly like a missing Standard §5 item, alongside any of the
  seven that are also missing — each is its own finding, never collapsed
  into one.
- **Seal: unaffected, independently `UNVERIFIABLE`.** The Archive Seal
  compares against its own sealed manifest, a distinct artifact from
  `archive_manifest.json` (Non-goals item 1: the sealed manifest's
  format is undecided and unbuilt; `archive_manifest.json`'s format is
  AD-030's, already built). The seal branch's result depends solely on
  whether *its* sealed manifest exists for this archive — never on
  `archive_manifest.json`'s presence. Under *Migration* item 2's current
  stub, no sealed manifest format exists yet for any archive, so this
  branch reports `UNVERIFIABLE` here exactly as it does everywhere else
  today — because no sealed manifest exists, not because
  `archive_manifest.json` is missing.
- **Reasoning.** Decision part 4 forbids either branch masking,
  satisfying, or substituting for the other. One artifact's absence is
  never grounds to infer, skip, or default the other branch's result;
  `INCOMPLETE` and Seal `UNVERIFIABLE` are two independently attributed
  facts, not one failure reported twice.
- **Overall status: `UNSOUND`.** The aggregation rule's step 1 fires on
  Completeness `INCOMPLETE` before step 2 is ever reached by the Seal's
  `UNVERIFIABLE`.

---

**Responsibilities.**

**Archive Seal — does:**

- verify archive content integrity — that the archived files covered by
  the sealed manifest have the bytes the manifest records for them,
  where "covered" excludes any file already carrying its own
  domain-owned content-hash record (Decision part 8);
- detect **modified** files — present, but not the recorded content;
- detect **missing** files — recorded in the sealed manifest, absent
  from the archive;
- detect **unexpected** files — present in the archive, absent from the
  sealed manifest;
- validate sealed manifest consistency — that the manifest is itself
  well-formed and internally coherent before any comparison result
  derived from it is reported.

**Archive Seal — does not:**

- decide whether an archive is *complete* under Standard §5. A sealed
  manifest records what was sealed, not what the Standard requires; an
  archive can be perfectly sealed and materially incomplete, and the seal
  must report the former without implying the latter;
- perform freeze-claim verification, resolve a freeze commit reference,
  or observe time-varying repository state — that remains exclusively
  `FreezeVerifier`'s responsibility (Decision part 5). It may read git
  objects at the commit recorded in the Archive Seal Register, fixed at
  archive close, where both sides of the comparison are archive-local
  *(amended 2026-07-26 — see Status, item 1)*;
- verify decision-chain linkage — `verify_chain_intact()` /
  `verify_chain_anchored()` remain `decision_recorder`'s, and a seal that
  re-derived chain semantics from file bytes would be a second, weaker
  implementation of an existing check;
- duplicate a content-hash record a domain component already owns —
  concretely, `dataset_hashes/*.jsonl` and any other file
  `dataset_manifest.json` describes by `content_hash`, which is
  `DatasetIntegrityChecker`'s input contract (Non-goals item 5) and
  stays outside the sealed manifest's coverage regardless of whether the
  seal or the dataset manifest was written first;
- write, repair, re-seal, or normalize anything;
- interpret evidence content, judge research substance, or read meaning
  from any archived document.

**`ArchiveVerifier` — does:**

- orchestrate archive validation for one archive;
- verify Standard §5 completeness — the presence and kind (file vs.
  directory) of the seven items Standard §5 itself lists
  (`hypothesis.md`, `methodology.md`, `dataset_manifest.json`,
  `dataset_hashes/`, `experiment_results/`, `reviewer_reports/`,
  `decision_log.md`) — **and, separately, `archive_manifest.json`'s own
  presence**, which is never counted as one of those seven (the Standard
  does not name it) but is a required item under AD-030's own
  applicability contract (below), checked and reported by this same
  branch alongside them. **The check is mechanical and uniform across
  all eight items.** For each item the branch asks exactly two
  questions — does an object exist at that path, and is it the required
  kind (`dataset_hashes/`, `experiment_results/`, and
  `reviewer_reports/` are directories; the remaining five items are
  files) — and nothing else. An object of the wrong kind is reported
  exactly as a missing one is: `INCOMPLETE`, as its own finding. Beyond
  existence and kind this branch reads no archived bytes: it does not
  open, parse, or hash any file, does not check JSON well-formedness
  (`archive_manifest.json`'s or `dataset_manifest.json`'s included),
  does not enumerate or count the entries of any required directory, and
  does not judge whether the evidence present is materially sufficient.
  **An existing but empty object passes the presence/kind check** — a
  zero-byte file and an empty directory are each present and of the
  correct kind, and both count toward `COMPLETE`, uniformly for all
  eight items with no per-item exception. Emptiness is a content fact;
  where it matters it is Standard §4's human question (Non-goals item
  6), never this branch's. The applicability and closure determinations
  below do read `archive_manifest.json`'s `lifecycle_version` and
  `transition_records.jsonl`'s terminal record; those are separate
  determinations made before this branch runs, not part of the
  presence/kind check;
- invoke the Archive Seal;
- invoke `FreezeVerifier` where appropriate — **"where appropriate"
  means, exactly and only, where the caller requested freeze
  verification. That one condition, and nothing about the archive's
  content, decides whether the freeze branch exists.** A caller that did
  not request freeze verification gets no freeze branch: absent from the
  report and excluded from aggregation (the *Overall status aggregation
  rule* above). A caller that did request it always gets a freeze branch,
  `FreezeVerifier` executes, and the branch always carries one of
  `FreezeStatus`'s three values — so the archive's own state decides only
  *which* value, never whether the branch is present. In particular, a
  freeze claim the archive does not state is `UNVERIFIABLE`, never
  absent-and-therefore-fine. The structured claim already exists, one
  layer below
  `archive_manifest.json`: `core/governance/decision_recorder.py` writes
  `freeze_commit_ref`, `freeze_covered_paths`, and
  `freeze_verification_status` into every record of
  `transition_records.jsonl`, already present in every v1 archive
  (confirmed at `research_archive/reference_h4/
  transition_records.jsonl`). No schema field is added anywhere for
  this — both inputs `verify_freeze(commit_ref, covered_paths)` requires
  pre-exist this AD, on the same record. **Selection rule:**
  `ArchiveVerifier` reads `freeze_commit_ref` **and**
  `freeze_covered_paths` from the chain's terminal record (highest
  `sequence_number`) as plain archived data — the same record, the same
  selection rule, for both inputs; `covered_paths` is never separately
  sourced, computed, or supplied by the caller. It may use
  `decision_recorder`'s `read_chain()` — a structural reader, not a
  verification authority — to reach the terminal record, but does not
  invoke `verify_chain_intact()` or `verify_chain_anchored()`; chain
  *verification* remains exclusively `decision_recorder`'s question,
  exactly as the Archive Seal is barred from it above, and this bullet
  extends that same exclusivity to `ArchiveVerifier` itself — reading
  two fields from the terminal record, whether via `read_chain()` or
  direct file access, is not chain verification. If
  `transition_records.jsonl` is absent,
  empty, or its terminal record carries no `freeze_commit_ref`, the
  freeze claim is absent and the branch is `UNVERIFIABLE` under the rule
  already stated; a terminal record with `freeze_commit_ref` but an
  empty `freeze_covered_paths` is passed to `verify_freeze()` exactly as
  read, unmodified, and yields `UNVERIFIABLE` under AD-051 — the same
  outcome AD-051 already assigns any caller's empty `covered_paths`, not
  a new rule for this one;
- determine applicability — `RESEARCH_ARCHIVE_MANIFEST.md`'s own
  "Applicability" rule never generates an `archive_manifest.json`
  retroactively, so manifest absence is the `lifecycle_version: "legacy"`
  signal **only for `reference_v1`, `reference_v2_h1`, and
  `reference_h3` — the three archives that rule names, and no other.**
  For every other archive, manifest absence is not a legacy signal; it is
  the absence of `archive_manifest.json` itself — a required item under
  AD-030/`RESEARCH_ARCHIVE_MANIFEST.md`'s applicability contract, **not**
  one of Standard §5's seven (per the completeness bullet above) —
  reported by the completeness branch as a failure with the same
  severity as any missing §5 item, never as exempt. Where a manifest
  exists, its `lifecycle_version` field governs as written. A legacy
  archive — one of the three named archives with no manifest, or any
  archive whose present manifest states `lifecycle_version: "legacy"` —
  is exempt from the v1 layout check and reported as exempt, never as
  failing;
- determine closure, before running the completeness or seal branch — a
  present `archive_manifest.json` with `lifecycle_version: "v1"` records
  that a project's archive directory was *scaffolded*
  (`RESEARCH_ARCHIVE_MANIFEST.md` "Archive scaffold generator"), which
  happens once, at directory creation, well before Phase 8; it does not
  record that the cycle has *closed*. Completeness (Q1) and the Archive
  Seal (Q2) both presuppose a closed cycle's evidence package (Problem
  statement P1, P2), so `ArchiveVerifier` reads
  `transition_records.jsonl`'s terminal record first: a terminal record
  whose `to_phase` is `Archive` — the Standard's terminal, no-outbound-
  transition phase — means the cycle is closed, and completeness and the
  seal run as designed. Any other terminal `to_phase`, or an absent or
  empty `transition_records.jsonl`, means the cycle is still open, and
  both branches report `UNVERIFIABLE` — never failing, never exempt. An
  open v1 archive is missing required items *because the research is
  still in progress*; that is a different fact from a closed archive
  missing them, and the two must not collapse into the same finding;
- produce a single validation report, with per-component attribution.

**`ArchiveVerifier` — does not:**

- compute content hashes, or hold any integrity algorithm;
- re-implement freeze verification, chain verification, reproduction, or
  dataset-manifest verification;
- write anything, anywhere;
- authorize, gate, or refuse a lifecycle transition. Its report is not a
  `GateResult`, is not a `GateOutcome`, never enters a `GateRunRecord` or
  a `DecisionRecord`, and never participates in `compose_transition()`
  (AD-059). Standard §2 Phase 8 is an in-phase completeness check on a
  terminal phase with no outbound transition — the exact row AD-072
  places outside mechanical enforcement — so an archive report has no
  transition to authorize even in principle;
- adjudicate research substance, review adequacy, or reviewer level.

**`FreezeVerifier` — unchanged.** Its module, its semantics, its
signature, its three-valued `FreezeStatus`, and its `covered_paths`
field are exactly as AD-033, AD-047, AD-051, and AD-060 leave them. This
AD adds a caller and nothing else. A `VerificationResult` obtained during
archive verification is reported by `ArchiveVerifier` as a
freshly-computed observation and is **never** written back into any
`GateRunRecord`'s stored `pre_freeze_verification` /
`post_freeze_verification`, which AD-059 step 4 fixes as the only freeze
evidence the Decision Chain may project from.

---

**Architectural rationale.**

**Why `ArchiveVerifier` remains an architectural abstraction.** It names
a *governance question* — "does this archive satisfy the Standard?" —
that outlives any mechanism used to answer it. Three existing references
already point at that question by that name, one of them in a document
(`RESEARCH_ARCHIVE_MANIFEST.md`, AD-030) that designates it as the
manifest's eventual consumer, and one in the platform architecture's own
interface table. The set of checks behind the question will grow —
dataset integrity, chain anchoring, and reproduction are all plausible
future branches — and each growth is an addition behind a stable name
rather than a new name for callers to learn. Deleting the abstraction in
favor of its first mechanism would trade a durable question for a
transient answer.

**Why the Archive Seal is an implementation primitive.** It names a
*mechanism* — content comparison against a recorded manifest — with no
governance meaning of its own. A seal result is not a Phase 8 answer:
the Standard does not require a seal, requires seven specific evidence
items the seal knows nothing about, and would be satisfied by an archive
that has never been sealed. Promoting a mechanism to an abstraction is
what AD-005 refuses ("no generic abstractions ahead of need") and what
AD-030/AD-039 already refused once for this exact area, keeping manifest
tooling in `tools/` precisely because no consumer existed to shape it.
The seal has exactly one consumer — `ArchiveVerifier` — and that is the
definition of a primitive on this platform.

**Why integrity and completeness are separate concerns.** They differ in
every dimension that matters architecturally:

| | Completeness | Integrity |
|---|---|---|
| Source of truth | Standard §5's fixed list | The sealed manifest for this archive |
| Failure means | Evidence was never produced | Evidence was produced and then changed |
| Remediation | Author the missing artifact (a new, dated file — Standard §5's supersession rule) | Investigate a mutation of an immutable archive; nothing legitimate produces it |
| Severity | Governance incompleteness | Suspected tampering or corruption |
| Can be true while the other is false | Yes — a sealed, incomplete archive | Yes — a complete, modified archive |

Collapsing them yields a single result that cannot distinguish "you never
wrote `methodology.md`" from "`methodology.md` changed after archival."
Those are not the same finding, do not carry the same severity, and do
not have the same response. The platform has refused this collapse
before, in the same shape: `FreezeStatus` and `GateStatus` are each
three-valued *because* "failed" and "could not be determined" are
different facts (AD-047, AD-051), and `GateRunRecord` stores per-gate
statuses rather than an aggregate (AD-049) for the same reason.

**Why this architecture avoids duplicate sources of truth.** Four
disjointness rules, each pinned to an existing decision:

1. **One question, one component.** Completeness is answered only by
   `ArchiveVerifier`'s own layer; content integrity only by the seal;
   commit binding only by `FreezeVerifier`; chain linkage only by
   `decision_recorder`. No component answers a question another one owns,
   so no two components can disagree about the same fact.
2. **One public entry point.** Callers ask `ArchiveVerifier`. The seal
   is not a second front door, so there is no "which report is
   authoritative" question to get wrong (P3).
3. **One authoritative hash record per file** (Decision part 8). The
   sealed manifest and the Phase-0 `protected_file_hashes.json` fixture
   never cover the same file. This also preserves the fixture's own
   convention — it is immutable Phase-0 data, and new coverage is never
   obtained by editing it.
4. **No derived state stored twice.** The report's overall status is
   derived from its components on demand, never stored as an independent
   value that could drift from them (AD-049 part 3).

---

**Alternatives considered.**

- ***Archive Seal replaces `ArchiveVerifier`.*** Rejected. It renames a
  governance abstraction after its first mechanism, invalidates three
  existing references — including AD-030's and
  `RESEARCH_ARCHIVE_MANIFEST.md`'s explicit designation of
  `ArchiveVerifier` as the manifest's future consumer, and §4.4's
  interface table — and leaves Standard §5 completeness with no owner at
  all, since a seal cannot answer it. It would also require edits across
  accepted documents to remove a name that is not wrong, which this
  register's discipline treats as the least acceptable kind of change.
- ***Two peer public components.*** Rejected. Two entry points produce
  two reports and force every caller to decide which one settles "is
  this archive sound" — the duplicate-source-of-truth failure P3 names.
- ***One combined check with one result.*** Rejected. It cannot
  distinguish never-produced from produced-then-modified evidence, and
  it forces a two-valued outcome where the platform has consistently
  chosen three (AD-047, AD-051, AD-056).
- ***Extend `FreezeVerifier` to cover archive content.*** Rejected. It
  verifies a different subject (repository vs. archive) with a different
  stability property (time-varying vs. fixed), and AD-059 freezes that
  module's role, with AD-060 recorded as the single scoped amendment
  ever made to it. A second, broader amendment for an unrelated subject
  is exactly what that discipline exists to prevent.
- ***Reuse `tests/fixtures/protected_file_hashes.json` for closed
  cycles.*** Rejected as the architecture, though it remains available
  as R-4's *interim* action on its own terms. It is a one-time pre-Phase-0
  snapshot, immutable by its own docstring; it is a test fixture, making
  a governance control CI-owned rather than Governance-owned; and
  extending it to files a seal also covers would violate Decision part 8.
- ***`verify_archive(project_id: ProjectId)` exactly as §4.4 sketches
  it.*** Deferred rather than rejected — see *Compatibility*, conflict
  **C-1**.
- ***Defer the whole area under a §8 time-boxed exception.*** Rejected
  as the primary path, since R-3's gating condition arrives before the
  next cycle's Phase 8 and Phase 8 is where the missing check is
  needed. It remains R-3's own permitted fallback if implementation does
  not follow this acceptance in time, and this AD's *Status* section
  makes that fallback explicit rather than implicit.

---

**Consequences.**

*Gained.* Standard §2 Phase 8's completeness requirement acquires a
mechanical instrument for the first time (P1). A closed cycle's content
integrity becomes answerable by a Governance-owned control rather than
only by a repository-wide test fixture (P2). `ArchiveVerifier`'s three
existing references become forward-accurate rather than aspirational,
without any of them being edited (P3). The archive manifest gains its
first *read-side* consumer, which is the condition AD-030 anticipated
when it called the manifest "`ArchiveVerifier`'s input contract."

*Costs and disclosed residuals.*

- **This AD adds a second named-but-unimplemented component.** The
  Archive Seal now exists in writing and not in code, which is the exact
  shape of G-3 — the failure mode AD-072 cited by name when it refused
  to name `phase_evidence.highest_review_level_attained` without
  designing it. Two things distinguish this case, and neither is a
  guarantee: the seal is designed here rather than merely mentioned, and
  it is bound to R-3's existing gating condition and to this AD's
  *Status* forward condition. If implementation does not follow, this AD
  becomes the fourth naming site for an unimplemented archive check, and
  the §8 deferral record becomes mandatory rather than optional.
- **`ArchiveVerifier`'s eventual signature will diverge from §4.4's
  sketch** (conflict **C-1**), and that divergence must be recorded at
  implementation time in the same way AD-033 recorded `FreezeVerifier`'s.
- **`core/governance/__init__.py`'s docstring becomes stale on
  implementation** — its "`ArchiveVerifier` … remain[s] unimplemented"
  sentence — and must be updated then, not now. It is accurate at this
  acceptance.
- **Verification is not enforcement.** Nothing in this AD causes
  `ArchiveVerifier` to be *run*. Wiring it into a test suite, a CI step,
  or a Phase 8 checklist is out of scope, so an unrun verifier detects
  nothing — the same distinction the independence linter already
  illustrates (G-6/R-6: implemented, unwired, and therefore never
  executed against `research_archive/`).
- **The live D-9 gap stays live.** This AD does not protect
  `research_archive/reference_h4/`. R-4's interim action remains the only
  thing that closes it today.
- **`reference_h4` cannot be retroactively sealed by any part of this
  AD.** Its archive is immutable per the Phase G decision §8, and a seal
  written into it would itself be the silent edit that decision forbids.

---

**Scope.**

In scope, and only this:

- the decomposition of archive verification into completeness, content
  integrity, and freeze binding;
- the relationship between `ArchiveVerifier` and the Archive Seal
  (abstraction / primitive), and the direction of invocation;
- the responsibility boundaries of all three participants, including
  what each may not do;
- the single-report, per-component-attribution rule and the
  derived-not-stored rule for any overall status;
- the read-only constraint and the absence of any new write authority;
- the one-authoritative-hash-record-per-file rule, and its boundary
  against every pre-existing domain-owned hash mechanism, not only the
  Phase-0 fixture;
- applicability to `lifecycle_version: "v1"` archives — signaled by a
  present manifest carrying that value, gated on the cycle having
  actually closed (`transition_records.jsonl`'s terminal record reaching
  `Archive`) before completeness or the seal run, with an open cycle
  reported `UNVERIFIABLE` on both branches;
- the legacy exemption, restricted to `reference_v1`, `reference_v2_h1`,
  and `reference_h3` by manifest absence, or to any archive whose present
  manifest states `lifecycle_version: "legacy"` — never to manifest
  absence generally;
- the composition rule for a path the Archive Seal and `FreezeVerifier`
  both cover: reported independently, never merged, never given
  precedence.

---

**Non-goals.** Stated as problems this AD deliberately does **not**
solve, so that no reader mistakes acceptance for coverage:

1. **Seal issuance.** Who creates a sealed manifest, when in the
   lifecycle, where it is stored, in what format, and under what write
   authority. Constrained but not decided here: AD-062 governs archive
   write authority, and this AD grants none. Until issuance and its
   manifest format are decided, the seal branch's *comparison* is
   deferred (Migration item 2): the branch exists and runs, but with
   nothing yet to compare against, so it reports `UNVERIFIABLE` for
   every archive, never a stand-in pass and never a failure.
2. **Re-protection of an already-closed cycle** (R-4/G-5/D-9), including
   the `reference_h4` gap that is live today, and including any change to
   `tests/test_repository_integrity_snapshot.py` or its fixture.
3. **CI/test wiring** of `ArchiveVerifier` or of the seal.
4. **Decision-chain verification and anchoring** (AD-065, R-5). Chain
   integrity remains `decision_recorder`'s; whether `ArchiveVerifier`
   should ever invoke it is future work, deliberately not decided here.
5. **Reproduction** (`ReproducibilityChecker`, `run_reproduction()`) and,
   *until 2026-07-26 (see Status, item 16, discharged for dataset
   integrity only)*, **dataset integrity** (`DatasetIntegrityChecker`,
   `dataset_manifest.json` content verification). `ReproducibilityChecker`
   remains a separate §4.4 component, undesigned and unimplemented, and
   is not folded into this architecture. `DatasetIntegrityChecker` is no
   longer a non-goal: it is implemented
   (`core/governance/dataset_integrity.py`) and is folded into this
   architecture as a fourth, always-invoked branch (Status, items 14–15).
6. **Evidence quality.** Whether `methodology.md` is adequate, whether a
   review was substantive, whether a conclusion is sound. Standard §4
   keeps these human; presence and integrity are not adequacy.
7. **Authorization.** No transition floor, no gate, no refusal power.
   AD-072's floors are untouched.
8. **Legacy archives.** `reference_v1`, `reference_v2_h1`, and
   `reference_h3` are not brought under the v1 layout check, are never
   given a retroactive `archive_manifest.json` (AD-030,
   `RESEARCH_ARCHIVE_MANIFEST.md` "Applicability"), and are never sealed
   retroactively.
9. **The Standard §8 exception artifact** (R-2) and the §5-vs-§2 Phase 8
   post-Archive-append question. A separate ADR owns both.
10. **Any change to `FreezeVerifier`, `decision_recorder`,
    `archive_manifest.py`, the import-boundary rules, or the Standard.**

---

**Migration strategy.**

Additive throughout; no existing artifact is rewritten at any step.

1. **On acceptance — nothing changes.** No code, no test, no fixture, no
   archive. All three existing `ArchiveVerifier` references remain
   accurate, because none of them claims it is implemented.
2. **Implementation increment (future), sequenced.** The completeness
   check is buildable today, in full: Standard §5's fixed list and
   `archive_manifest.json`'s applicability contract are both already
   specified (Decision parts 1–8; the completeness bullet and item 5
   below), and nothing in this AD blocks it. The seal primitive's
   *comparison logic* cannot be built before a sealed manifest format
   exists, and that format is Non-goals item 1 — seal issuance,
   deliberately out of scope here. This is not a contradiction between
   this AD's scope and its own migration path: `ArchiveVerifier`
   composes both branches unconditionally from the start, but until a
   manifest format is decided (R-4, *Future work*), the seal branch is
   implemented as a stub that reports `UNVERIFIABLE` for every archive
   it is asked to check — the same outcome item 5 below already assigns
   an already-closed cycle with no seal, generalized here to *every*
   archive for as long as no seal format exists anywhere. `FreezeVerifier`
   is invoked unmodified. Governance's existing dependency rule is
   preserved: no import of Research, Validation, or Reporting, so
   `tools/check_import_boundaries.py` needs no change — if any proposed
   implementation would need one, that is a signal the decomposition is
   wrong, not that the linter is.
3. **Documentation at implementation time.** One docstring sentence in
   `core/governance/__init__.py` is updated; `RESEARCH_ARCHIVE_MANIFEST.md`
   and AD-030's forward references become descriptions of something that
   exists, requiring no edit; the signature divergence from §4.4 is
   recorded in the implementing module's docstring, following AD-033's
   pattern exactly.
4. **Manifest tooling stays where it is.** AD-039 defers moving
   `tools/archive_manifest.py` into `core/governance/` until
   "`ArchiveVerifier` exists and needs it as an input contract."
   `ArchiveVerifier` reading a manifest does not require the module to
   move: reading is not writing, and `write_manifest()`'s legacy-archive
   guards belong where they are. The smallest compatible outcome is to
   leave the module in `tools/` and revisit only if a *write*-side need
   ever appears (conflict **C-2**).
5. **Legacy and closed cycles.** Legacy archives are reported exempt,
   never failing. Already-closed v1 cycles with no seal report the seal
   branch as `UNVERIFIABLE` — accurately, because no seal exists to check
   against — and never as verified or as failed. Until item 2's stub
   period ends, this is every v1 cycle, not only ones that individually
   lack a seal; once a manifest format exists and sealing begins, the
   same rule continues to apply per-archive, to whichever archives
   individually still have no seal. Sealing them, if it ever happens, is
   R-4's decision, not this one.

---

**Acceptance criteria.**

These are the criteria a reviewer applies to any implementation claiming
to satisfy AD-073. They are properties, not tests, and they are
deliberately implementation-neutral:

- **AC-1.** Exactly one public entry point exists for the
  archive-soundness question, and it is `ArchiveVerifier`.
- **AC-2.** `ArchiveVerifier`'s own layer computes no content hash and
  contains no integrity algorithm; every integrity finding originates in
  the seal primitive.
- **AC-3.** *(Amended 2026-07-26 — see Status, item 1; further amended
  2026-07-26 — see Status, item 13.)* The seal primitive performs no
  freeze-claim verification, resolves no freeze commit reference, no
  chain-linkage verification, and makes no Standard §5 completeness
  judgment. It may read git objects at a commit fixed at archive close,
  where both sides of the comparison are archive-local and stable, and it
  never invokes `verify_freeze()`, `verify_chain_intact()`, or
  `verify_chain_anchored()`. It observes no time-varying repository state
  **in the sense that matters**: it may consult `HEAD` for two bounded
  admissibility questions (is the Register record committed; is the
  sealing commit reachable) that can only ever move a result toward
  `UNVERIFIABLE`, never toward a `MATCHED` or `MISMATCH` the comparison
  would not otherwise have reached — the comparison's *result* remains a
  pure function of the sealing commit and the archive bytes alone.
- **AC-4.** Every finding in the report is attributed to exactly one of
  the four branches *(three at this AD's original acceptance — see
  Status, item 15)*, and each branch's own status is individually
  readable from the report.
- **AC-5.** Any overall status is a pure, documented derivation over the
  branch statuses, recomputable by a reader from what the report already
  carries — exactly the *Overall status aggregation rule* in
  *Architecture overview*, with no other derivation permitted.
- **AC-6.** Outcomes are three-valued, never boolean. Absence of evidence
  — no manifest, no seal, no stated freeze claim, an empty covered-path
  set — yields `UNVERIFIABLE`, never a pass. This is AD-051's rule,
  applied unchanged.
- **AC-7.** A missing file, a modified file, and an unexpected file are
  three distinguishable finding kinds, never one.
- **AC-8.** A complete-but-modified archive and a sealed-but-incomplete
  archive each produce a report that names precisely which branch
  failed.
- **AC-9.** No component writes, creates, or mutates anything under
  `research_archive/`. Verified structurally, not by convention.
- **AC-10.** No Governance → Research/Validation/Reporting import is
  introduced; `tools/check_import_boundaries.py` passes unmodified.
- **AC-11.** No file under `research_archive/` is covered by both a
  sealed manifest and `tests/fixtures/protected_file_hashes.json`, and no
  file under `research_archive/` is covered by both a sealed manifest and
  `dataset_manifest.json`'s `content_hash` field.
- **AC-12.** `core/governance/freeze_verifier.py` is unmodified, and no
  freeze result produced during archive verification is written into any
  `GateRunRecord` or `DecisionRecord`.
- **AC-13.** All three pre-existing `ArchiveVerifier` references are
  still accurate after implementation, with no edit beyond
  `core/governance/__init__.py`'s "unimplemented" sentence.
- **AC-14.** A legacy archive — **one of `reference_v1`,
  `reference_v2_h1`, or `reference_h3` with no `archive_manifest.json`,
  or any archive whose present manifest states `lifecycle_version:
  "legacy"`** — is reported exempt, never failing. Manifest absence in
  any archive outside that named three is **not** legacy; it is reported
  by the completeness branch as a missing required item —
  `archive_manifest.json` under its own AD-030/`RESEARCH_ARCHIVE_MANIFEST.md`
  applicability contract, **not** one of Standard §5's seven — with the
  same failure severity as any missing §5 item, never as exempt.
- **AC-15** *(amended 2026-07-26 — see Status, item 7; the original text
  required the Archive Seal branch to read the terminal record too)*. The
  completeness branch reads `transition_records.jsonl`'s terminal record
  before running. A `lifecycle_version: "v1"` archive whose terminal
  `to_phase` is not `Archive` — including an absent or empty
  `transition_records.jsonl` — reports the completeness branch
  `UNVERIFIABLE`, never failing and never exempt, and therefore reports
  `OverallStatus.UNVERIFIABLE` for the archive under the aggregation
  rule. The Archive Seal branch makes no closure judgement of its own; it
  answers only whether the archive's tree matches the sealing commit
  named by the Register. `transition_records.jsonl` is a working-tree
  file, and the Seal's inputs are all fixed at the sealing commit.
- **AC-16.** A freeze branch exists exactly when the caller requested
  freeze verification, and then always. Where it exists, both
  `verify_freeze()` inputs come from the same record: `transition_records.jsonl`'s terminal
  record's `freeze_commit_ref` (the commit) and `freeze_covered_paths`
  (the paths), both read as plain data, optionally via `decision_recorder`'s
  `read_chain()` structural reader, but never by calling `verify_chain_intact()` or
  `verify_chain_anchored()`, and never sourced from anywhere else. An
  absent file, an empty file, or a terminal record with no
  `freeze_commit_ref` yields `UNVERIFIABLE` under AC-6; a terminal
  record with `freeze_commit_ref` but an empty `freeze_covered_paths`
  also yields `UNVERIFIABLE`, under AD-051's existing empty-`covered_paths`
  rule, not a new one.
- **AC-17.** A path covered by both the Archive Seal and a
  `FreezeVerifier` `covered_paths` entry produces two independently
  attributed findings, never a merged verdict and never one taking
  precedence over the other.

---

**Future work.** Named without being designed, and none of it authorized
by this AD:

- **R-4** — seal issuance and the re-protection path for a closed cycle;
  the natural place to decide whether a sealed manifest is the substrate
  R-4's "append-only closed-cycle hash fixture" candidate describes.
- **R-5/AD-065** — chain anchoring, and with it the question of whether
  `ArchiveVerifier` should ever invoke `verify_chain_intact()` /
  `verify_chain_anchored()` as a further branch *("fourth branch" at this
  AD's original acceptance; the Dataset Integrity branch now occupies
  that position — Status, items 14–15 — so chain anchoring, if ever
  added, would be a fifth)*.
- **`ReproducibilityChecker`** as a possible further branch, requiring its
  own decision about whether orchestration or independence serves the
  auditor better. *(`DatasetIntegrityChecker`'s identical question is
  resolved — orchestration — at Status, item 14; it is no longer future
  work.)*
- **A `ProjectId`-keyed wrapper** once `core/research/`'s registry can
  resolve an identifier to an archive location, following AD-033's stated
  path: a thin resolver in front of an unchanged function, not a rewrite.
- **Standard revision (R-7 window, v1.2)** — citing `ArchiveVerifier` by
  name as Phase 8's instrument, once it exists.
- **Wiring** — the decision to *run* archive verification as a standing
  check, alongside R-6's identical open question for the independence
  linter.

---

**Compatibility with existing decisions.**

Two genuine conflicts, each with the smallest compatible adjustment
rather than a breaking change:

***C-1 — `PLATFORM_ARCHITECTURE_V1.md` §4.4's sketched signature.*** The
sketch is `verify_archive(self, project_id: ProjectId) ->
ArchiveCompletenessReport`. Resolving a `ProjectId` to an archive
location requires Research's `ProjectRegistry`, and Governance may never
import Research (§4.4's own rule, enforced by
`tools/check_import_boundaries.py`). *Smallest adjustment:* the
interface takes what the caller already holds — the archive location —
exactly as AD-033 resolved the identical tension for
`FreezeVerifier.verify_freeze(freeze_id)`, and for the identical reason.
This is a documented scope reduction of a sketch, not a change to any
accepted rule; §4.4's text stays as the forward interface, and the
divergence is disclosed at implementation time. The sketch's return type
name (`ArchiveCompletenessReport`) is likewise not binding: this AD's
report spans three branches, of which completeness is one, and naming is
left to implementation.

***C-2 — AD-039's move trigger.*** AD-039 defers moving
`tools/archive_manifest.py` into `core/governance/` until
"`ArchiveVerifier` exists and needs it as an input contract." That
condition is now foreseeable. *Smallest adjustment:* it is not
triggered by *reading*. `ArchiveVerifier` consuming
`archive_manifest.json` requires no relocation of the module that
*writes* it, and `write_manifest()`'s legacy-archive guards are exactly
where AD-030 wanted them. AD-039 is neither reopened nor amended; its
trigger is simply not met by this AD.

One near-conflict, resolved rather than merely noted:

***AD-049 part 3 — "Validation never aggregates."*** A "single validation
report" reads, at a glance, like the aggregate AD-049 forbids. It is not.
AD-049 assigns *gate-outcome* aggregation to Research by name, and an
archive report contains no gate outcomes, produces no `sequence_status`,
and never reaches a `DecisionRecord`. What this AD does adopt from AD-049
is its discipline: per-component statuses stored, any overall status
derived under a documented rule (Decision part 6). The name "validation
report" is used in this AD's prose in its plain sense — the output of a
verification run — and must not be implemented as, or converted into, a
`core/validation/` type.

The remainder, each verified as untouched:

- **AD-005** — no new generic abstraction: one public component with a
  named consumer (Standard §2 Phase 8, R-3), one primitive with exactly
  one consumer. The refusal to promote the seal to a peer abstraction is
  this rule applied, not waived.
- **AD-030 / `RESEARCH_ARCHIVE_MANIFEST.md`** — the manifest remains an
  early preservation guard, and this AD makes it the input contract
  AD-030 predicted, without changing its schema or its applicability
  carve-out for the three legacy archives.
- **AD-033 / AD-047 / AD-051 / AD-060** — `FreezeVerifier`'s semantics,
  scope-boundedness, `UNVERIFIABLE` rule, and `covered_paths` field are
  unchanged; this AD adds a caller and inherits AC-6 from AD-051.
- **AD-059** — the lifecycle remains the sole Validation + Governance
  composition boundary. `ArchiveVerifier` composes Governance components
  only, never a `GateRunRecord`, and never runs inside
  `compose_transition()`. Step 4's "`verify_freeze` is never called
  again during composition" is untouched, because archive verification
  is not composition.
- **AD-062** — no new writer of any artifact. The single-writer rule is
  neither extended nor reopened; seal issuance is deferred precisely so
  that it is not silently amended here.
- **AD-063** — no new Decision Chain authority. Neither component binds
  a `GateRunRecord` to a `DecisionRecord`, verifies chain linkage, or
  writes chain state; enumerations (a) and (b) are untouched and remain
  scoped to Phase F modules, which neither component is. `ArchiveVerifier`
  reading `transition_records.jsonl`'s terminal record (selected by
  highest `sequence_number`) for `to_phase`, `freeze_commit_ref`, and
  `freeze_covered_paths` — optionally by calling `decision_recorder`'s
  `read_chain()`, a structural reader, never `verify_chain_intact()` or
  `verify_chain_anchored()` — is a plain read of already-archived data,
  on par with reading `archive_manifest.json`: it is not chain
  verification, and naming `read_chain()` is not naming a chain
  *verification* authority.
- **AD-066 / AD-067** — no registry of who may call anything, and no
  runtime policy check. The applicability rule this AD does state
  (`lifecycle_version` → which checks apply) is data already recorded in
  the manifest, of the same kind AD-072 defended as a value check over a
  recorded field.
- **AD-072** — lifecycle floors unchanged. Its Phase 8 row — an in-phase
  completeness check on a terminal phase, out of mechanical
  transition-enforcement scope — is precisely the row this AD gives a
  mechanism to, without turning it into a transition check.
- **Standard §5 and the Phase G §8 immutability determination** — no
  archived file is edited, added to, or reinterpreted. Verification is
  read-only by Decision part 7.

No existing invariant is weakened by this AD.

---

**Adversarial self-review.**

*What assumption could still be wrong?* That Standard §5's seven items
are mechanically checkable as *presence and kind* without drifting into
content judgment. The rule stated in *Responsibilities* removes the drift
path by construction — existence plus object kind, uniform across all
eight items, empty objects passing — but §5 also states content
requirements ("one file per review event,"
"every file is dated in its own content or filename") that a future
implementer could read as in-scope. They are not: presence is
mechanical, adequacy is Standard §4's human question, and an
implementation that starts parsing dates out of filenames has crossed a
line this AD draws but cannot enforce.

*What future implementation mistake could this ADR accidentally allow?*
Treating "thin orchestration layer" as license to let a branch's failure
short-circuit the others — running completeness, failing, and never
invoking the seal. The report would then be silently partial, and a
reader could not distinguish "integrity was checked and held" from
"integrity was never checked." AC-4 and AC-6 are written to catch this:
an invoked branch that reached no verdict is `UNVERIFIABLE`, reported as
such, never omitted and never inferred. The one branch that may
legitimately be absent rather than `UNVERIFIABLE` is a freeze branch the
caller never requested — the *Overall status aggregation rule*'s single
stated exclusion, and no other branch may be dropped from a report for
any reason.

*Does this AD create a second source of truth about archive soundness?*
No, by construction: one public entry point (AC-1), one owner per
question, one authoritative hash record per file (AC-11), and no stored
aggregate (AC-5). The residual risk is not architectural but
operational — if R-4 closes by extending the Phase-0 fixture over files a
seal later covers, AC-11 is violated by sequence rather than by design.
That is a real coupling between this AD and R-4, and it is disclosed here
rather than resolved: whichever lands second inherits the obligation to
check.

*Is accepting this AD a way of appearing to close G-3 without closing
it?* That is the sharpest objection available, and it is the reason the
*Status* section states the forward condition in R-3's own words. A
design is not an implementation; R-3's gating condition is unchanged;
and if the next cycle reaches Phase 8 with neither an implementation nor
a §8 deferral record, this document will have made the register longer
without making the archive safer.

---

### AD-074: The Archive Seal is a witnessed commit reference, verified by tree comparison (accepted 2026-07-26, after implementation)

**Review basis.** Level 2 (AI-assisted adversarial review), across four
sequential passes over the same material, each re-verified against
`core/governance/archive_verifier.py`, `freeze_verifier.py`,
`decision_recorder.py`, `dataset_manifest.py`, `tools/archive_manifest.py`,
`tests/test_repository_integrity_snapshot.py`,
`tests/fixtures/protected_file_hashes.json`,
AD-030/AD-033/AD-047/AD-051/AD-060/AD-062/AD-063/AD-065/AD-072/AD-073, and
`docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md` §§4/5/8/10: the design
review itself, an accept-with-conditions review of it, a governance
hardening pass conducted against the *shipped*
`core/governance/archive_seal.py` rather than against the design, and an
acceptance audit of that hardening pass. The four passes are recorded in
`docs/AD_074_ARCHIVE_SEAL_DESIGN_REVIEW.md` as, respectively, §§1–12,
§7/§7A, §7B D7–D12, and §7B's RF-1/RF-2/F-3 amendments.

**Level 3 is unavailable and no Level 3 review was performed. No review
of AD-074 is independent, and none may be cited as such** (Standard §4:
"no document may describe a Level 2 review using the unqualified word
'independent'"). This applies to the fourth pass in particular: AD-073's
2026-07-26 amendment block above introduces it as "the **independent**
audit of the hardening pass," and that word is used there in the narrow
sense of *a separate pass over the implementing pass's output* — it
asserts no organizational independence, no distinct accountable party,
and no external reviewer, because none existed. AD-074 does not inherit
that word, and the phrasing in the block above is disclosed here rather
than rewritten, per this register's own no-silent-supersession rule.

**Acceptance basis.** This entry accepts
`docs/AD_074_ARCHIVE_SEAL_DESIGN_REVIEW.md` — its §5 contract, §8
acceptance criteria AC-74-1…AC-74-13, and §7's four amendments to AD-073,
all of which are already applied inline in this document — as an
architecture decision of this register.

It is recorded **after** the implementation it accepts, and says so
rather than presenting a tidier sequence. The design review's §11
sequences the work as three separately-approvable increments; what
actually happened is:

| Increment | §11's plan | What occurred |
|---|---|---|
| 1 — accept AD-074 + the AD-073 amendment, documentation only | first | **Performed by this entry, 2026-07-26.** The AD-073 amendments it names were applied inside `2392de2`; the AD-074 register entry itself was never written until now. |
| 2 — implement the Seal branch and the Register reader, Register empty | second | **Done at `2392de2`** (`feat(governance): implement AD-074 archive seal hardening`), corrected documentation-only at `a8f031b` (`docs(governance): clarify AD-074 hardening references and register limits`). |
| 3 — issue `reference_h4`'s seal and wire the check | third | **Not started.** `docs/archive_seal_register.jsonl` is empty (0 bytes) [verified]. |

Three things this acceptance therefore does **not** claim, stated
explicitly because each is the kind of claim an ordered register invites
a later reader to assume:

1. **It does not claim Increment 1 happened before Increment 2.** It did
   not. The implementation landed first, the register entry second, and
   the gap between them is the defect this entry repairs — not a
   sequence it retroactively asserts.
2. **It does not claim a Level 3 or independent review.** See *Review
   basis*.
3. **It does not close R-4.** §11 is explicit that only Increment 3 does.
   D-9/G-5 stay live, `reference_h4` stays unprotected by any seal, and
   no archive can report `SOUND` while the Register is empty.

**Numbering.** AD-070 and AD-071 remain unconsumed, for the reason AD-072
and AD-073 both record: per `docs/PHASE_F_PRE_IMPLEMENTATION_AMENDMENT_PLAN.md`
§8 they are the named (not formally reserved) candidates Track C's own
commit C0 may claim for Golden Run 001. This AD takes AD-074, the next
number after AD-073, and claims neither. No AD number is reserved by this
entry for any future work, including the Register self-integrity gap
(design review §9 item 9), which is recorded there as unassigned.

**Status.** **Accepted, 2026-07-26.** This entry is documentation only:
no code, test, fixture, archive, or protected-file snapshot is changed by
it, and `docs/archive_seal_register.jsonl` is neither written nor
populated. The implementation it accepts already exists, at `2392de2` and
`a8f031b`, and is unmodified by this acceptance.

**Decision.** A **sealed archive** is one for which a **sealing commit**
has been recorded in the **Archive Seal Register**
(`docs/archive_seal_register.jsonl`, canonical JSONL, append-only, one
record per issuance). `ArchiveVerifier`'s Seal branch verifies that every
in-scope file under the archive's working-tree directory is identical to
the same path at that commit, and that the two path sets agree. In the
design review's terms, the Seal is a *witnessed commit reference* (the
Register) plus *tree comparison against it* (the mechanism) — §4's
candidates (c) and (d), which compose rather than compete.

The load-bearing parts, each stated so that this entry is readable
without the design review:

1. **Subject.** `research_archive/<project_id>/**`, minus that archive's
   `dataset_manifest.json` `snapshot_path` set and the
   `protected_file_hashes.json` key set — **both read at the sealing
   commit**, never the working tree, so the seal's own scope is a
   property of that commit and of nothing else (§7B D2, D9). Excluded
   paths' *existence* is still checked (AC-74-4).
2. **Comparison.** Blob identities — `git rev-parse <commit>:<path>`
   against `git hash-object --path <path> -- <file>` — never `git diff`
   (which routes one side through the index, falsifiable in both
   directions) and never `cat-file blob` against raw working-tree bytes
   (which applies no filters). Path enumeration is NUL-delimited (§7B
   D4).
3. **Fixed reference.** `sealed_commit` is a full-length lowercase
   hexadecimal object id, validated syntactically before resolution and
   round-tripped against the resolved id; a symbolic ref, a tag, or an
   abbreviated hash is `UNVERIFIABLE` (§7B D11, AC-74-5b). **Ancestry
   relative to `HEAD` is required** *(reversed 2026-07-26, post-AD-075
   governance hardening pass — design review §7A, "B-1 reversed"; this
   bullet previously read "is not checked," on the premise that an
   unreachable commit was already `UNVERIFIABLE` under D3's resolution
   step. That premise is withdrawn: `git commit-tree` mints a commit
   object that resolves identically to a real, referenced one while
   being reachable from no ref, so resolution alone does not prove
   history membership.)* — checked via
   `git merge-base --is-ancestor <sealed_commit> HEAD`: not-an-ancestor
   is `UNVERIFIABLE`, an undetermined answer is `UNVERIFIABLE`, and
   either way `HEAD`'s position still cannot turn an
   `UNVERIFIABLE`/`MISMATCH` result into `MATCHED` or the reverse — the
   seal's result remains a function of the sealing commit and the
   archive bytes alone, which is the property `HEAD`'s time-varying
   position must not affect, restated rather than abandoned (§7A B-1).
4. **Third input, pinned.** The git attribute stack governs *how* the
   bytes are hashed and is therefore an input to the result alongside the
   commit and the bytes. All five influences are neutralised: system
   attributes (`GIT_ATTR_NOSYSTEM=1`), global (`-c core.attributesFile=`),
   `$GIT_COMMON_DIR/info/attributes` (refused — `UNVERIFIABLE`, since git
   offers no way to disable it), working-tree `.gitattributes` (verified
   blob-for-blob against the sealing commit), and `attr.tree` /
   `GIT_ATTR_SOURCE` source selection (`-c attr.tree=` **and** the
   environment variable removed, since it overrides the config). A
   `filter` attribute on a compared path is refused outright, its `clean`
   driver being arbitrary code configured outside every artifact this
   design verifies (§7B D7, AC-74-5a).
5. **Shape refusals.** Symlinks, gitlinks, and — on Windows — NTFS
   junctions and other reparse points are refused rather than followed
   (§7B D8 and its F-3 follow-up).
6. **Vocabulary and boundary.** The Seal reports `MATCHED` /
   `MISMATCH` (findings `modified`, `missing`, `unexpected`, never
   collapsed) / `UNVERIFIABLE`, distinct from `FreezeStatus`'s values.
   It makes no closure judgement (AD-073 AC-15 as amended, item 7 above),
   enters no gate or decision record (AC-74-10), writes nothing under
   `research_archive/` (AC-74-7), and defeats accidental mutation,
   committed edits, additions, and deletions — **not** history rewrite
   and not loss of the repository (§5.2, AC-74-12).
7. **Issuance is a recorded human act**, performed after the Decision →
   Archive record is committed, and mechanised by nothing (§5.3, §9 item
   3). Supersession is attributable, not preventable: a re-seal is a new
   record naming its `supersedes` predecessor, the latest record by file
   order governs, and the prior record stays readable (§5.5 C-2,
   AC-74-6).

**Relationship to AD-073.** AD-074 answers the question AD-073 named and
deliberately declined to design — Non-goals item 1, seal issuance: format,
author, location, write authority. It is *subordinate* to AD-073, not a
replacement: AD-073 remains the architecture (three branches, one entry
point, one owner per question, one authoritative hash record per file),
and AD-074 fills the one hole that made the Seal branch a permanent stub
and `OverallStatus.SOUND` structurally unreachable.

Four amendments to AD-073's accepted text were required, and all four are
already applied inline above, in the "Amended, 2026-07-26" block (items
1–6) — the Responsibilities git-access bar, Decision part 5, the Status
vocabulary and Architecture overview's "sealed manifest", and A8-C1's
first platform-level machine-artifact exception at **A8-C12**. A fifth,
AC-15 (items 7–8), and the trust-model corrections RF-1/RF-2/F-3 (items
9–12) followed from the Increment 2 passes. **This acceptance adds no
amendment of its own.** Where the design review's §7 prose and this
document's amended AD-073 text differ, the amended AD-073 text governs,
per §7's own statement.

AD-074 does not reopen AD-062 (the Register is a new artifact class with
one writer, not a second writer of an existing artifact), AD-063 (no
Decision Chain authority), AD-059 (no `compose_transition()`
participation), AD-072 (issuance is not a lifecycle transition and holds
no authorization floor), or AD-030 (`archive_manifest.json`'s schema is
untouched). `tools/check_import_boundaries.py` passes unmodified
(AC-74-8).

**Consequences.**

- `ArchiveVerifier`'s Seal branch is real, so an archive's report can now
  be `UNVERIFIABLE` for a *per-archive* reason ("no seal has been
  issued") instead of a platform-wide one ("no format exists"). This is
  what closes **R-3**'s design-and-implementation pair together with the
  completeness branch (`da9ca34`) and the freeze branch (`414b07e`).
- **R-4 / D-9 remain open**, and this entry must never be cited as
  closing them. They close when Increment 3 issues `reference_h4`'s
  Register record naming `29553b7`, adds the `SOUND` assertion, and drops
  the expired exclusion clauses at
  `tests/test_repository_integrity_snapshot.py`:100–106.

  **Corrected by AD-075, 2026-07-26. The sentence above is retained as
  written rather than rewritten, per this register's own
  no-silent-supersession rule.** Its third clause — *"drops the expired
  exclusion clauses"* — is wrong, and not cosmetically. Dropping them
  returns `research_archive/reference_h4/**` to the gained/lost-files set
  in `tests/test_repository_integrity_snapshot.py`, whose closing
  assertion is `current_files == set(EXPECTED_HASHES)`; that assertion
  then fails unless `tests/fixtures/protected_file_hashes.json` gains a
  key for every archived file. That fixture is immutable Phase-0 data
  (design review §3 S-3, §9 item 7) — and, decisively, its key set is
  precisely what the Seal reads *at the sealing commit* as an
  **exclusion** set (§7B D9, hardening item BLOCKER 1). Adding those keys
  would therefore not double-protect the archive; it would remove the
  archive from the Seal's comparison. The clauses are **re-based onto
  Seal authority, not dropped**, and the fixture is not touched. AD-075
  issues the record, performs that re-basing, and makes the
  fixture/Seal boundary a permanent partition rather than a temporary
  exclusion. The first two clauses of the sentence above are correct and
  are discharged by AD-075 unchanged.
- The Archive Seal Register is not protected by the seal it drives, and
  nothing in AD-074 hashes or anchors it (design review §7B D5, §9 item
  9). A committed tamper is visible to `git log`-based review only if a
  human performs that review; an uncommitted working-tree rewrite leaves
  no commit to review at all. Disclosed, unassigned, not closed.
- `DatasetIntegrityChecker` **is no longer unimplemented**
  *(discharged 2026-07-26, post-AD-075 governance hardening pass —
  design review §9 item 6, AD-073 Status items 14–15)*. It is
  implemented at `core/governance/dataset_integrity.py` and orchestrated
  by `ArchiveVerifier` as a fourth, always-invoked branch;
  `dataset_hashes/*.jsonl` is excluded from the Seal's own comparison
  exactly as before (AD-073 Decision part 8), but is no longer covered
  only by a recorded hash that nothing verifies. `OverallStatus.SOUND`
  is narrowed accordingly (AC-74-13, design review §8, as amended).

  *Original bullet, at AD-074's acceptance:* `DatasetIntegrityChecker` is
  still unimplemented, so `dataset_hashes/*.jsonl` remains excluded from
  the seal and covered by a recorded hash that nothing verifies (§9 item
  6). Inherited from AD-073, not widened here.
- The design review's §7C registry is now the authoritative definition of
  the `BLOCKER 1`–`3` and `M-1`/`M-3`–`M-6` labels that appear as inline
  comments in `core/governance/archive_seal.py` and
  `tests/test_governance_archive_verifier.py`; `M-2` is recorded there as
  an unused gap in that numbering, reserved rather than reassigned.

**Rejected alternatives.** Recorded because §7 states the first of them
as a genuine fork the accepting authority had to decide, not a rhetorical
one:

- *Candidate (b) — a second per-file SHA-256 hash fixture, parallel to
  the Phase-0 one (R-4's own named candidate, and §7's stated fallback if
  the AD-073 amendment were refused).* Rejected: it records a second
  expected hash for bytes git already content-addresses, needs an
  issuance component and a write authority, and — decisively — **must be
  re-issued on every legitimate supersession**, so a tamper-evidence
  control would have to be rewritten to stay true. Its one real advantage
  is disclosed rather than dismissed: it survives squash/rebase merges,
  branch deletion plus gc, and shallow clones, all of which make a
  git-anchored seal `UNVERIFIABLE` with no archived byte having changed
  (§7B D3).
- *Candidate (a) — a manifest hash.* Rejected as a category error: a
  hash-of-hashes is an encoding choice inside a design, not the design.
- *Compare the working tree against `HEAD`.* Rejected: detects only
  uncommitted mutation, so a committed edit — threat 2, the one that
  matters — reads as clean.
- *Treat "the archive is in git" as sufficient.* Rejected: it is exactly
  the claim the Phase G decision §8 already refused, "immutable as a
  matter of governance and unprotected as a matter of mechanism."
- *Store the seal inside `research_archive/<project>/`.* Rejected as
  structurally impossible, not merely undesirable: the sealing commit is
  the commit that first contains the complete closed archive, so a record
  naming it cannot exist inside the tree it seals (§3 S-1), and Phase G
  §8 holds that directory immutable (S-2).

**Adversarial self-review.**

*What assumption could still be wrong?* That the sealing commit is
unambiguous. It is, for `reference_h4`, because that archive closed in a
single commit [verified]. A future cycle whose Archive phase spans
several commits has no single "the archive is now complete" commit, and
issuance would pick one by human judgment; `sealed_by` makes that
judgment attributable, which is the most the design can do and less than
mechanical.

*What future implementation mistake could this AD accidentally allow?*
Reading the sealing commit from anywhere other than the Register — from
`HEAD`, from the terminal record's `commit_hash`, or from `git log` over
the archive path. All three look reasonable and §3 S-1 proves the second
is wrong: the terminal record's own `commit_hash` (`8bc3f93`) precedes
the archive-closing commit (`29553b7`) and sees one fewer record, so a
seal keyed to it would report `MISMATCH` on a sound archive.

*Does accepting an AD after its implementation weaken this register?*
Yes, and the honest answer is that it does so in a specific, bounded way:
the acceptance could not have refused the design without also reverting
shipped code, so it carried less optionality than an Increment-1-first
acceptance would have. Two things bound the cost. The implementation was
adversarially audited twice *as shipped* — which an acceptance before
implementation could not have done, and which is what found the attribute
stack, the index-mediated comparison, and the Windows junction hole. And
the sequence is recorded here rather than smoothed over, so the register
shows what happened. The correct lesson is the one §11 already stated and
this cycle did not follow: increments exist to be taken in order, and an
entry like this one is the repair, not the pattern.

*Is accepting AD-074 a way of appearing to close R-4 without closing it?*
That is the sharpest objection available, and it is why *Acceptance
basis* item 3 and *Consequences* both state the negative explicitly. If
Increment 3 never lands, this entry will have made the register longer
without making `reference_h4` any safer — the same failure AD-073
disclosed against itself, repeated here rather than assumed learned.

---

### AD-075: `reference_h4`'s seal is issued, and the Phase-0 fixture / Seal coverage boundary is a permanent partition (accepted 2026-07-26)

**Review basis.** Level 2 (AI-assisted adversarial review), conducted
against `core/governance/archive_seal.py` and
`core/governance/archive_verifier.py` as shipped at `2392de2`/`a8f031b`,
`tests/test_repository_integrity_snapshot.py`,
`tests/fixtures/protected_file_hashes.json`,
`docs/AD_074_ARCHIVE_SEAL_DESIGN_REVIEW.md` §§3, 5.6, 7B D2/D3/D5/D9,
9–11, `docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md` §§4 D-9, 5 G-5,
8, 10 R-4, and AD-030/AD-062/AD-063/AD-072/AD-073/AD-074.

**Level 3 is unavailable and no Level 3 review was performed. No review
of AD-075 is independent, and none may be cited as such** (Standard §4).
Nothing in this entry, in the Register record it authorizes, or in the
tests that accompany it asserts organizational independence, a distinct
accountable party, or an external reviewer, because none exists on this
platform.

**Status.** **Accepted, 2026-07-26.** This entry is documentation only:
it changes no code, no test, no fixture, no archive, and it does not
itself write `docs/archive_seal_register.jsonl`. The issuance it
authorizes lands in the immediately following commit, separately
reviewable and separately revertible, per AD-074 design review §11's
"do not merge the increments."

**Acceptance basis.** This entry accepts AD-074 design review §11's
**Increment 3** — with one correction to its wording, stated below and
recorded rather than silently applied — and issues the first Archive
Seal Register record on this platform.

#### 1. What is issued

Exactly one record, appended to `docs/archive_seal_register.jsonl`:

| Field | Value |
|---|---|
| `schema_version` | `1` |
| `project_id` | `reference_h4` |
| `sealed_commit` | `29553b7e5d96118b3f38ecc4de27362a07a210d1` |
| `sealed_by` | supplied by the repository owner at issuance; a human attribution, never generated |
| `sealed_at` | the UTC instant of issuance |
| `supersedes` | `null` — first seal for this project |

`29553b7` is the commit that first contains the complete closed archive
(`research(h4): record Decision -> Archive transition (cycle complete)`).
It is **not** the terminal transition record's own `commit_hash`
(`8bc3f93`), which precedes it and sees one fewer record — AD-074 design
review §3 S-1 proves that a seal keyed to the latter reports `MISMATCH`
on a sound archive.

**Issuance is a recorded human act and is mechanised by nothing** (AD-074
§5.3, §9 item 3). This AD commissions no issuance tool, no CLI command,
no hook, no CI enforcement, no automatic Register writer, and no
governance gate. The record is appended by a human, `sealed_by` names
that human, and no part of that attribution is derived from a git
identity, a session, or any automated actor.

#### 2. The correction to AD-074's Increment 3 wording

AD-074's *Consequences* (and design review §10's migration-impact row and
§11's Increment 3 paragraph, both annotated in place) state that
Increment 3 **"drops the expired exclusion clauses"** at
`tests/test_repository_integrity_snapshot.py`:100–106. **That clause is
withdrawn as an instruction and retained as history.** It is unsafe on
its own terms:

1. Dropping the clauses returns `research_archive/reference_h4/**` to
   that test's gained/lost-files walk, whose closing assertion is
   `current_files == set(EXPECTED_HASHES)`.
2. The assertion then fails unless `protected_file_hashes.json` gains a
   key for every archived file.
3. That fixture is immutable Phase-0 data by its own docstring, by
   standing convention (a new legitimate file gets a test-code exclusion
   clause, never a fixture edit), and by AD-074's own §3 S-3 and §9 item
   7, which state that it is untouched, unedited, and unextended.
4. **Decisively:** the fixture's key set is what the Seal reads *at the
   sealing commit* as an **exclusion** set (AD-074 §7B D9, hardening item
   `BLOCKER 1`; `archive_seal._protected_file_hashes_exclusion_set`).
   Adding `research_archive/reference_h4/...` keys to it would not
   double-protect those bytes — it would **remove them from the Seal's
   content comparison**, converting the strongest control available into
   silence.

Only the third clause of that sentence is wrong. Issuing the record and
adding the `SOUND` assertion — its first two clauses — are correct and
are discharged here unchanged.

#### 3. The coverage boundary, stated as a partition

`protected_file_hashes.json` and the Archive Seal are **two controls with
two different roots of trust, over two disjoint path sets, and the
disjointness is load-bearing rather than incidental**:

| Control | Root of trust | Covers |
|---|---|---|
| Phase-0 snapshot fixture | a per-file SHA-256 recorded before Phase 0, immutable | the three legacy archives, `research_archive/README.md`, the historical `experiments/*.py` scripts, `maintenance/remediate_h3_invalid_pricebar_rows.py` |
| Archive Seal | a sealing commit named in the Register, git's own content addressing | `research_archive/reference_h4/**`, minus that archive's `dataset_manifest.json` `snapshot_path` set |

Because a fixture key is an exclusion *to the Seal*, an overlap is not
redundancy but a hole. The invariant is therefore stated positively and
asserted by test: **no key of `protected_file_hashes.json` may name a
path under a Seal-covered prefix.** The exclusion clauses in
`tests/test_repository_integrity_snapshot.py` are consequently **re-based
onto Seal authority, not dropped**: they stop being a temporary "until
this cycle reaches Phase 8 Archive" waiver — which D-9 correctly found had
expired — and become a permanent, documented delegation to a control that
now exists.

The delegated set is declared **once**, as
`SEAL_COVERED_ARCHIVE_PREFIXES` in `tests/test_sealed_archive_integrity.py`,
and imported by the snapshot test. One list, one place: a delegation that
could be spelled differently in two files is a delegation that can drift
into a gap.

`assert current_files == set(EXPECTED_HASHES)` is preserved verbatim and
unweakened, and the fixture's SHA-256 logic, the `positive_control_phase3`
rules, and the `maintenance/` rules are untouched.

#### 4. What closes, and what does not

**Closes — for `reference_h4`'s archived bytes only:**

- **D-9** (the protected-file exclusion had expired by its own terms) and
  **G-5** (a closed cycle had no path back into protected status) for
  this archive: `research_archive/reference_h4/**` is now covered by an
  automated control that fails on an edit, an addition, or a deletion.
- **R-4**, on its own terms, for this cycle. Phase G §8's qualification —
  *"immutable as a matter of governance and unprotected as a matter of
  mechanism"* — no longer holds for these bytes. It still holds for
  everything in item 5 below.

`OverallStatus.SOUND` becomes reachable for the first time on a real
archive. It means exactly what AD-074 AC-74-13 says and nothing more: the
completeness check passed and the sealed archive paths match the sealing
commit tree. It does **not** assert dataset-hash verification, research
reproducibility, or experiment validity.

**Does not close:**

1. **R-4b — the unsealed `reference_h4` tooling.** *(Opened by this
   entry.)* `experiments/run_reference_h4_lifecycle.py` and
   `experiments/validate_h4_kurtosis.py` are the cycle's orchestration
   and Phase 5 implementation artifacts. They lie **outside**
   `research_archive/`, so they are outside the Seal's subject (AD-074
   §5.1) and cannot be reached by extending it; and they remain excluded
   from the Phase-0 snapshot, whose fixture may not be extended. They are
   therefore covered by **no automated integrity control today** —
   exactly D-9's finding, surviving for two files after AD-075 closes it
   for sixteen. This is disclosed, bounded, and pinned by test (the
   residual is exactly those two paths, no more), and it is **open and
   unassigned**: no AD number is reserved for it, no increment owns it,
   and nothing schedules it. It must never be reported as closed by this
   entry.
2. **Register self-integrity** (AD-074 §9 item 9). The Archive Seal
   Register is not protected by the seal it drives. Nothing hashes it,
   anchors it, or verifies its own history, and the Seal trusts the
   latest record for a `project_id` at face value. A *committed* tamper is
   visible to `git log -p` review only if a human performs that review,
   which nothing automates; an *uncommitted* working-tree rewrite leaves
   no commit for such a review to reach. Issuing the first record makes
   this gap live in practice rather than only in principle — before this
   entry the Register was empty, so there was nothing to tamper with.
   Disclosed, unassigned, **not closed**.

   **Forward note, 2026-07-26 (post-AD-075 governance hardening pass;
   this item's own text above is retained unchanged, per this register's
   no-silent-supersession rule).** Of the two cases this item names, the
   *second* — an uncommitted working-tree rewrite, which "leaves no
   commit for such a review to reach" — is now closed:
   `archive_seal._committed_register_text()` reads the Register at
   `HEAD` as committed content only, so an uncommitted rewrite has no
   effect on any seal result, neither to grant one nor to revoke one.
   The *first* case is unchanged and remains open: a **committed**
   Register tamper is still visible to `git log -p` / `git blame` only
   if a human actually performs that review, which nothing here
   automates. This item is therefore half-closed, not closed, and must
   not be cited as fully closed.
3. **`DatasetIntegrityChecker`** (AD-073 Decision part 8, AD-074 §9 item
   6). Still unimplemented. `reference_h4`'s three
   `dataset_hashes/*.jsonl` files are excluded from the seal's content
   comparison and are covered by a recorded `content_hash` that nothing
   verifies. Their *existence* is checked (AC-74-4). Inherited, not
   widened, and not closed.

   **Forward note, 2026-07-26 (post-AD-075 governance hardening pass;
   this item's own text above is retained unchanged).** `DatasetIntegrityChecker`
   is now implemented at `core/governance/dataset_integrity.py` and
   orchestrated by `ArchiveVerifier` as a fourth, always-invoked branch
   (AD-073 Status items 14–15; AD-074 §9 item 6, discharged). For
   `reference_h4` specifically, its three `dataset_hashes/*.jsonl` files
   are now verified — hash and row count recomputed against
   `dataset_manifest.json` read at sealing commit `29553b7` — every time
   `verify_archive(research_archive/reference_h4)` runs. This item is
   discharged by that later work, not by this entry; AD-075 itself
   implements nothing here (AC-75-14, unaltered, below).
4. **G-5 as a platform-wide defect.** The re-protection *path* now exists
   and has been exercised once. `positive_control_phase3` will still
   reproduce D-9 the moment it closes: issuing its record will be a
   separate human act under this same AD's mechanism, and nothing here
   performs or schedules it.
5. **History rewrite and repository loss** (AD-074 §5.2, §9 item 1,
   §3 S-4). A squash/rebase merge, a force-push dropping `29553b7` from
   every ref, a branch deletion plus `gc`, or a shallow clone all make
   this seal report `UNVERIFIABLE` with no archived byte having changed.
   That is an accurate "cannot currently verify", never a false
   `MISMATCH`, and the accompanying test's failure message says so and
   names the remedies (restore the object, or issue a superseding
   Register record). No same-repo mechanism defeats this ceiling.

#### 5. Acceptance criteria — AC-75-1 … AC-75-15

- **AC-75-1.** Exactly one record is appended to
  `docs/archive_seal_register.jsonl`, for `project_id` `reference_h4`,
  naming `sealed_commit` `29553b7e5d96118b3f38ecc4de27362a07a210d1`, with
  `schema_version` `1` and `supersedes` `null`.
- **AC-75-2.** The Register remains canonical JSONL: UTF-8, LF-only,
  sorted keys, compact separators, exactly one trailing newline, one JSON
  object per line — the form `archive_seal._latest_register_record`
  enforces whole-file (hardening item `M-6`).
- **AC-75-3.** `sealed_by` is an attribution supplied by the repository
  owner. It is not derived from a git identity, not generated by tooling,
  and never attributes the act to an AI session.
- **AC-75-4.** No issuance tooling, CLI command, hook, CI enforcement,
  automatic Register writer, or new governance gate is introduced.
  Issuance remains a recorded human act (AD-074 §9 item 3).
- **AC-75-5.** `verify_archive(research_archive/reference_h4)` reports
  completeness `COMPLETE`, seal `MATCHED`, and overall `SOUND`, asserted
  by a test that never skips, never xfails, and never downgrades the
  failure to a warning.
- **AC-75-6.** That test's failure message names the three environmental
  causes that make a *sound* archive `UNVERIFIABLE` — a shallow clone, a
  sealing commit made unreachable by history rewrite or `gc`, and a
  non-git working tree — and the two remedies: restore the object, or
  issue a superseding Register record. It never presents any of them as
  evidence of tampering (AD-074 §7B D3).
- **AC-75-7.** Exactly one delegation list exists on the platform:
  `SEAL_COVERED_ARCHIVE_PREFIXES`, defined once in
  `tests/test_sealed_archive_integrity.py` and *imported* — never
  re-declared — by `tests/test_repository_integrity_snapshot.py`.
- **AC-75-8.** Fixture/Seal disjointness is asserted by test: no key of
  `protected_file_hashes.json` begins with any delegated prefix.
- **AC-75-9.** `tests/fixtures/protected_file_hashes.json` is not edited,
  extended, regenerated, or reordered.
- **AC-75-10.** `assert current_files == set(EXPECTED_HASHES)` is
  preserved verbatim and unweakened; the SHA-256 fixture logic, the
  `positive_control_phase3` rules, and the `maintenance/` rules are
  unchanged.
- **AC-75-11.** Nothing under `research_archive/` is created, edited,
  moved, or deleted: `git diff 29553b7 -- research_archive/reference_h4`
  is empty (Phase G §8 immutability, AC-74-7).
- **AC-75-12.** `core/governance/archive_seal.py`,
  `core/governance/archive_verifier.py`,
  `core/governance/freeze_verifier.py`,
  `core/governance/decision_recorder.py`, and
  `tools/archive_manifest.py` are unmodified. The only source change is
  one stale docstring sentence in `core/governance/__init__.py`, with no
  behaviour change.
- **AC-75-13.** The unsealed residual is exactly
  `experiments/run_reference_h4_lifecycle.py` and
  `experiments/validate_h4_kurtosis.py` — pinned by test, disclosed as
  **R-4b**, open and unassigned.
- **AC-75-14.** This entry closes R-4/G-5/D-9 for `reference_h4`'s
  archived bytes only. It claims no closure of R-4b, of Register
  self-integrity (AD-074 §9 item 9), or of `DatasetIntegrityChecker`
  (§9 item 6), and it must never be cited as doing so.
- **AC-75-15.** No review of AD-075 is independent and no Level 3 review
  was performed or claimed; the full test suite passes, and
  `tools/check_import_boundaries.py` reports **exactly** the ETF-coupling
  inventory it reported before this change — 5 violations across the
  `data -> etf` and `governance -> etf` edges, the pre-existing AD-068 /
  AD-069 state pinned by `tests/test_import_boundaries.py`'s
  `test_known_etf_coupling_inventory_is_exactly_as_documented` and its
  strict `xfail` on `test_real_repository_has_no_boundary_violations`.
  AD-075 adds no import and creates no new domain edge. *(Stated this way
  rather than as "the check passes" because the standalone script exits
  non-zero on that documented inventory today, before and after this
  work; a criterion asserting otherwise would be false on its face.)*

**Forward note, 2026-07-26 (post-AD-075 governance hardening pass).
AC-75-14's text above is unaltered and remains this entry's own,
historical claim: AD-075 itself closed no more than R-4/G-5/D-9 for
`reference_h4`'s archived bytes, and never claimed to close R-4b,
Register self-integrity, or `DatasetIntegrityChecker`.** A later,
separate pass — recorded at AD-073 Status items 14–17, AD-074 §7A's
"B-1 reversed" and §9 item 6, and the "Does not close" items 2 and 3
above — has since discharged part of what AC-75-14 disclaims: dataset
integrity is implemented and orchestrated (`DatasetIntegrityChecker`,
§9 item 6, fully discharged), and Register self-integrity's *second*
case — an uncommitted working-tree rewrite — is closed, while its
*first* case — a committed tamper, defended only by human `git log -p`
review — remains open. Neither discharge is performed by AD-075, is
backdated onto it, or changes what AC-75-14 says AD-075 itself did;
this note exists so a reader of AC-75-14 in isolation is pointed to the
later record rather than left to assume the disclaimed gaps are still
fully open today.

**Relationship to prior ADs.** AD-075 is subordinate to AD-074 exactly as
AD-074 is subordinate to AD-073: it adds no mechanism, changes no
contract, and amends no accepted text. It performs the one act AD-074
deliberately left to a human, and corrects one instruction in AD-074's
sequencing that could not have been followed as written. AD-062 (the
Register is a new artifact class with one writer), AD-063 (no Decision
Chain authority), AD-059 (no `compose_transition()` participation),
AD-072 (issuance is not a lifecycle transition and carries no
authorization floor), and AD-030 (`archive_manifest.json`'s schema) are
untouched. `tools/check_import_boundaries.py` is itself unmodified and
its result is unchanged by this work — see AC-75-15, which states what
that result actually is rather than repeating AD-074's "passes
unmodified" shorthand.

**Numbering.** AD-070 and AD-071 remain unconsumed, for the reason
AD-072, AD-073, and AD-074 all record. AD-075 reserves no number for
R-4b or for the Register self-integrity gap; both are recorded as
unassigned rather than referred onward to a plan that does not exist.

**Adversarial self-review.**

*What assumption could still be wrong?* That `29553b7` is reachable from
some ref for the lifetime of the archive. It is today [verified], and the
seal's honesty under loss is designed for — `UNVERIFIABLE`, never
`MISMATCH` — but a squash merge of the `reference_h4` branch would break
this seal silently from the operator's point of view: nothing warns at
merge time, and the failure surfaces only the next time the test runs.
That is a real operational hazard of a git-anchored seal, and it is the
one concrete advantage the rejected candidate (b) held (AD-074 *Rejected
alternatives*).

*What does issuing this record make worse?* Register self-integrity. An
empty Register cannot be tampered with; a populated one can, and the Seal
trusts its latest record at face value. AD-075 converts a theoretical gap
into a live one, which is stated here rather than left for a reader to
notice.

*Is re-basing the exclusion clauses a way of appearing to close D-9
without closing it?* It would be, if the clauses stayed while nothing
replaced them — which is precisely what D-9 found. The distinguishing
fact is mechanical, not rhetorical: with the record issued, editing any
file under `research_archive/reference_h4/` now fails
`tests/test_sealed_archive_integrity.py`, and before it, nothing failed.
The two `experiments/` scripts are the part where the objection still
lands, which is why R-4b is opened rather than absorbed into the closure
claim.

---

### AD-077: The governance spine is workload-neutral in semantics; the dataset and reproduction path is not. Each claim is stated separately. (accepted 2026-07-27)

**Relationship to AD-076.** This decision **replaces the withdrawn,
never-accepted AD-076 draft** in `docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md`
§8. It does **not** supersede AD-076, because there is no AD-076 to
supersede: that draft was never appended to
`docs/ARCHITECTURE_DECISIONS.md`, never cited by a test, never
referenced by an accepted decision, and never used to authorize any
item in the cleanup. **AD-076 remains unconsumed** and is not spent by
this decision, by the cleanup record, or by the review that carries it.
"Supersedes AD-076" is the wrong verb and is not used anywhere in this
entry, because superseding a number consumes it. **"Unconsumed" here means
"nothing was decided under it" — it does not mean the number is
available for reuse; see *Numbering* below, which reserves and retires
AD-076 and starts new numbering at AD-078.**

**Review basis.** **Level 1 — self-review.** One reviewer with
repository access, working against the branch `master` working tree at
HEAD `fd7a26c` plus the uncommitted Engine Boundary Cleanup. **Level 3
is unavailable and no Level 3 review was performed. This is not an
independent review, and neither this entry nor the review document that
carries it may be cited as one** (`docs/RESEARCH_GOVERNANCE_STANDARD.md`
§4). Nothing in this entry asserts organizational independence, a
distinct accountable party, or an external reviewer, because none exists
on this platform. This is the same standing AD-068 and AD-069 declare
for their own basis.

**Numbering.** AD-070 and AD-071 remain unconsumed, for the reason
AD-072, AD-073, AD-074, and AD-075 all record.

**AD-076 is reserved and retired. It is not available, and it must not
be described as free, open, or reusable.** The facts and their
consequence, separately:

- **What happened.** AD-076 was **drafted, withdrawn, and never
  appended** to `docs/ARCHITECTURE_DECISIONS.md`. It was never cited by
  a test, never referenced by an accepted decision, and never used to
  authorize any item in the Engine Boundary cleanup. Nothing was decided
  under it (`docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md` §8, §8.1).
- **What that does not imply.** "Nothing was decided under it" does
  **not** make the number recyclable. The number has a public trail: it
  is named in the cleanup record's status table, in §8's withdrawal
  notice, and throughout this review. Re-issuing AD-076 for an unrelated
  decision would give one number two meanings across the written record,
  which is exactly the ambiguity an append-only decision log exists to
  prevent.
- **Where its meaning went.** AD-076's substance is **disclosed and
  mapped into AD-077**, not discarded: §6.1 of the carrying review
  (`docs/ENGINE_NEUTRALITY_ARCHITECTURE_REVIEW_2026-07-27.md`)
  states the three defects that caused the withdrawal, and this entry's
  clauses 1, 2, and 3 carry forward what survived — the two-part
  neutrality claim, the three-class axis (corrected on
  `core/market_data`), and per-rule enforcement (corrected on the
  enforcement gap AD-076 clause 3 admitted). A reader who follows the
  number arrives at this entry.
- **Consequence for numbering.** **New ADR numbering starts from
  AD-078.** AD-076 is retired in place and AD-077 is this entry.

AD-076 is nonetheless **unconsumed in the append sense** and stays that
way: withdrawing it spends nothing, and no step in this review appends
it. "Retired" describes the number; "unconsumed" describes the log.
Neither licenses reuse.

This entry reserves no number for Phase 1.6's reproduction-shim policy,
for Phase 2, or for Phase 3; each is recorded as unassigned rather than
referred onward to a plan that does not exist. Any such number is
allocated at the time the decision is written, from AD-078 upward.

**Status.** **Accepted, 2026-07-27.** Documentation only: no code,
test, tooling, fixture, archive, or CI change.

**Context.** Engine Boundary cleanup C1–C6 discharged the `governance -> etf`
import edge and produced a genuine improvement. It also produced a draft
decision claiming a neutrality the tree does not have. This decision records
what is true, in two parts, so that neither part can be cited as the other.

**Decision.**

**1. The neutrality claim is two claims, and they are stated separately.**

- **1a. The governance spine is workload-neutral in semantics.**
  `archive_identity`, `archive_seal`, `archive_verifier`,
  `canonical_jsonl`, `dataset_integrity`, `decision_recorder`,
  `freeze_verifier`, `independence_linter`, `network_guard`,
  `pinned_worktree`, `reproduction_record`, and all of
  `core/validation`, `core/research`, `core/store`, and
  `core/reporting` contain **no workload fact that reaches behaviour** —
  no **workload schema name** appears in these modules as a constant, a
  dict key, a comparison, a parameter default, or any other control-flow
  input.

  **"Workload schema name" is the load-bearing term and is defined
  here:** a table name, a column name, a domain entity name, or a
  calendar identifier — the vocabulary of a workload's data model.
  Identifiers naming a *particular artifact this platform produced* are
  a different kind and are **not** covered by that term; the one such
  case in this module set is `LEGACY_ARCHIVE_PROJECT_IDS`, disclosed in
  full below rather than left implicit in the word "workload".

  **This is a semantics claim, and it is review-derived.** It was
  established by reading the modules, not by a tool, and **no test
  currently asserts it.** It is not pinned by test, and no statement in
  this decision, in `docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md`, or in
  the review that carries this entry may describe it as pinned,
  enforced, or asserted by test.

  **Lexical mentions exist inside this set and are named here rather
  than rounded away.** The inventory is **five modules at six
  locations**:

  | Location | Form of the mention |
  |---|---|
  | `core/governance/canonical_jsonl.py:2` | dataset names as an illustrative list |
  | `core/governance/reproduction_record.py:33` | dataset names in a field's worked description |
  | `core/governance/dataset_integrity.py:13` | a worked example path (`dataset_hashes/ETF.jsonl`) |
  | `core/store/__init__.py:8` | names what a *neighbouring* module owns |
  | `core/research/execution/experiment.py:8` | **negation** — "domain-blind and carries no ETF-specific logic" |
  | `core/research/execution/experiment.py:51` | **negation** — "No implementation, no ETF-specific logic" |

  Each is prose. None is read by code. The last two are **negations**:
  they state that the module carries *no* ETF-specific logic, so they
  are disclaimers of coupling rather than instances of it, and they are
  listed here only because a lexical scan would return them.

  **Lexical vocabulary presence is not workload semantic coupling.**
  This decision claims the latter and not the former: 1a is a statement
  about what reaches behaviour, and a grep count of the string `ETF`
  neither establishes nor refutes it. Any restatement of 1a as "zero
  occurrences of the string" is a different — and false — claim.

  The enumeration above is the complete known set **at this
  working-tree state**; it is a snapshot, not a guarantee of
  exhaustiveness, and it will go stale as modules change. **This
  decision introduces no lexical scanner and authorizes none.** A future
  decision may propose one; that is a separate AD with its own cost
  argument, and the absence of one here is deliberate, not an oversight.

  **Disclosure — `LEGACY_ARCHIVE_PROJECT_IDS` is a control-flow input
  inside this set, and is named here rather than left for a reader to
  find.** Three of the modules 1a lists do compare against a frozen set
  of literal identifiers:

  | Location | Form |
  |---|---|
  | `core/governance/archive_identity.py:54` | `LEGACY_ARCHIVE_PROJECT_IDS = frozenset({"reference_v1", "reference_v2_h1", "reference_h3"})` |
  | `core/governance/archive_seal.py:1077` | `if identity.project_id in LEGACY_ARCHIVE_PROJECT_IDS` — a legacy archive is never sealed (AC-74-9) |
  | `core/governance/archive_verifier.py:501` | `if manifest is None and archive_dir.name in LEGACY_ARCHIVE_PROJECT_IDS` — exemption from the v1 layout check, reached only when no `archive_manifest.json` is present |

  These are real comparisons and they really do reach behaviour, so
  they are disclosed rather than covered by 1a's "no … comparison"
  phrasing. **They are not a counterexample to 1a**, for a reason that
  is stated rather than assumed: `reference_v1`, `reference_v2_h1`, and
  `reference_h3` are **artifact and research-cycle identifiers — the
  names of three specific archives this platform produced — not
  workload schema vocabulary.** They are not table names, column names,
  entity names, or calendar identifiers; they name *instances*, not a
  *schema*. A second workload's archives get their own identifiers and
  are unaffected by this set, whereas a second workload is refused
  outright by `dataset_manifest`'s `REQUIRED_SOURCE_TABLES` (1b). That
  is the difference 1a and 1b divide on.

  **No artifact classification rule is introduced by this disclosure.**
  It records what the constant is and what it decides. It does not
  define a category of "artifact identifier", does not authorize adding
  to or removing from `LEGACY_ARCHIVE_PROJECT_IDS`, does not rule on
  whether such identifiers belong in engine modules at all, and does not
  create an exemption that a future workload name could be admitted
  under. Should that question need deciding, it is a separate AD.
- **1b. The dataset and reproduction path is workload-bound.**
  `dataset_manifest`, `identity_verification`, `reconstruction_loader`,
  `reproduction_runner`, and `calendar_definitions` encode ETF's table names,
  column names, foreign-key topology, and calendar. A second workload cannot
  produce a governed archive without changing them.

Any statement about this platform's neutrality — in documentation, a release
note, or an external presentation — must name which of 1a and 1b it refers to.
An unqualified claim of "workload-neutral platform" is false while 1b holds.

**2. Three classes, and this is a second axis — not a re-drawing of the
domain map.** The axis has exactly three classes — **Engine**,
**Reference Workload**, and **Artifact** — and they are mutually
exclusive: a module classified under this axis carries exactly one of
them, decided at introduction and stated in its own docstring.
`core/analytics` is Reference Workload. `research_artifacts/`,
`research_archive/`, and `experiments/*.py` are Artifact.

**A namespace this decision does not name is not classified by it.**
The three classes are the only values the axis admits; they are not a
claim that every namespace in the tree has already been assigned one.
Where this decision is silent, the classification is simply not made
here — the deferral of `core/market_data` below is the worked case —
and this entry classifies no such namespace, by implication or
otherwise.

**AD-068's domain mapping is unchanged by this decision.** AD-068
decision 1 maps `core.analytics` to `etf` — that is the mapping AD-068
decision 1 itself makes, and it is the whole of what it makes. The
`core.market_data → data` mapping is not AD-068 decision 1's: it is
the boundary checker's `DOMAIN_OF_TOPLEVEL`
(`tools/check_import_boundaries.py:119`), which predates AD-068 and
which AD-068 did not change. AD-068 decision 3 separately attributes
ETF symbols hosted inside `core.market_data` by the name they bind.
Those mappings, and the `ETF_SYMBOLS_BY_MODULE` mechanism that
implements decision 3, are **untouched here**. AD-077 adds a **second,
orthogonal classification axis**
(Engine / Reference Workload / Artifact) over the same tree; a module
has a domain under AD-068 *and* a class under AD-077, and neither
derives from the other.

**`core/market_data` is not classified by this decision, and the split
is deferred.** Earlier phrasing spoke of "the ETF half of
`core/market_data`" as though that half were a module with a class.
It is not: it is two `data -> etf` violations
(`ingestion/price_ingestion.py:7`, `persistence/repository.py:15`)
inside a package that is otherwise Data, held under a strict `xfail`.
**A package cannot carry two classes, and this decision does not
pretend to assign it one.** Whether `core/market_data` splits, and
where the boundary falls, remains **deferred** —
`docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md` §9.1 defers it until a
second workload exists, and nothing here disturbs that deferral or
pre-decides its outcome. What this decision *does* correct is the
withdrawn AD-076 draft's placement of `core/market_data` in **Engine**,
which the repository's own checker refutes; the correction is that the
package is **not Engine**, not that it is something else.

**3. Enforcement is stated per rule, at the strength it actually has.**

The enforcement facts, stated before the table so they cannot be read
off it too generously:

- `tools/check_import_boundaries.py` **exists** and implements the
  `core/` domain-edge check by symbol attribution (AD-068 decision 3).
- `tests/test_import_boundaries.py` enforces the **pinned coupling
  inventory** (`test_known_etf_coupling_inventory_is_exactly_as_documented`),
  **per-symbol resolution** (`test_every_etf_symbol_resolves_in_its_named_module`),
  the **kernel non-exemption** (`test_no_kernel_module_hosts_an_etf_symbol`),
  and the **empty governance edge**
  (`test_governance_does_not_reach_the_etf_domain`). These are real,
  blocking assertions and they run in the suite.
- **CI invocation is advisory, not blocking.**
  `.github/workflows/governance.yml:92` runs
  `python tools/check_import_boundaries.py || true`. A boundary
  violation introduced today does **not** fail CI through that step.
  The blocking pressure comes from the test suite, not from the CI
  invocation.
- The strict `xfail` on
  `test_real_repository_has_no_boundary_violations`
  (`tests/test_import_boundaries.py:200`, `strict=True`) **remains in
  place** for the two known deferred `data -> etf` violations. It is
  the forcing function AD-068 decision 4 installed: it fails the suite
  if the violations are fixed without removing the marker, and it does
  not mask new violations of other edges, which the inventory test
  catches instead.

**This decision changes no CI configuration and authorizes no CI
change.** The `|| true` is recorded here as a fact about current
enforcement strength, not as a defect this decision repairs.

| Rule | Enforcement, accurately |
|---|---|
| `core/` dependency table | `tools/check_import_boundaries.py` (exists) + suite assertions (blocking); CI step advisory (`\|\| true`) |
| Engine may not import a workload | same checker + `test_governance_does_not_reach_the_etf_domain` (blocking) |
| Known `data -> etf` violations stay visible | strict `xfail`, `strict=True`, unchanged |
| A file may name at most one workload | **not enforced today**; proposed for Phase 1.5, unauthorized by this decision |
| Artifacts may not live under `core/` | **not enforced today** — the checker scans `core/` only, so `core → research_artifacts` is invisible to it; proposed for Phase 1.5, unauthorized by this decision |
| Every module declares its class in its docstring | **review only — unenforced, and this is stated, not implied** |

**4. A workload fact reaches the engine as a value, never as a default —
applying to new and changed engine signatures.** Required tables,
identity-table specs, row parsers, loaders, seed steps, and coverage
providers are supplied by the composition root as parameters with no
default. Precedent: C4's `parse_row`/`load_rows`, adopted here as a
general rule. A default would let a caller who forgot one silently
receive ETF's semantics.

**Scope, stated so this decision does not make the current tree
non-conformant on acceptance.** The rule binds **any engine signature
introduced or modified after this decision is accepted**. It is **not
retroactive**, and accepting it does **not** put the tree in violation
of an accepted decision.

**Known existing non-conformance, recorded rather than discovered
later:**

| Location | Non-conformance |
|---|---|
| `core/governance/reconstruction_loader.py:272` | `reconstruct_database(..., calendar_id: str = "XNYS", ...)` — a workload fact as a parameter **default** in an engine signature |

This is a real instance of exactly what clause 4 forbids going forward,
and it is named so that clause 4 cannot be read as a claim that no such
case exists. **No remediation is authorized by this decision.** It
schedules no fix, sets no deadline, and does not license editing that
signature; the change is proposed in Phase 1 item 1.3, which is not
authorized here (see *What this decision does not do*). Should that
signature be modified for any reason before Phase 1 is authorized, the
rule binds it at that point, because modifying it makes it a changed
signature.

**5. A rename in `core/` is a reproduction-compatibility change.** Because
a pinned commit's scripts resolve `core.*` through HEAD, any public name
removed or renamed in `core/` that is imported by the `experiments/`
script at **the pinned commit named by a cycle's
`reproduction_record.json`** must either (a) keep a permanent shim,
explicitly classified as a reproduction shim and covered by a test
asserting a real pinned importer exists, or (b) have every affected
cycle's reproduction status re-derived and re-recorded. Silent removal
is prohibited.

**The anchor is the reproduction record's commit, not the Archive
Seal.** For `reference_h4` the anchor is
`research_archive/reference_h4/reproduction_record.json`'s
`commit_hash` (`3d586ded…`), which is the commit
`run_reproduction()` checks out into a pinned worktree and whose
scripts therefore do the importing.

**Archive sealing and reproduction compatibility are separate
mechanisms and are not merged by this clause.** The Archive Seal
(AD-074, AD-075) witnesses a *different* commit for a *different*
purpose — it binds archived bytes to a witnessed commit and is verified
by tree comparison — and the Seal's commit is not the reproduction
anchor. Wording that speaks of "the sealed commit" in a reproduction
context conflates the two, and is not used here. A cycle can have a
reproduction anchor and no seal, or a seal and no reproduction anchor;
this clause is triggered by the former alone.

**Retroactive application, already measured.** C1's `ETFId` rename and
C4's deletion of `core.governance.dataset_snapshots` were examined
under this rule before the cleanup was committed, and the measurement
is `docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md` §11.3: 45 distinct
`(module, symbol)` pairs across 20 core modules resolved, 0 unresolved,
and neither removed name is imported by any pinned experiment script.
Branch (a) and branch (b) are therefore both unnecessary for those two
removals. That measurement discharges this clause for C1 and C4; it
does not, by itself, establish the rule, which is what this clause
does.

**6. Neutrality claims expire at one implementation.** No seam with exactly
one implementation may be described as workload-neutral. It may be described
as *parameterized*, which is a different and smaller claim.

**7. Interaction with AD-068, stated explicitly so clause 5 cannot be
read as an escape hatch.**

- **AD-068 decision 3 remains unchanged.** This decision does not
  amend, weaken, reinterpret, or grant an exception to it.
  `ETF_SYMBOLS_BY_MODULE`, symbol attribution, and decision 5's guard
  test continue exactly as accepted.
- **A permanent ETF alias or reproduction shim created under clause 5
  does not bypass AD-068 decision 3's termination logic.** If such a
  shim binds an ETF-specific name in an asset-class-neutral module, it
  is an ETF symbol in that module and belongs in
  `ETF_SYMBOLS_BY_MODULE` like any other — clause 5 supplies a *reason*
  for a symbol to persist, never a reason for it to be invisible to the
  checker. Decision 3's termination condition is that symbol
  attribution ends when the mapping **empties**; a permanent shim that
  is exempted from the mapping would make it appear to empty while the
  coupling persists, which is precisely the false-success shape AD-068
  decision 5 exists to catch.
- **Conflict is possible and is not resolved here.** A permanent shim
  that must never be removed and a mapping that must eventually empty
  are in tension. **Any actual conflict requires a separate AD**,
  argued on its own terms, with its own number allocated at that time.
  This decision neither pre-authorizes that resolution nor reserves a
  number for it, and **AD-068 is not amended by this entry.** Until
  such an AD exists, clause 5's branch (a) may not be exercised in a
  way that would remove an entry from `ETF_SYMBOLS_BY_MODULE`.

**What this decision does not do.** It creates no registry, no plugin
system, no dependency-injection container, and no dynamic discovery.

**It authorizes no implementation work of any kind, and no module
moves.** Concretely: it authorizes no Phase 1 item (1.1 through 1.6),
no Phase 2 work, and no Phase 3 work. It moves no module, relocates no
constant, changes no signature, adds no test, and modifies no CI
configuration. The phase plan in §5 of
`docs/ENGINE_NEUTRALITY_ARCHITECTURE_REVIEW_2026-07-27.md`, the review
that carries this entry, is a **proposal**, not a grant of authority;
where this entry names a Phase 1 item it does so to identify a
proposal, never to approve it. Earlier phrasing of this paragraph excepted "those Phase 1
names" from the no-moves rule — that exception is **removed**, because
it made an authorization out of a cross-reference. Each phase requires
its own authorization, recorded separately.

**Known weakness, stated rather than discovered later.** Four things in
this decision are held by reading alone: **clause 1a's semantics claim**
(no test asserts it), **clause 2's docstring rule**, and **clause 3's
last three rows** (one-workload-per-file, artifacts-outside-`core/`,
and the docstring declaration). A fifth is weaker than it looks:
clause 3's first row is enforced by the suite but **not** by the CI
step, which is advisory. And this repository has no independent
reviewer (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4 — Level 3
unavailable; see *Review basis*). The honest claim is that this
decision makes drift *nameable in review*, not that it prevents drift.

---

### AD-078: The dependency boundary is stated per top-level namespace, at the strength each namespace is enforced (accepted 2026-07-28)

#### Review basis

**Level 1 — self-review.** One reviewer with repository access, working against branch `master` plus the uncommitted dependency-boundary checker and test changes to `tools/check_import_boundaries.py` and `tests/test_import_boundaries.py`.

**Level 3 is unavailable and no Level 3 review was performed. This is not an independent review, and neither this entry nor the review documents that carry it may be cited as one** (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4). Nothing here asserts organizational independence or a distinct accountable party, because neither exists on this platform. This is the same standing AD-068, AD-069, and AD-077 declare for their own basis.

**Numbering.** AD-078 is the next number, per AD-077's *Numbering* section: AD-070 and AD-071 remain unconsumed, AD-076 is reserved and retired, and new numbering starts at AD-078.

**Acceptance.** This entry records acceptance only against commit `a38089ae4f4bb1d7cb057e9f3fe04e5d91d2317b`, the commit carrying the dependency-boundary checker and test changes described below. Acceptance against a working tree is not acceptance: the tooling this entry describes was uncommitted when the entry was drafted, and the named commit is what fixes the state the entry speaks about.

---

#### Context

AD-005 records two rules in one entry:

1. **A dependency rule** — "the entire codebase is Python standard library only."
2. **An abstraction rule** — no ORM, no dependency-injection container, no `UnitOfWork`, no event bus, no CQRS, no generic repository base class; the fix for a multi-write transaction is the `with conn:` boundary (AD-001), not a new abstraction.

**AD-005 is not edited. It remains in the decision log exactly as accepted. The split between dependency wording and abstraction wording below is AD-078's reading for AD-078's own scope; it is not a restatement, amendment, or replacement of AD-005.**

The two rules are independent. The later entries listed here — AD-025, AD-028, AD-040, AD-044, and the Step 9 and Phase F resolutions — cite AD-005 for **abstraction** restraint. That list is illustrative and not exhaustive. **AD-005 is also cited elsewhere in this log for dependency-related reasoning** — AD-016 refuses `requests` and `yfinance` on it, and AD-021 rests its rejection of a `CalculationEnvironment` concept partly on the codebase having zero external numerical dependencies. That the same entry is cited on two different axes is part of why this entry records its own namespace-scoped dependency boundary rather than relying on a citation trail to disambiguate them.

**This entry states a dependency boundary of its own, per namespace.** AD-005's abstraction rule is unchanged, unweakened, and remains the authority it already is.

AD-005's dependency sentence is written at whole-codebase scope. Two namespaces carry documented non-standard-library imports: `pytest` in `tests/`, and `exchange_calendars` in one `experiments/` setup utility. **Each is documented in an accepted decision or in its own module documentation, and neither was undisclosed** — AD-068 decision 4 states that AD-005 is unaffected because pytest is the runner, not a framework added to the platform; `experiments/seed_trading_calendar.py`'s own module docstring, and Phase 4 Architecture Amendment v1.0 §A.2.1, record the other. What was absent was a single place stating the boundary **per namespace**, at the strength each namespace is actually held to.

The dependency-boundary checker and test changes supplied the missing half of that: `core/`'s dependency boundary is now measured by a checker rule and asserted by a blocking test rather than held in prose. This decision records the boundary that enforcement establishes, and records — as separate columns — what is merely measured and what is merely written down.

---

#### Decision

##### 1. The dependency policy is keyed by top-level namespace, and by nothing else

This is a **third classification axis** over the same tree.

- It is **not** keyed by AD-068's domains. `check_dependency_purity` does not consult `DOMAIN_OF_TOPLEVEL`, and this decision does not either.
- It is **not** keyed by AD-077's Engine / Reference Workload / Artifact classes. AD-077 declines to classify `core/market_data`, and nothing here classifies it, by implication or otherwise.
- **A package under `core/` carries the same dependency rule regardless of which domain it belongs to.** `core/statistics`, `core/governance`, `core/store`, and `core/shared` are held identically. No per-domain dependency grant, exemption, or gradation is created.

A namespace this decision does not name is not classified by it.

**Terminology.** "Purity" in this entry always means **dependency purity** — whether an imported top-level name is standard library or repository-local. AD-069 uses "purity" for a different property: I/O purity, the ground on which `statistics -> store` is refused. The two rules are unrelated and the collision is disclosed rather than resolved.

##### 2. Scope table — measured state, decided rule, and enforcement are separate columns

| Namespace | Measured at this commit (fact) | Rule decided here (normative) | Enforcement today |
|---|---|---|---|
| `core/` | imports `core` and standard library only | **No third-party dependency. No non-`core` repository-local import.** | third-party: checker rule + blocking test; sibling-local: **tripwire test only** (see 3) |
| `adapters/` | imports `core`, `adapters` only | **None decided here.** No permission granted | none — `check_repository` does not scan `adapters/` (the tool currently operates on the core tree only) |
| `tools/` | imports `core` only | **None decided here.** No permission granted | none |
| `maintenance/` | imports `core` only | **None decided here.** No permission granted | none |
| `research_artifacts/` | imports `core` only | **None decided here.** No permission granted | none |
| `experiments/` | imports `core`, `experiments`, and `exchange_calendars` in one file | **None decided here.** See 4 | none |
| `tests/` | imports `pytest` (61 files) and repository-local packages | **None decided here.** `pytest` is the test runner, per AD-068 decision 4 | none — CI installs `pytest` only |
| `migrations/` | contains no Python | **Not applicable** — a dependency rule over SQL files would be vacuous | n/a (AD-004 governs it) |
| `workloads/` | does not exist | see 5 | n/a |

"None decided here" means exactly that: this decision states the measured fact and **grants no permission and imposes no new prohibition**. A third-party import in one of those namespaces would be governed by whatever decision introduces it, and no such decision exists.

##### 3. `core/`

**Decided rule.** `core/` imports the Python standard library and `core.*` only. No third-party package. No repository-local package other than `core` itself.

**Enforcement, at the strength it has:**

- **Third-party:** `check_dependency_purity` classifies every absolute import under `core/` as standard library, repository-local, or violation, with no fourth bucket; `tests/test_import_boundaries.py::test_real_repository_imports_no_third_party_package` asserts the result is empty. It carries **no `xfail`** and must never acquire one. This is the strongest rule in this entry.
- **Non-`core` repository-local:** enforced by **`test_real_repository_core_imports_no_non_core_repository_local_package` alone.** The checker permits it: `check_dependency_purity` allows any repository-local name, and `check_repository` resolves a domain only for names beginning `core.`. **`python -m tools.check_import_boundaries` reporting no purity failure is therefore a weaker statement than the suite passing, and the two must not be quoted interchangeably.**

**Three properties of the mechanism, stated rather than left to be found:**

- **Repository-local discovery is filesystem-derived, not declared.** `_repository_local_toplevel_names` reads the repository root and admits any directory holding an `__init__.py` or a direct `*.py` child. It is not a reviewed list, and it widens automatically when a new top-level Python directory appears.
- **Dynamic imports are outside the analysis.** `importlib.import_module(name)` and `__import__` are invisible to any AST check. Known and unclosed limit, not an exemption.
- **`sys.stdlib_module_names` is interpreter-version-bound.** It is the interpreter's own answer to "is this standard library", chosen deliberately over a hand-kept list, and its verdict can differ between Python versions.

A package placed under `core/` that is absent from `DOMAIN_OF_TOPLEVEL` raises `UnmappedPackageError` from the direction rule. That behaviour is unchanged by this decision.

##### 4. The one existing `exchange_calendars` use, recorded as a fact

**This decision creates no exception template, no qualifying criteria, and no procedure by which a further dependency could be admitted.** What follows is a record of one existing thing.

- There is **one** documented third-party use outside `tests/`: `exchange_calendars`, imported by `experiments/seed_trading_calendar.py`.
- That file is a setup utility, not a research runner. It is **not imported by any reproduction path**: `reproduction_runner` pins `experiments/daily_etf_universe_update.py` as the universe module, and `reference_h4` reproduces through `experiments/validate_h4_kurtosis.py` (`docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md` §11.2). Neither imports the package.
- **The containment claim was verified two ways, and the distinction matters:** (i) a repository-wide import search finds exactly **one** `import exchange_calendars` site, at `experiments/seed_trading_calendar.py`; and (ii) **no module in the repository imports `experiments/seed_trading_calendar.py`** — every other reference to it is prose in a docstring or comment. The "not imported by any reproduction path" statement is therefore **transitive, not merely a direct-import observation**: no execution path reaches the package through an intermediate module either. The claim is not strengthened beyond this, and it is a statement about the tree at this commit, not a guarantee about future ones.
- Its `TradingSession` output **is** a frozen dataset — one of the three tables in `dataset_manifest`'s required set, hash-verified through `reference_h4`'s `dataset_content_hashes`.
- Its `Calendar` values are **not** snapshot-frozen. `core/governance/calendar_definitions.py` holds the `XNYS` values as committed module literals that mirror the script's own constants, specifically so that reconstruction never invokes the package.

**The protection is layered, and all four layers are load-bearing:**

- **(a)** the frozen, hash-verified `TradingSession` dataset;
- **(b)** the committed `Calendar` literal duplication in `calendar_definitions.py`;
- **(c)** exclusion of the producing script from every reproduction execution path;
- **(d)** `network_guard`, under which any network call during reproduction is an automatic `REPRODUCTION_FAILED`.

**A second dependency exception requires its own decision, argued on its own terms, with its own number allocated at that time.** This record is an inventory of one existing fact. **It is not an allow-list, and nothing is exempted by appearing in it** — the same standing `ETF_SYMBOLS_BY_MODULE` carries under AD-068 decision 5.

`docs/RESEARCH_GOVERNANCE_STANDARD.md` §8 governs research-cycle exceptions and is **not** imported here — not its record form and not its Level 2 approval requirement. §8 does not govern architecture decisions, and borrowing it would manufacture a requirement this platform cannot satisfy.

##### 5. `workloads/` — conditional pre-commitment only

- **`workloads/` does not exist.**
- **This decision creates none.**
- **This decision authorizes none**, and classifies nothing that would live inside one.
- `core/`'s decided rule in 3 already forbids `core/` importing any repository-local package other than `core` itself. That covers a future `workloads/` by name-independence, and requires no new mechanism.
- **Should a future decision permit a third-party dependency inside a workload, that permission would not extend to `core/`, `adapters/`, `tools/`, `maintenance/`, `research_artifacts/`, or any other namespace.**
- **This decision takes no position on whether such permission should ever be granted.** It neither pre-authorizes that outcome nor forecloses it.

Per AD-077 clause 6 — neutrality claims expire at one implementation — this clause describes a namespace with **zero** implementations and may not be described as a general, neutral, or proven policy.

##### 6. AD-021 is not touched

- **This decision does not amend, reinterpret, restate, or rewrite AD-021**, including its rejection of a `CalculationEnvironment` concept, its stated rationale, and its revisit condition. `IndicatorDefinition.version` remains a plain integer.
- **This decision records its own dependency boundary and nothing more.** The boundary in 1–5 is AD-078's; AD-021's trigger is AD-021's and is untouched by it.
- Any tension between the presence of a third-party dependency anywhere in the tree and this platform's reproducibility claims is **not resolved here**. It is noted in *Known weakness* and left for whatever decision introduces such a dependency.

---

#### Rationale

1. **A claim stated at a scope the tree does not satisfy is a liability on a governance platform.** AD-005's dependency sentence is written at whole-codebase scope while `tests/` and one `experiments/` file carry documented non-standard-library imports. Any reader can establish that in one grep. AD-077 exists because a *drafted* completeness claim that review could falsify is a worse finding than the coupling it misdescribes; the same argument applies to scope. Stating a boundary where it is true and enforced is a stronger position than relying on a broader wording to cover it.

2. **The checker and test changes altered what is possible to record.** Before them, "`core/` is standard-library-only" was prose and nothing else — `import numpy` in `core/statistics` was invisible to every tool and every test. It is now measured by a checker rule and asserted by a blocking test. The claim did not change; the ability to hold it did.

3. **The remaining gap is documentary, not mechanical.** A reader can now run the checker and learn what `core/` does. No single document told them what `tools/`, `experiments/`, or `tests/` are held to, or which of those statements a mechanism backs. This entry is that document, and it adds no mechanism.

4. **Four concerns are separate and are kept separate.** Dependency purity is about which top-level names a namespace may import. Dataset provenance is about immutable, hash-verified snapshots (`RESEARCH_GOVERNANCE_STANDARD.md` §6). Environment capture — interpreter version, package versions, platform, compiled artifacts — is captured nowhere today; `reproduction_record.json` holds fields including commit hash, dataset hashes, reproduction status, result hash, notes, and verification timestamp, but no environment field. Reproduction semantics are `ReproductionStatus`'s four states. Conflating any two of these produces a claim stronger than any of them supports.

5. **The `exchange_calendars` case is protected by four mechanisms, not by one principle.** The layered account in 4 is what the tree actually implements, and it is recorded that way deliberately. A single-mechanism summary would be inaccurate for the `Calendar` values, which are protected by committed duplication rather than by a snapshot.

---

#### Consequences

**Positive.**

- AD-078 states the dependency boundary at a scope that is both true and, for `core/`, enforced, without altering AD-005.
- A future reader cannot mistake `core/`'s dependency purity for a platform-wide reproducibility guarantee: the two are separated here, and AD-077 clause 1b already holds that the dataset and reproduction path is workload-bound.
- The dependency policy has a named boundary — the top-level namespace — that is independent of AD-068's domains and AD-077's classes, so a change to either of those axes does not silently move this one.
- The single `exchange_calendars` use is recorded in the decision log rather than only in a module docstring and a Phase 4 amendment section.

**Negative.**

- Most namespaces have a measured state and no enforcement. `adapters/`, `tools/`, `maintenance/`, `research_artifacts/`, and `experiments/` are clean today and nothing prevents that from changing.
- The repository-local bucket is permissive by construction and widens automatically as top-level Python directories appear.
- Dynamic imports remain outside the analysis entirely.
- The `Calendar` literal duplication across `calendar_definitions.py` and `seed_trading_calendar.py` is covered by a **one-sided pin, not a mirror test**. `tests/test_governance_calendar_definitions.py::test_xnys_matches_seed_trading_calendar_literals` asserts `core/governance/calendar_definitions.XNYS`'s four field values against literals hardcoded in the test body; it does not import, parse, or compare against `experiments/seed_trading_calendar.py`. Drift in `calendar_definitions.py` is detected; drift in `seed_trading_calendar.py` is not.

---

#### What this decision does not do

It **adds no dependency**. No package is permitted, installed, declared, vendored, or pinned. `numpy`, `scipy`, `pandas`, and every other name are exactly as absent after this decision as before it.

It **creates no dependency declaration file or mechanism** — no `[project]` table, no requirements file, no lock file, no Dockerfile, no Nix expression, no environment capture. `pyproject.toml` is unchanged.

It **creates no `workloads/` directory** and **authorizes no workload implementation**. It **does not authorize a biomedical workload**. It **does not authorize an ML workload**. It chooses between none of them and takes no position on the choice.

It **creates no `WorkloadProfile`**, no registry, no plugin system, no dependency-injection container, and no dynamic discovery.

It **modifies no phase plan.** No Phase 1 item (1.1 through 1.6), no Phase 2 work, and no Phase 3 work in `docs/ENGINE_NEUTRALITY_ARCHITECTURE_REVIEW_2026-07-27.md` §5 is authorized, altered, or endorsed. That plan remains a proposal; where this entry names a fact it also names, it does so to describe the tree, never to approve a phase.

It **changes no reproduction record** — not `ReproductionRecord`'s field set, not `ReproductionStatus`'s four states, not any archived `reproduction_record.json`.

It **changes no archive** — no sealed bytes, no `dataset_manifest.json`, no `schema_version`, no `archive_seal_register.jsonl`, no protected-file fixture.

It **modifies no CI configuration.** The advisory `|| true` on the boundary-checker step is recorded as a fact about enforcement strength, not repaired.

It **adds no checker rule, no test, and no tooling.** Extending the checker to scan outside `core/` is proposed elsewhere and is authorized neither by AD-077 nor by this entry.

It **does not edit or amend AD-005**, and in particular does not amend AD-005's abstraction clause. No framework, no ORM, no DI container, no event bus, no CQRS, no generic repository base class.

It **does not amend AD-021.**

It **does not amend AD-068, AD-069, AD-073, AD-074, AD-075, or AD-077.** `ETF_SYMBOLS_BY_MODULE`, symbol attribution and its termination condition, the `store` grant list and its demand-driven growth rule, archive integrity verification, the Archive Seal, `reference_h4`'s seal, and AD-077's two-part neutrality claim and three-class axis all stand exactly as accepted.

---

#### Known weakness

Stated here rather than discovered later.

1. **The checker's repository-local bucket expands automatically.** It is derived from the filesystem, not from a reviewed list, so a new top-level Python directory becomes a name the checker will accept from `core/` on the day it appears, with no edit and no review.
2. **`core/`'s sibling-import rule rests on a single tripwire test.** The checker permits what the test forbids. If that test were ever removed or relaxed while fixing something unrelated, the rule would have no mechanism at all. The checker CLI is not a fallback and its exit status settles the question in neither direction: it can still exit non-zero because of the unrelated direction violations `core/` already carries, and it reports no sibling import today and would report none then. The point is narrow and is only this — the sibling-import rule has no checker enforcement of its own, so removing or relaxing the tripwire test leaves it with no mechanism at all.
3. **Most namespaces in the scope table have a measured state and no enforcement**, and four of them have no decided rule either. This entry makes drift nameable in review; it does not prevent drift.
4. **The `Calendar` literal duplication is protected on one side only.** `tests/test_governance_calendar_definitions.py::test_xnys_matches_seed_trading_calendar_literals` exists and pins the four field values of `core/governance/calendar_definitions.XNYS` against literals hardcoded in the test body. It does **not** import, parse, or compare against `experiments/seed_trading_calendar.py`, so nothing compares the two files to each other. It is a one-sided pin, not a mirror test: a drift in `calendar_definitions.py` fails the test, and a drift in `seed_trading_calendar.py` is detected by nothing. **No remediation is proposed, scheduled, or authorized here; this is a record of the current state.**
5. **Dependency declaration and environment capture remain unresolved.** There is no place a dependency could be declared, the interpreter version is pinned only in CI, and `reproduction_record.json` captures no environment. These are open questions, not gaps this decision closes.
6. **This entry is held by reading in every part except `core/`'s third-party rule**, and this repository has no independent reviewer.

---

#### Status

**Accepted against commit `a38089ae4f4bb1d7cb057e9f3fe04e5d91d2317b` (2026-07-28).** Documentation only: no code, test, tooling, fixture, archive, or CI change.

---

### AD-079: core/'s sibling-import rule (AD-078 Section 3) is now enforced by the checker, closing AD-078 Known Weakness 2 (accepted 2026-07-28, after implementation)

#### Review basis

**Level 1 — self-review.** One reviewer with repository access, working
against `tools/check_import_boundaries.py` and
`tests/test_import_boundaries.py` as changed by commit
`bfdca9ceec931eb07fc4588a3793597e57dcb40f`. **Level 3 is unavailable and
no Level 3 review was performed. This is not an independent review, and
neither this entry nor any document citing it may describe it as one**
(`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4). This is the same standing
AD-068, AD-069, and AD-078 declare for their own basis.

**Numbering.** AD-079 is the next number, per AD-077's *Numbering*
section as continued by AD-078: unconsumed numbers stay unconsumed, and
this entry claims only the next one in sequence.

**Acceptance basis.** This entry accepts, and records the closure
effected by, commit `bfdca9ceec931eb07fc4588a3793597e57dcb40f` — the
commit that changed `tools/check_import_boundaries.py`'s
`check_dependency_purity` and the corresponding tests in
`tests/test_import_boundaries.py`. It is recorded **after** the
implementation it accepts, and says so rather than presenting a tidier
sequence, following the precedent AD-074 sets for the same situation.

**Status.** **Accepted, 2026-07-28.** This entry is documentation only:
it enacts no code, test, fixture, or archive change of its own. The
implementation it describes already exists at commit
`bfdca9ceec931eb07fc4588a3793597e57dcb40f` and is unmodified by this
acceptance.

---

#### Context

**AD-078 Section 3 is not reopened, reinterpreted, or restated here.**
The decided rule remains exactly what AD-078 recorded: *"`core/` imports
the Python standard library and `core.*` only. No third-party package.
No repository-local package other than `core` itself."* This entry
touches none of that wording and grants no new permission.

What AD-078 also recorded, in its *Enforcement* subsection and in
*Known weakness* item 2, was the **strength** at which that rule was
held:

> "Non-`core` repository-local: enforced by
> `test_real_repository_core_imports_no_non_core_repository_local_package`
> alone. The checker permits it: `check_dependency_purity` allows any
> repository-local name, and `check_repository` resolves a domain only
> for names beginning `core.`."

> Known weakness 2: "`core/`'s sibling-import rule rests on a single
> tripwire test. The checker permits it. If that test were ever removed
> or relaxed while fixing something unrelated, the rule would have no
> mechanism at all."

That description was accurate at AD-078's acceptance commit and is
preserved here verbatim, not corrected in place — AD-078 is append-only
and this entry does not amend it. What follows records that the
described gap has since been closed by implementation, and updates
nothing else.

---

#### Decision

**1. Enforcement state before this commit.** `check_dependency_purity`
accepted any top-level name resolvable to a real package or module
directly under the repository root (`adapters`, `experiments`, a bare
top-level module, etc.), not only `core`. The only mechanism refusing a
non-`core` sibling import from `core/` was
`tests/test_import_boundaries.py::test_real_repository_core_imports_no_non_core_repository_local_package`,
which replicated the AST walk independently rather than exercising the
checker's own accept/reject path.

**2. Implementation change, at commit
`bfdca9ceec931eb07fc4588a3793597e57dcb40f`.** `check_dependency_purity`
in `tools/check_import_boundaries.py` now accepts a repository-local
top-level name only when it equals `core_root`'s own name (`"core"` on
the real tree). Every other repository-local sibling is rejected by the
same function that already rejected genuine third-party packages, and
reported through the existing `ForeignImport` type, extended with a
boolean flag that distinguishes, for message purposes only, a real
sibling package from a name that resolves to nothing in this repository
— never used to admit either case.

**3. Enforcement state after this commit.**
`check_dependency_purity` is now the enforcement mechanism for both
halves of AD-078 Section 3's `core/` rule — third-party rejection and
non-`core` repository-local rejection alike — asserted directly by
`tests/test_import_boundaries.py::test_real_repository_imports_no_third_party_package`
and the synthetic-tree tests in that file's dependency-purity section,
none of which is an `xfail`.
`test_real_repository_core_imports_no_non_core_repository_local_package`
is retained, not because it is still the only mechanism, but as an
**independent cross-check**: it re-derives the same fact by a separate
AST walk over the real tree, using a different code path than
`check_dependency_purity` itself — the same role
`test_real_tree_statistics_and_kernel_import_no_store` already plays for
`core.store` — so a defect specific to the production checker's own
logic would still be caught. It is no longer the sole enforcement
mechanism, and this entry is what changes that description from AD-078's.

**AD-078 Known Weakness 2 is closed as of commit
`bfdca9ceec931eb07fc4588a3793597e57dcb40f`; this entry is the record of
that closure.** AD-078's other four known weaknesses are untouched and
remain open exactly as AD-078 recorded them.

---

#### Non-goals

This decision does not:

- Add enforcement to `adapters/`, `experiments/`, `tools/`,
  `maintenance/`, `research_artifacts/`, `tests/`, or any namespace
  outside `core/`. AD-078 Section 2's scope table stands unchanged for
  every namespace other than the one enforcement-strength cell this
  entry corrects.
- Authorize, define, or take any position on a `workloads/` directory or
  any workload architecture. AD-078 Section 5 stands unchanged.
- Create a dependency-exception mechanism, allow-list, or procedure by
  which a further dependency could be admitted to `core/`. AD-078
  Section 4's `exchange_calendars` record is the only such fact in the
  log and is untouched.
- Alter AD-077's Engine / Reference Workload / Artifact classification,
  or reclassify `core/market_data`.
- Amend AD-005 or AD-021 in any respect.
- Amend AD-078 itself, in wording, scope, or intent.

---

#### Known limitations

Carried forward from AD-078 Section 3 and unchanged by this decision:

- **Dynamic imports remain outside the analysis.**
  `importlib.import_module(name)` and `__import__` are invisible to any
  AST-based check, here as everywhere else in this checker. Known and
  unclosed, not an exemption.
- **Repository-local discovery remains filesystem-derived, not
  declared.** `_repository_local_toplevel_names` still reads the
  repository root at one directory level and widens automatically when a
  new top-level Python directory appears; this decision changes what the
  checker *does* with that discovery for `core/`, not how the discovery
  itself works.
- **CI enforcement status is unchanged.** The advisory `|| true` on
  `tools/check_import_boundaries.py` in CI, recorded as a fact (not a
  defect) by AD-078, is untouched by this entry. Making the checker
  blocking in CI, if ever done, is a separate decision.
- **`sys.stdlib_module_names` remains interpreter-version-bound**, exactly
  as AD-078 recorded.

---

#### Rationale

An accepted decision entry that states a mechanism's strength goes stale
the moment that strength changes, and AD-078's own Rationale point 1
names exactly this failure mode: "a claim stated at a scope the tree does
not satisfy is a liability on a governance platform." AD-078 cannot be
edited to prevent that staleness without violating the append-only
principle it and every other entry in this log observe. Recording the
change as its own entry is the only way to keep AD-078 readable as a
snapshot of its own acceptance commit while keeping the current
enforcement state discoverable from the log.

---

#### Consequences

**Positive.**

- **AD-078 Known Weakness 2 is closed as of commit
  `bfdca9ceec931eb07fc4588a3793597e57dcb40f`: the sibling-import rule is
  now enforced by the checker itself, not by a single test that could be
  weakened or deleted without the rule noticing.**
- The tripwire test's role is now correctly described as independent
  verification rather than sole enforcement, matching the pattern already
  used for `core.store`.
- A future reader consulting AD-078 for the *decided rule* still gets an
  accurate answer; a reader consulting it for *enforcement strength* is
  directed here by this entry rather than misled by a stale sentence.

**Negative.**

- None identified beyond the known limitations above, all of which
  predate this decision and are unchanged by it.

---

#### What this decision does not do

It **adds no dependency rule** beyond what AD-078 Section 3 already
decided. It **grants no permission** to any namespace. It **creates no
`workloads/` directory** and **authorizes no workload**. It **does not
amend AD-005, AD-021, AD-068, AD-069, AD-073, AD-074, AD-075, AD-077, or
AD-078** — every fact, grant list, and classification those entries
record stands exactly as accepted. It **modifies no CI configuration**.
It **adds no new checker rule or mechanism**: `check_dependency_purity`
is the same function AD-078 already named, with its existing
accept/reject boundary tightened by commit
`bfdca9ceec931eb07fc4588a3793597e57dcb40f` to match the rule AD-078
already decided, not a new rule of its own.
