# Phase F — Implementation Readiness Review

**Date:** 2026-07-24
**Reviewer role:** principal software architect / research platform lead.
**Repository state reviewed against:** canonical `D:\Claude\etf_platform`,
`master`, HEAD **`67b42bd`**, working tree clean, `origin/master ==
master`, suite **789 collected → 787 passed, 1 skipped, 1 xfailed**
(re-derived by `pytest --collect-only`).
**Documents read in full:** `PHASE_F_ARCHITECTURE_ACCEPTANCE.md`,
`PHASE_F_ACCEPTANCE_CONDITIONS.md`,
`PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md`,
`PHASE_4_PHASE_F_RESEARCH_EXECUTION_ENGINE_PROPOSAL.md`,
`ARCHITECTURE_DECISIONS.md` AD-060 … AD-069 and the AD-061 … AD-067
reservation block.
**Finding numbering:** **R-16 … R-23**, continuing the series the
Resolution opened (R-1 … R-7) and the Acceptance Review continued
(R-8 … R-15).

**Review level: Level 2 — AI-assisted adversarial review**
(`RESEARCH_GOVERNANCE_STANDARD.md` §4). Procedurally separate from the
sessions that produced the Proposal, the Resolution, the Gate Review, the
Acceptance Review, and the Conditions amendment; every load-bearing claim
below was re-derived from the repository by execution. **Not**
organizationally independent under any definition §4 recognizes: same
model family and vendor, no incentive separation, no accountable
persistent reviewer identity. **Level 3 review is unavailable on this
platform.** Per §4's binding sentence, **this document must never be
cited using the unqualified word "independent."**

**This document is not a second F-0 architecture review.** F-0's
precondition is discharged by `PHASE_F_ARCHITECTURE_ACCEPTANCE.md` as
restated by F-C4. This is a **readiness** review: it asks whether the
repository can begin implementing an architecture that has already been
approved, and what the first executable milestone must be.

**Production code modified: none. Tests modified: none. ADRs modified:
none.** AD-061 … AD-067 remain reserved and unaccepted; the accepted
ceiling remains AD-069.

---

## 0. Verdict

> ## ⚠️ READY FOR F-0 ONLY — NOT READY FOR F-1

Split, because a single answer would be false in one direction or the
other:

| Track | Verdict | Why |
|---|---|---|
| **F-0** (ADR acceptance, docs only) | **READY — proceed now** | Every precondition holds at HEAD `67b42bd`. The Level 2 architecture review exists and its conditions are written down. F-0 is the next commit. |
| **F-1 … F-10** (the Phase F engine, fixture-only) | **NOT READY — blocked on F-0 only** | No structural obstacle found. The blocker is the repository's own discipline: decisions are recorded before they are implemented. Unblocks the moment F-0 lands. |
| **Golden Run 001** (a real ETF experiment, real evidence) | **NOT READY — four findings must be ruled on in F-0's text** | R-16 … R-19 below. Three of the four are gaps **no Phase F document names**, and none is visible from inside F-1 … F-10, because F-10 runs a fixture experiment against a fixture cycle. |

The architecture is sound and I am not re-litigating it. Everything below
is about the distance between an approved design and a first real run —
which is larger than the Phase F documents imply, in three specific and
repairable places.

---

## 1. Is the repository ready to start Phase F implementation?

### 1.1 What holds (re-derived, not carried over)

| Precondition | Verified at `67b42bd` | Verdict |
|---|---|---|
| Tree clean, pushed | `git status --porcelain` empty; branch matches origin | ✅ |
| Suite green | 789 collected = 787 + 1 skipped + 1 xfailed — exactly the claimed state | ✅ |
| AD-061 … AD-067 unoccupied | Only occurrences are inside the reservation block, `ARCHITECTURE_DECISIONS.md:3098-3137` | ✅ |
| Accepted ceiling is AD-069 | AD-068 at `:3139`, AD-069 at `:3274`, file ends at `:3552` | ✅ |
| Phase F target packages do not exist | No `core/research/execution/`; `adapters/` holds `cli/` alone | ✅ (clean start) |
| The kernel has never been exercised | `find` → no `transition_records.jsonl` anywhere | ✅ (as documented) |
| `research` holds no `store` grant | `check_import_boundaries.py:176` — `{data, statistics, governance, validation}` | ✅ |
| The Level 2 architecture review exists | `PHASE_F_ARCHITECTURE_ACCEPTANCE.md`, conditions C-1 … C-12 + F-C1 … F-C4 | ✅ |

The governance substrate Phase F consumes is genuinely complete and
genuinely unexercised. That combination is the correct state to begin
from, and the repository is in it.

### 1.2 What does not hold

**F-0 has not been written.** No code may land before it. That is not a
formality here: four of the seven ADs carry *required content* that
constrains F-1's field sets (F-C2), F-2's test obligations (F-C3), and
the wording of every disclosure. Writing F-1 first would mean writing the
field set and then back-filling the decision that authorized it — the
inversion this repository's discipline exists to prevent.

**The Golden Run track is blocked on findings, not on F-0.** R-16 … R-19
are gaps in the *plan*, not defects in the *design*. Each is cheap to
close and each is invisible from inside the F-1 … F-10 sequence.

---

## 2. Which AD decisions must be accepted before code exists?

