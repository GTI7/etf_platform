# Phase 4 / Step 9 — Architecture Resolution

**Status: resolution. No code is introduced or modified by this
document. No existing file is edited by it.**

**Inputs reconciled.**
`docs/STEP_9_VALIDATION_ORCHESTRATION_PROPOSAL.md` (the proposal) and
`docs/STEP_9_ARCHITECTURE_RECONCILIATION_REVIEW.md` (the adversarial
review, verdict C+ / return for correction).

**Baseline.** `2c7fb2c`, tag `phase4-final-before-h4-20260722`. Every
factual claim in this document was re-verified against that tree by
direct reading, independently of both input documents. Where this
document affirms a review finding, it affirms it because the tree was
re-checked — not because the review asserted it. Where the review's
diagnosis was right but its remedy was not, that is recorded as a
partial acceptance with the remedy replaced (§2).

**Standing constraint on this document.** The review's central
diagnosis is that the proposal's characteristic failure mode is *a
claim being stronger than the mechanism behind it*. That diagnosis
applies to the review as well, and §2 records three places where it
does. §5 exists so the same failure cannot re-enter through this
document: every claim Step 9 is permitted to make is listed against the
mechanism that backs it, and no claim without a mechanism is admitted.

---

## 0. Independent verification log

| Claim under review | Source checked | Result |
|---|---|---|
| `verify_freeze` returns `VERIFIED` for an empty `covered_paths` | `core/governance/freeze_verifier.py:154-170` | **Confirmed by reading.** `errors`/`drifted` are populated only inside `for path in paths`. Empty iterable ⇒ both empty ⇒ `else: status = VERIFIED`. No emptiness guard exists anywhere in the function |
| No guard or test pins this behavior | `core/`, `tests/` | **Confirmed.** No emptiness check on `covered_paths` in either tree |
| Shared kernel is exempt as an import *source*, not only as a target | `tools/check_import_boundaries.py:94-98, 133-136` | **Confirmed, and narrower than the true hole — see §1.4** |
| `ALLOWED_DEPENDENCIES["governance"] == {"data"}` | `tools/check_import_boundaries.py:64` | **Confirmed verbatim** |
| §5's table permits Validation → Governance | `docs/PLATFORM_ARCHITECTURE_V1.md:505-509` | **Confirmed** — `| Validation | ✅ | ✅ | ✅ | — | ✕ | ✕ |` |
| §5's prose forbids it four paragraphs later | `docs/PLATFORM_ARCHITECTURE_V1.md:537-539` | **Confirmed verbatim** — "Validation and Governance, both Layer 1, never call each other" |
| Only Research may aggregate gate outcomes | `docs/PLATFORM_ARCHITECTURE_V1.md:245-247` | **Confirmed verbatim** — "only Research aggregates gate outcomes into a" terminal decision |
| AD-045 is terminal and states its own re-opening condition | `docs/ARCHITECTURE_DECISIONS.md:1150-1157` | **Confirmed verbatim**, including "not a resumption of this one" |
| AD-044 names `GateRunner` as the trigger for `GateContext` | `docs/ARCHITECTURE_DECISIONS.md:1066-1072` | **Confirmed verbatim** |
| Migration Plan §10 item 4 contains a replacement clause | `docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md:399-402` | **Confirmed verbatim** — "not hand-authored into a `decision_log.md` after the fact" |
| §10 forbids rounding a partial result up | same, :410-415 | **Confirmed verbatim** |
| No hash chain exists in Phase 4 governance | `core/governance/*.py` | **Confirmed.** Search for `prev_hash` / `previous_hash` / `chain` returns nothing |
| `ReviewLevel` exists only as a sketch | repository-wide | **Confirmed** — one occurrence, `PLATFORM_ARCHITECTURE_V1.md:210` |
| No `LifecyclePhase`, no `advance_phase()` | `core/` | **Confirmed**, and stated by `core/validation/__init__.py` itself |
| Standard §2 defines exactly 8 phases, Hypothesis → Archive | `docs/RESEARCH_GOVERNANCE_STANDARD.md:80-87` | **Confirmed** |
| Three registered projects, none named `h4` | `core/research/historical_backfill.py:43,59,76` | **Confirmed** — `reference_v1`, `reference_v2_h1`, `reference_h3` |
| `research_archive/` holds a **fourth** directory | `research_archive/` | **Confirmed — not found by either input document.** `positive_control_phase3` exists on disk and is **not** a registered project. See §1.3 |
| No relative imports exist under `core/` | `core/` | **Confirmed** — relevant to §1.4, which is safe to tighten |

