"""Governance domain (Layer 1).

Reserved package for the platform's future artifact/state auditing
capability -- ``FreezeVerifier``, ``IndependenceLabelLinter``,
``ArchiveVerifier``, ``DatasetIntegrityChecker``, ``ReproducibilityChecker``,
``DecisionLogger`` -- per docs/PLATFORM_ARCHITECTURE_V1.md Section 4.4.

Empty as of Phase 0 of docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md: no
business logic has been written here yet. Today, every check this
package will eventually automate (freeze-commit verification,
independence-label linting, archive completeness) is performed only by
manual, one-off audit passes -- see docs/RESEARCH_PLATFORM_RETROSPECTIVE.md
Section 3.

Depends only on the Data domain (``core.market_data``,
``core.analytics.persistence``). Per the architecture document,
Governance must never import from Research, Validation, or Reporting --
it audits their output as opaque artifacts, never their internals.
"""
