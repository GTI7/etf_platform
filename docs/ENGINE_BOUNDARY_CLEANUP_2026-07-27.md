# Engine Boundary Cleanup — implementation record (2026-07-27)

**Status: implemented in the working tree, uncommitted. The three AD
amendments in §7 are *prepared*, not accepted. The AD-076 draft that
previously occupied §8 is **withdrawn undelivered** — see §8.**

**Record correction, 2026-07-27.** This document was revised before commit
to withdraw the AD-076 draft and to remove two claims it made that the tree
does not support. Measured verification results — full suite, sealed-cycle
reproduction, and pinned-import compatibility — are in §11, which also
records finding **N-1**. No code, test, or tooling changed in that revision;
it is documentary only.

**Baseline.** Branch `master`, HEAD `fd7a26c`, working tree clean and in
sync with `origin/master` at start. Test baseline before any change:
**979 passed, 3 skipped, 1 xfailed** (253 s). `ruff check` reported three
pre-existing findings, all untouched by this work.

**Scope.** Executes the accepted cleanup items C1, C2, C4, C5, C6 from
the Engine Boundary Review. No item was widened, narrowed, or
substituted. No plugin system, dependency-injection framework, registry,
or dynamic discovery was introduced. A draft of AD-076 was also prepared
and has since been **withdrawn** (§8); nothing in this cleanup was
authorized by it, and its withdrawal changes no item above.

**What this cleanup is not.** It discharges two import edges and moves
three misplaced things. It does **not** make the engine workload-neutral,
and no statement here should be read as claiming that it does: five
`core/governance/` modules still encode ETF table names, column names,
foreign-key topology, and a trading calendar. §8 enumerates them.

**Review level.** This document is **Level 1** — one implementer with
repository access. It discharges no independent-review requirement and
must never be cited as an independent review of anything it records,
the same standing AD-068 and AD-069 declare for their own basis.

---

## 1. Readiness assessment (performed before any change)

Confirmed against `docs/ARCHITECTURE_DECISIONS.md`,
`docs/PLATFORM_ARCHITECTURE_V1.md`, `tests/test_import_boundaries.py`,
and `tools/check_import_boundaries.py`.

| Item | Ready to implement? | Why |
|---|---|---|
| **C2** — single source of archive constants | **Yes, no AD needed.** | No accepted decision requires or blesses the duplication. Each duplicate carried a *comment* justifying itself, not a recorded decision. Import direction is preserved, so no Section 5 edge changes. |
| **C6** — remove dead intent | **No — needs an AD.** Implemented under the prepared amendment in §7.2. | AD-003 introduced `UniverseId`/`PortfolioId`/`HoldingId` and **AD-031 explicitly reserves `ArtifactRef`** with a recorded rationale. Deleting them reverses part of two accepted decisions. `config/`/`portfolio/` are named only in a migration-plan inventory, not in any AD. |
| **C1** — `ETFId` → `InstrumentId` | **No — needs an AD amendment.** Implemented under §7.1. | **AD-068 decision 3 names `ETFId` explicitly** as an `ETF_SYMBOLS_BY_MODULE` entry, and the rename removes an entry from the pinned inventory. AD-068 decision 5 makes an unexplained shrink of that mapping the exact false-success mode to guard against. |
| **C5** — artefact separation | **Yes, no AD needed.** | Relocation of two modules with no accepted decision fixing their location. AD-050 A6-C4 fixes `reference_h4`'s *identifier*, not the module path; the identifier is unchanged. |
| **C4** — governance/workload separation | **Yes as to mechanism; the inventory reduction is recorded in §7.1.** | AD-068 decision 4 explicitly *deferred* discharging this coupling to a later step and named the discharge as expected work, so discharging it needs a record but not a reversal. The safety check in §2 was built and passing first, as required. |
| **AD-076** | **Withdrawn undelivered.** | Drafted, then deliberately not accepted. Never inserted into `docs/ARCHITECTURE_DECISIONS.md`, never cited by a test, never used to authorize any item in this table. §8. |

**Not implemented, and why:** nothing in the accepted scope was skipped.
Items outside the accepted scope are listed in §9 and were left alone.

---

## 2. Safety check first: sealed-snapshot byte identity

**Built and passing before C4 was attempted**, as the cleanup scope
required.