---

## 1. Accepted findings

All five findings named in the review are accepted. Three are accepted
as stated; two are accepted in diagnosis with the remedy corrected
(cross-referenced to §2).

### 1.1 PR0 freeze-verification hole — ACCEPTED IN FULL

`verify_freeze('<ref>', [])` returns `VERIFIED`. This is live at the
baseline, unguarded and untested, and it is load-bearing rather than
cosmetic:

- AD-043 makes a gate render `AMBIGUOUS` when verification is not
  `VERIFIED`. An empty covered-path set returns `VERIFIED`, so a gate
  with **zero freeze coverage** may legitimately render `PASS`.
- The proposal's INV-3 is therefore **vacuously satisfiable**, and so is
  the §6.6 pre/post bracket: both ends return `VERIFIED` on an empty
  set and agree with each other perfectly while proving nothing.

The disclosure obligation is independent of Step 9 and is not
discharged by building anything. The remediation record naming this
(`docs/PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md`) was
destroyed in the 2026-07-21 incident and exists in no reachable ref.
The repository today holds the hole, no fix, no test, and no
disclosure. Re-issuing that disclosure is the first obligation of
Step 9 and it precedes all other work.

**Accepted with a correction to the remedy's claim strength — see §2.3.**
The guard (reject an empty covered-path set in new Validation code) is
accepted. The implied claim that a *non-empty* set makes verification
meaningful is not.

**INV-3 is restated** as: *no gate executes against a freeze
verification whose covered-path set is empty, unresolved, or drifted,
and no `VERIFIED` result is admitted as evidence without its
covered-path list recorded alongside it.*

### 1.2 DecisionLogger clarification — ACCEPTED IN FULL

The proposal's "AD-050 supersedes AD-045 narrowly" framing is rejected;
the review's "clarify, do not supersede" is adopted, on both of its
grounds, both of which the tree confirms:

- **On the facts.** AD-045's decision — *"No `DecisionLogger`
  implementation is planned; `core/governance/` is not expanded by this
  AD"* — remains **literally true** after `DecisionRecorder` ships. No
  `DecisionLogger` exists; no code writes `decision_log.md`;
  hand-authorship stays canonical. A decision that has not been
  contradicted has not been superseded. AD-045 pre-authorized this exact
  path in its own final paragraph, and closed it with *"not a resumption
  of this one"* — which is an instruction to make a **new** decision,
  not to overturn the old one.
- **On the hazard.** An AD index reading "AD-045 — superseded" tells
  every future reader that the no-automated-decision-logging decision
  was overturned. The next component wanting to write a judgment field
  cites it as precedent. The supersession language is itself the
  governance risk.

Two structural requirements are accepted with it:

1. **"Mechanical" must be enforced structurally, not by review.** The
   record is a frozen dataclass with a **closed** field set, and a test
   pins the exact serialized key set. Adding a field fails a test and
   forces an AD. Prose whitelists do not survive a v2 that adds `notes`.
2. **Transcription, not certification.** Governance cannot import
   Validation, so it cannot re-derive a gate outcome it stores. A
   Governance artifact asserting "gate X passed" reads to an auditor as
   Governance vouching for gate X. The artifact must self-document as a
   transcription with integrity guarantees: it certifies that retained
   bytes were not altered, never that the transcribed content is true.

**Migration Plan §10 item 4 is permanently partially met, by design.**
Item 4's replacement clause is rejected on AD-038/AD-045 grounds.
Step 10's retrospective records it as *mechanical record present,
replacement of hand-authorship deliberately declined*. Rounding it up to
"met" is the violation §10 itself names.

### 1.3 Missing research cycle identity model — ACCEPTED AND EXPANDED

Accepted as stated: the repository has **infrastructure lifecycle
states only** (`ProjectLifecycleState` = ACTIVE/FROZEN/ARCHIVED), no
`LifecyclePhase`, no `advance_phase()`, and H1–H4 are hypothesis
identities rather than phases. Two axes, not one.

