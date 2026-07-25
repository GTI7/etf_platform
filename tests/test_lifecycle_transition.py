"""Tests for core/research/lifecycle.py -- the pure phase-transition
decision primitive (Phase 4 / Step 9, increment B-3a).
"""

from __future__ import annotations

import dataclasses

import pytest

import inspect

from core.research.lifecycle import (
    Authorization,
    IllegalPhaseTransition,
    TransitionDecision,
    TransitionRecordKind,
    UnauthorizedTransition,
    _TRANSITION_AUTHORIZATION_FLOORS,
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


# --- AD-072: transition-authorization floors --------------------------------

ENFORCED_FLOOR_TRANSITIONS = [
    (LifecyclePhase.RESEARCH_PROPOSAL, LifecyclePhase.PRE_VALIDATION, 2),
    (LifecyclePhase.PRE_VALIDATION, LifecyclePhase.METHODOLOGY_FREEZE, 2),
    (LifecyclePhase.METHODOLOGY_FREEZE, LifecyclePhase.IMPLEMENTATION, 2),
    (LifecyclePhase.IMPLEMENTATION, LifecyclePhase.VALIDATION, 1),
    (LifecyclePhase.VALIDATION, LifecyclePhase.DECISION, 2),
    (LifecyclePhase.DECISION, LifecyclePhase.ARCHIVE, 2),
]


def test_floor_table_has_no_hypothesis_or_archive_from_phase_entry() -> None:
    """Structural pin (AD-072): Hypothesis->Research Proposal is out of this
    AD's scope by the Standard's own text, and Archive can never be a
    from_phase at all (test_archive_cannot_advance) -- a floor there would
    be dead policy. A future edit adding either key must fail this test and
    force a deliberate second look, not land silently."""
    keys = set(_TRANSITION_AUTHORIZATION_FLOORS)
    assert not any(from_phase is LifecyclePhase.HYPOTHESIS for from_phase, _ in keys)
    assert not any(from_phase is LifecyclePhase.ARCHIVE for from_phase, _ in keys)


@pytest.mark.parametrize("from_phase, to_phase, required_level", ENFORCED_FLOOR_TRANSITIONS)
def test_sufficient_reviewer_level_is_accepted(
    from_phase: LifecyclePhase, to_phase: LifecyclePhase, required_level: int
) -> None:
    decision = advance_phase(
        from_phase,
        to_phase,
        GateStatus.PASS,
        _authorization(reviewer_level=f"Level {required_level} (adversarial review)"),
    )
    assert decision.kind is TransitionRecordKind.NORMAL


@pytest.mark.parametrize("from_phase, to_phase, required_level", ENFORCED_FLOOR_TRANSITIONS)
def test_higher_than_required_reviewer_level_is_accepted(
    from_phase: LifecyclePhase, to_phase: LifecyclePhase, required_level: int
) -> None:
    decision = advance_phase(
        from_phase, to_phase, GateStatus.PASS, _authorization(reviewer_level="Level 3")
    )
    assert decision.kind is TransitionRecordKind.NORMAL


@pytest.mark.parametrize(
    "from_phase, to_phase, required_level",
    [row for row in ENFORCED_FLOOR_TRANSITIONS if row[2] > 1],
)
def test_insufficient_reviewer_level_is_rejected(
    from_phase: LifecyclePhase, to_phase: LifecyclePhase, required_level: int
) -> None:
    """Every floor above Level 1 has a genuine insufficient case (Level 1
    self-review); Implementation->Validation's own floor is Level 1, the
    platform's lowest level, so it has no insufficient case and is excluded
    here rather than faked."""
    with pytest.raises(UnauthorizedTransition):
        advance_phase(
            from_phase,
            to_phase,
            GateStatus.PASS,
            _authorization(reviewer_level="Level 1 (self-review)"),
        )


def test_phase5_level1_is_sufficient() -> None:
    """Implementation -> Validation's floor is Level 1 (Standard code
    review) -- the platform's lowest level satisfies it. This is the one
    row where the low floor is the point being tested, not merely implied
    by the parametrized sufficiency test above."""
    decision = advance_phase(
        LifecyclePhase.IMPLEMENTATION,
        LifecyclePhase.VALIDATION,
        GateStatus.PASS,
        _authorization(reviewer_level="Level 1 (self-review)"),
    )
    assert decision.kind is TransitionRecordKind.NORMAL


def test_phase5_level2_conformance_check_is_not_mechanically_required() -> None:
    """The Standard's Level 2 conformance check for Implementation is a
    recommendation only (AD-072) -- recording Level 1 or Level 2 must
    produce an identical, unrefused outcome, proving the recommendation
    carries no mechanical weight."""
    level_1 = advance_phase(
        LifecyclePhase.IMPLEMENTATION,
        LifecyclePhase.VALIDATION,
        GateStatus.PASS,
        _authorization(reviewer_level="Level 1 (self-review)"),
    )
    level_2 = advance_phase(
        LifecyclePhase.IMPLEMENTATION,
        LifecyclePhase.VALIDATION,
        GateStatus.PASS,
        _authorization(reviewer_level="Level 2 (conformance check)"),
    )
    assert level_1.kind is level_2.kind is TransitionRecordKind.NORMAL


def test_phase7_decision_to_archive_requires_level_2() -> None:
    with pytest.raises(UnauthorizedTransition):
        advance_phase(
            LifecyclePhase.DECISION,
            LifecyclePhase.ARCHIVE,
            GateStatus.PASS,
            _authorization(reviewer_level="Level 1 (self-review)"),
        )
    decision = advance_phase(
        LifecyclePhase.DECISION,
        LifecyclePhase.ARCHIVE,
        GateStatus.PASS,
        _authorization(reviewer_level="Level 2 (adversarial review)"),
    )
    assert decision.kind is TransitionRecordKind.NORMAL


@pytest.mark.parametrize(
    "malformed_level",
    [
        "2",  # missing "Level " prefix
        "Level four",  # non-numeric level
        "Level 4",  # outside supported range
        "Level 0",  # outside supported range
        "Level 2 self-review",  # free text without parentheses -- not inferred
        "level 2",  # wrong case -- not inferred
        "",  # empty
    ],
)
def test_malformed_reviewer_level_fails_safe(malformed_level: str) -> None:
    """A floor violation and a malformed value both raise
    UnauthorizedTransition -- malformed input is refused, never treated as
    satisfying (or silently failing to satisfy) any floor by default."""
    with pytest.raises(UnauthorizedTransition):
        advance_phase(
            LifecyclePhase.VALIDATION,
            LifecyclePhase.DECISION,
            GateStatus.PASS,
            _authorization(reviewer_level=malformed_level),
        )


# --- E-6 semantics: this record's own value, never the phase's highest ------


def test_advance_phase_has_no_fifth_argument_for_supplementary_evidence() -> None:
    """Structural proof of the E-6 resolution: there is no parameter
    through which a phase's later or higher-level evidence could ever reach
    this call. The floor check can only ever see the one Authorization
    object passed to this one call."""
    parameters = list(inspect.signature(advance_phase).parameters)
    assert parameters == ["from_phase", "to_phase", "sequence_status", "authorization"]


def test_earlier_insufficient_call_is_unaffected_by_a_later_sufficient_one() -> None:
    """Two independent calls for the same transition: an earlier Level 1
    call must still fail after a later Level 2 call has already succeeded
    -- proving no shared state lets a later, higher-level authorization
    retroactively cover an earlier one (the exact failure mode reference_h4's
    D-1 disclosed: a genuine Level 2 review that arrived after the
    transition it would need to authorize)."""
    later_decision = advance_phase(
        LifecyclePhase.VALIDATION,
        LifecyclePhase.DECISION,
        GateStatus.PASS,
        _authorization(reviewer_level="Level 2 (adversarial review)"),
    )
    assert later_decision.kind is TransitionRecordKind.NORMAL

    with pytest.raises(UnauthorizedTransition):
        advance_phase(
            LifecyclePhase.VALIDATION,
            LifecyclePhase.DECISION,
            GateStatus.PASS,
            _authorization(reviewer_level="Level 1 (self-review)"),
        )


# --- reference_h4 regression: the exact transitions AD-072 cites ------------
#
# Values transcribed from research_archive/reference_h4/transition_records.jsonl
# (7 records; every one recorded "Level 1 (self-review)"), matching AD-072's
# own "Reference H4 compliance implications" section in
# docs/ARCHITECTURE_DECISIONS.md. reference_h4's archive is not read here --
# these are hand-transcribed literal values, so this test never depends on
# archive file layout and can never be read as touching the archive.


@pytest.mark.parametrize(
    "seq, from_phase, to_phase",
    [
        (2, LifecyclePhase.RESEARCH_PROPOSAL, LifecyclePhase.PRE_VALIDATION),
        (3, LifecyclePhase.PRE_VALIDATION, LifecyclePhase.METHODOLOGY_FREEZE),
        (4, LifecyclePhase.METHODOLOGY_FREEZE, LifecyclePhase.IMPLEMENTATION),
        (6, LifecyclePhase.VALIDATION, LifecyclePhase.DECISION),
        (7, LifecyclePhase.DECISION, LifecyclePhase.ARCHIVE),
    ],
)
def test_reference_h4_recorded_transitions_would_be_refused_under_ad072(
    seq: int, from_phase: LifecyclePhase, to_phase: LifecyclePhase
) -> None:
    with pytest.raises(UnauthorizedTransition):
        advance_phase(
            from_phase, to_phase, GateStatus.PASS, _authorization(reviewer_level="Level 1 (self-review)")
        )


def test_reference_h4_seq5_would_pass_under_ad072() -> None:
    """seq5 (Implementation -> Validation) is the one reference_h4
    transition AD-072 does not flag: its recorded Level 1 satisfies
    Phase 5's real Level 1 floor."""
    decision = advance_phase(
        LifecyclePhase.IMPLEMENTATION,
        LifecyclePhase.VALIDATION,
        GateStatus.PASS,
        _authorization(reviewer_level="Level 1 (self-review)"),
    )
    assert decision.kind is TransitionRecordKind.NORMAL
