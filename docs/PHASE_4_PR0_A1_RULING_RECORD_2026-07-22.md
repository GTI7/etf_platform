# Phase 4 / PR0 — A-1 Ruling Record (2026-07-21 deviation-record ruling request)

**Date filed:** 2026-07-22
**Repository state ruled against:** canonical `D:\Claude\etf_platform`, `master`, HEAD `8bd8f8a`.
**Status: ruling record.** It disposes of the ruling request raised by the
2026-07-21 PR0 governance deviation record, and of nothing else. It is
**not** a disclosure (that is `8bd8f8a`), **not** a remediation (that is
`4c7ca8d`), **not** a gate determination, and **not** an architecture
decision.

**Closes limb 2 of prerequisite A-1** of
[`PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`](PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md)
§4.1, whose "Done when" condition is two-limbed: "The disclosure exists
in `docs/`" **and** "the PR0 ruling is closed or confirmed obsolete".

- **Limb 1 — disclosure.** Already satisfied, by
  [`PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md`](PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md)
  (`8bd8f8a`). Not re-decided here.
- **Limb 2 — ruling.** Disposed of by §2 and §6 of this record.

**No file is edited by this record, and no code is introduced by it.**
This is a new, dated file. `ARCHITECTURE_DECISIONS.md` (AD-047 draft,
AD-051), `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md`,
`PHASE_4_STEP9_DRAFT_ADRS.md`, `PHASE_4_PR0_REMEDIATION_PROPOSAL.md` and
`PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` are all retained unedited, and
each is cited below by section rather than amended.

**Supersession discipline, and the precision on its citation.** The
convention followed is the one stated in
[`RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md) §5
("Naming and versioning conventions"): a correction is a new, dated file,
cross-referenced from the file it supersedes, and the superseded file is
retained unedited. As
[`PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md`](PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md)
already discloses in its header, §5 states that convention for
evidence-package artifacts under `research_archive/<cycle_name>/`, not
for `docs/`; this record is in `docs/` and applies it **by extension, not
by direct scope**. The stated rule for `docs/` is the preamble of
[`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) — "Where a later
phase revised an earlier decision, the entry says so explicitly rather
than silently superseding it." That is the discipline this record
follows, and it is the same one the re-disclosure record followed one
commit earlier. GOV-1 (Standard §10.1) is not relied on; it governs
theory-based target corrections to validation gates and does not govern
this record.

