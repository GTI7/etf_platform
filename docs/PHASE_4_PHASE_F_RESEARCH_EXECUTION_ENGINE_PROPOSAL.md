# Phase 4 / Phase F — Research Execution Engine (architecture proposal)

**Date filed:** 2026-07-24
**Repository state proposed against:** canonical `D:\Claude\etf_platform`,
`master`, HEAD `58908fe` (`phase4-phase-e-complete`), working tree clean,
749 tests passing, import boundaries clean.
**Status:** proposal. Not an ADR, not an amendment, not code.
**Review level: Level 1 — self-review**
(`RESEARCH_GOVERNANCE_STANDARD.md` §4). The word *independent* is not
used of this document.
**Amended 2026-07-24** by
`docs/PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` (the "Resolution"),
findings R-1 … R-7, and further by **R-1a** (*package boundaries are not
authority boundaries*), which **supersedes R-1's restatement of AD-063's
rule** and adds **AD-067**. Amended passages are marked **[R-n]**. The
Resolution is itself Level 1; **no independent review has been read**,
and neither document may be cited as having cleared one.

**Corrected 2026-07-24 — governance audit pass, editorial, applied after
R-1a / AD-067**, per Resolution §2 (R-1a ruling items 6–7) and §4 rows
14–17. Corrected passages are marked **[audit]**. Four corrections, all
to wording: **(1)** AD-063 enumeration (a) is restated as **module-scoped
over `core.governance.decision_recorder`'s export surface** and every
description of it as "a list of three names" is withdrawn — that surface
is **fourteen public names at HEAD `58908fe`**, and the three previously
recited were examples. **(2)** Three clarifications are stated
explicitly: package boundaries are not authority boundaries; enumerations
are exhaustive only over **declared surfaces**; authority reachability
can change through **relocation, re-export, or a new access path**.
**(3)** Four **amendment triggers** are named (§7.1). **(4)** Repository
census claims are **dated to HEAD `58908fe`**. This pass consumes no
finding number, adds **no mechanism and no runtime policy framework**,
changes **no code**, and edits **no accepted AD** — AD-047 … AD-060 are
untouched.

---

## 0. What this document is, and what it is not

**It is** an architecture and governance design for the minimal execution
layer that lets one research cycle run end-to-end through the governance
kernel completed at Phase E.

**It is not**, and explicitly does not do:

- It **does not modify any accepted ADR.** AD-047 … AD-060 are read as
  settled input. §6.3 states, AD by AD, why none needs modification.
- It **does not modify any frozen Phase C/D/E module.**
  `decision_recorder.py`, `gate_runner.py`, `gate.py`, `gate_result.py`,
  `gate_context.py`, `gate_run_record.py`, `freeze_verifier.py`,
  `lifecycle.py`, `phase_derivation.py`, `sequence_aggregation.py`,
  `validation_registry.py`, `project.py` and
  `tools/check_import_boundaries.py` are all **untouched** by every step
  in §7.
- It **does not simplify, relax, or re-derive** any existing governance
  rule. Where Phase F needs a rule that already exists, it consumes it;
  it never restates it as its own.
- It **contains no code**, and no step in §7 is authorized by this
  document — §7 is a proposed decomposition, each item of which is its
  own review and its own commit.

**The central claim this design is built to preserve**, stated once and
enforced throughout: *the system must never record a claim stronger than
the mechanism that produced the evidence* (the governing principle under
which AD-056 … AD-060 were accepted).

---

## 1. The gap Phase F closes

The kernel is complete and has **never been exercised**. That is a
statement of fact about the repository, not a criticism of Phase E:
`compose_transition()` is fully implemented and fully tested, and **no
`transition_records.jsonl` exists anywhere in the repository**.

The reason is mechanical. `compose_transition()` requires, from its
caller:

| Required input | Who produces it today |
|---|---|
| `run_record: GateRunRecord` | `GateRunner.run_sequence()` — exists |
| `context: GateContext` | **nobody** — `measurements` have no producer |
| `required_gate_names` | `ValidationRegistry` — exists, deliberately empty |
| `recorder: DecisionRecorder` | **nobody** — no module constructs one outside tests |
| `authorization`, `expected_anchor`, `recorded_at`, `commit_hash` | the human operator |

Two of those five have no producer. `GateContext.measurements` is a
values-only mapping — *"no callables, no lazy handles, no database
connection, no path to recompute"* (`gate_context.py`) — which is
precisely what makes AD-041 structurally true, and precisely what means
**something outside Validation must measure**. Nothing does.

Separately, `GateRunRecord` is documented as an **in-memory artifact
only**, with persistence *"explicitly deferred to Phase E, where Research
owns archive writes"* (`gate_run_record.py`), and A-8 R-5 fixes where it
goes *if* persisted: `research_archive/<cycle_name>/experiment_results/`,
dated filename. **Phase E did not do it.** That deferral is still open.

**Phase F is therefore not new architecture. It is the discharge of two
deferrals the accepted ADRs already wrote down**: the measurement
producer that `GateContext` was designed to receive from, and the
`GateRunRecord` persistence that AD-049/A-8 R-5 already located.

---

## 2. Architecture proposal

### 2.1 `ResearchRunner` — responsibilities

`ResearchRunner` executes **one** candidate phase transition for **one**
cycle: it obtains measurements, assembles the gate input, runs the gate
sequence, archives the raw evidence, and hands the result to the
composition boundary. It is an **orchestrator with no opinions**.

**In scope — exactly six things:**

1. Read the clock **once** and freeze that instant for the whole
   execution.
