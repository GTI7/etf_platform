# REFERENCE v2 — H1 Low Volatility Research Specification

Frozen research specification, incorporating the corrections identified
by the adversarial review that preceded this document. No code, module,
or file design is proposed here — this document defines what must be
true before any implementation of H1 begins. Nothing in this document
is derived from or justified by REFERENCE v1's own statistical results
— REFERENCE v1 is referenced only to describe its methodology (for
reuse/comparison purposes), never as evidence for H1.

---

## 1. Research hypothesis

**Two pre-registered hypotheses**, resolved explicitly to separate the
classical anomaly test from a related-but-distinct risk-adjusted
performance question:

**H1-A — primary.** ETFs ranked lower in trailing realized volatility
will show a higher future *raw* return than ETFs ranked higher in
realized volatility, at a 20-trading-day forward horizon. This is
designated primary because it is the direct empirical form of the
classical low-volatility anomaly as actually tested in the founding
literature (see Part 2).

**H1-B — secondary diagnostic.** ETFs ranked lower in trailing realized
volatility will show a higher future *risk-adjusted* return than ETFs
ranked higher in realized volatility, at the same 20-trading-day
horizon, where risk-adjusted return is defined as:

> forward raw return ÷ forward realized volatility

**Forward realized volatility (exact definition, resolved).** The
denominator above is calculated **identically to Part 3's
trailing-volatility methodology** — close-to-close log returns, sample
standard deviation (N−1), not annualized — applied to the 20 forward
trading days following each ranking date. This is the same calculation
as Part 3's score, only applied prospectively instead of retrospectively;
no separate method is introduced.

**Clarification.** H1-B tests future risk-adjusted *performance* — a
distinct, economically meaningful but different question from H1-A. A
positive H1-B result indicates favorable risk-adjusted characteristics;
it does **not**, by itself, confirm or replicate the classical
low-volatility anomaly, which is defined in terms of raw returns
deviating from what a linear risk-return relationship predicts. H1-B
must never be substituted for H1-A, treated as equivalent to it, or
promoted to "primary" status after seeing results.

**Score construction is identical across both tests** — see Part 3.
Only the outcome variable differs between H1-A and H1-B.

*("Lower drawdowns" remains rejected as a primary or secondary claim —
a loss-avoidance statement, not a return-prediction statement, and out
of scope here.)*

---

## 2. Economic rationale

**Mechanism.** Two complementary, independently established
explanations:

- **Leverage-constrained arbitrage (Black, 1972; formalized in
  Frazzini & Pedersen, "Betting Against Beta," 2014).** Investors who
  want higher expected returns than a low-beta/low-volatility asset
  offers, but cannot or will not use leverage to scale that asset up to
  their target risk level, instead overweight higher-beta/
  higher-volatility assets directly. This bids up high-volatility
  asset prices and leaves low-volatility assets relatively underpriced
  against their fundamental risk-adjusted value.
- **Institutional benchmarking behavior (Baker, Bradley & Wurgler,
  "Benchmarks as Limits to Arbitrage," 2011).** Managers evaluated
  against a cap-weighted benchmark are structurally biased toward
  higher-beta, higher-tracking-error names, reinforcing the same
  distortion through preference rather than leverage constraint.

**Factor construct clarification (correction applied).** The
implemented score is **total realized volatility** — not idiosyncratic
volatility, not beta, and not a BAB-style (beta-neutral, risk-adjusted)
construct. These are three distinct constructs, routinely conflated
under the informal label "low-volatility anomaly," but not
interchangeable:

- Ang, Hodges, Xing & Zhang's headline result concerns *idiosyncratic*
  volatility (unexplained by a factor model), not total volatility.
- Frazzini & Pedersen's BAB factor is built as a beta-neutral,
  risk-adjusted long-short portfolio return — a risk-adjusted
  construct by design, not a raw-return comparison.

