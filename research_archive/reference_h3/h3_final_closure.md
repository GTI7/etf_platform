# H3 — Final Closure Record

**Role.** Institutional Quant Research Archival Reviewer. This record
performs no new analysis, re-review, or reinterpretation of H3's
evidence. It consolidates, into a single terminal document, the
determination already reached and recorded elsewhere in this archive,
and states in one place that H3 is permanently closed under its frozen
specification.

---

## 1. Hypothesis identifier

**H3** — ETF relative-strength / segment-rotation. An ETF's relative
standing versus its own peer market segment persists in the near term,
because capital reallocates *between* market segments at a slower,
governance-bound cadence than security-specific information is
absorbed. Full statement, mechanism, and falsification criteria:
`attempt_001_specification.md` §1–2;
`docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`.

- **H3-A** (primary): daily cross-sectional Spearman autocorrelation of
  the H3 score, `H3_score_i(t)` vs. `H3_score_i(t+60)`.
- **H3-B** (secondary/diagnostic): top-5 vs. bottom-5 H3-ranked
  portfolio spread in forward 60-trading-day raw return.

## 2. Frozen methodology commit

**`07f0da379d8cccf06d17c34a51cbb557da047fef`** (short: `07f0da3`) —
"docs(governance): freeze REFERENCE H3 construction Attempt 1 and
pre-validation governance record." Fixes the 25-ETF universe, six
peer segments, score formula, 60-day lookback, ranking convention, and
missing-data handling. Provenance: `FREEZE_RECORD.md`, `COMMIT.txt`.

## 3. Acceptance criteria freeze commit

**`a6439934882d5ad2c08ce8dba597810ac99e69f9`** (short: `a643993`) —
"Freeze H3 acceptance criteria before validation." Fixes the dual
holding horizon (60d primary / 20d diagnostic), bucket size 5, minimum
panel size 10, statistical machinery (permutation, block bootstrap,
Holm-Bonferroni), the compound "passes" bar, and the significant-
reversal decision rule (§5.2 item 2). Provenance:
`ACCEPTANCE_CRITERIA_FREEZE.md`. Three items were left explicitly
unresolved rather than invented: net-of-cost minimum excess return,
maximum-drawdown threshold, volatility ceiling (§7).

## 4. Validation evidence

- **Script:** `experiments/validate_h3_phase6_economic_validation.py`
  — reuses `compute_h3_scores()` (Gate 1) and the platform's existing
  statistical machinery (`validate_reference_v1_significance.py`,
  `validate_reference_v2_h1_significance.py`,
  `validate_scoring_signal.py`) unmodified.
- **Machine-readable output:**
  `phase6_economic_validation_2026-07-19.json` — seed `2026071901`,
  483 nominal window dates (2024-08-13 to 2026-07-17), 423 usable at
  the 60d horizon, 10,000 permutations, 2,000 bootstrap iterations per
  block length (20/40/60d).
- **Full report:** `docs/H3_PHASE6_ECONOMIC_VALIDATION_REPORT.md`.
- **Results (60d primary horizon):**

| Statistic | Observed | Adjusted p (Holm-Bonferroni) | Bootstrap excludes 0 (20/40/60d) | Correct sign | Passes |
|---|---|---|---|---|---|
| H3-A (score autocorrelation) | +0.04986 | 0.0000 | No / No / No | Yes | No |
| H3-B (top-5/bottom-5 spread) | −0.00573 | 0.0251 | No / No / No | **No** | No |

  H3-B is Holm-Bonferroni-significant with the wrong sign: ETFs ranked
  in H3's bottom 5 outperformed ETFs ranked in H3's top 5 over the
  following 60 trading days. Global-equity-segment sensitivity
  (`VT`/`ACWI`) checked and ruled out as the driver (H3-B bit-identical
  with/without).

## 5. Final determination

