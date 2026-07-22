# Phase 4 — PR0 Remediation Proposal: `verify_freeze` empty-coverage hole

**Status: proposal. No code is introduced or modified by this document.
No existing file is edited by it. Not implementation-authorized —
awaiting approval.**

**Relationship to Step 9.** `docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`
§2.5 and `docs/PHASE_4_STEP9_DRAFT_ADRS.md` (AD-047, "why the baseline is
not fixed here") both identify this exact defect and both explicitly
defer fixing it, naming the fix "a separate increment with its own AD."
This document is that increment. It does not depend on Step 9 Phase
A–E and Step 9 does not depend on it landing first — the two are
independent, though once this lands it satisfies part of AD-047's
concern for any future Step 9 code that calls `verify_freeze`.

---

## 1. Problem statement

`core/governance/freeze_verifier.py`'s `verify_freeze(commit_ref,
covered_paths)` returns `FreezeStatus.VERIFIED` when `covered_paths` is
empty. A caller can claim a freeze is verified while supplying zero
evidence, and the function will agree.

This is load-bearing, not cosmetic: `AD-043` makes both existing
Validation gates (`signal_independence`, `economic_rationale`) render
`GateStatus.AMBIGUOUS` whenever `verify_freeze` does not return
`VERIFIED`. With the current bug, a gate called with
`freeze_covered_paths=[]` sails past that safeguard and is free to
render `PASS`/`FAIL` on zero freeze coverage — silently defeating the
one invariant (`AD-043`) that exists to keep a gate from evaluating
against an untrustworthy basis.

## 2. Verified current behavior

Read directly from `core/governance/freeze_verifier.py:129-178`
(`verify_freeze`), independent of any prior document's characterization:

```python
paths = [str(p) for p in covered_paths]          # [] if covered_paths is empty
resolved_hash = _resolve_commit(commit_ref, ...)  # succeeds for any real ref

errors: list[str] = []
drifted: list[str] = []
for path in paths:                                # loop body never runs when paths == []
    ...

if errors:
    status = FreezeStatus.UNVERIFIABLE
elif drifted:
    status = FreezeStatus.DRIFTED
else:
    status = FreezeStatus.VERIFIED                 # <-- reached when paths == []
```

Confirmed: `errors` and `drifted` are populated exclusively inside the
`for` loop. An empty `covered_paths` iterable means the loop body never
executes, both lists stay empty, and execution falls through to the
`else` branch. `verify_freeze('<any resolvable ref>', [])` returns
`VerificationResult(status=VERIFIED, drifted_files=(), errors=())`.

**Existing tests.** `tests/test_governance_freeze_verifier.py` has eight
tests covering: unmodified-file verification, committed drift,
uncommitted drift, unresolvable ref, path absent at commit, multiple
paths, short-hash resolution, non-git-directory error, and
no-mutation. **None construct an empty `covered_paths` list.** The bug
is untested in both directions — no test currently pins the buggy
behavior, and no test would fail if it were fixed.

**Existing Architecture Decisions.** `AD-033` establishes the three-way
status contract: `UNVERIFIABLE` is for a run that "fail[s] to complete"
(unresolvable ref, or a path that never existed at that commit) —
categorically different from a completed run that finds drift.
`AD-033` does not discuss the empty-`covered_paths` case at all; it is
silent, not contradicted, by this proposal. `AD-043` (Validation domain)
is the invariant this hole actually defeats: it never anticipated
`verify_freeze` returning `VERIFIED` for zero evidence, because nothing
in `AD-033`'s contract description says an empty set should verify.

**Callers, verified exhaustively.** Exactly two production call sites
import `verify_freeze`: `core/validation/gates/signal_independence.py:60`
and `core/validation/gates/economic_rationale.py:54`. Both call it
identically —

```python
verification = verify_freeze(freeze_commit_ref, freeze_covered_paths, repo_root=repo_root)
if verification.status is not FreezeStatus.VERIFIED:
    return GateResult(status=GateStatus.AMBIGUOUS, ...)
