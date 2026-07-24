# Phase F — F-0 Architecture Acceptance Review

**Date:** 2026-07-24
**Reviewer role:** architecture reviewer, commissioned for Phase F's F-0
entry gate.
**Repository state reviewed against:** canonical `D:\Claude\etf_platform`,
`master`, HEAD **`befa486`**, working tree clean,
`origin/master == master` (0 ahead / 0 behind), suite **787 passed, 1
skipped, 1 xfailed**.
**Documents reviewed:**
`docs/PHASE_4_PHASE_F_RESEARCH_EXECUTION_ENGINE_PROPOSAL.md` (the
"Proposal"), `docs/PHASE_F_GATE_REVIEW.md` (the "Gate Review"),
`docs/PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md` (the "Resolution"),
`docs/ARCHITECTURE_DECISIONS.md` at HEAD.
**Finding numbering:** **R-8 … R-15**, continuing the Resolution's §2
series, per Resolution §1.2 and §7 item 1, which reserved R-8 onward for
this review.

**Production code modified by this review: none. Phase F code written:
none. Architecture decisions accepted by this review: none** —
acceptance is F-0, an act performed in
`docs/ARCHITECTURE_DECISIONS.md`, not here.

---

## 0. Decision

> # ✅ APPROVED WITH CONDITIONS

The Phase F architecture is **sound and accepted as designed**. No
structural defect was found: the layering, the composition boundary, the
authority model, the failure taxonomy, and the archive-before-compose
ordering all hold under adversarial reading and against the repository at
HEAD. Every load-bearing census in the Proposal and the Resolution was
re-derived at HEAD `befa486` and **all of them still hold** (§5).

The conditions are **eight findings (R-8 … R-15)**, of which **five must
be discharged inside F-0's own text** before AD-061 … AD-067 are written,
and **three before F-1 code lands**. None requires a new AD number; none
changes the architecture. Three of the five are corrections to claims the
Proposal makes that are **stronger than the mechanism at HEAD** — the
precise class of defect this repository's governing principle exists to
catch, and the reason a self-review pass could not close this gate.

**What this decision does and does not discharge.** It discharges the
Gate Review's **B-1 / H-1** and the Resolution's §7 item 1 *to the extent
a Level 2 review can*: Phase F is no longer resting on a Level 1
self-review. It does **not** make Phase F "independently reviewed" in the
unqualified sense, and §1 states exactly what it is instead. Read with
R-8, the F-0 blocker is **discharged**, not waived.

---

## 1. Review level — the disclosure this document is required to make

**Level 2 — AI-assisted adversarial review** (`RESEARCH_GOVERNANCE_STANDARD.md`
§4). Stated in the terms that standard requires, without softening:

- This review is **procedurally independent**: a separate pass over the
  material, with no conversational continuity to the sessions that wrote
  the Proposal, the Resolution, or the Gate Review, and with every
  load-bearing claim re-derived from the repository rather than read out
  of those documents.
- It is **not organizationally independent** under any definition
  §4 recognizes: the same model family and vendor performed the work and
  this review; there is no incentive separation, no accountable persistent
  reviewer identity, and the claim of no conversational memory is
  self-reported.
- **Level 3 review is not available on this platform** and never has been
  (§4, Level 3, "Limitations"). This review is not a substitute for one
  and must not be recorded as one.

Per §4's binding sentence — *no document may describe a Level 2 review
using the unqualified word "independent"* — **this document must never be
cited as "the independent architecture review."** It is the **Level 2
adversarial architecture review** F-0 needs, and R-8 below restates F-0's
own precondition so that the artifact F-0 requires is the artifact that
can exist.

---

## 2. The six questions, answered

### 2.1 Is Phase F architecture approved?

**Yes — approved with conditions, and not yet *accepted*.** The two are
different acts and the distinction is the whole of F-0.

- **Approved (this document).** The design is fit to be written into
  `ARCHITECTURE_DECISIONS.md`, subject to §4's conditions.
- **Accepted (F-0, not yet performed).** AD-061 … AD-067 are **reserved
  and unaccepted** at HEAD: `ARCHITECTURE_DECISIONS.md:3098-3137` records
  the reservation and states in terms that *"None of the seven is
  accepted."* The accepted ceiling in the file is **AD-069**; the
  reservation block sits between AD-060 and AD-068 and is intact. Nothing
  in the file occupies AD-061 … AD-067 (verified by grep: the only five
  occurrences are inside the reservation block itself).

The Gate Review's **NOT READY** verdict was correct on the facts it had —
its blocker was the absence of any review above Level 1, and it correctly
refused to self-certify. That blocker is the one this document addresses.
Nothing else in its assessment stood in the way then, and nothing does
now: its C-1 (commit the Proposal), C-2 (push), C-6 (`ImportError` Path A
fix **and** the AD-069 record amendment), and C-7 (`reproduction_runner`
isolation docstring) are all **discharged at HEAD** — verified at
`core/governance/reproduction_runner.py:162`
(`except (OSError, ImportError)`), the corrected module docstring at
`:1-40`, and the dated AD-069 amendment at
`ARCHITECTURE_DECISIONS.md:~3437`.

