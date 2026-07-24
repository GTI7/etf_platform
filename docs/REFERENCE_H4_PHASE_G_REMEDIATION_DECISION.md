# `reference_h4` — Phase G Remediation Decision

**Formal governance decision. Decision-only: no code was written, executed,
or modified to produce it, and no artifact under
`research_archive/reference_h4/` was edited, moved, or deleted.**

**Date:** 2026-07-25
**Subject of review:** the `reference_h4` cycle's *governance controls* —
`research_archive/reference_h4/` (all 13 files),
`research_archive/reference_h4/transition_records.jsonl` (7 records),
commits `985227e`…`29553b7` on branch
`research/reference-h4-first-governed-cycle`, and the platform machinery
those artifacts exercised (`core/research/lifecycle.py`,
`core/governance/decision_recorder.py`,
`core/governance/independence_linter.py`,
`tests/test_repository_integrity_snapshot.py`).
**Standard applied:** `docs/RESEARCH_GOVERNANCE_STANDARD.md` v1.1.

**Reviewer-independence disclosure (read before anything below).** This is a
**Level 2** review — procedurally independent of the sessions that ran the
`reference_h4` cycle, **not organizationally independent** (Standard §4). No
Level 3 reviewer exists or is available on this platform. Where this
document uses institutional vocabulary ("ownership," "authority"), those
words describe *roles*, not distinct organizational bodies: this platform
operates with a single human operator directing all research and all review
(Standard §4, Level 3, "Limitations"). An external auditor should weight
this document accordingly.

---

## 0. What this document does not do

It does **not** reopen, revise, qualify, or invalidate the `reference_h4`
research conclusion. `research_archive/reference_h4/decision_record.md`
records **PASS**, and that outcome stands unchanged, for the reasons set out
at N-1 in §6 below. Under Standard §3 ("How changes are handled after
freeze") the trigger for invalidating a cycle is a change to a frozen
element; no frozen element changed. Under Standard §7 the trigger for a new
cycle is FAIL or INCONCLUSIVE; `reference_h4` is neither.

It also does not amend the Standard. Several findings below recommend
amendments; a Standard amendment is a new dated version (v1.2) authored
separately, per that document's own revision discipline.

It does not authorize any downstream use of the `reference_h4` result.
`decision_record.md`'s closing paragraph already withholds that
authorization, and nothing here grants it.

## 1. What "Phase G" means here

`reference_h4` completed the **research** lifecycle's Phases 1–8 (Standard
§2). "Phase G" is **not** a ninth research phase and does not extend the
Standard's lifecycle. It is the next lettered **platform-engineering** phase
in the Phase A–F sequence (`docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`,
`docs/PHASE_4_PHASE_F_ARCHITECTURE_RESOLUTION.md`); no document in `docs/`
currently uses the label, so it is free. Keeping the two sequences separate
is deliberate: the research lifecycle must not acquire a "remediation phase"
that a future cycle could be tempted to route a bad result through.

**Premise of this decision, stated plainly.** `reference_h4` was, by its own
`hypothesis.md`, an instrument test: its stated purpose was proving the
Phase A–E governance machinery end-to-end against the real repository for
the first time. It succeeded at that, and the success is exactly why this
document exists — a first real run is the only thing that can show which
controls are load-bearing and which are prose. **The science passed; the
control environment did not fully hold.** Both statements are findings of
this decision, and neither weakens the other.

## 2. Evidence base

Every finding below cites a file, a line, a commit, or a command output.
Verification performed for this decision:

