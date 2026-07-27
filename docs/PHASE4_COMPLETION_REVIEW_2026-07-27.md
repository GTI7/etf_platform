# Phase 4 Completion Review

**Status.** Milestone completion summary. **This document is not an ADR.**
It records what Phase 4 achieved, citing the architecture decisions and
commits that already establish those facts. It introduces no new decision,
no new AD number, and no new obligation; where it summarizes an AD, that
AD's own text governs in case of any discrepancy.

**Date.** 2026-07-27. **Author basis.** Level 1 — one reader with
repository access, compiled from `docs/ARCHITECTURE_DECISIONS.md`
(AD-061 through AD-077), the release commits below, and a full local test
run. This is not an independent review and must never be cited as one
(`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4, the same standing every Level
1/Level 2 entry in this repository's decision register already discloses).

---

## 1. Executive Summary

Phase 4 exists because the platform's research work — dataset assembly,
scoring methodology, cycle-by-cycle decisions — had accumulated faster than
the governance apparatus around it. `docs/RESEARCH_PLATFORM_RETROSPECTIVE.md`
Section 2 (cited in AD-069 and elsewhere in the register) documents that
"what phase is a project in" was, before this work, only prose scattered
across each cycle's `decision_log.md` and `README.md` — not a queryable
fact. Phase 4's problem, stated at the level the AD register states it, was
to convert research infrastructure that had been built experimentally
(direct, ad hoc scripts against a growing pile of research cycles) into
research infrastructure that is **governed**: every phase transition
recorded, every archived dataset provenance-checked, every archived cycle's
bytes verifiable against a fixed reference, and the boundary between the
platform's reusable engine and its first workload (ETF scoring) made
explicit rather than assumed.

The transition Phase 4 records is from **experimental research code** —
where a script could compute a result and a human could act on it with no
mechanical record of what was measured, what was decided, or by what
authority — toward **governed research infrastructure**, where a decision
chain (`transition_records.jsonl`), a dataset provenance manifest
(`dataset_manifest.json`), an archive integrity verifier, and a lifecycle
authorization floor together make a research cycle's history
machine-checkable, without claiming that checkability equals correctness or
that governance equals research validity. Phase 4 closes with the platform
having run one real governed cycle end-to-end (`reference_h4`, whose
Decision-phase gates passed — a governance-process outcome, not a claim
about the underlying signal's predictive validity — 2026-07-25) and having
recorded, in the same register, the gaps that cycle exposed.

## 2. Starting Problem

The following risks are drawn from what the cited ADs state as their own
context or motivation — not from a general narrative:

- **Reproducibility gaps.** Before AD-073/AD-074, `docs/PLATFORM_ARCHITECTURE_V1.md`
  §4.4 sketched an `ArchiveVerifier` with a one-line protocol and no
  implementation; `core/governance/reconstruction_loader.py` and
  `reproduction_runner.py` existed, but nothing tied a reproduction attempt
  to a verified, tamper-evident archive of the bytes it reproduced against.
- **Dataset provenance uncertainty.** `dataset_manifest.py`'s schema (hash
  and row-count per source table) existed, but — per AD-073's own
  Correction basis (finding F-1) — AD-073's own original draft text
  overlooked that this existing `content_hash` mechanism already covered
  archived bytes, naming only one pre-existing hash mechanism
  (`protected_file_hashes.json`) where a second already existed. The
  relationship between dataset provenance and archive-level integrity
  verification was corrected the same day (AD-073's Correction basis), not
  established from a clean starting point.
- **Archive integrity limitations.** Prior to AD-074, the only tamper
  check covering research archives was `tests/fixtures/protected_file_hashes.json`,
  a Phase-0 snapshot fixture covering three named legacy archives
  (`reference_v1`, `reference_v2_h1`, `reference_h3`) and a small fixed set
  of other files. It covered nothing produced after Phase 0, and — per
  `docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md` D-9/G-5, cited in
  AD-075 — its Phase-0 exclusion for `reference_h4` had already expired
  before a replacement control existed, leaving that archive unprotected
  for a real, disclosed interval.
- **Lifecycle enforcement gaps.** AD-072's own Context states the
  pre-existing design directly: `Authorization.reviewer_level` was
  "recorded, never adjudicated" — `advance_phase()` accepted
  `"Level 1 (self-review)"` at any transition without objection, because no
  mechanism held the governance standard's phase → minimum-review-level
  table. AD-072 names this the direct structural cause of four disclosed
  defects (D-1 through D-4) in the `reference_h4` cycle's own review
  record.
- **Workload coupling.** Before AD-068, the import boundary checker mapped
  `core.analytics` (ETF-specific scoring and ranking) to the generic `data`
  domain, and ETF-specific types living inside `core.market_data` were
  indistinguishable from asset-class-neutral ones beside them — so every
  platform domain could reach ETF concepts through an edge the architecture
  document already permitted, and the coupling was invisible to the only
  mechanism that could have reported it.

No claim above is extended beyond what its cited AD states. In particular:
none of these ADs claim the underlying research findings were wrong, or
that any research decision was invalid — the findings are about governance
*apparatus*, not about research *conclusions*.

## 3. Completed Capabilities

### Research Governance

- **Lifecycle phases.** `core/research/lifecycle.py` holds transition
  legality (`IllegalPhaseTransition`, `UnauthorizedTransition`) and is, per
  AD-063 enumeration (a), the one non-test module in `core/` permitted to
  name `core.governance.decision_recorder` symbols.
- **Decision records.** `DecisionRecord` and the hash-chained
  `transition_records.jsonl` (`core/governance/decision_recorder.py`) are
  the platform's append-only record of phase transitions. The first real
  instance of this chain — not a fixture — was produced by the
  `reference_h4` cycle (memory: `project_reference_h4_first_governed_cycle`;
  verified in this review: `research_archive/reference_h4/transition_records.jsonl`
  exists and holds 7 records at repository HEAD).
- **Authorization controls.** AD-072 (accepted 2026-07-25) defines a
  mechanical lifecycle authorization floor — a fixed minimum
  `reviewer_level` per transition-authorization event (Level 2 for most
  transitions, Level 1 for Implementation → Validation), evaluated against
  the value already recorded on a `DecisionRecord`, refusing a transition
  whose floor is unmet. AD-072 discloses, against its own worked example,
  that the `reference_h4` cycle's own five self-review transitions would
  **not** have satisfied this floor had it existed at the time — a
  disclosed gap the AD deliberately preserves rather than retroactively
  resolves.

### Reproducibility

- **Dataset manifests.** `core/governance/dataset_manifest.py`
  (`MANIFEST_SCHEMA_VERSION = 3`) defines the per-source-table hash and
  row-count contract every frozen dataset snapshot is checked against.
- **Integrity checks.** `core/governance/dataset_integrity.py` verifies a
  `DatasetEntry` against its snapshot file; `core/governance/reconstruction_loader.py`
  runs the full pre-flight validation sequence (canonical JSONL shape,
  duplicate keys, unresolvable references, calendar coverage) before any
  database is opened.
- **Reproduction contracts.** `core/governance/reproduction_runner.py`
  runs one full reproduction attempt against a pinned worktree, reporting a
  governed status (`VERIFIED`, `UNVERIFIABLE`, `DRIFTED`,
  `REPRODUCTION_FAILED`) rather than an uncaught exception — a distinction
  AD-069 records as having been corrected during Phase 4 (commit `91634c8`,
  cited in AD-069) after being identified as a crash-not-status defect.
- **Pinned execution identity.** `core/governance/pinned_worktree.py`
  provides the pinned-commit worktree reproduction runs against;
  `core/governance/identity_verification.py` snapshots identity state for
  comparison. As of the Engine Boundary cleanup (`fe29fd7`), the workload
  facts a reconstruction needs (`parse_row`, `load_rows`) are supplied by
  the caller as required parameters with no default, rather than imported
  from an ETF-specific module inside Governance.

### Archive Integrity

- **Archive sealing.** AD-073 (accepted 2026-07-25) establishes the
  architecture: the Archive Seal is a *witnessed commit reference* (the
  Archive Seal Register, `docs/archive_seal_register.jsonl`) plus *tree
  comparison against it*. AD-074 (accepted 2026-07-26, after
  implementation at commits `2392de2`/`a8f031b`) specifies the mechanism in
  full: blob-identity comparison (`git rev-parse <commit>:<path>` against
  `git hash-object`), a full-length hexadecimal `sealed_commit` validated
  and ancestry-checked against `HEAD`, and neutralization of the git
  attribute stack as a comparison input.
- **Verification.** `core/governance/archive_verifier.py` composes three
  branches — Standard §5 completeness, the Archive Seal, and
  `FreezeVerifier` — which AD-073 states "composes Governance components
  only" (AD-073's AD-059 compatibility note); each branch answers a
  different question and none substitutes for another (AD-073's Decision
  parts, amended by AD-074's four-item correction inline in that AD's own
  text).
- **Immutable evidence handling.** Two disjoint controls with two
  different roots of trust cover different path sets: `tests/fixtures/protected_file_hashes.json`
  (a Phase-0, immutable SHA-256 snapshot covering the three legacy
  archives and a small fixed set of other files) and the Archive Seal
  (covering `research_archive/reference_h4/**`, minus that archive's own
  `dataset_manifest.json` `snapshot_path` set). AD-075 (accepted
  2026-07-26) states the invariant positively and by test: no key of the
  Phase-0 fixture may name a path under a Seal-covered prefix — an overlap
  would not be redundancy, it would be a hole, because a fixture key is an
  *exclusion* to the Seal's comparison. AD-075 also issued the first
  Archive Seal Register record, for `reference_h4`, sealed at commit
  `29553b7e5d96118b3f38ecc4de27362a07a210d1` (verified in this review:
  `docs/archive_seal_register.jsonl` exists and holds 1 record at
  repository HEAD). AD-075 records, and does not close, a second gap
  (R-4b): the two `experiments/` scripts pinned by `reference_h4`'s
  reproduction record are outside the Seal's `research_archive/` scope.

### Engine Neutrality

- **AD-077** (accepted 2026-07-27, commit `6b92ade`) states two separate
  neutrality claims rather than one unqualified one: (1a) the governance
  spine (`archive_identity`, `archive_seal`, `archive_verifier`,
  `canonical_jsonl`, `dataset_integrity`, `decision_recorder`,
  `freeze_verifier`, and others) is workload-neutral **in semantics** — no
  workload schema name reaches behaviour in those modules, a claim
  established by review, not by test; (1b) the dataset and reproduction
  path (`dataset_manifest`, `identity_verification`, `reconstruction_loader`,
  `reproduction_runner`, `calendar_definitions`) is **workload-bound** —
  it encodes ETF's table names, column names, foreign-key topology, and
  calendar, and a second workload cannot produce a governed archive without
  changing them. AD-077 is explicit that an unqualified "workload-neutral
  platform" claim is false while 1b holds.
- **Workload separation.** AD-077 introduces a second, orthogonal
  classification axis — Engine / Reference Workload / Artifact — over the
  same module tree, distinct from AD-068's domain map. `core/analytics` is
  classified Reference Workload; `research_artifacts/`, `research_archive/`,
  and `experiments/*.py` are classified Artifact. `core/market_data` is
  explicitly **not classified** by AD-077 (deferred, per
  `docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md` §9.1, until a second
  workload exists).
- **Removal of ETF-specific assumptions from engine infrastructure.** The
  Engine Boundary Cleanup implementation (commit `fe29fd7`) discharges the
  concrete items AD-077 records: the shared-kernel identifier `ETFId` was
  renamed to `InstrumentId` (`core/shared/ids.py`), with the two unused
  `PortfolioId`/`HoldingId` aliases and `UniverseId`/`ArtifactRef`
  withdrawn as unused since Phase 0; `core/governance/reconstruction_loader.py`
  and `reproduction_runner.py` no longer import ETF-specific row parsers
  and loaders — those are now caller-supplied parameters
  (`parse_row`, `load_rows`) with no default; the ETF-registration modules
  `historical_backfill.py` and `reference_h4_registration.py` moved from
  `core/research/` to the top-level `research_artifacts/` package; and a
  duplicated constant (`LEGACY_ARCHIVE_PROJECT_IDS`, `ARCHIVE_MANIFEST_FILENAME`)
  that had drifted into three separate module-local copies was
  consolidated into one new module, `core/governance/archive_identity.py`.
  AD-077 states explicitly that this work authorizes no further Phase 1,
  Phase 2, or Phase 3 item beyond what it names, and that CI's advisory
  (`|| true`) invocation of the boundary checker is disclosed, not
  repaired, by this decision.

## 4. Verification Evidence

**Final repository state (verified 2026-07-27, post-push):**

```
$ git status
On branch master
Your branch is up to date with 'origin/master'.
nothing to commit, working tree clean

$ git branch -vv
* master fe29fd7 [origin/master] refactor: enforce engine boundary cleanup
```

Local `master` and `origin/master` point at the identical commit; the
working tree carries no uncommitted or untracked changes.

**Release commits:**

| Commit | Message | Files changed |
|---|---|---|
| `6b92ade122d46e35bbff68b206478242c4de0bf8` | `docs: append AD-077 engine neutrality decision` | 1 file, `docs/ARCHITECTURE_DECISIONS.md`, 396 insertions(+), 0 deletions — pure append |
| `fe29fd7fe8ec9b650d48471a6cca1558009468b7` | `refactor: enforce engine boundary cleanup` | 44 files, 3157 insertions(+), 558 deletions(-) |

**Separation between governance and implementation.** The two commits are
disjoint by construction and were verified disjoint before each was made:
`6b92ade` touches only `docs/ARCHITECTURE_DECISIONS.md`; `fe29fd7` touches
code, tests, tooling, and cleanup-tracking documentation, and does **not**
touch `docs/ARCHITECTURE_DECISIONS.md`. `git show --stat` on each commit
(re-run for this review) confirms the same file sets. `docs/ARCHITECTURE_DECISIONS.md`
was not modified, and no existing AD entry was edited, superseded, or
renumbered, by the work this review documents.

**Test results.** Full local suite, run against `fe29fd7` before it was
pushed:

```
996 passed, 3 skipped, 1 xfailed in 200.68s (0:03:20)
```

This matches the task's stated known-final-verification figures exactly
(996 passed, 3 skipped, 1 xfailed). The one `xfail` is the pre-existing,
`strict=True`-marked `test_real_repository_has_no_boundary_violations`
(AD-068 Decision 4), which inventories the two known, deferred
`data -> etf` violations in `core/market_data` rather than hiding them; a
`strict` marker converts an unexpected pass into a failure, so this is a
recorded, deliberate posture, not an oversight. A targeted re-run of tests
specific to the Engine Boundary Cleanup (import boundaries, domain package
imports, reconstruction loader, reproduction runner/contract,
`reference_h4` registration, research project registry, and the four new
snapshot/frozen-dataset test files) passed 122, with 1 skip and 1 xfail,
consistent with the full-suite figures above.

## 5. Explicit Non-Goals / Remaining Boundaries

Phase 4 does not claim, and this review does not claim on its behalf:

- **No Level 3 independent review.** Every AD cited in this document —
  AD-061 through AD-077 without exception — states its own review basis as
  Level 1 or Level 2 (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4) and states
  explicitly that Level 3 is unavailable on this platform and has never
  been performed. No AD in this range may be cited as an independent
  architecture review, and this document does not cite any of them as one.
- **No production trading system.** Nothing in the cited ADs, and nothing
  in the release commits this review documents, adds order execution,
  capital allocation, brokerage integration, or any live-trading capability.
  Phase 4's scope is governance and reproducibility infrastructure around
  research, not a trading system.
- **No guarantee of alpha.** Governance and reproducibility infrastructure
  verify *process* — that a stated dataset was used, that a phase
  transition was recorded and authorized at the required floor, that
  archived bytes match a witnessed commit. None of that verifies that any
  research conclusion is correct or that any scoring signal has predictive
  value. `docs/BASELINE_STATUS.md` separately and explicitly records that
  the platform's own scoring-signal research remains an open empirical
  question, not resolved by this or any prior phase.
- **No removal of all future workload-specific extensions.** AD-077
  states plainly that the dataset and reproduction path (1b) remains
  workload-bound, that `core/market_data`'s classification under AD-077's
  Engine/Reference-Workload/Artifact axis is deferred rather than decided,
  and that AD-077 authorizes no further phase of the cleanup it proposes.
  A second workload is not supported today without changing
  `dataset_manifest`, `identity_verification`, `reconstruction_loader`,
  `reproduction_runner`, and `calendar_definitions`.
- **Other disclosed, still-open items**, carried forward rather than
  resolved by this review: the boundary checker's CI invocation remains
  advisory (`|| true`) rather than blocking (AD-077 §3); the Archive Seal's
  coverage does not extend to the `experiments/` scripts pinned by
  `reference_h4`'s reproduction record (AD-075's R-4b); and the mechanical
  authorization floor AD-072 defines is accepted but was not yet in force
  during the one governed cycle completed to date, a fact AD-072 discloses
  about itself rather than concealing.

## 6. Phase 5 Transition

The following are possible directions consistent with where Phase 4 leaves
the platform. None is committed to here; each would require its own
proposal and, where it changes governed behavior, its own AD:

- **Research expansion.** With one governed cycle (`reference_h4`)
  complete and its gaps recorded, a natural next step is running additional
  research cycles under the now-accepted AD-072 authorization floor, to
  test the floor against real review workflows rather than only against
  the worked example in AD-072's own text.
- **Productization.** AD-077's two-part neutrality claim (1a governance
  spine neutral in semantics, 1b dataset/reproduction path workload-bound)
  frames what productization would require: extending Engine Neutrality
  from semantics to a second real workload would mean parameterizing the
  1b modules the way `reconstruction_loader`/`reproduction_runner` were
  parameterized for row parsing in the Engine Boundary Cleanup — work
  AD-077 explicitly does not authorize on its own.
  `core/market_data`'s deferred classification would need resolving at
  that point, not before.
- **Incubator preparation.** The archive-sealing and lifecycle-authorization
  machinery built in Phase 4 (AD-072 through AD-075) is the kind of
  evidentiary trail an external reviewer or incubator process would look
  for; whether and how to present it externally is a separate,
  unaddressed question.
- **Further validation.** The disclosed gaps this review carries forward
  in Section 5 — CI enforcement strength, `experiments/` script coverage
  under the Seal, and untested interaction between the authorization floor
  and a live review workflow — are candidates for the next round of
  governance hardening, in the same incremental, AD-by-AD style Phase 4
  itself used (AD-072 → AD-073 → AD-074 → AD-075 → AD-077).

No implementation plan, timeline, or commitment is made by naming these
directions.
