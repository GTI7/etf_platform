# Phase 4 / Step 9 — A-8 Ruling Record (machine-artifact location)

**Date filed:** 2026-07-22
**Repository state ruled against:** canonical `D:\Claude\etf_platform`, `master`, HEAD `3ee23fd`, working tree clean.

---

## 1. Status

**Status: ruling record.** It disposes of prerequisite A-8 and of nothing
else. It is **not** an ADR, **not** an amendment to any ADR draft, **not**
a schema revision, **not** a storage mechanism, and **not** a Phase B
artifact.

**Prerequisite addressed:**
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
§4.1 row A-8 — *"Machine-artifact location decided relative to
`RESEARCH_ARCHIVE_MANIFEST.md`'s expected layout"*, whose "Done when"
column reads **"Recorded in AD-048"**.

**A-8 is decided by this record. A-8 is not closed by this record**, and
this record does not claim otherwise. The distinction is the same one
[`PHASE_4_A6_RESEARCH_IDENTITY_RULING_2026-07-22.md`](PHASE_4_A6_RESEARCH_IDENTITY_RULING_2026-07-22.md)
(`3ee23fd`) drew for A-6, and it holds for the same reason:

- A-8's "Done when" condition is *recorded in AD-048*. AD-048 does not
  exist in [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) — the
  accepted set runs AD-001 … AD-046 plus AD-051, and AD-047 … AD-050
  exist only as drafts in
  [`PHASE_4_STEP9_DRAFT_ADRS.md`](PHASE_4_STEP9_DRAFT_ADRS.md). Writing
  them in is **A-2**, a separate prerequisite.
- This record supplies the **decided content** A-8 requires and fixes it
  in writing at a date, so A-2's transcription has something settled to
  transcribe. **A-8 closes when AD-048 is written and accepted under A-2
  carrying the decisions in §4 below.** Until then A-8 stays open, and
  Step 9 stays blocked on it exactly as it stood at `3ee23fd`.

**No file is edited by this record, and no code is introduced by it.**
This is a new, dated file.
[`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md),
[`PHASE_4_STEP9_DRAFT_ADRS.md`](PHASE_4_STEP9_DRAFT_ADRS.md),
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md),
[`RESEARCH_ARCHIVE_MANIFEST.md`](RESEARCH_ARCHIVE_MANIFEST.md),
[`RESEARCH_LINEAGE_REGISTER.md`](RESEARCH_LINEAGE_REGISTER.md) and
[`RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md) are
all retained unedited, and each is cited below by section or line rather
than amended. In particular **`RESEARCH_ARCHIVE_MANIFEST.md`'s
`schema_version` is not incremented and its four fields are unchanged**
(§4.3).

**Supersession discipline.** Same convention, and the same disclosed
limitation on its scope, as the A-1 and A-6 ruling records: Standard §5's
"a correction is a new, dated file, cross-referenced from the file it
supersedes" is stated for evidence packages under
`research_archive/<cycle_name>/` and is applied here **by extension, not
by direct scope**, together with `ARCHITECTURE_DECISIONS.md`'s preamble
rule that a later phase revising an earlier decision says so explicitly.

