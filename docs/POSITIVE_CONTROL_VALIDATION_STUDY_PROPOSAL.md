# Positive Control Validation Study — Research Proposal

**Status: Phase 1–2 artifact (Hypothesis + Research Proposal) under
`docs/RESEARCH_GOVERNANCE_STANDARD.md`. Not yet frozen. No code has
been written for this study.** This document is the committee-facing
design that must be reviewed and approved before Phase 3
(Pre-validation) may open.

**Working cycle name:** `positive_control_v1` (alternate names
considered: `synthetic_signal_validation_v1`,
`statistical_power_calibration_v1` — see Section 9 for why
`positive_control_v1` is recommended).

---

## 0. Committee finding this responds to

> The platform has demonstrated that it can reject hypotheses, but it
> has not yet demonstrated that it can reliably detect a true signal
> when one exists (absence of a positive control and statistical power
> calibration).

This proposal treats that finding as correct and does not attempt to
argue it away. Section 1 confirms it against the repository directly.

---

## 1. Review of existing work (Objective 1)

A repository-wide search (`docs/`, `core/`, `research_archive/`,
`tests/`) for power, positive-control, synthetic-data, false-negative,
minimum-detectable-effect, or Monte Carlo methodology found **no
implementation of any kind**. What exists instead is a consistent,
repeated *qualitative* acknowledgment of the same gap:

- REFERENCE v1's closeout names "insufficient statistical power" as
  "the dominant and correct" explanation for its non-result
  ([`docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md:118`](REFERENCE_V1_RESEARCH_CLOSEOUT.md)).
- REFERENCE v2 H1's closeout repeats the same phrase
  ([`docs/REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md:105`](REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md)).
- H3's closeout repeats it a third time
  ([`docs/REFERENCE_H3_RESEARCH_CLOSEOUT.md:156`](REFERENCE_H3_RESEARCH_CLOSEOUT.md)).
- The roadmap memo goes furthest, correctly diagnosing the *mechanism*
  — an effective sample size of ~20–23 independent windows behind 463
  overlapping 20-day ranking dates, a property of the panel's
  overlapping-window structure rather than of any one hypothesis
  ([`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md:37-43,118-124,185-202`](REFERENCE_RESEARCH_ROADMAP_NEXT.md)).

What none of these four documents do — and what no code in the
repository does — is *quantify* the claim. "Insufficient power" has
been asserted three times as a diagnosis and never once measured.
There is no evidence the pipeline can detect a real signal of any
size, at any power level, because it has never been given one to
detect. The committee's finding is confirmed, not merely plausible.

**Conclusion:** this is genuinely new work, not a refinement of an
existing study. Section 9 covers naming and archive placement.

---

## 2. Scientific rationale

A hypothesis-testing pipeline has two ways to be uninformative: it can
fail to reject false hypotheses at an inflated rate (Type I error,
already checked implicitly by permutation testing's own construction),
or it can fail to reject true ones — deliver a false negative on a
real signal — which is a property of *power*, and power has never been
touched by this platform's evaluation apparatus. Three consecutive
"insufficient power" verdicts (v1, H1, H3) are consistent with two
completely different underlying realities that the platform currently
cannot distinguish between:

1. There is no real signal in any of the three tested constructs, and
   the pipeline correctly said so.
2. There is a real, economically meaningful signal in one or more of
   them, but the pipeline's effective sample size makes it structurally
   incapable of detecting an effect of that size at the promotion bar
   in use.

These two explanations call for opposite next actions — (1) says stop
testing variants of these three mechanisms; (2) says the mechanisms may
be fine and the *instrument* needs a larger effective sample before it
can see them. Without a power calibration, the platform cannot tell
these apart, and every future FAIL or INCONCLUSIVE inherits the same
ambiguity. A positive control resolves this by giving the pipeline a
signal whose existence and magnitude are known by construction, so its
detection or non-detection is informative about the *instrument*, not
about ETF markets.

---

## 3. What this study is not

Stated up front because it bounds every design choice below:

- **Not an economic hypothesis.** It makes no claim about ETF returns,
  momentum, value, volatility, or relative strength. It never touches
  real forward-return outcome data.
- **Not a modification of the validated pipeline.** Per Constraint 3/4,
  every statistical primitive used —
  [`mean_ic`](../core/statistics/significance.py), `top_bottom_spread`,
  `permutation_null`, `empirical_p_value`, `bootstrap_ci`,
  `holm_bonferroni` — is imported from
  [`core/statistics/significance.py`](../core/statistics/significance.py)
  and called exactly as implemented. No function in that module is
  edited, wrapped, or monkey-patched. This is a hard, checkable
  constraint: the implementation phase's conformance note (Standard
  Phase 5) will diff `core/statistics/significance.py` against its
  pre-study commit and require it to be byte-identical.
