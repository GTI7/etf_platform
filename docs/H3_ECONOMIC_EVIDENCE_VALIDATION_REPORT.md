# H3 Economic Evidence Validation Report

**Report date:** 2026-07-19
**Prepared by:** AI research assistant (Claude), acting as Institutional
Quant Research Validation Lead. This role reviews evidence only; it does
not develop, improve, tune, or modify H3's frozen construction or
methodology.
**Scope:** whether the frozen H3 construction (Attempt 1) demonstrates
economically meaningful evidence — forward returns, rank persistence,
portfolio outcomes, risk-adjusted performance — sufficient to justify
further research. This is explicitly **not** a re-statement of the Gate
1 independence question ("is H3 distinct from MOMENTUM?"), which is
already closed and is not re-litigated here.

---

## 1. Executive Summary

**Status: INCONCLUSIVE.**

No economic evidence exists to evaluate. Across every document in the
frozen H3 archive — the construction specification, the Gate 1
independence validation and its reproduction, the Gate 4
degrees-of-freedom audit, and the append-only decision log — **no
forward return, Information Coefficient, p-value, Sharpe ratio,
drawdown, portfolio outcome, or any other outcome/performance figure
has ever been read, computed, or referenced for H3.** This is not an
omission or a gap in reporting; it is the explicit, repeatedly-stated
design of the phase H3 has completed. The pre-validation plan's
"Standalone principle" (`docs/REFERENCE_H3_PREVALIDATION_PLAN.md`
§2) forbids touching outcome data during Gates 1–4 by rule, precisely
so that construction choices cannot be shaped by a preview of results.
Under this platform's own eight-phase lifecycle
(`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2), outcome data may be
computed **only** in Phase 6 (Validation) — a phase H3 has not yet
entered.

H3 has completed Phase 3 (Pre-validation: Gates 1–4, all PASS) and has
not yet reached Phase 4 (Methodology Freeze finalization, including
acceptance-criteria authoring), Phase 5 (Implementation), or Phase 6
(Validation, where forward-return testing would first occur). Asking
"does the frozen H3 construction demonstrate economically meaningful
predictive value?" of a cycle that has not yet run Phase 6 is asking a
question the record cannot yet answer — not because the answer is
negative, but because it has not been measured.

This is not a judgment that H3 is weak evidence dressed up as strong;
it is the absence of any evidence bearing on economic value at all. Per
this task's own instruction ("If evidence is weak, report
INCONCLUSIVE"), the correct and only honest status here is
**INCONCLUSIVE** — with the stronger qualifier that this is a
"not yet measured" INCONCLUSIVE, not an "measured and ambiguous" one.

---

## 2. Frozen Methodology Confirmation

- **No methodology changes.** No H3 construction element, scoring
  formula, universe, segment grouping, lookback window, missing-data
  rule, evaluation window, or acceptance criterion was modified, tuned,
  optimized, or reinterpreted in the course of producing this report.
  No alternative lookback, benchmark, or parameter was tested. No
  outcome data was computed by this report.
- **Freeze reference.** Commit `07f0da379d8cccf06d17c34a51cbb557da047fef`
  (`research_archive/reference_h3/FREEZE_RECORD.md`). Verified at the
  time of this report: current repository `HEAD` is `798f052` (six
  commits ahead, all governance/archival documentation — Gate 1 and
  Gate 4 final determinations and their archival); `git diff 07f0da3
  HEAD` against every frozen file
  (`attempt_001_specification.md`, `docs/REFERENCE_H3_PREVALIDATION_PLAN.md`,
  `docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`,
  `docs/RESEARCH_GOVERNANCE_STANDARD.md`) is empty — no drift.
- **Analysis scope.** This report reads and synthesizes only the six
  evidence sources named in the task instructions, plus the decision
  log, archive README, and the governance standard's Phase 6/Decision
  Framework sections consulted solely to establish *what phase H3 is
  currently in* (necessary to correctly scope this question, not to
  introduce new analysis). No database query, script execution, or
  computation was performed by this report. No new metric appears
  anywhere below that is not already stated in a cited source.
- **Gate 1 vs. economic validation — kept distinct.** Gate 1
  (`docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`,
  `gate1_final_determination.md`) measured same-date score-to-score
  Spearman rank correlation and rank-overlap between the H3 score and
  REFERENCE v1's MOMENTUM score — a test of whether H3 is a distinct
  signal, not of whether it predicts anything. That question is
  answered (PASS) and is not reopened here. This report addresses the
  separate, unanswered question of economic value, which Gate 1 was
  explicitly and repeatedly documented as *not* addressing (see
  Section 3 below).

---

## 3. Economic Evidence

**Observed results: none.** The frozen record contains no instance of
any of the following, for H3, anywhere:

| Evidence type requested | Found in frozen record? |
|---|---|
| Forward returns | No |
| Rank persistence (score-to-future-outcome) | No |
| Portfolio outcomes (top-vs-bottom spread, bucket returns) | No |
| Consistency over time / sub-period stability of returns | No |
| Information Coefficient / p-value / significance test | No |
| Sharpe ratio, volatility of returns, drawdown | No |
| Turnover, transaction-cost, or capacity estimate | No |

This absence is independently attested, in nearly identical language,
by every primary source read for this report:

- `attempt_001_specification.md` (opening statement): "No forward
  return, IC, p-value, or other outcome variable is read, computed, or
  referenced anywhere in this document."
- `docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md` §0: Gate 1 is "not
  a forward-return backtest, an IC/p-value significance test, or a
  risk-adjusted-performance comparison; the frozen methodology
  explicitly prohibits touching any of those in this phase."
- `research_archive/reference_h3/decision_log.md`, "Current status" (as
  of both Entry 12 and Entry 14): "No outcome data (forward return, IC,
  p-value, Sharpe, or any other performance figure) has been read,
  computed, or referenced at any point reflected in this log."
- `research_archive/reference_h3/README.md`: "No H3 signal, score,
  benchmark, peer group, lookback window, IC, p-value, or forward
  return appears anywhere in any of these files."

**What does exist** is upstream of economic evidence, not a substitute
for it:

1. **A frozen construction** (`attempt_001_specification.md`) —
   defines *how* H3's score would be computed, not what it predicts.
2. **Gate 1: independence from MOMENTUM** — PASS. Daily Spearman
   correlation between H3 and MOMENTUM scores across 483 trading dates
   (2024-08-13 to 2026-07-17): median 0.108, mean 0.101, IQR -0.036 to
   0.229. This measures whether H3 is a *distinct* signal from
   MOMENTUM — a necessary precondition for H3 to be worth testing
   economically — not whether H3 itself has any predictive content.
   A signal can be perfectly independent of MOMENTUM and have zero, or
   negative, economic value; independence and economic value are
   orthogonal questions.
3. **Gate 4: degrees-of-freedom control** — PASS. Confirms the
   construction's design choices (universe, lookback, segments, scoring
   formula, missing-data rule) were fixed before any outcome was seen,
   which protects the *future* Phase 6 result from hindsight bias. It
   says nothing about what that future result will be.

**Time-series evidence:** none exists for any performance quantity.
The only time-series evidence in the record is the day-by-day Spearman
correlation and rank-overlap series underlying Gate 1 (Section 5.1–5.2
of the Gate 1 report), which is a same-date score-comparison series,
not a forward-looking performance series.

**Limitations:** the fundamental limitation is completeness, not
quality — the required Phase 6 (Validation) has not run. Two
second-order limitations are already disclosed in the Gate 1/Gate 4
record and are relevant context for whenever Phase 6 does run:

- A bottom-tail rank-overlap asymmetry between H3 and MOMENTUM (median
  40% bottom-5 overlap vs. 20% top-5, chance-level) is measured,
  reproduced, and explicitly unexplained by any source
  (`gate1_final_determination.md` §5; `gate4_final_determination.md`
  §6). This does not bear on economic value directly, but it means H3
  and MOMENTUM may behave more similarly at one tail than the other in
  whatever future forward-return test is run — worth watching for in
  Phase 6, not resolved here.
- 19 of the nominal 502-date evaluation window could not be evaluated
  even for the independence check, due to a `Score`-table data gap
  unrelated to H3's own data (Gate 1 report §3). This affects data
  completeness generally and would need to be re-checked against
  whatever window Phase 6 eventually uses.

---

## 4. Benchmark Comparison

The task instructions request comparison "only against predefined
references." The only predefined reference in the frozen record is
REFERENCE v1's MOMENTUM score, and the only predefined comparison
against it is Gate 1's same-date rank-correlation/overlap methodology
(`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2, "Frozen methodology
summary"). That comparison is reported in full in Section 3 above and
is **not** a performance benchmark — it compares two scores on the same
date, not H3's returns against MOMENTUM's returns, a buy-and-hold
index, or any other economic reference point.

**No performance benchmark comparison can be reported**, because none
is defined in the frozen methodology for this phase and none has been
computed. `docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md` §5.3 states
this explicitly: "No market index or buy-and-hold comparison exists in,
or is authorized by, this phase." Introducing one now — even informally
— would violate both this task's restrictions (no new benchmarks after
seeing results) and the frozen methodology's own Standalone principle.

