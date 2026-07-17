# v0.6.0 Candidate Design — Write-Side Pipeline Composition

This document is a **design review**, not a decision record and not an
implementation. Nothing in the repository changes as a result of it. It
traces the actual v0.5.0 code (never assumed) and proposes a single
orchestration entry point for the next milestone identified in
`docs/BASELINE_STATUS.md`'s activation-trigger table: *"A concrete
requirement for automated, composed execution of ingest→indicator→score."*

Every claim about existing behavior below is grounded in a specific file
and line, not inferred from naming or intent.

---

## 1. Existing workflow analysis

Four orchestration functions exist today. All four are independently
callable, independently tested, and — confirmed by a repository-wide
search — **never called from one another or from any fifth function**.
`docs/BASELINE_STATUS.md` already states this as the one open gap in the
v0.5.0 baseline; tracing the code confirms it exactly: there is no
`main.py`, `cli.py`, `app.py`, or any entry point anywhere in the
repository. The only callers of these four functions are tests.

### `run_pipeline` — [`pipeline_run.py:19`](../core/market_data/ingestion/pipeline_run.py)

- **Responsibility:** the sole transaction boundary for a single
  `(pipeline_name, pipeline_date)` attempt. Not indicator- or
  ingestion-specific — reused unmodified across packages (`core.analytics`
  imports it directly from `core.market_data`).
- **Inputs:** `conn`, `clock`, `pipeline_name: str`, `pipeline_date: date`.
- **Output:** yields `ingestion_run_id: str` to the caller's `with` block.
- **Transaction ownership:** the *only* place in the codebase that opens a
  commit/rollback boundary.
  - `start_ingestion_run` commits **immediately**, on its own — a crash
    during the body leaves a visible orphaned `'running'` row rather than
    erasing the attempt.
  - On success: `complete_ingestion_run(..., SUCCESS)` +
    `advance_pipeline_watermark(...)` commit **together**, in one
    transaction, along with every write the caller's body made — so the
    run can never be observed as `'success'` without the watermark having
    advanced, or vice versa.
  - On exception: `conn.rollback()` first (discarding the body's partial
    writes), then `complete_ingestion_run(..., FAILED, error_message=...)`
    commits as its own, separate transaction. The failure record can never
    coexist with partial data from the same attempt.
- **Idempotency:** `advance_pipeline_watermark` upserts with
  `MAX(last_successful_session, excluded.last_successful_session)` —
  monotonic only, never regresses. `run_pipeline` itself does not check
  whether `pipeline_date` was already processed before running the body;
  whether re-invoking a given stage is safe is entirely up to what that
  stage's body does on a repeat call. This is the load-bearing fact
  behind the asymmetry documented in §2 and §5.

### `ingest_daily_prices` — [`price_ingestion.py:15`](../core/market_data/ingestion/price_ingestion.py)

- **Responsibility:** fetch and store one ETF's price bar for one trading
  session from a `DataProvider`.
- **Inputs:** `conn`, `clock`, `provider: DataProvider`, `etf: ETF`,
  `session_date: date`.
