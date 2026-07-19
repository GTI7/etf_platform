"""Phase 0 of docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md: the five new
domain packages must import successfully and must contain no business
logic yet -- only a package docstring."""

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


@pytest.mark.parametrize("module_name", NEW_DOMAIN_MODULES)
def test_domain_package_imports_successfully(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module is not None


@pytest.mark.parametrize("module_name", NEW_DOMAIN_MODULES)
def test_domain_package_has_documentation(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module.__doc__ is not None
    assert len(module.__doc__.strip()) > 0


@pytest.mark.parametrize("module_name", NEW_DOMAIN_MODULES)
def test_domain_package_defines_no_public_members(module_name: str) -> None:
    """Empty as of Phase 0: no function, class, or constant is exported
    yet -- only dunder attributes Python itself sets on every module."""
    module = importlib.import_module(module_name)
    public_names = [name for name in vars(module) if not name.startswith("__")]
    assert public_names == []