---

## 5. Risk and Robustness Assessment

**Strengths (process, not outcome):**

- The construction's researcher degrees of freedom are well-controlled:
  Gate 4 found 5 of 7 audited categories CONTROLLED and the remaining 2
  (evaluation window, acceptance criteria) PARTIALLY CONTROLLED for
  disclosed, non-outcome-driven reasons, with independently
  git-verified (not merely self-reported) evidence that the universe
  and segment definitions predate H3 by two days
  (`docs/H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md` §2, §4).
  This is a meaningful process strength: whenever Phase 6 does run, the
  construction being tested was not shaped by a preview of its own
  results.
- Two of four candidate constructions were rejected by algebraic proof
  of rank-degeneracy (not by outcome comparison), and the frozen
  construction was checked and shown not to reduce to that degenerate
  case (`attempt_001_specification.md` §4).
- Gate 1's independence figures were independently reproduced to full
  floating-point precision via two disjoint implementations
  (`gate1_final_determination.md` §3).

**Weaknesses / risks that bear directly on economic value, unresolved:**

- **Volatility, drawdowns, concentration, turnover, implementation
  constraints: not assessable.** None of these can be computed without
  a return series, which does not exist for H3 in the frozen record.
  This is not a "weak" finding on these dimensions — it is a complete
  absence of the data needed to form one.
