# Research Platform MVP Migration Plan v0.1

**Role: Principal Engineer, transitioning an existing quant research
repository to MVP. Scope: migration sequencing only.** This document
does not redesign anything in `docs/PLATFORM_ARCHITECTURE_V1.md` (the
six domains, their interfaces, and their dependency rules are treated
as fixed input, not open questions), does not add a domain beyond the
six already designed, and does not propose any SaaS, multi-tenant, or
UI feature. It contains no code — every file listed below is a
*target*, not a diff. Its only job is to answer: in what order, with
what safeguards, does the current repository become the platform
`PLATFORM_ARCHITECTURE_V1.md` describes, without breaking anything H3
(or REFERENCE v1, or REFERENCE v2 H1) already produced.

**Sources.** Direct inspection of the current repository (`core/`,
`adapters/`, `experiments/`, `maintenance/`, `docs/`, `research_archive/`,
`tests/`, `pyproject.toml`, `.gitignore`) as it exists today, plus
`docs/PLATFORM_ARCHITECTURE_V1.md` (target domain design) and
`docs/RESEARCH_PLATFORM_RETROSPECTIVE.md` (gap analysis and roadmap
this plan sequences). Two specific claims below were verified against
the repository rather than assumed from those documents — see
Section 4's note on the `docs/governance/` split.

---

## 1. Current State Mapping

| Path | What it actually is today | Architecture-doc domain (if any) |
|---|---|---|
| `core/market_data/` | Providers, ingestion, persistence, domain models for prices/calendar | Data (already, per architecture §8) |
| `core/analytics/persistence/` | Repository for indicators/scores | Data (already, per architecture §4.6) |
| `core/analytics/domain/calculations.py`, `ranking.py`, `score_calculation.py`, `models.py` | ETF-scoring business logic (SMA/RSI, blend scoring, ranking) — mechanism-specific, not a general statistics library | Not yet a domain; stays product logic |
| `core/analytics/indicator_calculation.py`, `scoring_pipeline.py`, `write_pipeline.py` | Orchestration of the above | Not yet a domain; stays product logic |
| `core/analytics/ranked_report.py` | Renders a ranked ETF report | Reporting-shaped, not yet extracted |
| `core/shared/` (`clock.py`, `ids.py`, `money.py`, `pipeline_names.py`) | Cross-cutting primitives every domain will keep using | Shared kernel, no domain of its own |
| `core/domain/exceptions.py` | Shared exception types | Shared kernel |
| `adapters/cli/` | `etf` CLI entry point | Presentation layer, outside the six domains |
| `experiments/validate_reference_v1_significance.py`, `validate_reference_v2_h1_significance.py`, `validate_h3_gate1_independence.py`, `validate_h3_phase6_economic_validation.py` | Each contains its **own inlined copy** of Statistics-domain-shaped pure functions (`_spearman`, `mean_ic`, `permutation_null`, `holm_bonferroni`, `bootstrap_ci`/`block_bootstrap_ci`) | Statistics logic exists, duplicated four times, not yet a package |
| `experiments/validate_scoring_signal.py` | Descriptive top/bottom spread only, no significance testing | Predates Statistics-domain need |
| `experiments/daily_etf_universe_update.py` | Research runner: drives the write pipeline over a fixed ETF universe | Calls Data domain; not itself a domain |
| `experiments/seed_trading_calendar.py`, `backfill_price_history.py` | One-time/occasional setup utilities | Calls Data domain; not itself a domain |
| `maintenance/remediate_h3_invalid_pricebar_rows.py` | One-off H3 incident remediation; contains a reusable two-directional coverage-check routine inlined inside it | Data-adjacent logic, not yet reusable |
| `docs/RESEARCH_GOVERNANCE_STANDARD.md`, `docs/ARCHITECTURE_DECISIONS.md`, `docs/PLATFORM_ARCHITECTURE_V1.md`, `docs/RESEARCH_PLATFORM_RETROSPECTIVE.md`, `docs/BASELINE_STATUS.md` | Permanent, cycle-independent framework docs | — |
| `docs/H3_*.md`, `docs/REFERENCE_H3_*.md`, `docs/REFERENCE_V1_*.md`, `docs/REFERENCE_V2_H1_*.md` | Per-cycle, historical, frozen documents | — |
| `research_archive/reference_v1/`, `reference_v2_h1/`, `reference_h3/` | Three cycles, three different archive shapes (3 flat files / 3 flat files / 19 files with no shared scaffold), all closed | — |
| `tests/` | Flat, one `test_*.py` per module, no subpackages | Mirrors `core/market_data` + `core/analytics` only — no domain packages exist yet to test |
| `config/`, `portfolio/` | Empty placeholder packages (`__init__.py` only) | Explicitly out of scope — no new domain work here |
| Root: `experiments_etf_universe.db`, `reference_v1_significance_report.json`, `reference_v2_h1_significance_report.json` | Gitignored generated output | — |

