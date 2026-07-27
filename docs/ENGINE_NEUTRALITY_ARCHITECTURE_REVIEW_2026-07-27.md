# Engine Neutrality — Architecture Redesign Review

**Date:** 2026-07-27
**Reviewer role:** Principal Software Architect / Governance Reviewer
**Subject:** next-phase architecture for two unrelated workloads; replacement for the AD-076 draft
**Baseline:** branch `master`, HEAD `fd7a26c` + uncommitted Engine Boundary Cleanup working tree
**Review level:** **Level 1** — one reviewer with repository access. This document
discharges no independent-review requirement and must never be cited as an
independent review, the same standing `docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md`
declares for itself.

**Deliverable only.** No code was written, no file under `core/`, `tests/`,
`tools/`, or `research_archive/` was modified, and nothing was committed.

---

## 0. Executive summary

The previous audit's verdict is **confirmed by direct inspection**, and is if
anything understated. The governance spine is genuinely reusable. The
dataset and reproduction path is not merely "still workload-bound" — it is
*hard-bound*: `core/governance/dataset_manifest.py:116` would **reject** a
non-ETF dataset manifest as structurally invalid. A second workload cannot
produce a governed archive today. It cannot even parse a manifest.

Measured, not asserted:

| Governance module set | Modules | Lines | Share |
|---|---|---|---|
| Contains **no** workload vocabulary | 11 | 3,679 | **80.4 %** |
| Contains ETF schema semantics | 5 | 896 | 19.6 % |

The neutral 80 % is the asset. The bound 20 % sits precisely on the
reproduction path — which is the capability the incubator framing sells.

**Final decision: (B) Yes, but only after one limited neutrality phase.**
Evidence in §6.

**Recommended next milestone: Phase 1 — "ETF becomes a proper reference
workload."** It introduces **zero** new abstractions. Every item is either a
constant relocation, a parameter, or a rename. Its exit criterion is a green
import-boundary check and an unchanged `VERIFIED` reproduction of the sealed
`reference_h4` archive.

---

## 1. Evidence base

Everything below was read at the working-tree state, not inferred.

```
python -m tools.check_import_boundaries
→ FAILED: 2 violation(s) across 1 forbidden domain edge(s).
  data -> etf
    core/market_data/ingestion/price_ingestion.py:7   core.market_data.domain.models.ETF
    core/market_data/persistence/repository.py:15     core.market_data.domain.models.ETF
```

Workload vocabulary in engine-classified modules (grep, whole tree):

| Engine module | Workload names it hardcodes |
|---|---|
| `core/governance/dataset_manifest.py` | `REQUIRED_SOURCE_TABLES = {"ETF","PriceBar","TradingSession"}` |
| `core/governance/identity_verification.py` | `FROZEN_IDENTITY_TABLES`, `_ORDER_BY` (`etf_id`, `session_date`, `calendar_id`) |
| `core/governance/reconstruction_loader.py` | `paths["ETF"]`, `row["ticker"]`, `row["etf_id"]`, `row["calendar_id"]`; seven ETF-named error classes |
| `core/governance/reproduction_runner.py` | `UNIVERSE_MODULE_RELATIVE_PATH = "experiments/daily_etf_universe_update.py"`, `module.ETF_UNIVERSE`, `_DRIFT_ERRORS` |
| `core/governance/calendar_definitions.py` | `XNYS`, `"New York Stock Exchange"`, `"NYSE"`; imports `core.market_data.domain.models.Calendar` |
| `core/statistics/significance.py` | `"etf_ids"` panel key |
| `core/shared/pipeline_names.py` | `ticker` parameter, `price_ingestion:` / `scoring:` prefixes |

Confirmed **clean of workload semantics** — no workload name reaches
behaviour: `archive_identity`, `archive_seal`, `archive_verifier`,
`canonical_jsonl`, `decision_recorder`, `freeze_verifier`,
`independence_linter`, `network_guard`, `pinned_worktree`,
`reproduction_record`, `dataset_integrity`, all of `core/validation`,
`core/research`, `core/store`, `core/reporting`, and `core/shared` except
`pipeline_names`.

**One control-flow input inside that set is disclosed rather than
implied:** `archive_identity.py:54`'s `LEGACY_ARCHIVE_PROJECT_IDS`
(`reference_v1`, `reference_v2_h1`, `reference_h3`) is compared against
at `archive_seal.py:1077` and `archive_verifier.py:501`. Those literals
are **artifact / research-cycle identifiers**, not workload schema
vocabulary — no table, column, entity, or calendar name — so they do not
make these modules workload-bound. AD-077 clause 1a states this in full,
including that no artifact classification rule is created by saying so.

**Lexical mentions do exist in that set, and are named rather than
rounded to zero.** The inventory is **five modules at six locations**:
`core/governance/canonical_jsonl.py:2`,
`core/governance/reproduction_record.py:33`,
`core/governance/dataset_integrity.py:13`, `core/store/__init__.py:8`,
and `core/research/execution/experiment.py:8` and `:51`. The first four
name ETF in a docstring as an illustrative dataset name, a worked example
path, or a statement of what a neighbouring module owns. The two in
`experiment.py` are of a different form again: both are **negations** —
"this Protocol is domain-blind and carries no ETF-specific logic" (`:8`)
and "No implementation, no ETF-specific logic" (`:51`). They assert the
absence of the coupling, not its presence, and a lexical scan that
counted them as vocabulary would be counting a disclaimer as a
dependency.

None of the six is a constant, a dict key, a comparison, or a
control-flow input, which is why the semantics claim above stands and the
"zero vocabulary" phrasing does not. **Lexical vocabulary presence is not
workload semantic coupling**, and the two must not be collapsed: the
former is a grep result, the latter is a statement about what reaches
behaviour, and only the latter is what 1a claims. The distinction is
review-derived; **no test asserts it**, and this review introduces no
lexical scanner.

---

## 2. Two findings the cleanup record does not contain

These change the shape of the next phase and must be resolved before Phase 1
is executed.

### F-1 (critical) — Renaming anything public in `core/` is a reproducibility change

> **Status: DISCHARGED** by `docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md`
> **§11.2** (live sealed-cycle reproduction of `reference_h4` returning
> `verified`, exit 0) and **§11.3** (pinned-import compatibility: 45
> distinct `(module, symbol)` pairs across 20 core modules resolved, 0
> unresolved; no symbol removed by C1 or C4 is required by any pinned
> reproduction). The empirical question this finding raised is answered
> and the answer is favourable. The finding's *analysis* — that a
> rename in `core/` is a reproduction-compatibility change — is
> unaffected by the measurement and remains the basis for AD-077 clause 5.
> The text below is the finding as originally written and is retained
> unedited except for this marker.

`core/governance/reproduction_runner.py` documents that a pinned commit's
experiment script resolves its `core.*` imports through **HEAD's** package,
not the worktree's:

> "There is no `sys.modules` isolation anywhere in `core/`."

The pinned universe module is real and it imports real names:

```
experiments/daily_etf_universe_update.py
    from core.market_data.domain.models import ETF
    from core.market_data.persistence.database import connect
    from core.analytics.persistence.repository import ...
```

`research_archive/reference_h4/reproduction_record.json` pins
`commit_hash = 3d586ded…` with `reproduction_status: verified`. That verdict
is only reproducible while HEAD's `core/` still exports every name that
commit's scripts import.

