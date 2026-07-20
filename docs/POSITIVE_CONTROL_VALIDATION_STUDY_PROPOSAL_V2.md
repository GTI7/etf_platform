# Positive Control Validation Study — Research Proposal v2

**Status: Methodology Freeze Resolution document, produced in response
to a Governance Level 2 validation review's outcome of CONDITIONS
IDENTIFIED on
[`docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL.md`](POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL.md)
("v1"). Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4, a Level 2 review
is procedurally independent (a fresh session, no conversational
continuity to v1's authoring) but is explicitly **not** organizationally
independent — no externally accountable, differently-incentivized
reviewer exists on this platform, and no document in this study may
describe a Level 2 review as unqualified "independent." No code has
been written. This document supersedes v1 wherever the two disagree; it
does not edit v1 in place, per the archive/supersession discipline
`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 5 already establishes for
every other document family on this platform. v1 remains the historical
record of what that review examined.**

**Status update (this revision): a second Governance Level 2 review —
of this document (v2) itself — returned NOT READY FOR FREEZE.** Three
defects were identified: unsupported "independent committee" language
(corrected throughout this document by this revision); §1.3's
conflation of proven and empirical claims (corrected below); and a
Recommendation (§16) declaring readiness while this document's own
§1.6 disclosed an unexecuted required Pre-validation step. §16 is
corrected accordingly. This document is **Phase 3 Pre-validation
Evidence, not a Methodology Freeze** — every frozen-looking value below
remains a proposed value, not yet effective under
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §3 (freeze requires a committed
`methodology.md` and a `decision_log.md` entry recording its commit
hash; neither exists). See
[`research_archive/positive_control_phase3/`](../research_archive/positive_control_phase3/)
for the first actual Phase 3 pilot execution this revision responds to.

**Constraints unchanged from v1:** `core/statistics/significance.py`
is frozen and imported unmodified; `docs/RESEARCH_GOVERNANCE_STANDARD.md`
is authoritative; this study validates the pipeline, it does not modify
it; no real outcome data (forward-return-vs-score alignment used for
hypothesis testing) is touched before Phase 6.

---

## 0. Provenance and resolution map

The Level 2 validation review's CONDITIONS IDENTIFIED outcome named
five conditions and a standing instruction to search for hidden
assumptions, researcher degrees of freedom, undocumented statistical
choices, information leakage, reproducibility weaknesses, governance
ambiguity, and maintenance risk. Every item below is resolved
completely in this document — none is deferred to Phase 4 as "TBD."
(A second Level 2 review of this document's own resolutions, in turn,
found the three defects corrected throughout this revision — see the
Status update above and §16.)

| # | Review condition | Resolved in |
|---|---|---|
| 1 | Redesign the generator-fidelity gate to validate the daily IC-series dependence structure, both score-side and return-side | §1 (model redesign), §2 (fidelity gate v2) |
| 2 | Remove the underdetermined calibration problem (minimal-assumption model or sufficient archived statistics) | §1, §3 |
| 3 | Document archived effect sizes as historical estimates, not validated signal magnitudes | §4 |
| 4 | Freeze the exact MDE estimation procedure (interpolation, model selection, uncertainty, CIs) | §5 |
| 5 | Eliminate every adaptive-replication researcher degree of freedom | §6 |
| — | Additional: hidden assumptions, DOF, leakage, reproducibility, governance ambiguity, maintenance risk | §7–§12 |

Everything in v1 not revised below (Sections 3, 4, 5.4's dimension
list, 7.1, 7.2 gates 2–4, 7.3, 8, 9, 10, 11, 12 of v1) is **carried
forward unchanged** and is not repeated in full here except where a
revision in this document requires restating it for consistency
(marked explicitly).

---

## 1. Redesigned generative model (resolves Conditions 1 and 2)

### 1.1 Why v1's Type A generator is being replaced, not patched

v1 Section 5.2's Type A constructed `score` as "forward return's rank,
corrupted by calibrated noise." This gives exact control over the
injected population correlation, but it has a structural gap the
the Level 2 review's Condition 1 exposes: **the synthetic score carries no
autocorrelation structure of its own.** Real scores (SMA(20), RSI(14))
are themselves moving-window functions of price history and therefore
autocorrelated day-to-day, exactly like the forward-return series is.
The daily IC series the pipeline's block bootstrap actually resamples
is a cross-sectional correlation of *two* autocorrelated series, not
one — and v1's generator-fidelity gate (v1 Section 7.2, item 1) checked
only the return side's effective-window count, leaving the score side
entirely unvalidated. This is precisely the gap Condition 1 names.

Patching v1's gate to also check score-side autocorrelation would not
be sufficient, because v1's generator has no mechanism that gives the
score any deliberate autocorrelation to check — a patched gate would
either measure zero (wrong) or measure whatever incidental
autocorrelation falls out of the noise-injection step (uncontrolled,
unfrozen). The generator itself must change.

### 1.2 The unified latent-path construction

One stochastic primitive drives everything for a given synthetic
instrument `i` and trading day `t` — a single daily latent return
`r_{i,t}`:

```
f_t        ~ i.i.d. N(0, 1)              one shared series, all instruments, day t
ε_{i,t}    ~ i.i.d. N(0, 1)              independent across i and t
r_{i,t}    = sqrt(β)·f_t + sqrt(1-β)·ε_{i,t}
```

`β ∈ [0, 1]` is the cross-sectional correlation strength: for `i ≠ j`,
`corr(r_{i,t}, r_{j,t}) = β`, same day. `r_{i,t}` has **zero
autocorrelation across days by construction** — this is a deliberate,
disclosed, minimal assumption, justified in §1.4.

**Return-side series** — computed exactly as the real pipeline
computes it, by overlapping summation, not as an independent draw per
period (carrying forward v1 Section 5.1's central design requirement
unchanged):

```
forward_return_{i,t} = Σ_{k=1}^{h} r_{i,t+k}          h = forecast horizon (20 at anchor)
```

**Score-side series** — a trailing simple moving average of the same
latent path, of order `L_score`, frozen to `L_score = h` (§1.5):

```
sma_{i,t} = (1/L_score) · Σ_{k=0}^{L_score-1} r_{i,t-k}
```

Because `sma_{i,t}` depends only on `r_{i,t-L_score+1 .. t}` and
`forward_return_{i,t}` depends only on `r_{i,t+1 .. t+h}` — disjoint
time indices, and `r` has no autocorrelation — `sma_{i,t}` and
`forward_return_{i,t}` are **independent under construction**. This is
what makes `ρ_true = 0` (the Type I check) fall out mechanically rather
than needing to be separately arranged.

**Injecting the target effect size.** To make `score` carry a genuine,
dial-able population Spearman correlation `ρ_true` with
`forward_return`, `score` is a weighted rank-space blend of
`forward_return` itself (the only true carrier of signal about
`forward_return`, by definition) and `sma` (which supplies realistic,
independent, autocorrelated "indicator-like" noise):

```
score_{i,t} = w · rank(forward_return_{i,t}) + sqrt(1 - w²) · rank(sma_{i,t})
```

`w ∈ [0, 1]` is solved, per target `ρ_true`, by a frozen deterministic
procedure (§1.6). Because `sma` is independent of `forward_return`, the
`sma` term contributes realistic score-side autocorrelation without
diluting or inflating the calibrated relationship between `w` and
`ρ_true` in expectation — the two goals (exact effect-size control,
realistic score autocorrelation) do not trade off against each other.

### 1.3 Why this resolves the calibration problem, not just the gate — and what is proven versus what is empirical

**This section previously stated a claim about `score`'s autocorrelation
with more certainty than the construction actually supports. This
revision corrects that, in response to a Governance Level 2 review
finding (Status update, top of document). The correction does not
change the generator model in §1.2 — it changes what this document
claims is true about it, and moves the unproven part into the gate
that is designed to check it (§2), rather than asserting it as settled
mathematics.**

**PROVEN PROPERTIES** (hold exactly, by construction, no simulation
needed to establish them):

- **`forward_return` and `sma` independence, via disjoint time
  support.** `sma_{i,t}` depends only on `r_{i,t-L_score+1..t}`;
  `forward_return_{i,t}` depends only on `r_{i,t+1..t+h}`. These index
  ranges do not overlap, and `r`'s own daily autocorrelation is exactly
  zero by construction (§1.4). Two linear functions of disjoint,
  mutually uncorrelated inputs from an i.i.d. process are independent.
  This is what makes `ρ_true = 0` at `w = 0` fall out mechanically —
  confirmed empirically, not just asserted, in
  `research_archive/positive_control_phase3/rho_calibration.csv`
  (`w=0 → ρ̂ ≈ -0.0027`, statistically indistinguishable from zero at
  that pilot's own precision).
- **Finite-memory cutoff.** Both `sma_{i,t}` and `forward_return_{i,t}`
  are functions of exactly `h` (or `L_score = h`) consecutive terms of
  `r`. Neither has any dependence on `r` outside that window, by
  construction — there is nothing to check by simulation here either.
- **Zero correlation after horizon `h`.** A direct consequence of the
  finite-memory property above and `r`'s own zero autocorrelation:
  once two windows of length `h` (or `L_score`) share no common `r`
  term, the resulting linear statistics are uncorrelated. This holds
  for `forward_return`'s own ACF at lag `k ≥ h` and for `sma`'s own ACF
  at lag `k ≥ L_score`, exactly, for the same disjoint-support reason.
- **`forward_return`'s own closed-form Bartlett (triangular)
  autocorrelation function**, a standard result for `h`-period moving
  sums of an i.i.d. series: `ACF(k) = max(0, 1 - k/h)`, `k = 0, 1, 2, ...`.
  This is a property of the *raw, untransformed* `forward_return`
  series and is proven the same way as the two points above. The same
  closed form holds for `sma`'s own raw ACF (an `L_score`-period moving
  *average* rather than *sum* — averaging by a constant `1/L_score`
  does not change the shape of an autocorrelation function, only a
  variance, which cancels in the correlation's own normalization).

**EMPIRICAL PROPERTIES** (plausible, motivated, but not proven by the
algebra above — genuinely require simulation to establish, and are what
§2's fidelity gate exists to check):

- **`score`'s intermediate-lag ACF profile after rank transformation.**
  `score_{i,t} = w · rank(forward_return_{i,t}) + sqrt(1-w²) · rank(sma_{i,t})`
  is **not** a linear combination of the raw `forward_return` and `sma`
  values — it is a linear combination of their *daily cross-sectional
  ranks*, a nonlinear, day-specific transform. The claim that mixing
  two proportionally-weighted, same-order Bartlett-shaped series
  "preserves the functional form" is true for linear combinations of
  the untransformed series; it is not established for a rank-transformed
  combination, and this document previously asserted it as though it
  were. **The score ACF shape is a validation target for §2's gate 2,
  not a mathematical certainty.** This is not a hypothetical concern:
  the first actual execution of gate 2 measured `score`'s empirical
  ACF falling systematically *below* the closed-form Bartlett(20)
  target at lags 1–16 of 20 (deviations of roughly −0.02 to −0.04,
  well outside the gate's own tolerance band) — see
  `research_archive/positive_control_phase3/pilot_results.md` §5b and
  `generator_fidelity_results.json`. The rank transform's effect on
  autocorrelation is real and measured, not a remote theoretical
  possibility.
- **Score-level "Bartlett shape" as a whole.** Generalizing the point
  above: no claim in this document that `score`'s dependence structure
  exactly matches a closed-form target should be read as proven. Only
  `forward_return`'s and `sma`'s own *raw* ACFs are proven Bartlett-shaped;
  what `score` (the rank-space blend) or the daily cross-sectional IC
  series built from it actually look like is an empirical question,
  answered by gate 2 and gate 3 respectively (§2), not derived here.

**No new autocorrelation parameter is calibrated to real data anywhere
in this construction**, regardless of the proven/empirical distinction
above — score-side and return-side autocorrelation *targets* are both
mechanical consequences of one frozen window length `h` (the proven
part), and whether `score` actually achieves its target is a checked,
falsifiable, empirical question (§2), never a fitted one. This still
satisfies Condition 2's option (a): a minimal-assumption synthetic
dependence model, not a fit to archived descriptive statistics that do
not exist at sufficient resolution (no real daily score-autocorrelation
or return-autocorrelation curve has ever been computed and archived on
this platform — only the single scalar "~20–23 effective windows"
figure exists, and that figure was intended to fall out of the model as
a *prediction*, checked against in §2, rather than being an *input* to
it — whether it actually does, given gate 2/3's measured failures, is
now an open question rather than a settled one).

The one parameter that genuinely cannot be derived mechanically is
`β` (cross-sectional correlation across instruments) — resolved in
§3.

### 1.4 Why zero daily autocorrelation is the conservative choice

Setting `r_{i,t}`'s own daily autocorrelation to exactly zero, rather
than some small positive value, is a disclosed assumption, not an
oversight. Any true daily autocorrelation in real returns would only
*add* further overlap-induced compression on top of what the h-period
moving-sum structure already produces mechanically — it cannot reduce
it. Assuming zero is therefore the assumption in the direction that
**cannot overstate the pipeline's effective sample size or its
power** — the exact failure direction v1 Section 5.1 already
identified as the one that matters. This is why zero is frozen rather
than fitted: fitting it to an unarchived, unmeasured real quantity
would reintroduce Condition 2's underdetermination; assuming the
conservative bound removes the parameter entirely.

### 1.5 Why `L_score = h` is frozen (not a free choice)

This study is deliberately indicator-agnostic (v1 Section 0/3 — it is
not testing MOMENTUM or VALUE specifically). `L_score` exists only to
give the synthetic score a realistic *order of magnitude* of
own-autocorrelation, not to reproduce any one real indicator's exact
window. Tying it to `h` (rather than a fixed constant like 20,
regardless of which horizon dimension point is being evaluated) is the
generic, structurally motivated choice: it means every dimension point
in the horizon sweep (§9) evaluates a score whose autocorrelation is
of comparable order to the return series it is being measured against,
at every swept horizon — not an artifact of one horizon happening to
match one real indicator's window by coincidence. Frozen: `L_score = h`
in every dimension point, no exception.

### 1.6 Frozen `w ↔ ρ_true` calibration procedure

`w` is not solved analytically (the composite Spearman correlation of
a rank-space blend of two dependent-on-a-shared-latent-process series
has no simple closed form). Frozen procedure:

1. During Phase 3 (Pre-validation — no outcome data, since this
   calibration only touches the synthetic generator, never real
   forward-return data), run a pilot Monte Carlo sweep of `w` over a
   fixed fine grid (e.g. 41 points, `w = 0.00, 0.025, ..., 1.00`), at
   the anchor dimension point, estimating population Spearman
   correlation empirically at each `w` from a large pilot panel (pilot
   size and its own seed are frozen in `methodology.md`, distinct from
   and not reused as any Validation-phase seed).
2. Fit a monotone interpolant (isotonic regression — the same method
   frozen for the MDE curve itself in §5, for consistency and so this
   document does not introduce two different curve-fitting conventions
   for two structurally similar problems) to `(w, ρ̂)`.
3. For each frozen target `ρ_true` in the Section 9 grid, invert the
   fitted curve to obtain the required `w`, by linear interpolation
   between the two bracketing fitted points.
4. The resulting `(ρ_true, w)` lookup table is committed into
   `methodology.md` verbatim at Phase 4 — Validation (Phase 6) reads
   `w` from this frozen table, it never re-solves it.

This keeps all outcome-touching, judgment-bearing curve-fitting inside
Pre-validation/Freeze, exactly where the lifecycle in
`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 2 places it, and leaves
Validation and Decision as pure execution against frozen numbers.

---

## 2. Generator-fidelity gate v2 (resolves Condition 1)

Replaces v1 Section 7.2, gate 1, in full. Three checks, each against a
**closed-form target derived from the model itself (§1.3)**, not
against an externally measured real-data figure — this is what makes
the gate mechanically verifiable and leak-free (§7's no-leakage gate,
carried forward from v1 unchanged, continues to apply and is now
easier to satisfy since no real-data read is needed for calibration at
all, only for the disclosed `β` convention in §3).

1. **Return-side fidelity.** On a pilot synthetic panel at the anchor
   dimension point, compute the empirical autocorrelation of
   `forward_return_{i,t}` (pooled across instruments, per standard
   practice for panel ACF estimation) at lags `k = 1..h`. Compare
   against the closed-form target `ACF(k) = max(0, 1 - k/h)`. Pass
   condition: every lag's empirical ACF falls within a frozen Monte
   Carlo tolerance band of the closed-form value (tolerance derived
   from the pilot panel's own sampling variance at the pilot's frozen
   size — a statistically principled band, not an eyeballed one; exact
   formula and pilot size fixed in `methodology.md`).
2. **Score-side fidelity.** Identical procedure applied to `score`
   instead of `forward_return`. Because `score` is a blend of two
   Bartlett(h)-shaped series (§1.3), its target ACF is the same
   closed-form curve; the gate confirms the implementation's blending
   step has not introduced an unintended distortion (e.g. an
   off-by-one in the window alignment between `sma` and
   `forward_return`) rather than confirming a value that was never in
   question mathematically.
3. **Combined daily-IC-series fidelity (new — this is the check
   Condition 1 specifically names and v1 lacked entirely).** Compute
   the empirical daily IC series (`daily_ic_series` from
   `core/statistics/significance.py`, called exactly as Validation
   will call it) on the pilot panel, and its own autocorrelation at
   lags `k = 1..60` (covering all three frozen block lengths, 20/40/60
   — carried forward from v1 unchanged). This is **not** compared
   against a pre-specified target — the daily IC series' ACF is an
   emergent property of the composition of two Bartlett(h) series
   through a cross-sectional correlation statistic, and no simple
   closed form is claimed for it. Instead, the gate's pass condition
   is structural: **the empirical daily-IC ACF must decay to
   statistically indistinguishable from zero by lag `h`** (the same
   horizon that bounds both component series' own ACFs) — a
   falsifiable, checkable prediction of the model in §1.3, and the
   quantity that directly justifies using block lengths of 20/40/60
   (all `≥ h` at the anchor) as adequate to capture the daily-IC
   series' true dependence structure. If this check fails, the
   generator does not match its own design assumptions and Phase 3
   cannot proceed to Freeze.

Gate 1 (return-side), gate 2 (score-side), and gate 3 (combined) are
run at the anchor dimension point only, plus a spot check at each
horizon-sweep value (10/20/40) confirming the ACF decay point tracks
`h` correctly (validates §1.5's `L_score = h` rule mechanically, not
just by assertion).

v1's gates 2 (no-leakage), 3 (engine-reuse), and 4
(no-unresolved-degrees-of-freedom) are carried forward unchanged.

---

## 2a. Frozen fidelity tolerance procedure

Specified here, in full, **before** any pilot replication is generated
or any fidelity result observed — added in response to a Governance
Level 2 review finding that §2 above promised "a statistically
principled band, not an eyeballed one" without ever specifying the
method. This procedure is deterministic: nothing below may be chosen,
adjusted, or reinterpreted after seeing gate results.

**Confidence level.** 95%, two-sided (`z_0.975 = 1.959964`), matching
`bootstrap_ci`'s existing 95% CI convention in
`core/statistics/significance.py`.

**Estimator.** For each checked series and lag `k`, `ACF_hat(k)` is the
mean, across `R` independent pilot replications (each a fresh draw from
the frozen generative model at the anchor dimension point, §9), of a
per-replication pooled sample autocorrelation:

- Return-side / score-side (gates 1–2): pool every `(instrument, day)`
  observation with its own lag-`k` value within the same instrument,
  across all instruments, and compute the Pearson correlation of the
  two pooled vectors — the panel-ACF convention already named in §2's
  gate 1.
- Combined daily-IC-series (gate 3): compute `daily_ic_series` (`core/statistics/significance.py`,
  called exactly as Validation will call it) once per replication, then
  its own autocorrelation at lag `k` via Pearson correlation of the
  series against its own lag-`k` shift.

**Deviation metric.** Gates 1–2 (closed-form target exists, §1.3):
`deviation(k) = ACF_hat(k) - ACF_target(k)`, `ACF_target(k) = max(0, 1 - k/h)`.
Gate 3 (no closed-form target — a structural pass condition instead,
§2 item 3): the checked quantity is `|ACF_hat(k)|` against zero, for
`k ≥ h` only (the decay region; `k < h` is reported for information but
is not itself a pass/fail condition).

**Tolerance band.** `tolerance(k) = z_0.975 × SE(k)`, where
`SE(k) = stdev_{r=1..R}(ACF_hat_r(k)) / sqrt(R)` — the standard
construction for the standard error of a Monte Carlo mean, computed
from the pilot's own `R` replications. **Pass condition:**
`|deviation(k)| ≤ tolerance(k)` for every lag `k` in the gate's checked
range.

**Pilot size (`R`), derived from a precision requirement — the same
style as §6's `M` derivation, not an independently chosen number.** A
conservative, closed-form prior bound (not fit to any data from this
study) on a single replication's own sampling variability is Fisher's
classical asymptotic result for a sample correlation `r` estimated from
`n` approximately-independent pairs, at the worst-case (largest
variance) case `ρ ≈ 0`: `SD(r) ≈ 1/sqrt(n)`. Using the smallest number
of independent pairs available across the full checked lag range
(gate 3's upper bound, `k` up to 60) at the frozen anchor evaluation
period (`T = 463`): `n_min = T - 60 = 403`, giving
`SD ≈ 1/sqrt(403) ≈ 0.0498`. Target precision: the tolerance band's own
standard-error component must not exceed half the smallest frozen
effect-size grid spacing (`0.02`, §9) — `SE_target = 0.01` — so a
fidelity failure can never be confused with the smallest difference the
primary grid is designed to resolve. Solving
`SD / sqrt(R) ≤ SE_target`: `R ≥ (0.0498/0.01)² ≈ 24.8` → **frozen:
R = 25**, applied uniformly to gates 1–3 at the anchor dimension point,
no adaptation.

**Pilot size for the `w ↔ ρ_true` calibration (§1.6), same method,
different `n`.** The relevant statistic at each `w` grid point is
`mean_ic`, which itself averages the daily IC series across all 463
days within one panel replication — this platform's own already-
established effective sample size for that averaging is
`N_eff ≈ T/h ≈ 463/20 ≈ 23` independent windows (§1.3, cited from
`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`, not re-derived here).
Applying the same Fisher bound with `n = N_eff - 1 ≈ 22`:
`SD ≈ 1/sqrt(22) ≈ 0.2132` for a single replication's `mean_ic`
estimate. Same target `SE_target = 0.01`. Solving:
`P ≥ (0.2132/0.01)² ≈ 454.6` → **frozen: P = 500** replications per `w`
grid point, applied uniformly across all 41 frozen grid points, no
adaptation.

**Horizon-sweep spot checks (h=10/20/40, §2).** Use the identical
procedure, with `n_min` and `N_eff` recomputed for each swept `h` (the
anchor-point derivation above is not assumed to transfer unchanged to a
different `h`); not yet executed as of this document's current revision
— see `research_archive/positive_control_phase3/pilot_results.md` §7.

**First execution and result.** This procedure was executed for the
first time in
[`experiments/positive_control_phase3_pilot.py`](../experiments/positive_control_phase3_pilot.py),
at the frozen `R = 25`, at the anchor dimension point only. Result:
**gate 1 PASS, gates 2 and 3 FAIL** — see
`research_archive/positive_control_phase3/pilot_results.md` and
`generator_fidelity_results.json` for full detail, and §16 below for
what this means for this document's own Freeze readiness. The
calibration pilot (`P`, above) was executed at a deliberately reduced
scale (11 of 41 `w` points, 50 of the required 500 replications each) —
see `rho_calibration.csv` and `pilot_results.md` §5c/§7.

---

## 3. Resolving the underdetermined calibration problem (Condition 2)

Every generator parameter is now classified into exactly one of three
categories — no parameter is left in an ambiguous fourth category
("assumed, unstated"):

| Category | Parameters | Treatment |
|---|---|---|
| **Mechanically derived** (no calibration input at all) | Score-side and return-side autocorrelation shape, effective-window count, daily-IC ACF decay point | Follow deterministically from `h` (§1.3) — verified, not assumed, by §2's gates |
| **Disclosed convention constant** (frozen, not fit to unarchived real data) | `β` (cross-sectional correlation), daily-return distribution family (Gaussian) | Frozen numeric value stated in §9, justified by general portfolio-theory convention for correlated sector instruments — explicitly **not** claimed to match this platform's own real correlation matrix, because that matrix has never been computed and archived at the resolution this would require |
| **Swept for sensitivity, never point-estimated as ground truth** | `β` low/high bounds, panel length, universe size, horizon, family size | v1 Section 5.4, carried forward unchanged, now explicitly framed as the mitigation for every disclosed-convention parameter above, not only for `β` |

This resolves Condition 2 via option (a) (minimal-assumption model)
rather than option (b): the only candidate "sufficient archived
descriptive statistic" available anywhere in the repository was the
single scalar "~20–23 effective windows" figure (`docs/
REFERENCE_RESEARCH_ROADMAP_NEXT.md`), which is one number, not a full
dependence structure — insufficient to calibrate score-side and
return-side autocorrelation separately, which is exactly the gap
Condition 1 named. Building a model where that figure is a *derived
prediction* rather than a *required input* is the more robust
resolution, and it happens to still reproduce that figure
(§1.3's `T/h ≈ 463/20 ≈ 23` calculation) as an independent
confirmation, which is reported in the fidelity gate's own record as a
cross-check, not cited as the calibration source.

---

## 4. Historical-estimate disclaimer (Condition 3)

**This is stated once here, in full, and referenced — never
restated with softened language — everywhere the archived IC figures
(H1-A −0.117225, H1-B −0.037941, REFERENCE v1's own reported ICs)
appear in any artifact this study produces:**

> These figures are point estimates from prior research cycles whose
> own Decision was ARCHIVE — not PASS. Neither H1-A nor H1-B's
> bootstrap confidence interval excluded zero at any block length
> (`docs/REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md`); REFERENCE v1's
> statistics did not survive bootstrap-robustness either. **They are
> historical estimates produced by an admittedly underpowered
> instrument, not validated economic signal magnitudes, and no
> statement in this study may describe them as evidence that ETF
> markets exhibit effects of these sizes.** Their only legitimate use
> in this study is as already-computed, non-arbitrary reference
> numbers for annotating a synthetic power curve after the fact — see
> §9 for why they are deliberately **not** used to place grid points.

**Structural reinforcement, beyond the caveat sentence.** v1 Section
5.3 required the primary grid to include literal points at the exact
archived IC decimals. This document removes that requirement (§9): the
frozen grid is a round, regularly-spaced sequence chosen independently
of the archived figures, and the archived IC magnitudes are plotted
only as reference annotations against the resulting interpolated power
curve, never as pre-registered grid points. Decoupling the grid's
shape from the specific numbers being disclaimed is a stronger
resolution than a caveat sentence alone — it removes the one place
those numbers could otherwise quietly steer a design choice (grid
density, in particular) even under a fully honest intent, which is
also the leakage risk logged in §12.3.

This disclaimer must appear verbatim (or by direct reference to this
section) in: `methodology.md`, any report generated by
`core/reporting` describing this study's results, and
`decision_log.md`'s final Decision entry.

---

## 5. Frozen MDE estimation procedure (Condition 4)

Four sub-elements, all fixed, none left as an "or" choice:

**5.1 Model / interpolation method — isotonic regression (PAVA),
not logistic regression.** v1 Section 6.2 left this as an unresolved
"isotonic or logistic" choice — itself a researcher degree of freedom.
Frozen to isotonic regression via the pool-adjacent-violators algorithm
(PAVA), for a stated reason: the only structural property the
underlying power curve is expected to have is monotonicity in
`ρ_true` (§1.3's model gives no reason to expect a logistic-specific
functional form, and imposing one would be an unjustified parametric
assumption this study's own emphasis on minimal assumptions argues
against). PAVA requires no third-party dependency (§12.4) and handles
Monte Carlo noise-induced local non-monotonicity in the raw
per-cell power estimates automatically, by construction, rather than
requiring a separate smoothing step.

**5.2 MDE point estimate.** `MDE_80` = the `ρ_true` value at which a
straight-line interpolation between the two grid points bracketing
power = 0.80, evaluated on the **isotonic-fitted** values (not the raw
per-cell power estimates), crosses 0.80. If the fitted curve never
reaches 0.80 within the frozen grid (§9), the result is INCONCLUSIVE
per v1 Section 8, not extrapolated beyond the grid — extrapolation
past the frozen grid is explicitly prohibited, closing another
potential researcher degree of freedom.

**5.3 Uncertainty / confidence interval — nonparametric bootstrap
over replications, fully specified.** For each grid cell, resample its
`M` per-replication "detected" booleans with replacement (independently
per cell); refit the isotonic curve on the resampled per-cell power
estimates; recompute `MDE_80` exactly as in §5.2. Repeat **2,000**
times (matching `bootstrap_ci`'s existing iteration convention in
`core/statistics/significance.py`, for consistency rather than an
independently chosen number). Report the 2.5th and 97.5th percentile
of the resulting `MDE_80` distribution as the frozen 95% CI. If more
than 5% of bootstrap iterations produce an isotonic curve that never
reaches 0.80 (i.e., an undefined `MDE_80` for that iteration), the
overall MDE estimate is INCONCLUSIVE rather than reported from the
remaining iterations — a frozen rule preventing a silent, favorable
selection among bootstrap iterations.

**5.4 Non-monotonicity and ties.** Handled entirely by PAVA's pooling
step (§5.1) — no separate rule is needed, and none is introduced.

---

## 6. Eliminating adaptive-replication degrees of freedom (Condition 5)

v1 Section 5.3 explicitly *permitted* an adaptive replication design
("if adaptive, the adaptation rule itself must be frozen in advance").
This is insufficient: it still leaves open which adaptation rule to
choose, a live researcher degree of freedom at Freeze time. **This
condition is resolved by banning adaptive replication outright, not by
requiring the adaptation rule to be pre-registered:**

- **Primary grid:** every cell (including `ρ_true = 0`) uses an
  identical, fixed `M = 400`, decided once from the precision formula
  in v1 Section 5.3 (`SE ≈ sqrt(p(1-p)/M)`, bounding SE at ≈2.5% at
  the conservative `p ≈ 0.5` case, `M ≥ 385`; 400 is the frozen,
  rounded value). No cell receives more or fewer replications than any
  other, regardless of proximity to the eventual MDE boundary.
- **Secondary grid:** every cell uses an identical, fixed `M = 100`
  (SE ≈ 5%, 95% CI half-width ≈10 power points — explicitly disclosed
  as directional/magnitude characterization only, per the existing
  governance exception in v1 Section 7.4, now with the literal number
  fixed rather than left as "reduced"). This remains the sole
  documented, time-boxed, Section-8-compliant governance exception in
  this design (§11.3 supplies its full worked-example record).
- **Explicit prohibition, stated for the record:** no grid cell's
  replication count may be changed after any simulation has begun, for
  any reason, including apparent proximity to a decision boundary,
  computational budget pressure discovered mid-run, or any other
  observation made during Validation. A budget constraint discovered
  mid-run is handled as an INCONCLUSIVE outcome and a new,
  separately-logged Phase 3 re-entry (v1 Section 8, carried forward
  unchanged) — never as an in-flight adjustment to `M`.

---

## 7. Type I calibration test — exact binomial test replaces the ad hoc tolerance band

v1 Section 6.2 proposed a tolerance band "e.g. [0.03, 0.07]... exact
band fixed at freeze" — an unresolved placeholder that would have left
the band's edges as a live researcher choice at Freeze. Replaced with a
named, standard statistical test with a single conventional free
parameter:

**PC-H1 is evaluated as an exact two-sided binomial test** of
`H0: true detection rate = 0.05` against the `M = 400` observed
outcomes at `ρ_true = 0` (the anchor dimension point). Reject `H0`
(→ FAIL, per v1 Section 8's FAIL criterion) if the exact binomial
test's p-value is below a frozen **`α_meta = 0.01`** — set below the
conventional 0.05 deliberately, because this is a meta-test whose
false trigger would (per v1 Section 8) require re-examining every
prior FAIL/INCONCLUSIVE verdict issued under the pipeline; a
conservative `α_meta` is the justified choice given that asymmetric
cost, not an arbitrarily chosen number. This fully replaces the band
concept — there is no separate "tolerance width" parameter left to
freeze.

---

## 8. RNG / seed scheme freeze (reproducibility fix)

v1 Section 6.1's illustrative seed formula (`hash(dimension_point,
rho_true, replication_index)`) has a concrete, non-hypothetical
reproducibility defect: Python's built-in `hash()` on strings (and on
tuples containing strings) is **randomized per-process** by default
(`PYTHONHASHSEED`), so the same "frozen" formula would silently
produce different seeds, and therefore different Monte Carlo results,
on every run unless every future execution environment happens to pin
`PYTHONHASHSEED` — an operational dependency nowhere stated in v1 and
easy to violate by accident (e.g. a CI runner with a different default).
This is exactly the kind of reproducibility weakness the Level 2 review
asked to be searched for. Frozen replacement:

```
seed_material = f"{base_seed}|{dimension_point_id}|{rho_true:.6f}|{stream_tag}|{replication_index}"
seed = int.from_bytes(hashlib.sha256(seed_material.encode("utf-8")).digest()[:8], "big")
rng = random.Random(seed)
```

`hashlib.sha256` is deterministic across processes, platforms, and
Python versions by construction — no environment variable dependency.
`stream_tag` distinguishes **two independent RNG streams per
replication** — `"panel"` (drives §1's generator) and `"test"` (drives
`permutation_null` and `bootstrap_ci`'s own internal resampling) — so
that panel-generation randomness and statistical-test resampling
randomness never share a stream. This closes a second, related
reproducibility risk v1 did not address: without stream separation, an
undetected correlation between "which panel got generated" and "how
the bootstrap happened to resample it" could not be ruled out, and
would be silently baked into every result with no way to detect it
after the fact. `dimension_point_id` is a canonical, frozen string
encoding of every swept-dimension value at that cell (exact format
fixed in `methodology.md`), never derived from a mutable object
identity. `base_seed` is a single literal integer, chosen once and
logged in `methodology.md` at Phase 4 — not re-chosen at Validation.

---

## 9. Frozen grid values

**Primary grid (`ρ_true`), anchor dimension point:**

`{0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16}` — 9 points,
regular 0.02 spacing, chosen independently of the archived IC figures
(§4). Range justified by the generally cited order of magnitude for
cross-sectional factor ICs in quantitative equity/ETF research
(small-to-moderate, conventionally described as roughly 0.02–0.15) —
a generic literature convention, not a figure computed from this
platform's own archived results, keeping the grid decoupled from
§4's disclaimer as intended. `M = 400` at every point (§6).

**Anchor dimension point (unchanged from v1 Section 5.4):** 25-instrument
universe, 463 overlapping ranking dates, `h = 20`, permutation
iterations = 10,000, bootstrap iterations = 2,000, block lengths =
(20, 40, 60), Holm-Bonferroni family size = 5 (its reproduction
mechanism is now fully specified in §10), `α = 0.05`, `β = 0.30`
(disclosed convention, §3).

**Secondary grid (v1 Section 5.4 dimensions, unchanged in kind, now
with fixed, non-adaptive `M = 100` at every cell per §6):**

| Dimension | Sweep values |
|---|---|
| Panel length | 250 / 463 / 750 / 1250 |
| Universe size | 15 / 25 / 40 |
| Forward horizon (`h`, drives `L_score` per §1.5) | 10 / 20 / 40 |
| Family size | 1 / 5 / 8 |
| `β` (cross-sectional dependence strength) | 0.10 / 0.30 / 0.50 |

---

## 10. The multi-statistic family-size reproduction design (a previously hidden degree of freedom, found and resolved)

The anchor case's family size is 5, matching REFERENCE v1's own
simultaneously-tested statistics. Neither v1 nor an unexamined reading
of this design specifies **how** a single injected `ρ_true` becomes
"5 simultaneous statistics" for Holm-Bonferroni correction to operate
on per replication — this is a genuine gap the Level 2 review's "search for
undocumented statistical choices" instruction surfaces. Resolved and
frozen:

Per replication, five statistics are computed, mirroring REFERENCE
v1's own five (MOMENTUM IC, VALUE IC, raw blend, normalized blend,
top-bottom spread) in *role*, not in economic content (this study has
no economic content):

1. `mean_ic` of the **primary** synthetic score (the one carrying the
   injected `ρ_true`, §1.2) — this is the **only** statistic whose
   "detected" outcome feeds the power calculation.
2. `mean_ic` of a **secondary** synthetic score, constructed
   identically to the primary but from an independently-seeded latent
   path (its own `panel` stream, distinct `stream_tag`) — always with
   `ρ_true = 0`, regardless of what `ρ_true` is being tested for the
   primary statistic.
3. `mean_ic` of the unweighted mean of statistics 1 and 2's underlying
   scores (raw blend analogue).
4. `mean_ic` of the rank-normalized blend of the same two scores
   (normalized blend analogue).
5. `top_bottom_spread` of the primary score.

Statistics 2–4 exist **only** to reproduce the multiple-testing
correction burden the real pipeline's promotion rule imposes on
statistic 1 — their own individual detection rates are never reported
or used. Freezing them at `ρ_true = 0` is the deliberately
conservative choice: it means the correction burden applied to
statistic 1 is exactly as large as if the other four tested constructs
carry no real signal, rather than assuming any of them are also
validated — again the assumption direction that cannot overstate
power (consistent with §1.4's reasoning). This is now a fully
specified, checkable procedure, not an implicit gap.

---

## 11. Governance resolutions (drafted, ready for a separate commit)

v1 Section 7.5 flagged three governance gaps as blocking Phase 4. Full
resolution text is drafted here; applying it to
`docs/RESEARCH_GOVERNANCE_STANDARD.md` and `docs/
REFERENCE_RESEARCH_ROADMAP_NEXT.md` is a separate, mechanical editorial
action this document recommends but does not itself perform (those
files are authoritative and outside this study's own scope to edit
unilaterally).

**11.1 Synthetic-cycle dataset-manifest addendum (for
`RESEARCH_GOVERNANCE_STANDARD.md`).** *"For a fully synthetic-data
research cycle (one with no real market outcome data at any phase),
`dataset_manifest.json` records, in place of a real data snapshot
hash: the generator code's commit hash, the frozen base seed and
stream-tag scheme (Section 3 item 2 of this standard, 'Dataset
version'), and the pilot-calibration commit hash if any pre-Freeze
pilot run (e.g. a `w ↔ ρ_true` lookup table) was used as a Freeze
input. This satisfies Evidence Package Standard Section 5's
`dataset_hashes/` requirement by treating the deterministic generator
plus its frozen seed scheme as the cycle's 'dataset.'"*

**11.2 Calibration-leakage firewall promotion (for
`REFERENCE_RESEARCH_ROADMAP_NEXT.md` Section 4).** Add as item 5:
*"No future hypothesis cycle may cite `positive_control_v1`'s
calibration parameters, power curves, or MDE figures to select, size,
or justify that cycle's own effect-size expectation, lookback, or
promotion criteria. Those outputs may describe what the pipeline can
detect in general; they may never inform what a specific hypothesis
should target."* (v1 Section 6.4, carried forward unchanged in
substance, now given a ready-to-merge location.)

**11.3 Reduced-replication worked example (for
`RESEARCH_GOVERNANCE_STANDARD.md` Section 8).** *"Worked example —
reduced replication for secondary sensitivity sweeps: `positive_control_v1`'s
secondary dimension grid (panel length, universe size, horizon, family
size, cross-sectional dependence strength) used a fixed M=100 per cell
against the primary grid's fixed M=400, a documented reason
(computational budget: the secondary grid spans 4+3+3+3+3=16 additional
cells beyond the anchor, each requiring a full generator-fidelity-
validated pilot run if replicated at primary-grid precision), an
impact assessment (secondary-grid power estimates carry a 95% CI
half-width of ≈10 power points versus ≈5 for the primary grid, and are
reported as directional/magnitude characterizations only, never as
precision estimates feeding the PASS/FAIL/INCONCLUSIVE Decision, which
is determined entirely by the anchor-case primary grid), and a time-box
(scope limited to this cycle's secondary grid only, expiring at this
cycle's Phase 8 archive, not a standing precedent for any other
cycle's own M choice without its own separate exception record)."*

---

## 12. Additional findings from the Level 2 review's standing search instructions

**12.1 (RNG determinism bug) — resolved in §8.** A concrete, not
hypothetical, reproducibility defect in v1's illustrative seed formula
(Python's randomized string `hash()`).

**12.2 (RNG stream correlation) — resolved in §8.** Panel-generation
and statistical-test resampling must use independently seeded streams
per replication; otherwise a correlation between the two could not be
ruled out and would be undetectable after the fact.

**12.3 (Information leakage risk in grid design) — resolved in §4 and
§9.** Requiring literal grid points at the exact archived IC decimals
(v1 Section 5.3) is a subtle channel by which already-known results
could shape a "should-be-blind" design choice (grid density near known
values), even under fully honest intent. Resolved by decoupling the
grid entirely from the archived figures (§9) and using them only as
post-hoc annotations (§4).

**12.4 (Implementation-phase dependency risk).** The frozen
methodology (isotonic regression/PAVA, exact binomial test, SHA-256
seeding) must be implementable using only the Python standard library,
matching `core/statistics/significance.py`'s own explicit "depends on
nothing outside the standard library" constraint
(`core/statistics/significance.py:40`). Freezing this now, rather than
leaving it implicit, prevents Phase 5 from quietly introducing a new
third-party dependency (e.g. `scipy.stats` for isotonic regression or
the binomial test) that the platform does not currently carry, which
would itself be an unfrozen Phase 5 design decision under `docs/
RESEARCH_GOVERNANCE_STANDARD.md`'s Phase 5 definition ("this phase
makes no design decisions"). **Frozen: pure-Python implementations
required for PAVA and the exact binomial test (both are short,
well-known algorithms with no numerically delicate edge cases at the
sample sizes in use here); no new dependency may be added without
reopening Methodology Freeze.**

**12.5 (Forward maintenance risk — significance.py version pinning).**
This study's calibration (fidelity gate targets, MDE procedure) is
validated against `core/statistics/significance.py` at a specific,
recorded commit hash (v1 Section 10, "engine-reuse gate," carried
forward). **New, explicit rule:** if that module is ever modified after
this cycle's Decision is recorded, `positive_control_v1`'s Decision no
longer describes the modified pipeline's power or calibration, and
this must **not** be silently assumed to still hold. Any future change
to `core/statistics/significance.py` must trigger a documented,
Level-2-minimum-reviewed decision — either "re-validate under
`positive_control_v2`" or "explicitly accept the gap and disclose it"
— recorded in the *modifying* change's own commit/decision trail, not
left as an implicit inheritance. This extends the freeze-invalidation
logic `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 3 already applies
*within* a cycle to this study's *downstream consumers* across time.

**12.6 (Governance ambiguity — Level 3 review) — no new finding.** v1
Section 7.3 already discloses the standing Level 3 unavailability
correctly and sufficiently; no further resolution needed here.

**12.7 (Semi-synthetic sensitivity check — scope boundary).** v1
Section 5.2 retains an optional Phase 6 semi-synthetic check "excluded
from the primary PASS/FAIL determination." Confirmed carried forward
unchanged, with one addition: **its output, if computed, is also bound
by §4's historical-estimate disclaimer**, since it necessarily reuses
real historical returns and could otherwise be misread as a stronger
validation than the disclaimer permits.

---

## 13. Complete Methodology Freeze checklist

Against `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 3's eight
required elements — every item below is either a literal frozen value
in this document already, or a named deterministic procedure that
produces one during Phase 3 pre-validation (§1.6) before Freeze
closes:

| # | Element | Status |
|---|---|---|
| 1 | Universe | Anchor: 25 synthetic instruments; secondary sweep 15/25/40 (§9) — frozen |
| 2 | Dataset version | Generator commit hash + base seed + stream-tag scheme (§8, §11.1) — frozen once committed |
| 3 | Evaluation period | Anchor: 463 overlapping ranking dates; secondary sweep 250/463/750/1250 (§9) — frozen |
| 4 | Benchmark | None (no economic benchmark; the "benchmark" is the frozen closed-form model prediction, §1.3/§2) — frozen |
| 5 | Metrics | `mean_ic` (×2, primary+secondary), raw/normalized blend `mean_ic`, `top_bottom_spread` — exact composition frozen (§10) | 
| 6 | Scoring rules | Full generative model, §1.2, including the `w↔ρ_true` lookup procedure (§1.6) — frozen |
| 7 | Parameters | `β=0.30` (anchor) + sweep, `L_score=h`, daily autocorrelation=0, all justified (§1.4, §1.5, §3) — frozen |
| 8 | Acceptance criteria | PASS/FAIL/INCONCLUSIVE per v1 Section 8, PC-H1 test redefined in §7, MDE procedure in §5, replication counts in §6 — frozen |

No element remains an "e.g." placeholder, an "or" choice, or an
"adaptive, rule TBD" clause anywhere in this document.

---

## 14. Decision table

| Decision | Frozen value | Rationale / justification | Alternatives considered | Why rejected |
|---|---|---|---|---|
| Synthetic generator family | Unified latent-path model, §1.2 | Makes score-side and return-side autocorrelation mechanical consequences of one frozen window `h`, closing Condition 1/2 simultaneously | v1's original Type A (rank-injected noise on forward return only) | No mechanism for score-side autocorrelation; left Condition 1's gap unaddressed |
| Daily-return autocorrelation | 0 (exactly) | Conservative direction — cannot overstate effective N or power (§1.4) | Fit to an archived real figure | No such figure is archived at sufficient resolution (only one scalar effective-N figure exists) |
| Cross-sectional correlation `β` (anchor) | 0.30 | Disclosed portfolio-theory convention for correlated sector instruments, not fit to unarchived real data | Fit to platform's real correlation matrix | Never computed/archived; would reintroduce Condition 2's underdetermination |
| `β` sensitivity sweep | 0.10 / 0.30 / 0.50 | Bounds the risk of the convention value being wrong (§3) | Point-estimate only, no sweep | Leaves a disclosed-but-unbounded assumption |
| `L_score` | `= h` at every dimension point | Generic, structurally motivated; avoids coincidental match to one real indicator's window | Fixed constant (e.g. always 20) | Would be an artifact of one horizon matching one real indicator by chance, not a general rule |
| Score construction | Rank-space blend of `forward_return` and `sma`, weight `w` | Exact effect-size control + realistic, independent autocorrelation, simultaneously (§1.2) | Direct noise injection on `forward_return` only (v1 original) | No score-side autocorrelation; superseded |
| `w ↔ ρ_true` calibration | Pilot Monte Carlo + isotonic fit, frozen lookup table at Phase 4 (§1.6) | Keeps all curve-fitting inside Pre-validation, none at Validation | Closed-form solve | No simple closed form exists for this composite construction |
| Generator-fidelity gate | 3 checks: return-side ACF, score-side ACF, combined daily-IC ACF decay (§2) | Directly validates Condition 1's named requirement | v1's single effective-window scalar check | Did not check score side at all; the specific gap Condition 1 named |
| MDE interpolation method | Isotonic regression (PAVA) | Only assumes monotonicity, the one structurally justified property; no dependency needed (§5.1, §12.4) | Logistic regression (v1's other option) | Assumes an unjustified parametric shape; removing the "or" closes Condition 4 |
| MDE uncertainty method | Bootstrap over per-cell replications, 2,000 iterations, refit isotonic each time (§5.3) | Fully specified single method; iteration count matches existing pipeline convention | Analytic/asymptotic CI | No general closed form for isotonic-fit inversion uncertainty |
| Primary replication count | Fixed `M = 400`, every cell, no adaptation | Precision-formula-justified (v1's own SE formula), applied uniformly | Adaptive M (v1's original allowance) | Leaves the adaptation rule itself as a live researcher DOF; banning is stronger than pre-registering |
| Secondary replication count | Fixed `M = 100`, every cell, no adaptation | Time-boxed governance exception with explicit impact assessment (§11.3) | Same M as primary throughout | Computationally intractable across 16 additional cells at full precision |
| Type I test | Exact two-sided binomial test, `α_meta = 0.01` | Replaces an unresolved tolerance-band placeholder with a named standard test | Ad hoc tolerance band (v1 original) | Band edges were never fixed — an unresolved researcher DOF |
| RNG seeding | SHA-256-derived, two streams (`panel`/`test`) per replication (§8) | Deterministic across process/platform/Python version; no stream reuse | Python built-in `hash()` (v1 original) | Randomized per-process by default — a real reproducibility defect, not merely a style choice |
| Effect-size grid | Round, regular 0.02-spaced grid, 0.00–0.16, chosen independent of archived figures (§9) | Removes the one channel by which known results could shape grid density (§12.3) | Grid including exact archived IC decimals (v1 original) | Subtle information-leakage risk into a "should-be-blind" design choice |
| Family-size (5) reproduction | 5 statistics per replication, secondary 4 always at `ρ_true=0` (§10) | Reproduces the real correction burden without assuming unvalidated secondary signal | Leave unspecified (v1's implicit gap) | Undefined how one injected ρ becomes 5 simultaneous statistics — a hidden DOF |
| Block bootstrap lengths | 20/40/60 (inherited from v1/real pipeline) | Matches real pipeline exactly; now justified post hoc by §2 gate 3's ACF-decay-by-`h` check | Re-derive from synthetic ACF | Unnecessary — real pipeline's own values are the correct benchmark to reuse, not re-optimize |
| Semi-synthetic check scope | Optional Phase 6 robustness only, bound by §4's disclaimer | Prevents a real-data-touching check from being read as stronger evidence than it is | Promote to primary | Reintroduces real outcome data into the primary determination — against Section 3 of this study |
| Implementation dependencies | Pure standard library only (§12.4) | Matches `significance.py`'s own constraint; prevents an unfrozen Phase 5 dependency decision | Use `scipy.stats` | Would be an undisclosed Phase 5 design decision under the Standard's own Phase 5 definition |

---

## 15. Remaining limitations after Freeze (stated regardless of outcome)

All of v1 Section 12's limitations are carried forward unchanged
(external validity out of scope by design; a single universe/horizon
anchor case; Level 3 review unavailable platform-wide; cannot
retroactively strengthen v1/H1/H3's archived Decisions). In addition:

- **The `β = 0.30` convention is disclosed, not measured**, and no
  amount of sensitivity sweeping (§9) converts a convention into a
  measurement — a materially different real cross-sectional
  correlation structure than assumed here would not be caught by this
  study's own gates, only bounded in its plausible impact.
- **This study's Decision is scoped to a specific commit of
  `core/statistics/significance.py`** (§12.5) and does not
  automatically transfer to any future modification of that module —
  a standing maintenance obligation on every future change to that
  file, not a one-time caveat.
- **The `w ↔ ρ_true` lookup table is itself a Phase 3 pilot-calibration
  artifact** — accurate to the pilot's own Monte Carlo precision, not
  exact. A materially undersized pilot would propagate imprecision
  into every downstream `ρ_true` grid point's actual realized
  correlation, which is why the pilot's own size and precision must be
  stated and justified in `methodology.md`, not chosen incidentally.
- **The 5-statistic family-size reproduction (§10) is a design choice
  about how to simulate correction burden, not a claim that this is
  the only valid way to do so** — a different, equally defensible
  scheme (e.g. all 5 statistics carrying partial signal rather than 4
  at exactly zero) would produce a different, likely larger, MDE. The
  chosen scheme is the conservative bound, disclosed as such, not the
  only conceivable one.

---

## 16. Recommendation

**NOT READY FOR FREEZE. Phase 3 Pre-validation Evidence produced;
Freeze decision pending.**

A Governance Level 2 validation review of this document found that,
notwithstanding the detailed resolution of all five review conditions
in §1–§12, this document's own (pre-correction) §1.6 named "the Phase 3
pilot run that produces the `w ↔ ρ_true` lookup table ... and executes
the generator-fidelity gate" as a genuinely outstanding pre-Freeze
action — and at the time this document previously declared READY FOR
FREEZE, that pilot had not been run. Declaring Freeze-readiness in the
same document that discloses an unexecuted required Pre-validation step
is a direct violation of `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2's
phase ordering: Phase 3 Pre-validation must complete before Phase 4
Methodology Freeze opens. A design being fully specified in writing is
not the same thing as its Pre-validation evidence existing. The same
review also found the committee-language and §1.3 proven/empirical
issues corrected elsewhere in this revision (Status update, top of
document; §1.3).

**This has since been partly addressed, not resolved.**
[`research_archive/positive_control_phase3/pilot_results.md`](../research_archive/positive_control_phase3/pilot_results.md)
records the first actual Phase 3 pilot execution: the generator-fidelity
gate run at its full frozen precision (`R = 25`, §2a), and a
**deliberately reduced, explicitly preliminary** pass of the
`w ↔ ρ_true` calibration procedure (11 of the frozen 41 grid points,
50 of the derived 500 replications per point). The result is not a
clean pass: **gate 1 (return-side ACF) PASSES; gates 2 (score-side ACF)
and 3 (combined daily-IC-series ACF decay) FAIL** at the anchor
dimension point. This is a substantive, measured finding, not a
paperwork gap — §1.3's corrected text explains why (the rank transform
applied to build `score` is not proven to preserve the closed-form
ACF shape its raw linear inputs have, and the first execution of the
gate designed to check this found that it measurably does not, at
this pilot's precision). Full detail, including what is and is not yet
explained about the failures, is in `pilot_results.md` §5b–§7; it is
not restated here.

**What remains before Methodology Freeze can be declared — all of
these are open, none is a formality:**

1. **The generator-fidelity gate fails at the anchor point** (gates 2
   and 3). Either the generator construction (§1.2) needs revision to
   actually achieve the ACF shape this document targets, or the target
   itself needs to be replaced with a measured (not assumed) one, or
   the fidelity gate's own tolerance needs re-examination — resolving
   which of these is correct is Phase 3 work, and none of it has been
   done. Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 Phase 3, any
   resulting change to the generator construction is a new, separately
   logged construction attempt, not a silent patch to this document.
2. **The full-precision `w ↔ ρ_true` calibration** (all 41 frozen grid
   points, `P = 500` replications each, §2a) has not been run — only a
   reduced preliminary pass exists, and running it against a generator
   that item 1 may still change would be premature in any case.
3. **Horizon-sweep spot checks** (h=10/20/40, §2/§2a) have not been run
   at all — anchor point (h=20) only.
4. **No Level 2 review of the pilot execution itself** (its code or its
   numerical output) has occurred — the pilot that produced the
   findings above is Level 1 (self-review) only.
5. **§11's three governance-document edits** (dataset-manifest
   addendum, calibration-leakage firewall promotion, reduced-replication
   worked example) remain drafted, not applied to their target
   documents.
6. **No `methodology.md` freeze document has been committed**; per
   `docs/RESEARCH_GOVERNANCE_STANDARD.md` §3, freeze is not effective
   until it is, independent of every other item above.

Nothing above reopens or weakens §1–§12's design resolutions for the
five original review conditions — the fidelity gate's *design*, the
MDE procedure, the replication-count rules, and the RNG scheme all
remain as specified, and item 1 above is about whether the *generator*
achieves what the design targets, not about the soundness of the
design's own logic. What changed in this revision is this document's
own claim about its readiness, corrected to match what has actually
been executed and reviewed, per
`research_archive/positive_control_phase3/decision_log.md`.
