"""Tests for core/research/lifecycle.py -- the pure phase-transition
decision primitive (Phase 4 / Step 9, increment B-3a).
"""

from __future__ import annotations

import dataclasses

import pytest

from core.research.lifecycle import (
    Authorization,
    IllegalPhaseTransition,
    TransitionDecision,
    TransitionRecordKind,
    UnauthorizedTransition,
    advance_phase,
)
from core.shared.lifecycle_phase import LifecyclePhase
from core.validation.gate_result import GateStatus

PHASES_IN_ORDER = list(LifecyclePhase)
VALID_SUCCESSOR_PAIRS = list(zip(PHASES_IN_ORDER, PHASES_IN_ORDER[1:]))


def _authorization(**overrides: object) -> Authorization:
    defaults: dict[str, object] = dict(
        reviewer_level="Level 2",
        authorizer="a.reviewer",
        ambiguity_acknowledged=False,
        override_acknowledged=False,
    )
    defaults.update(overrides)
    return Authorization(**defaults)  # type: ignore[arg-type]


# --- Phase ordering ----------------------------------------------------------


def test_lifecycle_phase_ordering_has_seven_successor_pairs() -> None:
    """Sanity check that the module is testing against the real eight-phase
    vocabulary, not a stale local copy of it."""
    assert len(PHASES_IN_ORDER) == 8
    assert len(VALID_SUCCESSOR_PAIRS) == 7


@pytest.mark.parametrize("from_phase, to_phase", VALID_SUCCESSOR_PAIRS)
def test_every_valid_successor_transition_is_accepted_on_pass(
    from_phase: LifecyclePhase, to_phase: LifecyclePhase
) -> None:
    decision = advance_phase(from_phase, to_phase, GateStatus.PASS, _authorization())

    assert decision.from_phase is from_phase
    assert decision.to_phase is to_phase
    assert decision.kind is TransitionRecordKind.NORMAL


def test_self_transition_fails() -> None:
    with pytest.raises(IllegalPhaseTransition):
        advance_phase(
            LifecyclePhase.PRE_VALIDATION,
            LifecyclePhase.PRE_VALIDATION,
            GateStatus.PASS,
            _authorization(),
        )


def test_backwards_transition_fails() -> None:
    with pytest.raises(IllegalPhaseTransition):
        advance_phase(
            LifecyclePhase.VALIDATION,
            LifecyclePhase.IMPLEMENTATION,
            GateStatus.PASS,
            _authorization(),
        )


def test_skip_transition_fails() -> None:
    with pytest.raises(IllegalPhaseTransition):
        advance_phase(
            LifecyclePhase.HYPOTHESIS,
            LifecyclePhase.PRE_VALIDATION,
            GateStatus.PASS,
            _authorization(),
        )


def test_archive_cannot_advance() -> None:
    for to_phase in PHASES_IN_ORDER:
        with pytest.raises(IllegalPhaseTransition):
            advance_phase(
                LifecyclePhase.ARCHIVE,
                to_phase,
                GateStatus.PASS,
                _authorization(),
            )


# --- Gate-status decision behavior -------------------------------------------


def test_pass_creates_normal_decision() -> None:
    decision = advance_phase(
        LifecyclePhase.IMPLEMENTATION,
        LifecyclePhase.VALIDATION,
        GateStatus.PASS,
        _authorization(),
    )

    assert decision.kind is TransitionRecordKind.NORMAL
    assert decision.sequence_status is GateStatus.PASS


def test_ambiguous_without_acknowledgement_is_rejected() -> None:
    with pytest.raises(UnauthorizedTransition):
        advance_phase(
            LifecyclePhase.IMPLEMENTATION,
            LifecyclePhase.VALIDATION,
            GateStatus.AMBIGUOUS,
            _authorization(ambiguity_acknowledged=False),
        )


def test_ambiguous_with_acknowledgement_creates_authorized_with_ambiguity_decision() -> None:
    decision = advance_phase(
        LifecyclePhase.IMPLEMENTATION,
        LifecyclePhase.VALIDATION,
        GateStatus.AMBIGUOUS,
        _authorization(ambiguity_acknowledged=True),
    )

    assert decision.kind is TransitionRecordKind.AUTHORIZED_WITH_AMBIGUITY


def test_fail_without_override_acknowledgement_is_rejected() -> None:
    with pytest.raises(UnauthorizedTransition):
        advance_phase(
            LifecyclePhase.IMPLEMENTATION,
            LifecyclePhase.VALIDATION,
            GateStatus.FAIL,
            _authorization(override_acknowledged=False),
        )


def test_fail_with_override_acknowledgement_creates_override_decision() -> None:
    decision = advance_phase(
        LifecyclePhase.IMPLEMENTATION,
        LifecyclePhase.VALIDATION,
        GateStatus.FAIL,
        _authorization(override_acknowledged=True),
    )

    assert decision.kind is TransitionRecordKind.OVERRIDE


def test_fail_override_kind_is_distinct_from_pass_normal_kind() -> None:
    pass_decision = advance_phase(
        LifecyclePhase.IMPLEMENTATION,
        LifecyclePhase.VALIDATION,
        GateStatus.PASS,
        _authorization(),
    )
    fail_decision = advance_phase(
        LifecyclePhase.IMPLEMENTATION,
        LifecyclePhase.VALIDATION,
        GateStatus.FAIL,
        _authorization(override_acknowledged=True),
    )

    assert pass_decision.kind is not fail_decision.kind
    assert fail_decision.kind is TransitionRecordKind.OVERRIDE
    assert pass_decision.kind is TransitionRecordKind.NORMAL


# --- Immutability -------------------------------------------------------------


def test_authorization_is_immutable() -> None:
    authorization = _authorization()
    with pytest.raises(dataclasses.FrozenInstanceError):
        authorization.ambiguity_acknowledged = True  # type: ignore[misc]


def test_transition_decision_is_immutable() -> None:
    decision = advance_phase(
        LifecyclePhase.HYPOTHESIS,
        LifecyclePhase.RESEARCH_PROPOSAL,
        GateStatus.PASS,
        _authorization(),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        decision.kind = TransitionRecordKind.OVERRIDE  # type: ignore[misc]


# --- No persistence fields have crept in -------------------------------------


def test_transition_decision_has_no_persistence_fields() -> None:
    field_names = {f.name for f in dataclasses.fields(TransitionDecision)}

    assert field_names == {
        "from_phase",
        "to_phase",
        "sequence_status",
        "kind",
        "authorization",
    }
    forbidden = {
        "sequence_number",
        "predecessor_hash",
        "timestamp",
        "commit_hash",
        "evidence_refs",
        "covered_paths",
    }
    assert field_names.isdisjoint(forbidden)


def test_authorization_has_no_persistence_or_governance_fields() -> None:
    field_names = {f.name for f in dataclasses.fields(Authorization)}

    assert field_names == {
        "reviewer_level",
        "authorizer",
        "ambiguity_acknowledged",
        "override_acknowledged",
    }
