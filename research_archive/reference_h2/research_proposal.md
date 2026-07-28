# `reference_h2` — Phase 2: Research Proposal

**Date:** 2026-07-28.
**Author:** Claude Sonnet 5 (this session).
**Artifact type:** Phase 2 Research Proposal (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2).
**Review level:** Level 1 self-review. No claim of independence is made anywhere in this document.

Phase 2 completion requires Level 1 review minimum. Before this proposal may proceed to Pre-validation, a Level 2 review is required according to `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 and §4.

This document consolidates already-existing candidate-selection evidence into this cycle's own artifact. It introduces no new ranking, no new score, and no new rejection rationale — every judgment below traces to `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` and `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`, both already accepted and committed. Where this document and those sources could be read to differ, the cited source governs.

---

## 1. Ranking Criteria

Per `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md` ("Remaining Candidates"), the **six** candidates under live consideration for the next REFERENCE research cycle — H2, H6, H7, H4, H5, H8, in that document's own ranking order — were ranked against criteria **fixed before any candidate was scored**:

1. **Economic rationale** — is there a plausible mechanism, and is it distinct from the platform's closed hypotheses?
2. **Overlap with closed tests** — independence from `reference_v1` (MOMENTUM/VALUE), `reference_v2_h1` (low volatility), and `reference_h3` (relative strength).
3. **Data requirements** — required history, available data, and known quality risks.
4. **Degrees-of-freedom risk** — how much researcher choice exists, and whether methodology can be frozen before results are seen.
5. **Expected research value** — what a positive or negative result would teach the platform.

These criteria are fixed for this cycle's own scoring pass in `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md` — Section 2's table below applies all five uniformly to all six candidates — and were not reweighted afterward. Whether criterion 5 ("Expected research value") existed in an earlier, unrecorded criteria set or was introduced for this cycle cannot be established from the repository: `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` (v1) scored these candidates on 4 of a disclosed-but-unrecovered 8-dimension original framework (v1 line 158), and that original framework is not present in this repository (`research_archive/reference_h3/decision_log.md`, Entry 1).

## 2. Candidates Considered

Restated from `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`'s ranking summary (all six remaining candidates) and, for H2/H5/H6/H7/H8, `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` §3–§4, using the same five criteria for every candidate, including the one selected — no candidate was scored on criteria the others were not also scored on. Note on sourcing: `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` §3 frames the field as a five-candidate shortlist (H2, H5, H6, H7, H8) without H4, and §1 discusses the remaining alternatives likewise without mentioning H4 anywhere. H4's row below is therefore sourced from `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md` alone, preserving that document's original rank (4 of 6), not from the Phase 5 review.

| Rank | Candidate | Economic rationale | Overlap w/ closed cycles | Data readiness | Degrees-of-freedom risk | Expected research value |
|---|---|---|---|---|---|---|
| 1 | **H2** — Momentum (return-based, formation-period-with-skip construction) | High | Weakest — needed a written overlap argument against `reference_v1` MOMENTUM | Needs depth extension | Low — literature-fixed construction | High, conditional on clearing the overlap gate |
| 2 | H6 — Long-horizon reversal | High | Strongest | Poor, worsened at longer horizons | Low in principle, undermined by sample size | Medium — real risk of repeating `reference_h3`'s H3-A failure shape |
| 3 | H7 — Correlation-regime / idiosyncrasy | Medium–Low | Strong | Best — no data extension needed | High — sign-selection risk | Medium — fast to run, but Pre-validation gate risk is real |
| 4 | H4 — Volume / flow acceleration | Medium | Strong | Uncertain — measurement validity, not fixable by more data | Medium | Low near-term — needs a data-quality sub-investigation first |
| 5 | H5 — Carry / yield | High | Strong | Poor — new external data source required | Low | Medium long-term, low near-term (new provenance work required) |
| 6 | H8 — Macro-conditional beta exposure | High | Strongest | Poor — new data source and new statistical infrastructure required | Highest of the six | Low near-term — largest scope of any candidate |

## 3. Selection

**H2 was selected**, on the basis of the comparative ranking above — not on any expectation, stated or implied, that it will validate (`docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` §1: "not on any expectation, stated or implied, that it will validate").

The selection was based on the pre-existing ranking process, not on any result produced after that process began. H2 was a member of the original candidate shortlist established before `reference_v1` — the platform's first cycle — produced any result at all (`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`: the shortlist "ranked H1 first and H3 second, prior to H1's own testing"). H2's construction was not adjusted in response to any numeric finding from `reference_v1`, `reference_v2_h1`, or `reference_h3`; each of those cycles' own entry requirements for what came after it explicitly prohibited exactly that: `reference_v1`'s own close-out states "No use of REFERENCE v1's results to select or tune v2's parameters," and the same discipline was preserved at each subsequent cycle, expressed in that cycle's own entry requirements rather than repeated verbatim — `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` §4's own item 3 for the candidate that became `reference_h3`, "No parameter tuning of v1 (or H1)," is one such restatement, not a quotation of the original sentence. No hindsight adjustment occurred: H2 is ranked and selected on the same criteria, stated the same way, as every rejected alternative — its rank was not raised, and no rejected candidate's rank was lowered, after any score was recorded.

## 4. Rejected Alternatives

Restated individually, preserving the specific reasoning already recorded in `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` §4 for H5/H6/H7/H8, and in `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md` for H4 (see sourcing note in §2 above) — not rewritten into generic "lower priority" language.

**H4 — Volume / flow acceleration.** Not addressed in `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` §4 — that document frames the field as only five remaining candidates (H2, H5, H6, H7, H8) and omits H4 from consideration entirely; this entry is restated instead from `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`'s "Remaining Candidates" §H4 (rank 4 of 6), not from the Phase 5 review like the other four entries below. Rejected on data readiness, specifically a measurement-validity problem rather than a data-volume problem: ETF-level volume is "contaminated by creation/redemption mechanics," which does not improve with more historical depth or a different forecast horizon. Data readiness is rated "Uncertain" — whether ETF-reported volume measures what the hypothesis needs is itself unverified, and resolving that would be a pre-validation research task of its own before any hypothesis-specific work could begin. Economic rationale was assessed as "Medium" (plausible order-flow-driven price-pressure mechanism, weaker literature grounding than H2 or H6) and independence from the three closed cycles as "High" (none of the closed cycles used volume/flow data). Expected near-term research value was rated "Low ... needs a data-quality sub-investigation first."

**H5 — Carry / yield.** Rejected on data readiness. No yield field exists in the current schema (`ETF`, `TradingSession`, `PriceBar`, indicators); a new external data source, with its own provenance and hash-tracking obligations under `docs/RESEARCH_GOVERNANCE_STANDARD.md` §6, would be required before any Phase 1–2 work could begin. Universe fit — whether the platform's curated sector/theme/regional universe exhibits meaningful, comparable yield dispersion — is unverified and not verifiable without that data. Economic rationale and degrees-of-freedom profile were both assessed favorably; readiness was the disqualifying factor.

**H6 — Long-horizon reversal (3–6 month).** Rejected on two grounds. First, an independence concern specific to this candidate: `reference_h3`'s own closed result (H3-B) is already a Holm-Bonferroni-significant reversal under a related construction; a long-horizon reversal hypothesis risks substantially overlapping with evidence the archive already contains, rather than testing a genuinely separate question. Second, a data-feasibility concern: a non-overlapping 3–6 month horizon consumes calendar history faster than shorter-horizon candidates, leaving as few as 4–8 independent windows even after a historical-depth extension — worse than H2's constraint, and not fully correctable by the same remedy.

**H7 — Correlation-regime / idiosyncrasy.** Rejected on economic rationale and freeze discipline, not on data or independence, both of which were assessed as the strongest in the shortlist. No a priori predicted direction has been established for this candidate in this project's record. Committing to a sign in order to run a one-sided test would itself introduce an undisclosed researcher degree of freedom — the specific failure mode `docs/RESEARCH_GOVERNANCE_STANDARD.md`'s freeze discipline exists to prevent. Retained informally as a fallback only if H2's Gate 1 (novelty review) fails and a genuinely pre-registered directional mechanism can be written for H7 independently.

**H8 — Macro-conditional beta exposure.** Rejected on readiness. Requires both a new external macro data source (no provenance path exists for it) and new statistical infrastructure beyond the `mean_ic` / `permutation_null` / `holm_bonferroni` / `bootstrap_ci` machinery reused unmodified across all three closed cycles to date. Carries the highest degrees-of-freedom exposure of any candidate considered — macro variable choice, conditional model form, and regime-detection method are all currently undetermined. Assessed as having the strongest independence and among the strongest economic rationale of the shortlist, but the furthest from executable.

## 5. Deferred Decisions Boundary

This artifact does **not** decide any of the following. Each remains open, exactly as `research_archive/reference_h2/hypothesis.md`'s "Known Open Questions" already states, and this document changes none of them:

- Formation period length.
- Skip interval length.
- Return calculation basis.
- Ranking method.
- Tie handling.
- Forecast horizon.
- Evaluation metrics.
- Rejection/promotion criteria.

These are Pre-validation and Methodology Freeze content (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2, Phases 3–4) and are not decided here. No correlation check, data-integrity re-check, or construction-attempt log is produced by this document — those belong to Pre-validation and remain unexecuted.

## 6. Approval State

Phase 2 completion requires Level 1 review minimum. Before this proposal may proceed to Pre-validation, a Level 2 review is required according to `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 and §4.

