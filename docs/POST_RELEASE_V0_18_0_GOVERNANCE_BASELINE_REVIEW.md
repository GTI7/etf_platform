# Post-Release Architecture & Governance Baseline Review — v0.18.0

**Type:** Self-review, decision-only. No source code, dataset, ADR, or
archived artifact is modified, created, or superseded by this document.
**Date:** 2026-07-25
**Reviewer:** Single human operator (Standard §4) plus AI assistance,
Level 2 procedural self-review — see §9.

---

## 1. Review scope

**Commit/tag reviewed.** `v0.18.0`, an annotated tag dereferencing to
commit `9a765c1e7f799aa886d68d1f9a7c2b03c8ea1401` on `master`, message
*"AD-072 lifecycle authorization floor enforcement baseline"*, dated
2026-07-25 11:05:57 +0200.

**Repository state.** `master` is up to date with `origin/master` at the
reviewed commit; the working tree is clean (no staged, unstaged, or
untracked changes). `9a765c1` is a merge of PR #1
(`platform/ad-072-lifecycle-floor-enforcement`), preceded on that branch
by `aee915f` (implementation) and `dc773c3` (ADR acceptance).

**Test result.** `python -m pytest tests/ -q` → **838 passed, 1 skipped,
1 xfailed**, at the reviewed commit. This number supersedes the 802-pass
figure recorded in `docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md`
§2, which was measured one commit range earlier; the growth is the 58
tests added for AD-072 (`tests/test_lifecycle_transition.py`) plus
incidental additions on the same branch.

**Reviewer limitations.** This is a **Level 2** review — procedurally
independent of the sessions that authored AD-072 and its implementation,
**not organizationally independent** (Standard §4: this platform has a
single human operator directing all research, engineering, and review).
No Level 3 reviewer exists or is available on this platform. Findings
below are grounded in commands run against the reviewed commit and are
reproducible by anyone with repository access; the judgements built on
top of those findings are this reviewer's own and are explicitly flagged
as such throughout (§9).

---

## 2. Verified baseline facts

Every row below is a command or file citation run against the reviewed
commit, not a recollection.

| Fact | Value | Evidence |
|---|---|---|
| HEAD commit | `9a765c1e7f799aa886d68d1f9a7c2b03c8ea1401` | `git rev-parse HEAD` |
| `v0.18.0` tag | Annotated, dereferences to `9a765c1` (same as HEAD) | `git rev-list -n1 v0.18.0`; `git cat-file -t v0.18.0` → `tag` |
| Test results | 838 passed, 1 skipped, 1 xfailed | `python -m pytest tests/ -q` |
| AD register state | 66 accepted ADs (`AD-001`…`AD-051`, `AD-056`…`AD-069`, `AD-072`); `AD-052`…`AD-055` retired and not available; `AD-070`/`AD-071` named as Track C candidates but not consumed | `grep -oE "^### AD-[0-9]+" docs/ARCHITECTURE_DECISIONS.md \| sort -u \| wc -l`; `docs/ARCHITECTURE_DECISIONS.md`:2849, :3098, :4242 |
| Lifecycle enforcement verification | `core/research/lifecycle.py` implements `_TRANSITION_AUTHORIZATION_FLOORS`, a `(from_phase, to_phase) -> int` table checked inside `advance_phase()`; violation raises `UnauthorizedTransition` | `core/research/lifecycle.py`:137–214; `git show --stat aee915f` (113 lines added to `lifecycle.py`, 223-line new test file) |
| `reference_h4` verification results (regression) | Under AD-072's floor table, replaying `reference_h4`'s 7 recorded transitions at their actual `"Level 1 (self-review)"` value: **5 of 7 would be refused** (seq 2, 3, 4, 6, 7); seq 5 (Implementation → Validation) would pass, since Phase 5's floor is Level 1; seq 1 (Hypothesis → Research Proposal) has no floor entry | `tests/test_lifecycle_transition.py`:411–450, `test_reference_h4_recorded_transitions_would_be_refused_under_ad072` (parametrized ×5, passing) and `test_reference_h4_seq5_would_pass_under_ad072` (passing) |
| `tests/test_lifecycle_transition.py` | 58 passed | `python -m pytest tests/test_lifecycle_transition.py -q` |

---

## 3. Governance capability assessment

"Evidence" cites the concrete mechanism verified in §2 or by direct
inspection at the reviewed commit. "Remaining gap" is this reviewer's
judgement, not a measured fact, and is marked accordingly where it
restates an open item from
`docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md` §10 (the `R-` IDs).