- **Output:** `ingestion_run_id: str`. Side effect: zero or more `PriceBar`
  rows (zero if the date isn't a trading day; normally one).
- **Transaction ownership:** none of its own — the entire body runs inside
  one `run_pipeline` call, `pipeline_name=f"price_ingestion:{ticker}"`.
- **Idempotency — evidence-based finding:** `insert_price_bar`
  ([`repository.py:103`](../core/market_data/persistence/repository.py))
  does an unconditional `INSERT`, and the `PriceBar` table
  ([`0001_initial_schema.sql`](../migrations/0001_initial_schema.sql))
  carries **no `UNIQUE` constraint** on `(etf_id, session_date)` — only an
  index. Nothing rejects or deduplicates a second insert for the same
  ETF/date. Unlike `IndicatorValue` (`UNIQUE` + `ON CONFLICT DO NOTHING`,
  §below) or `Score` (explicit `get_score()` guard + `UNIQUE` backstop),
  **re-calling `ingest_daily_prices` for a session that already
  succeeded will insert a second, duplicate `PriceBar` row.** No test in
  `tests/test_price_ingestion.py` exercises repeated execution — this is
  a real, currently-untested gap in v0.5.0, not a hypothetical one, and it
  directly shapes the composition design in §2.
- On a non-trading `session_date` (per `is_trading_day`), the body is a
  no-op and the watermark still advances past it.

### `calculate_sma` / `calculate_rsi` — [`indicator_calculation.py`](../core/analytics/indicator_calculation.py)

- **Responsibility:** compute and store one `IndicatorValue` for one
  `(IndicatorDefinition, ETF, session_date)`. Structurally identical
  functions — same window-resolution helpers, same transaction pattern —
  differing only in the math (`sma()` vs `rsi()`) and the JSON parameter
  key they read (`"window"` vs `"period"`).
- **Inputs:** `conn`, `clock`, `etf: ETF`, `definition: IndicatorDefinition`,
  `session_date: date`.
- **Output:** `ingestion_run_id: str`. Side effect: one `IndicatorValue` row.
- **Transaction ownership:** none of its own — one `run_pipeline` call per
  invocation, `pipeline_name=f"indicator:{definition.name}:v{definition.version}:{ticker}"`
  (SMA and RSI therefore get independent watermarks per ETF).
- **Idempotency:** genuinely idempotent. `insert_indicator_value`
  ([`repository.py:67`](../core/analytics/persistence/repository.py)) uses
  `ON CONFLICT (indicator_definition_id, etf_id, session_date) DO NOTHING`,
  backed by a real `UNIQUE` constraint
  ([`0002_analytics_indicators.sql:15`](../migrations/0002_analytics_indicators.sql)).
  A rerun is a silent no-op — never a duplicate, never an overwrite.
- Neither function checks `is_trading_day` itself. Window resolution
  (`_resolve_trading_window`) uses trading days `<= session_date`, so a
  `session_date` that is *not itself* a trading day does not block
  computation — it just uses the same window it would have used for the
  most recent actual trading day. This is a real asymmetry against
  `ingest_daily_prices`/`calculate_score` (both of which special-case
  non-trading days explicitly) — noted here because it directly affects
  what "non-trading day" means for the composed pipeline (§6).

### `calculate_score` — [`scoring_pipeline.py:71`](../core/analytics/scoring_pipeline.py)

- **Responsibility:** compute and store one `Score` and its
  `DimensionScore` rows for one `(ETF, ScoringProfile, session_date)`.
- **Inputs:** `conn`, `clock`, `etf: ETF`, `profile: ScoringProfile`,
  `session_date: date`.
- **Output:** `ingestion_run_id: str`. Side effect: one `Score` +
  N `DimensionScore` rows, or nothing.
- **Transaction ownership:** none of its own — one `run_pipeline` call,
  `pipeline_name=f"scoring:{profile.name}:v{profile.version}:{ticker}"`.
- **Idempotency:** explicit `get_score()` check *before* any computation
  (`scoring_pipeline.py:100`) — required because `Score`+`DimensionScore`
  is a parent/child pair, so `ON CONFLICT DO NOTHING` on `Score` alone
  would still leave freshly-generated `DimensionScore` rows referencing a
  `score_id` that was never written. `UNIQUE(etf_id, scoring_profile_id,
  session_date)` on `Score` is a defense-in-depth backstop only, per its
  own migration comment. Also explicitly `is_trading_day`-aware: a
  non-trading `session_date` is a no-op success, same as ingestion.
- **Dependency, not composed:** raises `MissingIndicatorValueError` if a
  referenced `IndicatorDefinition` has no `IndicatorValue` yet for this
  ETF/session — i.e. it already assumes indicators were computed first,
  but nothing enforces that ordering today except manual call order in a
  test.

### Precedent for composition: `generate_ranked_etf_report` — [`ranked_report.py:27`](../core/analytics/ranked_report.py)

Read-side only, and not part of this design's scope, but directly
relevant as precedent: it is a "composition/use-case function, not a pure
domain function" (its own docstring) that lives outside both the
repository and domain layers, takes a live `conn`, and calls existing
pieces (`get_scores_for_session` → `rank_scores` → `get_etf`) in sequence.
It establishes that this codebase already has a place for
"compose existing orchestration/repository calls, add no business logic"
— it's just never been done on the write side.

---

## 2. Composition design

### Proposed entry point

```
run_write_pipeline(
    conn: sqlite3.Connection,
    clock: Clock,
    provider: DataProvider,
    etf: ETF,
    session_date: date,
    sma_definition: IndicatorDefinition,
    rsi_definition: IndicatorDefinition,
    scoring_profile: ScoringProfile,
) -> WritePipelineResult
```

Proposed location: `core/analytics/write_pipeline.py` — it depends on
both `core.market_data` (ingestion) and `core.analytics` (indicators,
scoring), same direction `scoring_pipeline.py` and
`indicator_calculation.py` already depend on `core.market_data`, so
placing it in `core.analytics` doesn't introduce a new cross-package edge.

`WritePipelineResult` is a proposed frozen, slotted dataclass carrying the
four `ingestion_run_id` values produced (`price_ingestion_run_id`,
`sma_run_id`, `rsi_run_id`, `score_run_id`, the last two `| None` when
skipped — see below) — nothing new is persisted; this only surfaces
identifiers the four stages already produce, for logging/observability.

- **Execution order:** ingest → SMA → RSI → score, strictly sequential,
  matching the goal diagram. RSI is not required by SMA or vice versa,
  but there is no evidence today (only one `ScoringProfile` example, only
  two indicators) that parallelizing them is worth the added complexity —
  sequential is the straight-line reading of the goal diagram.
- **Failure behavior:** fail-fast. The first stage to raise propagates
  its exception out of `run_write_pipeline` immediately; no later stage
  is invoked. See §5.
- **Idempotency expectations:**
  - Before calling `ingest_daily_prices`, check whether a `PriceBar`
    already exists for this exact `(etf_id, session_date)`, via the
    already-existing `get_price_bars(conn, etf.etf_id,
    start_date=session_date, end_date=session_date)`
    ([`repository.py:146`](../core/market_data/persistence/repository.py)).
    If it returns a non-empty list, skip the call. **This is a corrected
    replacement for an earlier draft of this design**, which proposed
    comparing `get_last_successful_pipeline_date(conn,
    f"price_ingestion:{etf.ticker}")` against `session_date`. That
    watermark comparison was rejected on independent review: `advance_pipeline_watermark`
    is a **monotonic MAX** (AD-011) — it records only the *latest* date a
    pipeline ever reached, not that every date up to it was actually
    processed. Backfill is an explicitly supported scenario in this
    repository's architecture (AD-011's own rationale: *"An out-of-order
    (e.g. backfill) run for an earlier session does not regress a later
    watermark"*), so a watermark-based check could see a later date's
    watermark and wrongly conclude an earlier, never-ingested backfill
    date was already handled — skipping ingestion for a date that has no
    `PriceBar` at all. Checking for the exact `PriceBar` row directly asks
    the only question that actually matters ("does data for this specific
    date exist?") and is correct regardless of the order sessions are
    processed in. It requires no new repository function, no schema
    change, and no migration — `get_price_bars` already exists and is
    already used elsewhere in this call graph (`_load_close_prices` in
    `indicator_calculation.py`).
  - This existence check exists **only** because §1 found
    `ingest_daily_prices` has no storage-level dedup — without it, calling
    `run_write_pipeline` twice for the same `(etf, session_date)` would
    silently duplicate `PriceBar` rows, a v0.5.0 gap this design must not
    paper over by touching `insert_price_bar` or the `PriceBar` schema
    (both are frozen, out of scope).
  - SMA, RSI, and score stages are called **unconditionally on every
    invocation**, relying entirely on their own, already-proven v0.5.0
    idempotency (`ON CONFLICT DO NOTHING` / explicit `get_score()` check).
    No pre-check is needed or added for these three — adding one would be
    redundant defensive logic duplicating a guarantee that already exists
    one layer down.

### Why this belongs in orchestration, not repositories or domain

- Repository functions execute SQL and nothing else, never commit, never
  sequence anything (AD-001, restated as "Repository responsibility" in
  `docs/BASELINE_STATUS.md`). Deciding "call stage B after stage A
  succeeds" is a sequencing decision, categorically not a repository
  concern.
- Domain functions (`calculations.py`, `score_calculation.py`) are pure —
  no `conn`, no `Clock`, no I/O (AD-025). `run_write_pipeline` needs both
  a live connection and a clock, so it cannot live there without breaking
  domain purity.
- `run_pipeline` itself already establishes that transaction-boundary and
  sequencing decisions live in orchestration functions one layer above
  repositories. `run_write_pipeline` is one more orchestration function
  at a higher layer, calling other orchestration functions — the same
  relationship `generate_ranked_etf_report` already has to
  `get_scores_for_session`/`rank_scores`/`get_etf` on the read side.
- Critically, **no calculation logic moves**: `run_write_pipeline` performs
  one `SELECT`-only read (the `PriceBar` existence check) and four function
  calls in sequence. It contains no SMA/RSI/scoring math, no window
  resolution, no SQL writes of its own.

---

## 3. Transaction model

**What runs inside `run_pipeline`:** exactly what already does today, per
stage, unchanged. Each of the four calls
(`ingest_daily_prices`/`calculate_sma`/`calculate_rsi`/`calculate_score`)
opens its own `run_pipeline` context, and each context's commit/rollback
boundary is precisely what §1 already described for that function
individually. Nothing about any individual stage's transaction is altered.

**What remains outside `run_pipeline` (i.e., inside `run_write_pipeline`
but outside any transaction):**
- The one `PriceBar` existence check (`get_price_bars` scoped to the exact
  `etf_id`/`session_date`) used to decide whether to skip the ingestion
  call — read-only, no transaction needed.
- The sequential `if`/`return` control flow deciding which stage to call
  next and whether to skip one.
- Exception propagation between stages (no `try`/`except` inside
  `run_write_pipeline` — a failing stage's own `run_pipeline` has already
  rolled back and recorded that failure by the time the exception reaches
  `run_write_pipeline`; there's nothing left for this function to do
  except let it propagate).

**Exactly one transaction owner, demonstrated:** `run_write_pipeline`
contains zero `conn.execute`, zero `conn.commit`/`conn.rollback`, and zero
`with conn:` blocks. It never opens a transaction and never calls
`run_pipeline` directly either — it only calls the four existing
functions, each of which internally owns exactly one `run_pipeline`
call. A single invocation of `run_write_pipeline` therefore produces
**up to four independent, sequential transactions** (fewer if the
ingestion guard skips, or if a failure stops the sequence early) — never
one wrapping transaction across stages. `run_pipeline`
([`pipeline_run.py`](../core/market_data/ingestion/pipeline_run.py))
remains the only code in the entire call graph that owns a transaction
boundary, exactly as it does today.

---

## 4. Indicator execution strategy

**Decision: A — call `calculate_sma()` then `calculate_rsi()`
explicitly**, as two named parameters
(`sma_definition: IndicatorDefinition`, `rsi_definition: IndicatorDefinition`)
and two straight-line calls. No registry, no `dict[str, Callable]`
dispatch, no loop over a generic `indicators: list[IndicatorDefinition]`.

Justification, from repository evidence only:

- `docs/BASELINE_STATUS.md`'s own activation-trigger table states the
  condition for building an indicator dispatch mechanism explicitly:
  *"A third real indicator, or a concrete need to select between
  indicators dynamically at runtime."* Exactly two concrete indicators
  exist as of v0.5.0 (`calculate_sma`, `calculate_rsi`); that trigger has
  not fired.
- The same document's "Abstraction discipline" guarantee states the
  general rule this codebase has followed at every phase: *"New
  abstractions require a second concrete use case, not a plausible
  first one"* — and cites RSI itself as the example: *"a second concrete
  indicator (RSI, v0.5.0) was added without introducing an indicator
  registry or dispatch mechanism... two working implementations were
  judged insufficient evidence."* A write-side composer over those same
  two functions has no new evidence to add.
- `calculate_sma` and `calculate_rsi` already differ in the JSON
  parameter key each reads from `definition.parameters` (`"window"` vs
  `"period"`) and in the trading-window length required (`window` vs
  `period + 1`). A name-based dispatch layer would need to either encode
  that difference somewhere generic (which doesn't exist yet) or just
  delegate straight back to two explicit functions — i.e. it would add a
  layer of indirection around exactly the two calls this design already
  makes directly, for no behavioral benefit.
- A `list[IndicatorDefinition]` parameter (rather than two named ones)
  would itself be the first step toward name-based dispatch inside
  `run_write_pipeline` (iterating and branching on `definition.name`) —
  that is precisely the mechanism the trigger table says is not yet
  justified. Two named, explicit parameters keep the composition function
  as literal as the two functions it calls.

---

## 5. Failure analysis

Every row below follows directly from §1's per-function transaction and
idempotency findings; none of it is new behavior introduced by
`run_write_pipeline`, which adds no `try`/`except` of its own.

| Stage fails | Rollback | Retry-safe? | Persisted state after failure |
|---|---|---|---|
| **Ingestion** | `run_pipeline` rolls back any partial `PriceBar` writes from *this* attempt; commits `IngestionRun(FAILED)` separately. Watermark unchanged. | Yes, via the §2 `PriceBar` existence check — without it, a naive retry would call `ingest_daily_prices` again and (per §1's finding) could duplicate `PriceBar` rows if an *earlier* attempt had already partially succeeded before a later stage failed. | No new `PriceBar` row from this attempt; one `FAILED` `IngestionRun`; no SMA/RSI/Score rows (stages never reached). |
| **SMA** | `run_pipeline` rolls back the one `IndicatorValue` insert attempt (idempotent-safe regardless, per §1); `IngestionRun(FAILED)` recorded for the `indicator:SMA:...` pipeline. Ingestion's watermark from this run is untouched (it already committed in its own, prior transaction). | Yes, unconditionally — `calculate_sma` is idempotent by construction. | `PriceBar` from stage 1 remains (already committed, separate transaction); no SMA `IndicatorValue`; no RSI `IndicatorValue`; no `Score`. |
| **RSI** | Same pattern as SMA, scoped to the `indicator:RSI:...` pipeline. | Yes, unconditionally — same idempotency guarantee. | `PriceBar` and SMA `IndicatorValue` from this run remain committed; no RSI `IndicatorValue`; no `Score`. |
| **Scoring** | `run_pipeline` rolls back the partial `Score`/`DimensionScore` insert attempt; `IngestionRun(FAILED)` recorded for the `scoring:...` pipeline. | Yes, unconditionally — `calculate_score`'s explicit `get_score()` guard makes even a blind retry safe. | `PriceBar`, SMA `IndicatorValue`, RSI `IndicatorValue` all remain committed; no `Score`/`DimensionScore`. |

**Scope and limits of the ingestion idempotency guard.** The §2
`PriceBar` existence check makes the *composed* path
(`run_write_pipeline`) safe to call repeatedly for the same
`(etf, session_date)`. Stated explicitly, because the guarantee does not
extend further than this:

- **It protects only the composed execution path.** The check lives in
  `run_write_pipeline`, not inside `ingest_daily_prices` itself.
- **`ingest_daily_prices()` called standalone is unchanged from v0.5.0** —
  it still has no idempotency guard of its own, exactly as documented in
  §1. Any existing or future caller that invokes it directly, outside
  `run_write_pipeline`, gets none of this protection.
- **`PriceBar` still has no `UNIQUE` constraint.** This design does not
  add one (schema changes are out of scope, §7), so the existence check
  is an application-level guard only — unlike `IndicatorValue`/`Score`,
  there is no database-level backstop behind it.
- **Therefore concurrent execution remains intentionally out of scope.**
  A check-then-insert guard with no `UNIQUE` backstop is race-prone under
  concurrent invocation (two overlapping calls could both see "no
  `PriceBar` yet" and both insert). This is acceptable only because
  scheduled/concurrent execution is explicitly out of scope for v0.6.0
  (§7) — it is not a defect being overlooked, it is a limitation being
  named so a future scheduler milestone doesn't inherit it silently.

**Why per-stage commits (not one meta-transaction) is the right model:**
stage 1..N-1's already-committed work is never rolled back by a later
stage's failure. This is deliberate: it means retrying after a stage-3
failure does not force re-fetching from the external provider or
recomputing already-correct indicators — only the failed stage (and
anything after it) runs again. The alternative (wrapping all four stages
in one transaction) would require `run_write_pipeline` to reach into each
stage's internals to share one transaction, which breaks each stage's own
self-contained `run_pipeline` boundary (AD-001, AD-026) and is exactly
the kind of layer-crossing this design is told not to do.

No retry loop, no backoff, and no automatic re-invocation exist inside
`run_write_pipeline` — a failure simply propagates to the caller, who
decides whether and when to call it again. Automated retry/scheduling is
explicitly out of scope (§7).

---

## 6. Testing strategy

All proposed, none written — this is still design only.

1. **Successful end-to-end execution** — seed one `Calendar`/`TradingSession`/
   `ETF`, both `IndicatorDefinition`s, one `ScoringProfile`; a fake
   `DataProvider` returning one bar for `session_date`. Call
   `run_write_pipeline` once. Assert: one `PriceBar`, one SMA
   `IndicatorValue`, one RSI `IndicatorValue`, one `Score` +
   `DimensionScore` rows, and all four pipeline watermarks advanced to
   `session_date`.
2. **Atomicity per stage** — for each of the four stages independently,
   force a failure inside that stage's body (reusing the "reproduce live"
   method already established for `run_pipeline` in AD-013/AD-019/AD-027:
   inject a failure, confirm the write rolls back, confirm earlier
   stages' commits survive untouched).
3. **Fail-fast ordering** — assert that when ingestion fails, no
   `IndicatorValue` or `Score` row exists afterward (SMA/RSI/score never
   invoked); repeat for an SMA failure (assert RSI/score never invoked)
   and an RSI failure (assert score never invoked).
4. **Idempotency / repeated execution** — call `run_write_pipeline` twice
   with identical arguments. Assert exactly one `PriceBar` row, one SMA
   value, one RSI value, one `Score` after both calls — this is the test
   that specifically proves the §2 `PriceBar` existence check closes the
   duplicate-`PriceBar` gap found in §1, by first confirming it *would*
   fail without the guard (same regression-first method as AD-013/AD-019).
   Extend with a **backfill case**: seed a watermark that already advanced
   past a *later* date, then invoke `run_write_pipeline` for an earlier,
   never-ingested `session_date`; assert ingestion still runs (proving the
   guard is keyed on actual `PriceBar` existence, not on the watermark).
5. **Partial failure then recovery** — first call fails at the RSI stage
   (inject a failure); assert `PriceBar` and SMA value are committed, RSI
   and scoring watermarks did not advance. Second call (no injected
   failure) succeeds; assert the ingestion stage was skipped (still
   exactly one `PriceBar` row, not two) while RSI and scoring complete;
   final state has exactly one row per table.
6. **Non-trading-day behavior through the full composition** — a
   `session_date` with no `TradingSession` row (or `is_trading_day=0`):
   assert ingestion no-ops (existing behavior) and scoring no-ops
   (existing behavior), while documenting/asserting the §1 asymmetry that
   SMA/RSI do **not** self-check `is_trading_day` and will still attempt
   computation from the most recent actual trading days — this is
   existing v0.5.0 behavior, unchanged by composition, and the test
   exists to make that explicit rather than silently rely on it.

---

## 7. Scope control

Out of scope for v0.6.0, explicitly:

- **ProviderRegistry activation** — `run_write_pipeline` takes a
  `DataProvider` instance directly, the same way `ingest_daily_prices`
  already does; no registry lookup is introduced.
- **Dynamic/registry-based indicator dispatch** — see §4's justification.
- **API or CLI** — no entry point of any kind is added; `run_write_pipeline`
  is a plain function, called only from tests until a named external
  consumer exists (per `docs/BASELINE_STATUS.md`'s deferred-capabilities
  list).
- **Portfolio support** — `PortfolioId`/`HoldingId` remain unused,
  untouched.
- **Universe support** — `UniverseId` remains unused, untouched; this
  composition is single-ETF only, matching the goal statement exactly.
- **Scheduler / background execution** — no automated, recurring, or
  cron-style invocation; no retry/backoff logic (§5).
- **Any change to `run_pipeline`, repository interfaces, migrations, or
  any v0.4.x/v0.5.0 function** — including *not* adding a `UNIQUE`
  constraint or `ON CONFLICT` clause to `PriceBar`/`insert_price_bar` to
  close the §1 idempotency gap at its source; that gap is worked around
  at the orchestration layer (§2's `PriceBar` existence check, using only
  the already-existing `get_price_bars`) specifically so v0.5.0 storage
  behavior stays untouched. No new repository function is introduced.
- **Multi-ETF or multi-day batch composition** — one ETF, one
  `session_date` per call, per the goal statement; no looping over an
  ETF universe or a date range.
- **Any new persisted table** — `WritePipelineResult` is an in-memory
  return value only; no new schema, no new migration.

---

v0.6.0 scope is limited to orchestration of the existing write pipeline. No new analytical capability is introduced.
