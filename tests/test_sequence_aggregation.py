"""Tests for core/research/sequence_aggregation.py -- the pure gate
-sequence aggregation (Phase 4 / Step 9, increment E; AD-059 step 5)."""

from __future__ import annotations

import pytest

from core.research.sequence_aggregation import EmptyGateSequence, aggregate_sequence_status
from core.validation.gate_result import GateStatus

P = GateStatus.PASS
F = GateStatus.FAIL
A = GateStatus.AMBIGUOUS


# --- truth table --------------------------------------------------------


@pytest.mark.parametrize(
    "statuses, expected",
    [
        # all pass -> PASS
        ([P], P),
        ([P, P, P], P),
        # any fail -> FAIL
        ([F], F),
        ([P, F], F),
        ([F, P], F),
        ([P, P, F], F),
        # some ambiguous, no fail -> AMBIGUOUS
        ([A], A),
        ([P, A], A),
        ([A, P], A),
        ([P, A, P], A),
        # FAIL dominates AMBIGUOUS
        ([A, F], F),
        ([F, A], F),
        ([P, A, F], F),
        ([F, A, P, A], F),
    ],
)
def test_aggregation_truth_table(statuses: list[GateStatus], expected: GateStatus) -> None:
    assert aggregate_sequence_status(statuses) is expected


def test_fail_dominates_ambiguous_specifically() -> None:
    """The one non-obvious rule, called out on its own: a mix of only
    AMBIGUOUS and FAIL (no PASS) aggregates to FAIL, never AMBIGUOUS."""
    assert aggregate_sequence_status([A, A, F, A]) is F


# --- refusals -----------------------------------------------------------


def test_empty_sequence_is_refused_not_vacuous_pass() -> None:
    with pytest.raises(EmptyGateSequence):
        aggregate_sequence_status([])


def test_non_gate_status_element_is_refused() -> None:
    with pytest.raises(TypeError):
        aggregate_sequence_status(["pass"])  # type: ignore[list-item]


# --- purity -------------------------------------------------------------


def test_aggregation_is_deterministic() -> None:
    statuses = [P, A, P]
    first = aggregate_sequence_status(statuses)
    second = aggregate_sequence_status(statuses)
    assert first is second is A
    # input is not mutated
    assert statuses == [P, A, P]
