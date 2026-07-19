from __future__ import annotations

import pytest

from core.reporting.report_builder import build_report
from core.validation.gate_result import DecisionMetadata, GateResult, GateStatus


def _decision() -> DecisionMetadata:
    return DecisionMetadata(reviewer="test-reviewer", review_level="Level 2", decided_at="2026-07-19")


def _gate_result(status: GateStatus) -> GateResult:
    return GateResult(
        gate_name="signal_independence",
        status=status,
        summary="measured=1 >= threshold=1: meets the frozen acceptance criterion.",
        evidence_refs=("a.json", "b.json"),
        decision=_decision(),
    )


@pytest.mark.parametrize("status", list(GateStatus))
def test_build_report_copies_every_field_verbatim(status: GateStatus) -> None:
    gate_result = _gate_result(status)
    model = build_report(gate_result)

    assert model.gate_name == gate_result.gate_name
    assert model.summary == gate_result.summary
    assert model.evidence_refs == gate_result.evidence_refs
    assert model.status == gate_result.status.value
    assert model.reviewer == gate_result.decision.reviewer
    assert model.review_level == gate_result.decision.review_level
    assert model.decided_at == gate_result.decision.decided_at


def test_build_report_evidence_refs_order_is_preserved() -> None:
    gate_result = _gate_result(GateStatus.PASS)
    model = build_report(gate_result)
    assert model.evidence_refs == ("a.json", "b.json")


def test_build_report_status_value_for_every_enum_member() -> None:
    assert build_report(_gate_result(GateStatus.PASS)).status == "pass"
    assert build_report(_gate_result(GateStatus.FAIL)).status == "fail"
    assert build_report(_gate_result(GateStatus.AMBIGUOUS)).status == "ambiguous"
