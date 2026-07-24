# `reference_h4` — Phase 3: Pre-validation Plan

**Date:** 2026-07-25
**Author:** Claude Sonnet 5 (this session), self-review only (Level 1). No
outcome data (return values, kurtosis statistics) is touched anywhere in
this document, per `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 2, Phase
3's objective.

Following the gate structure `REFERENCE_H3_PREVALIDATION_PLAN.md`
established (signal independence, data adequacy, economic rationale, no
unresolved degrees of freedom), generalized here.

## 1. Signal independence — not applicable

This cycle tests a **distributional property of returns** (excess
kurtosis), not a scoring signal used to rank or select instruments. There
is no candidate signal to check for duplication against `reference_v1`,
`reference_v2_h1`, or `reference_h3`'s scoring constructions, because none
is being constructed. This sub-check is stated as N/A rather than silently
omitted, per Standard §2 Phase 3's requirement that the two standing
questions (duplicate signal / data adequacy) both be addressed.

## 2. Data adequacy

Verified directly against `experiments_etf_universe.db` in this session
(2026-07-24): all 25 ETFs in the universe (`ACWI, ARKK, BND, BOTZ, EEM, EFA,
EWJ, GLD, HACK, ICLN, IWM, QQQ, SCHD, SKYY, SPY, TLT, USMV, VGK, VNQ, VT,
VTI, XLE, XLF, XLK, XLV`) have exactly 2474 `PriceBar` rows each, spanning
2016-09-13 to 2026-07-17, all `source="yahoo_finance"` (a code-producible
source tag per Standard §6 item 2 — `core/market_data/providers/yahoo_finance.py`).

A minimum-adequate-sample threshold of **n ≥ 500 daily observations per
ETF** is adopted for this check — comfortably above what a 4th-moment
(kurtosis) point estimate needs to be numerically stable, and far below the
2474 actually available. All 25 ETFs clear this threshold by roughly 5×.
**Data adequacy: PASS**, min(count) = 2474 ≥ 500.

**Disclosed limitation** (Standard §6 items 2/5): `PriceBar.close` is
sourced from `quote["close"]` in `core/market_data/providers/yahoo_finance.py`
and has not been confirmed to be split/dividend-adjusted. If it is raw
(unadjusted) close, discrete jumps at ex-dividend dates or stock splits
would appear as return outliers and could inflate the measured excess
kurtosis beyond what a purely volatility-clustering/jump-risk mechanism
would produce on its own. This is recorded here as a known, unconfirmed-origin
data-provenance caveat (Standard §6 item 5 — an anomaly-adjacent disclosure,
not a defect being silently corrected), to be repeated in `methodology.md`
and accounted for when interpreting the Decision. It does not block
Pre-validation: it affects interpretation of *why* excess kurtosis might be
found, not whether the data is sufficient to measure it at all.

## 3. Economic rationale

Covered in `hypothesis.md` (volatility clustering / jump risk as the
candidate mechanism for fat tails). No new content added here — Standard §2
Phase 3 does not require re-stating it, only that Pre-validation's own gate
structure references it.

## 4. No unresolved degrees of freedom

The following are **not yet fixed** as of this document and will be fixed,
completely and immutably, at Methodology Freeze (Phase 4), before any
outcome data is read:

- the exact return definition (log return of `close`),
- the kurtosis estimator (sample excess kurtosis, Fisher definition),
- the cross-sectional aggregation rule (median across the 25 ETFs),
- the significance procedure (bootstrap CI, resampling scheme, iteration
  count, random seed),
- the frozen acceptance criteria (the exact PASS/FAIL/INCONCLUSIVE rule).

This document deliberately specifies none of them — doing so here would
make the later Methodology Freeze editorial rather than binding.

## Construction attempt log

This cycle has **one** planned construction attempt (attempt cap = 1),
stated before any attempt is logged, per Standard §2 Phase 3's requirement.
Rationale for a cap of 1: the methodology has no researcher-facing
construction step to iterate on (no signal weights, no lookback tuning) —
it is a single, fully-specifiable statistical procedure. If Methodology
Freeze confirmation (Phase 4) finds an unresolved degree of freedom this
document missed, that is treated as attempt 1 failing to clear Pre-validation,
and — per Standard §4 Phase 3's "Allowed changes" — requires this plan to
be revised and re-approved before a second attempt, rather than silently
patching the freeze document.

**Attempt 1** (this specification): logged 2026-07-25. No alternative
constructions were informally considered and set aside beyond the four
candidates already ranked and rejected in `research_proposal.md` — this
attempt is that hypothesis, unmodified.

## Approval state

Level 1 (self-review). Level 2 is applied at Methodology Freeze confirmation
(Phase 4) and the Decision record (Phase 7), per Standard §4's stated
minimums for those specific gates — not required here to proceed into
Methodology Freeze, and not claimed here.
