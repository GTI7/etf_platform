# Archive Seal — Design Review and Proposed AD-074

**Status:** **Accepted as AD-074, 2026-07-26** — recorded in
`docs/ARCHITECTURE_DECISIONS.md` under **AD-074**, which is the accepted
decision; this document remains the design review that entry accepts.
See the **Acceptance record** immediately below for the commits that
acceptance covers and for what it does and does not claim.

**Review history.** **Reviewed 2026-07-26: Accept with conditions.**
The conditions are remediated below (§7, §7A, §7B, and the count correction
in §2). Until the acceptance recorded above, this document read "not yet
formally accepted as an AD pending that remediation's own review" — and it
still read that way after the Increment 2 implementation landed. That gap
is what the AD-074 register entry closes, and it is why that entry records
acceptance *after* implementation rather than before it. One architecture
document,
`docs/ARCHITECTURE_DECISIONS.md`, **is** changed — narrowly, by the four
amendments §7 enumerates (AD-073's Responsibilities, Decision part 5, AC-3,
Status vocabulary, the Architecture overview table, and new **A8-C12**) —
and, under the hardening pass below, by one further amendment to AC-15.

**Acceptance record (2026-07-26).** Three commits, in the order they were
made, stated as the audit trail rather than as a sequence anyone planned:

| Commit | What it did |
|---|---|
| `2392de2` | `feat(governance): implement AD-074 archive seal hardening` — **Increment 2** (§11): `core/governance/archive_seal.py`, the Seal branch in `core/governance/archive_verifier.py`, the empty `docs/archive_seal_register.jsonl`, this document, and the AD-073 amendment blocks + **A8-C12** in `docs/ARCHITECTURE_DECISIONS.md`. |
| `a8f031b` | `docs(governance): clarify AD-074 hardening references and register limits` — documentation-only correction of Increment 2: §7C's `BLOCKER`/`M` registry and the D5 rewording. No behaviour changed. |
| *this commit* | `docs(governance): formally accept AD-074 archive seal decision` — adds the **AD-074 entry to `docs/ARCHITECTURE_DECISIONS.md`**, sets this document's status to accepted, and fixes D1's symbol names, D5's forward reference, and §7B's heading range. Documentation only. |

What that trail means, stated plainly:

- **`2392de2` and `a8f031b` implemented Increment 2** — the Seal branch and
  the Register reader, with the Register left empty. They did not, and
  could not, perform Increment 1.
- **This acceptance closes the Increment 1 documentation gap.** §11's
  Increment 1 ("accept AD-074 + the AD-073 AC-3 amendment", documentation
  only) was never performed as its own act: the AD-073 amendments it names
  were applied inside the implementation commit, and no AD-074 register
  entry was ever written. This commit writes that entry. It records
  acceptance **as of today**, after implementation; it does **not** claim
  Increment 1 preceded Increment 2, and no reader may cite it as evidence
  that it did.
- **Increment 3 remains future work.** No Register record has been issued,
  `docs/archive_seal_register.jsonl` is empty (0 bytes) **[verified]**, no
  archive can report `SOUND`, and **R-4 / D-9 stay live** — exactly as §11
  warns.

**Amended 2026-07-26 — Increment 2 governance hardening pass.** A second
adversarial audit, against the *shipped*
`core/governance/archive_seal.py` rather than against this design, found
that the comparison had a **third input** nobody had enumerated: the
things that decide *how* the archive's bytes are hashed and *which* of
them are compared at all. Every one of those was live working-tree or
machine state rather than a property of the sealing commit. Unlike the
two passes above, this one **does** change code and tests. Its findings
are recorded as **§7B D7–D12**, with the §5.6 table, AC-74-4, AC-74-5,
AC-74-9 and new AC-74-5a/5b updated to match, and one amendment to
AD-073 AC-15 recorded in `ARCHITECTURE_DECISIONS.md` (§7B D10). The
architecture is unchanged throughout: the Seal remains independent of
`FreezeVerifier`, makes no research-validity claim, enters no gate or
decision record, and still answers only archive tree integrity against a
fixed sealing commit.

**Baseline:** commit `414b07e` (AD-073 Phase B accepted; `ArchiveVerifier`
completeness branch and freeze branch implemented; Seal branch an intentional
stub).

**Review basis.** Level 2 (AI-assisted adversarial review, single pass) against
`core/governance/archive_verifier.py`, `decision_recorder.py`,
`freeze_verifier.py`, `dataset_manifest.py`, `tools/archive_manifest.py`,
`tests/test_repository_integrity_snapshot.py`,
`tests/fixtures/protected_file_hashes.json`, AD-030/AD-033/AD-047/AD-051/
AD-060/AD-062/AD-063/AD-065/AD-072/AD-073, and
`docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md` §§4/5/8/10. Level 3
unavailable; **never to be cited as independent** (Standard §4).

Every factual claim marked **[verified]** below was executed against the
working tree at `414b07e`. Claims not so marked are inference.

---

## 1. What this review answers