**Consequence.** The just-completed cleanup already carries this risk:
`ETFId` was renamed (C1), `core.governance.dataset_snapshots` was **deleted**
(C4), and `reconstruct_database` gained two required parameters (C4). Whether
`reference_h4` still reproduces is an **empirical question that the cleanup
record does not answer** — the suite's 996 passing tests do not include an
end-to-end re-run of `tools/reproduce_cycle.py` against the sealed archive.

**Action, before anything else:** run

```bash
python -m tools.reproduce_cycle research_archive/reference_h4 --experiment-module experiments/validate_h4_kurtosis.py
```

and record the outcome. If it is not `VERIFIED`, that is a Phase-0 blocker and
this review's phasing is void until it is resolved. This is a ten-minute check
that decides whether the platform's central claim still holds.

**Outcome, recorded:** run and `verified` — cleanup record §11.2. The
experiment module named here is the one `reference_h4` actually
reproduces through; `experiments/daily_etf_universe_update.py` is the
*universe* module `reproduction_runner` hardcodes, which is a different
file and is the subject of finding N-1 (cleanup §11.4), not of this one.

### F-2 (high) — The `ETF` aggregate contains nothing ETF-specific

```python
class ETF:
    etf_id: InstrumentId
    ticker: str
    name: str
    currency: str
    calendar_id: str
    created_at: datetime
```

Not one field distinguishes an ETF from an equity, a bond, or a currency pair.
The two remaining `data -> etf` violations are therefore a **naming** defect,
not a coupling defect. `§9.1` of the cleanup record defers them as
"abstraction ahead of a second concrete need" — but renaming a class to what it
already is introduces no abstraction and no seam. C1 renamed the identifier
(`ETFId → InstrumentId`) and stopped short of the aggregate the identifier
identifies; C1 is simply incomplete.

The genuine difficulty is elsewhere and is F-1: `ETF` is a name imported by
the script at the **pinned commit named by the cycle's
`reproduction_record.json`** — not by the commit an Archive Seal witnesses,
which is a separate mechanism (AD-074/AD-075) and a different commit. That
makes the rename a *shim-policy* decision, not an *abstraction* decision —
and it should be re-argued on those grounds.

---

## 3. Target architecture (minimal, for exactly two workloads)

No registry. No dependency-injection framework. No dynamic discovery. No base
classes. Three layers and one rule.

```
┌── ENGINE ─────────────────────────────────────────────────────────────┐
│ core/governance   lifecycle records, freeze verification, archive     │
│                   sealing, manifest parsing, integrity, offline       │
│                   guard, pinned worktrees, reproduction orchestration │
│ core/validation   Gate protocol, GateRunner, gate records             │
│ core/research     Project, lifecycle phases, Experiment protocol,     │
│                   MeasurementBundle                                   │
│ core/statistics   pure numerics                                       │
│ core/store        connect(), run_migrations(dir)                      │
│ core/shared       Clock, Money, LifecyclePhase, InstrumentId          │
│                                                                       │
│ Knows: phases, gates, freezes, seals, manifests, hashes, records.     │
│ Knows nothing about: table names, column names, entities, calendars.  │
└───────────────────────────────────────────────────────────────────────┘
                              ▲ values and callables passed in
┌── WORKLOAD ───────────────────────────────────────────────────────────┐
│ ETF (reference)          core/analytics + the ETF half of             │
│                          core/market_data + migrations/               │
│ ML validation (#2)       workloads/mlval/ + workloads/mlval/migrations│
│                                                                       │
│ Owns: domain models, SQL schema, row↔object serialization, the        │
│ frozen-table set, the frozen-identity table spec, semantic validation │
│ rules, coverage expectations, seed literals.                          │
└───────────────────────────────────────────────────────────────────────┘
                              ▲ chosen here
┌── COMPOSITION ROOT ───────────────────────────────────────────────────┐
│ tools/*.py, experiments/*.py                                          │
│ The only files permitted to name an engine module and a workload      │
│ module together. Precedent already set: tools/reproduce_cycle.py.     │
└───────────────────────────────────────────────────────────────────────┘
```

**The one rule (enforceable):** *a module may import the engine, or the engine
plus exactly one workload — never two workloads.* Engine may never import a
workload. This is checkable by extending the existing AST walker in
`tools/check_import_boundaries.py` to scan outside `core/`; roughly twenty
lines, and it closes the enforcement gap that the **withdrawn, never-accepted**
AD-076 draft's clause 3 admitted it had. The gap is real and is measured here
independently; the withdrawn draft is cited as the place it was first written
down, not as live authority for it.

**Where workload selection happens.** In the composition-root file, as a
literal two-entry mapping over two names known at edit time. This is the same
construct `core/analytics/persistence/frozen_dataset.py:41` already uses and
already defends in its own docstring:

> "**Not a registry.** … Nothing registers into it at runtime, nothing
> discovers it, and an unknown `source_table` raises rather than being
> skipped."

Adding a workload is a file edit, which is the intended cost.

**On a `WorkloadProfile` parameter object.** The engine will eventually need
about eight things from a workload (required tables, identity table spec,
`parse_row`, `load_rows`, semantic validator, coverage provider, migrations
directory, seed step). Threading eight loose parameters through three call
layers is worse than one frozen dataclass — but **it must not be created in
Phase 1**, when there is one implementation and it would be shaped by one
workload. Trigger for introducing it: *four or more workload-supplied
parameters threaded through two or more call layers, with two real
constructors in existence.* That is AD-069's demand-driven growth rule applied
to a parameter object.

### Choice of workload #2: **(b) ML model validation** — recommended

| | Biomedical lab | ML model validation |
|---|---|---|
| Distance from ETF | greater | sufficient |
| Developer competence | absent | present |
| Data obtainable, locally reproducible | hard | easy (fixed split + pinned seed) |
| Risk of a *fabricated* research cycle | **high** | low |
| Fit to the stated pitch | none | direct |

Biomedical is the better *neutrality* proof and the worse *credibility* bet. A
governance platform whose second workload is a research cycle its author cannot
honestly conduct undermines the exact property it sells. ML validation is
simultaneously the architectural proof and the pitch demo, and reproducibility
there is genuinely meaningful (seed pinning, split hashing, determinism).

**The risk of choosing ML is that it is too similar and fails to break the
false abstractions.** Mitigate by making the divergence contract binding —
see §5, Phase 2.

---

## 4. Classification of the six named couplings

Legend: **E** engine concern · **W** workload concern · **C** composition
concern · **D** defer until workload #2.

### A) `core/governance/dataset_manifest.py` — **E + W, split now (Phase 1)**

The parser, the `sha256:` prefix rule, the per-entry field requirements, the
schema-version check, the duplicate-`source_table` check and the "a manifest
declares a *closed* set of datasets" invariant are all engine. Exactly one
thing is not:

```python
REQUIRED_SOURCE_TABLES = frozenset({"ETF", "PriceBar", "TradingSession"})
```

**Why this is the single most important item in the review.** Line 116 raises
`DatasetManifestError` for any manifest whose table set differs. A second
workload does not degrade here — it is refused. Every downstream governance
control (`dataset_integrity`, `archive_seal`, `archive_verifier`,
`reconstruction_loader`) funnels through this parser, so this one constant
makes the entire archive apparatus ETF-only.