### 2.2 Are domain boundaries clear?

**Yes — clear in all three senses, with one deliberately unenforced.**

| Boundary | Clear? | Enforced by |
|---|---|---|
| `core/research/execution/` → its domain | **Yes.** `research` is mapped in `DOMAIN_OF_TOPLEVEL` (`tools/check_import_boundaries.py:113`) and `_domain_of_file` keys on the toplevel package only, so a new subpackage inherits `research` with no mapping change and no `UnmappedPackageError` | `tools/check_import_boundaries.py`, as today |
| Phase F → Governance (authority) | **Yes.** AD-063's two enumerations are literal, satisfiable, and checkable. Enumeration (b)'s single permitted module, `canonical_jsonl`, verifiably holds no authority — it imports nothing from this repository (`canonical_jsonl.py:16-21`) and is already imported by frozen Validation (`gate_runner.py:39`) | F-9's AST test, plus AD-067's disclosure of what it cannot see |
| `adapters/research/` → anything | **Defined, deliberately unenforced.** `check_repository` scans `core/` only (`:341`); `adapters/` holds `cli/` alone at HEAD and imports neither domain | F-9's named-file AST test **only**. Weaker than the checker it substitutes for, and both facts are already recorded (R-2) |

The conceptual ambiguity that mattered — *is `core/governance/`
membership an authority claim?* — was correctly resolved by R-1a and
AD-067: **it is not**, and I re-derived the evidence at HEAD (§5). The
resolution is right, it is honestly disclosed as unenforced, and the
four amendment triggers are the correct instrument for a rule that a
human maintains.

### 2.3 Are reproduction guarantees sufficient?

**No — and this is the sharpest finding of this review.** They are
sufficient for *evidence retention* and insufficient for *reproduction*,
and the Proposal does not say so.

What Phase F guarantees, and does guarantee well: every run's raw
measurement bundle and raw `GateRunRecord` are archived, in canonical
JSONL, with a content hash, dated, before anything is composed, and never
deleted, overwritten, or repaired — including for refused transitions.
That is Standard §5's append-only raw-output discipline, correctly
implemented, and it is genuinely stronger than what exists today.

What it does **not** guarantee, established from the code:

1. **The chain's reproduction field is an optional, unvalidated,
   caller-supplied string.**
   `lifecycle.py:389` sets
   `reproduction_record_ref = run_record.measurement_provenance`, which
   traces back through `GateContext.measurement_provenance` to
   `MeasurementBundle.provenance_ref` — a field §3.3 permits to be `None`
   and AD-064 requires be recorded as `None` and never backfilled.
   **Nothing refuses a transition with no reproduction ref, and nothing
   checks a non-`None` ref resolves to anything.** Phase F's default,
   fully legal, fully compliant output is a valid `DecisionRecord` with
   **no reproduction path** (R-10).
2. **Phase F ships no `ReproductionRecord` producer**, and its execution
   model is structurally disconnected from the one the repository already
   has. `reproduction_runner` reproduces a cycle by loading an experiment
   **script by relative path out of a pinned worktree**; Phase F's
   `Experiment` is a live injected object with no path, no commit pin,
   and only a caller-chosen `experiment_name: str`. Nothing binds the two
   models, and `experiment_name` must not be read as answering *what code
   measured this* (R-11).
3. **The run's own inputs are archived nowhere.** `ExperimentSpec.parameters`
   exists, per §3.2, *"so an operator can pin a run's inputs"* — and no
   step in §7 serializes it. §2.2 step 4 archives "…bundle…"; §3.5 takes
   an opaque payload; F-3 specifies run-record serialization and no step
   specifies bundle serialization at all (R-12).

None of this is a reason to reject the architecture. Phase F is
explicitly *not* the reproduction increment, and the right repair is
disclosure plus one specification gap closed — not new mechanism. But
the Proposal's §8 ledger currently claims *"Evidence exists before it is
cited"* without the companion non-claim that **the evidence need not be
sufficient to re-derive the measurement**, and AD-064's `None` clause
reads as a purity argument when its actual consequence reaches the
Decision Chain. Conditions C-3 and C-6 close this.

### 2.4 Does Phase F introduce any dependency on `core.store`?

**No — verified, not assumed, and not merely at the direct-import level.**

I computed the full transitive first-party import closure of everything
Phase F reaches at HEAD — `core.research.lifecycle`,
`core.validation.gate_runner`, `core.validation.validation_registry`,
`core.governance.canonical_jsonl`, `core.shared.clock`. **Fourteen
modules are reachable; `core.store` is in none of them.** The closure is:

