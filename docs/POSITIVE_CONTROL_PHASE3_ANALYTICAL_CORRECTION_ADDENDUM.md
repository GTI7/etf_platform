# Positive Control Study — Phase 3 Analytical Correction Addendum

## The Score-Side ACF Target Under Cross-Sectional Rank Transformation

**Status: theory-only derivation, produced by post-hoc analysis of already-archived
Phase 3 evidence. No code was written or modified to produce this document. No new
experiment was executed — every empirical number cited below is read from the
existing, already-committed-pending
[`generator_fidelity_results.json`](../research_archive/positive_control_phase3/generator_fidelity_results.json)
(R=25, anchor dimension point, `w=0`). This addendum does NOT claim Gate 2 passes,
does NOT reopen Phase 4, and does NOT itself constitute a Phase 3 decision-log entry
— see §9 for the explicit list of what this document does not claim.**

Companion documents: `docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md` (§1.2
generator, §1.3 proven/empirical split, §2/§2a fidelity gate), and
`research_archive/positive_control_phase3/pilot_results.md` /
`decision_log.md` (Entry 3: Gate 2 FAIL as originally measured against the naive
target this addendum corrects).

---

## 1. Why this addendum exists

V2 §1.3 (pre-correction) asserted that `score`, built as a rank-space blend of
`forward_return` and `sma`, "inherits" the same closed-form Bartlett(h) ACF that
governs the raw series. Entry 1 of the Phase 3 decision log already flagged this as
an unproven claim dressed in the certainty of a proven one; Entry 3's actual
execution confirmed the flag was justified — Gate 2 FAILs at 16 of 20 lags, with the
empirical score-side ACF running measurably *below* the naive Bartlett(h) target at
every short-to-medium lag.

