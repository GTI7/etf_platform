# Step 9 Prerequisites — Validation Orchestration and Mechanical Decision Records

**Status: proposal. No code is introduced by this document.**

**Baseline.** Written against `phase4-final-before-h4-20260722`
(`2c7fb2c`). Every statement about existing code in this document was
verified against that tree, not against the Migration Plan's
description of it. Nothing at or before this baseline is modified by
anything proposed here.

**Scope.** The prerequisites for Migration Plan Step 9 (H4 end-to-end
validation), specifically the two components Step 9's success criterion
names but the repository does not have: `GateRunner`
(§10 item 3) and `DecisionLogger` (§10 item 4).

---

## 1. Executive summary

Step 9's MVP success criterion (`docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md`
§10) requires six things be true when H4 reaches Phase 8. Two of them
depend on components that do not exist, and the two are **not in the
same state**:

| Component | Current state | Can Step 9 build it? |
|---|---|---|
| `GateRunner` | **Deferred** pending a second calling pattern (AD-040) | **Yes** — Step 9 *is* that second pattern. The deferral condition is satisfied on its own terms. |
| `DecisionLogger` | **Closed.** "No `DecisionLogger` implementation is planned" (AD-045) | **No, not as specified.** AD-045 must be superseded by a new AD, against a narrower object, or Step 9 §10 item 4 must be recorded as unmet. |

These are the two findings that shape everything below. A third,
smaller one shapes the module boundaries: the architecture document's
own sketches for both components describe imports the repository's
import-direction linter (`tools/check_import_boundaries.py`) would
reject, so neither can be implemented as sketched.

**Recommendation.** Build `GateRunner` under a new AD that records the
AD-040 condition as met. Do **not** revive `DecisionLogger`; propose
instead a strictly narrower `DecisionRecorder` that appends a
*mechanical* record (phase, timestamp, commit, gate outcomes) to a
machine artifact **alongside** the human-authored `decision_log.md`,
never into it — which is precisely, and only, the re-opening condition
AD-045 itself left open. Both depend on a Research-domain prerequisite
(`advance_phase()`) that Step 9 must build first and that neither of
the two named components can substitute for.

---

## 2. What exists at the baseline

Verified against the tree, since the Migration Plan describes several
of these more expansively than they were built.

| Area | What is actually there | Gap vs. Step 9 |
|---|---|---|
| `core/validation/gate_result.py` | `GateStatus` (PASS/FAIL/AMBIGUOUS), `DecisionMetadata` (reviewer, review_level, decided_at — all `str`), `GateResult` (gate_name, status, summary, evidence_refs, decision) | No run envelope; a `GateResult` does not record what inputs produced it |
| `core/validation/gates/` | Two functions: `evaluate_signal_independence_gate`, `evaluate_economic_rationale_gate`. Keyword-only, **heterogeneous** signatures | Nothing dispatchable by name; no `Gate` protocol |
| `core/governance/freeze_verifier.py` | `verify_freeze(commit_ref, covered_paths)` → 3-state `VerificationResult` | Consulted per-gate; no sequence-level stability guarantee |
| `core/governance/` Phase 4 chain | `reproduction_record`, `reproduction_runner`, `pinned_worktree`, `network_guard`, `reconstruction_loader`, `canonical_jsonl`, `identity_verification`, `dataset_manifest` | Reproduces *measurements*; nothing reproduces *verdicts* |
| `core/research/project_registry.py` | `register_project`, `get_project`, `list_projects`. Docstring: lifecycle transitions "deferred, none stubbed here" | **No `advance_phase()`** — verified, zero definitions in `core/` |
| `core/research/project.py` | `ProjectLifecycleState` = ACTIVE/FROZEN/ARCHIVED | This is a *storage* state, **not** the 8-phase research lifecycle. No `LifecyclePhase` exists |
| `core/reporting/report_builder.py` | `build_report(GateResult) -> ReportModel`, pure, no I/O (AD-046) | Consumes one `GateResult`; no concept of a sequence |
| `core/shared/clock.py` | `Clock` protocol, `SystemClock`, `FixedClock` | Available for injection; **currently unused by Validation** |

