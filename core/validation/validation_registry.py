"""``ValidationRegistry`` -- maps a lifecycle phase to the ordered gate
names it requires (Phase 4 / Step 9, increment D --
docs/PLATFORM_ARCHITECTURE_V1.md Section 4.2's sketch;
docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md Section 4.2 row D).

Same shape as `core.research.project_registry.ProjectRegistry` and
`core.market_data.providers.registry` (AD-015): explicit, dict-backed,
duplicate registration raises `ValueError`, an unknown phase raises
`KeyError`, no auto-discovery, no module-level singleton (INV-8 -- two
instances in one process share no state).

**Deliberately empty of any phase->gate assignment.** Which gates each
of the eight `LifecyclePhase` values actually requires is H4 research
content and a Phase E/lifecycle-integration decision, not Phase D
infrastructure -- this registry only provides the mechanism a caller
populates, the same way `ProjectRegistry` never ships with a project
pre-registered.
"""

from __future__ import annotations

from collections.abc import Sequence

from core.shared.lifecycle_phase import LifecyclePhase


class ValidationRegistry:
    def __init__(self) -> None:
        self._gates_by_phase: dict[LifecyclePhase, tuple[str, ...]] = {}

    def register_phase_gates(self, phase: LifecyclePhase, gate_names: Sequence[str]) -> None:
        if phase in self._gates_by_phase:
            raise ValueError(f"phase {phase!r} is already registered")
        self._gates_by_phase[phase] = tuple(gate_names)

    def gates_for_phase(self, phase: LifecyclePhase) -> tuple[str, ...]:
        if phase not in self._gates_by_phase:
            raise KeyError(phase)
        return self._gates_by_phase[phase]
