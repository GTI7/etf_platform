# Phase 4 Governance — Architecture Review Board Determination

**Date:** 2026-07-21
**Status: determination — binding on Phase 4 implementation sequencing. No code committed by this document.**

This adjudicates two review events against the Phase 4 governance
implementation (`core/governance/*`, the eight `tests/test_governance_*.py`
files, and the persistence layer they depend on):

1. **Hostile Level-3 architecture review** — 20 findings across four
   severity bands, plus a section explicitly naming six subsystems as
   architecturally sound.
2. **Independent peer review of that review** — a finding-by-finding
   audit of (1) against the same source, with five claims independently
   re-executed.

Per this platform's own Standard §5 supersession discipline, this is a
new, dated, cross-referenced file. Neither review is edited or
superseded by it; this document rules on them.

**What this document is not.** It is not a third architecture review. No
finding here originates with the ARB. Every ruling below is on a finding
already raised by review (1), as challenged or affirmed by review (2).
Where the ARB reaches a conclusion neither review reached, it is a
*bucketing* or *sequencing* ruling on their evidence, and it is flagged
as such in place.

**Provenance gap — action required.** Neither review exists as a
repository artifact; both live only in session transcripts
(`Phase 4 governance architecture review`). Standard §5 requires
`reviewer_reports/` to contain one file per review event, each with its
own date, reviewer identity, and independence-level declaration. Two
review events currently have no such file. This determination cites
them; it does not substitute for them. **Both reviews should be written
to `reviewer_reports/` before this determination is acted on**, or the
evidence chain for the decisions below starts at a document that cites
sources the archive does not contain.

**Related documents.**

| Document | Relationship |
|---|---|
| [PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md](PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md) | Base proposal. §2.3 (exact-match policy) is load-bearing for the A1(b) ruling below. |
| [PHASE_4_ARCHITECTURE_AMENDMENT_V1.md](PHASE_4_ARCHITECTURE_AMENDMENT_V1.md) | Superseded by v1.1; retained. |
| [PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md](PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md) | Current design of record. §G lists `reproduction_record.json` binding and the report hash as MUST HAVE — findings A1/A3 below are the gap between that list and the implementation. |
| [PHASE_4_RESULT_REPORT_CANONICALIZATION_CHARTER.md](PHASE_4_RESULT_REPORT_CANONICALIZATION_CHARTER.md) | Chartered by ruling A1(b) below. |
| [RESEARCH_GOVERNANCE_STANDARD.md](RESEARCH_GOVERNANCE_STANDARD.md) | §5 supersession discipline and evidence-package completeness; §6 data provenance. |

---

## Chair's summary

The Level-3 review is the stronger **discovery** instrument. All twenty
findings originate there, and the peer review — which independently
re-executed five of them — could not overturn a single factual claim
about Python import machinery, `pathlib`, `json`, or SQLite transaction
semantics.

The peer review is the stronger **adjudication** instrument. It is
decisively right on three fix-level claims (A1's "no new architecture",
A2's `sys.modules` assertion, D1's platform validity) and on the
severity curve, which the Level-3 review inflates by roughly one level
across bands A and B.

The ARB sides with the peer review on the majority of contested points.
It sides with the Level-3 review on one substantive semantic point (A1,
frozen-identity as an input check). It corrects **both** on the bucketing
of A1(a)/A3, which neither got right.

**Bottom line:** the defect density is low and the component-level
engineering is above the standard both reviewers expected. What is
missing is the layer binding verified components into a verified
*claim* — and the subsystem has never been run end-to-end against a real
archive.

---

## 1. Rulings — Band A (Critical)

### A1 — `ReproductionRecord` is unwired

**ACCEPT WITH MODIFIED SEVERITY.** Critical-*blocking*, not
Critical-*live*.

The defect is accepted in full: the runner reads one field of
`reproduction_record.json` ([reproduction_runner.py:292](../core/governance/reproduction_runner.py))
and discards the experiment's return value ([:211](../core/governance/reproduction_runner.py)).
Neither `dataset_content_hashes` nor `result_report_hash` participates in
any verdict.

The peer review's three challenges split:

