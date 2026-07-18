# REFERENCE v1 Research Close-Out

This document closes the REFERENCE v1 research cycle. It does not modify
REFERENCE v1's implementation, propose retuning it, or propose
REFERENCE v2. Its purpose is governance: record what was found, freeze
what was tested, extract lessons, and define the entry bar for whatever
research cycle comes next. See `docs/BASELINE_STATUS.md`'s "Scoring
signal research" section for the first descriptive finding this
close-out builds on, and the two scripts named below for the full
implementation.

**Final research status: Implementation correct. Evidence insufficient
to validate REFERENCE v1 for promotion. REFERENCE v1 is not promoted,
not deleted, and not modified. It is frozen as a tested, documented,
inconclusive research artifact.**

## A. Research close-out report

### Original hypothesis

REFERENCE v1's ranking — `overall_score` as the unweighted mean of
MOMENTUM (SMA(20), unnormalized) and VALUE (RSI(14), bounded 0–100), no
cross-sectional normalization — carries predictive information about
subsequent ETF returns: ETFs ranked higher by `overall_score` on a
given date would show higher subsequent returns than ETFs ranked lower,
over a 20-trading-day horizon.

### Experiments performed

1. **`experiments/validate_scoring_signal.py`** (commit `cae13e7`) — a
   purely descriptive measurement: average forward return of the
   top-5-ranked ETFs minus the bottom-5-ranked ETFs, per ranking date,
   averaged across dates. No significance testing.
2. **`experiments/validate_reference_v1_significance.py`** (commit
   `19771d4`) — the full 5-phase statistical validation: descriptive
   stats; a unified permutation test (10,000 within-date shuffles per
   statistic, each of the five statistics tested against its own
   independent shuffle — MOMENTUM, VALUE, raw blend, normalized blend,
   and the top-vs-bottom spread never share a shuffle); block bootstrap
   (2,000 iterations per statistic at each of three block lengths — 20
   days primary, 40/40 and 60 days robustness-only); Holm-Bonferroni
   correction across the five simultaneous tests; a mechanical
   decision engine (`BUILD_V2_JUSTIFIED` only if MOMENTUM, VALUE, or the
   normalized blend passes both the corrected-significance test and
   bootstrap-robustness across all three block lengths).
3. **A code-only verification audit** of that implementation (no
   rerun) — confirmed the bootstrap and permutation machinery matched
   their documented design exactly, produced the full numeric 95% CI
   table below, and classified the result.

Both scripts ran against the same real data: 25 ETFs, 2024-07-17 to
2026-07-17, 463 observed ranking dates, 20-trading-day forward horizon,
via Yahoo Finance-sourced price history.

### Statistical results

| Statistic | Observed | Adjusted p (Holm-Bonferroni) | Significant? | Bootstrap-robust (20/40/60d all exclude 0)? | Passes |
|---|---|---|---|---|---|
| momentum_ic | 0.028817 | 0.005 | Yes | No | No |
| value_ic | 0.071280 | 0.000 | Yes | No | No |
| raw_blend_ic | 0.031967 | 0.0021 | Yes | No | No |
| normalized_blend_ic | 0.065012 | 0.000 | Yes | No (1 of 3 blocks only) | No |
| top_bottom_spread | 0.002311 | 0.0718 | No | No | No |

Four of five statistics were nominally significant under permutation
testing alone. None survived the more conservative bootstrap-robustness
requirement — `normalized_blend_ic` came closest, excluding zero at the
60-day block only (1 of 3 required). Full CIs and per-statistic detail
are in the verification-audit transcript and in
`reference_v1_significance_report.json` from the completed run (see
Section B — this file is currently a generated, gitignored artifact and
is the single most at-risk piece of evidence behind this report).

### Audit conclusions

The verification audit (code inspection only, no rerun) found **no
implementation error** in either script: block construction, statistic
recomputation per resample, percentile-based CI calculation,
per-statistic-independent permutation, and Holm-Bonferroni correction
all matched their documented design and were checked against the
literal source. The disagreement between "significant" permutation
results and "non-robust" bootstrap results was explained as an expected
consequence of financial time series' serial dependence — the
permutation null discards it, the block bootstrap preserves it — not as
evidence of a coding defect.

### Remaining limitations

- **Effective sample size**: 463 ranking dates with 20-trading-day
  overlapping forward windows reduce to roughly 23 effective
  independent windows — the actual binding constraint on what this
  data can resolve, independent of how many permutation or bootstrap
  iterations are run.