**All seven — AD-061 … AD-067 — in one docs-only commit. No eighth
number.** I checked for a decision Phase F makes that falls outside the
seven and found none, including for my own findings below.

### 2.1 Required content, consolidated

Each AD must carry, at minimum, what §6.1 of the Proposal specifies, as
amended by Resolution §5, plus:

| AD | Additional required content, and its source |
|---|---|
| **AD-061** | F-C2's closed measurement-artifact field set (incl. a **code revision reference**); F-C3's propagation **contract clause**; F-C1's §8 non-claims; C-5's `core.store` scoping sentence; **and R-16's `etf` scoping sentence** (new, §3.1) |
| **AD-062** | Unchanged; plus C-10's collision bullet. `ArchiveWriter` stays domain-blind — F-C2 must not be read as widening it |
| **AD-063** | The two literal enumerations, module-scoped, censuses **re-dated to the HEAD at which F-0 lands** (C-4) |
| **AD-064** | F-C1's full `provenance_ref = None` → `reproduction_record_ref = None` path; the `reproduction_runner` disconnect; per-element **absence semantics**; `experiment_name` is a label, not an identity |
| **AD-065** | Unchanged — receipt is a convenience transcription |
| **AD-066** | F-C3's **propagation attestation** at gate registration; two-registry disagreement disclosed as unenforced |
| **AD-067** | The four amendment triggers; F-C3's non-detection disclosure; censuses re-dated (C-4) |
| **All seven** | F-C4's **review-basis line**, citing the Acceptance Review **by level**, disclosing Level 3 unavailability. Never "the independent architecture review" |

### 2.2 Which are load-bearing for the *first slice*, specifically

Not all seven bind equally on day one, and knowing which is which
prevents F-0 from being written as a formality:

- **AD-061, AD-062, AD-063, AD-064** constrain F-1 … F-6 directly. A
  field set, a filename rule, an import rule, and a separation rule — all
  four are consumed by the first four code commits.
- **AD-066** is not consumed until F-10, but it governs the **human act**
  that makes Golden Run 001 possible. It cannot be deferred past F-0
  because the attestation obligation F-C3 puts in it has to exist before
  anyone registers a gate.
- **AD-065, AD-067** are disclosures. They bind readers, not code.

### 2.3 One correction owed to the reservation block

See **R-22**: the block states *"New ADRs therefore number from
**AD-068**."* True when written; **stale at HEAD** — AD-068 and AD-069
are both accepted and the next free number is **AD-070**. The block is
the single place a reservation is discoverable, and a stale "next free
number" in it is exactly the collision hazard it was written to prevent.
Correct it in the F-0 commit.

---

## 3. Findings

### R-16 (blocking — the ETF slice) — a real ETF `Experiment` cannot be written under `core/research/`, and AD-068 makes that permanent rather than repairable

**Finding.** The Acceptance Review's R-14 asks the right question — *what
dependency does a real `Experiment` acquire?* — and answers it only for
`core.store`. It concludes that a direct `core.store` import from
`core/research/` would be "a boundary violation requiring a recorded
decision in the same commit — correct and loud." That is true, and it
understates the case by one whole domain.

An `Experiment` that ranks ETFs must reach ETF data. At HEAD:

- `DOMAIN_OF_TOPLEVEL["analytics"] = ETF_DOMAIN`
  (`check_import_boundaries.py:107-118`).
- `ALLOWED_DEPENDENCIES["research"] = {data, statistics, governance,
  validation}` (`:176`) — **no `etf`**.
- `ALLOWED_DEPENDENCIES[ETF_DOMAIN] = {data, statistics}` (`:173`), and
  the file's own comment states that `etf` *"deliberately appears in no
  other domain's value set (AD-068 decision 2)… an edge into ETF from any
  of them is a boundary violation by construction."*
- Worse, and the part R-14 could not have reached without looking:
  `ETF_SYMBOLS_BY_MODULE` (`:131-142`) attributes **`ETFId`**
  (`core.shared.ids`), **`ETF`** (`core.market_data.domain.models`), and
  **`insert_etf` / `get_etf` / `get_etf_by_ticker`**
  (`core.market_data.persistence.repository`) to the `etf` domain
  **regardless of which module hosts them**. So reaching ETFs through the
  *granted* `research → data` edge is **also** a violation.

The difference from R-14's `store` case is decisive. A `research → store`
grant is *addable* by recorded decision — AD-069's rule is explicitly
demand-driven. A `research → etf` grant is **not addable**: AD-068
decision 2 exists precisely to make Research asset-class-neutral, and
granting it would contradict an accepted AD in the same commit that
consumed it.

**This is not a defect. It is the design working, one increment before
anyone noticed.** The `Experiment` Protocol is domain-blind *because* the
ETF implementation cannot live inside Research. The Proposal says the
right thing — *"the runner never learns what an ETF is"* (§3.1) — without
ever stating that this is **structurally enforced** rather than
stylistically preferred.

**Ruling.**

1. **AD-061 gains one sentence, beside C-5's:** *no `Experiment`
   implementation that reads ETF data may live under `core/research/`.
   `analytics` is the `etf` domain and `research` holds no `etf` grant;
   AD-068 decision 2 makes that grant unavailable, not merely absent, and
   `ETF_SYMBOLS_BY_MODULE` extends the rule to ETF symbols hosted in
   asset-class-neutral modules. An ETF `Experiment` therefore lives
   **outside `core/`** — at the composition root or under `experiments/`
   — and this is a structural consequence of AD-068, not a placement
   preference.*
