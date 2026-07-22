# Phase 4 / Step 9 — A-6 Ruling Record (research cycle identity model)

**Date filed:** 2026-07-22
**Repository state ruled against:** canonical `D:\Claude\etf_platform`, `master`, HEAD `aca36fb`, working tree clean.

---

## 1. Status

**Status: ruling record.** It disposes of the three questions prerequisite
A-6 puts, and of nothing else. It is **not** an ADR, **not** an amendment
to any ADR draft, **not** a registration, **not** a gate determination,
and **not** a Phase B artifact.

**Prerequisite addressed:**
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
§4.1 row A-6 — *"Research cycle identity model decided — lineage / cycle /
attempt named; H4 naming reconciled with the existing three; the
`positive_control_phase3` registry/archive divergence ruled on"*, whose
"Done when" column reads **"Recorded in AD-050"**.

**A-6 is decided by this record. A-6 is not closed by this record, and
this record does not claim otherwise.** The distinction is stated first
because it is the one a later reader is most likely to get wrong:

- A-6's "Done when" condition is *recorded in AD-050*. AD-050 does not
  exist in [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) —
  verified at `aca36fb`, the accepted set runs AD-001 … AD-046 plus
  AD-051, and AD-047 … AD-050 exist only as drafts in
  [`PHASE_4_STEP9_DRAFT_ADRS.md`](PHASE_4_STEP9_DRAFT_ADRS.md).
  Writing them in is **A-2**, a separate prerequisite.
- This record therefore supplies the **decided content** A-6 requires and
  fixes it in writing at a date, so that A-2's transcription has
  something settled to transcribe rather than a draft to re-litigate.
  **A-6 closes when AD-050 is written and accepted under A-2 carrying
  the decisions in §4 below.** Until then A-6 stays open, and Step 9
  stays blocked on it exactly as it stood at `aca36fb`.

**No file is edited by this record, and no code is introduced by it.**
This is a new, dated file.
[`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md),
[`PHASE_4_STEP9_DRAFT_ADRS.md`](PHASE_4_STEP9_DRAFT_ADRS.md),
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md),
[`RESEARCH_LINEAGE_REGISTER.md`](RESEARCH_LINEAGE_REGISTER.md),
[`RESEARCH_ARCHIVE_MANIFEST.md`](RESEARCH_ARCHIVE_MANIFEST.md) and
[`RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md) are
all retained unedited, and each is cited below by section or line rather
than amended.

**Supersession discipline.** Same convention, and same disclosed
limitation on its scope, as
[`PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md`](PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md)
(`aca36fb`): Standard §5's "a correction is a new, dated file,
cross-referenced from the file it supersedes" is stated for evidence
packages under `research_archive/<cycle_name>/` and is applied here **by
extension, not by direct scope**, together with the stated `docs/` rule —
`ARCHITECTURE_DECISIONS.md`'s preamble, *"where a later phase revised an
earlier decision, the entry says so explicitly rather than silently
superseding it."*