| Check | Command / source | Result |
|---|---|---|
| Chain integrity | `verify_chain_intact(transition_records.jsonl)` | `True`, 7 contiguous records |
| Chain anchoring | `verify_chain_anchored(path, 6, sha256:cb1a04c7…bab7d59)` | `True` (seq 6 only — see D-6) |
| Head record hash | `hash_record(row[7])` | `sha256:50a27d2a09963e098794e750b2502c1d362dac376ab6a602927cee4942c390d8` |
| Freeze status per record | `transition_records.jsonl` seq 4–7 | `verified` at every bracket, freeze commit `7b0e816` unchanged |
| Reproduction | `research_archive/reference_h4/reproduction_record.json` | `verified` at pinned commit `3d586de` |
| Protected-file fixture | `git diff master -- tests/fixtures/protected_file_hashes.json` | empty; 36 entries, **zero** matching `reference_h4` |
| Independence linter | `lint()` over the archive's 8 `.md` files | 15 raw findings, all adjudicated at N-6 |
| `ArchiveVerifier` | `grep -rn ArchiveVerifier core/ tools/ tests/ --include=*.py` | no implementation (docstring references only) |
| Full suite | `python -m pytest tests/ -q` | 802 passed, 1 skipped, 1 xfailed |

## 3. Classification framework

Three categories, as required, plus one severity scale applied uniformly.

- **Category 1 — Cycle-specific deviations requiring disclosure.** A
  departure from the Standard that actually occurred in `reference_h4`.
  Remedy is disclosure and, where possible, a compensating record. Not a
  code change.
- **Category 2 — Platform-wide governance defects requiring
  ADR/remediation.** A structural gap that caused, or would independently
  cause, a Category 1 deviation on *any* cycle. Remedy is an ADR and, where
  the ADR so decides, an implementation.
- **Category 3 — Non-findings rejected by evidence.** A plausible charge
  that the evidence does not support. Recorded so it is not re-raised.

**Severity.** `Critical` — the archived conclusion, the freeze, the chain's
integrity, or the reproduction is impugned. `High` — a mandatory
Standard-required control was not obtained at the point the Standard
requires it, and the protection it provides cannot be fully reconstructed
afterwards. `Medium` — a mandatory control was not obtained at the required
point but was substantively obtained later, or a real gap exists whose
exploitation would be detectable. `Low` — the process record is incomplete;
no protection was lost.

**No finding in this document is Critical.** Nothing found impugns the
result, the freeze, the chain, or the reproduction.

---

## 4. Category 1 — Cycle-specific deviations requiring disclosure

### D-1 — Methodology Freeze was confirmed at Level 1; the Level 2 confirmation arrived after Validation — **High**

Standard §2 Phase 4, Approval state: *"Level 2 minimum, confirming the
freeze document is complete against Section 3's checklist and that no
element was selected or adjusted using outcome data. **Freeze is not
effective until this confirmation is recorded.**"*

`transition_records.jsonl` seq 4 (Methodology Freeze → Implementation,
commit `7b0e816`, `2026-07-25T00:30:00Z`) records
`authorization.reviewer_level = "Level 1 (self-review)"`. The Level 2 freeze
confirmation does exist —
`reviewer_reports/2026-07-25_level2_adversarial_review.md` §(b) walks all
eight §3 items and finds no gap — but it was authored after Phase 6
Validation had run and its output was archived (commit `258ee2b`, after
`3d586de`). Phases 5 and 6 therefore executed under a freeze that, by the
Standard's own words, was not yet effective.

