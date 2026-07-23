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

**Citations *into* this file shift by a single uniform offset, and the
accepted ruling records that carry them are not edited.** Four accepted
ruling records cite `PHASE_4_STEP9_DRAFT_ADRS.md` by line range, each
taken against the file as committed at its own HEAD. The AD-047 revision
above is confined to the AD-047 section, so **every such citation moves
by exactly +218 and none of them changes what it points at.** Verified
by matching the cited anchor text line-for-line:

| Cited as | Resolves here to | Anchor content, unchanged | Cited by |
|---|---|---|---|
| `:110-115` | `:328-333` | AD-048's consumer-less-abstraction condition ("This AD is void if…") | A-9 F-22 |
| `:121-128` | `:339-346` | AD-048's closed field set, `project_id` … predecessor SHA-256 | A-5 F-2 and §10 |
| `:121-131` | `:339-349` | The same field set plus the "Never records" opening | A-9 F-23 and §10 |
| `:144-150` | `:362-368` | AD-048's canonical-JSONL storage and read-append-rewrite sentence | A-8 F-16; A-9 F-5 and §10 |
| `:170-178` | `:388-396` | AD-048's external anchoring, all three parts | A-5 F-1 and §10; A-8 F-18 and re-run |
| `:329` | `:547` | The AD-050 heading | A-6 F-18 |
| `:336-339` | `:554-557` | AD-050's lineage / cycle / attempt sentence | A-6 F-19 |
| `:383-403` | `:601-621` | AD-050 part 3's four grounds and its stated cost | A-8 F-24 |
| `:457-461` | `:675-679` | AD-050's evidence preconditions, incl. "verified intact **and anchored**" | A-5 F-16; A-9 F-11 and §10 |

**Nothing in those rulings is reopened, re-read, or amended by this
table.** Each finding continues to rest on the text it quoted verbatim
in its own body; the quoted text is what makes the finding checkable,
and every quotation still matches this file byte-for-byte. The line
number is a locator, not the evidence. This note exists so a later
reader following a locator lands where the ruling meant, without any
accepted record being touched — which is the least invasive resolution
available, and the only one consistent with retaining accepted rulings
unedited.

**A standing consequence for later revisions of this file.** Any future
edit above AD-048 moves these locators again. The obligation that
follows is to update **this table**, never the rulings.

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
  replace). The known Windows CRLF fragility in this module is inherited
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
auto-committing:

- every record carries a monotonic `sequence_number`;
- the hand-authored `decision_log.md` entry — written anyway under
  AD-038 — **cites the chain head hash and sequence number** at time of
  writing, giving a human-witnessed anchor at zero new machinery;
- the anchoring **commit is performed by a human, outside any gate
  sequence**, under the existing archive discipline.

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
mechanism, unchanged. `PLATFORM_ARCHITECTURE_V1.md` §4.4's
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