Two consequences worth stating plainly:

1. **`ProjectLifecycleState` is not `LifecyclePhase`.** The registry's
   three storage states (ACTIVE/FROZEN/ARCHIVED) are orthogonal to the
   Standard's research phases (Hypothesis … Archive). Step 9 needs the
   latter and it does not exist anywhere. Overloading the former would
   be a semantic collapse of exactly the kind `project.py`'s own
   docstring warns against for `lifecycle_state`/`research_outcome`.
2. **`DecisionMetadata.decided_at` is a bare `str`.** There is no
   clock injection anywhere in Validation today, and no format
   constraint on that field. Any reproducibility claim about gate runs
   has to close that hole (§9, INV-7).

---

## 3. Blocking governance findings

### 3.1 Finding A — `DecisionLogger` is closed, not deferred (AD-045)

AD-045 is not a "not yet" record. It is a terminal one:

> "No `DecisionLogger` implementation is planned. `core/governance/` is
> not expanded by this AD."

Its reasoning is not stale, and Step 9 does not invalidate it:

- **AD-038's rationale still holds.** Mechanically generating a
  decision-log entry "would satisfy 'an entry exists' while omitting
  the actual content the template requires — 'which candidate was
  ranked where and why,' 'known limitations' — fields that are, and can
  only be, human judgment." Step 9 does not change that. H4's decision
  log still needs authored narrative.
- **The consumer-less-abstraction objection is now void, but only
  partly.** AD-045's second argument was that `DecisionLogger.log()`
  had no caller because `advance_phase()` does not exist. Step 9 can
  supply `advance_phase()` — but only if Step 9 *builds* it, which is a
  Research-domain prerequisite neither named component covers (§4).

AD-045 states its own re-opening condition exactly:

> "If a future concrete need re-opens automated decision logging — for
> instance, once `advance_phase()` exists and a real caller wants a
> *mechanical* entry (phase, timestamp, commit hash) **alongside, not
> instead of**, the human-authored narrative — that is a new decision to
> make at that time, against that concrete need."

**Proposed resolution.** Step 9 meets that condition literally, and
should be scoped to it literally. The component built is **not**
`DecisionLogger` as sketched (which replaces hand-authorship, writes
`DecisionLogEntry` objects containing judgment fields, and owns
`decision_log.md`). It is a narrower `DecisionRecorder` (§7) that:

- appends **only** mechanically-derivable facts;
- writes to a **separate machine artifact**, never to `decision_log.md`;
- is **additive** to the human log, which remains canonical for judgment.

This must land as a new AD superseding AD-045's scope, not as a silent
resumption. If that AD is not accepted, Step 9 §10 item 4 is
**partially unmet** and Step 10's retrospective must say so — the
Migration Plan §10 explicitly anticipates this outcome and forbids
rounding it up.

### 3.2 Finding B — `GateRunner`'s deferral condition is satisfied

AD-040 deferred the runner because "today there are exactly two gates
and one caller shape (a script invoking a function directly)."
AD-044 named the exact trigger for `GateContext`:

> "When a second calling pattern (a `GateRunner` dispatching by name,
> for instance) actually needs to pass the same bundle of frozen inputs
> to gates it does not know the concrete signature of, `GateContext` is
> the natural type to introduce then — not before."

Step 9 §10 item 3 requires gates run "through `core/validation/`'s
`GateRunner` against a registered `Gate`, **not** a bespoke
`experiments/validate_h4_*.py` script." That is the second calling
pattern, stated as a hard acceptance criterion. Building `GateRunner`
now is consistent with AD-040/AD-044, not a violation of them. A new AD
should record that the condition was met and by what.

### 3.3 Finding C — both sketches violate the import-direction table

`tools/check_import_boundaries.py` enforces the Section 5 dependency
table, and `tests/test_import_boundaries.py` asserts the real tree is
clean. Two sketches in `PLATFORM_ARCHITECTURE_V1.md` cannot be
implemented as written:

| Sketch | Violation | Consequence for Step 9 |
|---|---|---|
| `ValidationRegistry.gates_for_phase(phase: LifecyclePhase)` (§4.2) | `LifecyclePhase` is a Research concept; **Validation must never import Research** (asserted in `core/validation/__init__.py` and by the linter) | Validation cannot own or import lifecycle vocabulary. See §5.2 |
| `DecisionLogger.log(project_id, entry)` where an entry cites gate outcomes (§4.4) | **Governance must never import Validation** — `tests/test_import_boundaries.py::test_detects_forbidden_governance_to_validation_import` asserts this exact edge | A decision record type in Governance **cannot** reference `GateResult`. See §5.3 |

Neither is a defect in the linter. Both are the architecture document's
own layering being stricter than its illustrative sketches. Per the
established convention (AD-033, AD-036, AD-040, AD-044), the ADs record
the divergence; the two documents are left as written.

---

## 4. Prerequisite dependency graph

Step 9 has a prerequisite the request did not name, and it is on the
critical path for both named components.

```
PR-1  LifecyclePhase vocabulary + ownership          (shared kernel)
        |
        +--> PR-2  ProjectRegistry.advance_phase()   (Research)
        |            [AD-045's re-opening precondition]
        |
        +--> PR-4  ValidationRegistry: phase -> gates (Validation)

PR-3  Gate protocol + GateContext + GateRunner       (Validation)
        |
        +--> PR-4

PR-5  DecisionRecorder: append-only chained store    (Governance)
        |
PR-2 --+--> PR-6  Lifecycle composition              (Research)
PR-3 --+          [the ONLY layer allowed to bind
PR-5 --+           gate outcomes to decision records]
```

**Ordering constraint.** PR-5 must not be built before PR-2. Building a
recorder whose only designed trigger does not exist would reproduce
exactly the consumer-less-abstraction pattern AD-045 refused, and would
forfeit the re-opening condition this proposal relies on.

**PR-6 is load-bearing, not glue.** Because Governance cannot import
Validation (Finding C), nothing in Governance can turn a `GateResult`
into a decision record. Research is the only domain permitted to depend
on both. If PR-6 is skipped and the binding is pushed into Governance
"for convenience," the import linter fails and the architecture is
broken. This is a structural fact, not a stylistic preference.

---

## 5. Module boundaries

### 5.1 Ownership

| Concern | Owner | Explicitly not |
|---|---|---|
| Gate identity, dispatch, sequencing | Validation | Research (which *requests* a sequence, never runs one) |
| Statistic computation | Statistics | Validation (AD-041, unchanged) |
| Freeze truth | Governance | Validation (which *consults*, never certifies) |
| Phase→gate mapping | Validation | Research (owns *which phase a project is in*, not what a phase requires) |
| Lifecycle phase vocabulary | Shared kernel (proposed, §5.2) | Validation, Governance |
| Mechanical decision record persistence | Governance | Validation, Research |
| Judgment narrative (`decision_log.md`) | **Human author** | All code (AD-038, AD-045) |
| Binding gate outcomes → decision records | Research (PR-6) | Governance (forbidden edge), Validation (forbidden edge) |

### 5.2 Where `LifecyclePhase` lives

Three options, and the recommendation:

| Option | Verdict |
|---|---|
| Define in `core/research/`, import from Validation | **Rejected** — forbidden edge, linter fails |
| Validation keys registry by opaque `str` | Workable, loses type safety, invites typo-driven silent mismatch between a Research phase name and a registry key |
| **Define `LifecyclePhase` in `core/shared/`** | **Recommended** |

`core/shared` is already the exempt cross-cutting kernel (`ProjectId`
lives there, which is why Governance may accept a `ProjectId` without
importing Research). The 8-phase research lifecycle is genuinely shared
vocabulary: Research advances through it, Validation maps gates to it,
Governance records transitions in it. It is a closed enum of names from
`RESEARCH_GOVERNANCE_STANDARD.md` §2 with no behavior and no
dependencies — the same profile as `ProjectId`.

**Caveat to settle before building:** the Standard's phase list must be
transcribed exactly, from the Standard, at freeze time. An invented or
approximated phase vocabulary hardcoded into the kernel would be a
governance defect of the kind this platform's retrospective catalogs.