This document is Level 1 self-review only. It does not claim independence, procedural or organizational, in any respect. `research_archive/reference_h4/research_proposal.md`'s own approval-state text — "Level 2 is not required to progress into Pre-validation" — is not adopted here: that statement is inconsistent with `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2's own text and with `core/research/lifecycle.py`'s `_TRANSITION_AUTHORIZATION_FLOORS` table, which sets a Level 2 floor on the Research Proposal → Pre-validation transition.

---

This document authorizes no implementation, no code change, no ADR, and no lifecycle-phase transition. `core/research/lifecycle.py` recognizes no phase this document could advance on its own; a `DecisionRecord` asserting genesis `from_phase=HYPOTHESIS` remains a separate, later act. No formation window, skip interval, return calculation, ranking method, forecast horizon, or evaluation metric is fixed by this document.

---

## 7. Evidence Chronology Addendum (2026-07-28)

**Purpose.** This addendum corrects a chronology error in its own prior text and records what that correction implies, without altering any ranking, score, or rejected-alternative reasoning recorded in Sections 1–4 above. This addendum's original text mischaracterized when `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` was produced relative to this proposal. The chronology below is verified directly against git commit timestamps, not reconstructed from session memory or narrative.

**Chronology (corrected).**
1. The candidate ranking and scoring in Sections 1–4 above were sourced from `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md` and `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md`, both committed in `76382b5` (2026-07-28 00:03), before this document was drafted.
2. `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` was committed in `97961d4` (2026-07-28 00:19) — after the two source documents in item 1, but **before**, not after, this proposal's original drafting in `c0d5a18` (2026-07-28 01:17). It predates the original Section 2 table by 58 minutes. The original drafting of this proposal did not cite or incorporate it.

