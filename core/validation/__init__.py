"""Validation domain (Layer 1).

Reserved package for the platform's future pluggable gate-execution
capability -- the ``Gate`` protocol, ``GateRunner``, and
``ValidationRegistry`` -- per docs/PLATFORM_ARCHITECTURE_V1.md
Section 4.2.

Empty as of Phase 0 of docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md: no
``Gate`` implementation or runner has been written here yet. Every gate
review performed to date (signal independence, economic rationale, and
others) was run by a hand-written ``experiments/validate_*.py`` script,
which remains unmodified and authoritative for its own historical
result.

Depends on Data, Statistics, and Governance. Per the architecture
document, Validation must never import from Research -- Research
invokes Validation as a lifecycle step, never the reverse.
"""
