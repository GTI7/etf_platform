from __future__ import annotations

import dataclasses

import pytest

from core.validation.gate_result import DecisionMetadata, GateResult, GateStatus


def _decision() -> DecisionMetadata:
    return DecisionMetadata(reviewer="test-reviewer", review_level="Level 2", decided_at="2026-07-19")


def test_gate_status_is_a_three_way_enum_not_a_boolean() -> None:
    assert {member.value for member in GateStatus} == {"pass", "fail", "ambiguous"}
    assert GateStatus.PASS is not GateStatus.FAIL
    assert GateStatus.AMBIGUOUS not in (GateStatus.PASS, GateStatus.FAIL)


def test_decision_metadata_is_frozen() -> None:
    decision = _decision()
    with pytest.raises(dataclasses.FrozenInstanceError):
        decision.reviewer = "someone-else"  # type: ignore[misc]


def test_gate_result_is_frozen() -> None:
    result = GateResult(
        gate_name="signal_independence",
        status=GateStatus.PASS,
        summary="measured=1 >= threshold=1: meets the frozen acceptance criterion.",
        evidence_refs=("research_archive/reference_h3/gate1_independence_analysis_2026-07-19.json",),
        decision=_decision(),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.status = GateStatus.FAIL  # type: ignore[misc]


def test_gate_result_evidence_refs_is_a_tuple() -> None:
    result = GateResult(
        gate_name="economic_rationale",
        status=GateStatus.FAIL,
        summary="does not meet the frozen acceptance criterion.",
        evidence_refs=("a.json", "b.json"),
        decision=_decision(),
    )
    assert isinstance(result.evidence_refs, tuple)
    assert result.evidence_refs == ("a.json", "b.json")


def test_gate_result_passed_property_reflects_status() -> None:
    passing = GateResult(
        gate_name="economic_rationale",
        status=GateStatus.PASS,
        summary="meets criterion",
        evidence_refs=(),
        decision=_decision(),
    )
    failing = dataclasses.replace(passing, status=GateStatus.FAIL)
    ambiguous = dataclasses.replace(passing, status=GateStatus.AMBIGUOUS)

    assert passing.passed is True
    assert failing.passed is False
    assert ambiguous.passed is False