Using **total** realized volatility as the score is a deliberate proxy
choice appropriate to this project's instruments: ETFs are themselves
diversified baskets, so a much larger share of an ETF's total return
variance is expected to be systematic (market-like) rather than
idiosyncratic, unlike individual equities, where idiosyncratic risk is
typically a much larger share of total variance. Total volatility is
therefore treated here as a reasonable, if imperfect, proxy for
market-risk exposure — not as a literal replication of either cited
study's specific construct.

**Attribution to H1-A and H1-B (correction applied).** Because Ang et
al.'s own reported result is a comparison of **raw/total** returns
across volatility-sorted portfolios, that literature is attributed
primarily to **H1-A**. Because Frazzini & Pedersen's BAB result is a
**risk-adjusted, beta-neutral** construction by design, that mechanism
is attributed primarily to **H1-B**, not to H1-A. The two pre-registered
tests in Part 1 are intentionally aligned with these two different
strands of the literature, rather than both citations jointly
justifying H1-A alone.

**Why this is not simply another price-trend signal.** REFERENCE v1's
MOMENTUM (SMA(20)) and VALUE (RSI(14)) are first-moment signals —
derived from the level and direction of recent price movement. Realized
volatility is a second-moment signal — it measures dispersion,
independent of direction. An ETF can be simultaneously low-volatility
and trending up, down, or flat. Whether MOMENTUM rank and the LowVol
score are empirically correlated in this specific 25-ETF universe is
unverified and is named as a risk in Part 8, not assumed away.

**No overclaiming.** The academic evidence for this anomaly comes from
broad equity universes over multi-decade samples. Testing it on 25
sector/theme/regional ETFs over roughly two years is a far smaller,
narrower, shorter test. A result here — in either direction, for
either H1-A or H1-B — speaks only to this specific implementation and
sample.

---

## 3. Exact factor definition

Identical for both H1-A and H1-B — only the outcome variable differs
(Part 1, Part 6).

- **Lookback window: 60 trading days, frozen.**
  - **Why not 20 days.** 20 days equals the forecast horizon exactly,
    creating a mechanical-proximity risk between the score's own
    construction and the forecast window. 20 daily observations is
    also a short base for estimating volatility — the resulting
    cross-sectional score differences could reflect estimation noise
    rather than real differences in riskiness across ETFs.
  - **Why not 252 days (~1 trading year).** A full year materially
    dilutes current-regime information, working against the Part 2
    mechanism (plausibly a function of prevailing conditions, not a
    multi-year-averaged trait), and would raise the required
    pre-history buffer from 60 to 252 trading days, likely
    disqualifying a meaningful share of the currently available
    backfilled dataset.
  - **Why 60 is frozen.** 60 trading days (~1 calendar quarter)
    meaningfully reduces estimation noise relative to a 20-day window
    while remaining short enough to track current-regime volatility,
    and is clearly distinct from the 20-day forecast horizon. This
    value is fixed as a single pre-registered choice, not a range to
    be swept, tested at multiple lengths, or selected after seeing
    which produces a more favorable result.
- **Return data for the score:** daily close-to-close log returns.
- **Volatility calculation:** sample standard deviation (N−1) of the 60
  trailing daily log returns; not annualized (a constant per-date
  rescaling that cannot change cross-sectional rank order).
- **Score formula: `score = -1 × realized_volatility`** (negation, not
  inversion — inversion is numerically unstable near zero volatility;
  since only rank order enters the Spearman statistic, the simplest,
  most stable monotonic transform is preferred).
- **Missing data:** an ETF is included in a date's cross-section only
  if all 60 trailing days have a resolvable close price; otherwise
  excluded from that date entirely. No forward-fill, no interpolation,
  no partial-window calculation.
- **Ties:** handled by the existing average-rank convention already
  implemented for Spearman correlation — no new rule introduced.

---

## 4. Forecast horizon

**Decision: retain the 20-trading-day forward horizon**, for both H1-A
and H1-B.

- **Pipeline compatibility.** No change to the existing daily
  cross-sectional IC calculation, permutation machinery, or the
  20/40/60-day block-bootstrap structure.