- **Single historical regime**: 2024-07-17 to 2026-07-17 only; no
  claim is made about any other period.
- **Survivorship bias**: the 25-ETF universe was selected from
  currently existing, currently liquid ETFs.
- **No transaction costs or implementation frictions modeled** at any
  point in either script.
- **No standardized effect size was computed by the script itself** —
  only observed value, null median, and their difference. A post-hoc
  standardized measure (observed value divided by an approximate
  bootstrap standard error) was computed by hand during the audit and
  found consistent with the CI table: no statistic's standardized
  effect reached the threshold a bootstrap-based 95% test would need.

### Distinguishing the three kinds of evidence

- **Evidence against the implementation**: none. Both scripts were
  read against their own documented design and found correct.
- **Evidence against the hypothesis** (i.e., a confident null result):
  weak, not present in a form that would justify "no signal." A
  confident null would show null-medians and observed values
  converging with tight, zero-centered bootstrap CIs. Instead, four of
  five statistics were directionally consistent with the hypothesis
  and nominally significant against a randomization null — the CIs
  were wide, not tightly centered on zero.
- **Insufficient statistical power**: this is the dominant and correct
  classification. The ~23-effective-independent-window ceiling is
  narrow enough that a real small effect and a zero effect that drew a
  somewhat-above-median sample are not currently distinguishable. More
  bootstrap iterations would not have changed this — it is bounded by
  the underlying data's independent information content, not by how
  many times that information is resampled.

## B. Frozen artifact inventory

To make REFERENCE v1 reproducible from this point forward, the
following need to be preserved. Nothing below has been deleted or
altered by this close-out.

**Source code (already in git history, reproducible from commit hash):**

- `experiments/daily_etf_universe_update.py` — defines `ETF_UNIVERSE`
  (the 25-ticker list), `CALENDAR_ID` ("XNYS"), and bootstraps the
  `ScoringProfile` row itself: `PROFILE_NAME, PROFILE_VERSION =
  "REFERENCE", 1`, with `parameters` binding MOMENTUM to SMA(20) and
  VALUE to RSI(14) — this is the literal, authoritative definition of
  what "REFERENCE v1" means (`daily_etf_universe_update.py:82`,
  `:171-185`).
- `experiments/backfill_price_history.py` — the price-history
  acquisition tool used to build the tested date range.
- `experiments/seed_trading_calendar.py` — the trading-calendar
  prerequisite.
- `experiments/validate_scoring_signal.py` — the descriptive spread
  measurement (`forward_return()`, `_resolve_close()` are reused
  directly by the significance script below).
- `experiments/validate_reference_v1_significance.py` — the full
  statistical validation pipeline.
- `core/analytics/domain/calculations.py`,
  `core/analytics/domain/score_calculation.py` — the SMA/RSI/blend
  arithmetic itself, frozen and unchanged since v0.4.0 per
  `docs/BASELINE_STATUS.md`.
- **Commit `19771d4`** is the exact state "REFERENCE v1 as tested" —
  every file above is present and unmodified at that commit.

**Documentation:**

- `docs/BASELINE_STATUS.md`'s "Scoring signal research" section (the
  descriptive finding).
- `experiments/README.md`'s `validate_reference_v1_significance.py`
  section (what the script does and how to rerun it).
- This document.

**Generated outputs (NOT in git, at real risk of being overwritten):**

- `reference_v1_significance_report.json` (repo root) — the exact
  machine-readable numeric results this report and the audit are based
  on. It is gitignored by design (every rerun regenerates it), which
  means **the specific evidence behind this close-out currently has no
  durable, version-controlled copy** — a future rerun (e.g. a
  REFERENCE v2 validation pass reusing the same script and default
  output path) would silently overwrite it.
- `experiments_etf_universe.db` (repo root, ~69 MB, gitignored) — the
  actual historical price/indicator/score data. This file is not
  practically or intentionally git-trackable, and is not the right
  reproducibility unit regardless: it will keep growing and mutating as
  future research reuses `daily_etf_universe_update.py`. What actually
  makes the result reproducible is not this specific file, but the
  combination of (the frozen `ETF_UNIVERSE` list, the exact date range
  2024-07-17 to 2026-07-17, the frozen scoring-profile definition, the
  frozen script versions at commit `19771d4`, and Yahoo Finance's
  historical data for that range) — rerunning the same scripts against
  a fresh database and the same parameters should reproduce
  statistically equivalent results, not a byte-identical database.
