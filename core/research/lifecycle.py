"""Research lifecycle: the pure phase-transition primitive **and** the
sole Validation + Governance composition boundary (Phase 4 / Step 9).

Two layers live here, at two altitudes:

**1. `advance_phase()` -- the pure decision primitive (increment B-3a;
docs/ARCHITECTURE_DECISIONS.md AD-050 part 4).** Given a candidate
transition, a gate `sequence_status`, and a recorded human
`Authorization`, it decides whether the transition is legal and what kind
of record it produces. It takes plain values and returns a plain value:
no filesystem, no database, no git, no clock, no mutation. Unchanged by
Phase E.

**2. `compose_transition()` -- the Phase E composition (increment E;
AD-059).** This is the **only** module that imports Validation and
Governance together, and therefore the only legal place a Validation
`GateRunRecord` is bound to a Governance `DecisionRecord` -- because
Governance cannot import Validation, no other layer can perform that
binding at all (AD-050 Migration/status). It validates gate completeness,
refuses a crashed outcome (AD-056) before aggregation, refuses an
invalidated freeze bracket, binds the supplied `GateContext` to the run
record's own verified coverage before trusting either (AD-060 -- a
mismatch refuses the transition), projects the freeze status from the run
record's **stored** verifications only (it never re-runs `verify_freeze`),
aggregates via the pure `aggregate_sequence_status`, re-uses
`advance_phase()` for legality and authorization, passes evidence and
provenance through untouched, and appends exactly one `DecisionRecord`
only after every precondition holds.

This module is still **not** a lifecycle engine, a `GateRunner`, or a
phase-storage mechanism: current phase is **derived** from the transition
chain (AD-058 / `phase_derivation.py`), never stored on `Project`. It
does not compute a statistic (AD-041), decide what a phase requires
(`ValidationRegistry`'s job), read a clock, or invoke git for its own
values -- `recorded_at` and `commit_hash` are injected by the caller,
exactly as `DecisionRecorder.append` and `GateRunner.run_sequence`
require.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum

from core.governance.decision_recorder import (
    AuthorizationRecord,
    DecisionRecord,
    DecisionRecorder,
    GateOutcome,
    read_chain,
    verify_chain_anchored,
)
from core.governance.freeze_verifier import FreezeStatus, VerificationResult
from core.research.phase_derivation import UNKNOWN_PHASE, derive_current_phase
from core.research.sequence_aggregation import aggregate_sequence_status
from core.shared.lifecycle_phase import LifecyclePhase
from core.validation.gate_context import GateContext
from core.validation.gate_result import GateStatus
from core.validation.gate_run_record import GateRunRecord

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


# ---------------------------------------------------------------------------
# Phase E composition (AD-059): bind a Validation GateRunRecord to a
# Governance DecisionRecord. Every refusal below raises *before* the single
# DecisionRecorder.append() call, so a refused transition writes nothing to
# the governance chain.
# ---------------------------------------------------------------------------


class PhaseChainMismatch(ValueError):
    """Raised when a non-genesis transition's `from_phase` does not equal
    the phase derived from the existing chain (AD-058): the chain is
    authoritative, and a supplied phase may not over-claim past it."""


class IncompleteGateSequence(ValueError):
    """Raised when a gate the target phase requires has no result in the
    run record (AD-050 evidence preconditions / AD-059 step 1): a missing
    required gate is a refusal, never an AMBIGUOUS."""


class CrashedGateInSequence(ValueError):
    """Raised when any outcome in the run record crashed -- carries an
    `error`, not a `result` (AD-056). A crash is inadmissible evidence: it
    blocks the transition and no DecisionRecord is written. Never coerced
    to PASS/FAIL/AMBIGUOUS or a fourth status."""


class BracketInvalidated(ValueError):
    """Raised when `GateRunRecord.bracket_invalidated` is True (AD-059
    step 3): the freeze bracket did not hold across the sequence."""


class FreezeNotVerified(ValueError):
    """Raised when the freeze status projected from the run record's
    stored pre/post verifications is not `verified` (AD-059 step 4). No
    AMBIGUOUS conversion -- an unverified freeze refuses the transition."""


class ContextRunRecordMismatch(ValueError):
    """Raised when the supplied `GateContext` does not match the run
    record on the freeze axis: either its `freeze_commit_ref` differs
    from the run record's bracketed commit ref, or its
    `freeze_covered_paths` differ from the paths the run record's own
    stored pre/post verifications were actually run against (AD-060) --
    a guard against recording covered paths that were never the ones
    actually verified."""


class UnanchoredTransition(ValueError):
    """Raised when a non-genesis transition is attempted with no operator
    -supplied `(sequence_number, head_hash)` anchor (AD-050 A5-C9): an
    unanchored append has satisfied *verified intact* but not *anchored*,
    and must not be recorded as though it had."""


class ChainNotAnchored(ValueError):
    """Raised when the supplied anchor does not verify against the chain
    (AD-050 A5-C9): the chain no longer retains a record at the cited
    sequence number with the cited hash."""


def _project_freeze_verification_status(
    pre: VerificationResult, post: VerificationResult
) -> str:
    """Project one freeze-verification status from the run record's
    **stored** bracket ends only. `verify_freeze` is never called here
    (AD-059 step 4). Returns `"verified"` only when both ends are VERIFIED
    and resolved to the same commit hash; otherwise refuses."""
    if (
        pre.status is FreezeStatus.VERIFIED
        and post.status is FreezeStatus.VERIFIED
        and pre.resolved_hash is not None
        and pre.resolved_hash == post.resolved_hash
    ):
        return "verified"
    raise FreezeNotVerified(
        "freeze bracket is not verified from stored artifacts -- refusing the "
        f"transition (pre={pre.status.value}, post={post.status.value}, "
        f"pre_hash={pre.resolved_hash!r}, post_hash={post.resolved_hash!r}); "
        "no AMBIGUOUS conversion (AD-059 step 4)"
    )


def _dedupe_stable(refs: Iterable[str]) -> tuple[str, ...]:
    """Stable de-duplication preserving first-appearance order. Pass
    -through only: no string is generated, rewritten, or reordered beyond
    dropping later duplicates (AD-059 step 7)."""
    seen: set[str] = set()
    ordered: list[str] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            ordered.append(ref)
    return tuple(ordered)


def compose_transition(
    *,
    recorder: DecisionRecorder,
    project_id: str,
    from_phase: LifecyclePhase,
    to_phase: LifecyclePhase,
    required_gate_names: Sequence[str],
    run_record: GateRunRecord,
    context: GateContext,
    authorization: Authorization,
    recorded_at: str,
    commit_hash: str,
    expected_anchor: tuple[int, str] | None = None,
) -> DecisionRecord:
    """Compose one phase transition from a Validation run into a
    Governance record, appending exactly one `DecisionRecord` iff every
    precondition holds (AD-059).

    `context` must be the same `GateContext` that produced `run_record`.
    The freeze-axis guard below rejects the most likely mismatch on
    `freeze_commit_ref`, and the covered-path guard (AD-060) rejects a
    `context` whose `freeze_covered_paths` disagree with the paths
    `run_record`'s own stored verifications were actually run against --
    the persisted `DecisionRecord.freeze_covered_paths` is read from
    `run_record`'s verified evidence itself, never from `context`, so a
    caller cannot claim broader or different coverage than what was
    mechanically verified merely by passing a different `context`.
    `recorded_at` and `commit_hash` are injected by the caller;
    this function reads no clock and invokes no git. `expected_anchor` is
    the operator-supplied `(sequence_number, head_hash)` pair read by hand
    from `decision_log.md` (AD-050 A5-C9); it is required for a
    non-genesis transition and unused for genesis (an empty chain has
    nothing to anchor)."""
    chain_path = recorder.chain_path(project_id)
    chain = read_chain(chain_path)

    # 1. Genesis vs. non-genesis (AD-058). Empty chain -> UNKNOWN; the
    #    supplied from_phase is then an explicit human assertion, accepted
    #    as given. A non-empty chain is authoritative: from_phase must
    #    match the derived current phase, never default or over-claim.
    derived = derive_current_phase(chain)
    is_genesis = derived is UNKNOWN_PHASE
    if not is_genesis and derived is not from_phase:
        raise PhaseChainMismatch(
            f"from_phase {from_phase.value!r} does not match the phase derived "
            f"from the chain ({derived.value!r}); the chain is authoritative "
            "(AD-058)"
        )

    # Bind context to run_record on the freeze axis (ContextRunRecordMismatch
    # guard) before trusting anything the context claims about coverage.
    if context.freeze_commit_ref != run_record.pre_freeze_verification.commit_ref:
        raise ContextRunRecordMismatch(
            f"context.freeze_commit_ref {context.freeze_commit_ref!r} does not "
            f"match the run record's bracketed commit ref "
            f"{run_record.pre_freeze_verification.commit_ref!r}"
        )

    # Covered-path binding (AD-060): the persisted DecisionRecord must be
    # mechanically bound to the paths that produced the VERIFIED freeze
    # result, not to whatever a caller's context happens to claim. Checked
    # against both bracket ends -- a real GateRunner always runs pre/post
    # against the same context.freeze_covered_paths, so both must agree
    # with what context claims, or the transition is refused.
    context_paths = frozenset(context.freeze_covered_paths)
    pre_verified_paths = frozenset(run_record.pre_freeze_verification.covered_paths)
    post_verified_paths = frozenset(run_record.post_freeze_verification.covered_paths)
    if context_paths != pre_verified_paths or context_paths != post_verified_paths:
        raise ContextRunRecordMismatch(
            f"context.freeze_covered_paths {sorted(context_paths)!r} does not match "
            f"the paths the run record's freeze verifications actually covered "
            f"(pre={sorted(pre_verified_paths)!r}, post={sorted(post_verified_paths)!r}); "
            "refusing to record coverage that was never mechanically verified (AD-060)"
        )

    # 2. Gate completeness (AD-059 step 1). Every required gate must have a
    #    result in the run record.
    outcome_by_name = {outcome.gate_name: outcome for outcome in run_record.outcomes}
    missing = [name for name in required_gate_names if name not in outcome_by_name]
    if missing:
        raise IncompleteGateSequence(
            f"required gate(s) {missing!r} have no result in the run record -- "
            "a missing required gate is a refusal, never an AMBIGUOUS (AD-050)"
        )

    # 3. Crash rejection (AD-056), BEFORE aggregation. Any crashed outcome
    #    in the run blocks the transition; no DecisionRecord is written.
    crashed = [outcome.gate_name for outcome in run_record.outcomes if outcome.error is not None]
    if crashed:
        raise CrashedGateInSequence(
            f"gate(s) {crashed!r} crashed (envelope error, not a GateStatus) -- "
            "a crash is inadmissible evidence and blocks the transition; no "
            "DecisionRecord is written (AD-056)"
        )

    # 4. Bracket rejection (AD-059 step 3).
    if run_record.bracket_invalidated:
        raise BracketInvalidated(
            "run record's freeze bracket was invalidated across the sequence -- "
            "refusing the transition (AD-059 step 3)"
        )

    # 5. Freeze projection from stored artifacts only (AD-059 step 4).
    freeze_verification_status = _project_freeze_verification_status(
        run_record.pre_freeze_verification, run_record.post_freeze_verification
    )

    # 6. Aggregate (AD-059 step 5). Only admitted (non-crashed) results
    #    reach here; statuses are taken in required-gate order.
    statuses = [outcome_by_name[name].result.status for name in required_gate_names]  # type: ignore[union-attr]
    sequence_status = aggregate_sequence_status(statuses)

    # 7. Legality + authorization via the pure primitive (AD-050 part 4).
    #    Raises IllegalPhaseTransition / UnauthorizedTransition; the record
    #    kind it computes is derivable from the stored fields, so it is not
    #    a separate persisted field (DecisionRecord is a closed set).
    advance_phase(from_phase, to_phase, sequence_status, authorization)

    # 8. Provenance pass-through (AD-059 step 7). Evidence refs are the
    #    admitted gates' own refs, in order, stably de-duplicated, with no
    #    generated strings; reproduction ref is exactly the run record's.
    evidence_refs = _dedupe_stable(
        ref
        for name in required_gate_names
        for ref in outcome_by_name[name].result.evidence_refs  # type: ignore[union-attr]
    )
    reproduction_record_ref = run_record.measurement_provenance

    # 9. Anchor before append (AD-050 A5-C9 / AD-059 step 8). Genesis has
    #    nothing to anchor; a non-genesis transition must supply and verify
    #    an anchor. (DecisionRecorder.append re-checks chain-intact.)
    if not is_genesis:
        if expected_anchor is None:
            raise UnanchoredTransition(
                "non-genesis transition supplied no (sequence_number, head_hash) "
                "anchor -- verified intact is satisfied, anchored is not; refusing "
                "to record as though it were (AD-050 A5-C9)"
            )
        anchor_sequence, anchor_head_hash = expected_anchor
        if not verify_chain_anchored(chain_path, anchor_sequence, anchor_head_hash):
            raise ChainNotAnchored(
                f"anchor (sequence={anchor_sequence}, head_hash={anchor_head_hash!r}) "
                "does not verify against the chain (AD-050 A5-C9)"
            )

    # 10. Append the single record (AD-059 step 8). GateOutcome.status is
    #     the closed three-value transcription vocabulary (AD-057).
    gate_outcomes = tuple(
        GateOutcome(
            gate_name=name,
            status=outcome_by_name[name].result.status.value,  # type: ignore[union-attr]
        )
        for name in required_gate_names
    )
    authorization_record = AuthorizationRecord(
        authorizer=authorization.authorizer,
        reviewer_level=authorization.reviewer_level,
        ambiguity_acknowledged=authorization.ambiguity_acknowledged,
        override_acknowledged=authorization.override_acknowledged,
    )

    return recorder.append(
        project_id=project_id,
        from_phase=from_phase.value,
        to_phase=to_phase.value,
        recorded_at=recorded_at,
        commit_hash=commit_hash,
        freeze_commit_ref=run_record.pre_freeze_verification.commit_ref,
        freeze_verification_status=freeze_verification_status,
        # AD-060: bound to the paths the run record's own verification
        # actually covered, not to context's copy -- the equality guard
        # above has already proven the two agree, but the verified value
        # is the one written, never the caller-supplied one.
        freeze_covered_paths=run_record.pre_freeze_verification.covered_paths,
        gate_outcomes=gate_outcomes,
        authorization=authorization_record,
        evidence_refs=evidence_refs,
        reproduction_record_ref=reproduction_record_ref,
    )
