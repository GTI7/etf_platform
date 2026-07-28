# `reference_h2` — Phase 2: Research Proposal

**Date:** 2026-07-28.
**Author:** Claude Sonnet 5 (this session).
**Artifact type:** Phase 2 Research Proposal (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2).
**Review level:** Level 1 self-review. No claim of independence is made anywhere in this document.

Phase 2 completion requires Level 1 review minimum. Before this proposal may proceed to Pre-validation, a Level 2 review is required according to `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 and §4.

This document consolidates already-existing candidate-selection evidence into this cycle's own artifact. It introduces no new ranking, no new score, and no new rejection rationale — every judgment below traces to `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` and `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`, both already accepted and committed. Where this document and those sources could be read to differ, the cited source governs.

---

## 1. Ranking Criteria

Per `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md` ("Remaining Candidates"), the five candidates under live consideration for the next REFERENCE research cycle — H2, H5, H6, H7, H8 — were ranked against criteria **fixed before any candidate was scored**:

1. **Economic rationale** — is there a plausible mechanism, and is it distinct from the platform's closed hypotheses?
2. **Overlap with closed tests** — independence from `reference_v1` (MOMENTUM/VALUE), `reference_v2_h1` (low volatility), and `reference_h3` (relative strength).
3. **Data requirements** — required history, available data, and known quality risks.
4. **Degrees-of-freedom risk** — how much researcher choice exists, and whether methodology can be frozen before results are seen.
5. **Expected research value** — what a positive or negative result would teach the platform.

These criteria were stated before the five candidates were scored against them and were not reweighted afterward. No criterion here is new; none was added, dropped, or adjusted after any candidate's score was seen.

## 2. Candidates Considered

Restated from `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`'s ranking summary and `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` §3–§4, using the same five criteria for every candidate, including the one selected — no candidate was scored on criteria the others were not also scored on.

| Rank | Candidate | Economic rationale | Overlap w/ closed cycles | Data readiness | Degrees-of-freedom risk | Expected research value |
|---|---|---|---|---|---|---|
| 1 | **H2** — Momentum (return-based, formation-period-with-skip construction) | High | Weakest — needed a written overlap argument against `reference_v1` MOMENTUM | Needs depth extension | Low — literature-fixed construction | High, conditional on clearing the overlap gate |
| 2 | H6 — Long-horizon reversal | High | Strongest | Poor, worsened at longer horizons | Low in principle, undermined by sample size | Medium — real risk of repeating `reference_h3`'s H3-A failure shape |
| 3 | H7 — Correlation-regime / idiosyncrasy | Medium–Low | Strong | Best — no data extension needed | High — sign-selection risk | Medium — fast to run, but Pre-validation gate risk is real |
| 4 | H5 — Carry / yield | High | Strong | Poor — new external data source required | Low | Medium long-term, low near-term (new provenance work required) |
| 5 | H8 — Macro-conditional beta exposure | High | Strongest | Poor — new data source and new statistical infrastructure required | Highest of the five | Low near-term — largest scope of any candidate |

## 3. Selection

**H2 was selected**, on the basis of the comparative ranking above — not on any expectation, stated or implied, that it will validate (`docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` §1: "not on any expectation, stated or implied, that it will validate").

The selection was based on the pre-existing ranking process, not on any result produced after that process began. H2 was a member of the original candidate shortlist established before `reference_v1` — the platform's first cycle — produced any result at all (`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`, cited in `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` §2.1: the shortlist "ranked H1 first and H3 second, prior to H1's own testing"). H2's construction was not adjusted in response to any numeric finding from `reference_v1`, `reference_v2_h1`, or `reference_h3`; each of those cycles' own entry requirements for what came after it explicitly prohibited exactly that: `reference_v1`'s own close-out states "No use of REFERENCE v1's results to select or tune v2's parameters," and the same discipline was preserved at each subsequent cycle, expressed in that cycle's own entry requirements rather than repeated verbatim — `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` §4's own item 3 for the candidate that became `reference_h3`, "No parameter tuning of v1 (or H1)," is one such restatement, not a quotation of the original sentence. No hindsight adjustment occurred: H2 is ranked and selected on the same criteria, stated the same way, as every rejected alternative — its rank was not raised, and no rejected candidate's rank was lowered, after any score was recorded.

## 4. Rejected Alternatives

Restated individually, preserving the specific reasoning already recorded in `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` §4 — not rewritten into generic "lower priority" language.

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
