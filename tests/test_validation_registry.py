from __future__ import annotations

import pytest

from core.shared.lifecycle_phase import LifecyclePhase
from core.validation.validation_registry import ValidationRegistry


def test_gates_for_unregistered_phase_raises_key_error() -> None:
    registry = ValidationRegistry()

    with pytest.raises(KeyError):
        registry.gates_for_phase(LifecyclePhase.PRE_VALIDATION)


def test_register_and_retrieve_ordered_gate_names() -> None:
    registry = ValidationRegistry()
    registry.register_phase_gates(
        LifecyclePhase.PRE_VALIDATION, ["signal_independence", "economic_rationale"]
    )

    assert registry.gates_for_phase(LifecyclePhase.PRE_VALIDATION) == (
        "signal_independence",
        "economic_rationale",
    )


def test_duplicate_phase_registration_raises_value_error() -> None:
    registry = ValidationRegistry()
    registry.register_phase_gates(LifecyclePhase.PRE_VALIDATION, ["signal_independence"])

    with pytest.raises(ValueError):
        registry.register_phase_gates(LifecyclePhase.PRE_VALIDATION, ["economic_rationale"])


def test_two_registries_share_no_state() -> None:
    """INV-8: no module-level mutable registry -- each instance owns its
    own mapping."""
    registry_a = ValidationRegistry()
    registry_b = ValidationRegistry()

    registry_a.register_phase_gates(LifecyclePhase.PRE_VALIDATION, ["signal_independence"])

    with pytest.raises(KeyError):
        registry_b.gates_for_phase(LifecyclePhase.PRE_VALIDATION)
