# Phase 4 / PR0 — A-1 Historical Re-Disclosure Record

**Date filed:** 2026-07-22
**Status: disclosure record.** It discloses a defect that existed, and
bounds what historical evidence produced under that defect can and cannot
support. It is **not** an approval, **not** a gate determination, and
**not** a remediation — the remediation is a separate, already-landed
increment (§4).

**Discharges the disclosure limb of A-1 only — A-1 is not fully
discharged.** Prerequisite **A-1** of
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
§4.1 states a **two-limbed** "Done when" condition: "The disclosure
exists in `docs/`" **and** "the PR0 ruling is closed or confirmed
obsolete."

- **Disclosure / re-disclosure limb — satisfied by this record.** It is
  the re-disclosure obligation stated as part 1 of draft **AD-047** in
  [`PHASE_4_STEP9_DRAFT_ADRS.md`](PHASE_4_STEP9_DRAFT_ADRS.md), and this
  dated record in `docs/` discharges it.
- **Ruling limb — open.** The 2026-07-21 PR0 ruling request carries only
  a **proposed disposition** ("obsolete"), stated in §5 of this record.
  A proposal is not a ruling. No accountable reviewer has accepted,
  rejected, or confirmed it, and this record has no authority to do so
  on its own behalf.

**Consequence: Step 9 remains blocked.** Per Resolution §4.1, Step 9
does not start until every Phase A prerequisite is closed in writing.
A-1 is not closed while its ruling limb is open, so no Step 9 work may
begin on the strength of this record.

