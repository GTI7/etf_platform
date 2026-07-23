"""Tests for core/shared/lifecycle_phase.py -- pins `LifecyclePhase`'s
membership, order, and values to docs/RESEARCH_GOVERNANCE_STANDARD.md
Section 2's eight-phase table so any future drift in that vocabulary
fails loudly here rather than silently.
"""

from __future__ import annotations

from enum import Enum

from core.shared.lifecycle_phase import LifecyclePhase

STANDARD_SECTION_2_PHASES = [
    ("HYPOTHESIS", "Hypothesis"),
    ("RESEARCH_PROPOSAL", "Research Proposal"),
    ("PRE_VALIDATION", "Pre-validation"),
    ("METHODOLOGY_FREEZE", "Methodology Freeze"),
    ("IMPLEMENTATION", "Implementation"),
    ("VALIDATION", "Validation"),
    ("DECISION", "Decision"),
    ("ARCHIVE", "Archive"),
]


def test_lifecycle_phase_is_a_closed_str_enum() -> None:
    assert issubclass(LifecyclePhase, str)
    assert issubclass(LifecyclePhase, Enum)


def test_lifecycle_phase_members_and_order_pin_standard_section_2() -> None:
    """Fails if the phase vocabulary changes in name, value, count, or
    order relative to the Standard's Section 2 table."""
    actual = [(member.name, member.value) for member in LifecyclePhase]
    assert actual == STANDARD_SECTION_2_PHASES


def test_lifecycle_phase_has_exactly_eight_members() -> None:
    assert len(LifecyclePhase) == 8
