# Positive Control Study — Phase 3 Pre-validation Pilot Results

**Status: Phase 3 (Pre-validation) pilot execution, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 Phase 3 and
`docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md` §1.6 / §2 / §2a.
This is NOT a Methodology Freeze. No `methodology.md` exists; none of
the values measured here are frozen. Governance status:
`Phase 3 Pre-validation completed (first pass) / Freeze decision
pending.`** No real market outcome data (forward-return-vs-score
alignment for any real ETF) was read, computed, or referenced anywhere
in producing this report — every input below is synthetic, generated
by the model in V2 §1.2.

---

## 1. Purpose of Phase 3

`docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md` §1.6 explicitly
names one action as "the one genuinely outstanding pre-Freeze action
this document identifies": the Phase 3 pilot run that (a) executes the
generator-fidelity gate (V2 §2) against the redesigned latent-path
model, and (b) produces the `w ↔ ρ_true` calibration lookup table.
Despite naming this as outstanding, V2's own §16 Recommendation
declared **READY FOR FREEZE** without that pilot having been run — a
direct violation of `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2's phase
ordering (Phase 3 must complete before Phase 4 opens). A Governance
Level 2 validation review of V2 caught this and returned **NOT READY
FOR FREEZE**.

This report is the first actual execution of that outstanding Phase 3
work: an honest attempt to run the fidelity gate and the calibration
procedure exactly as V2 specifies them, at the frozen anchor dimension
point, and to report what is actually found — not what the design
document predicted would be found.

## 2. Frozen methodology version used

- Design document: `docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md`,
  as corrected by this same change (committee-language and
  proven/empirical corrections — see that document's revision history).
  **Not yet committed at freeze-effective status** — per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §3, freeze requires a committed
  `methodology.md` and a `decision_log.md` entry recording its commit
  hash; neither exists yet. This pilot uses V2's §1.2/§1.6/§2/§2a
  procedures as a **working specification**, not a frozen one.
- Statistical primitives: `core/statistics/significance.py`
  (`rank_average_ties`, `pearson_correlation`, `daily_ic_series`,
  `mean_ic`), imported unmodified — no function in that module was
  edited, wrapped, or reimplemented.
- Runner: [`experiments/positive_control_phase3_pilot.py`](../../experiments/positive_control_phase3_pilot.py)
  (new script, this change).

## 3. RNG procedure

Per V2 §8's frozen scheme: every seed is derived via
`int.from_bytes(hashlib.sha256(seed_material.encode("utf-8")).digest()[:8], "big")`,
never Python's built-in `hash()`. `seed_material = "{base_seed}|{dimension_point_id}|{rho_true:.6f}|{stream_tag}|{replication_index}"`.

- `base_seed = 20260720` (literal, date-based, logged here).
- `stream_tag = "panel"` for every draw in this pilot — no permutation
  or bootstrap resampling is run in Phase 3 (that machinery uses the
  `"test"` stream, reserved for Phase 6), so `"test"` is unused here.
- **Disclosed deviation from the literal V2 §8 formula:** the formula's
  `rho_true` slot assumes `rho_true` is a known input. For the fidelity
  gate, `w = 0` is used (no injected signal), which is `ρ_true = 0` by
  construction, so `rho_true_for_seed = 0.0` is exact, not a
  substitution. For the calibration pilot, `ρ_true` is the *output*
  being measured, not a known input — the calibration's own `w` value
  occupies the formula's `rho_true` slot instead, distinguished by a
  separate `dimension_point_id` (`phase3_calibration_...` vs.
  `phase3_fidelity_anchor_...`) so no seed can collide between the two
  procedures or between different `w` values. This is a literal,
  disclosed convention, not a silent change to the frozen scheme; it
  should be written into `methodology.md` verbatim if/when this
  procedure is frozen.
- Full seed list (25 fidelity-gate seeds) is recorded in
  `generator_fidelity_results.json`; each calibration grid point's
  first/last of 50 seeds is recorded in `rho_calibration.csv`.

## 4. Parameter values (anchor dimension point, V2 §9)

| Parameter | Value |
|---|---|
| Universe (instruments) | 25 synthetic |
| Dates | 463 |
| Forecast horizon `h` | 20 |
| `L_score` | 20 (`= h`, V2 §1.5) |
| `β` (cross-sectional correlation) | 0.30 |
| `α` | 0.05 (not exercised in this pilot — no hypothesis test is run; recorded for completeness against the task's frozen-parameter list) |
| Permutation iterations | 10,000 (frozen for Phase 6; **not run** in this pilot — no permutation test is part of the fidelity gate or the calibration procedure) |
| Bootstrap iterations | 2,000 (frozen for Phase 6; **not run** in this pilot, same reason) |

## 5. Executed gates and results

### 5a. Fidelity Tolerance Procedure (Task 3 — frozen before any result was observed)

Written in full in `docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md`
new §2a; reproduced in summary:

- **Confidence level:** 95%, two-sided (`z_0.975 = 1.959964`, matching
  `bootstrap_ci`'s existing convention).
- **Estimator:** mean pooled sample autocorrelation at lag `k`, across
  `R` independent pilot replications; `SE(k) = stdev_r(ACF_hat_r(k)) / sqrt(R)`.
- **Deviation metric:** `ACF_hat(k) − ACF_target(k)` (gates 1–2, closed
  form `max(0, 1 − k/h)`); `|ACF_hat(k)|` against zero for `k ≥ h`
  (gate 3, structural decay check, no closed form — per V2 §2 item 3).
- **Pass condition:** `|deviation| ≤ z_0.975 · SE(k)`.
- **Pilot size `R`, derived (not chosen after seeing results):**
  conservative Fisher bound `SD ≈ 1/√(n_min)`, `n_min = 463 − 60 = 403`
  (smallest pooled-pair count across the full lag range checked, `k`
  up to 60), target `SE ≤ 0.01` (half the frozen `0.02` effect-size
  grid spacing, V2 §9) → `R ≥ (0.0498/0.01)² ≈ 24.8` → **R = 25**,
  executed in full at this size (no reduction).
- **Calibration pilot size `P`, derived, same method:** `SD ≈ 1/√(N_eff − 1)`,
  `N_eff ≈ T/h ≈ 23` (this platform's own established effective sample
  size, V2 §1.3) → `P ≥ (0.2132/0.01)² ≈ 454.6` → **P = 500** required
  for the full-precision calibration. **This pilot executed a reduced,
  explicitly preliminary pass: 11 of the frozen 41 `w` grid points, at
  `P_pilot = 50` of the required 500 replications each** — see §7
  Limitations for why, and for what remains before this procedure can
  be considered complete.

### 5b. Generator-fidelity gate — anchor dimension point (25 × 463, h=20, β=0.30, w=0), R=25

Full machine-readable output:
[`generator_fidelity_results.json`](generator_fidelity_results.json).

| Gate | Result | Detail |
|---|---|---|
| Gate 1 — return-side ACF | **PASS** | All 20 lags within tolerance of the closed-form Bartlett(20) target. Largest deviation: lag 20, −0.0124 (tolerance ±0.0212). Confirms the *proven* property (§1.2/§1.3 of V2, as corrected): `forward_return` is an exact `h`-period moving sum of an i.i.d. series and its ACF is mechanically Bartlett-shaped. |
| Gate 2 — score-side ACF | **FAIL** | Lags 1–16 of 20 fall outside tolerance, systematically **below** the Bartlett(20) target (deviations from −0.022 to −0.038, roughly 5–15× the tolerance band at those lags). Lags 17–20 pass. |
| Gate 3 — combined daily-IC-series ACF decay by lag `h` | **FAIL** | Lags 20–43 and 52–60 pass (indistinguishable from zero within tolerance); **lags 44–51 fail** (deviations −0.045 to −0.060, exceeding the ≈0.05 tolerance band at those lags by a small margin) — a mild negative excursion past the expected decay-to-zero point, not a large or one-directional failure. |
| **Overall** | **FAIL** | Two of three checks fail at the anchor point. |

**What Gate 2's failure means.** V2 §1.3 (pre-correction) asserted that
`score`, as a rank-space blend of two Bartlett(h)-shaped series,
"inherits" the same closed-form ACF — stated as a structural
consequence of linear-combination algebra. That algebra is valid for
*linear* combinations of the raw series. `score` is built from
**cross-sectional ranks** of `forward_return` and `sma`, not from the
raw values — a nonlinear, per-day transform. This pilot's own data
shows the two are not interchangeable: the rank-transformed score's
empirical ACF decays measurably faster than the linear Bartlett(h)
target at short-to-medium lags. This is exactly the gap the corrected
§1.3 (this same change) now labels **EMPIRICAL, not PROVEN** — and the
gate built specifically to check it (§2 item 2) has, on its first
actual execution, found the empirical claim does not hold at this
pilot's precision. This is a real, structural finding about the
generator design, not a documentation issue.

**What Gate 3's failure means.** The dip at lags 44–51 is a real
measured signal, not obviously noise: it is one-directional
(consistently negative) across an 8-lag run, and R=25 already yields
tolerance bands (~0.04–0.05) narrower than the observed deviation at
its worst point (lag 49, −0.0605 vs. tolerance ±0.0483). It is also
not large or persistent — the series returns inside tolerance from lag
52 onward. Two explanations are plausible and not yet distinguished:
(a) a genuine higher-order dependence in the daily-IC series beyond
what a single window length `h` bounds (the gate's own designed
question), possibly connected to Gate 2's rank-transform effect, or
(b) Monte Carlo noise from R=25 being adequate for the ≤lag-20 checks
(large per-lag signal-to-tolerance ratio there) but marginal at
lags 44–51 where the per-replication standard deviation of the IC-ACF
is much larger (~0.10–0.13 vs. ~0.005–0.05 in gates 1–2). Distinguishing
these requires more replications at this specific lag range — not yet
run.

### 5c. `w ↔ ρ_true` calibration — reduced preliminary pilot (11 of 41 points, 50 of 500 replications)

Full data: [`rho_calibration.csv`](rho_calibration.csv).

| `w` | `ρ_true` measured (mean) | SE (this pilot, n=50) |
|---|---|---|
| 0.0 | −0.0027 | 0.0042 |
| 0.1 | 0.0603 | 0.0048 |
| 0.2 | 0.1590 | 0.0052 |
| 0.3 | 0.2509 | 0.0041 |
| 0.4 | 0.3517 | 0.0037 |
| 0.5 | 0.4550 | 0.0031 |
| 0.6 | 0.5592 | 0.0027 |
| 0.7 | 0.6655 | 0.0019 |
| 0.8 | 0.7971 | 0.0009 |
| 0.9 | 0.9042 | 0.0004 |
| 1.0 | 1.0000 | 0.0000 |

Sanity checks pass: `w=0` gives `ρ̂ ≈ 0` (consistent with the *proven*
disjoint-time-support independence property, §1.2), the curve is
monotone increasing, and `w=1` gives exactly `ρ̂ = 1.0` (score equals
`rank(forward_return)` exactly at `w=1`, so a perfect rank correlation
is mechanically guaranteed, not merely expected). The curve is visibly
nonlinear (concave then convex), confirming V2 §1.6's statement that no
simple closed form exists for the `w ↔ ρ_true` relationship — an
isotonic fit is genuinely needed, not a formality. **No isotonic fit or
lookup-table inversion was performed in this pilot** — out of scope
until the full 41-point, `P=500` run exists; fitting an 11-point,
`P=50` curve and calling it the frozen lookup table would misrepresent
its precision.

## 6. Reviewer level

**Level 1 (self-review) only, for this entire report and the code that
produced it.** No Level 2 (AI-assisted adversarial, procedurally
independent) review of this pilot's code, its numerical output, or this
report's own claims has been obtained. Per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4, Level 1 is never sufficient,
alone, to satisfy a Pre-validation gate — this report does not claim
Gate 2 or Gate 3's FAIL results, or any other figure here, has cleared
Phase 3's required review bar. It is disclosed as Level 1 evidence,
not represented as anything higher. No Level 3 (organizationally
independent) review exists or is available on this platform, per the
Standard §4's standing disclosure.

## 7. Limitations

- **Gates 2 and 3 FAIL at the anchor point, at this pilot's precision.**
  This is the headline finding, not a limitation to caveat away: V2's
  redesigned generator, on its first actual execution, does not fully
  match its own design document's claims. Whether this is fixable by a
  generator redesign (e.g., a different score construction that
  preserves ACF shape under rank transformation), an acceptance of a
  measured-not-assumed score ACF target, or a re-scoped fidelity gate is
  an open design question this report does not resolve — resolving it
  is Phase 3 work still to be done, not Phase 4 work.
- **The horizon-sweep spot checks (h=10/20/40, V2 §2) were not run** —
  only the anchor `h=20` point. The gate's own spec requires all three;
  this pilot covers one of three.
- **The calibration pilot ran at ~2% of the derived required scale**
  (11 of 41 `w` points; 50 of 500 replications per point). The `P=500`
  derivation itself (§5a) is a closed-form, precision-driven number,
  not a guess, but this report does not claim to have met it. Running
  it at full scale in pure Python is expected to take materially longer
  than this reduced pass (roughly 10× the points × 10× the replications
  ≈ two orders of magnitude more panel generations); it was not run in
  this first pass and remains required before §1.6's lookup table can
  be frozen.
- **No isotonic-fit inversion was performed** — see §5c.
- **Gate 3's lags 44–51 dip is not yet explained**, only measured and
  flagged (§5b). Whether it reflects a real generator property requiring
  a design change, or is a Monte Carlo artifact of R=25 at that specific
  lag range, is unresolved.
- **§11's three governance-document edits** (drafted in V2 §11, targeting
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` and
  `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`) remain unapplied.
- **This report and its underlying code are uncommitted** at the time of
  writing — no commit hash exists yet for
  `experiments/positive_control_phase3_pilot.py` or any file in this
  directory. Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §3's own
  standard ("a document's own claim to be frozen is not freeze
  evidence"), nothing here should be cited as having committed
  provenance until it is committed.
- **No real market data was used or needed** — this entire report, and
  every number in it, is a property of the synthetic generator and the
  statistical primitives it was checked against, not of ETF markets.

## 8. Governance status

**Phase 3 Pre-validation completed (first pass) / Freeze decision
pending.** This is explicitly **not** "Methodology Freeze achieved" and
**not** "READY FOR FREEZE." Per `docs/RESEARCH_GOVERNANCE_STANDARD.md`
§2, Phase 4 (Methodology Freeze) may not open while Phase 3 gates the
freeze is meant to depend on (the fidelity gate) are failing at the
dimension point the freeze would apply to. See `decision_log.md` in
this directory for the formal decision-log entries, and
`docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md` §16 for the
corrected Recommendation and the full remaining-blocker list.
