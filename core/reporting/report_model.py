"""``ReportModel`` -- the single boundary type between Validation and
Reporting's renderers (docs/ARCHITECTURE_DECISIONS.md AD-046,
docs/STEP_8_REPORTING_DESIGN.md Section 2).

Every field is a direct, unmodified copy of a ``GateResult``/
``DecisionMetadata`` field. Neither renderer imports
``core.validation.gate_result`` because this type exists precisely so
they don't have to.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReportModel:
    gate_name: str
    status: str
    summary: str
    evidence_refs: tuple[str, ...]
    reviewer: str
    review_level: str
    decided_at: str
