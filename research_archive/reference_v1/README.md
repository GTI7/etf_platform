# reference_v1/

Frozen evidence for the REFERENCE v1 research cycle. See
`docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md` for the full close-out report
(hypothesis, results, audit conclusions, limitations, lessons learned,
and REFERENCE v2 entry requirements) — this directory holds only the
raw evidence, not the narrative.

## Contents

- **`reference_v1_significance_report_2026-07-18.json`** — a frozen
  copy of `reference_v1_significance_report.json`, the machine-readable
  output of `experiments/validate_reference_v1_significance.py`'s
  completed run (25 ETFs, 2024-07-17 to 2026-07-17, 463 ranking dates,
  10,000 permutations, 2,000 bootstrap iterations per block length,
  random seed `20260718`). This is the exact result the close-out
  report and its preceding verification audit are based on. The
  gitignored working copy at the repo root
  (`reference_v1_significance_report.json`) will be overwritten by any
  future rerun of that script; this copy will not be.
- **`COMMIT.txt`** — the exact commit hash (`19771d4`) the result was
  produced against. Checking out that commit reproduces the exact
  source code (scoring profile definition, statistical methodology,
  ETF universe list) that generated this snapshot.

## Verdict recorded in this snapshot

`ARCHIVE` — no statistic (MOMENTUM IC, VALUE IC, raw blend IC,
normalized blend IC, or top-vs-bottom spread) survived both
Holm-Bonferroni-corrected permutation significance and bootstrap
robustness across all three block lengths (20/40/60 days). Per the
close-out report, this is classified as **insufficient statistical
power**, not evidence against the hypothesis and not an implementation
defect — the binding constraint is an effective sample size of roughly
23 independent 20-day windows behind the 463 observed, overlapping
ranking dates.
