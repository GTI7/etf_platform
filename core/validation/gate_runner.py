"""``GateRunner`` -- dispatches named ``Gate``\\ s against a
``GateContext`` and, for a sequence, emits an in-memory ``GateRunRecord``
envelope (Phase 4 / Step 9, increment D -- Step 9 Validation
Orchestration Proposal Section 6.1;
docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md Section 4.2 row D;
docs/ARCHITECTURE_DECISIONS.md AD-049).

**In scope:** hold an explicit registry of named gates (no
auto-discovery); dispatch a gate by name; run an ordered sequence and
return an ordered result set; bracket the sequence with freeze
verification so it cannot straddle a freeze change; emit a run envelope
binding results to the inputs that produced them.

**Out of scope, permanently:** computing any statistic (AD-041 -- the
runner carries measurements, it does not produce them); deciding what a
phase requires (``ValidationRegistry``'s job); deciding whether a
project may advance (Research's job, Phase E); writing any file (R1
ruling, 2026-07-24 -- ``GateRunRecord`` persistence is deferred to Phase
E); importing ``core.governance.decision_recorder`` or
``core.governance.pinned_worktree`` -- the former is Phase E's binding
point, the latter would turn a comparison engine into a code-execution
engine.

**No module-level mutable registry (INV-8).** Each ``GateRunner``
instance owns its own registry; two runners in one process share no
state, mirroring ``core.research.project_registry.ProjectRegistry``.

**No aggregation (AD-049 part 3).** ``run_sequence`` never computes a
PASS/FAIL/AMBIGUOUS verdict over its outcomes -- that rule is a pure
function that belongs in Research (Phase E), not here.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

from core.governance.canonical_jsonl import canonical_bytes
from core.governance.freeze_verifier import FreezeStatus, verify_freeze
from core.shared.clock import Clock
from core.validation.gate import Gate
from core.validation.gate_context import GateContext
from core.validation.gate_result import GateResult
from core.validation.gate_run_record import GateExecutionOutcome, GateRunRecord


def _context_digest(context: GateContext) -> str:
    """`sha256:<64 lowercase hex>` over the canonical serialization of
    exactly the two GateContext fields §6.7 names: `measurements` and
    `frozen_criteria`. Everything else in the context (freeze basis,
    evidence refs, decision, provenance) is recorded on the envelope in
    its own field already and is deliberately excluded here."""
    payload = {
        "measurements": {name: str(value) for name, value in context.measurements.items()},
        "frozen_criteria": {
            name: {
                "threshold": None if criterion.threshold is None else str(criterion.threshold),
                "direction": criterion.direction,
            }
            for name, criterion in context.frozen_criteria.items()
        },
    }
    return "sha256:" + hashlib.sha256(canonical_bytes(payload)).hexdigest()


class GateRunner:
    def __init__(self) -> None:
        self._gates: dict[str, Gate] = {}

    def register_gate(self, gate: Gate) -> None:
        if gate.name in self._gates:
            raise ValueError(f"gate {gate.name!r} is already registered")
        self._gates[gate.name] = gate

    def run_gate(self, gate_name: str, context: GateContext) -> GateResult:
        if gate_name not in self._gates:
            raise KeyError(gate_name)
        return self._gates[gate_name].run(context)

    def run_sequence(
        self,
        gate_names: Sequence[str],
        context: GateContext,
        *,
        clock: Clock,
        code_commit_hash: str,
        repo_root: Path | None = None,
    ) -> GateRunRecord:
        """Run every gate in `gate_names`, in order, against `context`.

        Atomic preflight: every name is resolved against the registry
        *before* any gate executes -- an unknown name refuses the whole
        call rather than producing a partial evidence set. No
        short-circuit: every gate runs even after an earlier FAIL or an
        earlier crash. A gate that raises is captured as an envelope
        error on its `GateExecutionOutcome`, never coerced into a
        `GateStatus` (INV-4).

        `clock` and `code_commit_hash` are injected by the caller --
        this method never reads a system clock and never invokes git for
        its own commit hash (it does invoke git, read-only, via
        `verify_freeze`'s bracket checks, exactly as each gate already
        does internally)."""
        resolved_gates: list[Gate] = []
        for name in gate_names:
            if name not in self._gates:
                raise KeyError(name)
            resolved_gates.append(self._gates[name])

        pre_verification = verify_freeze(
            context.freeze_commit_ref, context.freeze_covered_paths, repo_root=repo_root
        )

        outcomes: list[GateExecutionOutcome] = []
        for name, gate in zip(gate_names, resolved_gates):
            try:
                result = gate.run(context)
            except Exception as exc:  # noqa: BLE001 -- envelope error, never a status (INV-4)
                outcomes.append(
                    GateExecutionOutcome(gate_name=name, result=None, error=f"{type(exc).__name__}: {exc}")
                )
            else:
                outcomes.append(GateExecutionOutcome(gate_name=name, result=result, error=None))

        post_verification = verify_freeze(
            context.freeze_commit_ref, context.freeze_covered_paths, repo_root=repo_root
        )

        bracket_invalidated = (
            pre_verification.status is not FreezeStatus.VERIFIED
            or post_verification.status is not FreezeStatus.VERIFIED
            or pre_verification.resolved_hash != post_verification.resolved_hash
        )

        return GateRunRecord(
            requested_gate_names=tuple(gate_names),
            outcomes=tuple(outcomes),
            pre_freeze_verification=pre_verification,
            post_freeze_verification=post_verification,
            bracket_invalidated=bracket_invalidated,
            context_digest=_context_digest(context),
            measurement_provenance=context.measurement_provenance,
            code_commit_hash=code_commit_hash,
            recorded_at=clock.now(),
        )
