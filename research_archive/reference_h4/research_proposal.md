# `reference_h4` — Phase 2: Research Proposal

**Date:** 2026-07-25
**Author:** Claude Sonnet 5 (this session), self-review only (Level 1).

Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 2, Phase 2, this document
ranks the Phase 1 hypothesis (`hypothesis.md`) against candidate alternatives
considered for this cycle, on criteria fixed before any candidate was scored.

## Ranking criteria (fixed before scoring)

This cycle's explicit purpose is proving the Phase A–E governance machinery
end-to-end for the first time against the real repository (see
`hypothesis.md`'s "Purpose of this cycle") — **not** an alpha search. The
criteria below are chosen for that purpose, not for research promise:

1. **Parameter count.** Fewer tunable choices (lookback windows,
   benchmarks, universes-within-universes) means fewer places a
   Methodology Freeze can silently under-specify something, and fewer
   researcher degrees of freedom for this cycle to demonstrate the freeze
   discipline against.
2. **Statistical self-containedness.** The candidate should be testable
   from data already in `experiments_etf_universe.db` (verified: 25 ETFs,
   daily `PriceBar` rows, 2016-09-13 to 2026-07-17), with no new data
   ingestion, indicator computation, or scoring-pipeline dependency.
3. **Prior replication strength.** A mechanism with strong, consistent
   prior replication in the literature is preferred, so a directionally
   unsurprising result (regardless of this cycle's actual outcome) can be
   attributed to the mechanism rather than to a novel or fragile
   construction — again because the goal is proving execution, not
   discovering something new.
4. **No overlap with in-flight or closed cycles.** Must be distinct from
   every mechanism already tested or in flight (`reference_v1`,
   `reference_v2_h1`, `reference_h3`, `positive_control_phase3`).

## Candidates considered

| Candidate | Parameter count | Self-contained? | Prior replication | Overlap | Score |
|---|---|---|---|---|---|
| **Excess kurtosis of daily log returns** (selected) | Lowest — one statistic, no lookback window, no benchmark index, no cross-sectional ranking | Yes — `PriceBar.close` only | Very strong — one of the most consistently replicated stylized facts in empirical finance across asset classes and periods | None — no prior cycle tests a return-distribution-shape property | **Selected** |
| Volatility clustering / ARCH effects (autocorrelation in squared returns) | Higher — requires choosing a lag structure and an autocorrelation significance test | Yes | Strong | None | Rejected — the lag-structure choice is exactly the kind of researcher degree of freedom this cycle's purpose (proving disciplined execution) is better served by avoiding, not because the mechanism is weak |
| Calendar effects (day-of-week / turn-of-month return patterns) | Higher — requires choosing which calendar effect(s) to test and a multiple-testing correction across them | Yes | Weak-to-mixed in post-2000 data — many published calendar effects have since attenuated or reversed | None | Rejected — weaker prior replication makes an unsurprising result less likely, and multiple candidate calendar effects reintroduces a selection decision this cycle doesn't need |
| Short-horizon mean reversion | Higher — requires a holding-period parameter and a benchmark for "reversion" | Yes | Mixed — regime-dependent, weaker consistency than kurtosis | None | Rejected — regime-dependence undermines "directionally unsurprising," and a holding-period parameter is a real degree of freedom |

## Selection

**Excess kurtosis of ETF daily log returns**, per `hypothesis.md`, ranks
highest on all four criteria: lowest parameter count, fully self-contained,
strongest prior replication, no overlap with any prior cycle. No further
candidates were scored after this ranking (Standard §2 Phase 2: "Ranking
criteria, once stated, may not be reweighted after candidates are scored").

## Approval state

Level 1 (self-review) only, recorded here per Standard §4. Level 2 is
applied later in this cycle at Methodology Freeze confirmation and the
Decision record (see `decision_log.md`); Level 2 is not required to
progress into Pre-validation and is not claimed here.
