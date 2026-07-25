# v0.18.0 — Governance Platform Consolidation Release

**Tag:** `v0.18.0`, annotated, dereferencing to `9a765c1` on `master`
("AD-072 lifecycle authorization floor enforcement baseline").
**Date:** 2026-07-25.

## What this release is

v0.18.0 is a **governance platform consolidation release**, not a single
AD landing on its own. It is the tag for the point at which the platform's
research-governance machinery — built and tested across Phase 4/Step 9,
then exercised for the first time end-to-end by a real research cycle,
then hardened in direct response to what that first run exposed — reaches
a coherent, testable baseline alongside the pre-existing analytics engine
(`core/analytics/`, `adapters/cli/`, unchanged since v0.17.1). AD-072 is
the most recent, most mechanically significant piece landing in this tag,
but describing v0.18.0 as "AD-072" alone understates the release: the
governed research lifecycle, the archive, the reproduction framework, and
the first governed cycle's evidence all predate AD-072 and are all part
of what this baseline now includes.

**Test suite at this tag:** 838 passed, 1 skipped, 1 xfailed
(`python -m pytest tests/ -q`).

## Highlights

### Lifecycle authorization floor enforcement (AD-072)

- `core/research/lifecycle.py` gains `_TRANSITION_AUTHORIZATION_FLOORS`,
  a `(from_phase, to_phase) -> int` table checked inside `advance_phase()`.
  A transition whose recorded `Authorization.reviewer_level` falls below
  its floor now raises `UnauthorizedTransition` instead of proceeding.
- Before this AD, `reviewer_level` was recorded but never adjudicated —
  any string was accepted at any transition.
- This enforces only the Standard §2 **unconditional** review-level floor.
  Conditional clauses ("Level 3 where available") remain unmechanized by
  explicit design, documented in the code and in AD-072's own text — not
  an oversight, but a real, stated boundary on what "enforced" means here.
- Regression evidence: replaying `reference_h4`'s own 7 recorded
  transitions under this floor table, **5 of 7 would now be refused**
  (`tests/test_lifecycle_transition.py`, 58 tests, all passing).
- Not retroactive: this check applies to transitions occurring after
  `9a765c1`. It does not, and cannot, re-adjudicate any already-recorded
  chain.

### Research archive governance

- `research_archive/` holds per-cycle governance evidence at different
  lifecycle stages, distinct from `experiments/` (research tooling) and
  `docs/` (process narrative) — see `README.md` for the three-way
  boundary and why normal analytical commands never read the archive.
- The `reference_h4` cycle is this baseline's first, and so far only,
  complete Phase 1-8 run through the full governed lifecycle, closed with
  a recorded **PASS** in `research_archive/reference_h4/decision_record.md`.

### Freeze verification

- `FreezeVerifier.verify_freeze()` (AD-033) mechanically confirms a
  cycle's freeze commit is unchanged before dependent transitions proceed.
- Exercised for real, not just tested in isolation: `reference_h4`'s
  freeze verified at every bracket from Phase 4 onward against frozen
  commit `7b0e816`.
- Scope-bounded to the `covered_paths` binding introduced by AD-060
  (Remedy A) — paths outside that binding are not covered by construction.

### Dataset manifest / provenance work

- Raw market data remains insert-only at the database level, enforced by
  SQLite triggers (AD-009, unchanged since the analytics-engine baseline).
- Each research cycle produces a Standard-mandated `dataset_manifest.json`
  recording source, version, date range, and content hash
  (`docs/RESEARCH_GOVERNANCE_STANDARD.md`).
- This is per-cycle, self-contained disclosure — there is no platform-wide
  registry cross-referencing manifests across concurrently open cycles.

### Reproduction framework

- `core/governance/reproduction_runner.py` implements `run_reproduction()`:
  loading and executing a pinned commit's own copy of an experiment
  script against its originally frozen dataset, as a controlled,
  independently verifiable operation distinct from an ordinary manual
  re-run.
- Exercised once: `reference_h4`'s `reproduction_record.json` recorded
  `VERIFIED` at pinned commit `3d586de`.

### `reference_h4` — the first governed research cycle

- The first cycle to exercise Phase 4/Step 9's governance machinery
  end-to-end against the real repository, not a synthetic or partial run.
