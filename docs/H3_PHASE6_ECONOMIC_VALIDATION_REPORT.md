# H3 Phase 6 — Economic Validation Report

**Role.** Institutional Quant Research Validation Engineer — execution
and evidence generation only. This report does not develop, tune, or
modify H3's construction, and does not modify the pre-registered
acceptance criteria. Every design choice below is either a mechanical
implementation of the two frozen documents cited in Section 2, or an
explicitly disclosed reporting-only construction (Section 4.4) that
does not affect any pass/fail figure.

---

## 1. Executive Summary

**Status: UNSUPPORTED.**

More specifically, this is not a bare non-result: the frozen decision
table (Acceptance Criteria §5) resolves this cycle to **EVIDENCE
AGAINST** the hypothesis, its strongest form of non-support. At the
pre-registered primary 60-trading-day horizon:

- **H3-A** (score autocorrelation, the primary statistic): point
  estimate +0.0499, correct sign, Holm-Bonferroni-adjusted p = 0.0000
  (highly significant by permutation), but its block-bootstrap
  confidence interval **includes zero at all three required block
  lengths** — it does not clear the frozen "passes" bar (Acceptance
  Criteria §4.2).
- **H3-B** (top-5 vs. bottom-5 portfolio spread, the secondary
  statistic): point estimate **−0.0057** — the **wrong sign**: ETFs
  ranked in H3's *bottom* 5 outperformed ETFs ranked in H3's *top* 5
  over the following 60 trading days, on average. This is
  Holm-Bonferroni-adjusted significant (p = 0.0251), which under
  Acceptance Criteria §5.2 item 2 makes this a **significant reversal**
  — recorded as evidence against the mechanism, not a milder finding.

Per Acceptance Criteria §5.3, this triggers the platform's
terminal-failure discipline: research under H3's exact frozen
construction stops now, with no tuning permitted to convert this into
a PASS.

---

## 2. Freeze Verification

| Item | Value | Verification performed |
|---|---|---|
| Methodology freeze commit | `07f0da379d8cccf06d17c34a51cbb557da047fef` (short: `07f0da3`) | `git cat-file -t 07f0da3...` → `commit`; `git rev-parse 07f0da3` → resolves to the full hash exactly. Commit message: "docs(governance): freeze REFERENCE H3 construction Attempt 1 and pre-validation governance record." |
| Acceptance criteria freeze commit | `a6439934882d5ad2c08ce8dba597810ac99e69f9` (short: `a643993`) | `git cat-file -t a643993...` → `commit`; `git rev-parse a643993` → resolves to the full hash exactly, matching the task-supplied hash character-for-character. Commit message: "Freeze H3 acceptance criteria before validation." |
| Working tree state at execution time | Clean, `HEAD` several commits ahead of both freezes, on `master` | `git status` (clean) and `git log --oneline` before any script was written. |
| No outcome data used prior to this cycle | Confirmed | `docs/H3_ACCEPTANCE_CRITERIA.md` §0's own preamble states no forward return, IC, p-value, Sharpe ratio, or drawdown figure for H3 existed anywhere in the archive at the time that document was written, and this is the first script anywhere in `experiments/` that reads a forward-shifted H3 score or a forward return alongside it — confirmed by inspecting every existing H3-related script (`validate_h3_gate1_independence.py` is same-date-only, by its own docstring and by re-reading it in full). |
| Reproducibility of validation inputs | Confirmed | `PriceBar` data (25 ETFs, 2016-09-13 to 2026-07-17, 61,850 rows) is the same table Gate 1 read and independently reproduced (`docs/H3_GATE1_REPRODUCTION_REVIEW.md` §2); no new data source was introduced. |

No mismatch found on any of the four required pre-execution checks.

---

## 3. Data and Implementation

**Dataset.** `PriceBar` close-to-close prices, `experiments_etf_universe.db`, 25-ETF REFERENCE universe (`experiments/daily_etf_universe_update.py:89-120`), full history 2016-09-13 to 2026-07-17 (used for trailing 60-day score construction reaching back before the evaluation window).

**Evaluation window (Acceptance Criteria §2.2, reused unmodified from Gate 1):** 2024-08-13 to 2026-07-17 — 483 nominal ranking dates.