The review's correction that **H4 is not a registered project** and must
be registered under a convention reconciled with the existing three
(`reference_v1`, `reference_v2_h1`, `reference_h3` — none of which use
bare H-numbering) is accepted and is on the critical path.

**Expanded on three points neither input document reached:**

1. **`Project` already claims to be the cycle record, and the claim is
   not true.** `core/research/project.py:3` states `Project` "gives
   every research cycle -- past or future -- one stable record."
   But `reference_v1` and `reference_v2_h1` are **two Projects that are
   successive cycles of one research lineage**, and `reference_h3` had
   multiple internal attempts (`attempt_001_specification.md`). The
   current model therefore has one identifier doing the work of three
   distinct things: **lineage**, **cycle**, and **attempt**. Step 9 must
   not deepen that conflation by hanging phase state off it without
   first naming which of the three a phase belongs to. It belongs to the
   **cycle**.
2. **The registry and the archive already disagree.**
   `research_archive/` contains four project directories; three are
   registered. `positive_control_phase3` exists on disk with no
   `Project` record. No invariant binds the two, and nothing detects the
   divergence. Registering H4 without addressing this adds a fifth
   directory to an already-unreconciled set.
3. **Phase must not be stored on `Project`.** The review proposed a new
   `current_phase` field plus an INV-12 exception (its AD-054). That is
   **rejected** — see §2.1. Phase is derived from the transition record
   chain.

### 1.4 GateRunner layering correction — ACCEPTED AND EXPANDED

Accepted as stated, on four counts, each independently verified:

- **The aggregate verdict moves out of Validation.**
  `PLATFORM_ARCHITECTURE_V1.md:245-247` assigns cycle-level aggregation
  to Research by name. The proposal's §6.5(c) placed it inside
  `GateRunner` and §6.7 stored it in the record. `GateRunRecord` stores
  **ordered per-gate statuses only, no aggregate field**; the
  aggregation rule — unchanged, including FAIL-dominates-AMBIGUOUS —
  becomes a pure function in Research. This also strengthens audit
  requirement 3: the auditor recomputes from stored primitives under a
  documented rule instead of trusting a stored aggregate.
- **The §5 table governs over §5's contradicting prose.** The
  contradiction is real and verified at both ends. Three independent
  facts resolve it in the table's favour: the linter implements the
  table, `test_allows_validation_to_import_statistics_and_governance`
  asserts it, and AD-043's gates depend on it. Left unrecorded, an
  auditor can cite the prose to argue every gate in the repository
  violates the layering.
- **`GateRunner` never imports `pinned_worktree`.** The proposal called
  the runner pure and then proposed reusing a component that creates
  worktrees and executes subprocesses. The edge is legal; the design is
  not. Re-running a gate under a pinned worktree is a Research- or
  tools-level concern, out of Step 9 scope.
- **`ReviewLevel` is not introduced.** It exists nowhere but one sketch
  line; `DecisionMetadata.review_level` is a `str`. An enum with one
  consumer, introduced against a frozen baseline type, creating a dual
  vocabulary for a Standard §4 governance concept under Validation's
  ownership, is the abstraction AD-005/AD-040/AD-044 already refuse.
  Review level stays `str`.

**INV-11 is restated** as the review requires: *given identical
`GateContext` inputs, identical freeze verification outcomes, and a
fixed clock, `GateRunRecord` serialization is byte-identical.* The
original wording is false — freeze outcomes derive from
`git status --porcelain` on the working tree, which is not a function of
the context at all — and an invariant that fails its own test gets the
test weakened to pass, which is the worst outcome.

**Expanded: the import linter's hole is strictly larger than the kernel.**
The review found that `core/shared/` is exempt as an import source.
Verified — and the mechanism is broader than the finding.
`_domain_of_file` resolves via `DOMAIN_OF_TOPLEVEL.get(...)`, returning
`None` for **any** top-level package not in that dict, and
`check_repository` `continue`s on `None`. Consequences:

- a **new** top-level package under `core/` (say `core/lifecycle/`) is
  silently exempt in **both** directions until someone remembers to add
  it to the dict — and nothing fails if they do not;
- `_imported_core_modules` only collects imports with `node.level == 0`,
  so a **relative** import (`from ..validation import ...`) inside
  Governance is invisible to the checker. The module's docstring says no
  relative imports exist under `core/`; re-verified true today, which is
  what makes tightening safe rather than disruptive.

