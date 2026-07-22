# Phase 4 / Step 9 — A-5 Ruling Record (chain-anchoring mechanism)

**Date filed:** 2026-07-22
**Repository state ruled against:** canonical `D:\Claude\etf_platform`, `master`, HEAD `e76bafe`, working tree clean.

**Dating note, disclosed rather than smoothed over.** This record was
authored in the same continuous effort as the A-6 (`3ee23fd`) and A-8
(`e76bafe`) rulings and carries their filing date and filename
convention. That effort ran past 2026-07-22 UTC into 2026-07-23. The
filename and filed date are retained as `2026-07-22` because the
requesting instruction fixed them; nothing in this record depends on
which of the two dates is taken as authoritative, and no claim below is
scoped by date. Standard §5's requirement (F-21) is satisfied either
way — this file is dated in both its filename and its content.

---

## 1. Status

**Status: ruling record.** It disposes of prerequisite A-5 and of nothing
else. It is **not** an ADR, **not** an amendment to any ADR draft, **not**
a schema, **not** a storage or verification mechanism, and **not** a
Phase B artifact.

**Prerequisite addressed:**
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
§4.1 row A-5 — *"Chain-anchoring mechanism decided (§2.2's replacement)"*,
whose "Done when" column reads **"Recorded in AD-048"**.

**A-5 is decided by this record. A-5 is not closed by this record**, and
this record does not claim otherwise. The distinction is the one
[`PHASE_4_A6_RESEARCH_IDENTITY_RULING_2026-07-22.md`](PHASE_4_A6_RESEARCH_IDENTITY_RULING_2026-07-22.md)
(`3ee23fd`) drew for A-6 and
[`PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md`](PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md)
(`e76bafe`) drew for A-8, and it holds here for the same reason:

- A-5's "Done when" condition is *recorded in AD-048*. AD-048 does not
  exist in [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) — the
  accepted set runs AD-001 … AD-046 plus AD-051 (F-19), and AD-047 … AD-050
  exist only as drafts in
  [`PHASE_4_STEP9_DRAFT_ADRS.md`](PHASE_4_STEP9_DRAFT_ADRS.md). Writing
  them in is **A-2**, a separate prerequisite.
- This record supplies the **decided content** A-5 requires and fixes it
  in writing at a date, so A-2's transcription has something settled to
  transcribe. **A-5 closes when AD-048 is written and accepted under A-2
  carrying the decisions in §4 below, together with the carrier amendment
  R-4 binds to that same increment.** Until then A-5 stays open, and
  Step 9 stays blocked on it exactly as it stood at `e76bafe`.

**No file is edited by this record, and no code is introduced by it.**
This is a new, dated file.
[`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md),
[`PHASE_4_STEP9_DRAFT_ADRS.md`](PHASE_4_STEP9_DRAFT_ADRS.md),
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md),
[`RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md),
[`RESEARCH_LINEAGE_REGISTER.md`](RESEARCH_LINEAGE_REGISTER.md),
[`RESEARCH_ARCHIVE_MANIFEST.md`](RESEARCH_ARCHIVE_MANIFEST.md) and
[`templates/decision_log_template.md`](templates/decision_log_template.md)
are all retained unedited, and each is cited below by section or line
rather than amended. **In particular, R-4 decides that the decision-log
template gains an anchor field and does not add one** (§4.4, §11).

**Supersession discipline.** Same convention, and the same disclosed
limitation on its scope, as the A-1, A-6 and A-8 ruling records:
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
Level 3 is unavailable on this platform. This is not a lifecycle Decision
in the Standard §2/§7 sense — no research conclusion, no gate
determination, no step toward capital allocation is made here.

**Verification basis.** Every factual claim in §3 was checked directly
against the canonical repository at `e76bafe` — file contents, `git
ls-files`, and the working tree — and each carries its source. No claim
rests on an off-repo artifact, and no claim rests on the assertion of an
earlier document that was not itself re-read.

---

## 2. Scope

**In scope — exactly five questions, no more:**

1. What anchors a machine-artifact chain.
2. The minimum provenance claim: what the system can truthfully prove.
3. What is explicitly **not** claimed.
4. The missing-carrier problem: where an anchor citation physically
   lives, in what format, and who writes it.
5. Keeping anchoring (A-5) separate from writer authority (A-9).

**Out of scope, and not decided here:** every other Phase A
prerequisite — A-1 (ruled on at `aca36fb`), A-6 (`3ee23fd`), A-8
(`e76bafe`); A-2, A-3, A-4, A-7, A-9 untouched and open on their own
terms. In particular:

- **A-9 (single-writer enforcement) is not decided here.** §9 records
  precisely how A-5's guarantee *depends* on A-9's answer and what a
  concurrency violation looks like to a verifier. Whether concurrency is
  prevented by a stated assumption or a mechanical lock is A-9's, and
  nothing in §4 may be cited as deciding it.
- **A-8's location ruling is not reopened.** The chain path
  `<archive_root>/<cycle_name>/transition_records.jsonl` (F-4) is taken
  as settled input. A-5 supplies exactly the three things A-8 explicitly
  deferred to it (F-3): the numbering **origin**, the anchor's **format**,
  and the **verification procedure**.
- **AD-048's field set is not reopened.** A-5 introduces **no new field**
  to the transition record (§4.3). It fixes the semantics of two fields
  the draft already lists (F-2).
- **Whether the tail-truncation exposure is acceptable** is a governance
  acceptance question that AD-048's acceptance under A-2 answers. A-5
  states the exposure at its true size; it does not pronounce it
  tolerable.

**Phase A discipline is binding on this record.** Resolution §4.1 scopes
Phase A to "documents only, zero code". Nothing here writes a chain,
implements a verifier, defines a JSONL schema in code, creates a Phase B
artifact, or edits an ADR. See §11.

---

## 3. Facts established

Each row was verified directly at `e76bafe`.

