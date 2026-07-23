"""Pure phase-transition decision primitive (Phase 4 / Step 9, increment
B-3a -- see docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md Section 4.2,
Phase B, and docs/ARCHITECTURE_DECISIONS.md AD-050).

This module is the pure decision half of `advance_phase()` only: given a
candidate transition, a gate `sequence_status`, and a recorded human
`Authorization`, it decides whether the transition is legal and what kind
of decision record it produces. It is deliberately **not**:

- a lifecycle engine, persistence layer, `DecisionRecorder`, `GateRunner`,
  governance service, or phase storage mechanism;
- wired to any evidence precondition AD-050 states for a *real* advance
  (a `GateRunRecord` per gate, freeze verification, chain anchoring) --
  those depend on `DecisionRecorder` (Phase C) and `GateRunner` (Phase D),
  neither of which exists yet. Non-negotiable ordering requires B-3
  before C, so this primitive cannot depend on either.

`advance_phase()` takes plain values and returns a plain value. No
filesystem access, no database access, no git access, no logging writes,
no mutation, no external services.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.shared.lifecycle_phase import LifecyclePhase
from core.validation.gate_result import GateStatus

_PHASE_ORDER: tuple[LifecyclePhase, ...] = tuple(LifecyclePhase)
_PHASE_INDEX: dict[LifecyclePhase, int] = {
    phase: index for index, phase in enumerate(_PHASE_ORDER)
}


class IllegalPhaseTransition(ValueError):
    """Raised when `from_phase -> to_phase` is not `Phase[i] -> Phase[i+1]`."""


class UnauthorizedTransition(ValueError):
    """Raised when `authorization` does not satisfy what `sequence_status`
    requires (AD-050 part 4's authorization table)."""


class TransitionRecordKind(str, Enum):
    """Which of AD-050 part 4's three record shapes a decision produced.
    FAIL's `OVERRIDE` must never read as equivalent to `NORMAL`."""

    NORMAL = "normal"
    AUTHORIZED_WITH_AMBIGUITY = "authorized_with_ambiguity"
    OVERRIDE = "override"


@dataclass(frozen=True, slots=True)
class Authorization:
    """A recorded human authorization. Recorded, never adjudicated: this
    module does not parse `reviewer_level`, compare it against any other
    level, or enforce a numeric hierarchy (Standard Section 4)."""

    reviewer_level: str
    authorizer: str
    ambiguity_acknowledged: bool = False
    override_acknowledged: bool = False


@dataclass(frozen=True, slots=True)
class TransitionDecision:
    """The outcome of one `advance_phase()` call. Not the persisted
    record -- carries no `DecisionRecorder` fields (sequence number,
    predecessor hash, timestamp, commit hash, evidence refs, covered
    paths)."""

    from_phase: LifecyclePhase
    to_phase: LifecyclePhase
    sequence_status: GateStatus
    kind: TransitionRecordKind
    authorization: Authorization


def _check_single_step_advance(from_phase: LifecyclePhase, to_phase: LifecyclePhase) -> None:
    from_index = _PHASE_INDEX[from_phase]
    to_index = _PHASE_INDEX[to_phase]
    if to_index != from_index + 1:
        raise IllegalPhaseTransition(
            f"{from_phase!r} -> {to_phase!r} is not an allowed single-step "
            "advance (self, backwards, skipped, and post-Archive "
            "transitions are all rejected)"
        )


def advance_phase(
    from_phase: LifecyclePhase,
    to_phase: LifecyclePhase,
    sequence_status: GateStatus,
    authorization: Authorization,
) -> TransitionDecision:
    """Decide whether `from_phase -> to_phase` is legal under
    `sequence_status`, given `authorization`. Pure function: same inputs,
    same output, every time.

    Never advances on its own initiative -- `authorization` is required
    at every `sequence_status` (AD-050 part 4). `sequence_status` decides
    only what kind of authorization is required and how the decision is
    recorded, never whether a machine may proceed unattended.
    """
    _check_single_step_advance(from_phase, to_phase)

    if sequence_status is GateStatus.PASS:
        kind = TransitionRecordKind.NORMAL
    elif sequence_status is GateStatus.AMBIGUOUS:
        if not authorization.ambiguity_acknowledged:
            raise UnauthorizedTransition(
                "AMBIGUOUS sequence_status requires "
                "authorization.ambiguity_acknowledged=True"
            )
        kind = TransitionRecordKind.AUTHORIZED_WITH_AMBIGUITY
    else:
        assert sequence_status is GateStatus.FAIL
        if not authorization.override_acknowledged:
            raise UnauthorizedTransition(
                "FAIL sequence_status requires "
                "authorization.override_acknowledged=True"
            )
        kind = TransitionRecordKind.OVERRIDE

    return TransitionDecision(
        from_phase=from_phase,
        to_phase=to_phase,
        sequence_status=sequence_status,
        kind=kind,
        authorization=authorization,
    )