**Governance logic today exists only as documents and manual audit
passes** (`docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md`), not as callable
code — there is no `core/governance/` equivalent at all yet, inlined
or otherwise. Same for Research-domain concepts: there is no project
registry or freeze manager anywhere; "what phase is H3 in" has only
ever lived in prose (`decision_log.md`, `README.md`).

## 2. Target State Mapping

Per `docs/PLATFORM_ARCHITECTURE_V1.md` §4 and §8, the target is **not**
a wholesale rename of `core/market_data/` or `core/analytics/` — the
architecture document itself says so explicitly. The target for MVP
v0.1 is narrower: add the domains that don't exist yet, as new
packages, and route exactly one consumer (H4) through them.

| Target path | Domain | Populated from |
|---|---|---|
| `core/market_data/` | Data | Unchanged — already correct per architecture §8 |
| `core/analytics/persistence/` | Data | Unchanged |
| `core/analytics/domain/`, `indicator_calculation.py`, `scoring_pipeline.py`, `write_pipeline.py` | Product logic (ETF scoring), outside the six domains | Unchanged |
| `core/statistics/` *(new)* | Statistics | Extracted (copied, not moved) from the four experiment scripts' duplicated helper functions |
| `core/governance/` *(new)* | Governance | New code implementing `FreezeVerifier`, `IndependenceLabelLinter`, `ArchiveVerifier`, `DecisionLogger` per architecture §4.4 |
| `core/validation/` *(new)* | Validation | New `Gate`/`GateRunner`/`ValidationRegistry` per architecture §4.2, initially wrapping the gate patterns H3 already used by hand (independence check, economic rationale, degrees-of-freedom audit) |
| `core/research/` *(new)* | Research | New `ProjectRegistry`/`FreezeManager` per architecture §4.1 — a plain, file- or SQLite-backed append log, nothing more for v0.1 |
| `core/reporting/` *(new)* | Reporting | New `ReportBuilder`/`Renderer` per architecture §4.5, applied only to gates run *after* it exists |
| `experiments/*.py` (all existing files) | — | **Unchanged in place** — see Section 6 |
| `maintenance/remediate_h3_invalid_pricebar_rows.py` | — | **Unchanged in place** |
| `maintenance/verify_price_coverage.py` *(new)* | Data-adjacent reusable tool | Extracted (copied) coverage-check logic from the remediation script |
| `docs/governance/` | — | **Deferred** — see Section 4's note |
| `research_archive/<project>/` scaffold | Governance | New: a documented manifest shape + generator, applied to H4's archive only |

## 3. Migration Steps

Ordered so that every step leaves the repository in a shippable,
fully-tested state, and every step before Step 6 touches only *new*
files.

1. **Stand up empty domain packages.** Create `core/statistics/`,
   `core/governance/`, `core/validation/`, `core/research/`,
   `core/reporting/`, each with an `__init__.py` and nothing else.
   Zero behavior change; this step alone is safe to commit and ship.
2. **Extract Statistics.** Copy (not move) `_spearman`, `mean_ic`,
   `permutation_null`, `holm_bonferroni`, `block_bootstrap_ci`, and
   related helpers out of `experiments/validate_reference_v1_significance.py`
   into `core/statistics/`, as the single canonical implementation.
   The four existing experiment scripts keep their own inlined copies
   untouched (Section 6 explains why); only code written *after* this
   step imports from `core/statistics/`.
