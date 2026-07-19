"""Validation domain (Layer 1).

As of Migration Plan Step 7, a minimal increment exists:
``core.validation.gate_result`` (``GateResult``, ``GateStatus``,
``DecisionMetadata``) and two concrete gate functions,
``core.validation.gates.signal_independence`` and
``core.validation.gates.economic_rationale`` -- see
docs/ARCHITECTURE_DECISIONS.md AD-040 through AD-044.

Still reserved, not built: the ``Gate`` protocol, ``GateRunner``,
``ValidationRegistry``, and ``GateContext`` per
docs/PLATFORM_ARCHITECTURE_V1.md Section 4.2 -- gates today are called
directly as functions with explicit typed parameters (AD-044), not
registered with or dispatched by anything. No ``LifecyclePhase`` enum
or workflow-state concept exists either. Every gate review performed
before this increment (signal independence, economic rationale, and
others) was run by a hand-written ``experiments/validate_*.py`` script,
which remains unmodified and authoritative for its own historical
result -- this increment is not backfilled onto that history (AD-044).

Depends on Data, Statistics, and Governance. Per AD-041, gate functions
compute no statistics themselves and therefore do not import
``core.statistics`` -- only ``core.governance`` (freeze verification)
today. Per the architecture document, Validation must never import
from Research -- Research invokes Validation as a lifecycle step,
never the reverse.
"""
