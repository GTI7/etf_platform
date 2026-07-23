# Phase 4 / Step 9 — Draft Architecture Decision Records

**Status: drafts. Not yet accepted. Not yet written into
`docs/ARCHITECTURE_DECISIONS.md`. No code is introduced by this
document and no existing file is modified by it.**

**Numbering.** The accepted AD set is **AD-001 … AD-046 plus AD-051**
(verified at HEAD `7698900`: `ARCHITECTURE_DECISIONS.md` runs to "AD-046:
Reporting input boundary" and then carries "AD-051: An empty
`covered_paths` set is `UNVERIFIABLE`, not `VERIFIED`"). **AD-047 …
AD-050 remain reserved and are not accepted.** That reservation is
AD-051's own, recorded in its "Numbering" paragraph: AD-051 was taken
instead of the next-in-sequence AD-047 because AD-047–050 are "left
reserved for `docs/PHASE_4_STEP9_DRAFT_ADRS.md`, which provisionally
claims them and is already cross-referenced by those numbers". These
drafts therefore keep **AD-047 … AD-050**. They replace the AD numbering
proposed in `STEP_9_VALIDATION_ORCHESTRATION_PROPOSAL.md` §13 and in
`STEP_9_ARCHITECTURE_RECONCILIATION_REVIEW.md` §6.2, neither of which
was accepted and which collide with each other.

**Line citations in this document resolve against baseline `2c7fb2c`,
not against `HEAD`.** Every `core/governance/freeze_verifier.py:N-M`
citation in the drafts below was taken by reading that file at `2c7fb2c`
(tag `phase4-final-before-h4-20260722`). Commit `4c7ca8d` (AD-051) then
changed that file in two additive hunks, so the same content now sits at
different line numbers. The offset is recorded here once, as a
navigational aid. **It corrects nothing, reinterprets nothing, and edits
no other document.**

| Baseline `2c7fb2c` lines | At HEAD `7698900` | Content, and who cites it |
|---|---|---|
| 1–58 | **unchanged** | Module docstring, incl. the read-only posture at `40-43` / `41-43`. Text identical at HEAD; citations still resolve as written. |
| 59–60 | rewritten in place as 59–61 | `FreezeStatus`'s docstring, extended by AD-051. Cited by no document. |
| 61–153 | **+1** | `_has_uncommitted_drift` `122-126` → `123-127`; `verify_freeze` `129-178` → `130-194`. |
| 154 onward | **+16** | The fall-through to `VERIFIED`, `154-170` → `170-186`. AD-051's early return occupies HEAD `155-168`. |

**No accepted ruling record is affected, and none is edited.** Checked at
HEAD: the only `freeze_verifier.py` line citations in accepted ruling
records are `PHASE_4_A5_CHAIN_ANCHORING_RULING_2026-07-22.md` F-22
(`41-43`) and `PHASE_4_A9_SINGLE_WRITER_RULING_2026-07-22.md` F-7 and its
§10 "How to re-run this ruling" paragraph (`40-43`) — all inside the
unshifted region, all still resolving to the text they quote. The
shifted citations occur only in `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`
(§0's table, §2.2), `PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` §1.4,
`PHASE_4_PR0_REMEDIATION_PROPOSAL.md`, and
`STEP_9_ARCHITECTURE_RECONCILIATION_REVIEW.md`. Each of those was
correct against the state it was verified against and is retained
unedited, per the supersession discipline
`PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md` follows in its header —
a correction is a new dated writing, never an edit to the record it
corrects. This table is that writing, and it is a reconciliation of line
numbers only.

**Citations *into* this file are re-resolved here, and the accepted
ruling records that carry them are not edited.** Four accepted ruling
records cite `PHASE_4_STEP9_DRAFT_ADRS.md` by line range, each taken
against the file as committed at its own HEAD. Two revisions have moved
them. The AD-047 revision was confined to the AD-047 section and moved
every such citation by exactly **+218**. The subsequent **A-2
preparation revision** — which transcribes A-5, A-8 and A-9 into the
AD-048 draft and A-6 plus A-5's AD-050 limb into the AD-050 draft — adds
material *inside* AD-048 and *inside* AD-050, so **the offset is no
longer uniform** and each row below now carries its own resolved value.
Verified by matching the cited anchor text line-for-line:

| Cited as | Resolves here to | Anchor content | Cited by |
|---|---|---|---|
| `:110-115` | `:344-349` | AD-048's consumer-less-abstraction condition ("This AD is void if…") — **unchanged** | A-9 F-22 |
| `:121-128` | `:355-362` | AD-048's closed field set, `project_id` … predecessor SHA-256 — **unchanged** | A-5 F-2 and §10 |
| `:121-131` | `:355-365` | The same field set plus the "Never records" opening — **unchanged** | A-9 F-23 and §10 |
| `:144-150` | `:378-386` | AD-048's canonical-JSONL storage bullet. The cited read-append-rewrite sentence, incl. "written atomically (temp + replace)", is **unchanged and present at `:378-383`**; `:383-385` is one appended sentence disambiguating "atomically" per A9-C6, and the inherited Windows-CRLF sentence follows at `:385-386` | A-8 F-16; A-9 F-5 and §10 |
| `:170-178` | `:406-418` | AD-048's external anchoring, **all three parts retained**, each now labelled with its role per A5-C1. Every fragment the citing rulings quote — "cites the chain head hash and sequence number", "commit is performed by a human, outside any gate sequence" — remains present verbatim in place; the anchor as a whole is amended (labels and an intro added) but no quoted fragment is altered or deleted | A-5 F-1 and §10; A-8 F-18 and re-run |
| `:329` | `:1222` | The AD-050 heading — **unchanged** | A-6 F-18 |
| `:336-339` | `:1229-1232` | AD-050's lineage / cycle / attempt sentence — **retained byte-identical**, and expressly *not* read as a `lineage_id` claim by A-6 textual change 1 later in the section | A-6 F-19 |
| `:383-403` | `:1433-1458` | AD-050 part 3's four grounds and its stated cost — **unchanged** | A-8 F-24 |
| `:457-461` | `:1507-1514` | AD-050's evidence preconditions, incl. "verified intact **and anchored**" — **retained byte-identical**, with A5-C9's decomposition added as a following block, not as an edit to the cited sentence | A-5 F-16; A-9 F-11 and §10 |

**Nothing in those rulings is reopened, re-read, or amended by this
table.** Each finding continues to rest on the text it quoted verbatim
in its own body; the quoted text is what makes the finding checkable,
and **the cited meaning of every quotation is preserved and each quoted
fragment remains recoverable in this file**. In the rows whose anchor is
unamended the quoted text is unchanged; in the two rows whose surrounding
anchor was amended the amendments add labels and following sentences and
delete no quoted fragment, so each cited fragment is still present
verbatim even though the anchor range as a whole is no longer identical
to the range the ruling cited. The line number is a locator, not the
evidence. This note exists so a later reader
following a locator lands where the ruling meant, without any accepted
record being touched — which is the least invasive resolution available,
and the only one consistent with retaining accepted rulings unedited.

**Where an amendment was made inside a cited anchor, it was made because
a ruling required it**, not for convenience: A5-C1 requires that no
wording read as though the chain or the commit anchors itself, and A9-C6
requires "written atomically" to be disambiguated. Both requirements
land inside ranges the rulings cite, and the least invasive way to
satisfy them is to retain the cited text and qualify it in place.

**A standing consequence for later revisions of this file.** Any future
edit **above or inside** a cited anchor moves these locators again. The
obligation that follows is to update **this table**, never the rulings.

**Adoption condition.** All four are Phase A items per
`docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md` §4.1. No Step 9 code may
be written before all four are accepted, and AD-047's disclosure
obligation (A-1) precedes even the acceptance of the other three.

---

### AD-047: Freeze verification is scope-bounded; the empty-covered-paths hole at baseline `2c7fb2c` was disclosed, and is guarded in new code

**Historical framing, stated first.** This AD was drafted at `8a91d35`
against baseline **`2c7fb2c`** (tag `phase4-final-before-h4-20260722`).
Every statement below about `freeze_verifier.py`'s behaviour describes
the repository **as it stood at that baseline** — not as it stands at
current `HEAD`. The defect described was subsequently closed by AD-051
(commit `4c7ca8d`). What this AD contributes is unchanged by that fix:
the historical disclosure, the guard in new Validation code, and the
claim bound all still stand.

**Relationship to AD-051: coexisting; neither supersedes the other.**
AD-051 is **not superseded, not amended, and not renumbered by this
AD**, and nothing here modifies its accepted meaning. The two sit at
different layers and both remain in force:

- **AD-047 (this AD)** documents the **historical architectural
  disclosure** — that the hole existed at `2c7fb2c`, what it made
  vacuously satisfiable, and what a `VerificationResult` produced under
  it is and is not worth — and places a guard in **new Validation
  code**, before any gate runs.
- **AD-051** records the **implemented remediation** inside
  `core/governance/freeze_verifier.py` itself: an empty `covered_paths`
  returns `FreezeStatus.UNVERIFIABLE`.

AD-047 does not supersede AD-051, and AD-051 does not discharge
AD-047's disclosure obligation — AD-051's own "Scope" paragraph states
that in terms. Both are needed.

**Decision.** Three parts, and the first was not conditional on the
other two.

1. **Disclosure.** A dated governance deviation record was required to
   be re-issued, stating that at baseline `2c7fb2c`
   `core/governance/freeze_verifier.py`'s
   `verify_freeze(commit_ref, [])` *returned* `FreezeStatus.VERIFIED`,
   that this behaviour was live at that baseline with no guard and no
   test in either direction, that the original remediation record
   (`docs/PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md`) was
   destroyed **as a committed object** in the 2026-07-21 incident — **no
   reachable git ref contains it**, while byte-identical copies of its
   content survive off-repository as untracked files in non-canonical
   working trees, so that its content is recoverable and its commit
   provenance is not — and that **every `VerificationResult` in the
   archive is only as strong as the covered-path set it was called
   with.** This obligation stood whether or not Step 9 proceeded, and it
   is **not weakened, narrowed, or retired by having been met.**

   **What has been filed against this obligation, limb by limb.**
   Prerequisite A-1 of
   [`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
   §4.1 is two-limbed on its face — done when "The disclosure exists in
   `docs/`" **and** "the PR0 ruling is closed or confirmed obsolete".
   The two limbs stand in different states and are stated separately
   here rather than summed.

   - **Limb 1 — the disclosure — is discharged.** It was closed by
     [`PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md`](PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md)
     (`8bd8f8a`), the dated record in `docs/` this part required.
     [`PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md`](PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md)
     §6 records limb 1 as "**Closed** at `8bd8f8a`", and its §5 states
     that ruling "does not discharge A-1 limb 1. That limb was closed by
     `8bd8f8a` and is not re-decided here."
   - **Limb 2 — the ruling — remains conditional, exactly as the accepted
     A-1 ruling states it.**
     [`PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md`](PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md)
     (`aca36fb`) disposes of both items of the 2026-07-21 ruling request
     — item 1 determined as a statement of fact (§2.1), item 2 VOID for
     failure of its own stated condition (§2.2) — and its §6 records
     limb 2 as "**Closed if this ruling is accepted.** On acceptance,
     limb 2's condition is met by §2 of this record." That condition is
     restated here without alteration and is **not** read as satisfied
     by this AD.

   **Consequently, A-1 as a whole is not stated here as discharged.**
   The accepted ruling's own closing statement governs and is adopted
   verbatim: "Until that acceptance, limb 2 stays open, A-1 stays
   undischarged, and Step 9 stays blocked — exactly as it stood at
   `8bd8f8a`." Resolution §4.1's rule that "Step 9 does not start until
   every item below is closed **in writing**" is unchanged by this AD,
   and A-2 … A-9 remain open on their own terms regardless of A-1's
   disposition.

   The destroyed-record wording above is stated as those records state
   it (re-disclosure record §1.4 and §1.5 rows 3–4), which corrected
   this AD's original, broader "exists in no reachable git ref" phrasing
   on evidence.
2. **Guard, in new code only.** `GateContext` construction rejects an
   empty `freeze_covered_paths`, and `GateRunner` refuses the run before
   any gate executes. `GateRunRecord` stores the **full covered-path
   list**, not a count. `freeze_verifier.py` is **not modified by this
   AD** — the guard lives in new Validation code, so the baseline stays
   untouched by Step 9 and INV-12 holds. That is not asserted here; it is
   [`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
   §3's decision D-2 — "`verify_freeze` is **not modified** by Step 9.
   New Validation code refuses an empty covered-path set; the full path
   list is recorded; the permitted claim is the narrow one (§2.3)" —
   which that decision table binds on AD-047 by name, and which this
   part restates rather than extends.

   **Why this guard is still required after AD-051: the two act at
   different layers.** AD-051 prevents empty coverage from being
   mistaken for success **inside freeze verification** — `verify_freeze`
   itself now returns `UNVERIFIABLE`. This AD prevents a run with empty
   coverage from **executing at all**: `GateRunner` refuses **before any
   gate runs**, rather than letting every gate execute and render
   `AMBIGUOUS` downstream of an `UNVERIFIABLE` verification.
   `GateRunRecord`'s full-path-list requirement is a third thing again —
   an **evidence-recording** obligation that no change to
   `verify_freeze` can satisfy, because a status value cannot carry its
   own coverage set (restated INV-3, below). Neither requirement is
   redundant with AD-051 and neither is weakened by it.
3. **Claim bound.** A `VERIFIED` result licenses exactly one statement:
   *these named paths were byte-identical to their content at the
   claimed commit, with no committed or uncommitted drift since.* No
   Step 9 artifact may render it as "the methodology was frozen."

**Rationale.** The mechanism was verified by reading
`freeze_verifier.py:154-170` **at baseline `2c7fb2c`**
(`git show 2c7fb2c:core/governance/freeze_verifier.py`): `errors` and
`drifted` were populated only inside `for path in paths`; an empty
iterable left both empty and the function fell through to
`else: status = VERIFIED`. **That line range is a citation into the
baseline, not into current `HEAD`** — at `HEAD` the same file carries
AD-051's early return at lines 155-168 and the block cited above has
moved to 170-186, so reading that line range against `HEAD` would not
reproduce the finding. This was load-bearing rather than cosmetic
because AD-043 makes a gate render `AMBIGUOUS` when verification is not
`VERIFIED` — so at that baseline a gate with **zero freeze coverage**
was free to render `PASS`, and any invariant of the form "no gate
executes against an unverified freeze" was **vacuously satisfiable**. A
pre/post freeze bracket over an empty set agrees with itself perfectly
while proving nothing.

**Why the guard is not the whole answer.** Non-emptiness is necessary
and not sufficient. A path set containing only `README.md` satisfies the
guard and verifies exactly as vacuously as the empty set. That is why
part 3 exists and why the full path list — not a count — is recorded:
adequacy of coverage is a **human review judgment**, disclosed as such,
and Step 9 does not mechanize it. Storing a count and calling the
verification non-vacuous would reproduce, inside the correction, the
claim-stronger-than-mechanism failure this AD exists to close.

**Why the baseline is not fixed here.** *(Title retained verbatim.
[`PHASE_4_PR0_REMEDIATION_PROPOSAL.md`](PHASE_4_PR0_REMEDIATION_PROPOSAL.md)'s
"Relationship to Step 9" cites this section by that title — "AD-047,
'why the baseline is not fixed here'" — and that citation must keep
resolving. "Here" has always meant **this AD and Step 9**, which is the
sense
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
§2.5 uses when it rejects "fixing `freeze_verifier.py` inside Step 9";
it has never meant "nowhere, ever". The body below records what has
since happened elsewhere.)*

A guard inside `verify_freeze` itself was identified here as the right
long-term answer, and was deliberately left out of Step 9: it is a
baseline modification, it required its own governance ruling, and
folding it into Step 9 would have repeated the exact scope violation PR0
was returned for. It was named as a separate increment with its own AD —
and that is exactly what it became.

**That increment was subsequently completed.** Its proposal landed at
`ced8636`, its implementation at `4c7ca8d`, and the decision is recorded
as **AD-051**; the split is determined as a matter of fact in
[`PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md`](PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md)
§2.1. What survives from this AD is the **architectural disclosure** —
the scope-bounded reading of freeze verification, the claim bound, and
the record of what the baseline did — none of which the fix discharges.
**AD-047 does not supersede AD-051.**

**Invariant restated.** *No gate executes against a freeze verification
whose covered-path set is empty, unresolved, or drifted, and no
`VERIFIED` result is admitted as evidence without its covered-path list
recorded alongside it.*

**Migration/status.** `freeze_verifier.py` **was modified by AD-051**
(commit `4c7ca8d`, one additive early return plus four additive tests);
**AD-047 introduces no further modification of it.** That modification
landed as its own increment outside Step 9, under its own proposal and
its own AD.

**That it is therefore not a Step 9 baseline change is read from the
Resolution, not asserted here.** INV-12 is a Step 9 invariant, and the
Resolution fixes its scope in two places, both of which put this
increment outside it:
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
§2.5 rejects "fixing `freeze_verifier.py` inside Step 9" and rules that
"The baseline fix is a separate increment with its own AD"; §4.1 then
lists that fix under "**Not a prerequisite, and explicitly deferred:**
the `freeze_verifier` baseline fix (§2.5), which is its own later
increment with its own ruling." `4c7ca8d` is that increment — the
disposition §2.5 ruled for, arrived at as
[`PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md`](PHASE_4_PR0_A1_RULING_RECORD_2026-07-22.md)
§2.1 determines as a matter of fact. What INV-12 constrains — Step 9's
own work — is untouched. This AD claims nothing beyond that reading, and
in particular does not rule on how INV-12 would apply to any other
modification of a baseline file.

Everything this AD requires still lives entirely in new Validation code
(`GateContext`, `GateRunner`, `GateRunRecord`). No existing
`VerificationResult` is invalidated by this AD; they are re-scoped by the
disclosure, which states what they did and did not prove — and, as the
re-disclosure record §4.2 states, no historical result is retroactively
improved by the fix either.

---

### AD-048: `DecisionRecorder` — mechanical transition records under AD-045's own re-opening condition

**Relationship to AD-045: clarifying, not superseding.** AD-045 is
**not superseded, not amended, and remains in force in full.** Its
decision — *"No `DecisionLogger` implementation is planned;
`core/governance/` is not expanded by this AD"* — remains **literally
true** after this AD: no `DecisionLogger` is built, no code writes
`decision_log.md`, and hand-authored narrative remains the canonical
record of judgment. This AD is the "new decision, against that concrete
need" that AD-045's final paragraph explicitly reserved — made now that
`advance_phase()` gives it a real caller. AD-045 closed with *"not a
resumption of this one"*, which instructs a new decision rather than an
overturned one. **No supersession marker may appear against AD-045 in
the AD index**: a future component wanting to write a judgment field
would cite it as precedent that the no-automated-decision-logging
decision no longer binds, which is precisely the erosion this AD guards
against.

**What AD-045 got right, and still constrains this AD.**

1. **AD-038's authored-evidence principle.** A mechanically generated
   entry would satisfy "an entry exists" while omitting "which candidate
   was ranked where and why" and "known limitations" — fields that are,
   and can only be, human judgment. This AD does not weaken that. It
   authorizes recording **only** facts that are mechanically derivable
   and independently checkable.
2. **The consumer-less-abstraction objection.** AD-045 refused to build
   a component whose only designed trigger did not exist. That objection
   is answered **only** by `advance_phase()` being built first. **This
   AD is void if `DecisionRecorder` is implemented before
   `ProjectRegistry.advance_phase()` has a real caller.** Ordering is a
   condition of this decision, not an implementation detail.

**Decision.** `core/governance/decision_recorder.py` provides an
append-only, hash-chained, externally-anchored store of **mechanical**
phase-transition records.

- **Records, exclusively:** `project_id`, `sequence_number`,
  `from_phase`, `to_phase`, injected UTC timestamp, code commit hash,
  freeze commit ref with its verification outcome **and its full
  covered-path list** (AD-047), gate names with their statuses as plain
  strings, the authorization record (AD-050), evidence refs as opaque
  strings (AD-042), the `ReproductionRecord` reference establishing
  measurement provenance where one exists, and the SHA-256 of the
  predecessor record's canonical serialization.
- **Never records:** rationale, interpretation, narrative, ranking,
  known limitations, or any free-text field capable of carrying them.
  The record is a frozen dataclass with a **closed field set**, and a
  test pins the **exact** serialized key set — so adding any field fails
  a test and forces a new AD rather than a commit. Prose whitelists were
  the mechanism the review found insufficient; this is the same
  discipline `GateStatus` gets.
- **Never writes** `decision_log.md`, nor any file the human authors.
- **Never commits, checks out, or resets anything** (see anchoring
  below).
- **Expressed in primitives and kernel types only.** Governance cannot
  import Validation (`ALLOWED_DEPENDENCIES["governance"] == {"data"}`,
  asserted by `test_detects_forbidden_governance_to_validation_import`).
  The recorder therefore never sees a `GateResult`. Research projects
  gate outcomes down to strings and passes them (AD-049).
- **Storage:** `core.governance.canonical_jsonl`, whose rules (UTF-8 no
  BOM, LF only, single trailing newline, sorted keys) already exist and
  are already tested. `write_canonical_jsonl` rewrites the whole file
  via `path.write_bytes`, so appends are read-append-rewrite with the
  prior prefix verified byte-identical, written atomically (temp +
  replace). **"Atomically" is disambiguated at A9-C6: temp-plus-replace
  makes the *replacement* atomic and leaves the *read-modify-write* not
  atomic.** The known Windows CRLF fragility in this module is inherited
  and must be covered by an explicit fixture, never assumed away.

**Transcription, not certification.** `PLATFORM_ARCHITECTURE_V1.md`
§4.4: Governance "certifies nothing it did not independently re-derive."
The recorder **cannot** re-derive a gate outcome — the forbidden
Governance → Validation edge is exactly what makes it auditable. It
therefore certifies one thing only: that the retained records were not
altered or reordered since they were written. It asserts nothing about
whether a transcribed gate status is true. **The artifact states this in
its own header**, so an auditor cannot read Governance as vouching for
Validation's conclusions.

**Tamper-evidence, at its true strength.** The chain proves no
**retained** record was altered, reordered, or interior-deleted. It
**cannot** prove no record was removed from the tail: truncating after
record *N* leaves a perfectly valid chain, and so does replacing the
file with a fresh genesis chain. **A self-contained chain cannot prove
its own length**, and the operator who would author retroactively is the
same actor who can truncate.

Anchoring is therefore external, and deliberately **not** by
auto-committing. The three parts below have three different roles, and
**only the second of them is the anchor** (A5-C1):

- **Ordering, not anchoring.** every record carries a monotonic
  `sequence_number`;
- **The anchor.** the hand-authored `decision_log.md` entry — written
  anyway under AD-038 — **cites the chain head hash and sequence
  number** at time of writing, giving a human-witnessed anchor at zero
  new machinery;
- **Retention, not anchoring.** the anchoring **commit is performed by a
  human, outside any gate sequence**, under the existing archive
  discipline.

**Why the recorder must not commit.** Two verified reasons. First, the
Governance domain's read-only posture is explicit and load-bearing:
`freeze_verifier.py:41-43` states "nothing in this module ever writes,
commits, checks out, or resets anything" — a committing recorder breaks
that property in the component whose entire value is being trustworthy.
Second, `verify_freeze` derives drift from `git status --porcelain` on
the **working tree** (`freeze_verifier.py:122-126`); an append that
commits mid-run mutates exactly that state, and could flip a pre/post
freeze bracket or mask real drift by committing it. **An anchoring
mechanism capable of altering the evidence is not an anchor.**

**No inherited precedent.** Earlier drafts justified the chain as
inheriting tamper-evidence "the Phase 4 dataset chain already has."
**No such chain exists** — verified: no `prev_hash`/`previous_hash`/
`chain` construct appears anywhere in `core/governance/`.
`ReproductionRecord` binds a hash *set* within a single record; nothing
links record *N* to *N−1*. The chain here is **novel work** and is
justified on its own merits. Overclaim-by-borrowed-authority is the
failure that returned PR0.

---

**Requirements transcribed from the Phase A ruling records — prefixed,
never merged.** Three accepted ruling records place requirements on this
AD, and all three number their consequence lists from `C-1`.
[`PHASE_4_A9_SINGLE_WRITER_RULING_2026-07-22.md`](PHASE_4_A9_SINGLE_WRITER_RULING_2026-07-22.md)
§9 discloses that collision as its F-25 and directs that A-2 "carry all
three sets under distinguishing prefixes", applying the same treatment
retroactively to A-5's and A-8's lists. That direction is followed here.
The three sets are **disjoint in content and colliding in label only**.
Each item below carries its prefix, its source ruling, and the ruling
section it is drawn from; **no item is merged with another, and no item
is restated inside a second block.**

| Prefix | Source ruling record | Consequence list | Items |
|---|---|---|---|
| **A5-C#** | [A-5 — chain anchoring](PHASE_4_A5_CHAIN_ANCHORING_RULING_2026-07-22.md) | §7 | C-1 … C-13 |
| **A8-C#** | [A-8 — machine-artifact location](PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md) | §6 | C-1 … C-11 |
| **A9-C#** | [A-9 — single writer](PHASE_4_A9_SINGLE_WRITER_RULING_2026-07-22.md) | §9 | A9-C1 … A9-C10 |

Two items from those lists are **not** carried here, because their own
rulings place them elsewhere: A-5 §7's closing paragraph places its C-9
decomposition of *"verified intact and anchored"* on **AD-050**, where it
is recorded as **A5-C9 (AD-050 limb)**; and A-8 §6's closing paragraph
places its R-5 (`GateRunRecord` location) on **AD-049**. Neither is
restated in this AD, and neither is discharged by it.

**None of the three rulings adds a field to the record.** A-5 §7 (F-2),
A-8 §6, and A-9 §9 (F-23) each state this in terms. The closed field set
above stands exactly as written, and the key-set test that pins it is
unchanged.

#### A-5 — chain anchoring (A5-C1 … A5-C13)

**A5-C1 — the anchor is the external human citation, and nothing inside
the chain is** *(A-5 R-1, §4.1)*. `sequence_number`, the predecessor
hash, and the commit are respectively ordering, interior integrity, and
retention. **None of the three is the anchor.**

| Part | Role | The anchor? |
|---|---|---|
| `sequence_number` | Ordering and interior completeness; the short value an anchor names | **No** |
| predecessor hash | Interior integrity: binds record *N* to *N−1* | **No** |
| the citation `(chain, sequence_number, head hash)` in the cycle's `decision_log.md` | External witness, authored by a human in a different artifact under a different discipline | **Yes** |
| the human-performed commit | Retention and co-visibility: divergence becomes a diff on tracked files | **No** |

No wording in this AD may read as though the chain or the commit anchors
itself. The commit is explicitly demoted on stated grounds: this
repository's git history has already failed to be durable — the PR0
remediation record was destroyed and exists in no reachable ref — so a
mechanism whose durability assumption the repository's own history has
falsified cannot be what the provenance claim rests on. The commit
remains **required** by A8-C8, as retention, not as anchor.

**A5-C2 — anchor content and hash domain** *(A-5 R-2, §4.2)*. An anchor
citation consists of exactly three elements: the **chain identity** (the
repository-relative path `research_archive/<cycle_name>/transition_records.jsonl`,
written in full so a reader holding only the citation can find the file);
the **sequence number** of the record being witnessed; and the **head
hash**, rendered `sha256:<64 lowercase hex>` per the repository's single
existing hash-citation convention and computed over **the UTF-8 bytes of
that record's canonical JSON serialization — the exact line
`write_canonical_jsonl` emits for it, excluding the terminating LF**. The
head hash is therefore **byte-identical to the predecessor-hash field
stored in record *N+1***, so verifying an old citation compares it
against a value the file already carries; only the current head requires
hashing a line.

**A5-C3 — rejected hash domains, recorded as closed** *(A-5 R-2, §4.2)*.
A **whole-file hash** is rejected on the decisive ground that a cited
value must remain checkable after further appends: a file hash cited at
sequence 3 is invalidated by the write of sequence 4, immediately and
permanently. A **Merkle root or hash-of-hashes** is rejected (no
consumer; the length problem is unchanged). A **separate running
"chain hash" field** distinct from the predecessor hash is rejected as a
second representation of one fact — the defect Resolution §2.1 rejected
`Project.current_phase` for. Any digest other than SHA-256 is rejected;
the repository has exactly one convention.

**A5-C4 — numbering origin, per-cycle scope, contiguity** *(A-5 R-3.1 –
R-3.3, §4.3)*. Origin is **1**: the first transition record of a cycle
carries `sequence_number = 1`, so **the head's sequence number is
identical to the record count** and a cited `N` is directly a claim that
the chain contained `N` records. Numbering is **per-file and restarts per
cycle**; sequence numbers are not global and do not order transitions
across cycles, which is why A5-C2's chain-identity element is mandatory
rather than inferred. Sequence numbers are **contiguous ascending
integers `1 … N`, with no gaps and no duplicates**; a gap or a duplicate
is a **chain-invalid** condition — verification refuses, and it is not
repaired, not renumbered, and not reported as a warning.

**A5-C5 — the genesis record** *(A-5 R-3.4, §4.3)*. The genesis record's
predecessor-hash **key is present with the JSON value `null`**. Never an
omitted key (the serialized key set is closed and pinned by test, so
omission changes the key set and fails that test), never an empty string,
and never a sentinel such as `"sha256:0000…"` or the SHA-256 of the empty
string — each of which is a value that could be computed and therefore
forged into an interior position, whereas `null` at any sequence other
than 1 is a structural error a verifier detects trivially. **A `null`
predecessor at any sequence other than 1 is a structural error.**

**A5-C6 — a zero-byte chain file is a valid empty chain** *(A-5 R-3.5,
§4.3)*. `read_canonical_jsonl` returns `[]` for a zero-byte file without
error, and that behaviour is adopted rather than guarded against. The
consequence is recorded because it is the sharpest statement of why the
external anchor is not optional: **a chain emptied to zero bytes is
indistinguishable, from the file alone, from a cycle that has never
transitioned.** Only the external witness distinguishes them.

**A5-C7 — the citation grammar, and the slot that carries it** *(A-5
R-4.1 – R-4.2, §4.4)*. The grammar is defined normatively here, in
exactly one place, as a **single self-locating line** in this fixed
order:

```
**Machine chain anchor.** `research_archive/<cycle_name>/transition_records.jsonl` — seq `<N>`, head `sha256:<64 lowercase hex>`
```

Ruled properties: **one line, found by its bold label alone**, without
the surrounding entry conforming to any particular shape — both decision
logs that exist already diverge from the template's entry shape, so a
carrier defined by position within an entry would be unsatisfiable by two
of two real files. **No version token**, because a version token implies
a parser with a version switch and no parser exists or is authorized
(A5-C9); a change to this grammar is a new AD, and existing citations are
never rewritten. **`Not applicable` is an explicit, valid value**, per
the template's own field discipline, and is the correct value for every
entry that records no phase transition and for every cycle that has no
chain.

The slot is **`docs/templates/decision_log_template.md`**, which gains
one new **required** entry field, `**Machine chain anchor.**`, placed
**after `**Evidence references.**` and before `**Governance status.**`** —
it is a citation, of the same class as evidence references, and must not
be confused with a judgment field. That amendment is a
documentation-only change **bound to the same increment that accepts this
AD**, so that the format and its carrier land together and both land
before Phase C can produce anything to cite. **A format with no slot is
the defect A-5 was raised to close; a slot with no format is
unverifiable.**

**A5-C8 — ordering, cardinality, and the one-to-one rule** *(A-5 R-4.3,
§4.4)*. **One citation per entry, in every entry**; entries recording no
transition carry `Not applicable`, so a reader can always distinguish *no
anchor because no transition* from *anchor omitted*. **A transition entry
cites its own record** — `N` is the `sequence_number` of the record that
the transition described by that entry produced, not the chain head at
some later time and not the predecessor — which yields a **one-to-one
correspondence between transition entries and cited sequence numbers**.
**Ordering is fixed:** human authorization → the mechanical append → the
human authors the entry citing the resulting record → the human commits
both files together under existing archive discipline. **A citation can
never name the commit that contains it** — that hash does not exist when
the line is written — and this AD does not require it to; the anchoring
commit is identified after the fact by git, from the tracked file's
history. **Nothing is retrofitted:** existing entries in
`reference_h3/decision_log.md` and
`positive_control_phase3/decision_log.md` are never edited, and the three
legacy archives, which never receive a chain, never receive a citation.

**A5-C9 — the verification procedure splits, and the split is between
machine and human** *(A-5 R-5, §4.5)*. **Internal verification is
mechanical**: recompute each record's canonical serialization and its
hash; check that record *N*'s stored predecessor hash equals record
*N−1*'s computed hash; check contiguity from 1 with no gaps or
duplicates (A5-C4); check that a `null` predecessor appears at sequence 1
and nowhere else (A5-C5). This detects mutation, reorder, insertion,
interior deletion and a forged predecessor — and it detects **nothing**
about the tail. **Anchored verification takes the anchor as an
argument**: the verifier accepts an expected `(sequence_number,
head_hash)` pair **supplied by the caller**, a human reading the citation
from `decision_log.md`, and confirms that the chain retains a record at
that sequence number whose hash is that value. This is how Phase C's
*"tail truncation detectable via the anchor"* criterion is satisfied and
it is the **only** way it is satisfied. **No code reads, parses, or
writes `decision_log.md`.** The verifier never locates an anchor for
itself; INV-10 is strengthened rather than strained, since the human
artifact is not merely un-written-to but un-read-from, so no code path
can develop a dependency on its formatting. Any future proposal to parse
`decision_log.md` is a new AD. **The corresponding decomposition of
AD-050's *"verified intact and anchored"* precondition is recorded in
AD-050, not here.**

**A5-C10 — anchor lag is inherent, disclosed, and not designed away**
*(A-5 R-6, §4.6)*. At any moment, **every record above the last cited
sequence number is unanchored, and during normal operation that is at
least the newest record**, because the citation is authored after the
append. This is not a defect to be closed and no mechanism is introduced
to close it: closing it would require the writer to anchor its own write,
which is A5-C1's rejected self-witnessing, or an automatic commit, which
is rejected at A5-C13. Consequently **no text in this AD, and no artifact
header, describes a chain as "anchored" without qualification.** The
precise property is **anchored through sequence `N`**, where `N` is the
last externally cited value. The window is bounded by discipline, not by
mechanism — the human writes the entry and commits both files in the same
act — and **nothing enforces that.**

**A5-C11 — the provenance claims, at their true strength** *(A-5 §6.1)*.
These are the **maximum** this AD asserts, and each names what it needs.
They are read together with A9-C8, which makes all of them conditional on
the A9-C4 assumption.

> **Claim 1 — chain alone.** *The records retained in this file form an
> unbroken chain from sequence 1 to sequence M: no retained record was
> altered, reordered, or interior-deleted, and no record was inserted
> between two retained records, without breaking a hash link or a
> sequence contiguity check.* Needs the file. Proves nothing about
> records that are not there.
>
> **Claim 2 — chain plus a citation.** *If the record at sequence `N`
> hashes to the cited `H`, then this file still retains, unaltered, the
> entire prefix of the chain that existed when that entry was authored.
> Removal of any record at or below `N` is detectable by a human
> comparing the citation to the file.* Needs the file and an intact
> `decision_log.md` entry. Answers "a self-contained chain cannot prove
> its own length" **only up to `N`**, never above.
>
> **Claim 2a — the entry-by-entry strengthening.** Because every
> transition entry cites its own record (A5-C8), *the number of
> transition entries in `decision_log.md` and the number of records in
> the chain must agree, and each entry's cited sequence number must match
> its position in that ordering.* A disagreement is an audit finding on
> its face, without any judgment about which artifact is wrong.
>
> **Claim 3 — chain plus citation plus commit.** *The chain and its
> witness were co-present in a committed repository state; a subsequent
> change to either is visible as a diff on a tracked file.* Needs an
> intact git history, which is why it is stated last and weakest.

**The honest summary, carried in these terms:**

> Anchoring converts silent, single-file tampering into tampering that
> requires a coordinated and mutually consistent edit to a
> human-authored, append-only, review-disciplined artifact. **It does not
> prevent tampering. It makes one specific class of it visible to a human
> who looks.**

**A5-C12 — what anchoring explicitly does NOT claim** *(A-5 §6.2)*.

| Not claimed | Because |
|---|---|
| **Automatic commit** | Nothing commits anything; the recorder never invokes git in any mode. The anchoring commit is a human act outside any run, and if the human does not perform it, no commit occurs and nothing reports that fact |
| **Automatic immutability** | A JSONL file on disk is fully writable. No filesystem permission is set, no attribute changed, no git hook installed, no CI check added, no lock file written. "Append-only" describes the **discipline**, not a property of the medium |
| **Immutability conferred by committing** | A commit records a state; it does not freeze a file. History can be rewritten, and in this repository history has already been destroyed once with permanent loss |
| **Writer enforcement** | A9-C2's, and it is a stated assumption. A-5 assumes a well-formed chain and specifies what a malformed one looks like; it prevents nothing |
| **Runtime guarantees** | No daemon, monitor, scheduled verification, CI job, or startup check. Verification runs when a human runs it; a chain can sit tampered and unexamined indefinitely |
| **Proof of time** | Record timestamps are injected and self-asserted. There is no trusted clock and no notarization; a timestamp is a claim by the writer, not evidence |
| **Completeness above the last cited `N`** | Structural, not incidental (A5-C10) |
| **That the transcribed content is true** | Unchanged from this AD's transcription-not-certification ruling: Governance cannot re-derive a gate outcome, so the chain attests to bytes, never to whether a transcribed gate status is correct |
| **That a `decision_log.md` citation is itself protected** | The witness is a text file the same actor can edit. Claim 2 is conditional on the entry being intact and says so. The protection is review discipline and visibility, not enforcement |
| **Anything about the three legacy archives** | They have no transition records and never will. Their absence of a chain is the true state, not a gap |

**A5-C13 — re-affirmed rejections, each closed rather than deferred**
*(A-5 R-7, §4.7)*. **Automatic commit on append remains rejected**, on
Resolution §2.2's two grounds re-verified in A-5: the Governance domain's
read-only posture, and the fact that a mid-run commit mutates the
working-tree state `verify_freeze` reads. Not reopened, not softened, not
made configurable. **The git commit is not the anchor** (A5-C1). **No
external timestamping, notary, blockchain, or third-party attestation
service** — no such dependency exists, it would put a network call inside
the domain that exists to be auditable, and no claim in A5-C11 requires
it. **No filesystem-level immutability, no read-only permissions, no git
hook, no CI check.** Each requires a new AD to reopen; none may be
treated as an obvious extension of this one.

#### A-8 — machine-artifact location (A8-C1 … A8-C11)

**A8-C1 — the partition rule, and no platform-level machine artifact**
*(A-8 R-1, §4.1)*. An artifact whose subject is a **single cycle** lives
inside that cycle's evidence package, `research_archive/<cycle_name>/`;
an artifact whose subject **spans cycles and outlives any one of them**
is platform-level and lives in `docs/`. The rule is adopted from
`RESEARCH_LINEAGE_REGISTER.md`'s own scope paragraph, not invented. Under
it, **every governance machine artifact is per-cycle**; the platform-level
tier is human prose and stays that way, and **Step 9 introduces no
platform-level machine artifact.** No record of this AD is ever written
to `docs/`.

**A8-C2 — the canonical path** *(A-8 R-2, §4.2)*. The transition chain is
**one file per cycle**, at

```
<archive_root>/<cycle_name>/transition_records.jsonl
```

where `<archive_root>` is `research_archive/` in this repository and is
**supplied as an injected parameter, never a module-level constant** —
the discipline `scaffold_project_archive` already follows. Never one
global chain, never one per lineage, never one per attempt. The file sits
at the **cycle directory root**, sibling of `decision_log.md`, not inside
`dataset_hashes/`, `experiment_results/`, or `reviewer_reports/`, each of
which has a defined meaning under Standard §5 that a governance chain is
not; `reproduction_record.json` is the existing precedent for a
fixed-name machine artifact at the cycle root. The filename is
`transition_records.jsonl` rather than `decision_records.jsonl` or
`decision_chain.jsonl` because a name reading as a sibling of
`decision_log.md` invites the conflation AD-045 and this AD exist to
guard against.

**A8-C3 — the filename is undated, and a dated file per append is
rejected** *(A-8 R-2, §4.2)*. Standard §5 requires each file to be dated
*"in its own content **or** filename"*; every record carries an injected
UTC timestamp, so the file is dated in its content, per record, which is
the stronger limb. **A dated file per append is affirmatively rejected:**
it would make every append its own genesis chain, and a chain that cannot
reference its predecessor file proves nothing — the naming convention
would destroy the mechanism it was meant to protect. The file is the
machine counterpart of `decision_log.md`, the one file Standard §5
already recognizes as literally append-only rather than
superseded-by-new-file, and it inherits that discipline. **This is a
reading of §5, not an amendment to it.**

**A8-C4 — the recorder never creates a directory** *(A-8 R-3.1, §4.3)*.
`write_canonical_jsonl` silently `mkdir`s its parent. Left unguarded, a
mistyped or unregistered `cycle_name` would **manufacture an archive
directory with no `archive_manifest.json`** — precisely the
archive↔registry divergence class A-6 R-2 ruled on and declined to
mechanize. **The cycle directory's existence is a precondition of the
first record, never a consequence of it.**

**A8-C5 — the write precondition** *(A-8 R-3.2, §4.3)*. A chain is
written **only into a directory that already contains
`archive_manifest.json`**. This single condition **excludes the three
legacy archives by construction** — they have no manifest and will never
be given one — with **no hardcoded name list**, and therefore without
`core/governance/` needing anything from `tools/archive_manifest.py`. It
is consistent with AD-050's position that the three historical projects
have no transition records at all.

**A8-C6 — identity is checked; completeness is not** *(A-8 R-3.3, §4.3)*.
The manifest is read for exactly one purpose: confirming that
`manifest.project_id`, the directory name, and the record's `project_id`
are **byte-identical**. `lifecycle_version` is **deliberately not
consulted** — interpreting it is `ArchiveVerifier`'s job, and
`ArchiveVerifier` is on Step 9's may-not-implement list. Disclosed: this
makes the recorder the **first component in the repository to read an
existing manifest**, which `RESEARCH_ARCHIVE_MANIFEST.md` anticipated
only for a future `ArchiveVerifier`. It is a three-way identity check,
not a completeness check, and **it must not grow into one.**

**A8-C7 — `RESEARCH_ARCHIVE_MANIFEST.md` is unamended and its
`schema_version` unchanged** *(A-8 R-3.4, §4.3)*. The manifest is a
four-field index that does not enumerate its directory's contents, so a
new file beside it changes nothing the manifest asserts. **The chain sits
inside the directory the manifest indexes, and outside the manifest's
schema.**

**A8-C8 — no new top-level directory, and nothing outside the
repository** *(A-8 R-3.5, §4.3)*. No `governance_records/`, no
`.governance/`, no untracked or out-of-repository store. The retention
half of anchoring requires a **human-performed commit** of the artifact
under existing archive discipline, and **an artifact that git does not
track cannot be anchored that way at all.** A5-C1's demotion of the
commit from anchor to retention does **not** relax this: co-visibility in
a tracked state is still required.

**A8-C9 — the identity relation** *(A-8 R-4, §4.4)*. `cycle_name` is the
**partition key** — the one path segment between the archive root and the
filename — and it is the same identity phase attaches to, so the file is
one-to-one with it. `project_id` is **not a second key**: it is
byte-identical to `cycle_name` and appears in the path exactly once, as
that segment; **the `project_id` field nevertheless stays in the record**,
because the field set is closed and pinned by test, removing a field is a
new AD, and the redundancy keeps a record self-describing if it is ever
quoted outside its file. **`lineage_id` never appears** — not in the
path, not in the filename, not in the record — because a lineage spans
cycles that were in different phases, and a lineage-partitioned chain
would interleave transitions from which no cycle's current phase could be
derived; **the lineage view is obtained by joining in the Register, never
by partitioning the machine artifact.** **`attempt_number` never
appears**, because an attempt does not advance the governance process.

**A8-C10 — `sequence_number` is scoped to the per-cycle file** *(A-8
R-4, §4.4)*. A cycle's sequence numbers are monotonic **within that
cycle**; they are not global and do not order transitions across cycles.
A-8 recorded that the numbering **origin** and the anchor's **format**
remained A-5's to decide; they have since been decided and are carried
here at **A5-C4** (origin 1, contiguity) and **A5-C7** (the citation
grammar). A8-C10 is not merged into those items: it fixes the *scope* of
the numbering, and A5-C4/A5-C7 fix its *origin* and its *citation form*.

**A8-C11 — `Project.repository_path` is a second stored representation,
and nothing binds it** *(A-8 R-4, §4.4)*. Governance may import only
`data`, so the recorder never sees a `Project` and **cannot consult
`repository_path`**; the path is computed from the injected archive root
and the `cycle_name` string. Disclosed: `repository_path` stores the same
location, it agrees with this rule for all three backfilled entries,
**nothing enforces that agreement, and no invariant binding them is
created** — consistent with A-6 R-2's refusal to mechanize the
archive↔registry relation. The only place the two could ever be
reconciled is `core/research/lifecycle.py`.

#### A-9 — single-writer enforcement (A9-C1 … A9-C10)

**A9-C1 — "single writer" is never printed undifferentiated** *(A-9 R-1,
§4.1)*. The phrase conflates three separable properties, and answering
them with one word would produce a claim stronger than its mechanism.
Every sentence in this AD that uses it says which one it means.

| Property | Question it asks | Answer | Mechanism? |
|---|---|---|---|
| **Authority** | Which code path may append to a transition chain? | Exactly one module, reachable through exactly one caller (A9-C3) | **Yes** — a design property, statically checkable and pinnable by test |
| **Exclusivity in time** | Can two appends to one chain file interleave? | Assumed not to; **nothing prevents it** (A9-C4) | **No** — a runtime property, unenforced, knowingly |
| **Ownership / accountability** | Who is answerable for a record having been written? | The single human operator who authorized that transition, never the module | **Partly** — the authorization record is stored; the identity claim in it is self-asserted |

Exclusivity may not borrow the credibility of authority. A reader
encountering an undifferentiated "single writer" will take it to mean the
strongest of the three, which is precisely the one that is not true.

**A9-C2 — the ruling is stated assumption, not mechanical lock, and the
lock is closed rather than deferred** *(A-9 R-2, §4.2)*. Resolution §4.1
posed A-9 as a binary; the answer is **stated assumption**. **No lock is
introduced, in Step 9 or by this decision.** Five grounds, the fourth
decisive:

1. **No lock primitive exists to adopt.** Nothing in `core/` or `tools/`
   imports `fcntl`, `msvcrt`, `flock`, `filelock` or `portalocker`, and
   nothing performs an `os.replace`. A lock is new machinery, with a new
   dependency or new platform-conditional code, in the domain that exists
   to be audited.
2. **A lock is a write, in the domain whose value is not writing.** An
   advisory lock file placed at the cycle root is an undeclared item in
   an evidence package; placed outside the repository it is untracked,
   and an untracked artifact can neither be shown to have been held nor
   be shown to have been absent — the appearance of discipline with none
   of the evidence.
3. **The contention it defends against does not occur.** The platform
   runs with a single human operator directing all sessions, the chain is
   per-cycle so distinct cycles do not contend at all (A8-C2), and no
   transition happens without explicit authorization. Building it would
   be a component whose only designed trigger does not exist — **AD-045's
   surviving objection, applied to the very AD that had to answer it.**
4. **A lock cannot deliver the property the chain needs.** The threat
   model is that *the actor who would author retroactively is the same
   actor who can truncate*. A lock acquired by that actor's own process
   constrains that actor not at all. A lock defends against *accidental*
   interleaving by *cooperating* writers, and the chain's adversary is
   neither. **A mechanism that raises the apparent strength of a claim
   without raising its actual strength is worse than no mechanism.**
5. **A lock here would be untestable in the environment that has it.** A
   single-operator platform cannot exercise real contention, so it would
   ship as load-bearing-looking code covered only by simulated tests.

Reopening requires a new AD arguing against those five grounds on their
merits. **"Stated assumption" is not permitted to mean *unstated*:**
A9-C4 fixes the words, A9-C5 fixes what happens when the assumption is
false.

**A9-C3 — the authority model binds the design, not the filesystem**
*(A-9 R-3, §4.3)*. Exactly **one module**,
`core/governance/decision_recorder.py`, may write a
`transition_records.jsonl`; no other module in any domain reads-modifies
or writes that file, and Phase C pins this by test. That module is
reachable **only through `core/research/lifecycle.py`**, which is already
the only module permitted to import Validation and Governance together
and therefore the only legal binding point that exists at all — this is
the existing import boundary doing the work, not a new restriction.
**Every append carries one explicit human authorization** (AD-050): there
is no writer without an authorizer, and a record with no authorization
record is not a record this system can produce. **The human operator, not
the module, owns the chain; the module is an instrument.** This
constrains what this system does, **not what can happen to the file**.

**A9-C4 — the assumption, in the words it must be stated in** *(A-9 R-4,
§4.4)*. Carried substantively unchanged, and carried in the artifact
header beside the chain's narrow tamper-evidence claim:

> **Single-writer assumption.** At most one process appends to any one
> `transition_records.jsonl` at any one time, and it does so on behalf of
> the single human operator who authorized that transition. **Nothing
> enforces this.** There is no lock, no advisory file, no process
> registry, and no runtime check. A violation is not prevented. It is
> either detected after the fact by chain verification, or — in the case
> named in A9-C7 — it is not detected at all.

Its scope is **one chain file**, not global: two cycles advancing
concurrently do not violate it, because they touch different files
(A8-C2). This is a real narrowing and is claimed as one. It is an
assumption about the **system's own writers** and says nothing about a
human editing the file by hand. It **names the operator, not a process
identity** — no field records which process wrote a line — so it is a
property of practice, not a checkable property of a record.

**A9-C5 — enforcement is detection, not prevention, and the detection is
A-5's** *(A-9 R-5 and R-6.1, §4.5 – §4.6)*. **A-9 introduces no new
detection mechanism.** What serves it is A5-C4's contiguity rule, ruled
for a different reason and covering two of the three concurrency failure
shapes:

| Concurrency failure shape | Detected by | Disposition |
|---|---|---|
| Two writers assign the **same** `sequence_number` and both records land | A5-C4 duplicate check | **Chain-invalid.** Verification refuses |
| A write is lost such that a number is **skipped** | A5-C4 gap check | **Chain-invalid.** Verification refuses |
| Two writers assign the same `sequence_number` and the **second rewrite discards the first record** | **Nothing** | **Undetectable** — A9-C7 |

**The actual enforcement is that an invalid chain blocks further
advancement**, via AD-050's precondition that the chain be verified
intact before any append, and **it is deliberately after the fact**.

**A9-C6 — "written atomically" is disambiguated** *(A-9 R-5, §4.5)*. The
storage clause above requires the append to be *"written atomically
(temp + replace)"*. **Temp-plus-replace makes the *replacement* atomic —
a reader never sees a half-written file. It does not make the
*read-modify-write* atomic, and it therefore does nothing about
last-writer-wins.** A reader who takes "atomic" as "concurrency-safe"
would be wrong. Phase C's docstrings and test names say *"atomic
replacement"*, never *"atomic append"* and never *"concurrency-safe"*.

**A9-C7 — the one failure that is invisible, stated as a non-claim**
*(A-9 §6.3)*. Carried in substantially these terms and not softened:

> If two authorized appends to the same chain interleave such that the
> second rewrite is computed from a prefix that does not include the
> first, the first record is lost and the resulting file is contiguous,
> correctly chained, and internally valid. **No mechanical check in this
> design detects that.** The anchor cannot cover it either, because the
> lost record is by definition the newest and the newest record is always
> unanchored (A5-C10). The only thing standing between this design and
> that outcome is the A9-C4 assumption, and the assumption is not
> enforced.

This is a **non-claim, not a risk with a mitigation.** A risk invites a
mitigation and a residual-risk rating; a non-claim states that the system
does not know, which is the true position. **No mitigation is built, and
this AD may not convert it into a risk.**

**A9-C8 — the whole of A5-C11 is conditional on the A9-C4 assumption**
*(A-9 R-7.5, §8)*. A-5 §9 pre-committed that if A-9 ruled "stated
assumption", A-5 §6.1's claims become conditional on that assumption **and
this AD must say so in those words**. A-9 rules stated assumption, so the
branch fires. **Claim 1, Claim 2, Claim 2a, Claim 3, and the honest
summary — all of A5-C11, none omitted — are conditional on the
single-writer assumption stated at A9-C4.** A-5's trigger names *"§6.1's
claims"* without qualification and is discharged without qualification:
**the condition may not be carried on a subset**, because an A5-C11 claim
printed unconditionally beside conditional ones will be read as the one
that survived the assumption.

One correction A-9 owes A-5 and states rather than elides: A-5 §9's row
describing a lost interleaved write as appearing "as a gap" holds **only
where the two writers assigned different sequence numbers.** In the
last-writer-wins shape both assign the same number and the survivor
leaves **no gap at all** (A9-C7). This corrects the *coverage
description* of a detection mechanism — not the mechanism, not A5-C4, and
not any A5-C11 claim.

**A9-C9 — what writer discipline explicitly does NOT claim** *(A-9 §7.2)*.

| Not claimed | Because |
|---|---|
| **OS-level locking** | No `fcntl`, `msvcrt`, `flock`, `filelock` or `portalocker` appears anywhere in `core/` or `tools/`, and A9-C2 introduces none. No advisory lock, mandatory lock, lock file, PID file, or sentinel |
| **Database locking** | There is no database on this path. Project storage is a plain in-memory dict; the chain is a flat file rewritten by `path.write_bytes`. No transaction, no row lock, no isolation level |
| **Runtime prevention** | No mutex, semaphore, queue, single-instance guard, process registry, daemon, or supervisor. Nothing runs between operator sessions to prevent anything |
| **Automatic enforcement** | Nothing checks the assumption at write time. `advance_phase()` verifies the chain is *intact* before appending; it cannot verify that no one else is appending *concurrently*, and it does not try |
| **Atomicity of the read-modify-write** | A9-C6. The lost-update window is unaffected by temp-plus-replace |
| **Detection of a lost update** | Structural, not incidental (A9-C7). The surviving file is valid on every check the design has |
| **Any claim about who wrote a record** | No writer-identity field exists and none is added. **The chain attests that bytes were not altered since they were written; it never attests who wrote them.** A record's `project_id`, timestamp and authorization record are claims made by whatever produced the line |
| **That the declared authorizer is who they claim** | Standard §4 stores the declared reviewer level verbatim and does not validate the independence claim. Authorization is recorded, never adjudicated |
| **Protection against a hand edit** | A JSONL file on disk is writable by any process with filesystem access. A9-C3 binds this system's design, not the operating system |
| **That an invalid chain can be made valid** | It cannot, and no tool is provided that would try (A9-C10) |
| **Anything about the three legacy archives** | They have no transition records and never will; they have no writer to be single |

**A9-C10 — conflict handling** *(A-9 R-6, §4.6)*. Governing principle:
**an invalid chain is evidence of a governance event, and evidence is not
repaired — it is disclosed.** Editing a chain to make verification pass
destroys the only record that the violation occurred, by the same act
that would conceal it. Therefore:

1. **Duplicates and gaps are chain-invalid and verification refuses**
   (A5-C4, adopted unchanged and not softened).
2. **Not repaired.** No renumbering, no deduplication, no
   "keep the one with the correct predecessor hash", no
   truncate-to-last-valid, no `--force`. None is built, and building one
   later is a new AD.
3. **The invalid chain is retained exactly as it is** — not deleted, not
   truncated, not moved aside. It is the artifact of record.
4. **The response is a governance act:** a dated disclosure under
   Standard §5's correction-is-a-new-file discipline, plus a
   `decision_log.md` entry recording that the chain went invalid, when it
   was noticed, and what is consequently unknown — stating what cannot be
   reconstructed as unreconstructable rather than supplying a
   reconstruction.
5. **The cycle stops advancing**, via AD-050's intact-chain precondition.
6. **The derived phase becomes unknown, and unknown is correct.** Phase
   is derived, not stored, and the failure direction under-claims by
   design; a cycle whose chain is invalid has no provable current phase.
7. **An unauthorized writer is not reached by A9-C3 at all.** A hand
   edit, an ad-hoc script, or any process with filesystem access is
   caught only by what catches tampering generally — and a **well-formed
   record appended by hand is caught by none of it.**
8. **Ambiguity is never tiebroken.** A citation naming a duplicated
   sequence number is ambiguous and verification refuses rather than
   picking a record. **No tiebreak by timestamp** (that trusts exactly
   the field a compromised writer controls); **no tiebreak by "the one
   whose hash matches the citation"** (circular — it makes the citation
   define which record is real, when its entire evidentiary value is
   being an independent witness of a record that already was); **no
   tiebreak by file order, longest valid prefix, or plausibility** (each
   invents a fact). Resolution is a human governance act whose
   permissible outcomes include *"the true state cannot be
   reconstructed"*. **An ambiguous anchor does not invalidate the
   citation:** the `decision_log.md` entry stands as written and is never
   edited; what is recorded is that the chain can no longer be matched
   against it.

---

**Migration Plan §10 item 4 is NOT satisfied by this AD.** Item 4
requires transitions logged "not hand-authored into a `decision_log.md`
after the fact." This AD **rejects that clause on governance grounds**,
per AD-038 and AD-045: hand-authorship of judgment is correct and is
retained. Item 4 is therefore **partially met — mechanical record
present, replacement of hand-authorship deliberately declined** — and
Step 10's retrospective must record it that way. Rounding it up to "met"
is the violation the Migration Plan §10 itself names.

**Migration/status.** `docs/templates/decision_log_template.md` and the
per-project `decision_log.md` files remain the canonical decision-log
mechanism. **One amendment to the template is required by A5-C7 and is
the only change to it:** it gains one required entry field,
`**Machine chain anchor.**`, carrying the citation grammar defined at
A5-C7, in the increment that accepts this AD. The template is otherwise
unchanged, no `decision_log.md` is edited or retrofitted (A5-C8), and no
code writes or reads either file (INV-10, A5-C9).
`PLATFORM_ARCHITECTURE_V1.md` §4.4's
`DecisionLogger` Protocol and the Migration Plan's references to it are
left as-written, per the convention that ADs record divergence rather
than editing those two documents (AD-036, AD-040, AD-044, AD-045).

---

### AD-049: Validation orchestration — `GateRunner` is built, the §5 table governs, and Validation never aggregates

**Decision, five parts.**

**1. `GateRunner` is built.** AD-040 deferred it because "today there
are exactly two gates and one caller shape"; AD-044 named the trigger
verbatim: *"When a second calling pattern (a `GateRunner` dispatching by
name, for instance) actually needs to pass the same bundle of frozen
inputs to gates it does not know the concrete signature of,
`GateContext` is the natural type to introduce then."* Migration Plan
§10 item 3 requires H4's gates to run "through `core/validation/`'s
`GateRunner` against a registered `Gate`, not a bespoke
`experiments/validate_h4_*.py` script." That is the second calling
pattern, as a hard acceptance criterion. Building it now is consistent
with AD-040/AD-044 on their own stated terms, not a violation of them.

**2. `PLATFORM_ARCHITECTURE_V1.md` §5's table governs over its
contradicting same-section prose.** The table (`:505-509`) marks
Validation → Governance ✅. The same section (`:537-539`) states
"Validation and Governance, both Layer 1, never call each other." Both
verified; they cannot both hold. **The table wins**, on three
independent facts: the linter implements the table
(`ALLOWED_DEPENDENCIES["validation"]` includes `"governance"`);
`test_allows_validation_to_import_statistics_and_governance` asserts it;
and AD-043's existing gates depend on it by calling `verify_freeze`. The
prose is an over-general gloss on the acyclicity argument, and it is
*harmlessly* wrong — a single Validation → Governance edge with no
return edge creates no cycle. Recording this is not bookkeeping: left
unrecorded, an auditor can cite the prose to argue that **every gate in
the repository violates the layering**.

**3. Validation never aggregates gate outcomes.**
`PLATFORM_ARCHITECTURE_V1.md:245-247` assigns cycle-level aggregation to
Research by name: a gate reports whether *its own* criteria were met;
"only Research aggregates gate outcomes into" a terminal decision.
Therefore:

- `GateRunRecord` stores the **ordered per-gate statuses only**, with
  **no aggregate field**;
- the aggregation rule — unchanged, `PASS` only if every gate passed,
  `FAIL` if any failed, otherwise `AMBIGUOUS`, with **FAIL dominating
  AMBIGUOUS** — becomes a pure function in `core/research/`,
  unit-testable against a truth table;
- the result is named `sequence_status`, **never** `verdict`, and is
  distinct from the Standard §7 determination (AD-050).

This also strengthens the audit story: "was the verdict derived, not
asserted?" is answered by the auditor recomputing from stored primitives
under a documented rule, rather than by trusting a stored aggregate.

**4. Scope limits on the runner.** `GateRunner` **never imports
`core.governance.pinned_worktree`** — that component creates worktrees
and executes subprocesses, and wiring it into the runner would turn a
comparison engine into a code-execution engine while contradicting the
runner's own purity claim. Re-running a gate under a pinned worktree is
a Research- or tools-level reproduction concern, out of Step 9 scope.
**`ReviewLevel` is not introduced**: it appears exactly once in the
repository, in a sketch (`PLATFORM_ARCHITECTURE_V1.md:210`), while
`DecisionMetadata.review_level` is a plain `str`. An enum with one
consumer, creating a dual vocabulary against a frozen baseline type and
placing a Standard §4 governance concept under Validation's ownership,
is the abstraction AD-005/AD-040/AD-044 already refuse. Review level
stays `str`. `GateResult`, `GateStatus`, `build_report` and the two gate
functions are **unmodified**; `GateStatus` remains exactly three-valued
and a gate crash is an **envelope error, never a status** (a fourth
member would silently change `build_report`'s contract, AD-046).

**5. The import linter is tightened on three counts before any Step 9
domain code lands.** The shared kernel is exempt as an import *source*,
not merely as a target — `_domain_of_file` returns `None` for
`core/shared/` and `check_repository` `continue`s on `None`, while
`test_shared_kernel_imports_are_exempt` only exercises the target
direction. The mechanism is broader than the kernel: `_domain_of_file`
resolves through `DOMAIN_OF_TOPLEVEL.get(...)`, so **any unmapped
top-level package** under `core/` is silently exempt in both directions;
and `_imported_core_modules` collects only `node.level == 0` imports, so
a **relative** import inside Governance is invisible to the checker.
Required, before `LifecyclePhase` or any new domain module lands:

- the shared kernel may import **nothing** from any `core` domain;
- an **unmapped** top-level package under `core/` is an **error**, not
  an exemption;
- relative imports are resolved or rejected.

All three are `tools/` changes, touch no baseline domain code, and are
strict tightenings that cannot make a currently-passing check fail
(verified: no kernel module imports any domain, and no relative imports
exist under `core/` today). **Ordering is part of this decision** —
adding lifecycle vocabulary to the kernel first and the guard second
leaves a window in which the escape hatch is both open and attractive.

**Invariant restated.** INV-11 as originally drafted — "identical inputs
produce a byte-identical `GateRunRecord` serialization" — is **false**:
the record contains freeze verification outcomes, which `verify_freeze`
derives from the working tree, not from the `GateContext` at all, and
the timestamp varies by design. Correct form: *given identical
`GateContext` inputs, identical freeze verification outcomes, and a
fixed clock, serialization is byte-identical.* An invariant that fails
its own test gets the test weakened to make it pass, which is worse than
having no invariant.

**Migration/status.** The two existing gate functions keep their
explicit-parameter contract (AD-044's rationale survives for direct
callers); the runner reaches them through thin per-gate adapters, and an
equivalence test proves dispatching through the runner returns exactly
what calling the function directly returns. `PLATFORM_ARCHITECTURE_V1.md`
§5's prose and §4.2's sketches are left as-written, per the recording
convention.

**Requirement transcribed from the A-8 ruling record — A-8 R-5, carried
here rather than on AD-048.**
[`PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md`](PHASE_4_A8_MACHINE_ARTIFACT_LOCATION_RULING_2026-07-22.md)
§4.5 (R-5) and its §6 closing paragraph place one consequence on
**AD-049**, not AD-048, because `GateRunRecord` is this AD's object. It is
transcribed here verbatim in effect, under the same
prefix-and-source convention the other transcriptions use, as **A8-R5**:

**A8-R5 — a persisted `GateRunRecord` takes the same per-cycle partition
as every other archive artifact** *(A-8 R-5, §4.5)*. *If* a
`GateRunRecord` is persisted to disk at all, its location is per-cycle,
at `research_archive/<cycle_name>/experiment_results/`, with a **dated
filename**. Standard §5 already assigns `experiment_results/` this exact
meaning — "raw, unmodified Validation output (Phase 6), append-only" — and
a gate run record is raw Validation output, so **no new location is
introduced**. The filename **is** dated (unlike the transition chain of
A8-C2/A8-C3, which is undated because it is a chain): each run record is a
discrete artifact superseded file-by-file under §5's convention, matching
the existing dated result JSONs under `reference_h3`.

This item is a **location/disclosure rule only**, and its scope is
expressly narrow:

- **Whether a `GateRunRecord` is persisted at all is a Phase D question
  and is *not* decided here.** A8-R5 fixes only *where* such a record
  goes *if* it is written, so that Phase D does not make a second, ad-hoc
  location choice.
- It asserts **no enforcement**: nothing in this AD makes the recorder,
  the runner, or any check reject a record written elsewhere; the rule
  records the correct location, it does not police it.
- It asserts **no automatic creation**: the `experiment_results/`
  directory is not created by this item, and this AD does not direct any
  component to create it.
- It confers **no path authority** on `GateRunner` or on Validation over
  the archive layout; the partition it names is Standard §5's, restated,
  not one this AD originates.
- It adds **no invariant** to `GateRunRecord` or to the record's field
  set — the closed field set and the INV-11 restatement above stand
  exactly as written.

---

### AD-050: Research cycle identity, derived phase state, and human-authorized transitions

**Decision, four parts.**

**1. The identity model names three things, not one.**
`core/research/project.py:3` claims `Project` "gives every research
cycle -- past or future -- one stable record." That claim is not true
today: `reference_v1` and `reference_v2_h1` are two `Project`s that are
successive **cycles of one research lineage**, and `reference_h3` ran
multiple internal **attempts** (`attempt_001_specification.md`). One
identifier is doing the work of **lineage**, **cycle**, and **attempt**.
Before any phase state is attached, the three are named and it is
recorded that **phase belongs to the cycle** — not to the lineage
(which spans cycles that were in different phases) and not to the
attempt (which does not advance the governance process on its own).

The registry and the archive are also already divergent:
`research_archive/` holds four project directories and three are
registered — `positive_control_phase3` exists on disk with no `Project`
record, no invariant binds the two, and nothing detects it. This AD
rules on that divergence before H4 adds a fifth directory.

**H4 must be registered** before Step 9 §10 item 1 can be met, under a
naming convention reconciled with the existing three — none of which use
bare H-numbering.

**Requirements transcribed from the A-6 ruling record — prefixed, never
merged.** The identity content of part 1 above is decided by
[`PHASE_4_A6_RESEARCH_IDENTITY_RULING_2026-07-22.md`](PHASE_4_A6_RESEARCH_IDENTITY_RULING_2026-07-22.md)
§6, whose consequence list numbers from `C-1` and therefore collides in
label with A-5's and A-8's lists on AD-048. Under the same prefix
convention A-9 §9 directs for those (see AD-048), A-6's items are carried
here as **A6-C1 … A6-C8**, each naming the ruling section it is drawn
from. **No item is merged with another.** A-6 §6 also mandates three
textual changes to this draft; they are applied below as **A-6 textual
change 1 – 3**, each quoting the draft sentence it governs so the change
is deliberate rather than silent. One further item, **A5-C9 (AD-050
limb)**, arrives from the A-5 ruling and is recorded with the evidence
preconditions at the end of this AD rather than here.

**A6-C1 — the canonical identity vocabulary is the Register's three
fields** *(A-6 R-3, §4.3)*. `lineage_id`, `cycle_name` and
`attempt_number` — already defined in `RESEARCH_LINEAGE_REGISTER.md`'s
Schema — are adopted verbatim, with their existing definitions, and **no
others are defined**. `cycle_name` is canonical with the strongest anchor
of the three: it originates in Standard §5, which outranks the Register
and predates it. This AD's terms map exactly onto them:

| Term used in this AD | Canonical field | Governing definition |
|---|---|---|
| "lineage" | `lineage_id` | The Register's: a **mechanism / target-function space** under a Phase 3 attempt cap, *"chosen to identify the mechanism being corrected, not the cycle or document that first defined it"* |
| "cycle" | `cycle_name` | Standard §5's: the research cycle whose evidence package is `research_archive/<cycle_name>/` |
| "attempt" | `attempt_number` | The Register's: an ordered attempt within a `lineage_id`, carrying `counted_against_cap` |

Two precisions attach. **`ProjectId` / `project_id` is a type and a key,
not a fourth identity concept:** where a cycle is registered, both carry
a string **byte-identical to its `cycle_name`**, the same identity in a
typed and a serialized position. **Attempt numbering outside a registered
lineage is cycle-local and caps nothing across cycles:** only attempts
recorded under a `lineage_id`, with `counted_against_cap`, consume a
cross-cycle cap, so `reference_h3`'s "attempt 1 of a maximum three" is a
real governance artifact but is not a Register entry and must not be
cited as though a lineage cap governed it.

**A6-C2 — no second identity vocabulary is created** *(A-6 R-3, §4.3)*.
This AD introduces **no** new identity field, type, enum, dataclass,
registry, or synonym for `lineage_id`, `cycle_name`, or
`attempt_number`. `Project` is unmodified and `ProjectRegistry`'s three
methods are unmodified. `LifecyclePhase` (part 2) is **phase**
vocabulary transcribed from Standard §2 and is orthogonal to identity —
it names *where a cycle is*, never *which cycle it is* — and nothing
here extends or constrains it beyond that boundary.

**A6-C3 — phase attaches to the `cycle_name`** *(A-6 R-3, §4.3;
Resolution D-15)*. D-15 — *phase belongs to the cycle* — is affirmed
unchanged and stated in canonical terms: phase attaches to a
`cycle_name`, **not** to a `lineage_id` (which spans cycles that were in
different phases) and **not** to an `attempt_number` (which does not
advance the governance process on its own).

**A6-C4 — H4's identifier is `reference_h4`** *(A-6 R-1, §4.1)*. The
form is `reference_<hypothesis-label>`, lowercase, satisfying
`^[a-z][a-z0-9_]*$`, following the most recent precedent `reference_h3`
and dropping the profile-version segment, which was already dropped and
did not return. **One string, four places:** the same literal
`reference_h4` is the `research_archive/` directory name, the
`cycle_name`, the `ProjectId` string, and `archive_manifest.json`'s
`project_id` field — **byte-identical**, never four independently-chosen
names. **Bare `h4` is rejected**: it matches none of the three existing
directory names and would be the sole exception to a format rule whose
own docstring records that no exception exists for any project. The
`"project_id": "h4"` in `RESEARCH_ARCHIVE_MANIFEST.md`'s schema example
is an illustrative field value inside a schema example, **not a naming
decision**, and that document is not edited; the divergence is disclosed
rather than corrected in place.

**A6-C5 — the identifier fixes the string, not the hypothesis** *(A-6
R-1 limitation, §4.1)*. The H-number tracks the **hypothesis label**, not
the ordinal — `reference_v2_h1` was the second cycle and carries `h1`.
Roadmap H4 is a specific hypothesis, volume / flow acceleration, which
was **rejected at H3's selection review on data-reliability grounds** and
has never had a Phase 1 artifact or a Phase 2 approval of its own.
Therefore: registering `reference_h4` **asserts nothing** about
hypothesis content, data adequacy, or Phase 2 selection; and
**`reference_h4` is not a generic label for "the fourth cycle"** — if the
next cycle's Phase 2 selects a different candidate, that cycle takes
`reference_h<n>` for *its own* hypothesis label and `reference_h4` is not
reused. **The identifier follows the hypothesis; it never follows the
ordinal.**

**A6-C6 — `positive_control_phase3` is an open cycle, recorded as a
`cycle_name`, unregistered, and deferred** *(A-6 R-2, §4.2)*. The three
registers genuinely disagree, and each is answered in its own terms:

| Register | Status of `positive_control_phase3` |
|---|---|
| `research_archive/` | **An open cycle's live evidence package — not a historical archive directory.** Its manifest declares `lifecycle_version: "v1"`, and that document defines "legacy" as exactly the three predating directories; its own README states it is not a Methodology Freeze, and the cycle has not reached Phase 4 |
| `RESEARCH_LINEAGE_REGISTER.md` | **A recorded `cycle_name`** — of both recorded attempts under the `active` lineage `gate2_score_acf_target_fn`. It is recorded *as a `cycle_name`*; it is **not** a `lineage_id` and must never be cited as one |
| `ProjectRegistry` | **Unregistered, and a future migration target — explicitly deferred** |

Registration is **deferred rather than performed**, on three grounds in
order of decisiveness: Phase A forbids it (documents only, zero code);
**no registration path for an open cycle exists**, since
`backfill_historical_projects()` is the only path, is deliberately
non-idempotent, and is scoped by its own docstring to closed historical
cycles; and — stated rather than borrowed — **it is not blocked on
representability**, because `Project` can already represent an open cycle
(`lifecycle_state=ACTIVE` with `research_outcome=None`) and `origin_date`
would be taken from `archive_manifest.json`'s `created_at`, an
already-recorded evidence date. The deferral rests on the first two
grounds, which are sufficient, and not on a claimed impossibility that
does not exist.

**A6-C7 — no archive↔registry invariant is created** *(A-6 R-2, §4.2)*.
What is absent is an **invariant binding the two**. No such invariant
exists, nothing detects the divergence, and **Step 9 creates none** —
creating one is a mechanism, and mechanisms are not Phase A work.
**`ProjectRegistry`'s contents mean *the set of projects that have been
registered*, and make no claim about the contents of
`research_archive/`.** A reader must not infer archive completeness from
the registry, or registry completeness from the archive.

**A6-C8 — the stale `historical_backfill.py` docstring is disclosed, not
fixed** *(A-6 R-2, §4.2)*. That module's *"the complete set; no fourth
candidate exists in `research_archive/`"* was **true when written and is
stale now**: the module landed 2026-07-19 and
`research_archive/positive_control_phase3/` landed 2026-07-20, one day
later. Correcting it is a code edit and belongs to the increment that
adds a registration path for a non-historical cycle; the correction is a
docstring edit accompanied by an AD or a dated note, **never a silent
rewrite**, because the record should say when the sentence stopped being
true.

**A-6 textual change 1 — the "one research lineage" sentence is not a
`lineage_id` claim** *(A-6 §6 item 1, R-3 precision 1)*. Part 1 above
states that `reference_v1` and `reference_v2_h1` are *"two `Project`s
that are successive **cycles of one research lineage**"*. That sentence
is retained as the observation it is, and is **not** written as a
`lineage_id` claim: **no `lineage_id` exists for that succession, and
none may be opened for it retroactively.** The Register is append-only
and is written to only when a Phase 3 attempt cap opens, so back-filling
one now would record a retroactive fact of exactly the class
`project.py:32-41` already refuses for `origin_date`. **The succession is
expressed as two `cycle_name`s related by the narrative already in the
closeout documents** — never as a shared `lineage_id`, and never with a
second, wider sense of the word "lineage" defined alongside the
Register's.

**A-6 textual change 2 — "H4 must be registered" stands, and its
identifier is now fixed** *(A-6 §6 item 2)*. The sentence *"**H4 must be
registered** before Step 9 §10 item 1 can be met"* stands as a statement
of Step 9's dependency. The identifier it must be registered under is
**`reference_h4`** (A6-C4), which discharges "under a naming convention
reconciled with the existing three". **The registration itself remains
Phase B work and is not authorized by this AD.**

**A-6 textual change 3 — "rules on that divergence" means disclosed and
bounded, not eliminated** *(A-6 §6 item 3)*. The sentence *"This AD rules
on that divergence before H4 adds a fifth directory"* is satisfied by
**A6-C6 and A6-C7** — a ruling that the divergence is **disclosed,
bounded, and unmechanized**, **not** that it is eliminated. The archive
holds four cycles, the registry holds three, the fourth is a live cycle
whose registration is deferred on stated grounds, and Step 9 may proceed
on that basis without either silently reconciling the two or treating the
divergence as an unknown.

**2. `LifecyclePhase` lives in `core/shared/`.** The eight phases of
`RESEARCH_GOVERNANCE_STANDARD.md` §2 (Hypothesis, Research Proposal,
Pre-validation, Methodology Freeze, Implementation, Validation,
Decision, Archive) are genuinely shared vocabulary: Research advances
through them, Validation maps gates to them, Governance records
transitions in them. A closed `str` enum with no behavior and no imports
beyond `enum` — the same profile as `ProjectId`, which is why the kernel
is where it belongs and why Research is not (Validation → Research is
forbidden, so Validation could not map phases to gates at all).

The values are **transcribed exactly from the Standard at freeze time**
and pinned by a test against §2's table. An invented or approximated
phase vocabulary hardcoded into the kernel would be a governance defect
of the kind the retrospective catalogs. **Gated on AD-049 part 5's
linter tightening landing first.**

**`ProjectLifecycleState` is not `LifecyclePhase`.** ACTIVE / FROZEN /
ARCHIVED is a *storage posture*; the eight phases are the *research
process*. Two orthogonal axes: a project can be ACTIVE in Phase 3 or
ACTIVE in Phase 6, and FROZEN says nothing about which phase produced
it. Collapsing them would rebuild exactly the semantic collapse
`project.py:11-13` already warns against for
`lifecycle_state`/`research_outcome`. **`advance_phase()` never
silently mutates `lifecycle_state`.**

**3. Current phase is DERIVED from the transition record chain, not
stored on `Project`.** `Project` is **not modified**, and **no INV-12
exception is created** by Step 9. Four grounds:

- **Two writable representations of one fact, with no reconciling
  invariant, is the defect part 1 already catches** between the archive
  and the registry. Step 9 must not introduce a second instance of the
  problem it is fixing.
- **The failure directions are asymmetric.** With a damaged or
  truncated chain, a derived phase **under-claims** — it regresses to
  the last provable transition. A stored field **over-claims** — it
  asserts Phase 7 with the supporting evidence gone. Only one of those
  is a safe failure.
- **The three historical projects have no transition records at all.** A
  stored field forces a value for them and any value is invented — the
  same retroactive-fact violation `project.py:32-41` already refuses for
  `origin_date` ("inventing one would be a governance violation"). A
  derived phase returns *unknown*, which is the true answer.
- **It keeps INV-12 intact** through the whole of Step 9.

Stated cost: reading current phase requires Research to read
Governance's artifact (a legal edge, already required by the transition
flow) at O(chain length). With four projects and fewer than twenty
transitions that cost is not real; if it later becomes real, a cache is
a derived-value optimization with its own AD, not grounds to duplicate
the source of truth now.

**4. No transition is ever automatic, at any gate status.**
`advance_phase()` requires an explicit human authorization argument
every time. Gate status determines *what kind* of authorization is
required and *what must be disclosed* — never whether a machine may
proceed unattended.

| `sequence_status` | Automatic | Authorization required | Recorded as |
|---|---|---|---|
| PASS | Never | Explicit authorization at the Standard §2 level for the target phase | normal record |
| AMBIGUOUS | Never | Explicit authorization **plus** a written `decision_log.md` rationale naming each AMBIGUOUS gate and why advancing is justified | `authorized_with_ambiguity`, ambiguous gate names stored |
| FAIL | Never | Explicit **override**, Level 2 minimum, plus a decision-log entry stating the failed criterion and the grounds for overriding | `override`, stored distinctly — never silently equivalent to a pass |

*Why not auto-advance on PASS.* A runner's PASS means only "the frozen
criteria compared favourably." Standard §2 assigns every transition a
reviewer-independence level, which is a human obligation. Advancing on
PASS satisfies the comparison while skipping the review — AD-038's trap
in a new location.

*Why AMBIGUOUS is permitted-with-disclosure rather than blocking.*
AD-043 establishes that AMBIGUOUS means the gate lacked a trustworthy
frozen basis to decide — a **process** gap, not evidence against the
hypothesis. H3 advanced with documented AMBIGUOUS gates. Blocking would
retroactively invalidate that run and would pressure operators to invent
a threshold to clear the block, which AD-043 forbids. The control is
disclosure, not prohibition.

*Why FAIL blocks harder.* FAIL means a real frozen criterion was
evaluated and not met. Advancing is legitimate only as a disclosed
override with a named accountable reviewer. Recording `override`
distinctly from `authorized_with_ambiguity` is what stops a future
reader from seeing "advanced" and assuming the criteria were met.

**Vocabulary boundary.** `GateStatus` is PASS/FAIL/**AMBIGUOUS**;
Standard §7's cycle determination is PASS/FAIL/**INCONCLUSIVE**. These
are different vocabularies at different levels and no mapping exists
anywhere in the repository. The sequence aggregate keeps **gate**
vocabulary and is named `sequence_status`; the Phase 7 determination is
a separate, **human-authored** Standard §7 value; and **no code derives
the latter from the former.** Recording an aggregate as "AMBIGUOUS"
where Phase 7 requires "INCONCLUSIVE" would put a determination in the
archive in a vocabulary the Standard does not define.

**Authorization is recorded, never adjudicated.** Per Standard §4 the
platform stores the declared reviewer level verbatim and does not
validate the independence claim. No record may describe a Level 2 review
as "independent" unqualified.

**Evidence preconditions for any advance.** A `GateRunRecord` for
**every** gate the target phase requires (a missing gate is a refusal,
not an AMBIGUOUS); freeze `VERIFIED` at both bracket ends with a
non-empty covered-path set and the full list recorded (AD-047);
`measurement_provenance` present or its absence explicitly recorded as
an audit finding; and the decision chain verified intact and anchored
**before** the append, so a transition is never written onto a broken
chain.

**A5-C9 (AD-050 limb) — "verified intact and anchored" decomposes into a
machine half and a human half** *(A-5 R-5 and §7 C-9)*. The A-5 ruling
places exactly one requirement on this AD rather than on AD-048, and it
is this: the precondition immediately above is **two conditions, not
one**, and the word "anchored" must not be read as something the machine
did.

- ***Verified intact* is mechanical and automatic.** Recompute each
  record's canonical serialization and hash; check that record *N*'s
  stored predecessor hash equals record *N−1*'s computed hash; check
  `sequence_number` contiguity from 1 with no gaps or duplicates; check
  that a `null` predecessor appears at sequence 1 and nowhere else. This
  detects mutation, reorder, insertion, interior deletion and a forged
  predecessor — and **nothing about the tail**.
- ***Anchored* is a human act.** The verifier takes the expected
  `(sequence_number, head_hash)` pair **as an argument supplied by the
  operator**, read by hand from the previous transition entry's
  `**Machine chain anchor.**` line in the cycle's `decision_log.md`. If
  the pair is supplied, the verifier additionally confirms that the chain
  retains a record at that sequence number whose hash is that value.
  **No code reads, parses, or writes `decision_log.md`**, so the verifier
  never locates an anchor for itself; INV-10 holds on the read side as
  well as the write side.

Two consequences follow and are stated rather than left to be inferred.
**An advance whose operator supplies no expected pair has satisfied
*verified intact* and has not satisfied *anchored***, and must not be
recorded as though it had. And because the newest record is always
unanchored until its entry is written (AD-048's A5-C10), the chain a
transition is appended to is **anchored through the last cited sequence
number**, never "anchored" unqualified.

**Migration/status.** `Project`, `ProjectLifecycleState`, and
`ProjectRegistry`'s existing three methods are unchanged.
`core/research/lifecycle.py` is the only module permitted to import
Validation and Governance together, and is therefore the only legal
binding point between gate outcomes and decision records — because
Governance cannot import Validation, no other layer can perform that
binding at all. Deliberately **not** built: any `Phase` class hierarchy,
transition-table object, event bus, phase-entry/exit hooks, or
`LifecycleEngine` — the same discipline AD-033/AD-036/AD-040/AD-044
applied.
