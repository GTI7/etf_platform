# Step 9 Architecture Reconciliation Review — Adversarial

**Status: review. No code, no existing file modified by this document.**

**Verdict on the proposal: C+ — ACCEPT DIRECTION, RETURN FOR CORRECTION.**
The proposal's core structural judgments are correct and better-verified
than its predecessors. But it contains **one factual error about the
baseline**, **two claims that would not survive an adversarial audit**,
and **three internal contradictions**. One blocking defect it correctly
flagged (PR0) is worse than it knew: the deviation it points at is not
merely undocumented — the underlying hole is **live in the code at the
baseline commit**, and it makes the proposal's central invariant
vacuously satisfiable.

**Baseline.** Every claim below was verified against `2c7fb2c`
(tag `phase4-final-before-h4-20260722`, confirmed to exist), by reading
the tree and by execution, not against any document's description of it.

---

## 0. What was verified, and what changed as a result

| Proposal claim | Status |
|---|---|
| AD-045 is terminal, with a literal re-opening clause | **Confirmed verbatim** (`ARCHITECTURE_DECISIONS.md:1150-1156`) |
| AD-040/AD-044 defer `GateRunner`/`GateContext` pending a second calling pattern | **Confirmed verbatim** (`:1068-1072`) |
| Governance → Validation is forbidden with a dedicated test | **Confirmed** (`ALLOWED_DEPENDENCIES["governance"] == {"data"}`; `test_detects_forbidden_governance_to_validation_import`) |
| Validation → Research is forbidden | **Confirmed** (`research` absent from validation's allowed set) |
| No `advance_phase()` anywhere in `core/` | **Confirmed** — zero definitions; only three docstring references |
| No `LifecyclePhase`; only `ProjectLifecycleState` (ACTIVE/FROZEN/ARCHIVED) | **Confirmed** |
| `DecisionMetadata.decided_at` is a bare `str` | **Confirmed** |
| `write_canonical_jsonl` rewrites whole-file via `write_bytes` | **Confirmed** |
| `core/shared` is exempt from the dependency table | **Confirmed — and materially worse than the proposal assumes (§1.2)** |
| Phase 4 gives the dataset chain tamper-evidence the recorder can inherit | **FALSE (§1.3)** — no hash chain exists anywhere in `core/governance/` |
| PR0 deviation ruling is "open, no trace in docs" | **Confirmed and understated (§1.1)** — not in `docs/`, not in any git ref, and the hole is live |

---

## 1. Blocking findings — these must close before Phase A completes

### 1.1 BLOCKER — `verify_freeze` returns `VERIFIED` for an empty path set

This is the finding that invalidates the proposal's provenance story if
left unaddressed, and it is the concrete substance behind the PR0
blocker the proposal lists as open question 6.

`verify_freeze` (`core/governance/freeze_verifier.py:129-178`) builds
`paths` from `covered_paths`, loops over it, and derives status from
whether `errors`/`drifted` are non-empty. With an empty iterable the
loop body never executes, both lists stay empty, and the function falls
through to `status = FreezeStatus.VERIFIED`.

Verified by execution against the baseline:

```
verify_freeze('2c7fb2c', [])  ->  FreezeStatus.VERIFIED, errors=(), drifted=()
```

**Why this is load-bearing for Step 9, not a stray edge case:**

- AD-043 makes gates render `AMBIGUOUS` when `verify_freeze` does not
  return `VERIFIED`. An empty `covered_paths` returns `VERIFIED`, so a
  gate with **zero freeze coverage** is free to render `PASS`.
- The proposal's **INV-3** ("no gate executes against an unverified or
  drifted freeze") is therefore **vacuously satisfiable**. So is the
  §6.6 pre/post bracket: both ends return `VERIFIED` on an empty set,
  and the bracket agrees with itself perfectly while proving nothing.
- Every `GateRunRecord` produced this way would be internally
  well-formed, chain-verifiable, and evidentially empty. An auditor who
  finds this does not dispute one gate — they dispute the meaning of
  every freeze verification in the archive.

**No guard exists.** A search across `core/` and `tests/` for any
emptiness check on `covered_paths` returns nothing. There is no test
pinning this behavior in either direction.

**The remediation record is gone.** Project memory records
`docs/PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md` disclosing
exactly this ("`freeze_verifier.py`'s empty-covered-paths fix is outside
PR0's frozen roadmap scope and requires a ruling"). That file does not
exist in `docs/`, and `git log --all --diff-filter=A` finds it in **no
reachable ref**. It was destroyed in the 2026-07-21 incident and never
restored. So the repository today has: the hole, no fix, no test, and no
disclosure.

**Required resolution, and it must not be a baseline edit.** The
proposal's INV-12 forbids modifying anything at or before the baseline,
and `freeze_verifier.py` is baseline code. Do both of the following,
neither of which touches it:

1. **Phase A (documentation):** re-issue the destroyed deviation record
   as a new, dated disclosure stating that the empty-`covered_paths`
   vacuous-`VERIFIED` behavior is live at `2c7fb2c`, that its original
   remediation record was destroyed, and that every existing
   `VerificationResult` in the archive is therefore only as strong as
   the path set it was called with. This is a governance disclosure
   obligation independent of whether Step 9 proceeds.
2. **Phase D (new code only):** `GateContext` construction **rejects an
   empty `freeze_covered_paths`**, and `GateRunner` refuses the run
   before any gate executes. The guard lives in new Validation code, so
   baseline stays untouched and INV-12 holds.

A fix inside `freeze_verifier` itself is the right long-term answer but
belongs to its own increment with its own ruling — not smuggled into
Step 9, which is precisely the mistake PR0 was cited for.

**INV-3 must be restated** as: *no gate executes against a freeze
verification whose covered-path set is empty, unresolved, or drifted.*
The current wording is satisfiable by a run that verified nothing.

### 1.2 BLOCKER — the shared kernel is an unguarded escape hatch

The proposal recommends placing `LifecyclePhase` in `core/shared/`, and
its reasoning (kernel exemption, `ProjectId` precedent, closed enum with
no behavior) is sound. Its *safety* claim is not.

`_domain_of_file` returns `None` for `core/shared/`, and `check_repository`
**`continue`s on `None`** — the kernel is exempt as an import *source*,
not merely as a *target*. `test_shared_kernel_imports_are_exempt` only
exercises the target direction. Consequence: a module in `core/shared/`
may import `core.validation`, `core.research`, or anything else, and the
linter stays green.

Today that is harmless because the kernel holds a `Clock` protocol, two
`NewType` blocks, and `Money`. The moment it holds *lifecycle
vocabulary*, it becomes the natural place for a "small helper" that
knows what a phase requires — and the linter will not stop it. The
forbidden-edge guarantee that all of Step 9's layering rests on would
then be enforced by nothing but reviewer attention.

**Required, in Phase B, before `LifecyclePhase` lands:** extend
`tools/check_import_boundaries.py` so the kernel may import **nothing**
from any `core` domain, with a test asserting a kernel→domain import is
a violation. This is a `tools/` change, not baseline domain code, and it
is a strict tightening — it cannot make any currently-passing check
fail (verified: no kernel module imports any domain today).

Do this **before** the enum is added, not after. Adding the vocabulary
first and the guard second leaves a window in which the escape hatch is
both open and attractive.

### 1.3 The Phase 4 "chain" the recorder inherits does not exist

§7.3 argues the hash chain gives the mechanical record "the same
tamper-evidence property the Phase 4 dataset chain already has."

There is no chain. `grep` for `prev_hash|previous_hash|chain` across
`core/governance/*.py` returns **nothing**. `ReproductionRecord` holds
`commit_hash`, a `dict[str, str]` of `dataset_content_hashes`, and a
`result_report_hash` — a **hash set bound in one record**, not a linked
sequence. Nothing in Phase 4 links record *N* to record *N−1*. The
commit message "Phase 4 governance evidence chain" describes an evidence
*chain of custody*, not a cryptographic hash chain.

This matters twice. It removes the proposal's strongest stated
precedent — the chain is **novel work**, not a reuse, and must be
budgeted and reviewed as such. And it is exactly the kind of
overclaim-by-borrowed-authority that got PR0 returned. Rewrite the
justification to stand on its own merits, which it can (§1.4 aside).

### 1.4 The hash chain does not detect the most likely attack

§7.3 claims: editing breaks every subsequent link; deleting breaks the
chain; reordering breaks it. The first and third are true. **The second
is only true for interior deletions.**

Truncate the file after record *N* — drop the last three entries
entirely — and what remains is a **perfectly valid chain**. Every link
verifies. Genesis is intact. A verifier that only checks link integrity
reports success. Deleting the file and starting a fresh genesis chain
also verifies clean.

This is not a hypothetical attack profile. The failure this component
exists to prevent — retrospective authorship, per the retrospective's
Entry 15 finding — is committed by an operator with write access to the
file, which is exactly the actor who can truncate it. **A self-contained
chain cannot prove its own length.** F-9's claim that chain verification
detects a truncated tail is wrong for whole-record truncation; it holds
only for a torn partial line.

**Required:** the chain must be **externally anchored**. Cheapest
mechanism consistent with this platform, requiring no new machinery:

- every record carries a monotonic `sequence_number` (catches interior
  deletion without rehashing);
- the artifact is **committed to git on every append**, so the chain
  head hash and record count are witnessed by an independent,
  append-only, hash-linked store the platform already runs;
- each record cites the commit of its own predecessor's append, making
  the git history the anchor;
- the human `decision_log.md` entry (which is written anyway, per
  AD-038) cites the chain head hash at time of writing — a second,
  human-witnessed anchor.

Without an anchor, the honest claim is narrower than §7.3's and must be
stated in the artifact: *this chain proves no retained record was
altered or reordered; it does not prove no record was removed.*

### 1.5 Migration Plan §10 item 4 cannot be met, and acceptance of AD-050 does not change that

The proposal frames the choice as: accept the new AD and item 4 is met,
or decline it and item 4 is "partially unmet." Both branches are wrong,
because item 4's actual text is:

> "every phase transition is logged via `DecisionLogger`, **not
> hand-authored into a `decision_log.md` after the fact**."

The clause after the comma is not decoration — it is a *replacement*
requirement. `DecisionRecorder` is deliberately **additive**: §7.1 keeps
`decision_log.md` canonical for judgment and INV-10 forbids any code
writing to it. So a fully-built, fully-accepted `DecisionRecorder`
leaves item 4 **permanently partially unmet by design**, and that is the
*correct* outcome — AD-038 and AD-045 both concluded hand-authorship is
right for this artifact.

**Required:** AD-050 must state plainly that item 4's replacement clause
is **rejected on governance grounds**, not satisfied, and that Step 10's
retrospective records item 4 as partially met with the reason. The
Migration Plan's own §10 anticipates exactly this and forbids rounding
up. Framing acceptance of AD-050 as "item 4 now met" would be the
rounding-up violation §10 names.

---

## 2. Issue 1 — the `DecisionLogger` contradiction

### 2.1 Verdict: **B — clarify AD-045. Do not supersede it.**

The proposal recommends AD-050 "supersedes AD-045 **narrowly**." Reject
that framing. Supersession is wrong on the facts and hazardous in
practice.

**On the facts:** AD-045's decision is *"no `DecisionLogger`
implementation is planned; `core/governance/` is not expanded by this
AD."* After `DecisionRecorder` ships, that sentence is **still literally
true**. No `DecisionLogger` exists; nothing writes `decision_log.md`;
hand-authorship remains canonical. A decision you have not contradicted
is not one you have superseded. AD-045 also pre-authorized this exact
path — *"that is a new decision to make at that time, against that
concrete need, **not a resumption of this one**."* AD-045 is not an
obstacle Step 9 must clear; it is the **specification** Step 9 is
building to.

**On the hazard:** an AD index reading "AD-045 — superseded" tells every
future reader that the no-automated-decision-logging decision was
overturned. The next component that wants to write a judgment field will
cite AD-050 as precedent for AD-045 no longer binding. That is precisely
the erosion §7.1 warns about, installed at the top of the AD by its own
status line. **Supersession language is itself the governance risk here.**

Since existing files are not modified, AD-050 must carry the
clarification internally and unmissably: *AD-045 is not superseded, is
not amended, and remains in force in full.*

### 2.2 Assessment of the `DecisionRecorder` concept

Against its five stated requirements:

| Requirement | Verdict |
|---|---|
| Not a decision authoring system | **Sound.** Enforced by the field whitelist (§7.1) + INV-10 |
| Not replacing `decision_log.md` | **Sound**, and it is the reason item 4 stays partially unmet (§1.5) |
| Only mechanical evidence | **Sound, but under-enforced** — see below |
| Append-only JSONL | **Sound**, with the whole-file-rewrite constraint the proposal correctly flags |
| Hash chained | **Necessary but insufficient** — see §1.4 |
| References commits, phases, gates, reproduction records | **Sound**, and correctly expressed in primitives only |

**One correction, one addition.**

*Correction — "mechanical" needs a structural test, not a review
convention.* The whitelist in §7.1 is prose. The failure mode (F-12) is
a field named `notes` or `context` appearing in v2 and quietly becoming
where judgment lives. **Required:** the record is a frozen dataclass
with a **closed** field set, and a test asserts the serialized key set
is **exactly** the expected set — so adding a field fails a test and
forces an AD. The same discipline `GateStatus` gets under INV-4.

*Addition — Governance must not appear to certify what it transcribes.*
Architecture §4.4: Governance "certifies nothing it did not
independently re-derive." `DecisionRecorder` stores gate names and
statuses that Governance **cannot re-derive**, because it cannot import
Validation (§1 forbidden edge). A Governance-owned artifact asserting
"gate X passed" reads, to an auditor, as Governance vouching for gate X.
It cannot and must not. **Required:** the recorder is documented, and
self-documents in its artifact header, as a **transcription with
integrity guarantees** — it certifies that the bytes were not altered,
never that the transcribed content is true. This is a one-line
distinction with large consequences and it belongs in the artifact, not
only in an AD.

### 2.3 Required ADR text

> ### AD-050: `DecisionRecorder` — mechanical transition records under AD-045's own re-opening condition
>
> **Relationship to AD-045: clarifying, not superseding.** AD-045 is not
> superseded, not amended, and remains in force in full. Its decision —
> "No `DecisionLogger` implementation is planned" — remains literally
> true after this AD: no `DecisionLogger` is built, no code writes
> `decision_log.md`, and hand-authored narrative remains the canonical
> record of judgment. This AD is the "new decision, against that
> concrete need" AD-045's final paragraph explicitly reserved, made now
> that the need is concrete.
>
> **What AD-045 got right and what still holds.** Both of AD-045's
> arguments survive intact and constrain this AD rather than being
> answered by it:
> 1. **AD-038's authored-evidence principle.** A mechanically generated
>    entry would satisfy "an entry exists" while omitting "which
>    candidate was ranked where and why" and "known limitations" —
>    fields that are, and can only be, human judgment. This AD does not
>    weaken that. It authorizes recording **only** facts that are
>    mechanically derivable and independently checkable, and forbids the
>    recorder from expressing judgment in any form.
> 2. **The consumer-less-abstraction objection.** AD-045 refused to
>    build a component whose only designed trigger did not exist. That
>    objection is answered **only** by `advance_phase()` actually being
>    built first. This AD is void if `DecisionRecorder` is implemented
>    before `ProjectRegistry.advance_phase()` has a real caller;
>    ordering is a condition of this decision, not an implementation
>    detail (see AD-049).
>
> **Decision.** `core/governance/decision_recorder.py` provides an
> append-only, hash-chained, externally-anchored store of **mechanical**
> phase-transition records. Scope:
>
> - **Records, exclusively:** `project_id`, `sequence_number`,
>   `from_phase`, `to_phase`, injected UTC timestamp, code commit hash,
>   freeze commit ref and its verification outcome **and its covered-path
>   count**, gate names with their statuses as plain strings, evidence
>   refs as opaque strings (AD-042), an authorization record (AD-049),
>   the `ReproductionRecord` reference establishing measurement
>   provenance where one exists, and the SHA-256 of the predecessor
>   record's canonical serialization.
> - **Never records:** rationale, interpretation, narrative, ranking,
>   known limitations, or any free-text field capable of carrying them.
>   The record type is a frozen dataclass with a closed field set; a
>   test pins the exact serialized key set, so adding any field requires
>   a new AD rather than a commit.
> - **Never writes** `decision_log.md`, nor any file the human authors.
> - **Expressed in primitives and kernel types only.** Governance cannot
>   import Validation (`ALLOWED_DEPENDENCIES["governance"] == {"data"}`,
>   asserted by `test_detects_forbidden_governance_to_validation_import`).
>   The recorder therefore never sees a `GateResult`. Research projects
>   gate outcomes down to strings and passes them (AD-047's PR-6).
>
> **Transcription, not certification.** Governance "certifies nothing it
> did not independently re-derive" (`PLATFORM_ARCHITECTURE_V1.md` §4.4).
> The recorder cannot re-derive a gate outcome — the forbidden edge is
> what guarantees its auditability. It therefore certifies exactly one
> thing: that the retained records were not altered or reordered since
> they were written. It asserts nothing about whether a transcribed gate
> status is correct. The artifact states this in its own header; an
> auditor must not be able to read Governance as vouching for
> Validation's conclusions.
>
> **Tamper-evidence, stated at its true strength.** The chain proves no
> **retained** record was altered, reordered, or interior-deleted. It
> **cannot** prove no record was removed from the tail, nor that the
> file was not replaced wholesale with a shorter valid chain — a
> self-contained chain cannot prove its own length, and the operator who
> would author retroactively is the same actor who can truncate.
> Length and existence are anchored externally: monotonic
> `sequence_number`s, the artifact committed to git on every append, and
> the head hash cited in the corresponding hand-authored
> `decision_log.md` entry. The claim in the artifact is the narrow one,
> never the broad one.
>
> **Migration Plan §10 item 4 is NOT satisfied by this AD.** Item 4
> requires transitions logged "not hand-authored into a
> `decision_log.md` after the fact." This AD **rejects that clause on
> governance grounds**, per AD-038 and AD-045: hand-authorship of
> judgment is correct and is retained. Item 4 is therefore **partially
> met — mechanical record present, replacement of hand-authorship
> deliberately declined** — and Step 10's retrospective must record it
> that way. Rounding it up to "met" is the violation §10 itself names.

---

## 3. Issue 2 — the research lifecycle gap

### 3.1 Finding: there is no research phase model, and H1–H4 are not phases

**Verified.** The repository has **infrastructure lifecycle states
only**:

- `ProjectLifecycleState` = `ACTIVE` / `FROZEN` / `ARCHIVED`
  (`core/research/project.py`) — storage/governance posture.
- No `LifecyclePhase`, no phase enum, no transition function anywhere in
  `core/`. `core/validation/__init__.py` states it outright: *"No
  `LifecyclePhase` enum or workflow-state concept exists either."*
- Zero `advance_phase` definitions.

**A necessary correction to the question's framing.** H1/H2/H3/H4 are
not lifecycle phases and were never candidates to be. They are
**hypothesis (project) identities**; the eight phases are
`RESEARCH_GOVERNANCE_STANDARD.md` §2's Hypothesis → … → Archive. Two
distinct axes, and conflating them would rebuild exactly the semantic
collapse `project.py`'s docstring already warns against for
`lifecycle_state`/`research_outcome`.

As **identities**, H1–H4 also do not exist as the question assumes. The
three registered projects are `reference_v1`, `reference_v2_h1`,
`reference_h3` (`core/research/historical_backfill.py:43,59,76`).
There is no `h4`, and the existing three do not use bare H-numbering.
Step 9 §10 item 1 requires H4's transitions recorded via
`ProjectRegistry`, which requires **registering an H4 project first**
under a naming convention reconciled with the existing three. The
proposal omits this; it is small, but it is on the critical path and
belongs in PR-2.

So: **only infrastructure lifecycle states exist.** The domain phase
model is genuinely absent, and the proposal is right that it is the
unnamed prerequisite for everything else.

### 3.2 Minimal `ResearchLifecycle` abstraction

Constraints honored: no enterprise abstraction, single-developer
maintainable, provenance semantics preserved. **Three pieces. No state
machine framework, no engine, no registry of transitions.**

**(1) `core/shared/lifecycle_phase.py` — vocabulary only.**

A closed `str` `Enum` of the Standard §2 phases, transcribed **exactly**
from the Standard at freeze time, with no behavior, no methods beyond
ordering, and no imports beyond `enum`. Same profile as `ProjectId`:
genuinely shared (Research advances through it, Validation maps gates to
it, Governance records transitions in it), which is why it belongs in
the kernel and not in Research.

Gated on §1.2's linter tightening landing first.

A test pins each member's value against the Standard's §2 table
(F-13). Phase ordering is the enum's declaration order — the Standard
says phases are sequential and may not be skipped, so `1 < 2 < … < 8` is
domain truth, not convenience.

**(2) `ProjectRegistry.advance_phase()` — one function, explicit inputs.**

Not a state machine. A function that validates a requested transition,
demands its evidence preconditions, and persists the result. Its policy
is §5's table, stated once, in one place, testable in isolation.

**(3) `core/research/lifecycle.py` — the composition seam (PR-6).**

The only module permitted to import Validation *and* Governance
together. Assembles the `GateContext`, calls the runner, projects
results to primitives, calls the recorder, and applies the transition
policy. This is load-bearing, exactly as the proposal argues — because
Governance cannot import Validation, **no other layer can legally bind
gate outcomes to decision records.**

**Deliberately not built:** no `Phase` class hierarchy, no transition
table object, no event bus, no phase-entry/exit hooks, no
`LifecycleEngine`. If a second transition shape ever appears, that is
when to reconsider — the same discipline AD-033/036/040/044 applied.

**What is *not* stored on `Project`.** `current_phase` must be a **new,
separate field**, never overloaded onto `lifecycle_state`. A project can
be `ACTIVE` in Phase 3 or `ACTIVE` in Phase 6; `FROZEN` is a storage
posture that says nothing about which phase produced it. Two axes, two
fields — and note this means `Project` (a baseline, frozen dataclass)
gains a field, which is a **baseline change** and therefore an INV-12
event requiring its own AD. The proposal does not notice this. See §6.2.

---

## 4. Issue 3 — `GateRunner` architecture and dependency direction

### 4.1 The dependency direction, stated correctly

The proposal's direction is right. The **rules that fix it** are worth
stating precisely, because the architecture document contradicts itself
on one of them (§4.2).

```
                    Research  (Layer 2)
                   /    |     \
        imports   /     |      \  imports
                 v      v       v
        Validation   Governance   Data        <- Layer 1 / 0
             |            |
             |  imports   |            Governance imports Data ONLY.
             +----------->+            It NEVER imports Validation.
                                       (asserted by a dedicated test)
```

- **Governance → Validation: FORBIDDEN.** Hard-asserted. This is what
  makes the recorder auditable, and it is why the record type must be
  primitives-only.
- **Validation → Governance: ALLOWED**, and already exercised — gates
  call `verify_freeze` today under AD-043.
- **Validation → Research: FORBIDDEN.** Hence `LifecyclePhase` cannot
  live in Research if Validation must map phases to gates.
- **Research → everything below: ALLOWED.** Research is the *only*
  legal binding point for gate outcomes → decision records.

### 4.2 The architecture document contradicts itself, and the proposal did not catch it

`PLATFORM_ARCHITECTURE_V1.md` §5's table says Validation → Governance is
**✅**. The *same section*, four paragraphs later, says:

> "no domain calls into a same-layer peer (Validation and Governance,
> both Layer 1, never call each other)"

These cannot both hold. The proposal's entire freeze-bracket design
(§6.6) rests on the table's reading — *"Validation → Governance is an
allowed edge, so a reproduction path may reuse it directly"* — and
never notices that the document's own cycle-prevention argument forbids
it.

This is live, not theoretical: an auditor challenging a gate result can
cite §5's prose to argue that **every gate in the repository violates
the layering**, because both existing gates call `verify_freeze`.

**Resolution — the table governs, and an AD must say so.** Three
independent facts already resolve it in the table's favor: the linter
implements the table (`ALLOWED_DEPENDENCIES["validation"]` includes
`"governance"`); `test_allows_validation_to_import_statistics_and_governance`
asserts it; and AD-043 depends on it. The prose sentence is an
over-general gloss on the acyclicity argument — and it is *harmlessly*
wrong, since a single Validation→Governance edge with no return edge
creates no cycle. **AD-053 must record this**, per the established
convention that ADs record divergence rather than editing the two source
documents. Leaving it unrecorded is leaving a loaded weapon for the
audit the proposal says it is preparing for.

### 4.3 The runner certifies evaluation, not truth — one contradiction to fix

The proposal's framing is correct and well-argued (§6.8's two-layer
table is the strongest passage in it). But **§6.5(c) violates it.**

`PLATFORM_ARCHITECTURE_V1.md` §4.2, "Explicitly out of scope":

> "Validation never decides PASS/FAIL/INCONCLUSIVE for the *cycle* —
> that is Phase 7's Decision, owned by Research using Standard §7's
> framework. A gate reports whether *its own* criteria were met; only
> **Research** aggregates gate outcomes into a terminal decision."

§6.5(c) puts the aggregate verdict — "PASS only if every gate PASSed;
FAIL if any FAILed; otherwise AMBIGUOUS" — **inside `GateRunner`**, and
§6.7 stores it in the `GateRunRecord`. That is Validation aggregating
gate outcomes into a cycle-level verdict, which §4.2 assigns to Research
by name.

**Required correction.** The aggregation *rule* is good and should be
kept exactly as specified, including FAIL-dominates-AMBIGUOUS. Move it:

- `GateRunRecord` stores the **ordered per-gate statuses only**. No
  aggregate field.
- The aggregation rule becomes a **pure function in Research**,
  `aggregate_sequence_status(statuses) -> ...`, unit-testable against a
  truth table, called by `lifecycle.py`.
- Audit requirement 3 ("was the verdict derived, not asserted?") is
  **better** served this way: the auditor recomputes from stored
  primitives using a documented rule, rather than trusting a stored
  aggregate.

**A vocabulary mismatch nobody has addressed.** `GateStatus` is
PASS/FAIL/**AMBIGUOUS**. Standard §7's cycle determination is
PASS/FAIL/**INCONCLUSIVE**. These are different vocabularies at
different levels, and no mapping is defined anywhere. If the aggregate
is recorded as "AMBIGUOUS" while Phase 7 requires "INCONCLUSIVE," the
archive contains a determination in a vocabulary the Standard does not
recognize. **AD-049 must define the mapping explicitly** — recommended:
the sequence aggregate keeps gate vocabulary and is named
`sequence_status`, never `verdict`; the Phase 7 determination is a
separate, human-authored Standard §7 value; and no code derives the
latter from the former.

### 4.4 Three further layering and purity defects

**(a) `GateRunner` must not touch `pinned_worktree`.** §6.1 says the
runner writes no file and is "pure apart from the git reads that
`verify_freeze` already performs." §6.6(2) then proposes reusing
`core.governance.pinned_worktree` for reproduction. `pinned_worktree`
creates worktrees on disk and executes pinned code in subprocesses.
These two statements are incompatible, and the second turns a
comparison engine into a code-execution engine. The edge is *legal*;
the design is not. **Required:** `GateRunner` never imports
`pinned_worktree`. Re-running a gate under a pinned worktree is a
Research- or tools-level reproduction concern, out of Step 9 scope.

**(b) INV-11 is false as written.** *"Identical inputs produce a
byte-identical `GateRunRecord` serialization."* The record contains
freeze verification outcomes, which `verify_freeze` derives from
`git status --porcelain` on the **working tree** — not a function of the
`GateContext` at all. Same inputs, dirty tree, different record. Also
the injected timestamp varies by design. **Restate:** *given identical
`GateContext` inputs, identical freeze verification outcomes, and a
fixed clock, serialization is byte-identical.* Otherwise the invariant
fails its own test and the test gets weakened to make it pass — the
worst outcome.

**(c) Do not introduce `ReviewLevel`.** §6.2's `Gate` protocol carries
`required_review_level`, following §4.2's sketch which types it
`ReviewLevel`. **No such type exists** — it appears exactly once in the
repository, in that sketch. Meanwhile `DecisionMetadata.review_level` is
a plain `str`. Introducing a `ReviewLevel` enum in Step 9 creates a dual
vocabulary against a frozen baseline type, and puts a Standard §4
*governance* concept under Validation's ownership. **Required:** keep
`str`, matching `DecisionMetadata`. An enum with one consumer is the
abstraction AD-005/AD-040 already refuse.

### 4.5 What survives review unchanged

Endorsed as specified, no correction needed: no short-circuit (§6.5a);
atomic preflight (§6.5b); `GateStatus` stays three-valued with crashes
as envelope errors, never a fourth status (§6.5d); registry semantics
following `ProjectRegistry` with no module-level singleton (§6.4);
adapters over unchanged gate functions with an equivalence test (§6.2);
values-only `GateContext` with no callables or lazy handles (§6.3);
the pre/post freeze bracket (§6.6) **as corrected by §1.1**; and the
two-layer reproduction model (§6.8), which is the proposal's best work.

---

## 5. Issue 4 — transition rules

### 5.1 The policy

The proposal correctly identifies this as a governance decision that
must be made before code, and correctly refuses to decide it implicitly.
Here is the recommended decision.

**Governing principle: `advance_phase()` never advances a project on its
own initiative, under any status.** Every transition requires an
explicit human authorization argument. The gate status determines *what
kind* of authorization is required and *what must be disclosed* — not
whether a machine may proceed unattended. This is the minimal design
that is simultaneously H3-compatible, non-enterprise, and free of
undisclosed policy.

| Status | Blocks automatic transition? | Human override required? | Disclosure obligation |
|---|---|---|---|
| **PASS** | Yes — there is no automatic transition | Explicit authorization, Level per Standard §2 for the target phase | Normal record |
| **AMBIGUOUS** | Yes | Explicit authorization **plus** a written rationale in `decision_log.md` naming each AMBIGUOUS gate and why advancing is justified | Recorded as `authorized_with_ambiguity`; the ambiguous gate names are stored in the mechanical record |
| **FAIL** | Yes — hard block on the normal path | Explicit **override**, Level 2 minimum, plus a decision-log entry stating the failed criterion and the grounds for overriding it | Recorded as `override`, distinctly from `authorized_with_ambiguity`. An override is never silently equivalent to a pass |

**Why not auto-advance on PASS?** Because "PASS" from a runner means
only "the frozen criteria compared favorably." Standard §2 assigns each
phase transition a *reviewer independence level* — a human obligation.
A machine advancing on PASS would satisfy the comparison while skipping
the review, which is AD-038's trap in a new location.

**Why AMBIGUOUS is permitted-with-disclosure rather than blocking.**
This is the H3-compatibility requirement, and it is not a concession —
it is the historically correct behavior. H3 advanced with documented
AMBIGUOUS gates; AD-043 establishes that AMBIGUOUS means *the gate
lacked a trustworthy frozen basis to decide*, which is a **process**
gap, not evidence against the hypothesis. Blocking on AMBIGUOUS would
retroactively invalidate H3's run and would pressure future operators to
invent a threshold to clear the block — precisely what AD-043 forbids.
The control is disclosure, not prohibition.

**Why FAIL blocks harder.** FAIL means a real frozen criterion was
evaluated and not met. Advancing is legitimate only as a disclosed
override with a named accountable reviewer. Distinguishing `override`
from `authorized_with_ambiguity` in the record is what stops a future
reader from seeing "advanced" and assuming the criteria were met.

**Evidence that must exist before any advance:**

1. A `GateRunRecord` for **every** gate the target phase requires per
   `ValidationRegistry` — a missing gate is a refusal, not an AMBIGUOUS.
2. Freeze verification `VERIFIED` at both bracket ends, **with a
   non-empty covered-path set** (§1.1). The covered-path count is stored
   in the record so an auditor can see the verification was not vacuous.
3. `measurement_provenance` present, or its absence explicitly recorded
   as an audit finding (§6.8) — never silently absent.
4. The decision chain verified intact and anchored (§1.4) *before* the
   append, so a transition is never written onto a broken chain.
5. An authorization record naming the human and their declared review
   level, stored verbatim and never validated by code (Standard §4: the
   platform records the declared level; it does not adjudicate the
   independence claim).

**Two-axis note:** advancing a phase does **not** imply changing
`ProjectLifecycleState`. Entering Phase 4 (Methodology Freeze) may
coincide with `FROZEN`, but the two fields move independently and
`advance_phase()` must not silently mutate the other.

---

## 6. Deliverables

### 6.1 Architecture decision summary

| # | Decision |
|---|---|
| 1 | **AD-045 is clarified, not superseded.** `DecisionRecorder` is a new object satisfying AD-045's own pre-authorized re-opening condition. AD-045 remains in force in full |
| 2 | **Migration Plan §10 item 4 is permanently partially met**, by design. Its hand-authorship-replacement clause is rejected on AD-038/AD-045 grounds and disclosed in Step 10 |
| 3 | **`GateRunner` is built.** AD-040/AD-044's deferral condition is met on its own stated terms by Step 9 §10 item 3 |
| 4 | **`LifecyclePhase` goes to `core/shared/`**, gated on the linter first being tightened so the kernel may import no domain |
| 5 | **The aggregate verdict moves to Research.** Validation never aggregates gate outcomes into a cycle-level result (`PLATFORM_ARCHITECTURE_V1.md` §4.2) |
| 6 | **Validation → Governance is allowed**; §5's contradicting prose is recorded as superseded by its own table |
| 7 | **No transition is ever automatic.** Status determines required authorization level and disclosure, not machine permission |
| 8 | **Chain tamper-evidence is externally anchored**, and its claim is stated at its true (narrower) strength |
| 9 | **The empty-`covered_paths` vacuous-VERIFIED hole is disclosed now** and guarded in new Validation code; the baseline fix is deferred to its own increment |

### 6.2 Required ADR changes

| AD | Subject | Change vs. proposal |
|---|---|---|
| AD-047 | `GateRunner` built; AD-040/AD-044 condition met, with evidence | As proposed |
| AD-048 | `LifecyclePhase` in the shared kernel | **Add** the kernel-escape-hatch finding and make the linter tightening a precondition (§1.2) |
| AD-049 | `advance_phase()` scope and transition policy | **Expanded** — must decide the policy explicitly (§5), define the AMBIGUOUS↔INCONCLUSIVE vocabulary boundary (§4.3), and cover H4 project registration/naming (§3.1) |
| AD-050 | `DecisionRecorder` | **Reframed** from "supersedes narrowly" to **clarifies, does not supersede**; adds transcription-not-certification, closed-field-set test, honest tamper-evidence claim, and the §10-item-4 rejection (§2.3) |
| AD-051 | `GateRunRecord` additive envelope | **Amended** — no aggregate verdict field; restate INV-11 correctly (§4.4b) |
| AD-052 | Freeze-stability bracket | **Amended** — a bracket over an empty covered-path set proves nothing; non-empty is a precondition (§1.1) |
| **AD-053** | **NEW.** `PLATFORM_ARCHITECTURE_V1.md` §5's table governs over its contradicting same-section prose; Validation → Governance is a legal edge (§4.2) |
| **AD-054** | **NEW.** `Project` gains `current_phase` as a field distinct from `lifecycle_state` — a baseline-type change, hence an explicit INV-12 exception with its own record (§3.2) |
| **AD-055** | **NEW.** `ReviewLevel` is not introduced; review level stays `str`, matching `DecisionMetadata` (§4.4c) |

### 6.3 Revised Step 9 implementation plan

Unchanged from the proposal except as noted; corrections are in **bold**.

- **PR-0 (new, documentation only).** Re-issue the destroyed PR0
  deviation record; disclose the live empty-`covered_paths` behavior at
  `2c7fb2c`; close or confirm-obsolete the PR0 ruling. **Nothing else
  starts until this lands** — an open, undisclosed deviation against the
  frozen chain undercuts every provenance reference downstream.
- **PR-1a (new).** Tighten `tools/check_import_boundaries.py`: the
  shared kernel may import no `core` domain. Test first, then the rule.
- **PR-1b.** `LifecyclePhase` in `core/shared/`, transcribed from
  Standard §2, pinned by test.
- **PR-2.** `Project.current_phase` (**AD-054**) + `advance_phase()`
  implementing §5's policy + **H4 project registration**.
- **PR-3.** `Gate` protocol (**`review_level: str`**), `GateContext`
  (**rejects empty `freeze_covered_paths`**), `GateRunner`,
  `GateRunRecord` (**no aggregate field**).
- **PR-4.** `ValidationRegistry`: phase → ordered gate names.
- **PR-5.** `DecisionRecorder`: closed-field record, chain, **external
  anchoring**, verifier. **Not before PR-2.**
- **PR-6.** `core/research/lifecycle.py` — composition, **plus the
  aggregation function moved here from the runner**.
- **PR-7 (new).** Integration + adversarial tests, including the
  **truncation** attack (§1.4) which no test in the proposal covers.

### 6.4 Dependency graph

```
PR-0  PR0 deviation disclosure + ruling          [docs only, BLOCKING]
  |
PR-1a linter: kernel imports no domain           [tools/]
  |
PR-1b LifecyclePhase                             [core/shared/]
  |
  +--> PR-2  current_phase + advance_phase()     [Research]   <-- AD-045's
  |            + H4 project registration                          precondition
  |
  +--> PR-4  ValidationRegistry: phase -> gates  [Validation]
              ^
PR-3  Gate / GateContext / GateRunner            [Validation]
      / GateRunRecord (no aggregate)
  |           |
  |           +--> PR-4
  |
PR-5  DecisionRecorder (chain + anchor)          [Governance]
  |     requires PR-2 to exist first
  |
  +--> PR-6  lifecycle.py + aggregation fn       [Research]
PR-2 -+        the ONLY legal binding point
PR-3 -+
PR-4 -+
  |
PR-7  integration + adversarial tests
```

Edges honored: Validation → Governance (legal, AD-053); Governance → Data
only; Research → all; nothing → Reporting.

### 6.5 Implementation order

**No code in Phase A. No component code until Phase A and B both close.**

| Phase | Content | Exit criterion |
|---|---|---|
| **A — Architecture decisions only** | PR-0 disclosure + PR0 ruling. AD-047 … AD-055 written and accepted. §5 transition policy decided. AMBIGUOUS↔INCONCLUSIVE mapping decided. Chain-anchoring mechanism decided. H4 naming decided. | Every open question in proposal §14 **and** every finding in §1 here is closed in writing. Zero code. |
| **B — Domain lifecycle foundation** | PR-1a (linter tightening, **first**), PR-1b (`LifecyclePhase`), PR-2 (`current_phase`, `advance_phase()`, H4 registration) | Kernel escape hatch closed and tested. Phase vocabulary pinned to Standard §2. `advance_phase()` has a real caller path. Full suite green, boundaries clean. |
| **C — DecisionRecorder** | PR-5 | Chain verifies; **truncation is detectable via the anchor**; closed field set pinned by test; CRLF fixture explicit; atomic write; single-writer stated and enforced. Never before B. |
| **D — GateRunner** | PR-3, PR-4 | Adapter equivalence proven against direct calls; empty-covered-paths refused; bracket invariant enforced; no aggregate stored; `GateStatus` still three-valued. |
| **E — Integration tests** | PR-6, PR-7 | H4 traverses a transition end-to-end; aggregation truth table incl. FAIL-dominates-AMBIGUOUS; every §10 failure mode tested; adversarial tamper suite incl. truncation; baseline suite passes **unmodified**. |

**Ordering constraints that are not negotiable:** A before everything
(the PR0 disclosure is a governance obligation, not a task). PR-1a
before PR-1b (never open the escape hatch first). PR-2 before PR-5
(AD-045's condition, and AD-050 is void if violated). C before D is
preferred but not required; both before E.

---

## 7. What a hostile auditor will attack, ranked

Assume the auditor's goal is to invalidate the provenance chain. In
descending order of what actually works:

1. **"Your freeze verification proves nothing."** Cite the empty
   `covered_paths` → `VERIFIED` behavior, live at `2c7fb2c`, untested,
   unguarded, and with its remediation record destroyed and never
   restored. This is the strongest attack available and it lands on the
   *baseline*, not on Step 9. **Mitigation: §1.1, in Phase A.**
2. **"Your append-only log proves nothing about what was removed."**
   Truncate the tail; the chain still verifies. **Mitigation: §1.4
   external anchoring.**
3. **"Every gate in your repository violates your own layering."** Cite
   §5's "Validation and Governance … never call each other" against
   AD-043's gates, which call `verify_freeze`. **Mitigation: AD-053.**
4. **"Governance vouched for results it is structurally incapable of
   checking."** The recorder stores gate statuses; Governance cannot
   import Validation. **Mitigation: transcription-not-certification,
   stated in the artifact.**
5. **"Your platform recorded a Phase 7 determination in a vocabulary
   your Standard does not define."** AMBIGUOUS vs. INCONCLUSIVE.
   **Mitigation: AD-049's mapping.**
6. **"Validation decided the cycle outcome, which your own architecture
   forbids."** §6.5(c)'s aggregate inside the runner. **Mitigation:
   §4.3, move it to Research.**
7. **"Your kernel is exempt from your own boundary rules."**
   **Mitigation: PR-1a.**
8. **"You claimed an inherited tamper-evidence property that does not
   exist."** §7.3's Phase 4 "chain." **Mitigation: §1.3, rewrite the
   justification.**
9. **"You reported a success criterion as met when your own plan text
   says otherwise."** §10 item 4. **Mitigation: §1.5, disclose as
   partially met.**
10. **"Your reproducibility invariant is untestable, so you weakened the
    test."** INV-11 vs. working-tree-dependent freeze results.
    **Mitigation: §4.4b, restate it.**

**The pattern across 1, 2, 3, and 8:** each is a case of a *claim being
stronger than the mechanism behind it*. That is this proposal's
characteristic failure mode, and it is the same one that returned
Amendment v1.0 and PR0. The corrections above are almost all of the form
"make the claim match the mechanism" — none require abandoning the
design.

---

## 8. Scope discipline — unchanged from the proposal

Still out of scope, endorsed: modifications to gate functions,
`GateResult`, `GateStatus`, or `build_report`; `ExperimentOrchestrator`,
`FreezeManager`, `ArchiveVerifier`, `DatasetIntegrityChecker`,
`ReproducibilityChecker`; historical backfill; any
`experiments/validate_h4_*.py`; H4's research content.

**Added to out-of-scope:** the `freeze_verifier` empty-path fix itself
(disclosed in Phase A, guarded in new code, fixed in its own later
increment with its own ruling — putting it inside Step 9 would repeat
the exact scope violation PR0 was returned for).

**One INV-12 exception is now required and must be explicit:**
`Project` gains `current_phase` (AD-054). Everything else at or before
`phase4-final-before-h4-20260722` stays untouched, and no existing test
may be edited to accommodate anything here.