### 5.3 Why `DecisionRecorder` cannot see a `GateResult`

Governance → Validation is a forbidden edge with a dedicated regression
test. Therefore the record type Governance persists must be expressed
in **primitives and kernel types only**: strings, a `ProjectId`, a
`LifecyclePhase`, hashes. Research (PR-6) reads a `GateResult`,
projects it down to those primitives, and hands the result to
Governance.

This is not a workaround. It is the same property that makes Governance
auditable: §4.4 states Governance "treats their outputs as opaque
artifacts (files, JSON records, commit hashes) to be independently
re-checked, exactly as an external auditor would." A Governance module
that imported Validation's result type would be coupled to the thing it
certifies.

---

## 6. `GateRunner` — proposed design

### 6.1 Responsibilities

**In scope:**

1. Hold an explicit registry of named gates (no auto-discovery).
2. Dispatch a gate by name against a `GateContext`.
3. Run an ordered sequence of gates and return an ordered result set.
4. Bracket the sequence with freeze verification so a sequence cannot
   straddle a freeze change (§6.5).
5. Emit a run envelope binding results to the inputs that produced them.

**Out of scope, permanently:**

- Computing any statistic (AD-041 — the runner does not weaken this;
  it carries measurements, it does not produce them).
- Deciding what a phase requires (that is `ValidationRegistry`).
- Deciding whether a project may advance (that is Research).
- Writing any file. The runner is pure apart from the git reads that
  `verify_freeze` already performs.

### 6.2 The `Gate` protocol and adapter strategy

The two existing gate functions have deliberately different signatures
(`measured_overlap` vs. `statistic_name` + `measured_value`). A generic
runner needs uniformity. **The existing functions are not modified** —
they are baseline code, they are directly tested, and Step 8's
Reporting contract depends on their output shape.

Proposed: a thin `Gate` protocol (`name`, `required_review_level`,
`run(context) -> GateResult`) plus one small adapter per existing gate
that unpacks the context into that gate's explicit parameters and calls
it unchanged. Adapters are additive; the underlying functions keep
their explicit-parameter contract (AD-044's rationale survives intact
for direct callers).

### 6.3 `GateContext` — data model

AD-044 permits introducing this exactly now. Its defining constraint,
inherited from §4.2: "a gate cannot reach outside what it was
explicitly given."

Proposed content:

| Field | Purpose | Constraint |
|---|---|---|
| `measurements` | Already-computed statistics, keyed by name | **Values only.** No callables, no lazy handles, no DB connection, no path to recompute. This is what keeps AD-041 structurally true rather than merely conventional |
| `frozen_criteria` | Thresholds + directions, keyed by gate/statistic | May be absent → gate yields AMBIGUOUS (AD-043), never an invented default |
| `freeze_commit_ref`, `freeze_covered_paths` | The freeze basis | Passed through to each gate unchanged |
| `evidence_refs` | Immutable evidence citations | Passed through unmodified (AD-042) |
| `decision` | `DecisionMetadata` attribution | Supplied by caller, never synthesized |
| `measurement_provenance` | Reference to the `ReproductionRecord` establishing where `measurements` came from | See §6.6 — this is the seam to the Phase 4 chain |

Frozen dataclass, `slots=True`, matching every record type in the
repository. Mappings must be immutable in effect; a mutable dict handed
to a runner is hidden state by another name.

### 6.4 Registry semantics

Follow the established `ProviderRegistry`/`ProjectRegistry` pattern
(AD-015, and `project_registry.py` verbatim): explicit dict-backed,
duplicate registration raises `ValueError`, unknown name raises
`KeyError`, no auto-discovery, no module-level singleton.

**No module-level mutable registry.** A process-global gate registry is
hidden state and would make two runs in one process non-independent.
The runner instance owns its registry; a test constructs its own.

### 6.5 Sequence semantics — the four decisions that matter

**(a) No short-circuit.** `run_sequence` runs every named gate even
after a FAIL. Stopping early destroys evidence about the gates that
never ran, and makes the evidence set depend on gate ordering. Every
gate produces a result; the aggregate verdict is computed separately.