`tests/test_sealed_snapshot_byte_identity.py` asserts that the current
snapshot serialization path — row dict → domain object → row dict →
canonical JSONL — reproduces
`research_archive/reference_h4/dataset_hashes/{ETF,TradingSession,PriceBar}.jsonl`
**byte for byte**, and that the files compared against are the ones the
sealed `dataset_manifest.json` describes (hash and row count), so the
comparison cannot be made vacuous by swapping a file.

- **Why byte-level and not object-equality.** The sealed archive's bytes
  are authoritative under AD-075. A serialization change that survives an
  object round-trip but shifts a key order, a `Decimal` string form, a
  timezone offset spelling, or a null representation would invalidate the
  Seal's own subject while every existing test stayed green.
- **Result.** Passed against unmodified sealed bytes **before** C4
  (7 tests, 10.3 s), and passed again **after** C4 moved every one of the
  six conversion functions to a different package. That before/after pair
  is the evidence that C4 preserved behaviour.
- **Sealed archives were not modified.** Nothing under
  `research_archive/` was written, and
  `tests/test_sealed_archive_integrity.py` continues to pass.

---

## 3. C2 — single source of archive constants

**Why.** `LEGACY_ARCHIVE_PROJECT_IDS` had **three** definitions
(`tools/archive_manifest.py`, `core.governance.archive_verifier`,
`core.governance.archive_seal`), each with a comment correctly naming an
import edge it was avoiding and incorrectly concluding that a third copy
was the answer. The failure mode is not tedium: that set decides both
whether an archive is exempt from the v1 layout check *and* whether it
can ever be sealed (AC-74-9). Two copies that disagreed would produce an
archive exempt from one control and subject to the other, silently, with
no test able to see it. The manifest filename had the same problem in two
forms (`ARCHIVE_MANIFEST_FILENAME` hosted incidentally by
`decision_recorder`; `MANIFEST_FILENAME` duplicated in `tools/`), and
`dataset_manifest.json` was spelled as a literal in two modules.

**Files.**
- Added `core/governance/archive_identity.py` — imports nothing, holds
  `ARCHIVE_MANIFEST_FILENAME` and `LEGACY_ARCHIVE_PROJECT_IDS`.
- `core/governance/decision_recorder.py`, `archive_seal.py`,
  `archive_verifier.py`, `tools/archive_manifest.py` — import instead of
  define; three duplicate definitions and one duplicate filename deleted.
- `core/governance/dataset_manifest.py` gains `DATASET_MANIFEST_FILENAME`
  beside the schema it names; `dataset_integrity.py` and `archive_seal.py`
  import it (`archive_seal._DATASET_MANIFEST_FILENAME` deleted).
- `tools/archive_manifest.py` docstring: corrected a claim that
  `core/governance/` "remains intentionally empty in Phase 0", untrue
  since Phase 1C.

**Risk.** Import direction: `archive_identity` imports nothing, so no
edge is created and no cycle is possible; `tools → core` is the direction
that was always allowed. Existing importers that reach the constants
*through* a re-exporting module (e.g. `tests` importing
`ARCHIVE_MANIFEST_FILENAME` from `archive_verifier`) still bind, since
the name is still in that module's namespace — verified by test, not
assumed. **No behaviour change and no inventory change.**

**Tests.** `test_archive_manifest_tooling`, `test_governance_archive_verifier`,
`test_governance_decision_recorder`, `test_governance_dataset_integrity`,
`test_sealed_archive_integrity`, `test_governance_dataset_manifest` —
195 passed, 2 skipped. Boundary inventory re-checked: unchanged at 5/2.

---

## 4. C6 — remove dead intent

**Why.** Each removed thing asserted the existence of something this
repository does not have. An empty `portfolio/` package and a
`PortfolioId` alias are indistinguishable, to a reader, from a Portfolio
domain that exists somewhere; `docs/BASELINE_STATUS.md` had to carry
standing prose explaining that they are unused. A `NewType` alias costs
one line to re-introduce when its first caller appears, which is less
than the cost of the standing explanation.

**Removed** (each verified unreferenced repository-wide by `git grep`
before deletion, across `core/`, `adapters/`, `experiments/`,
`maintenance/`, `tools/`, `tests/`, `migrations/`, and packaging config):
`config/__init__.py`, `portfolio/__init__.py`, and the aliases
`UniverseId`, `PortfolioId`, `HoldingId`, `ArtifactRef`.

**Kept:** `ProjectId` (used throughout `core.research`), `ScoreId` (used
by `core.analytics.domain.models`), `ETFId` → renamed by C1.