This ordering was pre-stated in `methodology.md`:120–123 ("Level 1
self-review confirms completeness now; a separate Level 2 adversarial review
is recorded in `reviewer_reports/` … before this freeze is relied upon for
the Decision"). It was therefore *visible*, but it was written as
compliance rather than routed through §8 as an exception — see D-5.

**Mitigation.** When the Level 2 review did occur it performed the full
substantive check the Standard asks for, including an element-by-element
drift check of `validate_h4_kurtosis.py` against `methodology.md`
deliberately conducted without reading the author's own conformance note.

**Residual risk, unrecoverable for this cycle.** The one property the
Standard's ordering exists to guarantee — that the freeze was confirmed
complete by a reviewer who had *not* seen the outcome — cannot be
reconstructed after the fact. The Level 2 reviewer read `methodology.md`
knowing the result was PASS. No later action can restore that condition for
`reference_h4`; it can only be guaranteed for future cycles (R-1).

### D-2 — Phase 2 proceeded to Pre-validation without the required Level 2 — **Medium**

Standard §2 Phase 2, Approval state: *"Level 1 … minimum; **Level 2 required
before the proposal may proceed to Pre-validation.**"*

`research_proposal.md`:55–58 states the opposite: *"Level 2 is not required
to progress into Pre-validation and is not claimed here."* `seq 2` is
recorded at Level 1. The deviation is compounded by the archived artifact
**misstating the Standard's requirement**, which is materially different
from disclosing a known gap: a future reader of the archive alone would
conclude the cycle was compliant.

### D-3 — Phase 3 gates were approved at Level 1 — **Medium**

Standard §2 Phase 3, Approval state: *"**Level 2 minimum for each individual
gate within this phase.**"* `prevalidation_plan.md`:93–98 states Level 2 is
*"not required here to proceed into Methodology Freeze."* `seq 3` is
recorded at Level 1. Same shape as D-2, including the misstatement.

### D-4 — Validation was approved at Level 1 at the transition — **Medium**

Standard §2 Phase 6, Approval state: *"Level 2 minimum."* `seq 6`
(Validation → Decision, commit `3d586de`) is recorded at Level 1. The Level 2
review of the Validation arithmetic — a bit-for-bit re-derivation from raw
`sqlite3` with no import of the implementation — is genuine and complete,
but landed at commit `258ee2b`, after the transition it was required to
authorize. Substantively obtained late; not obtained at the gate.

### D-5 — No §8 exception record exists for D-1…D-4 — **Medium**

Standard §8 permits every one of D-1…D-4 *as an exception*, and requires all
three of: a documented reason, an impact assessment naming the specific
protection weakened, and an approval record at Level 2 minimum that is **not
self-approved by the party requesting it** — plus time-boxing. Level 3 is
required "where available" for any exception touching Methodology Freeze,
Validation, or Decision; it is unavailable here, which is itself disclosed
(`decision_record.md`:16–21).

`decision_log.md` contains no exception record of any kind. This is the
finding that converts D-1…D-4 from *deferred controls* into *undisclosed
deviations*: the cycle's artifacts consistently characterize the Level 2
deferrals as permitted by the Standard rather than as exceptions to it.
**This decision is the compensating record**, at Level 2, authored by a
party that did not run the cycle — which satisfies §8's non-self-approval
requirement to the maximum degree this platform can currently reach.

### D-6 — The chain head (`seq 7`, Decision → Archive) is unanchored — **Medium**

`decision_recorder.py`:19–35 states the threat model directly:
`verify_chain_intact()` "proves nothing about the tail," and
`verify_chain_anchored()` closes that gap "only up to the cited sequence
number." `decision_log.md`'s "Chain anchors" table cites sequences **1–6**.
`decision_log.md` was committed at `8bc3f93` (Phase 7); `seq 7` was appended
afterwards at `29553b7`. Verified for this decision:
`verify_chain_anchored(path, 6, sha256:cb1a04c7…)` → `True`.

Consequence: the single record that proves the cycle actually reached
Archive is the single record with no external anchor. Truncating it leaves a
valid, correctly chained, internally consistent 6-record file.

**Compensating record, effective on commit of this document.** The head
record's canonical hash is published here, outside the archive:

> `reference_h4` `transition_records.jsonl`, sequence **7**
> (Decision → Archive), record hash
> **`sha256:50a27d2a09963e098794e750b2502c1d362dac376ab6a602927cee4942c390d8`**,
> predecessor `sha256:cb1a04c7…bab7d59`, commit `8bc3f93`,
> `recorded_at 2026-07-25T01:05:00Z`.

This is an anchor of the same strength as `decision_log.md`'s — a
hand-transcribed citation, per AD-065 — and no stronger. It closes the
cycle-specific gap. The structural cause is G-4.

### D-7 — `decision_log.md` is not literally append-only; it has no Phase 8 entry — **Low**

Standard §5 makes `decision_log.md` "the one file in this package that is
genuinely append-only in the literal sense." It was composed in a single
pass at Phase 7. **This is already self-disclosed**, in explicit and
unflattering terms, at `decision_log.md`:7–15; it is recorded here only so
the register is complete, and requires no further disclosure. A second,
undisclosed consequence does follow from it: because the file was finalized
at Phase 7, the Decision → Archive event — a decision point §5 requires the
log to contain — was never entered. See D-6 and G-7.

### D-8 — Phase 8's completeness check was not recorded — **Low**

Standard §2 Phase 8, Approval state: *"A completeness check against Section
5's manifest (Level 1 sufficient — this is a checklist, not a judgment
call)."* All seven §5 items are physically present under
`research_archive/reference_h4/`, confirmed for this decision. No artifact
records that the check was performed, and `29553b7`'s message does not
assert it. Structural cause: G-3 (the component named to perform this check
does not exist). **This decision performs and records that check: the
package is complete against §5.**

