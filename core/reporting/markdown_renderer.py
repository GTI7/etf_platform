"""``render_markdown`` -- format a ``ReportModel``'s fields into a
Markdown document (docs/STEP_8_REPORTING_DESIGN.md Section 5).

Replaces only the mechanical, templated portions of a hand-written
determination document (status / summary / evidence refs / attribution)
-- never the narrative portions (economic rationale prose, "known
limitations"), which stay human-written per AD-038's reasoning. Takes a
``ReportModel`` only; never imports ``core.validation`` or anything
outside ``core.reporting``.
"""

from __future__ import annotations

from core.reporting.report_model import ReportModel

_STATUS_LABELS = {
    "pass": "PASS",
    "fail": "FAIL",
    "ambiguous": "AMBIGUOUS",
}


def render_markdown(model: ReportModel) -> str:
    status_label = _STATUS_LABELS.get(model.status, model.status)
    evidence_lines = "\n".join(f"- {ref}" for ref in model.evidence_refs)
    lines = [
        f"# {model.gate_name}",
        "",
        f"**Status:** {status_label}",
        "",
        model.summary,
        "",
        "## Evidence",
        "",
        evidence_lines,
        "",
        "## Decision",
        "",
        f"- Reviewer: {model.reviewer}",
        f"- Review level: {model.review_level}",
        f"- Decided at: {model.decided_at}",
    ]
    return "\n".join(lines)