**Stale comments updated.** `core/shared/ids.py` module docstring;
`core/governance/freeze_verifier.py`'s "`core/research/` is still an
empty stub" and its `ArtifactRef` reference; `docs/BASELINE_STATUS.md`
Deliberately-not-built entries and two Activation-trigger rows (the
triggers themselves are unchanged — only the claim that the names are
already reserved); `docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md` §6.

**Not edited: `docs/PLATFORM_ARCHITECTURE_V1.md`.** Its §4.1/§4.4
signature sketches use `ArtifactRef`. That document's own §9 requires "a
new, dated version, not a silent edit", and a signature sketch for an
interface that does not exist is not falsified by the absence of a type
alias for it — the name is introduced with the interface. Recorded here
rather than actioned.

**Risk.** A future reader of AD-003/AD-031 finds names those decisions
say exist. §7.2 is the note that answers them. No runtime behaviour
touched — all four aliases were `NewType` over `str` with zero callers.

**Tests.** `test_research_project_id`, `test_domain_packages_import`,
`test_import_boundaries`, `test_repository_integrity_snapshot` — 103
passed, 1 skipped, 1 xfailed.

---

## 5. C1 — kernel identity cleanup (`ETFId` → `InstrumentId`)

**Why.** The shared kernel is exempt from the dependency table *as an
import target for every domain* — including Statistics, which
`docs/PLATFORM_ARCHITECTURE_V1.md` §4.3 requires to have "no knowledge
that 'ETF' or 'H3' exist". An asset class's vocabulary in the kernel is
therefore uniquely damaging: it is reachable from everywhere by
construction. `ETFId` was that name.

`ETFId` was **not moved** — C1 explicitly excludes relocating it, and the
kernel is the right home for a neutral identity primitive. It was
**renamed**. `InstrumentId` is not a coined word: §4.6 of the
architecture document already writes the Data-domain provider contract as
`fetch(self, instrument_id: str, ...)`.

**No alias and no compatibility shim were created**, as required. Every
reference was repointed in the same change.

**Files.** `core/shared/ids.py`; `core/market_data/domain/models.py`;
`core/analytics/{domain/models.py, domain/ranking.py, ranked_report.py,
write_pipeline.py}`; `tools/check_import_boundaries.py`
(`ETF_SYMBOLS_BY_MODULE` loses its `core.shared.ids` entry, with the
reason recorded in the module docstring);
`tests/test_import_boundaries.py`.

**Field names are unchanged.** Fields typed by the alias are still
spelled `etf_id`, and no database column moved. The aggregates holding
them (`ETF`, `PriceBar`, `Score`) are genuinely ETF-workload objects;
extracting them is deferred (§9). Renaming the fields would also have
changed the sealed snapshot bytes, which §2 exists to forbid.

**Risk, and how it was contained.** The dangerous move here is not the
rename — it is that the rename *shrinks the pinned inventory*, and
AD-068 decision 5 identifies exactly that shrink as the shape a false
success takes. Three things keep it honest:
1. The removal is itemized in `EXPECTED_ETF_COUPLING`'s ledger comment
   with the intent that authorized it, so a reader sees *how* the count
   fell, not merely that it fell.
2. `test_etf_symbol_hosted_by_the_shared_kernel_is_not_exempt` was
   **kept**, not deleted with the symbol: it now injects a kernel-hosted
   ETF symbol via `monkeypatch` and proves the checker still refuses to
   launder it through the kernel exemption. The mechanism is unchanged
   and is still under test.
3. **New** `test_no_kernel_module_hosts_an_etf_symbol` asserts against
   the real mapping that no kernel module may reappear in it.

**Inventory effect.** 5 → 4 violations, `data -> etf` 3 → 2.

**Tests.** `test_import_boundaries` (33 passed, 1 xfailed) plus every
analytics / market-data / CLI test (289 passed, 1 xfailed).

---

## 6. C4 and C5 — artefact separation and governance/workload separation

### 6.1 C5 — artefact separation

**Why.** `core/research/historical_backfill.py` and
`core/research/reference_h4_registration.py` are *records of specific
research cycles that happened* — identifiers, origin dates, outcomes, and
pointers to committed evidence. They would be wrong to carry into a fresh
deployment of this platform, which is the test that distinguishes an
artefact from a capability. Living under `core/research/` made the
Research engine name `reference_h4` and the three REFERENCE cycles in its
own source tree.

