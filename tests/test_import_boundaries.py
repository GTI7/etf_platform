"""Tests for tools/check_import_boundaries.py -- the stdlib-only import-
direction checker enforcing docs/PLATFORM_ARCHITECTURE_V1.md Section 5.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_import_boundaries import UnmappedPackageError, check_repository


def test_real_repository_has_no_boundary_violations() -> None:
    """The actual core/ tree, as it exists today, must be clean -- this
    is the check that would fail CI if a future change violated the
    architecture document's dependency table."""
    violations = check_repository()
    assert violations == [], "\n".join(str(v) for v in violations)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_detects_forbidden_governance_to_validation_import(tmp_path: Path) -> None:
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "governance" / "__init__.py", "")
    _write(
        core_root / "governance" / "checker.py",
        "from core.validation import gate\n",  # forbidden: governance -> validation
    )
    _write(core_root / "validation" / "__init__.py", "")
    _write(core_root / "validation" / "gate.py", "")

    violations = check_repository(core_root)

    assert len(violations) == 1
    violation = violations[0]
    assert violation.from_domain == "governance"
    assert violation.to_domain == "validation"
    assert violation.imported_module == "core.validation"


def test_allows_validation_to_import_statistics_and_governance(tmp_path: Path) -> None:
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "statistics" / "__init__.py", "")
    _write(core_root / "governance" / "__init__.py", "")
    _write(
        core_root / "validation" / "__init__.py",
        "from core.statistics import significance\n"
        "from core.governance import freeze_verifier\n"
        "import core.market_data.persistence.database\n",
    )
    _write(core_root / "market_data" / "persistence" / "database.py", "")

    violations = check_repository(core_root)

    assert violations == []


def test_detects_forbidden_import_of_reporting(tmp_path: Path) -> None:
    """'Anything -> Reporting' is forbidden -- Reporting is a true leaf."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "reporting" / "__init__.py", "")
    _write(
        core_root / "research" / "__init__.py",
        "from core.reporting import report_builder\n",
    )

    violations = check_repository(core_root)

    assert len(violations) == 1
    assert violations[0].from_domain == "research"
    assert violations[0].to_domain == "reporting"


def test_shared_kernel_imports_are_exempt(tmp_path: Path) -> None:
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "shared" / "__init__.py", "")
    _write(core_root / "shared" / "clock.py", "")
    _write(
        core_root / "statistics" / "__init__.py",
        "from core.shared.clock import Clock\n",  # kernel import, never a violation
    )

    violations = check_repository(core_root)

    assert violations == []


def test_same_domain_imports_are_always_allowed(tmp_path: Path) -> None:
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "market_data" / "__init__.py", "")
    _write(core_root / "market_data" / "persistence.py", "")
    _write(
        core_root / "analytics" / "__init__.py",
        "from core.market_data.persistence import repository\n",  # both map to 'data'
    )

    violations = check_repository(core_root)

    assert violations == []


def test_shared_kernel_may_not_import_a_domain(tmp_path: Path) -> None:
    """AD-049 part 5 / Resolution 1.4: the kernel is exempt as an import
    *target*, not as a *source*. A kernel module reaching into a domain
    package must be flagged like any other boundary violation."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "governance" / "__init__.py", "")
    _write(
        core_root / "shared" / "__init__.py",
        "from core.governance import freeze_verifier\n",  # forbidden: kernel -> domain
    )

    violations = check_repository(core_root)

    assert len(violations) == 1
    violation = violations[0]
    assert violation.from_domain == "kernel"
    assert violation.to_domain == "governance"
    assert violation.imported_module == "core.governance"


def test_unmapped_toplevel_package_is_an_error_not_an_exemption(tmp_path: Path) -> None:
    """AD-049 part 5: an unrecognized top-level package under core/ must
    fail loudly rather than being silently skipped -- silent exemption is
    the exact escape hatch a future package could fall through unnoticed."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "mystery_package" / "__init__.py", "")
    _write(core_root / "mystery_package" / "thing.py", "")

    with pytest.raises(UnmappedPackageError):
        check_repository(core_root)


def test_relative_import_within_domain_is_allowed(tmp_path: Path) -> None:
    """A relative import that stays inside the importing module's own
    domain is not a boundary violation and must not be rejected."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "statistics" / "__init__.py", "")
    _write(core_root / "statistics" / "helpers.py", "")
    _write(
        core_root / "statistics" / "significance.py",
        "from . import helpers\n",  # relative, same domain -- legal
    )

    violations = check_repository(core_root)

    assert violations == []


def test_relative_import_crossing_domains_is_detected(tmp_path: Path) -> None:
    """A relative import that crosses a domain boundary must be resolved
    to its absolute target and checked exactly like an absolute import --
    it must not be invisible to the checker."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "validation" / "__init__.py", "")
    _write(core_root / "governance" / "__init__.py", "")
    _write(
        core_root / "governance" / "checker.py",
        "from ..validation import gate\n",  # relative, forbidden: governance -> validation
    )
    _write(core_root / "validation" / "gate.py", "")

    violations = check_repository(core_root)

    assert len(violations) == 1
    violation = violations[0]
    assert violation.from_domain == "governance"
    assert violation.to_domain == "validation"