**EVIDENCE AGAINST.** Per Acceptance Criteria §5.2 item 2, a
Holm-Bonferroni-significant result in the direction opposite the
hypothesis's stated prediction is a **significant reversal**, recorded
as evidence against the mechanism — this platform's FAIL-tier terminal
outcome, and a stronger conclusion than a bare non-result. H3-A
additionally fails the compound "passes" bar (permutation-significant
but not bootstrap-robust at any of the three required block lengths).
No parameter was tuned, no alternative specification was run, and no
criterion was relaxed after this result was seen. Full record:
`decision_log.md` Entries 16–17;
`docs/H3_PHASE6_ECONOMIC_VALIDATION_REPORT.md` §7;
`docs/REFERENCE_H3_RESEARCH_CLOSEOUT.md`.

## 6. Governance status

- Phase 3 (four gates: 1, 2, 3, 4): all **PASS** (`decision_log.md`
  Entries 3–14).
- Phase 4 (Methodology Freeze): complete — construction frozen
  (`07f0da3`, Entry 10), acceptance criteria frozen (`a643993`, Entry
  15).
- Phase 5 (Implementation): complete (Entry 16).
- Phase 6 (Validation): complete — **EVIDENCE AGAINST** (Entry 16).
- Phase 7 (Decision): complete — **FAIL-tier, significant reversal**
  (Entry 17).
- Phase 8 (Archive): opened by Entry 17; this document is part of that
  archive step.
- **Reviewer level throughout:** Level 2 — AI-assisted adversarial
  (procedurally independent, **not organizationally independent**) for
  Gates 1–4; **Level 1 (self-review only)** for the Phase 6 run, the
  Phase 7 decision, and this closure document. No Level 2 or above
  confirmation of Phase 6–8 has been obtained. No Level 3
  (organizationally independent) review exists or is available on this
  platform, for H3 or any prior cycle.
- Outstanding, disclosed, non-blocking gaps (not resolved by this
  document): the dataset-hash / provenance policy
  (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §5); this cycle's
  non-idealized archive layout (Entry 17); absence of Level 2+ review
  for Entries 15–17's own artifacts.

## 7. Lessons learned (factual only)

- Setting the Phase 6 script's default output path directly to the
  dated `research_archive/reference_h3/` location, rather than the
  repo root, eliminated the "gitignore-then-copy" step both REFERENCE
  v1 and REFERENCE v2 H1 required after the fact.
- `build_statistic_view()` (originally written for REFERENCE v2 H1's
  H1-A/H1-B outcome separation) was reused unmodified for H3-A/H3-B's
  own outcome separation — a different pair of outcome types than H1
  used — without requiring changes.
- Pre-registering the small-effective-sample-size risk in the
  acceptance criteria (§2.2), before Phase 6 ran, meant H3-A's
  permutation-significant-but-not-bootstrap-robust result was
  immediately interpretable as an anticipated failure mode rather than
  a result requiring new judgment calls after the fact.
- The acceptance-criteria freeze commit (`a643993`) was not logged in
  `decision_log.md` at the time it was made; Entry 15 had to
  reconstruct it retroactively. A future cycle should log its Phase 4
  freeze commit in `decision_log.md` in the same session as the freeze
  itself.

## 8. Terminal status

**H3 is permanently closed under its frozen specification
(Attempt 1, commit `07f0da3`, acceptance criteria commit `a643993`).**
Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §7's FAIL terminal-failure
discipline and Acceptance Criteria §5.3:

- No parameter of the frozen construction or the frozen acceptance
  criteria — lookback, segment boundary, benchmark, peer-averaging
  method, bucket size, holding horizon, or any other — may be adjusted
  on this result in an attempt to produce a different outcome.
- No alternative evaluation period or date subset may be substituted
  in search of a window where this construction would have passed.
- No criterion in `docs/H3_ACCEPTANCE_CRITERIA.md` may be relaxed or
  reinterpreted having seen this result.

**Any future work touching relative-strength, rotation, or
segment-momentum ideas must be registered as a new hypothesis (H4, H5,
or later) under a new Phase 1–2 cycle, not as a modification, revival,
retry, or reinterpretation of H3.** That new cycle must explicitly
engage with this archived evidence in writing and state why it is
genuinely different from H3 Attempt 1.

This document does not itself constitute independent (Level 2+)
review of the Phase 6–8 artifacts it consolidates; that gap is
disclosed in Section 6 above, not resolved here.
