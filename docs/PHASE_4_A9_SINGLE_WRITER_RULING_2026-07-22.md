# Phase 4 / Step 9 — A-9 Ruling Record (single-writer enforcement)

**Date filed:** 2026-07-22
**Repository state ruled against:** canonical `D:\Claude\etf_platform`, `master`, HEAD `f7802fe`, working tree clean.

**Dating note, disclosed rather than smoothed over.** This record was
authored in the same continuous effort as the A-6 (`3ee23fd`), A-8
(`e76bafe`) and A-5 (`f7802fe`) rulings and carries their filing date and
filename convention. That effort ran past 2026-07-22 UTC into
2026-07-23. The filename and filed date are retained as `2026-07-22`
because the requesting instruction fixed them; nothing in this record
depends on which of the two dates is taken as authoritative, and no claim
below is scoped by date. Standard §5's requirement (F-24) is satisfied
either way — this file is dated in both its filename and its content.

---

## 1. Status

**Status: ruling record.** It disposes of prerequisite A-9 and of nothing
else. It is **not** an ADR, **not** an amendment to any ADR draft, **not**
a schema, **not** a lock, **not** a writer, and **not** a Phase B or
Phase C artifact.

**Prerequisite addressed:**
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
§4.1 row A-9 — *"Single-writer enforcement decided — stated assumption or
mechanical lock"*, whose "Done when" column reads **"Recorded in
AD-048"**.

**A-9 is decided by this record. A-9 is not closed by this record**, and
this record does not claim otherwise. The distinction is the one
[`PHASE_4_A6_RESEARCH_IDENTITY_RULING_2026-07-22.md`](PHASE_4_A6_RESEARCH_IDENTITY_RULING_2026-07-22.md)
(`3ee23fd`) drew for A-6,
[`PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md`](PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md)
(`e76bafe`) drew for A-8, and
[`PHASE_4_A5_CHAIN_ANCHORING_RULING_2026-07-22.md`](PHASE_4_A5_CHAIN_ANCHORING_RULING_2026-07-22.md)
(`f7802fe`) drew for A-5, and it holds here for the same reason:

- A-9's "Done when" condition is *recorded in AD-048*. AD-048 does not
  exist in [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) — the
  accepted set runs AD-001 … AD-046 plus AD-051 (F-21), and AD-047 …
  AD-050 exist only as drafts in
  [`PHASE_4_STEP9_DRAFT_ADRS.md`](PHASE_4_STEP9_DRAFT_ADRS.md). Writing
  them in is **A-2**, a separate prerequisite.
- This record supplies the **decided content** A-9 requires and fixes it
  in writing at a date, so A-2's transcription has something settled to
  transcribe. **A-9 closes when AD-048 is written and accepted under A-2
  carrying the decisions in §4 below.** Until then A-9 stays open, and
  Step 9 stays blocked on it exactly as it stood at `f7802fe`.

**No file is edited by this record, and no code is introduced by it.**
This is a new, dated file.
[`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md),
[`PHASE_4_STEP9_DRAFT_ADRS.md`](PHASE_4_STEP9_DRAFT_ADRS.md),
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md),
[`RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md),
[`RESEARCH_ARCHIVE_MANIFEST.md`](RESEARCH_ARCHIVE_MANIFEST.md) and
[`templates/decision_log_template.md`](templates/decision_log_template.md)
are all retained unedited, and each is cited below by section or line
rather than amended.

**Supersession discipline.** Same convention, and the same disclosed
limitation on its scope, as the A-1, A-6, A-8 and A-5 ruling records:
Standard §5's *"a correction is a new, dated file, cross-referenced from
the file it supersedes"* is stated for evidence packages under
`research_archive/<cycle_name>/` and is applied here **by extension, not
by direct scope**, together with `ARCHITECTURE_DECISIONS.md`'s preamble
rule that a later phase revising an earlier decision says so explicitly.

