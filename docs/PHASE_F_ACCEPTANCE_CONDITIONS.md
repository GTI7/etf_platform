# Phase F — Architecture Acceptance Amendment (Conditions F-C1 … F-C4)

**Date:** 2026-07-24
**Author role:** lead architect
**Decision recorded:** **APPROVED WITH CONDITIONS**
**Amends:** `docs/PHASE_F_ARCHITECTURE_ACCEPTANCE.md` (the "Acceptance
Review"), by adding four conditions that bind F-0's authoring act.
**Repository state:** canonical `D:\Claude\etf_platform`, `master`, HEAD
**`befa486`**, working tree clean at the time of the Acceptance Review,
suite 787 passed / 1 skipped / 1 xfailed.

**What this document is.** A **binding acceptance amendment**. It records
the four conditions attached to the Phase F architecture approval, with
rationale, affected AD number, and implementation consequence for each.

**What this document is not.** It is **not** a review — it performs no
re-derivation and claims no findings of its own; every factual claim it
makes is carried from the Acceptance Review and cited to it. Its own
review level is **Level 1** (`RESEARCH_GOVERNANCE_STANDARD.md` §4) and it
must never be cited as an independent review of anything.

**Explicitly out of scope, and untouched by this document:**

- **No production code.** No module under `core/`, `adapters/`, or
  `tools/` is added, edited, or deleted by this amendment.
- **No tests.** No test is added or modified. Where a condition names a
  test obligation, that obligation lands in a **phase exit criterion**,
  not here.
- **No ADR changes.** `docs/ARCHITECTURE_DECISIONS.md` is **not edited**
  by this amendment. AD-061 … AD-067 remain **reserved and unaccepted**;
  the accepted ceiling remains **AD-069**. Every "affected AD" below
  names the AD whose **required content** a condition binds **when F-0
  writes it** — a forward obligation on an unwritten AD, not an edit to
  an accepted one.

---

## 0. Status of the approval

The Phase F architecture is **approved**. No structural defect was found
(Acceptance Review §0). The approval is **conditional**: the four
conditions below are prerequisites on the *content* of F-0, not
objections to the *design*.

| | |
|---|---|
| Architecture verdict | **Approved** — sound as designed |
| Acceptance act (F-0) | **Not yet performed.** AD-061 … AD-067 reserved, unaccepted |
| Conditions attached | **F-C1, F-C2, F-C3, F-C4** (this document) |
| Conditions inherited | **C-1 … C-12** (Acceptance Review §4), unchanged and still binding |
| Code authorized by this document | **None** |

**Relationship to the Acceptance Review's own conditions.** The Acceptance
Review already carries twelve conditions, C-1 … C-12. The four conditions
here **do not replace them**. Three of the four (F-C1, F-C3, F-C4)
restate and, in two cases, **strengthen** a subset of them at the
architect's authority; F-C2 is **broader than any of them** and §5 states
exactly where. Where a condition here is stronger than the review ruling
it derives from, **the stronger form governs** and §5 records the
divergence so it is not discovered later as an inconsistency.

---

## 1. Condition F-C1 — Evidence references are not reproduction guarantees

> **Condition.** Evidence references are not reproduction guarantees.
> Phase F must distinguish **evidence retention** from **reproducibility
> contracts**, in its architecture decisions and in its claim ledger. It
> may not let a retention property be read as a reproduction property.

### 1.1 Rationale

Phase F genuinely delivers **evidence retention**: every run's raw
measurement bundle and raw `GateRunRecord` are archived in canonical
JSONL, content-hashed, dated, written **before** anything is composed,
and never deleted, overwritten, or repaired — including for refused
transitions. That is `RESEARCH_GOVERNANCE_STANDARD.md` §5's append-only
raw-output discipline, correctly implemented, and stronger than what the
repository has today (Acceptance Review §2.3).

It does **not** deliver **reproducibility**, and three mechanisms
establish that (Acceptance Review §2.3, R-10, R-11):

1. The Decision Chain's own reproduction field is an **optional,
   unvalidated, caller-supplied string**. `MeasurementBundle.provenance_ref`
   may be `None`; it flows unchanged to
   `GateContext.measurement_provenance` → `GateRunRecord.measurement_provenance`
   → `DecisionRecord.reproduction_record_ref`. **Nothing refuses a `None`,
   and nothing checks that a non-`None` value resolves to anything.** A
   fully compliant Phase F transition can be recorded — permanently,
   immutably, hash-chained — with **no reproduction path at all**.
2. Phase F ships **no `ReproductionRecord` producer**, and its execution
   model is structurally disconnected from the repository's existing one
   (`core.governance.reproduction_runner`, which reproduces by pinned
   worktree and script path).
3. The one artifact class Phase F invents has **no defined serialized
   field set**, so what is retained is itself under-specified (R-12).

The failure mode this condition prevents is **not** a code defect. It is
a **claim stronger than its mechanism** — the precise class of defect
this repository's governing principle exists to catch. The Proposal's §8
ledger asserts *"Evidence exists before it is cited"* with no companion
non-claim that the evidence need not suffice to re-derive the
measurement. A later reader, or a later increment, reading an archived
bundle and a hash-chained record as *reproduction* evidence would be
making an inference the architecture does not license and no mechanism
refuses.

**This condition is a disclosure obligation, not a mechanism obligation.**
Phase F is explicitly not the reproduction increment. Adding a
non-`None` guard at the runner would duplicate a rule that belongs in
`compose_transition()` (frozen), which is exactly the drift R-5 refuses.
The repair is that the architecture record must **say what it does not
guarantee**.

### 1.2 Affected AD numbers

| AD | Obligation added by F-C1 |
|---|---|
| **AD-064** (primary) | Must record the full `provenance_ref = None` → `reproduction_record_ref = None` path and its endpoint, in these terms or their equivalent: *a `provenance_ref` of `None` becomes a `DecisionRecord.reproduction_record_ref` of `None`. Nothing refuses it. A Phase F transition may therefore be recorded, permanently and validly, with no reproduction path, and no mechanism in Phase F or below will say so at the time it happens.* Must also record the disconnect from `reproduction_runner` (see F-C2). |
| **AD-061** (secondary) | Its §8 non-claims must gain: *that an archived Phase F run is reproducible* (nothing requires a provenance ref, and nothing validates one that is supplied); and *that a `DecisionRecord` cites the measurement artifact* (see F-C3). |

**No new AD number is created.** Both obligations land inside
already-reserved ADs, per Acceptance Review §2.5.

### 1.3 Implementation consequence

1. **F-0 (docs only).** AD-064 and AD-061 cannot be written without the
   clauses above. F-0's exit criterion is not met if either AD is written
   with retention language that reads as reproduction language.
2. **Terminology, repository-wide, from this ruling forward.** *Evidence
   retention* = the archive property Phase F delivers. *Reproducibility
   contract* = a commitment that a run can be re-executed to the same
   result. Phase F holds the first and **makes no instance of the
   second**. The two terms must not be used interchangeably in any Phase F
   document.
3. **F-8 gains one failure case**, at no new mechanism: *a transition
   composed with `provenance_ref=None` succeeds and appends a record whose
   `reproduction_record_ref` is `None`* — pinning the property as designed
   behaviour rather than leaving it to be discovered as a surprise.
4. **No guard is added anywhere.** Not in `ResearchRunner`, not in
   `ArchiveWriter`, not in `compose_transition()` (frozen). A future
   decision to require a resolvable provenance ref is a **later
   increment's** decision and F-0 does not make it.

---

## 2. Condition F-C2 — Experiment execution must persist sufficient identity

> **Condition.** Experiment execution must persist sufficient identity.
> The archived record of a run must carry, at minimum:
> - **experiment specification**
> - **parameters**
> - **dataset reference**
> - **code revision reference**
> - **environment / provenance reference**
>
> Where an element is unavailable, it is persisted as an explicit absence,
> never omitted and never inferred.

### 2.1 Rationale

At approval, a Phase F run's own inputs and identity are **archived
nowhere** (Acceptance Review R-11, R-12):

- `ExperimentSpec.parameters` exists, per Proposal §3.2, *"so an operator
  can pin a run's inputs without the runner acquiring domain knowledge"* —
  and **no step in §7 serializes it**. It appears in no artifact and no
  record. The frozen instant survives in the filename; the parameters
  survive nowhere. The field's stated purpose is currently unmet by the
  design that declares it.
- **`MeasurementBundle` has no specified serialization.** F-3 specifies
  `GateRunRecord` → canonical `dict`; **no step specifies
  `MeasurementBundle` → `dict`**. `ArchiveWriter.write_experiment_result`
  takes an opaque `payload: Mapping[str, Any]` and is deliberately
  domain-blind. An artifact class with an undefined shape acquires its
  fields **by commit rather than by decision**.
- **The only identity that survives is `experiment_name: str`** — a
  caller-chosen label that nothing validates. Phase F's `Experiment` is a
  **live object injected by the caller**, fully constructed with whatever
  database handle and configuration it needs; it has no path, no commit
  pin, and no hash. `experiment_name` must never be read as answering
  *what code measured this*.

The consequence is that an archived Phase F artifact answers *what was
measured* and does not answer *what produced it*. That is a defect in
**evidence sufficiency**, and it is separable from — and repairable
without — any reproduction guarantee. F-C1 forbids overclaiming;
F-C2 requires that what **is** retained be worth retaining.

**The distinction that makes this condition consistent with F-C1.**
F-C2 requires the persistence of **identity**, not the delivery of
**re-execution**. Recording a code revision reference alongside a
measurement is an act of evidence retention. It does **not** assert that
the run can be re-run, does not bind Phase F to
`core.governance.reproduction_runner`, and does not create a
reproducibility contract. Phase F remains, after F-C2 is discharged, an
architecture with **no reproduction guarantee** — one whose evidence is
now sufficient for a later increment to build one **from**, rather than
one whose evidence is silently insufficient for anything.

### 2.2 Affected AD numbers

| AD | Obligation added by F-C2 |
|---|---|
| **AD-061** (primary) | Must record the measurement artifact's **closed serialized field set** alongside the ten-step flow — for the same reason `GateRunRecord`'s is pinned. The set must include, at minimum: `experiment_name`, the frozen `as_of`, `parameters`, `measurements`, `evidence_refs`, `dataset_refs`, `provenance_ref`, and a **code revision reference** field. |
| **AD-064** (primary) | Must record that `experiment_name` is a **caller-chosen label, not an identity**; that Phase F archives *what was measured* and — absent an explicitly supplied revision and provenance reference — does **not** record *what code measured it*; and that a Phase F transition is **not** reproducible through `core.governance.reproduction_runner`, whose model is a pinned worktree and a script path. Must record each identity element's **absence semantics**: an unavailable element is persisted as an explicit `None`/empty, **never backfilled, never inferred**. |
| **AD-062** (secondary, bounded) | Unchanged in substance. Recorded here only to fix the boundary: `ArchiveWriter` **stays domain-blind**. Serialization of the bundle belongs beside the bundle (F-1), **never inside the writer**. F-C2 must not be read as widening `ArchiveWriter`'s knowledge. |

### 2.3 Implementation consequence

1. **F-1's exit criterion is extended** and is the load-bearing half of
   this condition: *the measurement artifact's serialized field set is
   **closed and pinned by test**, and includes every element enumerated
   above.* The bundle is serialized **together with the spec that
   produced it**, or `parameters`' stated purpose is withdrawn from §3.2
   — those are the only two admissible outcomes.
2. **`ExperimentSpec` and `MeasurementBundle` gain identity fields.** The
   five-element minimum requires at least a **code revision reference**
   and an **environment/provenance reference** to be *representable*.
   Whether they are added to `ExperimentSpec` (declared by the caller) or
   to `MeasurementBundle` (emitted by the experiment) is an **F-1 design
   choice**, constrained by one rule already accepted: an `Experiment`
   **cannot emit a status, threshold, direction, or narrative** (AD-064).
   Identity is not a criterion, so this constraint is not strained.
3. **Absence is recorded, never filled.** This is a direct application of
   AD-064's existing `provenance_ref` rule to every identity element. No
   element may be derived by the runner — no `git rev-parse` inside
   `ResearchRunner`, no environment sniffing, no inference from the
   archive path. The caller supplies identity or the record says it was
   not supplied.
4. **No bridge to `reproduction_runner` is authorized.** A
   `ReproducibilityChecker` remains on Proposal §7.1's forbidden list and
   has no consumer. F-C2 makes a future bridge **possible**; it does not
   build one and does not authorize F-1 … F-10 to build one.
5. **Scope note.** F-C2 is broader than Acceptance Review C-6 (which
   covered the serialization gap and `parameters` only). See §5 for the
   divergence and its justification.

---

## 3. Condition F-C3 — Gate evidence propagation must become an explicit contract

> **Condition.** Gate evidence propagation must become an **explicit
> contract**. It may not rest on adapter convention. Phase F must not
> claim an evidence-citation property that only holds because the two
> shipped adapters happen to implement it.

### 3.1 Rationale

Proposal §3.4 rule 1 appends exactly one ref — the measurement artifact's
— to `GateContext.evidence_refs` and states this *"is what makes a
`DecisionRecord` cite the measurements it rests on."* **That consequence
does not follow at HEAD** (Acceptance Review R-9). `compose_transition()`
builds the record's refs from the **admitted gates' own results**, not
from the context:

```python
# lifecycle.py:387-390
evidence_refs = _dedupe_stable(
    ref
    for name in required_gate_names
    for ref in outcome_by_name[name].result.evidence_refs
)
```

So `GateContext.evidence_refs` reaches a `DecisionRecord` **only** if each
required gate copies it into its `GateResult`. Both shipped adapters do
(`gates/economic_rationale_adapter.py:49`,
`gates/signal_independence_adapter.py:44`, each
`evidence_refs=context.evidence_refs`). But `Gate` is a **structural
Protocol**; nothing in it requires the propagation, and **no test pins
it**. A conforming `Gate` returning `evidence_refs=()` is legal, and a
phase whose required gates all do so produces a transition that **cites
nothing**, with **no refusal anywhere**.

Two properties therefore rest on convention: the citation itself, and the
Proposal §8 ledger claim *"Evidence exists before it is cited."* Both are
true today and neither is guaranteed. A future gate adapter — written by
someone who never reads this document — silently removes them.

**Why "contract" and not merely "disclosure".** The Acceptance Review
ruled disclosure plus one end-to-end test pin (C-2, C-7). At the
architect's authority this condition is **strengthened**: disclosure
alone leaves the property held by nothing and detected by nothing, and
this is the one convention in the design on which a **governance-visible
claim** rests. A contract is what makes the requirement discoverable by
the person who breaks it.

**What "contract" can and cannot mean here, stated precisely.** The `Gate`
Protocol lives in **frozen Validation**. Phase F is not authorized to
amend it, and AD-063 forbids Phase F holding authority there. The
contract is therefore expressed at the altitudes Phase F **does** control:

- **Stated** as a requirement in AD-061 — not as an observation that the
  adapters happen to comply.
- **Bound** to the governance act that admits a gate: registering a
  phase → gate assignment (AD-066) is already a `decision_log.md` entry
  with a named human, and that act must now **attest propagation**.
- **Pinned** end-to-end by test through at least one real gate adapter
  (F-2 exit criterion, provable inside F-10 at no new mechanism).
- **Disclosed** where it still cannot be enforced: `ResearchRunner`
  cannot verify propagation for the same reason it cannot verify a gate's
  measurement key (§5.2) — it would have to reach into adapter internals.

A Protocol-level requirement is the correct long-term home and is a
**Validation-owned decision in a later increment**. Phase F does not make
it and this amendment does not authorize it.

### 3.2 Affected AD numbers

| AD | Obligation added by F-C3 |
|---|---|
| **AD-061** (primary) | Must record the dependency **as a contract clause**, not an observation: *the appended measurement-artifact ref reaches `DecisionRecord.evidence_refs` only through the required gates' own `GateResult.evidence_refs`. A gate admitted to a Phase F sequence **is required to propagate `context.evidence_refs`**. Both shipped adapters do; the `Gate` Protocol does not require it and Phase F cannot make it require it; `ResearchRunner` cannot verify it without reaching into adapter internals.* |
| **AD-066** (primary) | Gate registration is already a governance act requiring a `decision_log.md` entry and a named human. That act must now **carry the propagation attestation**: registering a gate to a phase asserts that the gate propagates `context.evidence_refs`. This is where the contract acquires an accountable holder. |
| **AD-067** (secondary) | The contract is **human-attested and unenforced by any mechanism**, which is the same class of obligation as AD-067's four amendment triggers. It is recorded under the same disclosure discipline: stated, owned, and explicitly **not detected by anything**. |

### 3.3 Implementation consequence

1. **Proposal §3.4's sentence is amended** from *"this is what makes a
   `DecisionRecord` cite the measurements it rests on"* to *"this is what
   makes the ref available to the gates, which is the only route by which
   it can reach a `DecisionRecord`."*
2. **Proposal §8's ledger gains the non-claim:** *that a `DecisionRecord`
   cites the measurement artifact* (it does so only if the phase's gates
   propagate the context's refs, which no mechanism requires).
3. **F-2's exit criterion gains a clause:** *the ref's arrival in a
   composed `DecisionRecord` is pinned end-to-end through at least one
   real gate adapter.* Provable in F-10's fixture traversal at **zero new
   mechanism**.
4. **No runtime check is added.** No propagation validator in
   `ResearchRunner`, no wrapper around `Gate`, no interceptor. Each would
   require adapter-internal knowledge the architecture forbids, and each
   would trade an observed property for an invented one.
5. **Escalation path, recorded so it is not rediscovered as novel:**
   making propagation a `Gate` **Protocol** requirement is a
   Validation-owned decision for a later increment. Phase F is not
   authorized to make it; F-0 must not be written as though it had.

---

## 4. Condition F-C4 — Architecture acceptance terminology

> **Condition.** This review is **Level 2 procedural independence**, not
> **Level 3 organizational independence**. Every record of Phase F's
> acceptance must say so in those terms, and no Phase F document may use
> the unqualified word *independent* to describe it.

### 4.1 Rationale

`RESEARCH_GOVERNANCE_STANDARD.md` §4 binds this repository to two
statements that are jointly decisive:

- **No document may describe a Level 2 review using the unqualified word
  "independent."**
- **No Level 3 review has ever been performed on this platform**, and the
  organizational structure required for one **does not exist**.

F-0's exit criterion, as originally worded, is *"blocked until an
**independent** architecture review has been read"* (Proposal §7;
Resolution §1.2 and §7 item 1). As worded, that precondition is
satisfiable **only by an artifact the platform cannot produce**. The
blocker is not procedural but **structural**: F-0 would be blocked
forever, and the pressure to eventually declare some Level 1 or Level 2
pass "independent" — the exact failure §4 was written to correct, and
which §4 records H3 having already committed once — grows with every
cycle it stays blocked (Acceptance Review R-8).

The Acceptance Review is **procedurally independent**: a separate pass,
no conversational continuity to the sessions that produced the Proposal,
the Resolution, or the Gate Review, and every load-bearing claim
re-derived from the repository rather than read out of those documents.
It is **not organizationally independent** under any definition §4
recognizes: same model family and vendor, no incentive separation, no
accountable persistent reviewer identity, and the claim of no
conversational memory is **self-reported**.

Naming the level precisely is what makes the acceptance honest. Naming it
loosely would record a claim the Standard forbids — in a permanent
governance file, under seven AD numbers, at the exact gate whose purpose
is to prevent that.

### 4.2 Affected AD numbers

**All seven — AD-061 … AD-067 — and no single one.** This condition binds
a **field common to all of them** rather than the content of any:

| AD | Obligation added by F-C4 |
|---|---|
| **AD-061 … AD-067** (each) | Each AD's **review-basis line** must cite `docs/PHASE_F_ARCHITECTURE_ACCEPTANCE.md` **by level** — *Level 2 adversarial architecture review* (`RESEARCH_GOVERNANCE_STANDARD.md` §4) — and must disclose that **Level 3 review is unavailable on this platform**. No AD may cite it as "the independent architecture review". Precedent for the form: AD-068's review-basis line, which states its Level 1 basis and its non-discharge in the same sentence. |
| **No AD content changes** | F-C4 changes no architectural decision. It is a **citation and terminology** obligation only. |

### 4.3 Implementation consequence

1. **F-0's exit criterion is restated**, and the requirement is **not
   weakened**: *blocked until a **Level 2 adversarial architecture
   review** (Standard §4) has been read and its findings folded in, with
   **Level 3 unavailability disclosed** in the record.* Under that
   restatement, the blocker is **discharged**, not waived.
2. **The Resolution's §7 item 1 is restated in the same terms**, and the
   Resolution **keeps its Level 1 label** — it is not upgraded by the
   Acceptance Review's existence.
3. **Every existing unqualified use of *independent* in a Phase F
   document is to be read as *Level 2* from this ruling forward** —
   Proposal §0 header and §7's F-0 row; Resolution §1.2 and §7 item 1;
   Gate Review §4.3 and §5 A.2–A.4. **No accepted AD is touched by this
   re-reading.**
4. **The reservation block in `ARCHITECTURE_DECISIONS.md`** records F-0 as
   blocked *"for want of an independent review that does not exist as a
   repository artifact."* When F-0 is performed, that sentence is
   superseded by the acceptance itself and must be replaced **in leveled
   terms** — not by asserting that an independent review was found.
5. **Standing prohibition.** `docs/PHASE_F_ARCHITECTURE_ACCEPTANCE.md`
   must **never** be cited as "the independent architecture review", in
   any document, at any later date. If a Level 3 review ever becomes
   possible, it is a **new artifact**; this one is not promoted to it.

---

## 5. Divergences from the Acceptance Review's own rulings

Recorded explicitly so the difference is not later read as an
inconsistency between two governance documents.

| Condition | Review ruling it derives from | Divergence | Authority and justification |
|---|---|---|---|
| **F-C1** | R-10, R-11; conditions C-3 | **None in substance.** Generalized from two specific disclosures into a **standing terminological rule** (retention ≠ reproducibility) that binds future Phase F documents, not only AD-064's text | Architect's clarification. Strictly additive; no ruling is reversed |
| **F-C2** | R-12; condition C-6 (bundle serialization + `parameters`) | **Broader.** C-6 required the serialized field set be closed and include `parameters`. F-C2 additionally requires a **code revision reference** and an **environment/provenance reference** be representable and persisted. R-11 had explicitly deferred *binding Phase F to the repository's reproduction model* to a later increment | **Partial, deliberate departure.** R-11 deferred the **bridge**; F-C2 requires the **record**. Persisting an identity element is evidence retention (F-C1's first term) and creates no reproducibility contract. R-11's actual prohibition — building a `ReproducibilityChecker` or wiring Phase F into `reproduction_runner` — **remains in force and is restated in §2.3 item 4.** The cost is bounded: fields on a spec/bundle that F-1 was already required to close |
| **F-C3** | R-9; conditions C-2, C-7 | **Stronger.** C-2/C-7 required disclosure plus one end-to-end test pin. F-C3 requires an **explicit contract** — a stated requirement in AD-061, an attestation obligation in AD-066, and an unenforceability disclosure in AD-067 | Architect's escalation. The disclosure form leaves a governance-visible claim held by nothing. The contract adds **no code and no runtime mechanism** (§3.3 item 4); it relocates an existing human obligation to the act that already has a named human owner |
| **F-C4** | R-8; condition C-1 | **None in substance.** Extends C-1's scope from F-0's precondition wording to **each of the seven ADs' review-basis lines** | Architect's clarification. C-1 fixed the precondition; F-C4 fixes what the resulting ADs say about their own basis |