```

— i.e. both branch on "is it `VERIFIED`?", never on which specific
non-`VERIFIED` status was returned. **No production script currently
calls either gate function** (`evaluate_signal_independence_gate` /
`evaluate_economic_rationale_gate` are invoked only from their own test
files, `tests/test_signal_independence_gate.py` and
`tests/test_economic_rationale_gate.py` — grep confirmed, no
`experiments/` or `research_archive/` caller exists). H4 gate execution
has not begun. **The hole is live and real but has not yet produced a
false `VERIFIED` in any archived governance record**, because nothing
has exercised it with real data yet. This claim is stated at its
verified strength, not inferred.

**Assumptions depending on empty coverage being allowed.** None found.
Neither gate function, neither gate's test suite, nor any documentation
states or relies on empty coverage being a legitimate, meaningful input.
The only place "empty covered paths" is discussed at all is the Step 9
documents diagnosing this exact bug.

## 3. Proposed correction

### 3.1 Status semantics: reuse `UNVERIFIABLE`, no new enum

**Decision: an empty `covered_paths` maps to `FreezeStatus.UNVERIFIABLE`.
No new enum member is introduced.**

Reasoning:

- `FreezeStatus`'s own docstring already frames `UNVERIFIABLE` as "a
  verification run can fail to complete" — a category distinct from a
  completed run finding drift. A run given zero paths to check has
  nothing to complete; it fits the existing category exactly, it does
  not strain it.
- `AD-047`'s own restated invariant (`docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`
  §1.1) already groups the three failure shapes together in one
  sentence: "no gate executes against a freeze verification whose
  covered-path set is **empty, unresolved, or drifted**." Unresolved
  already maps to `UNVERIFIABLE`; empty is named in the same breath, not
  set apart.
- Both existing gate call sites branch on `is not VERIFIED`, not on a
  specific status. Reusing `UNVERIFIABLE` therefore requires **zero
  changes** to either gate function — a new enum member would be
  equally sufficient for that specific check, but would add a fourth
  value to a type two other call sites, `AD-043`'s reasoning, and the
  existing test suite all currently treat as exhaustively three-valued,
  for no behavioral gain. This is the same "no abstraction ahead of
  need" discipline `AD-005`/`AD-025`/`AD-028` already apply throughout
  this repository.
- A distinct status (e.g. `EMPTY` or `NO_COVERAGE`) would let a future
  caller pattern-match on it specifically and treat it differently from
  a bad ref — but no such caller exists or is proposed, and inventing
  the distinction without a consumer is exactly the premature
  abstraction this codebase's own conventions rule out.

### 3.2 Code change

One additive guard in `verify_freeze`, inserted **after** commit
resolution and **before** the per-path loop:

- After `paths = [str(p) for p in covered_paths]` and after
  `resolved_hash` is confirmed non-`None` (i.e. the existing
  unresolvable-ref branch is unchanged and still returns first), check
  whether `paths` is empty.
- If empty: return `VerificationResult` with `status=UNVERIFIABLE`,
  `resolved_hash=resolved_hash` (the commit *did* resolve — this is
  deliberately preserved so `resolved_hash is None` continues to mean
  exactly what it means today: "the commit ref itself did not resolve,"
  never "something else was wrong"), `drifted_files=()`, and `errors`
  containing one fixed, descriptive message (e.g. `"covered_paths is
  empty; a freeze verification with zero covered paths cannot be
  VERIFIED"`).
- The per-path loop and its existing branches (`errors` → `UNVERIFIABLE`,
  `drifted` → `DRIFTED`, neither → `VERIFIED`) are **untouched**.

This is a single early return sitting between two pieces of existing,
unmodified logic. It changes no other branch, no function signature, no
type, and no import.

### 3.3 What this does *not* change

- `VerificationResult`'s shape (fields, types) — unchanged.
- The unresolvable-commit-ref branch — unchanged, still returns first,
  still sets `resolved_hash=None`.
- The path-absent-at-commit and drift-detection branches — unchanged.
- `signal_independence.py`, `economic_rationale.py` — **zero edits**.
  Both already branch on `is not VERIFIED`; `UNVERIFIABLE` from an empty
  set is handled identically to `UNVERIFIABLE` from a bad ref, which is
  the correct behavior with no new code.
- `GateResult`, `GateStatus`, `DecisionMetadata` — untouched.
- Any Step 9 concept (`GateContext`, `GateRunner`, `DecisionRecorder`,
  `LifecyclePhase`, `advance_phase`) — none exist yet in the codebase and
  none are referenced by this change.
- The research lifecycle / project models (`core/research/`) — untouched,
  not imported by this module today, not imported by this change.

## 4. Invariants preserved

- **`AD-001`–`AD-005` cross-cutting conventions**: no new abstraction, no
  framework, standard-library only — unaffected, nothing here touches
  them.
- **`AD-033`'s three-way, non-boolean status contract**: preserved
  exactly. This proposal adds a new *trigger* for the existing
  `UNVERIFIABLE` value; it does not add a value, remove one, or change
  what any existing trigger returns.
- **`freeze_verifier.py`'s read-only posture** (module docstring: "every
  git invocation here is a read-only plumbing command... nothing in this
  module ever writes, commits, checks out, or resets anything"):
  preserved. The new guard performs no git invocation at all — it is a
  pure length check on an already-materialized list.
- **`AD-043`'s "verification failure is `AMBIGUOUS`, never `FAIL`" rule**:
  strengthened, not altered. A gate called with empty coverage now
  correctly lands in the `AMBIGUOUS` branch it was always supposed to
  reach; the rule itself is not touched.