2. Ask `ValidationRegistry` which gates the **target** phase requires
   (AD-059 step 1: what a phase requires is the registry's to state).
3. Run the injected `Experiment` and receive a `MeasurementBundle`.
4. Assemble a `GateContext` from the bundle plus the operator-supplied
   frozen criteria and freeze basis, and archive the bundle.
5. Run `GateRunner.run_sequence()` and archive the resulting
   `GateRunRecord` — **before** any governance call.
6. Invoke the injected `TransitionComposer` port exactly once and return
   an `ExperimentResult`.

**Out of scope, permanently — and each is somebody else's by name:**

| Not `ResearchRunner`'s | Whose it is |
|---|---|
| Computing any statistic | the `Experiment` (AD-041 — the runner carries measurements, never produces them) |
| Deciding what a phase requires | `ValidationRegistry` |
| **Populating `ValidationRegistry` and `GateRunner`** **[R-4]** | the **human operator**, at the composition root, per cycle — a governance act (AD-066). The runner reads both registries and populates neither |
| Deciding PASS/FAIL/AMBIGUOUS for a gate | the `Gate` |
| Aggregating gate outcomes | `aggregate_sequence_status()`, via `compose_transition()` (AD-049 part 3) |
| Deciding whether a transition is legal | `advance_phase()` (AD-050 part 4) |
| Binding a `GateRunRecord` to a `DecisionRecord` | `lifecycle.compose_transition()` **only** (AD-059) |
| Writing `transition_records.jsonl` | `DecisionRecorder` **only** (A-9 R-3.1) |
| Writing `decision_log.md` | the **human**. INV-10 — no code writes it, ever |
| Supplying an authorization | the **human**. Required parameter, never defaulted (AD-050 part 4, F-10) |
| Supplying the anchor | the **human**, reading `decision_log.md` (AD-050 A5-C9) |
| Choosing a phase, or defaulting one | nobody — `from_phase` is supplied and checked against the derived phase (AD-058) |
| Retrying, repairing, or cleaning up anything | nobody. Evidence is not repaired (A-9 R-6.1) |

**Three structural refusals**, each of which is what keeps a discipline
from degrading into a convention:

- **`ResearchRunner` never imports Governance.** **[audit]** It cannot
  name **any symbol exported by `core.governance.decision_recorder`** —
  `DecisionRecorder`, `DecisionRecord` and `read_chain` are three
  examples of the fourteen that module exports at HEAD `58908fe`, not the
  extent of the rule (§2.5, AD-063 enumeration (a)). It reaches
  governance through one injected port whose only implementation lives at
  the composition root (§2.4).
- **`ResearchRunner` holds no state between calls.** `execute()` is a
  single expression of one transition attempt. There is no session, no
  cycle object, no phase field, no cursor, no cached chain. Current phase
  stays derived (AD-058); nothing in Phase F stores it.
- **`ResearchRunner` never invents a value.** Every string, threshold,
  path, hash, timestamp and reference either comes from a caller, comes
  from an artifact, or does not exist. The one string it composes is an
  archive filename, from an injected instant and a fixed template
  (§2.6).

### 2.2 Execution flow

Ten steps. Steps 1–8 are mechanical; step 9 is the only governance act;
step 10 returns.

```
 1. now      := clock.now()                       one read, frozen for the run
 2. required := registry.gates_for_phase(to_phase)   unregistered -> KeyError,
                                                     breakage, no writes  [R-5]
 3. bundle   := experiment.run(spec)                 raises   -> breakage, no writes
 4. m_art    := archive_writer.write(...bundle...)   raises   -> breakage, no writes
 5. context  := build_gate_context(bundle, request, m_art)   pure, no IO
 6. run_rec  := gate_runner.run_sequence(required, context,
                    clock=FixedClock(now), code_commit_hash=..., repo_root=...)
 7. r_art    := archive_writer.write(...run_rec...)  raises   -> breakage, NO compose
 8. (no aggregation, no status inspection, no branching on gate outcomes here)
 9. receipt  := compose(project_id, from_phase, to_phase, required,
                    run_rec, context, authorization, recorded_at, commit_hash,
                    expected_anchor)                 raises   -> refusal, captured
10. return ExperimentResult(m_art, run_rec, r_art, receipt | refusal)
```

**[R-5] A *registered-but-empty* gate list is a different case, and it
is reachable.** `ValidationRegistry.register_phase_gates(phase, [])` is
legal — no non-empty check exists. Step 2 then returns `()`, step 6 runs
zero gates, **steps 4 and 7 archive both artifacts**, and step 9 is
refused by `EmptyGateSequence` from `aggregate_sequence_status`. That is
the design working, not a hole: the refusal already exists at the correct
altitude. Phase F adds no second non-empty check at the registry, the
runner, or `build_gate_context` — a duplicated rule upstream could drift
from the one that governs.

**Step 8 is deliberately empty and is the load-bearing line of the whole
design.** `ResearchRunner` never looks at a gate's status. It does not
skip composition because a gate failed, does not short-circuit on a
crash, does not compute an aggregate to decide whether to proceed. Every
one of those decisions already has an owner inside
`compose_transition()`, and a runner that pre-empts any of them would
have created a second, undocumented decision point. The runner's only
branch on outcome is: *did the composer raise a declared refusal?*

**Why the archive writes bracket the gate run the way they do.**

- **Measurement bundle is archived before the context is built (step 4 <
  step 5)**, so the reference the context carries into the gates — and
  therefore into `GateResult.evidence_refs`, and therefore into
  `DecisionRecord.evidence_refs` — points at a file that **already
  exists**. AD-042 calls `evidence_refs` *"references to immutable
  evidence locations"*; a reference minted before the artifact exists
  would be a claim ahead of its mechanism.
- **Run record is archived before composition (step 7 < step 9)**, for
  the same reason and a stronger one: `DecisionRecord` cites the
  evidence, and a chain record citing an artifact that was never written
  is unrecoverable. Ordering it this way means the only surviving failure
  mode is an **orphan artifact with no chain record** — which is
  *correct*: `experiment_results/` is defined by Standard §5 as *"raw,
  unmodified Validation output, append-only"*, and a run whose transition
  was refused **did happen** and its evidence must be retained. The
  reverse ordering would produce a chain record citing nothing, which is
  a governance defect with no remedy.

**Consequence, stated so it is not discovered later:** a refused
transition leaves **two archived artifacts and no chain record**. That is
the designed outcome, not a leak. Orphan artifacts are never deleted,
never renumbered, never "cleaned up" (A-9 R-6.1's governing principle:
evidence is not repaired, it is disclosed).

### 2.3 Component diagram

```
                     ┌─────────────────────────────────────────────┐
   composition root  │ adapters/research/lifecycle_composer.py     │
   (outside core/)   │  · constructs DecisionRecorder(archive_root)│
                     │  · calls lifecycle.compose_transition()     │
                     │  · returns TransitionReceipt (primitives)   │
                     └───────────────────┬─────────────────────────┘
                                         │ implements
                                         ▼
 ┌───────────────────────────────────────────────────────────────────────┐
 │ core/research/execution/                                              │
 │                                                                       │
 │   ┌──────────────┐   spec    ┌────────────────┐                       │
 │   │ ResearchRunner├─────────►│  Experiment    │ (Protocol; caller-built)│
 │   │              │◄──────────┤                │                       │
 │   └──┬───┬───┬───┘  bundle   └────────────────┘                       │
 │      │   │   │                                                        │
 │      │   │   │  ┌──────────────────┐                                  │
 │      │   │   └─►│ context_assembly │ (pure)                           │
 │      │   │      └──────────────────┘                                  │
 │      │   │      ┌──────────────────┐   ┌────────────────┐             │
 │      │   └─────►│  ArchiveWriter   │──►│ canonical_jsonl│ (Governance)│
 │      │          └──────────────────┘   └────────────────┘             │
 │      │  port: TransitionComposer                                      │
 │      └──────────────────────────────────► (injected; see top)         │
 └───────────────┬───────────────────────────────────────────────────────┘
                 │ uses, unmodified
                 ▼
 ┌───────────────────────────┐        ┌────────────────────────────────┐
 │ core/validation/          │        │ core/research/lifecycle.py     │
 │  GateRunner, GateContext, │        │  compose_transition()          │
 │  GateRunRecord, Gate,     │        │  advance_phase()               │
 │  ValidationRegistry       │        └────────────┬───────────────────┘
 └───────────────────────────┘                     │ sole caller of
                                                   ▼
                                       ┌────────────────────────────┐
                                       │ core/governance/           │
                                       │  DecisionRecorder.append() │
                                       └────────────────────────────┘
```

**Read the diagram for what it forbids, not only for what it connects.**
There is **no arrow from `ResearchRunner` to `core/governance/`**, and
**no arrow from anywhere except `lifecycle.py` into
`DecisionRecorder.append()`**. Those two absences are the design.

### 2.4 Ownership boundaries

| Concern | Sole owner | Enforced by |
|---|---|---|
| Producing measurements | the caller's `Experiment` | `GateContext` is values-only; the runner has no measurement code path |
| Supplying frozen criteria | the operator, via `TransitionRequest` | `Experiment` cannot return a criterion — `MeasurementBundle`'s field set is closed (§3.3) |
| Gate dispatch and the freeze bracket | `GateRunner` (unmodified) | used as-is; Phase F calls `run_sequence` |
| **Registering phase→gate names, and name→`Gate` instances** **[R-4]** | the **human operator** (AD-066) | **nothing.** No mechanism checks the two registries agree; a disagreement surfaces as `run_sequence`'s preflight `KeyError` — breakage, before any gate runs. Disclosed as unenforced |
| Aggregation | `aggregate_sequence_status()` via `compose_transition()` | `ExperimentResult` carries **no aggregate field** (§3.6) |
| Legality + authorization | `advance_phase()` | reached only through `compose_transition()` |
| Binding run record → decision record | `lifecycle.compose_transition()` | AD-059; and §2.5's per-module import rule |
| Writing `transition_records.jsonl` | `DecisionRecorder` | A-9 R-3.1; `ArchiveWriter` cannot name that filename (§3.5) |
| Writing `experiment_results/*` | `ArchiveWriter` | new; §6.1 AD-062 |
| Writing `archive_manifest.json` | `tools/archive_manifest.py` | pre-existing; `ArchiveWriter` refuses that filename |
| Writing `decision_log.md` | the **human** | INV-10; nothing in Phase F opens that path |
| Creating any directory | **nobody in Phase F** | `ArchiveWriter` refuses if `experiment_results/` is absent (§3.5) |

### 2.5 How AD-059's composition boundary survives a new orchestrator

AD-059's sentence is literal: `core/research/lifecycle.py` *"is the only
module that imports Validation and Governance together and is therefore
the only legal place a `GateRunRecord` is bound to a `DecisionRecord`."*
A naive `ResearchRunner` that imports `GateRunner` **and**
`DecisionRecorder` would make that sentence false — and the fix must not
be to amend the sentence.

**[R-1a] First, what kind of boundary this is.** AD-059 is an
**authority** boundary: it governs who may *bind* a `GateRunRecord` to a
`DecisionRecord`, and its own parenthetical grounds it in what can be
bound, not in where a module sits. The repository's *other* boundary —
the §5 domain dependency table, enforced by
`tools/check_import_boundaries.py` — is a **package** boundary: it
governs import *direction* at package granularity. **These are not the
same boundary, and a rule written in package paths cannot enforce the
authority one.** **[audit] The evidence, dated to HEAD `58908fe` and
recorded as a census at that commit, not as an invariant:** thirteen
modules besides `__init__.py` live under `core/governance/` and exactly
**one** — `decision_recorder.py` — can write `transition_records.jsonl`,
while [`canonical_jsonl.py`](core/governance/canonical_jsonl.py) imports
nothing from this repository at all (`canonical_jsonl.py:16-21`; five
module-level functions) and is already imported by the frozen Validation
module [`gate_runner.py:39`](core/validation/gate_runner.py:39).
`core/governance/__init__.py` re-exports **nothing** at that commit —
prose only, no `import`, no `__all__` — which is the condition
enumeration (a) below is written against. Package membership therefore
neither confers authority nor withholds it. **A later commit can change
every count in this paragraph**, which is what §7.2's amendment triggers
exist for.

**The rule Phase F adopts (proposed AD-063), stated by symbol:**

> **[R-1a] AD-063 governs Decision Chain authority only, in two literal
> enumerations:**
> **(a)** *No module added by Phase F names any symbol exported by
> `core.governance.decision_recorder`.* **[audit] The containment is
> module-scoped over that module's export surface** — every public name
> it exports, whatever their number, present and future — **not a list of
> selected names**. A symbol added to `decision_recorder` tomorrow is
> inside the rule the day it is added, with no edit to (a).
> **(b)** *The only `core.governance` module a Phase F module may import
> is `core.governance.canonical_jsonl`.* `archive_writer.py` does, and
> that import is **not** an authority crossing.
>
> **[audit] The surface, dated.** At HEAD `58908fe` `decision_recorder`
> declares **no `__all__`**, so its export surface is its public
> module-level names — **fourteen**: `TRANSITION_RECORDS_FILENAME`,
> `ARCHIVE_MANIFEST_FILENAME`, `MissingArchiveManifestError`,
> `ProjectIdentityMismatchError`, `ChainInvalidError`,
> `ChainPrefixMismatchError`, `AuthorizationRecord`, `GateOutcome`,
> `DecisionRecord`, `hash_record`, `read_chain`, `verify_chain_intact`,
> `verify_chain_anchored`, `DecisionRecorder`. That recital is
> **illustrative of the surface and dated to that commit**; the rule
> binds to the module, never to the recital, and **must not be worded as
> "three names" or as any other count**.
>
> `core/research/lifecycle.py` remains the sole module in `core/` that
> names both a Validation type and a `decision_recorder` symbol, and the
> sole place the binding occurs. AD-063 makes **no claim** about the
> other **eleven** modules under `core/governance/` **(count at HEAD
> `58908fe`)**; enumeration (b)'s allow-list of one keeps them out of
> Phase F without AD-063 having to govern them, however many they are.
>
> **[audit] What the enumerations are exhaustive over.** (a) is
> exhaustive over `decision_recorder`'s export surface; (b) over
> `core.governance`'s **module** surface as reached by direct module-path
> import. **Neither is exhaustive over *authority*.** Anything holding
> Decision Chain authority without appearing on one of those two declared
> surfaces is outside both enumerations and outside what F-9's AST test
> can see, and the test passing says nothing about it. **Authority
> reachability can change without either enumeration changing** — through
> **relocation** of a chain-authority symbol out of `decision_recorder`,
> **re-export** of one under another path, or a **new access path** to
> `transition_records.jsonl`. Each leaves (a) and (b) textually correct
> and materially defeated. §7.2's four amendment triggers name the
> occasions on which they must be re-derived; AD-067 is the disclosure.

> **[R-1a] Why not the package-path wording.** The Resolution's R-1
> originally restated this rule as *"no `core.governance.*` import
> statement"*. That wording is **withdrawn as unsatisfiable**: §3.5
> requires `ArchiveWriter` to call `write_canonical_jsonl`, so the rule
> forbade a module this design requires, and the only way to satisfy it
> would have been a **second canonicalization implementation** — which
> §2.6 exists to forbid. R-1's items 2, 3 and 4 stand.

> **[R-1a] No new mechanism.** F-9's single AST test remains the only
> mechanism; **only its predicate changes**, from a path prefix to the
> two enumerations. An authority registry, a `core/governance/authority.py`,
> a classifier deriving which symbols carry authority, a runtime policy
> check, and any decorator or metadata scheme are all **rejected** — each
> would be a framework standing in for **one module's export surface and
> one permitted module path** **[audit]**, and §7.1's closing prohibition
> covers exactly that. **[audit]** What is hand-maintained is the
> **choice of surface**, not a roster of names: within each surface the
> rule is exhaustive and needs no upkeep, and outside them it derives
> nothing. That cost is disclosed in AD-067.

> **[R-1] Required disclosure — what this rule does *not* do.** Phase F
> modules reach `core.governance` **transitively**, via
> `core.research.lifecycle`, which is where `Authorization` is defined
> (`lifecycle.py:87`) and which imports `decision_recorder` at module
> scope. The rule prevents a Phase F module from **naming any symbol
> `decision_recorder` exports** — `DecisionRecorder`, `DecisionRecord`
> and `read_chain` among them **[audit]**. It does **not** keep the
> Governance package out of the process, and it must never be cited as if
> it did. (Relocating `Authorization` to `core/shared/` would
> make the stronger claim true; it is rejected for Phase F because
> `lifecycle.py` is frozen — see Resolution R-1.)

It is satisfiable, not by contortion, but by putting the recorder where
it belongs — at the **composition root**, outside `core/`:

- `research_runner.py` imports Validation (`GateRunner`, `GateContext`,
  `GateRunRecord`) and research-local modules. **No Governance import.**
- `archive_writer.py` imports `core.governance.canonical_jsonl` for
  serialization. **No Validation import** — it takes plain
  `Mapping[str, Any]` payloads, which is also what makes it
  domain-independent. **[R-1a] That `core.governance` import is
  permitted, named in AD-063's enumeration (b), and carries no
  authority:** `canonical_jsonl` imports nothing from this repository,
  holds no path, reads no chain, and names no record type; Validation's
  frozen `gate_runner.py:39` already imports it. Reusing it is what keeps
  Phase F from writing a second canonicalization rule set (§2.6).
- `run_record_serialization.py` imports Validation
  (`GateRunRecord` → `dict`). **No Governance import.**
- `transition_port.py` declares the `TransitionComposer` Protocol using
  Validation types for parameters and a **research-local**
  `TransitionReceipt` for the return. **No *direct* Governance import**;
  Governance is reached transitively through `core.research.lifecycle`,
  which is where `Authorization` lives **[R-1]**. No `DecisionRecord`
  object ever crosses into the runner.
- `adapters/research/lifecycle_composer.py` is the **only**
  implementation. It imports `lifecycle`, `decision_recorder`, and
  `gate_run_record` — and it lives **outside `core/`**, because
  constructing and wiring domains together is exactly what a composition
  root is for.

  **[R-2] Required disclosure — placing it there removes it from the
  repository's only standing import enforcement.**
  `tools/check_import_boundaries.py` scans `core/` and nothing else, and
  `adapters/` currently imports neither domain. `lifecycle_composer.py`
  would be the **first module in `adapters/` to import Governance**, in a
  tree with no boundary check. The compensating mechanism is the new
  Phase F AST test **alone**, and it is weaker than the checker it
  substitutes for: it pins a **named file set**, not a tree, so a Phase F
  module added outside that set is covered by nothing. The test's scope
  is therefore fixed by name — `core/research/execution/` **and**
  `adapters/research/`. `tools/check_import_boundaries.py` is
  deliberately **not** extended to `adapters/`: doing so would silently
  change what the §5 dependency table is asserted to cover and make every
  future adapter a boundary subject with no AD saying so. That refusal is
  why the substitute is weaker, and both facts are recorded together.

**What this preserves, precisely:**

| Property | Before Phase F | After Phase F |
|---|---|---|
| Only `decision_recorder.py` writes the chain (A-9 R-3.1 / W0) | true | **unchanged** |
| The recorder is reachable only through `lifecycle.py` (A-9 R-3.2 / W1) | true | **unchanged** — `append()` still has exactly one caller |
| Exactly one **non-test** module *calls* `compose_transition()` **[R-3]** | vacuous (tests only) | **strengthened** — exactly one, named, and test-pinned. `tests/test_lifecycle_composition.py` calls it at several sites and always will; the pinning test excludes `tests/` **by a stated rule**, not by an incidental path filter |
| Only `lifecycle.py` imports both domains inside `core/` | true | **unchanged** |
| Every append carries one explicit human authorization (W2) | true | **unchanged** — `Authorization` is a required field of `TransitionRequest`, never defaulted |

**Non-claim, stated here rather than left implicit:** this does not make
concurrent writers impossible, and Phase F adds no lock (A-9 R-2 closed
that, with grounds). The lost-update case of A-9 §6.3 remains
**undetectable**, and Phase F does not narrow it. A runner that executes
transitions faster than a human could does not change the assumption's
truth — it changes how easy the assumption is to violate by accident,
and that is disclosed in §6.1 as a required clause of AD-062.

### 2.6 The one string Phase F composes

Archive filenames, from the frozen instant and a fixed template:

```
research_archive/<project_id>/experiment_results/
    measurements_<YYYYMMDD>T<HHMMSS>Z.jsonl
    gate_run_<YYYYMMDD>T<HHMMSS>Z.jsonl
```

Dated in the filename per A-8 R-5 and Standard §5's *"every file is dated
in its own content or filename"*. **One row of canonical JSONL per
file**, via `write_canonical_jsonl` — the repository's existing
canonicalization rule set, not a second one.

**Collision is a refusal, never a suffix.** If the target path exists,
`ArchiveWriter` raises. It does not append `_2`, does not overwrite, does
not increment. Two runs inside one second therefore refuse, which is the
correct answer: uniqueness that was not observed is not invented. This
mirrors `write_manifest()`'s existing `ManifestAlreadyExistsError`
precedent.

---

## 3. Public APIs

Signatures are the contract; bodies are out of scope. Every record type
below is a **frozen, slotted dataclass with a closed field set pinned by
test**, following the `DecisionRecord` / `GateRunRecord` convention — so
adding a field fails a test and forces an AD rather than a commit.

### 3.1 `Experiment` (Protocol)

```python
class Experiment(Protocol):
    name: str

    def run(self, spec: ExperimentSpec) -> MeasurementBundle: ...
```

Structural typing only, exactly like `Gate` — nothing is a base class.
An `Experiment` is **fully constructed by its caller** with whatever
database handle, repository, or configuration it needs, the same way
`EconomicRationaleGateAdapter` receives its `statistic_name` and
`repo_root`. This is what keeps `ResearchRunner` domain-independent: the
runner never learns what an ETF is.

An `Experiment` **may not** return a status, a threshold, a criterion, a
verdict, or a narrative. It returns measured values and references to
where they came from. §3.3's closed field set is the mechanism.

### 3.2 `ExperimentSpec`

```python
@dataclass(frozen=True, slots=True)
class ExperimentSpec:
    project_id: str
    as_of: datetime          # the runner's single frozen instant
    parameters: Mapping[str, str]   # opaque; the runner never reads a key
```

`parameters` is passed through untouched — the runner does not inspect,
validate, default, or merge it. It exists so an operator can pin a
run's inputs without the runner acquiring domain knowledge.

### 3.3 `MeasurementBundle`

```python
@dataclass(frozen=True, slots=True)
class MeasurementBundle:
    experiment_name: str
    measurements: Mapping[str, Decimal]   # keyed as the gates look them up
    evidence_refs: tuple[str, ...]        # opaque refs (AD-042)
    dataset_refs: tuple[str, ...]         # opaque refs; empty recorded as empty
    provenance_ref: str | None            # -> GateContext.measurement_provenance
```

**Closed field set. Five fields, and the absences are the design:**

- **No `status`, no `verdict`, no `passed`.** A measurer that could also
  conclude would collapse measurement into judgment, which is the exact
  separation AD-041 exists to hold.
- **No `threshold`, no `criterion`, no `direction`.** The yardstick comes
  from the operator's frozen methodology through `TransitionRequest`,
  never from the thing being measured. **This is the structural form of
  claim-to-mechanism discipline**: the party that produces a number
  cannot also produce the bar it is compared against.
- **No `summary`, no `notes`, no `rationale`.** AD-045's prohibition on
  narrative in mechanical records is not reopened at a new altitude.
- **`provenance_ref` may be `None`, and `None` is recorded as `None`**
  (AD-059 step 7). The runner never substitutes the archive path it just
  wrote — that would invent a reproduction reference that does not exist.
  Its absence is an audit finding, disclosed, never filled in.
- **`measurements` is values-only.** Same rule as `GateContext`: no
  callables, no handles, no paths to recompute. `Decimal`, matching what
  `GateContext.measurements` requires.

### 3.4 `MeasurementBundle` → `GateContext` (pure)

```python
def build_gate_context(
    *,
    bundle: MeasurementBundle,
    frozen_criteria: Mapping[str, FrozenCriterion],
    freeze_commit_ref: str,
    freeze_covered_paths: Sequence[str],
    decision: DecisionMetadata,
    measurement_artifact_ref: str,
) -> GateContext: ...
```

Pure: no IO, no clock, no git. Two rules, both test-pinned:

1. `evidence_refs` = `bundle.evidence_refs` **followed by exactly one
   appended ref** — `measurement_artifact_ref`, the repo-relative path of
   the artifact written at step 4. Nothing is rewritten, reordered, or
   dropped. This is the only ref the system mints, it names a file that
   already exists, and it is what makes a `DecisionRecord` cite the
   measurements it rests on.
2. `measurement_provenance` = `bundle.provenance_ref`, pass-through.

`freeze_covered_paths` flows through unchanged and hits
`GateContext.__post_init__`'s empty-set refusal (AD-047 part 2 /
AD-051's discipline) — Phase F adds no second check there and weakens
none.

### 3.5 `ArchiveWriter`

```python
class ArchiveWriter:
    def __init__(self, archive_root: Path) -> None: ...

    def write_experiment_result(
        self, *, project_id: str, filename: str, payload: Mapping[str, Any]
    ) -> ArchivedArtifact: ...
```

```python
@dataclass(frozen=True, slots=True)
class ArchivedArtifact:
    path: Path              # absolute, as written
    repo_relative_ref: str  # the string used as an evidence ref
    content_hash: str       # "sha256:<64 hex>" over the bytes written
```

**Domain-independent by construction:** it takes a `Mapping[str, Any]`
and a filename. It knows nothing about gates, measurements, phases, or
research.

**Preconditions, checked in order, each a refusal:**

0. **[R-6]** `filename` is a **single path component**: no separator, no
   `..`, no absolute path, no drive letter. Refused, **never
   normalized**. This is precondition **0**, not a prohibition listed
   elsewhere, because precondition 3's guarantee is a statement about the
   **target path's immediate parent** — and is void unless this check has
   already established that the parent is `experiment_results/`.
1. `<archive_root>/<project_id>/` exists — **never created**. Same rule,
   and the same reason, as `DecisionRecorder`: a cycle directory's
   existence is a precondition of evidence, never a consequence of it
   (A-8 C-4).
2. `archive_manifest.json` exists in it, and
   `manifest.project_id == directory name == project_id`, byte-identical
   — the same three-way identity check the recorder performs. This is a
   **deliberately duplicated guard, not duplicated state**: each writer
   must independently establish that it is writing into the cycle it
   thinks it is, and the alternative — importing the recorder's private
   check — would put a Governance import into the archive writer and
   break §2.5's rule for no benefit.
3. `experiment_results/` exists — **never created**. See the disclosed
   gap in §7 step F-9.
4. The target file does not exist (§2.6).

**Prohibitions, test-pinned:**

- It **never** writes a file named `transition_records.jsonl`,
  `decision_log.md`, or `archive_manifest.json` — checked by name, and by
  the fact that it writes only inside `experiment_results/`.
- It **never** writes outside `<archive_root>/<project_id>/experiment_results/`
  — enforced by precondition 0 above **[R-6]**.
- It **never** deletes, truncates, or modifies an existing file.
- It calls `write_canonical_jsonl` only after precondition 3 has passed,
  so that function's silent `parent.mkdir(parents=True, exist_ok=True)`
  — the specific hazard A-8 C-4 names — can never be what creates a
  directory here.

**Atomicity wording, per A-9 C-6, stated in the required words:** if the
implementation writes via temp-file-plus-`os.replace`, its docstring and
test names say **"atomic replacement"**. Never "atomic append", never
"concurrency-safe". Temp-plus-replace makes the *replacement* atomic and
the read-check-write **not** atomic, and does nothing about
last-writer-wins.

### 3.6 `ExperimentResult`

```python
@dataclass(frozen=True, slots=True)
class ExperimentResult:
    project_id: str
    experiment_name: str
    executed_at: datetime
    measurement_artifact: ArchivedArtifact
    run_record: GateRunRecord
    run_record_artifact: ArchivedArtifact
    transition: TransitionReceipt | None
    refusal: TransitionRefusal | None

    def __post_init__(self) -> None:
        # exactly one of transition / refusal, never both, never neither
        ...
```

The exactly-one invariant is `GateExecutionOutcome`'s, reused
deliberately: a transition that was recorded and a transition that was
refused are categorically different outcomes and must not be
representable simultaneously or ambiguously.

**Absences, each load-bearing:**

- **No aggregate status field.** AD-049 part 3 assigns aggregation to
  Research *at the composition point*, and `GateRunRecord` carries no
  aggregate for exactly this reason. A convenience `sequence_status` on
  `ExperimentResult` would be a second, unreviewed copy of a value the
  chain does not store either — recomputable from `run_record.outcomes`
  under a documented rule, and therefore never stored.
- **No `current_phase`.** Phase is derived from the chain (AD-058).
- **No `ok` / `success` boolean.** A caller must inspect which of the two
  outcomes it got. A boolean invites `if result.ok:` and would let a
  refusal read as a soft failure.

```python
@dataclass(frozen=True, slots=True)
class TransitionRefusal:
    kind: str      # the refusing exception's class name, verbatim
    message: str   # its message, verbatim — never paraphrased or shortened
```

Two fields. **No severity, no remediation, no retry hint, no category.**
A refusal is transcribed exactly as the governance layer stated it;
interpreting it is a human act.

```python
@dataclass(frozen=True, slots=True)
class TransitionReceipt:
    project_id: str
    sequence_number: int
    from_phase: str
    to_phase: str
    recorded_at: str
    record_hash: str    # sha256: over the appended record's canonical line
    chain_path: Path
```

**Required disclosure, carried in the type's own docstring (proposed
AD-065).** `record_hash` is the value an operator needs to write the
`(sequence_number, head_hash)` citation into `decision_log.md` for the
*next* transition's anchor. Emitting it is a **convenience
transcription**; it does **not** make the anchor machine-verified, and it
must never be read as one. Specifically:

- The machine **never** writes `decision_log.md` (INV-10). The operator
  copies the citation by hand, and the citation's evidentiary value comes
  from being committed to a separate hand-authored artifact at a known
  time — not from who computed the hash.
- The receipt is **never auto-carried** into a subsequent `execute()`
  call. `expected_anchor` is always operator-supplied, read from
  `decision_log.md`, exactly as AD-050 A5-C9 requires. `ResearchRunner`
  holds no state between calls (§2.1), so it *cannot* carry it, and this
  is why.
- Anchor lag is unchanged (A-5 R-6): the newest record is always
  unanchored. Phase F narrows that window not at all.

### 3.7 `TransitionComposer` (Protocol) and `TransitionRequest`

```python
class TransitionComposer(Protocol):
    def compose(
        self,
        *,
        project_id: str,
        from_phase: LifecyclePhase,
        to_phase: LifecyclePhase,
        required_gate_names: Sequence[str],
        run_record: GateRunRecord,
        context: GateContext,
        authorization: Authorization,
        recorded_at: str,
        commit_hash: str,
        expected_anchor: tuple[int, str] | None,
    ) -> TransitionReceipt: ...
```

A one-to-one mirror of `compose_transition()`'s signature minus
`recorder`, which the implementation owns. No parameter is optional
except `expected_anchor`, which is `None` only for genesis (AD-058) —
matching `compose_transition()` exactly, so the port cannot drift from
what it forwards to.