**Review level: Level 1 — self-review**, per
[`RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md) §4.
Authored and reviewed within the same effort that produced the material
it rules on. Standard §4's Level 1 limitations apply in full and are
adopted, not softened; the word "independent" is not used of this record.
Level 3 is unavailable on this platform — and the *reason* it is
unavailable, the single-operator fact at F-6, is load-bearing in §4.2
below. That is disclosed rather than left for a reader to notice: this
record leans on a limitation of the platform as a ground for a decision,
and it says so.

**Verification basis.** Every factual claim in §3 was checked directly
against the canonical repository at `f7802fe` — file contents, `git
ls-files`, directory listings, and repository-wide search — and each
carries its source. Negative facts (F-3, F-18) were established by
search over `core/` and `tools/` and are stated as searches, not as
intuitions.

---

## 2. Scope

**In scope — exactly five questions, no more:**

1. What "single writer" means in this governance context.
2. The minimum valid governance claim about writer discipline.
3. What is explicitly **not** claimed — OS-level locking, database
   locking, runtime prevention, automatic enforcement.
4. How conflicts are handled: duplicate sequence numbers, competing
   writers, ambiguous anchors.
5. Keeping writer authority (A-9) separate from evidence anchoring
   (A-5).

**Out of scope, and not decided here:** every other Phase A
prerequisite — A-1 (ruled on at `aca36fb`), A-6 (`3ee23fd`), A-8
(`e76bafe`), A-5 (`f7802fe`); A-2, A-3, A-4, A-7 untouched and open on
their own terms. In particular:

- **A-5's anchoring rulings are not reopened, extended, or weakened.**
  The anchor, its grammar, its carrier, the numbering origin, the
  contiguity rule and the verification split are taken as settled input.
  A-9 consumes them; it does not restate them as its own, and no ruling
  in §4 may be cited as amending one.
- **A-8's location ruling is not reopened.** The chain path
  `research_archive/<cycle_name>/transition_records.jsonl` (F-16) is
  taken as settled input, and its per-cycle partition is what makes §4.4's
  scoping of the assumption possible rather than being re-argued here.
- **AD-048's field set is not reopened.** A-9 introduces **no new
  field** — in particular **no writer-identity, process-id, host,
  session, or signature field** (§4.6, §7.2). The closed field set stays
  closed.
- **A-3's authorization policy is not decided here.** A-9 takes §1.5's
  human-authorization requirement (F-10) as settled input and rules on
  *who may write*, not on *what authorizes a transition*. Where the two
  meet — every write has exactly one accountable authorizer — A-9 records
  the consequence and A-3/AD-050 keep the decision.
- **Whether the residual concurrency exposure is acceptable** is a
  governance acceptance question that AD-048's acceptance under A-2
  answers. A-9 states the exposure at its true size, including the part
  that is undetectable (§6.3); it does not pronounce it tolerable.

**Phase A discipline is binding on this record.** Resolution §4.1 scopes
Phase A to "documents only, zero code". Nothing here implements a lock,
writes a writer, creates a lock file, defines a schema in code, creates a
Phase B or Phase C artifact, or edits an ADR. See §11.

---

## 3. Facts established

Each row was verified directly at `f7802fe`.

| # | Fact | Source |
|---|---|---|
| F-1 | Resolution §4.1 states A-9 as a **binary**: *"Single-writer enforcement decided — **stated assumption or mechanical lock**"*, done when *"Recorded in AD-048"* | `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:478` |
| F-2 | Phase C's exit criteria include *"single-writer **enforced** as decided in A-9"*, in the same list as the tamper-detection criteria | `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:491` |
| F-3 | **No locking primitive of any kind exists in this repository.** A search of `core/` and `tools/` for `fcntl`, `msvcrt`, `flock`, `filelock`, `portalocker` and `os.replace` returns **no match**. The only `tempfile` uses are scratch *directories* — `pinned_worktree.py:46` and `reproduction_runner.py:308` — neither a lock nor an atomic replace | repository-wide search of `core/`, `tools/` |
| F-4 | `write_canonical_jsonl` writes the **whole file** via `path.write_bytes`. There is no append mode, no `O_APPEND`, no temp-file, and no atomic replace anywhere in the module | `core/governance/canonical_jsonl.py:24-33` |
| F-5 | AD-048's draft nonetheless describes the append as *"read-append-rewrite with the prior prefix verified byte-identical, written atomically (temp + replace)"* — which is a **requirement on Phase C**, not a description of any behaviour that exists at `f7802fe` (F-4) | `PHASE_4_STEP9_DRAFT_ADRS.md:144-150` |
| F-6 | Standard §4 records, as a stated platform limitation, that *"the platform operates with a single human operator directing all research and all review sessions"*, and that consequently no Level 3 review has ever been performed here | `RESEARCH_GOVERNANCE_STANDARD.md:399` |
| F-7 | The Governance domain's read-only posture is stated in the module that defines it: *"nothing in this module ever writes, commits, checks out, or resets anything"* | `core/governance/freeze_verifier.py:40-43` |
| F-8 | Governance may import **only** `data`: `ALLOWED_DEPENDENCIES["governance"] == frozenset({"data"})` | `tools/check_import_boundaries.py:64` |
| F-9 | `core/research/lifecycle.py` is *"the only module permitted to import Validation and Governance together, and is therefore the only legal binding point"* — and because Governance cannot import Validation, **no other layer can perform that binding at all** | `PHASE_4_STEP9_DRAFT_ADRS.md` AD-050 *Migration/status*; `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:493` |
| F-10 | **No transition is ever automatic, at any gate status.** `advance_phase()` requires an explicit human authorization argument every time; gate status determines *what kind* of authorization and *what must be disclosed*, never whether a machine may proceed unattended | `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:230-243`; `PHASE_4_STEP9_DRAFT_ADRS.md` AD-050 part 4 |
| F-11 | AD-050's evidence preconditions require *"the decision chain verified intact **and anchored** before the append, so a transition is never written onto a broken chain"* | `PHASE_4_STEP9_DRAFT_ADRS.md:457-461` |
| F-12 | Current phase is **derived from the chain, not stored**, and the failure direction is deliberately asymmetric: a damaged or truncated chain makes a derived phase **under-claim** (regress to the last provable transition), which is the safe failure | `PHASE_4_STEP9_DRAFT_ADRS.md` AD-050 part 3; `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:294-318` |
| F-13 | A-5 R-3.3: sequence numbers are contiguous ascending integers `1 … N` with **no gaps and no duplicates**; a gap or duplicate is **chain-invalid** — verification refuses, and it is *not repaired, not renumbered, and not reported as a warning* | A-5 §4.3 R-3.3 |
| F-14 | A-5 R-6: **anchor lag is inherent.** Every record above the last cited sequence number is unanchored, and during normal operation that is at least the newest record. No mechanism closes the window | A-5 §4.6 |
| F-15 | A-5 §9 **pre-committed the consequence of this ruling**: *"If A-9 rules 'stated assumption'"* → *"then §6.1's claims are **conditional on that assumption**, and AD-048 must say so in those words rather than asserting them unconditionally"*. A-5 also ruled that a citation naming a duplicated sequence number is **ambiguous, and ambiguity is a failure: verification refuses rather than picking a record** | A-5 §9 |
| F-16 | The chain is one file per cycle at `research_archive/<cycle_name>/transition_records.jsonl`; A-8 §5 item 5 records that this bounds concurrency blast radius — *"concurrent advancement of different cycles does not contend at all"* — explicitly as *"a consequence recorded, **not** a decision of A-9"* | A-8 R-2, §5 item 5 |
| F-17 | A-8 R-3.5 forbids any store outside the repository; A-5 §4.4 records that Standard §5's package is a closed enumeration, such that *"adding an eighth required item would amend the Standard"* | A-8 §4.3 item 5; A-5 §4.4 |
| F-18 | **No CI configuration exists in this repository** — there is no `.github` directory, and no hook, workflow, or scheduled job of any kind | directory listing at repository root |
| F-19 | The only project-storage implementation is `InMemoryResearchProjectRepository`, *"a plain dict"*; the module states it *"commits to exactly one concrete storage mechanism today"*. **There is no database anywhere in this path** | `core/research/project_repository.py:5-12,37-48` |
| F-20 | Resolution §2.2's threat model is stated in one sentence: *"The actor who would author retroactively is the same actor who can truncate."* | `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:333-334` |
| F-21 | The accepted AD set is AD-001 … AD-046 plus **AD-051**, leaving AD-047 … AD-050 reserved for the Step 9 drafts | `docs/ARCHITECTURE_DECISIONS.md:1288-1295` |
| F-22 | AD-045's surviving objection is the **consumer-less abstraction**: it *"refused to build a component whose only designed trigger did not exist"*, and AD-048 is *void* if that ordering condition is violated | `PHASE_4_STEP9_DRAFT_ADRS.md:110-115` |
| F-23 | AD-048's closed field set contains **no writer-identity element of any kind** — no process id, host, user, session, or signature. Every field in it is self-asserted by whatever wrote the line, including `project_id`, the injected timestamp, and the authorization record | `PHASE_4_STEP9_DRAFT_ADRS.md:121-131` |
| F-24 | Standard §5's dating rule is *"Every file is dated in its own content **or** filename"* | `RESEARCH_GOVERNANCE_STANDARD.md:439-443` |
| F-25 | **A-5's and A-8's AD-048 consequence lists both number from `C-1`** — A-5 carries C-1 … C-13, A-8 carries C-1 … C-11. The two sets are disjoint in content and colliding in label | A-5 §7; A-8 §6 |

---

## 4. Decision

Seven rulings, R-1 … R-7, cited elsewhere as **A-9 R-*n*** to keep them
distinct from A-5's and A-8's identically numbered rulings. Each is
stated in the form it is to be transcribed under A-2.

### 4.1 R-1 — "Single writer" is three questions, and they have different answers

**Ruled: the phrase "single writer" conflates three separable properties.
Answering them with one word is what would produce a claim stronger than
its mechanism. They are ruled apart, and only one of the three has a
mechanism.**

| Property | The question it actually asks | Ruled answer | Has a mechanism? |
|---|---|---|---|
| **Authority** | *Which code path is permitted to append to a transition chain?* | Exactly one module, reachable through exactly one caller (R-3) | **Yes.** A design property, statically checkable by reading the source and pinnable by test |
| **Exclusivity in time** | *Can two appends to one chain file interleave?* | Assumed not to; **nothing prevents it** (R-2, R-4) | **No.** A runtime property, unenforced, and knowingly so |
| **Ownership / accountability** | *Who is answerable for a record having been written?* | The single human operator who authorized that transition (F-10), never the module | **Partly.** The authorization record is stored; the identity claim in it is self-asserted (F-23) |

**Ruled consequence, and it is the whole shape of this record:
"single writer" is a statement about *authority and accountability*,
which are documented and checkable, plus a statement about *exclusivity*,
which is an assumption.** AD-048 must not let the second borrow the
credibility of the first. Where the three are collapsed, a reader
encountering "single writer" will take it to mean the strongest of them —
exclusivity — which is precisely the one that is not true.

**Rejected readings, each closed:**

| Reading of "single writer" | Ruled |
|---|---|
| **Exclusive process** — at most one OS process may hold the chain open | **Rejected as a claim.** It is what is *assumed* (R-2), not what is *guaranteed*. No mechanism in this repository can make it true (F-3), and asserting it would be false |
| **Exclusive authority alone** — one authorized code path, nothing more said | **Rejected as insufficient.** True and checkable (R-3), but silent on the runtime question a reader is actually asking, and silence there will be read as a guarantee |
| **Documented ownership alone** — a named owner in prose | **Rejected as insufficient.** Necessary (R-3.3) and worth nothing on its own: a document naming an owner does not narrow what any process can do to a writable file |
| **All three, asserted together and undifferentiated** | **Rejected.** This is the failure mode the whole resolution exists to prevent — *"a claim with no mechanism is not admitted"* (Resolution §5) |

### 4.2 R-2 — The binary is answered: **stated assumption**, not mechanical lock

Resolution §4.1 posed A-9 as a binary (F-1). **Ruled: stated assumption.
No lock is introduced, in Step 9 or by this decision.**

Five grounds, the fourth decisive:

1. **No lock primitive exists to adopt.** Nothing in `core/` or `tools/`
   imports `fcntl`, `msvcrt`, `flock`, `filelock` or `portalocker`, and
   nothing performs an `os.replace` (F-3). A lock is therefore not a
   configuration choice but new machinery, with a new dependency or new
   platform-conditional code, in the domain that exists to be audited.
2. **A lock is a write, in the domain whose value is not writing.**
   Governance states of itself that *"nothing in this module ever writes,
   commits, checks out, or resets anything"* (F-7). An advisory lock file
   is an artifact, and A-9 finds no place for it in the governance model
   that has been chosen — reasoning independently, because no existing
   ruling reaches it. Placed at the cycle root it is an undeclared item in
   an evidence package whose contents Standard §5 enumerates as a closed
   list (F-17). Placed outside the repository it is untracked, and an
   untracked artifact is one this model cannot reason about at all: every
   governance claim in Step 9 is made about artifacts a later human can
   read, diff and cite, and a lock file that leaves no committed trace can
   neither be shown to have been held nor be shown to have been absent, so
   it would carry the appearance of discipline with none of the evidence.
   **A-8 R-3.5 is not cited for this.** That ruling fixes where the
   *anchored machine artifact* lives and is left exactly as it stands
   (F-16, F-17); it says nothing about lock files, and A-9 does not
   enlarge it into a prohibition it did not issue. The ground here is
   A-9's own, and it stands or falls on its own merits.
3. **The contention it defends against does not occur.** The platform
   runs with a single human operator directing all sessions (F-6), the
   chain is per-cycle so distinct cycles do not contend at all (F-16), and
   no transition happens without that operator explicitly authorizing it
   (F-10). Building a lock is a component whose only designed trigger does
   not exist — **AD-045's surviving objection, exactly** (F-22), applied
   to the very AD that had to answer it.
4. **A lock cannot deliver the property the chain actually needs, and
   this is why the answer is not merely "not yet".** The threat model is
   stated in one sentence: *"the actor who would author retroactively is
   the same actor who can truncate"* (F-20). A lock acquired by that
   actor's own process constrains that actor not at all — they may
   release it, bypass it, or edit the file with any text editor. A lock
   defends against *accidental* interleaving by *cooperating* writers. The
   chain's adversary is neither accidental nor cooperating. **A mechanism
   that raises the apparent strength of a claim without raising its actual
   strength is worse than no mechanism**, because a reader who sees a lock
   will believe something about the artifact that is not true.
5. **A lock here would be untestable in the environment that has it.** A
   single-operator platform cannot exercise real contention, so the lock
   would ship as load-bearing-looking code covered only by simulated
   tests, carrying unearned assurance. Phase C's exit criteria are about
   demonstrated properties; a lock would add one that cannot be
   demonstrated.

**What "stated assumption" is not permitted to mean.** It is not
permitted to mean *unstated*. R-4 fixes the exact words, R-5 fixes where
they appear, and R-6 fixes what happens when the assumption is false. An
assumption that is not written down, not located, and not paired with a
detection story is an omission wearing a ruling's clothes, and this
record does not make one.

### 4.3 R-3 — Writer authority: one module, one caller, one authorizer

**Ruled in three parts. This is the part of A-9 that has a mechanism, and
it is stated as narrowly as the mechanism supports.**

**R-3.1 — One writing module.** Exactly one module,
`core/governance/decision_recorder.py`, may write to a
`transition_records.jsonl`. No other module in any domain reads-modifies
or writes that file. This is checkable by inspection today (no such file
exists to be written, F-3 context) and is pinnable by test in Phase C:
no module other than the recorder may reference a transition-chain path.

**R-3.2 — One caller path.** The recorder is reachable only through
`core/research/lifecycle.py`, which is already the only module permitted
to import Validation and Governance together and therefore **the only
legal binding point that exists at all** (F-9). This is not a new
restriction; it is the existing import boundary (F-8) doing the work, and
A-9 records that it doubles as the writer-authority boundary. Nothing new
is built to enforce it, and the linter that enforces the boundary is
B-1's, not A-9's.

**R-3.3 — One accountable authorizer per record.** Every append is caused
by an `advance_phase()` call carrying an explicit human authorization
argument (F-10). Ruled consequence: **there is no writer without an
authorizer, and a record with no authorization record is not a record
this system can produce.** The human operator, not the module, owns the
chain; the module is an instrument. AD-048 must state ownership that way,
because "the recorder owns the chain" would put accountability on a
component that cannot hold it.

**Ruled explicitly, so it is not read as more than it is:** R-3 constrains
**what this system does**, not **what can happen to the file**. A JSONL
file on disk is writable by any process and any editor with filesystem
access. R-3 is an authority model, and an authority model binds the
design; it does not bind the operating system. §7.2 states this as a
non-claim.

### 4.4 R-4 — The assumption, stated in the words it must be stated in

**Ruled: the assumption is per-chain-file, not global, and is stated in
these terms.** AD-048 carries it substantively unchanged; the artifact
header carries it in the same place the chain already states its narrow
tamper-evidence claim (Resolution §2.2).

> **Single-writer assumption.** At most one process appends to any one
> `transition_records.jsonl` at any one time, and it does so on behalf of
> the single human operator who authorized that transition. **Nothing
> enforces this.** There is no lock, no advisory file, no process
> registry, and no runtime check. A violation is not prevented. It is
> either detected after the fact by chain verification, or — in the case
> named in §6.3 — it is not detected at all.

Ruled properties of that statement:

1. **Scope is one chain file.** Two cycles advancing concurrently do not
   violate it, because they touch different files (F-16). This is a real
   narrowing and is claimed as one: the assumption that must hold is much
   smaller than "only one thing ever runs".
2. **It is an assumption about the *system's own* writers.** It says
   nothing about a human editing the file by hand, which R-6.2 handles
   separately and which no assumption can constrain.
3. **It names the operator, not a process identity.** No field records
   which process wrote a line (F-23), so the assumption cannot be phrased
   as a checkable property of a record. It is a property of practice.
4. **It is disclosed at its true strength every time the chain's claim
   is.** Wherever AD-048 states what the chain proves, the conditionality
   introduced by A-5 §9 (F-15) is stated with it — see R-7 and §8.

### 4.5 R-5 — Enforcement is detection, not prevention, and it is already built into A-5

**Ruled: A-9 introduces no new detection mechanism. The detection that
serves it is A-5 R-3.3's contiguity rule (F-13), which was ruled for a
different reason and happens to cover two of the three concurrency
failure shapes.** A-9 records the coverage, states its edge honestly, and
adds nothing.

| Concurrency failure shape | Detected by | Ruled disposition |
|---|---|---|
| Two writers assign the **same** `sequence_number` and both records land | A-5 R-3.3 duplicate check | **Chain-invalid.** Verification refuses (R-6.1) |
| A write is lost such that a number is **skipped** | A-5 R-3.3 gap check | **Chain-invalid.** Verification refuses (R-6.1) |
| Two writers assign the same `sequence_number` and the **second rewrite discards the first record** | **Nothing** | **Undetectable.** §6.3, stated as a non-claim, not as a residual risk to be managed |

**Why the third shape exists and is not closed here.** The append is
read-append-rewrite over the whole file (F-4, F-5): a writer reads the
prefix, computes the next sequence number, and rewrites the file. Two
writers that both read prefix `1 … N−1` both produce a file ending at
`N`, and the later write wins. The result is a **contiguous, correctly
chained, internally valid file** that is missing a transition that
happened. No mechanical check can see it, because there is nothing wrong
with the bytes.

**The atomic-write wording must not be allowed to obscure this.** AD-048's
draft says the append is *"written atomically (temp + replace)"* (F-5).
Ruled: temp-plus-replace makes the **replacement** atomic — a reader never
sees a half-written file. It does **not** make the
**read-modify-write** atomic, and it therefore does nothing about
last-writer-wins. AD-048 must say which of the two it means, in those
words (§9, C-6). A reader who takes "atomic" as "concurrency-safe" would
be wrong, and the current wording invites it.

**A-5's anchor is the only thing that could ever surface the third
shape, and it cannot surface it in time.** A lost head record is
detectable only if it was externally cited, and A-5 R-6 (F-14) rules that
the newest record is always unanchored during normal operation. The two
rulings are consistent and the consequence is uncomfortable: **the
window is exactly the window the anchor cannot cover.** That is stated
here rather than left for a Phase C engineer to discover.

### 4.6 R-6 — Conflict handling: three named cases, one governing principle

**Governing principle, ruled first because all three cases follow from
it: an invalid chain is evidence of a governance event, and evidence is
not repaired. It is disclosed.** Editing a chain to make verification
pass destroys the only record that the violation occurred, and it does so
by the same act that would conceal it. Nothing in Step 9 may offer a
repair, a renumber, a merge, a dedupe, or a `--force`.

**R-6.1 — Duplicate sequence numbers.**

1. **Chain-invalid, and verification refuses** — A-5 R-3.3, adopted
   unchanged, not softened (F-13).
2. **Not repaired.** No renumbering, no deduplication, no "keep the one
   with the correct predecessor hash", no tool that offers to fix it.
   None is built, and building one later is a new AD.
3. **The chain is retained exactly as it is.** The invalid file is the
   artifact of record. It is not deleted, not truncated back to the last
   valid record, and not moved aside.
4. **The response is a governance act**: a dated disclosure following
   Standard §5's correction-is-a-new-file discipline, plus a
   `decision_log.md` entry recording that the chain went invalid, when it
   was noticed, and what is consequently unknown. The disclosure states
   what cannot be reconstructed as unreconstructable rather than
   supplying a reconstruction.
5. **The cycle stops advancing.** AD-050's evidence precondition requires
   the chain *verified intact* before any append (F-11), so an invalid
   chain blocks every further transition until a human disposes of it in
   writing. **This is the actual enforcement A-9 delivers, and it is
   deliberately after the fact.**
6. **The derived phase becomes unknown, and unknown is correct.** Phase is
   derived, not stored, and the failure direction is designed to
   under-claim (F-12). A cycle whose chain is invalid has no provable
   current phase. That is a true statement, and it is the safe one.

**R-6.2 — Competing writers.** Two classes, separated because they have
different dispositions and collapsing them would overstate the second.

*Class 1 — two invocations of the authorized path.* Violates the R-4
assumption. Disposition: R-5's table. Duplicate and gap are chain-invalid
and handled by R-6.1; **the lost-update shape is undetectable and is
disclosed as such** (§6.3). No mechanism is added for any of the three.

*Class 2 — an unauthorized writer.* A hand edit, an ad-hoc script, a
future module that ignores R-3, or any process with filesystem access.
Ruled:

- **A-9 does not reach this at all, and does not pretend to.** R-3 is an
  authority model over this system's design; it cannot constrain a
  process that is not part of this system.
- **What detects it is what detects tampering generally**, and no more:
  the hash chain catches mutation, reorder, insertion and interior
  deletion; the anchor catches truncation at or below the last cited
  sequence number (A-5 §6.1). A *well-formed record appended by hand* is
  caught by none of them.
- **The chain makes no authorship claim.** There is no signature, no
  writer identity, and no attestation of origin (F-23). Ruled
  consequence, stated so AD-048 cannot imply otherwise: **the chain
  attests that bytes were not altered since they were written; it never
  attests who wrote them.** A record's `project_id`, timestamp and
  authorization record are claims made by whatever produced the line.

**R-6.3 — Ambiguous anchors.** A-5 §9 ruled that a citation naming a
duplicated sequence number is ambiguous and that verification refuses
rather than picking a record (F-15). A-9 adds what "refuses" forbids,
because a refusal with an obvious workaround is not a refusal:

1. **No tiebreak by timestamp.** Record timestamps are injected and
   self-asserted; A-5 §6.2 already rules that there is no proof of time.
   Choosing by timestamp resolves ambiguity by trusting exactly the field
   the compromised writer controls.
2. **No tiebreak by "the one whose hash matches the citation".** This
   looks compelling and is circular: it makes the citation define which
   record is real, when the citation's entire evidentiary value is being
   an *independent* witness of a record that already was.
3. **No tiebreak by file order, by longest valid prefix, or by
   plausibility.** Each invents a fact.
4. **Resolution is a human governance act with a written outcome**, and
   its permissible outcomes include *"the true state cannot be
   reconstructed"*. That outcome is recorded, not avoided.
5. **An ambiguous anchor does not invalidate the citation.** The
   `decision_log.md` entry stands as written and is never edited — it is
   an append-only artifact (A-5 R-4.3 item 4). What is recorded is that
   the chain can no longer be matched against it.

### 4.7 R-7 — Re-affirmed rejections and the conditionality trigger

Stated so they cannot be reopened by omission.

1. **No lock, in any form** — OS advisory lock, mandatory lock, lock
   file, PID file, sentinel file, mutex, semaphore, single-instance
   guard, work queue, or serializing daemon. Closed by R-2, reopenable
   only by a new AD that argues against R-2's five grounds on their
   merits.
2. **No database, and no database locking.** There is no database in this
   path — the only project-storage implementation is an in-memory dict
   (F-19) and the chain is a flat file (F-4). A transactional store is not
   a smaller change than a lock; it is a larger one, and it is not
   proposed.
3. **No writer-identity field.** AD-048's field set is closed and gains
   nothing here (F-23). A process id or user name would be a self-asserted
   string with the evidentiary weight of any other self-asserted string,
   while reading as an authorship attestation. Rejected on the
   claim-stronger-than-mechanism ground.
4. **No CI check, no git hook, no scheduled verification.** None exists
   (F-18), and A-9 introduces none. Verification runs when a human runs
   it — A-5 §6.2, adopted.
5. **The A-5 conditionality trigger fires.** A-5 §9 pre-committed that
   *if* A-9 ruled "stated assumption", A-5 §6.1's provenance claims become
   **conditional on that assumption and AD-048 must say so in those
   words** (F-15). **A-9 rules stated assumption. The condition is
   therefore live, and §8 states exactly what it obliges.**

---

## 5. Writer authority model

The model in one statement:

> **Authority over the chain is singular by design and checkable.
> Exclusivity over the file is singular by assumption and unchecked.
> Accountability for a record is singular by requirement and
> self-asserted. Three different kinds of "single", and AD-048 must never
> print the word without saying which one it means.**

Laid out as layers, each with what it establishes and what it cannot do:

| Layer | Property | Established by | Cannot do |
|---|---|---|---|
| **W0 — authority** | Exactly one module may append (R-3.1) | Design, pinnable by test in Phase C | Stop a process that is not part of this system |
| **W1 — reachability** | That module is reachable only via `core/research/lifecycle.py` (R-3.2) | The existing import boundary (F-8, F-9), enforced by B-1's linter | Stop a direct import written in defiance of the boundary before B-1 lands |
| **W2 — authorization** | Every append carries one explicit human authorization (R-3.3, F-10) | AD-050's required argument | Verify that the declared authorizer is who they say — Standard §4 records the level, never adjudicates it |
| **W3 — exclusivity** | At most one process appends to one chain at a time (R-4) | **Nothing. Assumption only** | Anything. It is a statement of practice |
| **W4 — detection** | Duplicate and gap are chain-invalid; the cycle stops advancing (R-5, R-6.1, F-11) | A-5 R-3.3 plus AD-050's precondition | See a lost-update (§6.3); see a well-formed hand-appended record (R-6.2) |
| **W5 — ownership** | The human operator owns the chain; the module is an instrument (R-3.3) | This ruling, in prose | Confer any technical property whatsoever |

**Reading the model correctly.** W0 – W2 are real and are the reason this
ruling is not merely "we assume one writer". W3 is an assumption and is
labelled as one at every point it is relied upon. W4 is post-hoc, partial,
and is A-5's mechanism rather than A-9's. W5 is documentation and is worth
exactly what documentation is worth. **The layers do not add up to
enforcement, and §7 claims exactly what they do add up to and nothing
more.**

---

## 6. Conflict handling — the operational summary

§4.6 rules; this section is the same content in the order an operator
meets it, and adds nothing.

### 6.1 What a verifier reports

| Observed | Verifier | Consequence for the cycle |
|---|---|---|
| Contiguous `1 … N`, links intact, `null` predecessor only at 1 | Valid | Advancement permitted, subject to every other AD-050 precondition |
| Duplicate `sequence_number` | **Refuses** | Chain-invalid. No advancement (F-11). Derived phase unknown (F-12) |
| Gap in `sequence_number` | **Refuses** | As above |
| Broken predecessor link | **Refuses** | As above |
| Cited `(seq, head)` matches no retained record | **Refuses** | As above; and the citation stands unedited (R-6.3 item 5) |
| Cited `seq` matches **two** records | **Refuses, without choosing** | R-6.3 |

### 6.2 What a human does about it

In order, and none of the steps is a repair:

1. **Stop.** The cycle does not advance (F-11).
2. **Retain the artifact unchanged** (R-6.1 item 3).
3. **Write a dated disclosure** under Standard §5's
   correction-is-a-new-file discipline, plus a `decision_log.md` entry
   (R-6.1 item 4).
4. **Record what is now unknown as unknown** — including, where it
   applies, that the true state cannot be reconstructed (R-6.3 item 4).
5. **A new chain, if one is ever started, is a new decision** with its own
   record. It does not inherit the old chain's claims, and the disclosure
   is what links them.

### 6.3 The one failure that is invisible — stated as a non-claim

**Ruled to be stated in AD-048 in substantially these terms, and not
softened:**

> If two authorized appends to the same chain interleave such that the
> second rewrite is computed from a prefix that does not include the
> first, the first record is lost and the resulting file is contiguous,
> correctly chained, and internally valid. **No mechanical check in this
> design detects that.** The anchor cannot cover it either, because the
> lost record is by definition the newest and the newest record is always
> unanchored (F-14). The only thing standing between this design and that
> outcome is the R-4 assumption, and the assumption is not enforced.

This is stated as a **non-claim rather than a risk**, deliberately. A risk
invites a mitigation and a residual-risk rating; a non-claim states that
the system does not know, which is the true position. **AD-048 may not
convert it into a risk with a mitigation, because no mitigation is being
built** (R-7.1).

---

## 7. Evidence claim boundary

### 7.1 The minimum valid governance claim

Ruled as the **maximum** AD-048 may assert on writer discipline, in three
parts:

**Claim W-1 — authority.** *Within this system, exactly one module writes
transition records, reachable through exactly one composition point, and
every write carries an explicit human authorization.*
Needs: the source, and B-1's boundary linter. **This claim is
mechanically checkable and is asserted unconditionally.**

**Claim W-2 — exclusivity.** *The system is operated on the assumption
that at most one process appends to a given chain at a time. Nothing
enforces the assumption.*
Needs: nothing — it is a statement of practice, and is asserted **as an
assumption**, never as a property.

**Claim W-3 — detection.** *If concurrent writes produce a duplicate or a
gap, chain verification refuses and the cycle cannot advance until a
human disposes of it in writing. If concurrent writes produce a lost
update, nothing detects it.*
Needs: A-5 R-3.3 and AD-050's precondition. Asserted with **both halves
together, never the first alone.**

**The honest summary, which AD-048 must carry in these terms:**

> Single-writer discipline here means *one authorized writer by design and
> one accountable authorizer per record* — not *one writer by
> enforcement*. The design narrows who is supposed to write. It does not
> narrow who can. Two of the three ways that assumption can break are
> detected after the fact; the third is not detected at all.

### 7.2 What is explicitly NOT claimed

Each line is a non-claim, and each names the reason it would otherwise be
assumed.

| Not claimed | Because |
|---|---|
| **OS-level locking** | No `fcntl`, `msvcrt`, `flock`, `filelock` or `portalocker` appears anywhere in `core/` or `tools/` (F-3), and R-2 rules that none is introduced. No advisory lock, no mandatory lock, no lock file, no PID file, no sentinel |
| **Database locking** | There is no database on this path. Project storage is a plain in-memory dict (F-19); the chain is a flat file rewritten by `path.write_bytes` (F-4). There is no transaction, no row lock, no isolation level, and nothing that could provide one |
| **Runtime prevention** | No mutex, semaphore, queue, single-instance guard, process registry, daemon, or supervisor. Nothing is running between operator sessions to prevent anything (F-18) |
| **Automatic enforcement** | Nothing checks the assumption at write time. `advance_phase()` verifies the chain is *intact* before appending (F-11); it cannot verify that no one else is appending *concurrently*, and it does not try |
| **Atomicity of the read-modify-write** | Temp-plus-replace, which AD-048 requires of Phase C (F-5), makes the replacement atomic and the read-modify-write **not** atomic. The lost-update window is unaffected by it (R-5) |
| **Detection of a lost update** | Structural, not incidental (§6.3). The surviving file is valid on every check the design has |
| **Any claim about who wrote a record** | No writer-identity field exists and none is added (F-23, R-7.3). The chain attests to bytes, never to authorship (R-6.2) |
| **That the declared authorizer is who they claim** | Standard §4 stores the declared reviewer level verbatim and does not validate the independence claim; AD-050 adopts this. Authorization is recorded, never adjudicated |
| **Protection against a hand edit** | A JSONL file on disk is writable by any process with filesystem access. R-3 binds this system's design, not the operating system (R-3, closing paragraph) |
| **That an invalid chain can be made valid** | It cannot, and no tool is provided that would try (R-6.1). Invalidity is disposed of by disclosure, not by repair |
| **Anything about the three legacy archives** | They have no transition records and never will (A-8 §9.5). They have no writer to be single |

---

## 8. Relationship to A-5 — separation held, and the trigger discharged

**Separation, stated plainly and in A-5's own terms:** A-5 is about *what
a record's place in a chain can be shown to be, and by whom*. A-9 is about
*who is permitted to put a record there*. A-9 names no anchor, defines no
citation, fixes no numbering origin, and adds no verification step. A-5
restricts no writer, names no writer, and introduces no lock. Neither
record's rulings may be cited as deciding the other's question.

**Where they touch, and A-9 does not exceed it:** A-5 §9 ruled A-9's
dependency in advance rather than discovering it later, and A-9 now
discharges that table row by row.

| A-5 §9 row | A-5's ruling | A-9's disposition |
|---|---|---|
| **What is anchored** | A well-formed chain — contiguous from 1, one record per transition | A-9 does not guarantee well-formedness. It states the assumption under which it holds (R-4) and what a verifier sees when it does not (R-5) |
| **Concurrency damage** | *Detectable*: duplicate or non-contiguous `sequence_number` is chain-invalid; a lost interleaved write appears as a gap | **Adopted with one correction that A-9 owes A-5 and states rather than eliding.** A lost interleaved write appears as a gap **only when the writers assigned different sequence numbers.** In the last-writer-wins shape, both assign the same number and the survivor leaves **no gap at all** (§6.3). A-5's row is right about the case it names and does not reach this one |
| **Anchor validity under a violation** | A citation naming a duplicated sequence number is ambiguous, and ambiguity is a failure — verification refuses rather than picking a record | Adopted unchanged, and extended only by R-6.3's list of tiebreaks that "refuses" forbids |
| **If A-9 rules "stated assumption"** | *"Then §6.1's claims are **conditional on that assumption**, and AD-048 must say so in those words rather than asserting them unconditionally"* | **This branch fires** (R-7.5). A-5 wrote *"§6.1's claims"* without qualification, and A-9 discharges it without qualification: **all of §6.1** — **Claim 1** (chain alone), **Claim 2** (chain plus a citation), **Claim 2a** (the entry-by-entry strengthening), **Claim 3** (chain plus citation plus commit), **and §6.1's honest summary** — is conditional on the R-4 assumption, and AD-048 must say so in those words. A-9 does not narrow A-5's trigger to a subset of its claims. §9 A9-C8 carries it |
| **If A-9 rules "mechanical lock"** | §6.1's claims stand as written | **Does not fire.** Recorded so a later reader does not select the wrong branch |

**The correction in row 2 is the only place A-9 speaks back to A-5**, and
it is deliberately narrow: it corrects the *coverage description* of a
detection mechanism, not the mechanism, not the ruling, and not any A-5
claim. A-5 R-3.3 stands exactly as written. Under
`ARCHITECTURE_DECISIONS.md`'s preamble rule, this is stated explicitly
rather than left to be inferred from a disagreement between two records.

---

## 9. Relationship to AD-048

AD-048 is a **draft**. This record does not edit it (§11). When it is
written into `ARCHITECTURE_DECISIONS.md` under A-2, it carries the
following, and A-9 closes at that point.

**Numbering hazard, disclosed.** A-5's consequence list and A-8's both
number from `C-1` (F-25), and this one would make a third. **A-2 must
carry all three sets under distinguishing prefixes** — the content is
disjoint and the labels are not. The items below are cited as **A9-C1 …
A9-C10** for that reason, and A-2 should apply the same treatment
retroactively to A-5's and A-8's lists when transcribing them.

| # | Required of AD-048 | Source |
|---|---|---|
| A9-C1 | **Never print "single writer" undifferentiated.** State the three properties separately — authority (design, checkable), exclusivity (assumption, unenforced), accountability (human, self-asserted) — and say which one any given sentence means | R-1 |
| A9-C2 | Record the ruling as **stated assumption, not mechanical lock**, with R-2's five grounds, and record that a lock is closed rather than deferred: reopening requires a new AD arguing against those grounds | R-2, F-1 |
| A9-C3 | State the authority model: one writing module, reachable only through `core/research/lifecycle.py` (F-9), every append carrying one explicit human authorization (F-10); and state that this binds the design, not the filesystem | R-3 |
| A9-C4 | Carry the R-4 assumption **verbatim in strength**, scoped **per chain file** (F-16), including the sentence "Nothing enforces this", and require the artifact header to carry it beside the chain's narrow tamper-evidence claim | R-4 |
| A9-C5 | State that enforcement is **detection, not prevention**, that the detection is A-5 R-3.3's contiguity rule rather than anything A-9 adds, and that an invalid chain **blocks further advancement** via AD-050's precondition (F-11) — which is the actual enforcement, and is after the fact | R-5, R-6.1 |
| A9-C6 | **Disambiguate "written atomically"** (F-5): temp-plus-replace makes the *replacement* atomic and the *read-modify-write* not atomic, and does nothing about last-writer-wins. Say which is meant, in those words | R-5 |
| A9-C7 | Carry §6.3's undetectable lost-update case **as a non-claim, not as a risk with a mitigation**, since no mitigation is built | §6.3, R-7.1 |
| A9-C8 | State **the whole of A-5 §6.1** as **conditional on the R-4 assumption**, in those words — **Claim 1**, **Claim 2**, **Claim 2a**, **Claim 3**, **and §6.1's honest summary**, none omitted. A-5 §9's trigger names *"§6.1's claims"* without qualification, and A-9 discharges it without qualification; **AD-048 may not carry the condition on a subset**, because a §6.1 claim printed unconditionally beside conditional ones will be read as the one that survived the assumption. The branch A-5 §9 pre-committed and that R-7.5 now fires | R-7.5, F-15 |
| A9-C9 | Carry §7.2's non-claims explicitly: no OS-level locking, no database locking, no runtime prevention, no automatic enforcement, no atomicity of the read-modify-write, no detection of a lost update, **no authorship claim of any kind** (F-23), no protection against a hand edit | §7.2 |
| A9-C10 | Record conflict handling: duplicate and gap are chain-invalid and **not repaired, not renumbered, not deduplicated**; the invalid artifact is retained unchanged; the response is a dated disclosure plus a decision-log entry; the derived phase becomes unknown and unknown is correct (F-12); and ambiguity is never resolved by timestamp, by matching the citation, or by plausibility | R-6 |

**What is unchanged in AD-048 by this record:** its field set (A-9 adds
**no** field, F-23), its storage decision, its
transcription-not-certification claim, its refusal to commit, A-8's
location rulings, and A-5's anchoring rulings C-1 … C-13. This record
speaks only to who may write, under what assumption, and what happens
when the assumption fails.

**Required of AD-050 rather than AD-048:** nothing new. A-9 relies on
AD-050's existing authorization requirement (F-10) and its existing
evidence precondition (F-11) and adds no clause to either.

**Required of the Resolution's Phase C exit-criteria wording:** the phrase
*"single-writer **enforced** as decided in A-9"* (F-2) is, under this
ruling, satisfied by disposition rather than by enforcement. The
Resolution is **not edited** by this record (§11); AD-048 states the
substitution, and §12 item 1 states what actually meets the criterion.

---

## 10. Effect

| Item | Status after this record |
|---|---|
| **A-9, question 1 — what "single writer" means** | **Decided:** three separable properties — exclusive **authority** (design, checkable), exclusive **process** (assumption, unenforced), documented **ownership** (human operator, self-asserted). Not one of them alone, and never collapsed into one word. §4.1 |
| **A-9, question 2 — minimum valid governance claim** | **Decided:** one authorized writer by design and one accountable authorizer per record; exclusivity asserted only as an assumption; detection stated with both halves, including the half that detects nothing. §7.1 |
| **A-9, question 3 — what is not claimed** | **Decided:** no OS-level locking, no database locking, no runtime prevention, no automatic enforcement, no atomic read-modify-write, no lost-update detection, no authorship claim, no protection against a hand edit. §7.2 |
| **A-9, question 4 — conflict handling** | **Decided:** duplicates and gaps are chain-invalid and verification refuses; nothing is repaired or renumbered; the artifact is retained and disclosed; the cycle stops advancing and the derived phase becomes unknown; ambiguous anchors are never tiebroken. §4.6, §6 |
| **A-9, question 5 — separation from A-5** | **Held**, and A-5 §9's conditionality trigger is **discharged** — the "stated assumption" branch fires. §8 |
| **The Resolution's binary (F-1)** | **Answered: stated assumption.** The mechanical-lock branch is closed with grounds, not deferred. §4.2 |
| **A-9 as a prerequisite** | **Decided in writing, not yet closed.** Closes when AD-048 is written and accepted under A-2 carrying A9-C1 … A9-C10. §1 |
| **A-2** | **Open, unchanged.** This record adds required content to AD-048 and a numbering-hygiene requirement (F-25); it writes and accepts nothing |
| **A-1, A-6, A-8, A-5** | **Ruled on at `aca36fb`, `3ee23fd`, `e76bafe`, `f7802fe`.** Not re-decided, not reopened. A-5's §9 row 2 coverage description is corrected in scope only, explicitly, at §8 |
| **A-3, A-4, A-7** | **Open, unchanged.** Not spoken to |
| **Step 9** | **Blocked, unchanged.** Resolution §4.1's rule — "Step 9 does not start until every item below is closed in writing" — is unchanged and unrelaxed |
| **Lost-update exposure** | **Disclosed and open, not eliminated and not mitigated.** Undetectable by every check in the design (§6.3) |
| **`core/governance/canonical_jsonl.py`** | **Unedited.** F-4 is a fact recorded about it, not a defect filed against it |

**How to re-run this ruling.** Every input is named so a later reader need
not trust this document: the binary and its "done when" against
`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:478`; the Phase C exit criterion
against `:491`; the absence of any locking primitive by searching `core/`
and `tools/` for `fcntl`, `msvcrt`, `flock`, `filelock`, `portalocker` and
`os.replace`; the whole-file rewrite against
`core/governance/canonical_jsonl.py:24-33` compared with
`PHASE_4_STEP9_DRAFT_ADRS.md:144-150`; the single-operator fact against
`RESEARCH_GOVERNANCE_STANDARD.md:399`; the read-only posture against
`core/governance/freeze_verifier.py:40-43`; the import boundary against
`tools/check_import_boundaries.py:64`; the authorization requirement
against `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:230-243`; the evidence
precondition against `PHASE_4_STEP9_DRAFT_ADRS.md:457-461`; the closed
field set against `PHASE_4_STEP9_DRAFT_ADRS.md:121-131`; the absence of CI
by listing the repository root; the storage implementation against
`core/research/project_repository.py:5-12,37-48`; and A-5's pre-committed
conditionality against `PHASE_4_A5_CHAIN_ANCHORING_RULING_2026-07-22.md`
§9.

---

## 11. Explicit non-actions

Stated as prohibitions honoured by this record, each verifiable against
the diff:

- **No lock is implemented.** No file lock, advisory lock, mandatory
  lock, lock file, PID file, sentinel file, mutex, semaphore,
  single-instance guard, queue, daemon, or supervisor — in code, in
  configuration, or on disk.
- **No code is modified or created.** `core/governance/`,
  `core/research/`, `core/shared/`, `core/validation/`, `tools/`, and
  every test file are untouched. In particular
  `core/governance/canonical_jsonl.py` is **not** modified: F-4 records
  what it does and R-5 records the consequence; no atomic-write helper is
  added here.
- **No writer code is created.** No `DecisionRecorder`, no append path,
  no path constant, no serializer, no hash function, no `advance_phase()`.
- **No verifier is implemented**, and no new verification rule is
  invented — R-5 consumes A-5 R-3.3 and adds no check.
- **No runtime enforcement of any kind is added.** Nothing checks the R-4
  assumption at write time, at start-up, or on a schedule; no CI job and
  no git hook is created, and F-18 records that none exists to modify.
- **No ADR file is modified.** `PHASE_4_STEP9_DRAFT_ADRS.md` is retained
  unedited; §9 states what AD-048 must carry and changes nothing in the
  draft. `ARCHITECTURE_DECISIONS.md` is not modified — no AD is added,
  amended, renumbered, accepted, or marked superseded.
- **`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md` is not edited**, including
  its Phase C exit-criteria wording (F-2), whose reading is corrected in
  AD-048 rather than in the Resolution.
- **No Phase B architecture is decided.** No `LifecyclePhase`,
  `advance_phase()`, `GateRunner`, `ProjectRegistry` change, repository
  implementation, or linter change is designed or authorized here. R-3.2
  records that the existing import boundary already carries the writer
  boundary; it does not modify the boundary or the linter.
- **No Phase C artifact is created**, and no schema, dataclass, key set,
  or test is written.
- **No field is added to any record type**, and no writer-identity,
  process, host, session, or signature field is introduced (R-7.3).
- **No A-5 or A-8 ruling is amended.** §8 corrects the *scope of a
  coverage description* in A-5 §9 row 2 and amends no ruling, no claim,
  and no file. `PHASE_4_A5_CHAIN_ANCHORING_RULING_2026-07-22.md` and
  `PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md` are
  untouched.
- **No `decision_log.md` is edited or appended to**, and
  `docs/templates/decision_log_template.md` is not edited — A-5 R-4.2's
  template amendment remains bound to A-2's increment and is not
  performed here.
- **`RESEARCH_GOVERNANCE_STANDARD.md` is not amended.** §5's package is
  read as a closed enumeration (F-17), not extended with a lock file or
  anything else.
- **No file or directory is created under `research_archive/`.** No
  `transition_records.jsonl` exists anywhere in the repository, and none
  is created here.
- **A-3, A-5 and A-8 are not decided or reopened**, and A-9 decides
  nothing about anchoring, location, identity, or authorization policy.
- **No hypothesis, gate determination, or research conclusion is made.**
- **No commit is made by this record.**

---

## 12. Future implementation boundary

Carried forward, in the increment each belongs to. None is a new
requirement on anyone; each is a disclosed consequence of a ruling above.

1. **Phase C's exit criterion is met by disposition, not by
   enforcement.** *"Single-writer enforced as decided in A-9"* (F-2) is
   satisfied by exactly four things: (a) the authority boundary is real
   and pinned by test — no module other than the recorder references a
   transition-chain path (R-3.1); (b) the R-4 assumption is stated
   verbatim in the artifact header (R-4); (c) A-5 R-3.3's contiguity and
   genesis checks are implemented (R-5); and (d) §6.3's undetectable case
   is disclosed in the artifact and in AD-048 (A9-C7). **A Phase C
   implementation that adds a lock has exceeded its boundary and needs a
   new AD; one that omits (d) has not met the criterion and must not be
   recorded as having met it.**
2. **Phase C must not present temp-plus-replace as concurrency safety**
   (A9-C6). If the implementation adds atomic replacement — and AD-048
   requires it (F-5) — its docstring and its test names must say
   *"atomic replacement"*, never *"atomic append"* and never
   *"concurrency-safe"*.
3. **Phase C must not build a repair path.** No renumbering utility, no
   dedupe, no truncate-to-last-valid, no `--force`. R-6.1 forbids it, and
   a helper that "fixes" a chain destroys the evidence that it broke.
4. **Phase B-3 (`advance_phase()`) enforces nothing about writers**, and
   must not be written as though it does. Its chain-intact precondition
   (F-11) is a check on the *artifact*, not a check on *who else is
   running*. If a future increment wants a concurrency check there, that
   is a new AD against R-2.
5. **Phase E's end-to-end traversal cannot demonstrate single-writer
   discipline**, because there is nothing to demonstrate — the property is
   an assumption. An adversarial test that simulates concurrent writes
   demonstrates the *detection* in R-5's first two rows and must be
   labelled as such; a test that simulates a lost update will find that
   the design does not detect it, and **that result is the expected one
   and must be recorded, not fixed** (§6.3).
6. **If a second operator, an automated runner, or a hosted deployment
   ever becomes real, R-2's third ground lapses** and A-9 must be
   reopened as a new decision. That trigger is named here so the change
   is noticed as a governance event rather than absorbed as an
   operational detail: **the ruling below is scoped to a single-operator
   platform (F-6), and it says so.**
7. **If the lost-update exposure is ever judged unacceptable**, the
   reopening is a new decision against R-7's closed list — not an
   extension of this one. It would have to argue against R-2's five
   grounds on their merits, and it should expect ground 4 in
   particular — that a lock does not constrain the actor in the threat
   model (F-20) — to be cited against it.
