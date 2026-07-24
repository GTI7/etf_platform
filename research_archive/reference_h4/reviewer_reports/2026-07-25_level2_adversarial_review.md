# `reference_h4` — Level 2 Adversarial Review

**Level 2 — AI-assisted adversarial review.** Procedurally independent
(separate session, no conversational continuity with the work being
reviewed, adversarial posture, independently re-derived rather than
inspected reported figures). **NOT organizationally independent** (same
underlying model family/vendor as the work being reviewed; no incentive
separation) — per `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 4, this
qualifier is required and this review must never be described with the
unqualified word "independent."

**Reviewer:** Claude Sonnet 5, fresh session, 2026-07-25.
**Scope reviewed:** `methodology.md`, `experiments/validate_h4_kurtosis.py`,
`experiment_results/kurtosis_results_2026-07-25.json`,
`prevalidation_plan.md`, `implementation_conformance.md`,
`dataset_manifest.json`, and the live `experiments_etf_universe.db`
(read-only). No file listed in the task was modified; nothing was
committed.

---

## (a) Independent re-derivation vs. reported figures

I wrote a standalone script (`sqlite3` directly against
`experiments_etf_universe.db` in read-only URI mode, hand-rolled excess
kurtosis / median / bootstrap — no import of anything from
`validate_h4_kurtosis.py`) that:

- pulls `close_amount` per ETF, ordered by `session_date`, for the same 25
  tickers;
- computes `r_t = ln(close_t/close_{t-1})`;
- computes `g2 = m4/m2^2 - 3` (plain Fisher excess kurtosis) per ETF, cross-
  checked against a second independent formula path using
  `statistics.fmean`/`statistics.pvariance` (agrees to ~1e-13, floating-
  point-noise level — confirms the formula, not just the code, is right);
- takes the cross-sectional median of the 25 point estimates;
- runs a 10,000-iteration i.i.d. bootstrap over the 25 point estimates,
  `random.Random(20260725)`, `rng.randrange(0, n)` per draw, same loop
  shape methodology.md Section 6 specifies, and takes the 2.5/97.5
  linear-interpolation percentiles.

**Result: exact match, to full float precision, on every reported number**
— all 25 per-ETF kurtosis values, all `n=2473`, the cross-sectional median
(9.995185801839456), and both bootstrap CI bounds (low
7.611023804796089, high 15.26846242545566). Nothing differed even at the
RNG-order-sensitivity level the task anticipated — my loop structure
(index-per-draw, iteration order = tuple order) happens to match
`_bootstrap_median_ci` exactly, so this is a genuine bit-for-bit
reproduction, not merely "close."

**Decision rule (methodology.md §7):** PASS iff CI lower bound > 0. My
re-derived lower bound is 7.611 > 0 → **PASS**, matching what the frozen
rule, applied mechanically to my own numbers, would render. No researcher
judgment was needed to reach that conclusion — the rule is unambiguous and
was applied correctly to the archived result.

I did not find a bug. The implementation matches the frozen methodology
and the reported output is genuinely reproducible from the archived
dataset snapshot and committed code alone (Standard §6 item 4).

## (b) 8-item Research Freeze Standard checklist (Standard §3)

Note up front: Standard §3's eight items were written with scoring/signal
research in mind (§3.4 "Benchmark," §3.6 "Scoring rules... weight,
lookback," §3.7 "Parameters... scoring rules depend on"). `reference_h4`
tests a distributional property, not a scoring signal, so several items
map onto methodology.md's sections rather than appearing as identically-
named headers. I checked substance, not header names.

1. **Universe** — Fixed completely: 25 named tickers, explicit list (§1).
   No gap.
2. **Dataset version** — Fixed completely: source, exact date range,
   per-table row counts and content hashes, snapshot files (§2). No gap.
3. **Evaluation period** — Not a separate section, but effectively fixed:
   §3 states "full available log-return series" and §2's date range
   (2016-09-13 to 2026-07-17) makes the period unambiguous and equal to
   the dataset version. This is an acceptable implicit fix, not a gap —
   there is no scenario where "full available history" leaves a choice
   open.
4. **Benchmark** — Not named as a "benchmark" section, but the Gaussian
   null (excess kurtosis = 0) is unambiguously encoded in the acceptance
   criterion (§7: "lower bound... strictly greater than 0"). Substance is
   fixed; only the Standard's generic vocabulary doesn't map 1:1 onto this
   hypothesis type. Minor documentation-structure note, not a governance
   gap.
5. **Metrics / Statistic** — Fixed completely and with the exact formula
   written out (§4), including an explicit, justified choice not to apply
   a small-sample bias correction. No gap.
6. **Scoring rules / Aggregation rule** — Fixed completely: median across
   25 ETFs (§5), with a stated rationale (robustness to one outlier ETF).
   No gap.
7. **Parameters** — Bootstrap seed (20260725) and iteration count
   (10,000) are both fixed and justified in §6 (exact reproducibility).
   No gap.
8. **Acceptance criteria** — Fixed completely and unambiguously in §7,
   including the specific INCONCLUSIVE resolution for the case the CI
   spans zero without clearing it on the low side. No gap.

**Verdict: methodology.md satisfies all eight items in substance.** The
only observation is cosmetic (§3's generic labels vs. this cycle's
distributional-property framing), not a hidden degree of freedom.

**Implementation vs. freeze — element-by-element drift check.** I read
`validate_h4_kurtosis.py` independently against methodology.md (not
against `implementation_conformance.md`'s own table, to avoid rubber-
stamping the author's self-review):

- Universe tuple: verbatim match, same order.
- Return definition: `_log_returns` uses `get_price_bars`'s
  `ORDER BY session_date` result directly, no reordering/filtering —
  matches §3.
- Statistic: `_sample_excess_kurtosis` is exactly `m4/m2^2 - 3`, no bias
  correction — matches §4, and matches my independently-written formula.
- Aggregation: `_median` over the 25 point estimates — matches §5.
- Significance procedure: `_bootstrap_median_ci` resamples the 25 point
  estimates (not the underlying return series — correctly a cross-
  sectional resample, not a time-series block bootstrap), seed 20260725,
  10,000 iterations, 2.5/97.5 linear-interpolation percentile — matches
  §6 exactly, including the specific interpolation convention.
- Acceptance criterion (§7): correctly *not* evaluated inside the script —
  left for the Decision phase, as the Standard's Phase 5/6/7 separation
  requires (Implementation must not embed the PASS/FAIL judgment).

**No drift found.** The one thing worth flagging for the eventual Decision
record: the acceptance-criterion application (my item (a) above) currently
exists only in this reviewer report and nowhere yet in the repo's Phase 7
artifacts, since `decision_log.md` and a decision record do not yet exist
in the archive as of this review. That's expected at this point in the
lifecycle (Phase 6 just completed per `transition_records.jsonl`), not a
defect.

## (c) Data-provenance caveat (`PriceBar.close` adjustment status)

The disclosure (prevalidation_plan.md §2, methodology.md §2) states
`PriceBar.close` is not confirmed split/dividend-adjusted and that this
could inflate measured kurtosis via corporate-action jumps. I checked this
two ways:

1. **Code inspection.** `core/market_data/providers/yahoo_finance.py`
   reads `quote["close"]` from Yahoo's `v8/finance/chart` endpoint and
   never requests or reads an `adjclose` field. This confirms the
   disclosure's factual premise: the ingestion code makes no adjustment
   decision at all, adjusted or not, so "not confirmed" is the accurate
   characterization (not an understatement).
2. **Empirical spot-check.** I scanned all 25 tickers' return series for
   single-day |log return| > 12%, and separately pulled `close_amount`
   around two specific known corporate actions in this universe: QQQ's
   3-for-1 split (ex-date 2024-03-18) and the Vanguard share-split batch
   that included VTI (~2021-10-12). **Neither shows any discontinuity** —
   QQQ's close is a smooth ~$433–446 through mid-March 2024 (no drop to
   the ~$146 a raw unadjusted post-split print would produce), and VTI
   shows normal single-digit-bp daily moves across its split window. Every
   |log return| > 12% event across all 25 tickers falls on 2020-03-09,
   -03-12, -03-13, -03-16, -03-18, -03-24, or two later dates
   (2022-11-10, 2025-04-09), and the large-move dates cluster tightly
   (12 of 25 tickers move >12% on 2020-03-16 alone) — consistent with
   genuine market-wide (COVID crash) or well-known sector events (e.g.
   XLE's 2020-03-09 oil-price-war crash, its 2020-11-09 vaccine-rally
   spike), not idiosyncratic single-ticker discontinuities.

**Assessment:** the disclosure is honest about what the code does not
confirm, but the empirical check suggests the *specific risk mechanism it
names (unadjusted splits)* likely does not materialize in this dataset —
Yahoo's `chart` "close" field appears to already be split-adjusted in
practice (consistent with Yahoo's typical behavior, where "close" is
split- but not dividend-adjusted, and "adjclose" additionally layers in
dividends). Dividend non-adjustment remains a real, unconfirmed, and
plausibly small residual effect (ex-dividend drops are on the order of a
few tenths of a percent to low single digits for these ETFs, well under my
12% scan threshold, so I cannot rule it out this way — a full check would
need a lower threshold or a comparison to a known adjusted series). **Net:
the disclosure is adequately flagged and not dishonest, but it is written
more cautiously than the split-jump evidence actually supports** — it
would be more precise to say the split-adjustment component of the risk
is empirically not observed in the checked cases, leaving only the
smaller dividend-adjustment component genuinely open.

## (d) Overall recommendation

The Validation-phase arithmetic is correct and independently reproducible
bit-for-bit; the frozen methodology was implemented without drift; the
frozen decision rule, applied to my own re-derived CI, yields PASS
(lower bound 7.611 > 0, decisively away from the 0 threshold — this is
not a near-miss requiring INCONCLUSIVE treatment). The Research Freeze
Standard's eight items are all substantively fixed with no hidden
researcher degree of freedom. The disclosed data-provenance caveat is
genuine and not overstated as a disclosure, though my spot-check suggests
its dominant named risk (split jumps) is not actually present in this
data; the residual (dividend adjustment) is smaller and still open.

**No blocking issue found.** This cycle's evidence supports proceeding to
a PASS Decision (Phase 7) at Level 2 review, with the standard's required
Level 3-unavailability disclosure carried into the decision record
(Standard §4: "Level 3 review not available; this Decision was made at
Level 2 only").