**Move:** the set becomes a required keyword parameter with no default, and
relocates to the ETF workload beside `frozen_dataset._ROW_PARSERS`, which
already declares itself the owner of the same three names. Precedent is exact:
C4 made `parse_row`/`load_rows` required with no default because "a default
would silently degrade validation for a caller who forgot one."

**Seal safety:** `schema_version` stays `3`. The sealed manifest's bytes are
untouched; only *who supplies the expected table set* changes. Verification of
`reference_h4` is bit-identical.

### B) `core/governance/identity_verification.py` — **E + W, split now (Phase 1)**

The invariant — *frozen identity must never regenerate across a reproduction
run* — is one of the platform's strongest governance ideas and is entirely
domain-neutral. The mechanism (ordered hash, row-count delta, named-table
error) is neutral. The data is not: `FROZEN_IDENTITY_TABLES` and `_ORDER_BY`
are ETF's four tables and their SQL key columns.

Identical shape to (A), identical move: the table→order-by mapping becomes a
parameter the workload supplies. Note the docstring's own warning that scope
"too narrow … too broad" are both failure modes — that argues for the spec
being *explicit and owned*, which is what this move achieves.

### C) `core/governance/reconstruction_loader.py` — **W, misplaced in engine; defer the split to Phase 2**

The most misclassified module in the tree, and the clearest evidence that C4
was incomplete. C4 removed *object construction*; it did not remove *schema
semantics*. What remains in `preflight_validate` is ETF's data model spelled
out in an engine module:

- table names as dict keys — `paths["ETF"]`, `paths["TradingSession"]`, `paths["PriceBar"]`
- column names — `row["ticker"]`, `row["etf_id"]`, `row["calendar_id"]`, `row["session_date"]`
- which uniqueness constraints exist, and on which composite keys
- which cross-table reference must resolve (`PriceBar.etf_id → ETF.etf_id`)
- that a "calendar" exists at all, and that two tables reference it
- seven error classes named after ETF concepts, re-exported into `reproduction_runner._DRIFT_ERRORS` (counted directly in the module; `docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md` §8.2 enumerates them)

Genuinely engine, and worth preserving exactly as-is: `_verify_dataset_integrity`
(hash + row count vs. manifest), canonical-JSONL reading, the
`ScratchDatabaseExistsError` guard, the "all pre-flight before the database is
touched" ordering, and the transaction structure.

**Why defer.** Splitting requires deciding the workload validator's *contract*
— per-table callbacks? one whole-dataset callback? a declarative constraint
description? — and each answer would be shaped by ETF's FK topology alone.
That is exactly the abstraction-ahead-of-need this repository refuses. The
correct shape is knowable only once a workload with a different topology
exists.

**Phase 1 does one free thing:** introduce a single engine-side
`DatasetSemanticsError` that workload validators raise, so `_DRIFT_ERRORS` stops
being a list of ETF error classes. That is a taxonomy fix, not a seam.

### D) `core/governance/reproduction_runner.py` — **E, with two workload leaks; Phase 2**

The orchestration is engine and is good: offline guard installed first, pinned
worktree, status mapping (`UNVERIFIABLE`/`DRIFTED`/`REPRODUCTION_FAILED`/
`VERIFIED`), the deliberate refusal to remap execution-phase `ImportError`.
That state machine transfers to any workload unchanged.

Two leaks:

1. `UNIVERSE_MODULE_RELATIVE_PATH = "experiments/daily_etf_universe_update.py"`
   plus `module.ETF_UNIVERSE`, plus the literal string comparison at line 233
   that decides whether the coverage check runs. An engine module hardcoding a
   path to one workload's script is the sharpest single instance of the
   misclassification.
2. `_DRIFT_ERRORS` — resolved by (C)'s taxonomy fix.

The *concept* — "a hash match confirms the file did not change, not that it
still covers the universe the pinned code will iterate over" — is excellent and
fully general. Only its ETF binding must move: the workload supplies a
`load_expected_coverage(worktree_path)` callable, or `None` for a workload with
no coverage notion. Paired with (C) in Phase 2 because they are one seam.

### E) `migrations/` — **C, composition concern; no engine change required**

The seam already exists and is already proven. `core/store/migrations.py` takes
the directory as an argument and documents itself as "neutral about *what* the
SQL creates"; `run_reproduction` already takes `migrations_relative_path`;
`tools/reproduce_cycle.py` already defaults it as a flag. Workload #2 gets
`workloads/mlval/migrations/` and passes it. Nothing in the engine changes.

Three ownership notes: `schema_migrations` is engine (created in code by the
runner). `Calendar`/`TradingSession`/`ETF`/`PriceBar` and
`IndicatorDefinition`/`IndicatorValue`/`ScoringProfile`/`Score`/`DimensionScore`
are ETF workload. `IngestionRun`/`PipelineState` are market-data operational
tables and travel with the ETF workload. **Nothing may be edited:**
`migrations/README.md` freezes an applied migration forever, so `0001`–`0003`
stay exactly as they are and the classification is documentation only.

### F) `core/statistics/significance.py` "etf_ids" — **E, cosmetic; defer to Phase 3, and never break the alias**

The module is genuinely neutral — the ids are opaque dictionary keys and the
docstring is honest that the name is "inherited verbatim from the source
script as part of its data contract." Zero functional coupling, but it is the
one place where a reader scanning for neutrality finds "etf" in a module whose
docstring claims to be domain-blind. Presentational cost, real.

**Do not rename it in Phase 1.** Per F-1, `experiments/positive_control_phase3_pilot.py`
imports `core.statistics.significance`, and pinned scripts bind HEAD's `core`.
A rename would alter the panel contract for every sealed cycle that reproduces
through it. If it is ever renamed to `entity_ids`, `etf_ids` must be accepted
permanently as an alias, and the change belongs in Phase 3 after workload #2
has actually called `mean_ic` and proven the contract generalizes.

### Not on the list, but should be — `core/governance/calendar_definitions.py` — **W, misplaced in engine; Phase 1**

A governance module that hardcodes the New York Stock Exchange and imports
`core.market_data.domain.models.Calendar` and `insert_calendar`. It is inside
the allowed `governance -> data` edge, so no tool sees it — which is precisely
why review found it and tooling did not. `reconstruct_database` even carries
`calendar_id: str = "XNYS"` as a **default** in an engine signature, three
weeks after C4 removed defaults on the same function's other workload
parameters for the stated reason that silent defaults degrade validation.

A biomedical or ML workload has no calendar at all. The general concept is
"the workload seeds code-defined literals the frozen datasets reference" — so
the module moves to the ETF workload and `reconstruct_database` takes a
`seed(conn)` callable. This also removes governance's last import of
`core.market_data`.

### Summary table

| Item | Class | Phase | Rationale |
|---|---|---|---|
| A `dataset_manifest` | E + W constant | **1** | One constant makes the whole archive apparatus ETF-only |
| B `identity_verification` | E + W constant | **1** | Same shape as A; neutral invariant, workload data |
| C `reconstruction_loader` | **W in engine** | **2** | Split shape unknowable with one topology |
| D `reproduction_runner` | E + 2 leaks | **2** | Same seam as C |
| E `migrations/` | **C** | **2** (use only) | Seam already exists and is parameterized |
| F `significance."etf_ids"` | E, cosmetic | **3** | Rename is a reproduction-contract change (F-1) |
| + `calendar_definitions` | **W in engine** | **1** | Trading calendar in the governance engine |

