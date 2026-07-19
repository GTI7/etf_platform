"""``build_report`` -- the only seam in ``core.reporting`` permitted to
import ``core.validation`` (docs/ARCHITECTURE_DECISIONS.md AD-046,
docs/STEP_8_REPORTING_DESIGN.md Section 3).

Constructs a ``ReportModel`` whose every field is a direct copy of the
corresponding ``GateResult``/``DecisionMetadata`` field. The only two
transformations allowed: ``GateStatus`` -> its ``.value`` string (a
type-boundary choice, not a semantic one), and flattening
``decision.{reviewer,review_level,decided_at}`` to the top level. No
other transformation, validation, or I/O.
"""

from __future__ import annotations

from core.reporting.report_model import ReportModel
from core.validation.gate_result import GateResult


def build_report(gate_result: GateResult) -> ReportModel:
    return ReportModel(
        gate_name=gate_result.gate_name,
        status=gate_result.status.value,
        summary=gate_result.summary,
        evidence_refs=gate_result.evidence_refs,
        reviewer=gate_result.decision.reviewer,
        review_level=gate_result.decision.review_level,
        decided_at=gate_result.decision.decided_at,
    )