| Capability | Status | Evidence | Remaining gap |
|---|---|---|---|
| Architecture decisions | **Recorded, versioned, cross-referenced** | 66 accepted ADs in `docs/ARCHITECTURE_DECISIONS.md`, each dated and citing predecessors; retirements (`AD-052`…`055`) and reservations (`AD-070`/`071`) are explicit, not silent gaps | None mechanical. The register's internal consistency (an AD not silently contradicting an earlier one) is checked by author review at acceptance time, not by tooling. |
| Lifecycle authority | **Partially mechanized as of AD-072** | `_TRANSITION_AUTHORIZATION_FLOORS` enforces an *unconditional* per-transition minimum `reviewer_level`; `Authorization.reviewer_level` docstring updated from "recorded, never adjudicated" to "adjudicated, narrowly" (`core/research/lifecycle.py`:92–103) | Conditional Standard §2 clauses ("Level 3 where available") remain unmechanized by explicit design (AD-072's own text, cited at `lifecycle.py`:141–143) — a deliberate scope boundary, not an oversight, but still a real gap between "floor enforced" and "Standard §2 fully enforced." |
| Transition enforcement | **Enforced for phase order and reviewer-level floor** | `advance_phase()` raises `IllegalPhaseTransition` for out-of-order transitions and `UnauthorizedTransition` for a floor violation or an unacknowledged AMBIGUOUS/FAIL sequence status (`lifecycle.py`:69–80) | No enforcement of §8 exception records (open gap, `R-2` in the Phase G register — ADR not yet drafted at this commit). |
| Freeze controls | **Mechanically verified, scope-bounded** | `FreezeVerifier.verify_freeze()` (AD-033); `reference_h4`'s freeze was `verified` at every bracket seq 4–7 against unchanged commit `7b0e816` (cited in the Phase G decision, not re-verified independently in this review) | `covered_paths` binding is Remedy-A-scoped (AD-060); paths outside that scope are not covered by construction, per that AD's own text. |
| Dataset provenance | **Structurally enforced at ingestion, not registry-tracked platform-wide** | Raw market data is insert-only, enforced by SQLite triggers (AD-009); `dataset_manifest.json` is a Standard-mandated per-cycle artifact (`docs/RESEARCH_GOVERNANCE_STANDARD.md`:424) | No platform-wide dataset registry cross-references manifests across cycles; each cycle's manifest is self-contained and not verified against a central index. |
| Dataset integrity | **Insert-only + idempotent writes, not archive-protected post-close** | AD-009 (raw data), AD-022 (`IndicatorValue` insert-only, idempotent) | `reference_h4`'s own archive is unprotected by the automated repository-integrity check post-Archive (D-9/`R-4` in the Phase G register, **not yet closed** at this commit — confirmed live: `tests/test_repository_integrity_snapshot.py`:100–106 still excludes `research_archive/reference_h4/`, and `tests/fixtures/protected_file_hashes.json` holds zero `reference_h4` entries). |
| Reproduction contracts | **Implemented and exercised once** | `research_archive/reference_h4/reproduction_record.json`, `run_reproduction()` returned `VERIFIED` at pinned commit `3d586de` (cited in the Phase G decision) | Exercised on exactly one cycle; no second independent cycle exists yet to confirm the contract generalizes. |
| Research gates | **Framework implemented; only fully exercised where a frozen criterion exists** | `GateRunner`/`GateResult`/`GateStatus` (AD-040, AD-049); `reference_h4` froze exactly one decision rule and ran exactly one real gate against it (Phase G decision §6, N-2) | Gate framework is unexercised for a multi-gate cycle; no cycle to date has tested more than one frozen criterion end-to-end. |
| Archive verification | **Not implemented** | `ArchiveVerifier` is named in `core/governance/__init__.py`, `tools/archive_manifest.py`, and `docs/PLATFORM_ARCHITECTURE_V1.md` §4.4, but `grep -rn "class ArchiveVerifier" core/ tools/` returns no implementation (re-confirmed at this commit) | Open (`R-3` in the Phase G register, not yet closed at this commit). Phase 8 completeness checks are performed manually, as the Phase G decision itself did. |
| Audit trail | **Hash-chained per cycle, externally anchored only up to the penultimate record** | `DecisionRecorder.append()`, `verify_chain_intact()`, `verify_chain_anchored()` (AD-048, AD-065); `reference_h4`'s chain head (seq 7) was unanchored until the Phase G decision published its hash out-of-band | Anchoring the terminal record is structurally unsolved for the *next* cycle (`R-5` in the Phase G register, not yet closed at this commit) — AD-072 does not touch this gap. |

---

## 4. External auditability assessment

Answering each question as it stands **today**, for a hypothetical
external reviewer with repository access but no conversation history:

- **What decision was made?** Yes, for closed cycles — `decision_record.md`
  per cycle (e.g. `research_archive/reference_h4/decision_record.md`
  records PASS) and `docs/ARCHITECTURE_DECISIONS.md` per architecture
  decision, each with an explicit "accepted" marker and date.
- **Why?** Yes, for cycles and ADs that follow the established citation
  discipline — every AD reviewed for this document cites the finding,
  clause, or prior AD it responds to (e.g. AD-072 cites Phase G's `R-1`
  and the Standard §2 table verbatim). Quality varies with how recently
  the artifact was written; older ADs (pre-`AD-040`) are shorter and cite
  less.
- **Which code?** Yes, at commit granularity — `git show --stat` on any
  cited commit; AD-072's ADR text names the exact file
  (`core/research/lifecycle.py`) implementation would land in, and it did.
- **Which data?** Partially. Per-cycle `dataset_manifest.json` names
  source, version, date range, and content hash (Standard convention).
  There is no platform-wide index of which datasets are in use across
  concurrently open cycles.
- **Which parameters?** Yes, for a frozen cycle — the Standard requires
  every frozen element enumerated in `methodology.md`, and
  `FreezeVerifier` mechanically checks the freeze commit is unchanged.
- **Which gates?** Yes, where a gate was actually run — `GateResult`
  records the criterion, the measured statistic, and the outcome. Where
  no gate exists for a transition (most of `reference_h4`'s, per §3
  above), the record correctly shows an empty `gate_outcomes` array
  rather than a fabricated pass.
- **Which results?** Yes — reproduction records, validation output, and
  decision records are archived per cycle and (for `reference_h4`)
  cross-checked bit-for-bit in an independent Level 2 pass (Phase G
  decision §6, N-1).

**Net assessment.** An external reviewer with time to read the cited
chain of documents can reconstruct the *what* and *why* for every closed
artifact reviewed here. What they cannot yet do is verify *mechanically,
platform-wide* that every phase transition on this repository's history
met its required review level — that check exists now only for
transitions occurring **after** `9a765c1` (AD-072 is not retroactive to
already-recorded chains) and only for the unconditional-floor subset of
Standard §2.

---

## 5. Maturity assessment

**Current maturity: Level 3 — Reproducible research system.**

**Already achieved:**
- A single research cycle (`reference_h4`) has been run end-to-end
  through the full Phase 1–8 lifecycle, hash-chained, and independently
  bit-for-bit re-derived (Phase G decision §6, N-1).
- Phase-transition legality (ordering, single-step advancement) and, as
  of AD-072, an unconditional reviewer-level floor are both mechanically
  enforced, not merely documented.
- A structured, three-category (disclosure / defect / non-finding)
  process exists for converting a real cycle's operational experience
  into platform-level remediation (the Phase G decision itself, and its
  `R-1`…`R-7` register).

**What blocks Level 4 (self-verifying governance system, in this
reviewer's working definition — not a term defined in
`docs/RESEARCH_GOVERNANCE_STANDARD.md`, which does not itself number
maturity levels):**
- `ArchiveVerifier` does not exist (§3, "Archive verification").
- Closed cycles have no automated re-protection path (§3, "Dataset
  integrity"; `R-4`, live gap as of this commit).
- The audit chain's terminal record has no structural anchoring solution
  (§3, "Audit trail"; `R-5`).
- Only one cycle has ever exercised the full machinery; a single
  successful run is evidence the mechanism *can* work, not that it
  reliably *does* across varied cycles.

**Outside current scope**, by this platform's own stated non-goals
(§8 below) and by the Phase G decision's explicit boundary (§1 of that
document: "Phase G" is a platform-engineering phase, not a research
lifecycle extension) — none of this maturity gap concerns the *research
findings* to date, which remain a separate, already-closed line of work
(`docs/RESEARCH_LINEAGE_REGISTER.md`).

---

## 6. Remaining risks

Ranked by this reviewer's judgement of impact if unaddressed, not
mechanically derived.

**Critical** — none identified. No finding in this review, or in the
Phase G decision it builds on, impugns a closed decision, a freeze, a
chain's integrity, or a reproduction result.

**High**
1. **`reference_h4`'s archive is currently unprotected by any automated
   integrity control** (D-9/`R-4`, confirmed live at this commit — see
   §3). Any file under `research_archive/reference_h4/` can be edited
   today with the full test suite still passing. This is a live gap, not
   a historical one.
2. **AD-072 enforces only unconditional floors.** A future contributor
   could read "the lifecycle enforces review levels" too broadly and
   assume Standard §2's conditional clauses ("Level 3 where available")
   are also mechanically checked. They are not, by explicit design
   (`lifecycle.py`:141–143), and nothing currently flags that
   distinction outside this document, the ADR text, and code comments.

**Medium**
3. **`ArchiveVerifier` is named in three places and implemented in
   none** (`R-3`, open). Phase 8 completeness checks depend on manual
   review until this lands.
4. **The audit chain's terminal record remains structurally
   unanchorable** under the current artifact ordering (`R-5`, open); this
   will recur, unchanged, on every future cycle's Archive transition
   until an ADR resolves it.
5. **Only one cycle has exercised the governed lifecycle end-to-end.**
   AD-072's regression test (§2) proves the floor logic is *correct*
   against `reference_h4`'s recorded values; it does not prove the
   floor is *sufficient* against a cycle shaped differently (e.g. one
   with more than one frozen decision rule, exercising the gate
   framework more heavily than `reference_h4` did).

**Low**
6. **AD-070/AD-071 remain named-but-unclaimed.** Not a defect, but a
   bookkeeping item: a future contributor unfamiliar with
   `docs/PHASE_F_PRE_IMPLEMENTATION_AMENDMENT_PLAN.md` §8 could
   plausibly claim either number without knowing Track C has first
   claim.

---

## 7. Recommended next phase — Phase H: Enforcement Closure

**This section documents objectives only. Nothing in this section is
implemented, scheduled, or authorized by this document.**

Candidate scope, drawn directly from the open items already surfaced in
§3 and §6 (all pre-existing register entries from
`docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md` §10 — Phase H would
not originate new findings, only close ones already on the books):

- Close `R-3`: implement `ArchiveVerifier`, or record its deferral as a
  time-boxed §8 exception — the Phase G decision already rules out
  leaving it named-but-absent as a permanent third option.
- Close `R-4`: an automated re-protection mechanism for a closed cycle's
  archive (candidate already proposed: a second, append-only
  closed-cycle hash fixture, structurally distinct from the Phase-0
  snapshot), and retire the now-expired `reference_h4` exclusion clause
  in `tests/test_repository_integrity_snapshot.py`.
- Close `R-5`: an ADR resolving how a chain's terminal record gets
  anchored without depending on a file committed before that record
  exists.
- Close `R-2`: give the Standard §8 exception record a schema and an
  enforcement point (this is also the vehicle for resolving the §5/§2
  Phase 8 append-vs-edit ambiguity on `decision_log.md`, per `G-7`).
- Close `R-6`: wire `IndependenceLabelLinter` into the test suite over
  `research_archive/` and `docs/`, addressing its documented
  false-positive rate on statistical usage first.

Phase H is **not yet scoped as an ADR or a proposal**; the above is a
restatement of existing open register items for planning visibility, not
a new commitment.

---

## 8. Explicit non-goals

The following are out of scope for this review and are not implied by
anything above:

- **No Phase F expansion.** `docs/PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md`
  and `docs/PHASE_F_ACCEPTANCE_CONDITIONS.md` stand as accepted; this
  review does not reopen, extend, or qualify them.
- **No UI work.** Nothing in this platform's current scope contemplates
  a user interface; this review does not propose one.
- **No permission system.** This platform operates with a single human
  operator (Standard §4). This review does not propose multi-user roles,
  access control, or a permission model.
- **No speculative enterprise features.** No multi-tenancy, no external
  API surface, no integrations beyond what already exists. Every item in
  §7 closes a gap already identified by a prior governance decision; none
  introduces new capability surface.

---

## 9. Reviewer limitation

**This is a self-review.**

The mechanical findings in this document — commit hashes, test counts,
`grep` results, the AD-register count, the regression test outcomes —
are reproducible by any party with repository access and are stated with
their exact evidence so they can be checked without trusting this
document's prose.

The architectural judgements in this document — the maturity-level
assignment (§5), the risk ranking (§6), and the Phase H scope proposal
(§7) — are this reviewer's own assessment and **require independent
review** before being treated as authoritative. Per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4, no Level 3 (organizationally
independent) reviewer exists on this platform today. Where this document
uses institutional vocabulary ("assessment," "recommended"), that
vocabulary describes a role this platform's single operator is
discharging, not a distinct organizational body.

This document does not claim independent review at any point, and no
statement in it should be read as such if that qualification is
separated from the text.
