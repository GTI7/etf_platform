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
| **A8-C#** | [A-8 — machine-artifact location](PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md) | §6 | C-1 … C-11 |
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

#### A-8 — machine-artifact location (A8-C1 … A8-C11)

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
