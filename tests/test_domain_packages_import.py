"""Phase 0 of docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md: the five new
domain packages must import successfully and must contain no business
logic yet -- only a package docstring. Phase 1A
(docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md Step 2) populates
``core.statistics`` with its first extracted module
(``core.statistics.significance``), so that one domain is carved out of
the "still empty" check below; ``core.governance``, ``core.validation``,
``core.research``, and ``core.reporting`` remain untouched and are still
held to the original Phase 0 emptiness guarantee."""

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

STILL_EMPTY_DOMAIN_MODULES = [
    "core.governance",
    "core.validation",
    "core.research",
    "core.reporting",
]


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