| Challenge | Ruling |
|---|---|
| "`REPRODUCTION_FAILED` also fires on `FrozenIdentityChangedError`" | **Rejected.** Frozen-identity tables are *inputs*. A post-run identity check detects the experiment mutating its own inputs; it is not an output comparison. The Level-3 review already conceded this check exists. Its core claim — the output is never compared — survives intact. This is the one substantive point where the Level-3 review is the more convincing of the two. |
| "'No new architecture; both seams already exist' is empirically false" | **Accepted against the Level-3 review.** The report carries a `generated_at` timestamp, so `sha256_of_file` can never match across runs. This is the single most valuable correction in the peer review, and it is what charters A1(b) as a design task rather than a patch. |
| "The exploit is currently unreachable (C7)" | **Accepted as to framing, rejected as to downgrade.** Severity is scored at the point of use, and this subsystem is pre-first-use. "Must be fixed before this runs once" and "High" are not the same statement. |

**Fix assessment.** Part (a) — bind manifest `content_hash` to
`record.dataset_content_hashes` — is correct and already minimal; no
smaller fix exists and it adds no complexity. Part (b) — result report
hashing — is correct in intent and wrong in sizing; as a patch it would
import an unsolved canonicalization problem into the runner. **Split
them.** Part (a) is MUST (see the indivisibility ruling at A3). Part (b)
is chartered separately.

### A2 — Pinned-commit execution is an illusion

**ACCEPT.** Critical, unmodified. The strongest finding in either
document.

Both reviewers independently confirmed that `core` is in `sys.modules`
before `exec_module` runs, that submodule resolution walks HEAD's
`__path__`, and that `sys.path.insert` is inert against an
already-imported package. The test named for this invariant
(`test_experiment_code_runs_from_the_pinned_commit_not_head`) is the one
test that cannot exercise it, because its fixture imports only `sqlite3`.

**Fix assessment — primary direction correct, cost understated.** The
peer review is right that "stays in-architecture" is false: out-of-process
execution deletes the `run_experiment: Callable[[ModuleType, Path], Any]`
contract whose documented reason for existing is that experiment
signatures differ, and it moves execution outside the in-process offline
guard.

**Fix assessment — fallback rejected as written.** "Assert no `core.*`
key is present in `sys.modules` before `exec_module`" would refuse 100%
of runs, because the runner's own imports put `core.governance.*` there.
Only a scoped denylist is workable, and a denylist is a *detector*, not
a guarantee. It is acceptable solely as a time-boxed stopgap with a
recorded expiry.

**Smaller fix:** none that preserves the guarantee. Purging and
restoring `sys.modules` around the exec is fewer lines and more fragile
than a subprocess boundary; the ARB does not recommend it.

> **Binding integration ruling A2/C6.** A2's fix *creates* C6's severity.
> Moving execution out-of-process without installing the offline guard in
> the child trades a silent code-substitution failure for a silent
> network-access failure. **They ship in the same change or not at all.**

### A3 — Dataset artifacts not pinned by `commit_hash`; manifest is self-attesting

**PARTIALLY ACCEPT.** Medium-High, architectural.

Facts confirmed by both reviews. Two overstatements are accepted against
the Level-3 review:

- Blame belongs to `_cli_main`, not `run_reproduction` — the latter takes
  `cycle_dir` and `dataset_manifest_path` as parameters and is already
  agnostic. This makes the fix smaller than the finding implies.
- *"No artifact in the repository would contradict the forgery"* is
  false. `research_archive/` is committed, and `freeze_verifier` checks
  committed **and** uncommitted drift
  ([freeze_verifier.py:103-120](../core/governance/freeze_verifier.py)).
  The accurate statement is narrower: nothing in the reproduction path
  consults it, because the dataset paths are not in the covered-paths
  list.

**Fix assessment.** The covered-paths variant is correct and smaller.
The relocate-`cycle_dir`-into-the-worktree variant is architecturally
cleaner — it makes the git object store the anchor, which is what the
runner docstring already claims — but it changes CLI semantics. Defer it
to hardening.

