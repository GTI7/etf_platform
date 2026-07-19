# REFERENCE H3 (Relative Strength / Segment Rotation) Research Close-Out

This document closes the H3 research cycle (Attempt 1). It does not
modify H3's construction or propose retuning it. See
`research_archive/reference_h3/attempt_001_specification.md` (commit
`07f0da3`) for the frozen hypothesis and construction,
`docs/H3_ACCEPTANCE_CRITERIA.md` (commit `a643993`) for the frozen
Phase 6 decision rule, and
`experiments/validate_h3_phase6_economic_validation.py` for the
implementation that produced the results below. Process-level detail
for the full cycle (Phases 2–8) is recorded chronologically in
`research_archive/reference_h3/decision_log.md`, Entries 1–17; this
document is the Phase 8 close-out report that log's Entry 17 points to,
not a replacement for it.

**Final research status: H3 Attempt 1 is CLOSED — EVIDENCE AGAINST.**
Under `docs/RESEARCH_GOVERNANCE_STANDARD.md` §7's three-outcome
Decision Framework, this is a FAIL-tier terminal outcome, in the
specific "significant reversal" form Acceptance Criteria §5.2 item 2
defines as evidence against the mechanism — stronger than a bare
non-result. H3-B (the top-vs-bottom portfolio-spread diagnostic) is
Holm-Bonferroni-significant in the direction *opposite* the
hypothesis's prediction. H3 is not modified, not deleted, and not
promoted.

## A. Research close-out report

### Original hypothesis

H3 claimed that an ETF's relative standing versus its own peer market
segment — not its absolute return — persists in the near term, because
capital reallocates *between* market segments at a slower,
governance-bound cadence than security-specific information is
absorbed (`attempt_001_specification.md` §1–2, grounded in industry
momentum, style investing, and cross-asset/segment momentum
literature). H3-A (primary): daily cross-sectional Spearman
autocorrelation of the H3 score itself, `H3_score_i(t)` vs.
`H3_score_i(t+60)`. H3-B (secondary/diagnostic): top-5 vs. bottom-5
H3-ranked portfolio spread in forward 60-day raw return. Both were
pre-registered before any H3 outcome data existed
(`docs/H3_ACCEPTANCE_CRITERIA.md` §0).

### Experiments performed

1. **Pre-validation (Phase 3), four gates, all PASS**
   (`decision_log.md` Entries 3–14): Gate 2 (historical data adequacy,
   including a remediation cycle for a discovered PriceBar surplus
   defect), Gate 3 (economic rationale, literature-grounded and
   independently reviewed), Gate 1 (candidate signal independence from
   REFERENCE v1's MOMENTUM — median Spearman correlation 0.108,
   independently reproduced exactly in
   `docs/H3_GATE1_REPRODUCTION_REVIEW.md`), Gate 4 (no unresolved
   specification degrees of freedom).
2. **Methodology freeze (Phase 4)** — construction Attempt 1 frozen
   (commit `07f0da3`, Entry 10); acceptance criteria frozen (commit
   `a643993`, Entry 15), resolving the two design choices the
   construction had explicitly left open (holding horizon,
   portfolio-formation logic) on non-outcome, economic-mechanism
   grounds, and leaving three items (net-of-cost hurdle,
   drawdown/volatility ceilings) explicitly UNRESOLVED rather than
   invented.
3. **Phase 6 Validation** — `experiments/validate_h3_phase6_economic_validation.py`,
   `run()`: 483 window dates (2024-08-13 to 2026-07-17), 423 usable at
   the 60-day primary horizon, 10,000-iteration within-date permutation
   test per statistic, Holm-Bonferroni correction jointly across
   exactly {H3-A, H3-B} at 60d, block bootstrap (2,000 iterations at
   20/40/60-day blocks) per statistic, seed `2026071901`. Full report:
   `docs/H3_PHASE6_ECONOMIC_VALIDATION_REPORT.md`.

### Statistical results

| Statistic (60d primary) | Observed | Adjusted p (Holm-Bonferroni) | Significant? | Bootstrap-robust (20/40/60d all exclude 0)? | Correct sign? | Passes |
|---|---|---|---|---|---|---|
| H3-A (score autocorrelation) | +0.04986 | 0.0000 | Yes | No | Yes | No |
| H3-B (top-5/bottom-5 spread) | **−0.00573** | 0.0251 | Yes | No | **No** | No |

