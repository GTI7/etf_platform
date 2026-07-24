# Phase 4 / Phase F — Architecture Resolution

**Date filed:** 2026-07-24
**Repository state resolved against:** canonical `D:\Claude\etf_platform`,
`master`, HEAD `58908fe` (`phase4-phase-e-complete`), working tree clean
apart from the Phase F proposal and this document.
**Resolves:** `docs/PHASE_4_PHASE_F_RESEARCH_EXECUTION_ENGINE_PROPOSAL.md`
(the "Proposal").
**Status:** architecture resolution. Not an ADR, not an amendment to an
accepted ADR, not code.

**Review level: Level 1 — self-review** (`RESEARCH_GOVERNANCE_STANDARD.md`
§4). The word *independent* is not used of this document, and §1.2 states
precisely what that costs.
**Amended 2026-07-24**, same Level 1 pass, by finding **R-1a** (§2) and
**AD-067** (§5): an architectural clarification only — *package
boundaries are not authority boundaries*. It is numbered **R-1a, not
R-8**, because §1.2 reserves R-8 onward for the independent review's
findings and that reservation is not consumed by a self-review. The
amendment changes **no accepted AD**, adds **no mechanism**, and changes
**no code**. **F-0 remains blocked** on the independent review.

**Corrected 2026-07-24 — governance audit pass, editorial, applied after
R-1a / AD-067.** Four corrections to how R-1a's and AD-067's content is
*worded*, none of them a new finding and none of them a design change:

1. **The containment claim is restated by scope, not by count.** Every
   description of AD-063 enumeration (a) as "a list of three names" is
   withdrawn. Decision Chain containment is **module-scoped over
   `core.governance.decision_recorder`'s export surface** — every symbol
   that module exports, whatever their number, present and future. At
   HEAD `58908fe` that surface is **fourteen public names**, not three;
   the three previously recited were examples, and reciting them as the
   rule understated it.
2. **Three boundary clarifications** are stated explicitly rather than
   left inferable: package boundaries are not authority boundaries;
   enumerations are exhaustive only over **declared surfaces**; and
   authority reachability can change through **relocation, re-export, or
   a new access path** (§2, R-1a ruling items 6–7).
3. **Four amendment triggers** are named, so the re-derivation AD-067
   already requires of a human reader has stated occasions rather than
   being left to notice (§2, R-1a ruling item 8).
4. **Repository census claims are dated to HEAD `58908fe`**, since every
   one of them is a count that a later commit can change.

This pass consumes **no finding number** — R-1a stands as the finding and
**R-8 onward remains reserved** for the independent review. It adds **no
mechanism, no runtime policy framework, and no code**; it edits **no
accepted AD** — AD-047 … AD-060 are untouched — and **F-0 remains
blocked** on the independent review.

---

## 0. Governing principle

> The repository must never record a claim stronger than the mechanism
> that enforces it.

This document is subject to that principle in the same way the Proposal
is. Where a resolution below weakens a claim rather than strengthening a
mechanism, it says so in those words.

---

## 1. What this document is

### 1.1 What it does

It resolves seven blocking findings against the Proposal, each
**established directly from the repository at HEAD `58908fe`** and cited
to `file:line`. Every resolution is either (a) a correction to a
Proposal statement that is **false at HEAD**, (b) a disclosure the
Proposal owes and does not make, or (c) an ownership assignment for an
act the Proposal leaves unowned.

It also rules on the Proposal's own three §9 open questions, and restates
the required content of AD-061 … AD-065 with the resolutions folded in,
plus two additional ADs (**AD-066**, **AD-067**) that the findings force.

### 1.2 What it does not do, and the disclosure that goes with it