**Finding and its scope.** That review's read-only database inspection found that the historical-depth extension `reference_h3`'s Gate 2 executed (backfill to 2016-09-13, all 25 ETFs) is already present in the live database, and that H2's raw-data depth requirement is therefore already met without further backfill — a fact not reflected in either source document listed in item 1, both of which describe H2's data feasibility as requiring an extension.

Because the Gate 0 review predates this proposal's original drafting (item 2), this fact was already present in the repository when Section 2's table was first written — it was not discovered afterward. The original Section 2 table's "Needs depth extension" entry for H2 was therefore an unresolved, already-stale data-readiness statement at the moment of authorship: this proposal's original drafting failed to incorporate evidence that already existed, rather than being overtaken by evidence that arose later. This is a materially different situation than "later evidence arriving after a completed judgment," and this addendum's prior text stated the wrong one.

This correction does **not** retroactively alter the Data readiness rating for H2 in Section 2's table, nor any other candidate's rating, ranking, or rejection rationale in Sections 2–4, and does not change the Selection in Section 3. Section 2's table restates what the two source documents in item 1 state; revising that restatement — regardless of whether the correcting evidence is old or new relative to this proposal's own drafting — is not itself a Phase 2 act under `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2: Phase 2 ranks candidates against fixed criteria, it does not re-verify the factual premises those criteria's inputs rest on. Per `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` §2, a defensible Gate 2 requires "a fresh, dated data-inventory re-check" of this finding — not a citation of this addendum, and not a citation of another cycle's snapshot — together with a written decision on ranking-date panel span. That evaluation, and the resulting authoritative data-readiness determination for H2, belongs to, and is deferred to, Phase 3 (Pre-validation) data adequacy validation. The Gate 0 finding is relevant evidence for that Phase 3 determination; it is not a substitute for it, and nothing in this correction performs it.

**Future Gate 1 evidence requirement.** `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` §1 identifies one item of evidence not named in either source document in item 1: a cross-sectional correlation check between `reference_v1`'s `SMA(20)` rank and a trailing-12-1-month-return rank, computed across the same 25-ETF universe and a shared date range. Per that review's own Governance Boundary (§4), producing this check "require[s] new code in `experiments/`... Producing them is Pre-validation-phase evidence, not Gate-0 preparation." This requirement is therefore deferred to Phase 3. It is not decided, scheduled, scoped, weighted, or answered by this document, and it does not change the Section 5 Deferred Decisions Boundary list, the Selection in Section 3, or the Rejected Alternatives in Section 4.

No formation window, skip interval, return calculation basis, ranking method, tie handling, forecast horizon, or evaluation/rejection criterion is fixed by this addendum. No experiment is executed, and no lifecycle-phase transition is made or implied by it.