3. **Extract the coverage check.** Copy the two-directional
   missing/surplus check out of
   `maintenance/remediate_h3_invalid_pricebar_rows.py` into a new
   `maintenance/verify_price_coverage.py`, callable standalone or from
   a test. The original remediation script is untouched.
4. **Build Governance (Tier 1 automation).** Implement
   `IndependenceLabelLinter` and `FreezeVerifier` first — they are
   pure functions over text/git state, need no schema, and directly
   automate the two cheapest items the retrospective identified. Add
   `ArchiveVerifier` once a manifest shape is chosen (Step 7).
5. **Build a minimal Research project registry.** A single
   append-only store (e.g. one JSON or SQLite file under a new,
   gitignored-equivalent `var/` or reused `experiments_etf_universe.db`-
   style local file — exact storage mechanism is an implementation
   decision, not an architecture decision) implementing
   `ProjectRegistry.register_project` / `advance_phase`. Backfill it
   with three **read-only, historical** entries for REFERENCE v1,
   REFERENCE v2 H1, and H3, all marked terminal/closed, to prove the
   registry's shape works against real history without touching any
   archive file.
6. **Define the `research_archive/` manifest + scaffold generator.**
   Pick one manifest shape (Governance Tier 2 item) and write a
   generator that creates an empty, correctly-shaped
   `research_archive/<project>/` directory for a *new* project.
   Applies to H4 only — `reference_v1/`, `reference_v2_h1/`, and
   `reference_h3/` keep their existing, different shapes permanently
   (Section 5).
7. **Build minimal Validation gates.** Implement `Gate`/`GateRunner`
   wrapping the pattern H3's own gate reviews already established
   (frozen dataset in, frozen methodology in, structured
   pass/fail/ambiguous result out), backed by `core/statistics/`
   from Step 2. First gates to implement: signal independence,
   economic rationale — the two H3 needed earliest.
8. **Build minimal Reporting.** `ReportBuilder` + a single Markdown
   `Renderer`, populated from `GateResult`/`DecisionLogEntry` shapes.
   Applied only to H4's gate results; no historical H3 report is
   regenerated or replaced by it.
9. **Run H4 through the new structure end to end.** H4's Phase 1
   through Phase 8 (per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2)
   uses `core/research/`, `core/validation/`, `core/statistics/`,
   `core/governance/`, `core/reporting/` at every phase — with zero
   new one-off script written specifically for H4. This step is the
   MVP acceptance test, not a separate milestone (Section 10).
10. **Retrospective #2, scoped to the migration itself.** After H4
    closes, write a short addendum (same spirit as
    `docs/RESEARCH_PLATFORM_RETROSPECTIVE.md`) evaluating whether the
    new domains actually removed one-off scripting, or just moved it —
    this determines what, if anything, graduates to a v0.2 scope
    (e.g. `docs/governance/` split, dataset hashing, Level 3 review).

## 4. Files to Create

All new, additive — no existing file is modified by creating these.

- `core/statistics/__init__.py`, `core/statistics/significance.py`
  (Spearman/Pearson, permutation null, block bootstrap,
  Holm-Bonferroni — signatures per architecture §4.3)