**Unchanged and still binding:** Acceptance Review conditions **C-1 …
C-12** in full, including C-8 (F-9's AST test must cover
`adapters/research/` by name; F-7 must not land before F-9's scope does),
C-9 (CI — the highest-leverage unaddressed risk in the repository),
C-10 … C-12. Nothing in this amendment discharges any of them.

---

## 6. Condition → discharge map

| Condition | Discharged in | Discharged by writing | Verified by |
|---|---|---|---|
| **F-C1** | **F-0** (docs only) | AD-064's `None`-path clause; AD-061's §8 non-claims | F-0's own commit review; F-8 failure case pins the behaviour |
| **F-C2** | **F-0** (AD content) + **F-1** (field set closed) | AD-061's closed field set; AD-064's identity/absence clauses | F-1 exit criterion — field set **pinned by test** |
| **F-C3** | **F-0** (AD content) + **F-2** (test pin) | AD-061's contract clause; AD-066's attestation clause; AD-067's non-detection disclosure | F-2 exit criterion — end-to-end pin through one real adapter, inside F-10 |
| **F-C4** | **F-0** (all seven review-basis lines) | The leveled citation in AD-061 … AD-067; restated F-0 exit criterion; restated Resolution §7 item 1 | F-0's commit review — grep for unqualified *independent* in Phase F documents |

**Gate on F-0.** F-0 is not complete unless **F-C1, F-C2 (AD half), F-C3
(AD half), and F-C4 are all discharged in its own text**, in addition to
Acceptance Review C-1 … C-5.

**Gate on F-1 / F-2.** F-1 must not land without F-C2's closed,
test-pinned field set. F-2 must not land without F-C3's end-to-end pin.

---

## 7. Claim-to-mechanism ledger for this amendment

| Claim this document makes | Mechanism | Where it fails if unbuilt |
|---|---|---|
| The four conditions bind F-0 | Each names the AD whose required content it enters, and §6 maps each to an exit criterion | A condition left as prose here and not folded into an AD would be discharged by memory |
| F-C2 does not create a reproducibility contract | F-C1's terminology rule, plus §2.3 item 4's restated prohibition on bridging to `reproduction_runner` | If a later increment reads persisted identity as a reproduction promise, F-C1's disclosure in AD-064 is the thing that refuses it |
| F-C3's contract is enforceable where it is stated | It is not, fully — the pin covers one adapter, the attestation is human, and AD-067 discloses that nothing detects a breach | A gate adapter written without reading AD-061 or AD-066 still breaks propagation silently. The contract makes it **discoverable and owned**, not **prevented** |
| No production code, tests, or ADRs changed | Nothing in this document is executable; `ARCHITECTURE_DECISIONS.md` is untouched and AD-061 … AD-067 remain unaccepted | If any "affected AD" line were read as an edit rather than a forward obligation, the reservation's integrity would be broken |

**What this document does not claim:** that Phase F is accepted (it is
not — acceptance is F-0, in `ARCHITECTURE_DECISIONS.md`); that any AD is
written; that Phase F runs are reproducible (F-C1 is precisely the
statement that they are not); that this amendment is a review of any
level above Level 1; that discharging F-C1 … F-C4 discharges Acceptance
Review C-1 … C-12, which remain open by their own terms.