### D-9 — The protected-file exclusion for `reference_h4` has expired by its own terms — **Medium**

`tests/test_repository_integrity_snapshot.py`:76–84 excludes
`research_archive/reference_h4/`, `experiments/run_reference_h4_lifecycle.py`,
and `experiments/validate_h4_kurtosis.py` from the Phase 0 gained/lost-files
check — explicitly *"until this cycle reaches Phase 8 Archive and is
closed."* The cycle reached Archive at `29553b7` on 2026-07-25. The
exclusion clauses (lines 100–106) are still in force, and
`tests/fixtures/protected_file_hashes.json` contains **zero** `reference_h4`
entries.

Consequence, verified: any file under `research_archive/reference_h4/` can
today be edited, added, or deleted and the full suite still passes (802
passed). The `reference_h4` archive is currently protected by **no automated
integrity control**. This is the finding that qualifies the immutability
determination in §8. Structural cause: G-5.

---

## 5. Category 2 — Platform-wide governance defects requiring ADR/remediation

### G-1 — Nothing on the platform adjudicates a phase's minimum review level — **High**

`core/research/lifecycle.py`:86–96 and
`core/governance/decision_recorder.py`:97–107 both state, as deliberate
design, that `reviewer_level` is *"recorded, never adjudicated"* — not
parsed, not compared, no hierarchy enforced. `advance_phase()` enforces
single-step ordering and ambiguity/override acknowledgement, and accepts
`"Level 1 (self-review)"` for a Phase 4 or Phase 6 transition without
objection.

The defect is **not** in `decision_recorder` — its scope is correctly
narrow, and Governance may not import Validation. The defect is that
Standard §2's phase → minimum-review-level table exists **nowhere in code**,
so no component can hold it. This is the direct structural cause of D-1
through D-4: four mandatory controls were missed and every automated check
on the platform passed. An ADR must decide where that authority lives; the
natural candidate is `core/research/`, adjacent to `advance_phase()`, which
already holds transition-legality authority.

### G-2 — §8 exceptions have no artifact type, no schema, and no enforcement point — **Medium**

Standard §8 requires exception records to live in `decision_log.md`. That
file is hand-authored prose that no module reads or writes —
`decision_recorder.py`:33–35: *"This module never reads, parses, or writes
`decision_log.md`."* An exception is therefore impossible to require,
validate, count, or detect the absence of. D-5 is the predictable result:
the cheapest path for a cycle under time pressure is to describe a deferral
as compliance, because nothing asks it to do otherwise.

### G-3 — `ArchiveVerifier` is named in three places and implemented in none — **Medium**