- `core/statistics/ranking.py` (`top_bottom_spread`, `rank_entities`,
  `ic_decay` — only if/when a second caller beyond the ETF-scoring
  path needs them; otherwise deferred, per the "no abstraction ahead
  of a second concrete need" discipline this repo already follows)
- `core/governance/__init__.py`, `core/governance/freeze_verifier.py`,
  `core/governance/independence_linter.py`,
  `core/governance/decision_logger.py`
- `core/governance/archive_verifier.py` (Step 6, once the manifest
  shape is fixed)
- `core/validation/__init__.py`, `core/validation/gate.py`
  (the `Gate` Protocol + `GateRunner`), `core/validation/registry.py`
  (`ValidationRegistry`)
- `core/validation/gates/signal_independence.py`,
  `core/validation/gates/economic_rationale.py` (first two concrete
  gates)
- `core/research/__init__.py`, `core/research/project_registry.py`,
  `core/research/freeze_manager.py`
- `core/reporting/__init__.py`, `core/reporting/report_builder.py`,
  `core/reporting/renderers/markdown.py`
- `maintenance/verify_price_coverage.py`
- `docs/RESEARCH_ARCHIVE_MANIFEST.md` (the chosen manifest shape,
  documented once, referenced by `ArchiveVerifier` and the scaffold
  generator)
- `docs/RESEARCH_PLATFORM_MIGRATION_RETROSPECTIVE.md` (Step 10, written
  after H4 closes — not now)
- Test files mirroring the above, flat, matching this repo's existing
  `tests/test_<module>.py` convention (no new subpackage convention
  introduced): `tests/test_statistics_significance.py`,
  `tests/test_governance_freeze_verifier.py`,
  `tests/test_governance_independence_linter.py`,
  `tests/test_validation_gate_runner.py`,
  `tests/test_research_project_registry.py`,
  `tests/test_reporting_report_builder.py`,
  `tests/test_verify_price_coverage.py`

## 5. Files to Move

**Deliberately short list.** Verified against the repository, not
assumed: `docs/RESEARCH_GOVERNANCE_STANDARD.md` and
`docs/ARCHITECTURE_DECISIONS.md` are referenced by relative path from
**10 files inside `research_archive/reference_h3/`** (decision log,
final closure, both gate determinations, the freeze record, and
others). The retrospective calls the `docs/governance/` split "pure
file move, zero risk" (§5.6/§6) — that is not true of link integrity
once H3's own frozen files are the ones doing the linking. Moving
those two files now would silently break resolvable paths inside
artifacts this plan is required to preserve unchanged.

- **Not moved in v0.1:** `docs/RESEARCH_GOVERNANCE_STANDARD.md`,
  `docs/ARCHITECTURE_DECISIONS.md`, `docs/PLATFORM_ARCHITECTURE_V1.md`,
  `docs/RESEARCH_PLATFORM_RETROSPECTIVE.md`, `docs/BASELINE_STATUS.md`
  all stay at their current `docs/` path. The `docs/governance/` split
  is deferred to a later, deliberate version — if done at all, it
  should add one-line pointer stub files at the old paths (the same
  "pointer added without editing the above" pattern
  `research_archive/reference_h3/README.md` already uses three times),
  not a bare `git mv`.
- **Nothing under `experiments/` or `maintenance/` moves** — see
  Section 6; every filename there is path-referenced by at least one
  frozen archive file across all three closed cycles.
- **Nothing under `research_archive/` moves or is reshaped** to match
  a common scaffold. The scaffold generator (Step 6) only applies
  going forward, to H4.

## 6. Files That Must Remain Untouched

Verified by direct search of `research_archive/`, not assumed:

- **All 19 files under `research_archive/reference_h3/`**, **all 3
  under `reference_v1/`**, **all 3 under `reference_v2_h1/`** — content,
  filenames, and paths. This is Objective 1, and it is also mechanically
  required: `decision_log.md`, `README.md`, `h3_final_closure.md`,
  `gate1_final_determination.md`, `gate4_final_determination.md`,
  `gate2_independent_review_2026-07-19_post_remediation.md`,
  `attempt_001_specification.md`, and both `reference_v1/README.md` /
  `reference_v2_h1/README.md` all reference specific `experiments/*.py`
  filenames by path; renaming or moving any of those scripts breaks a
  citation inside a frozen artifact.
- **All five existing `experiments/validate_*.py` scripts** —
  `validate_scoring_signal.py`, `validate_reference_v1_significance.py`,
  `validate_reference_v2_h1_significance.py`,
  `validate_h3_gate1_independence.py`,
  `validate_h3_phase6_economic_validation.py` — including their
  inlined statistics-helper duplication. These are historical
  evidence-producing code, not live infrastructure; editing them to
  import the new `core/statistics/` module would change what
  "reproduce this result" means for a closed cycle.
- **`experiments/daily_etf_universe_update.py`,
  `seed_trading_calendar.py`, `backfill_price_history.py`** — path-
  referenced the same way, and explicitly out of scope per
  `experiments/README.md`'s own stated boundary rules (never modified
  to add CLI commands, config, or scheduling).
- **`maintenance/remediate_h3_invalid_pricebar_rows.py`** — path-
  referenced by 5 files including two JSON data-inventory artifacts.