```
core.governance.{canonical_jsonl, decision_recorder, freeze_verifier}
core.research.{lifecycle, phase_derivation, sequence_aggregation}
core.shared.{clock, lifecycle_phase}
core.validation.{gate, gate_context, gate_result, gate_run_record,
                 gate_runner, validation_registry}
```

Consistently, `ALLOWED_DEPENDENCIES["research"]` =
`{data, statistics, governance, validation}`
(`tools/check_import_boundaries.py:176`) — **no `store` grant, and none
needed.** Under AD-069's demand-driven rule that is the correct state.

**One route by which Phase F could acquire one, recorded so a future
author meets the rule rather than discovering it (R-14).** A *real*
`Experiment` implementation will very likely read the database. If it is
written under `core/research/`, importing `core.store.connection`
directly is a boundary violation requiring a recorded decision in the
same commit — correct and loud. But importing the **permanent shim**
`core.market_data.persistence.database` is `research → data`, which is
**already granted**, and the shim's own `data → store` edge is granted
too. The checker is a direct-import checker; a granted edge into a
permanent re-export shim reaches `store` invisibly. This is inherent to
the mechanism, not a Phase F defect, and AD-069 made the shims permanent
with its eyes open. It is worth one sentence in AD-061 so that Phase F's
"no store dependency" is recorded as **true of Phase F's own modules**
rather than as a property an `Experiment` author inherits.

### 2.5 Are there missing ADRs before implementation?

**Yes — all seven, and no eighth.**

- **AD-061 … AD-067 are reserved, drafted, resolved, and unaccepted.**
  F-0 is exactly the act of writing them. This is an **acceptance** gap,
  not a **coverage** gap — I found no architectural decision Phase F
  makes that falls outside the seven, and I agree with the Gate Review
  §4.3 on this point after checking it independently.
