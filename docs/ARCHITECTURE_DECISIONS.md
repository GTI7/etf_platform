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
