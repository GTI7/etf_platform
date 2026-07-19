"""Import boundary enforcement for ``core/reporting`` -- the direct
enforcement of docs/STEP_8_REPORTING_DESIGN.md Section 6/7 and
docs/ARCHITECTURE_DECISIONS.md AD-046: ``json_renderer.py`` and
``markdown_renderer.py`` must never import ``core.validation`` (or any
other domain Reporting doesn't need); ``report_builder.py`` is the only
file in this package permitted to import ``core.validation``, and
permitted nothing beyond that one import from outside ``core.reporting``.

Uses ``ast``, not ``importlib``, the same style
``tools/check_import_boundaries.py`` and
``tests/test_signal_independence_gate.py`` already use, so the check
does not depend on the imports under test actually succeeding.
"""

from __future__ import annotations

import ast
from pathlib import Path

import core.reporting.json_renderer as json_renderer
import core.reporting.markdown_renderer as markdown_renderer
import core.reporting.report_builder as report_builder

_FORBIDDEN_DOMAIN_MODULES = (
    "core.validation",
    "core.governance",
    "core.statistics",
    "core.analytics",
    "core.research",
)
_FORBIDDEN_STDLIB_MODULES = ("pathlib", "os")


def _imported_modules(module: object) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))  # type: ignore[attr-defined]
    names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    names |= {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    return names


def _references_any(imported: set[str], forbidden_prefixes: tuple[str, ...]) -> bool:
    return any(
        module == prefix or module.startswith(prefix + ".")
        for module in imported
        for prefix in forbidden_prefixes
    )


def test_json_renderer_does_not_import_forbidden_modules() -> None:
    imported = _imported_modules(json_renderer)
    assert not _references_any(imported, _FORBIDDEN_DOMAIN_MODULES)
    assert not _references_any(imported, _FORBIDDEN_STDLIB_MODULES)


def test_markdown_renderer_does_not_import_forbidden_modules() -> None:
    imported = _imported_modules(markdown_renderer)
    assert not _references_any(imported, _FORBIDDEN_DOMAIN_MODULES)
    assert not _references_any(imported, _FORBIDDEN_STDLIB_MODULES)


def test_report_builder_only_imports_core_validation_gate_result_outside_reporting() -> None:
    imported = _imported_modules(report_builder)
    outside_reporting = {
        module
        for module in imported
        if (module == "core" or module.startswith("core."))
        and not (module == "core.reporting" or module.startswith("core.reporting."))
    }
    assert outside_reporting == {"core.validation.gate_result"}
