# Phase 4 / Step 9 — Draft Architecture Decision Records

**Status: drafts. Not yet accepted. Not yet written into
`docs/ARCHITECTURE_DECISIONS.md`. No code is introduced by this
document and no existing file is modified by it.**

**Numbering.** The accepted ceiling is **AD-046** (verified:
`ARCHITECTURE_DECISIONS.md` ends at "AD-046: Reporting input boundary").
These drafts take **AD-047 … AD-050**. They replace the AD numbering
proposed in `STEP_9_VALIDATION_ORCHESTRATION_PROPOSAL.md` §13 and in
`STEP_9_ARCHITECTURE_RECONCILIATION_REVIEW.md` §6.2, neither of which
was accepted and which collide with each other.

**Adoption condition.** All four are Phase A items per
`docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md` §4.1. No Step 9 code may
be written before all four are accepted, and AD-047's disclosure
obligation (A-1) precedes even the acceptance of the other three.

---

### AD-047: Freeze verification is scope-bounded; the empty-covered-paths hole is disclosed, guarded in new code, and not fixed here

**Decision.** Three parts, and the first is not conditional on the
other two.

1. **Disclosure.** A dated governance deviation record is re-issued
   stating that `core/governance/freeze_verifier.py`'s
   `verify_freeze(commit_ref, [])` returns `FreezeStatus.VERIFIED`, that
   this behavior is live at `2c7fb2c` with no guard and no test in
   either direction, that the original remediation record
   (`docs/PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md`) was
   destroyed in the 2026-07-21 incident and exists in no reachable git
   ref, and that **every `VerificationResult` in the archive is only as
   strong as the covered-path set it was called with.** This obligation
   stands whether or not Step 9 proceeds.
2. **Guard, in new code only.** `GateContext` construction rejects an
   empty `freeze_covered_paths`, and `GateRunner` refuses the run before
   any gate executes. `GateRunRecord` stores the **full covered-path
   list**, not a count. `freeze_verifier.py` is **not modified** —
   the guard lives in new Validation code, so the baseline stays
   untouched and INV-12 holds.
3. **Claim bound.** A `VERIFIED` result licenses exactly one statement:
   *these named paths were byte-identical to their content at the
   claimed commit, with no committed or uncommitted drift since.* No
   Step 9 artifact may render it as "the methodology was frozen."

**Rationale.** The mechanism is verified by reading
`freeze_verifier.py:154-170`: `errors` and `drifted` are populated only
inside `for path in paths`; an empty iterable leaves both empty and the
function falls through to `else: status = VERIFIED`. This is
load-bearing rather than cosmetic because AD-043 makes a gate render
`AMBIGUOUS` when verification is not `VERIFIED` — so a gate with **zero
freeze coverage** is free to render `PASS`, and any invariant of the
form "no gate executes against an unverified freeze" is **vacuously
satisfiable**. A pre/post freeze bracket over an empty set agrees with
itself perfectly while proving nothing.

**Why the guard is not the whole answer.** Non-emptiness is necessary
and not sufficient. A path set containing only `README.md` satisfies the
guard and verifies exactly as vacuously as the empty set. That is why
part 3 exists and why the full path list — not a count — is recorded:
adequacy of coverage is a **human review judgment**, disclosed as such,
and Step 9 does not mechanize it. Storing a count and calling the
verification non-vacuous would reproduce, inside the correction, the
claim-stronger-than-mechanism failure this AD exists to close.

**Why the baseline is not fixed here.** A guard inside `verify_freeze`
itself is the right long-term answer. It is a baseline modification, it
requires its own governance ruling, and folding it into Step 9 would
repeat the exact scope violation PR0 was returned for. It is a separate
increment with its own AD.

**Invariant restated.** *No gate executes against a freeze verification
whose covered-path set is empty, unresolved, or drifted, and no
`VERIFIED` result is admitted as evidence without its covered-path list
recorded alongside it.*

**Migration/status.** `freeze_verifier.py` is unchanged. No existing
`VerificationResult` is invalidated by this AD; they are re-scoped by
the disclosure, which states what they did and did not prove.

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