Referenced by `core/governance/__init__.py`:4,13,
`tools/archive_manifest.py`:10, and
`docs/PLATFORM_ARCHITECTURE_V1.md` §4.4. `grep` over `core/`, `tools/`, and
`tests/` returns no implementation. `decision_recorder.py`:78–82 states
"archive completeness is never inspected." Standard §2 Phase 8 requires a
completeness check with no mechanism available to perform it — so D-8 recurs
on every cycle, not only this one. The ADR should either commission the
component or record its deferral as a time-boxed §8 exception; leaving it
named-but-absent is the one option the Standard does not allow.

### G-4 — Anchoring the chain head is structurally impossible under the current artifact ordering — **Medium**

The anchor lives in a hand-authored `decision_log.md` committed at Phase 7;
the final record is appended at Phase 8. No ordering of the current
artifacts lets the file that anchors records 1…n−1 also anchor record n.
D-6 is therefore not operator error and will recur on every cycle. AD-065
already accepted that the anchor receipt is a transcription rather than a
machine-verified anchor; this defect is narrower and separate — the head
record is not transcribed **at all**. Candidate remedies for the ADR: a
post-Archive anchor addendum artifact, or an anchor file written outside the
cycle package after the final append.

### G-5 — A closed cycle has no path back into protected status — **Medium**

`tests/fixtures/protected_file_hashes.json` is immutable Phase-0 data by
that test's own docstring (lines 5–13) and by standing convention: a new
legitimate file gets a test-code exclusion clause, never a fixture edit.
That convention is correct and was followed (see N-3) — but it has no
terminal state. A cycle's evidence is excluded while the cycle is open, and
when the cycle closes there is no fixture it may enter. The only mechanism
available is a prose "until Phase 8" condition inside a test docstring,
which nothing enforces and nothing expires. G-5 produces D-9, and will
produce the identical finding for `positive_control_phase3` the moment that
cycle closes. Candidate remedy for the ADR: a second, append-only
closed-cycle hash fixture, structurally distinct from the Phase-0 snapshot
so the Phase-0 immutability rule is not weakened to achieve it.

### G-6 — `IndependenceLabelLinter` is built and wired to nothing — **Low**

`core/governance/independence_linter.py` implements Standard §4's "no
document may describe a Level 2 review using the unqualified word
'independent'" rule. Its only callers are
`tests/test_governance_independence_linter.py` (unit tests over synthetic
input) and an import-existence assertion in
`tests/test_domain_packages_import.py`. No test, tool, or phase gate runs it
over `research_archive/` or `docs/`. It was never executed against
`reference_h4` during the cycle. A control that exists and is never
executed is not a control. Remediation should also address the heuristic's
false-positive rate on statistical usages of "independent" (see N-6),
since an unusable signal will simply be switched off.

### G-7 — Standard §5 and §2 Phase 8 conflict on post-Archive appends to `decision_log.md` — **Low**