**Script.** [`experiments/validate_h3_phase6_economic_validation.py`](../experiments/validate_h3_phase6_economic_validation.py), executed via `python -c "from experiments.validate_h3_phase6_economic_validation import run; raise SystemExit(run())"`.

**Calculations performed, in order:**

1. **H3 score** — imported unchanged from `experiments/validate_h3_gate1_independence.compute_h3_scores()` (same function already reviewed at Gate 1 and independently reproduced in `docs/H3_GATE1_REPRODUCTION_REVIEW.md`): `H3_score_i(t) = own_return_i(t) − peer_return_i(t)`, 60-trading-day trailing log return, six frozen peer segments, missing-data exclusion per `attempt_001_specification.md` §3.9.
2. **H3-A panel** — for each window date `t` and each horizon `h ∈ {60, 20}`, forward-shifted `H3_score_i(t+h)` looked up against `H3_score_i(t)`; a date is mechanically dropped if `t+h` falls outside the trading calendar (Acceptance Criteria §2.2). Minimum panel size 10 (Acceptance Criteria §3.3), enforced by `build_statistic_view()` (imported unchanged from `experiments/validate_reference_v2_h1_significance.py`).
3. **H3-B panel** — forward *raw* return per ETF at the same horizons, via `forward_return()` (imported unchanged from `experiments/validate_scoring_signal.py`, simple `(end/start) − 1`), narrowed the same way.
4. **Statistics** — `mean_ic()` (daily Spearman between `H3_score(t)` and its forward-shifted counterpart, averaged across dates, never pooled) for H3-A; `top_bottom_spread()` (bucket size 5) for H3-B — both imported unchanged from `experiments/validate_reference_v1_significance.py`.
5. **Inference** — `permutation_null()` (10,000 within-date shuffles, independent per statistic), `empirical_p_value()`, `holm_bonferroni()` (jointly across exactly {H3-A, H3-B} at the 60-day horizon, n=2), `bootstrap_ci()` (2,000 iterations, contiguous whole-date blocks at 20/40/60 days) — all imported unchanged from `validate_reference_v1_significance.py`.
6. **Global-equity-segment sensitivity** (Acceptance Criteria §3.3) — the same H3-A/H3-B point estimates recomputed with `VT`/`ACWI` excluded from every date's cross-section.
7. **Descriptive risk reporting** (Acceptance Criteria §3.1/3.2) — realized drawdown and annualized volatility of the H3-B long leg, short leg, and spread, built from **non-overlapping** 60-trading-day periods (a disclosed reporting-only construction, not part of the frozen criteria — see the script's module docstring — chosen because compounding the overlapping 60-day-forward series used for the point-estimate statistics would double-count the same underlying days).

**Reproducibility.** Single fixed seed `2026071901` (documented in the script before this run, distinct from REFERENCE v1's `20260718` and REFERENCE v2 H1's `2026071801`), one `random.Random` instance for the whole run.

**Runtime.** 483 window dates × 2 horizons × 2 statistics × (10,000 permutations + 3×2,000 bootstrap resamples) — approximately 82 minutes wall-clock on this machine.

**Machine-readable evidence:** [`research_archive/reference_h3/phase6_economic_validation_2026-07-19.json`](../research_archive/reference_h3/phase6_economic_validation_2026-07-19.json).

---

## 4. Results

### 4.1 H3-A — score autocorrelation (primary statistic)

| Horizon | n dates | Observed (mean daily Spearman IC) | Raw p | Holm-adj. p | Bootstrap CI (20d) | Bootstrap CI (40d) | Bootstrap CI (60d) | Robust across all 3 blocks | Correct sign |
|---|---|---|---|---|---|---|---|---|---|
| **60d (primary)** | 423 | **+0.04986** | 0.0000 | 0.0000 | [−0.0418, 0.1352] | [−0.0543, 0.1390] | [−0.0492, 0.1376] | **No** | Yes |
| 20d (diagnostic) | 463 | +0.63434 | 0.0000 | (excluded from correction) | [0.5738, 0.6914] | [0.5734, 0.6943] | [0.5808, 0.6906] | Yes (not decision-relevant) | Yes |

### 4.2 H3-B — top-5/bottom-5 portfolio spread (secondary statistic)

| Horizon | n dates | Observed (mean 60d forward return spread) | Raw p | Holm-adj. p | Bootstrap CI (20d) | Bootstrap CI (40d) | Bootstrap CI (60d) | Robust across all 3 blocks | Correct sign |
|---|---|---|---|---|---|---|---|---|---|
| **60d (primary)** | 423 | **−0.00573** | 0.0251 | 0.0251 | [−0.0320, 0.0186] | [−0.0366, 0.0219] | [−0.0334, 0.0226] | **No** | **No** |
| 20d (diagnostic) | 463 | +0.00947 | 0.0000 | (excluded from correction) | [−0.0030, 0.0221] | [−0.0023, 0.0216] | [−0.0012, 0.0207] | No (not decision-relevant) | Yes |

Both 60-day statistics fail the compound "passes" bar (Acceptance Criteria §4.2: adjusted p < 0.05 **and** CI excludes zero at all three block lengths). H3-B additionally has the wrong sign at the primary horizon.

### 4.3 Global-equity-segment sensitivity (Acceptance Criteria §3.3, disclosure only)

| Statistic (60d) | Full 25-ETF universe | Excluding `VT`/`ACWI` (23 ETFs) |
|---|---|---|
| H3-A observed | +0.04986 | +0.04262 |
| H3-B observed | −0.00573 | −0.00573 (bit-identical) |

H3-A shifts modestly downward with Global-equity excluded; H3-B is unaffected to full floating-point precision, indicating `VT`/`ACWI` essentially never occupy a top-5/bottom-5 extreme position across the 423 evaluated dates. Neither result is disproportionately carried by the disclosed 2-member segment.

### 4.4 H3-B descriptive risk report (Acceptance Criteria §3.1/3.2, reporting only, no threshold)

Non-overlapping 60-trading-day periods (n = 8, consistent with the ≈8 independent windows already disclosed as this platform's effective sample size at this horizon, Acceptance Criteria §2.2):

| Leg | n periods | Max drawdown | Annualized volatility | Cumulative return |
|---|---|---|---|---|
| Long (top-5) | 8 | 6.89% | 10.76% | +39.01% |
| Short (bottom-5) | 8 | 8.66% | 16.58% | +40.54% |
| Spread (long − short) | 8 | 11.37% | 14.72% | **−4.12%** |

The spread's negative cumulative return over the 8 non-overlapping periods is directionally consistent with H3-B's negative 60-day point estimate above; the short leg slightly outearned the long leg over the full window.

---

## 5. Acceptance Criteria Evaluation

| Criterion (Acceptance Criteria section) | Verdict | Note |
|---|---|---|
| Statistical significance, H3-A 60d (§2.3 statistical bar / §4.1) | PASS | Adjusted p = 0.0000 |
| Statistical significance, H3-B 60d (§2.3 statistical bar / §4.1) | PASS | Adjusted p = 0.0251 |
| Bootstrap-CI-excludes-zero at all 3 blocks, H3-A 60d (§4.2) | **FAIL** | Includes zero at 20/40/60d blocks |
| Bootstrap-CI-excludes-zero at all 3 blocks, H3-B 60d (§4.2) | **FAIL** | Includes zero at 20/40/60d blocks |
| Compound "passes" bar, H3-A 60d (§4.2) | **FAIL** | Significance alone insufficient; CI rule not met |
| Compound "passes" bar, H3-B 60d (§4.2) | **FAIL** | Significance alone insufficient; CI rule not met; also wrong sign |
| Correct-sign gross economic bar, H3-B 60d (§2.3) | **FAIL** | Point estimate negative — opposite the hypothesis's predicted direction |
| Net-of-implementation-cost minimum excess return (§2.3, §3.3, §7 item 1) | NOT TESTABLE | Pre-registered as unresolved; no cost/turnover/capacity model exists on this platform |
| Maximum-drawdown acceptance threshold (§3.1, §7 item 2) | NOT TESTABLE | Pre-registered as unresolved (no numeric ceiling); reporting requirement itself: PASS (§4.4 above) |
| Volatility ceiling (§3.2, §7 item 3) | NOT TESTABLE | Pre-registered as unresolved; reporting requirement itself: PASS (§4.4 above) |
| Minimum panel size / missing-data handling (§3.3) | PASS | Enforced mechanically via `build_statistic_view()`; 423/423 (60d) and 463/463 (20d) evaluated dates cleared the 10-ETF floor |
| Global-equity-segment disclosure (§3.3) | PASS | Computed and disclosed with/without (§4.3 above) |
| Gross-vs-net-of-cost disclosure requirement (§3.3) | PASS | Stated explicitly here: this is a gross-of-cost, research-only result |
| Reviewer-independence-level disclosure requirement (§3.3) | PASS | Stated explicitly here: at most Level 2 (procedurally independent, not organizationally independent); no Level 3 review exists on this platform for any cycle |
| Multiple-testing correction, exactly {H3-A, H3-B} family, 60d only (§4.3) | PASS | Holm-Bonferroni applied with n=2; 20d diagnostics correctly excluded from the family |
| Fixed, documented seed (§4.4) | PASS | `2026071901`, fixed before execution |
| Undefined-statistic auto-fail rule (§4.4) | PASS (not triggered) | No permutation p-value or bootstrap CI was undefined at any required block length |
| Decision table application (§5.1) | Resolved to row 4 equivalent (both fail) | See §5.2 below — elevated, not softened |
| Terminal failure — significant reversal (§5.2 item 2) | **TRIGGERED** | H3-B is Holm-Bonferroni significant (p=0.0251) in the direction opposite the hypothesis's prediction |

---

## 6. Limitations

- **Net-of-cost gap (unresolved, pre-registered).** This result is gross-of-cost only. No transaction-cost, turnover, borrowing-cost, or capacity model exists anywhere on this platform. Given the finding is EVIDENCE_AGAINST rather than a borderline PASS, this gap is not the reason the cycle failed — but it means even a hypothetical PASS would not have been an investability conclusion.
- **Single ~2-year, single-regime history.** All ≈8 independent 60-day windows come from one historical regime (2024-08 to 2026-07). No claim here generalizes to a different regime, and the descriptive drawdown/volatility figures in §4.4 rest on only 8 data points each — too few to characterize a return distribution, reported for disclosure only, not as a robustness claim.
- **Small effective sample size drives an internal tension worth flagging explicitly.** H3-A's permutation p-value is essentially zero (0/10,000 shuffles as extreme) while its block-bootstrap CI is wide and includes zero. This is not a contradiction or a bug: the permutation test's null treats each of 423 within-date shuffles as informative, while the block bootstrap correctly accounts for date-to-date autocorrelation at only ≈7 independent 60-day blocks — exactly the effective-sample-size problem the Acceptance Criteria's §2.2 pre-registered as a risk before any result existed. The frozen decision rule (§4.2, "ambiguity resolves to the stricter reading") is why H3-A does not pass despite the strong permutation significance.
- **20-day diagnostic figures are structurally inflated and not informative on their own.** H3-A's 20-day IC (+0.634) is very large because the score's own 60-day trailing window at `t` and at `t+20` share 40 of 60 underlying days — a mechanical overlap effect, not evidence of 20-day economic persistence. This is exactly why Acceptance Criteria §2.1 designated 60 days (where the trailing windows are contiguous and non-overlapping) as the only horizon that governs the decision, and excluded the 20-day figures from the decision rule entirely. They are reported here for cross-hypothesis comparability only, per that section.
- **Global-equity segment (`VT`, `ACWI`).** Confirmed, per §4.3, not to be a disproportionate driver of either result at this horizon — but this is one disclosure among several structural weak points named in the frozen construction (§3.10), not an exhaustive robustness check.
- **No Level 3 (organizationally independent) review exists for this result**, consistent with every prior cycle on this platform.
- **This report and the script that produced it have not yet received any independent review** (Level 1 self-review only, at the point of writing). Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4 and the evidence-package requirements in §5, a Level 2 (or above) review should be obtained before this record is treated as governance-final, consistent with the practice already followed for Gates 1–4 of this same cycle.

---

## 7. Final Determination

**Does the evidence support H3?** No. At the pre-registered primary horizon, H3-A (the direct test of the hypothesis's literal claim — persistence of relative standing) does not clear the frozen bootstrap-robustness bar despite a highly significant permutation p-value, and H3-B (the portfolio-spread diagnostic) is significantly **reversed** — bottom-ranked ETFs outperformed top-ranked ETFs over the following 60 trading days, the opposite of what the hypothesis predicts. Per Acceptance Criteria §5.2 item 2, a significant reversal is not treated as a milder finding than FAIL; it is recorded as **evidence against** the mechanism.

**Is further research under this exact frozen construction justified?** No. Per Acceptance Criteria §5.3 and `docs/RESEARCH_GOVERNANCE_STANDARD.md` §7's FAIL terminal-failure discipline (which this determination inherits in full, being at least as strong as a plain FAIL):

1. Research under H3's exact frozen construction (`attempt_001_specification.md` Attempt 1) stops immediately, other than Phase 8 archive steps.
2. No lookback, segment boundary, benchmark, peer-averaging method, bucket size, holding horizon, or any other frozen parameter may be adjusted on this result to attempt to convert it into a PASS. Any such change is a new construction attempt or a new cycle, not a correction.
3. No alternative evaluation period or date subset may be substituted in search of a window where this construction would have passed.
4. No criterion in `docs/H3_ACCEPTANCE_CRITERIA.md` may be relaxed or reinterpreted after seeing this result, including the bootstrap-CI rule that determined the outcome.
5. A future hypothesis touching relative-strength or rotation-style ideas is only legitimate as a wholly new cycle from Phase 1 that explicitly engages with this archived evidence and states, in writing, why it is a genuinely different hypothesis — not a renamed or restarted H3 attempt.

**Decision record (Acceptance Criteria §8 template, completed):**

- **Determination:** ☒ Evidence against (reversal)
- **Determination date:** 2026-07-19
- **Reviewer(s) and independence level:** AI research assistant (Claude), Level 1 (self-review) at the point of writing this report — no independent Level 2 confirmation has yet been obtained for this specific document (distinct from, and later than, the Level 2 reviews already completed for Gates 1–4 of this cycle).
- **Freeze commit of acceptance criteria in effect:** `a6439934882d5ad2c08ce8dba597810ac99e69f9`
- **H3-A result (60d primary):** point estimate +0.04986, Holm-Bonferroni adjusted p = 0.0000, bootstrap CI (20/40/60d): [−0.0418, 0.1352] / [−0.0543, 0.1390] / [−0.0492, 0.1376] — none exclude zero
- **H3-B result (60d primary):** point estimate −0.00573, Holm-Bonferroni adjusted p = 0.0251, bootstrap CI (20/40/60d): [−0.0320, 0.0186] / [−0.0366, 0.0219] / [−0.0334, 0.0226] — none exclude zero
- **Diagnostic-only 20d results (not decision-relevant):** H3-A +0.634 (structurally inflated by trailing-window overlap, §6); H3-B +0.00947
- **Global-equity-segment sensitivity:** H3-A shifts +0.0499 → +0.0426 without `VT`/`ACWI`; H3-B unchanged (§4.3)
- **Gross-vs-net-of-cost disclosure:** This is a gross-of-cost, research-only conclusion. No transaction-cost, turnover, borrowing-cost, or capacity model exists on this platform (§6). Moot for this determination, since the outcome is evidence against, not a PASS.
- **Synthesis rationale:** H3's primary statistic shows a small, permutation-significant, correctly-signed autocorrelation that nonetheless fails the pre-registered bootstrap-robustness requirement once date-to-date autocorrelation is properly accounted for — a direct manifestation of the ≈8-independent-window effective sample size problem disclosed before this result was ever computed. More importantly, the secondary portfolio-spread diagnostic — the statistic closest to an implementable test of the hypothesis — is significantly reversed: ETFs H3 ranks as recent relative laggards outperformed ETFs H3 ranks as recent relative leaders over the next quarter. Taken together, this is not an ambiguous or underpowered result that would justify INCONCLUSIVE; it is a specific, pre-registered failure mode (§5.2 item 2) that this platform's own governance standard requires to be recorded as evidence against the mechanism, with the same terminal-failure discipline as FAIL.