> **Binding bucketing ruling A1(a)/A3 — correcting both reviews.** The
> peer review places A1(a) in MUST and A3 in SHOULD. That split is
> incoherent. A1(a) binds the manifest to the record; if the record is
> not itself covered by `freeze_verifier` at the pinned commit, the fix
> relocates the self-attestation one file over and a forger edits three
> files instead of two. The Level-3 review states this dependency
> explicitly ("*provided* `reproduction_record.json` is itself covered")
> and then fails to act on it in its own priority list.
> **A1(a) and A3's covered-paths addition are one indivisible change.
> Both are MUST. Neither ships alone.**

---

## 2. Rulings — Band B (Serious)

### B1 — TOCTOU between hashing and loading

**ACCEPT WITH MODIFIED SEVERITY.** Low; reclassified from security to
consistency/performance.

The peer review's threat-model argument is decisive: an adversary who can
swap a snapshot mid-run has write access to the cycle directory, and A3
hands that same adversary a strictly easier attack with no race. **The
tampering exploit is rejected.** What remains is accidental corruption on
a shared filesystem — real, rare.

**Fix assessment.** Larger than "minimal": three loaders take `Path` and
re-read internally, `preflight_validate` returns `dict[str, Path]`, and
four signatures change. The genuine payoff is the one the peer review
identified and the Level-3 review missed — eliminating 4× full reads of
a potentially very large `PriceBar` snapshot. **Not before v1.0.**
Schedule when loader signatures are being touched anyway.

### B2 — `commit_hash` never validated as a commit hash

**ACCEPT.** Medium. Uncontested on mechanism. The peer review's
correction stands: an ambiguous abbreviation makes git *error* rather
than silently resolve, so the live case is `"main"` / tags / `HEAD`. That
case alone justifies the fix.

**Fix assessment.** Correct, ~3 lines, reuses the existing
`freeze_verifier._resolve_commit`. No smaller fix; no added complexity.
**Before v1.0: yes.** Best value-per-line after B4.

### B3 — Exception masking collapses the four-state outcome

**PARTIALLY ACCEPT.** Medium, split in two.

- **Execution backstop — accepted in full.** `ModuleNotFoundError`
  reported as `REPRODUCTION_FAILED` assigns the most damaging verdict the
  system can emit to an environment problem. Narrowing costs nothing.
- **Reconstruction backstop — the peer review is right** that this is
  documented, deliberate policy ([reproduction_runner.py:24-32](../core/governance/reproduction_runner.py)),
  not an oversight. But a documented policy can still be wrong policy,
  and it plainly is for the enumerated classes: `ScratchDatabaseExistsError`
  is operator error and a disk-full `OSError` is not input drift. The ARB
  accepts the Level-3 review on the named classes and **rejects its
  blanket framing** that the four-state outcome is "unreliable as
  evidence."

**Fix assessment.** Both reviews converge and the convergent fix is
correct: route the named classes to `UNVERIFIABLE`, keep the backstop,
tag its detail explicitly. **Before v1.0: yes.** Implement as one change
with C5.

### B4 — A raw exception escapes `run_reproduction`

**ACCEPT.** Medium, uncontested, and provably reachable — the real
universe module executes ten `core.*`/provider imports at module scope
during `exec_module`. The runner docstring's guarantee that no raw
exception escapes is currently false.

**Fix assessment.** One line; it *is* the minimal fix; zero complexity.
**Before v1.0: yes.** Highest fix-value-per-line in the submission.

### B5 — No audit record is produced or persisted

**ACCEPT WITH MODIFIED SEVERITY — raised, against both reviews.**

Both place this at Medium / SHOULD. The ARB moves it to MUST. The
reasoning is present in both documents and neither followed it through:
this is evidence-producing machinery whose evidence is, in the Level-3
review's words, a terminal line that vanishes. The first production
reproduction exists *for the purpose of producing a citable artifact*. A
run that emits stdout and nothing else has not produced evidence.

**Fix assessment.** Correct, additive, in-architecture: carry
`resolved_commit`, `observed_dataset_hashes`, `started_at`/`finished_at`,
and platform/Python/SQLite versions; have `_cli_main` write
`reproduction_attempt_<timestamp>.json` next to the cycle. No smaller
fix; no added complexity. **Before v1.0: yes.**

> **Conditional flag.** If the persisted record ever includes the
> frozen-identity digest, **C3 becomes must-fix-before-first-write** —
> changing a hash format after evidence is published is a migration. As
> currently designed the digest is same-run ephemeral, so this does not
> bind today. Do not let it drift unnoticed.

