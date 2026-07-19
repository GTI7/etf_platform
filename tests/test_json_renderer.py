from __future__ import annotations

import json

from core.reporting.json_renderer import render_json
from core.reporting.report_model import ReportModel

_EXPECTED_KEYS = {
    "gate_name",
    "status",
    "summary",
    "evidence_refs",
    "reviewer",
    "review_level",
    "decided_at",
}


def _model() -> ReportModel:
    return ReportModel(
        gate_name="signal_independence",
        status="pass",
        summary="measured=1 >= threshold=1: meets the frozen acceptance criterion.",
        evidence_refs=("a.json", "b.json"),
        reviewer="test-reviewer",
        review_level="Level 2",
        decided_at="2026-07-19",
    )


def test_render_json_round_trips_every_field() -> None:
    model = _model()
    parsed = json.loads(render_json(model))

    assert parsed["gate_name"] == model.gate_name
    assert parsed["status"] == model.status
    assert parsed["summary"] == model.summary
    assert parsed["evidence_refs"] == list(model.evidence_refs)
    assert parsed["reviewer"] == model.reviewer
    assert parsed["review_level"] == model.review_level
    assert parsed["decided_at"] == model.decided_at


def test_render_json_key_set_is_exactly_report_model_fields() -> None:
    parsed = json.loads(render_json(_model()))
    assert set(parsed.keys()) == _EXPECTED_KEYS


def test_render_json_is_byte_identical_across_calls() -> None:
    model = _model()
    assert render_json(model) == render_json(model)


def test_render_json_preserves_evidence_refs_order() -> None:
    model = ReportModel(
        gate_name="economic_rationale",
        status="fail",
        summary="does not meet the frozen acceptance criterion.",
        evidence_refs=("z.json", "a.json"),
        reviewer="test-reviewer",
        review_level="Level 3",
        decided_at="2026-07-20",
    )
    parsed = json.loads(render_json(model))
    assert parsed["evidence_refs"] == ["z.json", "a.json"]
