from __future__ import annotations

import dataclasses

import pytest

from core.reporting.report_model import ReportModel


def _model(**overrides: object) -> ReportModel:
    fields: dict[str, object] = dict(
        gate_name="signal_independence",
        status="pass",
        summary="measured=1 >= threshold=1: meets the frozen acceptance criterion.",
        evidence_refs=("a.json", "b.json"),
        reviewer="test-reviewer",
        review_level="Level 2",
        decided_at="2026-07-19",
    )
    fields.update(overrides)
    return ReportModel(**fields)  # type: ignore[arg-type]


def test_report_model_is_frozen() -> None:
    model = _model()
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.status = "fail"  # type: ignore[misc]


def test_report_model_evidence_refs_is_a_tuple() -> None:
    model = _model()
    assert isinstance(model.evidence_refs, tuple)
    assert model.evidence_refs == ("a.json", "b.json")


def test_report_model_holds_seven_fields_verbatim() -> None:
    model = _model()
    assert model.gate_name == "signal_independence"
    assert model.status == "pass"
    assert model.summary == "measured=1 >= threshold=1: meets the frozen acceptance criterion."
    assert model.reviewer == "test-reviewer"
    assert model.review_level == "Level 2"
    assert model.decided_at == "2026-07-19"