**One partial supersession is made explicit rather than left implicit.**
`PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` §5 records a **proposed**
disposition of the ruling request ("obsolete — not confirmed, and not
ruled on by this record"), and offers as its basis for the request's
second item that it "appears unactionable as written." This record rules
on a **different and narrower basis** for that item — the failure of its
own stated condition (§2.2) — and the proposed "unactionable" basis is
therefore **not adopted**, is not needed, and is not relied on. That
prior record is not edited; its §5 stands as the historical record of
what was proposed before a ruling existed.

**Verification basis.** Every factual claim below was checked directly
against the canonical repository at HEAD `8bd8f8a` — `git log`, commit
messages, `git show --stat`, `docs/` content, and the working tree — or
is quoted from, and attributed to, a named document. Claims resting on
evidence outside the canonical repository are labelled **off-repo** at
the point of use, and the evidence inventory relied upon is
`PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` §1.5, which is not restated here.

---

## 1. The ruling request, restated verbatim

### 1.1 Provenance and evidence class of the quoted text

The request being ruled on is §5 of
`docs/PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md`, the
governance deviation record raised by PR0 remediation adversarial review
(recorded there as finding F4).

**Evidence class: off-repo — untracked working-tree copy, non-canonical
directory.** This is
`PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` §1.5 rows 3–4:
`D:\Claude\etf_platform_rebuild\docs\PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md`
and its byte-identical mirror under
`D:\Claude\SynologyDrive\etf_platform_rebuild\docs\` (8,580 bytes each).
Row 4 is a mirror of row 3, so agreement between them is **not**
independent corroboration.

**The request survives only as content, without canonical commit
provenance. This is stated as a limit on the ruling, not as a
formality.** Specifically, and verified at HEAD `8bd8f8a`:

- No commit object for the destroyed fix (`13ef2d2`) or its sibling
  (`88dd282`) exists in the canonical repository.
- `git log --all -- docs/PHASE_4_PR0_GOVERNANCE_DEVIATION_RECORD_2026-07-21.md`
  returns nothing across all reachable commits, and the file is absent
  from the canonical working tree.
- The surviving copies are untracked files, in non-canonical
  directories, in working trees whose own git history terminates at
  `3021c83` — i.e. before the destroyed Phase 4 commits were authored.
  There is no commit object, no hash chain, and no provenance anchor;
  nothing distinguishes the surviving bytes from bytes edited after the
  fact.
- The read-only forensic snapshot
  (`C:\Users\GTi\etf_platform_forensic_2026-07-21`) does not contain the
  record either, and its `.git` predates the destroyed work.

**Consequence for this ruling, stated plainly.** This record rules on a
request whose *content* is recoverable and whose *provenance is not*. It
does not treat the quoted text as canonical git evidence, and it does not
convert it into canonical evidence by quoting it. What it does is dispose
of the obligation that text created, so that the obligation cannot
persist indefinitely on the strength of an artifact that can never be
provenance-anchored. Nothing here restores the record to the evidence
chain; whether to re-commit the surviving copies into `docs/` is a
separate question this record does not decide, exactly as
`PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` §1.4 left it.

### 1.2 The request, verbatim

Quoted in full and unaltered from §5 of the source named in §1.1. The
two numbered items are the entirety of what was requested.

> ## 5. Approval required before merge
>
> This deviation is **not self-approving.** Required before the PR0
> remediation commit merges:
>
> 1. A ruling on whether the change stays in PR0 or is split into its own
>    change. Either is implementable; the split is a clean revert of the
>    8-line block plus its three tests.
> 2. If it stays: acknowledgement that the roadmap's PR0 file list is
>    inaccurate as frozen, recorded by reference to this document. Per
>    Standard §5 and the freeze record's post-freeze discipline, the
>    roadmap itself is **not** to be edited to match.
>
> Until that ruling exists, PR0 is not merge-ready regardless of the state
> of the code — which is the point of recording it rather than deciding it
> here.

---

## 2. Determinations

### 2.1 Item 1 — determined as a statement of fact: the change was split into its own increment

**Determination.** The disjunction item 1 puts ("stays in PR0" *or* "is
split into its own change") is **resolved by the repository's own
history**: the change was split out and landed as its own increment. This
determination records a fact established by evidence; it does not select
between two live options, because only one of them is instantiated at
HEAD `8bd8f8a`.

**Evidence, verified at HEAD `8bd8f8a`.**

| Element | Commit | What it contains |
|---|---|---|
| Its own proposal | `ced8636` "docs: define phase 4 PR0 remediation" | Exactly one file: `docs/PHASE_4_PR0_REMEDIATION_PROPOSAL.md` (+351 lines). Its §9 "Implementation boundary" scopes the increment to the `verify_freeze` guard, one docstring sentence, one AD, and four tests — and explicitly places coverage-adequacy, commit-reference authentication, the A-1 obligation, and all Step 9 Phase A–E work out of scope. |
| Its own implementation | `4c7ca8d` "fix: prevent empty freeze verification from passing" | `core/governance/freeze_verifier.py`, `docs/ARCHITECTURE_DECISIONS.md`, and three test files; 180 insertions, 2 deletions. Its message states: "PR0 scope closed for the empty-coverage defect only." |
| Its own architecture decision | **AD-051**, added by `4c7ca8d` | "An empty `covered_paths` set is `UNVERIFIABLE`, not `VERIFIED`". Self-contained: decision, rationale, mechanism, an explicit "what this AD does not claim to fix" paragraph, and a "Scope" paragraph. |

Two further checks confirm the increment is genuinely standalone rather
than a re-bundling:

- **It is not bundled with the reproduction-runner work that the frozen
  roadmap's PR0 acceptance criteria 1–6 concerned.** That work is a
  separate commit, `2c7fb2c` "Fix reproduction runner universe coverage
  validation", touching only `core/governance/reproduction_runner.py`
  (13 insertions, 4 deletions). The deviation record's own §4 table noted
  that "PR0 acceptance criteria 1–6" are "Unaffected... all six concern
  `reproduction_runner`"; those criteria and this change are now in
  different commits.
- **The AD carries its own numbering ruling rather than inheriting one.**
  AD-051's "Numbering" paragraph, and `4c7ca8d`'s commit message, both
  record that AD-051 was taken instead of the next-in-sequence AD-047
  because AD-047–050 remain reserved for the Step 9 draft ADRs already
  cross-referenced by number in settled documents. A change absorbed into
  a larger PR0 would not have needed a numbering ruling of its own.

**How the split came about, disclosed rather than glossed.** The split
was **not** effected by an approver selecting option (b) of item 1. Per
`PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` §1.4, the original fix `13ef2d2`
and the deviation record were destroyed as committed objects in the
2026-07-21 incident, the defect was independently re-identified on
2026-07-22, and the fix was then re-specified and re-landed as the
standalone increment tabulated above. The outcome matches the option the
deviation record itself described as "a clean revert of the 8-line block
plus its three tests"; the route to it was destruction and
re-implementation, not adjudication. This ruling records the fact and its
cause, and does not represent the fact as a prior approval.

**What this determination does not do.** It makes no judgement that the
split was the better of the two options, and it assigns no retrospective
merit to either. Item 1 asked which of two states would obtain; the
repository answers it. That is the whole of the determination.

### 2.2 Item 2 — VOID: its own stated condition was never satisfied

**Determination: VOID.**

Item 2 is conditional on its own face. Its operative words are **"If it
stays:"** — the acknowledgement it requires is owed only in the branch of
item 1 where the change remains inside PR0. Per §2.1, that branch is not
the branch that obtains: the change did not stay in PR0; it was split
into its own increment. **The condition was never satisfied, so the
obligation it governs never came due.** There is nothing to grant, refuse,
or defer.

**This is a determination on the request's own terms.** It requires no
finding about the roadmap, no interpretation beyond the text quoted in
§1.2, and no new principle. A conditional obligation whose condition
fails is void; that is the ordinary reading of the sentence as written.

**Two observations recorded, and expressly not relied upon as the basis
of this determination.**

1. `docs/PHASE_4_IMPLEMENTATION_ROADMAP.md` — the document whose PR0 file
   list item 2 would have had the acknowledgement address — exists in no
   reachable ref, in no working tree of the canonical repository, and in
   no off-repo source inventoried in
   `PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` §1.5. Had the condition been
   satisfied, this would have been the next question. It was not
   satisfied, so it is not reached. As stated in this record's header,
   the "appears unactionable as written" basis proposed in that record's
   §5 is **not adopted** — it is an alternative basis that this ruling
   does not need and does not endorse.
2. Item 2's closing instruction — "the roadmap itself is **not** to be
   edited to match" — is consistent with the supersession discipline this
   record and its predecessor both follow, and is in any event moot for
   the same reason. No document is edited by this record.

**What VOID means here, stated exactly.** Void as to obligation: the
acknowledgement is not owed and will not be filed. It is **not** a
finding that the frozen roadmap's PR0 file list was accurate, and it is
**not** a finding that it was inaccurate. That question is not decided,
because the surviving evidence cannot reach it and, more importantly,
because the request never required it to be reached in this branch. The
deviation record's own §4 assessment of that file list remains what it
was: a dated statement in an off-repo, self-attested, unreviewed record.

---

## 3. Where authorization is recorded

**Authorization for the increment determined in §2.1 is recorded in the
commit message of `4c7ca8d`, together with AD-051 in
[`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md).** That pair is
the authorization artifact this repository holds, and this record
identifies it rather than creating one.

