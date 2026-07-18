# REFERENCE Research Roadmap — Next Cycle Decision Memo

A review-only decision memo, not an implementation plan. It evaluates
the two completed research cycles —
[`docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md`](REFERENCE_V1_RESEARCH_CLOSEOUT.md)
and
[`docs/REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md`](REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md)
— asks whether a next hypothesis cycle is justified, and if so, ranks
the remaining candidates from the REFERENCE v2 research strategy
document (the 8-hypothesis evaluation that ranked H1 first and H3
second, prior to H1's own testing). No code is written, no experiment
is designed, and no implementation plan is proposed here.

**Recommendation: a next hypothesis cycle is justified, conditionally.**
Neither prior cycle disproved the platform's ability to detect a real
signal if one exists — both were constrained by the same effective
sample size ceiling, not by a confirmed absence of predictability.
Proceeding is conditional on the entry requirements in Section 4 and
the structural caveat in Section 6: unless historical depth is
increased, a third cycle will likely meet the identical power ceiling
regardless of which economic idea is chosen next.

## 1. What REFERENCE v1 established

**Validated signals:** none. No statistic (MOMENTUM IC, VALUE IC, raw
blend IC, normalized blend IC, top-vs-bottom spread) survived
Holm-Bonferroni-corrected permutation testing combined with bootstrap
robustness across all three block lengths. What *was* established with
confidence: the validation pipeline itself is correctly implemented
(independently audited, no defect found), 4 of 5 statistics were
directionally consistent with the hypothesis and permutation-significant
on their own, and the scale-dominance risk in the raw (unnormalized)
blend was a real, confirmed architectural concern — addressed by
percentile normalization, though even the normalized blend didn't clear
the bar either.

**Limitations:** effective sample size of roughly 23 independent
20-day windows behind 463 overlapping ranking dates — the binding
constraint on what the data could resolve, independent of permutation
or bootstrap iteration counts. Single historical regime (2024–2026).
Survivorship-biased 25-ETF universe. No transaction costs or
implementation frictions modeled anywhere in either script.

**What remains unexplained:**
- Whether the *same* MOMENTUM/VALUE hypothesis would resolve to a clear
  verdict given a genuinely larger effective sample (longer history, or
  a shorter/non-overlapping horizon) — never attempted, since REFERENCE
  v1's close-out explicitly ruled out a rerun without a concrete
  implementation error.
- Whether MOMENTUM and VALUE carry meaningfully different-strength
  effects individually, or whether the apparent difference in their
  bootstrap CI widths is a small-sample artifact.
- Whether RSI(14)'s conventional short-horizon (day-scale) character
  was mismatched against the 20-day forecast horizon it was tested at
  — no alternative horizon was ever tried.
- Whether the result is stable across a differently composed ETF
  universe.
- Whether nonlinear or regime-conditional relationships exist that a
  monotonic Spearman rank correlation cannot detect.
- No out-of-sample or walk-forward split was ever performed; the full
  window was treated as one evaluation, not a discovery/holdout split.

## 2. What REFERENCE v2 H1 established

**Hypothesis tested:** H1-A (primary) — ETFs ranked lower in 60-day
trailing realized volatility would show higher future *raw* returns.
H1-B (secondary diagnostic) — the same ranking would show higher future
*risk-adjusted* returns. Score: total realized volatility (a deliberate
proxy for diversified ETF instruments, distinct from idiosyncratic
volatility or beta as used in the source literature).

**Why archived:** neither statistic survived the same promotion bar
REFERENCE v1 was held to. Notably, this was a *different failure mode*
from REFERENCE v1's: both H1-A (IC −0.117225) and H1-B (IC −0.037941)
were permutation-significant, Holm-Bonferroni-corrected, and
*directionally opposite* to the hypothesis — lower realized volatility
was associated with *lower*, not higher, subsequent returns in this
sample. Neither statistic's bootstrap CI excluded zero at any block
length, so the reversed-direction point estimate could not be confirmed
as robust either.

**What was learned:**
- A second, independent confirmation that the validation pipeline
  (permutation testing, Holm-Bonferroni, block bootstrap) generalizes
  cleanly to an economically unrelated hypothesis without modification
  — reused unmodified by import, not by refactor.
- The effective-sample-size ceiling is a property of the *panel
  structure* (overlapping 20-day forward windows over a ~2-year window),
  not of any one specific hypothesis — it bound two mechanistically
  unrelated constructs (price-trend/oscillator in v1, volatility
  dispersion in H1) in essentially the same way.
- H1's result, unlike v1's, leans toward evidence *against* its
  hypothesized direction rather than merely "insufficient evidence" —
  though not confirmed by bootstrap robustness, so still short of a
  confident disproof.
- The experiments-only architecture decision (no `core/` change, no new
  `IndicatorDefinition`/`ScoringProfile`) held up for a second,
  differently-shaped hypothesis, reinforcing that this is the correct
  default posture for research cycles whose outcome is unknown in
  advance.
- A real process gap: H1's generated report was not gitignored at
  implementation time (since fixed) — a concrete reminder that each new
  script's output-path hygiene needs to be a checked step, not an
  assumed inheritance from the previous script's convention.

## 3. Is a next hypothesis cycle justified?

Yes, conditionally. Neither REFERENCE v1 nor H1 produced a confident
disproof of ETF-level predictability in general — REFERENCE v1's result
was "insufficient power," and H1's was "leans against, not confirmed."
Both cycles instead demonstrated that the validation infrastructure
itself is sound and reusable, which lowers the marginal cost of testing
a third, genuinely different hypothesis. There is no finding from either
cycle that argues the *research program* should stop — only that these
two specific, narrow implementations did not clear a deliberately
conservative bar.

The condition: both cycles hit the same binding constraint (~20–23
effective independent windows) for two unrelated reasons converging on
the same data structure. A third hypothesis tested against the identical
2024–2026 window and 20-day horizon should be expected, going in, to
face the same ceiling — see Section 6. Proceeding without acknowledging
this risks a third "insufficient evidence" result that teaches the
project little beyond what the first two already established.

## 4. Entry requirements for the next hypothesis

Carried forward from REFERENCE v1's own close-out (Section D, 7 items,
still fully binding) plus H1's own addition (its close-out, Section D).
The four requirements specifically named for this memo:

1. **Independent economic rationale.** A written mechanism, documented
   before any code is written, resting on established literature — not
   reverse-engineered from a result, and not selected because it
   "seems likely to pass" given what was learned from v1 or H1.
2. **Novelty versus existing factors — now checked against *two* priors,
   not one.** The candidate must be economically distinct from both
   REFERENCE v1's price-trend/oscillator construct (MOMENTUM/VALUE) and
   H1's volatility-dispersion construct. A hypothesis that is a
   disguised variant of either (e.g., a different momentum lookback, or
   a differently-windowed volatility measure) does not satisfy this.
3. **No parameter tuning of v1 (or H1).** Neither REFERENCE v1's nor
   H1's specific numeric results (ICs, p-values, CIs, or which
   direction they pointed) may be used to select, tune, or bias the
   next candidate's hypothesis, lookback window, outcome variable, or
   promotion criteria.
4. **Frozen specification before implementation.** The same discipline
   both prior cycles followed: exact factor definition, forecast
   horizon, GO checkpoint criteria, and promotion table fixed in
   writing, reviewed, and frozen before any code is written — no
   post-hoc adjustment after results are seen.

## 5. Ranked candidate directions

The 7 remaining candidates from the REFERENCE v2 research strategy
document (H1 now tested and closed), ranked by economic justification,
independence from v1/H1, data availability, and overfitting risk —
the four criteria specified for this memo, not the fuller 8-dimension
evaluation the original strategy document used.

| Rank | Candidate | Economic justification | Independence from v1/H1 | Data availability | Overfitting risk |
|---|---|---|---|---|---|
| 1 | **H3 — Relative strength / sector rotation** | High | High | Good — no new data source | Low–Medium |
| 2 | H2 — Long-term momentum (12-1 month) | High | Medium–Low (closest of all candidates to v1's own MOMENTUM) | Fair — needs deeper history than currently backfilled | Low |
| 3 | H6 — Long-horizon reversal (3–6 month) | High | High | Poor — as few as 4–8 non-overlapping windows in the current history | Low (in principle; practically undermined by sample size) |
| 4 | H5 — Carry / yield | High | High | Poor — genuine new data source required; universe fit unverified | Low |
| 5 | H4 — Volume / flow acceleration | Medium | High | Uncertain — volume data reliability unverified; ETF-level volume is contaminated by creation/redemption mechanics | Medium |
| 6 | H7 — Correlation-regime / idiosyncrasy | Medium–Low (no clear a priori direction) | High | Good | Medium–High (sign-selection risk without a clear a priori direction) |
| 7 | H8 — Macro-conditional beta exposure | High | Highest of all candidates | Poor — new external data source required | High (most researcher degrees of freedom; needs new statistical infrastructure beyond a simple score) |

**H3 is the recommended next candidate.** It is the only remaining
candidate that scores well on all four criteria simultaneously: strong,
independent economic rationale (sector/theme rotation via slow
institutional reallocation — a mechanism unrelated to either price
extrapolation or volatility mispricing); high novelty against both
priors (a *relative*-to-benchmark ranking methodology, not an absolute
price level or a dispersion measure); no new data acquisition (a
benchmark series is available from within the existing 25-ETF universe);
and low-to-medium overfitting risk (the only material design choice —
which ETF serves as the benchmark — must be fixed in advance, not
tuned). It is also arguably the best economic fit to this project's
specific universe composition (curated sector/theme/regional ETFs),
independent of and not because of either prior result.

## 6. Structural recommendation: historical depth

Both completed cycles were bound by the same effective-sample-size
ceiling (~20–23 independent windows from a ~2-year, 20-day-overlapping-
horizon panel), for two economically unrelated hypotheses. This is not
a property of what was tested — it is a property of *how much
independent history exists to test against*. Before, or in parallel
with, a third hypothesis cycle, the project should explicitly consider
whether extending the backfilled price history window (more calendar
time, not more permutation/bootstrap iterations) is warranted. This
does not block H3 specifically — H3's own data requirements are already
satisfied by the current window — but it is a standing, unresolved
question the research program has now encountered twice, and treating
it as a one-off footnote each time understates its significance.
Candidates with materially longer lookback requirements (H2, H6) are
specifically data-constrained by the current window's depth, not by
their own economic merit — extending history would directly improve
their feasibility, not just their odds of clearing the promotion bar.
