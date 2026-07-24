# `reference_h4` — Phase 4: Methodology Freeze

**Date:** 2026-07-25
**Author:** Claude Sonnet 5 (this session).
**Status:** FROZEN as of the git commit that adds this file alongside
`dataset_manifest.json` and `dataset_hashes/` (cited in `decision_log.md`).
Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 2, Phase 4: no element
below may change for any reason after this freeze; any change invalidates
the cycle and requires restarting from Phase 3 (attempt cap already at 1,
so in practice a wholly new cycle from Phase 1).

This fixes all eight elements Standard §3 requires before Implementation
(Phase 5) may begin.

## 1. Universe

Exactly 25 ETFs, named explicitly (not "the current universe" by
reference): `ACWI, ARKK, BND, BOTZ, EEM, EFA, EWJ, GLD, HACK, ICLN, IWM,
QQQ, SCHD, SKYY, SPY, TLT, USMV, VGK, VNQ, VT, VTI, XLE, XLF, XLK, XLV`.

## 2. Dataset version

`experiments_etf_universe.db`, `source="yahoo_finance"`, full available
history per ETF: 2016-09-13 to 2026-07-17, 2474 `PriceBar` rows per ETF
(61,850 total), 25 `ETF` rows, 2725 `TradingSession` rows. Snapshotted and
content-hashed in this same commit:

| source_table | rows | content_hash |
|---|---|---|
| ETF | 25 | `sha256:8a4ec0c201a6377a528ee76b7192f990451615fc5f40f4c8f16e96d185059ced` |
| TradingSession | 2725 | `sha256:e6dbc91aaf9636b6ce93b3a8b89e05ac1d5c0cab7a086baea7ac429101cb7a89` |
| PriceBar | 61850 | `sha256:132befd87b4f6095157701dd4e9d45eb5d9808bba21b9dbda65c24ad95b238c0` |

Full manifest: `dataset_manifest.json`; snapshot files: `dataset_hashes/{ETF,TradingSession,PriceBar}.jsonl`.

**Disclosed limitation (repeated from `prevalidation_plan.md`):**
`PriceBar.close` has not been confirmed to be split/dividend-adjusted. No
adjustment is applied in this methodology. If corporate-action jumps are
present in the raw series, they may inflate the measured excess kurtosis
beyond what volatility clustering / jump risk alone would produce. This is
a known, accepted limitation of this cycle's dataset, not a defect
requiring remediation before Implementation — remediating it would require
new ingestion work outside this cycle's scope.

## 3. Return definition

For each ETF and each pair of consecutive trading sessions (ordered by
`session_date`) with both `close` values present: `r_t = ln(close_t /
close_{t-1})`. No adjustment, no winsorization, no outlier removal. Rows are
taken in the order the frozen `PriceBar.jsonl` snapshot lists them for each
`etf_id`, sorted by `session_date`.

## 4. Statistic

Sample **excess kurtosis** (Fisher definition, i.e. kurtosis minus 3) of
each ETF's full log-return series:

```
g2 = (1/n) * sum((r_i - mean(r))^4) / [(1/n) * sum((r_i - mean(r))^2)]^2 - 3
```

computed once per ETF using that ETF's full available log-return series
(n ≈ 2473 returns per ETF, one fewer than the price-bar count). This is the
plain (uncorrected) sample excess kurtosis — no small-sample bias
correction is applied, since n ≈ 2473 is large enough that the correction's
effect is negligible and introducing it would be an added degree of freedom
this methodology does not need.

## 5. Cross-sectional aggregation rule

The **median** of the 25 per-ETF excess-kurtosis point estimates. Median,
not mean, is used specifically so a single extreme ETF (e.g. one more
affected by the close-price adjustment limitation above) cannot dominate
the cross-sectional summary.

## 6. Significance procedure

95% confidence interval for the cross-sectional median via **i.i.d.
bootstrap resampling of the 25 ETF-level point estimates** (not a
per-return-series block bootstrap): draw 25 of the 25 per-ETF kurtosis
values with replacement, compute the median of that draw, repeat, and take
the 2.5th/97.5th percentiles of the resulting distribution of medians.

- **Iterations:** 10,000.
- **Random seed:** `20260725` (fixed, so the CI is exactly reproducible from
  the frozen per-ETF point estimates alone — Standard §6 item 4).
- Implemented as a small, self-contained routine inside
  `experiments/validate_h4_kurtosis.py` (Phase 5) — not a reuse of
  `core.statistics.significance.bootstrap_ci`, whose block-bootstrap-over-a-
  panel shape is built for a different sampling unit (consecutive time
  periods within one series) than this cycle's cross-sectional resample
  (independent draws across the 25 ETFs). Forcing that function's shape
  onto this problem would misrepresent what is actually being resampled.

## 7. Aggregation rule / acceptance criterion (Standard §3 item 8)

**Frozen decision rule — the only rule that decides the outcome:**

> **PASS** if the bootstrap CI's lower bound (2.5th percentile) for the
> cross-sectional median excess kurtosis is **strictly greater than 0**.
> **FAIL** if the CI's upper bound (97.5th percentile) is **less than or
> equal to 0** (median excess kurtosis is not distinguishable from zero or
> negative). **INCONCLUSIVE** if neither — the CI spans zero on the lower
> side without clearing it (lower bound ≤ 0 < upper bound), the specific
> ambiguous case this rule is stated in advance to resolve as INCONCLUSIVE
> rather than adjudicated after seeing the result.

No other threshold, p-value, or robustness check determines PASS/FAIL/
INCONCLUSIVE for this cycle. This criterion may not be reweighted,
relaxed, or reinterpreted after Validation runs (Standard §7).

## 8. No unresolved degrees of freedom

Every choice `prevalidation_plan.md` §4 listed as open is now fixed above:
return definition, estimator, aggregation rule, significance procedure
(including seed and iteration count), and the acceptance criterion. Nothing
is left to be decided during Implementation or Validation.

## Freeze confirmation

This freeze document is confirmed complete against all eight items above.
Level 1 self-review confirms completeness now; a separate Level 2
adversarial review is recorded in `reviewer_reports/` (see
`decision_log.md`) before this freeze is relied upon for the Decision.