2. **No grant is added. No AD is amended. No file is moved.** The repair
   is a sentence, because the mechanism already refuses correctly.
3. **F-9's AST test is unaffected** — its predicate is AD-063's authority
   enumerations, and `core.analytics` carries no Decision Chain
   authority.

---

### R-17 (blocking — Golden Run) — dataset identity has a reader, no writer, and zero instances repository-wide

**Finding.** The Golden Run must capture dataset identity. The repository
has a complete, tested apparatus for *consuming* it and none for
*producing* it:

| Capability | Exists? | Where |
|---|---|---|
| Parse & structurally validate `dataset_manifest.json` (schema v3) | **yes** | `dataset_manifest.py:81` `parse_dataset_manifest` |
| Verify a declared `content_hash` / `row_count` against the file | **yes** | `reconstruction_loader.py:116` `_verify_dataset_integrity` |
| Reconstruct a database from a manifest + snapshots | **yes** | `reconstruction_loader.py:233` `reconstruct_database` |
| Write ETF / TradingSession / PriceBar snapshots | **yes** | `dataset_snapshots.py:74, 127, 198` |
| **Emit a `dataset_manifest.json`** | **no** | nothing anywhere |

And the census: **`find . -name dataset_manifest.json` returns nothing.**
Not one instance exists, for any cycle, real or fixture. The manifest
class has a parser, a verifier, a consumer, and no producer and no
production instance.

Compounding it: **the database is not a repository artifact.**
`.gitignore:27` excludes `*.db`, and `experiments_etf_universe.db` is
confirmed ignored. Dataset identity for any real run therefore *cannot*
come from the database — it can only come from committed snapshots plus a
manifest that hashes them. There is no alternative route.

**Ruling.**

1. **One additive `tools/` module is required** — the smallest thing that
   emits schema-v3 entries `(dataset_id, type, source_table, row_count,
   snapshot_path, content_hash, schema_version)` for exactly the three
   required source tables, hashing with the **same** `sha256_of_file`
   (`canonical_jsonl.py:68`) that `_verify_dataset_integrity` checks with.
2. **It goes in `tools/`, beside `archive_manifest.py`, for the same
   reason Q1's ruling put `experiment_results/` creation there:** it
   touches no `core/` module, it is not a domain abstraction, and it does
   not belong to Phase F's layer.
3. **Its acceptance test is a round-trip against the existing reader**, not
   a schema assertion of its own: build → `parse_dataset_manifest` →
   `preflight_validate` → `reconstruct_database`. A writer verified only
   against its own idea of the schema is a second schema.
4. **It is not a framework.** No dataset registry, no snapshot scheduler,
   no refresh policy, no incremental hashing. One function, one consumer.

---

### R-18 (blocking — Golden Run) — the reproduction leg has no admissible form, and exactly one route needs no new authority

**Finding.** The Golden Run must let a reproduction attempt verify the
result. The repository's reproduction model is `run_reproduction`
(`reproduction_runner.py:183`), and its signature is decisive:

```python
run_reproduction(*, repo_root, cycle_dir, dataset_manifest_path,
                 migrations_relative_path,
                 experiment_module_relative_path,   # <- a path, in a pinned worktree
                 commit_hash, scratch_db_path, run_experiment)
```

It loads the experiment **module by relative path out of a pinned
worktree**. Phase F's `Experiment` is a **live object injected by the
caller** with no path, no commit pin, and no hash — R-11's finding,
which I confirm.

The three obvious ways to close that gap are each forbidden:

- A bridge object (`ReproducibilityChecker`) — Proposal §7.1 forbidden
  list, restated as still in force by F-C2 §2.3 item 4.
- Wiring `ResearchRunner` into `reproduction_runner` — R-11 defers it to
  a later increment explicitly.
- `experiments/validate_h4_*.py` as a substitute for the runner —
  §7.1 forbidden.

**There is a fourth route, and it requires no new authority, no bridge,
and no new abstraction: one implementation, two callers.**

Write the ETF experiment **once**, as a module under `experiments/` with
a `run()` entrypoint — the shape `run_reproduction`'s `run_experiment`
callable already expects, and the shape every existing
`experiments/validate_*.py` already has. Then adapt it to the
`Experiment` Protocol with a thin object **at the composition root**,
outside `core/`. The module is the reproduction target; the adapter is
the Phase F input. Nothing binds the two models to each other — the
**composition root** binds them, which is what a composition root is for.

This also satisfies R-16 for free: the module and its adapter both live
outside `core/`, where the `etf` grant is not required.

**Ruling.**

1. **F-0 must record this route explicitly**, in AD-064 beside R-11's
   disconnect disclosure, in these terms or their equivalent: *Phase F
   builds no bridge to `core.governance.reproduction_runner`. An
   experiment that is to be both executed under Phase F and reproduced
   under `run_reproduction` is implemented once as a module with a `run()`
   entrypoint and adapted to the `Experiment` Protocol at the composition
   root. The two models remain unconnected; the operator connects them by
   choosing the same module for both.*
2. **§7.1's `experiments/validate_h4_*.py` prohibition is unrelaxed and
   must be restated as what it is:** a prohibition on **H4 research
   content** written as a shortcut around the runner. A non-H4 experiment
   module that the runner itself invokes through an adapter is not that
   shortcut. **This reading must be written down in F-0, not assumed** —
   it is close enough to the prohibition that a later reader will
   otherwise have to guess.