The tightening required before any Step 9 domain code lands is
therefore three rules, not one: the kernel may import no `core` domain;
an **unmapped** top-level package under `core/` is an error rather than
an exemption; and relative imports are resolved or rejected. All three
are strict tightenings of `tools/` code, they touch no baseline domain
module, and none can make a currently-passing check fail.

### 1.5 Human authorization requirement — ACCEPTED IN FULL

**`advance_phase()` never advances a project on its own initiative,
under any gate status.** Every transition requires an explicit human
authorization argument. Gate status determines *what kind* of
authorization is required and *what must be disclosed* — never whether
a machine may proceed unattended.

| Sequence status | Automatic transition | Authorization required | Recorded as |
|---|---|---|---|
| **PASS** | Never | Explicit authorization at the Standard §2 level for the target phase | normal record |
| **AMBIGUOUS** | Never | Explicit authorization **plus** a written `decision_log.md` rationale naming each AMBIGUOUS gate and why advancing is justified | `authorized_with_ambiguity`, with the ambiguous gate names stored |
| **FAIL** | Never | Explicit **override**, Level 2 minimum, plus a decision-log entry stating the failed criterion and the grounds for overriding | `override`, stored distinctly — never silently equivalent to a pass |

**Why not auto-advance on PASS.** A runner's PASS means only "the
frozen criteria compared favourably." Standard §2 assigns each
transition a reviewer-independence level, which is a human obligation.
Advancing on PASS satisfies the comparison while skipping the review —
AD-038's trap relocated.

**Why AMBIGUOUS is permitted-with-disclosure rather than blocking.**
AD-043 establishes that AMBIGUOUS means *the gate lacked a trustworthy
frozen basis to decide* — a process gap, not evidence against the
hypothesis. H3 advanced with documented AMBIGUOUS gates. Blocking would
retroactively invalidate that run and would pressure operators to invent
a threshold to clear the block, which AD-043 forbids outright. The
control is disclosure, not prohibition.

