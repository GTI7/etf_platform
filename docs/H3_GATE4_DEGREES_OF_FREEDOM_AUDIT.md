# H3 Gate 4 — Degrees-of-Freedom Audit

**Auditor role.** Institutional Quant Research Degrees-of-Freedom
Auditor. This document does not evaluate, improve, tune, or modify H3's
methodology, scoring logic, parameters, or acceptance criteria, and no
experiment was rerun to produce it. It assesses whether material
researcher choices were frozen, justified, and documented **before**
validation, using only the written record and git history as evidence.

**Frozen reference audited.** Commit `07f0da379d8cccf06d17c34a51cbb557da047fef`
("freeze REFERENCE H3 construction Attempt 1 and pre-validation
governance record"), plus the untracked Gate 1 evidence produced after
that commit (`docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`,
`docs/H3_GATE1_REPRODUCTION_REVIEW.md`,
`research_archive/reference_h3/gate1_final_determination.md`), read as
of repository `HEAD` `149ae44`.

**Evidence reviewed.**
`research_archive/reference_h3/attempt_001_specification.md`,
`docs/REFERENCE_H3_PREVALIDATION_PLAN.md`,
`docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`,
`docs/H3_GATE1_REPRODUCTION_REVIEW.md`,
`docs/RESEARCH_GOVERNANCE_STANDARD.md`,
`research_archive/reference_h3/FREEZE_RECORD.md`,
`research_archive/reference_h3/decision_log.md`,
`research_archive/reference_h3/gate1_final_determination.md`, plus
direct inspection of `experiments/daily_etf_universe_update.py:89-120`
and its git history (`git log --follow`, `git merge-base --is-ancestor`)
to independently verify — not merely accept — the specification's claim
that the universe and segment definitions predate H3.

---

## 1. Executive Summary

**Overall Gate 4 status: PASS**, on the specific question this audit is
scoped to answer — whether the researcher degrees of freedom in the
frozen H3 construction (Attempt 1) were controlled, i.e. fixed and
justified before any outcome or correlation figure was seen.

**Rationale.** Across all seven audited categories, the material design
choices are documented as having been fixed in writing before the
relevant measurement was made, with disclosed rejected alternatives and,
in two categories (universe, segment definitions), independent
git-history proof — not merely a document's own claim — that the choice
predates H3's existence by two days and was authored for an unrelated
purpose. The one category with a genuinely open item (acceptance
criteria for H3's *eventual* significance test, as opposed to Gate 1's
own interpretation rule) is an explicitly deferred, disclosed,
appropriately-scoped-to-a-later-phase gap under this project's own
governance framework, not a silent or discovered-after-the-fact
degree of freedom — it is documented as open, not concealed as closed.

This PASS is qualified by two disclosed, non-blocking limitations
(Section 3, "Non-blocking issues") that a reader should not mistake for
resolved: the absence of any Level 3 (organizationally independent)
review anywhere on this platform, and the fact that Gate 1's own final
determination record has not yet been committed to version control or
logged in the append-only decision log. Neither is a degrees-of-freedom
control failure in the frozen construction itself; both bear on how much
weight this PASS should carry until closed.

---

## 2. Degrees-of-Freedom Matrix

| Category | Status | Evidence | Risk |
|---|---|---|---|
| 1. Universe selection | CONTROLLED | 25-ETF universe (`attempt_001_specification.md` §3.1) reused unchanged from `experiments/daily_etf_universe_update.py:89-120`. Git history: that file was authored in commit `0e06fdd` (2026-07-17, "add external ETF universe experiment runner"), independently confirmed via `git merge-base --is-ancestor 0e06fdd 07f0da3` to be an ancestor of the H3 freeze commit — i.e. it predates H3's first construction attempt (2026-07-19) by two days and was written for an unrelated purpose. | Low. Cannot have been shaped by an H3 result that did not yet exist when the universe was fixed. |
| 2. Lookback period (60 days) | CONTROLLED | `attempt_001_specification.md` §3.5 gives two non-outcome justifications: (a) matches the institutional quarterly review cadence Gate 3's mechanism itself cites; (b) reuses the identical 60-day window independently justified in `docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` Part 3 for a prior, unrelated research cycle — confirmed present in that document by direct read. The document explicitly records that 60 days was *not* set to match MOMENTUM's 20-day `SMA` window, and states why matching it would itself have been a red flag ("gaming the independence check"). | Low. Reuse of a previously-frozen, differently-motivated parameter is a materially weaker overfitting path than a parameter chosen fresh for this construction. |
| 3. Segment definitions | CONTROLLED | Six segments (§3.2), partitioning all 25 ETFs with no overlap and no residual, reused verbatim from the same pre-existing, pre-H3 comment blocks in `daily_etf_universe_update.py:89-120` (same git-history proof as row 1). The one structural weak point — a 2-member Global equity segment — is disclosed by name in §3.10 as a known limitation, not silently corrected. | Low–Medium. The 2-member segment concentrates whatever noise exists in that segment's peer-relative score into a single comparison; disclosed but not analytically resolved by the frozen construction. |
| 4. Scoring methodology | CONTROLLED | Formula frozen in §3.5 (`own_return − peer_return`, equal-weighted peer average, self excluded, log returns). Two alternative formulations (single common-benchmark subtraction; leave-one-out universe-mean subtraction) were rejected via algebraic proof of rank-identity to absolute-return ranking, worked out and recorded in §4 *before* any Gate 1 correlation was computed. A further within-group affine-invariance property was likewise derived algebraically, before measurement, so an explanation would exist on the record regardless of what any future correlation showed. | Low. The rejections rest on provable algebra, not on an impression of how alternatives would correlate with MOMENTUM. |
| 5. Missing data handling | CONTROLLED | Rule frozen in §3.9 (exclude unless own 60-day return and ≥1 peer's are resolvable; no forward-fill/interpolation) before Gate 1 ran. Independently verified in `docs/H3_GATE1_REPRODUCTION_REVIEW.md` §4.4 that all 483 evaluated dates carried a full 25-ETF cross-section — the rule did not silently distort any evaluated date. | Low. |
| 6. Evaluation window | PARTIALLY CONTROLLED | Nominal window (2024-07-17 to 2026-07-17) is REFERENCE v1's own already-fixed window, reused rather than chosen for H3 — not a new discretionary choice. However, 19 of the nominal 502 dates were found, during validation, to have no `Score` row for any ETF and were mechanically dropped (483/502 evaluated). This is disclosed, non-discretionary (data-availability driven, not a boundary picked to improve the result), and independently re-confirmed against the live database by the reproduction review. It is marked PARTIALLY rather than fully CONTROLLED because the realized evaluation set was only established *during* the validation run, not fully known at freeze time. | Low–Medium. No evidence the dropped dates were selected to favor a result; the gap sits on the MOMENTUM/`Score` side, not the H3 side, and both reports flag it as a database completeness issue for a future maintainer, not a methodology lever. |
| 7. Acceptance criteria | PARTIALLY CONTROLLED | Gate 1's own PASS/FAIL interpretation rule — the near-1.0 degenerate-case rejection trigger, the moderate-correlation-requires-explanation rule, and the ambiguity-resolution default to the stricter reading — was frozen in `REFERENCE_H3_PREVALIDATION_PLAN.md` §2 before any Gate 1 figure existed, and applied without amendment in the validation report. This narrow criterion is CONTROLLED. Separately, and explicitly disclosed rather than concealed, the acceptance criteria for H3's *eventual* significance test (forward-return promotion threshold) has not been written — `decision_log.md` Entry 10 records this as "explicitly deferred to a document not yet written." Under this project's own eight-phase lifecycle (`RESEARCH_GOVERNANCE_STANDARD.md` §2), that criterion belongs to Phase 4 (Methodology Freeze), which follows a Gate 4 PASS — so its absence now is appropriately sequenced, not a violation, but it is a real open item a reader should not assume is already closed. | Medium. Not a hindsight-bias risk today (no outcome data has touched this undefined criterion), but it is the one place in this audit where "no unresolved degree of freedom" is not yet literally true — it is deferred, not resolved. |

---

## 3. Material Findings

### Blocking issues

None identified. No category shows a design choice that was selected,
adjusted, or reverse-engineered after outcome data was seen.

### Non-blocking issues

1. **No Level 3 (organizationally independent) review exists on this
   platform, for H3 or any prior cycle.** Every attestation this audit
   relied on — that no outcome data influenced construction selection,
   that rejected alternatives were set aside on economic grounds only —
   is self-reported by the same single-operator, same-model-vendor
   process that did the underlying work, disclosed as such throughout
   the archive (`RESEARCH_GOVERNANCE_STANDARD.md` §4). This does not
   invalidate the CONTROLLED findings above, which rest on independently
   checkable evidence (git history, algebraic proof, byte-for-byte
   reproduction) rather than on the attestations alone — but the
   attestations themselves cannot be verified beyond the Level 2 tier.
2. **Gate 1's final determination is not yet archived per this
   project's own discipline.** `research_archive/reference_h3/gate1_final_determination.md`
   and its supporting evidence (`docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`,
   `docs/H3_GATE1_REPRODUCTION_REVIEW.md`,
   `experiments/validate_h3_gate1_independence.py`,
   `research_archive/reference_h3/gate1_independence_analysis_2026-07-19.json`)
   remain untracked in git as of `HEAD` `149ae44`, and no corresponding
   entry has been appended to the append-only `decision_log.md`. This is
   a documentation-completeness gap, not a degrees-of-freedom problem in
   the construction itself — but until it is committed and logged, Gate
   1 is evidenced, not yet governance-final, by the archive's own
   standard.
3. **Bottom-tail rank-overlap asymmetry is measured but unexplained.**
   Bottom-5 overlap (median 40%) is roughly double top-5 overlap (median
   20%, at chance), confirmed identically by independent reproduction.
   This is not itself a degree-of-freedom violation — no parameter was
   adjusted in response to it — but it is a disclosed open analytical
   question that a future reviewer should not mistake for resolved.
4. **Acceptance criteria for H3's eventual significance test remain
   unwritten** (Matrix row 7). Appropriately sequenced to a later phase
   under this project's own lifecycle, but worth restating here as a
   standalone item: nothing in H3's specification currently states how
   near-threshold Phase 6 (Validation) results will be resolved, beyond
   the general principle ("default to the stricter reading") already
   established for Gate 1 specifically.

---

## 4. Hindsight Bias Assessment

**Could decisions have been influenced by observed outcomes?** The
evidence trail supports "no" for every frozen construction element,
with independently checkable support in the two highest-leverage
categories:

- **Universe and segment definitions** were authored in a commit
  (`0e06fdd`, 2026-07-17) that is a git-verified ancestor of the H3
  freeze commit and predates any H3-related document by two days,
  for a stated purpose ("external ETF universe experiment runner")
  unrelated to H3. These choices cannot have been shaped by an H3
  result, because no H3 result — and no H3 hypothesis — existed yet.
- **Lookback window, scoring formula, and missing-data rule** were
  fixed in a single specification document (`attempt_001_specification.md`,
  dated 2026-07-19) whose own Section 5 attestation discloses four
  informally considered and rejected alternatives, each with a
  stated non-outcome reason, and whose Section 4 algebraic analysis
  is dated and reasoned *before* the Gate 1 correlation figure existed
  — confirmed by the validation report's own freeze-drift check
  (`git diff 07f0da3 HEAD` empty for the specification file) and by
  the independent reproduction review reaching identical figures via a
  second, disjoint implementation.
- **Gate 1's interpretation rule** (degenerate-case boundary, moderate-
  correlation explanation requirement, ambiguity-resolution default)
  was committed as part of the same freeze (`07f0da3`) before the
  validation report that applied it was produced.

**Did methodology changes occur after results were known?** None found.
`git diff 07f0da3 HEAD` for every frozen file (`attempt_001_specification.md`,
`REFERENCE_H3_PREVALIDATION_PLAN.md`,
`docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`,
`RESEARCH_GOVERNANCE_STANDARD.md`) is empty, independently confirmed by
both the validation report and the reproduction review, each run in a
separate session. The one repository change since the freeze commit
(`149ae44`) adds only provenance/decision-log documents and does not
touch any frozen construction or methodology file.

**Residual caveat.** This assessment can confirm internal consistency
and chronological ordering (via git history) beyond what the documents
merely claim about themselves. It cannot independently confirm that no
*undisclosed*, off-repository exploration occurred before the first
commit — that assurance rests on the pre-log attestation and the Level
2-only review tier disclosed throughout the archive (Section 3, Non-
blocking issue 1).

---

## 5. Final Gate 4 Determination

**PASS**, on the degrees-of-freedom question this audit is scoped to
answer: the material researcher choices behind H3 Attempt 1 — universe,
lookback window, segment grouping, scoring formula, missing-data rule,
and Gate 1's own interpretation criteria — were frozen, justified on
non-outcome grounds, and documented before the relevant measurement was
made, with independently verifiable (not merely self-reported) support
in the two categories carrying the most disguised-momentum risk
(universe, segments).

**Remaining limitations (carried forward, not resolved by this audit):**

1. No Level 3 (organizationally independent) review exists for H3 or
   any prior cycle on this platform; every finding above rests on
   Level 2 (procedurally independent) evidence at most.
2. Gate 1's final determination record and its supporting evidence are
   not yet committed to version control or logged in the append-only
   decision log.
3. The bottom-tail rank-overlap asymmetry is measured, reproduced, and
   unexplained.
4. Acceptance criteria for H3's eventual significance test (as distinct
   from Gate 1's own, already-frozen interpretation rule) have not been
   written, and are not required to have been at this stage under this
   project's own phase sequencing — but they remain a real, open item.
5. 19 of 502 nominal evaluation-window dates could not be evaluated due
   to a database coverage gap on the MOMENTUM/`Score` side, disclosed
   and independently re-confirmed, not a discretionary window choice.

**Next allowed action.** Per this project's own governance framework,
this Gate 4 determination does not itself authorize writing a frozen H3
specification — that requires Gates 1–3 to also be governance-final
(Gate 1's determination committed and logged, per Section 3, Non-
blocking issue 2), and requires the acceptance-criteria item (Matrix row
7) to be resolved at the Methodology Freeze phase, not before. No H3
methodology, parameter, benchmark, universe, or acceptance criterion
was modified, tuned, tested against an alternative, or newly introduced
by this audit.