**Files.** Both modules moved (via `git mv`, history preserved) to a new
top-level `research_artifacts/` package with a docstring stating the
classification and the one-way dependency. `core/research/__init__.py`
and `core/research/project.py` no longer name any cycle. Importers
repointed: `tests/test_research_project_registry.py`,
`tests/test_reference_h4_registration.py`,
`tests/test_domain_packages_import.py`.

**Not moved**, as required: `Project`, `ProjectRegistry`,
`create_project_id`, `ResearchProjectRepository`, and all lifecycle
machinery.

**Risk — stated plainly.** `tools/check_import_boundaries.py` scans
`core/` only, so a future `core → research_artifacts` import would be
**invisible to it**. This edge is held by reviewers, not by tooling. It
is recorded in `research_artifacts/__init__.py`. The withdrawn AD-076
draft cited this gap as its own motivation (§8); with that draft withdrawn
the gap is simply **open and unenforced**, held by review alone, and no
accepted decision closes it. `experiments/` was rejected as a destination:
`tests/test_repository_integrity_snapshot.py` treats every
`experiments/*.py` as a protected historical artifact, so adding files
there would have failed the Phase-0 snapshot test.

**Tests.** 88 passed, 1 skipped, 1 xfailed across the five affected test
modules, including a new
`test_cycle_registrations_live_outside_core_and_still_import` that
asserts **both** halves — importable from the new location *and* gone
from `core.research` — because either half alone passes for the wrong
reason.

### 6.2 C4 — governance/workload separation

**Why.** `core/governance/dataset_snapshots.py` imported `ETF` and
`insert_etf`: the two `governance -> etf` violations AD-068 decision 4
named as "the coupling the step was written to expose" and deliberately
left for a later step. A Governance audit that constructs the asset class
it audits cannot be run against a second one, which contradicts §4.4's
definition of the domain as auditing by re-deriving from Data and plain
artifacts.

**The split.**

