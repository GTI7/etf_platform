# H3 Gate 1 Reproduction Review

**Tier: Level 2 — AI-assisted adversarial review**, per
[`docs/RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md)
§4 — produced in a new session with no conversational continuity to the
session that produced
[`docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`](H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md)
or any prior REFERENCE H3 gate review. This is **procedurally
independent** (a fresh session, a real separate pass over the material,
and the figures below were independently recomputed rather than
inspected) but **not organizationally independent**: same AI model
vendor as the work reviewed, same single operator, no incentive
separation, no standing accountable reviewer role, and the claim of "no
conversational memory" is self-reported and not third-party-verifiable.
Per §4, this fact is stated here in those terms rather than using the
unqualified word "independent."

**Role boundary observed.** This review does not modify H3's
methodology, formulas, thresholds, parameters, or acceptance criteria.
It does not add new metrics, use forward returns, or introduce a
benchmark beyond REFERENCE v1's frozen MOMENTUM score already specified
by the frozen methodology. Where this review's recomputed figures are
reported below, no adjustment was made to bring them into agreement
with the original report — none was needed (Section 4).

---

## 1. Reproduction status

**PASS.**

Every figure in the original report's Sections 5.1 and 5.2 was
independently recomputed and matches exactly — both by re-running the
committed script against the live database and, as an additional check
not requested by the frozen methodology but performed here for rigor,
by an independently written second implementation that shares no code
with the original script (Section 4.3).

---

## 2. Environment verification

**Freeze commit.**

| Check | Result |
|---|---|
| `git cat-file -t 07f0da379d8cccf06d17c34a51cbb557da047fef` | `commit` — object exists |
| `git rev-parse 07f0da3` | Resolves to `07f0da379d8cccf06d17c34a51cbb557da047fef` — matches in full |
| Current `HEAD` | `149ae4405037bff0e82134e98f070c9922ea30a0` (one commit ahead of the freeze) |
| `git diff 07f0da3 HEAD -- research_archive/reference_h3/attempt_001_specification.md docs/REFERENCE_H3_PREVALIDATION_PLAN.md docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md docs/RESEARCH_GOVERNANCE_STANDARD.md` | Empty — no drift on any of the four frozen files cited by the original report |
| Content of the one commit between freeze and `HEAD` (`149ae44`) | Adds `research_archive/reference_h3/{COMMIT.txt,FREEZE_RECORD.md,decision_log.md}` and appends to `README.md` only — governance/provenance records, not construction or methodology files. Does not touch any file the freeze covers. |

**Files.**

| File | State |
|---|---|
| `experiments/validate_h3_gate1_independence.py` | Present, untracked (`git status --short` shows `??`), read in full (406 lines) |
| `research_archive/reference_h3/gate1_independence_analysis_2026-07-19.json` | Present, untracked, read in full |
| `docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md` | Present, untracked, read in full |
| `research_archive/reference_h3/attempt_001_specification.md` | Present, committed at `07f0da3`, unchanged since; read in full at the frozen commit (`git show 07f0da3:...`), not from the working tree, to rule out any working-tree edit the `git diff` check above might have missed |
| `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` | Same treatment — read in full at the frozen commit |
| `research_archive/reference_v1/reference_v1_significance_report_2026-07-18.json` | Present, read in full |

**Data state.** Live SQLite database `experiments_etf_universe.db`,
queried directly (not only through the script):

- `PriceBar`: `SELECT COUNT(*), COUNT(DISTINCT etf_id), MIN(session_date), MAX(session_date)` → **61,850 rows, 25 distinct ETFs, 2016-09-13 to 2026-07-17** — matches the report's Section 3 claim exactly.
- `Score`: `SELECT session_date, COUNT(*) FROM Score WHERE session_date BETWEEN '2024-07-17' AND '2024-08-13' GROUP BY session_date` → returns exactly **one** row, `('2024-08-13', 25)` — confirming zero `Score` rows exist for any of the 19 XNYS trading days from 2024-07-17 through 2024-08-12, and that 2024-08-13 is the first date all 25 ETFs have a `Score` row. This matches the report's disclosed coverage-gap claim exactly, independently verified against the database rather than taken from the report's own SQL description.
- `MIN(session_date)` over all of `Score`: `2024-08-13` — consistent with the above.

No discrepancy found in any environment check.

---

## 3. Method verification

**Frozen methodology documents read in full at commit `07f0da3`** (not
from the working tree): `docs/REFERENCE_H3_PREVALIDATION_PLAN.md`
Section 2 ("Research independence verification," including the "Frozen
methodology summary" table and Section 4's independent-confirmation
duties) and `research_archive/reference_h3/attempt_001_specification.md`
Sections 3.1–3.10 (universe, peer-segment grouping, score definition,
missing-data rule, disclosed 2-member Global-equity limitation) and
Section 5 (attempt log / pre-log attestation).

**Same methodology, confirmed by direct comparison of script to frozen
text, not by trusting the report's own description of itself:**

| Frozen element | Frozen source | Script implementation | Match |
|---|---|---|---|
| Universe: 25-ticker REFERENCE v1 set | Spec §3.1 | `ETF_UNIVERSE` imported unchanged from `experiments/daily_etf_universe_update.py` | ✓ |
| Six-segment peer grouping | Spec §3.2 (table) | `SEGMENTS` dict in the script, checked ticker-for-ticker against the spec's table and against the inline comments in `daily_etf_universe_update.py:89-120` | ✓ exact match, all 25 tickers, no overlap/residual |
| `own_return_i(t) = ln(close_i(t)/close_i(t-60))`, 60-trading-day index offset | Spec §3.5 | `compute_h3_scores()`: `math.log(c_t / c_prior)` with `t_minus_60 = trading_days[idx - 60]` | ✓ |
| `peer_return_i(t)` = equal-weighted mean of peers' `own_return`, self excluded | Spec §3.5 | `peer_return = sum(own_returns[p] for p in peers) / len(peers)` where `peers` excludes `ticker` | ✓ |
| `H3_score_i(t) = own_return_i(t) − peer_return_i(t)` | Spec §3.5 | `day_scores[ticker] = own_return - peer_return` | ✓ |
| Missing-data rule: exclude unless own return *and* ≥1 peer's own return resolvable; no forward-fill/interpolation | Spec §3.9 | `if c_t is None or c_prior is None or ...: continue` (own-return gate) and `if not peers: continue` (peer gate) | ✓ |
| MOMENTUM read from existing `DimensionScore`, not recomputed | Plan §2 "Benchmark" row | `compute_momentum_scores()` calls `generate_ranked_etf_report()` unchanged, reads `Dimension.MOMENTUM` | ✓ — confirmed independently by reading MOMENTUM directly via SQL join on `Score`/`DimensionScore` (Section 4.3 below), bypassing `generate_ranked_etf_report()` entirely, and obtaining identical values |
| Daily Spearman, average-rank tie handling, one correlation per date (not pooled) | Plan §2 | `_spearman()`/`_rank_average_ties()` imported unchanged from `validate_reference_v1_significance.py`; loop computes one correlation per date in `window_days` | ✓ — algorithm re-derived independently in Section 4.3 below and confirmed correct (Pearson correlation on average-tie ranks; standard, textbook Spearman) |
| Score overlap at top-5/bottom-5, bucket size 5 | Plan §2 "Score overlap analysis"; bucket size sourced from Spec §3.7 / `validate_reference_v1_significance.py` convention, disclosed as an interpretive but non-invented reuse | `score_overlap()`: top/bottom 5 by each score, `overlap = |intersection| / 5` | ✓ |
| Evaluation window 2024-07-17 to 2026-07-17 = REFERENCE v1's own window | Plan §2 "Evaluation basis" | `PERIOD_START`/`PERIOD_END` hard-coded to those dates, cited to `reference_v1_significance_report_2026-07-18.json` | ✓ — independently confirmed: that JSON's `config.period_start`/`period_end` read directly are `2024-07-17`/`2026-07-17` |
| Standalone principle: no forward return/IC/p-value anywhere | Plan §2 | Confirmed by full read of the 406-line script: no return series other than the 60-day trailing own-return is touched; no forward-looking date arithmetic exists anywhere in the file | ✓ |

**Same inputs.** `PriceBar` (61,850 rows, 25 ETFs, 2016-09-13 to
2026-07-17) and the existing `Score`/`DimensionScore` tables, both
queried live from `experiments_etf_universe.db` — the same database
file the original report used (same path, same working directory,
re-run without copying or altering the file).

**Same calculations.** Confirmed both by re-running the committed
script unmodified (Section 4.1) and by an independently written
second implementation (Section 4.3) that does not import or call any
function from the original script or from
`validate_reference_v1_significance.py`.

No methodology deviation of any kind was introduced by this review.

---

## 4. Result comparison

### 4.1 Script re-run (same code, live database, output diffed against archived evidence)

The original evidence file
(`research_archive/reference_h3/gate1_independence_analysis_2026-07-19.json`)
was backed up before re-running, then
`experiments/validate_h3_gate1_independence.py` was executed unmodified
against the live database. The script's own console summary from this
review's run:

```
Ranking dates evaluated: 483 of 502 in window
-- Daily Spearman correlation (H3 score vs. MOMENTUM score) --
  n=483  mean=0.10076286032807771  median=0.10846153846153846
  p25=-0.036153846153846154  p75=0.22923076923076924
  min=-0.3223076923076923  max=0.45153846153846156
-- Top-5 overlap fraction  -- n=483 mean=0.20165631469979298 median=0.2
-- Bottom-5 overlap fraction -- n=483 mean=0.337888198757764 median=0.4
```

The newly written JSON output was then diffed field-by-field against
the pre-run backup of the original evidence file: **identical in every
field except `generated_at`** (a timestamp, not a result). All 483
per-date records — date, `n_etfs`, `spearman_correlation`,
`top_overlap_fraction`, `bottom_overlap_fraction` — matched exactly.
The original evidence file was restored byte-for-byte afterward so this
review leaves no working-tree change behind.

### 4.2 Aggregate statistics, recomputed independently from the per-date records

Using an independently written percentile function (linear
interpolation, same textbook definition but written fresh, not copied
from `_percentile()`) applied to the 483 per-date values in the JSON:

| Statistic | Recomputed | Original report (§5.1) |
|---|---|---|
| n | 483 | 483 |
| Mean | 0.10076286032807771 | 0.1008 |
| Median | 0.10846153846153846 | 0.1085 |
| P25 | -0.036153846153846154 | -0.0362 |
| P75 | 0.22923076923076924 | 0.2292 |
| Min | -0.3223076923076923 | -0.3223 |
| Max | 0.45153846153846156 | 0.4515 |

| Statistic | Recomputed top overlap | Original (§5.2) | Recomputed bottom overlap | Original (§5.2) |
|---|---|---|---|---|
| Mean | 0.20165631469979298 | 0.2017 | 0.337888198757764 | 0.3379 |
| Median | 0.2 | 0.20 | 0.4 | 0.40 |

Full agreement to the precision the original report rounded to.

### 4.3 Independent second implementation (no shared code)

A separate script was written for this review that: (a) reads
`PriceBar` and `Score`/`DimensionScore` via raw SQL rather than through
`get_price_bars()` / `generate_ranked_etf_report()`; (b) recomputes H3
scores with its own loop (not `compute_h3_scores()`); (c) uses its own
rank/Pearson/Spearman functions (not `_rank_average_ties()`/`_pearson()`/
`_spearman()`); (d) uses its own top/bottom-5 overlap logic. Run against
four dates spanning the evaluated window (the first evaluated date,
one high-correlation date, one mid-window date, and the last date in
the window):

| Date | n | Spearman (this review) | Spearman (original JSON) | Top overlap | Bottom overlap |
|---|---|---|---|---|---|
| 2024-08-13 | 25 | 0.1946153846153846 | 0.1946153846153846 | 0.0 / 0.0 match | 0.4 / 0.4 match |
| 2025-02-05 | 25 | 0.4169230769230769 | 0.4169230769230769 | 0.4 / 0.4 match | 0.8 / 0.8 match |
| 2025-08-15 | 25 | 0.06615384615384616 | 0.06615384615384616 | 0.2 / 0.2 match | 0.0 / 0.0 match |
| 2026-07-17 | 25 | 0.24769230769230768 | 0.24769230769230768 | 0.0 / 0.0 match | 0.6 / 0.6 match |

All four dates match to full floating-point precision using code that
shares nothing with the original script beyond the frozen formulas
themselves.

### 4.4 Additional integrity check

The report's Section 3 claim that "`n_etfs` per evaluated date is 25
for every date in the output" was checked directly against all 483
records: `set(r["n_etfs"] for r in daily_results) == {25}` — confirmed,
no partial cross-section on any evaluated date.

---

## 5. Differences

**None found.** Every figure in the original report — the six-number
Spearman distribution summary, the two overlap distributions, the
483/502 evaluated-date count, the 25-ETF-per-date integrity claim, and
the Score-table coverage-gap claim — was independently reproduced
exactly, both by re-running the original script and by an independently
written second implementation. No adjustment of any kind was made to
bring this review's figures into agreement with the original; none was
needed.

This section exists per the reproduction requirements regardless of
outcome; it is empty because no discrepancy was found, not because the
check was skipped.

---

## 6. Final determination

**Reproduction result: PASS.** The rank-correlation calculation and the
score-overlap calculation were independently reproduced — not merely
inspected — per
[`docs/REFERENCE_H3_PREVALIDATION_PLAN.md`](REFERENCE_H3_PREVALIDATION_PLAN.md)
Section 4, duty 4, and this review's own figures match the original
report's Sections 5.1–5.2 exactly.

**Can Gate 1's quantitative evidence be accepted?** The measurement
itself — yes, at the reproduction tier available. The reported
correlation and overlap distributions are correct and reproducible from
the written record alone (the frozen documents, the committed script,
and the raw database), consistent with the Plan's "Reproducibility
standard" (Section 4): this review reached identical figures without
any clarification from the original session.

Two matters remain outside this review's scope but bear directly on
whether Gate 1 as a whole — not just its quantitative evidence — is
governance-final, and are flagged rather than adjudicated, consistent
with this task's restriction against tuning results or expanding scope:

- **This review's own independence tier.** Per Section 0 above, this is
  a Level 2 (procedurally independent, not organizationally
  independent) confirmation — the same tier the original report itself
  identifies as the "next allowed action," and the same tier already
  used for Gates 2 and 3 in this archive. It satisfies Plan Section 4's
  duty 4 (independent reproduction) at the level of rigor this
  platform's governance standard currently supports. It does not, and
  cannot, constitute Level 3 (organizationally independent) review,
  which this platform has never performed for any prior gate either
  (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4).
- **Duties 1–3 of Plan Section 4** (review of the full construction
  attempt log; confirmation that no outcome data was used anywhere in
  the construction or measurement; confirmation that REFERENCE v1/v2 H1
  results did not influence construction selection) were read as part
  of verifying method (Section 3 above — `attempt_001_specification.md`
  Section 5's pre-log attestation discloses four rejected alternatives,
  none evaluated against outcome data) but a full adversarial audit of
  those attestations was not the task this review was scoped to
  perform, which was the quantitative reproduction specifically (duty
  4). Nothing found while reading them contradicts the original
  report's claims, but this review does not certify them with the same
  rigor applied to Sections 4.1–4.4 above.
- **The bottom-tail overlap asymmetry** the original report flags in
  its Section 6 (bottom-5 overlap median 40% vs. top-5 median 20%,
  chance-level) is confirmed, exactly, as a measured fact by this
  review's independent reproduction (Section 4 above). This review
  does not attempt to explain it, per this task's restriction against
  adding new metrics or analysis beyond reproduction.

**Remaining limitations, carried forward from the original report and
unchanged by this reproduction:**

1. 19 of 502 nominal window dates (2024-07-17 through 2024-08-12) could
   not be evaluated because no `Score` row exists for any ETF in that
   range — independently confirmed against the live database (Section 2
   above), not merely re-stated from the report.
2. The evaluated window spans a single ~2-year historical period, not
   multiple independent regimes.
3. The bottom-tail overlap asymmetry remains unexplained (flagged, not
   resolved, by either the original report or this review).
4. Gate 4 (no unresolved specification degrees of freedom) is out of
   scope for both the original report and this review.
5. No Level 3 (organizationally independent) review is available on
   this platform for any gate, including this one.

---

## Evidence produced by this review

- This document.
- No file was modified. The one file this review's script re-run wrote
  to (`research_archive/reference_h3/gate1_independence_analysis_2026-07-19.json`)
  was backed up before the re-run and restored byte-for-byte afterward;
  `git status --short` at the end of this review shows the same three
  untracked files it showed at the start, plus this document.
- The independent second-implementation script used for Section 4.3 was
  written and run in this review's scratch workspace, outside the
  repository, and is not part of the repository's evidence trail; its
  role was to cross-check the committed script's arithmetic with
  disjoint code, not to serve as a second archived artifact. If a
  permanent, repository-committed independent-implementation artifact
  is wanted for the archive, that is a decision for whoever maintains
  `research_archive/reference_h3/`, not something this review adds
  unilaterally.