**(b) Atomic preflight.** Every name in the sequence is resolved
*before* any gate executes. An unknown gate name at position 3 must not
produce two real results and a crash — a partial evidence set that
looks like a completed run is worse than a refusal.

**(c) Aggregate verdict is derived, not stored per-gate.** Proposed:
`PASS` only if every gate PASSed; `FAIL` if any FAILed; otherwise
`AMBIGUOUS`. **FAIL dominates AMBIGUOUS** — a real failed criterion is
not softened by an unrelated gate lacking a frozen threshold.

**(d) `GateStatus` stays three-valued and closed.** A gate that raises
an exception is **not** given a fourth status. Adding an enum member
would silently change `build_report`'s output contract (AD-046) and the
meaning of every persisted result. Instead the *envelope* records the
error (§6.7): the run failed to produce a verdict, which is
categorically different from a gate concluding one. This mirrors
`ReproductionStatus` conceptually extending `FreezeStatus` without
subclassing it.

### 6.6 Freeze stability — the bracket invariant

`verify_freeze` consults the **working tree** (`git status --porcelain`),
not only the commit. Two consequences the runner must handle:

1. **A sequence can straddle a change.** Gate 1 verifies clean; the
   operator edits a frozen file; gate 3 verifies DRIFTED. The result set
   is then internally inconsistent — half of it evaluated against a
   basis the other half rejected.

   **Proposed invariant:** the runner verifies the freeze *before* the
   first gate and *again after* the last, and records both. If the two
   disagree, or either is not `VERIFIED`, the entire run is marked
   invalidated at the envelope level. Individual `GateResult`s are
   retained (they are evidence of what happened) but the run carries no
   usable verdict. This requires **no change** to the gate functions,
   which keep their own internal verification.

2. **A gate verdict is not reproducible from a commit alone.** A dirty
   working tree changes the outcome. Reproducing a gate run therefore
   requires the pinned-worktree execution model Phase 4 already built
   (`core.governance.pinned_worktree`). Validation → Governance is an
   allowed edge, so a reproduction path may reuse it directly rather
   than reinventing one.

### 6.7 The run envelope

`GateResult` is deliberately **not modified** — Step 8's `build_report`
depends on its exact five fields, and it is baseline code. The
reproducibility requirement is met by an additive envelope
(`GateRunRecord`) recording, at minimum:

- the ordered gate names requested and the ordered results returned;
- the pre- and post-sequence freeze verification outcomes and resolved
  hashes (§6.6);
- the code commit the runner itself ran at;
- a digest of the `GateContext` inputs (measurements, criteria) so a
  replay can prove it used the same inputs;
- the `measurement_provenance` reference (§6.3);
- the injected timestamp (§9, INV-7);
- any gate execution error, as an error field — never as a status.

### 6.8 Two reproduction layers, and how they compose

This is the seam Step 9 must get right, and it is easy to miss:

| Layer | Component | Answers |
|---|---|---|
| Measurement | `reproduction_runner` (Phase 4, frozen) | "Does re-running the pinned experiment against the pinned data produce the same numbers?" |
| Verdict | `GateRunner` + `GateRunRecord` (proposed) | "Do those numbers, against the frozen criteria, produce the same PASS/FAIL?" |

**The runner certifies the comparison, never the measurement.** That is
a direct consequence of AD-041 and it is a real, disclosable limitation:
a `GateRunRecord` whose `measurement_provenance` is absent proves only
that a comparison was performed correctly on numbers of unverified
origin. Step 9 should treat a missing provenance reference as an audit
finding, not a normal case.

---

## 7. `DecisionRecorder` — proposed design

Deliberately not named `DecisionLogger`, because it is deliberately not
that component (§3.1).

### 7.1 What it records, and what it must never record