---

## 5. Transition path

Governing distinction, applied throughout: **a parameter is not an
abstraction; an interface is.** Phase 1 moves values. Phase 2 builds a second
concrete thing. Phase 3 abstracts only what two concrete things proved.

### Phase 0 (prerequisite, hours) — **satisfied**

Run `tools/reproduce_cycle.py` against `research_archive/reference_h4` and
record the outcome (F-1). Commit the current cleanup only after that outcome is
known. If it is not `VERIFIED`, stop and resolve.

**Done.** Cleanup record §11.2 records `verified` (exit 0) via
`experiments/validate_h4_kurtosis.py`, and §11.3 records pinned-import
compatibility. Phase 0 is no longer a blocker on Phase 1.

### Phase 1 — "ETF becomes a proper reference workload"

**Goal:** every workload fact currently hardcoded in an engine module becomes a
value the ETF workload supplies. **New abstractions introduced: zero.**

| # | Change | Files |
|---|---|---|
| 1.1 | `parse_dataset_manifest(path, *, required_source_tables)` — required, no default; ETF set relocates | `core/governance/dataset_manifest.py`, `dataset_integrity.py`, `archive_seal.py`, `archive_verifier.py`, `reconstruction_loader.py`, `core/analytics/persistence/frozen_dataset.py`, `tools/reproduce_cycle.py` |
| 1.2 | `snapshot_identity_state(conn, *, table_order)`; `FROZEN_IDENTITY_TABLES`/`_ORDER_BY` relocate | `core/governance/identity_verification.py`, `reproduction_runner.py`, `core/analytics/persistence/frozen_dataset.py` |
| 1.3 | `calendar_definitions` moves to the ETF workload; `reconstruct_database` takes `seed(conn)` instead of `calendar_id="XNYS"` | `core/governance/calendar_definitions.py` (moved), `reconstruction_loader.py`, `tools/reproduce_cycle.py` |
| 1.4 | Engine-side `DatasetSemanticsError`; `_DRIFT_ERRORS` stops naming ETF classes | `core/governance/reconstruction_loader.py`, `reproduction_runner.py` |
| 1.5 | Boundary checker also scans `tools/`, `experiments/`, `research_artifacts/`; enforces "at most one workload per file" | `tools/check_import_boundaries.py`, `tests/test_import_boundaries.py` |
| 1.6 | **Conditional** — `ETF → Instrument` rename (class only; SQL table, JSONL keys, dataclass fields unchanged), with a permanent `ETF = Instrument` reproduction shim | `core/market_data/domain/models.py`, `price_ingestion.py`, `repository.py` |

**1.6 is gated on an AD, not on effort.** The rename discharges both remaining
`data -> etf` violations and turns the checker green, and F-2 shows it is a
rename rather than an abstraction. But the shim it requires is a *policy*
question: a permanent alias keeps an ETF-named symbol in a Data module, so
`ETF_SYMBOLS_BY_MODULE` must gain an explicit "reproduction shim" category with
a test asserting each shim is actually imported by at least one pinned commit
— otherwise the category becomes the silent-exemption escape hatch AD-049 part
5 exists to close. Decide the shim policy in AD-077 first; then execute 1.6
last, or defer it to Phase 3. **Do not execute 1.6 by treating the alias as
incidental.**

**Risk: low, except 1.6 (medium).** Every change is mechanical and every one is
covered by an existing test. The single real hazard is a regression in sealed
archive verification.

**Verification gate — run before and after *each* item:**
`tests/test_sealed_snapshot_byte_identity.py`, `tests/test_sealed_archive_integrity.py`,
and a live `python -m tools.reproduce_cycle research_archive/reference_h4 …`
returning `VERIFIED`. The byte-identity test already proved its worth on C4;
the live reproduction is the control that was missing.

**Do NOT change in Phase 1:** sealed bytes under `research_archive/`;
`schema_version = 3`; JSONL key names; `migrations/0001`–`0003`;
`DecisionRecord`'s field set; the Archive Seal; `LifecyclePhase`;
`core/statistics` (F stays deferred); the `Experiment` Protocol. Do **not**
create a `WorkloadProfile` dataclass, a `workloads/` directory, a plugin
registry, a second migrations directory, or any interface with one
implementation.

**Exit criteria:** `python -m tools.check_import_boundaries` exits 0; the
strict `xfail` in `tests/test_import_boundaries.py` is removed (not relaxed);
the seven engine modules of §1 no longer hardcode a workload *constant, dict
key, or comparison* (a review-derived criterion, judged by reading — there is
no lexical test and none is proposed); `reference_h4` still `VERIFIED`;
AD-077 accepted.

### Phase 2 — "Introduce second workload"

**Goal:** one real, minimal, honestly-conducted ML-validation research cycle,
carried end to end through the same engine: hypothesis → methodology freeze →
frozen dataset → one gate → decision → archive → reproduction.

**Binding divergence contract.** Workload #2 is worthless as a proof unless it
breaks assumptions. It **must** have:

1. a frozen-table count that is **not three**;
2. **no** calendar and **no** time axis;
3. at least one **composite** primary key;
4. entity identifiers that are not tickers and are not the same shape as `InstrumentId`;
5. **at least one frozen artifact that is not canonical JSONL** — e.g. an `.npz`
   eval split or a model checkpoint.

Requirement 5 is the highest-value item in the entire plan. It is the only test
of whether `dataset_manifest`'s entry schema generalizes: a binary artifact has
a `content_hash` but no `row_count`, which forces an honest artifact-kind
discriminator. Handle it as **schema v4, strictly additive**, with v3 still
accepted so the sealed `reference_h4` manifest verifies unchanged.

**Files affected:** new `workloads/mlval/**` (models, migrations, row
conversion, semantic validator, coverage provider), new
`tools/reproduce_cycle.py` workload selection (a literal two-entry mapping),
new `research_archive/<mlval_cycle>/`, plus the engine changes workload #2
*physically forces* — predicted to be `reconstruction_loader` (C),
`reproduction_runner` (D), and `dataset_manifest` v4. Each engine change is
recorded with the specific blockage that forced it.

**Risk: high on scope, low on regression.** The regression surface is small
because the ETF path is untouched. The real risks are (i) scope inflation into
a full second product, and (ii) — more serious — workload #2 becoming a
*fabricated* research cycle. For a platform whose entire value proposition is
governance, presenting a synthetic cycle as research would be self-refuting.
Mitigation: the cycle's `research_outcome` is recorded honestly whatever it is,
and its `hypothesis.md` states plainly that the cycle exists to exercise the
engine.

**Do NOT change in Phase 2:** anything in the ETF workload except at a seam
workload #2 actually forces; sealed archives; the two workloads' models must
**not** be unified, and no shared base type may be introduced between them. No
third workload. No `WorkloadProfile` unless its stated trigger fires.

### Phase 3 — "Generalize only proven seams"

Nothing here is pre-authorized. Each item has a trigger; if the trigger does not
fire, the item is not done.