- **Economic suitability.** The low-volatility anomaly is documented
  across horizons from roughly one month to multi-year holding
  periods; 20 trading days (~1 month) sits within that range.
- **Whether changing it would be a new question.** Yes, explicitly —
  a longer horizon would be a distinct study requiring its own
  specification, not a variant of this one.
- Retaining the horizon avoids changing the factor *and* the horizon
  simultaneously, which would make any eventual result harder to
  attribute.

---

## 5. Data requirements

- **Existing data sufficiency:** no new data source required. The
  score (60-day trailing realized volatility) and both outcome
  variables (raw forward return; forward realized volatility for
  H1-B's denominator, per Part 1) are all derivable from the existing
  daily close-price history.
- **Minimum lookback/lookahead:** at least 60 trading days of price
  history before the first ranking date, plus at least 20 trading days
  after the last ranking date.
- **Requiring verification, not assumed:**
  1. Whether the currently backfilled price history extends at least
     60 trading days before the first candidate ranking date —
     unconfirmed.
  2. Whether any ETF's price history contains gaps that would silently
     shrink its usable 60-day lookback window below the required
     minimum on a non-trivial number of dates — unconfirmed.
  3. Cross-sectional volatility dispersion adequacy — see the GO
     checkpoint below.
- **Universe:** reuse REFERENCE v1's same 25-ETF universe, for
  infrastructure comparability only.

### GO checkpoint — cross-sectional volatility dispersion (revised per adversarial review)

A **data suitability check, not a new experiment**, to be performed
before implementation begins.

- **Metric (corrected):** cross-sectional **coefficient of variation**
  of realized volatility across the 25-ETF universe on a given date:

  > CV = standard deviation(realized volatility across the 25 ETFs) ÷
  > mean(realized volatility across the 25 ETFs)

  computed using the exact Part 3 volatility definition (60-day
  trailing, log returns, sample stdev N−1, non-annualized). This
  replaces the previously specified max/min ratio, which characterized
  only the two most extreme ETFs and was blind to the rest of the
  cross-section.
- **Sample date selection (corrected, deterministic):** one valid
  ranking date per calendar quarter across the full available history,
  taking the **first valid ranking date in each quarter** — fixed by
  rule, not selected for favorable appearance.
- **Aggregation (corrected):** the **median** CV across all sampled
  dates. ("Typical" is no longer used as an undefined term.)
- **GO threshold: median CV ≥ 0.20** across sampled dates.
- **Scope (explicit):** this check uses the score variable only. It
  does not compute, read, or reference any forward return,
  risk-adjusted return, or any other outcome-variable quantity, and
  involves no hypothesis test, no p-value, no permutation, and no
  bootstrap. This is what makes it a suitability check rather than an
  experiment — it cannot leak outcome information into the score's
  design and carries no look-ahead risk.
- **NO-GO consequence:** if dispersion is inadequate, the correct
  response is to reconsider the universe composition — a
  specification-level decision requiring its own review, not a
  code-level workaround.

---

## 6. Validation protocol

Reuses REFERENCE v1's statistical machinery without modification to
its methodology, applied to two pre-registered statistics.

- **H1-A (primary) statistic:** daily cross-sectional Spearman IC
  between the LowVol score and raw forward return, averaged across
  ranking dates — one correlation per date, never pooled.
- **H1-B (secondary diagnostic) statistic:** daily cross-sectional
  Spearman IC between the LowVol score and risk-adjusted forward
  return (forward raw return ÷ forward realized volatility, per Part 1's
  exact definition), averaged across ranking dates, same construction.
- **Significance:** within-date permutation test (score shuffled
  within each date, each outcome held fixed for its respective test),
  10,000 iterations minimum, per statistic, each with its own
  independent shuffle series.
- **Multiple comparisons — Holm-Bonferroni handling:** Holm-Bonferroni
  correction is applied jointly across exactly this family of 2
  statistics (H1-A, H1-B) — sorted ascending by raw p-value, adjusted
  p = min((n − rank) × raw p, 1.0), n = 2. Fixed before either statistic
  is computed.
- **Uncertainty:** block bootstrap at 20/40/60-trading-day blocks,
  2,000 iterations per block length minimum, per statistic, identical
  contiguous whole-date-block construction to REFERENCE v1.
- **Minimum panel size rule (new, correction applied).** For a given
  ranking date to be included in either H1-A's or H1-B's daily
  cross-sectional IC calculation, at least **10 ETFs** must have valid
  score data (per Part 3) and valid outcome data (resolvable forward
  prices) on that date. Dates with fewer than 10 valid ETFs are
  excluded from the panel entirely — not down-weighted, not imputed.
  This threshold is inherited unmodified from REFERENCE v1's own
  established minimum (`bucket_size × 2`, with `bucket_size = 5`).
- **Reproducibility requirement (new, correction applied).** All
  permutation and bootstrap procedures must use a single, fixed,
  documented random seed, selected and recorded before any results are
  generated or examined. The literal seed value is an implementation
  detail and is not fixed by this specification.
- **Undefined-statistic handling (new, correction applied).** An
  undefined permutation p-value, or a bootstrap confidence interval
  that cannot be computed at a given block length (e.g. due to an
  insufficient number of usable resampled estimates), automatically
  fails that criterion — inherited unmodified from REFERENCE v1's
  convention. No manual interpretation or case-by-case judgment is
  permitted.

**Promotion criteria (unchanged from the prior revision):**

| H1-A result | H1-B result | Outcome |
|---|---|---|
| Passes (Holm-Bonferroni significant + bootstrap-robust across 20/40/60d) | Passes | **Promote to REFERENCE v2.** Strongest result: classical anomaly confirmed and corroborated by superior risk-adjusted performance. |
| Passes | Fails | **Promote to REFERENCE v2**, on H1-A alone, since H1-A is the pre-registered primary driver of promotion. The H1-A/H1-B divergence must be explicitly explained in the audit stage, not silently dropped. |
| Fails | Passes | **Do not promote.** H1-B passing alone is insufficient — the primary, classical-anomaly test did not clear the bar. Recorded distinctly as "risk-adjusted characteristic observed, classical anomaly not confirmed" — a real, preserved finding, but not a promotion trigger. |
| Fails | Fails | **Archive**, classified via the same three-category framework used for REFERENCE v1 (implementation error / implementation correct, evidence insufficient / implementation correct, evidence against), determined by an independent code-only audit. |

"Passes" for either statistic means, identically to REFERENCE v1:
Holm-Bonferroni-adjusted p < 0.05 **and** the bootstrap CI excludes
zero at all three block lengths (20, 40, 60 days), subject to the
undefined-statistic handling rule above.

---

## 7. Comparison with REFERENCE v1

- **Not hidden momentum.** MOMENTUM is a first-moment (level/direction)
  signal; the LowVol score is a second-moment (dispersion) signal,
  structurally distinct by construction. Whether the two are
  empirically correlated in this universe is unverified and named as a
  risk (Part 8).
- **Not parameter tuning.** H1 adjusts none of REFERENCE v1's SMA/RSI
  windows, weights, thresholds, or normalization method. Its 60-day
  lookback was independently justified against 20-day and 252-day
  alternatives (Part 3) — not derived from or tuned relative to
  REFERENCE v1's own window lengths.
- **Not engineered from REFERENCE v1's results.** This specification's
  sole justification (Part 2) is established, independent literature.
  REFERENCE v1's numeric results were not consulted in selecting this
  hypothesis, its lookback window, its outcome variables, or its
  promotion criteria.

---

## 8. Research risks

- **Small universe (25 ETFs)** may lack adequate cross-sectional
  volatility dispersion — addressed procedurally by the Part 5 GO
  checkpoint, but the checkpoint's own 0.20 CV threshold is itself a
  judgment call, not a guarantee of a meaningful effect if passed.
- **Limited effective sample size** from overlapping 20-day forward
  windows — a structural constraint independent of which factor is
  tested.
- **Reduced return magnitude in H1-A.** If volatility genuinely
  compresses raw returns, H1-A's effect (if any) may be small in
  absolute terms and harder to distinguish from noise than H1-B's.
- **Regime dependence.** The anomaly's documented strength varies by
  market regime, including weakening or reversal during strong
  momentum-driven markets; the available ~2-year window represents one
  regime only.
- **ETF composition bias.** Diversified sector/theme/regional baskets
  already have dampened idiosyncratic volatility relative to
  single-name equities, which may compress the dispersion the anomaly
  needs to be detectable.
- **Score/outcome mean-reversion overlap (H1-B).** Both the score's
  60-day trailing lookback and H1-B's 20-day forward risk-adjustment
  denominator are volatility measures of the same price series.
  Realized volatility is known to mean-revert, creating a risk of a
  mechanical statistical relationship between score and H1-B's outcome
  unrelated to any genuine excess-return anomaly. This risk does not
  apply to H1-A, whose outcome (raw return) is not itself a volatility
  measure.
- **H1-B denominator risk (explicit disclosure, correction applied).**
  No floor or clipping is applied to the forward realized-volatility
  denominator. Extremely low forward-volatility observations may
  produce extreme, rank-distorting risk-adjusted values unrelated to
  genuine risk-adjusted performance. This limitation applies only to
  H1-B — H1-A's raw-return outcome involves no division and is
  unaffected — and is a further, explicit reason H1-B cannot
  independently drive the promotion decision (Part 6). It is disclosed
  here rather than corrected via a new floor/clip parameter, to avoid
  introducing an undocumented threshold.

---

## 9. Go / No-Go checklist

**GO if:**
- [ ] H1-A (primary) and H1-B (secondary diagnostic) hypotheses, their
  score formula, outcome variables (including H1-B's exact forward
  realized-volatility definition, Part 1), lookback window, and
  forecast horizon are each specified exactly once with no remaining
  either/or choices (Parts 1, 3, 4)
- [ ] The 60-trading-day pre-history and 20-trading-day post-history
  requirements are confirmed present in the currently available price
  history (Part 5, item 1)
- [ ] The cross-sectional volatility dispersion GO checkpoint (Part 5)
  has been run using the corrected CV metric, quarterly deterministic
  sample dates, and median aggregation, and the median CV ≥ 0.20
  threshold is met
- [ ] No missing-data gaps materially shrink the usable lookback window
  for a meaningful share of ETF-dates (Part 5, item 2)
- [ ] The minimum panel size rule (≥10 valid ETFs per date, Part 6) is
  understood to apply identically to both H1-A and H1-B
- [ ] A fixed, documented random seed for all permutation/bootstrap
  procedures has been selected and recorded before any results are
  generated (Part 6)
- [ ] The undefined-statistic handling rule (Part 6) is confirmed to
  apply without exception
- [ ] Promotion criteria and Holm-Bonferroni handling for the H1-A/H1-B
  pair (Part 6) are fixed in writing and will not be revisited after
  results are seen

**NO-GO if:**
- [ ] The dispersion checkpoint fails the median CV ≥ 0.20 threshold,
  and the response would require silently lowering the threshold or
  reweighting the universe after the fact rather than a documented
  specification-level revision
- [ ] Any other verification above surfaces a problem requiring a new
  assumption introduced only to route around it
- [ ] Implementation would require deciding, after seeing results,
  which of H1-A or H1-B counts as "primary" — this must never happen;
  the assignment in Part 1 is final
- [ ] The volatility-mean-reversion and denominator-distortion
  confounds affecting H1-B (Part 8) cannot be explicitly planned for in
  the eventual audit stage
- [ ] A fixed random seed has not been selected and recorded before
  results are generated

This specification is frozen as written. No implementation should
begin until every unresolved verification item above is closed.