| Records (mechanical, derivable, verifiable) | Never records (judgment, human-authored) |
|---|---|
| Project id, from phase, to phase | "Which candidate was ranked where and why" |
| UTC timestamp (injected clock) | "Known limitations" |
| Code commit hash | Rationale, interpretation, narrative |
| Gate names + statuses + aggregate verdict, as primitives | Anything that would make `decision_log.md` redundant |
| Freeze commit ref and verification outcome | |
| Evidence refs (opaque strings, AD-042) | |
| Hash of the prior record (§7.3) | |

`decision_log.md` remains canonical for judgment, hand-authored, per
AD-038 and AD-045. The recorder's artifact is a **cross-referenceable
index**, not a replacement. If this distinction erodes during
implementation, AD-045's original objection re-applies in full and the
component should be abandoned rather than widened.

### 7.2 Storage format

Reuse `core.governance.canonical_jsonl` — the canonicalization rules
(UTF-8 no BOM, LF only, single trailing newline, sorted keys) already
exist, are already tested, and already back the dataset-hash pipeline.
A second serialization format for governance evidence would be a
gratuitous divergence.

Proposed location: a machine artifact under the project's archive
directory, sibling to `decision_log.md`, cross-referenced from it.

**Known constraint to resolve:** `write_canonical_jsonl` rewrites the
whole file via `path.write_bytes`. Append-only semantics need either an
append helper that preserves prior bytes exactly, or a documented
read-append-rewrite whose output is verified byte-identical in its
prefix. The latter is safer to verify and matches the existing reader's
strictness. Note also the CRLF fragility already recorded against this
module on Windows — the recorder inherits it and must be tested for it
explicitly, not assumed away.

### 7.3 Append-only enforcement — structural, not conventional

