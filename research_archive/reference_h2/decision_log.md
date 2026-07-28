# REFERENCE H2 — Decision Log

**Status: append-only.** Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5,
this is intended to become the single, chronological record of every
decision point in the `reference_h2` pre-validation cycle. **This log was
created retroactively on 2026-07-28, during Phase 3 remediation** (the same
remediation pass that produced `provenance_record_gate1_2026-07-28.json`
and `attempt_001_chronology_correction_2026-07-28.md`), to consolidate
decision points that were, until now, scattered across the cycle's
individually dated artifacts and commit history. It does not restate those
documents in full; each entry cites its primary source rather than
duplicating it.

**This is a retroactive chronological index, not a claim that every entry
below was contemporaneously recorded in this file at the time.** Entry
dates and times reflect the evidence available at that point (commit
timestamps, file mtimes, and each cited document's own stated timestamps),
reconstructed after the fact from repository history — not the date this
log itself was written. Going forward from 2026-07-28, new decisions are to
be appended here at the time they occur; a correction to an existing entry
is added as a new, separately dated entry cross-referencing the one it
corrects, never by editing the original.

This log records process decisions only. It does not itself evaluate,
redesign, or change any `reference_h2` methodology, scoring logic, or gate
determination, and it creates no gate outcome and no lifecycle transition.

---

## Entry 1 — Hypothesis registration (Phase 1)

- **Date:** 2026-07-28 00:42 (registered), 00:53 (generalized)
- **Decision:** `reference_h2` governance identity initialized;
  `hypothesis.md` drafted, then generalized to remove Phase-1 numeric
  specificity.
- **Evidence references:** `hypothesis.md` (commits `b7bedba`, `ee802aa`);
  `research_artifacts/reference_h2_registration.py`; `archive_manifest.json`
  (`b7bedba`).
- **Governance status:** Phase 1 — complete.
- **Reviewer level:** Level 1 (self-review; authoring commits).
- **Known limitations:** Not independently reviewed at this stage; no
  disclosure recorded beyond the artifact's own text.

## Entry 2 — Research proposal drafted, iterated, and accepted (Phase 2)

- **Date:** 2026-07-28 01:17 (drafted) through 13:05 (final Level 2 PASS
  review)
- **Decision:** `research_proposal.md` drafted (`c0d5a18`) and revised
  across six subsequent commits (`9e774cf` wording-drift fix, `9c12826`
  citation-chain fix, `b9746f9` candidate-coverage completion, `77b6b4e`
  evidence-chronology addendum, `8e6fa80` evidence-chronology correction,
  `7e7566f` review-provenance-claims fix). A first Level 2 review
  (`2026-07-28_level2_adversarial_review.md`, commit `d6d51af`, 12:42)
  returned **FAIL** on an unsupported provenance claim in Section 1; the
  finding's classification was clarified
  (`2026-07-28_level2_review_clarification.md`, `9a54306`, 12:42); the
  flagged claim was remediated (`201b8ae`, 12:43); a fresh Level 2 review
  against the remediated HEAD
  (`2026-07-28_level2_review_head_201b8ae.md`, `4030d86`, 13:05) returned
  **PASS**.
- **Evidence references:** `research_proposal.md`;
  `2026-07-28_level2_adversarial_review.md`;
  `2026-07-28_level2_review_clarification.md`;
  `2026-07-28_level2_review_head_201b8ae.md`; commits `c0d5a18`…`4030d86`.
- **Governance status:** Phase 2 — satisfied (PASS on the remediated
  proposal).
- **Reviewer level:** Level 2 — AI-assisted adversarial (procedurally
  independent per each review's own stated tier; **not organizationally
  independent**).
- **Known limitations:** The original FAIL review (`d6d51af`) is retained
  unedited, per archive discipline, as the historical record; it is
  superseded in effect, not in text, by the PASS review against the
  remediated HEAD. No Level 3 review exists or is available on this
  platform.

## Entry 3 — RESEARCH_PROPOSAL → PRE_VALIDATION transition

- **Date:** 2026-07-28 13:25:02
- **Decision:** `transition_records.jsonl` sequence 1 recorded:
  `from_phase: "Research Proposal"` → `to_phase: "Pre-validation"`,
  `gate_outcomes: []`.
- **Evidence references:** `transition_records.jsonl` (commit
  `839d000d57945152f3f0f22867137af0b3717a8c`);
  `experiments/run_reference_h2_lifecycle.py`; the record's own
  `freeze_commit_ref` (`4030d86e2316a7fe3b0ec70c84a44bbf389fac2d`) and
  `evidence_refs` (`research_proposal.md`,
  `2026-07-28_level2_review_head_201b8ae.md`).
- **Governance status:** Phase 2 → Phase 3 transition recorded.
  `reference_h2` entered PRE_VALIDATION.
- **Reviewer level:** Level 2, per the transition record's own
  `authorization` block (`reviewer_level: "Level 2 (AI-assisted adversarial
  review)"`).
- **Known limitations:** `freeze_verification_status` is recorded as
  `"not_applicable"` in the transition record itself; no further caveat is
  disclosed at this entry.

## Entry 4 — Pre-validation plan frozen

- **Date:** 2026-07-28 13:47:49
- **Decision:** `prevalidation_plan.md` committed, establishing the
  cycle's gate structure and methodology-freeze process.
- **Evidence references:** `prevalidation_plan.md` (commit
  `a7d0938c66ab86e0bfb46b643698f67229b224a2`).
- **Governance status:** Phase 3 (Pre-validation) — governing plan
  established.
- **Reviewer level:** Level 1 (self-review; authoring commit). No distinct
  Level 2 confirmation of the plan's own completeness is recorded as of
  this entry.
- **Known limitations:** Not independently reviewed as of this entry.

## Entry 5 — Attempt #1 specification frozen

- **Date:** drafted 2026-07-28 14:08:15 (local); committed 14:52:13, as
  part of the same commit as Entry 6's remediation
- **Decision:** `attempt_001_specification.md` logged Construction
  Attempt #1: 252-trading-day formation, 21-trading-day skip,
  close-to-close log-return basis, `reference_v1`'s frozen `SMA(20)`
  momentum score, 25-ETF universe, bucket size 5, minimum panel size 10,
  2024-07-17–2026-07-17 window.
- **Evidence references:** `attempt_001_specification.md` (committed at
  `41ce0fbd58606e3da3476e28e0973a5b1990d866`, alongside Entry 6).
- **Governance status:** Phase 3 — Attempt #1 construction fixed in
  writing.
- **Reviewer level:** Level 1 at time of drafting. The pre-log attestation
  originally accompanying this specification was later found false and
  corrected — see Entry 6 for the full governance disposition.
- **Known limitations:** See Entry 6 (attestation falsity) and Entry 9
  (O-3, a narrower documentary-support correction). Sections 2, 4, and 6 of
  the specification itself (frozen construction, alternatives considered,
  traceability) are not contradicted by any repository evidence found
  during this remediation and remain in effect unmodified.

## Entry 6 — False-attestation discovery and correction; attempt-cap disposition

- **Date:** script executed 2026-07-28 13:58:46 (local) — before the
  specification below existed; specification drafted 14:08:15; remediation
  committed 14:52:13
- **Decision:** `attempt_001_specification.md`'s pre-log attestation
  falsely claimed that `experiments/validate_h2_gate1_independence.py` had
  not been executed and that no correlation figure existed under this
  cycle. Both claims were already false when written: the script ran and
  produced `h2_gate1_independence_analysis_report.json` at 13:58:46,
  roughly 9.5 minutes before the specification was drafted, at the same
  commit. `attempt_001_addendum_2026-07-28.md` corrected the attestation
  without editing the superseded document. A first review accepting the
  addendum was authored in the same pass as the addendum itself
  (self-confirmed, not independently confirmed);
  `2026-07-28_level2_independent_confirmation_attempt_001_addendum.md`
  supplied the missing independent second pass, re-deriving the chronology
  from repository evidence alone and confirming the addendum's conclusions.
- **Governance ruling** (recorded here as a governance ruling, not a gate
  outcome — this remediation reserves `Gate`/`GateRunner`-style transitions
  for a measured statistic against a frozen threshold, and this is not
  one): the original 14:08:15 logging of Attempt #1 is **procedurally
  invalid** (a mandatory truthful attestation was not actually produced),
  but this is a procedural invalidation of the attestation only, not a
  substantive invalidation of the construction — no repository evidence
  shows the frozen construction elements were selected, adjusted, or
  influenced by the pre-existing figures; the construction was named,
  by convention citation, in `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md`
  nearly fourteen hours before the script existed. Attempt #1 is **not
  abandoned**, is **not re-numbered**, and does **not** require re-freezing.
  The invalid original logging does not count against the three-attempt
  cap; the corrected re-submission becomes the first validly logged
  attempt. Two further attempts remain available under the cap.
- **Evidence references:** `attempt_001_addendum_2026-07-28.md`;
  `2026-07-28_level2_review_attempt_001_false_attestation.md`;
  `2026-07-28_level2_independent_confirmation_attempt_001_addendum.md` (all
  committed at `41ce0fbd58606e3da3476e28e0973a5b1990d866`).
- **Governance status:** Phase 3 — attestation corrected; construction
  remains Attempt #1; no lifecycle transition; `transition_records.jsonl`
  unchanged at one entry, `gate_outcomes` empty.
- **Reviewer level:** Level 2 — AI-assisted adversarial, independent
  confirmation pass (procedurally independent per the confirmation
  report's own tier statement; **not organizationally independent**).
- **Known limitations:** Whether the pre-existing correlation/overlap
  figures were actually consulted while drafting Section 2 or Section 4 of
  the specification is not establishable from repository evidence and is
  recorded, permanently, as an open, disclosed, unconfirmed-status residual
  risk (addendum §10) — **not resolved in either direction** by this
  entry.

## Entry 7 — Gate 1 evidence generation; O-5 disclosure

- **Date:** generated 2026-07-28T11:58:46Z (13:58:46 local); archived
  2026-07-28 during this remediation pass (not yet committed as of this
  entry)
- **Decision:** `gate1_independence_analysis_2026-07-28.json` archived as
  a byte-identical, SHA-256-verified frozen snapshot of the root-level
  Gate 1 evidence-generation-capability output (component 1: cross-
  sectional Spearman rank correlation vs. `reference_v1`'s `SMA(20)`;
  component 2: top-5/bottom-5 overlap fraction; 483 of 502 nominal window
  dates evaluated). This artifact does not, by itself, satisfy Gate 1 — its
  own `disclosure` block states the attempt log, pre-log attestation, and
  Level 2 independent confirmation remain required elsewhere — and makes no
  PASS/FAIL/INCONCLUSIVE determination.
- **O-5 disclosure:** The archived artifact's own `repository_commit`
  field states `a7d0938c66ab86e0bfb46b643698f67229b224a2`, but the script
  that produced it, `experiments/validate_h2_gate1_independence.py`, was
  untracked at that commit and was modified on disk 67 minutes after the
  report was generated; the exact producing script version was never
  committed and no longer exists anywhere (working tree or git history).
  This is accepted here as a **documented, permanent residual risk** — full
  disclosure in `provenance_record_gate1_2026-07-28.json` — and has **no
  numerical reproducibility impact** (see Entry 8; the independent
  reproduction derives from the frozen written specification, not from the
  since-modified script).
- **Evidence references:** `gate1_independence_analysis_2026-07-28.json`
  (SHA-256 `b021ed4461e81f36c5947f3b04c9975aafff5f8c4eceed8f100638fe88996197`);
  `provenance_record_gate1_2026-07-28.json`.
- **Governance status:** Phase 3, Gate 1 — evidence generated and
  archived; not yet gated.
- **Reviewer level:** Level 1 at generation (script run); disclosure
  recorded at Level 1 (this remediation pass). See Entry 8 for the Level 2
  confirming pass.
- **Known limitations:** O-5 (script provenance, unrepairable) and O-2
  (database identity not recorded contemporaneously by the artifact
  itself — see Entry 8) are both disclosed in full in
  `provenance_record_gate1_2026-07-28.json`; neither affects the
  reproduction result.

## Entry 8 — Gate 1 confirming reproduction

- **Date:** reproduction run 2026-07-28T13:42:41Z; report committed
  2026-07-28 15:58:53 (commit `04f83d1`)
- **Decision:** `2026-07-28_level2_gate1_confirming_reproduction.md`
  independently re-derived both Gate 1 components from the frozen written
  specification (`attempt_001_specification.md` §2), not from the
  since-modified script, against a pinned database
  (`experiments_etf_universe.db`, SHA-256
  `cd4fd53d2032fbc87364adc578bcab4fc5ad1a1a779ce72c62697a037a148103`,
  unchanged since 2026-07-18). **Result: both components reproduced
  exactly — 483/483 dates bitwise identical, absolute tolerance 0,** for
  both the rank-correlation distribution and the top-5/bottom-5 overlap
  distributions. No PASS/FAIL/INCONCLUSIVE interpretation of the measured
  correlation is recorded by this report or this entry; no Methodology
  Freeze is authorized; no lifecycle transition occurs.
- **Evidence references:**
  `2026-07-28_level2_gate1_confirming_reproduction.md` (commit
  `04f83d11c32d14e7c509fae181c115004cffe34b`).
- **Governance status:** Phase 3, Gate 1 — independent reproduction
  complete; **Gate 1 determination itself not yet made.** `reference_h2`
  remains in PRE_VALIDATION; `transition_records.jsonl` unchanged at one
  entry, `gate_outcomes` empty.
- **Reviewer level:** Level 2 — AI-assisted adversarial (procedurally
  independent: fresh session, independently re-implemented rather than
  re-ran the original script; **not organizationally independent**).
- **Known limitations:** Five provenance/packaging observations (O-1…O-5)
  recorded by this report, disclosed for whoever makes the eventual Gate 1
  determination. O-5 is the most consequential (Entry 7). O-1 is recorded
  in Entry 10 below. O-3 is recorded in Entry 9 below. O-4 (evidence
  package incomplete against the idealized seven-item structure) remains
  open — expected to narrow as this log and the other Phase-3 artifacts
  created in this remediation are added, but not closed by this entry. No
  Level 3 review exists or is available on this platform.

## Entry 9 — O-3 chronology correction

- **Date:** 2026-07-28 (this remediation pass, prior to this log's
  creation)
- **Decision:** `attempt_001_chronology_correction_2026-07-28.md` narrows
  one supporting sentence in `attempt_001_addendum_2026-07-28.md` §9 point
  3, which overstated that `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md`
  named all of "252-day formation, 21-day skip, log return." Verified: only
  the 252-day formation window and the existence of a skip are named
  there; the exact 21-day integer and the log-return basis were first
  fixed in `attempt_001_specification.md` §2.4, under disclosed
  convention-reuse grounds (the platform's 21-trading-day-month convention;
  the log-return basis shared with `reference_v2_h1` and `reference_h3`).
  Explicitly a **provenance correction**, not a claim that the frozen
  construction parameters are invalid; does not reopen or re-freeze
  Attempt #1's construction, does not change the attempt count, and does
  not affect the Gate 1 reproduction result (Entry 8).
- **Evidence references:**
  `attempt_001_chronology_correction_2026-07-28.md`; O-3 in
  `2026-07-28_level2_gate1_confirming_reproduction.md` §6.
- **Governance status:** Phase 3 — narrows a documentary-support claim
  only; no gate outcome; no lifecycle transition.
- **Reviewer level:** Level 1 (self-directed correction, performed at the
  direction of this governance-remediation task; not itself a review of
  `reference_h2`'s research substance).
- **Known limitations:** This correction has not itself received Level 2
  or above review as of this entry.

## Entry 10 — O-1 archive preservation

- **Date:** 2026-07-28 (this remediation pass)
- **Decision:** Closes, in part, O-1 ("the Gate 1 evidence artifact is not
  under version control and is not in the evidence package") by placing a
  byte-identical, SHA-256-verified copy of the root-level evidence
  artifact under `research_archive/reference_h2/`, per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5's evidence-package location
  requirement. The root-level `h2_gate1_independence_analysis_report.json`
  remains gitignored and subject to overwrite by any future rerun; the
  archived copy, `gate1_independence_analysis_2026-07-28.json`, is the
  durable copy.
- **Evidence references:** `gate1_independence_analysis_2026-07-28.json`;
  O-1 in `2026-07-28_level2_gate1_confirming_reproduction.md` §6.
- **Governance status:** Phase 3 — evidence-package placement gap (O-1)
  closed for this artifact.
- **Reviewer level:** Level 1 (archival action; not a research review).
- **Known limitations:** This artifact, this log, and
  `provenance_record_gate1_2026-07-28.json` /
  `attempt_001_chronology_correction_2026-07-28.md` are all still
  **untracked** as of this entry — no commit hash exists for any of them
  yet. Per this project's own standing discipline (a document's own claim
  to have preserved something is not commit evidence until it is actually
  committed), this entry's citations should not be read as claiming
  committed provenance until a future commit closes that gap.

---

## Current status (as of Entry 10)

- **Phase 1 (Hypothesis):** complete (Entry 1).
- **Phase 2 (Research Proposal):** complete, PASS (Entry 2).
- **Phase 2 → Phase 3 transition:** recorded (Entry 3);
  `transition_records.jsonl` holds exactly one record, `gate_outcomes: []`.
- **Phase 3 (Pre-validation):** governing plan frozen (Entry 4); Attempt #1
  construction frozen (Entry 5), attestation corrected (Entry 6), attempt
  count unaffected (still Attempt #1 of 3).
- **Gate 1:** evidence generated and archived (Entry 7); independently
  reproduced exactly, 483/483 dates at tolerance 0 (Entry 8). **Gate 1
  itself has not been determined — no PASS/FAIL/INCONCLUSIVE outcome
  exists.**
- **Gates 2–4:** not addressed in this cycle's artifacts to date; not
  assessed by this log.
- **`reference_h2` remains in PRE_VALIDATION.** No Methodology Freeze, no
  gate outcome, and no lifecycle transition beyond Entry 3 has occurred.
- **Open items carried forward, not resolved by this log:** O-4 (evidence
  package still incomplete against the idealized seven-item structure);
  the unconfirmed-status residual risk from Entry 6 (whether pre-existing
  figures were consulted during specification drafting); the O-5 script-
  provenance gap (Entry 7, permanent and unrepairable, no numerical
  impact); no Level 3 review exists or is available on this platform for
  any entry above.
- **No outcome data** (forward return, Information Coefficient, p-value,
  or any other performance figure) has been read, computed, or referenced
  at any point reflected in this log.

---

## Entry 11 — Gate 1 ordering-requirement violation: finding recorded and exception granted

- **Date:** 2026-07-28 (this remediation pass; the events it concerns
  occurred earlier the same day — see the chronology below)
- **Decision:** `gate1_ordering_defect_finding_2026-07-28.md` records that
  the **Gate 1 ordering requirement in `prevalidation_plan.md` §3 was
  violated**. That requirement states that Gate 3's economic rationale must
  be frozen for the specific construction under test *before* the Gate 1
  check is run against it, the check being confirmatory on an
  already-decided construction rather than a search across candidates.
  Re-verified from repository evidence in this pass: `prevalidation_plan.md`
  was committed at 13:47:49 (`a7d0938`), the Gate 1 evidence run executed at
  13:58:46 (= `2026-07-28T11:58:46Z`, the artifact's own `generated_at`),
  and `attempt_001_specification.md` fixed the construction in writing only
  at 14:08:15 — 9 minutes 29 seconds *after* the run. **No Gate 3 economic
  rationale existed at the time of the run, and none exists now**; the
  cycle contains no Gate 3 document and no Gate 3 review at any date.
  `hypothesis.md` (00:53) states a candidate mechanism and predates the run,
  but is a Phase 1 artifact written before the construction existed and
  carries none of Gate 3's three required distinctness statements, so it
  does not discharge Gate 3. Both limbs of the ordering requirement were
  therefore unsatisfied at 13:58:46, with the requirement already in force
  (committed 10 minutes 57 seconds earlier). By contrast, `reference_h3` —
  whose ordering language this plan adopts by citation — ran Gate 3 (Entry 8
  of its own log, 01:48–02:00), then the construction freeze (10:51), then
  the Gate 1 evidence run (14:38), in the required order.
- **Distinctness from Entry 6.** This defect is **not** the false
  attestation Entry 6 corrected, and is not cured by that correction. Entry
  6 concerned a false *statement* about the chronology; its remedy was a
  truthful restatement, which was made and independently confirmed. This
  entry concerns the *chronology itself*: a perfectly truthful attestation
  at 14:08:15 would have left the ordering violation intact and undiminished.
  It is likewise distinct from the O-2/O-5 provenance limitations (Entry 7),
  which concern evidence-to-code/data traceability, not sequence.
- **Not retroactively curable.** No document written after 13:58:46 can
  place a Gate 3 rationale before it. Writing Gate 3 now, re-running the
  check against the now-frozen construction, the exact reproduction at Entry
  8, and any re-freezing of Attempt #1 are each recorded as **not** curing
  this defect.
- **Exception record** (per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §8, all
  four elements recorded together here):
  - **(1) Documented reason.** Attempt #1's Gate 1 evidence was produced out
    of the order `prevalidation_plan.md` §3 requires. The evidence is
    numerically reproducible (Entry 8: 483/483 dates bitwise identical,
    tolerance 0, re-derived from the frozen written specification) and is
    **not invalidated** by the ordering failure, which bears on governance
    sequence rather than arithmetic. Because the defect cannot be cured, the
    evidence is usable **only** under this exception, and only with the
    weakening at (2) disclosed wherever it is relied upon.
  - **(2) Impact assessment.** The protection weakened is **anti-hindsight**
    (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §1, first failure mode). It can
    no longer be established from the record that the construction fixed at
    14:08:15 was uninfluenced by figures already nine and a half minutes old,
    nor that any future Gate 3 rationale for this cycle is being written
    without knowledge of the Gate 1 result it must justify — a contamination
    risk that now attaches permanently to that future document, which must
    itself disclose it. The confirmatory-only posture the requirement
    enforces was not in place, so the record cannot exclude candidate-
    construction search. Residual risk is **accepted and unresolved in either
    direction**: no repository evidence shows any frozen element was selected
    or adjusted using the pre-existing figures, and none can now show it was
    not. Arithmetic evidence is **unaffected**.
  - **(3) Approval record.** Level 2 (AI-assisted adversarial) adjudication
    directing this remediation pass, whose factual premises were each
    re-verified against repository evidence before being recorded. **Gap,
    disclosed:** that adjudication reached this cycle as a governance
    directive, not as a dated `reviewer_reports/` artifact under §5's
    one-file-per-review-event convention, so its tier is self-reported and
    not independently verifiable from the archive alone. This entry and the
    finding artifact are themselves Level 1.
  - **(4) Time-box and remediation commitment.** Scoped to **this cycle and
    to Attempt #1's existing Gate 1 evidence only**; it does not extend to
    any later attempt, gate, or cycle. Commitments recorded: any future Gate
    3 economic rationale for `reference_h2` must disclose that it was written
    after the Gate 1 figures existed and must be reviewed at Level 2 with
    that disclosure in view; any Gate 1 evidence run for a subsequent attempt
    must follow `prevalidation_plan.md` §3's ordering; and whoever eventually
    makes the Gate 1 determination must have this entry and the finding
    artifact before them. This exception grants **no** permission to make
    that determination.
- **Evidence references:** `gate1_ordering_defect_finding_2026-07-28.md`
  (this entry's factual basis); `prevalidation_plan.md` §3, Gate 1
  ("Ordering requirement") and Gate 3 ("Economic rationale");
  `attempt_001_specification.md`; `attempt_001_addendum_2026-07-28.md`;
  `gate1_independence_analysis_2026-07-28.json` (`generated_at`);
  `reviewer_reports/2026-07-28_level2_gate1_confirming_reproduction.md`;
  commits `a7d0938`, `41ce0fb`, `c771355`, `04f83d1`;
  `research_archive/reference_h3/decision_log.md` Entries 8, 10, 11 (the
  precedent ordering).
- **Governance status:** Phase 3, Gate 1 — ordering violation recorded and
  governed by exception. **No gate outcome is created; Gate 1 remains
  undetermined.** No lifecycle transition; `transition_records.jsonl`
  unchanged at exactly one record with `gate_outcomes: []`; no Methodology
  Freeze exists. `reference_h2` remains in PRE_VALIDATION.
- **Reviewer level:** Level 1 (self-directed governance remediation),
  recording a Level 2 adjudication basis subject to the disclosed gap at
  exception element (3). No Level 3 review exists or is available on this
  platform.
- **Known limitations:**
  - The ordering defect is **permanent**. This entry records and governs it;
    it does not close it, and no future entry can.
  - Whether the pre-existing figures were actually consulted while drafting
    the specification remains **unconfirmed in either direction**, carried
    forward unchanged from Entry 6 rather than resolved here.
  - **The attempt-cap ruling in Entry 6 remains provisional** — valid on the
    facts as recorded, but not independently confirmed. The remaining
    attempt budget (two further attempts under the three-attempt cap) is to
    be treated as **provisional until confirmed**; nothing in this entry
    confirms it.
  - Entry 7's and Entry 10's notes that the remediation artifacts were "not
    yet committed" / "still untracked" were accurate when written and are
    **not edited**, per this log's append-only discipline; they are
    superseded in effect by the commit that carries this entry, which places
    `gate1_independence_analysis_2026-07-28.json`,
    `provenance_record_gate1_2026-07-28.json`,
    `attempt_001_chronology_correction_2026-07-28.md`, this log, and
    `gate1_ordering_defect_finding_2026-07-28.md` under version control for
    the first time.
  - Before that commit, and while all five were still uncommitted, two
    pre-commit corrections were made to as-yet-unarchived text: the
    placeholder `created_at` value in
    `provenance_record_gate1_2026-07-28.json` was replaced with the record's
    real authoring time and its `archiving_commit` handling was made
    logically consistent (see §"repository_provenance" of that file); and
    `attempt_001_chronology_correction_2026-07-28.md` §6's wording, which
    assumed this log did not yet exist, was updated to reference it. Neither
    edit changed a historical fact, a figure, or a conclusion. No committed
    archived file was edited.
  - O-4 (evidence package incomplete against the idealized seven-item
    structure) is narrowed by this pass but not closed; Gate 3's own
    required evidence, in particular, does not exist.

---

## Current status (as of Entry 11)

- **Phases 1–2 and the Phase 2 → 3 transition:** unchanged from the Entry 10
  status block above.
- **Phase 3 (Pre-validation):** governing plan frozen (Entry 4); Attempt #1
  construction frozen (Entry 5); attestation corrected (Entry 6);
  **Gate 1 ordering requirement violated, recorded, and governed by
  exception (Entry 11)**.
- **Gate 1:** evidence generated and archived (Entry 7); reproduced exactly,
  483/483 dates at tolerance 0 (Entry 8); ordering defect disclosed
  (Entry 11). **Gate 1 itself has not been determined — no PASS/FAIL/
  INCONCLUSIVE outcome exists.**
- **Gate 3:** **not started.** No economic-rationale document and no Gate 3
  review exists for this cycle at any date — the fact underlying Entry 11.
- **Gates 2 and 4:** not addressed in this cycle's artifacts to date.
- **`reference_h2` remains in PRE_VALIDATION.** No Methodology Freeze, no
  gate outcome, and no lifecycle transition beyond Entry 3 has occurred.
- **Attempt budget:** Attempt #1 of 3, with two further attempts nominally
  remaining — **provisional, per Entry 11's known limitations, until the
  Entry 6 cap ruling is independently confirmed.**
- **Open items carried forward, not resolved by this entry:** the permanent
  ordering defect (Entry 11); the O-5 script-provenance gap and O-2
  post-hoc database-identity capture (Entry 7); the unconfirmed-status
  residual risk from Entry 6; O-4 (evidence package incomplete); no Level 3
  review exists or is available on this platform for any entry above.
- **No outcome data** (forward return, Information Coefficient, p-value, or
  any other performance figure) has been read, computed, or referenced at
  any point reflected in this log.

---

## Entry 12 — Archived Level 2 review of the ordering exception

- **Date:** 2026-07-28
- **Decision:** The procedural exception recorded in Entry 11 has now
  received an independently archived Level 2 governance review:
  `reviewer_reports/2026-07-28_level2_ordering_exception_review.md`
  (commit `cdff7b5`). That review — a fresh session with no conversational
  continuity to the work under review — independently re-verified the
  chronology underlying Entry 11 and
  `gate1_ordering_defect_finding_2026-07-28.md` directly against
  repository evidence (commit timestamps, the artifact's `generated_at`
  field), confirmed the absence of any Gate 3 artifact at any date prior
  to or since the Gate 1 measurement, and confirmed that no
  `reviewer_reports/` artifact existed, prior to itself, supporting Entry
  11's approval-record claim under
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §8 item 3. The review accepted
  the exception as a narrowly scoped procedural exception, subject to the
  conditions stated in its own §7 (no expansion of scope beyond Attempt
  #1's existing Gate 1 evidence; Entry 11's forward commitments remain
  binding; whoever eventually makes the Gate 1 determination must have
  Entry 11, the finding, and the review itself before them; a
  discard-and-rerun of Attempt #1 under correct ordering remains an
  available alternative and is not foreclosed by this acceptance). This
  entry records the existence of that archived review and links it to
  Entry 11. **It does not modify, supersede, or withdraw Entry 11, and it
  introduces no new governance exception.**
- **Evidence references:** `decision_log.md` Entry 11 (the exception this
  entry links to); `gate1_ordering_defect_finding_2026-07-28.md`;
  `reviewer_reports/2026-07-28_level2_ordering_exception_review.md`
  (commit `cdff7b5`).
- **Governance status:** Phase 3, Gate 1 — the §8 item 3 approval-record
  gap Entry 11 itself disclosed (its claimed Level 2 basis was
  self-reported and had no archived, independently checkable form) is now
  closed by the cited review. Entry 11 remains the authoritative record
  describing the ordering defect and the exception itself; this entry
  supplies the missing approval artifact, it does not restate or
  re-adjudicate the underlying finding. The review's conditions are
  binding on all subsequent Gate 3 and Gate 1 work under this cycle. **No
  gate outcome is created by this entry; Gate 1 remains undetermined.** No
  lifecycle transition; `transition_records.jsonl` unchanged at exactly
  one record, `gate_outcomes: []`. No Methodology Freeze exists.
  `reference_h2` remains in **PRE_VALIDATION**.
- **Reviewer level:** Level 2 — AI-assisted adversarial, per the cited
  review's own tier statement (procedurally independent; **not
  organizationally independent**). This entry itself, which only records
  that review's existence and links it to Entry 11 rather than performing
  new review work, is Level 1.
- **Known limitations:** This entry does not alter
  `gate1_ordering_defect_finding_2026-07-28.md` and does not cure the
  historical sequencing defect, which remains permanent per Entry 11 and
  the finding's own §6. It does not change the requirement that any
  future Gate 3 artifact for this cycle must explicitly disclose that it
  was authored after the Gate 1 measurement already existed. It does not
  resolve, narrow, or touch the provisional attempt-cap ruling (Entry 6),
  the unconfirmed-influence residual risk (Entry 6, restated at Entry 11),
  or the O-1/O-2/O-4/O-5 provenance observations (Entries 7 and 10) — all
  remain open exactly as previously recorded. No Level 3 review exists or
  is available on this platform.

---

## Current status (as of Entry 12)

- **Phases 1–2 and the Phase 2 → 3 transition:** unchanged from the Entry
  10 status block above.
- **Phase 3 (Pre-validation):** governing plan frozen (Entry 4); Attempt #1
  construction frozen (Entry 5); attestation corrected (Entry 6); Gate 1
  ordering requirement violated, recorded, and governed by exception
  (Entry 11); **the exception's §8 item 3 approval-record gap closed by an
  archived Level 2 review (Entry 12)**.
- **Gate 1:** evidence generated and archived (Entry 7); reproduced exactly,
  483/483 dates at tolerance 0 (Entry 8); ordering defect disclosed and now
  Level-2-reviewed (Entries 11–12). **Gate 1 itself has still not been
  determined — no PASS/FAIL/INCONCLUSIVE outcome exists.**
- **Gate 3:** **not started.** No economic-rationale document and no Gate 3
  review exists for this cycle at any date.
- **Gates 2 and 4:** not addressed in this cycle's artifacts to date.
- **`reference_h2` remains in PRE_VALIDATION.** No Methodology Freeze, no
  gate outcome, and no lifecycle transition beyond Entry 3 has occurred.
- **Attempt budget:** Attempt #1 of 3, with two further attempts nominally
  remaining — **still provisional**, per Entry 11's known limitations,
  until the Entry 6 cap ruling is independently confirmed; Entry 12 does
  not confirm it.
- **Open items carried forward, not resolved by this entry:** the permanent
  ordering defect (Entry 11); the O-5 script-provenance gap and O-2
  post-hoc database-identity capture (Entry 7); the unconfirmed-status
  residual risk from Entry 6; O-4 (evidence package incomplete); no Level 3
  review exists or is available on this platform for any entry above.
- **No outcome data** (forward return, Information Coefficient, p-value, or
  any other performance figure) has been read, computed, or referenced at
  any point reflected in this log.