**Vocabulary boundary, which nothing in the repository currently
defines.** `GateStatus` is PASS/FAIL/**AMBIGUOUS**; Standard §7's cycle
determination is PASS/FAIL/**INCONCLUSIVE**. These are different
vocabularies at different levels. The sequence aggregate keeps gate
vocabulary and is named `sequence_status`, **never** `verdict`. The
Phase 7 determination is a separate, human-authored Standard §7 value,
and **no code derives the latter from the former**.

**Authorization is recorded, never adjudicated.** Per Standard §4 the
platform stores the declared reviewer level verbatim and does not
validate the independence claim. No record may describe a Level 2
review as "independent" unqualified.

**Two-axis note.** Advancing a phase does not imply changing
`ProjectLifecycleState`. Entering Phase 4 may coincide with `FROZEN`,
but the fields move independently and `advance_phase()` must never
silently mutate the other.

---

## 2. Rejected findings

Rejections are of *remedies*, not of the diagnoses behind them. Each
rejection replaces the mechanism with one that survives the same
adversarial standard the review applied to the proposal.

### 2.1 REJECTED — `Project.current_phase` as a stored field (review AD-054)

The review requires `Project` to gain a `current_phase` field distinct
from `lifecycle_state`, and — noticing this mutates a frozen baseline
dataclass — proposes an explicit INV-12 exception to permit it.

The two-axis reasoning is accepted (§1.3). The storage decision is
rejected.

**Ruling: current phase is *derived* from the append-only transition
record chain. `Project` is not modified. No INV-12 exception is
created.**

Grounds:

1. **A stored field can disagree with the evidence chain, and nothing
   would detect it.** Two writable representations of the same fact,
   with no reconciling invariant, is the divergence §1.3 already
   catches between `research_archive/` and the registry. Step 9 should
   not introduce a second instance of the defect it is fixing.
2. **The failure directions are not symmetric.** If the chain is damaged
   or truncated, a derived phase **under-claims** (it regresses to the
   last provable transition). A stored field **over-claims** — it
   asserts Phase 7 with the supporting evidence gone. Only one of those
   is a safe failure, and it is not the stored one.
3. **The three historical projects have no transition records at all.**
   A stored field forces a value for them, and any value is invented.
   That is precisely the retroactive-fact governance violation
   `project.py:32-41` already refuses for `origin_date` ("inventing one
   would be a governance violation"). A derived phase returns *unknown*
   for them, which is the true answer.
4. **It eliminates the INV-12 exception entirely.** The review's own
   ordering constraints treat baseline changes as serious; an
   architecture that achieves the same outcome without one is strictly
   preferable, and INV-12 survives Step 9 intact.

**Cost, stated honestly.** Reading the current phase requires reading
Governance's artifact from Research (Research → Governance is a legal
edge, already required by the transition flow), and it is O(chain
length) rather than O(1). With four projects and fewer than twenty
transitions, that cost is not real. If a future scale makes it real, a
cache is a derived-value optimization with its own AD — not a reason to
duplicate the source of truth now.

### 2.2 REJECTED — commit-to-git-on-every-append as the chain anchor

The review's §1.4 diagnosis is **accepted in full and is correct**: a
self-contained hash chain cannot prove its own length. Truncating the
tail leaves a perfectly valid chain; so does replacing the file with a
fresh genesis chain. The actor who would author retroactively is the
same actor who can truncate. F-9's claim that chain verification
detects a truncated tail is wrong for whole-record truncation.

Its proposed mechanism — "the artifact is **committed to git on every
append**" — is rejected.

Grounds:

1. **It makes a Governance module a git writer.** The Governance
   domain's read-only posture is currently explicit and load-bearing:
   `core/governance/freeze_verifier.py:41-43` states "nothing in this
   module ever writes, commits, checks out, or resets anything." A
   recorder that commits on every append breaks that property for the
   domain that exists to audit others, and it does so in the component
   whose entire value is being trustworthy.
2. **It perturbs the very input the freeze bracket reads.** `verify_freeze`
   determines drift from `git status --porcelain` on the **working
   tree** (`freeze_verifier.py:122-126`). An append that commits during
   a run mutates exactly that state. The anchor would therefore be
   capable of changing the freeze verification outcome it exists to
   protect — including flipping a pre/post bracket from agreement to
   disagreement, or masking real drift by committing it. An anchoring
   mechanism that can alter the evidence is not an anchor.

**Replacement mechanism**, preserving the requirement and dropping the
hazard:

- every record carries a monotonic `sequence_number` (catches interior
  deletion without rehashing, and makes tail truncation visible against
  any independent witness of the count);
- the corresponding **hand-authored `decision_log.md` entry cites the
  chain head hash and sequence number** at time of writing — the entry
  is written anyway under AD-038, so this adds an anchor at zero new
  machinery and anchors it in a human-witnessed artifact;
- the anchoring **commit is performed by a human, outside any gate
  sequence**, as part of the existing archive discipline — never by the
  recorder, and never while a run is in flight;
- the artifact states the narrow claim in its own header: *this chain
  proves no retained record was altered, reordered, or interior-deleted;
  it does not prove that no record was removed from the tail.*

**Related, accepted:** the review's §1.3 finding that the "Phase 4
dataset chain" the proposal claimed to inherit **does not exist** is
confirmed — no hash chain exists anywhere in `core/governance/`.
`ReproductionRecord` binds a hash *set* within one record; nothing links
record *N* to *N−1*. The chain is **novel work**, must be budgeted and
reviewed as such, and its justification must stand on its own merits
rather than on a borrowed precedent. Overclaim-by-borrowed-authority is
the failure that returned PR0.

### 2.3 REJECTED — "non-empty covered paths" as a sufficient guard

The review's remedy for §1.1 is that `GateContext` construction rejects
an empty `freeze_covered_paths` and the covered-path **count** is stored
so an auditor can see the verification was not vacuous.

The guard is accepted. The claim attached to it is rejected.

**Non-emptiness is necessary and nowhere near sufficient.** A path set
containing one irrelevant file — `README.md` — satisfies the guard, has
a count of 1, and verifies exactly as vacuously as the empty set. An
auditor reading a stored count of 1 learns nothing about whether the
frozen methodology was covered. This is the review's own diagnosed
failure mode — a claim stronger than its mechanism — reproduced inside
the correction for it.

**Ruling:**

- the guard stands (empty set refused, before any gate executes);
- the record stores the **full covered-path list**, not a count, so
  adequacy is inspectable rather than merely non-zero;
- the permitted claim is the narrow one: *these named paths were
  byte-identical to the claimed commit with no drift.* Nothing in Step 9
  may claim that a `VERIFIED` result means "the methodology was frozen."
  Whether the path set covers the methodology is a **human review
  judgment**, disclosed as such, and it is not mechanized by Step 9.

### 2.4 REJECTED — the proposal's "AD-050 supersedes AD-045 narrowly"

Rejected on the review's grounds, affirmed here after verifying AD-045's
text verbatim. See §1.2. Recorded as a rejection so the AD index never
carries a supersession marker against AD-045.

### 2.5 REJECTED — fixing `freeze_verifier.py` inside Step 9

Not a review finding; ruled here to close it. The right long-term answer
to §1.1 is a guard inside `verify_freeze` itself. It does **not** belong
to Step 9: it is a baseline modification, it requires its own governance
ruling, and folding it in would repeat the exact scope violation PR0 was
returned for. Step 9 discloses the hole and guards against it in new
code. The baseline fix is a separate increment with its own AD.

---

## 3. Final architecture decisions

| # | Decision | Binding on |
|---|---|---|
| D-1 | The PR0 freeze-verification deviation is **re-disclosed in writing before any other Step 9 work begins**. The disclosure is a governance obligation, not a task, and is not discharged by building anything | AD-047 |
| D-2 | `verify_freeze` is **not modified** by Step 9. New Validation code refuses an empty covered-path set; the full path list is recorded; the permitted claim is the narrow one (§2.3) | AD-047 |
| D-3 | **AD-045 is clarified, not superseded, not amended, and remains in force in full.** `DecisionRecorder` is a new object satisfying AD-045's own pre-authorized re-opening condition | AD-048 |
| D-4 | `DecisionRecorder` records **mechanical facts only**, in a frozen dataclass with a **closed field set pinned by test**, expressed in primitives and kernel types only. It never sees a `GateResult` and never writes `decision_log.md` | AD-048 |
| D-5 | The recorder is a **transcription with integrity guarantees, never a certification**. It states this in its own artifact header | AD-048 |
| D-6 | Chain tamper-evidence is **externally anchored** via `sequence_number` + head-hash citation in the human decision-log entry + a human-performed commit outside any run. **The recorder never commits** (§2.2) | AD-048 |
| D-7 | Migration Plan §10 item 4 is **permanently partially met by design**; its replacement clause is rejected on governance grounds and disclosed in Step 10 | AD-048 |
| D-8 | **`GateRunner` is built.** AD-040/AD-044's deferral condition is met on its own stated terms by Step 9 §10 item 3 | AD-049 |
| D-9 | **Validation → Governance is a legal edge.** `PLATFORM_ARCHITECTURE_V1.md` §5's table governs over its contradicting same-section prose | AD-049 |
| D-10 | **Validation never aggregates.** `GateRunRecord` stores ordered per-gate statuses only; the aggregation rule is a pure function in Research | AD-049 |
| D-11 | `GateRunner` **never imports `pinned_worktree`**; `ReviewLevel` is **not introduced** (review level stays `str`); INV-11 is restated conditionally | AD-049 |
| D-12 | `sequence_status` (gate vocabulary) and the Standard §7 determination (PASS/FAIL/INCONCLUSIVE) are **separate**. No code derives the §7 value | AD-049, AD-050 |
| D-13 | `LifecyclePhase` lives in `core/shared/`, transcribed exactly from Standard §2, pinned by test — **gated on the linter tightening landing first** | AD-050 |
| D-14 | **Current phase is derived from the transition chain, not stored on `Project`.** `Project` is unmodified; **no INV-12 exception is created** (§2.1) | AD-050 |
| D-15 | Phase belongs to the **cycle**, not the lineage and not the attempt. The identity model names all three before phase state is attached to any of them | AD-050 |
| D-16 | **No transition is ever automatic, at any status.** Status determines required authorization and disclosure, never machine permission | AD-050 |
| D-17 | The import linter is tightened on **three** counts before any domain code lands: kernel imports no domain; unmapped top-level package is an error; relative imports resolved or rejected (§1.4) | AD-049 |
| D-18 | `GateResult`, `GateStatus`, `build_report`, and the two gate functions are **unmodified**. `GateStatus` stays three-valued; a gate crash is an envelope error, never a status | AD-049 |

**Endorsed from the proposal without change**, all re-affirmed here: no
short-circuit; atomic preflight; registry semantics following
`ProjectRegistry` with no module-level singleton; adapters over
unchanged gate functions with an equivalence test; values-only
`GateContext` with no callables or lazy handles; the pre/post freeze
bracket as corrected by §1.1; and the two-layer reproduction model
(measurement vs. verdict), which remains the strongest passage in either
input document.

---

## 4. Final implementation boundary

### 4.1 Must be complete before Step 9 begins — Phase A (documents only, zero code)

Step 9 does not start until every item below is closed **in writing**.

| # | Prerequisite | Done when |
|---|---|---|
| A-1 | **PR0 deviation record re-issued.** New dated disclosure stating that empty-`covered_paths` ⇒ `VERIFIED` is live at `2c7fb2c`, that its original remediation record was destroyed on 2026-07-21 and never restored, and that every `VerificationResult` in the archive is only as strong as the path set it was called with | The disclosure exists in `docs/` and the PR0 ruling is closed or confirmed obsolete |
| A-2 | **AD-047 … AD-050 accepted** (drafts in `docs/PHASE_4_STEP9_DRAFT_ADRS.md`) | Written into `docs/ARCHITECTURE_DECISIONS.md` and accepted |
| A-3 | **Transition/authorization policy decided** (§1.5's table) | Recorded in AD-050, not inside code |
| A-4 | **`sequence_status` ↔ Standard §7 vocabulary boundary decided** | Recorded in AD-050 |
| A-5 | **Chain-anchoring mechanism decided** (§2.2's replacement) | Recorded in AD-048 |
| A-6 | **Research cycle identity model decided** — lineage / cycle / attempt named; H4 naming reconciled with the existing three; the `positive_control_phase3` registry/archive divergence ruled on | Recorded in AD-050 |
| A-7 | **Phase vocabulary source confirmed** — Standard §2's eight phases transcribed exactly, at freeze time, from the Standard | Recorded in AD-050 |
| A-8 | **Machine-artifact location decided** relative to `RESEARCH_ARCHIVE_MANIFEST.md`'s expected layout | Recorded in AD-048 |
| A-9 | **Single-writer enforcement decided** — stated assumption or mechanical lock | Recorded in AD-048 |

**Not a prerequisite, and explicitly deferred:** the `freeze_verifier`
baseline fix (§2.5), which is its own later increment with its own
ruling.

### 4.2 What Step 9 is allowed to implement

Ordered. Phase B may not begin until Phase A closes.

| Phase | Permitted work | Exit criterion |
|---|---|---|
| **B — foundation** | **B-1** tighten `tools/check_import_boundaries.py` on §1.4's three counts, **test first**. **B-2** `LifecyclePhase` in `core/shared/`, pinned to Standard §2 by test. **B-3** `advance_phase()` implementing §1.5's authorization policy, with phase **derived** from the chain; H4 project registration | Escape hatches closed and tested; phase vocabulary pinned; `advance_phase()` has a real caller path; full suite green; boundaries clean |
| **C — DecisionRecorder** | `core/governance/decision_recorder.py`: closed-field frozen record, hash chain, verifier, anchoring per §2.2, canonical-JSONL storage, atomic write. **Never before B-3** | Chain verifies; interior deletion, mutation, reorder and forged-predecessor all detected; **tail truncation detectable via the anchor**; closed key set pinned by test; explicit CRLF fixture; single-writer enforced as decided in A-9 |
| **D — GateRunner** | `Gate` protocol (`review_level: str`), `GateContext` (rejects empty `freeze_covered_paths`, stores the full path list), `GateRunner`, `GateRunRecord` (**no aggregate field**), `ValidationRegistry` phase→ordered gate names, one adapter per existing gate | Adapter equivalence proven against direct calls; empty path set refused before any gate runs; bracket invariant enforced; no aggregate stored; `GateStatus` still three-valued |
| **E — composition** | `core/research/lifecycle.py` — the only module importing Validation and Governance together — plus the aggregation function, plus integration and adversarial tests | H4 traverses one transition end-to-end; aggregation truth table incl. FAIL-dominates-AMBIGUOUS; every failure mode tested; tamper suite incl. **truncation**; **baseline suite passes unmodified** |

**Non-negotiable ordering.** A before everything. B-1 before B-2 (never
open the escape hatch first). B-3 before C (AD-045's condition; AD-048
is void if violated). C and D before E.

### 4.3 What Step 9 may not implement

- Any modification to `freeze_verifier.py`, gate functions, `GateResult`,
  `GateStatus`, `build_report`, or `Project`.
- Any new `GateStatus` member; any aggregate verdict field inside
  Validation; any code deriving a Standard §7 determination.
- Any code writing `decision_log.md`; any judgment, rationale, narrative,
  ranking, or free-text field on the mechanical record.
- Any automatic phase transition, at any gate status.
- Any git write from `core/governance/`; any use of `pinned_worktree`
  from `GateRunner`.
- A `ReviewLevel` type; a `Phase` class hierarchy, transition-table
  object, event bus, phase hooks, or `LifecycleEngine`.
- `ExperimentOrchestrator`, `FreezeManager`, `ArchiveVerifier`,
  `DatasetIntegrityChecker`, `ReproducibilityChecker` — no Step 9
  consumer exists for any of them.
- Historical backfill of gate reviews (AD-044); any
  `experiments/validate_h4_*.py` script (writing one is the documented
  fallback and a disclosable finding, never a shortcut).
- H4's research content. This boundary is infrastructure readiness only.
- **Any edit to an existing test.** An existing test needing
  modification means INV-12 was violated and the work stops.

---

## 5. Claim-to-mechanism ledger

The four constraints the reconciliation was required to guarantee,
each traced to the mechanism that enforces it. A claim with no
mechanism is not admitted.

| Required guarantee | Mechanism | Where it fails if unbuilt |
|---|---|---|
| **No automatic governance decisions** | `advance_phase()` requires an explicit human authorization argument at every status (§1.5); no code derives a Standard §7 determination (D-12); PASS confers no permission | If authorization is defaulted or made optional, D-16 is void and AD-038's trap has been relocated |
| **No Governance → Validation dependency** | `ALLOWED_DEPENDENCIES["governance"] == {"data"}`, `test_detects_forbidden_governance_to_validation_import`, plus the three-count linter tightening (D-17). The record type is primitives-only and never sees a `GateResult`; Research is the only legal binding point | If the record type takes a `GateResult`, the linter fails. If a relative import or an unmapped package is used, the **untightened** linter would not — which is why B-1 precedes all domain code |
| **No replacement of human decision logs** | INV-10 (no code writes `decision_log.md`); closed field set pinned by test; the record is a transcription, self-documented as such; §10 item 4 disclosed as partially met (D-7) | If a `notes`/`context` field appears, the key-set test fails and an AD is forced. Prose whitelists alone would not catch it |
| **No claims stronger than mechanisms** | Every claim below is bounded by what its mechanism actually proves | — |

**The bounded claims, stated at their true strength:**

| Claim Step 9 may make | Claim Step 9 may **not** make |
|---|---|
| These named covered paths were byte-identical to the claimed commit, with no drift | "The methodology was frozen" — path-set adequacy is a human judgment (§2.3) |
| No retained decision record was altered, reordered, or interior-deleted | "No record was removed" — a self-contained chain cannot prove its own length (§2.2) |
| These bytes were transcribed and not since altered | "Gate X passed" as a Governance assertion — Governance cannot re-derive it (D-5) |
| The comparison of these measurements against these frozen criteria was performed correctly | "These measurements are correct" — absent `measurement_provenance`, origin is unverified; a missing reference is an audit finding, never a normal case |
| A hash chain provides tamper-evidence | "…inherited from the Phase 4 chain" — no such chain exists (§2.2) |
| Migration Plan §10 item 4: mechanical record present | "Item 4 met" — the replacement clause is rejected, not satisfied (D-7) |

---

## 6. Status of this document

This resolution supersedes the proposal's §13 AD table and the review's
§6.2 AD table, both of which proposed AD numbering (AD-047 … AD-055)
that was never accepted and that collides across the two documents. The
operative set is the four drafts in
`docs/PHASE_4_STEP9_DRAFT_ADRS.md`, numbered AD-047 … AD-050 against a
verified ceiling of AD-046.

Where this document and either input document disagree, this document
governs. Where it is silent, the review governs over the proposal.

No code was written, no file was modified, and no commit was made in
producing this resolution.