| Candidate | Trigger |
|---|---|
| `WorkloadProfile` frozen dataclass | ≥4 workload parameters threaded through ≥2 call layers, with 2 real constructors |
| `etf_ids → entity_ids` (+ permanent alias) | workload #2 actually calls `mean_ic`/`top_bottom_spread` |
| Move ETF workload under `workloads/etf/` | workload #2's layout has proven the shape |
| Reproduction-shim policy AD | 1.6 executed, or a second rename becomes necessary |
| `pipeline_names` out of the kernel | a second workload needs pipeline naming |

**Risk: low if trigger-gated.** The actual danger is doing Phase 3 work *during*
Phase 2 — generalizing while the second instance is still being written,
against a shape that is still moving.

**Do NOT change in Phase 3:** anything with one instance; the `Experiment`
Protocol (structural typing is correct — do not give it a base class); the
`Gate` protocol; `LifecyclePhase`. Build no plugin loader, no entry-point
discovery, no configuration-driven workload selection.

---

## 6. AD-077 — replacement for the AD-076 draft

### 6.1 Why AD-076 cannot be accepted as drafted

**Status first, so nothing below reads as a critique of a live decision:**
AD-076 was drafted, then **withdrawn undelivered** — never appended to
`docs/ARCHITECTURE_DECISIONS.md`, never accepted, never cited
(`docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md` §8). The three defects below
are why it was withdrawn and are the requirements AD-077 must meet; they
are not defects in the accepted decision log, which never contained them.

Three defects, all checkable:

1. **Clause 4 is factually false.** It states that `ETFId` and `reference_h4`
   "were the two live instances; both are discharged." §1 of this review lists
   **seven** engine modules that still name a workload concept, five of them in
   `core/governance/`. The correct statement is "two of nine are discharged."
   An accepted decision containing a false completeness claim is worse than no
   decision.
2. **Clause 1 contradicts the repository's own tooling.** It classifies
   `core/market_data` as **Engine**, while `tools/check_import_boundaries.py`
   simultaneously reports two ETF-domain violations inside that package. A
   classification that the project's own checker refutes cannot be the
   authority for future classifications.
3. **It has no rule about renames.** F-1 shows that removing or renaming a
   public name in `core/` can silently invalidate a sealed cycle's
   reproduction verdict. That is the highest-consequence classification rule
   the repository needs, and AD-076 does not mention it.

### 6.2 The entry, as appended

