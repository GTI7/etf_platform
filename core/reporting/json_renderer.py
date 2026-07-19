"""``render_json`` -- serialize a ``ReportModel`` to a JSON string,
nothing else (docs/STEP_8_REPORTING_DESIGN.md Section 4).

Output key set is exactly ``ReportModel``'s seven field names, in a
fixed order, so two calls on equal input produce byte-identical output.
Takes a ``ReportModel`` only; never imports ``core.validation`` or
anything outside ``core.reporting``.
"""

from __future__ import annotations

import json

from core.reporting.report_model import ReportModel

_FIELD_ORDER = (
    "gate_name",
    "status",
    "summary",
    "evidence_refs",
    "reviewer",
    "review_level",
    "decided_at",
)


def render_json(model: ReportModel) -> str:
    payload = {field: getattr(model, field) for field in _FIELD_ORDER}
    return json.dumps(payload)