3. **No `ReproductionRecord` producer is authorized by this ruling.**
   Writing the `(commit_hash, dataset_content_hashes,
   result_report_hash)` triple for Golden Run 001 is a **human act**
   against the existing frozen dataclass, not a new component.

---

### R-19 (blocking — Golden Run) — Golden Run 001 must not be `reference_h4`

**Finding.** The obvious target for a first real run is `reference_h4`
— it is registered (`core/research/reference_h4_registration.py`), it has
an `archive_manifest.json`, and it is the repository's one open cycle.
It is the wrong target, on the Proposal's own terms and on the evidence:

- §7.1: *"Producing the repository's first **real**
  `transition_records.jsonl` for `reference_h4` is a governance act, not
  an implementation step,"* requiring a real hypothesis, a real frozen
  methodology, and a `decision_log.md` entry. **No Phase 1 or Phase 2
  artifact exists for `reference_h4`** — its own registration module
  states this, twice, and asserts nothing about hypothesis content.
- §7.1 again: registering a phase → gate assignment for a **real** cycle
  is a governance act that decides what evidence a phase requires.
- `research_archive/reference_h4/` contains **`archive_manifest.json` and
  nothing else** (verified). It has no `experiment_results/` (H-4, C-11
  open), no `dataset_hashes/`, no `decision_log.md`.

Running Golden Run 001 against `reference_h4` would therefore either
require inventing H4 research content or produce a permanent,
hash-chained record on a real research cycle asserting a transition that
demonstrates a mechanism. Both are the class of defect the governing
principle forbids.

**Ruling.**

1. **Golden Run 001 runs against a dedicated cycle, `golden_run_001`**,
   scaffolded by the existing `scaffold_project_archive()`
   (`tools/archive_manifest.py:107`), which creates all three evidence
   subdirectories (`dataset_hashes`, `experiment_results`,
   `reviewer_reports`) with `.gitkeep`. This **sidesteps C-11 entirely**
   rather than depending on it — no `ArchiveWriter` precondition is
   relaxed and `reference_h4` is not touched.
2. **`golden_run_001` is a mechanism cycle and must be marked as one** in
   its own `README.md` and `decision_log.md`, in the same words §7.1 uses:
   it demonstrates the mechanism and nothing more; its ranking is not a
   research result; its frozen criteria are demonstration criteria frozen
   for this run only.
3. **C-11 remains open and remains correct**, on its own timetable, by
   the additive `tools/` route.

---

### R-20 (required disclosure) — freeze verification is real git I/O, and Golden Run 001 has an operating constraint no Phase F document states

**Finding.** `GateRunner.run_sequence` brackets the gate sequence with
`verify_freeze` (`freeze_verifier.py:141`), which resolves a commit ref
and diffs the covered paths against it, **with no committed or
uncommitted drift permitted since**. `compose_transition()` then refuses
with `FreezeNotVerified` or `BracketInvalidated` if the bracket does not
project to `verified`.

The consequence for a first real run, stated because nowhere else states
it: **Golden Run 001's `freeze_commit_ref` must be a commit that already
contains its methodology and criteria files, and the run must execute
against a clean working tree.** Freezing a methodology and running the
experiment in the same uncommitted edit produces `DRIFTED` → a refusal.
Additionally, `freeze_covered_paths` cannot be empty: `GateContext`
refuses it in `__post_init__` before the runner ever gets there
(AD-047 part 2), and `verify_freeze` would return `UNVERIFIABLE` for it
in any case (AD-051).

**Ruling.** No mechanism, no guard. One bullet in Golden Run 001's own
milestone definition (§7.4 below) and one sentence in its
`decision_log.md`. This is an operator obligation, discharged by
sequencing: **freeze commit → clean tree → run**.

---

### R-21 (required disclosure) — `dataset_refs` is opaque, so F-C2's "dataset reference" element is satisfiable by an arbitrary string

**Finding.** F-C2 requires that the archived record carry a **dataset
reference**. `MeasurementBundle.dataset_refs` is `tuple[str, ...]` of
*opaque* refs (§3.3, AD-042). Nothing resolves them, and — consistent
with R-5, R-10, and F-C1 §1.3 item 4 — **nothing should**: a runner-side
resolver would be a duplicated rule at the wrong altitude.

The consequence: F-C2's dataset-identity element can be discharged in
letter by any string. Opaque refs are evidence retention; they are not
dataset identity. Dataset identity lives in `dataset_manifest.json`
(R-17), and the two are only connected if the operator connects them.

**Ruling.** Not a Phase F mechanism obligation. A **Golden Run 001
acceptance criterion**: *every entry in `dataset_refs` resolves to a
declared `snapshot_path` in `golden_run_001`'s own
`dataset_manifest.json`, checked as part of the milestone's acceptance,
not by any runtime guard.* Record it in AD-064 as a stated non-claim:
*Phase F does not validate that a `dataset_ref` identifies a dataset.*

---

### R-22 (correction, non-blocking) — the reservation block's "next free number" is stale at HEAD

**Finding.** `ARCHITECTURE_DECISIONS.md:3107` states *"New ADRs therefore
number from **AD-068**."* AD-068 (`:3139`) and AD-069 (`:3274`) are both
accepted. The next free number is **AD-070**.