- **All `docs/H3_*.md`, `docs/REFERENCE_H3_*.md`,
  `docs/REFERENCE_V1_*.md`, `docs/REFERENCE_V2_H1_*.md` files** —
  historical, per-cycle, frozen.
- **`core/market_data/`, `core/analytics/`** internals — per
  architecture §8, these are already correctly placed; this migration
  does not touch them structurally. Only new packages are added
  beside them.
- **`config/`, `portfolio/`** — empty placeholders, explicitly not a
  domain to build in this migration (Objective: do not add new
  domains).

## 7. Test Strategy

- **New domains get new, isolated unit tests**, following this repo's
  existing flat `tests/test_<module>.py` convention (no new
  directory-per-domain convention introduced — one structural change
  at a time). `core/statistics/` functions are tested exactly the way
  `experiments/validate_reference_v1_significance.py`'s inlined
  versions already implicitly were: known inputs, known
  permutation/bootstrap outputs given a fixed seed, matching the
  determinism guarantee architecture §4.3 requires.
- **A regression check that the extraction didn't drift.** For Step 2,
  add one test that runs both the new `core/statistics/` function and
  the old inlined copy in `validate_reference_v1_significance.py`
  against the same fixed input and asserts identical output. This is
  the only test allowed to import from an `experiments/` script, and
  only to prove the copy is faithful — it is deleted once Step 2 is
  confirmed correct, not kept as permanent coupling.
- **No existing test changes.** Every current file under `tests/`
  keeps passing unmodified throughout every step above; if any step
  requires editing an existing test, that step has scope-crept beyond
  "additive" and should be split.
- **Governance and Validation tests run against synthetic fixtures**,
  never against `research_archive/reference_h3/` directly — a bug in
  `ArchiveVerifier` must never be able to mutate or "fix" a real
  archive during test runs. Point tests at a `tests/fixtures/` copy if
  a realistic archive shape is needed.
- **H4's own tests are the true integration test of this migration.**
  Whatever gates, freeze records, and reports H4 produces via
  `core/research/`, `core/validation/`, `core/governance/`,
  `core/reporting/` are the first real end-to-end exercise of the new
  packages together — Step 9 in Section 3 is deliberately also the
  test plan's capstone, not a separate activity.

## 8. Rollback Strategy

Because every step through Step 8 is purely additive (new packages,
new files, zero edits to existing files), rollback at any point before
Step 9 is trivial: delete the new package(s) or `git revert` the
commit(s) that introduced them. Nothing else in the repository
references them yet, so nothing else breaks.

- **Per-step rollback.** Each step (Section 3) should land as its own
  commit (or small commit series), so `git revert` can undo exactly
  one domain's introduction without touching another's.
- **H4-specific rollback (Step 9).** If H4 hits a wall the new
  Validation/Research/Governance code can't handle, the fallback is
  the same one every prior cycle used: hand-write an
  `experiments/validate_h4_*.py` script the way H3's were written, and
  treat the gap as a finding for Step 10's retrospective rather than a
  blocker to H4 itself. H4's own governance requirements (frozen
  methodology, gate reviews, decision log) do not depend on which
  infrastructure produces them — falling back to manual process for
  one phase does not invalidate H4's results, it only means that
  phase doesn't count toward the MVP success criterion.
- **No migration step is ever allowed to require a rollback of
  anything under `research_archive/`** — because nothing in this plan
  writes to that directory except the net-new scaffold for H4
  (Step 6), there is nothing historical to roll back.
- **Archive-verifier false positives.** If `ArchiveVerifier` (Step 6)
  is later pointed at a historical archive and reports it
  "incomplete" against the new manifest, that is expected and correct
  — `reference_h3/`'s own `decision_log.md` Entry 17 already discloses
  it doesn't match the idealized layout. This is a reporting output,
  never a trigger to modify the historical archive to satisfy the
  checker.

## 9. First 30 Days Implementation Plan

Assumes a single operator, consistent with every cycle to date.

**Days 1–5 — Steps 1–3 (Statistics extraction + coverage check).**
Stand up empty packages; extract Statistics functions with the
drift-regression test from Section 7; extract the coverage check.
Fully additive, lowest risk, immediately reusable by whichever H4 gate
needs significance testing first.