| # | Fact | Source |
|---|---|---|
| F-1 | Resolution §2.2 **rejects** commit-on-every-append as the anchor and states the replacement as three parts: a monotonic `sequence_number`; a hand-authored `decision_log.md` entry citing **the chain head hash and sequence number**; and a **human-performed commit outside any run**. The rejection grounds are that the recorder would become a git writer, and that committing mid-run mutates the `git status --porcelain` working-tree state `verify_freeze` reads | `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:328-373`; `PHASE_4_STEP9_DRAFT_ADRS.md:170-178` |
| F-2 | AD-048's draft field set **already contains both fields anchoring needs**: `sequence_number`, and "the SHA-256 of the predecessor record's canonical serialization". No further field is required to anchor | `PHASE_4_STEP9_DRAFT_ADRS.md:121-128` |
| F-3 | A-8 explicitly deferred three things to A-5, verbatim: *"The numbering **origin**, the anchor's format, and the verification procedure are **A-5's and are not decided here**"*; restated as C-10 — *"`sequence_number` is scoped to the per-cycle file, and … its origin and the anchor's format remain A-5's"* | `PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md` §4.4, §6 C-10 |
| F-4 | The chain is one file per cycle at `<archive_root>/<cycle_name>/transition_records.jsonl`, at the cycle directory root, sibling of `decision_log.md`; `<archive_root>` is injected, never a module-level constant | A-8 R-2 |
| F-5 | `decision_log.md` is per-cycle, at `research_archive/<cycle_name>/decision_log.md`, and is **the one file in the Standard §5 package that is genuinely append-only in the literal sense** (entries added, nothing removed or edited) rather than superseded-by-new-file | `RESEARCH_GOVERNANCE_STANDARD.md:430,452-456` |
| F-6 | The decision-log template's field discipline is explicit: *"Every field is required; a field with nothing to report still gets an explicit value (`None`, `Not applicable`), **never a silently omitted line**"* | `docs/templates/decision_log_template.md:19-21` |
| F-7 | The template's entry shape is a level-3 heading `### Entry [N] — [YYYY-MM-DD]` followed by five bold-labelled paragraph fields: `**Decision.**`, `**Evidence references.**`, `**Governance status.**`, `**Reviewer level.**`, `**Known limitations.**` | `docs/templates/decision_log_template.md:23-42` |
| F-8 | **Neither decision log that actually exists follows that shape.** Both use a level-2 heading `## Entry N — <title>` with bullet fields (`- **Date:**`, `- **Evidence references:**`). `grep -c '^### Entry'` returns **0** for `research_archive/reference_h3/decision_log.md` | `research_archive/reference_h3/decision_log.md:19-30`; `research_archive/positive_control_phase3/decision_log.md:13-15,69` |
| F-9 | Exactly two `decision_log.md` files exist under `research_archive/` — `reference_h3/` and `positive_control_phase3/` — plus the template in `docs/templates/` | `git ls-files` |
| F-10 | `write_canonical_jsonl` serializes each row with `sort_keys=True, ensure_ascii=False, separators=(",", ":")`, joins with `"\n"`, appends exactly one trailing newline when there is at least one row, and writes UTF-8 bytes | `core/governance/canonical_jsonl.py:24-33` |
| F-11 | `read_canonical_jsonl` returns **`[]` for a zero-byte file**, without error, and otherwise rejects CR characters and a missing trailing newline | `core/governance/canonical_jsonl.py:36-51` |
| F-12 | The repository's existing hash-citation convention is the string prefix `sha256:` followed by lowercase hex — used by `sha256_of_file` and enforced on read by `dataset_manifest` | `core/governance/canonical_jsonl.py:54-58`; `core/governance/dataset_manifest.py:65-67` |
| F-13 | **No hash chain of any kind exists in `core/governance/` today.** `ReproductionRecord` binds a hash *set* within one record; nothing links record *N* to *N−1* | `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:44,374-382` |
| F-14 | **Git history in this repository has already failed to be durable, as a matter of record.** The PR0 remediation record `docs/PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md` *"was destroyed in the 2026-07-21 incident and exists in no reachable ref"* | `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:74-79` |
| F-15 | INV-10: **no code writes `decision_log.md`**, and the closed field set plus transcription framing are what keep the mechanical record from replacing the human one | `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:534` |
| F-16 | AD-050's draft makes *"the decision chain verified intact **and anchored** before the append"* an **evidence precondition of any advance**, so a transition is never written onto a broken chain | `PHASE_4_STEP9_DRAFT_ADRS.md:457-461` |
| F-17 | Phase C's exit criteria require that *"interior deletion, mutation, reorder and forged-predecessor"* are all detected and that **"tail truncation [is] detectable via the anchor"**, with single-writer behaviour "enforced as decided in A-9" | `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:491` |
| F-18 | Governance may import **only** `data`: `ALLOWED_DEPENDENCIES["governance"] == frozenset({"data"})` | `tools/check_import_boundaries.py:64` |
| F-19 | The accepted AD set is AD-001 … AD-046 plus **AD-051** (*"An empty `covered_paths` set is `UNVERIFIABLE`, not `VERIFIED`"*), which explicitly leaves AD-047 … AD-050 reserved for the Step 9 drafts | `docs/ARCHITECTURE_DECISIONS.md:1288-1295` |
| F-20 | A-8 R-3.5 forbids any store outside the repository, **precisely because** the anchor requires a human-performed commit of a tracked file: *"an artifact that git does not track cannot be anchored that way at all"* | A-8 §4.3 item 5 |
| F-21 | Standard §5's dating rule is *"Every file is dated in its own content **or** filename"* | `RESEARCH_GOVERNANCE_STANDARD.md:439-443` |
| F-22 | The Governance domain's read-only posture is stated in the module that defines it: *"nothing in this module ever writes, commits, checks out, or resets anything"* | `core/governance/freeze_verifier.py:41-43` |
| F-23 | `RESEARCH_LINEAGE_REGISTER.md`'s subject is defined narrowly: it tracks *"every mechanism/target-space that has been made subject to a Phase 3 construction-attempt cap"*, and it is platform-level **human prose** | `RESEARCH_LINEAGE_REGISTER.md:9-31` |
| F-24 | A-8 R-1 ruled that the platform-level tier is human prose and **stays that way**: *"Step 9 introduces no platform-level machine artifact"* | A-8 §4.1 property 1 |

---