> ### AD-077: The governance spine is workload-neutral in semantics; the dataset and reproduction path is not. Each claim is stated separately. (accepted 2026-07-27)
>
> **Relationship to AD-076.** This decision **replaces the withdrawn,
> never-accepted AD-076 draft** in `docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md`
> §8. It does **not** supersede AD-076, because there is no AD-076 to
> supersede: that draft was never appended to
> `docs/ARCHITECTURE_DECISIONS.md`, never cited by a test, never
> referenced by an accepted decision, and never used to authorize any
> item in the cleanup. **AD-076 remains unconsumed** and is not spent by
> this decision, by the cleanup record, or by the review that carries it.
> "Supersedes AD-076" is the wrong verb and is not used anywhere in this
> entry, because superseding a number consumes it. **"Unconsumed" here means
> "nothing was decided under it" — it does not mean the number is
> available for reuse; see *Numbering* below, which reserves and retires
> AD-076 and starts new numbering at AD-078.**
>
> **Review basis.** **Level 1 — self-review.** One reviewer with
> repository access, working against the branch `master` working tree at
> HEAD `fd7a26c` plus the uncommitted Engine Boundary Cleanup. **Level 3
> is unavailable and no Level 3 review was performed. This is not an
> independent review, and neither this entry nor the review document that
> carries it may be cited as one** (`docs/RESEARCH_GOVERNANCE_STANDARD.md`
> §4). Nothing in this entry asserts organizational independence, a
> distinct accountable party, or an external reviewer, because none exists
> on this platform. This is the same standing AD-068 and AD-069 declare
> for their own basis.
>
> **Numbering.** AD-070 and AD-071 remain unconsumed, for the reason
> AD-072, AD-073, AD-074, and AD-075 all record.
>
> **AD-076 is reserved and retired. It is not available, and it must not
> be described as free, open, or reusable.** The facts and their
> consequence, separately:
>
> - **What happened.** AD-076 was **drafted, withdrawn, and never
>   appended** to `docs/ARCHITECTURE_DECISIONS.md`. It was never cited by
>   a test, never referenced by an accepted decision, and never used to
>   authorize any item in the Engine Boundary cleanup. Nothing was decided
>   under it (`docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md` §8, §8.1).
> - **What that does not imply.** "Nothing was decided under it" does
>   **not** make the number recyclable. The number has a public trail: it
>   is named in the cleanup record's status table, in §8's withdrawal
>   notice, and throughout this review. Re-issuing AD-076 for an unrelated
>   decision would give one number two meanings across the written record,
>   which is exactly the ambiguity an append-only decision log exists to
>   prevent.
> - **Where its meaning went.** AD-076's substance is **disclosed and
>   mapped into AD-077**, not discarded: §6.1 of the carrying review
>   (`docs/ENGINE_NEUTRALITY_ARCHITECTURE_REVIEW_2026-07-27.md`)
>   states the three defects that caused the withdrawal, and this entry's
>   clauses 1, 2, and 3 carry forward what survived — the two-part
>   neutrality claim, the three-class axis (corrected on
>   `core/market_data`), and per-rule enforcement (corrected on the
>   enforcement gap AD-076 clause 3 admitted). A reader who follows the
>   number arrives at this entry.
> - **Consequence for numbering.** **New ADR numbering starts from
>   AD-078.** AD-076 is retired in place and AD-077 is this entry.
>
> AD-076 is nonetheless **unconsumed in the append sense** and stays that
> way: withdrawing it spends nothing, and no step in this review appends
> it. "Retired" describes the number; "unconsumed" describes the log.
> Neither licenses reuse.
>
> This entry reserves no number for Phase 1.6's reproduction-shim policy,
> for Phase 2, or for Phase 3; each is recorded as unassigned rather than
> referred onward to a plan that does not exist. Any such number is
> allocated at the time the decision is written, from AD-078 upward.
>
> **Status.** **Accepted, 2026-07-27.** Documentation only: no code,
> test, tooling, fixture, archive, or CI change.
>
> *(Carrier note, not part of the entry. This Status line is the text
> that stands in `docs/ARCHITECTURE_DECISIONS.md`, where this entry has
> now been appended; the `DRAFT — not accepted` marker that governed
> before the append is removed. §6.2 is the carrier's record of what was
> appended — the decision log holds the accepted text, and this note is
> not part of it.)*
>
> **Context.** Engine Boundary cleanup C1–C6 discharged the `governance -> etf`
> import edge and produced a genuine improvement. It also produced a draft
> decision claiming a neutrality the tree does not have. This decision records
> what is true, in two parts, so that neither part can be cited as the other.
>
> **Decision.**
>
> **1. The neutrality claim is two claims, and they are stated separately.**
>
> - **1a. The governance spine is workload-neutral in semantics.**
>   `archive_identity`, `archive_seal`, `archive_verifier`,
>   `canonical_jsonl`, `dataset_integrity`, `decision_recorder`,
>   `freeze_verifier`, `independence_linter`, `network_guard`,
>   `pinned_worktree`, `reproduction_record`, and all of
>   `core/validation`, `core/research`, `core/store`, and
>   `core/reporting` contain **no workload fact that reaches behaviour** —
>   no **workload schema name** appears in these modules as a constant, a
>   dict key, a comparison, a parameter default, or any other control-flow
>   input.
>
>   **"Workload schema name" is the load-bearing term and is defined
>   here:** a table name, a column name, a domain entity name, or a
>   calendar identifier — the vocabulary of a workload's data model.
>   Identifiers naming a *particular artifact this platform produced* are
>   a different kind and are **not** covered by that term; the one such
>   case in this module set is `LEGACY_ARCHIVE_PROJECT_IDS`, disclosed in
>   full below rather than left implicit in the word "workload".
>
>   **This is a semantics claim, and it is review-derived.** It was
>   established by reading the modules, not by a tool, and **no test
>   currently asserts it.** It is not pinned by test, and no statement in
>   this decision, in `docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md`, or in
>   the review that carries this entry may describe it as pinned,
>   enforced, or asserted by test.
>
>   **Lexical mentions exist inside this set and are named here rather
>   than rounded away.** The inventory is **five modules at six
>   locations**:
>
>   | Location | Form of the mention |
>   |---|---|
>   | `core/governance/canonical_jsonl.py:2` | dataset names as an illustrative list |
>   | `core/governance/reproduction_record.py:33` | dataset names in a field's worked description |
>   | `core/governance/dataset_integrity.py:13` | a worked example path (`dataset_hashes/ETF.jsonl`) |
>   | `core/store/__init__.py:8` | names what a *neighbouring* module owns |
>   | `core/research/execution/experiment.py:8` | **negation** — "domain-blind and carries no ETF-specific logic" |
>   | `core/research/execution/experiment.py:51` | **negation** — "No implementation, no ETF-specific logic" |
>
>   Each is prose. None is read by code. The last two are **negations**:
>   they state that the module carries *no* ETF-specific logic, so they
>   are disclaimers of coupling rather than instances of it, and they are
>   listed here only because a lexical scan would return them.
>
>   **Lexical vocabulary presence is not workload semantic coupling.**
>   This decision claims the latter and not the former: 1a is a statement
>   about what reaches behaviour, and a grep count of the string `ETF`
>   neither establishes nor refutes it. Any restatement of 1a as "zero
>   occurrences of the string" is a different — and false — claim.
>
>   The enumeration above is the complete known set **at this
>   working-tree state**; it is a snapshot, not a guarantee of
>   exhaustiveness, and it will go stale as modules change. **This
>   decision introduces no lexical scanner and authorizes none.** A future
>   decision may propose one; that is a separate AD with its own cost
>   argument, and the absence of one here is deliberate, not an oversight.
>
>   **Disclosure — `LEGACY_ARCHIVE_PROJECT_IDS` is a control-flow input
>   inside this set, and is named here rather than left for a reader to
>   find.** Three of the modules 1a lists do compare against a frozen set
>   of literal identifiers:
>
>   | Location | Form |
>   |---|---|
>   | `core/governance/archive_identity.py:54` | `LEGACY_ARCHIVE_PROJECT_IDS = frozenset({"reference_v1", "reference_v2_h1", "reference_h3"})` |
>   | `core/governance/archive_seal.py:1077` | `if identity.project_id in LEGACY_ARCHIVE_PROJECT_IDS` — a legacy archive is never sealed (AC-74-9) |
>   | `core/governance/archive_verifier.py:501` | `if manifest is None and archive_dir.name in LEGACY_ARCHIVE_PROJECT_IDS` — exemption from the v1 layout check, reached only when no `archive_manifest.json` is present |
>
>   These are real comparisons and they really do reach behaviour, so
>   they are disclosed rather than covered by 1a's "no … comparison"
>   phrasing. **They are not a counterexample to 1a**, for a reason that
>   is stated rather than assumed: `reference_v1`, `reference_v2_h1`, and
>   `reference_h3` are **artifact and research-cycle identifiers — the
>   names of three specific archives this platform produced — not
>   workload schema vocabulary.** They are not table names, column names,
>   entity names, or calendar identifiers; they name *instances*, not a
>   *schema*. A second workload's archives get their own identifiers and
>   are unaffected by this set, whereas a second workload is refused
>   outright by `dataset_manifest`'s `REQUIRED_SOURCE_TABLES` (1b). That
>   is the difference 1a and 1b divide on.
>
>   **No artifact classification rule is introduced by this disclosure.**
>   It records what the constant is and what it decides. It does not
>   define a category of "artifact identifier", does not authorize adding
>   to or removing from `LEGACY_ARCHIVE_PROJECT_IDS`, does not rule on
>   whether such identifiers belong in engine modules at all, and does not
>   create an exemption that a future workload name could be admitted
>   under. Should that question need deciding, it is a separate AD.
> - **1b. The dataset and reproduction path is workload-bound.**
>   `dataset_manifest`, `identity_verification`, `reconstruction_loader`,
>   `reproduction_runner`, and `calendar_definitions` encode ETF's table names,
>   column names, foreign-key topology, and calendar. A second workload cannot
>   produce a governed archive without changing them.
>
> Any statement about this platform's neutrality — in documentation, a release
> note, or an external presentation — must name which of 1a and 1b it refers to.
> An unqualified claim of "workload-neutral platform" is false while 1b holds.
>
> **2. Three classes, and this is a second axis — not a re-drawing of the
> domain map.** The axis has exactly three classes — **Engine**,
> **Reference Workload**, and **Artifact** — and they are mutually
> exclusive: a module classified under this axis carries exactly one of
> them, decided at introduction and stated in its own docstring.
> `core/analytics` is Reference Workload. `research_artifacts/`,
> `research_archive/`, and `experiments/*.py` are Artifact.
>
> **A namespace this decision does not name is not classified by it.**
> The three classes are the only values the axis admits; they are not a
> claim that every namespace in the tree has already been assigned one.
> Where this decision is silent, the classification is simply not made
> here — the deferral of `core/market_data` below is the worked case —
> and this entry classifies no such namespace, by implication or
> otherwise.
>
> **AD-068's domain mapping is unchanged by this decision.** AD-068
> decision 1 maps `core.analytics` to `etf` — that is the mapping AD-068
> decision 1 itself makes, and it is the whole of what it makes. The
> `core.market_data → data` mapping is not AD-068 decision 1's: it is
> the boundary checker's `DOMAIN_OF_TOPLEVEL`
> (`tools/check_import_boundaries.py:119`), which predates AD-068 and
> which AD-068 did not change. AD-068 decision 3 separately attributes
> ETF symbols hosted inside `core.market_data` by the name they bind.
> Those mappings, and the `ETF_SYMBOLS_BY_MODULE` mechanism that
> implements decision 3, are **untouched here**. AD-077 adds a **second,
> orthogonal classification axis**
> (Engine / Reference Workload / Artifact) over the same tree; a module
> has a domain under AD-068 *and* a class under AD-077, and neither
> derives from the other.
>
> **`core/market_data` is not classified by this decision, and the split
> is deferred.** Earlier phrasing spoke of "the ETF half of
> `core/market_data`" as though that half were a module with a class.
> It is not: it is two `data -> etf` violations
> (`ingestion/price_ingestion.py:7`, `persistence/repository.py:15`)
> inside a package that is otherwise Data, held under a strict `xfail`.
> **A package cannot carry two classes, and this decision does not
> pretend to assign it one.** Whether `core/market_data` splits, and
> where the boundary falls, remains **deferred** —
> `docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md` §9.1 defers it until a
> second workload exists, and nothing here disturbs that deferral or
> pre-decides its outcome. What this decision *does* correct is the
> withdrawn AD-076 draft's placement of `core/market_data` in **Engine**,
> which the repository's own checker refutes; the correction is that the
> package is **not Engine**, not that it is something else.
>
> **3. Enforcement is stated per rule, at the strength it actually has.**
>
> The enforcement facts, stated before the table so they cannot be read
> off it too generously:
>
> - `tools/check_import_boundaries.py` **exists** and implements the
>   `core/` domain-edge check by symbol attribution (AD-068 decision 3).
> - `tests/test_import_boundaries.py` enforces the **pinned coupling
>   inventory** (`test_known_etf_coupling_inventory_is_exactly_as_documented`),
>   **per-symbol resolution** (`test_every_etf_symbol_resolves_in_its_named_module`),
>   the **kernel non-exemption** (`test_no_kernel_module_hosts_an_etf_symbol`),
>   and the **empty governance edge**
>   (`test_governance_does_not_reach_the_etf_domain`). These are real,
>   blocking assertions and they run in the suite.
> - **CI invocation is advisory, not blocking.**
>   `.github/workflows/governance.yml:92` runs
>   `python tools/check_import_boundaries.py || true`. A boundary
>   violation introduced today does **not** fail CI through that step.
>   The blocking pressure comes from the test suite, not from the CI
>   invocation.
> - The strict `xfail` on
>   `test_real_repository_has_no_boundary_violations`
>   (`tests/test_import_boundaries.py:200`, `strict=True`) **remains in
>   place** for the two known deferred `data -> etf` violations. It is
>   the forcing function AD-068 decision 4 installed: it fails the suite
>   if the violations are fixed without removing the marker, and it does
>   not mask new violations of other edges, which the inventory test
>   catches instead.
>
> **This decision changes no CI configuration and authorizes no CI
> change.** The `|| true` is recorded here as a fact about current
> enforcement strength, not as a defect this decision repairs.
>
> | Rule | Enforcement, accurately |
> |---|---|
> | `core/` dependency table | `tools/check_import_boundaries.py` (exists) + suite assertions (blocking); CI step advisory (`\|\| true`) |
> | Engine may not import a workload | same checker + `test_governance_does_not_reach_the_etf_domain` (blocking) |
> | Known `data -> etf` violations stay visible | strict `xfail`, `strict=True`, unchanged |
> | A file may name at most one workload | **not enforced today**; proposed for Phase 1.5, unauthorized by this decision |
> | Artifacts may not live under `core/` | **not enforced today** — the checker scans `core/` only, so `core → research_artifacts` is invisible to it; proposed for Phase 1.5, unauthorized by this decision |
> | Every module declares its class in its docstring | **review only — unenforced, and this is stated, not implied** |
>
> **4. A workload fact reaches the engine as a value, never as a default —
> applying to new and changed engine signatures.** Required tables,
> identity-table specs, row parsers, loaders, seed steps, and coverage
> providers are supplied by the composition root as parameters with no
> default. Precedent: C4's `parse_row`/`load_rows`, adopted here as a
> general rule. A default would let a caller who forgot one silently
> receive ETF's semantics.
>
> **Scope, stated so this decision does not make the current tree
> non-conformant on acceptance.** The rule binds **any engine signature
> introduced or modified after this decision is accepted**. It is **not
> retroactive**, and accepting it does **not** put the tree in violation
> of an accepted decision.
>
> **Known existing non-conformance, recorded rather than discovered
> later:**
>
> | Location | Non-conformance |
> |---|---|
> | `core/governance/reconstruction_loader.py:272` | `reconstruct_database(..., calendar_id: str = "XNYS", ...)` — a workload fact as a parameter **default** in an engine signature |
>
> This is a real instance of exactly what clause 4 forbids going forward,
> and it is named so that clause 4 cannot be read as a claim that no such
> case exists. **No remediation is authorized by this decision.** It
> schedules no fix, sets no deadline, and does not license editing that
> signature; the change is proposed in Phase 1 item 1.3, which is not
> authorized here (see *What this decision does not do*). Should that
> signature be modified for any reason before Phase 1 is authorized, the
> rule binds it at that point, because modifying it makes it a changed
> signature.
>
> **5. A rename in `core/` is a reproduction-compatibility change.** Because
> a pinned commit's scripts resolve `core.*` through HEAD, any public name
> removed or renamed in `core/` that is imported by the `experiments/`
> script at **the pinned commit named by a cycle's
> `reproduction_record.json`** must either (a) keep a permanent shim,
> explicitly classified as a reproduction shim and covered by a test
> asserting a real pinned importer exists, or (b) have every affected
> cycle's reproduction status re-derived and re-recorded. Silent removal
> is prohibited.
>
> **The anchor is the reproduction record's commit, not the Archive
> Seal.** For `reference_h4` the anchor is
> `research_archive/reference_h4/reproduction_record.json`'s
> `commit_hash` (`3d586ded…`), which is the commit
> `run_reproduction()` checks out into a pinned worktree and whose
> scripts therefore do the importing.
>
> **Archive sealing and reproduction compatibility are separate
> mechanisms and are not merged by this clause.** The Archive Seal
> (AD-074, AD-075) witnesses a *different* commit for a *different*
> purpose — it binds archived bytes to a witnessed commit and is verified
> by tree comparison — and the Seal's commit is not the reproduction
> anchor. Wording that speaks of "the sealed commit" in a reproduction
> context conflates the two, and is not used here. A cycle can have a
> reproduction anchor and no seal, or a seal and no reproduction anchor;
> this clause is triggered by the former alone.
>
> **Retroactive application, already measured.** C1's `ETFId` rename and
> C4's deletion of `core.governance.dataset_snapshots` were examined
> under this rule before the cleanup was committed, and the measurement
> is `docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md` §11.3: 45 distinct
> `(module, symbol)` pairs across 20 core modules resolved, 0 unresolved,
> and neither removed name is imported by any pinned experiment script.
> Branch (a) and branch (b) are therefore both unnecessary for those two
> removals. That measurement discharges this clause for C1 and C4; it
> does not, by itself, establish the rule, which is what this clause
> does.
>
> **6. Neutrality claims expire at one implementation.** No seam with exactly
> one implementation may be described as workload-neutral. It may be described
> as *parameterized*, which is a different and smaller claim.
>
> **7. Interaction with AD-068, stated explicitly so clause 5 cannot be
> read as an escape hatch.**
>
> - **AD-068 decision 3 remains unchanged.** This decision does not
>   amend, weaken, reinterpret, or grant an exception to it.
>   `ETF_SYMBOLS_BY_MODULE`, symbol attribution, and decision 5's guard
>   test continue exactly as accepted.
> - **A permanent ETF alias or reproduction shim created under clause 5
>   does not bypass AD-068 decision 3's termination logic.** If such a
>   shim binds an ETF-specific name in an asset-class-neutral module, it
>   is an ETF symbol in that module and belongs in
>   `ETF_SYMBOLS_BY_MODULE` like any other — clause 5 supplies a *reason*
>   for a symbol to persist, never a reason for it to be invisible to the
>   checker. Decision 3's termination condition is that symbol
>   attribution ends when the mapping **empties**; a permanent shim that
>   is exempted from the mapping would make it appear to empty while the
>   coupling persists, which is precisely the false-success shape AD-068
>   decision 5 exists to catch.
> - **Conflict is possible and is not resolved here.** A permanent shim
>   that must never be removed and a mapping that must eventually empty
>   are in tension. **Any actual conflict requires a separate AD**,
>   argued on its own terms, with its own number allocated at that time.
>   This decision neither pre-authorizes that resolution nor reserves a
>   number for it, and **AD-068 is not amended by this entry.** Until
>   such an AD exists, clause 5's branch (a) may not be exercised in a
>   way that would remove an entry from `ETF_SYMBOLS_BY_MODULE`.
>
> **What this decision does not do.** It creates no registry, no plugin
> system, no dependency-injection container, and no dynamic discovery.
>
> **It authorizes no implementation work of any kind, and no module
> moves.** Concretely: it authorizes no Phase 1 item (1.1 through 1.6),
> no Phase 2 work, and no Phase 3 work. It moves no module, relocates no
> constant, changes no signature, adds no test, and modifies no CI
> configuration. The phase plan in §5 of
> `docs/ENGINE_NEUTRALITY_ARCHITECTURE_REVIEW_2026-07-27.md`, the review
> that carries this entry, is a **proposal**, not a grant of authority;
> where this entry names a Phase 1 item it does so to identify a
> proposal, never to approve it. Earlier phrasing of this paragraph excepted "those Phase 1
> names" from the no-moves rule — that exception is **removed**, because
> it made an authorization out of a cross-reference. Each phase requires
> its own authorization, recorded separately.
>
> **Known weakness, stated rather than discovered later.** Four things in
> this decision are held by reading alone: **clause 1a's semantics claim**
> (no test asserts it), **clause 2's docstring rule**, and **clause 3's
> last three rows** (one-workload-per-file, artifacts-outside-`core/`,
> and the docstring declaration). A fifth is weaker than it looks:
> clause 3's first row is enforced by the suite but **not** by the CI
> step, which is advisory. And this repository has no independent
> reviewer (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4 — Level 3
> unavailable; see *Review basis*). The honest claim is that this
> decision makes drift *nameable in review*, not that it prevents drift.

