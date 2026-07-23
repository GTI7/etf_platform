"""Thin ``Gate``-protocol adapter over
``evaluate_signal_independence_gate`` (Phase 4 / Step 9, increment D --
Step 9 Validation Orchestration Proposal Section 6.2).

Unpacks a ``GateContext`` into the gate function's own explicit
parameters and calls it unchanged. The underlying function keeps its
explicit-parameter contract for direct callers (AD-044's rationale
survives intact) -- this adapter is purely additive.

``required_review_level``, ``measurement_key``, and ``repo_root`` are
all supplied by whoever constructs the adapter, never invented here.
"""

from __future__ import annotations

from pathlib import Path

from core.validation.gate_context import GateContext
from core.validation.gate_result import GateResult
from core.validation.gates.signal_independence import GATE_NAME, evaluate_signal_independence_gate


class SignalIndependenceGateAdapter:
    def __init__(
        self,
        *,
        required_review_level: str,
        measurement_key: str | None = None,
        repo_root: Path | None = None,
    ) -> None:
        self.name = GATE_NAME
        self.required_review_level = required_review_level
        self._measurement_key = measurement_key or GATE_NAME
        self._repo_root = repo_root

    def run(self, context: GateContext) -> GateResult:
        criterion = context.frozen_criteria.get(self._measurement_key)
        return evaluate_signal_independence_gate(
            measured_overlap=context.measurements[self._measurement_key],
            frozen_threshold=None if criterion is None else criterion.threshold,
            threshold_direction=None if criterion is None else criterion.direction,
            freeze_commit_ref=context.freeze_commit_ref,
            freeze_covered_paths=context.freeze_covered_paths,
            evidence_refs=context.evidence_refs,
            decision=context.decision,
            repo_root=self._repo_root,
        )