## 4. Decision

Seven rulings, R-1 … R-7. Each is stated in the form it is to be
transcribed under A-2.

### 4.1 R-1 — What anchors a chain: nothing inside it

**Ruled: the anchor is an external, human-authored witness of a specific
chain state. The chain does not anchor itself, `sequence_number` is not
an anchor, and the git commit is not the anchor.**

The three parts Resolution §2.2 names (F-1) have **three different roles**,
and conflating them is how an anchoring claim gets stronger than its
mechanism. They are ruled apart:

| Part | Role | Is it the anchor? |
|---|---|---|
| `sequence_number` (in the record) | **Ordering and interior completeness.** Makes interior deletion visible without rehashing, and gives the anchor something short and human-transcribable to name | **No.** It is what an anchor *names*. Alone it proves nothing: the whole file, sequence numbers included, can be rewritten from scratch by the actor who wrote it |
| predecessor hash (in the record) | **Interior integrity.** Binds record *N* to record *N−1* so mutation, reorder, insertion and interior deletion break a link | **No.** Self-contained: a truncated chain and a fresh genesis chain are both perfectly valid (F-1) |
| **the citation `(cycle, sequence_number, head hash)` in the cycle's `decision_log.md`** | **External witness.** A statement, made by a human in a different artifact under a different discipline, that the chain had a specific length and a specific head at a specific time | **Yes. This is the anchor.** |
| the human-performed commit | **Retention and co-visibility.** Puts the chain and its witness into one tracked state, so a later divergence appears as a diff on tracked files rather than as an unobservable edit | **No.** It is what preserves the anchor and makes tampering visible; it is not what makes the claim |

**Why the commit is explicitly ruled *not* to be the anchor**, beyond the
role distinction: this repository has already demonstrated that its git
history is not durable. The PR0 remediation record was destroyed and
*"exists in no reachable ref"* (F-14). A mechanism whose durability
assumption the repository's own history has falsified inside the last
two days cannot be the thing the claim rests on. It remains valuable —
it is the difference between a silent edit and a reviewable diff — and it
remains **required** by A-8 R-3.5 (F-20). It is not load-bearing for the
provenance claim, and no AD-048 text may imply that committing the file
makes it immutable (§6.2).

### 4.2 R-2 — Anchor content and hash domain

**Ruled: an anchor citation consists of exactly three elements, and the
head hash is the hash of a record, not of a file.**

| Element | Ruled value |
|---|---|
| **Chain identity** | The repository-relative path of the cycle's chain file, `research_archive/<cycle_name>/transition_records.jsonl` (F-4). Written in full rather than as a bare `cycle_name`, so a reader who has only the citation can find the file |
| **Sequence number** | The `sequence_number` of the record being witnessed — the record produced by the transition that entry describes (R-4.3) |
| **Head hash** | `sha256:<64 lowercase hex>` (F-12), computed over **the UTF-8 bytes of that record's canonical JSON serialization — the exact line `write_canonical_jsonl` emits for it (F-10), excluding the terminating LF** |

**Why the record's serialization and not the file's bytes.** Three
grounds, the first decisive:

1. **The cited value must remain checkable after further appends.** A
   whole-file hash is invalidated by the very next append, so a citation
   made at sequence 3 becomes uncheckable the moment sequence 4 is
   written — which is to say, immediately, and permanently. A record hash
   is stable forever: the bytes of record 3 do not change when record 4
   is appended.
2. **It is a value already in the file.** The hash cited for record *N*
   is **byte-identical to the predecessor-hash field stored in record
   *N+1*** (F-2). A human verifying an old citation can therefore compare
   it against a field the file already carries, with no recomputation at
   all; only the current head requires hashing a line. This is a property
   worth having and it is free.
3. **It hashes a record, and a record is what the chain is made of.** A
   file-region hash would silently bind the citation to formatting
   concerns (trailing newline, position in the file) that are not
   properties of the record.

**Excluding the terminating LF** keeps the value a property of the
record rather than of its position in the file, and keeps it identical
whether the record is currently the last line or an interior one.

**Rejected, and closed:** a Merkle root or hash-of-hashes (no consumer,
and the length problem is unchanged); a running "chain hash" field
distinct from the predecessor hash (a second representation of the same
fact — the defect Resolution §2.1 rejected `Project.current_phase` for);
a whole-file hash (above); any digest algorithm other than SHA-256 (the
repository has exactly one convention, F-12, and a second would need a
reason that does not exist).

### 4.3 R-3 — Numbering origin, genesis, and contiguity

A-8 deferred the numbering origin to A-5 (F-3). Ruled:

1. **Origin is 1.** The first transition record of a cycle carries
   `sequence_number = 1`. Consequence, and the reason: **the head's
   sequence number is identical to the record count**, so a cited `N` is
   directly a claim that the chain contained `N` records. Under 0-origin
   the count is `N+1` and every reader performs an arithmetic step in
   which an off-by-one truncation hides.
2. **Numbering is per-file and restarts per cycle**, following A-8 R-4:
   sequence numbers are not global and do not order transitions across
   cycles. A citation is therefore meaningless without its chain-identity
   element, which is why R-2 makes that element mandatory rather than
   inferred from the entry's surrounding file.
3. **Sequence numbers are contiguous ascending integers `1 … N` with no
   gaps and no duplicates.** A gap or a duplicate is a **chain-invalid**
   condition — verification refuses; it is not repaired, not renumbered,
   and not reported as a warning.
4. **The genesis record's predecessor-hash field is JSON `null`, and the
   key is present.** Never an omitted key (the serialized key set is
   closed and pinned by test — omitting it changes the key set and fails
   that test), never an empty string, never a sentinel like
   `"sha256:0000…"` or the SHA-256 of the empty string (each of which is
   a value that could be *computed* and therefore *forged into* an
   interior position, whereas `null` at any position other than sequence
   1 is a structural error a verifier detects trivially).
5. **A zero-byte chain file is a valid empty chain, not an error** —
   `read_canonical_jsonl` returns `[]` for it (F-11). This is stated as a
   ruled consequence because it is the exact shape of total truncation:
   a chain emptied to zero bytes is indistinguishable, *from the file
   alone*, from a cycle that has never transitioned. Only the external
   witness distinguishes them, which is the clearest statement of why
   R-1's anchor is not optional.