---

## 7. Final decision

### **(B) Yes, but only after one limited neutrality phase.**

**Evidence for "yes."**

- 80.4 % of the governance layer (3,679 of 4,575 lines, 11 of 16 modules) is
  already workload-neutral by inspection, not by intent.
- The capabilities are real and unusual: append-only decision records, archive
  sealing against a witnessed commit, freeze verification, an offline guard
  that makes a network call an automatic reproduction failure, pinned-worktree
  execution, and a frozen-identity invariant that catches silent regeneration.
  These map directly onto EU AI Act Art. 11 (technical documentation), Art. 12
  (record-keeping), and Art. 10 (data governance) without being retrofitted to
  them.
- There is one governed cycle that actually ran: `reference_h4`, sealed, with a
  real `transition_records.jsonl` and a recorded `VERIFIED` reproduction. A
  working example beats a specification.
- The engine already accepts behaviour as parameters (C4's `parse_row`/
  `load_rows`) and already has a composition root outside the domain graph
  (`tools/reproduce_cycle.py`). The seam pattern is established, not
  hypothetical.
- The discipline itself is a differentiator: an import-direction lint, an
  architecture decision log whose highest **accepted** entry was **AD-075**
  when this review was written, xfail-as-forcing-function, and a
  byte-identity test guarding a sealed
  archive. **The ceiling was AD-075, not AD-076.** AD-076 was never accepted
  and never appended, so it is no part of the log's contents and is not
  evidence of anything here; citing "a decision log at AD-076" would count a
  withdrawn draft as delivered work. AD-077 was this review's proposed next
  entry and has since been accepted and appended (2026-07-27), which moves
  the ceiling to AD-077 and leaves AD-076 exactly as described.