The block is the repository's **single place a reservation is
discoverable**, and it exists because a stale number claim previously
caused a real collision — boundary-hardening step 2 was drafted as
"AD-061" and cited under that number from six files. A stale "next free
number" inside the very block written to prevent that is worth one line
to fix.

**Ruling.** Correct in the F-0 commit, alongside F-C4 §4.3 item 4's
required replacement of the block's *"blocked for want of an independent
review that does not exist as a repository artifact"* sentence — both
sentences are in the same block and both are superseded by the same act.

---

### R-23 (documentation overclaim) — the reproduction stack is cited as "the repository's reproduction model" without disclosing that it has never produced an instance

**Finding.** I was asked to look for places where documentation overclaims
implementation. The Phase F censuses hold — I re-derived the ones that
matter and found no overclaim in them; the Acceptance Review's §5 table
is accurate, including the suite state.

The overclaim is by **implication**, and it is in R-11 and F-C1 §1.1
item 2. Both describe `core.governance.reproduction_runner` as *"the
repository's existing"* reproduction model and frame the finding as
*Phase F fails to connect to it*. A reader concludes the repository has a
working reproduction path that Phase F merely declines to join.

What is actually true at HEAD: the reproduction stack —
`reproduction_runner`, `reconstruction_loader`, `dataset_snapshots`,
`dataset_manifest`, `identity_verification`, `pinned_worktree`,
`network_guard` — is fully built and **tested against fixtures only**
(`test_reproduction_contract.py`, `test_governance_reproduction_runner.py`
use toy `experiment.py` modules and synthetic snapshots). **Zero
`dataset_manifest.json` files exist. Zero snapshots exist for any real
cycle. No real reproduction has ever been attempted.** It is a mechanism
with no production instance — exactly the same status as
`compose_transition()`, which H-6 *does* disclose.

**Ruling.** Symmetry with H-6, at no new mechanism. **AD-064's
`reproduction_runner` disconnect clause gains the census:** *the
reproduction model Phase F does not connect to has itself never been run
against a real cycle; no `dataset_manifest.json` and no dataset snapshot
exists in the repository at the commit at which this AD is accepted.*
Two facts, one sentence, and it prevents a later reader from treating
Golden Run 001's reproduction leg as a reuse when it is a first.

---

## 4. What existing ETF analytics components should be reused unchanged?

**Nothing under `core/analytics/` is modified. Not one line.** That is
both the instruction and — per R-16 — the structurally enforced outcome.

### 4.1 Analytics — the Golden Run's measurement and ranking

| Component | Reuse | Why it is safe unchanged |
|---|---|---|
| `core.analytics.domain.ranking.rank_scores` | **as-is** | Pure, deterministic, explicit stable tie-break (`-overall_score, etf_id`), no clock, no randomness, nothing persisted. Its own docstring guarantees the property Golden Run 001 needs: *two calls with the same input always produce the same output*. This **is** the reproducible ranking. |
| `core.analytics.ranked_report.generate_ranked_etf_report` | **as-is** | Already used by `experiments/validate_scoring_signal.py` to reconstruct a historical date's ranking; that script records it as *"already has no 'today'"* — i.e. no wall-clock dependence. |
| `core.analytics.persistence.repository.get_scores_for_session` | **as-is** | Lets the Golden Run **measure** an existing ranking rather than recompute one. Prefer this: fewer moving parts, and no write path into the frozen-identity tables. |
| `core.analytics.scoring_pipeline`, `indicator_calculation` | **as-is, and preferably not invoked** | They *write* `Score` / `IndicatorValue` rows. Those tables are in the **derived** set, which `identity_verification` explicitly permits to change across a run — so invoking them is legal. It is still avoidable complexity for a first milestone. |
| `core.statistics.significance` | **as-is** | Whatever scalar the gate compares. Pure. |

### 4.2 Governance and validation — reused wholly unmodified

`canonical_jsonl` (incl. `sha256_of_file`), `dataset_snapshots.write_*`,
`reconstruction_loader.{preflight_validate, reconstruct_database}`,
`identity_verification`, `network_guard.offline_guard`, `pinned_worktree`,
`reproduction_runner.run_reproduction`, `freeze_verifier`,
`decision_recorder`, `tools/archive_manifest.scaffold_project_archive`;
`GateRunner`, `ValidationRegistry`, `GateContext`, `GateRunRecord`, and
**both shipped gate adapters** — each of which I verified propagates
`context.evidence_refs` into its `GateResult`
(`economic_rationale_adapter.py:49`, `signal_independence_adapter.py:44`),
which is what makes F-C3's end-to-end pin achievable with a **real**
adapter rather than a fake.

`core.research.{lifecycle, phase_derivation, sequence_aggregation,
project_registry}` — frozen, consumed, untouched.

---

## 5. What new abstractions are truly required?

**Nine. Each has a named consumer that exists.** Anything not on this
list is speculative.