H3-B's negative point estimate means ETFs H3 ranked in its *bottom* 5
by relative standing outperformed ETFs ranked in its *top* 5 over the
following 60 trading days, on average — the reverse of persistence.
Because this reversal survives Holm-Bonferroni correction, Acceptance
Criteria §5.2 item 2 requires it be recorded as evidence against the
mechanism, not as a milder "no detectable relationship" outcome.

Diagnostic-only 20-day figures (not decision-relevant, structurally
inflated by trailing-window overlap — see Limitations): H3-A +0.634,
H3-B +0.00947.

### Audit conclusions

No dedicated, independent (Level 2+) verification audit of this
specific Phase 6 run has been performed as of this close-out — a real,
disclosed gap, consistent with the same gap already disclosed for
REFERENCE v2 H1's own close-out. What can be said without a full audit:
the statistical machinery used (`mean_ic`, `top_bottom_spread`,
`permutation_null`, `holm_bonferroni`, `bootstrap_ci`,
`_statistic_verdict`) is imported unmodified from REFERENCE v1's own
implementation, already reused and not newly audited for this cycle;
the H3 score construction itself (`compute_h3_scores()`) was already
independently reproduced at Gate 1
(`docs/H3_GATE1_REPRODUCTION_REVIEW.md`) using a disjoint second
implementation. What is new and unaudited by an independent reviewer is
this script's own panel construction (the forward-shifted-score view
for H3-A, the forward-raw-return view for H3-B), the Global-equity
sensitivity computation, and the non-overlapping-period drawdown/
volatility construction. A future audit, if performed, should focus on
those three pieces specifically.

### Remaining limitations

- **Small effective sample size.** ≈483 usable ranking dates at a
  non-overlapping 60-day horizon imply only ≈7–8 truly independent
  windows — pre-registered as a risk before this result existed
  (Acceptance Criteria §2.2), and directly responsible for H3-A's
  internal tension (near-zero permutation p-value vs. a zero-inclusive
  bootstrap CI): the permutation test and the block bootstrap are
  measuring different things, and the frozen decision rule's stricter
  reading (bootstrap CI must exclude zero) is why H3-A does not pass
  despite its strong permutation significance.
- **Single ~2-year, single historical regime** — no claim here
  generalizes to a different regime; the 8-period drawdown/volatility
  series in the Phase 6 report is far too short to characterize a
  return distribution and is reported for disclosure only.
- **Net-of-cost gap.** This result is gross-of-cost only; no
  transaction-cost, turnover, borrowing-cost, or capacity model exists
  anywhere on this platform. Moot for this specific outcome (the result
  is not a PASS), but would have gated any hypothetical PASS.
- **20-day diagnostic figures are not informative on their own** — the
  score's own 60-day trailing window at `t` and at `t+20` share 40 of
  60 underlying days, mechanically inflating the 20d IC; this is
  exactly why the 60-day horizon (where trailing windows are
  contiguous and non-overlapping) was pre-designated as the only
  horizon governing the decision.
- **No dedicated code-only audit of this specific run** (see Audit
  conclusions above).
- **No Level 3 (organizationally independent) review** exists or is
  available on this platform, for this cycle or any prior one.
- **This close-out and the Phase 6 run it summarizes have not yet
  received independent (Level 2+) review** — Level 1 (self-review)
  only, as of this document.

### Distinguishing the three kinds of evidence

- **Evidence against the implementation:** not identified, but not
  independently confirmed either — the panel-construction pieces named
  in Audit conclusions above are the specific place a future reviewer
  should look first. Open item, not a clean pass.
- **Evidence against the hypothesis:** the strongest of this platform's
  three closed REFERENCE cycles to date. REFERENCE v1's result was
  directionally consistent with its hypothesis but underpowered;
  REFERENCE v2 H1's was directionally opposite but not
  bootstrap-confirmed in either direction; H3's is directionally
  opposite **and** Holm-Bonferroni significant on the statistic closest
  to an implementable test of the hypothesis (H3-B), which the frozen
  acceptance criteria themselves designate as a reversal requiring
  "evidence against" treatment rather than a milder non-confirmation.
- **Insufficient statistical power / insufficient evidence:** still
  real for H3-A specifically — its bootstrap CI does not exclude zero
  at any block length, so the correctly-signed, permutation-significant
  point estimate cannot be confirmed robust to the sample's own serial
  dependence. This does not soften H3-B's reversal finding, which does
  not depend on H3-A at all (Acceptance Criteria §5.2 item 2 applies to
  either statistic independently).