The reason is structural, not incidental: `forward_return` and `sma` enter `score`
only through their **cross-sectional ranks**, `rank_average_ties`, recomputed
independently each day. Rank is a nonlinear, order-statistic transform. Linear
combination algebra (the basis of V2's original "inherits" claim) does not commute
with a nonlinear transform applied before the combination. What *does* commute, and
what this addendum derives from first principles, is a different, exact
relationship between the raw series' correlation structure and the correlation
structure of their ranks — the classical Pearson-to-grade-correlation identity for
jointly Gaussian variables. Applying it correctly produces a **new, closed-form
target** for Gate 2 that is provably distinct from — and, checked against the R=25
pilot data already on disk, measurably closer to — what the generator actually
produces.

## 2. Setup and notation

Per V2 §1.2 (unrestated in full; reproduced only as needed). Instrument `i`, day
index `t`. Daily latent return:

```
r[i][t] = sqrt(beta) * f[t] + sqrt(1 - beta) * eps[i][t]
```

`f[t]` i.i.d. N(0,1) (shared across instruments, drives cross-sectional correlation
`beta`), `eps[i][t]` i.i.d. N(0,1) (independent across `i` and `t`). For a reference
day `d`, with horizon/window length `h` (frozen `L_score = h`):

```
sma[i][d]           = (1/h) * sum_{t = d+1}^{d+h}     r[i][t]     -- trailing window, length h
forward_return[i][d] =        sum_{t = d+h+1}^{d+2h}  r[i][t]     -- forward window, length h
```

These windows are adjacent and disjoint by construction — the "proven" independence
property already established in V2 §1.2/§1.3. `score[i][d] = w * rank_d(forward_return)[i]
+ sqrt(1 - w^2) * rank_d(sma)[i]`, rank taken cross-sectionally over `i` at fixed `d`.

## 3. Lemma 1 — Cross-sectional ranking removes the common factor exactly

**Claim.** For any fixed day `d`, `rank_d(forward_return)[i] = rank_d(E_FR[i][d])`,
where `E_FR[i][d] = sum_{t=d+h+1}^{d+2h} eps[i][t]` is the purely idiosyncratic part
of `forward_return[i][d]`. The same holds for `sma`. This is **exact for every
finite N, not an approximation** — no Gaussianity, no large-N limit, no independence
assumption beyond `f[t]` being common across `i` at fixed `d` is required.

**Proof.** Write `forward_return[i][d] = c[d] + E_FR[i][d]`, where
`c[d] = sqrt(beta) * sum_{t=d+h+1}^{d+2h} f[t]` does not depend on `i` — it is
identical for every instrument on day `d`, since `f[t]` is the shared factor. Rank
is invariant under adding an identical constant to every element of the set being
ranked: for any set `{x_i} = {c + y_i}`, the ordering of `{x_i}` equals the ordering
of `{y_i}`, for any real `c` and any distribution of `{y_i}`, at any N ≥ 1. Hence
`rank_d(forward_return)[i] = rank_d(c[d] + E_FR[i][d])[i] = rank_d(E_FR[i][d])[i]`.
∎ (Identical argument for `sma`, replacing `E_FR` with the analogous idiosyncratic
sum over its own window and noting the `1/h` normalization is a positive scalar,
which also does not affect rank.)

**Why this matters.** `beta` is completely absent from the derivation. Cross-sectional
ranking is not an approximate or `beta`-dependent denoising step — it is an *exact*
projection onto the idiosyncratic subspace, for any `beta` and any N. This is the
correct, provable content behind the intuition "ranking removes the common factor."
It is also the necessary lemma for §4: it establishes that the object actually being
ranked each day is a set of `i.i.d.`-across-`i` idiosyncratic Gaussians, which is the
precondition the classical grade-correlation identity requires.

## 4. The Pearson-to-Spearman (grade correlation) transformation

For a bivariate standard normal pair `(X, Y)` with correlation `rho`, define the
**grade correlation** as the correlation of their probability-integral transforms,
`Corr(Phi(X), Phi(Y))`, where `Phi` is the standard normal CDF. This is the N -> infinity
limit of the sample Spearman rank correlation computed on N i.i.d. draws of `(X,Y)`.
The closed-form population identity (Sheppard's formula, 1899; equivalently derivable
from the bivariate normal density in polar/Mehler expansion form) is:

```
rho_grade = (6 / pi) * arcsin(rho / 2)
```

Two properties used below: (a) it is odd and monotone increasing in `rho`, fixed at
0 and at the endpoints `rho = +-1 -> rho_grade = +-1`; (b) it is **strictly closer to
zero than `rho` itself** for every `rho` in `(-1, 1)` except the endpoints and zero —
i.e., grade correlation always attenuates the raw correlation. This attenuation is
the entire content of Gate 2's failure: the naive target (raw Bartlett(k)) is
systematically too high, because it never applies this attenuation.

**Caveat carried into §8/§10 below.** This identity is exact for the *population*
grade correlation (N -> infinity in the cross-section). `rank_average_ties` computes
a *finite*-N (N=25 here) empirical rank each day. The sample statistic converges to
`rho_grade` as N -> infinity but carries an O(1/N)-type finite-sample bias at finite
N whose exact form for *this* estimator (see §7's caveat) is not read off a textbook
result. This is the seed of §9's finite-N residual discussion — flagged here, not
resolved here.

## 5. The own-series idiosyncratic correlation kernel is exactly Bartlett(k)

Both `forward_return` and `sma` are length-`h` sums (or averages) of i.i.d. terms.
For `E_FR[i][d] = sum_{t=d+h+1}^{d+2h} eps[i][t]`, the two windows for lags `d` and
`d+k` (0 < k < h) overlap in exactly `h - k` terms, giving:

```
Cov(E_FR[i][d], E_FR[i][d+k]) = (h - k),   Var(E_FR[i][d]) = h
Corr(E_FR[i][d], E_FR[i][d+k]) = (h - k) / h = max(0, 1 - k/h) = Bartlett(k)
```

The identical argument applies to `sma`'s idiosyncratic part (the `1/h` scalar
cancels in the correlation). **Both idiosyncratic kernels are exactly Bartlett(k),
independent of `beta`** — a short side-computation (mixing two processes with
identical temporal kernels but different cross-sectional correlation, `f` at `rho=1`
across `i` and `eps` at `rho=0` across `i`, preserves the temporal kernel regardless
of the mixing weight `beta`) shows this is also exactly the kernel of the *raw*,
un-ranked series — which is precisely why Gate 1 (raw `forward_return` ACF) passes
against the naive Bartlett(k) target with sub-0.02 deviations throughout. Gate 1's
target was never wrong; only Gate 2's was, because Gate 2 additionally passed the
series through a nonlinear rank transform that Gate 1 does not apply.

## 6. Corrected score-side ACF target — pure single-series case

Applying §4's identity to §5's kernel gives the corrected target for the pure case
(`w = 0` or `w = 1`, where `score` equals `rank_d(sma)` or `rank_d(forward_return)`
exactly):

```
G(k) = (6 / pi) * arcsin( Bartlett(k) / 2 ),   Bartlett(k) = max(0, 1 - k/h)
```

This is the theory-based replacement for V2 §1.3's naive "inherits Bartlett(h)"
claim, restricted to the pure case. §8 generalizes it to arbitrary `w`.

## 7. Forward_return / sma cross-lag covariance functions

Needed for the general `w`-blend (§8): the correlation of `forward_return` at day
`d` against `sma` at day `d+k`, and the reverse. Both windows have length `h`;
`forward_return[d]`'s window starts at `d+h+1`, `sma[e]`'s window starts at `e+1`.
Two length-`h` windows starting at positions `p, q` overlap in `max(0, h - |p-q|)`
terms. Applying this with `(p,q) = (d+h+1, d+k+1)`:

```
overlap(k) = max(0, h - |k - h|)      for forward_return[d] vs. sma[d+k]
```

giving, after the same variance normalization as §5 (and the same `beta`-cancellation
argument, which holds identically here since it depends only on both processes
sharing a temporal kernel, not on which pair of series is being compared):

```
CrossCorr(k) = Corr(forward_return[d], sma[d+k]) = overlap(k) / h
             = max(0, 1 - |k - h| / h),   supported on k in (0, 2h)
```

This is a triangle centered at `k = h`, reaching exactly 1 there — at `k = h`,
`sma[d+h]`'s trailing window is *literally* `forward_return[d]`'s forward window
(same h returns, sum vs. mean of the identical set), so perfect correlation is
mechanical, not approximate. This is a genuine structural feature of the generator
worth naming explicitly, since it is easy to mistake for a bug: `forward_return` at
one date and `sma` roughly `h` days later are highly correlated *by construction*.

**The reverse direction is exactly zero for k >= 0.** By the same window-start
argument applied to `sma[d]` (window start `d+1`) against `forward_return[d+k]`
(window start `d+k+h+1`): `overlap(k) = max(0, h - |k+h|) = 0` for all `k >= 0`,
since `|k+h| >= h` whenever `k >= 0`. This recovers the k=0 disjoint-window
independence property already established in V2 §1.2 as the `k=0` special case of a
more general fact: `sma` never correlates with a *later* `forward_return` at all,
at any non-negative lag — only the reverse direction (`forward_return` leading `sma`)
carries the triangular cross-correlation above.

## 8. The general w-blend formula

`score[i][d] = w * R_FR[i][d] + sqrt(1-w^2) * R_SMA[i][d]`, where `R_FR = rank_d(forward_return)`,
`R_SMA = rank_d(sma)` (by Lemma 1, functions of the idiosyncratic parts only). Both
have identical marginal distribution (same N, same rank-average-ties convention), so
their variances are equal and the standard bivariate-combination correlation formula
applies directly to the two unit-normalized grade series:

```
Corr(score[d], score[d+k])
  = w^2 * Corr(R_FR[d],R_FR[d+k]) + (1-w^2) * Corr(R_SMA[d],R_SMA[d+k])
    + w*sqrt(1-w^2) * [ Corr(R_FR[d],R_SMA[d+k]) + Corr(R_SMA[d],R_FR[d+k]) ]
```

By §6, the first two (own-series) terms are both `G(k)` (§5 showed the two raw
kernels are identical, so their grade-transformed versions are too), so
`w^2*G(k) + (1-w^2)*G(k) = G(k)` regardless of `w`. By §7, for `k >= 0` the second
cross term (`R_SMA[d]` vs. `R_FR[d+k]`) is identically zero, leaving only the
`R_FR[d]` vs. `R_SMA[d+k]` cross term, grade-transformed:

```
Gx(k) = (6/pi) * arcsin( CrossCorr(k) / 2 ),   CrossCorr(k) = max(0, 1 - |k-h|/h)

ACF_score(k; w) = G(k)  +  w * sqrt(1 - w^2) * Gx(k)          for k >= 0
```

**Sanity checks.** `w=0` and `w=1` both collapse the second term to zero
(`sqrt(1-0^2)=1` but coefficient `w=0`; `sqrt(1-1^2)=0`), so both pure cases give
exactly `G(k)` — consistent with §5/§6's finding that `forward_return` and `sma`
share the same idiosyncratic kernel. The cross term is maximized at `w = 1/sqrt(2)`
(the blend weight that maximizes `w*sqrt(1-w^2)`) and is always non-negative
(`Gx(k) >= 0` since `CrossCorr(k) >= 0`), so the formula makes a falsifiable,
directional prediction distinguishing it from a naive guess: **for `0 < w < 1`, the
score's ACF should sit slightly *above* the pure-case `G(k)` curve at lags near
`k = h`, and coincide with `G(k)` at `w in {0,1}`.** This prediction is not yet
tested against any executed pilot data — see §10 item 2.

## 9. Numerical comparison against the already-archived R=25 pilot (w=0 case)

The fidelity gate as executed used `w=0`, i.e., `score = rank_d(sma)` exactly, so
§8's formula reduces to the pure case `G(k)` from §6. Comparing `G(k)` against the
naive Bartlett(k) target and the empirical mean ACF already recorded in
`generator_fidelity_results.json` (same R=25, same seeds, no rerun):

| k | Bartlett(k) (naive) | G(k) (corrected) | empirical mean ACF | tol95 | dev. vs. naive | dev. vs. corrected | passes corrected? |
|---|---|---|---|---|---|---|---|
| 1 | 0.9500 | 0.9453 | 0.9283 | 0.0013 | -0.0217 | -0.0171 | No |
| 2 | 0.9000 | 0.8915 | 0.8712 | 0.0023 | -0.0288 | -0.0202 | No |
| 3 | 0.8500 | 0.8384 | 0.8164 | 0.0031 | -0.0336 | -0.0220 | No |
| 4 | 0.8000 | 0.7859 | 0.7638 | 0.0039 | -0.0362 | -0.0221 | No |
| 5 | 0.7500 | 0.7341 | 0.7123 | 0.0044 | -0.0377 | -0.0219 | No |
| 6 | 0.7000 | 0.6829 | 0.6616 | 0.0050 | -0.0384 | -0.0213 | No |
| 7 | 0.6500 | 0.6322 | 0.6122 | 0.0054 | -0.0378 | -0.0200 | No |
| 8 | 0.6000 | 0.5819 | 0.5635 | 0.0059 | -0.0365 | -0.0184 | No |
| 9 | 0.5500 | 0.5321 | 0.5152 | 0.0066 | -0.0348 | -0.0169 | No |
| 10 | 0.5000 | 0.4826 | 0.4677 | 0.0074 | -0.0323 | -0.0149 | No |
| 11 | 0.4500 | 0.4334 | 0.4208 | 0.0081 | -0.0292 | -0.0126 | No |
| 12 | 0.4000 | 0.3846 | 0.3742 | 0.0088 | -0.0258 | -0.0104 | No |
| 13 | 0.3500 | 0.3360 | 0.3280 | 0.0093 | -0.0220 | -0.0080 | **Yes** |
| 14 | 0.3000 | 0.2876 | 0.2818 | 0.0097 | -0.0182 | -0.0058 | **Yes** |
| 15 | 0.2500 | 0.2394 | 0.2352 | 0.0101 | -0.0148 | -0.0042 | **Yes** |
| 16 | 0.2000 | 0.1913 | 0.1890 | 0.0106 | -0.0110 | -0.0023 | **Yes** |
| 17 | 0.1500 | 0.1434 | 0.1434 | 0.0111 | -0.0066 | -0.0000 | **Yes** |
| 18 | 0.1000 | 0.0955 | 0.0970 | 0.0114 | -0.0030 | +0.0015 | **Yes** |
| 19 | 0.0500 | 0.0478 | 0.0510 | 0.0120 | +0.0010 | +0.0033 | **Yes** |
| 20 | 0.0000 | 0.0000 | 0.0049 | 0.0125 | +0.0049 | +0.0049 | **Yes** |

**Reading this honestly, per the task's instruction not to overclaim.** Under the
corrected target, 8 of 20 lags (13–20) now pass at the same R=25 tolerance that
failed 18 of 20 lags under the naive target — a real, substantial improvement, and
directionally exactly as predicted (§4 property (b): grade correlation always
attenuates raw correlation, and the empirical data sits below the raw target
precisely where the attenuation should put it). **It does not make Gate 2 pass
overall.** Lags 1–12 still fail, with a residual deviation that is itself smooth,
one-directional (always negative), and roughly unimodal — largest (~-0.022) around
`k=4-6`, shrinking toward zero at both `k->0` and `k->h`. This shape (smooth,
one-directional, not lag-to-lag erratic) is the signature of a genuine structured
bias, not of Monte Carlo noise at R=25 — noise of that kind would not produce 12
consecutive lags moving the same direction with a smooth envelope. The leading
candidate explanation is the finite-N=25 gap flagged in §4's caveat: §4's identity
is an N -> infinity population statement, and `rank_average_ties` at N=25 per day is
a long way from that limit. §10 proposes how to test this directly rather than
assert it.

## 10. Ancillary result: Gate 3's true decay-to-zero cutoff is `2h`, not `h`

Out of primary scope for this addendum (which is about Gate 2/the score ACF), but
derived along the way and worth recording rather than discarding. Gate 3 checks that
the daily-IC series decays to (statistically indistinguishable from) zero by lag
`h=20`. IC(d) is a function only of `{score[i][d], forward_return[i][d] : i}`, which
by §2/§7 depends on `r[i][t]` for `t` in `[d+1, d+2h]` only — a span of `2h`, not
`h`. IC(d) and IC(d+k) are computed from **disjoint** underlying `r[i][t]` values,
hence are **exactly, provably independent** (not merely uncorrelated-in-the-limit)
whenever `k >= 2h`. For `h=20` this means the provable zero-cutoff is `k=40`, not
`k=20` — the Phase 3 pilot's own gate target (`k >= h`) is checking a *sufficient*
region too early by construction; correlation is expected, not a defect, throughout
`20 <= k < 40`.

This reframes the observed lags 44–51 failure: those lags are *past* the provable
`k=40` cutoff, where the true population ACF is exactly zero by the disjoint-support
argument, not merely close to it. Any nonzero measurement there is estimation noise
by construction — and the `stdev_acf` column at those lags (~0.12–0.13, roughly
5–20x the size of Gate 1/2's per-lag stdevs) confirms R=25 is a genuinely noisy
estimator in that regime, and the same 25 replications are reused across all 60
lags, so nearby lags' sampling errors are highly serially correlated — a multi-lag
"run" of simultaneous excursions (like 44–51) is the expected behavior of correlated
resampling noise, not evidence of a real generator defect. This is a plausible,
not yet confirmed, resolution of Entry 3's open Gate 3 question; formalizing a
corrected Gate 3 target (analogous to `G(k)` here, but for the IC series rather than
`score` itself, which V2 already flags as having "no closed form" for good reason —
IC is itself a ratio/correlation statistic, so its own autocorrelation is a
fourth-cumulant-type object, not a simple grade transform) is explicitly **not**
attempted here and is out of this addendum's bounded scope. Recommended, if pursued,
as a separate, later addendum — not folded into the Gate 2 correction this document
makes.

## 11. Finite-N residual — candidate sources, not yet distinguished

Four distinct effects could plausibly contribute to §9's residual (lags 1–12 still
failing under the corrected target); this addendum does not adjudicate between them:

1. **Finite cross-sectional N in the grade-correlation identity itself (leading
   candidate).** §4's `(6/pi)arcsin(rho/2)` is the N -> infinity population identity.
   `rank_average_ties` at N=25 is a finite-sample estimator of the corresponding
   quantity; a first-order `O(1/N)`-type bias is expected in general for
   rank-based estimators relative to their population limit, but the *specific*
   estimator used here — a same-instrument, cross-day autocorrelation of a daily
   cross-sectional rank, pooled over `T=463` days and `R=25` replications — is not
   the textbook i.i.d.-pairs Spearman-rho setting that most published finite-sample
   bias formulas assume. No existing closed-form correction is asserted; §12 item 1
   proposes measuring it directly.
2. **R=25 Monte Carlo noise on the empirical side of the comparison.** Gate 2's own
   `se_mean` column (§9 table, `tol95` column) is already accounted for in the
   pass/fail test; residual bias beyond that band, if real, is a *mean* bias, not a
   noise band issue — but this should be ruled in/out by increasing R, not assumed.
3. **Tie-handling in `rank_average_ties`.** With continuous Gaussian inputs, exact
   ties have probability zero in principle but finite floating-point precision could
   in rare cases produce them; this is very unlikely to be the dominant effect at
   the observed magnitude (~0.02) but is cheap to rule out.
4. **A genuinely missing second-order term in the analytical derivation** (e.g., an
   interaction between the finite-N grade transform and the specific pooling scheme
   `pooled_acf` uses — same-instrument-across-days, not cross-instrument-pairs).
   Distinguishing this from (1) requires the N-sweep in §12 item 1: if the residual
   shrinks toward zero as N grows with everything else fixed, (1) is confirmed as
   sufficient; if a nonzero residual survives as N -> large, a genuine second-order
   term (4) is implicated and would require new derivation, not just more data.

## 12. Bounded Phase 3 research plan

Scoped deliberately narrow, each step with an explicit stop condition, per this
platform's existing discipline of not letting a correction cycle become an
open-ended search:

1. **Add `G(k)` (§6) as an alternative `target_fn` in the fidelity-gate script,
   change nothing else** (same R=25, same tolerance procedure, same seeds), and
   record whether Gate 2 passes under it at the anchor point. This is the direct,
   already-partially-answered-by-§9 test — formalizing it as an actual gate rerun
   (not a post-hoc table) is the first concrete step, and the honest expected
   outcome, per §9, is **still FAIL** (lags 1–12) unless the finite-N effect closes
   the remaining gap, which is not yet known.
2. **Test the general `w`-blend prediction (§8)** by rerunning the fidelity gate's
   Gate-2-style ACF check at 2–3 additional `w` values already in this pilot's
   existing grid (e.g. `w=0.3, 0.5, 0.7`, reusing `rho_calibration.csv`'s existing
   seeds/dimension-point convention where possible) and checking whether the
   observed ACF sits above the pure `G(k)` curve by approximately
   `w*sqrt(1-w^2)*Gx(k)`, as §8 predicts. This is the only proposed test of the
   cross-term half of the formula — §9 only validates the `w=0` pure case.
3. **If step 1 still fails after the corrected target, run one isolated N-sensitivity
   diagnostic**: same `h=20`, `beta=0.30`, small fixed R (no need for R=25 at each
   point — this is a diagnostic, not a fidelity determination), sweeping
   `N in {25, 50, 100, 400}`, to check whether the residual from §9/§11 item 1
   shrinks toward zero. This directly adjudicates §11 items 1 vs. 4.
4. **Explicit scope boundary, stated up front so it cannot silently expand:** no
   change to `beta`, `h`, or the rank-average-tie convention; no generator redesign;
   no increase in R beyond what step 3's diagnostic needs; no attempt at a Gate 3
   correction (§10 is a separate, later addendum if pursued at all). If steps 1–3
   do not produce a passing Gate 2, the correct next governance action is to log
   that outcome and treat "generator redesign" as a new, separately-scoped
   construction attempt — not to keep adjusting this derivation to fit the data.
5. **Log the outcome, whichever it is, as a new decision-log entry** (Entry 5 or
   later, this addendum does not itself append one) referencing this document's
   commit hash once it exists — per the same "a document's own prose claim to be
   frozen is not freeze evidence" discipline already established for H3 and this
   study's own Entry 1–4 record.

## 13. What this addendum does NOT claim

- Does **not** claim Gate 2 passes. Under the corrected target, using data already
  on disk, 8 of 20 lags pass; 12 do not. The overall gate result, if rerun today
  with `target_fn = G(k)`, would still read **FAIL**.
- Does **not** modify `experiments/positive_control_phase3_pilot.py` or any other
  code. Every number in §9 is a closed-form evaluation of §6's formula against
  already-recorded JSON output; nothing was re-executed.
- Does **not** validate §8's general `w`-blend formula against any data — the
  existing pilot only ran the fidelity gate at `w=0`, where the cross term is
  identically zero and cannot be tested. §8 is a derivation, not yet a measurement.
- Does **not** resolve Gate 3. §10 is offered as a plausible, structurally
  motivated explanation for the lags 44–51 anomaly, explicitly flagged as
  unconfirmed and out of scope for this document's bounded plan.
- Does **not** reopen or advance Phase 4 (Methodology Freeze). No `methodology.md`
  exists; this addendum, even if fully validated by §12, would only make Gate 2 a
  better-grounded theory-based gate — it does not by itself satisfy every remaining
  Phase 3 blocker already listed in `pilot_results.md` §7 (horizon-sweep spot
  checks, full-scale calibration, isotonic fit, Level 2 review).
- Does **not** constitute a decision-log entry. If this derivation is adopted, the
  execution in §12 step 1 is what should be logged, with this document cited as its
  theoretical basis.

## 14. Governance status

**Phase 3 Pre-validation — analytical correction derived and partially checked
against already-archived evidence; not executed as a new gate run; not reviewed at
Level 2; Gate 2's status remains FAIL as recorded in `decision_log.md` Entry 3 until
§12 step 1 is actually run and separately logged.** This document proposes a
theory-based replacement for Gate 2's target function that is closer to the
generator's actual behavior than the naive target it replaces, demonstrably so on
existing data, but explicitly insufficient by itself to flip Gate 2 to PASS. Whether
Gate 2 can be preserved as a fully theory-based gate — the goal stated at the top of
this task — depends on §12's N-sensitivity diagnostic distinguishing a closable
finite-N estimator bias from a genuinely missing second-order term; that
determination has not yet been made.