- **No new AD number is required.** Every finding below lands as
  *required content* inside an already-reserved AD: R-9 → AD-061;
  R-10, R-11 → AD-064; R-12 → AD-061 (+ F-1's exit criterion); R-13 →
  AD-063 and AD-067; R-14 → AD-061. Creating an eighth number for any of
  them would dilute the register for no reader benefit, which is the same
  reasoning the Gate Review applied to GR-16 and §3.3 and which I endorse.
- **R-8 is the exception in kind, not in number:** it corrects F-0's own
  *precondition wording*, and belongs in the Resolution's §7 item 1 and
  F-0's exit criterion, not inside any AD.

The granularity ruling — seven ADs, with AD-064, AD-065, AD-066 and
AD-067 kept separate because each carries a claim-sensitive disclosure —
is **correct and should not be re-litigated**. AD-067 in particular must
stay separate: an AD cannot assert a containment property in one
paragraph and withdraw its mechanical basis in the next without the
withdrawal reading as a caveat.

### 2.6 Are there hidden risks?

Eight carried forward from the Gate Review, of which I re-verified all
and **re-rated two**; plus four this review adds.

| # | Risk | Status at HEAD `befa486` | Rating |
|---|---|---|---|
| **H-1** | F-0 rests on a review that does not exist | **Discharged by this document**, at Level 2, with Level 3 disclosed unavailable — see R-8 | **CLOSED (conditionally)** |
| **H-2** | Four amendment triggers, zero detection | Unchanged and correct as designed. None has fired since `58908fe` (§5) | HIGH (standing) |
| **H-3** | No CI — every guarantee runs only when a human runs pytest | Re-verified: no `.github/`, no `.pre-commit-config.yaml`, no `Makefile` | HIGH |
| **H-4** | `reference_h4` has no `experiment_results/` | Re-verified: the directory holds `archive_manifest.json` and nothing else | MEDIUM |
| **H-5** | Two registries, no agreement check | Confirmed in code: `register_phase_gates` applies no non-empty check, `gates_for_phase` raises `KeyError` (`validation_registry.py:32,38`) | MEDIUM |
| **H-6** | `transition_records.jsonl` has never existed | Re-verified: `find` returns nothing repository-wide | MEDIUM |
| **H-7** | Both Phase F documents pinned to a stale HEAD | **Worse in degree, unchanged in kind**: `58908fe` is now 14 commits back. All load-bearing censuses re-derived and hold; two `file:line` citations have drifted — R-13 | MEDIUM |
| **H-8** | Closed field sets pinned by test only | Unchanged. Acceptable: it is the same instrument `DecisionRecord` and `GateRunRecord` already use | LOW |
| **H-9** *(new)* | **`DecisionRecord.evidence_refs` does not come from `GateContext`.** The measurement artifact ref reaches the chain only if each gate copies `context.evidence_refs` into its `GateResult` — an adapter convention, not a `Gate` Protocol requirement, and pinned by no test — R-9 | New this review | **HIGH** |
| **H-10** *(new)* | **A compliant Phase F transition can carry no reproduction path at all** — R-10, R-11 | New this review | **HIGH** |
| **H-11** *(new)* | **The measurement artifact's payload shape is unspecified and `parameters` is archived nowhere** — R-12 | New this review | MEDIUM |
| **H-12** *(new)* | **Archive filename collision is second-granular and now reachable.** Two runs of one project inside one second refuse — correct, and previously unreachable at human speed. A step-7 collision refuses *after* the gates have run, leaving an orphan measurement artifact — consistent with the disclosed orphan policy, but reached by a new route — R-15 | New this review | LOW |

---

## 3. Findings

Each is established from the repository at HEAD `befa486` and cited to
`file:line`. Numbering continues the Resolution's §2 series from **R-8**,
as that document reserved.

### R-8 (blocking — F-0 wording) — F-0's precondition names an artifact the platform's own standard forbids producing

**Finding.** F-0's exit criterion is *"**Blocked** until an independent
architecture review has been read"* (Proposal §7), and the Resolution
§1.2 and §7 item 1 use the same term. But
`RESEARCH_GOVERNANCE_STANDARD.md` §4 states that **no document may
describe a Level 2 review using the unqualified word "independent"**, and
records that **no Level 3 review has ever been performed on this
platform** and that the organizational structure for one does not exist.

As worded, F-0's precondition is therefore satisfiable only by an
artifact the platform cannot produce. The blocker is not procedural but
**structural**: F-0 would be blocked forever, and the pressure to
eventually declare some Level 1 or Level 2 pass "independent" — the exact
failure §4 was written to correct, and which §4 records H3 having already
committed once — grows with every cycle it stays blocked.

**Ruling.** The precondition is restated in the standard's own vocabulary;
the requirement is not weakened.

1. **F-0's exit criterion is restated:** *blocked until a **Level 2
   adversarial architecture review** (Standard §4) has been read and its
   findings folded in, with **Level 3 unavailability disclosed** in the
   record.*
2. **The Resolution's §7 item 1 is restated in the same terms**, and its
   header keeps its Level 1 label — it is not upgraded by this document's
   existence.
3. **This document is that review**, and F-0's record must cite it by its
   level, never as "the independent architecture review."
4. Every Phase F document's use of the unqualified word *independent* —
   Proposal §0 header, §7 F-0 row; Resolution §1.2, §7 item 1; Gate
   Review §4.3, §5 A.2–A.4 — is to be read as **Level 2** from this
   ruling forward. No accepted AD is touched.

---

### R-9 (blocking) — the evidence-ref append rule does not deliver what §3.4 says it delivers

**Finding.** Proposal §3.4 rule 1 appends exactly one ref — the
measurement artifact's — to `GateContext.evidence_refs`, and states this
*"is what makes a `DecisionRecord` cite the measurements it rests on."*

**That consequence does not follow at HEAD.** `compose_transition()` step
8 builds the record's refs from the **admitted gates' own results**, not
from the context:

```python
# lifecycle.py:387-390
evidence_refs = _dedupe_stable(
    ref
    for name in required_gate_names
    for ref in outcome_by_name[name].result.evidence_refs
)
```

`GateContext.evidence_refs` reaches a `DecisionRecord` **only** if each
required gate copies it into its `GateResult`. Both shipped adapters do —
`gates/economic_rationale_adapter.py:49` and
`gates/signal_independence_adapter.py:44`, each
`evidence_refs=context.evidence_refs` — but `Gate` is a **structural
Protocol** (`gate.py`), nothing in it requires the propagation, and
**no test pins it**. A conforming `Gate` that returns
`evidence_refs=()` is legal, and a phase whose required gates all do so
produces a transition that cites nothing, with no refusal anywhere.

This is not a defect in Phase F's design — the append rule is right, and
so is minting the ref only for a file that already exists. It is a
**claim stronger than its mechanism**, in a document whose §8 ledger
asserts *"Evidence exists before it is cited."*

**Ruling.**

1. **AD-061 records the dependency, in these terms:** *the appended
   measurement-artifact ref reaches `DecisionRecord.evidence_refs` only
   through the required gates' own `GateResult.evidence_refs`. Both
   shipped adapters propagate `context.evidence_refs`; the `Gate`
   Protocol does not require it and Phase F cannot make it require it.
   `ResearchRunner` cannot verify the propagation for the same reason it
   cannot verify a gate's measurement key (§5.2) — it would have to reach
   into adapter internals.*
2. **§3.4's sentence is amended** from *"this is what makes a
   `DecisionRecord` cite the measurements it rests on"* to *"this is what
   makes the ref available to the gates, which is the only route by which
   it can reach a `DecisionRecord`."*
3. **F-2's exit criterion gains a clause**, and this is the cheap half of
   the repair: *the ref's arrival in a composed `DecisionRecord` is
   pinned end-to-end through at least one real gate adapter* — provable in
   F-10's fixture traversal at zero new mechanism.
4. **§8's ledger gains the non-claim:** *that a `DecisionRecord` cites the
   measurement artifact (it does so only if the phase's gates propagate
   the context's refs, which no mechanism requires).*

---

### R-10 (blocking) — `provenance_ref = None` is disclosed as a purity property; its actual consequence lands on the Decision Chain

**Finding.** §3.3 permits `MeasurementBundle.provenance_ref = None` and
AD-064 requires it be recorded as `None` and never backfilled with the
archive path. Both are **correct** and the reasoning is right: inventing
a reproduction reference that does not exist would be the precise defect
the governing principle forbids.

What neither document states is where that `None` **goes**:

```
MeasurementBundle.provenance_ref
  -> GateContext.measurement_provenance          (§3.4 rule 2, pass-through)
  -> GateRunRecord.measurement_provenance        (gate_run_record.py:72)
  -> DecisionRecord.reproduction_record_ref      (lifecycle.py:389)
```

`DecisionRecord.reproduction_record_ref` is `str | None`
(`decision_recorder.py:139`), defaulted to `None` at `:277`, and **no
guard in `compose_transition()` or `DecisionRecorder.append()` refuses a
`None`, and none checks that a non-`None` value resolves to a file.**

So the chain's own reproduction field is, at Phase F's altitude, an
optional unvalidated caller-supplied string. The Proposal's §5.2 lists
`provenance_ref`'s absence as *"an audit finding, disclosed, never filled
in"* — but the finding it produces is a **permanent, immutable,
hash-chained record asserting a transition with no reproduction path**,
and that is a different and larger statement than "an audit finding."

**Ruling.** Disclosure, not mechanism. Phase F adds no guard — a
non-`None` check at the runner would be exactly the duplicated-rule drift
R-5 refuses, and the correct altitude for such a check, if one is ever
wanted, is `compose_transition()`, which is frozen.

1. **AD-064 must record the full path above and its endpoint**, in these
   words or their equivalent: *a `provenance_ref` of `None` becomes a
   `DecisionRecord.reproduction_record_ref` of `None`. Nothing refuses
   it. A Phase F transition may therefore be recorded, permanently and
   validly, with no reproduction path, and no mechanism in Phase F or
   below will say so at the time it happens.*
2. **AD-061's §8 non-claims gain:** *that an archived Phase F run is
   reproducible (nothing requires a provenance ref, and nothing validates
   one that is supplied).*
3. **F-8's failure suite gains one case**, at no new mechanism: *a
   transition composed with `provenance_ref=None` succeeds and appends a
   record whose `reproduction_record_ref` is `None`* — so the property is
   pinned as designed behaviour rather than discovered later as a
   surprise.

---

### R-11 (blocking) — Phase F's execution model and the repository's reproduction model do not meet

**Finding.** `core/governance/reproduction_runner.py` reproduces a cycle
by installing the offline guard, checking out a **pinned worktree**, and
loading the experiment **script by relative path** from that worktree
(`_load_module_from_worktree`, `:106-121`), alongside that commit's own
migrations and dataset snapshots. Its status taxonomy — `UNVERIFIABLE`,
`DRIFTED`, `REPRODUCTION_FAILED`, `VERIFIED` — is built on artifacts that
have paths and hashes.

Phase F's `Experiment` is a **live object injected by the caller**
(§3.1), fully constructed with whatever database handle and configuration
it needs. It has no path, no commit pin, and no hash. The only identity
that survives into the archive is `experiment_name: str`, a
caller-chosen string that nothing validates.

The two models are not in conflict — they simply do not connect. A
transition produced by `ResearchRunner` cannot be re-run by
`run_reproduction`, and nothing in either document says so.

**Ruling.** Not a defect to repair in Phase F, and explicitly **not** a
licence to build a bridge — a `ReproducibilityChecker` is on §7.1's
forbidden list and has no consumer.

1. **AD-064 records the disconnect** as a stated non-claim: *`experiment_name`
   is a caller-chosen label, not an identity. Phase F archives what was
   measured; it does not record what code measured it, and a Phase F
   transition is not reproducible through `core.governance.reproduction_runner`,
   whose model is a pinned worktree and a script path.*
2. **Recorded as a deferred option so it is not rediscovered as novel:**
   binding the two models — an `Experiment` that declares a
   `commit_hash` + script path, or a `ReproductionRecord` produced beside
   the measurement artifact — is a **later increment's** decision. Phase F
   is not authorized to make it and this ruling does not.

---

### R-12 (required disclosure) — the measurement artifact's payload is unspecified, and `ExperimentSpec.parameters` is archived nowhere

**Finding.** §2.2 step 4 reads `m_art := archive_writer.write(...bundle...)`.
§3.5 gives `write_experiment_result(*, project_id, filename, payload:
Mapping[str, Any])` and is deliberately domain-blind. **F-3 specifies
`GateRunRecord` → canonical `dict`; no step specifies `MeasurementBundle`
→ `dict`.** The one artifact class Phase F invents has no defined
serialized field set.

The concrete loss: `ExperimentSpec.parameters` exists, per §3.2,
*"so an operator can pin a run's inputs without the runner acquiring
domain knowledge"* — and it appears in **no artifact and no record**. The
frozen instant is in the filename; the parameters are nowhere. A run's
inputs are therefore not recoverable from its evidence, which undercuts
the field's stated purpose.

**Ruling.**

1. **F-1's exit criterion gains:** *the measurement artifact's serialized
   field set is closed and pinned by test, and includes `experiment_name`,
   the frozen `as_of`, `parameters`, `measurements`, `evidence_refs`,
   `dataset_refs`, and `provenance_ref`.* The bundle is serialized
   **with** the spec that produced it, or `parameters`' stated purpose is
   withdrawn from §3.2.
2. **AD-061 records the field set** alongside the ten-step flow, for the
   same reason `GateRunRecord`'s is pinned: an artifact class whose shape
   is undefined acquires fields by commit rather than by decision.
3. `ArchiveWriter` stays domain-blind. The serialization belongs beside
   the bundle (F-1), never inside the writer.

---

### R-13 (required disclosure) — the censuses hold, two citations have drifted, and the re-derivation obligation is now due

**Finding.** Both Phase F documents pin their evidence to HEAD `58908fe`;
HEAD is `befa486`, **fourteen commits later**. I re-derived every
load-bearing census (§5): **all hold**, and **none of AD-067's four
amendment triggers has fired**. Two `file:line` citations have drifted:

| Citation | In documents | At HEAD `befa486` |
|---|---|---|
| `lifecycle.py:48` — the `decision_recorder` import | Resolution R-1 | **`lifecycle.py:46`** |
| `lifecycle.py:87` — `Authorization` | Resolution R-1, Proposal §2.5 | **holds** |

**Ruling.** Cheap, and owed before F-0 by the documents' own discipline.

1. **Every census in AD-063 and AD-067 is dated to the HEAD at which F-0
   lands**, not to `58908fe`, and is re-derived at that commit — four
   `git`/`ast` checks, listed in §5 of this document in the form that
   re-runs them.
2. **The two citations are corrected** in the Resolution.
3. **AD-067 states the recurrence explicitly**: the census is a count at a
   commit, the obligation to re-derive recurs on every HEAD move that
   touches `core/governance/`, and §7.2's triggers name the occasions on
   which it is *mandatory* rather than merely stale.

---

### R-14 (observation, non-blocking) — "no `core.store` dependency" is true of Phase F's modules, and the shims make it not automatically true of an `Experiment`

**Finding.** Established in §2.4: `core.store` is absent from the
fourteen-module transitive closure of everything Phase F reaches, and
`research` holds no `store` grant. But `tools/check_import_boundaries.py`
is a **direct-import** checker, and AD-069 made the
`core.market_data.persistence.{database,migrations}` re-export shims
**permanent**. Any `research` module may import a shim under its existing
`data` grant and reach `core.store` through it, with no violation raised
and no recorded decision — the demand-driven grant rule (GR-03, §5.3) is
satisfied in letter while the dependency exists in fact.

**Ruling.** One sentence in AD-061, no mechanism. *Phase F's own modules
depend on `core.store` neither directly nor transitively (verified at
HEAD). A future `Experiment` implementation that reads the database
acquires that dependency; if written under `core/research/`, a direct
`core.store` import is a boundary violation requiring a recorded decision
in the same commit, while a shim import is not flagged. Phase F's
no-store property must be recorded as a property of Phase F's modules,
never as one inherited by an `Experiment`.*

---

### R-15 (required disclosure) — the collision refusal is correct, and automation is what makes it reachable

**Finding.** §2.6 dates archive filenames to the second and refuses on
collision — never a suffix, never an overwrite. Correct, and it mirrors
`write_manifest()`'s existing precedent. Two consequences the Proposal
does not state: two runs of one project inside one second refuse (a
condition unreachable at human speed and reachable by an automated
caller, including F-10 and any future loop); and a **step-7** collision
refuses *after* the experiment and the gates have run, leaving an orphan
measurement artifact.

**Ruling.** §5.2 gains one bullet. The orphan is already governed by the
disclosed retention policy; what is new is the route, and it belongs
beside AD-062's existing disclosure that *automating execution makes the
unenforced single-writer assumption easier to violate by accident*. Same
sentence, same reason, one more instance. **No suffixing, no retry, no
sub-second timestamps** — each would trade an observed property for an
invented one.

---

## 4. Conditions

### Must be discharged **inside F-0's own text**, before AD-061 … AD-067 are written

- **C-1 (R-8).** Restate F-0's precondition and the Resolution's §7 item 1
  in leveled terms; cite this document as the **Level 2** adversarial
  architecture review, with **Level 3 unavailability disclosed**. Never
  as "the independent architecture review."
- **C-2 (R-9).** Fold the evidence-ref propagation dependency into
  AD-061; amend §3.4's sentence; add the §8 non-claim.
- **C-3 (R-10, R-11).** Fold the `provenance_ref` → `reproduction_record_ref`
  path, its `None` endpoint, and the disconnect from
  `reproduction_runner` into AD-064; add both §8 non-claims.
- **C-4 (R-13).** Re-derive and re-date every AD-063/AD-067 census to the
  HEAD at which F-0 lands; correct `lifecycle.py:48` → `:46`.
- **C-5 (R-14).** One sentence in AD-061 scoping the no-`core.store`
  property to Phase F's own modules.

### Must be discharged before **F-1 code lands**

- **C-6 (R-12).** Close the bundle-serialization specification gap in
  F-1's exit criterion, including `parameters`.
- **C-7 (R-9 item 3).** Extend F-2's exit criterion to pin the ref's
  arrival in a composed record through one real gate adapter — provable
  inside F-10 at no new mechanism.
- **C-8 (R-2, restated as binding).** F-9's AST test must cover
  `adapters/research/` **by name**. F-7 must not land before F-9's scope
  does. This was already ruled; it is restated here because it is the one
  condition whose omission leaves the composition root covered by
  *nothing*.

### Strongly recommended, independent of Phase F

- **C-9 (H-3).** Introduce CI running pytest on push, gating on **pytest
  only** — `tools/check_import_boundaries.py` exits 1 at HEAD by design
  (5 known AD-068 ETF violations), and the posture is correctly encoded
  as the strict `xfail`. This remains the highest-leverage unaddressed
  risk in the repository and it is cheap. Not a blocker: the repository's
  standing discipline is a human-run suite, and Phase F does not change
  that.
- **C-10 (R-15).** Add the collision bullet to §5.2.

### May proceed in parallel with Phase F

- **C-11 (H-4).** Create `research_archive/reference_h4/experiment_results/`
  by the additive `tools/` route (Q1's ruling), as a dated human act —
  **never** by relaxing F-4's precondition.
- **C-12 (H-2).** AD-067's four amendment triggers remain standing human
  obligations with nothing detecting them. Confirmed correct as designed;
  building a detector stays forbidden (§7.1).

---

## 5. Censuses re-derived at HEAD `befa486`

Every claim below was executed, not read out of the documents under
review. All hold; none of AD-067's four triggers has fired since
`58908fe`.

| Claim | Source in the documents | Re-derived at `befa486` | Verdict |
|---|---|---|---|
| `decision_recorder` declares no `__all__`; export surface is **14** public module-level names | AD-063 / AD-067 | AST walk → exactly the 14 recited, in that order, no `__all__` | ✅ holds |
| **13** modules besides `__init__.py` under `core/governance/` | AD-067 | 13 | ✅ holds |
| Exactly **one** of them can write `transition_records.jsonl` | AD-067 | `decision_recorder.py` alone | ✅ holds |
| `core/governance/__init__.py` re-exports **nothing** | AD-063 (a)'s premise | prose only — no `import`, no `from`, no `__all__` | ✅ holds |
| `canonical_jsonl.py` imports nothing from this repository; **5** module-level functions | AD-063 (b)'s premise | `hashlib`, `json`, `pathlib`, `typing` only (`:16-21`); 5 functions | ✅ holds |
| Frozen `gate_runner.py:39` already imports `canonical_jsonl` | R-1a | holds | ✅ holds |
| `write_canonical_jsonl` does `parent.mkdir(parents=True, exist_ok=True)` | R-6 | `canonical_jsonl.py:46` | ✅ holds |
| `Authorization` is defined in `lifecycle.py` | R-1 | `:87` | ✅ holds |
| `lifecycle.py` imports `decision_recorder` at module scope | R-1 | **`:46`**, cited as `:48` | ⚠️ citation drift (R-13) |
| `register_phase_gates(phase, [])` is legal; `gates_for_phase` raises `KeyError` | R-5, R-4 | `validation_registry.py:32` (no non-empty check), `:38` | ✅ holds |
| `FixedClock` refuses a naive datetime | R-7 | `core/shared/clock.py:19` | ✅ holds |
| `compose_transition` is called by **no non-test module** | R-3 | only `tests/test_lifecycle_composition.py` (7 sites) | ✅ holds |
| `check_repository` scans `core/` only | R-2 | `:341` | ✅ holds |
| `adapters/` imports neither Validation nor Governance; `adapters/research/` does not exist | R-2 | `adapters/` holds `cli/` only | ✅ holds |
| `research` grant = `{data, statistics, governance, validation}`, no `store` | §4.1 | `:176` | ✅ holds |
| `research_archive/reference_h4/` has no `experiment_results/` | Q1, H-4 | manifest only | ✅ holds (gap open) |
| No `transition_records.jsonl` exists anywhere | §1, H-6 | `find` → nothing | ✅ holds |
| No CI configuration exists | H-3 | no `.github/`, `.pre-commit-config.yaml`, `Makefile` | ✅ holds |
| Suite state | Gate Review §2.3 (783/1/1) | **787 passed, 1 skipped, 1 xfailed** — 4 tests added since | ✅ green |
| `master` is pushed | C-2 | `origin/master...master` → `0 0` | ✅ discharged |
| The Proposal is a tracked artifact | C-1 / GR-20 | `git status --porcelain` → empty | ✅ discharged |
| `ImportError` Path A is governed | C-6 | `reproduction_runner.py:162` — `except (OSError, ImportError)`; AD-069 amended with the dated `91634c8` note | ✅ discharged |
| `reproduction_runner`'s isolation docstring is corrected | C-7 | `:1-40` now states the `sys.modules['core']` resolution explicitly and cites AD-069 and T-2 | ✅ discharged |

**New findings' evidence.** `lifecycle.py:387-390`
(`evidence_refs` built from gate results, not context) and `:389`
(`reproduction_record_ref = run_record.measurement_provenance`);
`decision_recorder.py:139,277` (`reproduction_record_ref: str | None`,
defaulted `None`); `gates/economic_rationale_adapter.py:49` and
`gates/signal_independence_adapter.py:44` (propagation by convention);
`reproduction_runner.py:106-121` (script-by-path model);
transitive closure of Phase F's reachable set = 14 modules, `core.store`
absent.

---

## 6. Method, and what this review did not do

**Verified by execution.** Full suite (787/1/1); AST enumeration of
`decision_recorder`'s export surface; transitive first-party import
closure over Phase F's entire reachable set; `git log`, `git status
--porcelain`, `git rev-list --left-right --count`; filesystem checks for
`transition_records.jsonl`, CI configuration, `reference_h4`,
`adapters/research/`, `core/research/execution/`, and the
`core/governance/` module census; grep census of `core.store` importers
and of `compose_transition` call sites.

**Verified by reading.** `lifecycle.py` composition steps 8–9 and the
`compose_transition` signature; `decision_recorder.py` record shape;
`gate_run_record.py` and `gate_context.py` field sets;
`validation_registry.py` in full; `clock.py` in full;
`canonical_jsonl.py` in full; both gate adapters' `GateResult`
construction; `reproduction_runner.py:1-40` and its worktree loader;
`check_import_boundaries.py` domain tables and scan root;
`ARCHITECTURE_DECISIONS.md` reservation block, AD-059, AD-060, AD-068,
AD-069; `RESEARCH_GOVERNANCE_STANDARD.md` §4 in full; the Proposal, the
Resolution, and the Gate Review in full.

**Not verified.** That the suite is green at each intermediate commit.
That `MeasurementBundle`'s and `ExperimentSpec`'s proposed shapes are
adequate for any *real* H4 experiment — no such experiment exists, and
Phase F is explicitly not authorized to write one. Any claim about a
Level 3 review, which does not exist and cannot be produced by this
platform. Whether the seven ADs, once written, actually carry the
required content — that is F-0's own exit criterion and belongs to
whoever reviews F-0's commit.

**Reviewed but deliberately not re-audited.** C0…C7's boundary-hardening
milestone. The Gate Review audited it at Level 1 and found it complete;
this review's scope is Phase F's architecture, and I re-checked only
those of its conclusions that Phase F rests on (§5).

---

## 7. Claim-to-mechanism ledger for this review

| Claim this document makes | Mechanism | Where it fails if unbuilt |
|---|---|---|
| Every census still holds at HEAD | Each re-derived by execution at `befa486` and listed in §5 in re-runnable form | If a census were carried over from the documents under review, this would be a citation, not a review |
| Phase F has no `core.store` dependency | Full transitive first-party import closure over Phase F's reachable set — 14 modules, `store` absent | A direct-import grep would have missed a transitive edge; the closure would not |
| The architecture is sound | **Nothing.** This is a Level 2 judgment, not a mechanism. Eight findings were corrections, disclosures, and one specification gap; none was structural — but a Level 2 pass is not proof of soundness | If the design has a defect no adversarial reading at this level detects, this document will not have found it |
| Phase F is no longer resting on self-review | This document is a separate pass with no continuity to the work, and it re-derived rather than inspected | If cited as Level 3, or as "independent" unqualified, the acceptance would record a claim the Standard §4 forbids — R-8 |
| The conditions are sufficient | Each of C-1 … C-8 names the AD or exit criterion it lands in, so F-0's and F-1's own exit criteria carry them | If a condition were left as prose here and not folded into an AD, it would be discharged by memory |

**What this document does not claim:** that Phase F has cleared Level 3
review (none exists, none can be produced here); that any AD is accepted
(none is — acceptance is F-0, in `ARCHITECTURE_DECISIONS.md`); that the
architecture is proven sound (a Level 2 pass is not evidence of
soundness); that a Phase F run will be reproducible (R-10, R-11); that
the four amendment triggers are detected by anything (they are not); that
any census here holds after HEAD `befa486` (each is a count at that
commit); that this review discharges the Gate Review's C-9 … C-12, which
remain open by their own terms.