**Days 6–12 — Step 4 (Governance Tier 1).** `IndependenceLabelLinter`
and `FreezeVerifier` — the two cheapest, highest-value items per the
retrospective's own ranking. Run both against the existing `docs/` and
`research_archive/` trees in **read-only report mode** as a smoke
test (confirming, for instance, that it correctly flags H3's own
historical "independent" mislabels retrospectively, without touching
those files) before trusting either against H4.

**Days 13–16 — Step 5 (Research project registry).** Build the
registry; backfill three closed, read-only historical entries
(REFERENCE v1, REFERENCE v2 H1, H3). This is the first point where
"what phase is a project in" becomes a queryable fact instead of prose
— verify it against the three already-known-correct historical
outcomes before opening H4 in it.

**Days 17–20 — Step 6 (Archive manifest + scaffold).** Fix the
manifest shape in `docs/RESEARCH_ARCHIVE_MANIFEST.md`; build the
generator; generate (do not hand-write) H4's empty
`research_archive/h4/` directory as the first real test of the
generator.

**Days 21–25 — Step 7 (first two Validation gates) + Step 8
(Reporting).** Signal-independence and economic-rationale gates,
backed by Step 1–3's Statistics extraction; minimal
`ReportBuilder` + Markdown renderer, tested against synthetic
`GateResult` fixtures per Section 7.

**Days 26–30 — Open H4 Phase 1–3 through the new structure (start of
Step 9).** Hypothesis statement and research proposal recorded via
`core/research/`'s registry; Phase 3 pre-validation run through the
new Validation gates and Statistics package. Phases 4–8 continue past
Day 30 at whatever pace H4's own research timeline requires — the
30-day window is deliberately scoped to *infrastructure readiness*,
not to closing H4 itself, since H3 alone took a full multi-phase cycle
and forcing H4 to close inside 30 days would reintroduce exactly the
same-day compression risk the retrospective already flagged as a
weakness (§2, "same-day, single-operator compression").

**Explicitly not in the first 30 days:** the `docs/governance/` split
(deferred per Section 4), dataset-hashing infrastructure (Tier 3 in
the retrospective's own roadmap, not required for H4 to run), the
`PriceBar`/`TradingSession` structural guard (real but orthogonal to
this migration), and any second hypothesis beyond H4.

## 10. MVP Success Criterion, Operationalized

> "A second hypothesis can complete the full research lifecycle using
> platform infrastructure without creating custom one-off scripts."

Concretely, verifiable, and falsifiable: when H4 reaches Phase 8
Archive, every one of the following must be true, or the criterion is
not met and Step 10's retrospective must say so plainly rather than
round up:

1. H4's phase transitions are recorded via `core/research/`'s
   `ProjectRegistry`, not hand-edited prose.
2. Every H4 statistical test (significance, bootstrap CI,
   multiple-comparison correction) calls `core/statistics/`, with zero
   new inlined copy of `_spearman`/`permutation_null`/etc. written for
   H4 specifically.
3. Every H4 gate runs through `core/validation/`'s `GateRunner` against
   a registered `Gate`, not a bespoke `experiments/validate_h4_*.py`
   script.
4. H4's freeze is verified via `core/governance/`'s `FreezeVerifier`
   before any gate runs against it, and every phase transition is
   logged via `DecisionLogger`, not hand-authored into a
   `decision_log.md` after the fact.
5. H4's markdown report(s) are produced via `core/reporting/`'s
   `ReportBuilder` + `Renderer` from JSON evidence, not hand-written
   prose duplicating a JSON file's numbers.
6. `research_archive/h4/` matches the manifest generated in Step 6,
   verified by `ArchiveVerifier`, not by a manual audit document the
   way `H3_GOVERNANCE_COMPLIANCE_AUDIT.md` had to be for H3.

Any item above that H4 ends up satisfying only partially (e.g., one
gate still needed a one-off script because Validation didn't yet
support it) is a legitimate, disclosable finding for Step 10 — exactly
the kind of honest gap disclosure this platform has already
demonstrated for freeze provenance and reviewer independence. Rounding
a partial result up to "criterion met" would itself be the first
governance violation of the new platform's life.