- **Not a claim that ETF-level predictability exists.** A positive
  control validates the *instrument*, not the *hypothesis*. Section 12
  states this limitation without hedging.

---

## 4. Hypotheses (Phase 1 statements)

Two methodological hypotheses, about the pipeline, not about markets:

**PC-H1 (calibration).** At the panel dimensions actually used by
REFERENCE v1/H1/H3 (25-instrument universe, 20-trading-day horizon,
overlapping-window panel), the empirical false-positive rate of the
frozen pipeline (permutation test → Holm-Bonferroni correction →
block-bootstrap CI, combined exactly as the promotion rule in
`experiments/validate_reference_v1_significance.py` uses them) is
statistically indistinguishable from its nominal α (0.05) when the true
population Spearman correlation between score and forward return is
exactly zero.

**PC-H2 (power).** At the same panel dimensions, the pipeline's
statistical power to detect a known, injected population Spearman
correlation is quantifiable as a function of effect size, and a
minimum detectable effect (MDE) at 80% power can be estimated with a
pre-registered precision target.

Both are falsifiable: PC-H1 fails if the empirical Type I rate falls
outside a pre-registered tolerance band around 0.05; PC-H2 fails to
produce an actionable answer only if the MDE cannot be bounded within
the pre-registered precision at the computational budget available
(an INCONCLUSIVE outcome, not a FAIL — see Section 8).

---

## 5. Experimental design

### 5.1 The central methodological risk (and why it drives everything else)

The single most consequential design decision in this study is **how
synthetic forward returns are generated across periods**, and getting
it wrong invalidates the entire calibration in the direction that
matters most: it would make the pipeline look more powerful than it
is.

The real panel's binding constraint — ~20–23 *effective independent*
windows behind 463 *overlapping* ranking dates — exists because
20-trading-day forward returns computed on consecutive ranking dates
share up to 19 of their 20 underlying daily returns. A synthetic panel
that draws each period's forward-return cross-section as an
independent Gaussian draw would not reproduce this overlap, would
implicitly have ~463 independent windows instead of ~20–23, and would
report power far above what the real pipeline achieves — a calibration
that is wrong in exactly the direction that would make the committee's
concern look resolved when it is not.

**Design requirement:** synthetic data must be generated as a single
underlying daily return path per synthetic instrument (with a
specified daily autocorrelation/cross-sectional correlation
structure), from which overlapping 20-day forward returns are then
computed by summation over the same overlapping windows the real
pipeline uses — never as independent per-period draws. This reproduces
the effective-sample-size compression mechanically, the same way it
arises in the real data, rather than asserting a target effective N by
assumption.

### 5.2 Two complementary generator designs

**Type A — Controlled rank-injection (primary).** For each synthetic
instrument and trading day, draw a latent daily return series with a
specified cross-sectional correlation structure (instruments are not
independent of each other, mirroring real ETFs' shared market-wide
component). Compute overlapping 20-day forward returns exactly as the
real pipeline does. Construct the `score` series as forward return's
rank, corrupted by calibrated noise, so that the *population* Spearman
correlation between score and forward return converges to a specified
target ρ_true as sample size grows. This gives exact, arbitrary control
over the injected effect size — the primary lever for the power curve
in Section 5.3.