**The independent architecture review this resolution was commissioned
against is not present in the repository, in this session's context, or
anywhere on disk.** Searched: the working tree (`git status
--untracked-files=all` reports the Proposal as the only untracked file),
`docs/` in full, the session scratchpad, and `D:\Claude\` at depth 1. No
review artifact exists.

Therefore:

- **This document does not discharge the findings of an independent
  review.** It cannot. Resolving findings that were never read, and
  recording them as resolved, would be the precise failure mode the
  governing principle exists to prevent — a resolution record stronger
  than the review that produced it.
- **The findings resolved below are this pass's own**, at Level 1. They
  are not attributed to an independent reviewer, and this document must
  not be cited as evidence that Phase F has cleared independent review.
- **F-0 remains blocked on the independent review**, not on this
  document. When the review is supplied, its findings are folded in as a
  §2 continuation (R-8 onward) and this document's review level is
  restated at the top; it is not silently upgraded.

---

## 2. Findings and rulings

### R-1 (blocking) — AD-063's rule does not deliver the property §2.5 and F-6 claim

**Finding.** `Authorization` is defined at
[`core/research/lifecycle.py:87`](core/research/lifecycle.py:87), inside
the one module that imports Governance at module scope
([`lifecycle.py:48`](core/research/lifecycle.py:48), `from
core.governance.decision_recorder import …`).

The Proposal's §3.7 gives both `TransitionRequest.authorization:
Authorization` and `TransitionComposer.compose(…, authorization:
Authorization, …)`. Any module declaring those must import
`core.research.lifecycle`, and importing `core.research.lifecycle`
imports Governance transitively **at runtime**.

Two Proposal statements are therefore false as written:

| Proposal | Statement | Status at HEAD |
|---|---|---|
| §2.5, bullet 4 | `transition_port.py` … "**No Governance import**" | **True only of direct imports.** Governance is reached transitively through `lifecycle`. |
| §7, F-6 exit | "**the test path imports no Governance at all**" | **False, and unachievable.** Constructing a `TransitionRequest` imports `lifecycle`, which imports `decision_recorder`. |

**Ruling.** The mechanism is a *direct-import* rule. The claim is
restated to match it; the mechanism is not inflated to match the claim.

1. **AD-063's rule is restated in these words:** *No module added by
   Phase F contains a `core.governance.*` import statement.* The
   preceding formulation ("both a `core.validation.*` and a
   `core.governance.*` import") is retained as a **derived consequence**,
   not as the primary rule — Phase F modules import Validation freely, so
   forbidding the Governance import alone is the stronger and the
   checkable statement.
   **[Superseded in part by R-1a.]** This wording takes a *package path*
   as a proxy for *authority*, and the proxy does not hold: it forbids
   `archive_writer.py`, which §3.5 requires to call
   `write_canonical_jsonl`. R-1a restates the rule by **symbol**. R-1's
   items 2, 3 and 4 stand unchanged.
2. **AD-063 must carry this disclosure verbatim in substance:** *Phase F
   modules reach `core.governance` transitively via
   `core.research.lifecycle`, which is where `Authorization` is defined.
   The rule prevents a Phase F module from **naming** `DecisionRecorder`,
   `DecisionRecord`, or `read_chain`. It does **not** prevent the
   Governance package from being imported into the process, and it must
   never be cited as if it did.*
3. **§2.5 bullet 4 is amended** to "No direct Governance import;
   Governance is reached transitively through `core.research.lifecycle`,
   which is where `Authorization` lives — see AD-063's disclosure."
4. **F-6's exit criterion is struck and replaced** with: *the runner's
   test path names no Governance symbol and constructs no
   `DecisionRecorder`; the composer is a fake.* This is what F-6 can
   actually prove.

**What survives untouched.** AD-059's literal sentence is unaffected:
`core/research/lifecycle.py` remains the only module in `core/` importing
both domains, and the only place a `GateRunRecord` is bound to a
`DecisionRecord`. R-1 corrects a Phase F claim, not an accepted AD.

**Alternative considered and not taken.** Moving `Authorization` to
`core/shared/` would make §2.5's original wording literally true. It is
**rejected for Phase F**: `lifecycle.py` is a frozen Phase E module
(Proposal §0), and relocating an accepted type to make a new document's
sentence true is the wrong direction of repair. Recorded here as a
deferred option so it is not rediscovered as novel.

---

### R-1a (blocking) — R-1's restated rule forbids a module Phase F requires, because it treats a package boundary as an authority boundary

**Numbering.** R-1a, not R-8. §1.2 reserves R-8 onward for the
independent review's findings; a self-review does not consume that
reservation. R-1a continues R-1 because it corrects R-1's own ruling.

**Finding — the two statements cannot both hold.**

| Where | Statement |
|---|---|
| R-1 ruling, item 1 | *No module added by Phase F contains a `core.governance.*` import statement.* |
| Proposal §2.5, bullet 2 | `archive_writer.py` **imports `core.governance.canonical_jsonl`** for serialization. |
| Proposal §3.5, §2.6 | `ArchiveWriter` **calls `write_canonical_jsonl`** — "the repository's existing canonicalization rule set, not a second one". |

The rule forbids a module the same design requires, and F-9's AST test —
scoped by R-2 to `core/research/execution/` — would **fail on
`archive_writer.py` the day F-4 lands**. This is not a wording slip that
a narrower phrasing repairs. The rule is unsatisfiable by Phase F's own
§3.5, and the only way to satisfy it as written would be for Phase F to
write a **second canonicalization implementation**, which §2.6 exists to
forbid and which would be a far worse outcome than the import it avoids.

**Finding — why the rule reads that way.** It uses the package path
`core.governance.*` as a proxy for *decision authority*. At HEAD the
proxy does not hold, in both directions:

- **A `core.governance` module can carry no authority.**
  [`canonical_jsonl.py`](core/governance/canonical_jsonl.py) imports
  **nothing from this repository** — `hashlib`, `json`, `pathlib`,
  `typing` only (`canonical_jsonl.py:16-21`). It holds no path, reads no
  chain, makes no decision, and names no record type. It is a
  serialization rule set that happens to live under `core/governance/`.
- **Importing it is already normal, accepted, and frozen.**
  [`core/validation/gate_runner.py:39`](core/validation/gate_runner.py:39)
  imports `core.governance.canonical_jsonl`, and `gate_runner.py:40`
  imports `core.governance.freeze_verifier`, alongside four
  `core.validation.*` imports (`gate_runner.py:42-45`). `gate_runner.py`
  is a module **AD-059 itself names as frozen and untouched**. Also
  importing `canonical_jsonl`: `decision_recorder.py:65`,
  `dataset_snapshots.py:25`, `reconstruction_loader.py:26`.
- **Authority is concentrated in one module, not in the package.**
  **Census, as of HEAD `58908fe` (2026-07-24):** `core/governance/` holds
  **thirteen** modules besides `__init__.py`, and exactly **one** —
  `decision_recorder.py` — can write `transition_records.jsonl`. It is
  also the module that defines `DecisionRecord` and `read_chain`. This is
  a **count at a commit**, not a structural invariant: a later commit can
  change it, which is why the amendment triggers below exist.
- **`core/governance/__init__.py` re-exports nothing, as of HEAD
  `58908fe`.** It contains prose only — no `import`, no `from`, no
  `__all__`. Every symbol in the package is therefore reachable only by
  its own module path today, and enumeration (a) below is written on that
  basis.

**Ruling.**

1. **Package boundaries are not authority boundaries.** This is a
   clarification of what the existing rules already mean, not a new rule.
   `tools/check_import_boundaries.py` governs *import direction* across
   the §5 domain table, at package granularity. AD-059 and AD-063 govern
   *who may bind a `GateRunRecord` to a `DecisionRecord` and who may
   append to the chain*. These are different questions, and a rule
   written in package paths cannot answer the second one.
2. **AD-063 is a rule about Decision Chain authority only**, and is
   restated by **symbol**, in two literal enumerations:
   > **(a)** No module added by Phase F names **any symbol exported by
   > `core.governance.decision_recorder`**. The rule is **module-scoped
   > over that module's export surface** — every public name it exports,
   > whatever their number, present and future — not a list of selected
   > names.
   > **(b)** The **only** `core.governance` module a Phase F module may
   > import is `core.governance.canonical_jsonl`. `archive_writer.py`
   > does, and that import is **not** an authority crossing.

   **Scope, stated as scope rather than as a count.** At HEAD `58908fe`
   `decision_recorder` declares **no `__all__`**, so its export surface
   is its public module-level names: **fourteen** of them —
   `TRANSITION_RECORDS_FILENAME`, `ARCHIVE_MANIFEST_FILENAME`,
   `MissingArchiveManifestError`, `ProjectIdentityMismatchError`,
   `ChainInvalidError`, `ChainPrefixMismatchError`, `AuthorizationRecord`,
   `GateOutcome`, `DecisionRecord`, `hash_record`, `read_chain`,
   `verify_chain_intact`, `verify_chain_anchored`, `DecisionRecorder`.
   That census is **dated to HEAD `58908fe`** and is illustrative of the
   surface, never a substitute for it: (a) binds to the module, so a
   symbol added to `decision_recorder` tomorrow is inside the rule the
   day it is added, with no edit to (a).
   R-1's item 2 disclosure named `DecisionRecorder`, `DecisionRecord` and
   `read_chain`. **Those were examples, and any reading of them as the
   rule's extent is withdrawn here** — they are three of fourteen at HEAD
   `58908fe`. R-1a makes the rule say, by scope, what its own disclosure
   was reaching for by example.
3. **AD-063 says nothing about the rest of `core/governance/`.** The
   Data-domain and reproduction modules there — **eleven of them as of
   HEAD `58908fe`**: `dataset_snapshots`, `reconstruction_loader`,
   `dataset_manifest`, `calendar_definitions`, `network_guard`,
   `pinned_worktree`, `identity_verification`, `independence_linter`,
   `reproduction_record`, `reproduction_runner`, `freeze_verifier` — are
   outside AD-063's subject. Rule (b)'s allow-list of **one** keeps them
   out of Phase F without AD-063 having to make any claim about them, and
   AD-063 must not be cited as governing them. The count is a **census at
   a commit**; the ruling does not depend on it, because (b) admits one
   named module and excludes the rest by default however many they are.
4. **No new mechanism.** F-9's single AST test remains the only
   mechanism; **only its predicate changes**, from a path prefix to the
   two enumerations above. Explicitly rejected as the wrong repair, and
   recorded so they are not rediscovered as novel: an authority registry
   or `core/governance/authority.py`; a classifier that derives which
   symbols carry authority; a runtime policy check; any decorator,
   marker, or metadata scheme. Each would be a framework standing in for
   **one module's export surface and one permitted module path**, and
   Phase F is not authorized to build one (Proposal §7.1's closing
   prohibition).
5. **New AD-067** (§5): the disclosure that the enumerations are
   hand-maintained and derived from nothing.
6. **Three clarifications, stated so they are not inferred.** Each is a
   statement about what the existing rules mean; none adds a rule.
   - **Package boundaries are not authority boundaries.** Restated from
     item 1 because the other two clarifications are read against it.
     Membership in `core/governance/` neither confers authority nor
     withholds it; authority is held by named symbols and by
     construction and call.
   - **Enumerations are exhaustive only over declared surfaces.**
     Enumeration (a) is exhaustive over `decision_recorder`'s export
     surface, and (b) over `core.governance`'s **module** surface as
     reached by direct module-path import. Neither is exhaustive over
     *authority*. Anything that carries Decision Chain authority without
     appearing on one of those two declared surfaces is outside both
     enumerations and outside what F-9's AST test can see, and the test
     passing says nothing about it.
   - **Authority reachability can change without either enumeration
     changing.** Three ways, all of which leave (a) and (b) textually
     correct and materially defeated: **relocation** of a chain-authority
     symbol out of `decision_recorder` into another module; **re-export**
     of one through a package `__init__.py` or any other alias, making it
     reachable under a path neither enumeration names; and a **new access
     path** to the chain — a second module that opens
     `transition_records.jsonl`, or an existing permitted module widened
     to reach it. Reachability is a property of the code at a commit, not
     of the enumerations, and the enumerations do not track it.
7. **Four amendment triggers.** AD-067 already requires that the
   enumerations be re-derived by a human reader. These are the **stated
   occasions** on which that re-derivation is owed, so it is not left to
   whether someone happens to notice. On any of them, **AD-063's
   enumerations and AD-067's disclosure must be re-derived and amended
   before F-9's test is cited as evidence of containment**:
   - **A new module is added under `core/governance/`.** Enumeration (b)
     excludes it by default — the safe direction — but the census in
     AD-067 and item 3 above is stale from that commit, and if the new
     module carries chain authority, (a) does not reach it.
   - **A chain-authority symbol is relocated** out of
     `core.governance.decision_recorder` — anything that writes, reads,
     hashes, or verifies `transition_records.jsonl`. Enumeration (a)
     binds to the module, so relocation moves the symbol out of the rule
     while the rule's text is unchanged and the AST test still passes.
   - **Any `__init__.py` re-export appears** that makes a
     `decision_recorder` symbol reachable under a different path. At HEAD
     `58908fe` `core/governance/__init__.py` re-exports nothing, which is
     the condition (a) is written against; a re-export creates an import
     form the enumeration does not name.
   - **`canonical_jsonl`'s access is widened** — it acquires a chain
     path, a chain-path constant, a default path, chain-awareness, or any
     repository import. Enumeration (b) permits it **because** it holds
     no path and imports nothing from this repository
     (`canonical_jsonl.py:16-21`, five module-level functions at HEAD
     `58908fe`); widening it turns the one permitted import into an
     authority crossing while (b) still reads as correct.

   These triggers are **amendment obligations on the text of AD-063 and
   AD-067, discharged by a human reader**. Phase F ships nothing that
   detects them, and this ruling authorizes nothing that would: no
   watcher, no CI check, no registry, no runtime policy framework. A
   trigger that fires unnoticed is exactly the failure AD-067 discloses,
   and naming the occasions narrows it without closing it.

**What survives untouched — AD-059, literally.** R-1a does **not**
reinterpret AD-059 and does not need to. AD-059's sentence names the
**binding act** — `GateRunRecord` bound to `DecisionRecord` — and grounds
it in its own parenthetical, *"since Governance cannot import
Validation"*, which is a statement about what can be bound, not about
where a module sits. Under R-1a, `core/research/lifecycle.py` remains the
only module in `core/` that names both a Validation type and a
`core.governance.decision_recorder` symbol, and the only place the
binding occurs. Phase F still adds none.

Recorded so a future reader does not "fix" AD-059 on the strength of a
misreading: **if** AD-059's sentence were read as a package-path
predicate, `core/validation/gate_runner.py:39-40` would already
contradict it at HEAD — and AD-059 names `gate_runner.py` as frozen and
untouched in the same breath. The authority reading is the one under
which AD-059 was accepted and is true. **This resolution reads AD-059 as
accepted and amends nothing in it.** (Same for `phase_derivation.py:34`,
which imports `DecisionRecord` and names no Validation type — Governance
without Validation, so no binding point, exactly as AD-059 predicts.)

**What this ruling costs, stated plainly.** The old rule was mechanically
derivable from a path prefix. The new one is not: it rests on **two
declared surfaces a human chose** — one module's export surface for (a),
one permitted module path for (b). Within those surfaces the rule is
exhaustive and needs no maintenance; what is hand-maintained is the
**choice of surface**, which is why the triggers in item 7 exist and why
relocation, re-export, or a widened access path defeats the rule without
contradicting its text. That cost is real, it is the subject of AD-067,
and it is paid because the alternative was a rule that Phase F cannot
satisfy without duplicating the repository's canonicalization.

---

### R-2 (blocking) — the composition root is placed outside the reach of the repository's only mechanical import governance, and this is presented as a justification rather than disclosed as a loss

**Finding.** [`tools/check_import_boundaries.py`](tools/check_import_boundaries.py)
scans `DEFAULT_CORE_ROOT = REPO_ROOT / "core"` and nothing else, and
[`tests/test_import_boundaries.py`](tests/test_import_boundaries.py)
pins the real repository by calling `check_repository()` with no
argument. `adapters/` is **not scanned**. Confirmed at HEAD: `adapters/`
currently imports neither `core.validation` nor `core.governance`
(grep over `adapters/` returns nothing for either).

The Proposal's §2.5 says the composition root "lives **outside `core/`**,
where the §5 dependency table does not reach, because constructing and
wiring domains together is exactly what a composition root is for." The
architectural reasoning is correct. The governance consequence is not
stated: `adapters/research/lifecycle_composer.py` would be **the first
module in `adapters/` to import Governance**, it is the single most
governance-sensitive module Phase F adds, and it would sit in a tree with
**zero** standing import enforcement.

**Ruling.** The placement stands; the silence does not.

1. **AD-062 and AD-063 must both record**, as a disclosed reduction:
   *placing the sole `TransitionComposer` implementation outside `core/`
   removes it from `tools/check_import_boundaries.py`, the repository's
   only standing import-direction enforcement. The compensating mechanism
   is the new Phase F AST test alone. That test is narrower than the
   checker it substitutes for: it pins a named file set, not a tree, and
   a Phase F module added outside that set is not covered.*
2. **The new AST test's scope is fixed by name**, in AD-063 and in F-9's
   exit criterion: it scans `core/research/execution/` **and**
   `adapters/research/`. Scanning only the former would leave the
   composition root unchecked by both mechanisms, which is the failure
   this finding exists to prevent.
3. **`tools/check_import_boundaries.py` is not extended to `adapters/`.**
   Extending it would silently change what the §5 dependency table is
   asserted to cover, and would make every future adapter a boundary
   subject without an AD saying so. This is a deliberate refusal, and
   AD-063 records it as one — together with the fact that it is *why* the
   compensating mechanism is weaker.

---

### R-3 (blocking) — F-7's and §2.5's single-caller claims are false as stated

**Finding.** `compose_transition` is called from
[`tests/test_lifecycle_composition.py`](tests/test_lifecycle_composition.py)
at five sites (lines 175, 229, 497, 521, 542, 563, 651 include calls and
call-shape assertions). The Proposal's F-7 exit criterion — "is the
**only** module in the repository calling `compose_transition()`, pinned
by test" — is false at HEAD and would remain false after Phase F.
§2.5's table row ("Exactly one module *calls* `compose_transition()` …
**strengthened** — exactly one, named, and test-pinned") carries the same
defect.

**Ruling.** Both are restated as: *`adapters/research/lifecycle_composer.py`
is the only **non-test** module in the repository that calls
`compose_transition()`.* The pinning test excludes `tests/` explicitly
and by a stated rule, not by an incidental path filter — a test that
excluded `tests/` implicitly would silently stop covering a test helper
that moved.

This is a wording correction, not a design change. The property Phase F
actually delivers is intact and is worth what the Proposal says it is
worth; it was over-stated by one word.

---

### R-4 (blocking) — two registration acts are unowned, nothing checks that the two registries agree, and F-10 cannot run without both

**Finding.** There are **two** registries, and the Proposal names only
one.

- [`ValidationRegistry`](core/validation/validation_registry.py) maps
  phase → ordered gate **names**. It ships deliberately empty;
  `gates_for_phase` raises `KeyError` for any unregistered phase
  (`validation_registry.py:38`).
- [`GateRunner`](core/validation/gate_runner.py) holds its own
  name → `Gate` **instance** registry; `run_sequence` resolves every name
  against it in an atomic preflight before any gate executes
  (`gate_runner.py:81`, `run_gate` raises `KeyError` at line 78).

The Proposal's §2.1 has the runner *read* `ValidationRegistry`, and its
§2.4 ownership table assigns "deciding what a phase requires" to that
registry. **Nobody is assigned the act of registering** — into either
registry. Three consequences:

1. **F-10 cannot execute** as specified. A genesis transition requires a
   populated `ValidationRegistry` *and* a `GateRunner` holding matching
   gate instances. Neither has a producer in §7.
2. **Nothing checks the two registries agree.** A name in
   `ValidationRegistry` that `GateRunner` does not hold refuses the whole
   call via preflight `KeyError` — correct behaviour, but it is
   **breakage**, and §5's failure table has no row for it.
3. **Registering phase → gate assignments for a real cycle is a
   governance act**, not configuration. It decides what evidence a phase
   requires. §7.1 already forbids "gate determination" as H4 research
   content, which makes the act simultaneously required and prohibited
   with no route between.

**Ruling.**

1. **New AD-066** (§5 below): gate registration is a governance act; the
   two-registry agreement is unenforced and disclosed as unenforced.
2. **§2.4's ownership table gains a row:** *Populating `ValidationRegistry`
   and `GateRunner` — the **human operator**, at the composition root,
   per cycle. Not `ResearchRunner`, which reads both and populates
   neither.*
3. **§5's failure table gains a row 0:** *Registry disagreement (a
   required gate name has no registered `Gate`) — writes performed: none;
   chain: untouched; runner behaviour: `run_sequence`'s atomic preflight
   raises `KeyError` before any gate executes; propagates as breakage.
   No partial evidence set is produced.* This row precedes row 1 because
   it fires earlier than the experiment.
4. **§7.1 gains a clause:** *Registering a phase → gate assignment for a
   real cycle is a governance act with the same standing as producing the
   first real `transition_records.jsonl`: it requires a `decision_log.md`
   entry and a named human. F-10 registers gates **in test fixture code
   only**, against a fixture phase, and Phase F's completion must not be
   recorded as having determined what any phase requires.*

---

### R-5 (required disclosure) — a phase may be registered with zero gates, and the refusal arrives after two archive writes

**Finding.** `register_phase_gates(phase, [])` is legal —
`validation_registry.py:32` applies no non-empty check. The consequence
chain: `gates_for_phase` returns `()` → `run_sequence` runs zero gates
and returns a `GateRunRecord` with no outcomes → both artifacts are
archived (Proposal §2.2 steps 4 and 7) → `compose_transition` reaches
`aggregate_sequence_status`, which raises `EmptyGateSequence` (Proposal
§5.1).

This is the design working: the refusal is correct, arrives before
`append()`, and leaves the chain byte-identical. But the Proposal
nowhere states that an **empty required-gate set is reachable**, and its
§2.2 step 2 annotation ("`KeyError` -> breakage, no writes") implies the
only registry-side failure is an unregistered phase.

**Ruling.** AD-061 must record: *an empty gate list is a legal registry
entry; the resulting run produces two archived artifacts and an
`EmptyGateSequence` refusal. Phase F adds no non-empty check at the
registry, at the runner, or in `build_gate_context` — the refusal already
exists at the correct altitude (`sequence_aggregation`), and a second
check upstream would be a duplicated rule that could drift from it.*
§2.2's step 2 annotation is amended to "unregistered phase → `KeyError`,
breakage, no writes; **registered-but-empty → runs, archives, and is
refused at composition** (R-5)."

---

### R-6 (blocking) — `ArchiveWriter`'s ordered precondition list omits the traversal check, leaving the one ordering that matters unspecified

**Finding.** The Proposal §3.5 lists four preconditions "checked in
order", and separately lists path-traversal refusal under
"Prohibitions" — with no position in the ordering.

This matters mechanically. Precondition 3 is *"`experiment_results/`
exists"*, and its stated purpose is to guarantee that
`write_canonical_jsonl`'s
`path.parent.mkdir(parents=True, exist_ok=True)`
([`canonical_jsonl.py:46`](core/governance/canonical_jsonl.py:46) —
confirmed present, exactly as the Proposal claims) can never be what
creates a directory. That guarantee holds **only if the target path's
immediate parent is `experiment_results/`**. A `filename` containing a
traversal or a separator makes the parent something else, and
precondition 3 then checks a directory the write will not go into.

**Ruling.** The traversal refusal is **precondition 0**, not a
prohibition, and AD-062 records the ordered list as five items:

> 0. `filename` is a single path component: no separator, no `..`, no
>    absolute path, no drive letter. Refused, never normalized.
> 1. `<archive_root>/<project_id>/` exists — never created.
> 2. `archive_manifest.json` exists there and the three-way identity
>    holds, byte-identical.
> 3. `experiment_results/` exists — never created.
> 4. The target file does not exist.

AD-062 must additionally state the reason in the form that survives
re-derivation: *precondition 3's guarantee about `mkdir` is a statement
about the target path's parent, and is void unless precondition 0 has
already established that the parent is `experiment_results/`.* F-4's exit
criterion is amended to require the refusal at precondition 0, asserted
before any filesystem state is consulted.

---

### R-7 (required disclosure) — the frozen instant must be timezone-aware, and nothing in the Proposal says so

**Finding.** Proposal §2.2 step 6 passes `clock=FixedClock(now)`.
[`FixedClock`](core/shared/clock.py:16) raises `ValueError` on a naive
datetime (`clock.py:19`). The Proposal's `ExperimentSpec.as_of:
datetime` and `ExperimentResult.executed_at: datetime` carry no
awareness requirement, and `ResearchRunner`'s injected `Clock` is a
Protocol with no such guarantee.

**Ruling.** Not a design change — a stated precondition. AD-061 records:
*the injected `Clock` must return a timezone-aware datetime; a naive
instant is refused at step 1, before the experiment runs, rather than at
step 6 after the experiment has already executed.* F-6's exit criteria
gain: *a naive-clock run refuses before `experiment.run()` is called.*
Refusing early is what keeps a wasted experiment run from being the
observable symptom of a configuration error.

---

## 3. Rulings on the Proposal's §9 open questions

**Q1 — `experiment_results/` for `reference_h4`.**
**Confirmed at HEAD:** `research_archive/reference_h4/` contains
`archive_manifest.json` and nothing else, while
`research_archive/positive_control_phase3/` does have an
`experiment_results/` directory. The gap is real and exactly as the
Proposal describes it.

**Ruling: the additive `tools/` route, as recommended.** The precondition
is the symmetry with `DecisionRecorder` that makes "creates no directory"
a property of the archive layer rather than of one module; relaxing it
for the convenience of one cycle would trade a structural property for a
one-time cost. The new helper lives beside the existing scaffold, touches
no `core/` module, and creating a directory for `reference_h4` is
recorded as the dated human act it is.

**Q2 — whether `TransitionReceipt` should exist.**
**Ruling: keep it, with AD-065's disclosure, as recommended** — and with
one addition the Proposal does not make. AD-065 must state that
`record_hash` is **recomputable by the operator** from the appended row
via `hash_record`, and that this is what makes emitting it a convenience
rather than a dependency. A receipt the operator *could not* independently
reproduce would be a claim about the chain that only the machine could
make; one they can reproduce is a transcription. That distinction is the
whole of AD-065's defensibility and it should not be left implicit.

**Q3 — whether five ADRs is the right granularity.**
**Ruling: ~~six~~ seven [R-1a].** Five was right for the Proposal's own
content; R-4 adds a claim-sensitive disclosure — that gate registration
is a governance act and that the two-registry agreement is unenforced —
which belongs under its own heading for exactly the reason the Proposal
gave for keeping AD-064 and AD-065 separate. See AD-066 below. **R-1a
adds a second** — that AD-063's authority enumerations are
hand-maintained and derived from nothing — which cannot live inside
AD-063 without the AD asserting a property in one paragraph and
withdrawing its mechanical basis in the next. See AD-067 below.

---

## 4. Consolidated amendments to the Proposal

Applied to `docs/PHASE_4_PHASE_F_RESEARCH_EXECUTION_ENGINE_PROPOSAL.md`
as part of this resolution. Each is a correction or a disclosure; none
changes the architecture.

| # | Proposal location | Amendment | Source |
|---|---|---|---|
| 1 | §2.2 step 2 annotation | registered-but-empty gate list runs and is refused at composition | R-5 |
| 2 | §2.4 ownership table | new row: populating both registries is the operator's, at the composition root | R-4 |
| 2b | §2.5 AD-063 rule block | rule restated **by symbol**, in two literal enumerations; package-path formulation withdrawn as unsatisfiable by §3.5 | R-1a |
| 2c | §2.5 bullet 2 (`archive_writer.py`) | its `core.governance.canonical_jsonl` import stated as **permitted and not an authority crossing** | R-1a |
| 3 | §2.5 bullet 4 | "no *direct* Governance import"; transitive path via `lifecycle` disclosed | R-1 |
| 4 | §2.5 preservation table | single-caller row qualified to "non-test module" | R-3 |
| 5 | §3.5 preconditions | traversal refusal promoted to precondition 0; five ordered items | R-6 |
| 6 | §5 failure table | new row 0: registry disagreement → preflight `KeyError`, no writes | R-4 |
| 7 | §6.1 | AD-063's rule restated; AD-062/063 disclosure clauses; **AD-066 added**; **AD-067 added** | R-1, R-1a, R-2, R-4 |
| 7b | §7 F-0 exit | ~~six~~ **seven** ADs, not five; F-0 marked blocked on the independent review | §1.2, R-4, R-1a |
| 7c | §8 ledger + non-claims | composition-boundary row requalified; ~~three~~ **five** new explicit non-claims | R-1, R-1a, R-2, R-4 |
| 7e | §6.3 AD-059 row | the reading under which AD-059 is preserved stated explicitly; no change to AD-059 itself | R-1a |
| 7d | §9 | the three open questions marked ruled-on, with the rulings named and the review level restated | §3 |
| 8 | §7 F-4 exit | precondition-0 refusal asserted before filesystem state is consulted | R-6 |
| 9 | §7 F-6 exit | unachievable "imports no Governance" clause struck and replaced; naive-clock refusal added | R-1, R-7 |
| 10 | §7 F-7 exit | "only **non-test** module calling `compose_transition()`" | R-3 |
| 11 | §7 F-9 exit | AST test scope fixed by name to include `adapters/research/` | R-2 |
| 11b | §7 F-9 exit | AST test **predicate** corrected from path prefix to the two symbol enumerations | R-1a |
| 11c | §7 F-4 exit | `archive_writer.py`'s permitted `canonical_jsonl` import asserted, not merely tolerated | R-1a |
| 12 | §7 F-10 exit | registries populated in fixture code only | R-4 |
| 13 | §7.1 | new prohibition: registering real phase → gate assignments is a governance act | R-4 |
| 14 | §2.1, §2.5 AD-063 rule block, §6.1 AD-063 / AD-067 rows, §7 F-9 exit, §7.1, §8 ledger | enumeration (a) restated as **module-scoped over `decision_recorder`'s export surface**; every "list of three names" formulation withdrawn | audit |
| 15 | §2.5, §6.1 AD-063 / AD-067 rows | the three clarifications stated explicitly: package boundaries are not authority boundaries; enumerations are exhaustive only over **declared surfaces**; authority reachability can change through **relocation, re-export, or a new access path** | audit |
| 16 | **new §7.2**, §6.1 AD-067 row | the **four amendment triggers** — new `core/governance/` module; chain-authority symbol relocation; `__init__.py` re-export; widened `canonical_jsonl` access — as human amendment obligations, with nothing built to detect them. A new subsection, since §7.1 is a prohibition list and a standing obligation is not a prohibition | audit |
| 17 | §2.5, §6.1 AD-067 row, §8 ledger | every repository census claim **dated to HEAD `58908fe`** and marked as a count at a commit | audit |

---

## 5. Required AD content, as resolved

AD-061 … AD-065 are the Proposal's §6.1 required content **plus** the
clauses below. AD-066 and AD-067 are new. **None of these is accepted by
this document** — acceptance is F-0, and F-0 remains blocked per §1.2.

| # | Added or changed required content |
|---|---|
| **AD-061** | R-5's empty-gate-list disclosure; R-7's timezone-aware clock precondition, refused at step 1 |
| **AD-062** | R-2's disclosed loss of `check_import_boundaries` coverage and the named-file-set weakness of its substitute; R-6's five ordered preconditions and the statement that precondition 3's `mkdir` guarantee is void without precondition 0 |
| **AD-063** | **R-1a's restated rule, which supersedes R-1's**: the rule is about **Decision Chain authority only**, and is two literal enumerations — *(a)* no Phase F module names any symbol exported by `core.governance.decision_recorder`, **module-scoped over that module's entire export surface** (fourteen public names at HEAD `58908fe`, no `__all__` declared; the surface, not any recital of it, is the rule, and **AD-063 must not be worded as "three names" or as any other count**); *(b)* the only `core.governance` module a Phase F module may import is `canonical_jsonl`, which `archive_writer.py` does and which is **not** an authority crossing. Plus: the statement that **package boundaries are not authority boundaries**, and that AD-063 makes no claim about the remaining eleven `core/governance/` modules **as counted at HEAD `58908fe`**; the statement that **the enumerations are exhaustive only over their declared surfaces**, never over authority; R-1's transitive-reach disclosure; R-2's AST-test scope fixed by name to `core/research/execution/` **and** `adapters/research/`; R-2's deliberate refusal to extend `tools/check_import_boundaries.py`; R-3's "non-test module" qualification. AD-063 must **not** be worded as a package-path rule, and must not be cited as one |
| **AD-064** | unchanged from Proposal §6.1 — no finding touched it |
| **AD-065** | Q2's addition: `record_hash` is operator-recomputable via `hash_record`, and that is what makes it a transcription rather than a dependency |
| **AD-066** *(new)* | **Gate registration is a governance act, and two-registry agreement is unenforced.** Must record: the two registries and what each holds; that `ResearchRunner` reads both and populates neither; that **nothing checks they agree**, and a disagreement surfaces as a `run_sequence` preflight `KeyError` — breakage, before any gate executes, with no partial evidence set; that registering a real phase → gate assignment requires a `decision_log.md` entry and a named human, with the same standing as producing the first real `transition_records.jsonl`; that Phase F ships **no** registry-consistency check, because the check would have to name gates and Phase F is not authorized to determine what any phase requires |
| **AD-067** *(new)* **[R-1a]** | **Policy authority composition: package boundaries are not authority boundaries, and the authority enumeration is hand-maintained.** Must record: **(1)** that the repository holds **two different kinds of boundary** — *import-direction* boundaries, enforced by `tools/check_import_boundaries.py` over the §5 domain table at **package** granularity and mechanically derived from a path; and *authority* boundaries — who may bind a `GateRunRecord` to a `DecisionRecord`, who may append to `transition_records.jsonl`, who may decide — which are held by **named symbols** and by **construction and call**, never by location. **(2)** The evidence, **dated to HEAD `58908fe` and recorded as a census at that commit rather than as an invariant**: thirteen modules besides `__init__.py` live under `core/governance/` and exactly **one**, `decision_recorder.py`, can write the chain; `core/governance/__init__.py` re-exports **nothing**; `canonical_jsonl.py` imports nothing from this repository, exposes five module-level functions, and is already imported by the frozen Validation module `gate_runner.py:39`. **(3)** That authority is conferred by construction and call: `adapters/research/lifecycle_composer.py` holds Decision Chain authority because it **constructs `DecisionRecorder` and calls `compose_transition()`**, not because of where it sits — and it sits outside `core/`, where the package checker does not reach (R-2); conversely `archive_writer.py` imports a `core.governance` module and holds **no** authority whatever. **(4) The disclosure proper:** AD-063's containment is **module-scoped over `decision_recorder`'s export surface** — exhaustive **within** that surface without maintenance, and **derived from nothing outside it**. Enumeration (b) is an allow-list of one, so any *new* `core.governance` module is excluded by default — the safe direction. Enumeration (a) does **not** follow authority: **reachability can change through relocation, re-export, or a new access path** while (a) and (b) remain textually correct. If a chain-writing or chain-reading symbol is defined **outside** `core.governance.decision_recorder`, if a `decision_recorder` symbol is re-exported under another path, or if `canonical_jsonl` acquires a chain path, the AST test **still passes** and the boundary is unprotected with nothing to say so. **(4a) The four amendment triggers**, on each of which AD-063's enumerations and this disclosure must be re-derived and amended **before F-9's test is cited as evidence of containment**: a **new module under `core/governance/`**; **relocation** of a chain-authority symbol out of `decision_recorder`; **any `__init__.py` re-export** making a `decision_recorder` symbol reachable under a different path; and **widening `canonical_jsonl`'s access** — a chain path, a path constant, chain-awareness, or any repository import. Each is a **human amendment obligation**; nothing detects them. **(5)** That Phase F ships **no** mechanism to close (4) or to notice (4a) — no authority registry, no classifier, no runtime policy check or interceptor, no decorator or metadata scheme, no watcher, no CI check — and that the surfaces are re-derived by a human reader, not by the machine. **(6)** That AD-067 **confers authority on nothing**, adds **no code and no runtime component**, amends no accepted AD, and must never be cited as a policy framework or as evidence that authority is mechanically governed |

**AD numbering confirmed at HEAD.** `docs/ARCHITECTURE_DECISIONS.md`
line 2849 retires AD-052 … AD-055 ("reserved and not available"), with
the dated 2026-07-24 citation corrections for AD-052 → AD-047 part 2 and
AD-055 → AD-049 part 4. The accepted ceiling is AD-060 (line 3039). The
next free number is **AD-061**, and this resolution consumes through
**AD-067**. Re-confirmed after R-1a: `docs/ARCHITECTURE_DECISIONS.md`
contains **no occurrence** of AD-061 … AD-067, so none of the seven
collides with an accepted decision.

---

## 6. Claim-to-mechanism ledger for this resolution

| Claim this document makes | Mechanism | Where it fails if unbuilt |
|---|---|---|
| Every finding is established from the repository, not asserted | Each is cited to `file:line` at HEAD `58908fe` and was read, not inferred | If a citation is stale, the finding is an opinion with a line number |
| Phase F has not cleared independent review | §1.2 states the review was absent and searched-for; the review level in the header is Level 1 | If this document were cited as clearing F-0, the acceptance would rest on a self-review |
| AD-063 delivers what it claims | The claim was lowered to the direct-import rule the AST test can actually check, and then **restated by symbol** so it is also satisfiable by Phase F's own §3.5 **[R-1a]** | If the original wording stood, an AD would assert a runtime property no mechanism holds. If R-1's wording stood, F-9 would fail on `archive_writer.py` and the only way to pass would be a second canonicalization implementation |
| AD-063's rule can be checked at all | One AST test, predicate = two literal enumerations. **No new mechanism was added** **[R-1a]** | If the enumerations were replaced by a classifier or registry, Phase F would have built the framework §7.1 forbids, to stand in for one module's export surface and one permitted module path |
| Decision Chain containment covers every chain symbol the rule can see | Enumeration (a) is **module-scoped over `decision_recorder`'s export surface**, so a symbol added to that module is inside the rule the day it is added | If the rule were written as a recital of selected names, a symbol added to `decision_recorder` would sit outside it while the test still passed. **This is a bound on the surface, not on authority** — relocation, re-export, or a new access path moves a symbol out of the surface and the test still passes (AD-067, triggers) |
| AD-059 is preserved literally, not reinterpreted | R-1a reads AD-059's binding sentence as accepted and shows `lifecycle.py` is still the sole module naming both a Validation type and a `decision_recorder` symbol | If AD-059 were read as a package-path rule, `gate_runner.py:39-40` would already contradict it and someone would "fix" an accepted AD to repair a misreading |
| The composition root is governed | A named AST test covering `adapters/research/`, plus the disclosure that it is weaker than the checker it substitutes for | If the test scopes only `core/research/execution/`, the composition root is covered by nothing |
| Gate registration has an owner | AD-066 assigns it to the human and requires a `decision_log.md` entry | If unowned, a phase's evidence requirements get set by whoever writes the wiring code first |

**What this document does not claim:** that the findings below R-7 do not
exist (no independent review was read — see §1.2); that any AD is
accepted (none is — F-0); that the Proposal's architecture is sound
(eight findings were corrections and disclosures, none of them structural,
but a Level 1 pass is not evidence of soundness); that
`reference_h4` is ready to execute (Q1's directory does not exist yet,
and R-4's registrations have not been made); **that authority is
mechanically governed (it is not — AD-063's containment is scoped to one
module's declared export surface and derives nothing outside it, AD-067);
that the enumerations are exhaustive over authority (they are exhaustive
only over their declared surfaces, and authority reachability can change
through relocation, re-export, or a new access path); that the four
amendment triggers are detected by anything (they are human amendment
obligations, and nothing in the repository fires on them); that any
repository census in this document holds after HEAD `58908fe` (each is a
count at that commit); that this document reinterprets, amends, or
weakens AD-059 or any other accepted AD (it does not — R-1a reads AD-059
as accepted and AD-047 … AD-060 are untouched).**

---

## 7. What remains open

1. **The independent architecture review.** Required for F-0. When
   supplied, its findings continue this document's §2 numbering from R-8
   and the header's review level is restated. **R-1a did not consume
   R-8**; the reservation is intact.
2. **F-0 acceptance of AD-061 … AD-067.** Blocked on (1). Seven ADs, not
   six — R-1a forced AD-067.
3. **Q1's `experiment_results/` creation for `reference_h4`** — a dated
   human act, unperformed.
4. **R-4's registry population for any real cycle** — a governance act,
   unperformed and, per §7.1 as amended, not Phase F's to perform.
5. **The four amendment triggers stand open indefinitely** (R-1a ruling
   item 7). They are not tasks to complete but standing obligations: on a
   new `core/governance/` module, a relocated chain-authority symbol, an
   `__init__.py` re-export, or a widened `canonical_jsonl`, AD-063's
   enumerations and AD-067's disclosure must be re-derived and amended
   before F-9's test is cited as evidence of containment. **Nothing
   detects them**, and nothing in this resolution is authorized to.
