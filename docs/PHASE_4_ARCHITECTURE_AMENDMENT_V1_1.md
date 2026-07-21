# Phase 4 Architecture Amendment v1.1

> ## ✅ CURRENT DESIGN OF RECORD — as of 2026-07-21
>
> This document supersedes
> [Amendment v1.0](PHASE_4_ARCHITECTURE_AMENDMENT_V1.md) and is the design
> of record for the Phase 4 governance subsystem, per
> [PHASE_4_ARB_DETERMINATION_2026-07-21.md](PHASE_4_ARB_DETERMINATION_2026-07-21.md).
>
> **Status correction (2026-07-21).** This document previously read
> *"proposal, not implemented."* That is no longer accurate. A partial
> implementation exists in the working tree: **10 of 13
> `core/governance/*.py` modules and 9 of 11
> `tests/test_governance_*.py` files are present but uncommitted.**
>
> **The implementation is not conformant with this design.** §G lists
> `reproduction_record.json` binding and the result-report hash as MUST
> HAVE; neither is wired. The gap between this document and the code is
> enumerated as findings A1, A2 and A3 in
> [RR-001](reviewer_reports/2026-07-21_RR-001_phase4_governance_architecture_review.md),
> peer-reviewed in
> [RR-002](reviewer_reports/2026-07-21_RR-002_phase4_governance_peer_review.md),
> and adjudicated in the ARB determination §6. Sequencing to close it is in
> [PHASE_4_IMPLEMENTATION_ROADMAP.md](PHASE_4_IMPLEMENTATION_ROADMAP.md).
>
> **Read this document as the specification, never as a description of the
> code.** Uncommitted code is not evidence under
> [RESEARCH_GOVERNANCE_STANDARD.md](RESEARCH_GOVERNANCE_STANDARD.md) §3.

**Status: current design of record. Partially implemented; implementation uncommitted and non-conformant (see banner above).**

[Amendment v1.0](PHASE_4_ARCHITECTURE_AMENDMENT_V1.md)
received a **C — RETURN FOR REDESIGN** on adversarial review. This
document corrects it. Per this platform's own Standard §5 supersession
discipline — the same discipline v1.0 itself invoked against the base
proposal — this is a new, dated, cross-referenced file. v1.0 is retained
unedited; where this document's text conflicts with v1.0's, this
document controls. Where this document is silent, v1.0's text (itself
built on [the base proposal](PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md))
stands.

**Method.** Same discipline as v1.0 claimed for itself, actually applied
here: every claim below was re-verified against this repository directly
— table schemas, actual function bodies, actual call sites — not taken
on the review's word and not taken on v1.0's word either. v1.0's failure
was exactly this: it built a "verified" dependency table (§A.8) that
turns out to be wrong about one entry, in a way its own stated
methodology should have caught. Section A explains the miss. One place
below reaches a conclusion narrower than the review's own instructions
literally state (Calendar, §A.4) — flagged explicitly, not smuggled in,
per the same "checks the corrections rather than just accepting them"
posture v1.0 itself used in its §A.4–A.5.

---

## Why v1.0 was wrong, stated plainly

v1.0 §A.8 classified `ETF` metadata as "Code-defined (`_ensure_etfs`,
universe literal) → Commit hash" — the same treatment given to
`IndicatorDefinition` and `ScoringProfile`. That classification is false,
and the falseness is load-bearing: it is the one entry in that table
whose error breaks the entire reconstruction pipeline v1.0 §A.4.2
specified.

Verified directly:

