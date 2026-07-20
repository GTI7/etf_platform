# positive_control_phase3/

Phase 3 (Pre-validation) evidence for the Positive Control Validation
Study, per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 Phase 3 and
`docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md` §1.6 / §2 / §2a.
**Not a Methodology Freeze** — no `methodology.md` exists, and nothing
in this directory is effective under
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §3 until it is committed and
recorded in `decision_log.md` with a commit hash (neither has happened
yet — this directory is uncommitted as of its creation).

## Contents

- **`pilot_results.md`** — the full report: purpose, RNG procedure,
  parameters, executed gates, results, limitations, and governance
  status. Start here.
- **`generator_fidelity_results.json`** — machine-readable output of
  the generator-fidelity gate (V2 §2), all three checks, all lags, all
  25 seeds, at the anchor dimension point.
- **`rho_calibration.csv`** — machine-readable output of the reduced
  preliminary `w ↔ ρ_true` calibration pilot (V2 §1.6), 11 of the
  frozen 41 grid points.
- **`decision_log.md`** — append-only record of this cycle's Phase 3
  decision points, per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5.

## Headline result

The generator-fidelity gate's **gate 1 (return-side ACF) PASSES**;
**gates 2 (score-side ACF) and 3 (combined daily-IC-series ACF decay)
FAIL** at the anchor dimension point (25 instruments, 463 days, h=20,
β=0.30, R=25 replications). This is why
`docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md` §16 reads NOT
READY FOR FREEZE rather than READY FOR FREEZE — see that document's
§1.3 and §16, and `pilot_results.md` §5b here, for the full account of
what the failure means and what is and is not yet explained about it.

No real market outcome data (or any other real ETF data) appears
anywhere in this directory — every figure here is a property of the
synthetic generator in V2 §1.2 and the statistical primitives in
`core/statistics/significance.py`, checked against each other.

## Producing script

[`experiments/positive_control_phase3_pilot.py`](../../experiments/positive_control_phase3_pilot.py)
— pure standard library, SHA-256-derived seeding (V2 §8), imports
`core/statistics/significance.py`'s primitives unmodified.