Standard §5 designates `decision_log.md` as literally append-only ("new
entries added, nothing removed or edited"). Standard §2 Phase 8 states
"Archive is append-only. A correction to any archived artifact is added as a
new, separately dated artifact; **no existing archived file is edited in
place**." Whether appending an entry to a closed cycle's `decision_log.md`
is a permitted append or a prohibited in-place edit is genuinely
undetermined by the text.

**This decision adopts the conservative reading** — after Phase 8 the whole
package is closed and §2 Phase 8 governs, so a post-Archive disclosure lands
as a **new dated artifact**, never as an append to `decision_log.md`. That
reading is what §9 relies on. The ambiguity should be resolved explicitly in
the Standard rather than left to each reader; folding it into R-2's ADR is
the efficient path.

---

## 6. Category 3 — Non-findings rejected by evidence

### N-1 — "The late freeze confirmation makes the PASS unsafe." **Rejected.**

The Level 2 review re-derived every reported figure bit-for-bit from raw
`sqlite3`, with no import of `validate_h4_kurtosis.py`, cross-checked
against a second formula path, and matched to full float precision on all 25
per-ETF values, `n=2473`, the median, and both CI bounds. It confirmed all
eight §3 items fixed with no hidden degree of freedom and found no
implementation drift element by element. `run_reproduction()` returned
`VERIFIED` at a pinned detached worktree with the offline guard active.
`verify_freeze()` returned `verified` at every bracket from `seq 4` through
`seq 7`, against the unchanged freeze commit `7b0e816`. The CI lower bound
(7.611) clears the frozen threshold (0) by a margin no disclosed limitation
plausibly closes. D-1's injury is to the *ordering guarantee*, which is a
process property; it is not evidence of a defect in the result, and this
decision declines to manufacture one.

### N-2 — "Six of seven transitions have empty `gate_outcomes`, so gates were skipped." **Rejected.**

`methodology.md` §7 froze exactly **one** decision rule, so exactly one
measurable criterion exists in this cycle. The one real gate
(`economic_rationale`, CI lower bound vs. frozen threshold 0, direction
`at_least`) ran at the one transition that has one — `seq 6`, status `pass`.
Recording gate outcomes at transitions with no frozen criterion would have
manufactured evidence of evaluation that did not occur, which is a strictly
worse defect than the emptiness it would conceal. The empty arrays are the
correct output.

### N-3 — "The protected-file fixture was edited to accommodate `reference_h4`." **Rejected.**

`git diff master -- tests/fixtures/protected_file_hashes.json` is empty. The
fixture holds 36 entries; none matches `reference_h4`. Commits `730d939` and
`ec3ed22` modify only `tests/test_repository_integrity_snapshot.py`, adding
exclusion clauses that follow the documented `positive_control_phase3`
precedent and say so. The convention was honoured exactly. The separate,
real finding is that the clause has now **expired** (D-9), not that creating
it was wrong.

### N-4 — "Deleting a test mid-cycle (`511c164`) weakened a governance control." **Rejected.**

`test_reference_h4_archive_has_no_evidence_subdirectories_scaffolded`
asserted that no evidence subdirectories existed under
`research_archive/reference_h4/` — a precondition of B-3b's identity-only
registration. Populating those directories is the intended behaviour of
running a real cycle, so the test's premise became intentionally false, not
regressed. The removal is recorded in place as a comment block stating the
reason and the date, and no other assertion in that file was touched.

### N-5 — "`reference_h4` should have been registered in the Research Lineage Register." **Rejected.**

`docs/RESEARCH_LINEAGE_REGISTER.md` requires an entry "before that cycle's
first *correction* attempt (as distinct from its baseline construction) is
logged." `prevalidation_plan.md` logs exactly one attempt — attempt 1, the
baseline construction, carried to freeze unrevised. No correction attempt
was ever opened, so no registration obligation arose.

### N-6 — "The archive describes a Level 2 review as unqualified 'independent'." **Rejected.**

Running `core.governance.independence_linter.lint()` over the archive's
eight markdown files returns 15 findings. Every one was read individually.
They divide into: (a) **statistical** usages unrelated to reviewer
independence — `methodology.md`:92 "independent draws across the 25 ETFs";
the review's "second independent formula path"; (b) reviewer-independence
statements that **are** qualified, just outside the linter's same-line /
previous-line window — `decision_record.md`:12–14 reads "Level 2
(AI-assisted adversarial review, procedurally independent, **not**
organizationally independent per … Section 4)"; and (c) sentences whose
subject is precisely the *absence* of independence
(`decision_log.md`:83, "No external, organizationally independent human
reviewer exists on this platform"). Standard §4's substantive rule was
followed throughout, conspicuously so. The finding count measures the
linter's own acknowledged heuristic (`independence_linter.py`:15,39), which
is a reason to wire and tune it (G-6) — not a charge against this cycle.

### N-7 — "`reference_h4` is missing from `docs/RESEARCH_ARCHIVE_MANIFEST.md`." **Rejected.**

That document defines the *schema* of `archive_manifest.json`; it does not
maintain a roster of archived cycles, and its list of three names is an
applicability carve-out for pre-standard archives, not an index.
`reference_h4` has a conforming manifest (`schema_version` 1, `project_id`
`reference_h4`, `lifecycle_version` `v1`).

---

## 7. Required outputs — summary

| Output | Determination |
|---|---|
| **Proposed artifact path** | `docs/REFERENCE_H4_PHASE_G_REMEDIATION_DECISION.md` (this file). Companion pointer recommended at `research_archive/reference_h4/reviewer_reports/2026-07-25_phase_g_remediation_decision.md` — additive and permitted, but see §8. |
| **Governance classification** | Platform-level governance remediation decision, Level 2, decision-only. Not a research artifact; not an amendment to the Standard; not a `decision_log.md` entry. Phase G is a platform-engineering phase, not a research lifecycle phase (§1). |
| **Severity — overall** | **Medium-High.** Highest single findings: D-1 and G-1 (High). No Critical finding: the archived conclusion, the freeze, the chain integrity, and the reproduction are all intact and independently verified. |
| **Remediation ownership** | §10 register. All roles currently discharged by the single human operator (Standard §4) — stated so the register is not read as implying an organization that does not exist. |
| **Does the `reference_h4` archive remain immutable?** | **Yes, as a matter of governance — with a disclosed enforcement gap.** See §8. |
| **Is a new `reference_h5` cycle required?** | **No.** See §9. |

## 8. Archive immutability determination

**`research_archive/reference_h4/` remains immutable.** No file in it may be
edited, moved, or deleted, and nothing in D-1…D-9 authorizes an edit. Every
remediation in §10 lands either outside the archive or as a **new, dated**
artifact within it, per Standard §2 Phase 8. Specifically:

- The Level 2 deferrals (D-1…D-4) are disclosed **here**, not by amending
  `research_proposal.md`, `prevalidation_plan.md`, or `methodology.md` —
  even though two of those files misstate the Standard (D-2, D-3). A
  misstatement in a closed archive is corrected by a superseding artifact
  that cites it, never by editing the original, which is retained "as the
  historical record of what was believed true at the time" (Standard §5).
- The head-record anchor (D-6) is published in this document, outside the
  archive, so no archived byte changes.
- Per G-7, this decision does **not** append to `decision_log.md`.

**Enforcement qualification, stated because it is material.** That
immutability is today **policy-only**. Per D-9, `reference_h4` is excluded
from the repository integrity snapshot and holds no entries in the protected
hash fixture, so an edit to any archived file would be detected by no
automated control. The archive is immutable as a matter of governance and
unprotected as a matter of mechanism. R-4 closes that gap, and until it does,
any claim that this archive is "protected" should be read as a statement
about rules, not about enforcement.

## 9. `reference_h5` determination

**A new `reference_h5` cycle is not required, and must not be opened as
remediation for the findings in this document.** Grounds:

1. **No frozen element changed.** Standard §3's trigger for invalidating a
   cycle and requiring a new freeze is a change to one of the eight frozen
   elements. `verify_freeze()` returned `verified` against commit `7b0e816`
   at every bracket, and the Level 2 review found no implementation drift.
2. **The outcome is PASS.** Standard §7 attaches the terminal-discipline and
   new-cycle requirements to FAIL and INCONCLUSIVE. Neither applies.
3. **The Standard's own remedy for a control gap is a record, not a re-run.**
   Standard §8 resolves a weakened control through an exception record with
   an impact assessment and a remediation commitment. It nowhere makes a
   review-level or exception-record deficiency a cycle-invalidation trigger.
4. **A re-run would be worse science, not better.** D-1's unrecoverable
   residual is the loss of outcome-blindness at freeze confirmation. Re-running
   the same methodology now — with the result known to every participant —
   cannot restore that property, and would produce an artifact that *looks*
   more compliant while being strictly less blind. This decision declines to
   trade a disclosed real deviation for an undisclosed cosmetic one.

**What is required instead** is that the *next* cycle, whatever it is
numbered, runs under R-1 and R-2. If `reference_h5` is opened for research
reasons, it must not open its Phase 2 → Pre-validation transition until R-1
and R-2 are discharged. That is a gating condition on the next cycle, not a
remediation obligation on this one.

## 10. Remediation register

Ownership names roles. On this platform all roles are currently discharged
by the single human operator (Standard §4); the split is recorded so that if
the platform ever acquires a second party, the boundary is already drawn.

| ID | Closes | Action | Owner (role) | Gating condition |
|---|---|---|---|---|
| **R-1** | G-1, D-1…D-4 | ADR: where the Standard §2 phase → minimum-review-level table lives and what refuses a transition that does not meet it. Then implement, most likely in `core/research/` beside `advance_phase()`. | Platform Architecture (ADR) → Research domain (impl) | **Blocks** the next cycle's Phase 2 → Pre-validation transition |
| **R-2** | G-2, D-5, G-7 | ADR: make the §8 exception record a first-class artifact with a schema and a required enforcement point; resolve §5 vs. §2 Phase 8 on post-Archive appends in the same ADR. | Platform Architecture | **Blocks** the next cycle's Phase 2 → Pre-validation transition |
| **R-3** | G-3, D-8 | Implement `ArchiveVerifier` per `PLATFORM_ARCHITECTURE_V1.md` §4.4, **or** record its deferral as a time-boxed §8 exception. Named-but-absent is not an allowed third option. | Governance domain | Before the next cycle's Phase 8 |
| **R-4** | G-5, D-9 | ADR + implementation: a re-protection path for a closed cycle (candidate: an append-only closed-cycle hash fixture, structurally separate from the Phase-0 snapshot). **Interim, actionable now:** fold `research_archive/reference_h4/` and the two `experiments/` scripts into that mechanism and drop the expired exclusion clauses at `tests/test_repository_integrity_snapshot.py`:100–106. | Platform Architecture → Test/CI | **Highest urgency** — the gap is live today |
| **R-5** | G-4, D-6 | ADR: how the chain head gets anchored (post-Archive anchor addendum, or an anchor file written outside the package). The cycle-specific gap is already closed by §4 D-6's published hash. | Governance domain | Before the next cycle's Phase 8 |
| **R-6** | G-6 | Wire `independence_linter.lint()` into the test suite over `research_archive/` and `docs/`, with the statistical-usage false positives resolved (widen the qualifier window, or scope the scan to reviewer-attribution blocks). | Governance domain → Test/CI | No hard gate; do before R-1 lands so the next cycle inherits it |
| **R-7** | D-2, D-3 | When the Standard is next revised, cite this decision's D-2/D-3 as the worked example of an archived artifact misstating the Standard, and consider requiring approval-state sections to *quote* the Standard's clause rather than paraphrase it. | Platform Architecture | Deferred to the next Standard revision (v1.2) |

## 11. Governance effect

This document has **no governance effect until committed**. On commit it
becomes:

- the compensating §8 disclosure record for D-1…D-5, authored at Level 2 by
  a party that did not run the cycle;
- the external anchor for `reference_h4`'s chain head (D-6);
- the recorded Phase 8 completeness check for `reference_h4` (D-8);
- the register of record for R-1…R-7.

It does not alter `research_archive/reference_h4/`. It does not alter
`docs/RESEARCH_GOVERNANCE_STANDARD.md`. It does not alter the `reference_h4`
**PASS**.

**Level 3 review not available; this decision was made at Level 2 only.**