- **No existing `VerificationResult` is retroactively invalidated.** This
  changes only the output of *future* calls with an empty path list. It
  does not reinterpret, re-run, or invalidate any past result — and, per
  §2 above, no past result is known to have been produced from an empty
  path list in the first place.
- **`AD-042`'s "evidence_refs are references, never validated content"
  boundary**: unaffected — this proposal does not touch `evidence_refs`
  or either gate's evidence handling at all.

## 5. Adversarial review

Five scenarios a malicious or careless operator could present, tested
against the proposed mechanism:

| Scenario | Caught by this fix? | Why |
|---|---|---|
| **Empty coverage** (`covered_paths=[]`) | **Yes.** | This is exactly the case the guard targets: zero paths ⇒ `UNVERIFIABLE`, never `VERIFIED`. |
| **Meaningless coverage** (`covered_paths=["README.md"]`, an irrelevant file) | **No — by design, and disclosed as such.** | The guard checks *cardinality*, not *relevance*. A one-file, irrelevant set passes the non-empty check and is verified faithfully against that one file — truthfully answering "is `README.md` byte-identical to commit X," which is a true and correct answer to a question nobody who wanted methodology coverage actually meant to ask. `AD-047` §2.3 already names this precisely: "non-emptiness is necessary and nowhere near sufficient... adequacy of coverage is a human review judgment," not something any automated check in this codebase performs. This proposal does not claim to solve it and must not be read as doing so. |
| **Incomplete coverage** (some frozen files covered, others silently omitted) | **No — same reason as above.** | Indistinguishable, mechanically, from "meaningless coverage": `verify_freeze` has no way to know what the *complete* set of frozen files should have been: `covered_paths` is caller-supplied with no independent source of truth to check it against (`core/research/` has no `FreezeId`-backed registry — `AD-033`). Out of scope for the same reason. |
| **Changed files outside declared coverage** | **No — explicit, pre-existing, unrelated limitation.** | `verify_freeze` only ever inspects the paths it is told to inspect. A file that drifted but was never named in `covered_paths` is invisible to it, today and after this fix — this is not the empty-coverage bug, it is the general shape of "coverage adequacy is not mechanized," restated. |
| **Modified/substituted commit reference** (operator cites a different, more favorable commit as "the freeze commit") | **No — different layer entirely.** | `verify_freeze` verifies fidelity *to whatever `commit_ref` it is given* — it has no independent way to confirm that ref is the one originally claimed as the freeze point. `commit_ref` is caller-supplied with no authentication. This is a provenance problem one layer up from anything `freeze_verifier.py` can address; `docs/PHASE_4_STEP9_DRAFT_ADRS.md` AD-048's hash-chain + human-witnessed anchor is the mechanism aimed at *that* problem, not this one. |

**Conclusion.** The fix closes exactly one hole: it makes zero-evidence
verification impossible to mistake for success. It does not, and does
not claim to, make coverage *adequate* — that remains, correctly, a
human review judgment with no mechanism behind it anywhere in this
codebase today. Any future document citing this PR0 fix must not
describe a `VERIFIED` result as proof the *methodology* was frozen —
only that the *named paths* were. (`freeze_verifier.py`'s own module
docstring already states this boundary in its "What verification
proves, and what it does not" section; this proposal does not weaken or
narrow it.)

## 6. Tests required

All additive — **zero edits to any existing test** (the same discipline
Step 9 imposes on itself: an existing test needing modification is a
sign an invariant broke).

1. **`test_empty_covered_paths_is_unverifiable`** — a resolvable freeze
   commit, `covered_paths=[]` ⇒ `status is UNVERIFIABLE`,
   `resolved_hash == freeze_hash` (not `None` — the commit did resolve),
   `drifted_files == ()`, `errors` non-empty and mentions the emptiness
   explicitly. This is the regression test that would have caught the
   original defect; its absence today is exactly what let it ship.
2. **`test_empty_covered_paths_with_unresolvable_ref_reports_ref_error`**
   — an unresolvable `commit_ref` combined with `covered_paths=[]` ⇒
   still `UNVERIFIABLE`, but `resolved_hash is None` and the error is the
   existing "does not resolve to a commit" message, not the new
   empty-coverage message. Proves the two failure causes stay
   distinguishable and that commit resolution is still checked first.
3. **Existing 8-test suite in `tests/test_governance_freeze_verifier.py`
   passes unmodified** — explicit CI/verification requirement, not a new
   test, but a required, checked outcome.