## B. Frozen artifact inventory

- **Source code:** `experiments/validate_h3_phase6_economic_validation.py`
  — the exact implementation this result was produced against (imports
  `compute_h3_scores()` from `experiments/validate_h3_gate1_independence.py`,
  commit `798f052`, and the statistical machinery from
  `experiments/validate_reference_v1_significance.py`, unmodified).
- **Documentation:** this file; `docs/H3_PHASE6_ECONOMIC_VALIDATION_REPORT.md`;
  `docs/H3_ACCEPTANCE_CRITERIA.md` (commit `a643993`);
  `research_archive/reference_h3/attempt_001_specification.md` (commit
  `07f0da3`); `research_archive/reference_h3/decision_log.md` (Entries
  1–17, full process history).
- **Generated output:** `research_archive/reference_h3/phase6_economic_validation_2026-07-19.json`
  — written directly into the archive directory by the script's own
  default output path (unlike REFERENCE v1 and REFERENCE v2 H1's
  scripts, which defaulted to a repo-root path and required a later
  gitignore-and-copy step; this script's `DEFAULT_OUTPUT_PATH` was set
  to the dated archive location from the start, closing that specific
  gap noted in both prior close-outs' Section B/C before it could
  recur).

## C. Lessons learned

- Setting a script's `DEFAULT_OUTPUT_PATH` directly to a dated
  `research_archive/<cycle>/` location, rather than the repo root,
  eliminated the entire "gitignore the generated report, then remember
  to copy a dated snapshot into the archive" step that both REFERENCE
  v1 and REFERENCE v2 H1's close-outs had to perform (or, in H1's case,
  flag as an outstanding gap) after the fact — a concrete, reusable
  fix for whatever candidate is evaluated next.
- Reusing `build_statistic_view()` (originally written for REFERENCE v2
  H1's H1-A/H1-B outcome separation) for H3-A/H3-B's own outcome
  separation — forward-shifted score vs. forward raw return, an
  entirely different pair of outcome types than H1 ever used — worked
  without modification, validating that adapter's generality beyond
  its original use case.
- Pre-registering the small-effective-sample-size risk in the
  acceptance criteria (§2.2) *before* running Phase 6 meant H3-A's
  permutation-significant-but-not-bootstrap-robust result was
  immediately interpretable as the anticipated failure mode, not a
  surprising or ambiguous one requiring new judgment calls after the
  fact — a concrete benefit of writing the acceptance criteria before
  touching any outcome data.
- The acceptance-criteria freeze commit (`a643993`) was not logged in
  `decision_log.md` at the time it was made; this closure's own Entry
  15 had to reconstruct it retroactively. A future cycle's Phase 4
  step should log its freeze commit in `decision_log.md` in the same
  session as the freeze commit itself, not deferred to the next
  archival pass.

## D. Next steps for the REFERENCE v2 candidate search

H3's closure returns the project to the ranked shortlist established in
the REFERENCE v2 research strategy document (chat-only, never persisted
to a file — see `research_archive/reference_h3/decision_log.md` Entry 1
for the disclosed provenance gap this already carries). H1 (ranked
first) and H3 (ranked second) are both now closed; no ranked, untested
candidate remains from that original shortlist as of this close-out.

- H3's specific results must not be used to tune, select, or bias any
  future candidate's parameters — the same "no tuning against prior
  results" discipline that governed H3's own selection and construction
  applies unchanged to whatever is evaluated next.
- Per Acceptance Criteria §5.3 item 5 and
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §7's FAIL discipline, a future
  relative-strength or segment-rotation hypothesis is only legitimate
  as a wholly new Phase 1–2 cycle that explicitly engages with this
  archived evidence and states, in writing, why it is genuinely
  different from H3 Attempt 1 — not a renamed or restarted attempt at
  it.
- Whoever picks up the next candidate should either locate the original
  8-candidate strategy document (to identify candidate #3) or
  reconstruct and re-rank the remaining candidates from scratch, and
  should close the two disclosed gaps this cycle leaves open before
  reusing this cycle's conventions: the dataset-hash/provenance policy
  required by `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5, and obtaining
  a Level 2 (or above) review of this close-out and the Phase 6 run
  itself before treating H3's determination as governance-final beyond
  Level 1.