```python
@dataclass(frozen=True, slots=True)
class TransitionRequest:
    project_id: str
    from_phase: LifecyclePhase
    to_phase: LifecyclePhase
    experiment: Experiment
    parameters: Mapping[str, str]
    frozen_criteria: Mapping[str, FrozenCriterion]
    freeze_commit_ref: str
    freeze_covered_paths: tuple[str, ...]
    decision: DecisionMetadata
    authorization: Authorization
    code_commit_hash: str
    expected_anchor: tuple[int, str] | None
    repo_root: Path | None = None
```

**Note what is absent:** `required_gate_names`. The runner obtains it
from `ValidationRegistry.gates_for_phase(to_phase)` and **the caller
cannot override it**. A caller able to pass its own gate list could
under-declare the required set and produce a complete-looking transition
over fewer gates than the phase requires — AD-059 step 1 would never
fire, because it checks the list it is given. Removing the parameter
removes the hole.

`authorization`, `expected_anchor` and `code_commit_hash` have **no
defaults**. There is no `authorization=None` path, no "unattended" mode,
no `--yes`.

### 3.8 `ResearchRunner`

```python
class ResearchRunner:
    def __init__(
        self,
        *,
        gate_runner: GateRunner,
        registry: ValidationRegistry,
        archive_writer: ArchiveWriter,
        composer: TransitionComposer,
        clock: Clock,
    ) -> None: ...

    def execute(self, request: TransitionRequest) -> ExperimentResult: ...
```