4. **Gate-level propagation tests** (one addition each to
   `tests/test_signal_independence_gate.py` and
   `tests/test_economic_rationale_gate.py`): call
   `evaluate_signal_independence_gate` / `evaluate_economic_rationale_gate`
   with `freeze_covered_paths=[]` against a real resolvable commit ⇒
   `GateStatus.AMBIGUOUS`, summary containing `status=unverifiable`. This
   is the evidence, not just the assertion, that both gates inherit the
   fix with no code change of their own — the concrete demonstration
   that "claims must never exceed mechanisms" holds for this fix.

## 7. Documentation changes required

1. **`core/governance/freeze_verifier.py`**: extend `FreezeStatus`'s
   docstring (currently: "a verification run can fail to complete (bad
   ref, path never existed at that commit)") to name the third trigger:
   an empty `covered_paths` set. One sentence; no restructuring of the
   docstring's existing "what verification proves, and what it does not"
   section, which already states the adequacy boundary this fix does not
   change.
2. **`docs/ARCHITECTURE_DECISIONS.md`**: one new AD recording this
   increment — decision (`UNVERIFIABLE` on empty `covered_paths`,
   §3.1–3.2 above), rationale (§1–2), and an explicit "what this does not
   claim to fix" paragraph mirroring §5's table, so a future reader
   cannot mistake this fix for a coverage-adequacy mechanism. Numbering
   is an open sequencing question (see §9) and is not resolved by this
   proposal.
3. **`docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`** and
   **`docs/PHASE_4_STEP9_DRAFT_ADRS.md`**: no edit required. Both
   documents already correctly describe the *pre-fix* state as a live,
   disclosed, deferred hole ("`verify_freeze` is not modified by Step
   9"). They remain accurate as historical record of the state at the
   time they were written; per this repository's own convention
   (`AD-036`, `AD-040`, `AD-044`, `AD-045`), a later fix is recorded as a
   new AD, not by editing a settled document.
4. **PR0 disclosure obligation (A-1)**: `AD-047`'s re-disclosure
   requirement — "a dated governance deviation record... stating that
   `verify_freeze(commit_ref, [])` returns `VERIFIED`... This obligation
   stands whether or not Step 9 proceeds" — is **independent of this
   proposal** and is not discharged by it. That disclosure documents that
   the hole *existed* and every historical `VerificationResult`'s
   evidentiary strength; this proposal *closes* the hole going forward.
   Both are needed; neither substitutes for the other. This proposal
   takes no position on when A-1 is filed and does not file it.

## 8. Migration impact

- **Callers**: two, both verified above, both require no change.
- **Existing tests**: zero required changes, verified in §6.
- **Existing archived governance artifacts**: none are known to have
  been produced by an empty-coverage call (§2, "callers, verified
  exhaustively"); this fix does not retroactively reinterpret any of
  them.
- **Behavioral change surface**: exactly one new return path in one
  function, reached only when `covered_paths` is empty — a case with no
  known legitimate current caller.
- **Downstream**: none. `core/research/`, `core/statistics/`,
  `tools/check_import_boundaries.py`, and every Step 9 concept are
  outside this change's reachable set (verified: `freeze_verifier.py`
  imports nothing beyond `subprocess`/`collections.abc`/`dataclasses`/
  `enum`/`pathlib`, and this proposal adds no import).

## 9. Implementation boundary

**In scope for this PR0 increment:**

- The one additive guard in `verify_freeze`, as specified in §3.2.
- The one docstring sentence in §7.1.
- The one new AD in §7.2 (number to be assigned at acceptance time).
- Tests 1–4 in §6.

**Explicitly out of scope, deferred to elsewhere:**

- Coverage-adequacy checking of any kind (README-only, incomplete sets,
  out-of-declared-scope drift) — no mechanism in this codebase performs
  this today and none is proposed here; it remains, and is disclosed as
  remaining, a human review judgment (§5).
- Commit-reference authentication / provenance anchoring — that is
  `AD-048`'s hash-chain-plus-human-anchor mechanism, a Step 9 concept,
  not touched by this proposal.
- The A-1 re-disclosure obligation (§7.4) — independent, not filed by
  this document.
- Any Step 9 Phase A–E work — this proposal has no ordering dependency
  on Step 9 in either direction, and introduces none of its vocabulary
  (`GateContext`, `GateRunner`, `DecisionRecorder`, `LifecyclePhase`,
  `sequence_status`, `advance_phase`).
- AD numbering: this document deliberately does not claim an AD number.
  `docs/PHASE_4_STEP9_DRAFT_ADRS.md` provisionally claims AD-047–050
  against a verified ceiling of AD-046, but those are drafts, not yet
  accepted. Whichever of this proposal's AD or Step 9's AD-047 lands
  first takes the next number in sequence; this is a sequencing
  decision for whoever accepts these documents, not a technical
  dependency — the two ADs' content does not conflict either way.

**No code, no test, and no documentation edit described above is applied
by this document. Implementation begins only on explicit approval.**