What each element carries, verified at HEAD `8bd8f8a`:

- **`4c7ca8d`'s message** states the acceptance-time ruling in terms:
  "Numbering ruling: AD-051 is intentionally used instead of proposal
  section 9's next-in-sequence AD-047... Ruling made at acceptance time
  according to `PHASE_4_PR0_REMEDIATION_PROPOSAL.md` sections 7.2 and 9."
  It also bounds itself — "PR0 scope closed for the empty-coverage defect
  only. A-1 historical re-disclosure remains open and is not discharged
  by this commit."
- **AD-051** carries the decision, the rationale, the mechanism, the
  explicit non-claims, and the "Scope" paragraph restating that the
  AD-047 (draft) re-disclosure obligation is independent of it and not
  discharged by it.
- **`ced8636`'s proposal**, at §9, is the boundary document those two
  execute against, and it closes with "No code, no test, and no
  documentation edit described above is applied by this document.
  Implementation begins only on explicit approval." The approval it
  contemplated is the acceptance recorded in `4c7ca8d`'s message.

### 3.1 Required disclosure: this is repository practice, not an independently approved authorization artifact

Stated plainly, because the difference is the whole of what a reader
needs to weigh this record correctly:

**A commit message plus an AD entry is how this repository has recorded
acceptance. It is not an authorization artifact that some accountable
party independent of the work approved.** The same operator directed the
proposal, the implementation, the acceptance-time numbering ruling, and
the commit that records it. There is no separate approver identity, no
counter-signature, no reviewer record in
`research_archive/*/reviewer_reports/`, and no artifact of any kind
attesting that a party other than the author assented.

