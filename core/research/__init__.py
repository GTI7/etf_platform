"""Research domain (Layer 2, orchestrator).

Reserved package for the platform's future hypothesis-lifecycle
orchestration capability -- ``ProjectRegistry``, ``FreezeManager``, and
``ExperimentOrchestrator`` -- per docs/PLATFORM_ARCHITECTURE_V1.md
Section 4.1.

Empty as of Phase 0 of docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md: no
registry or freeze manager has been written here yet. "What phase is a
project in" exists today only as prose, across each cycle's
``decision_log.md`` and ``README.md`` -- see
docs/RESEARCH_PLATFORM_RETROSPECTIVE.md Section 2.

Depends on Data, Statistics, Governance, and Validation -- the only
domain permitted to depend on all four, since coordinating them across
a hypothesis's lifecycle is its entire job. Depended on only by
Reporting.
"""
