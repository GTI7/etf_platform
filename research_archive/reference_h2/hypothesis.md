# `reference_h2` — Phase 1: Hypothesis

**Date:** 2026-07-27 (matches `archive_manifest.json`'s own `created_at` date, generated the same session as this document).
**Author:** Claude Sonnet 5 (this session), self-review only (Level 1 — see `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 4).

## Status

Phase 1 — Hypothesis. No formal gate applies at this phase (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2, Phase 1). This document is freely revisable until a Research Proposal is opened against it, and every revision must remain dated so a later reviewer can establish that this hypothesis predated any subsequent phase's results. It fixes no formula, benchmark, parameter, ranking method, forecast horizon, or evaluation metric — those belong to Research Proposal, Pre-validation, and Methodology Freeze, and are deliberately not decided here.

## Research Question

Do ETFs ranked higher by a trailing, multi-month cumulative return measure — formed over a recent formation period that excludes a short skip interval immediately preceding the ranking date — exhibit different subsequent returns than ETFs ranked lower by the same measure? The literature-standard prediction (see "Economic Mechanism," below) is that higher-ranked ETFs would show higher subsequent returns; this document states that prediction as the hypothesis under test, not as an expected or claimed finding.

## Economic Mechanism

Prices do not incorporate new information instantaneously. Information relevant to an asset's value diffuses gradually across investors with heterogeneous attention, information access, and processing speed, so a price's adjustment to a fundamental shock can continue for some time after the shock itself, rather than completing immediately. Under this account, an asset's return over a recent, sufficiently long formation period carries information about a still-incomplete price adjustment, and that adjustment's continuation is what a subsequent-period return would capture — this is the general underreaction / slow-information-diffusion account most closely associated with the cross-sectional momentum literature (Jegadeesh & Titman's original formation-period/holding-period framework, and its later behavioral-finance elaborations). A short skip interval between the formation period and the ranking date is a design feature of that same literature, intended to separate this effect from short-horizon reversal dynamics operating on a different, shorter timescale — named here as part of why the candidate is constructed this way, not as a frozen parameter.

No claim is made that this mechanism operates in this platform's specific universe, sample, or regime. The literature basis establishes plausibility of a general mechanism, not evidence for this platform's data.

## Novelty Boundary

`reference_v1`'s MOMENTUM used `SMA(20)` — a 20-day simple moving average of close price, unnormalized — directly as its cross-sectional score. This is a price *level* statistic, denominated in currency, not a return, rate-of-change, or trend-strength measure. H2 is constructed instead from trailing cumulative *return* over a materially longer formation period: a dimensionless ratio, invariant to an ETF's absolute share-price scale. This is a difference in what statistic is measured, not a parameter adjustment to an unchanged statistic.

`reference_v1`'s own documentation states no economic mechanism for MOMENTUM — no underreaction, trend-continuation, or other behavioral or informational account appears anywhere in its hypothesis or close-out record. H2's mechanism above is therefore not offered in contrast to a documented `reference_v1` mechanism; it would be the first explicit mechanism statement attached to a momentum-labeled construct on this platform. H2's mechanism is also distinct from the mechanisms already tested and closed on this platform: `reference_v2_h1`'s leverage-constrained-arbitrage / benchmarking-behavior account for low volatility, and `reference_h3`'s slower-cadence institutional-reallocation account for segment rotation.

**This does not establish that H2 is independent of `reference_v1`'s MOMENTUM in every sense.** A practical concern remains open and unresolved by this document: an ETF's price level and its trailing return are not guaranteed to be uncorrelated in this platform's specific 25-ETF universe, for reasons unrelated to either construct's own economic story. Whether `SMA(20)`'s cross-sectional rank and the candidate return measure's cross-sectional rank are empirically correlated in this data is a Pre-validation Gate 1 evidence item — construction and mechanism distinctness, established above, are necessary but not sufficient for that gate, and this document does not substitute for it.

The self-review supporting this novelty boundary (this session) was conducted adversarially but is not organizationally or procedurally independent under `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4: it was performed in the same session as the work it reviewed. It is correctly classified as Level 1 self-review, not Level 2 — §4's Level 2 definition requires review "by a separate AI session with no conversational continuity to the work," which did not occur. §4 states Level 1 is acceptable usage for "Hypothesis-phase... sanity checks only," which is the purpose this review was put to; it does not substitute for the genuine Level 2 review Research Proposal's approval state will require before Pre-validation.

## Expected Falsifiable Outcome

This hypothesis is falsifiable in the same terms every prior cycle on this platform has used: it would not be promoted if the candidate return measure shows no significant cross-sectional relationship with subsequent returns in this platform's sample, if a significant relationship exists but points opposite to the direction this mechanism predicts, or if a correctly-signed relationship does not survive the platform's established robustness bar. `reference_v1` (insufficient evidence), `reference_v2_h1` (directionally opposite), and `reference_h3` (evidence against) are each real, closed outcomes of that kind, not failures of the research process. No claim is made here about which of these outcomes, or a positive result, is more likely for H2.

## Known Open Questions

Deliberately undecided at this phase, deferred to Research Proposal, Pre-validation, and Methodology Freeze as appropriate:

- The SMA(20)-rank vs. candidate-return-rank correlation check (Pre-validation Gate 1 evidence, named above).
- Exact formation-period and skip-period length, in trading days.
- Return calculation basis (log vs. simple return) and treatment of dividends/distributions.
- How much of the platform's available price history the ranking-date panel will use.
- Forecast/holding horizon.
- Ranking method: tie-handling and minimum cross-sectional panel size.
- Statistical test design, significance and robustness protocol, and promotion/rejection criteria.

This document, together with `research_artifacts/reference_h2_registration.py` and `research_archive/reference_h2/archive_manifest.json`, establishes this cycle's identity and its Phase 1 hypothesis content. Nothing here authorizes Research Proposal, Pre-validation, Methodology Freeze, or Implementation to begin. No lifecycle transition under `core/research/lifecycle.py` has been executed.