- `PriceBar.etf_id` is `NOT NULL REFERENCES ETF (etf_id)`
  ([migrations/0001_initial_schema.sql:35](../migrations/0001_initial_schema.sql#L35)).
- Every connection this codebase opens sets `PRAGMA foreign_keys=ON`
  ([core/market_data/persistence/database.py:24](../core/market_data/persistence/database.py#L24)) —
  this constraint is live, not advisory.
- `ETF.etf_id` is minted with `uuid.uuid4().hex`
  ([experiments/daily_etf_universe_update.py:130](../experiments/daily_etf_universe_update.py#L130)),
  and only when `get_etf_by_ticker(conn, ticker)` returns `None`
  ([experiments/daily_etf_universe_update.py:127-136](../experiments/daily_etf_universe_update.py#L127)).
  `ticker` is looked up via a `UNIQUE` constraint
  ([migrations/0001_initial_schema.sql:25](../migrations/0001_initial_schema.sql#L25)), but every
  foreign key in the schema — `PriceBar.etf_id`, `IndicatorValue.etf_id`,
  `Score.etf_id` — points at `etf_id`, never at `ticker`. Ticker is a
  human-facing lookup key; `etf_id` is the actual relational identity.

v1.0's reconstruction pipeline (§A.4.2) was: fresh SQLite → migrate →
load `PriceBar` + `TradingSession` JSONL → run the experiment unmodified.
It never loads an `ETF` table from anywhere. On a freshly migrated,
empty scratch database, `get_etf_by_ticker` returns `None` for every
ticker the first time any script touches the `ETF` table, so
`_ensure_etfs` mints a **new**, random `etf_id` per ticker — necessarily
different from whatever `etf_id` values are baked into the frozen
`PriceBar` snapshot's `etf_id` column, because that snapshot was
extracted from the live database where the ETF rows already existed
under their original identities.

There is no load order in v1.0's pipeline where this reconciles:

- Load `PriceBar` first, `ETF` never → `PriceBar` insert fails
  immediately, `IntegrityError`, FK enforcement is on (this is in fact
  the *good* failure mode — loud, not silent — but v1.0 never specified
  loading `ETF` at all, so this is simply what v1.0's design does today).
- Run the experiment against a `PriceBar`-only scratch DB → any script
  path that calls `get_etf_by_ticker` gets `None` and either crashes
  (the four `validate_*` scripts, which do a bare lookup with no insert:
  `experiments/validate_reference_v2_h1_significance.py:213`,
  `experiments/validate_h3_phase6_economic_validation.py:182`,
  `experiments/validate_h3_gate1_independence.py:239`) or, for the
  v1-class regeneration path specifically, silently mints fresh `ETF`
  rows with new `etf_id` values that share nothing with the `PriceBar`
  rows already sitting in the same table
  (`experiments/daily_etf_universe_update.py:249` → `_ensure_etfs`).

v1.0 treated "code can regenerate this row" as sufficient grounds to
skip freezing it, which is exactly right for `IndicatorDefinition`,
`ScoringProfile`, `IndicatorValue`, `Score`, `DimensionScore` (§A.1.3's
reasoning there is sound and unchanged). It is not right for `ETF`,
because `ETF` is the only uuid4-keyed, code-regenerable table that a
*frozen* table (`PriceBar`) has a hard foreign-key dependency on.
Regenerating `IndicatorDefinition` on every run is safe because nothing
frozen points at its generated id. Regenerating `ETF` on every run is
unsafe because `PriceBar` — frozen, byte-hashed, the one artifact this
entire design exists to protect — points at exactly that id.

---

## A. Corrected dependency model

### A.1 Full classification, re-derived

| Dependency | Identity mechanism (verified) | A frozen table depends on this identity? | Classification | Treatment |
|---|---|---|---|---|
| `Calendar` | Literal constant `calendar_id="XNYS"`, `name`, `exchange`, `timezone` all module-level literals ([experiments/seed_trading_calendar.py:86-89](../experiments/seed_trading_calendar.py#L86)) | Yes (`ETF.calendar_id`, `TradingSession.calendar_id`) | Code-defined, deterministic natural key | Commit hash — loader inserts idempotently (§A.4) |
| `ETF` | `etf_id = uuid.uuid4().hex`, minted only when the ticker isn't already present ([daily_etf_universe_update.py:130](../experiments/daily_etf_universe_update.py#L130)) | **Yes** — `PriceBar.etf_id` | Non-deterministic surrogate key, referenced by a frozen table | **Frozen dataset snapshot** (v1.0's error, corrected here) |
| `TradingSession` | `(calendar_id, session_date)`, values sourced from unpinned third-party `exchange_calendars` | No FK from `PriceBar`, but `RANGE_TRADING_DAYS`/`get_trading_days` gates every experiment's date logic | Frozen external reference data | Frozen dataset snapshot (unchanged from v1.0 §A.2) |
| `PriceBar` | `price_bar_id = uuid4`, `etf_id` FK → `ETF` | N/A (this *is* the frozen table) | Frozen raw input | Frozen dataset snapshot (unchanged from v1.0, load-ordered **after** `ETF`, §C–D) |
| `IndicatorDefinition`, `ScoringProfile` | `uuid4` PK, looked up by natural `(name, version, parameters)` UNIQUE | No frozen table references these ids | Code-defined | Regenerate / commit hash (unchanged) |
| `IndicatorValue`, `Score`, `DimensionScore` | `uuid4` / composite PK | No | Derived deterministic state | Regenerate (unchanged, v1.0 §A.1.3 reasoning stands) |
| Migrations | File-based, applied via idempotent `run_migrations` | — | Code artifact | Commit hash (unchanged) |

### A.2 The narrow, exact reason ETF is different

Not "ETF is metadata, therefore freeze all metadata." The dividing line
is precise: **a table is a frozen-identity artifact exactly when (a) its
primary key is minted non-deterministically (`uuid4`, not a literal or a
value derived purely from inputs) and (b) a table this design freezes
elsewhere holds a foreign key into that primary key.** `IndicatorDefinition`
satisfies (a) but not (b) — nothing frozen points at
`indicator_definition_id`. `Calendar` satisfies (b) but not (a) — its key
is a hardcoded string, not a `uuid4`. `ETF` is the only dependency in
this codebase that satisfies both, and it satisfies both by a real
margin: three separate tables FK into `ETF.etf_id`
(`PriceBar`, `IndicatorValue`, `Score`), one of which is frozen.

### A.3 Artifact hierarchy (per the mandate, confirmed)

**Frozen datasets** (identity and/or externally-sourced values that
cannot be regenerated bit-for-bit from code alone):
- `ETF` identity snapshot
- `PriceBar` snapshot
- `TradingSession` snapshot

**Derived** (pure functions of the frozen datasets + committed code +
committed literal parameters, correctly regenerated every run, never
snapshotted — v1.0 §A.1.3's argument, unchanged):
- `IndicatorValue`
- `DimensionScore`
- `Score`
- rankings
- reports

**Code-defined, not frozen, not "derived" either** (deterministic from a
literal in the committed code, reconstructed by a tiny idempotent loader
step rather than either a snapshot file or the experiment scripts
themselves): `Calendar`, `IndicatorDefinition`, `ScoringProfile`. This
third bucket is not named in the mandate's own two-bucket framing
(frozen vs. derived) but is necessary to state explicitly — see §A.4.

### A.4 A finding narrower than the mandate as literally stated

The mandate's artifact hierarchy names two buckets. Applied literally to
everything `PriceBar`/`ETF`/`TradingSession` transitively touch, a third
candidate for "frozen dataset" appears: `Calendar`, since both `ETF` and
`TradingSession` carry a `calendar_id` foreign key into it, and it sits
in the identical FK-dependency shape that made `ETF` dangerous.

Verification does not support freezing it. `Calendar`'s only row in this
codebase (`calendar_id="XNYS"`) is a hardcoded module-level literal in
`experiments/seed_trading_calendar.py:86-89` — not a `uuid4`, not sourced
from `exchange_calendars` (only the `TradingSession` *rows* are; the
`Calendar` row's own fields are plain committed strings), not
non-deterministic in any way. Two independent runs of the same committed
code produce byte-identical `Calendar` rows, unconditionally. Freezing it
as a JSONL snapshot would add a dataset entry, a hash, a load step, and a
provenance check for zero risk reduction — a violation of this
platform's own "don't build ahead of a concrete need" discipline
(AD-005, invoked repeatedly in the base proposal and v1.0 §A.7). What
`Calendar` does need, which it does not have today, is a load step: no
existing script inserts it except `seed_trading_calendar.py` (the
deliberate, isolated, `exchange_calendars`-touching exception v1.0 §A.2.1
already excludes from the reproduction path). §D specifies this as new,
small, loader-owned code.

**This narrows the mandate's item 7 in one respect and confirms it in
another:** the corrected dataset manifest below has exactly the three
entries the mandate names (`ETF`, `PriceBar`, `TradingSession`) — not
four. `Calendar` is deliberately excluded from `datasets`, with the
reasoning stated here rather than silently applied, so a future reviewer
does not mistake the omission for an oversight of the same kind that
produced the C grade.

---

## B. Artifact classification

Restating §A.3 as the operative rule, since it is what §C–§F build on:

| Bucket | Members | Storage | Loaded/produced by |
|---|---|---|---|
| Frozen dataset (content-hashed, git-tracked JSONL) | `ETF`, `PriceBar`, `TradingSession` | `research_archive/<cycle>/dataset_hashes/*.jsonl` | Reconstruction loader, §D |
| Code-defined (deterministic literal, loader-inserted) | `Calendar` | Not stored — module-level literal in committed code | Reconstruction loader's own idempotent insert step, §D |
| Code-defined (deterministic literal, script-inserted) | `IndicatorDefinition`, `ScoringProfile` | Not stored — module-level literal in committed code | The experiment scripts themselves, unmodified (`_ensure_indicator_definitions`, `_ensure_scoring_profile`) |
| Derived (regenerated every run) | `IndicatorValue`, `Score`, `DimensionScore`, rankings, reports | Not stored as input; only the final result report is archived | The experiment scripts themselves, unmodified |

The distinction between the second and third rows matters operationally,
not architecturally: both are "code-defined," but `Calendar` has no
existing caller that creates it outside the one script v1.0 already
excludes from the reproduction path, so the reconstruction harness must
own that insert. `IndicatorDefinition`/`ScoringProfile` already have a
caller inside the unmodified experiment scripts (`_ensure_indicator_definitions`,
`_ensure_scoring_profile`), so no new code is needed for them — this was
correct in v1.0 and is unchanged.

---

## C. Dataset manifest v3

`schema_version` bumps to `3` (v1.0 bumped 1→2 for the calendar-snapshot
addition; this is the second content-shape revision). Adds the `ETF`
dataset entry; `type` field routing (v1.0 §A.2.2) is unchanged.

```json
{
  "schema_version": 3,
  "project_id": "h4",
  "generated_at": "2026-08-01T00:00:00+00:00",
  "datasets": [
    {
      "dataset_id": "etf_h4_universe_v1",
      "type": "identity_reference_data",
      "source_table": "ETF",
      "row_count": 24,
      "snapshot_path": "dataset_hashes/etf_h4_universe_v1_2026-08-01.jsonl",
      "content_hash": "sha256:...",
      "schema_version": 1
    },
    {
      "dataset_id": "pricebar_h4_universe_v1",
      "type": "primary_market_data",
      "source": "yahoo_finance",
      "source_table": "PriceBar",
      "universe": ["SPY", "QQQ", "..."],
      "coverage": {
        "evaluation_period": {"start": "2020-01-01", "end": "2026-07-01"},
        "max_lookback_start": "2018-07-04",
        "forward_horizon_end": "2026-08-15"
      },
      "extraction_query": "sql/h4_pricebar_extract.sql",
      "extraction_query_hash": "sha256:...",
      "row_count": 14832,
      "snapshot_path": "dataset_hashes/pricebar_h4_universe_v1_2026-08-01.jsonl",
      "content_hash": "sha256:...",
      "ingestion_run_ids": ["...", "..."],
      "source_tags_observed": ["yahoo_finance_daily"],
      "schema_version": 1
    },
    {
      "dataset_id": "trading_calendar_snapshot_v1",
      "type": "external_reference_data",
      "source": "exchange_calendars",
      "source_table": "TradingSession",
      "calendar_id": "XNYS",
      "coverage": {"start": "2018-07-04", "end": "2026-08-15"},
      "row_count": 2038,
      "snapshot_path": "dataset_hashes/trading_calendar_snapshot_v1_2026-08-01.jsonl",
      "content_hash": "sha256:...",
      "schema_version": 1
    }
  ]
}
```

Every entry carries `dataset_id`, `type`, `schema_version` (per-entry,
independent of the manifest's own top-level `schema_version` — same
non-conflation discipline v1.0 §1.3 already established for
`archive_manifest.json` vs. `dataset_manifest.json`), `content_hash`,
`row_count`, `snapshot_path` — the mandate's item 7 requirement, applied
to all three entries uniformly.

### C.1 Canonical `ETF` JSONL schema — corrected against the actual table

The mandate's own illustrative schema for this section listed
`etf_id, ticker, name, exchange, currency, type, created_at`. Verified
against the actual table (`migrations/0001_initial_schema.sql:23-30`)
and domain model (`core/market_data/domain/models.py:12-18`): the `ETF`
table has six columns — `etf_id, ticker, name, currency, calendar_id,
created_at`. There is no `exchange` column and no `type` column anywhere
in the schema, migrations, or domain model. Adding two new columns that
don't exist is out of scope for a reproduction-evidence amendment (it
would need its own migration, its own backfill, and its own review) and
is not adopted here. `calendar_id` — present in the real table, absent
from the mandate's illustrative list, and the exact field that makes
`ETF` depend on `Calendar` (§A.4) — is included.

```json
{"calendar_id": "XNYS", "created_at": "2024-01-03T14:30:00+00:00", "currency": "USD", "etf_id": "3f2a1b9c4d5e4f6a8b7c9d0e1f2a3b4c", "name": "SPDR S&P 500 ETF Trust", "ticker": "SPY"}
```

Rules (reusing v1.0 §A.6's canonicalization rule set unchanged — UTF-8
no BOM, LF only, exactly one trailing newline, alphabetical key order,
`Decimal`-compatible fields as strings where applicable — this file has
none, since `ETF` carries no `TEXT`-as-`Decimal` columns):

- **Row ordering:** `ORDER BY ticker` — `ticker` is `UNIQUE` and
  human-legible, unlike `etf_id`, which is an opaque, run-independent
  random value; ordering by the arbitrary key would make the file's row
  order carry no information and would make diffs across regenerated
  supersets harder to read for no benefit.
- **Rule:** preserve the original `etf_id` exactly as extracted — never
  regenerate through `uuid4` at extraction time, at load time, or at any
  point in reproduction. This is the rule the mandate states and the one
  rule this entire amendment exists to make true.
- **Rule:** preserve `calendar_id` exactly as extracted, so the loader
  (§D) can validate it resolves against the code-defined `Calendar` row
  before inserting `ETF` — an FK-validity check the frozen snapshot
  alone cannot self-certify.

---

## D. Reconstruction workflow

Corrected pipeline — v1.0 §A.4.2's diagram never loaded `ETF` or
`Calendar` at all; this replaces it:

```
fresh SQLite (scratch path, never experiments_etf_universe.db)
        │
        ▼
run existing migrations (core.market_data.persistence.migrations.run_migrations,
                          unchanged, reused as-is -- idempotent, already the
                          exact call every experiment script makes today)
        │
        ▼
insert Calendar row(s) (code-defined literal, NEW loader-owned step --
                          no existing script does this outside
                          seed_trading_calendar.py, which is excluded
                          from the reproduction path per v1.0 §A.2.1)
        │
        ▼
load ETF snapshot (frozen JSONL, preserves original etf_id -- NEW)
        │
        ▼
load TradingSession snapshot (frozen JSONL, unchanged from v1.0 §A.4.2)
        │
        ▼
load PriceBar snapshot (frozen JSONL -- now explicitly AFTER ETF,
                          because PriceBar.etf_id is a live FK
                          constraint against ETF.etf_id, enforced by
                          PRAGMA foreign_keys=ON on every connection)
        │
        ▼
execute the pinned commit's own experiment code, unmodified,
against the scratch DB path (git-worktree execution model, §F)
```

`Calendar` before `ETF` and `TradingSession` because both carry a
`calendar_id` FK into it. `ETF` before `PriceBar` because of the FK this
whole amendment is about. `TradingSession` has no ordering dependency on
`ETF` or `PriceBar` and can load any time after `Calendar`.

### D.1 Loader fail conditions (mandate item 3)

All three run **before the scratch database is touched at all** — fail
fast, matching `FreezeVerifier`'s existing precedent (its own docstring:
"never running review logic against unverified state") and v1.0 §2.3's
carried-over failure-condition ordering:

- **Orphan `PriceBar` rows.** A pure, offline set-difference over the
  two JSONL files: every `etf_id` value appearing in the `PriceBar`
  snapshot must appear in the `ETF` snapshot's `etf_id` column. If not,
  refuse before any DB write, with the specific offending `etf_id`
  values named in the error. (`PRAGMA foreign_keys=ON` would also catch
  this at INSERT time if the pre-check were skipped — kept as a second,
  independent line of defense per §H.1, not the primary mechanism, since
  a raw `sqlite3.IntegrityError` is not a governance-quality error
  message.)
- **ETF identities do not match.** The `ETF` snapshot file's re-computed
  sha256 must equal `dataset_manifest.json`'s declared `content_hash`
  for that entry (byte-level check) — plus a semantic check comparing
  the snapshot's `(ticker, etf_id)` pairs against what the pinned
  commit's own `ETF_UNIVERSE` literal expects by ticker, since a hash
  match alone confirms the file didn't change but not that it still
  covers the universe the experiment code will iterate over.
- **Row counts differ.** Each snapshot file's line count must equal its
  `dataset_manifest.json` entry's declared `row_count`, checked before
  any DB write, for all three frozen datasets.

### D.2 Why the pinned commit's own code has to run, not HEAD's

§A.2's `_ensure_etfs` short-circuits safely only when `get_etf_by_ticker`
finds a match — which requires the ticker set the loaded `ETF` snapshot
covers to equal the ticker set the *executing* code's `ETF_UNIVERSE`
literal iterates over. If reproduction ran HEAD's current experiment
scripts (as opposed to the pinned commit's) against an old `ETF`
snapshot, a ticker added to `ETF_UNIVERSE` after the freeze would be
missing from the snapshot, and `_ensure_etfs` would silently mint a new
`uuid4` for it — reintroducing exactly this amendment's defect through a
different door. This is why §F's git-worktree execution model — running
the exact pinned commit's code, not HEAD's code against pinned data — is
not an incidental implementation detail but a second, independent
requirement for §A's fix to actually hold.

---

## E. Offline guarantee

v1.0's network-fuse test (§A.4.3) patched one private function
(`core.market_data.providers.yahoo_finance._http_get`) inside one pytest
test. v1.0's own "explicitly unresolved" section (item 2) already
flagged this as coupled to a single construction call and not immune to
silent invalidation. The mandate is right that this is insufficient —
it is a policy statement about one code path, not a guarantee about the
process.

**Structural mechanism: a process-level socket guard, installed by the
reproduction runner's own entrypoint, not by pytest.** Before importing
or invoking any experiment code, the reproduction runner (a plain
script/CLI, e.g. `python -m core.governance.reproduction_runner <cycle>`)
monkeypatches `socket.socket.connect` and `socket.create_connection`
(stdlib only — consistent with AD-005, no new dependency) to raise an
`OfflineViolationError` unconditionally, for the lifetime of the
reproduction process. This closes the coupling gap directly: the guard
does not need to know which function, which provider, or which future
code path might attempt a fetch — it blocks the one primitive every
network call in a stdlib-only codebase must ultimately go through.
Critically, this guarantee holds **when an external auditor runs the
reproduction runner directly**, satisfying the mandate's explicit
requirement — it does not depend on the auditor using pytest, or on
`pytest`-only fixtures being active.

This does not replace the other two layers v1.0 §A.5 already
established; it upgrades the weakest of the three from "assumption" to
"enforced," making all three genuinely structural:

1. **Process-level socket guard** (new, this section) — no code path in
   the reproduction process can open a socket, full stop.
2. **Snapshot completeness** (v1.0 §A.5, unchanged) — removes the
   *reason* a fetch would ever be attempted, since every row any script
   could need already exists in the scratch DB.
3. **The existing `yahoo_finance._http_get` patch test** (v1.0 §A.4.3) —
   kept as a cheap, specific, defense-in-depth check, now secondary
   rather than the sole guarantee.

---

## F. Reproduction verification contract

### F.1 Pre-execution

- Resolve `reproduction_record.json.commit_hash` (git plumbing, same
  read-only pattern as `freeze_verifier.py`).
- For each of the three `dataset_manifest.json` entries (`ETF`,
  `PriceBar`, `TradingSession`): re-hash the snapshot file, compare to
  the declared `content_hash`. Any mismatch → refuse before touching the
  scratch DB (this is v1.0 §2.1/§A.3.2's existing contract, widened from
  1-2 entries to 3 — a scope change, not a new mechanism).
- Run §D.1's three loader-level checks.

### F.2 Execution

- `git worktree add <scratch-worktree> <commit_hash> --detach` — a
  read-only, isolated checkout of the exact historical commit, separate
  from the operator's actual working tree (never disturbs uncommitted
  work, mirroring this platform's existing "never touch live state"
  discipline, e.g. never opening `experiments_etf_universe.db`).
- Migrations, dataset snapshots, and the experiment script all come from
  **that same commit's own tree** — the dataset artifacts for a given
  cycle are committed alongside `methodology.md` at freeze time per
  Standard §5's archive layout, so `commit_hash` pins code and data
  together; nothing needs to reach outside the worktree.
- Dependency installation: per AD-005 (stdlib-only) and v1.0 §4
  (unchanged, reaffirmed), there is nothing to install for the runtime
  path — the only import outside the standard library anywhere in
  `core/`, `adapters/`, `experiments/` is `pytest`, dev-only, not needed
  to execute the experiment script itself. The interpreter must match
  `.python-version` (base §4.2 MUST HAVE — still not implemented in this
  repository as of this writing; carried forward as open, §H).
- Run `run(db_path=<scratch path>, ...)` from the worktree's own copy of
  the experiment script, completely unmodified — the same call every
  experiment script already exposes (v1.0 §A.4.1, unchanged).
- Remove the worktree after the run (or retain for debugging — operator
  discretion, not a structural requirement).

### F.3 Post-execution

- Result report hash / tolerance check — unchanged from v1.0 §2.3.
- No network access occurred — enforced structurally by §E, verified by
  checking the guard was never tripped (or, inverted: the guard raising
  at all is itself an automatic `REPRODUCTION_FAILED`, not a silent
  pass).
- **Frozen-identity tables unchanged: row count and an ordered hash of
  `ETF`, `PriceBar`, `TradingSession`, and `Calendar` must be identical
  before and after the run.** This is the check that would have caught
  v1.0's actual defect — a silent `_ensure_etfs` insert shows up here as
  a nonzero `ETF` row-count delta, immediately, rather than surfacing
  three steps later as an unrelated-looking numerical discrepancy in the
  result report.

**Explicit scope limit on the above, stated because the mandate's own
wording invites over-scoping it:** the mandate's item 4 says "verify no
new ETF rows created... no new PriceBar rows created" without naming
`IndicatorValue`, `Score`, or `DimensionScore`. A literal, careless
reading — "assert no new rows anywhere in the database" — is wrong and
would fail every single successful reproduction, because
`IndicatorValue`/`Score`/`DimensionScore` are *required* to gain new
rows on every run (v1.0 §A.1.3: freezing them would hide a regression
instead of catching one). The post-run row-count/hash check in this
section applies **only** to `{Calendar, ETF, TradingSession, PriceBar}`
— the frozen-identity set from §A.3 — and must never be applied to the
derived set. This scope boundary is itself a MUST HAVE (§G) precisely
because getting it wrong in either direction breaks something: too
narrow, and v1.0's actual defect goes uncaught again; too broad, and the
checker false-fails on correct, working reproductions.

---

## G. Updated MUST HAVE / SHOULD HAVE / FUTURE ENHANCEMENT

| Tier | Item | Status vs. v1.0 |
|---|---|---|
| **MUST HAVE** | `ETF` frozen dataset snapshot, canonical JSONL, preserving original `etf_id` (§A, §C.1) | **New — the core defect fix** |
| **MUST HAVE** | `dataset_manifest.json` schema v3 — three-entry array (`ETF`, `PriceBar`, `TradingSession`), `Calendar` deliberately excluded (§A.4, §C) | Revised (was v2, two entries) |
| **MUST HAVE** | Reconstruction loader inserts `Calendar` from its code-defined literal before `ETF`/`TradingSession` (§D) | New — no existing script does this outside the excluded `seed_trading_calendar.py` |
| **MUST HAVE** | Load order: migrations → `Calendar` → `ETF` → `TradingSession` → `PriceBar` → execute (§D) | Revised — v1.0 never loaded `ETF` or `Calendar` at all |
| **MUST HAVE** | Loader pre-flight checks: orphan-row set-difference, identity/ticker match, row-count match, all before any DB write (§D.1) | Revised — widened from PriceBar/TradingSession-only to include ETF |
| **MUST HAVE** | Process-level socket guard installed by the reproduction runner's entrypoint, unconditional for the process lifetime (§E) | **New — replaces v1.0's single-function-patch test as the load-bearing mechanism** |
| **MUST HAVE** | `yahoo_finance._http_get` patch test retained as secondary defense-in-depth (v1.0 §A.4.3) | Unchanged, demoted from primary to secondary |
| **MUST HAVE** | Git-worktree execution: reproduction runs the pinned commit's own code against the pinned commit's own dataset artifacts, not HEAD's code (§D.2, §F.2) | **New — v1.0 never specified which commit's code actually executes** |
| **MUST HAVE** | Post-run check scoped exactly to `{Calendar, ETF, TradingSession, PriceBar}`; never applied to `{IndicatorValue, Score, DimensionScore}` (§F.3) | **New — a scope boundary the mandate's own wording doesn't state and a careless implementation would get wrong** |
| **MUST HAVE** | `reproduction_record.json` binding commit + 3 dataset hashes + report hash (v1.0 §A.3.2) | Revised (N=3, was N=2) |
| **MUST HAVE** | Result report echoes every effective experiment parameter (v1.0 §A.3.3) | Unchanged |
| **MUST HAVE** | `ReproductionStatus` enum extending `FreezeStatus` (v1.0 §2.2) | Unchanged |
| **MUST HAVE** | `.python-version` + `requires-python` + pinned `requirements-dev.txt` (base §4.2) | Unchanged, still not implemented |
| **MUST HAVE** | `LEGACY_PROVENANCE_NOTE.md` per legacy archive + shared `LEGACY_ARCHIVE_PROJECT_IDS` (base §3.2) | Unchanged |
| **MUST HAVE** | CI workflow running `pytest` on every push/PR (base §5.1, §5.3) | Unchanged |
| **MUST HAVE** | `tests/test_reproduction_contract.py`, merge-blocking, extended to assert the frozen-identity-only post-run scope (§F.3) | Revised |
| **SHOULD HAVE** | Snapshot size ceiling (20 MB) applies per-dataset-entry, now three entries not two (base §1.5) | Unchanged, scope note only |
| **SHOULD HAVE** | CI asserts interpreter matches `.python-version` (base §4.2) | Unchanged |
| **SHOULD HAVE** | Weekly scheduled full-suite CI run (base §5.3) | Unchanged |
| **SHOULD HAVE** | Re-verify the `Calendar`-is-code-defined reasoning if a second, dynamically-sourced calendar is ever added (§A.4, §H.2) | New, low-cost, explicit coupling to watch |
| **FUTURE ENHANCEMENT** | External content-addressed storage past the size ceiling (base §1.5) | Unchanged |
| **FUTURE ENHANCEMENT** | Docker/Nix, only if AD-005 is revisited (base §4.2) | Unchanged |
| **FUTURE ENHANCEMENT** | Point-in-time (bitemporal) market data storage (base §6) | Unchanged |
| **FUTURE ENHANCEMENT** | WORM/branch-protection enforcement on archive history (base §6) | Unchanged |

**Preserved from v1.0, per its own §A.7, unaffected by any correction in
this amendment:** no full-SQLite-snapshot, no Docker/Nix/Poetry/uv,
`FreezeVerifier` and `ReproductionStatus`'s 4-state enum, git as artifact
storage at the 20 MB soft ceiling, `config_hash` removal (v1.0 §A.3),
regeneration (not freezing) of `IndicatorValue`/`Score`/`DimensionScore`,
the canonical-JSONL philosophy, the zero-tolerance policy on
non-float-derived figures.

---

## H. Remaining unresolved risks

Stated plainly, matching this document's own adversarial mandate, not
implied to be closed:

1. **FK enforcement is a second line of defense, not the primary one,
   and it has a single point of failure.** `PRAGMA foreign_keys=ON` is
   set inside `core.market_data.persistence.database.connect()`
   ([database.py:24](../core/market_data/persistence/database.py#L24)).
   If any future code path opens `sqlite3.connect()` directly instead of
   going through this helper, the pragma is silently off (SQLite's
   default), and the orphan-row protection this design leans on as a
   backstop disappears without any error. §D.1's pre-flight checks are
   the actual primary defense and do not depend on this pragma — but the
   pragma's fragility is still worth naming, since a reader could
   mistake "FK enforcement is on" for a structural guarantee rather than
   a configuration choice made in exactly one function.
2. **`Calendar`'s code-defined classification (§A.4) is coupled to
   `calendar_id` staying a hardcoded literal.** If this platform ever
   adds a second, dynamically-sourced calendar (a real exchange-calendar
   API call at runtime, not a seed script), the reasoning that let
   `Calendar` skip a frozen snapshot no longer applies and must be
   re-derived — flagged as a coupling to watch, the same posture v1.0
   §A.4.3 took toward its own network-fuse test's patch target.
3. **Git-worktree execution runs literal historical code with no
   sandboxing or timeout specified.** Acceptable under this platform's
   current single-operator trust model (the same trust boundary already
   implicit in every other tool in this repository), but if this
   reproduction tooling is ever pointed at an external contributor's
   commit in CI, executing arbitrary historical code becomes a real
   supply-chain question this amendment does not resolve — consistent
   with base §6 gap 4 (single-operator risk), not a new category of gap,
   but sharper here because §F.2 is the first place this platform's
   tooling actually executes non-HEAD code rather than only reading it.
4. **The process-level socket guard is unconditional for the life of the
   reproduction run.** By design — but it means the reproduction runner
   process cannot itself perform any network operation (e.g., fetching a
   remote CI artifact as a separate concern) without being restructured
   into a pre-step that runs before the guard installs. Not a defect,
   but a constraint a future implementer should not have to rediscover.
5. **v1.0's own already-open risks are untouched by this amendment and
   remain open:** the residual config-drift risk (v1.0 §A.3.3 — a
   schema/documentation discipline, not a structural guarantee) and
   everything in the base proposal's §6 (no point-in-time storage, no
   WORM guarantee, no Level 3 review).
6. **The frozen/derived post-run scope boundary (§F.3) is enforced by
   the checker's own code, not by the database schema.** A future
   migration adding a new frozen table (a hypothetical `MacroObservation`
   raw table, say, following the pattern the migrations' own comments
   already anticipate — `migrations/0001_initial_schema.sql:79`, "the
   same pattern must be applied to future raw tables") would need this
   scope list updated by hand. Missing that update produces a checker
   that either misses a real defect (too narrow) or false-fails every
   run (too broad) — the same class of manual-discipline risk v1.0
   §A.3.3 already accepted for parameter-echoing, not a new kind of gap,
   but worth naming here rather than presenting §F.3's fix as
   self-maintaining.

**Does this amendment close the C-grade finding?** Yes, for the specific
structural break identified: `ETF` is now a frozen dataset, the
reconstruction pipeline loads it before `PriceBar` in an order that
actually satisfies the foreign key, and the post-run check is scoped to
catch a silent identity regeneration without false-failing on the
derived tables that are supposed to change every run. What this
amendment does not claim is that the risk list above is now empty — six
items remain, stated above rather than minimized, matching the mandate's
own instruction not to soften them.
