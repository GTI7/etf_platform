# Platform Architecture v1.0

**Role: Principal Software Architect, institutional quant research
platforms. Scope: architecture only.** This document designs the
reusable research platform intended to carry H4, H5, H6, and every
hypothesis after them, using H3 as a closed, historical case study —
not as something to redesign, re-evaluate, or extend. It does not
propose H4 or any future hypothesis, does not modify or re-interpret
any H3 artifact, does not generate governance reports, and does not
contain implementation code. Every interface shown below is a
signature-level sketch (method names, inputs, outputs, one-line
intent) to establish a contract — not a working implementation.

**Sources.** `docs/ARCHITECTURE_DECISIONS.md` (AD-001–AD-028, the
codebase's actual recorded decisions), `docs/RESEARCH_GOVERNANCE_STANDARD.md`
(the 8-phase lifecycle, freeze standard, reviewer independence model,
evidence package standard, data provenance requirements, decision
framework), `docs/RESEARCH_PLATFORM_RETROSPECTIVE.md` (gap analysis
and automation opportunities from H3's actual run), and the current
`core/`, `adapters/`, `experiments/`, `research_archive/` layout,
cross-checked directly against the repository.

---

## 1. Purpose

H3 proved the platform's statistical and governance machinery works
end to end, but it also proved — per the retrospective — that the
machinery is still mostly *manual*: hand-written markdown, one-off
scripts, ad hoc archive shapes, and gaps caught only by a dedicated
audit pass rather than by routine tooling. That is acceptable for a
single hypothesis run by a single operator. It does not scale to
hundreds of hypotheses.

This document defines the domain boundaries, public interfaces, and
dependency rules a v1.0 platform needs so that:

- adding hypothesis H*n* never requires touching the platform's code,
  only registering a new project against existing domain APIs;
- adding a new validation stage (a Gate 5, a new statistical test
  family, a new phase) never requires redesigning Validation or
  Statistics;
- adding a new asset class (equities, crypto, bonds) never requires
  touching Research, Validation, Statistics, Governance, or Reporting
  — only a new Data-domain provider;
- every domain can be tested, versioned, and reasoned about in
  isolation, with dependencies flowing in one direction only.

## 2. Design Principles

| Principle | What it means concretely here |
|---|---|
| **Modular** | Six domains, each with one responsibility and one public interface; no domain reaches into another's internals. |
| **Reproducible** | Every domain boundary is a serializable contract (plain data in, plain data out) — nothing depends on in-process object identity or session state, matching AD-002/AD-020's existing discipline. |
| **Deterministic** | Statistics and Validation take explicit inputs (dataset snapshot, parameters, seed) and produce the same output every time; no domain reads a wall-clock or "latest" value implicitly (`Clock` stays an injected `Protocol`, AD-007, not a global). |
| **Testable** | Every public interface is a `Protocol` or a small set of pure functions operating on plain values — the same shape that already made `DataProvider` (AD-014) and `Clock` (AD-007) trivial to fake in tests. |
| **Extensible** | New hypotheses, new gates, new asset classes, and new report formats are additive registrations against existing interfaces, never edits to a domain's contract. |
| **Automation-first** | Every manual H3 activity the retrospective flagged (Section 3 of that document) has a named owning domain and a concrete interface below — automation is a matter of implementing against the contract, not inventing one. |
| **Commercial-ready** | Domain boundaries double as the seams a future multi-tenant or SaaS deployment would need (per-tenant Data domain instance, shared Statistics library, per-tenant Governance policy) — not built now, but not precluded by anything below. |

This inherits, rather than replaces, AD-005: no frameworks, no ORM, no
DI container, no generic repository base class, stdlib only. Domain
boundaries below are enforced by **module structure and import
direction**, not by a framework.

## 3. Platform Overview

Six domains in four dependency layers. Arrows mean "depends on" (calls
into, imports from). No arrow ever points from a lower layer to a
higher one — this is what makes the graph acyclic.

```
 Layer 3   ┌────────────┐
 (leaf)    │ Reporting  │  consumes structured output from every other domain
           └─────┬──────┘  nothing depends on Reporting
                  │ reads
 Layer 2   ┌──────┴──────┐
           │  Research   │  orchestrates the hypothesis lifecycle
           └──┬───┬───┬──┘
              │   │   │
 Layer 1   ┌──┘   │   └──┐
           │      │      │
      ┌────┴───┐  │  ┌───┴────────┐
      │Validation│ │  │ Governance │  audits artifacts/state; calls
      └────┬────┘ │  └─────┬──────┘  nothing above it
           │      │        │
 Layer 0   └──┬───┴───┬────┘
              │        │
         ┌────┴───┐┌───┴────┐
         │  Data  ││Statistics│   both zero-dependency foundations;
         └────────┘└─────────┘   Statistics never touches Data or I/O
```

**Layer 0 — Data, Statistics.** Foundations. Neither depends on the
other, neither depends on anything above. Data owns I/O and storage;
Statistics is a pure computational library with no I/O and no
knowledge that "ETF" or "H3" exist.

**Layer 1 — Validation, Governance.** Both depend only on Layer 0.
Neither depends on the other, and neither depends on Research —
Research depends on them, never the reverse.

**Layer 2 — Research.** The orchestrator. The only domain permitted to
depend on all four domains below it, because coordinating them across
a hypothesis's lifecycle is its entire job.

**Layer 3 — Reporting.** A pure consumer. Depends on all five other
domains' *structured output* (never their internal state), and
nothing depends on it. Removing Reporting entirely would not break any
other domain's ability to function — only humans' ability to read the
result.

## 4. Domain Architecture

Each domain below is specified as: **Responsibility**, **Owns** (the
data/state it is the sole writer of), **Public interface** (signature
sketch only), **Depends on**, **Depended on by**, and **Explicitly out
of scope** (mirroring the discipline `ARCHITECTURE_DECISIONS.md`
already uses for "considered and rejected" notes).

---

### 4.1 Research Domain

**Responsibility.** Owns the hypothesis's identity and its passage
through the 8-phase lifecycle defined in
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 (Hypothesis → Research
Proposal → Pre-validation → Methodology Freeze → Implementation →
Validation → Decision → Archive). It is the only domain that knows
"H3" or "H4" exist as concepts — every other domain operates on
opaque IDs and structured payloads it hands them.

**Owns.**
- The **Project Registry**: every hypothesis ever opened, its current
  lifecycle phase, and its terminal status (open / PASS / FAIL /
  INCONCLUSIVE), across every asset class.
- **Research metadata**: hypothesis statements, research proposals,
  ranked-candidate memos — the Phase 1–2 artifacts.
- **Freeze management**: recording a methodology freeze (the eight
  elements in Standard §3) and its commit hash. Research *records* a
  freeze; it does not *verify* one is real — that is Governance's job
  (§4.4), kept separate so the party proposing a freeze is never the
  same party certifying it, per Standard §1's "separating research,
  review, and decision."
- **Experiment orchestration**: sequencing calls into Validation for
  each gate a project's lifecycle requires.

**Public interface (sketch).**

```python
class ProjectRegistry(Protocol):
    def register_project(self, name: str, asset_class: str, mechanism: str) -> ProjectId: ...
    def get_project(self, project_id: ProjectId) -> ProjectRecord: ...
    def list_projects(self, *, phase: LifecyclePhase | None = None,
                       status: TerminalStatus | None = None) -> list[ProjectRecord]: ...
    def advance_phase(self, project_id: ProjectId, to_phase: LifecyclePhase,
                       evidence_ref: ArtifactRef) -> None: ...

class FreezeManager(Protocol):
    def record_freeze(self, project_id: ProjectId,
                       elements: FreezeElements,  # Standard §3's 8 elements
                       commit_hash: str) -> FreezeId: ...
    def get_active_freeze(self, project_id: ProjectId) -> FreezeRecord | None: ...
    def supersede_freeze(self, prior_freeze_id: FreezeId,
                          new_elements: FreezeElements, commit_hash: str,
                          reason: str) -> FreezeId: ...

class ExperimentOrchestrator(Protocol):
    def run_lifecycle_phase(self, project_id: ProjectId,
                             phase: LifecyclePhase) -> PhaseResult: ...
```

**Depends on.** Data (reads/writes project + freeze metadata),
Statistics (candidate ranking in Phase 2 needs correlation/ranking
primitives directly, not only via Validation), Validation (invokes
gates as lifecycle phases require), Governance (calls
`verify_freeze()` before treating a freeze as effective; calls
`log_decision()` at every phase transition).

**Depended on by.** Reporting only.

**Explicitly out of scope.** Research never computes a statistic
itself (that is Statistics' job via Validation), never decides whether
a freeze is *real* (Governance's job), and never renders a document
(Reporting's job). A Research-domain function that contains a
p-value calculation or writes Markdown directly is a layering
violation.

---

### 4.2 Validation Domain

**Responsibility.** Runs a specific gate or phase's checks against a
frozen methodology and a frozen dataset, and returns a structured
result. Must support new stages (a "Gate 5," a new phase, a new
robustness family) as pure additions, never edits to how existing
gates run.

**Owns.** Gate/phase definitions and their results (not the underlying
statistics — those are computed by Statistics and merely *carried* by
Validation's result objects).

**Public interface (sketch).**

```python
class Gate(Protocol):
    """One pluggable validation stage. New gates implement this and register
    themselves; nothing about GateRunner or existing gates changes."""
    name: str
    required_review_level: ReviewLevel  # Standard §4: Level 1/2/3

    def run(self, context: GateContext) -> GateResult: ...

class GateRunner(Protocol):
    def register_gate(self, gate: Gate) -> None: ...
    def run_gate(self, gate_name: str, context: GateContext) -> GateResult: ...
    def run_sequence(self, gate_names: list[str], context: GateContext) -> list[GateResult]: ...

class ValidationRegistry(Protocol):
    """Maps a lifecycle phase to the ordered gates it requires -- e.g. Phase 3
    Pre-validation currently maps to [signal_independence, data_adequacy,
    economic_rationale, degrees_of_freedom]; Phase 6 Validation maps to
    whatever gate sequence a project's methodology freeze specifies."""
    def gates_for_phase(self, phase: LifecyclePhase) -> list[str]: ...
```

`GateContext` carries a frozen dataset reference (from Data), frozen
methodology parameters (from Research's `FreezeRecord`), and nothing
else — a gate cannot reach outside what it was explicitly given.
`GateResult` is a plain record: statistic values, pass/fail/ambiguous
against the frozen acceptance criteria, and evidence references. This
is the shape H3's own `phase6_economic_validation_2026-07-19.json`
already has; Validation formalizes it as a contract instead of a
convention each script reinvents.

**Depends on.** Data (reads the frozen dataset snapshot), Statistics
(every actual calculation — permutation tests, bootstrap, correlation,
Holm-Bonferroni), Governance (`verify_freeze()` before running, so a
gate can never execute against an unverified or drifted freeze).

**Depended on by.** Research (invokes gates as lifecycle steps),
Reporting (reads `GateResult` history to build reports).

**Explicitly out of scope.** Validation never decides PASS/FAIL/
INCONCLUSIVE for the *cycle* — that is Phase 7's Decision, owned by
Research using Standard §7's framework. A gate reports whether *its
own* criteria were met; only Research aggregates gate outcomes into a
terminal decision.

---

### 4.3 Statistics Domain

**Responsibility.** A pure, stateless computational library. Every
function takes plain numeric/sequence inputs and returns plain numeric
outputs. Contains zero references to ETFs, hypotheses, tickers, gates,
or anything else research-specific — it is exactly as generalizable
today as `experiments/validate_reference_v1_significance.py`'s
`_spearman`, `mean_ic`, `permutation_null`, `holm_bonferroni`, and
`bootstrap_ci` already are, formalized as a first-class domain instead
of living inside one experiment script.

**Owns.** Nothing persistent. Statistics has no database, no files —
its "state" is the pure-function library itself, versioned with the
codebase (AD-021's existing "git tag + integer version" reproducibility
model applies unchanged, since AD-005 already forbids any numeric
dependency whose version could silently drift).

**Public interface (sketch).**

```python
def spearman_rank_correlation(x: Sequence[Decimal], y: Sequence[Decimal]) -> Decimal: ...
def pearson_correlation(x: Sequence[Decimal], y: Sequence[Decimal]) -> Decimal: ...

def permutation_null(observed: Decimal, resample_fn: Callable[[], Decimal],
                      iterations: int, seed: int) -> PermutationResult: ...
def block_bootstrap_ci(series: Sequence[Decimal], block_length: int,
                        iterations: int, seed: int, confidence: Decimal) -> ConfidenceInterval: ...
def holm_bonferroni(p_values: Sequence[Decimal], family_labels: Sequence[str]) -> list[AdjustedResult]: ...

def top_bottom_spread(ranked: Sequence[tuple[EntityId, Decimal]], bucket_size: int) -> Decimal: ...
def rank_entities(scores: Sequence[tuple[EntityId, Decimal]]) -> list[RankedEntity]: ...

def ic_decay(series_by_horizon: Mapping[int, Sequence[Decimal]]) -> PersistenceProfile: ...
```

Every function is deterministic given its inputs and an explicit
`seed` where randomness is involved (no function reads a global RNG
state) — this is what makes a `GateResult` regenerable by a second
party from the archived dataset and methodology alone, per Standard §1
and §6 item 4.

**Depends on.** Nothing. Zero imports from any other domain. This is
the one rule in this document with no exception: the moment a
Statistics function imports from Data, Research, or Governance, it has
stopped being reusable across hypotheses and asset classes and needs
to be split.

**Depended on by.** Validation (primary caller), Research (Phase 2
candidate ranking), Reporting (may recompute a summary statistic for
display, never a new inferential test).

**Explicitly out of scope.** No dataset access, no file I/O, no
knowledge of "acceptance criteria" or "gates" — those are Validation's
vocabulary, not Statistics'.

---

### 4.4 Governance Domain

**Responsibility.** Audits artifacts and state that other domains
produce; certifies nothing it did not independently re-derive. This is
the domain formalization of every gap the retrospective's Section 2/3
identified as "caught only by a dedicated audit pass" — the goal is
that these checks become routine, callable operations instead.

**Owns.** The **decision log** (Standard §5's `decision_log.md`
contract, generalized to every project) and verification results. Does
*not* own the freeze itself (Research does) or the dataset (Data
does) — Governance's outputs are always *about* another domain's
artifact, never a replacement for it.

**Public interface (sketch).**

```python
class FreezeVerifier(Protocol):
    """Confirms a claimed freeze corresponds to a real, resolvable commit
    whose content matches the file's current state -- automates retrospective
    Section 3 item 1."""
    def verify_freeze(self, freeze_id: FreezeId) -> VerificationResult: ...

class IndependenceLabelLinter(Protocol):
    """Flags any document using 'independent' without a Level 2/3 qualifier
    -- automates retrospective Section 3 item 2."""
    def lint(self, paths: Iterable[Path]) -> list[LintFinding]: ...

class ArchiveVerifier(Protocol):
    """Validates a research_archive/<project>/ directory against the Standard
    §5 manifest (hypothesis.md, methodology.md, dataset_manifest.json,
    dataset_hashes/, experiment_results/, reviewer_reports/, decision_log.md)
    -- automates retrospective Section 3 item 4."""
    def verify_archive(self, project_id: ProjectId) -> ArchiveCompletenessReport: ...

class DatasetIntegrityChecker(Protocol):
    """Confirms a dataset snapshot's content hash matches its manifest entry,
    and that every stored source tag is one the current ingestion code can
    actually produce -- Standard Section 6 controls 1-2."""
    def verify_dataset(self, manifest_ref: ArtifactRef) -> IntegrityReport: ...

class ReproducibilityChecker(Protocol):
    """Re-runs a GateResult from its archived dataset + methodology + code
    reference and confirms the figures match -- Standard Section 6 control 4."""
    def reproduce(self, gate_result_ref: ArtifactRef) -> ReproductionReport: ...

class DecisionLogger(Protocol):
    """Append-only. Every entry is immutable once written; a correction is a
    new entry, never an edit -- Standard Section 5's decision_log.md rule,
    generalized to every project."""
    def log(self, project_id: ProjectId, entry: DecisionLogEntry) -> None: ...
    def history(self, project_id: ProjectId) -> list[DecisionLogEntry]: ...
```

**Depends on.** Data only — Governance reads datasets, manifests, and
committed files/artifacts through Data's read APIs. It explicitly does
**not** import Research's, Validation's, or Statistics' internal
logic; it treats their outputs as opaque artifacts (files, JSON
records, commit hashes) to be independently re-checked, exactly as an
external auditor would. This is what lets Governance certify Research
and Validation without being coupled to either.

**Depended on by.** Research (calls `verify_freeze()` and `log()` at
lifecycle gates), Validation (calls `verify_freeze()` before running a
gate), Reporting (reads verification reports and decision-log history
for compliance sections).

**Explicitly out of scope.** Governance never *fixes* what it finds —
`FreezeVerifier` reports a drifted freeze; it does not re-freeze
anything. Remediation is always a human or Research-domain action
taken in response to a Governance finding, keeping the "who checks"
and "who fixes" roles separate for the same reason review and decision
stay separate under Standard §1.

---

### 4.5 Reporting Domain

**Responsibility.** Produces human-readable output from structured
data other domains already hold. Never computes a new figure, never
makes a determination — a report is a rendering, not a source of
truth.

**Owns.** Report templates and rendered output artifacts.

**Public interface (sketch).**

```python
class ReportBuilder(Protocol):
    """Assembles structured evidence from Research/Validation/Governance into
    one format-neutral document model."""
    def build(self, project_id: ProjectId, report_type: ReportType) -> ReportModel: ...

class Renderer(Protocol):
    """One renderer per output format. New formats (HTML now planned, PDF
    later) are new Renderer implementations -- ReportBuilder and every
    existing renderer are untouched."""
    format: Literal["markdown", "json", "html", "pdf"]
    def render(self, model: ReportModel) -> bytes: ...

class ReportRegistry(Protocol):
    def register_renderer(self, renderer: Renderer) -> None: ...
    def render(self, model: ReportModel, format: str) -> bytes: ...
```

`ReportModel` is the same kind of plain, serializable structure
`GateResult` and `DecisionLogEntry` already are — this is what makes
"generate the report from JSON evidence" (retrospective Section 3 item
7) a real automation target instead of an aspiration: today's
hand-written `H3_PHASE6_ECONOMIC_VALIDATION_REPORT.md` and today's
`phase6_economic_validation_2026-07-19.json` are the same information
authored twice; `ReportBuilder` + `Renderer` make the JSON the only
authored copy.

**Depends on.** Research, Validation, Governance, Statistics, Data —
as a read-only consumer of each domain's structured output types. Never
calls a mutating method on any of them.

**Depended on by.** Nothing. Reporting is a true leaf; no domain's
correctness can ever depend on Reporting having run.

**Explicitly out of scope.** No PASS/FAIL logic, no statistical
recomputation beyond display-level summarization, no write access to
any other domain's owned state.

---

### 4.6 Data Domain

**Responsibility.** Datasets, providers, storage, caching, and
versioning for every asset class the platform will ever support — the
one domain every future asset class extends, and the only domain that
should ever need a new concrete implementation when ETFs become
"ETFs and equities and crypto and bonds."

**Owns.** Raw and derived data: prices, indicators, scores, dataset
manifests and content hashes, provider registrations, cache state. The
existing `core/market_data/` and `core/analytics/persistence/`
packages are Data-domain code today, organized by asset-class-specific
subpackage; this domain's job is to keep that pattern rather than let
Research/Validation/Statistics/Governance reach into `sqlite3` calls
directly.

**Public interface (sketch).**

```python
class DataProvider(Protocol):
    """Already exists as AD-014's contract, generalized here beyond price
    bars: any provider (price, fundamentals, on-chain, macro) implements
    this shape. Provider-specific parsing stays fully isolated at this
    boundary, same as today's YahooFinanceProvider."""
    name: str
    asset_class: AssetClass
    def fetch(self, instrument_id: str, start: date, end: date) -> list[RawObservation]: ...

class ProviderRegistry(Protocol):
    """AD-015's existing explicit dict pattern, unchanged."""
    def register(self, provider: DataProvider) -> None: ...
    def get(self, name: str) -> DataProvider: ...

class DatasetRepository(Protocol):
    def get_snapshot(self, manifest_ref: ArtifactRef) -> DatasetSnapshot: ...
    def write_snapshot(self, data: DatasetSnapshot, source_tag: str) -> ArtifactRef: ...

class DatasetVersioner(Protocol):
    """Closes retrospective Technical Debt item 1 -- no dataset-hashing
    infrastructure exists today. Content-addressed, immutable per Standard
    Section 6 control 1: a correction is always a new snapshot + new
    manifest entry, never an in-place UPDATE."""
    def compute_hash(self, snapshot: DatasetSnapshot) -> ContentHash: ...
    def write_manifest(self, snapshot_refs: list[ArtifactRef]) -> ArtifactRef: ...

class CacheLayer(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def put(self, key: str, value: bytes, ttl: int | None = None) -> None: ...
```

**Depends on.** Nothing. True foundation, matching `core/market_data/`
and `core/analytics/persistence/`'s current position at the bottom of
the existing import graph.

**Depended on by.** Every other domain (directly or, for Statistics,
not at all — Statistics is handed data by its caller and never fetches
its own).

**Explicitly out of scope.** No statistical computation (that belongs
to Statistics), no gate logic, no knowledge of "hypothesis" as a
concept — Data's vocabulary is instruments, snapshots, providers, and
manifests, the same vocabulary regardless of which asset class or
which research project is consuming it.

## 5. Cross-Domain Dependency Rules

**Allowed (per §3's layering):**

| From ↓ / To → | Data | Statistics | ETF | Governance | Validation | Research | Reporting |
|---|---|---|---|---|---|---|---|
| Data | — | ✕ | ✕ | ✕ | ✕ | ✕ | ✕ |
| Statistics | ✕ | — | ✕ | ✕ | ✕ | ✕ | ✕ |
| ETF | ✅ | ✅ | — | ✕ | ✕ | ✕ | ✕ |
| Governance | ✅ | ✕ | ✕ | — | ✕ | ✕ | ✕ |
| Validation | ✅ | ✅ | ✕ | ✅ | — | ✕ | ✕ |
| Research | ✅ | ✅ | ✕ | ✅ | ✅ | — | ✕ |
| Reporting | ✅ | ✅ | ✕ | ✅ | ✅ | ✅ | — |

The **ETF** row and column were added by AD-068 (boundary-hardening step
1). ETF is an *asset class*, not a platform layer: it plugs in above the
platform and reaches down into Data and Statistics, and nothing reaches
back up into it.

**Forbidden dependencies, stated explicitly:**

- **Statistics → anything.** The single hard rule (§4.3). A pure
  computational library that imports a domain concept stops being
  reusable across hypotheses or asset classes.
- **Data → anything.** The foundation never calls upward; if Data code
  needs "what hypothesis is this for," that information is being
  threaded through the wrong layer.
- **Anything → ETF** (AD-068). No platform domain may depend on an asset
  class. §1 requires that "adding a new asset class (equities, crypto,
  bonds) never requires touching Research, Validation, Statistics,
  Governance, or Reporting", and §3 requires Statistics to have "no
  knowledge that 'ETF' or 'H3' exist"; an edge into ETF from any of them
  contradicts both. This includes **Data → ETF**, which the "never calls
  upward" rule above already covers. This is the table's first
  "nothing may depend on X" entry, which is why AD-068 records it as a
  novel rule rather than an application of an existing one.
- **Governance → Research, Validation, Reporting.** Governance audits
  by re-deriving from Data and from plain artifacts (files, hashes,
  JSON records) — never by calling into another domain's orchestration
  code. This is what lets a Governance check remain valid evidence
  even if Research's internal implementation changes.
- **Validation → Research.** Research invokes Validation as a
  lifecycle step; Validation must never call back into Research, or a
  gate's execution could depend on lifecycle state in a way that makes
  it impossible to run a gate in isolation (e.g., for `Reproducibility
  Checker` re-runs).
- **Anything → Reporting.** No domain's correctness may depend on a
  report having been generated. Reporting failing or being skipped
  must never block a lifecycle phase, a gate, or a decision.

**Why this prevents cycles.** Every allowed edge points from a domain
in a higher-numbered layer (§3) to one in an equal-or-lower layer,
and no domain calls into a same-layer peer (Validation and Governance,
both Layer 1, never call each other; Data and Statistics, both Layer
0, never call each other). A cycle would require an edge that violates
this ordering, and the table above contains none. ETF cannot introduce
one either: it has out-edges only and no in-edges, so no path can
return to it.

**Enforcement.** Consistent with AD-005 (no frameworks), this is
enforced by two cheap, stdlib-only mechanisms rather than a DI
container or a plugin system:
1. **Import-direction lint** — a script (naturally a Governance-domain
   tool) that fails if any module under `core/statistics/` imports
   from `core/data/`, `core/governance/`, `core/validation/`,
   `core/research/`, or `core/reporting/`, and equivalently for every
   other domain's forbidden edges in the table above.
2. **Package structure mirrors the domain, one-to-one** — e.g.
   `core/data/`, `core/statistics/`, `core/governance/`,
   `core/validation/`, `core/research/`, `core/reporting/` — so the
   forbidden-edge check is a matter of scanning `import` statements
   by top-level package name, no AST-level cleverness required.

   **Amendment (AD-068).** Item 2 holds for every domain that *has* a
   package of its own, which is the steady state this document
   describes. It does not hold during a split. Where a domain has been
   decided but its symbols still live inside another domain's packages,
   the check may attribute an import to a domain **by the symbol it
   binds** rather than by the module path that hosts it, which requires
   reading imports per-alias rather than per-statement.

   This permission is **narrow and self-terminating**. It applies only
   to domains not yet separated by package path; the symbols concerned
   must be enumerated in one place (`ETF_SYMBOLS_BY_MODULE` in
   `tools/check_import_boundaries.py`), which is an inventory of where
   the split has not been made and not an exemption list; and the
   departure **ends when that inventory empties**, at which point the
   domain is identified by path like every other and the per-alias
   attribution is deleted. Nothing here licenses AST analysis for any
   other purpose, and the rest of item 2 is unchanged.

## 6. Automation Roadmap

The retrospective (`docs/RESEARCH_PLATFORM_RETROSPECTIVE.md` §3, §6)
already identified *what* to automate from H3's real run. This section
assigns each item an owning domain and interface from §4, so
implementation has a concrete target rather than a general intention.

| Retrospective item | Owning domain | Interface |
|---|---|---|
| Freeze-commit verifier | Governance | `FreezeVerifier.verify_freeze()` |
| Independence-label linter | Governance | `IndependenceLabelLinter.lint()` |
| Decision-log entry scaffolding | Governance | `DecisionLogger.log()`, invoked automatically by Research at every `advance_phase()` call rather than authored by hand |
| Archive-completeness checker | Governance | `ArchiveVerifier.verify_archive()` |
| Dataset snapshot/hash utility | Data | `DatasetVersioner.compute_hash()` / `write_manifest()` |
| Two-directional coverage check as standing tooling | Data | a `DatasetIntegrityChecker`-adjacent check inside `DatasetRepository`, replacing the one-off `maintenance/remediate_h3_invalid_pricebar_rows.py` script |
| Report generation from JSON evidence | Reporting | `ReportBuilder.build()` + `Renderer.render()`, sourced from the same `GateResult`/`DecisionLogEntry` structures Validation and Governance already produce |

**Sequencing.** The retrospective's own Tier 1–4 roadmap (§6 of that
document) remains the right prioritization — cheap governance wins
before archive tooling before dataset-hashing infrastructure before
the organizationally-unsolvable Level 3 review gap. This document adds
only the mapping of *where in the platform* each tier's work lands:
Tier 1 and most of Tier 2 are Governance-domain interfaces; Tier 3 is
almost entirely Data-domain (`DatasetVersioner`); the Report-from-JSON
item is Reporting-domain and can be built independently of the other
tiers, since Reporting depends on their output shape but not on their
implementation being finished first — a `ReportBuilder` can render
today's hand-written-equivalent JSON immediately.

## 7. Extensibility

**New asset classes (equities, crypto, bonds) require zero changes
outside the Data domain.** Every other domain already operates on
asset-class-neutral vocabulary:
- Research's `ProjectRecord` carries an `asset_class` field but
  contains no asset-class-specific logic — a crypto momentum
  hypothesis follows the identical 8-phase lifecycle as an ETF one.
- Validation's `Gate` and `GateContext` operate on whatever dataset
  and parameters a project's freeze specifies; nothing about
  `GateRunner` assumes "ETF."
- Statistics never had asset-class knowledge to begin with (§4.3).
- Governance's checks (freeze verification, archive completeness,
  dataset integrity) are defined over artifacts and hashes, not over
  instrument type.
- Reporting templates parameterize on `ReportModel`, which is populated
  identically regardless of what asset class produced the evidence.

The only new code a new asset class requires is a `DataProvider`
implementation (equities: a new provider beside
`YahooFinanceProvider`; crypto: an exchange/on-chain provider; bonds: a
yield-curve or pricing-service provider) registered with the existing
`ProviderRegistry` (AD-015). This is the same seam AD-014 already
proved works — `YahooFinanceProvider` is fully isolated behind the
`DataProvider` Protocol today, and nothing above the Data domain knows
or cares that Yahoo Finance specifically is the source.

**New research domains (a "credit spread" research program, a
"portfolio construction" program) require zero platform redesign.**
The Research domain's Project Registry is already general — a project
is `(name, asset_class, mechanism)`, not `(ETF ticker, scoring
dimension)`. A structurally different research program is simply
projects with a different `mechanism` description under the same
lifecycle, the same Validation gate contract, the same Statistics
library, the same Governance checks, and the same Reporting templates.

**What *would* require redesign (stated explicitly, so it is not
silently discovered later).** A change to the 8-phase lifecycle itself,
or to the Standard §3 freeze-element list, is a Research-domain and
Governance-domain contract change, not an asset-class extension — it
should be rare and deliberate, versioned the same way
`docs/RESEARCH_GOVERNANCE_STANDARD.md` itself is versioned (§9 of that
document: "a revision is a new, dated version, not a silent edit").

## 8. Relationship to the Current Codebase

This document is descriptive of a target shape, not a mandate to
refactor `core/market_data/` and `core/analytics/` today. The existing
code already follows most of this document's principles by convention
— `DataProvider` and `ProviderRegistry` (AD-014/015) are already
exactly the Data-domain interface shape in §4.6; `core/shared/clock.py`
is already the kind of injectable-Protocol pattern every domain
interface above follows; the `experiments/*.py` statistical helper
functions are already Statistics-domain-shaped pure functions, just not
yet organized under a `core/statistics/` package of their own.

The gap this document identifies is organizational, not behavioral:
Statistics logic currently lives inside `experiments/` scripts rather
than a first-class package Validation can import from without
depending on an experiment script's other side effects; Governance
logic currently exists only as documents and one-off audit passes
(`H3_GOVERNANCE_COMPLIANCE_AUDIT.md`) rather than callable checks;
Reporting is currently hand-authored Markdown rather than rendered
from the JSON that validation scripts already emit. Closing those gaps
is future implementation work, sequenced per §6 — out of scope for
this document by its own restrictions.

## 9. Document Versioning

**Version:** 1.0. This document follows the same discipline
`RESEARCH_GOVERNANCE_STANDARD.md` §9 establishes for itself: a future
revision is a new, dated version referencing what changed and why, not
a silent edit. Domain boundaries and the dependency table in §5 are
the parts of this document future revisions should change least
often — they are the platform's load-bearing contract.