Everything injected, nothing constructed internally, no module-level
singleton (INV-8 — two runners in one process share no state, mirroring
`GateRunner` and `ProjectRegistry`). One public method.

---

## 4. Sequence diagrams

### 4.1 Successful transition

```
Operator      ResearchRunner    Experiment  ArchiveWriter  GateRunner  Composer   lifecycle   DecisionRecorder
   │                 │              │            │             │           │          │              │
   ├─execute(req)───►│              │            │             │           │          │              │
   │                 ├─now=clock.now()           │             │           │          │              │
   │                 ├─gates_for_phase(to_phase) │             │           │          │              │
   │                 ├─run(spec)───►│            │             │           │          │              │
   │                 │◄──bundle─────┤            │             │           │          │              │
   │                 ├─write(measurements)──────►│             │           │          │              │
   │                 │◄──ArchivedArtifact────────┤             │           │          │              │
   │                 ├─build_gate_context()  (pure)            │           │          │              │
   │                 ├─run_sequence(gates, ctx)───────────────►│           │          │              │
   │                 │                          verify_freeze (pre)        │          │              │
   │                 │                          gate.run() × N             │          │              │
   │                 │                          verify_freeze (post)       │          │              │
   │                 │◄──GateRunRecord─────────────────────────┤           │          │              │
   │                 ├─write(run_record)───────►│              │           │          │              │
   │                 │◄──ArchivedArtifact───────┤              │           │          │              │
   │                 ├─compose(...)─────────────────────────────────────►  │          │              │
   │                 │                                          ├─compose_transition()►│              │
   │                 │                                          │   1 phase-chain check (AD-058)      │
   │                 │                                          │   2 context↔run-record bind (AD-060)│
   │                 │                                          │   3 gate completeness (AD-059.1)    │
   │                 │                                          │   4 crash rejection   (AD-056)      │
   │                 │                                          │   5 bracket check     (AD-059.3)    │
   │                 │                                          │   6 freeze projection (AD-059.4)    │
   │                 │                                          │   7 aggregate         (AD-059.5)    │
   │                 │                                          │   8 advance_phase()   (AD-050.4)    │
   │                 │                                          │   9 anchor verify     (A5-C9)       │
   │                 │                                          │                      ├─append()────►│
   │                 │                                          │                      │◄─DecisionRecord
   │                 │                                          │◄─DecisionRecord──────┤              │
   │                 │◄──TransitionReceipt──────────────────────┤                      │              │
   │◄─ExperimentResult                                                                 │              │
   │                                                                                   │              │
   ├─ (human) copies (sequence_number, record_hash) into decision_log.md ──────────────────────────────►
```

The last line is not decoration. It is a **required human step** with no
machine substitute, and the next transition cannot be anchored without
it.

### 4.2 Governance refusal (e.g. a crashed gate, AD-056)

```
ResearchRunner   GateRunner        ArchiveWriter    Composer      lifecycle     DecisionRecorder
      │              │                   │              │              │               │
      ├─run_sequence─►                   │              │              │               │
      │           gate 2 raises          │              │              │               │
      │           → GateExecutionOutcome(error=...)     │              │               │
      │           (no short-circuit: gate 3 still runs) │              │               │
      │◄─GateRunRecord (1 error outcome) │              │              │               │
      ├─write(run_record)───────────────►│              │              │               │
      │◄─ArchivedArtifact────────────────┤   raw output retained       │               │
      ├─compose(...)────────────────────────────────────►              │               │
      │                                                 ├─compose_transition()►        │
      │                                                 │  step 4: crash detected      │
      │                                                 │  raises CrashedGateInSequence│
      │                                                 │  ── BEFORE append ──         │
      │                                                 │                    ╳ never called
      │◄─CrashedGateInSequence──────────────────────────┤              │               │
      ├─ caught: TransitionRefusal(kind, message verbatim)             │               │
      │                                                                                │
      └─► ExperimentResult(transition=None, refusal=..., artifacts retained)
                                        chain file: BYTE-IDENTICAL
```

---

## 5. Failure handling

**The governing split:** *a refusal is data; breakage is an exception.*
A refusal means the governance kernel correctly declined to record a
transition — the run happened, its evidence is valid and archived, and
the operator must see all of it. Breakage means the machinery could not
complete an operation, in which case there is nothing trustworthy to
return.

`ResearchRunner` catches **only** the declared refusal types raised by
`compose_transition()` and its transitive callees. It catches nothing
else — no bare `except Exception`, no retry, no fallback.

| # | Failure | Writes performed | Chain | Runner behaviour |
|---|---|---|---|---|
| 0 | **Registry disagreement** **[R-4]** — a required gate name has no registered `Gate` | none | untouched | `run_sequence`'s **atomic preflight** raises `KeyError` before any gate executes. Propagates as breakage. **No partial evidence set.** Listed first because it fires earlier than the experiment. |
| 1 | **Experiment crash** | none | untouched | Propagates as `ExperimentCrashed`, `__cause__` preserved. No `MeasurementBundle` is partially constructed, no artifact written, no gate run. |
| 2 | **Gate failure** (`FAIL` status) | both artifacts | appended **iff** `override_acknowledged` | Not an error path at all. `FAIL` is a *result*. `advance_phase()` raises `UnauthorizedTransition` unless the operator acknowledged an override, in which case an `OVERRIDE`-kind record is written and must never read as `NORMAL`. |
| 3 | **Gate crash** | both artifacts | **untouched** | `GateRunner` captures it as an envelope `error`, never a fourth status (INV-4); every remaining gate still runs; `compose_transition()` raises `CrashedGateInSequence` before aggregation (AD-056). Refusal captured. |
| 4 | **Archive write failure** | possibly the measurement artifact | **untouched** | Propagates. **`compose()` is not called.** A `DecisionRecord` citing an artifact that was never written is the one outcome this ordering exists to make impossible. An orphaned measurement artifact is retained, never deleted. |
| 5 | **Governance refusal** | both artifacts | **byte-identical** | Captured as `TransitionRefusal`, verbatim. |

### 5.1 The refusal set, enumerated

Every one of these is raised **before** `DecisionRecorder.append()` and
therefore leaves the chain byte-identical:

| Raised by | Exception | Meaning |
|---|---|---|
| `lifecycle` | `PhaseChainMismatch` | supplied `from_phase` contradicts the derived phase (AD-058) |
| `lifecycle` | `ContextRunRecordMismatch` | context's freeze basis or covered paths disagree with the run record's verified evidence (AD-060) |
| `lifecycle` | `IncompleteGateSequence` | a required gate has no result (AD-059 step 1) |
| `lifecycle` | `CrashedGateInSequence` | inadmissible evidence (AD-056) |
| `lifecycle` | `BracketInvalidated` | the freeze bracket did not hold across the sequence |
| `lifecycle` | `FreezeNotVerified` | stored pre/post verifications do not project to `verified` |
| `lifecycle` | `IllegalPhaseTransition` | not a single-step advance |
| `lifecycle` | `UnauthorizedTransition` | authorization does not satisfy the aggregate status |
| `lifecycle` | `UnanchoredTransition` | non-genesis transition with no anchor (A5-C9) |
| `lifecycle` | `ChainNotAnchored` | the supplied anchor does not verify |
| `sequence_aggregation` | `EmptyGateSequence` | refused rather than a vacuous `PASS` |
| `decision_recorder` | `MissingArchiveManifestError` | cycle directory has no manifest |
| `decision_recorder` | `ProjectIdentityMismatchError` | three-way identity mismatch |
| `decision_recorder` | `ChainInvalidError` | the chain is already broken — **the cycle stops advancing** (A-9 R-6.1 item 5) |
| `decision_recorder` | `ChainPrefixMismatchError` | on-disk bytes are not canonical JSONL |

**`ChainInvalidError` deserves its own sentence.** It is not a bug and
not a transient condition. It means the chain went invalid, the cycle
cannot advance, and the disposition is a **dated human disclosure plus a
`decision_log.md` entry** — never a repair. Phase F ships **no**
renumbering utility, no dedupe, no truncate-to-last-valid, and no
`--force` (A-9 R-6.1, §12 item 3).

### 5.2 Disclosed residuals

Stated as non-claims, not as risks with mitigations, because nothing is
being built to mitigate them:

- **An interrupted `DecisionRecorder.append()` may leave a
  `transition_records.jsonl.tmp` sibling.** That file is not the chain;
  no verifier reads it; Phase F does not clean it up, because deleting
  files near a governance artifact after a failure is exactly the class
  of act this design refuses.
- **Orphan `experiment_results/` artifacts accumulate** for every refused
  transition. This is the append-only evidence discipline working as
  designed, not a leak.