| # | Abstraction | Step | Consumer |
|---|---|---|---|
| 1 | `Experiment` Protocol, `ExperimentSpec`, `MeasurementBundle` (+ F-C2 identity fields) | F-1 | `ResearchRunner` |
| 2 | `build_gate_context()` — pure function | F-2 | `ResearchRunner` |
| 3 | `run_record_serialization` — `GateRunRecord` → canonical `dict` | F-3 | `ArchiveWriter` step 7 |
| 4 | `ArchiveWriter`, `ArchivedArtifact` | F-4 | `ResearchRunner` steps 4, 7 |
| 5 | `TransitionComposer` Protocol, `TransitionReceipt`, `ExperimentResult`, `TransitionRefusal` | F-5 | `ResearchRunner` return type |
| 6 | `ResearchRunner` | F-6 | the operator |
| 7 | `adapters/research/lifecycle_composer.py` | F-7 | `ResearchRunner`'s injected port |
| 8 | **`dataset_manifest` writer, `tools/`** *(not in any Phase F document — R-17)* | GR-1 | Golden Run 001 |
| 9 | **ETF experiment module + its `Experiment` adapter, both outside `core/`** *(R-16, R-18)* | GR-2 | Golden Run 001 |

Items 1–7 are the Proposal's, unchanged and unexpanded. Items 8 and 9 are
this review's additions, and both are small, additive, and outside
`core/`.

---

## 6. What should explicitly NOT be built yet?

§7.1's forbidden list is carried forward **unrelaxed and in full**. Named
again, because a list that is only referenced stops being read:

- **No `ExperimentOrchestrator`, `FreezeManager`, `ArchiveVerifier`,
  `DatasetIntegrityChecker`, `ReproducibilityChecker`, `LifecycleEngine`,
  phase-hook system, or event bus.** No consumer exists for any of them.
- **No authority framework of any kind** — no authority registry, no
  `core/governance/authority.py`, no classifier, no runtime policy check,
  no decorator or metadata scheme, no trigger detector. AD-067 is a
  disclosure, not a licence to build what it discloses the absence of.
- **No bridge between `ResearchRunner` and `reproduction_runner`**
  (R-11, F-C2 §2.3 item 4, restated by R-18).
- **No guard on `provenance_ref is None`**, anywhere (F-C1 §1.3 item 4).
- **No registry-agreement check** (AD-066).
- **No lock, no writer-identity field, no repair path, no retry, no
  orphan cleanup** (A-9 R-7).

Added by this review:

- **Nothing for `reference_h4`** — no records, no gate registration, no
  hypothesis, no methodology. Not on the Golden Run path at all (R-19).
- **No dataset framework** — R-17 authorizes one function that emits one
  manifest. Not a snapshot scheduler, not a refresh policy, not an
  incremental hasher, not a dataset registry.
- **No CLI command for the runner.** `adapters/cli/` exists and adding a
  `run-experiment` verb is tempting and premature: the operator inputs
  (authorization, anchor, frozen criteria, freeze commit) are exactly the
  things that must not acquire defaults, and a CLI is where defaults
  appear.
- **No `MeasurementBundle` → report renderer.** `core/reporting/` exists;
  leave it. The ranking artifact is canonical JSONL, like every other
  piece of evidence.
- **No second experiment.** Golden Run 001 is one experiment. A second
  one is how a bespoke module becomes a framework.

**One exception, and it is not a Phase F abstraction: CI (C-9).** The
Acceptance Review calls it the highest-leverage unaddressed risk in the
repository and I agree — no `.github/`, no `.pre-commit-config.yaml`, no
`Makefile`, verified. Every guarantee in this repository runs only when a
human remembers to run pytest, and Phase F multiplies the number of
guarantees. It gates on **pytest only** —
`tools/check_import_boundaries.py` exits 1 at HEAD by design, with the
five known AD-068 ETF violations correctly encoded as a strict `xfail`.
Keep it off the Phase F critical path; do it anyway.

---

## 7. The first executable milestone: **Golden Run 001**

### 7.1 Definition

> **Golden Run 001** is one complete, human-authorized, genesis phase
> transition for the cycle **`golden_run_001`**, driven by a **real ETF
> ranking experiment over real price data**, producing the repository's
> first `transition_records.jsonl`, its first `dataset_manifest.json`,
> and its first reproduction attempt — and **asserting nothing whatever
> about ETFs, markets, or any hypothesis.**

It demonstrates the mechanism. Recording it as anything more is the
defect this repository exists to prevent.

### 7.2 What it proves, mapped to the mechanism that proves it

| Proof obligation | Mechanism (all existing except where marked) | Surviving artifact |
|---|---|---|
| A real ETF research experiment executes end-to-end | `experiments/golden_run_001_ranking.py::run()`, adapted to `Experiment` at the composition root **(new, item 9)** | `ExperimentResult` |
| **Inputs are identified** | `ExperimentSpec.parameters` — scoring profile id, session date, universe — serialized into the measurement artifact per F-C2 | `experiment_results/measurements_*.jsonl` |
| **Dataset identity is captured** | `dataset_snapshots.write_*` → `dataset_hashes/`; manifest built by the new `tools/` writer **(new, item 8)**; hashes verified by the *existing* reader | `dataset_manifest.json`, `dataset_hashes/*.jsonl` |
| **Parameters are captured** | Same closed field set; `parameters` is a required member of it (F-C2) | `measurements_*.jsonl` |
| **Code version is captured** | Already delivered twice: `GateRunRecord.code_commit_hash` (`gate_run_record.py:73`) and `DecisionRecord.commit_hash`. F-C2 adds the third, on the bundle. **No new mechanism.** | `gate_run_*.jsonl`, `transition_records.jsonl` |
| **Output ranking is generated** | `rank_scores` / `generate_ranked_etf_report`, **unchanged** (§4.1); ranking written as canonical JSONL; its `sha256_of_file` is the `result_report_hash` | `experiment_results/ranking_*.jsonl` |
| **A reproduction attempt can verify the result** | `run_reproduction(...)` against the pinned commit, the manifest, and the same module — the R-18 route, **no bridge** | `ReproductionOutcome` + a hand-written `reproduction_record.json` |

