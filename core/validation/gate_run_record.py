"""``GateRunRecord`` -- the additive run envelope binding one
``GateRunner.run_sequence()`` call's ordered results to the inputs that
produced them (Phase 4 / Step 9, increment D -- Step 9 Validation
Orchestration Proposal Section 6.7; docs/ARCHITECTURE_DECISIONS.md
AD-049 part 3, AD-051).

**In-memory validation artifact only (R1 ruling, 2026-07-24).**
Persistence of ``GateRunRecord`` is out of scope for Phase D and is
explicitly deferred to Phase E, where Research owns archive writes. This
module therefore defines plain, frozen dataclasses only -- no
serialization method, no file path, no write helper, and no import of
``core.governance.canonical_jsonl``'s write/read halves or of
``core.governance.decision_recorder``. A8-R5's location rule
(``research_archive/<cycle_name>/experiment_results/``, dated filename)
governs only *if and when* a record is later persisted; nothing in this
module acts on it.

**No aggregate field (AD-049 part 3).** ``PLATFORM_ARCHITECTURE_V1.md``
Section 4.2 assigns cycle-level aggregation to Research by name -- "only
Research aggregates gate outcomes into" a terminal decision. This record
stores the ordered per-gate outcomes only; there is no ``verdict`` or
``sequence_status`` field here, and none should ever be added without a
new AD reopening AD-049 part 3.

**``GateStatus`` stays three-valued (INV-4).** A gate that raises is not
given a fourth status. ``GateExecutionOutcome`` carries the crash as an
``error`` string instead -- the run failed to produce a verdict for that
gate, which is categorically different from the gate concluding one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.governance.freeze_verifier import VerificationResult
from core.validation.gate_result import GateResult


@dataclass(frozen=True, slots=True)
class GateExecutionOutcome:
    """One gate's outcome within a sequence: exactly one of ``result``
    (the gate concluded, mechanically, per its own ``GateStatus``) or
    ``error`` (the gate raised; no status was ever reached) is set."""

    gate_name: str
    result: GateResult | None
    error: str | None

    def __post_init__(self) -> None:
        if (self.result is None) == (self.error is None):
            raise ValueError(
                "GateExecutionOutcome must carry exactly one of result or error, "
                "never both and never neither"
            )


@dataclass(frozen=True, slots=True)
class GateRunRecord:
    """In-memory-only envelope for one ``run_sequence()`` call. Closed
    field set -- ``tests/test_gate_runner.py`` pins the exact field set,
    so adding a field (an aggregate, in particular) fails a test and
    forces a new AD rather than a commit, mirroring
    ``core.governance.decision_recorder.DecisionRecord``'s convention."""

    requested_gate_names: tuple[str, ...]
    outcomes: tuple[GateExecutionOutcome, ...]
    pre_freeze_verification: VerificationResult
    post_freeze_verification: VerificationResult
    bracket_invalidated: bool
    context_digest: str
    measurement_provenance: str | None
    code_commit_hash: str
    recorded_at: datetime