- **The lost-update case (A-9 §6.3) is unchanged and remains
  undetectable.** Phase F adds no lock and no writer-identity field.
- **`ResearchRunner` cannot verify that a gate's measurement key is
  present in the bundle**, because a gate's `measurement_key` is adapter
  -private and the runner would have to reach into adapter internals to
  learn it. A missing measurement therefore surfaces as a **gate crash**,
  which AD-056 already governs correctly (transition refused, no record).
  A runner-side guard was considered and **rejected**: it would require
  either a key-naming convention the runner cannot enforce or an
  introspection hook on `Gate`, and both would be claims about gates the
  runner cannot support.

---

## 6. ADR impact

### 6.1 New ADRs required — ~~five~~ ~~six~~ **seven [R-4, R-1a]**

Accepted ceiling is **AD-060**. **AD-052 … AD-055 remain retired and are
not reused** (see AD-059's "Governance risks carried forward" note). The
next free number is **AD-061**.

| # | Title | Must record |
|---|---|---|
| **AD-061** | *Phase F: `ResearchRunner` is an orchestrator with no decision authority* | The six in-scope responsibilities and the out-of-scope table (§2.1); the ten-step flow with **step 8 empty** — the runner never inspects a gate status; the archive-before-compose ordering and **why the reverse is forbidden**; `required_gate_names` comes from `ValidationRegistry` and cannot be overridden by a caller; the refusal-is-data / breakage-is-exception split, with the closed list of caught exception types; `ExperimentResult` carries **no aggregate, no phase, no boolean** |
| **AD-062** | *Archive write authority: a second writer of a different artifact class, never a second writer of any artifact* | The honest formulation — **two writers, zero artifacts with two writers**; `ArchiveWriter` writes only inside `<archive_root>/<project_id>/experiment_results/` and can never name `transition_records.jsonl`, `decision_log.md`, or `archive_manifest.json`; A-9 R-3.1's rule is **extended by analogy, not amended** — this AD may not be cited as reopening it; the four preconditions incl. **creates no directory**; no-overwrite-ever; A-9 C-6's *"atomic replacement"* wording obligation; and the disclosure that **automating execution makes the unenforced single-writer assumption easier to violate by accident without making it any less unenforced** |
| **AD-063** **[R-1a]** | *Composition-boundary preservation: no Phase F module holds Decision Chain authority* | **The rule is about Decision Chain authority only**, stated as §2.5's two literal enumerations — *(a)* no Phase F module names a symbol exported by `core.governance.decision_recorder`, **module-scoped over that module's entire export surface** (fourteen public names at HEAD `58908fe`, no `__all__` declared; the surface is the rule, any recital of it is illustrative and dated) **[audit]**; *(b)* the only `core.governance` module a Phase F module may import is `canonical_jsonl`, which `archive_writer.py` does and which is **not** an authority crossing — pinned by a **new** test that AST-scans the Phase F packages; `tools/check_import_boundaries.py` is **not** modified. **AD-063 must not be worded as a package-path rule**, must not be cited as one, and **must not be worded as "three names" or as any other count** **[audit]**; it makes no claim about the other eleven `core/governance/` modules **(count at HEAD `58908fe`)**. **[audit] It must also record that the enumerations are exhaustive only over their declared surfaces, never over authority, and that authority reachability can change through relocation, re-export, or a new access path without either enumeration changing** — with the four amendment triggers held in AD-067. Plus: the `TransitionComposer` port and the fact that its sole implementation lives at the composition root **outside `core/`**; `TransitionReceipt` carries primitives so **no `DecisionRecord` object crosses into `ResearchRunner`**; the before/after preservation table |
| **AD-064** | *Measurement and criterion have different producers, structurally* | `MeasurementBundle`'s **closed five-field set** and each absence's reason; an `Experiment` cannot emit a status, threshold, direction, or narrative; `provenance_ref=None` is recorded as `None` and never backfilled with the archive path; an experiment crash produces **no bundle and no artifact** — no partial measurement is ever constructed |
| **AD-065** | *The anchor receipt is a convenience transcription, not a machine-verified anchor* | `TransitionReceipt.record_hash` exists to be **hand-copied** into `decision_log.md`; the machine never writes that file (INV-10); the receipt is **never auto-carried** into the next `execute()` and `ResearchRunner`'s statelessness is why it *cannot* be; anchor lag (A-5 R-6) is unchanged; AD-050 A5-C9's operator-supplied anchor is not weakened |
| **AD-066** **[R-4]** | *Gate registration is a governance act, and two-registry agreement is unenforced* | That there are **two** registries — `ValidationRegistry` (phase → gate **names**) and `GateRunner`'s own (name → `Gate` **instance**); that `ResearchRunner` reads both and populates neither; that **nothing checks they agree**, and a disagreement surfaces as `run_sequence`'s preflight `KeyError` — breakage, before any gate executes, no partial evidence; that registering a real phase→gate assignment requires a `decision_log.md` entry and a named human, with the same standing as producing the first real `transition_records.jsonl`; that Phase F ships **no** registry-consistency check, because such a check would have to name gates and Phase F is not authorized to determine what any phase requires |
| **AD-067** **[R-1a]** | *Policy authority composition: package boundaries are not authority boundaries, and the authority enumeration is hand-maintained* | That the repository holds **two different kinds of boundary** — *import-direction* boundaries, enforced by `tools/check_import_boundaries.py` over the §5 domain table at **package** granularity and mechanically derived from a path, and *authority* boundaries (who may bind, who may append, who may decide), which are held by **named symbols** and by **construction and call**, never by location; **[audit] the evidence that they differ, dated to HEAD `58908fe` and recorded as a census at that commit rather than as an invariant** — thirteen modules besides `__init__.py` under `core/governance/`, exactly **one** able to write the chain, `core/governance/__init__.py` re-exporting **nothing**, and `canonical_jsonl.py` importing nothing from this repository (five module-level functions) while the frozen `gate_runner.py:39` imports it; that authority is conferred by construction and call — `adapters/research/lifecycle_composer.py` holds chain authority because it **constructs `DecisionRecorder` and calls `compose_transition()`**, not because of where it sits, while `archive_writer.py` imports a `core.governance` module and holds **none**; **the disclosure proper** — AD-063's containment is **module-scoped over `decision_recorder`'s export surface**, exhaustive **within** that surface without maintenance and **derived from nothing outside it** **[audit]**: (b) is an allow-list of one, so a *new* `core.governance` module is excluded by default, but **neither enumeration follows authority** — **reachability can change through relocation, re-export, or a new access path** while both remain textually correct, and a chain-writing or chain-reading symbol defined **outside** `core.governance.decision_recorder`, a `decision_recorder` symbol re-exported under another path, or a `canonical_jsonl` that acquires a chain path would each leave the AST test **passing** with the boundary unprotected and nothing to say so; **[audit] the four amendment triggers**, on each of which AD-063's enumerations and this disclosure must be re-derived and amended **before F-9's test is cited as evidence of containment** — a **new module under `core/governance/`**; **relocation** of a chain-authority symbol out of `decision_recorder`; **any `__init__.py` re-export** making a `decision_recorder` symbol reachable under a different path; and **widening `canonical_jsonl`'s access** (a chain path, a path constant, chain-awareness, or any repository import) — each a **human amendment obligation** that nothing detects; that Phase F ships **no** mechanism to close the disclosure or to notice a trigger — no registry, no classifier, no runtime policy check or interceptor, no decorator or metadata scheme, no watcher, no CI check — and the surfaces are re-derived by a human reader; and that AD-067 **confers authority on nothing**, adds **no code and no runtime component**, amends no accepted AD, and must never be cited as a policy framework or as evidence that authority is mechanically governed |

**[R-1 / R-1a / R-2 / R-3 / R-5 / R-6 / R-7] The Resolution amends the
required content of AD-061, AD-062, AD-063 and AD-065**, and **R-1a
supersedes R-1's restatement of AD-063's rule**. See
`docs/PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` §5 for the added
clauses; they are required content of those ADs, not optional commentary.
AD-064 is unchanged.

AD-064 could be folded into AD-061 and AD-065 into AD-062. They are kept
separate because each carries a **claim-sensitive disclosure** that a
reader is likelier to find under its own heading than in a subsection of
a larger AD. **AD-066 is separate for the same reason [R-4]. AD-067 is
separate for a sharper one [R-1a]:** its content is the **withdrawal of
the mechanical basis** for a rule AD-063 states, and an AD cannot assert
a property in one paragraph and disclose that nothing derives it in the
next without the disclosure being read as a caveat rather than as the
finding it is.

### 6.2 Existing ADRs referenced (consumed, never modified)

AD-005 (no third-party dependency — Phase F adds none), AD-007 (injected
clock), AD-015 (explicit registry shape), AD-038 (no empty stub mistaken
for evidence), AD-041 (gates evaluate, never compute), AD-042
(`evidence_refs` are opaque references to immutable locations), AD-043
(three-way status), AD-044 (explicit parameters), AD-045 (no narrative on
a mechanical record), AD-047 … AD-060 (§6.3), plus the ruling records
A-5 (anchoring), A-8 (machine-artifact location, **R-5 in particular**),
A-9 (single-writer), and `RESEARCH_GOVERNANCE_STANDARD.md` §4 and §5.

### 6.3 Why none of AD-047 … AD-060 needs modification

| AD | Subject | Why Phase F does not touch it |
|---|---|---|
| **AD-047** | freeze verification is scope-bounded; empty-`covered_paths` disclosure | Phase F **never calls `verify_freeze`**. Freeze basis flows through `GateContext`, whose empty-set refusal fires unchanged. No new code path reaches the verifier. |
| **AD-048** | `DecisionRecorder`, mechanical records, closed field set | Phase F **adds no field**, adds no writer-identity, and **never calls `append()`**. The recorder is constructed at the composition root and passed to `compose_transition()`, which is the only caller of `append()` before and after. |
| **AD-049** | `GateRunner` built; Validation never aggregates | `GateRunner` is **used unmodified**. `GateRunRecord` gains no aggregate field, and `ExperimentResult` deliberately has none either. **A-8 R-5, recorded as "required of AD-049", already fixed where a persisted `GateRunRecord` goes** — `experiment_results/`, dated filename. Phase F **discharges that deferral at the location AD-049 already named**; it does not choose a new one. |
| **AD-050** | authorization policy, anchoring, derived phase | `Authorization` stays a required, undefaulted field; `expected_anchor` stays operator-supplied and is **never auto-carried** (AD-065); no transition is automatic at any status. |
| **AD-051** | empty `covered_paths` is `UNVERIFIABLE`, not `VERIFIED` | Untouched — no Phase F code computes a freeze result. |
| **AD-056** | a crashed outcome is inadmissible, not `AMBIGUOUS` | **Strengthened in practice, unchanged in text.** Phase F archives the crashed run record as raw output (Standard §5) and lets `compose_transition()` refuse. The runner never inspects, coerces, or filters a crashed outcome. |
| **AD-057** | closed transcription vocabulary for `GateOutcome.status` | Phase F **never transcribes a status**. Only `lifecycle.py` reads `GateResult.status.value`, and it is unmodified. `TransitionRefusal` carries an exception class name, which is not a gate status and never reaches the chain. |
| **AD-058** | genesis is a human assertion; empty chain derives `UNKNOWN` | `ResearchRunner` stores no phase, defaults no phase, and derives no phase. `from_phase` is supplied by the operator and checked against the chain by `compose_transition()`, unchanged. Statelessness (§2.1) makes a cached phase impossible. |
| **AD-059** | `lifecycle.py` is the sole composition boundary | **Preserved literally**, by AD-063's per-module authority rule plus the single-caller rule. `lifecycle.py` remains the only module that binds a `GateRunRecord` to a `DecisionRecord`, and the only one naming both a Validation type and a `core.governance.decision_recorder` symbol. Phase F **narrows** the callers of `compose_transition()` from "anyone" to exactly one named module. **[R-1a] The reading matters and is stated so no one repairs the wrong thing:** AD-059's sentence names the **binding act**, and grounds itself in what can be bound (*"since Governance cannot import Validation"*). Read instead as a *package-path* predicate, it would already be contradicted at HEAD by `gate_runner.py:39-40` — a module AD-059 itself names as frozen and untouched. The authority reading is the one under which AD-059 was accepted and is true. Phase F reads AD-059 as accepted and **amends nothing in it**. |
| **AD-060** | `VerificationResult.covered_paths` closes the covered-path binding gap | The guard is in `compose_transition()` and is unmodified. Phase F passes the operator's `freeze_covered_paths` into the same `GateContext` that `GateRunner` verifies against, which is exactly the shape the guard was written for. Phase F adds no second covered-path source. |

**The general argument, in one paragraph.** Phase F adds a layer
**strictly above** the composition boundary and **strictly outside** the
governance chain. Every governance decision — completeness, crash
rejection, bracket, freeze projection, aggregation, legality,
authorization, anchoring, append — remains inside
`compose_transition()`, reached through one call, with the same
arguments, in the same order. Phase F supplies inputs and archives
evidence; it decides nothing. An architecture that decides nothing cannot
contradict a decision record.

---

## 7. Implementation roadmap

Ten steps. Each is independently reviewable and independently
committable. **Ordering constraints are stated where they are real; the
rest may be reordered.** No step modifies an existing test (INV-12 — an
existing test needing modification means the work stops).

| # | Step | Content | Exit criterion |
|---|---|---|---|
| **F-0** | ADR acceptance | Write AD-061 … **AD-067** into `ARCHITECTURE_DECISIONS.md` per §6.1, **including the Resolution §5 clauses**. **Docs only, zero code.** | The **seven [R-1a]** ADs are accepted; AD-052 … AD-055 confirmed still retired; **AD-047 … AD-060 unedited**; no existing AD edited. **Blocked** until an independent architecture review has been read — Resolution §1.2 and §7 item 1 |
| **F-1** | Measurement types | `experiment.py` (`Experiment` Protocol, `ExperimentSpec`), `measurement_bundle.py` | Closed field sets **pinned by test**; no domain import; a bundle carrying a status/threshold is impossible by construction |
| **F-2** | Context assembly | `context_assembly.build_gate_context()` — pure | Evidence-ref append rule test-pinned (exactly one ref appended, order preserved); `provenance_ref=None` passes through as `None`; empty `freeze_covered_paths` still refused by `GateContext` |
| **F-3** | Run-record serialization | `run_record_serialization.py`: `GateRunRecord` → canonical `dict` | Round-trips; every field represented; **no aggregate can be introduced** — a field-set test mirrors `test_gate_runner.py`'s |
| **F-4** | Archive writer | `archive_writer.py`, `ArchivedArtifact` | All **five** preconditions refuse, **precondition 0 asserted to fire before any filesystem state is consulted [R-6]**; **no directory ever created**; overwrite refused; chain/`decision_log`/manifest filenames refused by name; "atomic replacement" wording pinned by test name; **its `core.governance.canonical_jsonl` import asserted as permitted under AD-063 enumeration (b), not merely tolerated [R-1a]** |
| **F-5** | Result and port types | `transition_port.py` (`TransitionComposer`, `TransitionReceipt`), `experiment_result.py` (`ExperimentResult`, `TransitionRefusal`) | Exactly-one invariant enforced in `__post_init__`; no aggregate/phase/boolean field; AD-065 disclosure present in the docstring |
| **F-6** | `ResearchRunner` — happy path | `research_runner.py`, exercised against a **fake** composer and a **fixture** experiment | One clock read, frozen and shared; **a naive (non-tz-aware) clock refuses at step 1, before `experiment.run()` is called [R-7]**; gate list comes from the registry and cannot be overridden; ordering (measure → archive → gate → archive → compose) pinned by call-order assertion; **the runner's test path names no Governance symbol and constructs no `DecisionRecorder`, and the composer is a fake [R-1]** — the stronger "imports no Governance at all" is struck as unachievable, since `Authorization` lives in `lifecycle` |
| **F-7** | Composition root | `adapters/research/lifecycle_composer.py` — the sole `TransitionComposer` implementation | Forwards every argument unchanged; converts `DecisionRecord` → `TransitionReceipt`; is the **only non-test module** in the repository calling `compose_transition()`, pinned by a test that excludes `tests/` **by a stated rule**, not an incidental path filter **[R-3]** |
| **F-8** | Failure-mode suite | All five classes in §5 plus the full refusal set in §5.1 | For every refusal: **chain file byte-identical before and after**, asserted on bytes; artifacts retained; `TransitionRefusal` message verbatim; archive-write failure proven **not** to reach `compose()` |
| **F-9** | Boundary tests + the disclosed subdirectory gap | New AST test, **scoped by name to `core/research/execution/` and `adapters/research/` [R-2]**, with the predicate **corrected from a path prefix to AD-063's two enumerations [R-1a]**: *(a)* no Phase F module names a symbol exported by `core.governance.decision_recorder` — **the predicate is module-scoped over that module's export surface, not a recital of selected names, so a symbol added to `decision_recorder` is covered without editing the test [audit]**; *(b)* the only `core.governance` module any of them imports is `canonical_jsonl`. **Enumerations only — no classifier, no registry, no runtime check [R-1a].** **[audit] The test is evidence about the two declared surfaces and nothing else**: it cannot see a chain-authority symbol that has been relocated, re-exported, or reached by a new access path, and a green result must not be cited as containment past §7.2's amendment triggers. `ArchiveWriter` never references a chain path. Separately: `reference_h4` has a manifest but **no `experiment_results/`** (it was created with `write_manifest()`, not `scaffold_project_archive()`), so `ArchiveWriter` would refuse. Closing it is an **additive** `tools/` change or a one-time human act — **not** a relaxation of F-4's precondition | Boundary tests green; the gap disclosed in writing and closed by whichever route is chosen, with the precondition intact |
| **F-10** | End-to-end traversal, **against a fixture cycle** | One complete genesis transition through the real composer, real recorder, real gates, in a temp archive root. **Both registries are populated in fixture code only, against a fixture phase [R-4]** | A real `transition_records.jsonl` is produced and verifies intact; the receipt's `record_hash` matches `hash_record` of the appended row; a second transition anchored on it succeeds; a wrong anchor refuses |

**Ordering constraints that are real:** F-0 before any code (the repo's
own discipline: decisions are recorded before they are implemented).
F-1 → F-2 (assembly needs the bundle). F-3 → F-4 is convenient, not
required. F-5 → F-6 (the runner needs its return types). F-6 → F-7 (the
runner is proven against a fake composer before a real one exists, which
is what keeps Governance out of its test path). F-7 → F-10.

### 7.1 What Phase F is **not** authorized to do

Carried forward from Resolution §4.3, which is unrelaxed:

- **No H4 research content.** No hypothesis, no gate determination, no
  research conclusion. F-10 runs against a **fixture** cycle in a temp
  archive root, with a fixture experiment returning pinned values. It
  demonstrates the **mechanism**, and must be recorded as demonstrating
  the mechanism and nothing more.
- **[R-4] Registering a phase → gate assignment for a *real* cycle is a
  governance act, not an implementation step.** It decides what evidence
  a phase requires. It has the same standing as producing the first real
  `transition_records.jsonl`: it requires a named human and a
  `decision_log.md` entry. F-10 registers gates **in test fixture code
  only**, and Phase F's completion must not be recorded as having
  determined what any phase requires.
- **No `experiments/validate_h4_*.py` script.** Writing one remains the
  documented fallback and a disclosable finding, never a shortcut.
- **Producing the repository's first *real* `transition_records.jsonl`
  for `reference_h4` is a governance act, not an implementation step.**
  It requires a real experiment, a real frozen methodology, real frozen
  criteria, a real freeze commit, a real human authorization, and a
  `decision_log.md` entry. It belongs to an H4 research increment, and
  Phase F's completion must not be recorded as having achieved it.
- **No lock, no writer-identity field, no CI check, no repair path, no
  retry** (A-9 R-7, §12).
- **No `ExperimentOrchestrator`, `FreezeManager`, `ArchiveVerifier`,
  `DatasetIntegrityChecker`, `ReproducibilityChecker`, `LifecycleEngine`,
  phase-hook system, or event bus.** No consumer exists for any of them,
  and AD-045's surviving objection — *a component whose only designed
  trigger does not exist* — applies to each.
- **[R-1a] No authority framework of any kind.** AD-067 is a
  **disclosure**, not a licence to build the thing it discloses the
  absence of. Specifically forbidden: an authority registry or
  `core/governance/authority.py`; a classifier that derives which symbols
  carry authority; a runtime policy check, guard, or interceptor; any
  decorator, marker, or metadata scheme annotating authority; and any
  generic composition engine. AD-063's rule is **two enumerations over
  two declared surfaces, checked by one AST test**, and a framework
  standing in for **one module's export surface and one permitted module
  path** **[audit]** is exactly the trade this section refuses.

### 7.2 Amendment triggers for AD-063 and AD-067 **[audit]**

Per Resolution §2 (R-1a ruling item 7). AD-067 already requires that the
declared surfaces be re-derived by a human reader; these are the
**stated occasions** on which that is owed, so it does not depend on
someone happening to notice. On **any** of the four, **AD-063's
enumerations and AD-067's disclosure must be re-derived and amended
before F-9's test is cited as evidence of containment**:

1. **A new module is added under `core/governance/`.** Enumeration (b)
   excludes it by default — the safe direction — but §2.5's and AD-067's
   census is stale from that commit, and if the module carries chain
   authority, (a) does not reach it.
2. **A chain-authority symbol is relocated** out of
   `core.governance.decision_recorder` — anything that writes, reads,
   hashes, or verifies `transition_records.jsonl`. (a) binds to the
   module, so relocation moves the symbol out of the rule while the
   rule's text is unchanged and the AST test still passes.
3. **Any `__init__.py` re-export appears** that makes a
   `decision_recorder` symbol reachable under a different path. At HEAD
   `58908fe` `core/governance/__init__.py` re-exports nothing, which is
   the condition (a) is written against.
4. **`canonical_jsonl`'s access is widened** — a chain path, a chain-path
   constant, a default path, chain-awareness, or any repository import.
   (b) permits it **because** it holds no path and imports nothing from
   this repository; widening it turns the one permitted import into an
   authority crossing while (b) still reads as correct.

These are **amendment obligations on the text of AD-063 and AD-067,
discharged by a human reader.** Phase F ships nothing that detects them
and §7.1 forbids building anything that would — no watcher, no CI check,
no registry, no runtime policy framework. Naming the occasions narrows
the gap AD-067 discloses; it does not close it, and this section must not
be cited as if it did.

---

## 8. Claim-to-mechanism ledger for Phase F

| Claim Phase F makes | Mechanism | Where it fails if unbuilt |
|---|---|---|
| The runner makes no governance decision | Step 8 is empty; the runner never reads a `GateStatus`; every decision is inside `compose_transition()` | If the runner branches on gate outcome, a second decision point exists and AD-059's boundary is decorative |
| No second writer of any artifact | `ArchiveWriter` is path- and filename-constrained and test-pinned; `append()` still has exactly one caller | If `ArchiveWriter` can name a chain path, A-9 R-3.1 is a comment |
| No duplicate state | `ExperimentResult` has no aggregate, no phase, no boolean; `TransitionReceipt` carries a citation, not a copy | If a convenience aggregate is added, the chain and the result can disagree with no reconciliation |
| Measurement cannot supply its own criterion | `MeasurementBundle`'s closed field set — there is no field to put a threshold in | If a `threshold` field appears, the measurer grades its own work |
| `lifecycle.py` remains the sole composition boundary | Per-module **authority** rule — AD-063's two enumerations — AST-pinned over a **named file set** incl. `adapters/research/`; single **non-test** caller of `compose_transition()`, test-pinned **[R-1, R-1a, R-2, R-3]** | If a Phase F module names a `decision_recorder` symbol, AD-059's premise is false and the AD needs amending — which this design exists to avoid. If the AST test's file set omits the composition root, nothing covers it at all. If the predicate were the package path instead, the test would fail on `archive_writer.py` and the only way to pass would be a second canonicalization implementation **[R-1a]** |
| Authority does not follow package membership | Nothing — this is a **statement of fact about HEAD `58908fe`**, not a mechanism, and a **census at that commit** **[audit]**: thirteen modules besides `__init__.py` under `core/governance/`, one chain writer, no `__init__.py` re-export, `canonical_jsonl` already imported by frozen Validation **[R-1a]** | It cannot fail if unbuilt, because nothing is built. What can fail is the **enumeration** that stands in for it — see AD-067 — and the census itself, which a later commit can change **[audit]** |
| Decision Chain containment covers every chain symbol the rule can see **[audit]** | Enumeration (a) is **module-scoped over `decision_recorder`'s export surface**, so a symbol added to that module is inside the rule the day it is added, with no edit to the rule or the test | If the rule were a recital of selected names, a symbol added to `decision_recorder` would sit outside it while F-9 stayed green. **The scope bounds the surface, not authority**: relocation, re-export, or a new access path moves a symbol off the surface and the test still passes — §7.2's triggers, AD-067's disclosure |
| A refused transition leaves the chain byte-identical | Every refusal raises before `append()`; F-8 asserts on **bytes**, not on record count | If asserted on record count, a same-length mutation would pass |
| Evidence exists before it is cited | Archive writes precede both context assembly and composition | If reversed, a `DecisionRecord` can cite a file that was never written |

**What Phase F does not claim:** that the single-writer assumption is
enforced (it is not — A-9 R-2); that a lost update is detectable (it is
not — A-9 §6.3); that the anchor is machine-verified (it is not —
AD-065); that an archived artifact proves the measurement was correct
(it proves only what bytes were written, and when relative to the
chain); that a green F-10 constitutes a research result (it does not —
§7.1); **that Governance is absent from the runner's process (it is not —
it is reached transitively through `lifecycle`, R-1); that the
composition root is covered by `tools/check_import_boundaries.py` (it is
not — R-2); that the two gate registries are checked for agreement (they
are not — R-4); that no Phase F module imports anything under
`core.governance` (`archive_writer.py` imports `canonical_jsonl`, by
design and permitted — R-1a); that AD-063's authority enumerations are
mechanically derived (they are scoped to two declared surfaces a human
chose, and a chain-writing symbol defined outside
`core.governance.decision_recorder` would leave the AST test passing —
AD-067); **[audit]** that the enumerations are exhaustive over authority
(they are exhaustive only over their **declared surfaces**, and authority
reachability can change through **relocation, re-export, or a new access
path** with both enumerations still textually correct); that anything
detects the four amendment triggers (§7.2 — they are human amendment
obligations, and §7.1 forbids building a detector); that any repository
census in this document holds after HEAD `58908fe` (each is a count at
that commit).**

