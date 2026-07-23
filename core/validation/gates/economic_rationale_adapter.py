"""Thin ``Gate``-protocol adapter over
``evaluate_economic_rationale_gate`` (Phase 4 / Step 9, increment D --
Step 9 Validation Orchestration Proposal Section 6.2).

Unpacks a ``GateContext`` into the gate function's own explicit
parameters and calls it unchanged. The underlying function keeps its
explicit-parameter contract for direct callers (AD-044's rationale
survives intact) -- this adapter is purely additive.

``statistic_name``, ``required_review_level``, ``measurement_key``, and
``repo_root`` are all supplied by whoever constructs the adapter, never
invented here -- the same "never invent it" discipline the gate function
itself already applies to its frozen threshold.
"""

from __future__ import annotations

from pathlib import Path

from core.validation.gate_context import GateContext
from core.validation.gate_result import GateResult
from core.validation.gates.economic_rationale import GATE_NAME, evaluate_economic_rationale_gate


class EconomicRationaleGateAdapter:
    def __init__(
        self,
        *,
        statistic_name: str,
        required_review_level: str,
        measurement_key: str | None = None,
        repo_root: Path | None = None,
    ) -> None:
        self.name = GATE_NAME
        self.required_review_level = required_review_level
        self._statistic_name = statistic_name
        self._measurement_key = measurement_key or GATE_NAME
        self._repo_root = repo_root

    def run(self, context: GateContext) -> GateResult:
        criterion = context.frozen_criteria.get(self._measurement_key)
        return evaluate_economic_rationale_gate(
            statistic_name=self._statistic_name,
            measured_value=context.measurements[self._measurement_key],
            frozen_threshold=None if criterion is None else criterion.threshold,
            threshold_direction=None if criterion is None else criterion.direction,
            freeze_commit_ref=context.freeze_commit_ref,
            freeze_covered_paths=context.freeze_covered_paths,
            evidence_refs=context.evidence_refs,
            decision=context.decision,
            repo_root=self._repo_root,
        )