- **Portfolio formation is explicitly unresolved.** Section 3.7 of the
  specification states portfolio formation "is not computed or
  implemented by this document," deferring even the top-vs-bottom
  bucket comparison to "a future, separately-scoped validation phase."
  No holding horizon has been fixed either (§3.8): "The separate
  question of what forward holding horizon a future validation phase
  would use to test this score is explicitly not decided here."
  Without a fixed holding horizon, no return, and therefore no risk
  metric, can even be defined yet.
- **Acceptance criteria for the eventual significance test are
  unwritten** (Gate 4 audit, Matrix row 7; decision log Entry 10).
  There is currently no predefined threshold against which a future
  Phase 6 result would be judged PASS/FAIL/INCONCLUSIVE — a real,
  disclosed open item, appropriately sequenced to Phase 4 under this
  project's own lifecycle, but relevant to flag here since it means
  even a future positive-looking result could not yet be judged
  "sufficient" without that criterion first being fixed in writing.
- **Single ~2-year historical regime.** Even when Phase 6 eventually
  runs, the same price history underlying Gate 1's 483 evaluated dates
  spans one historical period (2024–2026), not multiple independent
  market regimes — a limitation already disclosed for REFERENCE v1 and
  REFERENCE v2 H1 in this archive and inherited by any future H3 test
  drawing on the same window.
- **No Level 3 (organizationally independent) review exists or is
  available on this platform**, for H3 or any prior cycle
  (`gate4_final_determination.md` §6). All findings cited in this
  report rest on Level 2 (procedurally independent, not
  organizationally independent) review at most.

**Statistical robustness (per the task's Section 4 request):**

- **Sample size:** N/A for economic evidence — no outcome sample exists.
  For the one statistic that does exist (Gate 1's independence
  correlation), n = 483 daily cross-sections of ≤25 ETFs each — that
  sample size question was already addressed in Section 3 and is not an
  economic-significance sample.
- **Uncertainty / significance limitations:** no significance test of
  any kind has been run for H3's predictive value (forbidden in this
  phase by design, per the Standalone principle). No p-value exists to
  assess, honestly report, or caveat.
- **Possibility of overfitting:** cannot be assessed on the dimension
  that matters most for economic evidence (in-sample vs. out-of-sample
  return performance), because no return performance of any kind has
  been computed. On the narrower, already-assessed dimension of
  construction-selection overfitting (i.e., was the *formula* chosen to
  fit a result), Gate 4 found this risk low, with independently
  checkable support. That is a different and much narrower question
  than whether H3's eventual forward-return result will replicate
  out-of-sample — which remains completely open.

No significance was manufactured here to fill this gap, per the task's
explicit restriction.