### 7.3 Acceptance criteria — each falsifiable, each checked

1. `research_archive/golden_run_001/transition_records.jsonl` exists with
   **exactly one** record, and `verify_chain_intact` passes on it.
2. That record's `evidence_refs` **contains the measurement artifact ref**
   — F-C3's end-to-end propagation pin, discharged here through a **real**
   gate adapter on **real** evidence, not a fixture.
3. `TransitionReceipt.record_hash == hash_record(<the appended line>)`.
4. `parse_dataset_manifest` → `preflight_validate` → `reconstruct_database`
   all succeed against the committed manifest and snapshots.
5. Every entry in `MeasurementBundle.dataset_refs` resolves to a declared
   `snapshot_path` in that manifest (R-21).
6. `run_reproduction(...)` returns **`VERIFIED`**.
7. **The three negative controls return the right refusals** — and this
   is the criterion that makes criterion 6 mean anything. A reproduction
   that can only ever return `VERIFIED` verifies nothing:
   - a mutated snapshot row → **`DRIFTED`**;
   - a deleted snapshot file → **`UNVERIFIABLE`**;
   - a perturbed ranking expectation → **`REPRODUCTION_FAILED`**.
8. `git diff --stat` for the run's own commits touches **no file under
   `core/analytics/`** and **no file under `research_archive/reference_h4/`**.
9. The suite is green before and after, and **no existing test is
   modified** (INV-12).

### 7.4 Operating constraints, stated because they are not obvious

- **Freeze first, then run** (R-20). The methodology and criteria files
  must be committed, and the tree clean, *before* the run — otherwise
  `verify_freeze` returns `DRIFTED` and the transition is refused.
  `freeze_covered_paths` must be non-empty.
- **Scope the snapshot.** The live database holds 25 ETFs, 61 850
  `PriceBar` rows, and 2 725 `TradingSession` rows. Snapshots are
  committed JSONL. `write_price_bar_snapshot` accepts an `etf_ids`
  filter — use it, and scope the experiment's universe to match, so the
  first golden artifact is a few thousand rows rather than a few tens of
  thousands. The `ETF` snapshot is unfiltered by design (25 rows) and
  that is fine.