---

## 3. Rulings — Band C (Governance)

| # | Finding | Ruling | Severity | Fix ruling |
|---|---|---|---|---|
| **C1** | `snapshot_path` unvalidated, escapes cycle dir | **PARTIALLY ACCEPT** | Low | Path semantics verified by both. The peer review is right that this is the same adversary as A3, not an independent vulnerability; surviving value is archive self-containment and the accidental-absolute-path case. Accept the relative-path/no-`..` check. **Reject the type-validation add-on** — a string `row_count` already yields a governed error, so the checks buy nothing and add surface. SHOULD. |
| **C2** | Calendar preflight validates a set the loader doesn't load | **ACCEPT** | Low now / Medium on the day a second calendar literal is added | Peer's mechanism correction accepted (FK violation at `load_etf_snapshot`, not `ensure_calendar`); same conclusion. **A smaller fix exists and the ARB prefers it:** validating preflight against the calendar actually loaded is ~1 line and converts a future silent trap into a named offline failure. Derive-calendars-from-data is the better end-state and the larger change — take it when a second calendar actually arrives. SHOULD, in the one-line form. Landmine remover. |
| **C3** | Frozen-identity hash has unescaped `\|` delimiter | **ACCEPT WITH MODIFIED SEVERITY** | Low practical | Collision reproduced by both. Peer's rhetoric objection sustained: the designed case is accidental regeneration, where an in-place edit conserving the pipe-join has ~0 probability. Fix: length-prefixed fields plus column names in the digest. Prefer length-prefixing over `json.dumps(list(row), sort_keys=True)` — `sort_keys` does nothing for a list. SHOULD, because it is free, not because it is live. |
| **C4** | `read_canonical_jsonl` doesn't enforce its documented rules | **PARTIALLY ACCEPT** | Low | All four sub-claims verified; exploitability requires A3. The peer's observed internal tension is fair — C4's blank-line path depends on reaching the very backstop B3 argues against. Accept the duplicate-key hook, the `isinstance(obj, dict)` assertion, and explicit trailing-blank-line handling. **Reject the recursive key-order assertion** — it pays a per-read cost on large snapshots to re-check a property the write path already guarantees. SHOULD. |
| **C5** | Failed reconstruction leaves a poisoning scratch DB | **ACCEPT WITH MODIFIED SEVERITY** | Low-Medium | Peer's narrowing correct: the default path is a fresh `mkdtemp` per run, so the poisoned retry requires an explicit `--scratch-db`. **A smaller fix exists:** the `UNVERIFIABLE` classification (already being done in B3) fully resolves the reported failure scenario. **Reject the unlink-on-failure half** — deleting the scratch database destroys the forensic state an auditor needs to diagnose the failure. Preserving artifacts is correct behaviour for an audit tool. MUST, via B3. |
| **C6** | Offline guard does not cover subprocesses | **ACCEPT** | Low now / High the moment A2 lands | Documentation defect today; today's only subprocess is local `git`. **Not independently schedulable** — see the binding A2/C6 ruling above. One docstring sentence if and only if A2 has not yet landed. |
| **C7** | No archive in the repository can be reproduced | **ACCEPT — reclassified** | Status, not defect | This is the most important sentence in either document. The peer review's structural criticism is **sustained**: the Level-3 review buries its own severity-limiting evidence in section C and then writes a priority list contradicting it. The ARB **rejects the Level-3 framing** that "a `VERIFIED` result today does not support the claim it appears to support" — no such result exists. C7's remedy is not a patch; it is the first end-to-end run on a real archive, which is itself the acceptance test for A1–A3. |

---

## 4. Rulings — Band D (Minor)