- Real `transition_records.jsonl` now exists (7 hash-chained records) —
  the machinery had been built and unit-tested before this, but never
  exercised by an actual cycle.
- Its own operational experience — where the Standard's process was
  followed correctly and where it wasn't — is what produced the Phase G
  remediation register (`docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md`,
  items R-1 through R-7), which in turn is what AD-072 (R-1) responds to.

## Explicitly not in this release

- **No enterprise governance.** No multi-tenancy, no multi-user roles or
  access control, no external API surface, no integrations beyond what
  already existed. This platform still operates with a single human
  operator directing all research, engineering, and review
  (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4).
- **No external, organizationally independent review.** Every governance
  document in this baseline, including AD-072's own acceptance and the
  post-release review this tag was reviewed against, is a **Level 2**
  review at best — procedurally independent of the authoring session, not
  organizationally independent. No Level 3 reviewer exists on this
  platform today.
- **No complete reproduction output verification.** The reproduction
  framework has been exercised exactly once, on one cycle
  (`reference_h4`). That one success demonstrates the mechanism *can*
  work; it is not evidence that it reliably does so across differently
  shaped cycles, and no second independent cycle exists yet to confirm
  the contract generalizes.
- **No `ArchiveVerifier`.** Named in `core/governance/__init__.py`,
  `tools/archive_manifest.py`, and `docs/PLATFORM_ARCHITECTURE_V1.md` §4.4;
  implemented in none of them. Phase 8 completeness checks are still
  performed manually.
- **No conditional review-level enforcement.** AD-072 covers unconditional
  floors only — see Highlights above.
- **No Phase H work.** A candidate scope (closing the remaining R-2
  through R-6 register items) is documented for planning visibility in
  `docs/POST_RELEASE_V0_18_0_GOVERNANCE_BASELINE_REVIEW.md` §7, but is
  explicitly not scoped as an ADR or proposal, not authorized, and not
  started.

## Known limitations carried into this baseline

Ranked by impact, full detail in
`docs/POST_RELEASE_V0_18_0_GOVERNANCE_BASELINE_REVIEW.md` §6:

- **`reference_h4`'s archive is currently unprotected** by any automated
  integrity control. Any file under `research_archive/reference_h4/` can
  be edited today with the full test suite still passing
  (D-9/R-4 — **High**, confirmed live at this tag).
- **AD-072 enforces unconditional floors only** — a future reader could
  reasonably over-read "the lifecycle enforces review levels" as covering
  Standard §2's conditional clauses too. It does not (R-1 residual —
  **High**).
- **`ArchiveVerifier` remains unimplemented** (R-3 — **Medium**).
- **The audit chain's terminal record has no structural anchoring
  solution** for future cycles; this recurs on every cycle's Archive
  transition until an ADR resolves it (R-5 — **Medium**).
- **Only one cycle has exercised the governed lifecycle end-to-end** —
  a single successful run is evidence the mechanism can work, not that
  it reliably does across varied cycles (**Medium**).
- **AD-070/AD-071 remain named-but-unclaimed**, reserved for a different
  track (`docs/PHASE_F_PRE_IMPLEMENTATION_AMENDMENT_PLAN.md` §8) — a
  bookkeeping item, not a defect (**Low**).

## Compatibility

- No migrations, no schema changes beyond what governance tables already
  required prior to this tag.
- No changes to `core/analytics/`, `core/market_data/`, or `adapters/cli/`
  — the analytics engine's read/write behavior is unchanged since v0.17.1.
- `advance_phase()`'s signature is unchanged; its behavior on an
  under-authorized transition changes from silent acceptance to
  `UnauthorizedTransition`, affecting only callers of the research
  lifecycle, not analytics-engine callers.

## See also

- `docs/POST_RELEASE_V0_18_0_GOVERNANCE_BASELINE_REVIEW.md` — the full
  Level 2 self-review this release was assessed against, including the
  external-auditability assessment and maturity-level judgement.
- `docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md` — the register
  (R-1…R-7) that produced AD-072 and that the remaining gaps above are
  tracked against.
- `docs/ARCHITECTURE_DECISIONS.md` (AD-072 entry) — the accepted ADR text.
- `docs/BASELINE_STATUS.md` — the project-wide baseline this release
  folds into, including the pre-existing analytics-engine history.
