"""Phase 0 of docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md: the five new
domain packages must import successfully and must contain no business
logic yet -- only a package docstring. Phase 1A
(docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md Step 2) populates
``core.statistics`` with its first extracted module
(``core.statistics.significance``), so that one domain is carved out of
the "still empty" check below. Phase 1C (Step 4) populates
``core.governance`` with its first two modules
(``core.governance.freeze_verifier``, ``core.governance.independence_linter``),
carving that domain out too. Phase 1D (Step 5) populates
``core.research`` with its identity/metadata slice
(``core.research.project``, ``project_id``, ``project_repository``,
``project_registry``, ``historical_backfill``), carving that domain out
as well. Migration Plan Step 7 populates ``core.validation`` with its
minimal gate-result increment (``core.validation.gate_result``,
``core.validation.gates.signal_independence``,
``core.validation.gates.economic_rationale`` -- see
docs/ARCHITECTURE_DECISIONS.md AD-040 through AD-044), carving that
domain out too. Step 8 populates ``core.reporting`` with its minimal
report-model/builder/renderer increment (``core.reporting.report_model``,
``.report_builder``, ``.json_renderer``, ``.markdown_renderer`` -- see
docs/ARCHITECTURE_DECISIONS.md AD-046), carving out the last of the
five -- no domain module remains in the "still empty" check below."""

from __future__ import annotations

import importlib

import pytest

NEW_DOMAIN_MODULES = [
    "core.statistics",
    "core.governance",
    "core.validation",
    "core.research",
    "core.reporting",
]

STILL_EMPTY_DOMAIN_MODULES: list[str] = []


@pytest.mark.parametrize("module_name", NEW_DOMAIN_MODULES)
def test_domain_package_imports_successfully(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module is not None


@pytest.mark.parametrize("module_name", NEW_DOMAIN_MODULES)
def test_domain_package_has_documentation(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module.__doc__ is not None
    assert len(module.__doc__.strip()) > 0


@pytest.mark.parametrize("module_name", STILL_EMPTY_DOMAIN_MODULES)
def test_domain_package_defines_no_public_members(module_name: str) -> None:
    """Empty as of Phase 0: no function, class, or constant is exported
    yet -- only dunder attributes Python itself sets on every module."""
    module = importlib.import_module(module_name)
    public_names = [name for name in vars(module) if not name.startswith("__")]
    assert public_names == []


def test_statistics_package_now_exposes_the_significance_submodule() -> None:
    """Phase 1A populates core.statistics with core.statistics.significance
    -- callers import the submodule explicitly (``core.statistics`` itself
    re-exports nothing), and the submodule must expose the extracted
    significance-testing functions."""
    import core.statistics.significance as significance

    assert significance is not None
    assert hasattr(significance, "spearman_correlation")


def test_governance_package_now_exposes_tier_1_submodules() -> None:
    """Phase 1C populates core.governance with its first two modules --
    callers import each submodule explicitly (``core.governance`` itself
    re-exports nothing), and each must expose its public entry point."""
    import core.governance.freeze_verifier as freeze_verifier
    import core.governance.independence_linter as independence_linter

    assert freeze_verifier is not None
    assert hasattr(freeze_verifier, "verify_freeze")
    assert independence_linter is not None
    assert hasattr(independence_linter, "lint")


def test_research_package_now_exposes_identity_and_metadata_submodules() -> None:
    """Phase 1D populates core.research with its identity/metadata slice
    -- callers import each submodule explicitly (``core.research`` itself
    re-exports nothing), and each must expose its public entry point."""
    import core.research.historical_backfill as historical_backfill
    import core.research.project as project
    import core.research.project_id as project_id
    import core.research.project_registry as project_registry
    import core.research.project_repository as project_repository

    assert hasattr(project, "Project")
    assert hasattr(project, "ProjectLifecycleState")
    assert hasattr(project_id, "create_project_id")
    assert hasattr(project_repository, "ResearchProjectRepository")
    assert hasattr(project_repository, "InMemoryResearchProjectRepository")
    assert hasattr(project_registry, "ProjectRegistry")
    assert hasattr(historical_backfill, "HISTORICAL_PROJECTS")
    assert hasattr(historical_backfill, "backfill_historical_projects")


def test_validation_package_now_exposes_step_7_submodules() -> None:
    """Step 7 populates core.validation with its minimal gate-result
    increment -- callers import each submodule explicitly (``core.validation``
    itself re-exports nothing), and each must expose its public entry point."""
    import core.validation.gate_result as gate_result
    import core.validation.gates.economic_rationale as economic_rationale
    import core.validation.gates.signal_independence as signal_independence

    assert hasattr(gate_result, "GateStatus")
    assert hasattr(gate_result, "DecisionMetadata")
    assert hasattr(gate_result, "GateResult")
    assert hasattr(signal_independence, "evaluate_signal_independence_gate")
    assert hasattr(economic_rationale, "evaluate_economic_rationale_gate")


def test_reporting_package_now_exposes_step_8_submodules() -> None:
    """Step 8 populates core.reporting with its minimal
    model/builder/renderer increment -- callers import each submodule
    explicitly (``core.reporting`` itself re-exports nothing), and each
    must expose its public entry point."""
    import core.reporting.json_renderer as json_renderer
    import core.reporting.markdown_renderer as markdown_renderer
    import core.reporting.report_builder as report_builder
    import core.reporting.report_model as report_model

    assert hasattr(report_model, "ReportModel")
    assert hasattr(report_builder, "build_report")
    assert hasattr(json_renderer, "render_json")
    assert hasattr(markdown_renderer, "render_markdown")