**No field is added to the transition record by this ruling.** Both
fields anchoring needs already exist in AD-048's draft set (F-2); R-3
fixes their semantics and nothing else. The closed field set stays
closed.

### 4.4 R-4 — The carrier: both mechanisms, with split ownership

The audit's finding is accepted in full: **an anchor mechanism needs an
actual place where the anchor citation exists**, and at `e76bafe` no such
place exists — Resolution §2.2 and AD-048's draft (F-1) say the
decision-log entry "cites the chain head hash and sequence number", while
the decision-log template (F-7) has no field for it and the two decision
logs that exist do not follow the template's shape at all (F-8). A format
with no slot is a claim with no mechanism; a slot with no format is
unverifiable. **Ruled: both, with ownership split, and neither alone.**

#### R-4.1 — AD-048 owns the format

The citation grammar is defined normatively in AD-048, in exactly one
place, as a **single line** in this fixed order:

```
**Machine chain anchor.** `research_archive/<cycle_name>/transition_records.jsonl` — seq `<N>`, head `sha256:<64 lowercase hex>`
```

Worked example of the form the line takes (illustrative values, naming
no real chain — no chain exists at `e76bafe`, F-13):

```
**Machine chain anchor.** `research_archive/reference_h4/transition_records.jsonl` — seq `1`, head `sha256:<64 lowercase hex>`
```

Ruled properties of the grammar:

- **One line, self-locating.** A reader must be able to find it by
  looking for the bold label alone, without the surrounding entry
  conforming to any particular shape. This is not aesthetic: **both**
  existing decision logs already diverge from the template's entry shape
  (F-8), so a carrier defined as "the fourth bold field of a level-3
  entry heading" would already be unsatisfiable by two of two real files.
  The label carries the field; the entry shape does not.
- **No version token.** A version token implies a parser with a version
  switch, and no parser exists or is authorized (R-5.3). A change to this
  grammar is a new AD, and existing citations are never rewritten — they
  sit in an append-only file (F-5).
- **`Not applicable` is an explicit, valid value**, per the template's
  own discipline (F-6). It is the correct value for every entry that
  records no phase transition, and for every cycle that has no chain.

#### R-4.2 — `decision_log_template.md` owns the slot

**Ruled: `docs/templates/decision_log_template.md` gains one new required
entry field, `**Machine chain anchor.**`, carrying the R-4.1 line.** The
template's existing rule — every field required, `Not applicable`
permitted, *"never a silently omitted line"* (F-6) — is precisely what
converts the citation from a convention someone may remember into a slot
whose absence is visible. That rule is adopted, not restated, and not
weakened.

Placement within the entry: **after `**Evidence references.**` and before
`**Governance status.**`**. It is a citation, of the same class as
evidence references, and it must not be confused with a judgment field.

**This record does not amend the template.** The amendment is a
documentation-only change **bound to A-2's increment** — the same
increment that writes AD-048 into `ARCHITECTURE_DECISIONS.md` — so that
the format and its carrier land together and both land **before Phase C
can produce anything to cite**. Landing the format without the slot is
the failure mode this ruling exists to close; landing the slot without
the format gives readers a field with no defined content.

#### R-4.3 — Placement, cardinality, and the one-to-one rule

1. **One citation per entry, in every entry.** Entries recording no
   transition carry `Not applicable`, so a reader can always distinguish
   *no anchor because no transition* from *anchor omitted*.
2. **A transition entry cites its own record.** `N` is the
   `sequence_number` of the record that the transition described by that
   entry produced — not the chain head at some later time, and not the
   predecessor. This yields a **one-to-one correspondence between
   transition entries and cited sequence numbers**, which is a real
   strengthening and is claimed as one in §6.1: the human log carries an
   entry-by-entry external witness of the numbering, not merely a single
   high-water mark.
3. **Ordering is fixed and is not negotiable:** human authorization
   (Resolution §1.5) → the mechanical append → the human authors the
   entry citing the resulting record → the human commits both files
   together under existing archive discipline. The citation cannot name
   the commit that contains it — that hash does not exist when the line
   is written — and AD-048 must not require it to. The anchoring commit
   is identified after the fact by git, from the tracked file's history,
   not by any text inside the citation.
4. **Nothing is retrofitted.** Existing entries in
   `reference_h3/decision_log.md` and
   `positive_control_phase3/decision_log.md` are never edited (F-5, and
   the append-only discipline both files state in their own headers). The
   three legacy archives never receive a chain (A-8 §9.5), so they never
   receive a citation either. New entries appended to an existing log
   after the amendment carry the field.

#### R-4.4 — Carriers considered and rejected

| Candidate carrier | Ruled |
|---|---|
| The existing `**Evidence references.**` field, unamended | **Rejected.** It is a free-text bucket; an anchor placed there is optional in practice and unlocatable in principle. The audit finding is exactly that the anchor has no *place*; putting it somewhere it may or may not be is not a place |
| `RESEARCH_LINEAGE_REGISTER.md` | **Rejected.** Its subject is Phase 3 attempt caps on mechanisms (F-23), not phase transitions. Using it as an anchor ledger would make a platform-level, human, cross-cycle prose document into a machine-facing register by the back door — against A-8 R-1's ruling that the platform tier introduces no machine artifact (F-24), and against the partition rule, since an anchor's subject is a single cycle |
| A new platform-level anchor file | **Rejected.** Same ground (F-24), plus it is a chain of chains with the same length problem it was introduced to solve |
| A second machine artifact beside the chain | **Rejected.** Self-referential: a machine artifact written by the same writer cannot witness that writer. The witness must be authored by a human, in a different artifact, under a different discipline — that is the entire content of R-1 |
| A field inside the chain records themselves | **Rejected.** A chain cannot witness itself (F-1); this is the failure Resolution §2.2 diagnosed, re-entering as a field |
| `methodology.md`, `reviewer_reports/`, or a new §5 package item | **Rejected.** Each has a defined meaning under Standard §5 that a governance anchor citation is not, and adding an eighth required item would amend the Standard, which this record does not do (§11) |

