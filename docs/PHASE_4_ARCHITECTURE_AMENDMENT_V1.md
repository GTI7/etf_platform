# Phase 4 Architecture Amendment v1.0

**Status: proposal, not implemented.** This amends
[docs/PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md](PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md)
(hereafter "the base proposal") after two adversarial reviews. Per this
platform's own Standard §5 supersession discipline — the same discipline
the base proposal itself applies to `research_archive/` in its §3 — this
is a **new, dated, cross-referenced file**. The base proposal is retained
unedited. Where a section below says "amends §X," read that as: §X's
text stands, this document's text controls where the two conflict.

**Method.** Every code claim below was re-verified against this
repository directly (function signatures, table schemas, actual import
statements), not taken on the reviewers' word. Two places where
verification produced a *stronger* finding than the correction asked for
are flagged explicitly (§A4, §A5) — this amendment does not just accept
the corrections, it checks them.

**What this amendment does NOT touch:** base proposal §3 (Archive
Evolution), §4 (Environment Reproducibility), §6 (Institutional
Benchmark), the rejection of full-SQLite-snapshots, the rejection of
Docker/Nix/Poetry/uv, `FreezeVerifier`, the append-only archive
philosophy, and the zero-tolerance policy on non-float-derived figures
(base §2.3) are unchanged and re-affirmed. Nothing in the corrections
this document incorporates bears on any of them.

---

## A.1 — Dataset scope correction (amends §1.2, §1.6)

### A.1.1 Verified dependency analysis

Re-derived directly from the three experiment scripts' code, not from
the correction's assertion of it:

| Script | Reads `PriceBar` | Reads `Calendar`/`TradingSession` | Touches `Score`/`DimensionScore`/`IndicatorValue` |
|---|---|---|---|
| [validate_reference_v1_significance.py](../experiments/validate_reference_v1_significance.py) | Yes | Yes (`get_trading_days`) | **Regenerates** them — [line 559](../experiments/validate_reference_v1_significance.py#L559) calls `run_daily_update(db_path=db_path, session_date=..., universe=...)` per trading day before reading `Score` via `build_panel` |
| [validate_reference_v2_h1_significance.py](../experiments/validate_reference_v2_h1_significance.py) | Yes | Yes | No — confirmed no `Score`/`DimensionScore`/`IndicatorDefinition`/`ScoringProfile` import or read anywhere in the file |
| [validate_h3_phase6_economic_validation.py](../experiments/validate_h3_phase6_economic_validation.py) | Yes | Yes | No — computes its own scores directly from `PriceBar` in-process; never reads the `Score` table |

`IndicatorValue`, `Score`, `DimensionScore` are confirmed pure functions
of `PriceBar` + `IndicatorDefinition`/`ScoringProfile` parameters (both
code-defined, see §A.8) + the committed calculation code. No script
reads a frozen `Score` snapshot; `validate_reference_v1_significance.py`
*regenerates* the rows it needs, in-process, from `PriceBar` and the
committed pipeline, every time it runs.

### A.1.2 Revision

Base §1.2's four-item list and §1.6's diagram both named "dataset
snapshot" as one undifferentiated item. Replace with:

**KEEP** — `PriceBar` snapshot (frozen input; base §1.3–1.5's schema and
canonicalization rules apply unchanged).

**ADD** — Trading calendar snapshot (§A.2).

**DO NOT ADD** — `Score`, `DimensionScore`, `IndicatorValue` snapshots.

### A.1.3 Why regenerating is a stronger claim than freezing

This is not a scope-reduction made for convenience; it is a strictly
stronger reproducibility guarantee than the base proposal's original
framing implied, for one structural reason: **a frozen `Score` snapshot
would prove the file didn't change. It would not prove the code can
still produce it.**

If `Score` were snapshotted and hash-bound like `PriceBar`, a
reproduction check would compare the archived `Score` bytes to
themselves and always pass — even if the scoring pipeline had silently
regressed, even if `core/analytics/domain/calculations.py` had a bug
introduced after the freeze that would produce different numbers today.
The check would be testing "did anyone edit this file," which
`FreezeVerifier` already does for code; it would not be testing "does
this platform's committed code, run today, still produce this result,"
which is the actual claim §2's reproduction contract exists to prove.

By *regenerating* `Score`/`DimensionScore`/`IndicatorValue` from the
frozen `PriceBar` snapshot and the pinned commit on every reproduction
run, the contract exercises the full computational chain — indicator
math, scoring blend, ranking — every single time. A silent regression
anywhere in that chain surfaces as `REPRODUCTION_FAILED` (base §2.2).
Freezing the derived output instead would have quietly disabled that
detection for the single largest piece of domain logic in the platform.
This also removes an entire snapshot-consistency problem the base
proposal's four-item model didn't fully surface: a frozen `Score`
snapshot generated from a given `PriceBar` extract could itself drift
out of sync with that `PriceBar` extract (e.g., if either were
regenerated independently), a failure mode that does not exist when one
is derived from the other at verification time instead of being stored
twice.

---

## A.2 — Trading calendar as a required evidence artifact (amends §1.3)

### A.2.1 Why it's required, not optional

Confirmed by reading [experiments/seed_trading_calendar.py](../experiments/seed_trading_calendar.py):
`TradingSession` rows are **not** derived from `PriceBar` or from any
in-repo heuristic. They come from the third-party `exchange_calendars`
package, which the script's own docstring states explicitly is "NOT
installed by any part of this platform" and is a deliberate, isolated
exception to AD-005's stdlib-only guarantee — confined to this one
setup utility, never imported by `core/` or `adapters/`.

This means `TradingSession` is the one evidentiary input in scope for
Phase 4 that AD-005's "no third-party library can silently change
behavior" argument (base proposal §0) does not cover. `RANGE_TRADING_DAYS`
used by every one of the three experiment scripts (`get_trading_days`)
is exactly as capable of silently drifting between reproduction attempts
as `PriceBar` is — a future `exchange_calendars` release correcting a
historical exchange-holiday determination would change which dates are
"trading days" without any code in this repository changing at all.
Freezing the calendar as a snapshot has an additional benefit beyond
"input completeness": **it means reproduction never re-invokes
`exchange_calendars`, so the package's own version never needs to be
pinned for reproduction to hold** — only the one-time generation step
(§A.9, item 3) touches the package at all.

### A.2.2 Revised `dataset_manifest.json` schema — multi-dataset array

```json
{
  "schema_version": 2,
  "project_id": "h4",
  "generated_at": "2026-08-01T00:00:00+00:00",
  "datasets": [
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
      "source_tags_observed": ["yahoo_finance_daily"]
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
      "content_hash": "sha256:..."
    }
  ]
}
```

`schema_version` bumps to `2` for the array-of-typed-datasets shape;
`dataset_id`/`content_hash`/`snapshot_path` semantics from base §1.3 are
unchanged per entry. `type` is a new required field distinguishing
`primary_market_data` from `external_reference_data` — the reproduction
checker (§A.9) uses it to route each entry to the correct loader, not
just to label it.

Calendar snapshot format: canonical JSONL, one row per
`(calendar_id, session_date)`, fields `calendar_id`, `session_date`,
`is_trading_day`, `close_time_utc` — the exact `TradingSession` columns
(`migrations/0001_initial_schema.sql`), no transformation. `close_time_utc`
is nullable in the schema; the JSONL writer must emit `null` explicitly,
never omit the key (§A.6).

---

## A.3 — Remove `config_hash` as a required artifact (amends §1.2 item 3, §1.6, §2.1, §2.3)

### A.3.1 Verified

Re-checked the `run()` signature of all three scripts directly:

```
validate_reference_v1_significance.py:530  horizon_trading_days=HORIZON_TRADING_DAYS, bucket_size=BUCKET_SIZE,
                                             permutations=PERMUTATIONS, bootstrap_iterations=BOOTSTRAP_ITERATIONS,
                                             block_lengths=BLOCK_LENGTHS, random_seed=RANDOM_SEED
validate_reference_v2_h1_significance.py:467 lookback_days=LOOKBACK_DAYS, forward_days=FORWARD_DAYS,
                                              permutations=PERMUTATIONS, bootstrap_iterations=BOOTSTRAP_ITERATIONS,
                                              block_lengths=BLOCK_LENGTHS
validate_h3_phase6_economic_validation.py:380 random_seed=RANDOM_SEED
```

Every one of these is a default bound to a **module-level constant
inside the git-tracked script itself** — not a CLI flag, not an
environment variable, not an external config file. `git show
<commit>:experiments/validate_reference_v1_significance.py` already
reveals every parameter that would have gone into a `config_hash`. A
separate, machine-hashable config artifact would hash a value that is
already fully pinned by `commit_hash` — a second lock on an already-locked
door.

### A.3.2 Revision

Base §1.2 item 3 ("Experiment configuration... needs a machine-hashable
companion") and §2.1's four-row "Input" table are revised. The
reproduction contract is now three required elements, with methodology
references optional:

| Element | Source | Must match |
|---|---|---|
| Repository commit | `reproduction_record.json.commit_hash` | Exactly (git SHA) |
| Dataset artifact(s) | `dataset_manifest.json.datasets[].content_hash`, one per entry | Exactly (sha256), all entries |
| Result report | `experiment_results/*_report*.json` | Byte-identical (or the declared exact-match rule, base §2.3) after regeneration |

`methodology.md`'s frozen-elements section remains required *documentation*
(human-readable rationale for why `RANDOM_SEED = 20260718`, why
`PERMUTATIONS = 10000`, etc.) but is no longer part of the machine
verification chain — it is cited by reference in `reproduction_record.json`,
not hashed into it.

### A.3.3 Residual risk (flagged, not resolved by this amendment)

This holds only as long as every experiment parameter that matters stays
a git-tracked literal. It breaks silently — with no error, just a
result that quietly stopped being reproducible — the day any future
script reads a parameter from a CLI flag with no recorded default, an
environment variable, or any other source outside the commit. **MUST
HAVE, carried into §A.9's readiness list:** the result report itself
must echo every effective parameter value used for that run (seed,
permutations, bootstrap iterations, block lengths, horizons, date
windows) as a JSON field, independent of where the value came from. This
already happens informally today (`"random_seed": 20260718` in the
existing v1 report, per project memory) — this amendment's addition is
to make it a **required, checked** field so a future parameter source
that *isn't* a commit-pinned literal is caught by "the report is missing
a field the schema requires," not discovered by a failed reproduction
years later with no record of why.

---

## A.4 — Remove the injectable data-source seam requirement (amends §5.2, §5.3, base Readiness item 4)

### A.4.1 Verified

All three experiment scripts already accept `db_path: Path` as a `run()`
parameter (confirmed above, §A.1.1, plus `validate_h3_gate1_independence.py:217`
and `validate_scoring_signal.py:111` — five of five `experiments/validate_*.py`
scripts). No refactor is required to point an experiment at a different
SQLite file than the live one. The base proposal's characterization of
this as "a real, non-trivial piece of implementation work this design
depends on" (§5.2) is **too strong** — for the `db_path` seam
specifically, the work is already done.

### A.4.2 Revision — reconstruct, don't inject

Replace the base's "experiments must accept injected data sources"
requirement with:

> The reproduction framework reconstructs an isolated SQLite database
> from frozen dataset artifacts, then runs the existing, unmodified
> experiment script against that database's path.

```
snapshot JSONL (PriceBar + trading_calendar)
        │
        ▼
temporary SQLite database (fresh file, scratch path)
        │
        ▼
run existing migrations (core.market_data.persistence.migrations.run_migrations —
                          already the exact call every experiment script
                          makes against the live DB; reused unchanged)
        │
        ▼
load frozen rows (PriceBar, Calendar, TradingSession) from JSONL
        │
        ▼
execute existing experiment: run(db_path=<scratch path>, ...) — unmodified
```

Requirements (all MUST HAVE):
- Never open, write to, or otherwise touch `experiments_etf_universe.db`
  (the live database) during a reproduction run.
- Never make a network request of any kind during a reproduction run.
- Never call `YahooFinanceProvider`'s live fetch path during a
  reproduction run.

### A.4.3 A finding stronger than the correction asked for

The correction states this class of requirement can simply be dropped.
Verification shows it is *mostly* true but surfaces one concrete gap the
correction did not name: `validate_reference_v1_significance.py`'s
regeneration path (§A.1.1) calls `run_daily_update(...)`, which is
[experiments/daily_etf_universe_update.py](../experiments/daily_etf_universe_update.py)'s
`run()`. That function's own `run()` signature (`db_path`, `session_date`,
`universe` — no provider parameter) **hardcodes**
`YahooFinanceProvider()` at [line 256](../experiments/daily_etf_universe_update.py#L256),
constructed with no injected `fetch`, which per
[core/market_data/providers/yahoo_finance.py:83–84](../core/market_data/providers/yahoo_finance.py#L83)
defaults to the real `urllib`-based `_http_get`.

Nothing about this requires an experiment-script refactor — `db_path`
injection is sufficient to point regeneration at the scratch database —
but it means the "no network access" guarantee for the v1-class
regeneration path is **incidental, not structural**: it holds only
because every `PriceBar` row the write pipeline would need already
exists in the scratch database (i.e., because the snapshot is complete,
§A.5). If the snapshot is ever incomplete, `run_daily_update` will not
error — it will silently attempt a live Yahoo Finance fetch to backfill
the gap, exactly the failure mode base §1.1 already documented as a
known live-ingestion behavior. This makes §A.5's completeness rule not
a hygiene nicety but the *actual* mechanism keeping reproduction
offline.

**Consequently, MUST HAVE (new, not in either the base proposal or the
correction as stated):** a reproduction-harness-level test that patches
`core.market_data.providers.yahoo_finance._http_get` (the same seam
`tests/test_yahoo_finance_provider.py` already exercises for offline
provider tests, per base §5.2) to raise on any call, then runs a full
reproduction cycle and asserts no exception was raised. This is a
network *fuse*, not a network *policy statement* — it proves the
offline invariant rather than documenting an intention. Because the
patch target is a private module function reached only through
`daily_etf_universe_update.run()`'s hardcoded construction, this test
must itself be re-verified (not just written once and trusted) if that
construction call is ever refactored — flagged as a coupling to watch,
not a blocker.

---

## A.5 — Snapshot completeness rules (amends §1.3–1.4)

`PriceBar` snapshots must cover three ranges, not one:

1. **Required evaluation period** — the dates the experiment actually
   scores/ranks/tests over (`dataset_manifest.json`'s
   `coverage.evaluation_period`).
2. **Maximum lookback window** — every prior trading day any indicator
   computed during regeneration needs (e.g., the longest SMA/RSI window
   in `IndicatorDefinition`) — must extend the snapshot's start date
   backward from the evaluation period's start, not just cover the
   visible interval (`coverage.max_lookback_start`).
3. **Forward return horizon** — every date needed to compute the forward
   returns the significance tests score against, extending the
   snapshot's end date forward past the evaluation period's end
   (`coverage.forward_horizon_end`).

A snapshot containing only the visible evaluation interval is **invalid**
— not merely incomplete. Per §A.4.3, an under-scoped snapshot doesn't
just produce a `REPRODUCTION_FAILED` from missing data; for the
v1-class regeneration path it produces a **live Yahoo Finance fetch**,
silently, inside what was supposed to be an offline verification run.

**Offline reproduction is a hard invariant.** Stated here as a named
principle because it is enforced in three independent places in this
design, deliberately redundant: (a) the reproduction harness never opens
a connection to any host other than `localhost`/the scratch SQLite file
(§A.4.2); (b) the snapshot completeness rule above removes the *reason*
a fetch would ever be attempted; (c) the network-fuse test (§A.4.3)
converts "no fetch happens" from an assumption into an assertion. Any
one of the three failing independently should still leave the other two
standing.

---

## A.6 — JSONL canonicalization, made explicit (amends §1.4)

Base §1.4 said "keys in a fixed order." That phrase is replaced with a
complete, unambiguous rule set — the previous wording left "fixed" doing
work it can't do alone (fixed *by what*, chosen *how*):

- **Encoding:** UTF-8, no BOM.
- **Line endings:** `\n` (LF) only — no `\r\n`, anywhere, on any
  platform the snapshot is generated on. (Named explicitly per the
  known CRLF test fragility already on record, per project memory:
  positive-control-study.)
- **Trailing newline:** file ends with exactly one `\n` after the final
  record — no missing terminal newline, no blank final line.
- **Key ordering:** alphabetical (codepoint order on the key string),
  applied independently to every JSON object in the file, including any
  nested objects.
- **Numeric representation:** any value that is `Decimal`-compatible
  `TEXT` in the source table (`open_amount`, `high_amount`, `low_amount`,
  `close_amount` in `PriceBar`) is preserved as a **string** in the
  JSONL row — never round-tripped through JSON's native number type,
  never through `float`, at any point in extraction or verification.
- **Row ordering:** deterministic, driven by the same index the live
  schema already provides —

  ```sql
  ORDER BY etf_id, session_date
  ```

  for `PriceBar` (matches `idx_pricebar_etf_session`, base §1.4); for
  the calendar snapshot,

  ```sql
  ORDER BY calendar_id, session_date
  ```

  (matches `TradingSession`'s primary key order, `migrations/0001_initial_schema.sql`).

These rules apply identically to both dataset types in §A.2's schema —
there is one canonicalization rule set for this design, not one per
dataset.

---

## A.7 — Confirmed unchanged (base §3, §4, §6, and named decisions)

Explicitly re-affirmed, not revised, not touched by any correction in
this amendment:

- Rejection of full-`experiments_etf_universe.db` snapshots (base §1.2).
- Rejection of Docker/Nix/Poetry/uv absent a real dependency-model change
  (base §4.2).
- `LEGACY_PROVENANCE_NOTE.md` treatment of the three legacy archives
  (base §3.2) — none of them gain a `dataset_manifest.json` under this
  amendment either; the calendar-snapshot addition applies to cycles
  opened after Phase 4 ships, same as everything else in base §3.
- Git as artifact storage at current scale, 20 MB soft ceiling (base
  §1.5).
- Zero-tolerance reproduction policy on non-float-derived figures, and
  the tolerance policy for `random.Random`/float-resampling statistics
  (base §2.3) — unaffected by removing `config_hash`, since the
  three-element contract (§A.3.2) still pins commit + dataset(s)
  exactly; only the *fourth* element was redundant, not the tolerance
  rule that depends on the other three.
- `FreezeVerifier` and `ReproductionStatus` (base §2.2) — the 4-state
  enum (`VERIFIED`/`DRIFTED`/`REPRODUCTION_FAILED`/`UNVERIFIABLE`) is
  unchanged; it now gates on three inputs instead of four, which
  changes nothing about the enum's semantics.

---

## A.8 — Dependency classification table (new)

| Dependency | Classification | Treatment |
|---|---|---|
| `PriceBar` | Frozen input | Dataset snapshot |
| `TradingSession` / `Calendar` | Frozen external reference data | Dataset snapshot |
| `IndicatorValue` | Derived deterministic state | Regenerate |
| `Score` | Derived deterministic state | Regenerate |
| `DimensionScore` | Derived deterministic state | Regenerate |
| `ETF` metadata | Code-defined (`_ensure_etfs`, universe literal) | Commit hash |
| `IndicatorDefinition` | Code-defined (`_ensure_indicator_definitions`) | Commit hash |
| `ScoringProfile` | Code-defined (`_ensure_scoring_profile`) | Commit hash |
| Migrations | Code artifact (`migrations/*.sql`, applied via `run_migrations`) | Commit hash |
| Random seeds / permutation & bootstrap counts / block lengths / horizons / date windows | Code artifact (module-level literals, §A.3.1) | Commit hash, **and** echoed in the result report (§A.3.3) |
| `exchange_calendars` package version | Generation-time tool dependency only | Not part of the reproduction contract at all (§A.2.1) — irrelevant once the calendar snapshot exists |

---

## Final Implementation Readiness Assessment

**Complexity, revised down from the base proposal's "moderate" estimate,**
because the two largest sources of estimated risk in the base proposal
turn out to already be solved or unnecessary:

- Base proposal flagged the injectable data-source seam as "the single
  largest unknown." Verified: it already exists (`db_path` on all five
  `experiments/validate_*.py` scripts). Removed from the risk list
  entirely (§A.4).
- `config_hash` generation/verification code — an entire artifact class
  the base design specified schema, hashing, and a CI test for — is
  removed outright as unneeded (§A.3).

**Remaining implementation work**, all net-new, none dependent on an
experiment-script refactor:

1. **Dataset extraction tool** — queries `PriceBar` for a stated
   universe + `coverage` ranges (§A.5) and writes canonical JSONL
   (§A.6). New code, no existing analog.
2. **Canonical JSONL writer** — shared by both dataset types (§A.2, §A.6);
   pure function, easily unit-tested against the exact rule set above.
3. **Calendar snapshot generator** — thin wrapper reading `TradingSession`
   for a `calendar_id` + date range and writing it through the same
   JSONL writer. Note: this tool, unlike the reproduction path itself,
   *does* need `exchange_calendars` already seeded into the source DB
   (via `experiments/seed_trading_calendar.py`, already committed) — it
   reads from `TradingSession`, it does not call `exchange_calendars`
   directly.
4. **Reproduction checker** (`core/governance/reproduction_checker.py`)
   — extends `freeze_verifier.py`'s pattern; now checks commit +
   N dataset entries (loop, not fixed four) + result hash. Slightly
   *simpler* than the base design's four-fixed-field checker because
   dataset entries are now a homogeneous list, not named singular
   fields.
5. **Scratch database loader** — runs existing migrations against a
   fresh temp-file SQLite DB, loads frozen JSONL rows for each
   `dataset_manifest.json` entry by `type`. New code; mechanically
   simple (migrations already exist and are idempotent, confirmed by
   `run_migrations` being called identically from every experiment
   script already).
6. **Network-fuse reproduction test** (§A.4.3) — patches
   `yahoo_finance._http_get` to raise, runs a full v1-class
   reproduction, asserts no call occurred. New, and specifically
   necessary because of the concrete gap found in §A.4.3, not a generic
   precaution.
7. **`tests/test_reproduction_contract.py`** — as base §5.2, minus the
   `config_hash` test, minus the dependency on a not-yet-existing
   injection seam (already satisfied).
8. **CI workflow** — unchanged from base §5.1/§5.3; still the one item
   with zero existing partial implementation to extend.

**Does this amendment change the base proposal's final claim?** No.
The claim in base proposal's closing section — *"every result from H4
onward is independently reproducible from the archive alone... every
result before it is exactly as trustworthy as it always was, honestly
labeled as predating this guarantee"* — holds unchanged. What changes is
*what* "independently reproducible" means for the derived tables: not
"a byte-identical frozen copy exists," but "the committed code, run
against the frozen inputs, reproduces it every time" — the strictly
stronger claim argued in §A.1.3.

---

## MUST HAVE / SHOULD HAVE / FUTURE ENHANCEMENT (revised)

| Tier | Item | Status vs. base proposal |
|---|---|---|
| **MUST HAVE** | `dataset_manifest.json` schema v2 — array of typed dataset entries (§A.2.2) | Revised (was v1, singular shape) |
| **MUST HAVE** | `PriceBar` snapshot: eval period + max lookback + forward horizon, all three, canonical JSONL (§A.5, §A.6) | Strengthened (base §1.3–1.4 didn't separate the three ranges) |
| **MUST HAVE** | Trading calendar snapshot (`TradingSession`/`Calendar`, canonical JSONL) (§A.2) | New |
| **MUST HAVE** | `reproduction_record.json` binding commit + N dataset hashes + report hash — **no `config_hash` field** (§A.3.2) | Revised (field removed) |
| **MUST HAVE** | Result report echoes every effective experiment parameter (seed, permutations, bootstrap iterations, block lengths, horizons, date windows) as a required, schema-checked field (§A.3.3) | New — direct mitigation for the removed `config_hash` |
| **MUST HAVE** | `ReproductionStatus` enum extending `FreezeStatus` (base §2.2) | Unchanged |
| **MUST HAVE** | Scratch-database reconstruction (migrations + frozen-row load), running existing `experiments/validate_*.py` scripts unmodified via `db_path` (§A.4.2) | Replaces base's "injectable data-source seam" item — already-existing capability, reframed as a harness responsibility, not an experiment-script change |
| **MUST HAVE** | Network-fuse test: patch `yahoo_finance._http_get` to raise, assert no call during a full reproduction run (§A.4.3) | New — surfaced by verification, not by either correction as originally stated |
| **MUST HAVE** | `LEGACY_PROVENANCE_NOTE.md` per legacy archive + shared `LEGACY_ARCHIVE_PROJECT_IDS` constant (base §3.2) | Unchanged |
| **MUST HAVE** | `.python-version` + `requires-python` + pinned `requirements-dev.txt` (base §4.2) | Unchanged |
| **MUST HAVE** | CI workflow running `pytest` on every push/PR (base §5.1, §5.3) | Unchanged |
| **MUST HAVE** | `tests/test_reproduction_contract.py`, merge-blocking (base §5.2–5.3), minus the `config_hash` sub-test | Revised |
| **SHOULD HAVE** | Documented snapshot size ceiling (20 MB), applies per-dataset-entry now that there are two dataset types (base §1.5) | Minor revision (scope clarified) |
| **SHOULD HAVE** | CI asserts interpreter matches `.python-version` (base §4.2) | Unchanged |
| **SHOULD HAVE** | Weekly scheduled full-suite CI run (base §5.3) | Unchanged |
| **SHOULD HAVE** | `ArchiveVerifier` treats "legacy + provenance note" as its own state (base §3.2) | Unchanged |
| **SHOULD HAVE** | Re-verify the network-fuse test's patch target if `daily_etf_universe_update.run()`'s provider construction is ever refactored (§A.4.3) | New, low-cost, explicitly a coupling to watch rather than a blocker |
| **FUTURE ENHANCEMENT** | External content-addressed storage past the size ceiling (base §1.5) | Unchanged |
| **FUTURE ENHANCEMENT** | Docker/Nix, only if AD-005 is revisited (base §4.2) | Unchanged |
| **FUTURE ENHANCEMENT** | Point-in-time (bitemporal) market data storage (base §6) | Unchanged |
| **FUTURE ENHANCEMENT** | WORM/branch-protection enforcement on archive history (base §6) | Unchanged |

---

## Explicitly unresolved after this amendment

Stated plainly, per this document's own adversarial mandate, rather than
implied to be closed:

1. **The residual config-drift risk (§A.3.3)** is a documentation/schema
   discipline, not a structural guarantee — nothing in this design
   *prevents* a future script from reading an unpinned parameter, it
   only makes the omission visible in the result report's required
   fields. A determined-enough mistake still slips through until a
   reproduction attempt actually fails.
2. **The network-fuse test's patch target (§A.4.3) is coupled to one
   specific function's current construction call.** It is not immune to
   silent invalidation if `daily_etf_universe_update.py` is refactored;
   this amendment does not add a structural guarantee against that,
   only a note to re-verify.
3. **`v2`/`h3`-class cycles have no live-network exposure at all**
   (§A.1.1) — the network-fuse test is strictly necessary only for
   `v1`-class regeneration paths. Whether to run it unconditionally for
   every cycle (defense in depth, cheap) or only for cycles that
   actually call `run_daily_update` is an implementation choice this
   amendment does not settle; the readiness assessment above assumes
   "unconditionally" as the safer default but this is a judgment call
   for whoever implements item 6, not a closed decision.
4. Everything the base proposal already listed as unresolved (§6's four
   remaining gaps — no point-in-time storage, no WORM guarantee, no
   Level 3 review, single-operator risk) is unaffected by this amendment
   and remains exactly as open as the base proposal stated.