R-4 asks for "a re-protection path for a closed cycle." AD-073 named the
Archive Seal as the mechanism that answers Q2 ("are the archived files still
the bytes that were archived?") and then deliberately declined to design it,
deferring seal **issuance** — format, author, location, write authority — to
Non-goals item 1.

That deferral is the whole remaining problem. The seal branch cannot be
implemented as anything but a stub until issuance is decided, and until the
seal branch is real, `ArchiveReport.overall_status` **can never be `SOUND`**
for any archive — a fact the implementation already states in its own
docstring (`core/governance/archive_verifier.py`:58–61). A verifier that
structurally cannot return a clean result is not yet the Phase 8 instrument
R-3 asked for.

This review answers the prior question AD-073 left open — *what is a sealed
archive* — and proposes the smallest contract that closes it.

---

## 2. Review of existing integrity mechanisms

Six mechanisms exist. They are not redundant; each anchors a different claim
to a different root of trust.

| Mechanism | Subject of the claim | Root of trust | Owner | Runs today? |
|---|---|---|---|---|
| `tests/fixtures/protected_file_hashes.json` | Byte content of 36 named files | A one-time pre-Phase-0 SHA-256 snapshot, immutable by convention | Test/CI | Yes, every suite run |
| `dataset_manifest.json` `content_hash` | Byte content of `dataset_hashes/*.jsonl` | Per-entry `sha256:` recorded at freeze | Governance (`dataset_manifest.py`) | Parsed; **no checker implemented** [verified] |
| `archive_manifest.json` | That an archive directory was *scaffolded*, and its lifecycle version | Write-side guard only (AD-030) | `tools/archive_manifest.py` | Write-side only |
| `transition_records.jsonl` hash chain | That retained records were not altered, reordered, or interior-deleted | Per-record canonical hash + predecessor link | `decision_recorder` | On append; tail truncation undetectable by design |
| `freeze_verifier.verify_freeze()` | That the **live repository** still matches a claimed freeze commit over `covered_paths` | git | Governance | On call |
| `ArchiveVerifier` completeness branch | That eight required items exist and are of the right kind | Standard §5's fixed list | Governance | On call |

**Three observations that shape the design.**

**O-1 — nothing in that table hashes a closed cycle's evidence files.** The
Phase-0 fixture stops at the three legacy archives; `dataset_manifest.json`
covers only `dataset_hashes/`; the chain hashes *records*, not files; the
freeze verifier verifies the repository, not the archive; completeness checks
existence, not content. Q2 is genuinely unanswered. **[verified]**

**O-2 — a seventh mechanism already exists and is not in the table: git
itself.** Every file under `research_archive/` is a content-addressed blob
reachable from the archive-closing commit. All 53 archive files are tracked;
`reference_h4`'s archive-closing commit is `29553b7`, all 16 of its files are
present in that tree, `29553b7` is an ancestor of `HEAD`, and
`git diff 29553b7 -- research_archive/reference_h4/` is empty — a complete,
zero-artifact integrity check that passes today. **[verified]**

**O-3 — the existing mechanisms partition `research_archive/` cleanly.**
This is the most useful finding in the review, because it means the seal's
domain can be defined *structurally* rather than by convention:

| Archive | Files | Covered by | Seal's role |
|---|---|---|---|
| `reference_v1`, `reference_v2_h1`, `reference_h3` | 26 | `protected_file_hashes.json`, fully | **None** — never sealed (AD-073 Non-goals 8) |
| `reference_h4/dataset_hashes/` | 3 | `dataset_manifest.json` `content_hash` | **None** — delegated (AD-073 part 8) |
| `reference_h4`, everything else | 13 | **Nothing** | **Exactly this** |
| `positive_control_phase3` | 10 (open cycle) | Excluded pending Phase 8 | None until it closes |
| `research_archive/README.md` | 1 | Nothing — not inside any project archive directory | **None** — not an archive at all, and never in any archive's file count above |

**Count reconciliation (correction).** `git ls-files research_archive` tracks
**53** files. 26 + 3 + 13 + 10 + 1 (the `README.md` row above) = **53** —
every tracked file under `research_archive/` is now accounted for by exactly
one row. `tests/fixtures/protected_file_hashes.json` is **not** in this
reconciliation at all: its ~36 entries live **outside project archive
domains** — most of them are pre-Phase-0 platform files never under
`research_archive/` — and only its 26 archive-scoped entries appear in the
first row above. **[verified]** — fixture entry counts by archive:
`reference_h3` 20, `reference_v1` 3, `reference_v2_h1` 3, `reference_h4`
**0**.

AD-073's AC-11 ("no file covered by both a sealed manifest and either
pre-existing hash mechanism") is therefore satisfiable by construction, not by
discipline. The seal's domain is precisely *closed `lifecycle_version: "v1"`
archives, minus the dataset-manifest set*.

---

## 3. Findings that constrain any Seal design

**S-1 — the chain cannot reference the commit that seals it.** The terminal
record's own `commit_hash` is `8bc3f93`; `transition_records.jsonl` at that
commit contains **6** records, while the working tree and the archive-closing
commit `29553b7` contain **7**. **[verified]** A seal that took its reference
from the chain's terminal record would report `transition_records.jsonl` as
`MISMATCH` on a perfectly sound archive. This is G-4's ordering problem
resurfacing in a new place: *the sealing reference must be recorded after the
final append, therefore outside the chain and outside the archive.* Any design
that stores the seal inside `research_archive/<project>/` is dead on arrival
for this reason alone — before the immutability constraint (§8 of the Phase G
decision) is even considered.

**S-2 — `reference_h4` is immutable, so the seal cannot live in it.** Phase G
decision §8: no file may be edited, moved, or deleted. A seal written into
the archive would itself be the silent edit that decision forbids — AD-073
already states this in its Consequences.

**S-3 — the Phase-0 fixture is not available.** It is immutable Phase-0 data
by its own docstring and by standing convention (a new legitimate file gets a
test-code exclusion clause, never a fixture edit). AD-073 rejected reusing it
as the architecture. That rejection stands.

**S-4 — no same-repo mechanism defeats history rewrite.** A JSON file of
SHA-256 hashes committed to this repository is exactly as rewritable as the
git blobs it describes. This is not a differentiator between the candidate
designs; it is a shared ceiling, and it must be disclosed rather than
designed around — precisely as AD-065 disclosed the same ceiling for chain
anchoring. The 2026-07-21 repository-destruction incident is the empirical
proof: both git objects and any committed hash file were destroyed together.

**S-5 — AD-073 AC-3 bars the seal from git, and the bar is over-broad
relative to its own rationale.** AC-3: *"The seal primitive performs no commit
resolution, no git invocation."* Decision part 5: *"The Archive Seal never
verifies a commit."* The rationale AD-073 gives for that bar is the
stability argument — a freeze result "varies with facts outside the sealed
set," so folding commit binding into a content seal yields "a seal that fails
for reasons that are not integrity failures."

That argument is sound, and it does not reach a blob comparison. Comparing
`research_archive/reference_h4/methodology.md` against
`29553b7:research_archive/reference_h4/methodology.md` has **both sides fixed
at archive close** — exactly the stability property AD-073's own branch table
demands of the Seal row ("Yes — both sides of the comparison are
archive-local"). AD-073 conflated *using git* with *verifying a time-varying
freeze claim*. The invariant it needed is "no time-varying subject," not "no
git." This is the one place where the accepted text must be amended (§7).

---

## 4. Resolving the four candidate answers

The brief asks which of four things the Seal is. All four are answerable now.

**(a) A manifest hash?** — **No.** A hash-of-hashes is an encoding choice
inside a design, not the design. It answers "how do I summarize the seal in
one line," which nothing has asked. Rejected as a category error.

**(b) A protected archive snapshot** (a second, append-only hash fixture
parallel to the Phase-0 one — R-4's own named candidate)? — **No, though it
is the closest rival.** Costs, each concrete:

- It records a second expected content hash for every file that already has
  one in git. AD-073 Decision part 8's stated principle is that *"two
  mechanisms recording an expected hash for the same bytes is the duplicate
  source of truth this architecture exists to avoid."* Part 8 enumerates only
  the fixture and the dataset manifest — it does not name git — but the
  principle reaches git on its face, and a design that survives the letter of
  a rule while breaking its stated reason is the weaker design.
- It needs an issuance component, a schema, and a write authority (AD-062).
- **It is mutable under supersession.** Standard §5 permits a closed archive
  to gain a new, dated superseding artifact — Phase G decision §8 relies on
  exactly that mechanism, and AD-073 Non-goals item 9 leaves the post-Archive
  append question to a future ADR. Every such append forces a *re-issue* of
  the hash list. A governance control that must be rewritten to stay true is
  the weakest shape available for a tamper-evidence control.
- It makes the control CI-owned rather than Governance-owned if it lands in
  `tests/fixtures/`, which is the objection AD-073 already recorded against
  reusing the Phase-0 fixture, and which is not answered by making a second
  copy of it.

**(c) A git reference verification layer?** — **Yes, this is the mechanism.**
It is the only candidate where the expected value is not a new assertion
anyone has to author, store, or maintain: the archived bytes are already
content-addressed, and the seal reduces to naming *which* tree is
authoritative. Under supersession it degrades gracefully — a superseding
artifact produces a *new* sealed commit, appended, and the prior seal remains
a true historical statement rather than a stale one.

**(d) A separate governance artifact?** — **Yes, but a one-line-per-archive
one.** S-1 and S-2 prove the sealing reference cannot live in the chain or the
archive, so a new artifact is unavoidable. What (c) buys is that the artifact
carries **one commit ref per archive** instead of **one hash per file**.

**(c) and (d) are not alternatives — they compose.** The Seal is a *witnessed
commit reference* (the artifact) plus *tree comparison against it* (the
mechanism).

---

## 5. Proposed AD-074 — the minimum viable Seal contract

> **AD-074: The Archive Seal is a witnessed commit reference, verified by
> tree comparison** *(proposed — not accepted)*

**Decision.** A sealed archive is one for which a **sealing commit** has been
recorded in the Archive Seal Register. The Seal branch verifies that every
file in the archive's working-tree directory is byte-identical to the same
path in that commit's tree, and that the two path sets agree.

The six contract questions, answered:

### 5.1 What artifact is sealed?

The archive **directory**, as a set of paths and bytes:
`research_archive/<project_id>/**`, **minus** every path named by that
archive's `dataset_manifest.json` `snapshot_path` entries (AD-073 part 8;
those bytes are `DatasetIntegrityChecker`'s, not the seal's).

Not the manifest, not the chain, not a summary — the tree.

### 5.2 What is the trust boundary?

Stated as what the seal defeats and what it does not. This is the section a
future reader is most likely to over-read, so it is stated as a table.

| Threat | Defeated? | By what |
|---|---|---|
| Accidental mutation (editor, script, bad merge) | **Yes** | Tree comparison, once wired to run |
| Deliberate edit committed normally | **Yes** | The sealing commit predates it; the blob differs |
| File added to a closed archive | **Yes** | Path-set comparison → `unexpected` |
| File deleted from a closed archive | **Yes** | Path-set comparison → `missing` |
| **History rewrite** (`amend`, `filter-repo`, force-push) | **No** | S-4 — no same-repo mechanism can; requires an external anchor |
| Loss of the repository | **No** | Not an integrity control; see 2026-07-21 |

The trust root is **the git object database, as reachable from the recorded
commit**. That root is *stronger* than a committed hash list against threats
1–4 (the comparison side is content-addressed and cannot be altered without
changing the recorded ref) and *identical* to it against threat 5. It is
weaker in exactly one respect: it requires a git working tree, so a tarball
export is `UNVERIFIABLE` rather than verifiable. That is an accurate report,
not a failure.

### 5.3 When is the seal created?

**After** the Decision → Archive record is appended and committed — i.e. the
sealing commit is the commit that first contains the complete closed archive
(`29553b7` for `reference_h4`). S-1 makes any earlier point structurally
impossible.

Issuance is a **human governance act**, recorded, not an automatic
consequence of a transition. It is not a lifecycle transition, holds no
authorization floor, and AD-072 is untouched.

### 5.4 How is it verified?

`ArchiveVerifier`'s Seal branch, unchanged in position: invoked
unconditionally, alongside completeness, reporting under its own vocabulary.
Mechanically:

1. Resolve the archive's `project_id` (read from the working-tree
   `archive_manifest.json` — necessarily so, since no commit is known
   yet at this step; see §7B D1's 2026-07-26 correction). Refuse a legacy
   archive here, before the Register is consulted (AC-74-9) → sealing
   commit from the Register.
2. Confirm `sealed_commit` is a full lowercase object id (§7B D11), that
   the commit object exists and is readable, and that it resolves to
   itself. **Ancestry relative to `HEAD` is not checked** (§7A B-1) —
   `HEAD`'s position must not affect the seal result.
2a. Pin the attribute stack (§7B D7) — including attribute-*source*
   selection, `attr.tree` / `GIT_ATTR_SOURCE` (§7B D7's RF-1 amendment)
   — and refuse what cannot be pinned or what names a live `filter`
   attribute on a compared path (same amendment), since the stack
   governs every hash computed in step 5.
3. Enumerate the archive's paths at that commit, and in the working tree.
   Refuse symlinks and gitlinks on either side (§7B D8), and refuse a
   working-tree reparse point (an NTFS junction as well as a symlink,
   §7B F-3's 2026-07-26 amendment). **The path-set comparison in step 5
   runs over these full sets**; only the content comparison is narrowed
   by step 4.
4. Subtract the dataset-manifest `snapshot_path` set and the
   `protected_file_hashes.json` key set — **both read at the sealing
   commit** (§7B D2, §7B D9) — from the set of paths whose *content* is
   compared.
5. Compare path sets, then compare the intersection per file as **blob
   identities** — `git rev-parse <sealed_commit>:<path>` against
   `git hash-object --path <path> -- <filesystem_path>` — never
   `cat-file blob` against working-tree bytes (§7B D4), and never
   through the git index (**§7B D4's 2026-07-26 amendment**, which
   replaces this step's original `git diff --quiet` mechanism).

Path enumeration in steps 3 and 4 is **NUL-delimited**
(`git ls-tree -r -z <commit> -- <subdir>`, without `--name-only` since
step 3's mode-based symlink/gitlink refusal (§7B D8) needs the mode
field alongside the path and object id — corrected 2026-07-26; the
original text here named `--name-only`, which the implementation moved
away from for exactly that reason), parsed by splitting on `\0` and
decoded as UTF-8 explicitly (§7B D4's amendment, second half).

All git access is read-only and of the same class `freeze_verifier` already
uses (`rev-parse`, `cat-file`, `ls-tree`, `show`) plus `hash-object`, which
without `-w` computes an identity and writes no object, and `check-attr`,
which only reports the attributes already in force (added 2026-07-26,
step 2a's filter refusal) — no new dependency, no new process class, and
no repository mutation.

### 5.5 What evidence is stored? — the Archive Seal Register (C-1…C-4)

One new artifact, one line per sealed archive per issuance:

**C-1 — location and schema.** `docs/archive_seal_register.jsonl` (§A8-C12
grants this its platform-level location) — canonical JSONL, append-only.
Per-record schema:

```json
{
  "schema_version": 1,
  "project_id": "...",
  "sealed_commit": "...",
  "sealed_at": "...",
  "sealed_by": "...",
  "supersedes": null
}
```

`schema_version` is a closed integer, starting at `1`, following the
repository's existing schema-version convention (`archive_manifest.json`,
`dataset_manifest.json`). `supersedes` is `null` for a first-time seal, or the
superseded record's `sealed_commit` when this record re-seals a
`project_id` already present in the Register — the field that makes
supersession attributable (below) rather than merely inferable from record
order.

It lives **outside** `research_archive/`, so S-2 is satisfied and AD-062's
single-writer-per-artifact rule is not touched: this is a new artifact class
with one writer, not a second writer of an existing artifact.

**C-2 — append-only history and supersession semantics.** The Register is
**append-only**: no record is ever edited, reordered, or deleted, and no
implementation may rewrite the file in place. Consequences, stated
explicitly because an implementer will otherwise infer the wrong one:

- **Append-only history.** Every record ever written remains in the file,
  in write order, forever.
- **The latest record for a `project_id`, by file order, governs the
  effective seal.** If a `project_id` appears more than once, the record
  with the highest position in file order (not the highest `sealed_at`,
  which a clock could misreport, and not the lowest `schema_version`) is
  the one `ArchiveVerifier` compares against. Readers must scan to the end,
  not the first match.
- **Previous records remain historical, not authoritative.** A superseded
  record is never deleted and never treated as invalid; it is simply no
  longer the one the seal branch compares against. A reader auditing *when*
  and *why* a project was re-sealed reads the historical records; a reader
  asking *is the archive sound now* reads only the latest.
- **Supersession is attributable, not preventable.** Nothing in this design
  stops a second seal from being issued for the same `project_id` — S-1's
  human-judgment residual (§12) already establishes that issuance is a
  human act the design cannot fully mechanize. What the schema guarantees is
  that a re-seal is never silent: `supersedes` names the prior
  `sealed_commit` explicitly, `sealed_by` names who performed it, and the
  prior record is still readable beside it. The control is honesty about
  supersession, not refusal of it — the same posture AD-062 takes toward
  Standard §5's own supersession allowance.

**C-3 — malformed Register behavior.** Each of the following yields
`UNVERIFIABLE` for the affected archive — never a skipped check, never a
fallback to "unsealed," and never a crash that aborts the rest of
`ArchiveVerifier`'s report:

- a record missing any required field (`schema_version`, `project_id`,
  `sealed_commit`, `sealed_at`, `sealed_by`; `supersedes` is the one field
  allowed to be `null`);
- a record whose `project_id` does not match the archive being verified, or
  is empty, or is not a string;
- a line that is not valid JSON, or a file that cannot be opened or read.

A malformed record for a *different* `project_id` must not make an
*unrelated* archive's seal `UNVERIFIABLE` — a single bad line is a
self-contained parse failure for its own record, not a reason to refuse the
whole file, unless the file itself cannot be read at all (the third bullet),
in which case every archive's seal branch is `UNVERIFIABLE` for that run.

**Amended, 2026-07-26 (Increment 2 integrity audit, items 4 and 5).** Two
gaps in the paragraph above, each of which the first implementation read in
the permissive direction:

- **`schema_version` is enforced, fail-closed.** It is required, must be an
  integer (Python's `bool` is an `int` subclass and is *not* one), and must
  equal the one currently supported value, `1`. `99`, `"wrong"`, and `null`
  were all reaching `MATCHED`. A record declaring a schema this code cannot
  vouch for is `UNVERIFIABLE`; bumping the supported value is a schema
  migration, never a tolerance widening.
- **An unattributable line is positional, not inert.** A line that is not
  valid JSON, is not a JSON object, or carries no non-empty string
  `project_id` cannot be matched to any project — but "cannot be attributed"
  is not "can be ignored." The rule, per project: such lines *before* that
  project's latest record are ignored (a later valid record supersedes
  whatever the bad line might have said); such a line *after* it invalidates
  that project's lookup — `UNVERIFIABLE`, **never a fallback to the earlier
  record**; a project whose own record follows every bad line is unaffected,
  which is what preserves the no-whole-file-refusal rule above for the
  projects it was written to protect. A project with no record at all is
  invalidated by any unattributable line, since nothing rules out that line
  having been its seal. The permissive reading — skip the bad line, use the
  last good one — is at its most dangerous in precisely the case it arises:
  an unreadable append to a project that already has a record is far more
  likely to *be* that project's re-seal than not, because a re-seal is the
  only reason anything is ever appended for such a project.

**Supersession is checked, not merely recorded** (same audit, secondary
item 2). Where a project has more than one record, the latest record's
`supersedes` must name the previous record's `sealed_commit`; where it has
exactly one, `supersedes` must be `null`. Anything else is `UNVERIFIABLE`.
C-2 calls supersession "attributable, not preventable" — a `supersedes`
field that names nothing, or names the wrong commit, makes it neither.

**C-4 — no schema field is added anywhere else.** No schema field is added
to `archive_manifest.json`, `dataset_manifest.json`, or
`transition_records.jsonl`. The Archive Seal Register is the entire evidence
surface this design adds.

### 5.6 What failures map to which status?

The brief asks for `VERIFIED / DRIFTED / UNVERIFIABLE`. Those are
`FreezeStatus`'s values; the Seal branch's own vocabulary under AD-073 is
`MATCHED / MISMATCH / UNVERIFIABLE`, deliberately not merged with the freeze
branch's. The mapping is stated in both vocabularies to make the
correspondence explicit, and the distinct names must be preserved in code.

| Condition | Seal status | (Freeze analogue) |
|---|---|---|
| Every in-scope path present, byte-identical, no extras | `MATCHED` | `VERIFIED` |
| ≥1 file present with different bytes | `MISMATCH`, finding `modified` | `DRIFTED` |
| ≥1 file in the sealed tree, absent from the working tree | `MISMATCH`, finding `missing` | `DRIFTED` |
| ≥1 file in the working tree, absent from the sealed tree | `MISMATCH`, finding `unexpected` | `DRIFTED` |
| No Register record for this archive | `UNVERIFIABLE` | `UNVERIFIABLE` |
| Register malformed, or record malformed | `UNVERIFIABLE` | `UNVERIFIABLE` |
| Sealing commit unresolvable, or its tree unreadable | `UNVERIFIABLE` | `UNVERIFIABLE` |
| Not a git working tree (`NotAGitRepositoryError`) | `UNVERIFIABLE` | `UNVERIFIABLE` |
| `dataset_manifest.json` unreadable → exclusion set underivable | `UNVERIFIABLE` | — |
| `snapshot_path` escaping `dataset_hashes/` *(§7B D9)* | `UNVERIFIABLE` | — |
| `protected_file_hashes.json` present but unreadable at the sealing commit *(§7B D9)* | `UNVERIFIABLE` | — |
| Legacy archive (the named three, or `lifecycle_version: "legacy"`) | `UNVERIFIABLE`, never sealed | — |
| `sealed_commit` not a full lowercase object id *(§7B D11)* | `UNVERIFIABLE` | — |
| `.git/info/attributes` present, or `.gitattributes` drifted since the seal *(§7B D7)* | `UNVERIFIABLE` | — |
| A `filter` attribute applies to a compared path *(§7B D7)* | `UNVERIFIABLE` | — |
| A symlink or gitlink is in scope *(§7B D8)* | `UNVERIFIABLE` | — |
| Register not canonical JSONL (CRLF, no trailing newline) *(§7B D12)* | `UNVERIFIABLE`, whole file | — |

**Withdrawn 2026-07-26 (§7B D10): "Archive's cycle not closed (AC-15) →
`UNVERIFIABLE`".** The Seal branch makes no closure judgement; AD-073
AC-15 is amended in `ARCHITECTURE_DECISIONS.md` accordingly.
`transition_records.jsonl` is a working-tree file, and every input to
this comparison is fixed at the sealing commit. The report-level
guarantee is unchanged — the completeness branch still reports an
unclosed cycle `UNVERIFIABLE`, and `overall_status` is derived from it.

The last two rows are the ones an implementer is most likely to get wrong.
A seal that cannot derive its own exclusion set must **not** fall back to
sealing everything — that would silently violate AC-11. And a legacy archive
is `UNVERIFIABLE` on the seal branch even though it is `EXEMPT` on the
completeness branch: the two branches keep their own vocabularies, and
"exempt from a layout check" is not "sealed."

`SealReport` should additionally carry the **excluded path set**, so that
bounded coverage is auditable from the report rather than inferred. Coverage
that a reader cannot see is coverage a reader cannot trust.

**Clarified, 2026-07-26 (Increment 2 integrity audit, secondary item 4):**
that set reports only paths within **this archive's own comparison domain**
— everything under `research_archive/<project_id>/`. `protected_file_hashes.json`
names ~36 platform files, most never under `research_archive/` at all;
listing them described the fixture rather than this seal's bounded coverage,
which is the one thing the field exists to make auditable. The comparison
itself is unaffected: both path sets contain only paths under that prefix,
so an out-of-domain exclusion subtracts nothing either way.

---

## 6. Why not simply verify against `HEAD`, or against nothing?

Recorded for completeness, because both are cheaper and both are wrong.

- ***Compare the working tree against `HEAD`.*** Rejected: it detects only
  *uncommitted* mutation. A committed edit reads as clean, which is threat 2 —
  the one that matters.
- ***Treat "the archive is in git" as sufficient.*** Rejected: it is exactly
  the claim Phase G decision §8 already refused, "immutable as a matter of
  governance and unprotected as a matter of mechanism." Git holds the
  evidence; nothing compares against it. The Register is the missing half.

---

## 7. Amendment surface — the explicit AD-073 and A8-C1 amendment list

AD-074 does not stand on an unstated "no other AD-073 text changes." Four
narrow amendments are required, each stated here as the exact text at issue,
each also applied inline in `ARCHITECTURE_DECISIONS.md` — this section
cross-references that document rather than restating it as the authority.
Where this section's prose and that document's amended text differ, the
amended AD-073 text governs.

**A-1 — no unstated blanket claim.** The prior draft of this section said
"No other AD-073 text changes" without enumerating what *did* change. That
sentence is withdrawn. §§A-2 through A-5 below are the complete list; §A-6
records where each is actually applied.

**A-2 — Responsibilities: the Archive Seal no longer "never resolves git
references."** AD-073's Responsibilities section bars the seal from "verify
any commit, resolve any git reference, or observe repository state." That bar
is replaced by one scoped to *freeze-claim verification* and *time-varying*
repository state — the distinction §3 S-5 shows AD-073's own rationale
actually needs:

- `FreezeVerifier` verifies **freeze claims** — a live, time-varying fact
  about the repository right now, per AD-033/AD-047/AD-051.
- The Archive Seal verifies **the tree state at a fixed sealing commit** — an
  archive-local, stable-once-recorded fact.
- The Archive Seal does not perform freeze verification, does not call
  `verify_freeze()`, and does not absorb any part of `FreezeVerifier`'s role;
  reading a git object at a commit already fixed at archive close is a read,
  not a verification of a claim.

**A-3 — Decision part 5: "the Archive Seal never verifies a commit" is
replaced.** The replacement text permits: reading git objects at a fixed
recorded commit; without observing live repository state; without replacing
any part of `FreezeVerifier`'s responsibility. Exact replacement, applied to
Decision part 5's last sentence and to AC-3's first clause alike:

> The seal primitive performs no freeze-claim verification, resolves no
> freeze commit reference, observes no time-varying repository state, and
> makes no Standard §5 completeness judgment. It may read git objects at a
> commit fixed at archive close, where both sides of the comparison are
> archive-local and stable, and it never invokes `verify_freeze()`,
> `verify_chain_intact()`, or `verify_chain_anchored()`.

This preserves every invariant AD-073's rationale actually relies on — the
subject distinction, the stability property, the no-chain-authority rule, the
single-entry-point rule — and removes only the over-broad "no git invocation"
phrasing that §3 S-5 shows was never load-bearing.

**A-4 — status vocabulary and the Architecture overview table: "sealed
manifest" is replaced.** Wherever AD-073's Status vocabulary (the Archive
Seal branch's `MATCHED`/`MISMATCH`/`UNVERIFIABLE` definitions) and the
Architecture overview's three-branch table name what the seal compares
against, "a sealed manifest" is replaced with "the sealing commit tree
identified by an Archive Seal Register record." AD-074 §5 is what resolves
AD-073's own Non-goals item 1 (seal issuance, format undecided): the expected
value was never going to be an authored manifest once §4(c) settled the
question, and the vocabulary now says so. Other occurrences of "sealed
manifest" remaining in AD-073's own Non-goals, Migration, and Future-work
prose describe the state *at AD-073's original acceptance* and are
superseded by this design, not individually rewritten.

**A-5 — A8-C1 amendment: why the Archive Seal Register is the first allowed
platform-level governance machine artifact.** Recorded at **A8-C12** in
`ARCHITECTURE_DECISIONS.md`'s A-8 section, the owning decision document for
A8-C1, not only here. Reason, in full:

1. **Per-cycle location is impossible, not merely inconvenient.** §3 S-1: the
   sealing commit is the commit that *first contains the complete closed
   archive*. A record naming that commit cannot be written before the commit
   exists, and so cannot live inside the archive directory the commit itself
   seals without either being absent from the sealed tree or requiring a
   second, later mutation of a directory Phase G's remediation decision §8
   already holds immutable. A8-C1's per-cycle rule cannot be satisfied by
   construction here, in the specific way it can be satisfied everywhere else
   (`transition_records.jsonl`, A8-C2).
2. **A8-C8 forecloses the obvious alternative.** "No new top-level directory,
   and nothing outside the repository" rules out a fresh location like
   `governance_records/` for the Register.
3. **Therefore the exception is justified.** Between A8-C1 (no platform-level
   machine artifact) and A8-C8 (no new top-level directory), the only
   location satisfying both is the existing platform-level tier —
   `docs/` — with the Register as the first machine-written, machine-read
   artifact placed there. This is a named, narrow exception to A8-C1, not a
   repeal of it, and it licenses nothing else by analogy (A8-C12's own
   closing paragraph).

**A-6 — where each amendment is actually applied.** This section states the
amendments; it does not carry them. The governing text is in
`ARCHITECTURE_DECISIONS.md`:

| Amendment | Applied to | Section |
|---|---|---|
| A-2, A-3 | AD-073 Responsibilities ("does not" list), Decision part 5, AC-3 | `ARCHITECTURE_DECISIONS.md`, inline, dated 2026-07-26 |
| A-4 | AD-073 Status vocabulary (Archive Seal branch bullet), Architecture overview table | `ARCHITECTURE_DECISIONS.md`, inline, dated 2026-07-26 |
| A-5 | A8-C1 | `ARCHITECTURE_DECISIONS.md`, new **A8-C12**, A-8 section |

**Nothing else changes.** Decision parts 1, 2, 3, 4, 6, 7, 8 stand; the
branch table's other two rows stand; the aggregation rule stands; AC-1, AC-2,
and AC-4…AC-17 stand. AC-11 is *satisfied more strongly* than before (§2
O-3).

**Alternative if the amendment is refused:** fall back to candidate (b) — a
per-file SHA-256 register, same location, same append-only property, same
Register-record shape plus a `files` map. Everything else in AD-074 is
unchanged; only §5.4 step 5 changes from "compare against the blob" to
"compare against the recorded hash." That fallback is strictly worse for the
reasons in §4(b), but it is a complete design and it requires no AD-073
amendment at all. **This is a genuine fork the accepting authority should
decide explicitly, not a rhetorical alternative.**

---

## 7A. Resolved internal contradictions (B-1, B-2)

**B-1 — AC-3/§5.2's "no time-varying repository state" vs. §5.4 step 2's
ancestry-of-`HEAD` check.** The original draft said both "no time-varying
repository state" (§5.2, and now A-3's amended AC-3) and, in the same design,
required the sealing commit to be "an ancestor of `HEAD`" (§5.4 step 2,
§5.6). Those two statements conflict: whether a given commit is an ancestor
of `HEAD` is itself a time-varying repository fact — it depends on where
`HEAD` currently points, which changes on every commit, merge, and branch
checkout, on a schedule that has nothing to do with whether the archived
bytes changed.

**Resolution chosen: remove the ancestry-of-`HEAD` requirement.** §5.4 step 2
and the §5.6 table row are amended above to:

- the commit object must exist and be readable;
- ancestry is not checked;
- `HEAD`'s position must not affect the seal result.

**Why.** Ancestry-of-`HEAD` answers a question about repository *topology at
the moment of the call* — the same kind of fact `FreezeVerifier` exists to
answer (Q3), not the kind the seal exists to answer (Q2). A sealing commit
that is a perfectly good, permanently reachable reference does not stop being
one merely because `HEAD` has since moved along a branch that no longer
descends from it — a topology fact, not a content-integrity fact. Requiring
ancestry would make the seal's result a function of the current branch's
shape, which is exactly the failure mode A-3's amended AC-3 exists to
prevent, applied one clause too narrowly in the original draft. Dropping the
check also removes a redundant gate rather than a real one: an unreachable
sealing commit is already `UNVERIFIABLE` under **D3** (git durability) — the
commit-resolution step (§5.4 step 1, "resolve … from the Register") already
fails first if the commit cannot be found at all, so the ancestry check was
never doing work the durability rule does not already do, only work that
introduced the contradiction.

**B-2 — dataset-hash exclusion: coverage boundary, not duplicate-hash
avoidance.** Two statements elsewhere in this review are in tension read
together: §5.1 excludes `dataset_manifest.json` `snapshot_path` entries
citing AD-073 Decision part 8 (the one-authoritative-hash-record rule), which
reads as "excluded to avoid a duplicate hash record" — while §12's
adversarial self-review states the seal itself "is a tree comparison, not a
hash record," which reads as "the seal produces no hash record at all, so
nothing is actually duplicated by including those files."

**Resolution chosen — the preferred explanation, stated once and used
throughout:** the dataset-hash exclusion exists because **AD-073's coverage
boundary excludes those files**, not because sealing them would create a
duplicate hash record. AD-073 Decision part 8 assigns
`dataset_hashes/*.jsonl` (and any other file `dataset_manifest.json`
describes by `content_hash`) to `DatasetIntegrityChecker`'s domain by naming
a single authoritative content-hash record per file; §5.1's exclusion
implements that domain assignment. It is **not** grounded in an
avoid-duplication argument, and it must not be described as one: the Archive
Seal's mechanism is a tree comparison, which asserts no hash of its own and
so duplicates nothing in the specific sense Decision part 8 targets ("two
mechanisms recording an expected hash for the same bytes"). Were the seal's
mechanism ever changed to a recorded hash (§7's fallback, candidate (b)),
*that* design would need the duplication argument — and would then actually
need to exclude the dataset-hash files for that reason, on top of the
coverage-boundary reason, which is why the fallback in §7 keeps the same
exclusion set unchanged. Under the design this review actually proposes
(candidate (c)+(d)), the coverage-boundary reason is the only one that
applies, and §12's self-review is corrected to state this rather than imply
duplication-avoidance.

---

## 7B. Hidden assumptions (D1–D12)

*(Heading range corrected 2026-07-26 at acceptance: it read "D1–D6" while
the section had held D1–D12 since the Increment 2 hardening pass added
D7–D12.)* **Order of items, stated because it is not sequential and is
deliberately left alone:** D1, D2, D3, D4, then the hardening pass's
D7, D8 (with its Windows follow-up **F-3**), D9, D10, D11, D12, then the
original D5 and D6 last. D7–D12 were appended where the pass wrote them
rather than interleaved, and D5/D6 are not renumbered or moved, because
every cross-reference elsewhere in this document and in
`core/governance/archive_seal.py` cites these items by label. **F-3** is
a label local to this section; `ARCHITECTURE_DECISIONS.md`'s AD-073 entry
carries an unrelated **F-3** from the 2026-07-25 correction pass, and its
item 11 already records that collision.

**D1 — project ID resolution.** `project_id` comes only from
`archive_manifest.json`'s own `project_id` field. It is never taken from:
the archive directory's name (even though A8-C6 requires the two to be
byte-identical at write time — the seal does not lean on that invariant
holding, because nothing re-checks it after issuance); `HEAD` or any other
live git state; or any field of `transition_records.jsonl`. A missing
`archive_manifest.json`, or a manifest present but missing `project_id`,
yields `UNVERIFIABLE` — never a fallback to the directory name, which would
silently paper over exactly the manifest/directory divergence A-6 R-2
already declined to mechanize

**Corrected, 2026-07-26** (governance hardening pass, against the shipped
`core/governance/archive_seal.py`). The original sentence above read
"read at the sealing commit (D2)" — that is wrong, and the parenthetical
cross-reference to D2 is what caused the error: D2 states that rule for
the *dataset-manifest exclusion set* (§5.4 step 4), a genuinely different
input read at a point in the algorithm where the sealing commit is
already known. D1's own input is read at §5.4 **step 1**, before the
sealing commit is known at all — the Register lookup this step performs
is keyed *by* `project_id` (`project_id → sealed_commit`), so resolving
`project_id` from the sealing commit would require already knowing the
sealing commit to look up the `project_id` used to find it. "Read at the
sealing commit" is not merely unimplemented for D1; it describes a
lookup sequence with no valid starting point.

The implementation (`_read_archive_identity`,
`core/governance/archive_seal.py` — *symbol name corrected 2026-07-26 at
acceptance; no such function as `_read_project_id` exists, and the
function that does this work also reads `lifecycle_version` for the
legacy refusal AC-74-9 requires, which is why it is named for the
identity rather than for the one field*)
resolves `project_id` from the **working-tree** copy of
`archive_manifest.json` at `archive_dir` — the only copy available before
any commit is known — and this is the corrected rule, not merely the
implementation's own workaround: **D1 lookup sequence, stated explicitly.**

1. Read `project_id` from the working-tree `archive_manifest.json` at
   `archive_dir`. (Absent or unparseable → `UNVERIFIABLE`, per the
   paragraph above — unchanged.)
2. Look up that `project_id`'s latest record in the Archive Seal Register
   → `sealed_commit` (§5.4 step 1, C-2's "latest by file order" rule).
3. Every subsequent read — the dataset-manifest exclusion set (D2), the
   sealed tree's path enumeration, the per-file blob-identity comparison
   (D4's 2026-07-26 amendment; the original text here said "`git diff`",
   which that amendment replaced — *corrected 2026-07-26 at acceptance*)
   — is anchored to `sealed_commit`, resolved in step 2, never to the
   working tree again.

This does not weaken the trust boundary D1's opening paragraph states,
for a reason worth making explicit rather than merely asserted: a working
tree `project_id` edited to name a *different* project's Register record
does not launder a tampered archive to `MATCHED`. `_sealed_tree_entries`
(*symbol name corrected 2026-07-26 at acceptance; `_ls_tree_paths` does
not exist, and the shipped function returns `{path: (mode, object_id)}`
rather than a bare path set, because D8's symlink/gitlink refusal needs
the mode*) and
the working-tree walk in `verify_seal` (`_working_tree_entries`) are both
scoped to
`archive_relative_prefix` — `archive_dir`'s own repository-relative path,
independent of whatever `project_id` resolved to — so a mismatched
lookup finds the *wrong project's* files (or none) at `sealed_commit`
under *this* archive's path and reports `mismatch` (every file
`"unexpected"`) or `unverifiable`, never a false `matched`. A forged
`project_id` can misroute the Register lookup; it cannot make the
byte-comparison step 3 performs agree with tampered content, because
that step never reads `project_id` again once `sealed_commit` is fixed.
(`ARCHITECTURE_DECISIONS.md` A8-C11).

**D2 — dataset exclusion source.** The exclusion set (§5.1, §5.4 step 4) is
derived from `dataset_manifest.json`'s `snapshot_path` entries **as they
read at the sealing commit** — never from the working tree's current copy
of `dataset_manifest.json`. Reading the working-tree copy would make the
seal's own scope a time-varying fact: a change to `dataset_manifest.json`
after archive close (legitimate under Standard §5's supersession allowance)
could silently widen or narrow what the seal compares, without the sealing
commit changing at all. Reading it at the sealing commit keeps the
exclusion set itself archive-local and fixed, matching every other input
to the comparison (§5.2). An unreadable or malformed
`dataset_manifest.json` at the sealing commit yields `UNVERIFIABLE`
(§5.6), exactly as already stated; D2 only fixes *which copy* is read.

**D3 — git durability limitation.** The seal depends on the sealing commit
remaining reachable in the repository's object graph. This is S-4's ceiling
made concrete: normal, entirely legitimate git workflows can make a
previously-`MATCHED` seal `UNVERIFIABLE` with no archived byte having
changed —

- a **squash merge** that folds the sealing commit's history into a single
  new commit, leaving the original commit hash unreachable from any branch;
- a **rebase merge** that rewrites the commits following the sealing commit,
  or the sealing commit itself, onto a new base;
- **branch deletion followed by garbage collection**, once no ref retains
  the commit and git's reflog expiry has passed;
- a **shallow clone**, where the sealing commit predates the clone's depth
  and was never fetched at all.

This is a **known tradeoff against a file hash register** (candidate (b)),
disclosed rather than designed around, exactly as S-4 requires: a hash
register survives all four cases because it does not depend on git history
shape, at the cost of being a second recorded hash for bytes git already
content-addresses (§4(b)). The seal trades that resilience for avoiding a
duplicate source of truth. `UNVERIFIABLE` under any of these four cases is
an accurate report of "cannot currently verify," not a false `MISMATCH` —
the design must never conflate "unreachable" with "modified."

**D4 — CRLF / normalization correctness.** Wherever this review's earlier
prose said "compare bytes" (§5.4 step 5), the mechanism is **not** a raw
byte comparison. It is the same normalization-aware mechanism
`freeze_verifier.py` already uses (`_content_matches`,
`freeze_verifier.py:128–130`):

```
git diff --quiet <sealed_commit> -- <path>
```

This is explicitly **not**:

```
git cat-file blob <sealed_commit>:<path>   # compared against working-tree bytes
```

**Reason, verified against this repository's own configuration:**
`core.autocrlf` is `true` (`git config core.autocrlf`), and
`.gitattributes` reads `*.jsonl -text` — it exempts only `.jsonl` files from
autocrlf's line-ending conversion, precisely so canonical JSONL and
content-hashed governance artifacts stay byte-exact across checkout
(`.gitattributes`'s own comment). Every other tracked file
(`.md`, `.py`, `.json`, `.csv`, …) is **still subject to `core.autocrlf`'s
conversion** on checkout. `git cat-file blob` returns the object's stored
bytes with no such conversion applied; a working-tree file checked out
under `core.autocrlf=true` can differ from its own blob by line endings
alone. Comparing those two directly would report `modified` for files whose
content is unchanged — a false `MISMATCH` from a checkout artifact, not an
integrity failure. A comparison mechanism must therefore apply the
repository's configured clean/smudge filters to both sides before
comparing, exactly as `freeze_verifier.py` already relies on for the
identical reason. Any implementation that reaches for `cat-file` to
"avoid the overhead of diff" must not do so.

**Amended, 2026-07-26 (Increment 2 integrity audit, items 1 and 2). The
mechanism is a blob-identity comparison, not `git diff`.** The original
text above named `git diff --quiet <sealed_commit> -- <path>` as the
mechanism, on the strength of its filter handling. That reasoning was
right about filters and wrong about the *subject*: `git diff` reaches the
working-tree side **through the index**, so the comparison it performs is
not "sealed commit tree ↔ archive filesystem" (§5.2's own statement of
what the seal compares) but "sealed commit tree ↔ index-mediated view of
the filesystem." The index is neither side of the seal's claim, and it is
trivially and *legitimately* manipulable:

- `git update-index --assume-unchanged <path>` makes `diff` report a
  tampered archive file **clean** — a false `MATCHED`, defeating threats
  1 and 2 of §5.2's table with one plumbing command that leaves no trace
  in any committed artifact;
- `git rm --cached <path>` (or any operation leaving the file untracked
  with identical bytes on disk) makes `diff` report an untouched file
  **modified** — a false `MISMATCH`, the failure mode §7B D3 insists must
  never be conflated with a real one.

The replacement compares the two sides directly as blob identities:
`git rev-parse <sealed_commit>:<path>` reads the sealed tree, and
`git hash-object --path <path> -- <filesystem_path>` hashes the on-disk
file. **The filter argument above is fully preserved**, which is why
`--path` is passed: `hash-object --path` applies exactly the attributes
and clean filters configured for that path, so a CRLF working-tree
checkout of an LF blob hashes back to that blob under
`core.autocrlf=true`, and `.gitattributes`'s `*.jsonl -text` exemption is
honoured identically. D4's actual bar — never compare `cat-file blob`
output against raw working-tree bytes — is unchanged and still binding;
`cat-file` applies no filters and is used here for nothing.

**Path enumeration is NUL-delimited for the same class of reason (audit
item 2).** `git ls-tree -r --name-only` *quotes* any path outside a
conservative ASCII set — an archive file named `résumé.md` is emitted as
`"r\303\251sum\303\251.md"` — and a quoted name matches nothing in the
working-tree walk, so a sound archive containing one non-ASCII filename
reports that file as both `missing` and `unexpected`. `-z` emits the
stored bytes verbatim, with no quoting and no escaping, regardless of
`core.quotepath`; the result is split on `\0` and decoded as UTF-8
explicitly, never by the ambient locale encoding (which on Windows is a
legacy code page).

**D7 — the attribute stack is a third input to the comparison, and it
was live state.** *(Added 2026-07-26, Increment 2 governance hardening
pass.)* D4 established that the comparison must be normalization-aware
and settled on `git hash-object --path` for the working-tree side,
precisely because `--path` applies the attributes configured for that
path. What D4 did not state is the consequence: **the attribute stack is
therefore an input to the seal result**, alongside the sealing commit and
the archive's bytes — and every part of it was live working-tree or
machine state, none of it fixed at the sealing commit, none of it visible
in the Register.

There are **five possible attribute influences, including
`attr.tree`/`GIT_ATTR_SOURCE` attribute-source selection** — four
stacked attribute *files*, plus the knob that decides which tree the
fourth is read from at all. Each is now pinned, by a different
mechanism, because git offers no single switch:

| Influence | Disposition | Why |
|---|---|---|
| System (`$(prefix)/etc/gitattributes`) | Disabled — `GIT_ATTR_NOSYSTEM=1` on every invocation | Machine state, outside the repository entirely |
| Global/user (`core.attributesFile`) | Disabled — `-c core.attributesFile=` on every invocation | Per-developer state; **[verified]** a global file assigning `*.dat filter=evil` reports `filter: evil` without the override and `filter: unspecified` with it |
| `$GIT_COMMON_DIR/info/attributes` | **Refused** — its existence is `UNVERIFIABLE` | **[verified]** not overridable by any config or environment variable; per-clone and never committed, so a seal depending on it depends on a file no diff will ever show |
| `.gitattributes`, per directory root→path | **Verified** blob-for-blob against the sealing commit | It is committed, so it *can* be verified; a post-seal edit is a change to the comparison's own rules |
| **Attribute-source selection** — `attr.tree` (config) and `GIT_ATTR_SOURCE` (environment), git ≥2.40 | Disabled — `-c attr.tree=` on every invocation **and** `GIT_ATTR_SOURCE` removed from the environment | *(Added 2026-07-26, acceptance-audit finding RF-1.)* Selects **which tree** the row above is read from, so setting it makes that row's verification vacuous |

**RF-1 — the source stack was not fully pinned.** *(Added 2026-07-26,
AD-074 Increment 2 acceptance audit.)* The four-row model above was
complete for git <2.40 and stopped being complete when `attr.tree` and
`GIT_ATTR_SOURCE` were introduced. Neither adds a rule; both redirect
attribute lookup to an arbitrary tree. Pointing either at a tree
containing no `.gitattributes` strips every attribute the comparison
depends on — and because the `.gitattributes` row is verified against
the sealing commit *by content*, not by whether it is consulted, that
verification passes while having no effect.

**[verified, end to end, before and after]** With the repository's
committed `*.jsonl -text` in force, a `transition_records.jsonl`
rewritten to CRLF is a genuine content change and reports `MISMATCH`.
With `GIT_ATTR_SOURCE` pointed at an empty tree, the same tampered file
hashes back to *exactly* its sealed blob and the archive reports
`MATCHED`. The same holds for `attr.tree` set in config. Both are now
regression-tested against the bypass itself, not against a status.

**The two are neutralised by different mechanisms, and the ordering is
load-bearing.** `GIT_ATTR_SOURCE` **overrides** `attr.tree`, so the
config pin alone leaves the bypass fully open — **[verified]**: with the
variable set and `-c attr.tree=` in force, the tampered file still
hashes to the sealed blob. The variable is therefore *removed from the
environment* of every invocation rather than set to any value. Nor does
the environment scrub suffice alone: `attr.tree` can be set in
repository, global, or system config, or injected through `GIT_CONFIG_*`
— none of which appears in any artifact this design verifies.

Pinning the stack still leaves one live input, and it is the sharpest
one: a `filter` attribute names a driver, but the driver's
`filter.<name>.clean` command lives in git **config**, not in any
attributes file. That command is arbitrary code run over the working-tree
bytes before they are hashed — it can make a tampered file hash to the
sealed blob, with no verified artifact touched. This is not hypothetical:
`filter.lfs.clean` is present in ordinary developer global config
**[verified on the machine this pass was performed on]**. A `filter`
attribute applying to any compared path is therefore **refused**
outright. This repository's `.gitattributes` assigns none, so the refusal
costs nothing today and closes the hole permanently.

Two live inputs are deliberately **not** pinned: `core.autocrlf` and
`core.eol`. They are what make the comparison normalization-aware at all,
and pinning them would reintroduce exactly the false `MISMATCH` on a CRLF
checkout that D4 exists to prevent.

**The remaining guarantee, stated precisely (corrected 2026-07-26,
acceptance-audit finding W-1).** The claim that these two "cannot make
differing content hash alike" is **false as originally stated, and is
withdrawn**: flipping `core.autocrlf` *can* make two byte-sequences that
differ only in line-ending style (`\n` vs `\r\n`) hash alike, on any path
where line-ending normalization applies at all — that is exactly what
"normalization-aware" means, and doing it is a config change, not a
preimage attack. **[verified]** an LF-sealed, non-`-text` file rewritten
to CRLF hashes back to its sealed blob under `core.autocrlf=true` and
does not under `core.autocrlf=false` — a genuine `MISMATCH → MATCHED`
transition driven by nothing but this config value.

What actually protects the archive is `.gitattributes`'s own `*.jsonl
-text` — not the claim above. `-text` disables line-ending normalization
for that path outright, so `core.autocrlf`/`core.eol` have no effect on
it at all, pinned or not, and the CRLF/LF collision above cannot reach
it; §7B D4 (above, lines 801–817) already establishes that every
content-hashed governance artifact on this platform is `-text` for
exactly this reason. For a path that is *not* `-text` (`.md`, `.py`,
`.json`), the two live inputs remain exactly as originally described —
sound to leave live, because flipping one can turn a true `MATCHED` into
a false `MISMATCH` (fail-loud, never conflated with tampering, D3) — but
the same flip can *also* collapse a line-ending-only tamper of such a
file into `MATCHED`, symmetrically. That residual is accepted, not
closed: it is the cost of D4's normalization tolerance, bounded to
line-ending bytes only, and it is why byte-exactness for any
Seal-relevant artifact must be asserted with `-text`, never assumed from
file type or from this paragraph's original, overstated claim.

**D8 — symlinks and gitlinks are refused, not compared.** *(Added
2026-07-26, same pass.)* Blob-identity comparison is defined for regular
files. A symlink's blob is its *target path string*, not the target's
content, and a gitlink (mode `160000`) is a commit id belonging to
another repository this design never reads. The superseded implementation
enumerated the working tree with `Path.is_file()`, which **resolves**
symlinks: a symlink was hashed as its target's content, and a symlinked
directory was descended into as though its contents were the archive's
own — in both cases reporting on bytes that are not at the path the seal
claims to compare.

Both sides are now checked for shape: tree entries whose mode is not
`100644`/`100755`, and any working-tree symlink under the archive, yield
`UNVERIFIABLE` with an explicit reason. This is a **disclosed
limitation, not a guarantee**: the seal does not say symlinked archives
are sound or unsound, it says it cannot answer for them. No archive on
this platform contains one today.

**F-3 — the working-tree half of this was platform-shaped.** *(Added
2026-07-26, AD-074 Increment 2 acceptance audit.)* The refusal was
implemented with `Path.is_symlink()`, which reports **False** for a
Windows NTFS **junction** — a reparse point that redirects a directory.
`os.walk(followlinks=False)` does not help either: it suppresses descent
into *symlinked* directories only. So on Windows the walk descended into
junctions and reported the target directory's files as the archive's own
— the exact defect D8 closed for symlinks, left open on the one platform
where it is **more** reachable, since creating a junction requires no
privilege while creating a symlink requires Developer Mode or elevation.
**[verified]**: before the fix, a junction planted in a sealed archive
produced `MISMATCH` with an `unexpected` finding naming a file outside
the archive entirely; after it, `UNVERIFIABLE`.

Detection is now "symlink **or** reparse point" (`os.path.isjunction`,
with an `st_file_attributes`/`FILE_ATTRIBUTE_REPARSE_POINT` fallback for
interpreters predating it). Existing symlink behaviour is unchanged — the
symlink test runs first — and the change only ever *adds* refusals, so it
can convert a wrong `MATCHED`/`MISMATCH` into `UNVERIFIABLE` and never
the reverse.

**D9 — `protected_file_hashes.json` is read at the sealing commit, for
the identical reason D2 gives for `dataset_manifest.json`.** *(Added
2026-07-26, same pass.)* The first implementation read the working-tree
copy, reasoning that the fixture is immutable Phase-0 data by convention
and so has no "which copy" ambiguity. **A convention is not a trust
boundary.** This file controls *what the Seal declines to check*, so
whoever can write it can exempt any archive path from verification:
appending `{"research_archive/<project>/methodology.md": "…"}` after
issuance turns a tampered archive into `MATCHED`, with no commit, no
Register record, and nothing for a reviewer to see. That is precisely the
failure D2 closed for the other exclusion source, left open on this one
because immutability-by-convention was believed to substitute for it.

Both exclusion sources are now fixed at the sealing commit, so the seal's
scope is a property of that commit and of nothing else. The fail-closed
shapes differ, deliberately:

- **absent at the sealing commit → exclude nothing.** This is a *derived*
  answer (the fixture named no paths then), not an underivable one, and
  the comparison that follows is strictly **wider**, so nothing escapes
  the seal.
- **present but unreadable → `UNVERIFIABLE`.** Genuinely underivable.

D2's rule for `dataset_manifest.json` is `UNVERIFIABLE` in *both* cases
because AC-74-5 fixes it that way and because that manifest is a required
item of every v1 archive, so its absence at the sealing commit is itself
evidence something is wrong. The Phase-0 fixture is a platform file under
no such per-archive requirement.

**`snapshot_path` containment** belongs to the same finding. Every
exclusion is a file the Seal will not check, so the exclusion set is a
**privilege**, and an unvalidated `snapshot_path` hands that privilege to
whatever the manifest says: `../decision_log.md` would drop a governance
artifact out of the comparison entirely. §5.1's exclusion is therefore
narrowed — each `snapshot_path` must be a relative path resolving
strictly inside `dataset_hashes/` (no `..`, no `.`, no absolute path, no
backslash or drive letter), checked **lexically**, since a rule that
consulted the live filesystem would reintroduce the time-varying input D2
removed. Anything else makes the exclusion set underivable →
`UNVERIFIABLE`. Reading the manifest at the sealing commit means only a
party who controls that commit can attempt this; a control whose
integrity depends on the trustworthiness of the thing it verifies is not
a control.

**D10 — the Seal makes no lifecycle-closure judgement; AD-073 AC-15 is
amended.** *(Added 2026-07-26, same pass.)* §5.6's table carried a row
"Archive's cycle not closed (AC-15) → `UNVERIFIABLE`", and AD-073 AC-15
required the completeness branch and the Seal branch to **both** read
`transition_records.jsonl`'s terminal record. The implementation reads it
in the completeness branch only. That is a specification/code
contradiction, and it is resolved in the **code's** favour: **the §5.6
row is withdrawn**, and AD-073 AC-15 is amended in
`ARCHITECTURE_DECISIONS.md` (Status, item 7 — the owning document, per
§7's own discipline).

The deciding argument is this pass's own: `transition_records.jsonl` is a
**working-tree** file. Making the Seal's answer depend on it would add a
live, post-seal-editable input to a comparison whose every other input
this pass just pinned to the sealing commit — the exact defect class
D7/D9 exist to remove, reintroduced by an acceptance criterion. AC-15's
user-visible guarantee is unaffected (an unclosed cycle already reports
`UNVERIFIABLE` through the completeness branch, and `overall_status` is
derived), and AD-074 supplies a **stronger** structural guard than a
closure read: an unclosed cycle has no Register record, because issuance
follows the Decision → Archive commit (§5.3). AC-15's original phrasing
predates AD-074; it was written when the Seal's expected value was an
unspecified "sealed manifest" with no issuance discipline, and a closure
read was the only guard available.

**D11 — the sealing commit must be a fixed object id.** *(Added
2026-07-26, same pass.)* C-1 specifies a `sealed_commit` field without
constraining its form, and the first implementation resolved it with
`git cat-file -e <commit>^{commit}` — which accepts `HEAD`, a branch
name, a tag, and an abbreviated hash. Each defeats the fixed-point
premise §5.2 rests on ("both sides fixed at archive close"):

- **`HEAD` or a branch name** resolves to whatever that ref points at
  *now*. A seal recorded against `master` re-derives its own expected
  value on every call: it verifies the archive against whatever the
  branch currently says the archive should contain, and can never detect
  a committed edit — **threat 2 of §5.2's table, the one that matters**.
  It is also exactly the "compare the working tree against `HEAD`" design
  §6 records as considered and rejected, reached through *data* rather
  than through code.
- **A tag** is a movable, deletable ref.
- **An abbreviated hash** is a prefix, not an identity: it names one
  object today and can become ambiguous as the object database grows, at
  which point the same record resolves differently, or stops resolving,
  with no record having changed.

C-1 is therefore narrowed: `sealed_commit` is a **full-length lowercase
hexadecimal object id** (40 for SHA-1, 64 for SHA-256). Lowercase is
*required*, not merely accepted, because `supersedes` chaining compares
these strings for equality — two spellings of one commit would silently
break a chain this reader is otherwise obliged to verify. Validation is
syntactic and precedes any resolution attempt, so a repository carrying a
branch literally named `HEAD` cannot make it pass. A second, independent
check closes the residual the syntactic one cannot: the resolved id is
compared against the recorded string, and a mismatch is `UNVERIFIABLE`.

**The residual case, corrected.** *(2026-07-26, acceptance-audit finding
RF-2.)* This paragraph previously justified the round-trip check with a
*ref whose name is 40 hex characters* impersonating a fixed id, on the
reasoning that git resolves names before object ids. **That claim is
withdrawn: it is not reachable.** git deliberately ignores refs whose
names end in 40 hex characters when resolving a 40-hex revision — it
warns about them precisely because they are only ever created by mistake
— so such a ref resolves to nothing and the record fails earlier, as an
unreadable commit. **[verified]**: `git rev-parse --verify` on a branch
named `b`×40 exits non-zero.

The actually reachable case is an **annotated tag**. A tag object's id is
a full-length lowercase hexadecimal string, so it passes the syntactic
check untouched, and `^{commit}` then *peels* it to a different object.
A Register record naming the tag object would seal the archive against a
commit the record does not name, through a ref that is itself movable and
deletable — precisely what the "a tag is a movable, deletable ref" bullet
above bars, reached by recording the tag's *object id* rather than its
name. The round-trip check is unchanged and remains correct; only the
example justifying it was wrong — and the regression test that claimed to
cover it was, for the same reason, passing whether or not the check
existed. It has been replaced with the annotated-tag case and now fails
when the check is removed.

**D12 — the Register is canonical JSONL, and is now validated as such.**
*(Added 2026-07-26, same pass.)* C-3's reader declines to use
`canonical_jsonl.read_canonical_jsonl`, for a good reason that stands:
that reader raises on the first bad line, which would refuse the Register
for *every* project, while C-3 requires per-project attribution.
Declining to reuse it is not licence to be **laxer** than it. Its two
whole-file rules — LF-only, and a required trailing newline — are now
enforced directly, as whole-file refusals (C-3's third bullet: a file
that is not canonical JSONL cannot be split into attributable records at
all). A missing trailing newline is how an append interrupted mid-record
presents, and assuming the last line complete is exactly the optimistic
read C-3's 2026-07-26 amendment already rejected elsewhere.

The reader was also *silently* laxer in one place: it split lines with
`str.splitlines()`, which breaks on U+2028, U+2029, U+0085, VT and FF —
all legal **unescaped** inside a JSON string under `ensure_ascii=False`,
which is what `canonical_jsonl` writes. One such character in a
`sealed_by` field would have split a valid record into two unparseable
fragments, and the positional rule would then have reported a corrupt
Register for a file that was never corrupt. Splitting on LF alone matches
exactly what the writer joins on.

**D5 — Register self-integrity.** *(Corrected 2026-07-26, post-merge AD-074
governance review: the original wording below overstated what git-log
review actually catches.)* The Archive Seal Register is **not protected by
the seal it drives.** It is a governance **control input**, not a sealed
artifact — nothing in this design hashes it, seals it, or verifies its own
history. `ArchiveVerifier` does not detect a Register tamper itself; it
trusts the Register's latest record for a `project_id` (§5.5 C-2) at face
value.

What git-log-based review actually catches is narrower than "detectable
through the repository's own history and human review" implies, and the two
cases below are not the same guarantee:

- **A silent edit to a *committed* past Register record** — changing a
  `sealed_commit`, appending a forged record, or rewriting one in place,
  then committing it — is visible in `git log -p` / `git blame` over
  `docs/archive_seal_register.jsonl`, the same git-log-based scrutiny that is
  the only defense against a rewritten `transition_records.jsonl`
  predecessor hash (S-4). This defense is real, but conditional: it catches
  the edit only if a human actually reviews that history. Nothing in this
  design runs that review automatically.
- **An uncommitted working-tree replacement or rewrite of the Register** —
  editing the file and running verification before, or without ever,
  committing the change — leaves **no commit to review at all**. Git
  history review answers "what changed between two commits"; it is
  structurally blind to a change that is never committed, which is not
  merely a harder case of the committed-edit defense above but a case that
  defense does not reach at all.

**Increment 2 (this pass) intentionally does not close this gap.** The
Register reader (§7B D12, `_latest_register_record`) validates the
Register's *shape* — canonical JSONL, schema, supersession — not its
*provenance*, and nothing added by this pass hashes the Register or anchors
it to a commit the way `sealed_commit` anchors an archive. Closing it would
require giving the Register the same kind of self-protection
`transition_records.jsonl` already has — a hash-chained, tamper-evident
issuance model for the Register itself. That is the *shape* of the remedy,
not a commitment that it is the one chosen.

**Forward reference corrected 2026-07-26 at acceptance.** This paragraph
previously said the remedy was "tracked as further work (§9)" when §9
contained no such item — a forward reference that resolved to nothing.
§9 now carries it as **item 9, "Register self-integrity"**, stated there
as what it actually is: a disclosed residual gap that AD-074 does not
close, **unassigned** — no AD number is reserved for it, no increment
owns it, and no work is scheduled. It remains distinct from this
document's own §11 Increment 1–3 sequence, which sequences the Seal's
rollout and not a future Register-hardening pass.

**D6 — `AC-74-13`, added to §8 below.** `OverallStatus.SOUND` means, and
means only, "the sealed archive paths match the sealing commit tree." It
does not imply dataset-hash verification (`DatasetIntegrityChecker` is
unimplemented, §9 item 6), research reproducibility, or experiment
validity — Standard §4's human question, untouched by any branch this AD
defines.

---

## 7C. Hardening item registry — `BLOCKER`/`M` labels

*(Added 2026-07-26, post-merge AD-074 governance review.)* `core/governance/archive_seal.py`
and `tests/test_governance_archive_verifier.py` mark several of the §7B findings above with
short inline labels — `BLOCKER 1`–`BLOCKER 3`, `M-1`, `M-3`–`M-6` — that were introduced during
the 2026-07-26 Increment 2 hardening pass but never given an authoritative definition in this
document or in `ARCHITECTURE_DECISIONS.md`. That gap is closed here. No label is renamed and no
code comment is touched; this table only records, for each label already in use, the finding it
names, where it is implemented, and what tests exercise it. Line numbers are as of this
document's writing (`archive_seal.py` at HEAD `2392de2`) and are a locator, not a contract — the
function names are the durable reference.

| Label | Meaning | Implementation | Tests | §7B / AC ref |
|---|---|---|---|---|
| **BLOCKER 1** | `protected_file_hashes.json`'s exclusion set must be read **at the sealing commit**, never the working tree — a working-tree read would let anyone exempt an archive path from verification after the fact, with no commit and no Register trace. | `_protected_file_hashes_exclusion_set` (`archive_seal.py:1278`) | `test_seal_post_seal_protected_fixture_edit_cannot_launder_a_tampered_file`, `test_seal_protected_fixture_absent_at_sealing_commit_excludes_nothing`, `test_seal_protected_fixture_malformed_at_sealing_commit_is_unverifiable` | D9 |
| **BLOCKER 2** | The git attribute stack — system/global attribute files, `$GIT_COMMON_DIR/info/attributes`, per-repo `.gitattributes`, `filter` drivers, and `attr.tree`/`GIT_ATTR_SOURCE` source selection — is a live third input to the hash comparison and must be pinned or refused so it cannot silently change a `MATCHED` result. | `_gitattributes_drift_error` (800), `_filter_attribute_error` (861), `_attribute_source_directories` (785), attribute-stack env pinning in `_git_env`/`_run_git` (377, 399) | `test_seal_post_seal_gitattributes_edit_is_unverifiable`, `test_seal_gitattributes_appearing_after_the_seal_is_unverifiable`, `test_seal_gitattributes_inside_the_archive_is_also_verified`, `test_seal_info_attributes_override_is_unverifiable`, `test_seal_clean_filter_on_a_compared_path_is_refused` | D7, AC-74-5a |
| **BLOCKER 3** | `sealed_commit` must be a full-length lowercase hex object id, never a symbolic ref (`HEAD`, a branch, a tag) or an abbreviated hash — and the resolved id must round-trip-match the recorded string, so a peeled annotated-tag id cannot stand in for the commit it peels to. | `_fixed_commit_id_error` (447), `_resolved_commit_id` (485), `_SEALED_COMMIT_PATTERN` (166) | `test_seal_non_fixed_object_id_is_rejected_before_resolution`, `test_seal_head_naming_the_sealed_commit_is_still_rejected`, `test_seal_full_lowercase_object_id_is_accepted`, `test_seal_ref_named_like_an_object_id_is_ignored_by_git_itself` (and the annotated-tag peel test) | D11, AC-74-5b |
| **M-1** | A `dataset_manifest.json` `snapshot_path` entry must resolve strictly inside `dataset_hashes/` (no `..`, no absolute path, no drive letter, no backslash), checked lexically, or the exclusion set is underivable. | `_is_contained_snapshot_path` (1245), `_DATASET_SNAPSHOT_ROOT` (157) | `test_seal_escaping_snapshot_path_refuses_the_exclusion_set` | D9 (`snapshot_path` containment paragraph), AC-74-5 |
| **M-2** | **Unused / reserved — no historical meaning recoverable.** No definition, code path, test, or git history reference (`git log -S` across all branches, and a full-text search of both files) exists anywhere in this repository under this label. The `BLOCKER`/`M` sequence otherwise runs contiguously (`BLOCKER 1`–`3`, `M-1`, `M-3`–`M-6`); `M-2` is a gap in that numbering, not a finding whose text was lost. Recorded here as reserved rather than invented, per this review's own discipline against unstated blanket claims (§7 A-1). If a future pass needs a ninth hardening-item label, it should not reuse `M-2` for an unrelated finding without first confirming no earlier meaning surfaces. | — | — | — |
| **M-3** | Legacy archives (`reference_v1`, `reference_v2_h1`, `reference_h3`, or any archive declaring `lifecycle_version: "legacy"`) are refused **before** the Register is consulted, so they can never report `MATCHED` even if given a manifest and a Register record. | `_legacy_archive_error` (943) | `test_seal_legacy_project_id_with_a_register_record_is_still_unverifiable`, `test_seal_lifecycle_version_legacy_with_a_register_record_is_unverifiable` | AC-74-9 |
| **M-4** | An excluded path's **existence** is still checked even though its content is excluded from comparison — deleting an excluded file must produce a `missing` finding, not silence. | `verify_seal` (1336), path-set-vs-narrowed-content-set logic (~1475–1484) | `test_seal_deleted_excluded_dataset_file_is_a_missing_finding`, `test_seal_excluded_file_content_change_remains_matched` | AC-74-4 |
| **M-5** | Symlinks and gitlinks — and, on Windows, NTFS junctions/reparse points — are refused outright rather than followed or guessed at, checked on both the sealed-tree side (mode check) and the working-tree side. | `_is_link_or_reparse_point` (695), mode check in `verify_seal` (~1449–1465), `_REGULAR_FILE_MODES` (173) | `test_seal_symlink_in_the_archive_is_unverifiable` (plus the F-3 junction regression) | D8 |
| **M-6** | The Archive Seal Register must be canonical JSONL — LF-only line endings, a required trailing newline, split only on `\n` (never `str.splitlines()`, which breaks on JSON-legal-but-non-LF separators) — or it is refused whole-file. | `_latest_register_record` (975), whole-file validation (~1057–1064) | `test_seal_register_with_crlf_is_refused`, `test_seal_register_missing_trailing_newline_is_refused` | D12 |

---

## 8. Proposed acceptance criteria

Properties, not tests, in AD-073's own style. Numbered in AD-074's own space.

- **AC-74-1.** The Seal branch remains reachable only through
  `verify_archive()`. No second public entry point is introduced (AD-073 AC-1
  preserved).
- **AC-74-2.** The Seal branch reads no freeze claim, calls no
  `verify_freeze()`, and calls neither chain-verification function. Its git
  access is read-only and confined to a commit read from the Register.
- **AC-74-3.** `modified`, `missing`, and `unexpected` are three distinct
  finding kinds, never collapsed (AD-073 AC-7 preserved).
- **AC-74-4** *(clarified 2026-07-26, §7B D9)*. The **content** of no path
  named by a `dataset_manifest.json` `snapshot_path` entry, and of no path
  present in `protected_file_hashes.json`, is ever compared by the Seal
  branch. Both exclusion sources are read **at the sealing commit**, never
  from the working tree. The excluded set is reported, not implicit.
  **Existence is still checked**: an exclusion assigns a file's *bytes* to
  another control, and neither `DatasetIntegrityChecker` nor the Phase-0
  fixture asserts that the file still exists, while §5.2's threat table
  promises that a file deleted from a closed archive is detected. Deleting
  an excluded file outright previously produced no finding from any
  mechanism at all; it is now a `missing` finding.
- **AC-74-5.** An underivable exclusion set yields `UNVERIFIABLE`, never a
  comparison over an unbounded set. A `snapshot_path` that does not resolve
  strictly inside `dataset_hashes/` makes the set underivable (§7B D9).
- **AC-74-5a** *(added 2026-07-26, §7B D7; amended the same day for RF-1)*.
  **No input outside the sealing commit may change a `MATCHED` result,
  including Git attribute source selection.** The attribute stack
  governing `hash-object --path` is pinned (system and global attribute
  files disabled; `$GIT_COMMON_DIR/info/attributes` refused;
  `.gitattributes` verified against the sealing commit), the
  attribute-*source* selection is pinned (`-c attr.tree=` on every
  invocation and `GIT_ATTR_SOURCE` removed from the environment, since
  the environment variable overrides the config setting), and a `filter`
  attribute on a compared path is refused, since its `clean` driver is
  arbitrary code configured outside every artifact this design verifies.
- **AC-74-5b** *(added 2026-07-26, §7B D11)*. `sealed_commit` is a
  full-length lowercase hexadecimal object id. A symbolic ref (`HEAD`, a
  branch, a tag) or an abbreviated hash yields `UNVERIFIABLE`, and the
  resolved id is checked against the recorded string so that an object id
  that *peels* to a different object — an annotated tag's — cannot stand
  in for the commit it peels to *(example corrected 2026-07-26, RF-2)*.
- **AC-74-6.** The Register is append-only (§5.5 C-2). No implementation
  rewrites, reorders, or deletes a record; a re-seal is a new record naming
  its `supersedes` predecessor, and the prior record remains readable. A
  malformed record yields `UNVERIFIABLE` for its own `project_id` (§5.5
  C-3), never a skip and never a whole-file refusal unless the file itself
  is unreadable.
- **AC-74-7.** Nothing under `research_archive/` is written, created, or
  mutated by seal verification **or** by seal issuance. Issuance writes the
  Register and nothing else.
- **AC-74-8.** No Governance → Research/Validation/Reporting import;
  `tools/check_import_boundaries.py` passes unmodified.
- **AC-74-9** *(strengthened 2026-07-26)*. The three legacy archives acquire
  no Register record, and the Seal branch reports them `UNVERIFIABLE`, never
  `MATCHED` and never `MISMATCH`. **This is now enforced, not assumed.** It
  previously held only by circumstance: the named three carry no
  `archive_manifest.json`, so they failed at `project_id` resolution for an
  unrelated reason, and anything that gave one a manifest — or any archive
  declaring `lifecycle_version: "legacy"` — would have been compared, and
  with a Register record would have reported `MATCHED`. The Seal now refuses
  a legacy archive explicitly, before the Register is consulted. A legacy
  archive's bytes are `protected_file_hashes.json`'s claim (§2 O-3), a
  different control with a different root of trust; "exempt from a layout
  check" is not "sealed", and neither is "covered by the Phase-0 fixture".
- **AC-74-10.** No seal result enters a `GateResult`, `GateOutcome`,
  `GateRunRecord`, or `DecisionRecord`, and none participates in
  `compose_transition()` (AD-059, AD-063 preserved).
- **AC-74-11.** With a Register record present and the archive intact,
  `verify_archive()` returns `OverallStatus.SOUND` — the first time any
  archive can. Absent a record, the report is `UNVERIFIABLE`, never `SOUND`.
- **AC-74-12.** The trust boundary of §5.2 — specifically that history rewrite
  is **not** defeated — is stated in the implementing module's docstring, not
  only here.
- **AC-74-13.** `OverallStatus.SOUND` means exactly "the sealed archive paths
  match the sealing commit tree" (§7B D6). No implementation, docstring, or
  report field may state or imply that `SOUND` additionally confirms dataset
  hash verification, research reproducibility, or experiment validity.

---

## 9. Non-goals

Stated as problems AD-074 deliberately does **not** solve.

1. **Defeating history rewrite.** S-4. An external anchor (signed tag, remote
   attestation, out-of-band publication) is the only thing that would, and
   none is designed here. AD-065 already accepted the same ceiling for chain
   anchoring.
2. **Sealing `reference_h4` retroactively into its own directory.** The
   Register records a commit *about* the archive; nothing is written into it.
3. **Automatic issuance.** No transition, gate, or hook creates a Register
   record. Issuance is a recorded human act.
4. **Wiring.** Deciding to *run* archive verification as a standing check is
   §11's separate increment, and is what actually closes R-4. AD-073's
   "verification is not enforcement" residual is inherited unchanged.
5. **The post-Archive append question.** AD-073 Non-goals item 9's separate
   ADR still owns it. AD-074 is *compatible* with either answer — that is the
   point of append-only — but does not decide it.
6. **`DatasetIntegrityChecker`.** Still unimplemented [verified]; the seal
   delegates to a checker that does not exist yet, so `dataset_hashes/*.jsonl`
   remains covered by a recorded hash that nothing verifies. **This is a real
   residual gap and is disclosed, not closed.**
7. **Retiring `protected_file_hashes.json`.** It keeps the three legacy
   archives. Untouched, unedited, unextended.
8. **Chain anchoring (R-5/G-4), reproduction, evidence quality,
   authorization floors.** All unchanged.
9. **Register self-integrity.** *(Added 2026-07-26 at acceptance, as the
   destination of §7B D5's forward reference.)* The Archive Seal Register
   is a governance **control input**, not a sealed artifact: nothing in
   this design hashes it, anchors it to a commit, or verifies its own
   history, and `ArchiveVerifier` trusts its latest record for a
   `project_id` at face value. §7B D5 states the two cases and their
   asymmetry — a *committed* Register edit is visible in `git log -p` /
   `git blame` **if a human reviews that history**, which nothing here
   automates, while an *uncommitted* working-tree rewrite leaves no
   commit for that review to reach at all. **This is a real residual gap
   and is disclosed, not closed**, on the same terms as item 6. Closing
   it would take a hash-chained, tamper-evident issuance model for the
   Register itself, of the kind `transition_records.jsonl` already has.
   **No AD number is reserved for that work, no increment owns it, and
   nothing schedules it** — this item exists so that the gap is recorded
   as unassigned rather than referred onward to a plan that does not
   exist.

---

## 10. Migration impact

Additive throughout. Nothing existing is rewritten.

| Area | Impact |
|---|---|
| `archive_manifest.json` schema | **None** |
| `dataset_manifest.json` schema | **None** — read-only, for `snapshot_path` |
| `transition_records.jsonl` schema | **None** |
| `protected_file_hashes.json` | **None** — not edited, not extended |
| `freeze_verifier.py` | **Unmodified** (AD-073 AC-12 preserved) |
| `decision_recorder.py` | **Unmodified** |
| `tools/archive_manifest.py` | **Unmodified**; AD-039's move trigger still not met (reading, not writing) |
| `tools/check_import_boundaries.py` | **Unmodified** |
| `core/governance/archive_verifier.py` | `_verify_seal()` gains a real body; `SealReport` gains `excluded_paths`; public signature unchanged |
| New files | `docs/archive_seal_register.jsonl`; one seal module; one test module |
| `core/governance/__init__.py` | One docstring sentence ("a stub — always `UNVERIFIABLE`") becomes stale and must be updated |
| **Existing tests** | `test_seal_stub_is_always_unverifiable` (`tests/test_governance_archive_verifier.py`:268) **must be replaced** — it asserts the stub behaviour AD-074 removes. The `derive_overall_status` tests at :462–476 already cover `MATCHED`/`MISMATCH` and need no change [verified] |
| `tests/test_repository_integrity_snapshot.py`:100–106 | Exclusions can be dropped **only** in §11's increment 3, not before |

**Zero data migration.** No existing artifact is re-read, re-hashed, or
re-written. `reference_h4`'s Register record names `29553b7`, a commit that
already exists and already contains the correct bytes [verified].

---

## 11. Recommendation — implement now, in three separately-approvable increments

**Recommendation: implement now.** Grounds, in order of weight:

1. **R-4 is the platform's only live High-severity gap** and is marked
   "Highest urgency — the gap is live today." It has been open since the
   `reference_h4` cycle closed. Its own named candidate (a second hash
   fixture) is candidate (b), which this review finds strictly weaker than the
   design available.
2. **The blocking unknown is gone.** AD-073 deferred the seal because "no
   sealed-manifest format exists yet." Under AD-074 no manifest format is
   needed — the format is one commit ref per archive, and the expected values
   already exist in git. The reason for the stub has been dissolved, not
   worked around.
3. **The cost is small and the blast radius is contained.** One new artifact,
   one new module, one function body replaced, one docstring sentence, one
   test replaced. No schema change, no data migration, no boundary change.
4. **`positive_control_phase3` will reproduce D-9 the moment it closes** —
   G-5 says so explicitly. Building the path before the next closure is
   cheaper than remediating a second archive after it.

**Against implementing now**, stated fairly: AD-074 requires amending an
AD accepted the same day, which is a real cost to the register's stability;
and §7's fallback exists precisely so the amendment is a choice rather than a
precondition. If the accepting authority prefers not to amend AD-073 at all,
take the §7 fallback and implement candidate (b) — worse, but complete, and
still better than the stub.

**Sequencing.** Three increments, each independently reviewable and
independently revertible:

**Increment 1 — accept AD-074 + the AD-073 AC-3 amendment.** Documentation
only. Closes nothing on its own; AD-073's own Status warns against citing a
design as partial closure, and that warning applies to AD-074 identically.

**Increment 2 — implement the Seal branch and the Register reader.** Register
empty. Every archive still reports `UNVERIFIABLE`, exactly as today — but by
*"no seal has been issued,"* a per-archive fact, rather than by *"no format
exists,"* a platform-wide one. **This is the increment that closes R-3**: the
completeness branch (`da9ca34`), the freeze branch (`414b07e`), and a real
seal branch together make `ArchiveVerifier` the Phase 8 instrument R-3 asked
for, and remove the structural impossibility of a `SOUND` result.

**Increment 3 — issue `reference_h4`'s seal and wire the check.** Append one
Register record naming `29553b7`; add a test asserting
`verify_archive(research_archive/reference_h4) == SOUND`; drop the expired
exclusion clauses at `tests/test_repository_integrity_snapshot.py`:100–106.
**This is the increment that closes R-4** — and only this one. Increments 1
and 2 leave D-9 exactly as live as it is today, and must not be reported
otherwise.

**Do not merge the increments.** Increment 3 changes a currently-passing test
file and takes `reference_h4` from unprotected to protected; it deserves its
own review, separate from a design acceptance and separate from a new module.

---

## 12. Adversarial self-review

*What assumption could still be wrong?* That the sealing commit is
unambiguous. It is unambiguous for `reference_h4` because the archive closed
in a single commit [verified]. A future cycle whose Archive phase spans
several commits — a decision record in one, a reviewer report in the next —
has no single "the archive is now complete" commit, and issuance would have to
pick one by human judgment. The Register's `sealed_by` field makes that
judgment attributable, which is the most the design can do; it does not make
it mechanical, and a reader must not assume it is.

*What future implementation mistake could this allow?* Reading the sealing
commit from anywhere other than the Register — from `HEAD`, from the terminal
record's `commit_hash`, or from `git log` over the archive path. All three are
available, all three look reasonable, and S-1 proves the second is
provably wrong. AC-74-2 is written to catch this, and the implementing module
should name S-1 in its docstring for the same reason `archive_verifier.py`
already names AD-073's conflict C-1.

*Does AD-074 create a second source of truth about archived bytes?* For
in-scope files, no: git holds the bytes, the Register names which tree, and
neither is a hash record the other duplicates — this is the specific advantage
over candidate (b). The residual is §9 item 6: `dataset_hashes/*.jsonl` has a
recorded `content_hash` and no checker, so those three files are excluded from
the seal because AD-073 Decision part 8's coverage boundary assigns them to
`DatasetIntegrityChecker`'s domain (§7A B-2) — **not** because sealing them
would duplicate a hash record; the seal asserts no hash of its own, so it has
nothing to duplicate. That is a gap AD-073 created and AD-074 inherits rather
than widens, and it should be closed by implementing `DatasetIntegrityChecker`,
not by extending the seal over it.

*Is accepting AD-074 a way of appearing to close R-4 without closing it?*
That is the sharpest objection, and it is the reason §11 splits the work into
three increments and states which one closes which item. If increments 1 and 2
land and increment 3 does not, D-9 stays live, `reference_h4` stays
unprotected, and this document will have made the register longer without
making the archive safer — the same failure AD-073 disclosed against itself,
and the reason that disclosure is repeated here rather than assumed learned.