| # | Finding | Ruling | Reasoning |
|---|---|---|---|
| **D1** | `mkdtemp` → `rmtree` → `worktree add` symlink race | **PARTIALLY ACCEPT** — reject as a security finding | The peer review's platform argument is decisive and the Level-3 review did not consider it: `%TEMP%` is per-user on win32, symlink creation requires privilege, and `git worktree add` refuses a pre-existing path. The two-line `mkdtemp`-a-parent variant survives as free hygiene only. |
| **D2** | `git worktree remove` return code discarded | **ACCEPT** | Correct, trivial, Low. Warn, do not raise — it is cleanup. Nice hardening. |
| **D3** | `sys.path.remove` / `sys.modules` contamination | **ACCEPT** | Low, and **largely absorbed by A2** — out-of-process execution eliminates it. The peer's rider (`module_from_spec` never registers the module in `sys.modules`) reinforces the same direction and is not separately actionable. |
| **D4** | `ReproductionOutcome` is mutable | **REJECT as a finding** | Style. **Fold into B5**, which rewrites that class anyway; making it `frozen=True, slots=True` there is free and consistent with its peers. No standalone work item. |
| **D5** | `SELECT *` / `row.keys()` in the identity digest | **REJECT** | The peer review's argument is decisive: before/after run against an identical schema in the same process, so column order cannot produce a wrong verdict. The portability point is moot because the digest is never compared across schema versions — and C3's fix addresses it incidentally. |

---

## 5. Band E — subsystems named as sound

Both reviews agree; the peer review did not contest a single item in the
Level-3 review's section E (`identity_verification` scope boundary,
`network_guard` depth counter, `dataset_manifest` coverage validation,
load ordering and fail-fast preflight, the `canonical_jsonl` write path,
`freeze_verifier`, `calendar_definitions`). **No ARB action.**

The ARB notes for the record that a hostile review's willingness to name
seven correct subsystems, and to close out its own disproved hypothesis
about duplicate manifest entries, is what makes its critical findings
credible. That posture should be a requirement of future Level-3 reviews,
not an accident of this one.

---

## 6. Must fix before the first production reproduction

Ordered by dependency, not severity.

1. **A2 + C6 (bundled).** Out-of-process execution of the pinned
   entrypoint, with the offline guard installed in the child. The scoped
   denylist refusal gate is acceptable only as a time-boxed stopgap, and
   **not** in the form the Level-3 review wrote it.
2. **A1(a) + A3 covered-paths (indivisible).** Bind manifest
   `content_hash` ↔ `record.dataset_content_hashes`, **and** add
   `reproduction_record.json` and `dataset_manifest.json` to the
   covered-paths list at the pinned commit. Either alone is theatre.
3. **B4.** Broaden the `except OSError` in
   `_load_expected_tickers_from_worktree`, wrapping as
   `ReproductionRunnerError` → `UNVERIFIABLE`. One line.
4. **B2.** Validate `commit_hash` as 40-hex and resolve it through the
   existing `_resolve_commit`. Three lines.
5. **B3 (execution backstop) + C5 (classification).** Route
   `ReproductionRunnerError`, `ImportError`, `ScratchDatabaseExistsError`,
   and `OSError` to `UNVERIFIABLE`; keep the backstop, tag its detail.
   One change, two findings.
6. **B5.** Persist the attempt record. *Raised from both reviews'
   placement* — the first production run exists to produce evidence.

**C7 is the trigger condition for this list, not a member of it.**

## 7. Should fix before public release

- **A1(b)** — result-report hashing, chartered separately as
  [PHASE_4_RESULT_REPORT_CANONICALIZATION_CHARTER.md](PHASE_4_RESULT_REPORT_CANONICALIZATION_CHARTER.md).
  Do not attempt it as a patch.
- **C2** — narrow preflight validation to the calendar actually loaded.
- **C3** — length-prefixed field hashing, column names in the digest.
- **C1** — reject non-relative and `..`-containing `snapshot_path`; type
  checks dropped.
- **C4** — duplicate-key rejection, `isinstance(dict)` assertion,
  explicit trailing-blank-line handling; recursive key-order assertion
  dropped.
- **C6** — docstring sentence, if and only if A2 has not yet landed.

## 8. Nice hardening

- **B1** — single-read-and-thread-rows, justified as consistency and
  large-snapshot performance, not as security.
- **A3 (architectural variant)** — resolve `cycle_dir` inside
  `worktree_path` so the git object store is the anchor, as the runner
  docstring already claims.
- **D2** — check the `git worktree remove` return code and warn.
- **D3** — residual `sys.path` re-entrancy, to the extent A2 leaves any.
- **D1** — `mkdtemp`-a-parent variant, as hygiene.
- `_cli_main`'s leaked `mkdtemp` scratch directory.