- **Golden Run 001 cannot be executed by a machine alone.** The
  `Authorization` is a required, undefaulted human input; the phase → gate
  registration is a governance act needing a named human and a
  `decision_log.md` entry (AD-066, as strengthened by F-C3's attestation);
  the anchor citation for any *subsequent* transition is hand-copied
  (AD-065, INV-10). The code can be written and reviewed by anyone. **The
  run is a human act.**

### 7.5 Explicit non-claims of Golden Run 001

That it is a research result. That it says anything about ETF returns,
ranking quality, or any hypothesis. That `golden_run_001`'s frozen
criteria are meaningful thresholds — they are demonstration criteria
frozen for this run only. That `reference_h4` has advanced in any way.
That a `VERIFIED` reproduction proves the measurement was *correct* — it
proves the same inputs produced the same output. That the repository now
has a reproducibility contract — per F-C1 it does not, and Golden Run 001
does not create one; it produces one instance of retained evidence
sufficient for a reproduction attempt, which is a different and smaller
thing.

---

## 8. Recommended commit sequence

Three tracks. **Track A is the only one that may start today.**

### Track A — F-0 (2 commits, docs only)

| # | Commit | Contents |
|---|---|---|
| **A1** | `phase4: accept AD-061…AD-067 (Phase F, F-0)` | Write all seven into `ARCHITECTURE_DECISIONS.md`. Discharge **F-C1 … F-C4** and **C-1 … C-5** in its own text. Add **R-16**'s `etf` scoping sentence and **R-18**'s one-implementation-two-callers ruling to AD-061/AD-064. Add **R-21**'s and **R-23**'s clauses to AD-064. Re-date every AD-063/AD-067 census to this commit. Replace the reservation block's *"blocked for want of an independent review"* sentence in leveled terms, and fix **R-22**'s stale *"number from AD-068"* → **AD-070**. |
| **A2** | `docs: fold Phase F acceptance conditions into the proposal and resolution` | Proposal §3.4's amended sentence; §8's three new non-claims; §5.2's collision bullet (C-10); Resolution's `lifecycle.py:48` → `:46` (C-4); restate F-0's exit criterion and Resolution §7 item 1 in leveled terms. |

### Track B — the Phase F engine (10 commits, fixture-only)

Unblocks the instant A1 lands. Ordering constraints that are **real**:
F-1 → F-2; F-5 → F-6 → F-7 → F-10; and **F-9 before F-7** (C-8: the
composition root must not land before the test that covers it).

| # | Step | Note |
|---|---|---|
| B1 | **F-1** measurement types | F-C2's closed field set, **pinned by test**, incl. the code-revision and provenance elements. Gate on this: F-1 must not land without it. |
| B2 | **F-2** context assembly | Evidence-ref append rule pinned; `provenance_ref=None` passes through. |
| B3 | **F-3** run-record serialization | Field-set test mirroring `test_gate_runner.py`'s; no aggregate introducible. |
| B4 | **F-4** archive writer | All five preconditions refuse, precondition 0 first; creates no directory; `canonical_jsonl` import asserted as permitted under AD-063 (b). |
| B5 | **F-5** result and port types | Exactly-one invariant; no aggregate/phase/boolean. |
| B6 | **F-6** `ResearchRunner`, fake composer | Call-order assertion; naive clock refuses at step 1. |
| B7 | **F-9** boundary AST test | **Before B8.** Scoped by name to `core/research/execution/` **and** `adapters/research/`. |
| B8 | **F-7** composition root | The sole `TransitionComposer` implementation; sole non-test caller of `compose_transition()`. |
| B9 | **F-8** failure-mode suite | Chain byte-identical asserted **on bytes**; F-C1's `provenance_ref=None` case included. |
| B10 | **F-10** fixture end-to-end traversal | Fixture cycle, temp archive root, both registries populated in fixture code only. F-C3's end-to-end pin lands here. |

### Track C — Golden Run 001 (5 commits, starts after B10)

| # | Commit | Note |
|---|---|---|
| **C1** | `tools: emit dataset_manifest.json for a cycle` | R-17. Additive, `tools/`, verified by round-trip through the **existing** reader — build → parse → preflight → reconstruct. |
| **C2** | `experiments: golden_run_001 ETF ranking experiment + composition-root adapter` | R-16, R-18. Module under `experiments/` with a `run()` entrypoint; `Experiment` adapter at the composition root. **Both outside `core/`.** Reuses `rank_scores` / `generate_ranked_etf_report` unchanged. |
| **C3** | `golden_run_001: scaffold cycle, freeze methodology and criteria` | **Human act.** `scaffold_project_archive()`; author `methodology.md`, frozen criteria, `README.md` marking it a mechanism cycle, `decision_log.md` with the named human and the AD-066 gate-registration attestation. **This is the freeze commit** (R-20). |
| **C4** | `golden_run_001: execute Golden Run 001` | **Human act**, against a clean tree at C3. Commits the dataset snapshots, `dataset_manifest.json`, both `experiment_results/` artifacts, the ranking artifact, and the first real `transition_records.jsonl`. |
| **C5** | `golden_run_001: reproduction attempt and negative controls` | `run_reproduction` → `VERIFIED`, plus the three negative controls of §7.3 item 7. Commits `reproduction_record.json` and the outcome. |

### Optional, in parallel, off the critical path

| # | Commit | Note |
|---|---|---|
| **X1** | `ci: run pytest on push` | C-9. Gates on **pytest only** — `check_import_boundaries.py` exits 1 at HEAD by design. Cheap; highest-leverage unaddressed risk in the repository. |
| **X2** | `tools: ensure evidence subdirectories for reference_h4` | C-11, Q1's additive route. **Not** on the Golden Run path (R-19) and must not be conflated with it. |

---

## 9. Claim-to-mechanism ledger for this review

| Claim this document makes | Mechanism | Where it fails if unbuilt |
|---|---|---|
| An ETF `Experiment` cannot live under `core/research/` | Read directly off `check_import_boundaries.py:107-118, 131-142, 173, 176` and AD-068 decision 2's own comment | If read off the Proposal instead, the `ETF_SYMBOLS_BY_MODULE` half — the part that defeats the granted `data` edge — would have been missed, as R-14 missed it |
| No `dataset_manifest.json` exists | `find . -name dataset_manifest.json` → empty; `dataset_manifest.py` exports a parser and no writer | A grep for the *type* would have found seven files and suggested the capability exists |
| The database cannot supply dataset identity | `.gitignore:27` `*.db`; `git check-ignore -v` confirms `experiments_etf_universe.db` | If the DB were tracked, snapshots would be optional and R-17 would be a convenience |
| Both shipped gate adapters propagate `context.evidence_refs` | `economic_rationale_adapter.py:49`, `signal_independence_adapter.py:44`, read | If either did not, F-C3's end-to-end pin would need a fake gate and would prove less |
| Golden Run 001 is achievable on real data | 25 `ETF`, 61 850 `PriceBar`, 2 725 `TradingSession`, 12 075 `Score`, 1 `ScoringProfile` in the live database | If the data were absent, the milestone would be a fixture run wearing a real name |
| The findings are sufficient | Each of R-16 … R-23 names the AD or acceptance criterion it lands in | A finding left as prose here and not folded into A1 would be discharged by memory |

**What this document does not claim:** that it is an independent review
(Level 2; Level 3 is unavailable on this platform); that it discharges
F-0 (`PHASE_F_ARCHITECTURE_ACCEPTANCE.md` does, as restated by F-C4);
that it discharges any of C-1 … C-12 or F-C1 … F-C4, all of which remain
open by their own terms; that the Phase F architecture is proven sound (a
Level 2 pass is not evidence of soundness, and I did not re-audit a
design already approved); that Golden Run 001 will succeed on first
attempt; that a `VERIFIED` reproduction constitutes a reproducibility
contract (F-C1 is precisely the statement that it does not); that any
census here holds after HEAD `67b42bd` — each is a count at that commit.