---

## 6. Economic Interpretation

**Mechanism claimed.** Per `attempt_001_specification.md` §1–2 and the
underlying Gate 3 rationale, H3 claims that ETFs whose recent
60-trading-day return has been relatively strong versus their own
peer market segment will continue to show relatively strong returns
versus that segment in the near term (and symmetrically for weak
performers), because institutional allocators reallocate capital
*between* market segments on a slow (roughly quarterly),
governance-driven review cadence, and flow-chasing retail/advisor
capital follows the same recently-favored segments through thematic and
sector ETF wrappers. This is a claim about relative-standing
persistence *within* a peer segment, not about any ETF's own absolute
price trend, and is argued to be actor- and mechanism-distinct from
MOMENTUM's single-security, information-diffusion story.

**Does observed evidence support that mechanism?** This cannot be
answered yet, and it is important to be precise about why: the evidence
gathered so far (Gates 1–4) was never designed to test the mechanism's
predictive claim. It was designed to test two narrower, necessary
preconditions — (a) that the proposed score is not merely a relabeling
of an existing signal (Gate 1), and (b) that the construction's design
choices were not shaped by hindsight (Gate 4). Both preconditions are
satisfied. Neither one is evidence that the reallocation-lag mechanism
actually produces the claimed return persistence. That would require
Phase 6 (Validation): computing H3's score, fixing a forward holding
horizon, and measuring whether relative standing at time *t* actually
predicts relative standing (or relative return) at *t + horizon*, with
predefined acceptance criteria fixed in advance.

No causal claim beyond this is warranted by the current evidence, and
none is made here.

---

## 7. Final Assessment

**Does the frozen H3 methodology demonstrate economically meaningful
evidence, without changing any research choices? No — because no
economic evidence has been produced yet, by design of the phase H3 has
completed.** This is not the same finding as "the evidence is weak" or
"the evidence points against H3"; it is "the evidence does not yet
exist," which is a categorically different and less resolved
situation.

**Whether evidence supports further investigation:** Yes, on the
narrow basis available — the construction cleared its one required
independence hurdle by a wide margin (median correlation 0.108, far
from the 1.0 degenerate-case trigger), has a documented, pre-registered
economic rationale distinct from MOMENTUM's, and has well-controlled
researcher degrees of freedom per Gate 4. These are legitimate,
necessary gatekeeping results that justify proceeding to the phase
that would actually generate economic evidence. They are not
themselves that evidence.

**Whether evidence is insufficient:** Yes, for any claim of economic
value, investability, or predictive skill. It would be a governance
violation of this platform's own Standalone principle, and a
misrepresentation to any reader, to characterize Gates 1 and 4 as
economic support for H3. No such characterization is made anywhere in
the frozen record itself, and none is made here.

**What future validation is allowed:** Per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2, the next legitimate step is
Phase 4 (Methodology Freeze) — finalizing the still-unwritten
acceptance criteria for H3's eventual significance test (holding
horizon, bucket/portfolio definition, and the specific PASS/FAIL/
INCONCLUSIVE thresholds), fixed *before* any return data is touched —
followed by Phase 5 (Implementation) and then Phase 6 (Validation),
the only phase in which forward returns, IC, significance tests, and
risk metrics may first be computed for H3. Per Phase 7's Decision
Framework, that Phase 6 result would then be judged against the
acceptance criteria fixed at Phase 4 — not against criteria chosen
after seeing the result.

This report does not, and under its scope cannot, recommend or perform
any part of that future work: no lookback, universe, scoring formula,
or benchmark was tested, adjusted, or proposed as an improvement here.

---

## Sources reviewed

- `research_archive/reference_h3/attempt_001_specification.md`
- `docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`
- `research_archive/reference_h3/gate1_final_determination.md`
- `docs/H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md`
- `research_archive/reference_h3/gate4_final_determination.md`
- `research_archive/reference_h3/FREEZE_RECORD.md`
- `research_archive/reference_h3/decision_log.md` (Entries 1–14, "Current status" sections)
- `research_archive/reference_h3/README.md`
- `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2 ("Standalone principle")
- `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 (Research Lifecycle, Phases 3–7), §7 (Decision Framework)

No H3 methodology, scoring logic, parameter, benchmark, universe, or
acceptance criterion was modified, tuned, tested against an
alternative, or newly introduced by this report. No outcome data was
computed by this report; all figures cited above are reproduced,
unmodified, from the sources listed.