That disclosure obligation is explicitly independent of the technical
fix; per
[`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) AD-051 ("Scope")
and [`PHASE_4_PR0_REMEDIATION_PROPOSAL.md`](PHASE_4_PR0_REMEDIATION_PROPOSAL.md)
§7.4, the fix does not discharge it and this record does not substitute
for the fix.

**No file is edited by this record, and no code is introduced by it.**
This is a new, dated file; superseded and prior documents are retained
unedited. The convention followed is the supersession convention stated
in `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5 ("Naming and versioning
conventions"): a correction is a new, dated file, cross-referenced from
the file it supersedes, and the superseded file is retained unedited.

**Precision on that citation.** §5 states that convention for
evidence-package artifacts under `research_archive/<cycle_name>/`, not
for `docs/`. This record is in `docs/` and applies the convention by
extension, not by direct scope. The stated rule for `docs/` is the
preamble of [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) —
"Where a later phase revised an earlier decision, the entry says so
explicitly rather than silently superseding it." AD-036, AD-040, AD-044
and AD-045 are **precedent instances** of that rule (each records a
divergence from `PLATFORM_ARCHITECTURE_V1.md` in a new entry without
editing the superseded document); they are not themselves statements of
correction discipline, and are cited here as precedent only. GOV-1
(Standard §10.1) is titled "Correction discipline" but governs
theory-based target corrections to validation gates; it does **not**
govern this record and is not relied on.

**Verification basis.** Every factual claim below was checked directly
against the canonical repository `D:\Claude\etf_platform` at `4c7ca8d` —
source at the pre-fix and post-fix revisions, `git log`, `git log --all`
over all 62 reachable commits, the test suites, and a content scan of
`research_archive/` and `experiments/`. Where a claim could not be
verified, it is labelled **unknown** and scoped to the evidence sources
that were searched, not asserted as unknowable in principle. Claims
sourced from another document, rather than from the tree, are attributed
to that document. Claims resting on evidence outside the canonical
repository are labelled **off-repo** at the point of use and inventoried
in §1.5, which also states what each off-repo source does and does not
restore.

---

## 1. Incident identification

### 1.1 Defect description

`core/governance/freeze_verifier.py`'s
`verify_freeze(commit_ref, covered_paths, *, repo_root=None)` returned
`FreezeStatus.VERIFIED` when `covered_paths` was empty.

Verified by reading the pre-fix source (`git show
917a6d5:core/governance/freeze_verifier.py`, lines 130-178): `errors` and
`drifted` are populated **exclusively inside** `for path in paths`. An
empty `covered_paths` means the loop body never executes, both lists stay
empty, and control falls through to `else: status =
FreezeStatus.VERIFIED`. The commit-resolution branch above it is
unaffected, so for any resolvable `commit_ref`,
`verify_freeze(commit_ref, [])` returned
`VerificationResult(status=VERIFIED, drifted_files=(), errors=())`.

**A freeze claim was confirmed by checking nothing.** The result was
indistinguishable in type, shape and status from a `VERIFIED` produced by
a real, non-empty check.

### 1.2 Affected mechanism

- **Directly:** freeze verification in the Governance domain — the
  mechanism AD-033 defines and whose semantics AD-033 states ("a
  `VERIFIED` result proves the covered files are byte-identical to their
  content at the claimed commit").
- **Downstream, and load-bearing:** AD-043 makes both Validation gates
  (`core/validation/gates/signal_independence.py:60`,
  `core/validation/gates/economic_rationale.py:54`) render
  `GateStatus.AMBIGUOUS` whenever verification is not `VERIFIED`. Both
  call sites branch on `is not VERIFIED` and nothing else. A gate invoked
  with `freeze_covered_paths=[]` therefore passed that safeguard and was
  free to render `PASS`/`FAIL` on zero freeze coverage — defeating the
  single invariant that exists to stop a gate evaluating against an
  untrustworthy basis. Any invariant of the form *"no gate executes
  against an unverified freeze"* was **vacuously satisfiable**.

### 1.3 Presence window

| Event | Commit | Date (author) |
|---|---|---|
| Defect introduced with the module itself | `917a6d5` "feat(governance): add Phase 1C verification tooling baseline" | 2026-07-19 |
| Defect live and unguarded at the Step 9 baseline | `2c7fb2c`, tag `phase4-final-before-h4-20260722` | 2026-07-22 |
| Defect closed | `4c7ca8d` "fix: prevent empty freeze verification from passing" | 2026-07-22 |

`git log --follow -- core/governance/freeze_verifier.py` returns exactly
two commits in the canonical repository, `917a6d5` and `4c7ca8d`. In the
history reachable from the current `master`, the defect was therefore
present continuously from the module's introduction until its fix, with
no intervening modification of that file.

**Caveat on that window.** This describes *reachable history in the
canonical repository as it stands today*. It is not a claim about the
commits destroyed on 2026-07-21 (§1.4). Scoped precisely: no commit
object for that destroyed work exists in the canonical repository, and
none exists in any off-repo source inventoried in §1.5 — each such source
carries a `.git` whose history terminates at `3021c83`, i.e. before the
destroyed Phase 4 commits were authored. The window above therefore
cannot be extended, corroborated, or contradicted from any evidence
source identified as of 2026-07-22. That is a statement about the sources
searched, not a claim that no such source could exist.

### 1.4 Discovery context — two independent identifications

**First identification, 2026-07-21.** The defect was found during PR0
remediation adversarial review (recorded there as finding F4), disclosed
in a dated governance deviation record
(`docs/PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md`), and fixed
in commit `13ef2d2`. That record disclosed the fix as an out-of-scope
deviation from a then-frozen roadmap and **explicitly requested a ruling
before merge**, which it stated it did not grant itself.

Both the fix commit and the record were lost, **as committed objects**,
in the 2026-07-21 repository destruction incident. Verified: `git log
--all -- docs/PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md`
returns nothing across all reachable commits, and the file is absent from
the canonical working tree. The document it deviates from,
`docs/PHASE_4_IMPLEMENTATION_ROADMAP.md`, is likewise absent from the
tree and from every reachable ref.

**Correction to a prior characterization, on evidence.** AD-047 (draft)
and `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md` §1.1 state that the
original record "was destroyed in the 2026-07-21 incident and exists in
no reachable git ref" / was "destroyed on 2026-07-21 and never restored."
The *git* half of that is confirmed and is affirmed here without
qualification. The broader reading — that the document's **content** is
lost — is **not** correct: byte-identical copies of the record survive
outside version control (**off-repo evidence**), at
`D:\Claude\etf_platform_rebuild\docs\PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md`
and `D:\Claude\SynologyDrive\etf_platform_rebuild\docs\` (verified
identical by byte comparison, 8,580 bytes each; both are untracked
working-tree files in non-canonical directories — see §1.5). Its content
was read in full while preparing this record and is the source of the
2026-07-21 quotation and attributions in **§3.4** below.

Those copies are **not** governance evidence of the same standing as a
committed artifact, and the distinction is one of provenance class, not
of content fidelity: the content is recoverable; the **commit provenance
is not**. They are untracked files, in non-canonical directories, in
working trees whose own git history stops at `3021c83` — no commit
object, no hash chain, no provenance anchor, and nothing that
distinguishes the surviving bytes from bytes edited after the fact. They
are disclosed here because concealing a surviving copy while asserting
destruction would itself be a provenance defect — not because they
restore the record to the evidence chain. They are not restored into
`docs/` by this record; whether to re-commit them is a separate ruling
this document does not make.

**Second identification, 2026-07-22.** After the incident returned the
defect to the tree, it was re-found independently — by direct reading of
`freeze_verifier.py:154-170`, logged in
`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md` §0's verification table and
§1.1 — and the re-disclosure obligation (A-1) was raised. The technical
fix was then specified in
`PHASE_4_PR0_REMEDIATION_PROPOSAL.md` (`ced8636`) and landed in `4c7ca8d`
as AD-051. This record closes the disclosure half.

### 1.5 Evidence inventory — canonical git evidence vs. off-repo evidence

Disclosed in full because the strength of several claims in this record
depends on which class of evidence supports them, and because a
forensic snapshot of the pre-incident machine state exists and must not
be left undisclosed. **Every row was inspected directly on 2026-07-22.**

| # | Location | Evidence class | State found | What it does **not** restore |
|---|---|---|---|---|
| 1 | `D:\Claude\etf_platform` | **Canonical git evidence** | HEAD `4c7ca8d`, 62 reachable commits, branch `master`. The sole authority for every claim in this record not otherwise labelled. | — |
| 2 | `C:\Users\GTi\etf_platform_forensic_2026-07-21` | **Off-repo — read-only forensic snapshot** | Contains a `.git`: `HEAD` = `3021c83` on `refs/heads/master`, 57 reachable commits, `refs/remotes/origin/master` = `b9a804c`. Phase 4 work present **only** as untracked working-tree files. | Contains **no** commit object `13ef2d2` or `88dd282` (`git cat-file -t 13ef2d2` → "Not a valid object name"); **no** `docs/PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md`; **no** `docs/PHASE_4_IMPLEMENTATION_ROADMAP.md`. Its `core/governance/freeze_verifier.py` still carries the defect — no empty-`covered_paths` guard — so it does not even preserve the destroyed fix as content. |
| 3 | `D:\Claude\etf_platform_rebuild` | **Off-repo — working rebuild, non-canonical** | On disk. `.git` HEAD `3021c83`. Holds the surviving deviation-record copy as an **untracked** file (`git ls-files --error-unmatch` → "did not match any file(s) known to git"). | Content only. No commit, no ref, no hash chain for that file. |
| 4 | `D:\Claude\SynologyDrive\etf_platform_rebuild` | **Off-repo — mirror of row 3** | On disk. `.git` HEAD `3021c83`. Same untracked copy, byte-identical to row 3. | Same as row 3. It is a mirror, not an independent witness — corroboration between rows 3 and 4 is not independent corroboration. |

**Naming hazard, disclosed explicitly.** Two distinct paths share the
basename `etf_platform_rebuild` and must never be conflated:

- **`D:\Claude\etf_platform_rebuild`** — row 3 above. **Still on disk**
  as of 2026-07-22. Non-canonical working rebuild at `3021c83`. This is
  the path cited in §1.4 as holding the surviving deviation-record copy.
- **`C:\Users\GTi\etf_platform_rebuild`** — a *different* directory, used
  during the post-incident rebuild and **removed after its content was
  promoted** into the canonical repository. Verified absent on
  2026-07-22 (`ls` → "No such file or directory"). It is **not** the
  source of any claim in this record, and any citation of the bare name
  `etf_platform_rebuild` without a drive prefix is ambiguous and should
  be read as unsourced.

**What the forensic snapshot establishes, stated at its actual
strength.** It confirms that git history up to `3021c83` survives outside
the canonical repository and corroborates the canonical repository's
account of that stretch of history. It does **not** restore the missing
Phase 4 git provenance: the destroyed commits were authored after
`3021c83`, and the snapshot's `.git` predates them. There is therefore no
evidence source, canonical or off-repo, from which the destroyed commits'
hashes, parentage, authorship dates, or exact content can be
reconstructed or verified. The snapshot narrows what is unknown; it does
not close it.

---

## 2. Historical impact assessment

This section bounds the evidentiary value of any `VerificationResult`
produced by the pre-fix mechanism — i.e. any result produced before
`4c7ca8d`.

### 2.1 What a historical `VERIFIED` result proves

**Exactly one statement, and only for the path set actually supplied to
that call:**

> The paths supplied in that invocation were byte-identical to their
> content at the commit ref supplied in that invocation, with no
> committed or uncommitted drift at the time the check ran.

This is AD-033's own stated semantics and the claim bound restated in
AD-047 part 3. It is a statement about *declared, supplied paths* and
about *the ref that was supplied*. Nothing more.

### 2.2 What a historical `VERIFIED` result does **not** prove

- **Not complete freeze coverage.** `verify_freeze` inspects only the
  paths it is given. It had, and has, no independent source of truth for
  what the complete frozen set should have been — `covered_paths` is
  caller-supplied and there is no `FreezeId`-backed registry to check it
  against (AD-033). A result cannot distinguish a complete path set from
  a partial one.
- **Not methodology integrity.** A `VERIFIED` result never licensed the
  statement "the methodology was frozen." It licensed only "these named
  paths were frozen." AD-033 states this explicitly ("it proves nothing
  about whether the frozen methodology was itself correct, adequate, or
  reviewed"); AD-051 and AD-047 part 3 restate it. This boundary is
  **unchanged** by the defect and unchanged by its fix — it was never
  weaker or stronger than this.
- **Not the absence of undeclared drift.** A file that drifted but was
  never named in `covered_paths` was, and remains, invisible to the
  verifier.
- **Not commit provenance.** The verifier confirms fidelity *to whatever
  `commit_ref` it is handed*; it cannot confirm that ref is the one
  originally claimed as the freeze point. `commit_ref` is caller-supplied
  and unauthenticated.
- **Not — under the pre-fix mechanism — its own non-vacuity.** This is
  the specific evidentiary damage the defect did. Because an empty set
  returned the same status value as a real check, **a pre-fix `VERIFIED`
  status, read in isolation, establishes no lower bound on how many paths
  were checked.** It cannot self-certify that anything at all was
  examined. Only the separately recorded covered-path set for that
  invocation can establish that, which is precisely why AD-047's restated
  INV-3 requires the path list to be recorded alongside the result.

### 2.3 The consequence, stated plainly

For any pre-`4c7ca8d` `VERIFIED` result, its strength is the strength of
the covered-path set it was called with. Where that set is recorded, the
result is worth exactly what §2.1 says about that set. Where that set is
**not** recorded, the result's non-vacuity is **unknown from the result
alone** and must be established from other evidence, or else the result
must not be relied upon.

---

## 3. Scope assessment

### 3.1 Findings

**No archived governance record has been identified as having been
produced by an empty-coverage call.** Basis, all re-run for this record:

1. A content scan of `research_archive/` (all four project directories:
   `reference_v1`, `reference_v2_h1`, `reference_h3`,
   `positive_control_phase3`) and `experiments/` finds **no** reference
   to `verify_freeze`, `covered_paths`, `VerificationResult`,
   `FreezeStatus`, or any serialized freeze-verification artifact. No
   record **within that search space** cites a machine-produced
   `VerificationResult` at all.
   **Search-space correction, added at final acceptance audit.** That
   scan covered `research_archive/` and `experiments/` — it did **not**
   cover `docs/`. `docs/` does contain such references, and one is
   material: **AD-033** in
   [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) records two
   `verify_freeze` invocations *together with the covered paths each was
   given* (§3.3). An earlier draft of this record generalized this
   archive-scoped negative into a repository-wide one and concluded on
   that basis that no covered-path set was recorded anywhere; that
   generalization was wrong and is withdrawn here. The archive-scoped
   negative itself stands, re-run and unchanged.
2. Repository-wide, `verify_freeze` is imported at exactly two production
   call sites (the two gates in §1.2), plus tests. No script under
   `experiments/`, `tools/`, or `research_archive/` invokes either gate
   function; the only callers of
   `evaluate_signal_independence_gate` / `evaluate_economic_rationale_gate`
   are their own test files. H4 gate execution has not begun.
3. Every pre-fix test in `tests/test_governance_freeze_verifier.py`
   supplied a **non-empty** `covered_paths`. The two empty-input tests
   (`test_empty_covered_paths_is_unverifiable`,
   `test_empty_covered_paths_with_unresolvable_ref_reports_ref_error`)
   were added *by* the remediation at `4c7ca8d`, together with one
   propagation test in each gate suite. The defect was untested in both
   directions before then — no test pinned it, and no test would have
   failed had it been fixed earlier.

### 3.2 Status of that finding: verified negative, over a bounded search space

The scan above is **verified** as to what it covered: the canonical
repository at `4c7ca8d`, its reachable history, and its on-disk archive.
Within that space, no empty-coverage-derived record exists.

It is **unknown**, on every evidence source identified as of 2026-07-22,
whether any artifact of the history destroyed on 2026-07-21 was produced
by an empty-coverage call. Scoped precisely: the destroyed commits are
absent from the canonical repository and from all three off-repo sources
in §1.5, each of whose git history terminates at `3021c83`; no scan can
be run against content that is present in none of them. The claim made
here is that **no identified source can settle the question**, not that
the question is unanswerable in principle — an artifact surfacing from
some source not inventoried in §1.5 would be admissible evidence against
this statement, and this record should be read as inviting that rather
than foreclosing it.

The finding is therefore stated at its verified strength: **no known
record has been identified as having used empty coverage, and none is
expected given (2) above — but "no archived record was affected" is a
statement about the surviving corpus, not a proof about all history that
ever existed.**

### 3.3 The known historical `VERIFIED` executions, and their recorded inputs

Disclosed because these are the concrete pre-fix `VERIFIED` executions
against real corpus data this record could identify, and because §2.2's
last bullet applies to them directly — and, in this instance, is
answered by a separately recorded path set rather than left open.

Commit `917a6d5`'s own message states that `FreezeVerifier` was
"smoke-tested read-only against the real docs/research_archive corpus"
and "independently reproduced both real H3 freeze verdicts (verified,
matching the prior human audit)."

What is verified, with the cited record's own context restored: the
commit message says this, and the H3 freeze it refers to
([`research_archive/reference_h3/FREEZE_RECORD.md`](../research_archive/reference_h3/FREEZE_RECORD.md))
documents a real, non-empty set of **ten** frozen files — eight newly
committed plus two updated in the same commit — at commit
`07f0da379d8cccf06d17c34a51cbb557da047fef` (`07f0da3`), author date
2026-07-19. Three pieces of that record's context were omitted in earlier
drafts and are restored here because they bear directly on how far it can
be cited:

1. `FREEZE_RECORD.md`'s own §"What this record does not do" states that
   it "does not evaluate, approve, or modify H3's methodology, scoring
   logic, or any gate's PASS/HOLD/FAIL determination" and "solely
   establishes tamper-evident provenance." It is a provenance record, not
   a methodology warrant — consistent with, and not an exception to,
   §2.2's "not methodology integrity" bullet.
2. It is a **human-authored** record of a commit's file set. It records
   no `verify_freeze` invocation, no `covered_paths` argument, and no
   `VerificationResult`. Its ten-file list is therefore evidence of what
   *was frozen*, not evidence of what *was checked* by the smoke test
   below.
3. Its own §"Immutability" invokes the same supersession convention this
   record follows, citing `RESEARCH_GOVERNANCE_STANDARD.md` §5 — the same
   citation, and the same scope caveat, noted in this record's header.

**Correction, made at final acceptance audit: the covered path sets
*are* recorded, in canonical repository evidence.** An earlier draft of
this record stated that "the `covered_paths` argument actually passed in
that smoke test is not recorded anywhere in the repository." **That
statement is false and is withdrawn.** AD-033 in
[`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md), under its
"Smoke test evidence (Days 6-12, read-only)" paragraph, records **two**
invocations and names the covered paths of each:

| # | Freeze | `commit_ref` supplied | `covered_paths`, as recorded in AD-033 |
|---|---|---|---|
| 1 | Methodology freeze (AD-033 cites [`docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`](H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md)'s freeze-commit table) | `07f0da3` | `attempt_001_specification.md`, `REFERENCE_H3_PREVALIDATION_PLAN.md`, `REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`, `RESEARCH_GOVERNANCE_STANDARD.md` — **four paths** |
| 2 | Acceptance-criteria freeze (AD-033 cites [`research_archive/reference_h3/decision_log.md`](../research_archive/reference_h3/decision_log.md) Entry 15) | `a643993` | `H3_ACCEPTANCE_CRITERIA.md` — **one path** |

AD-033 states that both "resolved to their documented full hashes and
returned `VERIFIED`, with no drifted files and no errors."

**What this establishes, at its actual strength.**

1. **Both recorded path sets are non-empty.** On the evidence of AD-033,
   neither verdict was produced by an empty-coverage call. This is
   **documentary evidence**, and it replaces the earlier **inference**
   (that a real-corpus verdict was unlikely to have come from an empty
   path set); that inference is withdrawn as no longer needed, and the
   §6 Challenge 2 answer is corrected accordingly.
2. **The evidence is documentary, not machine-generated.** AD-033 is a
   human-authored prose record of what the runs were given and what they
   returned. **No serialized `VerificationResult` artifact from either
   run survives** — not in the canonical repository, and not in any
   off-repo source inventoried in §1.5. §2.2's last bullet is therefore
   **unchanged**: the verdicts still cannot self-certify their own
   coverage. It is AD-033, a separate record, that supplies the path
   list — which is precisely the discipline AD-047's restated INV-3
   requires, satisfied here by prose rather than by an artifact.
3. **AD-033 is not overstated.** Per
   [`RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md)
   §4, it is a **Level 1 self-attested** governance document, authored by
   the same party that ran the smoke tests and given no independent
   review. Its standing as **canonical git evidence** (§1.5 row 1) is a
   statement about provenance class — committed, hash-anchored, in
   `docs/` — not about reviewer independence. Nothing in this record
   treats it as verification by a second party.

**Correcting the relationship between `FREEZE_RECORD.md`'s ten files and
the recorded `covered_paths`.** Earlier drafts set the two side by side
without stating how they relate. They are **different sets**, and
neither is evidence of the other:

- `FREEZE_RECORD.md` lists the **ten files commit `07f0da3` froze** —
  eight newly committed plus two updated.
- AD-033's invocation 1 supplied **four** paths, sourced from
  `H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`'s freeze-commit table,
  **not** from `FREEZE_RECORD.md`.
- All four are members of the ten. The set actually checked was
  therefore a **proper subset: four of ten.** Six frozen files —
  `H3_GOVERNANCE_REMEDIATION_ADDENDUM.md`,
  `H3_GOVERNANCE_COMPLIANCE_AUDIT.md`, the three 2026-07-19 gate review
  records, and `research_archive/reference_h3/README.md` — were **not**
  covered by that check, and the `VERIFIED` verdict says nothing about
  them.
- This is §4.2's "**cardinality, not relevance**" limitation instanced
  on real data: a true, non-vacuous answer about four supplied paths,
  which is neither a statement about the full freeze nor a defect in the
  verifier. Under §2.1 the verdict is worth exactly that and no more.
- Invocation 2's single path, `H3_ACCEPTANCE_CRITERIA.md`, belongs to a
  **different** freeze (`a643993`) and does not appear in
  `FREEZE_RECORD.md`'s list at all. The two invocations must not be
  merged into one coverage claim.

**What remains unknown — narrowed, not closed.** Only this: whether the
arguments literally passed at the terminal were the paths AD-033
records, since no machine-generated artifact survives against which to
check the prose. That is the ordinary residual of a Level 1 self-attested
record. It is **not** the earlier claim that the coverage set is
unknown; that claim was false and is withdrawn.

Nothing in the archive depends on either smoke test: they are cited in
commit `917a6d5`'s message and in AD-033 as development-time evidence
for an interface decision, not as a gate determination, a freeze
approval, or an archived research result. No gate determination, freeze
record, or archived decision rests on either verdict — §3.1 item 2
independently confirms that neither gate has ever been invoked outside
its own test files.

### 3.4 A prior, dated statement on the same question — and its limits

**Evidence class: off-repo (§1.5 rows 3-4), not canonical git
evidence.** The passage below is quoted from the surviving untracked
copy of the destroyed 2026-07-21 deviation record described in §1.4; it
exists in no commit, in the canonical repository or in any inventoried
snapshot. It is read here as a dated statement of what its author
believed, not as a verified artifact.

The destroyed 2026-07-21 deviation record (§1.4) stated, in its §4:

> "No existing `VERIFIED` result anywhere in this repository was produced
> from an empty covered-paths list, because the subsystem has never run
> against a real research cycle."

This is consistent with §3.1's independent re-scan a day later, and is
recorded here as corroboration from a different date. Two limits are
disclosed with it:

1. It is **self-attested** in an unreviewed record whose own §6 states it
   "has had no independent review," and it survives only as an untracked
   off-repo copy (§1.4, §1.5 rows 3-4). It is not treated as
   verification. Rows 3 and 4 being byte-identical adds nothing: row 4 is
   a mirror of row 3, so the agreement between them is not corroboration.
2. Its stated *reason* ("never run against a real research cycle") is in
   tension, on its face, with `917a6d5`'s read-only smoke test against
   the real archive corpus (§3.3). The two reconcile only under the
   narrower reading "never run inside a gate execution of a research
   cycle" — which is true and is independently confirmed by §3.1 item 2.
   The looser reading is not supportable, and the corroboration is
   accepted only at the narrower one.

---

## 4. Remediation boundary

The remediation is commit `4c7ca8d`, recorded as **AD-051**: an additive
early return in `verify_freeze` mapping an empty `covered_paths` to
`FreezeStatus.UNVERIFIABLE`, plus four additive tests and one docstring
sentence. No existing test was modified; neither gate required any code
change.

### 4.1 What the remediation does

- It prevents **future** false `VERIFIED` results arising from an empty
  `covered_paths`. From `4c7ca8d` forward, zero-evidence verification
  returns `UNVERIFIABLE` and cannot be mistaken for success.
- Both gates inherit that behavior with no code of their own, because
  both already branch on `is not VERIFIED`. This is demonstrated by a
  propagation test in each gate's suite, not merely asserted.
- `resolved_hash` is deliberately preserved on the empty-coverage return,
  so `resolved_hash is None` continues to mean exactly "the commit ref
  did not resolve" and nothing else.

### 4.2 What the remediation does **not** do

- **It does not rewrite history.** No past artifact, document, commit, or
  archived record is altered, re-run, or re-interpreted by it.
- **It does not upgrade old `VerificationResult`s.** A `VERIFIED`
  produced before `4c7ca8d` is not made stronger, more trustworthy, or
  retroactively guarded by a change to code that ran after it. Its
  strength is fixed at what §2.1-§2.3 describe and cannot be improved by
  any later commit.
- **It does not prove coverage adequacy.** The guard checks
  **cardinality, not relevance**. `covered_paths=["README.md"]` passes it
  and verifies faithfully against that one file — a true answer to a
  question nobody meaning "was the methodology frozen?" intended to ask.
  An incomplete set is mechanically indistinguishable from a complete
  one. Drift outside declared coverage remains invisible.
- **It does not authenticate the commit reference.** Substituting a more
  favorable commit as "the freeze commit" is a provenance problem one
  layer above anything `freeze_verifier.py` can address.
- **It does not discharge this disclosure**, and this disclosure does not
  substitute for it. AD-051's own "Scope" paragraph and the remediation
  proposal §7.4 both state this; it is restated here from the disclosure
  side so neither document can be cited as having closed both halves.

Coverage **adequacy** remains a human review judgment with no mechanism
behind it anywhere in this codebase. No future document may cite AD-051,
this record, or a `VERIFIED` result as evidence that a methodology was
frozen — only that named paths were.

---

## 5. Governance status

| Item | Status |
|---|---|
| **PR0 technical defect** (empty `covered_paths` ⇒ `VERIFIED`) | **Closed.** Fixed at `4c7ca8d`; recorded as AD-051; guarded and tested in both directions, with gate-level propagation proven. |
| **A-1, limb 1 — disclosure obligation** (AD-047 part 1; Resolution §4.1) | **Satisfied by this record.** A dated disclosure now exists in `docs/`, stating that the defect existed, when it was identified, what the old mechanism proved, and what archived results may and may not mean. |
| **A-1, limb 2 — "the PR0 ruling is closed or confirmed obsolete"** (Resolution §4.1) | **Open.** Only a *proposed* disposition exists (next row); no accountable reviewer has ruled. **A-1 as a whole is therefore not discharged, and Step 9 remains blocked** until that decision exists in writing. This record cannot close this limb and does not claim to. |
| **The 2026-07-21 PR0 ruling request** | **Proposed disposition: obsolete — not confirmed, and not ruled on by this record.** This record has no authority to close a ruling request and does not purport to. The proposal, with its basis: the original record asked for a ruling on whether the fix should stay inside PR0 or be split into its own change; the change was in fact split out and landed as its own increment with its own proposal (`ced8636`) and its own AD (AD-051), which appears to moot the question. Its second item — acknowledgement that the frozen roadmap's PR0 file list was inaccurate — appears unactionable as written, because `docs/PHASE_4_IMPLEMENTATION_ROADMAP.md` exists in no reachable ref, in no working tree of the canonical repository, and in no off-repo source inventoried in §1.5, so the list it refers to cannot be examined. Both points are stated **off-repo-sourced** (the request itself survives only per §1.5 rows 3-4) and remain open pending a ruling by the accountable reviewer. Until that ruling is recorded, A-1 limb 2 above stays open and Step 9 stays blocked. |
| **Remaining limitation 1 — coverage adequacy** | **Open, disclosed, unmechanized.** Non-emptiness is necessary and nowhere near sufficient. No mechanism in this codebase assesses relevance or completeness of a covered-path set; it is a human review judgment (AD-051; AD-047 §"why the guard is not the whole answer"). |
| **Remaining limitation 2 — commit provenance** | **Open, disclosed, unmechanized.** `commit_ref` is caller-supplied and unauthenticated. Draft AD-048's hash-chain-plus-human-anchor is the mechanism aimed at this problem; it is not built. |
| **Evidentiary status of the destroyed 2026-07-21 history** | **Unknown on all evidence sources identified as of 2026-07-22, disclosed as such** (§1.5, §3.2). The destroyed commits are absent from the canonical repository and from every inventoried off-repo source, each of whose git history terminates at `3021c83`; the forensic snapshot corroborates history up to that point but restores none of the missing provenance. Not closable by any work within this evidence base — stated as a bound on the sources searched, not as a claim of unknowability in principle. |

**Consequential requirement, stated once.** Because a pre-`4c7ca8d`
`VERIFIED` cannot self-certify non-vacuity (§2.2), any future artifact
citing a `VerificationResult` — historical or new — must record the
covered-path list alongside the status. This is AD-047's restated INV-3
and it is a condition on citation, not a new mechanism introduced here.

---

## 6. Adversarial review of this record

Four challenges were put to this document and the wording adjusted until
each is answered by evidence rather than by assertion. They are recorded
so a later reader can re-run them.

**Challenge 1 — "This document rewrites history."**
*Answer:* It edits nothing. No prior document is amended, corrected, or
withdrawn; §1.4's correction of AD-047's "exists in no reachable ref"
characterization is stated as a new dated finding in a new file, with the
verified portion of the prior claim affirmed and only the unverified
portion narrowed. That is the supersession convention of Standard §5,
applied by extension to `docs/` as the header states, with
`ARCHITECTURE_DECISIONS.md`'s preamble as the governing rule for `docs/`
and AD-036/AD-040/AD-044/AD-045 as precedent instances — not, as an
earlier draft of this record implied, four ADs that state a correction
discipline. The record adds no favorable reinterpretation of any past
result; §2 and §4.2 exist specifically to forbid one.

**Challenge 2 — "It claims more than the evidence supports."**
*Answer:* Each claim is bound to its check. Source-level claims cite the
revision and line range read. The scope finding is stated as a verified
negative **over an explicitly named search space** (§3.2) rather than as
a universal, and the one thing that would have made it universal — the
destroyed history — is declared unknown *over the evidence base
inventoried in §1.5*, not unknowable in principle, so that a source
surfacing later can contradict this record rather than be argued away by
it. **Corrected at final acceptance audit:** an earlier draft answered
this challenge by pointing to a single labelled inference (§3.3, that a
real-corpus smoke test probably used a non-empty path set). That
inference has been **withdrawn and replaced by documentary evidence** —
AD-033 records the covered path set of both smoke-test invocations
(§3.3) — so the answer no longer rests on it. What replaces it is
bounded in turn: AD-033 is Level 1 self-attested, no serialized
`VerificationResult` survives, and the four-of-ten subset relationship
to `FREEZE_RECORD.md` is stated rather than glossed. Where a prior
document's statement is used as support, §3.4 discloses that it is
self-attested, unreviewed, and accepted only under a narrowed reading.

**Challenge 3 — "It hides unknown or inconvenient archived results."**
*Answer:* **This challenge previously failed, and the failure is
disclosed rather than quietly repaired.** Until the final acceptance
audit, this record asserted in §3.3 that the smoke test's
`covered_paths` argument was "not recorded anywhere in the repository."
It was recorded — in AD-033, in `docs/`, committed and hash-anchored.
The record missed it because its own §3.1 scan searched
`research_archive/` and `experiments/` and the conclusion was
generalized past that search space (§3.1's search-space correction).
The practical effect was to overstate what was unknown and to rest a
paragraph on inference where canonical evidence existed. Both the false
statement and the reason it was made are now stated in the sections that
carried them, in place of a silent fix. That an audit had to find this
is itself evidence for the residual weakness disclosed at the end of
this section.

With that correction made, the items an auditor would most want and that
a self-serving version would omit are present and volunteered: the
surviving off-repo copies of a record elsewhere described as destroyed
(§1.4); the **read-only forensic snapshot of the pre-incident machine
state**, disclosed with what it does and does not restore, including the
fact that its own `freeze_verifier.py` still carries the defect (§1.5);
the two known real-corpus `VERIFIED` executions, including the fact that
the checked set was a **four-of-ten proper subset** of the files that
freeze actually covered and that no serialized artifact of either run
survives (§3.3); and the internal tension between the 2026-07-21 record's
stated reason and those smoke tests (§3.4). None of the four strengthens
this record's position; each is disclosed because omitting it would be
the defect. §1.5 further labels every claim's evidence class, so that no
off-repo artifact can be read as carrying canonical git standing.

**Challenge 4 — "It conflates the fix with the disclosure."**
*Answer:* They are separated structurally and asserted separately in
three places: the header ("not a remediation"), §4.2's final bullet, and
§5's table, which closes the technical defect and the disclosure
obligation as two distinct rows and leaves two further rows open.
Critically, §4.2 states the fix does **not** improve any historical
result — the exact conflation an auditor would test for, refused
explicitly rather than left to inference.

**Residual weakness, disclosed rather than resolved.** This record is
itself self-attested and has had no independent review; per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4 ("Reviewer Independence
Model", Level 3), which states that "no Level 3 review has ever been
performed on this platform," this record is a Level 1 artifact and is
labelled as such rather than described as independent. It documents a
scan **it performed itself**. An auditor wanting independent assurance
must re-run §3.1's scan against `4c7ca8d` and re-inspect §1.5's four
locations directly; the searches and the exact commands are named in
both places precisely so that this is possible without trusting this
document.
