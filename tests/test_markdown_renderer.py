from __future__ import annotations

from core.reporting.markdown_renderer import render_markdown
from core.reporting.report_model import ReportModel

_DENYLIST = ("approved", "recommend", "should")


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


def test_render_markdown_contains_summary_verbatim() -> None:
    model = _model()
    assert model.summary in render_markdown(model)


def test_render_markdown_contains_every_evidence_ref() -> None:
    model = _model()
    output = render_markdown(model)
    for ref in model.evidence_refs:
        assert ref in output


def test_render_markdown_contains_attribution_fields() -> None:
    model = _model()
    output = render_markdown(model)
    assert model.reviewer in output
    assert model.review_level in output
    assert model.decided_at in output


def test_render_markdown_displays_status_as_a_fixed_label() -> None:
    assert "PASS" in render_markdown(_model())

    failing = ReportModel(
        gate_name="economic_rationale",
        status="fail",
        summary="does not meet the frozen acceptance criterion.",
        evidence_refs=(),
        reviewer="test-reviewer",
        review_level="Level 3",
        decided_at="2026-07-20",
    )
    assert "FAIL" in render_markdown(failing)

    ambiguous = ReportModel(
        gate_name="signal_independence",
        status="ambiguous",
        summary="freeze verification did not return VERIFIED.",
        evidence_refs=(),
        reviewer="test-reviewer",
        review_level="Level 2",
        decided_at="2026-07-20",
    )
    assert "AMBIGUOUS" in render_markdown(ambiguous)


def test_render_markdown_does_not_introduce_narrative_language() -> None:
    output = render_markdown(_model()).lower()
    for word in _DENYLIST:
        assert word not in output
