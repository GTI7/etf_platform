"""Validation domain (Layer 1).

As of Migration Plan Step 7, a minimal increment exists:
``core.validation.gate_result`` (``GateResult``, ``GateStatus``,
``DecisionMetadata``) and two concrete gate functions,
``core.validation.gates.signal_independence`` and
``core.validation.gates.economic_rationale`` -- see
docs/ARCHITECTURE_DECISIONS.md AD-040 through AD-044. Both gate
functions keep their explicit-parameter contract unchanged; they are not
modified by anything below.

As of Phase 4 / Step 9 increment D (docs/ARCHITECTURE_DECISIONS.md
AD-049, AD-051, AD-052), the previously-reserved dispatch apparatus is
built: ``core.validation.gate.Gate`` (protocol), ``core.validation.
gate_context.GateContext``/``FrozenCriterion``, ``core.validation.
gate_runner.GateRunner``, ``core.validation.gate_run_record.
GateRunRecord``/``GateExecutionOutcome``, ``core.validation.
validation_registry.ValidationRegistry``, and one thin adapter per
existing gate function (``core.validation.gates.
economic_rationale_adapter``, ``core.validation.gates.
signal_independence_adapter``). ``GateRunRecord`` is an **in-memory
validation artifact only** (R1 ruling, 2026-07-24) -- this domain never
writes it to disk, never imports ``core.governance.decision_recorder``,
and never aggregates gate outcomes into a cycle-level verdict (AD-049
part 3); persistence and aggregation are Phase E's concern, composed in
``core.research.lifecycle``. No ``LifecyclePhase``-to-gate assignment is
made here either -- ``ValidationRegistry`` is mechanism only, populated
by a caller. Every gate review performed before this increment (signal
independence, economic rationale, and others) was run by a hand-written
``experiments/validate_*.py`` script, which remains unmodified and
authoritative for its own historical result -- this increment is not
backfilled onto that history (AD-044).

Depends on Data, Statistics, and Governance. Per AD-041, gate functions
compute no statistics themselves and therefore do not import
``core.statistics`` -- only ``core.governance`` (freeze verification)
today. Per the architecture document, Validation must never import
from Research -- Research invokes Validation as a lifecycle step,
never the reverse.
"""