## 9. Reject

**Findings rejected outright**

- **D1 as a security finding** — platform-invalid on the platform this
  repository runs on.
- **D4** — style; folded into B5, no standalone item.
- **D5** — cannot produce a wrong verdict.

**Claims and fix-components rejected (the finding survives, the claim
does not)**

- **B1's tampering exploit** — subsumed by A3; grants no new capability
  to the same adversary.
- **A1's "no new architecture; both seams already exist"** —
  empirically false; `generated_at` defeats naive file hashing.
- **A1's "`REPRODUCTION_FAILED` is unreachable for its stated cause"** —
  narrowly overstated. The peer's counter is *also* wrong: frozen-identity
  is an input-integrity check, not an output check.
- **A2's `sys.modules` assertion as written** — would refuse every run.
- **A3's "no artifact would contradict the forgery"** — git and
  `freeze_verifier` would, for covered paths.
- **C3's "lands exactly on the case it was designed for"** — rhetoric.
- **The Level-3 priority-list framing** that a `VERIFIED` result today is
  uncitable — contradicted by its own C7.
- **C4's recursive key-order assertion** — per-read cost for a
  write-path guarantee.
- **C5's unlink-on-failure** — destroys forensic state an audit tool
  should preserve.
- **C1's type-validation add-on** — the failure is already governed.

---

## 10. Certification question

> *If this platform were submitted for an independent scientific
> reproducibility audit tomorrow, what issues would actually prevent
> certification?*

Six, in the order an auditor would encounter them. All are drawn from
findings both reviews confirmed.

**1. There is nothing to audit. (C7)** No archive contains a
`dataset_manifest.json` or a `reproduction_record.json` — not
`reference_v1`, `reference_v2_h1`, `reference_h3`, or
`positive_control_phase3`. The subsystem has never executed against a
real cycle; every test fixture is synthetic. An auditor asking "show me
one reproduction" gets nothing. **Disqualifying on its own**; no other
finding needs to be reached.

**2. The flagship experiment cannot be reproduced offline at all.** The
peer review raised this as a closing footnote and it belongs at the top:
`daily_etf_universe_update.py` fetches through `YahooFinanceProvider`, so
under `offline_guard` it trips `OfflineViolationError` →
`REPRODUCTION_FAILED` regardless of everything else. The first production
reproduction therefore cannot use that script. Either an already-offline
`validate_*` script is designated as the reproduction target, or the
provider must be satisfiable from the frozen snapshot. Until one is true,
the platform cannot demonstrate a successful reproduction of its own
headline pipeline. **This is not on the critical path of any code change
in §6 and can be resolved in parallel.**

**3. A reproduction would not run the reproduced code. (A2)** Only the
~200-line entrypoint comes from the pinned worktree; the scoring,
indicator, ranking, and money code comes from HEAD. A run that executes
today's library against frozen data is not a reproduction of the
published result.

**4. A reproduction would never look at the output. (A1)**
`result_report_hash` is unread and the experiment's return value is
discarded. "Reproduced" without an output comparison does not meet the
definition of the word — and per the peer review's correction, closing
this requires a canonicalization spec, so it cannot be closed the week
before an audit.

**5. The integrity chain does not close. (A3 + A1(a))** Snapshot bytes
are checked against the manifest; the manifest is checked against
nothing; `archive_manifest.json` carries no file hashes; the record field
that exists to anchor the loop is unread. Git and `freeze_verifier`
*would* catch an edit — but only for covered paths, and the dataset paths
are not covered.

**6. No run produces a durable evidence artifact. (B5)** Even a fully
correct run today emits one line to stdout: no record of when it ran,
against which resolved SHA, on which interpreter, with which observed
hashes. Certification rests on artifacts.

**What would not prevent certification:** C1–C6, all of D, and B1–B3. An
auditor would likely record C2, C3, C5, and C6 as observations with
remediation dates. None bear on whether a reproduction is trustworthy
today, because no reproduction exists today.

**Determination.** The platform is not certifiable tomorrow, and the
reason is not defect density. It is that the layer binding verified
components into a verified claim is absent, and the subsystem has never
been run end-to-end against real evidence. Section 6 is the shortest path
to a first citable reproduction; items 1 and 2 above determine the
schedule.