**Type B — Factor-model simulation (secondary, robustness only).** A
single latent common factor plus per-instrument idiosyncratic noise
generates daily returns; `score` is a noisy read of each instrument's
factor loading. Less exact control over the realized ρ_true (it is an
emergent property of the factor loadings rather than a direct target),
but a more realistic proxy for "a real economic signal buried in
correlated instruments." Used only for the robustness-across-dependence-
structure checks in Section 5.4, never as the primary power-curve
source, precisely because its effect size is not directly dialable —
using it as primary would make the effect-size grid a derived
quantity, not a frozen input, which conflicts with the freeze
requirement in Section 7.

**Rejected: semi-synthetic (reuse real historical returns, inject a
synthetic score on top).** Considered and rejected as the *primary*
method because it partially reintroduces real market outcome data into
what should be a fully synthetic exercise, blurring the "no outcome
data touched outside Validation" boundary the governance standard
enforces (Section 6, Phase 3). Retained as an optional Phase 6
sensitivity check only, explicitly labeled semi-synthetic and excluded
from the primary PASS/FAIL determination.

**Rejected: closed-form (Fisher z) power approximation instead of
Monte Carlo.** Rejected as the primary method because it approximates
power for a plain Spearman significance test, not for the actual
composite procedure in use (permutation null → Holm-Bonferroni →
block-bootstrap agreement). Constraint 4 requires reusing the existing
engine exactly as implemented; a closed-form shortcut would validate a
different, simpler procedure than the one actually deployed. Retained
only as a cross-check at 2–3 grid points to sanity-check the Monte
Carlo engine itself is not misimplemented.

**Rejected: i.i.d. per-period synthetic panels.** Rejected per Section
5.1 — this is the design error that would produce an invalid,
overly-optimistic calibration.

**Rejected: single-dimension study (anchor case only, no parameter
grid).** Rejected because Objective 6 explicitly requires robustness
across realistic parameter ranges, and because the roadmap memo's own
open structural question about historical depth
([`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` Section 6](REFERENCE_RESEARCH_ROADMAP_NEXT.md))
is directly answerable by this study's secondary grid (Section 5.4) if
and only if panel length is a swept dimension, not fixed.

### 5.3 Primary grid — effect size (the power curve)

At the **anchor dimension point** (Section 5.4, matching REFERENCE
v1/H1/H3 exactly), sweep ρ_true over a pre-registered grid. The grid
must include:

- **ρ_true = 0** — the Type I error / calibration check (PC-H1).
- **Archive-anchored points** — the actual observed IC magnitudes
  already in evidence from the completed cycles (H1-A: −0.117225,
  H1-B: −0.037941, plus v1's own reported ICs), taken in absolute
  value as concrete, non-fabricated anchors for "what real candidate
  hypotheses on this platform have actually produced." Using
  already-published archive figures as grid anchors — rather than
  inventing a plausibility range from unverified literature claims —
  keeps every number in this design traceable to something already
  committed to the repository.
- **A fine grid between 0 and the largest anchor** (e.g. steps of
  ~0.02–0.03) sufficient to fit a monotonic power curve and interpolate
  an MDE at a pre-registered power threshold (80%, the field-standard
  convention, fixed here before any simulation runs).
- **At least one point above the largest anchor** to confirm the curve
  saturates toward power ≈ 1 as expected (a sanity check on the
  generator and the pipeline both).

The exact numeric grid, replication count M per grid point, and RNG
seeding scheme are Methodology Freeze artifacts (Section 7), not
decided in this document — this section fixes the *design principle*
the frozen grid must satisfy, per Phase 2's role under the governance
standard (rank and justify the approach; the Phase 4 document fixes
the literal numbers).

**Replication count.** M must be justified by a stated target
precision, not chosen arbitrarily. For a power estimate treated as a
binomial proportion, `SE ≈ sqrt(p(1-p)/M)`; at p≈0.5 (the most
conservative case), M≈385 bounds the standard error at ≈2.5%, i.e. a
95% CI half-width of ≈5 points of power. The frozen methodology must
state its own chosen M against this formula explicitly, including
whether M varies by grid point (e.g., fewer replications far from the
MDE boundary, more near it, an adaptive design) — if adaptive, the
adaptation rule itself must be frozen in advance, not chosen after
seeing intermediate results.

### 5.4 Secondary grid — robustness across realistic parameter ranges (Objective 6)

Anchor case (must exactly match the real, already-committed cycles):
25-instrument universe, 463 overlapping ranking dates, 20-trading-day
horizon, permutation iterations = 10,000, bootstrap iterations = 2,000,
block lengths = (20, 40, 60), Holm-Bonferroni family size = 5 (matching
REFERENCE v1's own five simultaneously-tested statistics), α = 0.05 —
every one of these values read directly from
[`experiments/validate_reference_v1_significance.py`](../experiments/validate_reference_v1_significance.py),
not re-derived.

Dimensions swept one at a time from the anchor, holding the rest fixed:

| Dimension | Sweep values | What it answers |
|---|---|---|
| Panel length (overlapping dates) | 250 / 463 / 750 / 1250 | Directly quantifies the roadmap memo's open "historical depth" question (Section 6 of that memo) — how much would extending backfilled history actually improve power, in power points, not qualitatively |
| Universe size | 15 / 25 / 40 | Sensitivity to instrument count, relevant if the universe is ever expanded |
| Forward horizon | 10 / 20 / 40 trading days | Effective-N is a function of overlap; this quantifies the power/horizon trade-off directly, rather than treating 20 days as an unquestioned given |
| Family size (Holm-Bonferroni) | 1 / 5 / 8 | How much power is sacrificed to multiple-testing correction as future cycles test more simultaneous statistics — directly relevant to any future hypothesis testing more than one construct at once |
| Cross-sectional dependence strength | low / calibrated-to-archive / high | Sensitivity to the one generator assumption that cannot be verified with certainty (Section 6.2) |

Each secondary sweep uses a reduced replication count relative to the
primary grid (a disclosed, time-boxed governance exception — Section
7.4), sufficient to characterize direction and rough magnitude of the
effect rather than a publication-precision estimate; the anchor case
itself always uses the full, precision-justified M.

---

## 6. Statistical methodology

### 6.1 Per-replication procedure

For each (dimension point, ρ_true) grid cell, each of M replications:

1. Generate one synthetic panel (Type A, Section 5.2), seeded
   deterministically from a frozen seed-derivation scheme (e.g.
   `seed = base_seed + hash(dimension_point, rho_true, replication_index)`,
   the exact formula fixed at freeze).
2. Compute the panel-shaped dict contract (`etf_ids`, `forward_return`,
   `score`) exactly as `core/statistics/significance.py` expects it —
   no adaptation layer, no reshaping beyond what any real caller does.
3. Run the identical procedure `validate_reference_v1_significance.py`
   runs: `mean_ic` → `permutation_null` (10,000 iterations) →
   `empirical_p_value` → `holm_bonferroni` (across the frozen family
   size) → `bootstrap_ci` at block lengths 20/40/60 (2,000 iterations
   each).
4. Apply the **same promotion rule** v1/H1 used: Holm-corrected p <
   0.05 **and** bootstrap CI excludes zero at all three block lengths.
   Record boolean "detected."

### 6.2 Derived quantities

- **Power(dimension, ρ_true)** = fraction of M replications "detected."
- **False negative rate** = 1 − Power, at each ρ_true > 0.
- **Empirical Type I rate** = Power at ρ_true = 0; PC-H1's tolerance
  band (e.g. [0.03, 0.07] around nominal 0.05, exact band fixed at
  freeze) is evaluated here using a binomial confidence interval
  around the observed rate, not a point comparison.
- **Minimum detectable effect (MDE)** at a pre-registered power
  threshold (80%) = interpolated from a monotonic curve fit (e.g.
  isotonic or logistic regression) across the effect-size grid at the
  anchor dimension point. The interpolation method and the 80%
  threshold are both frozen before Validation, per Freeze Standard
  item 8's requirement to fix how ambiguous or interpolated results
  are resolved in advance.
- **Robustness surfaces** — power/MDE as a function of each secondary
  dimension (Section 5.4), reported as tables/plots, not collapsed to
  a single number.

### 6.3 The one unverifiable assumption, disclosed explicitly

The cross-sectional and autocorrelation structure used to generate
synthetic daily returns (Section 5.1) is *calibrated to*, but not
identical to, the real ETF universe's actual dependence structure.
Calibration draws only on already-published, already-archived
descriptive figures (e.g., the ~20–23 effective-window count already
stated in the roadmap memo, itself derived from committed v1/H1
results) — it does not perform any new read of real historical price
or return data, live or otherwise. This keeps the calibration
consistent with Phase 3's "no outcome data touched" rule (nothing new
is read; only already-frozen, already-public summary statistics are
reused as generator targets), but it means the calibration is only as
good as those summary figures' own representativeness. This is not
fully resolvable within this study; Section 5.4's dependence-strength
sweep is the mitigation (bound the sensitivity rather than assume
point-calibration is exact), and Section 12 restates this as a
residual limitation regardless of outcome.

### 6.4 Firewall against calibration leakage into future hypotheses

Because this study's dependence-structure calibration draws on
descriptive statistics from the same real ETF universe that a future
H2/H6/H5/etc. hypothesis cycle would also use, there is a specific,
non-obvious risk: if this study's calibration inputs were later reused
to inform *what effect size a future hypothesis should target or how
its construction should be tuned*, that would be exactly the
hindsight-bias failure mode
`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 1 exists to prevent,
laundered through a "methodology validation" study instead of a direct
parameter tune. **This study's outputs (power curves, MDE, calibration
parameters) may be cited by a future hypothesis cycle only to describe
what the pipeline can detect in general — never to select, size, or
justify that cycle's own effect-size expectation, lookback, or
promotion criteria.** This extends the "no parameter tuning of v1 (or
H1)" entry requirement from
[`docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` Section 4, item 3](REFERENCE_RESEARCH_ROADMAP_NEXT.md)
to cover this study as an additional prior. Recorded here as a binding
constraint on all future cycles, not merely a note to self.

---

## 7. Governance plan

### 7.1 Fit against the existing 8-phase lifecycle

The lifecycle in `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 2 was
written for hypothesis-driven factor research with real market outcome
data. This study has no real outcome data at all — its "outcome" is
simulation output from a frozen generator. The phases map, with one
adaptation flagged in Section 7.5 as a required governance addendum:

| Phase | This study's instance |
|---|---|
| 1. Hypothesis | Section 4 (PC-H1, PC-H2) — a methodological hypothesis about the pipeline, not a market mechanism |
| 2. Research Proposal | This document, including rejected alternatives (Section 5.2, 5.3) |
| 3. Pre-validation | Verify the Type A/B generators reproduce the target dependence structure and effective-N compression *without* touching new real data (Section 6.3) — analogous to signal-independence/data-adequacy gates, adapted to "generator fidelity" and "no-leakage" gates (Section 7.2) |
| 4. Methodology Freeze | The effect-size grid, dimension grid, seed scheme, M per cell, MDE threshold (80%), Type I tolerance band, and interpolation method — all fixed in `methodology.md` before any simulation runs |
| 5. Implementation | A new, isolated `experiments/validate_positive_control_power.py` (name illustrative), importing `core/statistics/significance.py` unmodified; no `core/` changes (Section 3) |
| 6. Validation | Run the frozen grid; this is the only phase where simulation *results* (power numbers) are observed |
| 7. Decision | PASS/FAIL/INCONCLUSIVE against the frozen criteria (Section 8) — a decision about the *pipeline's* calibration and power, not about any ETF strategy |
| 8. Archive | `research_archive/positive_control_v1/`, same evidence package structure as prior cycles (Section 10) |

### 7.2 Pre-validation gates (Phase 3, adapted)

Four gates, mirroring H3's own pre-validation gate structure but
retargeted at a synthetic study:

1. **Generator fidelity gate.** Demonstrate, on a small pilot run using
   only *already-frozen* calibration inputs, that Type A's realized
   effective independent-window count converges to the same ~20–23
   range already documented for the real panel at matching dimensions
   — the mechanical check that Section 5.1's design requirement is
   actually satisfied by the implementation, not merely intended.
2. **No-leakage gate.** Confirm, by code review, that no function in
   the synthetic generator reads any real market data table, live or
   historical — only pre-committed scalar summary statistics already
   published in archived closeout documents.
3. **Engine-reuse gate.** Confirm, by diff, that
   `core/statistics/significance.py` is unmodified from its pre-study
   commit, and that every statistic in this study is computed by
   direct import, not reimplementation.
4. **No-unresolved-degrees-of-freedom gate.** Every generator
   parameter not itself a swept dimension (Section 5.4) must have a
   stated justification traceable to an already-archived figure or a
   stated, non-outcome-dependent convention (e.g. the 80% power
   threshold) — no free parameter may be "whatever produces a clean
   result," the same discipline `REFERENCE_H3_PREVALIDATION_PLAN.md`
   already applies to construction choices.

### 7.3 Reviewer independence

Level 2 (AI-assisted adversarial review, session-separated) is
available and required at every gate this standard designates Level 2
minimum: Pre-validation gates, Methodology Freeze confirmation,
Implementation conformance. **Level 3 is not available on this
platform** — identical, disclosed gap to every prior cycle
(`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 4). The Decision
record (Phase 7) must state explicitly: "Level 3 review not available;
this Decision was made at Level 2 only," exactly as required for v1,
H1, and H3.

### 7.4 Governance exception needed for the study

Section 5.4's secondary grid uses reduced replication counts relative
to the anchor case for computational tractability. Per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 8, this requires a
documented exception in `decision_log.md` before Implementation:
documented reason (compute budget), impact assessment (secondary-grid
power estimates carry wider confidence intervals than the anchor
case's and are reported as directional/magnitude characterizations,
not precision estimates), approval record (Level 2 minimum, recorded
before Phase 5 begins), and an explicit scope limit (applies to the
secondary grid only, never to the anchor-case or MDE-boundary
replication counts, which must always use the fully precision-
justified M from Section 5.3).

### 7.5 Governance improvements needed before this study begins (Objective 8)

1. **A "Statistical Infrastructure Validation Study" cycle-type note.**
   The current 8-phase lifecycle implicitly assumes real market
   outcome data exists and is touched only at Phase 6. A fully
   synthetic study has no such data — its "dataset" is a generator
   plus an RNG seed set. Before Phase 3 opens, the platform needs a
   short addendum (either a new section in
   `docs/RESEARCH_GOVERNANCE_STANDARD.md` or a companion document it
   references) stating explicitly that for a synthetic-data cycle,
   `dataset_manifest.json` records the generator code's commit hash
   and the frozen seed-derivation scheme in place of a real data
   snapshot hash — otherwise Evidence Package Standard Section 5's
   `dataset_hashes/` requirement has no natural referent for this
   cycle, and a future reviewer would have to improvise an
   interpretation rather than follow a written rule.
2. **The calibration-leakage firewall (Section 6.4)** should be
   promoted from a note in this document to a standing addition to the
   "entry requirements for the next hypothesis" list currently in
   `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md` Section 4, so every future
   cycle — not just the next one — is bound by it without needing to
   have read this specific proposal.
3. **The reduced-replication exception pattern (Section 7.4)** is
   likely to recur for any future Monte Carlo-style study on this
   platform. Worth adding as a fourth worked example to
   `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 8 once this cycle's
   own exception record exists, so it is documented from a real
   instance rather than a hypothetical.

None of these three block Phase 1–2 (this document); all three should
be resolved before Phase 4 (Methodology Freeze) is committed, since
Freeze is where the dataset-manifest ambiguity in item 1 would
otherwise surface without a rule to follow.

---

## 8. Success / failure criteria

Decision applies to the **pipeline**, not to any ETF strategy — there
is no economic PASS/FAIL here.

**PASS** requires both:
- PC-H1 confirmed: empirical Type I rate at ρ_true = 0 falls within
  the frozen tolerance band around nominal α (0.05), at the anchor
  dimension point, with the binomial CI computed at the frozen M.
- PC-H2 answered with an MDE at 80% power, at the anchor dimension
  point, reported to the precision the frozen M supports — **regardless
  of whether that MDE is small or large relative to the archive-
  anchored effect sizes in Section 5.3.** A large MDE (i.e., the
  pipeline needs a bigger true effect than any of v1/H1/H3's own point
  estimates to reliably detect it) is a valid PASS outcome: it means
  the calibration question has been answered, even though the answer
  is "the instrument is underpowered for effects this small." See
  Section 9 for why this is still a resolution of the committee's
  concern.

**FAIL** applies only to PC-H1: if the empirical Type I rate is
significantly outside the frozen tolerance band (e.g. materially above
0.05), that indicates a genuine defect in how permutation testing,
Holm-Bonferroni correction, and block-bootstrap agreement combine —
not a property of ETF markets, a property of the validated pipeline
itself. This is the one outcome serious enough to require revisiting
every prior FAIL/INCONCLUSIVE verdict issued under that pipeline (v1,
H1, H3), since their false-positive control would then be in question.
This is explicitly flagged as a low-probability, high-consequence
outcome: each component (permutation testing, Holm-Bonferroni,
bootstrap) is a standard, individually well-understood construction: the
risk is in their combination via the "AND" promotion rule (Section
6.1, step 4), which conservatively pushes the actual family-wise error
rate below α, not above it, so a Type I inflation finding would be
genuinely surprising and would need independent confirmation before
being treated as established rather than acted on directly.

**INCONCLUSIVE** applies if the computational budget available cannot
resolve the MDE within the pre-registered precision target (Section
5.3) — a resource constraint, not a pipeline defect. Re-entry path per
Standard Section 7: reopen at Phase 3 with a revised, separately
logged compute-budget decision (more replications, a coarser grid, or
a narrower dimension sweep), never by relaxing the tolerance band or
precision target to make an underpowered simulation look conclusive.

---

## 9. Does this close the committee's highest-priority criticism?

**Yes — conditional on completing Phase 6–7 to a recorded Decision,
and regardless of which way that Decision comes out.**

The committee's finding was an absence of information: the platform
had never demonstrated detection capability in either direction. This
study is designed so that *both* possible substantive outcomes resolve
that absence:

- If PASS with a small MDE (the pipeline reliably detects effects at
  or below the magnitude v1/H1/H3 actually reported), the three prior
  "insufficient power" verdicts are now known to likely reflect a true
  absence of signal in those specific constructs, not an underpowered
  instrument — a materially stronger conclusion than any single prior
  cycle could support alone.
- If PASS with a large MDE (the pipeline needs a bigger effect than
  any prior cycle produced), the three prior verdicts are now known to
  be genuinely ambiguous for a *quantified, actionable* reason — with
  a specific number attached (the MDE) that a future decision to
  extend historical depth (roadmap memo Section 6) can be justified
  against directly, rather than by qualitative appeal.
- If FAIL (Type I inflation), that is itself the single most important
  finding this platform's research program could currently produce,
  since it would mean every past PASS/FAIL determination needs
  re-examination — arguably a more urgent resolution of the
  committee's underlying concern (can this pipeline be trusted at all)
  than a clean PASS would be.

What this study does **not** and cannot close: whether ETF markets
actually contain the specific mispricings v1, H1, or H3 hypothesized.
That is a question about markets, not about the instrument, and no
positive control — by construction — can answer it (Section 12).

On naming: **`positive_control_v1`** is recommended over
`synthetic_signal_validation_v1` or `statistical_power_calibration_v1`
because the study answers both a detection question (positive
control) and a calibration question (power) under one frozen
methodology, and "positive control" is the term that scopes the
*purpose* (does the instrument see something known to be there) rather
than either the *mechanism* (synthetic data) or one of its two outputs
(power) alone.

---

## 10. Reproducibility plan

- Every synthetic panel is generated from a documented, deterministic
  seed-derivation function (Section 6.1, step 1) — any reviewer with
  the frozen generator code and the frozen seed scheme can regenerate
  every panel and every result bit-for-bit.
- Raw Monte Carlo output (per-replication "detected" booleans, not
  only aggregated power numbers) is retained in
  `experiment_results/`, append-only, so power/MDE figures can be
  independently recomputed from the rawest available layer rather than
  trusted from a summary table.
- `dataset_manifest.json` (per Section 7.5, item 1) records the
  generator commit hash and seed scheme in place of a real-data hash.
- The Implementation-phase conformance note includes the literal diff
  output showing `core/statistics/significance.py` is byte-identical
  to its pre-study commit, making "the existing engine was reused
  unmodified" independently checkable rather than merely asserted.

---

## 11. Implementation roadmap (not yet authorized — Phase 3/4 must complete first)

1. Phase 3: generator-fidelity pilot run + three remaining pre-
   validation gates (Section 7.2), Level 2 reviewed.
2. Phase 4: `methodology.md` freeze — literal grid values, M per cell
   (with the precision-justification formula from Section 5.3 filled
   in), seed scheme, MDE threshold, Type I tolerance band, interpolation
   method. Committed; commit hash logged in `decision_log.md`.
3. Phase 5: `experiments/validate_positive_control_power.py`
   (illustrative name) — generator + grid runner, importing
   `core/statistics/significance.py` unmodified. Conformance note plus
   the byte-diff from Section 10.
4. Phase 6: run the frozen grid; produce `experiment_results/`.
5. Phase 7: Decision record — PASS/FAIL/INCONCLUSIVE per Section 8,
   Level 2 (Level 3 unavailable, disclosed per Section 7.3).
6. Phase 8: archive to `research_archive/positive_control_v1/`
   following the Section 5 evidence package structure exactly
   (`hypothesis.md`, `methodology.md`, `dataset_manifest.json`,
   `dataset_hashes/`, `experiment_results/`, `reviewer_reports/`,
   `decision_log.md`).

No step in this roadmap is authorized by this document alone — Phase 2
approval (this proposal being accepted) only opens Phase 3.

---

## 12. Remaining limitations after completion (stated regardless of outcome)

- **External validity is out of scope by design.** A well-calibrated,
  well-powered pipeline says nothing about whether MOMENTUM, VALUE,
  volatility-ranking, or relative-strength effects actually exist in
  real ETF markets. Positive controls validate instruments, not
  hypotheses under test with that instrument.
- **The dependence-structure calibration is not independently
  verifiable to certainty** (Section 6.3) — it is bounded by
  sensitivity analysis (Section 5.4), not eliminated.
- **A single universe/horizon combination is the anchor case.** The
  secondary grid (Section 5.4) characterizes sensitivity but does not
  exhaustively cover every combination a future hypothesis might use
  (e.g. a hypothesis requiring a 6-month horizon, per H6's own
  data-availability concerns in the roadmap memo's candidate table).
- **Level 3 review remains unavailable platform-wide.** This study
  inherits, not resolves, that standing organizational gap.
- **This study cannot retroactively strengthen v1/H1/H3's own
  archived Decisions.** Per the Standard's Archive discipline (Section
  2, Phase 8), those records are immutable; this study's findings can
  only inform *future* cycles' interpretation, recorded as new, dated
  cross-references — never as edits to the closed cycles' own files.

---

**This document is a Phase 2 artifact.** It requires committee approval
before Phase 3 (Pre-validation) may open. No implementation exists and
none should be written against this design until that approval is
recorded.