**Evidence for "not yet" (why not A).**

- The demo that carries the pitch is "one engine, two unrelated governed
  workloads." That demo is currently impossible at the first step:
  `dataset_manifest.py:116` **rejects** any non-ETF manifest. Not degrades —
  rejects.
- An engine module hardcodes a filesystem path to one workload's script
  (`reproduction_runner.py:109`) and another hardcodes the New York Stock
  Exchange (`calendar_definitions.py:31`). Both are visible in a five-minute
  technical read by anyone who asks "show me the neutral part."
- The completeness claim that was *drafted* as AD-076 clause 4 is verifiably
  false (§6.1). **This is evidence about the drafting, not about the decision
  log:** AD-076 was never accepted and never appended, so no accepted decision
  on this platform carries that claim, and the log is not defective. It is
  recorded as "not yet" evidence because the claim was written down and
  believed before review caught it — in front of a technical evaluator, a
  governance platform whose drafts assert unsupported completeness is a worse
  finding than the coupling those drafts misdescribe. What AD-077 fixes is the
  claim; what the withdrawal already fixed is its status.
- ~~Per F-1, whether the sealed archive still reproduces after this week's
  cleanup is currently **unknown**.~~ **Superseded by measurement:** cleanup
  §11.2/§11.3 record `verified` and full pinned-import resolution. This is no
  longer evidence for "not yet"; it is now a measured fact, and the remaining
  evidence for "not yet" is the three bullets above, which stand on their own.

**Why not C.** Nothing needs redesigning. There are no cyclic dependencies, no
god objects, no leaked framework, no persistence coupling in the lifecycle
layer. `run_migrations` already takes a directory; the seal and verifier are
already generic; the `Experiment` and `Gate` protocols are structural typing
done correctly. The gap is five modules and four constants, addressable by
parameter passing. Calling this a major redesign would be as inaccurate as
calling it already-neutral.

### Recommended next milestone

> **Milestone: "Reference Workload Extraction" (Phase 0 + Phase 1, items 1.1–1.5).**
>
> **Definition of done**
> 1. `python -m tools.reproduce_cycle research_archive/reference_h4 …` returns
>    `VERIFIED` — recorded before the milestone starts and again at its end.
> 2. `python -m tools.check_import_boundaries` exits 0, or exits 1 solely on
>    1.6 pending its AD.
> 3. The workload constants named in §4 items A, B, and `calendar_definitions`
>    no longer live under `core/governance/`. **Judged by review, not by test:**
>    no lexical assertion exists, none is proposed here, and this criterion may
>    not be restated as "zero ETF literals, asserted by test".
> 4. AD-077 accepted; the AD-076 draft withdrawn undelivered.
> 5. Full suite green; `tests/test_sealed_snapshot_byte_identity.py` and
>    `tests/test_sealed_archive_integrity.py` unchanged and passing.
>
> **Explicitly out of scope:** workload #2, any `workloads/` directory, any
> `WorkloadProfile`, any registry, any statistics rename, any change to sealed
> bytes.
>
> After that milestone the honest claim becomes: *"the governance engine takes
> its workload's schema as a parameter; the ETF research programme is its first
> workload; the second is next."* That claim is true, it is checkable by a
> visitor in ten minutes, and it is a materially stronger position than the
> one the withdrawn AD-076 draft attempted to assert. AD-076 asserts nothing
> now: it was never accepted, and the comparison is against a draft that was
> withdrawn, not against a live decision.