**Review level: Level 1 — self-review**, per
[`RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md) §4.
Authored and reviewed within the same effort that produced the material
it rules on. Standard §4's Level 1 limitations apply in full and are
adopted, not softened; the word "independent" is not used of this record.
Level 3 is unavailable on this platform (Standard §4: *"no Level 3 review
has ever been performed on this platform"*). This is not a lifecycle
Decision in the Standard §2/§7 sense — no research conclusion, no gate
determination, no step toward capital allocation is made here.

**Verification basis.** Every factual claim in §3 was checked directly
against the canonical repository at `aca36fb` — file contents, `git log`,
and the working tree — and each carries its source. No claim rests on an
off-repo artifact; where a prior record's off-repo evidence would have
been relevant, it is not relied on.

---

## 2. Scope

**In scope — exactly three questions, no more:**

1. The correct project/cycle identifier for H4, under the existing
   historical convention (`reference_v1`, `reference_v2_h1`,
   `reference_h3`).
2. The status of `research_archive/positive_control_phase3` across
   `research_archive/`, `RESEARCH_LINEAGE_REGISTER.md`, and
   `ProjectRegistry`.
3. Reconciliation of AD-050's identity vocabulary against
   `RESEARCH_LINEAGE_REGISTER.md`'s.

**Out of scope, and not decided here:** every other Phase A prerequisite
(A-1 — ruled on at `aca36fb`, discharged only on acceptance of that
ruling, on its own terms; A-2, A-3, A-4, A-5, A-7,
A-8, A-9 — untouched and open on their own terms); H4's hypothesis
content, Phase 1 artifact, or Phase 2 selection; the `freeze_verifier`
baseline fix (Resolution §2.5); and everything in Resolution §4.2's
Phases B–E.

**Phase A discipline is binding on this record.** Resolution §4.1 scopes
Phase A to "documents only, zero code". Nothing here modifies code,
registers a project, opens a lineage entry, writes an ADR, or creates a
Phase B artifact. See §8.

---

## 3. Facts established

Each row was verified directly at `aca36fb`.

| # | Fact | Source |
|---|---|---|
| F-1 | Exactly three projects are registered, via one non-idempotent path: `reference_v1`, `reference_v2_h1`, `reference_h3` | `core/research/historical_backfill.py:43,59,76`; `backfill_historical_projects()` at `:101-107` |
| F-2 | That module's docstring scopes itself to *"the three existing, closed research cycles … the complete set; no fourth candidate exists in `research_archive/`"* | `core/research/historical_backfill.py:3-6` |
| F-3 | F-2 was **true when written and is stale now**. The module landed `6240844` (2026-07-19); `research_archive/positive_control_phase3/` landed `c0be233` (2026-07-20), one day later | `git log -1 --format=%h\ %ad` on each path |
| F-4 | `research_archive/` holds **four** cycle directories; three are registered | `research_archive/` listing vs. F-1 |
| F-5 | `positive_control_phase3` carries `archive_manifest.json` with `lifecycle_version: "v1"`, `project_id: "positive_control_phase3"`, `created_at: 2026-07-20T09:36:27.790943+00:00` | `research_archive/positive_control_phase3/archive_manifest.json` |
| F-6 | `lifecycle_version: "legacy"` is defined as describing archives predating the manifest concept, named exhaustively as `reference_v1`, `reference_v2_h1`, `reference_h3`. `"v1"` is therefore, by that document's own definition, **not** a legacy/historical archive | `RESEARCH_ARCHIVE_MANIFEST.md`, `lifecycle_version` values |
| F-7 | The cycle is **open, not frozen and not archived**: *"Not a Methodology Freeze — no `methodology.md` exists"*; gates 2 and 3 FAIL; the governing proposal reads NOT READY FOR FREEZE | `research_archive/positive_control_phase3/README.md`; `POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md` §16 |
| F-8 | `RESEARCH_LINEAGE_REGISTER.md` names `positive_control_phase3` as the `cycle_name` of both recorded attempts under lineage `gate2_score_acf_target_fn`, whose `lineage_status` is `active` | `RESEARCH_LINEAGE_REGISTER.md:102,112,120` |
| F-9 | The Register's canonical identity fields are `lineage_id`, `attempt_number`, `cycle_name` (plus `governing_cap`, `status_log`, `outcome`, `counted_against_cap`, `certifications`) | `RESEARCH_LINEAGE_REGISTER.md`, "Schema" |
| F-10 | `lineage_id` is defined as identifying *"the mechanism being corrected, not the cycle or document that first defined it"* — a mechanism/target-function space under a Phase 3 attempt cap, e.g. `gate2_score_acf_target_fn` | `RESEARCH_LINEAGE_REGISTER.md`, "Schema", `lineage_id` |
| F-11 | The term `cycle_name` originates **above** the Register: Standard §5 fixes the evidence package at `research_archive/<cycle_name>/` | `RESEARCH_GOVERNANCE_STANDARD.md:416,420` |
| F-12 | `ProjectId` is format-gated to `^[a-z][a-z0-9_]*$`, stated to match every existing `research_archive/` directory name *"with no exceptions carved out for any of them"* | `core/research/project_id.py:22,26-33` |
| F-13 | `Project.research_outcome` is `str \| None`, documented as `None` for a project with no concluded outcome yet (e.g. still `ACTIVE`) — an open cycle is representable by the existing dataclass | `core/research/project.py:29-30,67` |
| F-14 | `reference_h3` ran numbered construction attempts local to its own plan — *"attempt 1 of the maximum three permitted under `REFERENCE_H3_PREVALIDATION_PLAN.md` §2"* — and **no** `lineage_id` exists for H3 in the Register | `research_archive/reference_h3/attempt_001_specification.md:1-7`; `RESEARCH_LINEAGE_REGISTER.md` (one entry only) |
| F-15 | The roadmap assigns the label **H4** to a specific hypothesis: *"H4 — Volume / flow acceleration"*, ranked 5 of 7, data reliability unverified | `REFERENCE_RESEARCH_ROADMAP_NEXT.md:167` |
| F-16 | H4 was **rejected at H3's selection review**, on data-reliability grounds | `REFERENCE_H3_PREVALIDATION_PLAN.md:76` |
| F-17 | `RESEARCH_ARCHIVE_MANIFEST.md`'s schema example carries `"project_id": "h4"` — a bare H-number, matching none of the three existing directory names | `RESEARCH_ARCHIVE_MANIFEST.md`, "Schema (`schema_version: 1`)" |
| F-18 | AD-047 … AD-050 are **not** in `ARCHITECTURE_DECISIONS.md`. The accepted set runs to AD-046, plus AD-051. AD-050 exists as a draft only | `docs/ARCHITECTURE_DECISIONS.md:1170,1288`; `PHASE_4_STEP9_DRAFT_ADRS.md:329` |
| F-19 | The AD-050 draft asserts that `reference_v1` and `reference_v2_h1` are *"two `Project`s that are successive **cycles of one research lineage**"* | `PHASE_4_STEP9_DRAFT_ADRS.md:336-339` |
| F-20 | No `lineage_id` exists in the Register for the `reference_v1` → `reference_v2_h1` succession, or for any cycle other than `positive_control_phase3` | `RESEARCH_LINEAGE_REGISTER.md:98-137` |

**Naming convention, as it actually reads across the three registered
projects** (F-1), stated as an observation before it is ruled on in §4.1:

| Directory / `ProjectId` | `Project.name` | Segments |
|---|---|---|
| `reference_v1` | REFERENCE v1 | `reference` + scoring-profile version |
| `reference_v2_h1` | REFERENCE v2 H1 (Low Volatility) | `reference` + profile version + **hypothesis number** |
| `reference_h3` | REFERENCE H3 (Relative Strength / Segment Rotation) | `reference` + **hypothesis number**, profile segment dropped |

Two properties of that sequence are load-bearing below and are recorded
as facts rather than inferences:

- **The H-number tracks the hypothesis, not the ordinal.**
  `reference_v2_h1` was the **second** cycle and carries `h1`;
  `reference_h3` was the **third** and carries `h3`. The number is the
  roadmap's hypothesis label in both cases, and coincides with the
  ordinal only by accident in the second.
- **The profile segment was dropped, and did not return.** The most
  recent cycle (`reference_h3`, 2026-07-19) uses `reference_<hN>` with no
  version segment.

---

## 4. Decision

Three rulings, R-1 … R-3. Each is stated in the form it is to be
transcribed into AD-050 under A-2.

### 4.1 R-1 — H4 identity: `reference_h4`

**Ruled: the identifier is `reference_h4`.**

- **Form.** `reference_<hypothesis-label>`, lowercase, satisfying
  `^[a-z][a-z0-9_]*$` (F-12), following the most recent precedent
  `reference_h3` and dropping the profile-version segment, which was
  already dropped and did not return.
- **One string, four places.** The same literal `reference_h4` is used as
  the `research_archive/` directory name, as `cycle_name` (Standard §5,
  F-11), as the `ProjectId` string, and as `archive_manifest.json`'s
  `project_id` field. These are **byte-identical**, never four
  independently-chosen names.
- **Bare `h4` is rejected.** It matches none of the three existing
  directory names and would be the sole exception to a format rule whose
  own docstring records that no exception exists for any project (F-12).
  The `"project_id": "h4"` in `RESEARCH_ARCHIVE_MANIFEST.md`'s schema
  example (F-17) is an **illustrative field value inside a schema
  example, not a naming decision**, and is not treated as one. That
  document is not edited by this record; the divergence is disclosed here
  and carried to §9.

**Limitation, stated as part of the ruling and not as a caveat to it: R-1
fixes the string, not the hypothesis.** The H-number tracks the
hypothesis label (§3), and roadmap H4 is a *specific* hypothesis —
volume / flow acceleration (F-15) — which was **rejected** at H3's
selection review on data-reliability grounds (F-16) and has never had a
Phase 1 artifact or a Phase 2 approval of its own. Therefore:

1. **Registering `reference_h4` asserts nothing about hypothesis
   content**, data adequacy, or Phase 2 selection. It is an identity
   string.
2. **`reference_h4` is not a generic label for "the fourth cycle."** If
   the next cycle's Phase 2 selects a candidate other than roadmap H4,
   that cycle takes `reference_h<n>` for *its own* hypothesis label under
   R-1's form rule, and `reference_h4` is not reused for it. The
   identifier follows the hypothesis; it never follows the ordinal.
3. This record **does not authorize the registration itself** (§8).
   Registration is Phase B work (Resolution §4.2, B-3).

### 4.2 R-2 — `positive_control_phase3`: a recorded `cycle_name`, and a deferred migration target

The three options A-6 puts are not mutually exclusive across three
different registers, and the honest answer names the register each
holds in. Ruled, one line per register:

| Register | Status of `positive_control_phase3` |
|---|---|
| `research_archive/` | **An open cycle's live evidence package — not a historical archive directory.** Its manifest declares `lifecycle_version: "v1"`, and that document defines "legacy" as exactly the three predating directories (F-5, F-6). Its own README states it is not a Methodology Freeze, and the cycle has not reached Phase 4, let alone Phase 8 (F-7). |
| `RESEARCH_LINEAGE_REGISTER.md` | **A recorded `cycle_name`.** It is named as the `cycle_name` of both recorded attempts under the `active` lineage `gate2_score_acf_target_fn` (F-8). It is recorded *as a `cycle_name`*; it is **not** a `lineage_id` and must never be cited as one (see R-3). |
| `ProjectRegistry` | **Unregistered, and a future migration target — explicitly deferred.** No `Project` record exists (F-1). |

**Ruled on the divergence itself: the divergence is real, is not a defect
of either the archive or the registry, and is not closed by this record.**

- What is actually absent is an **invariant binding the two**. No such
  invariant exists, nothing detects the divergence, and **this record
  creates none.** Creating one is a mechanism, and mechanisms are Phase B.
- `ProjectRegistry`'s contents are hereby stated to mean *the set of
  projects that have been registered* — and **not** a claim about the
  contents of `research_archive/`. A reader must not infer archive
  completeness from the registry, or registry completeness from the
  archive, at `aca36fb`.
- **`historical_backfill.py`'s "no fourth candidate exists" is stale, and
  is disclosed rather than fixed** (F-2, F-3). It was true on 2026-07-19
  and was overtaken on 2026-07-20. Correcting it is a code edit,
  forbidden in Phase A, and belongs to the increment that adds a
  registration path for a non-historical cycle (§9).

**Why registration is deferred rather than performed** — three grounds,
in order of decisiveness:

1. **Phase A forbids it.** Resolution §4.1 scopes Phase A to documents
   only, zero code. Registration is code.
2. **No registration path for an open cycle exists.**
   `backfill_historical_projects()` is the only path, is deliberately
   non-idempotent, and is scoped by its own docstring to closed
   historical cycles (F-2). Registering a fourth, *open* cycle needs a
   new path — new code, with its own review.
3. **It is not blocked on representability, and this record says so
   rather than borrowing a better-sounding reason.** `Project` can
   already represent an open cycle: `lifecycle_state=ACTIVE` with
   `research_outcome=None` is documented behaviour (F-13), and
   `origin_date` would not have to be invented — `archive_manifest.json`'s
   `created_at` (F-5) is an already-recorded evidence date of exactly the
   kind `project.py:32-41` requires. The deferral rests on grounds 1 and
   2, which are sufficient, and not on a claimed impossibility that does
   not exist.

**Consequence for Step 9's premise.** Resolution §1.3 warns that
*"Registering H4 without addressing this adds a fifth directory to an
already-unreconciled set"*, and the AD-050 draft states that it *"rules
on that divergence before H4 adds a fifth directory."* That remains true
after this record. What
changes is that the unreconciled state is now **ruled and dated** rather
than merely observed: the archive holds four cycles, the registry holds
three, the fourth is a live cycle whose registration is deferred on
stated grounds, and Step 9 may proceed on that basis without either
silently reconciling the two or treating the divergence as an unknown.

### 4.3 R-3 — Vocabulary: `lineage_id` / `cycle_name` / `attempt_number` are canonical

**Ruled: the canonical research identity vocabulary is the three fields
already defined in `RESEARCH_LINEAGE_REGISTER.md`'s Schema —
`lineage_id`, `cycle_name`, `attempt_number` (F-9). AD-050 adopts these
names and definitions verbatim and defines no others.**

`cycle_name` is canonical with the strongest anchor of the three: it
originates in Standard §5 (F-11), which outranks the Register and
predates it.

**AD-050 terminology maps as follows, and the mapping is exact:**

| AD-050 draft term | Canonical field | Definition that governs |
|---|---|---|
| "lineage" | `lineage_id` | The Register's: a **mechanism / target-function space** under a Phase 3 attempt cap, *"chosen to identify the mechanism being corrected, not the cycle or document that first defined it"* (F-10) |
| "cycle" | `cycle_name` | Standard §5's: the research cycle whose evidence package is `research_archive/<cycle_name>/` (F-11) |
| "attempt" | `attempt_number` | The Register's: an ordered attempt within a `lineage_id`, carrying `counted_against_cap` (F-9) |

**Three precisions, each of which resolves a live ambiguity rather than
restating the mapping:**

1. **The Register's narrower `lineage_id` governs; AD-050's wider use of
   "lineage" is not canonical and receives no term.** The AD-050 draft
   states that `reference_v1` and `reference_v2_h1` are "successive
   cycles of one research lineage" (F-19). Under the Register's
   definition (F-10) that is **not** a `lineage_id` claim: no
   `lineage_id` exists for that succession (F-20), and none may be opened
   for it retroactively — the Register is append-only and is written to
   only when a Phase 3 attempt cap opens, so back-filling one now would
   record a retroactive fact of exactly the class `project.py:32-41`
   already refuses for `origin_date`. **Ruled:** when AD-050 is written
   under A-2, the succession is expressed as two `cycle_name`s related by
   the narrative already in the closeout documents — never as a shared
   `lineage_id`, and never with a second, wider sense of the word
   "lineage" defined alongside the Register's.
2. **`ProjectId` / `project_id` is a type and a key, not a fourth
   identity concept.** `ProjectId` is the registry's typed key
   (`core/shared/ids.py`, AD-031/AD-003) and `project_id` is
   `archive_manifest.json`'s field name. **Ruled:** where a cycle is
   registered, both carry a string **byte-identical to its `cycle_name`**.
   Neither introduces an identity distinct from `cycle_name`; they are
   the same identity in a typed and a serialized position respectively.
3. **Attempt numbering outside a registered lineage is cycle-local and
   caps nothing across cycles.** `reference_h3`'s "Construction Attempt 1
   of a maximum three" (F-14) is numbered under that cycle's own
   prevalidation plan, and H3 has no `lineage_id`. **Ruled:** only
   attempts recorded under a `lineage_id`, with `counted_against_cap`,
   consume a cross-cycle cap. A cycle-local attempt log is a real
   governance artifact but is not a Register entry, and must not be cited
   as though a lineage cap governed it.

**No second identity vocabulary is created — stated explicitly, as A-6
requires.** AD-050 introduces **no** new identity field, type, enum,
dataclass, registry, or synonym for `lineage_id`, `cycle_name`, or
`attempt_number`. `Project` is unmodified. `ProjectRegistry`'s three
methods are unmodified. `LifecyclePhase` (Resolution D-13) is **phase**
vocabulary transcribed from Standard §2 and is orthogonal to identity —
it names *where a cycle is*, never *which cycle it is* — and this ruling
neither extends nor constrains it beyond that boundary.

**Where phase attaches.** Resolution D-15 — *phase belongs to the cycle*
— is affirmed unchanged and is now expressible in canonical terms: phase
attaches to a `cycle_name`, not to a `lineage_id` (which spans cycles
that were in different phases) and not to an `attempt_number` (which does
not advance the governance process on its own).

---

## 5. Rationale

**R-1.** Three independent facts converge on `reference_h4`, and none of
them alone would be sufficient:

- **The convention's own trajectory.** The profile-version segment was
  dropped at `reference_h3` and did not return (§3). Reintroducing it
  (`reference_v3_h4`) would revive a discarded segment and assert a
  scoring-profile version that does not exist.
- **The H-number is a hypothesis label, not a counter** (§3). Any scheme
  based on ordinal position (`reference_4`, `reference_cycle_4`) would
  contradict `reference_v2_h1`, where the second cycle carries `h1`.
- **Every governing document already calls this cycle "H4"** — Migration
  Plan Step 9, `PLATFORM_ARCHITECTURE_V1.md`, `RESEARCH_ARCHIVE_MANIFEST.md`,
  and Resolution §4.2's Phase B/E exit criteria. Choosing a stem other
  than `reference_h4` would create a second name for a cycle the
  repository already refers to by one — the precise failure R-3 exists to
  prevent.

The limitation attached to R-1 is stated because the alternative is
worse: an identifier silently implying that a rejected candidate (F-16)
has been re-selected would be a claim stronger than its mechanism, which
Resolution §5 names as the failure mode the whole reconciliation exists
to stop.

**R-2.** The question "archive directory, registered cycle, or migration
target?" presupposes one register. There are three, and they genuinely
disagree — that disagreement *is* the divergence A-6 asks to be ruled on.
Answering with a single label would have required suppressing two of the
three true answers. The manifest's `lifecycle_version` (F-5/F-6) is
decisive against "historical archive directory" because it is the
platform's own, already-committed, machine-readable statement that this
directory is not legacy; the README and the open gate status (F-7)
confirm it against a second, independent source. The Register entry (F-8)
is decisive for "recorded `cycle_name`" in the only register that has
ever recorded this cycle. And ProjectRegistry's silence is a fact about
ProjectRegistry, not about the cycle.

Deferral over registration follows from Phase A's own boundary. The third
ground is included because omitting it would leave a reader to assume
registration is blocked by something structural, when it is blocked by
process and by the absence of a code path — a weaker but true reason,
and stating the true one is the point.

**R-3.** Two vocabularies for one set of concepts is a governance defect
of the same shape as two writable representations of one fact, which
Resolution §2.1 already rejects for `Project.current_phase`. The Register
was committed first, defines its fields precisely, and inherits
`cycle_name` from the Standard itself; AD-050 is an unwritten draft
(F-18). A draft yields to a committed register, not the reverse.

The one place where AD-050's draft and the Register genuinely conflict —
the width of the word "lineage" (F-19 vs F-10) — is resolved in the
Register's favour rather than by widening `lineage_id` to cover both
senses, because widening it would break the field's stated purpose: a
`lineage_id` exists to prevent an attempt cap being reset by renaming a
cycle. A `lineage_id` that also meant "a family of related cycles" would
make it ambiguous whether a cap travels with it, and the cap is the whole
reason the field exists.

---

## 6. Consequences for AD-050

AD-050 is a **draft** (F-18). This record does not edit it. When it is
written into `ARCHITECTURE_DECISIONS.md` under A-2, it carries the
following, and A-6 closes at that point:

| # | Required of AD-050 | Source |
|---|---|---|
| C-1 | Adopt `lineage_id`, `cycle_name`, `attempt_number` as the canonical identity vocabulary, with the Register's and Standard §5's definitions, and define no others | R-3 |
| C-2 | State that no second identity vocabulary is created — no new field, type, enum, registry, or synonym | R-3 |
| C-3 | State that phase attaches to the **`cycle_name`**, restating D-15 in canonical terms | R-3, D-15 |
| C-4 | Record `reference_h4` as H4's identifier, byte-identical across archive directory, `cycle_name`, `ProjectId`, and manifest `project_id` | R-1 |
| C-5 | Record that the identifier fixes the string and not the hypothesis, that roadmap H4 was rejected at H3's selection review, and that the H-number follows the hypothesis and never the ordinal | R-1 |
| C-6 | Record `positive_control_phase3` as an open cycle recorded as a `cycle_name` in `RESEARCH_LINEAGE_REGISTER.md`, unregistered in `ProjectRegistry`, deferred on the grounds in §4.2 — not a historical archive directory | R-2 |
| C-7 | Record that no archive↔registry invariant is created by Step 9, and that `ProjectRegistry` makes no claim about `research_archive/`'s contents | R-2 |
| C-8 | Disclose `historical_backfill.py`'s stale "no fourth candidate exists" docstring, without editing it | R-2, F-2/F-3 |

**Three points on which AD-050's draft text must change when transcribed,
recorded here so the change is deliberate rather than silent:**

1. The draft's "successive cycles of one research lineage" (F-19) is
   **not** to be written as a `lineage_id` claim (R-3 precision 1).
2. The draft's "**H4 must be registered** before Step 9 §10 item 1 can be
   met" stands as a statement of Step 9's dependency, but the identifier
   it must be registered under is now fixed as `reference_h4` (R-1), and
   the registration itself remains Phase B work not authorized here.
3. The draft's statement that the AD "rules on that divergence" is
   satisfied by C-6/C-7 — a ruling that the divergence is disclosed,
   bounded, and unmechanized, **not** that it is eliminated.

**What is unchanged in AD-050 by this record:** parts 2, 3 and 4 of the
draft — `LifecyclePhase` in `core/shared/`, phase derived from the
transition chain with `Project` unmodified and no INV-12 exception, and
no automatic transition at any gate status — are untouched. So are
Resolution D-12 … D-16 as written, except that D-15 gains the canonical
expression in C-3.

---

## 7. Effect

| Item | Status after this record |
|---|---|
| **A-6, question 1 — H4 identity** | **Decided:** `reference_h4`. §4.1 |
| **A-6, question 2 — `positive_control_phase3` divergence** | **Decided:** open cycle; recorded as a `cycle_name` in `RESEARCH_LINEAGE_REGISTER.md`; unregistered in `ProjectRegistry` and a deferred migration target; **not** a historical archive directory. §4.2 |
| **A-6, question 3 — vocabulary** | **Decided:** `lineage_id` / `cycle_name` / `attempt_number` canonical; AD-050's terms map 1:1; no second vocabulary. §4.3 |
| **A-6 as a prerequisite** | **Decided in writing, not yet closed.** Closes when AD-050 is written and accepted under A-2 carrying C-1 … C-8. §1 |
| **A-2** | **Open, unchanged.** This record adds required content to AD-050; it does not write or accept it |
| **A-1** | **Ruled on at `aca36fb`; discharged if that ruling is accepted.** Limb 1 closed at `8bd8f8a`; limb 2 closes on acceptance. Not re-decided, not reopened |
| **A-3, A-4, A-5, A-7, A-8, A-9** | **Open, unchanged.** Not spoken to |
| **Step 9** | **Blocked, unchanged.** Resolution §4.1's rule — "Step 9 does not start until every item below is closed in writing" — is unchanged and unrelaxed |
| **Archive ↔ registry divergence** | **Open, disclosed, unmechanized.** Ruled and dated; no invariant created |
| **`historical_backfill.py` stale docstring** | **Open, disclosed, unfixed.** Correction deferred to the increment that adds a non-historical registration path |
| **`RESEARCH_ARCHIVE_MANIFEST.md` `"project_id": "h4"` example** | **Open, disclosed, unedited.** Superseded in effect by R-1; the document is not amended |

**How to re-run this ruling.** Every input is named so a later reader need
not trust this document: the convention (§3) against
`core/research/historical_backfill.py` and the `research_archive/`
listing; the format gate against `core/research/project_id.py:22`; the
divergence against `research_archive/positive_control_phase3/archive_manifest.json`,
that directory's `README.md`, and `RESEARCH_LINEAGE_REGISTER.md:102-130`;
the staleness against `git log -1 -- core/research/historical_backfill.py`
and `git log -1 -- research_archive/positive_control_phase3`; the
vocabulary against `RESEARCH_LINEAGE_REGISTER.md`'s Schema and
`RESEARCH_GOVERNANCE_STANDARD.md:416`; the H4 hypothesis label against
`REFERENCE_RESEARCH_ROADMAP_NEXT.md:167` and
`REFERENCE_H3_PREVALIDATION_PLAN.md:76`; and the AD ceiling against
`docs/ARCHITECTURE_DECISIONS.md`.

---

## 8. Explicit non-actions

Stated as prohibitions honoured by this record, each verifiable against
the diff:

- **No code is modified or created.** `core/research/project.py`,
  `project_id.py`, `project_registry.py`, `historical_backfill.py`,
  `core/shared/`, `core/governance/`, `core/validation/`, `tools/`, and
  every test file are untouched.
- **No ADR draft is modified.** `PHASE_4_STEP9_DRAFT_ADRS.md` is retained
  unedited; §6 states what AD-050 must carry, and changes nothing in the
  draft itself.
- **`ARCHITECTURE_DECISIONS.md` is not modified.** No AD is added,
  amended, renumbered, accepted, or marked superseded. AD-050 remains
  unwritten; AD-045 carries no supersession marker (Resolution §2.4
  unchanged).
- **Nothing is registered in `ProjectRegistry`.** No `Project` record is
  constructed for `reference_h4` or `positive_control_phase3`. No
  registration path is added.
- **Nothing is written to `RESEARCH_LINEAGE_REGISTER.md`.** No
  `lineage_id` is opened, retired, or certified; no attempt, status_log
  entry, or certification is appended. The append-only discipline is
  observed by not appending.
- **No `research_archive/` directory is created**, and no
  `archive_manifest.json` is written. `reference_h4/` does not exist and
  is not created here.
- **No Phase B artifact is created.** No `LifecyclePhase`, no
  `advance_phase()`, no `DecisionRecorder`, no `GateRunner`, no linter
  change.
- **No invariant, mechanism, check, or test binding `research_archive/`
  to `ProjectRegistry` is created**, and none is required by this record
  of any future increment.
- **No new approval requirement is created.** No sign-off,
  counter-signature, reviewer report, or process step is introduced for
  any future increment beyond those Resolution §4.1 already imposes.
- **No historical governance decision is reopened.** No prior AD, gate
  determination, freeze record, archived result, or closeout is amended,
  withdrawn, re-run, or re-interpreted. A-1's ruling at `aca36fb`, and
  its acceptance-dependent discharge, stand exactly as they stand.
- **No hypothesis is selected, proposed, or approved.** R-1 names a
  string; H4's Phase 1 and Phase 2 are untouched and unperformed.
- **No commit is made by this record.**

---

## 9. Future migration notes

Carried forward, in the increment each belongs to. None is a new
requirement on anyone; each is a disclosed consequence of a ruling above.

1. **`historical_backfill.py:3-6` — stale completeness claim (F-2/F-3).**
   The sentence "the complete set; no fourth candidate exists in
   `research_archive/`" should be corrected in the increment that adds a
   registration path for a non-historical cycle. The correction is a
   docstring edit accompanied by an AD or a dated note, never a silent
   rewrite: the sentence was true when written, and the record should say
   when it stopped being true.
2. **`RESEARCH_ARCHIVE_MANIFEST.md`'s `"project_id": "h4"` (F-17).** When
   `reference_h4/archive_manifest.json` is generated (Resolution §4.2,
   Phase B/E), its `project_id` reads `reference_h4` per R-1. The
   document's schema example is not edited by this record; if it is ever
   updated, it is updated as a new dated revision under that document's
   own "Versioning" section, not in place.
3. **`positive_control_phase3` registration.** When that cycle reaches a
   point at which registration is wanted, R-2's grounds 1 and 2 are what
   must be cleared — a Phase-B-legal registration path for an open cycle.
   `origin_date` should be taken from `archive_manifest.json`'s
   `created_at` (2026-07-20), which is an already-recorded evidence date;
   nothing about that date is to be invented or back-derived.
4. **The archive↔registry invariant.** If one is ever built, it is its
   own increment with its own AD, and it must decide explicitly what it
   does with an *open* cycle directory and with a directory that is
   evidence for a cycle that never registers. This record deliberately
   leaves both open rather than pre-deciding them.
5. **A lineage for the `reference_v1` → `reference_v2_h1` succession.**
   None exists and none is created (R-3 precision 1). If a future cycle
   opens a Phase 3 attempt cap on a mechanism either of those cycles
   touched, that cap opens a **new** `lineage_id` under the Register's
   own certification procedure — it does not retroactively constitute a
   lineage over the historical pair.
6. **If the next cycle is not roadmap H4.** R-1's limitation governs:
   the new cycle takes `reference_h<n>` for its own hypothesis label, and
   `reference_h4` is not reused. Any document that then refers to "H4" as
   shorthand for "the next cycle" is, at that moment, referring to a
   hypothesis that was not selected, and should be read accordingly.
