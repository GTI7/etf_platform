# reference_v2_h1/

Frozen evidence for the REFERENCE v2 H1 (low volatility) research
cycle. See `docs/REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md` for the full
close-out report (hypothesis, results, audit conclusions, limitations,
lessons learned, and next steps for the REFERENCE v2 candidate search)
— this directory holds only the raw evidence, not the narrative.

## Contents

- **`reference_v2_h1_significance_report_2026-07-18.json`** — a frozen
  copy of `reference_v2_h1_significance_report.json`, the
  machine-readable output of
  `experiments/validate_reference_v2_h1_significance.py`'s completed
  run (25 ETFs, 421 ranking dates spanning 2024-10-11 to 2026-06-17,
  10,000 permutations, 2,000 bootstrap iterations per block length,
  random seed `2026071801`). This is the exact result the close-out
  report is based on. The gitignored working copy at the repo root
  (`reference_v2_h1_significance_report.json`) will be overwritten by
  any future rerun of that script; this copy will not be.
- **`COMMIT.txt`** — the exact commit hash (`8831d54`) the result was
  produced against. Checking out that commit reproduces the exact
  source code (score definition, panel construction, statistical
  methodology, ETF universe list) that generated this snapshot.

## Verdict recorded in this snapshot

`ARCHIVE` — neither H1-A (primary: LowVol score vs. raw return) nor
H1-B (secondary diagnostic: LowVol score vs. risk-adjusted return)
survived both Holm-Bonferroni-corrected permutation significance and
bootstrap robustness across all three block lengths (20/40/60 days).
Unlike REFERENCE v1's result, both H1-A (IC −0.117225) and H1-B (IC
−0.037941) are permutation-significant but **directionally opposite**
to the hypothesized relationship — lower realized volatility was
associated with lower, not higher, subsequent returns in this sample.
Per the close-out report, this leans more toward evidence against the
hypothesized direction than REFERENCE v1's own result did, but does
not clear the same pre-registered bar in either direction, since no
bootstrap CI (either statistic, any block length) excludes zero.