**Review level: Level 1 — self-review**, per
[`RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md) §4.
Authored and reviewed within the same effort that produced the material
it rules on. Standard §4's Level 1 limitations apply in full and are
adopted, not softened; the word "independent" is not used of this record.
Level 3 is unavailable on this platform. This is not a lifecycle Decision
in the Standard §2/§7 sense — no research conclusion, no gate
determination, no step toward capital allocation is made here.

**Verification basis.** Every factual claim in §3 was checked directly
against the canonical repository at `3ee23fd` — file contents, `git
ls-files`, and the working tree — and each carries its source. No claim
rests on an off-repo artifact.

---

## 2. Scope

**In scope — exactly three questions, no more:**

1. Whether governance machine artifacts are per-project, platform-level,
   or hybrid.
2. The canonical path/location.
3. How that location relates to `project_id`, `cycle_name`, `lineage_id`,
   and the future Phase B implementation.

**Out of scope, and not decided here:** every other Phase A prerequisite
(A-1 — ruled on at `aca36fb`; A-6 — ruled on at `3ee23fd`; A-2, A-3, A-4,
A-5, A-7, A-9 — untouched and open on their own terms). In particular:

- **A-5 (chain-anchoring mechanism) is not decided here.** This record
  fixes *where* the chain file sits and therefore what a
  `sequence_number` is scoped to; the anchor's format, its numbering
  origin, and the verification procedure are A-5's and remain open.
- **A-9 (single-writer enforcement) is not decided here.** §5 records how
  the location *bounds* the blast radius of a concurrent write; whether
  enforcement is a stated assumption or a mechanical lock is A-9's and
  remains open.
- Whether a `GateRunRecord` is persisted at all (Phase D's question);
  only *where, if it is* (R-5).

**Phase A discipline is binding on this record.** Resolution §4.1 scopes
Phase A to "documents only, zero code". Nothing here writes a file into
any archive, creates a directory, implements a store, or creates a
Phase B artifact. See §8.

---

## 3. Facts established

Each row was verified directly at `3ee23fd`.

| # | Fact | Source |
|---|---|---|
| F-1 | The evidence package is defined as **"a single, self-contained evidence package under `research_archive/<cycle_name>/`, in the following fixed structure"** — seven named items | `RESEARCH_GOVERNANCE_STANDARD.md:413-437` |
| F-2 | Standard §5's completeness rule is a **minimum, not a maximum**: *"A package missing any of the seven items above is incomplete"*. No rule forbids additional files | `RESEARCH_GOVERNANCE_STANDARD.md:459-460` |
| F-3 | The archive already carries additional machine artifacts beyond the seven, with dated filenames: `reference_h3/` holds 7 such `.json` files (e.g. `phase6_economic_validation_2026-07-19.json`); `reference_v1/` and `reference_v2_h1/` hold one each; `positive_control_phase3/` holds `generator_fidelity_results.json` and `rho_calibration.csv` | `git ls-files` over `research_archive/` |
| F-4 | Standard §5's naming convention: *"Every file is dated in its own content **or** filename; nothing in this package is ever silently overwritten. A correction is a new, dated file"* | `RESEARCH_GOVERNANCE_STANDARD.md:439-443` |
| F-5 | `decision_log.md` is named as **the one file in the package that is genuinely append-only in the literal sense** (entries added, nothing removed or edited) rather than superseded-by-new-file | `RESEARCH_GOVERNANCE_STANDARD.md:452-456` |
| F-6 | `RESEARCH_LINEAGE_REGISTER.md` states its own partition rule verbatim: it is *"a **platform-level** governance artifact, not scoped to any single research cycle"*, living in `docs/` because it is *"a living, cross-cutting document that outlives any one cycle's `research_archive/<cycle_name>/` package … it is never filed inside a single cycle's archive folder"* | `RESEARCH_LINEAGE_REGISTER.md:9-20` |
| F-7 | The only fixed-location machine artifacts governance code reads today are **per-cycle and at the cycle directory's root**: `cycle_dir / "reproduction_record.json"` and `cycle_dir / "dataset_manifest.json"` | `core/governance/reproduction_runner.py:294-295,312-313` |
| F-8 | `reproduction_record.json` is therefore an existing precedent for a **fixed-name, undated, machine-read artifact at the cycle root** that is not one of Standard §5's seven items | F-7 with `RESEARCH_GOVERNANCE_STANDARD.md:413-437` |
| F-9 | `archive_manifest.json` is per-cycle, written **once**, at the point a *new* project's archive directory is created, and never retroactively into the three legacy directories | `RESEARCH_ARCHIVE_MANIFEST.md:25-35,87-94` |
| F-10 | `write_manifest()` refuses to write into `reference_v1`, `reference_v2_h1`, `reference_h3`, and refuses to overwrite an existing manifest | `tools/archive_manifest.py:33,81-89` |
| F-11 | The scaffold generator takes the archive root as an **injected parameter** — `scaffold_project_archive(project_id, archive_root, clock, *, lifecycle_version="v1")` — not a module-level constant | `RESEARCH_ARCHIVE_MANIFEST.md:96-107`; `tools/archive_manifest.py:107` |
| F-12 | Exactly one `archive_manifest.json` exists in the repository, in `positive_control_phase3/`. The three legacy directories have none and will never be given one (F-9) | `git ls-files`; `RESEARCH_ARCHIVE_MANIFEST.md:25-35` |
| F-13 | `manifest.project_id` is defined as *"matching its `research_archive/<project_id>/` directory name and … its `ProjectId`"* | `RESEARCH_ARCHIVE_MANIFEST.md:51` |
| F-14 | `tools/archive_manifest.py` **does not read or interpret an existing manifest**, and does not implement `ArchiveVerifier` | `RESEARCH_ARCHIVE_MANIFEST.md:14-18,76-78` |
| F-15 | `ArchiveVerifier` is on Step 9's may-not-implement list — *"no Step 9 consumer exists for any of them"* | `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:512-514` |
| F-16 | AD-048's storage is `core.governance.canonical_jsonl`; append is read-append-rewrite, written atomically | `PHASE_4_STEP9_DRAFT_ADRS.md:144-150` |
| F-17 | `write_canonical_jsonl` **silently creates the parent directory** — `path.parent.mkdir(parents=True, exist_ok=True)` — and then rewrites the whole file via `path.write_bytes` | `core/governance/canonical_jsonl.py:32-33` |
| F-18 | AD-048's anchor is the **hand-authored `decision_log.md` entry citing the chain head hash and sequence number**, plus a human-performed commit outside any run | `PHASE_4_STEP9_DRAFT_ADRS.md:170-178`; Resolution §2.2 |
| F-19 | `decision_log.md` is **per-cycle**, at `research_archive/<cycle_name>/decision_log.md` — Standard §5's structure, and the path the Register already cites for `positive_control_phase3` | `RESEARCH_GOVERNANCE_STANDARD.md:430`; `RESEARCH_LINEAGE_REGISTER.md:116` |
| F-20 | Governance may import **only** `data`: `ALLOWED_DEPENDENCIES["governance"] == frozenset({"data"})`. It cannot import Research, and therefore cannot see a `Project` | `tools/check_import_boundaries.py:64` |
| F-21 | `Project` stores `repository_path: str`, and all three backfilled entries set it to exactly `research_archive/<project_id>` | `core/research/project.py:69`; `core/research/historical_backfill.py:52,69,86` |
| F-22 | A-6 ruled that **phase attaches to a `cycle_name`**, not to a `lineage_id` (which spans cycles that were in different phases) and not to an `attempt_number` | A-6 §4.3, restating Resolution D-15 |
| F-23 | A-6 ruled that `ProjectId`/`project_id` carry a string **byte-identical to `cycle_name`** and introduce no identity distinct from it | A-6 §4.3 precision 2 |
| F-24 | AD-050 derives current phase **from the transition record chain**, and records that the three historical projects have **no transition records at all** | `PHASE_4_STEP9_DRAFT_ADRS.md:383-403` |
| F-25 | Standard §5 assigns `experiment_results/` the meaning *"raw, unmodified Validation output (Phase 6), append-only"* | `RESEARCH_GOVERNANCE_STANDARD.md:426` |
| F-26 | No governance machine artifact is stored outside `research_archive/` today. The only repository-level machine artifact of any kind is `tests/fixtures/protected_file_hashes.json`, a test fixture read solely by `tests/test_repository_integrity_snapshot.py` | `git ls-files` over `*.json`/`*.jsonl`; `tests/test_repository_integrity_snapshot.py:25` |
| F-27 | No `.jsonl` file is tracked anywhere in the repository, and no top-level governance-artifact directory exists | `git ls-files` |

---

## 4. Decision

Five rulings, R-1 … R-5. Each is stated in the form it is to be
transcribed under A-2.

### 4.1 R-1 — Taxonomy: hybrid as a class; **per-cycle** for every governance machine artifact

**Ruled: the platform's governance artifacts are hybrid, under a
deterministic partition rule — and under that rule every governance
*machine* artifact is per-cycle. No governance machine artifact is
platform-level today, and Step 9 creates none.**

The partition rule is **adopted, not invented**: it is
`RESEARCH_LINEAGE_REGISTER.md`'s own scope paragraph (F-6), generalized
one step and stated as a rule.

> **Partition rule.** An artifact whose subject is a **single cycle**
> lives inside that cycle's evidence package, `research_archive/<cycle_name>/`.
> An artifact whose subject **spans cycles and outlives any one of them**
> is platform-level and lives in `docs/`.

Applied to the repository as it stands, exhaustively:

| Tier | Artifacts at `3ee23fd` | Location | Step 9 adds |
|---|---|---|---|
| **Per-cycle machine artifacts** | `archive_manifest.json` (F-9), `dataset_manifest.json`, `dataset_hashes/`, `experiment_results/`, `reproduction_record.json` (F-7) | `research_archive/<cycle_name>/` | the transition chain (R-2) |
| **Platform-level governance artifacts** | `RESEARCH_LINEAGE_REGISTER.md`, `RESEARCH_GOVERNANCE_STANDARD.md`, `RESEARCH_ARCHIVE_MANIFEST.md` — all **human-authored, append-only or versioned prose** (F-6) | `docs/` | **nothing** |
| **Repository-integrity artifacts** | `tests/fixtures/protected_file_hashes.json` (F-26) | `tests/fixtures/` | **nothing** |

Two properties of that table are load-bearing and are ruled, not merely
observed:

1. **The platform-level tier is human prose, and stays that way.** Every
   cross-cutting governance artifact on this platform is a document a
   person writes and reads. **Step 9 introduces no platform-level machine
   artifact**, and none of AD-048's records is ever written to `docs/`.
2. **The third tier is not a governance tier.** `protected_file_hashes.json`
   is a test fixture about the repository, not about any cycle or any
   research process. It is named here only so the taxonomy is exhaustive
   against the repository as it stands; nothing in Step 9 touches it, and
   it is **not** a precedent for placing governance records outside
   `research_archive/`.

### 4.2 R-2 — Canonical path

**Ruled: the AD-048 transition chain is one file per cycle, at**

```
<archive_root>/<cycle_name>/transition_records.jsonl
```

**where `<archive_root>` is `research_archive/` in this repository and is
supplied as an injected parameter, never a module-level constant** (F-11,
the discipline `scaffold_project_archive` already follows).

| Element | Ruled | Ground |
|---|---|---|
| **One chain per cycle** | Exactly one chain file per `cycle_name`; never one global chain, never one per lineage, never one per attempt | R-4, §5 |
| **Cycle directory root** | Sibling of `decision_log.md`, not inside `dataset_hashes/`, `experiment_results/`, or `reviewer_reports/` | Each of those three has a defined meaning under Standard §5 (F-1); filing a governance chain in one would misrepresent it as a dataset hash, an experiment result, or a review. Precedent: `reproduction_record.json` sits at the cycle root (F-7/F-8) |
| **Filename `transition_records.jsonl`** | Fixed, lowercase, undated | Below |
| **Extension `.jsonl`** | Storage is canonical JSONL per AD-048 (F-16); the extension states the format rather than hiding it behind `.json` | AD-048 |

**Why `transition_records.jsonl` and not `decision_records.jsonl` or
`decision_chain.jsonl`.** AD-045 and AD-048 exist to keep the mechanical
record and the hand-authored `decision_log.md` **distinguishable by a
reader who is not holding the ADs**. A filename that reads as a sibling
of `decision_log.md` invites exactly the conflation those decisions
guard against — a later reader treating the chain as "the decision log,
automated." The file records **phase transitions**, which is what AD-048
says it records, and the name says so.

**Why the filename is undated, and why that does not violate Standard
§5.** F-4 requires each file to be dated *"in its own content **or**
filename"*. Every record in this file carries an injected UTC timestamp
(AD-048's field set), so the file is dated in its content, per record,
which is the stronger of the two options. **A dated file per append is
affirmatively rejected**: it would make every append its own genesis
chain, and a chain that cannot reference its predecessor file proves
nothing — the mechanism AD-048 exists to build would be destroyed by the
naming convention meant to protect it. The file is the same class as
`decision_log.md`, the one file Standard §5 already recognizes as
literally append-only rather than superseded-by-new-file (F-5): **it is
the machine counterpart of that file, and it inherits that discipline.**
This is a reading of §5, not an amendment to it; the Standard is not
edited (§8).

### 4.3 R-3 — Preconditions and prohibitions attaching to the path

Ruled, and each is a **precondition on writing**, not a mechanism built
here:

1. **The recorder never creates a directory.** `write_canonical_jsonl`
   silently `mkdir`s its parent (F-17). Left unguarded, a mistyped or
   unregistered `cycle_name` would **manufacture an archive directory
   with no `archive_manifest.json`** — an unmanifested archive directory,
   which is precisely the archive↔registry divergence class A-6 R-2 ruled
   on and declined to mechanize. AD-048 must therefore state that the
   cycle directory's existence is a **precondition of the first record**,
   never a consequence of it.
2. **A chain is written only into a directory that already contains
   `archive_manifest.json`.** This single condition also **excludes the
   three legacy archives by construction** — they have no manifest and
   will never be given one (F-9, F-12) — without a hardcoded name list,
   and therefore without `core/governance/` needing anything from
   `tools/archive_manifest.py`. It is consistent with AD-050's own
   position that the three historical projects have no transition records
   at all (F-24).
3. **Identity is checked, completeness is not.** The manifest is read for
   exactly one purpose: confirming `manifest.project_id` (F-13), the
   directory name, and the record's `project_id` are **byte-identical**
   (F-23). `lifecycle_version` is **deliberately not consulted**:
   interpreting it is `ArchiveVerifier`'s job, and `ArchiveVerifier` is on
   Step 9's may-not-implement list (F-14, F-15). Disclosed: this makes the
   recorder the **first component in the repository to read an existing
   manifest**, which `RESEARCH_ARCHIVE_MANIFEST.md` anticipated only for a
   future `ArchiveVerifier`. It is a three-way identity check, not a
   completeness check, and it must not grow into one.
4. **`RESEARCH_ARCHIVE_MANIFEST.md` is not amended and its
   `schema_version` is not incremented.** The manifest is a four-field
   index that does not enumerate its directory's contents; a new file
   beside it changes nothing the manifest asserts. This is the direct
   answer to A-8's wording, *"relative to `RESEARCH_ARCHIVE_MANIFEST.md`'s
   expected layout"*: the chain sits **inside the directory the manifest
   indexes, and outside the manifest's schema**.
5. **No new top-level directory, and nothing outside the repository.** No
   `governance_records/`, no `.governance/`, no untracked or
   out-of-repository store. AD-048's anchor requires a **human-performed
   commit** of the artifact under existing archive discipline (F-18); an
   artifact that git does not track cannot be anchored that way at all.

### 4.4 R-4 — Relation to `project_id`, `cycle_name`, and `lineage_id`

| Identity | Relation to the location | Ruled |
|---|---|---|
| **`cycle_name`** | **The partition key.** It is the one path segment between the archive root and the filename | Phase attaches to the cycle (F-22). The chain exists to derive current phase (F-24). Partition key and phase-bearing identity are therefore the **same** identity, and the file is one-to-one with it |
| **`project_id`** | **Not a second key.** It is byte-identical to `cycle_name` (F-23), so it appears in the path exactly once, as that segment | The `project_id` **field stays in the record** even though the path implies it: the field set is closed and pinned by test (AD-048), removing a field is a new AD, and the redundancy keeps a record self-describing if it is ever quoted outside its file |
| **`lineage_id`** | **Never appears** — not in the path, not in the filename, not in the record | A lineage spans cycles that were in different phases (F-22). A lineage-partitioned chain would interleave transitions of different cycles into one sequence from which no cycle's current phase could be derived. Cross-cycle lineage facts stay where F-6 puts them: `RESEARCH_LINEAGE_REGISTER.md`, platform-level, human, append-only. **The lineage view is obtained by joining in the Register, never by partitioning the machine artifact** |
| **`attempt_number`** | Never appears | An attempt does not advance the governance process (A-6 §4.3 precision 3); it is not a phase-bearing identity |

**Two consequences of the partition key, stated because they are forced
by the location and would otherwise be re-decided ad hoc:**

- **`sequence_number` is scoped to the file, and the file is the chain.**
  A cycle's sequence numbers are monotonic within that cycle; they are
  not global and do not order transitions across cycles. The numbering
  **origin**, the anchor's format, and the verification procedure are
  **A-5's and are not decided here** (§2).
- **`Project.repository_path` is not consulted, and cannot be.**
  Governance may import only `data` (F-20), so the recorder never sees a
  `Project`. The path is computed from the injected archive root and the
  `cycle_name` string. Disclosed: `repository_path` is a second, stored
  representation of the same location (F-21). It agrees with this rule
  for all three backfilled entries, **nothing enforces that agreement, and
  this record creates no invariant binding them** — consistent with A-6
  R-2's refusal to mechanize the archive↔registry relation. The only place
  the two could ever be reconciled is `core/research/lifecycle.py`, the
  sole module permitted to import Validation and Governance together.

### 4.5 R-5 — Validation's records take the same partition rule

**Ruled: if a `GateRunRecord` is persisted to disk at all, it is
per-cycle, at `research_archive/<cycle_name>/experiment_results/`, with a
dated filename.**

- Standard §5 assigns `experiment_results/` exactly this meaning: *"raw,
  unmodified Validation output (Phase 6), append-only"* (F-25). A gate run
  record is raw Validation output; no new location is needed and none is
  created.
- The filename **is** dated, unlike R-2's chain, because each run record
  is a discrete artifact superseded-by-new-file under §5's convention
  (F-4) rather than a chain — matching `reference_h3`'s existing dated
  result JSONs (F-3).
- **Whether it is persisted at all is Phase D's question and is not
  decided here.** Only the location, and only so that Phase D does not
  make a second, ad-hoc location choice.
- **This ruling is transcribed into AD-049, not AD-048**, since
  `GateRunRecord` is AD-049's object. A-8's "Done when" column names
  AD-048; that remains correct for R-1 … R-4.

---

## 5. Rationale

**Why per-cycle rather than one platform-level chain** — five grounds, in
order of decisiveness. The first is sufficient on its own.

1. **Standard §5 requires the package to be self-contained** (F-1). A
   cycle whose phase-transition evidence lives in a shared file outside
   its package is not self-contained by inspection. At Phase 8 the cycle
   would be archived while the file holding its transition history stays
   live and continues to be appended to by other cycles — an archived
   package whose central governance evidence is still mutating elsewhere.
2. **The anchor is per-cycle, so the chain must be.** AD-048's
   tamper-evidence is not self-contained: the head hash and sequence
   number are cited in the hand-authored `decision_log.md` entry (F-18),
   and `decision_log.md` is per-cycle (F-19). Under a global chain, the
   head hash cited in cycle X's decision log would anchor a chain
   containing cycles Y and Z's records; verifying X's tail would require
   collecting every other cycle's decision log, and a cycle archived at
   Phase 8 would be anchoring records written after it closed. Per-cycle
   makes the chain and its anchor **co-located and one-to-one**.
3. **Truncation locality.** Resolution §2.2 accepts that a self-contained
   chain cannot prove its own length and that tail truncation is the
   residual exposure. Under a global chain, one truncation silently
   removes the most recent transitions of **whichever cycles happen to be
   at the tail**, and each cycle's latest record is at an arbitrary
   interior position. Under a per-cycle chain the exposure is bounded to
   one cycle, and that cycle's latest record is its own head — the object
   its own anchor names.
4. **The partition rule already exists and points this way** (F-6). The
   Register states that a cross-cutting artifact belongs in `docs/`
   *because* it outlives any one cycle. A phase-transition chain does not
   outlive its cycle; it terminates with it.
5. **Blast radius under A-9.** Single-writer enforcement is A-9's to
   decide, but the location fixes what a violation costs: with a global
   chain, two cycles advancing concurrently contend on one file and a lost
   write corrupts an unrelated cycle's evidence. Per-cycle, concurrent
   advancement of different cycles does not contend at all. This is a
   consequence recorded, **not** a decision of A-9 (§2).

**Why the cycle root rather than a subdirectory.** The three §5
subdirectories are typed by content, and none of them is "governance
machine records" (F-1). Placing the chain in one would assert something
false about what it is. `reproduction_record.json` establishes that a
fixed-name machine artifact at the cycle root is the existing shape for
exactly this case (F-8), and the chain's reader — a human verifying an
anchor cited in `decision_log.md` — finds it adjacent to the document
that cites it.

**Why the manifest is the precondition rather than a name list.** A
hardcoded list of legacy directory names inside `core/governance/` would
duplicate `tools/archive_manifest.py:33` (F-10) in a second location that
nothing keeps in sync, or force a `core/` → `tools/` import that the
boundary checker does not currently police (it collects only `core`
modules). Keying on the manifest's presence derives the same exclusion
from a fact already on disk, needs no list, and stays true automatically
when a fifth cycle is created.

**Why an eighth file in the package is not a Standard change.** §5's
seven items are a **minimum** (F-2), all four archive directories already
carry machine artifacts beyond the seven (F-3), and one of
them — `reproduction_record.json` — is a fixed-name machine artifact
defined by committed code (F-7). Reading §5 as a closed list would
retroactively make three of the four existing packages non-conforming,
which is not what the document says and not how it has been applied.

---

## 6. Consequences for AD-048

AD-048 is a **draft**. This record does not edit it. When it is written
into `ARCHITECTURE_DECISIONS.md` under A-2, it carries the following, and
A-8 closes at that point:

| # | Required of AD-048 | Source |
|---|---|---|
| C-1 | State the partition rule: an artifact scoped to one cycle lives in `research_archive/<cycle_name>/`; a cross-cutting artifact is platform-level in `docs/`. Record that Step 9 adds **no** platform-level machine artifact | R-1 |
| C-2 | Record the canonical path `<archive_root>/<cycle_name>/transition_records.jsonl`, one file per cycle, with `<archive_root>` injected and never a module-level constant | R-2 |
| C-3 | Record why the filename is undated (dated per record in content, §5's "or filename" limb) and that a dated-file-per-append is rejected because it destroys the chain | R-2 |
| C-4 | Record that the recorder **never creates a directory**, and that `write_canonical_jsonl`'s silent parent `mkdir` is the specific hazard being guarded | R-3.1, F-17 |
| C-5 | Record the write precondition: the target directory exists **and** contains `archive_manifest.json`, which excludes the three legacy archives by construction with no hardcoded name list | R-3.2 |
| C-6 | Record that the manifest is read for a three-way `project_id` identity check only; `lifecycle_version` is not consulted, because interpreting it is `ArchiveVerifier`'s and `ArchiveVerifier` is out of Step 9 scope | R-3.3 |
| C-7 | Record that `RESEARCH_ARCHIVE_MANIFEST.md` is unamended and its `schema_version` unchanged — the chain sits inside the directory the manifest indexes and outside the manifest's schema | R-3.4 |
| C-8 | Record that no new top-level directory is created and that nothing is stored outside the repository, since the anchor requires a human-performed commit of a tracked file | R-3.5, F-18 |
| C-9 | Record the identity relation: `cycle_name` is the partition key; `project_id` is byte-identical to it and stays in the record; `lineage_id` and `attempt_number` never appear in the path, filename, or record | R-4 |
| C-10 | Record that `sequence_number` is scoped to the per-cycle file, and that its origin and the anchor's format remain A-5's | R-4 |
| C-11 | Disclose that `Project.repository_path` is a second stored representation of the same location, that the recorder cannot consult it (Governance imports only `data`), and that **no invariant binding them is created** | R-4, F-20, F-21 |

**Required of AD-049 rather than AD-048:** R-5 — if a `GateRunRecord` is
persisted, it goes to `research_archive/<cycle_name>/experiment_results/`
with a dated filename.

**What is unchanged in AD-048 by this record:** its field set, its
transcription-not-certification claim, its tamper-evidence limits, its
refusal to commit, its rejection of the borrowed-precedent justification,
and its Migration Plan §10 item 4 disposition. This record speaks only to
where the artifact sits.

---

## 7. Effect

| Item | Status after this record |
|---|---|
| **A-8, question 1 — per-project / platform-level / hybrid** | **Decided:** hybrid as a class, under a partition rule adopted from `RESEARCH_LINEAGE_REGISTER.md`; **per-cycle** for every governance machine artifact. §4.1 |
| **A-8, question 2 — canonical path** | **Decided:** `<archive_root>/<cycle_name>/transition_records.jsonl`, one per cycle, archive root injected. §4.2 |
| **A-8, question 3 — identity and Phase B relation** | **Decided:** `cycle_name` is the partition key; `project_id` is byte-identical and stays in the record; `lineage_id` and `attempt_number` never appear; Phase B boundary in §9. §4.4 |
| **A-8 as a prerequisite** | **Decided in writing, not yet closed.** Closes when AD-048 is written and accepted under A-2 carrying C-1 … C-11. §1 |
| **A-2** | **Open, unchanged.** This record adds required content to AD-048 and one item to AD-049; it does not write or accept either |
| **A-5 (anchor), A-9 (single writer)** | **Open, unchanged.** Bounded by this record's location decision; not decided by it. §2 |
| **A-1, A-6** | **Ruled on at `aca36fb` and `3ee23fd` respectively.** Not re-decided, not reopened |
| **A-3, A-4, A-7** | **Open, unchanged.** Not spoken to |
| **Step 9** | **Blocked, unchanged.** Resolution §4.1's rule — "Step 9 does not start until every item below is closed in writing" — is unchanged and unrelaxed |
| **`RESEARCH_ARCHIVE_MANIFEST.md`** | **Unedited, `schema_version` 1 unchanged.** No revision required by this ruling |
| **Archive ↔ registry divergence** | **Open, disclosed, unmechanized.** Unchanged from A-6 R-2; R-3.1 explains why the location rule must not be allowed to widen it |

**How to re-run this ruling.** Every input is named so a later reader need
not trust this document: the package definition against
`RESEARCH_GOVERNANCE_STANDARD.md:413-461`; the partition rule against
`RESEARCH_LINEAGE_REGISTER.md:9-20`; the per-cycle precedent against
`core/governance/reproduction_runner.py:294-313`; the manifest facts
against `RESEARCH_ARCHIVE_MANIFEST.md` and `tools/archive_manifest.py`;
the `mkdir` hazard against `core/governance/canonical_jsonl.py:32-33`; the
anchor against `PHASE_4_STEP9_DRAFT_ADRS.md:170-178` and Resolution §2.2;
the import boundary against `tools/check_import_boundaries.py:64`; and the
artifact inventory against `git ls-files`.

---

## 8. Explicit non-actions

Stated as prohibitions honoured by this record, each verifiable against
the diff:

- **No code is modified or created.** `core/governance/`, `core/research/`,
  `core/shared/`, `core/validation/`, `tools/`, and every test file are
  untouched.
- **No ADR file is modified.** `PHASE_4_STEP9_DRAFT_ADRS.md` is retained
  unedited; §6 states what AD-048 and AD-049 must carry and changes
  nothing in either draft. `ARCHITECTURE_DECISIONS.md` is not modified —
  no AD is added, amended, renumbered, accepted, or marked superseded.
- **No storage mechanism is implemented.** No file writer, no chain, no
  reader, no path constant, no directory guard, no manifest reader, no
  lock. Every "must" in §4 is a decision to be transcribed, not a
  behaviour introduced.
- **No file or directory is created under `research_archive/`.** No
  `transition_records.jsonl` exists anywhere in the repository, and none
  is created here. No `archive_manifest.json` is written or read.
- **`RESEARCH_ARCHIVE_MANIFEST.md` is not amended**, its four fields are
  unchanged, and `schema_version` is not incremented.
- **`RESEARCH_GOVERNANCE_STANDARD.md` §5 is not amended.** R-2 reads §5's
  existing "or filename" limb and its existing decision_log.md carve-out;
  it does not add an eighth required item, and a package without a
  transition chain is not thereby incomplete.
- **Nothing is written to `RESEARCH_LINEAGE_REGISTER.md`.** No
  `lineage_id` is opened, retired, or certified. The append-only
  discipline is observed by not appending.
- **No Phase B artifact is created.** No `LifecyclePhase`,
  `advance_phase()`, `DecisionRecorder`, `GateRunner`, or linter change.
- **No invariant or mechanism binding `Project.repository_path` to the
  archive path is created**, and none is required of any future increment.
- **A-5 and A-9 are not decided**, and no part of §4 may be cited as
  deciding them.
- **No hypothesis, gate determination, or research conclusion is made.**
- **No commit is made by this record.**

---

## 9. Future implementation boundary

Carried forward, in the increment each belongs to. None is a new
requirement on anyone; each is a disclosed consequence of a ruling above.

1. **Phase B-3 (`advance_phase()`, H4 registration)** establishes the
   first cycle that will have a chain. Under A-6 R-1 that cycle's
   `cycle_name` is `reference_h4`, so its chain path is
   `research_archive/reference_h4/transition_records.jsonl` — and by
   R-3.2 the directory and its `archive_manifest.json` must exist
   **before** the first transition is recorded. Nothing in the repository
   currently fixes *when* an archive directory is scaffolded relative to a
   cycle's first phase transition (F-9 fixes only that it happens once, at
   directory creation). **Phase B must state that ordering explicitly
   rather than discover it**, and the archive root must be injected, not
   hardcoded (F-11).
2. **Phase C (`DecisionRecorder`)** owns the guard implementing R-3.1 and
   R-3.2. It must not reach the guard through `tools/archive_manifest.py`:
   `core/` → `tools/` is not policed by the boundary checker, and adding
   an unpoliced edge from the domain that exists to be trustworthy is the
   wrong trade. Deriving the exclusion from the manifest's presence needs
   no shared list (§5).
3. **The manifest reader introduced by R-3.3** is the first component to
   read an existing `archive_manifest.json`. It reads `project_id` and
   nothing else. If a later increment wants `lifecycle_version` or a
   completeness check, that is `ArchiveVerifier` — its own increment, its
   own AD, and out of Step 9 scope (F-15).
4. **Phase D (`GateRunner`)** takes R-5 if it persists a `GateRunRecord`:
   `research_archive/<cycle_name>/experiment_results/`, dated filename.
   Whether to persist at all remains Phase D's decision.
5. **The three legacy archives never receive a chain**, and their absence
   of one is the true state, not a gap to be backfilled (F-24). Any future
   proposal to give them transition records is a retroactive-fact
   violation of the class `project.py:32-41` already refuses for
   `origin_date`, and would need its own ruling.
6. **`positive_control_phase3` already satisfies R-3.2's precondition** —
   it is the one directory with an `archive_manifest.json` (F-12). That
   does **not** authorize writing a chain into it: it is unregistered in
   `ProjectRegistry` and its registration is deferred on A-6 R-2's stated
   grounds. If it is ever registered, its chain path follows R-2 with no
   special case.
7. **If a genuinely cross-cutting machine artifact is ever needed** — one
   whose subject spans cycles — R-1's partition rule sends it to the
   platform-level tier, which today contains only human prose. Creating
   the first platform-level *machine* artifact would be a new platform
   concept requiring its own AD and its own location ruling. This record
   deliberately does not pre-decide it.