### 4.5 R-5 — Verification procedure

**Ruled, in three parts, splitting what code does from what a human does.**

1. **Internal verification is mechanical** (Phase C's object): recompute
   each record's canonical serialization and its hash; check that record
   *N*'s stored predecessor hash equals record *N−1*'s computed hash;
   check `sequence_number` contiguity from 1 with no gaps or duplicates
   (R-3.3); check that `null` predecessor appears at sequence 1 and
   nowhere else (R-3.4). This detects mutation, reorder, insertion,
   interior deletion, and a forged predecessor — Phase C's stated
   criteria (F-17) — and it detects **nothing** about the tail.
2. **Anchored verification takes the anchor as an argument.** The
   verifier accepts an expected `(sequence_number, head_hash)` pair
   **supplied by the caller**, a human reading the citation from
   `decision_log.md`. If the pair is supplied, the verifier additionally
   confirms that the chain retains a record at that sequence number whose
   hash is that value. This is how Phase C's *"tail truncation detectable
   via the anchor"* (F-17) is satisfied, and it is the **only** way it is
   satisfied.
3. **No code reads, parses, or writes `decision_log.md`.** The verifier
   never locates an anchor for itself. INV-10 (F-15) is unchanged and is
   strengthened rather than strained: the human artifact is not merely
   un-written-to, it is un-read-from, so no code path can develop a
   dependency on its formatting. **Any future proposal to parse
   `decision_log.md` is a new AD**, and it should expect this ruling to
   be cited against it.

**Consequence for AD-050's precondition.** AD-050's draft requires the
chain *"verified intact and anchored before the append"* (F-16). Under
this ruling that precondition decomposes: *verified intact* is
mechanical and automatic; ***anchored* is a human act** — the operator
supplies the expected pair from the previous transition entry. AD-050
must state it that way, or the word "anchored" will be read as something
the machine did (§7, C-9).

### 4.6 R-6 — Anchor lag is inherent, disclosed, and not designed away

**Ruled: at any moment, every record above the last cited sequence number
is unanchored, and during normal operation that is at least the newest
record.** The citation is authored after the append (R-4.3 ordering), so
a freshly appended record is necessarily unanchored until a human writes
its entry.

This is **not** a defect to be closed and no mechanism is introduced to
close it. Closing it would require the writer to anchor its own write,
which is R-1's rejected self-witnessing, or an automatic commit, which
Resolution §2.2 rejected on grounds this record does not reopen (F-1).

Ruled consequences:

- No AD-048 text, and no artifact header, may describe a chain as
  "anchored" without qualification. The precise property is: **anchored
  through sequence `N`**, where `N` is the last externally cited value.
- The window is bounded by discipline, not by mechanism: the human writes
  the entry and commits both files in the same act (R-4.3). AD-048 states
  this as the expected practice and states plainly that nothing enforces
  it.

### 4.7 R-7 — Re-affirmed rejections

Stated so they cannot be reopened by omission. None is a new decision;
each is Resolution §2.2's or is forced by R-1.

1. **Automatic commit on append — remains rejected**, on Resolution
   §2.2's two grounds, both re-verified here: the Governance domain's
   read-only posture is stated in its own module (F-22), and a mid-run
   commit mutates the working-tree state `verify_freeze` reads. Not
   reopened, not softened, not made configurable.
2. **The git commit is not the anchor** (R-1), on F-14's demonstrated
   grounds.
3. **No external timestamping, notary, blockchain, or third-party
   attestation service.** No such dependency exists in this repository, it
   would put a network call inside the domain that exists to be
   auditable, and it is not required by any claim in §6. Closed
   explicitly so that a future "strengthen the anchor" proposal must open
   it as a new decision rather than treat it as an obvious extension.
4. **No filesystem-level immutability, no read-only permissions, no git
   hook, no CI check** is introduced by A-5. §6.2 states this as a
   non-claim; it is also a non-action (§11).

---

## 5. Anchor model

The model in one statement:

> **A cycle's transition chain is internally self-checking and externally
> witnessed. The chain proves the integrity of what it retains. A human,
> writing in a different artifact under append-only discipline, witnesses
> how much it retained. Neither half is sufficient; the anchor is the
> second half.**

Laid out as layers, each with what it adds and what it cannot do:

| Layer | Artifact | Written by | Adds | Cannot do |
|---|---|---|---|---|
| **L0 — record** | one line of `transition_records.jsonl` | machine (Phase C) | the mechanical facts of one transition | attest to itself |
| **L1 — chain** | the file, via predecessor hashes + contiguous `sequence_number` | machine | integrity and ordering of **retained** records | prove its own length (F-1); a zero-byte file is a valid empty chain (R-3.5) |
| **L2 — anchor** | the `**Machine chain anchor.**` line in the cycle's `decision_log.md` | **human** | an external claim that the chain held `N` records with head `H` at authoring time; one citation per transition (R-4.3) | survive an edit to `decision_log.md`; anchor records written after it |
| **L3 — retention** | the human commit of both files together | **human** | co-visibility: divergence becomes a diff on tracked files | confer immutability; survive history rewrite or repository loss (F-14) |

**Reading the model correctly.** Each layer's guarantee is conditional on
the layer below being intact and on the artifact at that layer not having
been edited. The layers do not multiply into certainty; they raise the
cost of undetected tampering from *edit one machine file* to *edit one
machine file and one human append-only file consistently, and commit
both, without the inconsistency being noticed by a reader of either*.
**That cost increase is the entire benefit, and §6 claims exactly it and
nothing more.**

---

## 6. Evidence claim boundary

### 6.1 The minimum provenance claim — what can truthfully be proven

Stated as three conditional claims of increasing strength, each naming
what it needs. These are the maximum AD-048 may assert.

**Claim 1 — chain alone.** *The records retained in this file form an
unbroken chain from sequence 1 to sequence M: no retained record was
altered, reordered, or interior-deleted, and no record was inserted
between two retained records, without breaking a hash link or a sequence
contiguity check.*
Needs: the file. Proves nothing about records that are not there.

**Claim 2 — chain plus a citation.** *If the record at sequence `N`
hashes to the cited `H`, then this file still retains, unaltered, the
entire prefix of the chain that existed when that entry was authored.
Removal of any record at or below `N` is detectable by a human comparing
the citation to the file.*
Needs: the file and an intact `decision_log.md` entry. This is the claim
that answers "a self-contained chain cannot prove its own length" — and
it answers it **only up to `N`**, never above.

**Claim 2a — the entry-by-entry strengthening.** Because every transition
entry cites its own record (R-4.3), the decision log carries an external
witness of the numbering *per transition*, not a single high-water mark.
Consequently: *the number of transition entries in `decision_log.md`
and the number of records in the chain must agree, and each entry's cited
sequence number must match its position in that ordering.* A disagreement
is an audit finding on its face, without any judgment about which
artifact is wrong.

**Claim 3 — chain plus citation plus commit.** *The chain and its witness
were co-present in a committed repository state; a subsequent change to
either is visible as a diff on a tracked file.*
Needs: an intact git history. F-14 is the reason this is stated last and
weakest.

**The honest summary, which AD-048 must carry in these terms:**

> Anchoring converts silent, single-file tampering into tampering that
> requires a coordinated and mutually consistent edit to a human-authored,
> append-only, review-disciplined artifact. **It does not prevent
> tampering. It makes one specific class of it visible to a human who
> looks.**

### 6.2 What is explicitly NOT claimed

Each line is a non-claim, and each names the reason it would otherwise be
assumed.

| Not claimed | Because |
|---|---|
| **Automatic commit** | Nothing commits anything. The recorder never invokes git in any mode (R-7.1, F-22). The anchoring commit is a human act, outside any run, and if the human does not perform it, no commit occurs and nothing reports that fact |
| **Automatic immutability** | A JSONL file on disk is fully writable. No filesystem permission is set, no attribute is changed, no git hook is installed, no CI check is added, no lock file is written (R-7.4). "Append-only" describes the **discipline**, not an enforced property of the medium |
| **Immutability conferred by committing** | A commit records a state; it does not freeze a file. History can be rewritten, and in this repository history has already been destroyed once with permanent loss (F-14) |
| **Writer enforcement** | Whether a single writer is assumed or mechanically enforced is **A-9's** and is undecided (§9). A-5 assumes a well-formed chain and specifies what a malformed one looks like; it prevents nothing |
| **Runtime guarantees** | No daemon, no monitor, no scheduled verification, no CI job, no startup check. Verification runs when a human runs it. A chain can sit tampered and unexamined indefinitely, and nothing will say so |
| **Proof of time** | Record timestamps are injected and self-asserted (AD-048's field set). There is no trusted clock and no notarization (R-7.3). A record's timestamp is a claim by the writer, not evidence |
| **Completeness above the last cited `N`** | Structural, not incidental (R-6). The tail is always unanchored by at least one record during normal operation |
| **That the transcribed content is true** | AD-048's transcription-not-certification ruling is unchanged: Governance cannot re-derive a gate outcome (F-18), so the chain attests to bytes, never to whether a transcribed gate status is correct |
| **That a `decision_log.md` citation is itself protected** | The witness is a text file the same actor can edit. Claim 2 is conditional on the entry being intact and says so. The protection is review discipline and visibility, not enforcement |
| **Anything about the three legacy archives** | They have no transition records and never will (A-8 §9.5). Their absence of a chain is the true state, not a gap |

---

## 7. Relationship to AD-048

AD-048 is a **draft**. This record does not edit it (§11). When it is
written into `ARCHITECTURE_DECISIONS.md` under A-2, it carries the
following, and A-5 closes at that point.

| # | Required of AD-048 | Source |
|---|---|---|
| C-1 | State that the anchor is the **external human citation**, and that `sequence_number`, the predecessor hash, and the commit are respectively ordering, interior integrity, and retention — **none of them the anchor**. Replace any wording that reads as though the chain or the commit anchors itself | R-1 |
| C-2 | Define the head hash exactly: SHA-256 over the UTF-8 bytes of the record's canonical JSON line (F-10), excluding the terminating LF, rendered `sha256:<64 lowercase hex>` (F-12); and record that this value is byte-identical to the predecessor-hash field of the next record | R-2 |
| C-3 | Record the rejection of a whole-file hash, a Merkle root, and any separate running chain-hash field, with the "must remain checkable after further appends" ground | R-2 |
| C-4 | Fix the numbering: origin **1**, per-cycle, contiguous, no gaps or duplicates; head sequence number equals record count; a gap or duplicate is chain-invalid and verification refuses | R-3.1-3.3 |
| C-5 | Fix the genesis record: predecessor-hash key **present** with value `null`; never omitted, never a sentinel, never the hash of the empty string. Record that a `null` predecessor at any sequence other than 1 is a structural error | R-3.4 |
| C-6 | Record that a **zero-byte chain file is a valid empty chain** (F-11), and that total truncation is therefore indistinguishable from "never transitioned" from the file alone — the sharpest statement of why the external anchor is not optional | R-3.5 |
| C-7 | Define the citation grammar normatively, as the single self-locating line of R-4.1, with no version token; and record that `docs/templates/decision_log_template.md` carries it as a **required** field, `Not applicable` where there is no transition, amended in the same increment that accepts this AD | R-4.1, R-4.2 |
| C-8 | Record the ordering and the one-to-one rule: authorize → append → cite the record just written → commit both files; a citation can never name the commit containing it; existing decision-log entries are never retrofitted | R-4.3 |
| C-9 | Split the verification procedure: internal checks are mechanical; **the expected `(sequence_number, head_hash)` pair is an argument supplied by a human**; **no code reads, parses, or writes `decision_log.md`**. State that AD-050's "verified intact and anchored" precondition decomposes accordingly, with *anchored* a human act | R-5, F-16 |
| C-10 | Record anchor lag as inherent: the chain is *anchored through sequence `N`*, never "anchored" unqualified; the tail above `N` is always unanchored; no mechanism closes the window and none is proposed | R-6 |
| C-11 | Carry §6.1's three conditional claims **verbatim in strength**, including the honest summary that anchoring makes one class of tampering visible rather than preventing tampering | §6.1 |
| C-12 | Carry §6.2's non-claims explicitly, especially: no automatic commit, no automatic immutability, no immutability from committing, no writer enforcement (A-9's), no runtime guarantee, no proof of time | §6.2 |
| C-13 | Re-affirm the rejections of commit-on-append, of the commit-as-anchor reading, of external timestamping/notarization, and of filesystem or hook-based immutability — each as a closed decision requiring a new AD to reopen | R-7 |

**What is unchanged in AD-048 by this record:** its field set (A-5 adds
**no** field, F-2), its storage decision, its
transcription-not-certification claim, its refusal to commit, its
rejection of the borrowed-precedent justification, its Migration Plan §10
item 4 disposition, and A-8's location rulings C-1 … C-11. This record
speaks only to what anchors the chain, what that proves, and where the
citation lives.

**Required of AD-050 rather than AD-048:** the decomposition in C-9 of
its own *"verified intact and anchored before the append"* precondition
(F-16).

---

## 8. Relationship to A-8

A-8 is taken as settled input and is not reopened. Three points of
contact, each closing a hole A-8 left open by name:

- **A-8 deferred the numbering origin, the anchor's format, and the
  verification procedure to A-5** (F-3). R-3 supplies the origin, R-4
  the format, R-5 the procedure. A-5 adds nothing else to A-8's rulings.
- **A-8's per-cycle partition is what makes the anchor coherent.** Its
  rationale §5 item 2 argued the chain must be per-cycle *because the
  anchor is per-cycle* (`decision_log.md` is per-cycle, F-5). R-2's
  chain-identity element and R-3.2's per-file numbering are the direct
  consequences: a citation names its chain explicitly and its sequence
  numbers mean nothing outside it.
- **A-8 R-3.5 forbids storing anything outside the repository precisely
  because the anchor needs a tracked file to commit** (F-20). R-1
  demotes the commit from anchor to retention, which **does not** relax
  that prohibition: co-visibility in a tracked state is still required,
  and an untracked chain still cannot be witnessed under this model.

---

## 9. Relationship to A-9

**A-9 is not decided here, and no part of §4 may be cited as deciding
it.** What this record does is state precisely how A-5's guarantee
depends on A-9's answer, so that A-9 is decided with that dependency
visible rather than discovered later.

| Aspect | A-5 (this record) | A-9 (open) |
|---|---|---|
| **What is anchored** | A well-formed chain: contiguous sequence numbers from 1, one record per transition | Whether concurrent or foreign writers can make it ill-formed |
| **Concurrency damage** | Ruled *detectable*: a duplicate or non-contiguous `sequence_number` is chain-invalid and verification refuses (R-3.3). A lost interleaved write appears as a gap | Whether it is *prevented* — stated assumption or mechanical lock |
| **Anchor validity under a violation** | A citation naming a duplicated sequence number is **ambiguous**, and ambiguity is a failure: verification refuses rather than picking a record | Whether that state can arise at all |
| **If A-9 rules "stated assumption"** | Then §6.1's claims are **conditional on that assumption**, and AD-048 must say so in those words rather than asserting them unconditionally | A-9's to rule |
| **If A-9 rules "mechanical lock"** | §6.1's claims stand as written, and the lock is one more thing that does not confer immutability (§6.2) | A-9's to rule |

**Separation held, stated plainly:** A-5 is about *what a record's place
in a chain can be shown to be, and by whom*. A-9 is about *who is
permitted to put a record there*. A-5 does not restrict writers, does not
name a writer, does not introduce a lock, and does not assume there is
exactly one writer — it states what a verifier sees if there is not.

---

## 10. Effect

| Item | Status after this record |
|---|---|
| **A-5, question 1 — what anchors a chain** | **Decided:** the external human citation in the cycle's `decision_log.md`. `sequence_number` = ordering; predecessor hash = interior integrity; commit = retention. None of the three is the anchor. §4.1 |
| **A-5, question 2 — minimum provenance claim** | **Decided:** three conditional claims (chain alone / plus citation / plus commit) with the entry-by-entry strengthening, and the honest summary that anchoring makes one class of tampering visible rather than preventing it. §6.1 |
| **A-5, question 3 — what is not claimed** | **Decided:** no automatic commit, no automatic immutability, no immutability from committing, no writer enforcement, no runtime guarantee, no proof of time, no completeness above the last cited `N`, no certification of transcribed content. §6.2 |
| **A-5, question 4 — the missing carrier** | **Decided:** both — AD-048 owns the citation format (R-4.1), `docs/templates/decision_log_template.md` gains a required `**Machine chain anchor.**` field as the slot (R-4.2), amended in A-2's increment. Register, new platform file, second machine artifact, and the unamended evidence-references field are each rejected with grounds. §4.4 |
| **A-5, question 5 — separation from A-9** | **Held.** §9 states the dependency without deciding A-9 |
| **A-5 as a prerequisite** | **Decided in writing, not yet closed.** Closes when AD-048 is written and accepted under A-2 carrying C-1 … C-13, together with R-4.2's template amendment. §1 |
| **A-2** | **Open, unchanged.** This record adds required content to AD-048, one item to AD-050, and one documentation-only amendment bound to that increment; it writes and accepts nothing |
| **A-9** | **Open, unchanged.** Bounded and made explicit by §9; not decided |
| **A-1, A-6, A-8** | **Ruled on at `aca36fb`, `3ee23fd`, `e76bafe`.** Not re-decided, not reopened |
| **A-3, A-4, A-7** | **Open, unchanged.** Not spoken to |
| **Step 9** | **Blocked, unchanged.** Resolution §4.1's rule — "Step 9 does not start until every item below is closed in writing" — is unchanged and unrelaxed |
| **`decision_log_template.md`** | **Unedited.** The amendment is decided and bound to A-2, not performed here |
| **`RESEARCH_GOVERNANCE_STANDARD.md` §5** | **Unedited.** No eighth package item; the anchor lives inside an existing item's file |
| **Tail-truncation exposure** | **Bounded and disclosed, not eliminated.** Detectable at or below the last cited sequence number; permanently open above it (R-6) |

**How to re-run this ruling.** Every input is named so a later reader need
not trust this document: the rejected mechanism and its replacement
against `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:328-373` and
`PHASE_4_STEP9_DRAFT_ADRS.md:170-178`; the existing field set against
`PHASE_4_STEP9_DRAFT_ADRS.md:121-128`; the deferral to A-5 against A-8
§4.4 and §6 C-10; the serialization and empty-file behaviour against
`core/governance/canonical_jsonl.py:24-51`; the hash-prefix convention
against `canonical_jsonl.py:54-58` and `dataset_manifest.py:65-67`; the
carrier gap against `docs/templates/decision_log_template.md:19-42`
compared with `research_archive/reference_h3/decision_log.md:19-30` and
`research_archive/positive_control_phase3/decision_log.md:13-15`; the
append-only carve-out against `RESEARCH_GOVERNANCE_STANDARD.md:439-456`;
the git-durability fact against
`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md:74-79`; and the import boundary
against `tools/check_import_boundaries.py:64`.

---

## 11. Explicit non-actions

Stated as prohibitions honoured by this record, each verifiable against
the diff:

- **No code is modified or created.** `core/governance/`, `core/research/`,
  `core/shared/`, `core/validation/`, `tools/`, and every test file are
  untouched.
- **No writer is implemented.** No `DecisionRecorder`, no append path, no
  hash function, no serializer, no path constant, no lock.
- **No verifier is implemented.** §4.5 describes a procedure to be built
  in Phase C and states which half is human; it builds neither half.
- **No JSONL schema is created in code.** The field semantics fixed in
  R-3 are decisions to be transcribed into AD-048, not a schema, not a
  dataclass, and not a test.
- **No ADR file is modified.** `PHASE_4_STEP9_DRAFT_ADRS.md` is retained
  unedited; §7 states what AD-048 and AD-050 must carry and changes
  nothing in either draft. `ARCHITECTURE_DECISIONS.md` is not
  modified — no AD is added, amended, renumbered, accepted, or marked
  superseded, and no supersession marker is placed against AD-045.
- **`docs/templates/decision_log_template.md` is not edited.** R-4.2
  **decides** that it gains a required `**Machine chain anchor.**` field
  and **binds that amendment to A-2's increment**. No field is added by
  this record, and the template at `e76bafe` is unchanged.
- **No `decision_log.md` is edited or appended to.** Neither
  `research_archive/reference_h3/decision_log.md` nor
  `research_archive/positive_control_phase3/decision_log.md` is touched,
  and no entry is retrofitted with an anchor.
- **`RESEARCH_GOVERNANCE_STANDARD.md` is not amended.** No eighth package
  item; §5's dating and append-only rules are read, not changed.
- **Nothing is written to `RESEARCH_LINEAGE_REGISTER.md`.** No
  `lineage_id` is opened, retired, or certified; §4.4 rejects it as a
  carrier without touching it.
- **`RESEARCH_ARCHIVE_MANIFEST.md` is not amended** and its
  `schema_version` is not incremented.
- **No file or directory is created under `research_archive/`.** No
  `transition_records.jsonl` exists anywhere in the repository, and none
  is created here.
- **No Phase B artifact is created.** No `LifecyclePhase`,
  `advance_phase()`, `DecisionRecorder`, `GateRunner`, or linter change.
- **No filesystem permission, git hook, CI job, or lock is introduced**,
  and §6.2 records that none exists.
- **A-9 is not decided**, and **A-8 is not reopened**.
- **No hypothesis, gate determination, or research conclusion is made.**
- **No commit is made by this record.**

---

## 12. Future implementation boundary

Carried forward, in the increment each belongs to. None is a new
requirement on anyone; each is a disclosed consequence of a ruling above.

1. **A-2 (documentation increment)** carries three things together, and
   the ordering is the point: AD-048 written with C-1 … C-13, AD-050
   amended per C-9, and `docs/templates/decision_log_template.md`
   amended with the required `**Machine chain anchor.**` field (R-4.2).
   **A format without a slot is the defect this ruling was raised to
   close; they land in one increment or the defect survives A-2.**
2. **Phase C (`DecisionRecorder`)** implements R-3's semantics — origin 1,
   contiguity, `null` genesis, the closed field set unchanged — and R-5.1's
   internal verification. Its exit criterion *"tail truncation detectable
   via the anchor"* (F-17) is satisfied by R-5.2's argument-supplied pair
   and by nothing else; a Phase C implementation that claims truncation
   detection without an externally supplied expected pair has not met the
   criterion and must not be recorded as having met it.
3. **Phase C must not build a `decision_log.md` reader or parser** (R-5.3).
   If a future increment wants automated anchor checking, it needs a new
   AD that reopens INV-10's read side explicitly, and it should expect
   this ruling to be cited against it.
4. **Phase B-3 (`advance_phase()`, H4 registration)** produces the first
   record that will ever be cited. Under A-6 R-1 the cycle is
   `reference_h4`, so the first citation will name
   `research_archive/reference_h4/transition_records.jsonl` at seq `1`.
   Phase B must state the ordering of R-4.3 as operator procedure, since
   nothing enforces it.
5. **The first real citation is a documentation act, not a code act.** No
   increment of Step 9 produces a citation; a human does, after an append.
   If Phase E's end-to-end traversal (Resolution §4.2) exercises a
   transition, the anchor for that transition is written by hand or it is
   not written at all — and an unanchored test transition must not be
   presented as demonstrating the anchoring mechanism.
6. **The three legacy archives never receive a chain and never receive a
   citation** (A-8 §9.5). Their decision logs stay as they are; any future
   proposal to add anchor lines to them is a retroactive-fact violation of
   the class `core/research/project.py:32-41` already refuses for
   `origin_date`, and needs its own ruling.
7. **If the tail exposure is ever judged unacceptable**, the reopening is
   a new decision against R-7's closed list — not an extension of this
   one. The candidates it would have to argue against on their merits are
   named in R-7 (auto-commit, external timestamping, medium-level
   immutability), and each was closed here with grounds rather than left
   unconsidered.