---

## 9. Open questions for the reviewer

Three, each with a recommendation. **All three were ruled on by the
Resolution §3 (Level 1, self-review — not an independent ruling):
Q1 additive `tools/` route, as recommended; Q2 keep the receipt, with the
added requirement that AD-065 state `record_hash` is
operator-recomputable via `hash_record`, which is what makes it a
transcription rather than a dependency; Q3 ~~**six**~~ **seven** ADRs,
not five — R-4 forced AD-066 and **R-1a forced AD-067**.** The original
text stands below unchanged.

1. **`experiment_results/` for `reference_h4` (F-9).** Recommend the
   additive `tools/` route — a small `ensure_evidence_subdirectories()`
   beside the existing scaffold, which touches no `core/` module — over
   relaxing `ArchiveWriter`'s precondition. The precondition is the
   symmetry with `DecisionRecorder` that makes "creates no directory" a
   property of the whole archive layer rather than of one module.
2. **Whether `TransitionReceipt` should exist at all (AD-065).** The
   conservative alternative is to return nothing and have the operator
   compute the head hash independently. Recommend keeping the receipt
   **with** its disclosure: the operator's independence comes from
   committing the citation to a hand-authored artifact, not from
   performing sha256 by hand, and an operator who cannot obtain the hash
   easily is an operator who will anchor less often.
3. **Whether five ADRs is the right granularity (§6.1).** Recommend
   five. Folding AD-064 and AD-065 into their neighbours would bury two
   disclosures that a reader is most likely to need under their own
   heading.