| Kept by Governance | Moved to workload |
|---|---|
| canonical serialization (`canonical_jsonl`) | row → domain object, domain object → row |
| content hashing, row counts, manifest integrity | database insertion |
| duplicate keys, orphan references, calendar coverage | table load order (a foreign-key fact of the caller's schema) |
| byte comparison (`archive_seal`, `dataset_integrity`) | — |

**Files.**
- **Deleted** `core/governance/dataset_snapshots.py`. After the split it
  would have held only wrappers around `canonical_jsonl`, so keeping it
  would have preserved the engine-names-workload defect in a module with
  nothing else to do.
- **Added** `core/market_data/persistence/snapshot_rows.py` (Data domain:
  `TradingSession`, `PriceBar`) and
  `core/analytics/persistence/etf_snapshot.py` (ETF domain: `ETF`). The
  file split follows the domain split — that is the point; one module
  holding all three would have been forced into whichever domain was more
  contaminating.
- **Added** `core/analytics/persistence/frozen_dataset.py` — the two
  callables Governance is handed. It may import both halves because
  `etf -> data` is an allowed edge; Governance may import neither, which
  is why they are passed *in*.
- `core/governance/reconstruction_loader.py`: `preflight_validate` and
  `reconstruct_database` take `parse_row` and `load_rows` as **required
  keyword parameters with no default** — a default would silently degrade
  validation for a caller who forgot one. `preflight_validate` now
  returns verified rows rather than paths, so nothing downstream re-reads
  bytes it already vouched for.
- `core/governance/reproduction_runner.py`: threads both callables
  through, alongside the `run_experiment` callable it already took.
- **Moved out of `core/`:** the `python -m core.governance.reproduction_runner`
  CLI is now `python -m tools.reproduce_cycle`. A CLI must *choose* which
  workload's implementations to pass, and a composition root that names
  both Governance and the ETF workload cannot sit inside Governance
  without reinstating the very edge this item removes. Behaviour is
  unchanged; the library half (`run_reproduction`) did not move.
  **This is a user-visible invocation change** and is the one
  externally-observable consequence of this cleanup.
- Tests: `tests/test_governance_dataset_snapshots.py` split into
  `tests/test_etf_snapshot_rows.py` and
  `tests/test_market_data_snapshot_rows.py` (following their subjects),
  plus new `tests/test_frozen_dataset_workload.py`. Call sites in
  `test_governance_reconstruction_loader`, `test_reproduction_contract`,
  and `test_governance_reproduction_runner` updated.

**Constraints honoured.** No plugin system, no generic registry, no
dynamic discovery. `frozen_dataset._ROW_PARSERS` is a three-entry dict
over names fixed by `dataset_manifest.REQUIRED_SOURCE_TABLES` and the
schema; nothing registers into it, nothing discovers it, and an unknown
`source_table` **raises rather than being skipped** — a table nobody can
parse must not pass validation by being invisible to it. Archive
verification semantics are untouched: no change to `archive_seal`,
`archive_verifier`, or `dataset_integrity` beyond C2's constant imports.

**Risk.** The real risk is silent serialization drift, and §2 is the
control for it: the byte-identity check passed before the move and passes
after it, against the same sealed bytes. Secondary risk is a caller that
forgets a callable — impossible, the parameters are required.

**Inventory effect.** 4 → 2 violations; the `governance -> etf` **import
edge** is **empty**. `test_governance_to_etf_coupling_is_reported_as_such`
(which asserted the coupling *exists*) is replaced by
`test_governance_does_not_reach_the_etf_domain`, which asserts emptiness
by domain rather than by file, so a *new* Governance module reaching into
ETF fails there rather than appearing as an unrecognized inventory line.

**What the empty edge does not mean.** It is a statement about *imports*
only. Governance no longer constructs ETF objects; it still **encodes ETF
schema semantics** — table names, column names, foreign-key topology, and a
trading calendar — in `dataset_manifest`, `identity_verification`,
`reconstruction_loader`, `reproduction_runner`, and `calendar_definitions`
(§8.2). Those are literals and dict keys, not imports, so no checker sees
them and the empty edge is silent about them. C4 removed object
construction from Governance; it did not remove schema knowledge, and this
record must not be cited as if it had.

---

## 7. Prepared AD amendment notes (not accepted, not inserted)

These are the recorded architectural intent the pinned inventory requires
for each reduction. They are written here, and cited from
`tests/test_import_boundaries.py`, so that no reduction is silent. They
are **not** appended to `docs/ARCHITECTURE_DECISIONS.md`; doing so is an
acceptance act.

### 7.1 Amendment note to AD-068 (decisions 3, 4 and 5)

1. **Decision 3's symbol list loses `core.shared.ids: {ETFId}`.** The
   entry is removed because **the name no longer exists** — it was
   renamed to `InstrumentId` (C1) — not because the symbol was
   reclassified, exempted, or relocated. This is the only permitted way
   for an `ETF_SYMBOLS_BY_MODULE` entry to disappear, and decision 5's
   guard test (`test_every_etf_symbol_resolves_in_its_named_module`) is
   unchanged and still passing over the remaining entries.
2. **Decision 3's termination condition is unaffected.** Symbol
   attribution remains in force for the two entries that remain
   (`core.market_data.domain.models: ETF`,
   `core.market_data.persistence.repository: get_etf, get_etf_by_ticker,
   insert_etf`) and still ends when the mapping empties.
3. **Decision 4's deferred discharge is partially executed.** The
   `governance -> etf` edge — the coupling decision 4 named explicitly —
   is discharged by C4. Decision 4's `xfail(strict=True)` marker
   **stays**, because `data -> etf` is not discharged and the test still
   fails. No marker was weakened, moved, or removed; `strict=True` is
   intact.
4. **New standing assertions**, so neither discharge can regress
   unnoticed: `test_no_kernel_module_hosts_an_etf_symbol` and
   `test_governance_does_not_reach_the_etf_domain`.

### 7.2 Amendment note to AD-003 and AD-031

`UniverseId`, `PortfolioId`, and `HoldingId` (AD-003) and `ArtifactRef`
(AD-031) are **withdrawn, unused**, on 2026-07-27.

AD-031's rationale was that reserving a name now is cheaper than
retrofitting a shared identifier after several domains have each grown
their own, and it priced the reservation at "two unused `NewType` lines".
That pricing omitted the standing cost actually incurred: two
Deliberately-not-built entries and two Activation-trigger rows in
`docs/BASELINE_STATUS.md`, maintained across every release since Phase 0
purely to explain that the names mean nothing, and a kernel a reader
cannot take at face value. The withdrawal does not
reverse AD-031's *reasoning*; it revises its cost estimate against
observed evidence — no caller appeared for any of the four in the whole
Phase 0→Phase F span.

**Nothing is decided about whether a Portfolio or Universe domain should
exist.** The activation triggers in `docs/BASELINE_STATUS.md` are
unchanged; only the claim that the names are already reserved is. Each
name is one line to re-introduce, in the commit that adds its first
caller — which is AD-069's demand-driven growth rule applied to
identifiers.

### 7.3 Note on AD-067's module census

AD-067's census is dated to HEAD `74e1693` and already predates
`archive_seal`, `archive_verifier`, and `dataset_integrity`. For the
record, `core/governance/` now holds **sixteen** modules besides
`__init__.py`: `archive_identity`, `archive_seal`, `archive_verifier`,
`calendar_definitions`, `canonical_jsonl`, `dataset_integrity`,
`dataset_manifest`, `decision_recorder`, `freeze_verifier`,
`identity_verification`, `independence_linter`, `network_guard`,
`pinned_worktree`, `reconstruction_loader`, `reproduction_record`,
`reproduction_runner`. `decision_recorder`'s public export surface is
numerically unchanged — `ARCHIVE_MANIFEST_FILENAME` is now imported
rather than defined, and is still bound in that module's namespace.
Exactly one module, `decision_recorder`, can still write
`transition_records.jsonl`.

---

## 8. AD-076 — WITHDRAWN UNDELIVERED (2026-07-27)

This section previously carried a draft of **AD-076: Every module is
classified Engine, Reference Workload, or Artifact at introduction**. That
draft is **withdrawn**. It was drafted and then **deliberately not
accepted**; the corrected successor draft is **AD-077**.

### 8.1 AD-076 is unconsumed

The draft was never appended to `docs/ARCHITECTURE_DECISIONS.md`, never
cited by a test, never referenced by an accepted decision, and never used
to authorize any item in this cleanup. Every item C1–C6 rests on the §7
amendment notes, not on AD-076. Withdrawing it therefore changes no code,
no test, no tooling, and no accepted decision — **the decision number
AD-076 remains unconsumed** and is not spent by this record.

### 8.2 Why it was not accepted

Three defects, each checkable against the tree at this working-tree state.

1. **Its completeness claim was false.** Clause 4 stated that `"ETF"` in
   `core/shared/ids.py` and `"reference_h4"` in `core/research/` "were the
   two live instances; both are discharged." They are two instances of
   nine, and the other seven are untouched. Engine-classified modules that
   still name a workload concept:

   | Engine module | Workload vocabulary it still hardcodes |
   |---|---|
   | `core/governance/dataset_manifest.py` | `REQUIRED_SOURCE_TABLES = {"ETF","PriceBar","TradingSession"}` |
   | `core/governance/identity_verification.py` | `FROZEN_IDENTITY_TABLES`, `_ORDER_BY` (`etf_id`, `session_date`, `calendar_id`) |
   | `core/governance/reconstruction_loader.py` | `paths["ETF"]`, `row["ticker"]`, `row["etf_id"]`, `row["calendar_id"]`, and **seven** ETF-named error classes |
   | `core/governance/reproduction_runner.py` | `UNIVERSE_MODULE_RELATIVE_PATH = "experiments/daily_etf_universe_update.py"`, `module.ETF_UNIVERSE`, `_DRIFT_ERRORS` |
   | `core/governance/calendar_definitions.py` | `XNYS`, `"New York Stock Exchange"`, `"NYSE"` |
   | `core/statistics/significance.py` | `"etf_ids"` panel key |
   | `core/shared/pipeline_names.py` | `ticker` parameter, `price_ingestion:` / `scoring:` prefixes |

   The seven ETF-named error classes in `reconstruction_loader` are
   `DuplicateTickerError`, `DuplicateEtfIdError`, `MissingExpectedTickerError`,
   `OrphanPriceBarError`, `UnknownEtfCalendarError`,
   `UnknownTradingSessionCalendarError`, and `DuplicateTradingSessionError`
   — counted directly in the module, correcting the count of six recorded
   elsewhere. The remaining six error classes in that module
   (`ReconstructionValidationError`, `MissingSnapshotArtifactError`,
   `DatasetHashMismatchError`, `DatasetRowCountMismatchError`,
   `MalformedSnapshotRowError`, `ScratchDatabaseExistsError`) are neutral.

   **The correct statement is that this cleanup discharged two import
   edges, not that it made the engine neutral.** An accepted decision
   carrying a false completeness claim is worse than no decision, and in a
   governance platform's own decision log it is the worst kind of finding.

2. **Its classification contradicted this repository's own tooling.**
   Clause 1 placed `core/market_data` in **Engine** while
   `tools/check_import_boundaries.py` simultaneously reports two
   `data -> etf` violations inside that package (§10). A classification the
   project's own checker refutes cannot be the authority for future
   classifications.

3. **It had no rule about renames.** A pinned commit's `experiments/`
   script resolves its `core.*` imports through **HEAD's** package, so
   removing or renaming a public name in `core/` is a
   reproduction-compatibility change, not a cosmetic one. That is the
   highest-consequence rule a classification decision here needs, and
   AD-076 did not mention it. §11.3 is the measurement this cleanup owed on
   that point; it is a measurement, not a rule.

### 8.3 Successor

`docs/ENGINE_NEUTRALITY_ARCHITECTURE_REVIEW_2026-07-27.md` §6.2 carries the
corrected successor draft, **AD-077**, which states the neutrality claim as
two separate claims (spine vs. dataset/reproduction path), corrects
`core/market_data`'s classification, and adds the rename rule.

**AD-077 is a draft and is not accepted.** This document neither accepts it
nor depends on it, and nothing in this revision changes its status. The
classification vocabulary AD-076 proposed is not in force; where a module
added by this cleanup states its own class in its docstring
(`research_artifacts/__init__.py`, `frozen_dataset.py`), that is descriptive
prose, not the discharge of an accepted rule.

---

## 9. Deferred, deliberately

Each is out of scope for this cleanup and is recorded so it is not
mistaken for an oversight.

1. **ETF aggregate extraction — until workload #2 exists.** The remaining
   two `data -> etf` violations are `core/market_data` declaring the
   `ETF` aggregate and its repository functions. Extracting it now would
   shape the seam around a single workload, which is the "abstraction
   ahead of a second concrete need" this repository's discipline
   (`docs/BASELINE_STATUS.md`) refuses. The `xfail(strict=True)` marker
   remains the forcing function.
2. **Manifest-derived schema — until the authority model is defined.**
   The frozen-table set is spelled in `dataset_manifest.REQUIRED_SOURCE_TABLES`,
   in `frozen_dataset._ROW_PARSERS`, and in the migrations. Deriving one
   from another requires deciding which is authoritative, and AD-067
   already records that policy authority composition is hand-maintained.
3. **Experiment implementation trigger.** Untouched by this cleanup.
4. **`positive_control_phase3` lifecycle decision.** That cycle remains
   open and unregistered; nothing here changes its status, its exclusion
   clauses in `tests/test_repository_integrity_snapshot.py`, or the
   decision owed on it.

5. **Finding N-1 — unreachable coverage validation.** Recorded in §11.4.
   Deferred to the neutrality phase; **no remediation is performed in this
   commit.**
6. **Engine neutrality itself.** The seven engine modules in §8.2 that
   still hardcode workload vocabulary are untouched by this cleanup and
   remain open. No decision here authorizes work on them.

Also deferred and worth naming: the **R-4b residual** (AD-075 §4 — two
`experiments/` scripts covered by no automated integrity control) is
untouched and still open.

---

## 10. Final state

**Boundary inventory ledger.**

| Edge | Before (`fd7a26c`) | After | Discharged by |
|---|---|---|---|
| `data -> etf` — `core/market_data/domain/models.py:7` → `core.shared.ids.ETFId` | violation | **gone** | C1 (rename) |
| `data -> etf` — `core/market_data/ingestion/price_ingestion.py:7` → `…models.ETF` | violation | violation | deferred (§9.1) |
| `data -> etf` — `core/market_data/persistence/repository.py:15` → `…models.ETF` | violation | violation | deferred (§9.1) |
| `governance -> etf` — `core/governance/dataset_snapshots.py:26` → `…models.ETF` | violation | **gone** | C4 |
| `governance -> etf` — `core/governance/dataset_snapshots.py:27` → `…repository.insert_etf` | violation | **gone** | C4 |
| **Total** | **5 across 2 edges** | **2 across 1 edge** | |

`ETF_SYMBOLS_BY_MODULE` shrank from three entries to two;
`core.shared.ids` is gone from it and no kernel module may return.

**Tests.** Full suite after all items: **996 passed, 3 skipped, 1
xfailed** (428 s), against a baseline of 979/3/1. The xfail is the same
one, still failing for the same remaining reason. `ruff check` reports
the same three pre-existing findings as the baseline and no new ones.
Re-measured independently before commit — §11.1.

---

## 11. Measured verification (2026-07-27)

Everything in this section is a **measurement taken at this working-tree
state**, not an inference from the sections above. Date of measurement:
**2026-07-27**. Baseline: branch `master`, HEAD `fd7a26c`, with the
uncommitted cleanup working tree in place.

### 11.1 Full test suite

```
python -m pytest -q
→ 996 passed, 3 skipped, 1 xfailed
```

Matches the figure recorded in §10 (that run reported 428 s; this one
285.54 s — wall-clock only, same counts). The single `xfail` is
`tests/test_import_boundaries.py::test_real_repository_has_no_boundary_violations`,
still `strict=True`, still failing on the two deferred `data -> etf`
violations of §9.1.

### 11.2 Sealed-cycle reproduction — `reference_h4`

The suite does **not** contain an end-to-end reproduction of the sealed
archive, so a green suite was not evidence that `reference_h4` still
reproduces after C1's rename and C4's module deletion. It was run
explicitly:

```
python -m tools.reproduce_cycle research_archive/reference_h4 --experiment-module experiments/validate_h4_kurtosis.py
→ verified: reproduction completed; frozen identities unchanged
  (exit 0)
```

**Reproduction status: `verified`.** This is the outcome for the cycle's
own pinned commit `3d586ded4aad31201cc4e3a349ff7e5d766ba8f5`, run against
the *current* working tree — which is the state that matters, because a
pinned script's `core.*` imports resolve through HEAD's package and not
through the pinned worktree's.

Nothing under `research_archive/` was written by this run; the scratch
database was created under a fresh temporary directory.

### 11.3 Pinned import compatibility — validation note

Because a rename or deletion in `core/` can silently break a sealed
cycle's reproduction, C1's and C4's removals were checked against every
pinned experiment script rather than only against the one §11.2 executes.

- **12 files inspected** in `experiments/` at pinned commit `3d586ded`
  (**11 scripts** plus `README.md`); the same 12 are present at HEAD.
- Every `core.*` import in those scripts was resolved against the current
  working tree: **45 distinct (module, symbol) pairs across 20 core
  modules**, all resolving. **0 unresolved.**
- **No symbol removed by C1 or C4 is required by any pinned reproduction.**
  `ETFId` (renamed by C1) is imported by no experiment script;
  `core.governance.dataset_snapshots` (deleted by C4) is imported by no
  experiment script; `reconstruct_database`, which gained two required
  parameters, is called only from `core`/`tools`, never from a pinned
  script.

**Scope of this note.** It validates *import resolution*, which is the
mechanism §8.2 defect 3 names. It is a measurement only — it establishes
no rename policy, and this cleanup records none. AD-077's proposed rename
clause remains a draft (§8.3).

### 11.4 Finding N-1 — coverage validation is effectively unreachable for `reference_h4`

`core/governance/reproduction_runner.py` carries a semantic coverage check
whose stated purpose is that "a hash match confirms the file did not
change, not that it still covers the universe the pinned code will iterate
over" — it loads the pinned worktree's own `ETF_UNIVERSE` and asserts the
ETF snapshot covers it. Its docstring states the check "is always
checked — there is no way to opt out of it from this function's
signature."

**That is not what the code does.** The check is gated on a literal path
comparison:

```python
if experiment_module_relative_path == UNIVERSE_MODULE_RELATIVE_PATH:  # "experiments/daily_etf_universe_update.py"
```

`reference_h4` reproduces through `experiments/validate_h4_kurtosis.py`
(§11.2), so the comparison is false and `expected_tickers` stays `None`.
**The coverage validation exists but never runs for `reference_h4`** — the
only sealed cycle there is. Its `verified` status therefore rests on hash
and row-count identity plus the frozen-identity invariant, and **not** on
universe coverage, contrary to what the module documents about itself.

- This does not invalidate §11.2. `verified` is correct for the controls
  that did run, and no control reported a failure it then swallowed.
- It does mean one advertised control is dormant, and that the gating
  mechanism — an engine module comparing against a hardcoded path to one
  workload's script — is the same defect §8.2 lists for
  `reproduction_runner`. Fixing the gate and removing the hardcoded path
  are one change, not two.

**Disposition: deferred to the neutrality phase. No remediation is
performed in this commit**, and none is authorized by this record. The
finding is recorded here so the `verified` status in §11.2 is never read
as stronger than it is.
