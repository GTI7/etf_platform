"""Research domain (Layer 2, orchestrator).

Package for the platform's hypothesis-lifecycle orchestration capability
-- ``ProjectRegistry``, ``FreezeManager``, and ``ExperimentOrchestrator``
-- per docs/PLATFORM_ARCHITECTURE_V1.md Section 4.1.

As of Migration Plan Step 5 / Phase 1D, identity and metadata ownership
is implemented: ``project.Project``/``ProjectLifecycleState``,
``project_id.create_project_id``, ``project_repository.ResearchProjectRepository``
(+ in-memory implementation), ``project_registry.ProjectRegistry``, and
``historical_backfill`` (registers the three closed historical cycles:
REFERENCE v1, REFERENCE v2 H1, REFERENCE H3). "What phase is a project
in" is now a queryable ``Project.lifecycle_state`` for those three,
instead of only prose across each cycle's ``decision_log.md`` and
``README.md`` -- see docs/RESEARCH_PLATFORM_RETROSPECTIVE.md Section 2.
``FreezeManager`` and ``ExperimentOrchestrator`` remain unimplemented;
no interface for either exists yet, per
docs/ARCHITECTURE_DECISIONS.md AD-036.

Depends on Data, Statistics, Governance, and Validation -- the only
domain permitted to depend on all four, since coordinating them across
a hypothesis's lifecycle is its entire job. Not yet exercised by the
identity/metadata slice implemented so far, which depends on nothing
beyond the standard library and ``core.shared.ids``. Depended on only
by Reporting.
"""