The consequence is bounded precisely: what §3 identifies is **where the
decision is written down**, not **evidence that it was independently
sanctioned**. A later reader must not cite `4c7ca8d` + AD-051 as an
approval by a second party, because it is not one. This ruling
nevertheless treats that pair as the authorization of record, because it
is the artifact the repository actually produced and because leaving the
increment with no identified authorization at all would be a worse and
less honest state than identifying it with its limitation attached.

This disclosure creates no obligation to produce a different artifact.
See §5.

---

## 4. Review level

**Level 1 — self-review**, per
[`RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md) §4.

This record is authored and reviewed within the same effort that produced
the material it rules on. Standard §4 requires every review record to
state its level explicitly and forbids describing anything below Level 3
with the unqualified word "independent"; this record therefore does not
use it. Standard §4's Level 1 limitations apply in full and are adopted,
not softened: self-review "cannot detect a bias the author holds, cannot
self-certify independence under any circumstance, carries the highest
risk of confirmation bias and post-hoc rationalization of any level."

**Level 3 review is not available on this platform.** Standard §4 states,
of Level 3, that "no Level 3 review has ever been performed on this
platform," the platform having a single human operator directing all
research and all review sessions. That is disclosed here as the reason
this record is Level 1, and is not offered as an excuse for it.

**Two precisions on the classification.**

1. This is not a lifecycle **Decision** in the sense of Standard §2 and
   §4's Decision-phase sign-off requirement — no research conclusion, no
   gate determination, and no step toward capital allocation is made
   here. The Level 3 requirement Standard §4 attaches to Decision-phase
   sign-off is therefore not engaged, and this record does not claim an
   exemption from a requirement that does not apply to it.
2. The predecessor artifacts this record rests on are themselves Level 1:
   `PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` labels itself Level 1 in its
   closing "Residual weakness" paragraph, and AD-033 is identified there
   (§3.3) as Level 1 self-attested. A Level 1 ruling resting on Level 1
   inputs does not compound to anything stronger, and nothing here should
   be read as if it did.

---

## 5. What this record does not do

- **It reopens no historical governance decision.** No prior AD, gate
  determination, freeze record, archived result, review record, or
  disclosure is amended, withdrawn, re-run, re-interpreted, or
  revisited. AD-033's recorded smoke-test verdicts, AD-043's gate
  behaviour, AD-047's draft status, AD-051, and every determination in
  `PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` §§2–4 stand exactly as they
  stand at `8bd8f8a`. The single relationship this record has to a prior
  document is the partial, explicitly-stated non-adoption of a
  *proposed* disposition's alternative basis (header, §2.2 observation
  1) — a proposal was never a decision, so declining to adopt its
  reasoning reopens nothing.
- **It introduces no new approval requirement.** No sign-off,
  counter-signature, reviewer report, artifact, register entry, or
  process step is created by this record for any future increment. §3.1
  discloses a limitation of existing practice; it does not impose a
  remedy for it, and no future work is blocked on producing a different
  class of authorization artifact.
- **It introduces no governance framework.** Every instrument used here
  already exists in the repository: Standard §4 (review levels),
  Standard §5 (supersession, applied by extension as the header states),
  `ARCHITECTURE_DECISIONS.md`'s preamble (the `docs/` rule), Resolution
  §4.1 (prerequisite A-1 and its two limbs), and the evidence-class
  distinction inventoried in `PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md`
  §1.5. No new vocabulary, tier, gate, status, or record type is
  defined.
- **It changes no code and no behaviour.** `verify_freeze` at `8bd8f8a`
  is what `4c7ca8d` made it. Nothing here touches it.
- **It does not improve any historical `VerificationResult`.** The
  bounds in `PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` §§2.1–2.3 and §4.2
  are unaffected by this ruling in every direction. In particular, a
  pre-`4c7ca8d` `VERIFIED` still cannot self-certify its own
  non-vacuity, and the consequential citation requirement (that record's
  §5, restating AD-047's INV-3 — record the covered-path list alongside
  any cited status) is untouched and continues to apply.
- **It does not restore the destroyed record to the evidence chain.**
  See §1.1. Re-committing the surviving off-repo copies remains an
  undecided, separate question.
- **It does not discharge A-1 limb 1.** That limb was closed by
  `8bd8f8a` and is not re-decided here.

---

## 6. Effect

| Item | Status after this record |
|---|---|
| **The 2026-07-21 PR0 ruling request, item 1** ("stays in PR0 or is split") | **Determined as a statement of fact.** The change was split into its own increment: `ced8636` (its own proposal) + `4c7ca8d` (its own implementation) + **AD-051** (its own architecture decision). §2.1. |
| **The 2026-07-21 PR0 ruling request, item 2** ("If it stays: acknowledgement...") | **VOID.** Its stated condition — "If it stays" — was never satisfied, because the change did not stay. The obligation never came due. §2.2. |
| **The 2026-07-21 PR0 ruling request, as a whole** | **Closed.** Both items are disposed of; no part of it remains outstanding. |
| **Authorization of record for the increment** | Commit `4c7ca8d`'s message together with AD-051, disclosed in §3.1 as **repository practice, not an independently approved authorization artifact**. |
| **A-1, limb 1 — disclosure** | **Closed** at `8bd8f8a`. Unchanged by this record. |
| **A-1, limb 2 — "the PR0 ruling is closed or confirmed obsolete"** | **Closed if this ruling is accepted.** On acceptance, limb 2's condition is met by §2 of this record. |
| **Prerequisite A-1 as a whole** (Resolution §4.1) | **Discharged if this ruling is accepted** — both limbs then closed in writing. |
| **Step 9 Phase A** | **A-1 ceases to be the blocker on acceptance of this ruling.** A-2 … A-9 are untouched and remain open on their own terms; Resolution §4.1's rule that "Step 9 does not start until every item below is closed in writing" is unchanged, and this record neither relaxes it nor speaks to any prerequisite other than A-1. |
| **Remaining limitation — coverage adequacy** | **Open, disclosed, unmechanized.** Unchanged (AD-051; `PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md` §5). |
| **Remaining limitation — commit provenance** | **Open, disclosed, unmechanized.** Unchanged; draft AD-048's mechanism is not built. |
| **Evidentiary status of the destroyed 2026-07-21 history** | **Unknown on all evidence sources identified as of 2026-07-22.** Unchanged; this record adds no source and closes no part of it. |

**Statement of closure, made explicitly as required.** *A-1 limb 2 is now
closed if this ruling is accepted.* The acceptance referred to is the
accountable reviewer's acceptance of this record — the same act
Resolution §4.1 already contemplates when it requires the ruling to be
"closed... in writing". It is not a new approval requirement (§5); it is
the pre-existing condition of limb 2, and this record is the writing that
satisfies it. Until that acceptance, limb 2 stays open, A-1 stays
undischarged, and Step 9 stays blocked — exactly as it stood at `8bd8f8a`.

**How to re-run this ruling.** Every input is named so a later reader
need not trust this document: the verbatim request (§1.2) against the
off-repo copies inventoried in `PHASE_4_PR0_A1_REDISCLOSURE_RECORD.md`
§1.5 rows 3–4; the split (§2.1) against `git show --stat ced8636 4c7ca8d
2c7fb2c` and AD-051 in `docs/ARCHITECTURE_DECISIONS.md`; the
authorization (§3) against `git log -1 --format=%B 4c7ca8d`; the review
level (§4) against `RESEARCH_GOVERNANCE_STANDARD.md` §4; and the A-1
condition (§6) against `PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md` §4.1.