- The random seed (`20260718`) is already a version-controlled
  constant in `validate_reference_v1_significance.py`, so this part is
  already frozen.

**Recommended archive structure** (a recommendation only — not created
by this close-out, since freezing artifacts that live outside the
normal "regenerated, gitignored" convention is a deliberate choice for
the user to make, not an automatic one):

```
research_archive/
  reference_v1/
    reference_v1_significance_report_2026-07-18.json   # dated, frozen copy of the completed run's output
    COMMIT.txt                                          # "19771d4" -- the exact commit this result was produced against
    README.md                                           # one paragraph: what this is, links to this close-out doc
```

A `research_archive/` (or `docs/research/`) directory, tracked by git
(explicitly carved out of the "generated output, don't commit"
`.gitignore` convention since these are frozen point-in-time snapshots,
not regenerable working files), keeps each completed validation run's
actual evidence safe from being silently overwritten by a later run —
including a future REFERENCE v2 run using the same script and default
output path. The most urgent item in this list is the JSON report:
recommend copying it into such a location before any REFERENCE v2 work
begins, since it is the one piece of evidence with no current durable
copy.

## C. Lessons learned

**Software architecture lessons**

- Reuse-first discipline (never duplicating
  `generate_ranked_etf_report()`, `forward_return()`,
  `_resolve_close()`, `daily_etf_universe_update.run()`) let two
  successive statistical rewrites happen entirely inside
  `experiments/` without ever risking the shipped CLI or `core/`
  analytics engine's behavior — validated the "no `core/` changes
  needed" pattern held even for a fairly heavy statistics module.
- The Decimal-in-`core/`, float-at-the-statistics-boundary precision
  split is a reusable pattern worth naming explicitly for any future
  work that mixes exact domain arithmetic with large-scale numerical
  computation (millions of permutation/bootstrap operations).

**Data engineering lessons**

- A silent universe-filtering bug (`build_panel()` never actually
  applied its `universe` parameter to filter
  `generate_ranked_etf_report()`'s output) went undetected until a
  smaller "smoke test" run happened to produce output numerically
  identical to the full-universe run — the bug did not corrupt the
  real, intended full-universe analysis, but it did silently defeat
  the *purpose* of subset testing. Lesson: a subset/smoke test must be
  verified to actually diverge from the full run's output, not merely
  to run without crashing.
- Calendar-correctness guards (`is_trading_day()`) were added to
  `calculate_sma()`/`calculate_rsi()` and `calculate_drawdown()` in two
  separate commits (`cebd5b0`, `67d9e90`) after `calculate_score()`
  already had the same guard — an inconsistently applied fix across
  sibling functions is itself a latent bug source. A shared regression
  test asserting the guard exists on every indicator-calculation
  function (rather than relying on catching each one by observation)
  would have caught both gaps at once.
- A large generated artifact (`experiments_etf_universe.db`, gitignored,
  69 MB) sitting at the repo root with no archival copy is a single
  point of failure for reproducibility: nothing currently prevents a
  future, differently-scoped `daily_etf_universe_update.py` run from
  mutating the exact dataset a past frozen result depended on.

**Quantitative research lessons**

- A descriptive spread alone (+0.231%) was not evidence of anything —
  it took a full second research phase (permutation + bootstrap) to
  learn that most of that spread is statistically indistinguishable
  from a randomization null once serial dependence is accounted for.
- Testing each dimension separately (not only the blend) was
  necessary, not optional: it surfaced that MOMENTUM and VALUE
  individually had directionally consistent, nominally significant
  permutation results that a blend-only test would have partly masked
  or muddled.
- REFERENCE v1's unnormalized-MOMENTUM / bounded-VALUE scale mismatch
  was a real, previously confirmed architectural risk (scale
  dominance) — worth carrying forward as a hard design constraint for
  any future hypothesis: normalize each dimension's scale before
  combining, never after.

**Statistical validation lessons**

- Permutation significance alone is not a safe stopping point for
  autocorrelated financial time series — it will read as "significant"
  against a null that discards real serial dependence between
  adjacent, overlapping ranking dates.
- Testing five statistics simultaneously required family-wise error
  control (Holm-Bonferroni) as a load-bearing step, not a formality:
  four of five statistics were nominally significant at the same time,
  which is exactly the scenario multiple-comparisons correction exists
  to guard against.
- Effective independent sample size (materially smaller than raw
  observation count, due to overlapping forward-return windows) is the
  real ceiling on what conclusions are possible — no amount of
  additional permutation or bootstrap iterations can substitute for
  more genuinely independent history.
- "Implementation correct, evidence insufficient" needed to exist as
  its own outcome, distinct from "bug" and from "no effect." Collapsing
  it into either neighbor would have produced the wrong governance
  call: false confidence in a clean null, or wasted effort chasing a
  phantom implementation defect.

## D. REFERENCE v2 entry requirements

These are gate criteria only — no REFERENCE v2 hypothesis is proposed
or designed here. Any future reference implementation must satisfy all
of the following before implementation begins:

1. **Genuinely different hypothesis.** Not a reweighting, renormalization,
   or threshold adjustment of REFERENCE v1's same two factors (SMA/RSI
   variants). Must rest on an economically distinct factor class.