The Standard requires append-only ("a correction is a new entry, never
an edit"). Today that is convention plus review. The retrospective's
own finding — `reference_h3/decision_log.md` Entry 15 "written
retroactively" — is evidence that convention alone was insufficient,
and closing that gap was `DecisionLogger`'s entire original purpose.

**Proposed:** hash-chain the records. Each entry carries the SHA-256 of
the canonical serialization of its predecessor. Then:

- editing any historical entry breaks every subsequent link;
- deleting an entry breaks the chain at that point;
- reordering breaks it;
- a verifier can prove the chain intact without trusting the writer.

This gives the mechanical record the same tamper-evidence property the
Phase 4 dataset chain already has, and it is the one thing the
hand-authored markdown log structurally cannot provide. It is also the
strongest available argument for building this component at all.

### 7.4 Interface shape

Two operations, mirroring §4.4's sketch but with primitives only
(Finding C): append one record, and read the history back. Plus a
third the sketch omits and the design above requires: **verify the
chain**. A recorder that can write a chain but not verify it provides
tamper-evidence nobody can check.

Genesis case (empty chain, no predecessor hash) must be explicit in the
data model, not implicit in a nullable field nobody validates.

---

## 8. Lifecycle integration

`advance_phase()` (PR-2) is where all of this composes. Proposed shape
of one transition, in Research (PR-6), which is the only layer allowed
to touch all three domains:

1. Research asks `ValidationRegistry` which gates the target phase
   requires.
2. Research assembles a `GateContext` from already-computed statistics
   and the frozen criteria.
3. Research calls `GateRunner.run_sequence(...)`, receiving results and
   a `GateRunRecord`.
4. Research projects that record down to primitives and calls
   `DecisionRecorder.append(...)`.
5. Research updates the project's phase **only if** the transition
   policy permits it given the aggregate verdict.
6. The human authors the corresponding `decision_log.md` entry, citing
   the mechanical record. **Step 5 does not substitute for step 6.**

**Open policy question (§14):** must a transition be *blocked* on a
non-PASS verdict, or recorded-and-permitted? Blocking is the stronger
control; recording-and-permitting matches how this platform has
actually operated (H3 advanced with documented AMBIGUOUS gates). This
is a governance decision, not an implementation detail, and it must be
made before the code is written — deciding it implicitly inside
`advance_phase()` would be exactly the kind of undisclosed policy the
retrospective flags.

---

## 9. Governance invariants

Each is stated so it can be mechanically tested (§12).

| # | Invariant |
|---|---|
| INV-1 | A gate never computes a statistic. `core.validation` does not import `core.statistics` (AD-041) |
| INV-2 | Governance never imports Validation; Validation never imports Research. Enforced by the existing linter test |
| INV-3 | No gate executes against an unverified or drifted freeze; a sequence whose pre/post freeze verification disagree yields no usable verdict (§6.6) |
| INV-4 | `GateStatus` remains exactly three values. A gate crash is an envelope error, never a status |
| INV-5 | A missing frozen criterion yields AMBIGUOUS with the fixed rationale; no threshold is ever invented (AD-043) |
| INV-6 | `evidence_refs` pass through unmodified; nothing reads, writes, or hashes what they point to (AD-042) |
| INV-7 | No component reads the wall clock directly. Time enters via an injected `Clock`; every recorded timestamp is timezone-aware UTC |
| INV-8 | No module-level mutable registry. Two runners in one process share no state |
| INV-9 | Decision records are append-only and chain-verifiable; a mutated historical entry is detectable |
| INV-10 | No code writes to `decision_log.md` |
| INV-11 | Identical inputs produce a byte-identical `GateRunRecord` serialization |
| INV-12 | Nothing at or before `phase4-final-before-h4-20260722` is modified |

---

## 10. Failure modes

| # | Failure | Detection | Proposed handling |
|---|---|---|---|
| F-1 | Freeze drifts mid-sequence | Pre/post bracket disagree | Run invalidated; results retained as evidence, verdict withheld |
| F-2 | Gate raises an exception | Runner catches per-gate | Envelope error field; **not** coerced to FAIL or AMBIGUOUS (INV-4) |
| F-3 | Unknown gate name in sequence | Atomic preflight | Refuse before executing any gate (§6.5b) |
| F-4 | Duplicate gate registration | Registry | `ValueError`, matching `ProjectRegistry` |
| F-5 | Frozen criterion missing for a required gate | Gate itself | AMBIGUOUS, fixed rationale (AD-043) — already correct today |
| F-6 | Measurement provenance absent | Envelope validation | Recorded as an audit finding; verdict is comparison-only (§6.8) |
| F-7 | Non-deterministic ordering (dict/set iteration) | Determinism test | Explicit ordered types throughout; no set iteration in serialization |
| F-8 | Naive or local-time datetime recorded | Clock injection + validation | Reject non-tz-aware; `FixedClock` already enforces this |
| F-9 | Torn write / crash mid-append | Chain verification | Chain verify detects a truncated tail; write must be atomic (temp + replace) |
| F-10 | Concurrent writers to the chain | Undetected without care | Single-writer assumption must be **stated and enforced**, not assumed |
| F-11 | CRLF corruption on Windows | Canonical JSONL reader already rejects CR | Must be covered by an explicit test — this fragility is already known in this repo |
| F-12 | Recorder used to satisfy the human log | Review | INV-10 + explicit refusal to write judgment fields (§7.1) |
| F-13 | Phase vocabulary drifts from the Standard | Transcription test | Enum values pinned to the Standard's §2 list, tested against it |

---

## 11. Audit requirements

An external auditor, given only the archive, must be able to answer:

1. **Which gates ran, in what order, against which freeze?** →
   `GateRunRecord`, ordered, with resolved freeze hashes.
2. **Were the inputs the same ones the archive claims?** → input digest
   plus `measurement_provenance` into the Phase 4 chain.
3. **Was the verdict derived, not asserted?** → aggregate verdict
   recomputable from the stored per-gate statuses by a documented rule.
4. **Has the decision history been altered?** → chain verification
   (§7.3), independent of the writer.
5. **Who is on record, at what independence level?** → `DecisionMetadata`,
   carried through unchanged. Note the Standard's §4 constraint: no
   record may describe a Level 2 review as "independent" unqualified.
   The recorder stores the declared level verbatim; it does not
   validate the claim, and must not appear to.
6. **What could this evidence *not* prove?** → §6.8's limitation must
   be stated in the artifact itself, not only in this proposal.

---

## 12. Test strategy

Following existing conventions (pytest, `tmp_path`, no third-party
deps per AD-005, no network).

**Contract tests (per component).** Registry duplicate/unknown
behavior; sequence ordering; no-short-circuit; atomic preflight
refusal; aggregate verdict truth table including FAIL-dominates-
AMBIGUOUS; adapter equivalence — *dispatching a gate through the runner
returns exactly what calling the underlying function directly returns*
(this is the test that proves the adapters changed no behavior).

**Invariant tests (per §9).** Extend `test_import_boundaries.py` for
INV-2; a determinism test serializing the same inputs twice for INV-11;
a two-runner isolation test for INV-8; a clock-injection test asserting
no wall-clock read for INV-7; a repository-wide assertion for INV-10.

**Failure-mode tests (per §10).** Each row gets a test. F-1 needs a
fixture that mutates a covered file between gates. F-9 needs a
truncated-file fixture. F-11 needs an explicit CRLF fixture given the
known Windows fragility.

**Adversarial/tamper tests.** Mutate a historical chain entry → verify
fails. Delete an entry → verify fails. Reorder → verify fails. Re-append
a valid-looking entry with a forged predecessor hash → verify fails.

**What must not be tested into existence.** No test may assert that a
gate computes a statistic, that the recorder writes `decision_log.md`,
or that a fourth `GateStatus` exists. These are the three ways this
design degrades into the thing AD-041/AD-045/AD-046 each ruled out.

**Baseline regression.** The full existing suite must pass unchanged.
No existing test may be edited to accommodate anything proposed here —
an existing test needing modification means INV-12 was violated.

---

## 13. Architecture decisions required

None of these may be implied by code. Each needs an AD before
implementation.

| Proposed AD | Subject |
|---|---|
| AD-047 | `GateRunner` built: AD-040/AD-044's deferral condition met by Step 9 §10 item 3, and by what evidence |
| AD-048 | `LifecyclePhase` placed in the shared kernel, not Research — with the Finding C rationale |
| AD-049 | `ProjectRegistry.advance_phase()` scope; whether a non-PASS verdict blocks or is merely recorded (§8) |
| AD-050 | `DecisionRecorder` supersedes AD-045 **narrowly**: mechanical records only, separate artifact, additive to hand-authorship. Must state what AD-045 got right and still holds |
| AD-051 | `GateRunRecord` as an additive envelope; `GateResult` and `GateStatus` unchanged (protects AD-046) |
| AD-052 | Freeze-stability bracket semantics and the invalidated-run outcome (§6.6) |

---

## 14. Open questions requiring a decision before implementation

1. **Transition blocking policy** (§8). Governance decision, not
   implementation detail.
2. **Does AD-045 get superseded, or does Step 9 §10 item 4 go unmet?**
   Both are legitimate; only silence is not.
3. **Phase vocabulary source.** The Standard §2 list must be
   transcribed exactly at freeze time, not approximated (F-13).
4. **Where the machine artifact lives** relative to
   `RESEARCH_ARCHIVE_MANIFEST.md`'s expected layout, and whether
   `ArchiveVerifier` (not yet built) should later expect it.
5. **Single-writer enforcement** (F-10) — stated assumption or
   mechanical lock.
6. **`PR0` deviation ruling.** Project memory records an open PR0
   deviation-ruling blocker against the Phase 4 architecture. No trace
   of it was found in `docs/` at this baseline. It must be located and
   closed, or confirmed obsolete, before Step 9 begins — an open
   deviation ruling against the frozen chain would undercut every
   provenance reference in §6.8.

---

## 15. Explicitly not in scope

- Any modification to gate functions, `GateResult`, `GateStatus`, or
  `build_report`.
- `ExperimentOrchestrator`, `FreezeManager`, `ArchiveVerifier`,
  `DatasetIntegrityChecker`, `ReproducibilityChecker` — all still
  forward references with no Step 9 consumer.
- Backfilling historical gate reviews into `GateResult`s (AD-044).
- Any `experiments/validate_h4_*.py` script. Step 9's criterion is that
  no such script is needed; writing one is the documented fallback and
  a disclosable finding, never a shortcut.
- H4's research content. This document is infrastructure readiness
  only.
