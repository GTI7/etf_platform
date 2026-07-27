"""Research domain (Layer 2, orchestrator).

Package for the platform's hypothesis-lifecycle orchestration capability
-- ``ProjectRegistry``, ``FreezeManager``, and ``ExperimentOrchestrator``
-- per docs/PLATFORM_ARCHITECTURE_V1.md Section 4.1.

As of Migration Plan Step 5 / Phase 1D, identity and metadata ownership
is implemented: ``project.Project``/``ProjectLifecycleState``,
``project_id.create_project_id``, ``project_repository.ResearchProjectRepository``
(+ in-memory implementation), and ``project_registry.ProjectRegistry``.
"What phase is a project in" is a queryable ``Project.lifecycle_state``
rather than prose across each cycle's ``decision_log.md`` and
``README.md`` -- see docs/RESEARCH_PLATFORM_RETROSPECTIVE.md Section 2.
``FreezeManager`` and ``ExperimentOrchestrator`` remain unimplemented;
no interface for either exists yet, per
docs/ARCHITECTURE_DECISIONS.md AD-036.

**No individual research cycle is named in this package.** The modules
that register particular cycles -- the three closed REFERENCE cycles and
the open ``reference_h4`` -- were moved to the top-level
``research_artifacts/`` package on 2026-07-27 (Engine Boundary cleanup
item C5). They import from here; nothing here imports from them. A
registry that names its own contents is not a registry.

Depends on Data, Statistics, Governance, and Validation -- the only
domain permitted to depend on all four, since coordinating them across
a hypothesis's lifecycle is its entire job. Not yet exercised by the
identity/metadata slice implemented so far, which depends on nothing
beyond the standard library and ``core.shared.ids``. Depended on only
by Reporting.
"""
