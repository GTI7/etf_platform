"""Proves the five historical experiments/validate_*.py scripts still
import and still compute correctly after Phase 0's changes, without
requiring the real experiments_etf_universe.db or network access (the
scripts' own run() functions need both; their pure helper functions do
not).

Each script's module-level code (constants, imports) is exercised by
the import itself -- if Phase 0 broke an import path anywhere under
core/, these imports would fail exactly as the real scripts would fail
to even start. Each script's pure, database-free functions are then
called with small synthetic inputs and checked against known-correct
values, the same self-check discipline each script already applies to
itself under its own `if __name__ == "__main__":` guard.

This is a smoke test, not a re-run of any historical result: it does
not touch experiments_etf_universe.db, research_archive/, or any
network resource, and it asserts nothing about H3, REFERENCE v1, or
REFERENCE v2 H1's actual findings.
"""

from __future__ import annotations

from decimal import Decimal


def test_validate_scoring_signal_imports_and_computes_forward_return() -> None:
    from experiments.validate_scoring_signal import forward_return

    assert forward_return(Decimal("100"), Decimal("110")) == Decimal("110") / Decimal("100") - 1


def test_validate_reference_v1_significance_imports_and_computes_correctly() -> None:
    from experiments.validate_reference_v1_significance import _spearman, holm_bonferroni

    assert abs(_spearman([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) - 1.0) < 1e-9
    assert abs(_spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) - (-1.0)) < 1e-9
    assert _spearman([1, 1, 1], [1, 2, 3]) is None

    corrected = holm_bonferroni([("a", 0.01), ("b", 0.04), ("c", 0.03), ("d", 0.005)])
    assert corrected["d"]["adjusted_p_value"] == 0.02
    assert corrected["a"]["adjusted_p_value"] == 0.03
    assert corrected["c"]["adjusted_p_value"] == 0.06
    assert corrected["b"]["adjusted_p_value"] == 0.06


def test_validate_reference_v2_h1_significance_imports_and_computes_realized_volatility() -> None:
    from experiments.validate_reference_v2_h1_significance import realized_volatility

    # Constant price series -> zero log returns -> zero volatility.
    assert realized_volatility([100.0, 100.0, 100.0, 100.0]) == 0.0
    # Exactly 2 prices -> 1 log return -> defined degenerate case, 0.0.
    assert realized_volatility([100.0, 105.0]) == 0.0


def test_validate_h3_gate1_independence_imports_and_computes_score_overlap() -> None:
    from experiments.validate_h3_gate1_independence import score_overlap

    h3_scores = {f"etf{i}": float(i) for i in range(10)}
    momentum_scores = {f"etf{i}": float(i) for i in range(10)}  # identical ranking -> full overlap

    result = score_overlap(h3_scores, momentum_scores, bucket_size=5)

    assert result is not None
    assert result["top_overlap_fraction"] == 1.0
    assert result["bottom_overlap_fraction"] == 1.0
    assert result["n_etfs"] == 10


def test_validate_h3_phase6_economic_validation_imports_and_computes_leg_returns() -> None:
    from experiments.validate_h3_phase6_economic_validation import _leg_returns

    day = {
        "etf_ids": [f"etf{i}" for i in range(10)],
        "raw_blend": {f"etf{i}": float(i) for i in range(10)},
        "forward_return": {f"etf{i}": 0.01 * i for i in range(10)},
    }

    result = _leg_returns(day, "raw_blend", bucket_size=5)

    assert result is not None
    top_return, bottom_return = result
    assert top_return > bottom_return  # higher-scored bucket has higher forward return by construction
