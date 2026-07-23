"""Tests for core/research/phase_derivation.py -- current phase is
derived from the transition chain, and an empty chain derives UNKNOWN
(Phase 4 / Step 9, increment E; AD-058)."""

from __future__ import annotations

from core.governance.decision_recorder import AuthorizationRecord, DecisionRecord, GateOutcome
from core.research.phase_derivation import (
    UNKNOWN_PHASE,
    DerivedPhaseUnknown,
    derive_current_phase,
)
from core.shared.lifecycle_phase import LifecyclePhase


def _record(from_phase: str, to_phase: str, sequence_number: int) -> DecisionRecord:
    return DecisionRecord(
        project_id="reference_h4",
        sequence_number=sequence_number,
        from_phase=from_phase,
        to_phase=to_phase,
        recorded_at="2026-07-24T00:00:00+00:00",
        commit_hash="a" * 40,
        freeze_commit_ref="b" * 40,
        freeze_verification_status="verified",
        freeze_covered_paths=("docs/x.md",),
        gate_outcomes=(GateOutcome(gate_name="g", status="pass"),),
        authorization=AuthorizationRecord(
            authorizer="alice",
            reviewer_level="2",
            ambiguity_acknowledged=False,
            override_acknowledged=False,
        ),
        evidence_refs=(),
        reproduction_record_ref=None,
        predecessor_hash=None,
    )


# --- genesis: empty chain derives UNKNOWN -------------------------------


def test_empty_chain_derives_unknown() -> None:
    assert derive_current_phase(()) is UNKNOWN_PHASE


def test_empty_chain_does_not_derive_hypothesis() -> None:
    """Registration does not imply Hypothesis (AD-058): the empty-chain
    answer is UNKNOWN, categorically not the first phase."""
    derived = derive_current_phase(())
    assert derived is not LifecyclePhase.HYPOTHESIS


def test_unknown_is_not_a_lifecycle_phase() -> None:
    """UNKNOWN is a derived-state sentinel, never a ninth LifecyclePhase
    -- the eight-phase enum stays the Standard Section 2 transcription."""
    assert not isinstance(UNKNOWN_PHASE, LifecyclePhase)
    assert isinstance(UNKNOWN_PHASE, DerivedPhaseUnknown)
    assert UNKNOWN_PHASE not in set(LifecyclePhase)


# --- non-empty chain: current phase is the last to_phase ----------------


def test_single_record_derives_its_to_phase() -> None:
    chain = (_record("Hypothesis", "Research Proposal", 1),)
    assert derive_current_phase(chain) is LifecyclePhase.RESEARCH_PROPOSAL


def test_multi_record_derives_last_to_phase() -> None:
    chain = (
        _record("Hypothesis", "Research Proposal", 1),
        _record("Research Proposal", "Pre-validation", 2),
        _record("Pre-validation", "Methodology Freeze", 3),
    )
    assert derive_current_phase(chain) is LifecyclePhase.METHODOLOGY_FREEZE