2. **A written economic rationale, documented before any code is
   written.** The reason the new hypothesis should carry signal must be
   stated in advance, not reverse-engineered from a result after the
   fact.
3. **No use of REFERENCE v1's results to select or tune v2's
   parameters.** No peeking at REFERENCE v1's per-ETF outputs, IC
   values, or errors to inform v2's design choices. This is the single
   requirement most directly aimed at preventing "rescue via retuning"
   — the failure mode this entire close-out was designed to close off.
4. **Compatibility with the existing validation pipeline as-is.** v2
   must be testable as a new score/profile plugged into the same
   tested machinery (daily cross-sectional IC, dimension-separated
   permutation, 20/40/60-day block bootstrap, Holm-Bonferroni
   correction) without modifying that pipeline's statistical
   methodology to be more favorable to v2's results.
5. **Predefined, written success criteria**, fixed before the first
   run — the exact promotion rule (Holm-Bonferroni significance *and*
   bootstrap-robustness across all block lengths) must not be adjusted
   after seeing results.
6. **An explicit, deliberate choice of dataset window** — either a
   distinct period from REFERENCE v1's 2024-2026 window, or an
   explicit, stated acknowledgment of reusing the same window and
   inheriting the same single-regime limitation. Never an implicit
   inheritance.
7. **A stated minimum effective-independent-sample-size target**,
   given the demonstrated ~20-day-horizon-driven autocorrelation
   problem — e.g., a minimum number of effective independent windows
   required before a bootstrap CI is treated as conclusive one way or
   the other.

## E. Repository roadmap

Recommendations for organizing the repository so future reference
implementations (v2, v3, …) can be compared against REFERENCE v1
objectively, using the same validation framework — none of this is
implemented by this close-out, per the existing project discipline of
not building generalized structure ahead of a second concrete need
(`docs/BASELINE_STATUS.md`'s "Abstraction discipline"):

- **Do not generalize `validate_reference_v1_significance.py` now.**
  Its statistic functions are currently coupled to REFERENCE v1's
  specific score keys (`"momentum"`, `"value"`, `"raw_blend"`,
  `"normalized_blend"`). The trigger for generalizing the panel /
  permutation / bootstrap machinery to accept an arbitrary named set of
  score keys and profile identifier is a second concrete hypothesis
  that actually needs to reuse it — not before. Note this here as the
  known trigger condition, consistent with how this project has always
  waited for a second concrete case before building an abstraction.
- **Create a git-tracked `research_archive/` (or `docs/research/`)
  directory** for dated, frozen result snapshots (JSON + short pointer
  doc) — see Section B. This is what actually enables objective
  comparison across profiles later: each profile's exact evidence,
  preserved at the commit it was produced against, rather than a
  single regenerable file at the repo root that only ever holds the
  most recent run.
- **When a second profile exists, add a profile identifier to the
  `decision` block** of the significance report's JSON output (it
  currently lives only in the `config` block) — so that multiple
  frozen snapshots in the archive above can't be confused with each
  other by a reader who only looks at the `decision` section.
- **Update `docs/BASELINE_STATUS.md`'s "Scoring signal research"
  section** in a future, explicitly requested edit to point at both
  the original descriptive finding and this close-out's audited
  significance result, so a future reader lands on the complete
  picture rather than only the earlier, weaker descriptive number.
  Not done as part of this close-out, since `BASELINE_STATUS.md`
  updates have consistently been their own explicitly requested task in
  this project's history.
