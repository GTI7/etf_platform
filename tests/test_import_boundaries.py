"""Tests for tools/check_import_boundaries.py -- the stdlib-only import-
direction checker enforcing docs/PLATFORM_ARCHITECTURE_V1.md Section 5.

**One test in this file is expected to fail** (AD-068 decision 4).
``test_real_repository_has_no_boundary_violations`` carries
``@pytest.mark.xfail(strict=True)``. Boundary-hardening step 1 splits ETF
out of the Data domain so the platform's existing ETF coupling becomes
visible; it deliberately does *not* fix the coupling it exposes. Step 1
is inventory, not repair, and the marker is the record of that posture.

``strict=True`` is mandatory and is what makes the marker stronger than
simply leaving the test red. An *unexpected pass* is a failure, so on the
day the last coupling is discharged the suite refuses to go green until
the marker is removed -- a forcing function a red test does not have.
A non-strict xfail would silently absorb that state and is forbidden
here. This is the repository's first and only xfail; it is scoped to
this one test and is **not** precedent for deferring any other failure.

``test_known_etf_coupling_inventory_is_exactly_as_documented`` pins the
inventory line by line and *passes*. The pair is the point and neither
substitutes for the other: the xfail records the aspiration, the
inventory test records the exact current state. Adding a new ETF
coupling turns the inventory test red; removing one likewise, until the
last removal makes the xfail pass unexpectedly, fails the suite under
``strict=True``, and forces the marker and the baseline below to be
deleted together with this note.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

from tools.check_import_boundaries import (
    ETF_SYMBOLS_BY_MODULE,
    UnmappedPackageError,
    check_repository,
    format_inventory,
)

# The complete ETF coupling present in core/ as of boundary-hardening
# step 1, as (domain edge, "repo/relative/path.py:lineno", imported name).
#
# Every entry is an import that was legal only because "ETF" and
# "generic market data" used to be the same domain to this checker:
#
#   governance -> etf   Governance serializes the ETF aggregate itself
#                       (dataset_snapshots' etf_to_row/row_to_etf), so a
#                       Governance audit today cannot run against a
#                       non-ETF asset class. This is the coupling the
#                       step was written to expose.
#   data -> etf         core/market_data is not asset-class-neutral: the
#                       generic ingestion and persistence layers, and the
#                       shared kernel's id vocabulary, name ETF directly.
#
# This is a baseline to shrink, never to extend. A new line here needs a
# recorded decision, not a test edit.
EXPECTED_ETF_COUPLING: tuple[tuple[str, str, str], ...] = (
    ("data -> etf", "core/market_data/domain/models.py:7", "core.shared.ids.ETFId"),
    (
        "data -> etf",
        "core/market_data/ingestion/price_ingestion.py:7",
        "core.market_data.domain.models.ETF",
    ),
    (
        "data -> etf",
        "core/market_data/persistence/repository.py:15",
        "core.market_data.domain.models.ETF",
    ),
    (
        "governance -> etf",
        "core/governance/dataset_snapshots.py:26",
        "core.market_data.domain.models.ETF",
    ),
    (
        "governance -> etf",
        "core/governance/dataset_snapshots.py:27",
        "core.market_data.persistence.repository.insert_etf",
    ),
)


def test_known_etf_coupling_inventory_is_exactly_as_documented() -> None:
    """The exposed coupling is exactly ``EXPECTED_ETF_COUPLING`` -- no
    more (no regression) and no less (no silent partial fix that leaves
    the red test below unexplained)."""
    actual = tuple(
        sorted(
            (v.edge, f"{v.file.as_posix()}:{v.lineno}", v.imported_name)
            for v in check_repository()
        )
    )
    assert actual == tuple(sorted(EXPECTED_ETF_COUPLING))


@pytest.mark.parametrize(
    ("module_name", "symbol"),
    sorted(
        (module_name, symbol)
        for module_name, symbols in ETF_SYMBOLS_BY_MODULE.items()
        for symbol in symbols
    ),
)
def test_every_etf_symbol_resolves_in_its_named_module(module_name: str, symbol: str) -> None:
    """Every name in ``ETF_SYMBOLS_BY_MODULE`` must actually exist where
    the mapping says it does.

    This guards a **false success**, which is why it exists (AD-068
    decision 5). ``ETF_SYMBOLS_BY_MODULE`` is hand-maintained and nothing
    else checks it. Rename or relocate a listed symbol and the mapping
    silently stops matching any import: the violation count falls toward
    zero, the coupling inventory shrinks, and
    ``test_real_repository_has_no_boundary_violations`` passes
    unexpectedly -- reporting "the ETF split is complete" while the
    coupling is entirely untouched. Under ``strict=True`` that unexpected
    pass does fail the suite, but it fails it with a misleading story;
    this test is what names the real cause.

    A failure here means a listed symbol moved or was renamed. Investigate
    and update the mapping to match reality. **Never** delete the entry to
    make this pass -- that is precisely the silent-shrink failure the test
    exists to catch."""
    module = importlib.import_module(module_name)

    assert hasattr(module, symbol), (
        f"ETF_SYMBOLS_BY_MODULE lists '{symbol}' in '{module_name}', but that "
        f"module does not define it. The symbol was renamed or relocated; the "
        f"checker has silently stopped attributing it to the ETF domain."
    )


def test_governance_to_etf_coupling_is_reported_as_such() -> None:
    """The specific thing step 1 exists to surface: Governance's reach
    into the ETF aggregate is reported on the 'governance -> etf' edge,
    even though every offending line's module path reads
    ``core.market_data`` and would previously have been blessed as the
    allowed 'governance -> data' edge."""
    governance_to_etf = [
        v for v in check_repository() if v.from_domain == "governance" and v.to_domain == "etf"
    ]

    assert governance_to_etf, "expected the governance -> ETF coupling to be exposed"
    assert {v.file.as_posix() for v in governance_to_etf} == {
        "core/governance/dataset_snapshots.py"
    }
    assert {v.imported_symbol for v in governance_to_etf} == {"ETF", "insert_etf"}
    # Reached through an asset-class-neutral module path, attributed by symbol.
    assert all(v.imported_module.startswith("core.market_data") for v in governance_to_etf)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "AD-068 decision 4: boundary-hardening step 1 inventories the "
        "pre-existing ETF coupling and does not discharge it. This test "
        "goes green -- and this marker must then be deleted -- when "
        "boundary-hardening step 3 relocates the symbols listed in "
        "ETF_SYMBOLS_BY_MODULE and repoints the importers named in "
        "EXPECTED_ETF_COUPLING. Under strict=True an unexpected pass "
        "fails the suite, which is how that deletion is forced."
    ),
)
def test_real_repository_has_no_boundary_violations() -> None:
    """EXPECTED TO FAIL until boundary-hardening step 3 -- see this
    module's docstring and the marker's reason.

    The actual core/ tree must eventually be clean under the ETF/Data
    split. It is not clean today, and step 1 does not make it clean: it
    only makes the existing coupling nameable. The assertion message is
    the inventory."""
    violations = check_repository()
    assert violations == [], "\n" + format_inventory(violations)


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
    _write(core_root / "market_data" / "persistence" / "__init__.py", "")
    _write(core_root / "market_data" / "persistence" / "repository.py", "")
    _write(
        core_root / "market_data" / "ingestion" / "__init__.py",
        "from core.market_data.persistence import repository\n",  # both are 'data'
    )

    violations = check_repository(core_root)

    assert violations == []


# --- ETF as a domain distinct from Data (boundary-hardening step 1) ------


def test_etf_may_depend_on_data(tmp_path: Path) -> None:
    """``core.analytics`` is the ETF domain, and ETF product logic sits
    *above* the generic data foundation -- reading market data is the
    one direction that stays legal across this new boundary."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "market_data" / "persistence" / "__init__.py", "")
    _write(core_root / "market_data" / "persistence" / "repository.py", "")
    _write(core_root / "statistics" / "__init__.py", "")
    _write(
        core_root / "analytics" / "__init__.py",
        "from core.market_data.persistence import repository\n"
        "from core.statistics import significance\n",
    )

    violations = check_repository(core_root)

    assert violations == []


def test_data_may_not_depend_on_etf(tmp_path: Path) -> None:
    """The inverse edge is forbidden: docs/PLATFORM_ARCHITECTURE_V1.md
    Section 1 requires that adding an asset class touch only a Data
    provider, which is impossible if Data itself imports ETF logic."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "analytics" / "__init__.py", "")
    _write(
        core_root / "market_data" / "__init__.py",
        "from core.analytics import scoring_pipeline\n",
    )

    violations = check_repository(core_root)

    assert len(violations) == 1
    assert violations[0].from_domain == "data"
    assert violations[0].to_domain == "etf"


def test_no_platform_domain_may_depend_on_etf(tmp_path: Path) -> None:
    """Not even the domains that may depend on everything below them:
    an asset class is a plug-in above the platform, so Research and
    Reporting -- which may import Data freely -- may not import ETF."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "analytics" / "__init__.py", "")
    _write(core_root / "research" / "__init__.py", "from core.analytics import ranked_report\n")
    _write(core_root / "reporting" / "__init__.py", "from core.analytics import ranked_report\n")
    _write(core_root / "validation" / "__init__.py", "from core.analytics import ranked_report\n")

    violations = check_repository(core_root)

    assert {v.from_domain for v in violations} == {"research", "reporting", "validation"}
    assert {v.to_domain for v in violations} == {"etf"}


def test_etf_symbol_in_a_generic_module_is_attributed_to_etf(tmp_path: Path) -> None:
    """Step 1 moves no files, so the ETF domain is identified by symbol
    where it still lives inside an asset-class-neutral module. Importing
    ``ETF`` from ``core.market_data.domain.models`` is a governance ->
    etf violation, not the governance -> data import it looks like."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "market_data" / "domain" / "__init__.py", "")
    _write(core_root / "market_data" / "domain" / "models.py", "")
    _write(
        core_root / "governance" / "__init__.py",
        "from core.market_data.domain.models import ETF\n",
    )

    violations = check_repository(core_root)

    assert len(violations) == 1
    violation = violations[0]
    assert violation.from_domain == "governance"
    assert violation.to_domain == "etf"
    assert violation.imported_module == "core.market_data.domain.models"
    assert violation.imported_symbol == "ETF"
    assert violation.imported_name == "core.market_data.domain.models.ETF"


def test_neutral_symbols_beside_an_etf_symbol_stay_data(tmp_path: Path) -> None:
    """Attribution is per imported name, not per import statement: one
    statement pulling ``ETF`` and ``PriceBar`` out of the same module
    yields exactly one violation, and the neutral names are untouched."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "market_data" / "domain" / "__init__.py", "")
    _write(core_root / "market_data" / "domain" / "models.py", "")
    _write(
        core_root / "governance" / "__init__.py",
        "from core.market_data.domain.models import ETF, PriceBar, TradingSession\n",
    )

    violations = check_repository(core_root)

    assert [v.imported_symbol for v in violations] == ["ETF"]


def test_etf_symbol_hosted_by_the_shared_kernel_is_not_exempt(tmp_path: Path) -> None:
    """The kernel is exempt as an import target because the kernel is
    asset-class-neutral. ``ETFId`` is not, so hosting it in
    ``core.shared.ids`` must not launder an ETF dependency through the
    kernel exemption."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "shared" / "__init__.py", "")
    _write(core_root / "shared" / "ids.py", "")
    _write(
        core_root / "market_data" / "domain" / "__init__.py",
        "from core.shared.ids import ETFId, ScoreId\n",
    )

    violations = check_repository(core_root)

    assert len(violations) == 1
    violation = violations[0]
    assert violation.from_domain == "data"
    assert violation.to_domain == "etf"
    assert violation.imported_symbol == "ETFId"  # ScoreId stays kernel, exempt


def test_relative_import_of_an_etf_symbol_is_detected(tmp_path: Path) -> None:
    """Symbol-level attribution survives relative-import resolution --
    the same AD-049 part 5 requirement that applies to module-level
    checks applies to the ETF split."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "market_data" / "domain" / "__init__.py", "")
    _write(core_root / "market_data" / "domain" / "models.py", "")
    _write(
        core_root / "market_data" / "ingestion" / "__init__.py",
        "",
    )
    _write(core_root / "governance" / "__init__.py", "")
    _write(
        core_root / "governance" / "snapshots.py",
        "from ..market_data.domain.models import ETF\n",
    )

    violations = check_repository(core_root)

    assert len(violations) == 1
    assert violations[0].to_domain == "etf"
    assert violations[0].imported_symbol == "ETF"


def test_star_import_is_not_attributed_to_a_symbol(tmp_path: Path) -> None:
    """``from X import *`` binds no nameable symbol, so it falls back to
    the module's own domain rather than silently claiming ETF or
    silently claiming exemption."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "market_data" / "domain" / "__init__.py", "")
    _write(core_root / "market_data" / "domain" / "models.py", "")
    _write(
        core_root / "governance" / "__init__.py",
        "from core.market_data.domain.models import *\n",  # governance -> data: allowed
    )

    violations = check_repository(core_root)

    assert violations == []


# --- store as the neutral storage substrate (boundary-hardening step 2) --


def test_store_grant_set_matches_demonstrated_importers(tmp_path: Path) -> None:
    """T-5. The ``store`` grant is exactly ``{data, governance}`` -- the
    two domains with a real importer -- and nothing else.

    This replaces an earlier ``test_every_domain_may_depend_on_store``,
    which encoded the over-broad grant as a *requirement* and so would
    have failed the moment the grant was correctly narrowed. Both
    directions are asserted here: the permitted edges must pass, and the
    denied ones must be reported as violations. Widening the grant is a
    recorded decision (AD-069), and this test is what makes an
    unrecorded widening fail."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "store" / "__init__.py", "")
    _write(core_root / "store" / "connection.py", "")
    _write(core_root / "store" / "migrations.py", "")
    reaches_store = (
        "from core.store.connection import connect\n"
        "from core.store.migrations import run_migrations\n"
    )
    for package in ("market_data", "governance"):
        _write(core_root / package / "__init__.py", reaches_store)
    for package in ("analytics", "statistics", "validation", "research", "reporting"):
        _write(core_root / package / "__init__.py", reaches_store)

    violations = check_repository(core_root)

    # data and governance: permitted, so absent from the violation set.
    assert {v.from_domain for v in violations} == {
        "etf",
        "statistics",
        "validation",
        "research",
        "reporting",
    }
    assert {v.to_domain for v in violations} == {"store"}


def test_statistics_may_not_depend_on_store(tmp_path: Path) -> None:
    """T-5, negative half, called out on its own because the *ground*
    matters. Statistics is refused the storage edge on **purity**, not on
    layering -- Section 4.3 defines it as a pure computational library
    and it is denied I/O for the same reason the kernel is. Section 5's
    "Statistics -> anything" hard rule is preserved intact by the narrow
    grant, which is the point of narrowing it."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "store" / "__init__.py", "")
    _write(core_root / "store" / "connection.py", "")
    _write(
        core_root / "statistics" / "__init__.py",
        "from core.store.connection import connect\n",
    )

    violations = check_repository(core_root)

    assert len(violations) == 1
    assert violations[0].from_domain == "statistics"
    assert violations[0].to_domain == "store"


def test_store_may_not_depend_on_any_domain(tmp_path: Path) -> None:
    """The substrate holds no domain knowledge, so the edge only runs one
    way. A repository function -- which knows table names -- belongs to
    its owning domain and may never be pulled down into ``core.store``."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "market_data" / "persistence" / "__init__.py", "")
    _write(core_root / "market_data" / "persistence" / "repository.py", "")
    _write(
        core_root / "store" / "__init__.py",
        "from core.market_data.persistence import repository\n",
    )

    violations = check_repository(core_root)

    assert len(violations) == 1
    assert violations[0].from_domain == "store"
    assert violations[0].to_domain == "data"


def test_shared_kernel_may_not_depend_on_store(tmp_path: Path) -> None:
    """Why ``store`` is its own domain rather than part of the kernel: the
    kernel is a pure value vocabulary (Money, Clock, ids) with no I/O. If
    ``core.store`` were mapped to "kernel", this import would be a
    same-domain import and could never be flagged, and ``core.shared``
    could quietly acquire sqlite3."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "store" / "__init__.py", "")
    _write(core_root / "store" / "connection.py", "")
    _write(
        core_root / "shared" / "money.py",
        "from core.store.connection import connect\n",
    )

    violations = check_repository(core_root)

    assert len(violations) == 1
    assert violations[0].from_domain == "kernel"
    assert violations[0].to_domain == "store"


def test_store_is_not_a_route_from_a_domain_into_etf(tmp_path: Path) -> None:
    """``store`` being reachable must not become a laundering path: an ETF
    symbol hosted by a ``core.store`` module would still be attributed to
    ETF, exactly as it is inside ``core.market_data``."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "analytics" / "__init__.py", "")
    _write(
        core_root / "store" / "__init__.py",
        "from core.analytics import scoring_pipeline\n",
    )

    violations = check_repository(core_root)

    assert len(violations) == 1
    assert violations[0].from_domain == "store"
    assert violations[0].to_domain == "etf"


@pytest.mark.parametrize("package", ["statistics", "shared"])
def test_real_tree_statistics_and_kernel_import_no_store(package: str) -> None:
    """T-6. The *actual* tree, not a synthetic one.

    ``test_statistics_may_not_depend_on_store`` and
    ``test_shared_kernel_may_not_depend_on_store`` both build a tree in
    ``tmp_path``: they prove the checker would report the edge, not that
    the edge is absent from this repository. The repository-wide check
    that would cover it is under a strict ``xfail`` for unrelated ETF
    reasons, so nothing asserts this today. It is cheap and independent
    of both.

    Statistics and the shared kernel are the two packages whose purity
    the reproducibility argument rests on: if either acquired a database
    connection, "pure computational library" would stop being true while
    the suite stayed green."""
    package_root = Path(__file__).resolve().parent.parent / "core" / package
    offenders = {}
    for path in sorted(package_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        reached = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                reached.update(a.name for a in node.names if a.name.startswith("core.store"))
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "core.store" or node.module.startswith("core.store."):
                    reached.add(node.module)
        if reached:
            offenders[path.name] = sorted(reached)

    assert offenders == {}, (
        f"core/{package}/ must not reach the storage substrate: {offenders}. "
        "Statistics is denied I/O on purity grounds (AD-069), and the kernel "
        "is denied it structurally."
    )


def test_format_inventory_groups_by_domain_edge(tmp_path: Path) -> None:
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "market_data" / "domain" / "__init__.py", "")
    _write(core_root / "market_data" / "domain" / "models.py", "")
    _write(core_root / "validation" / "__init__.py", "")
    _write(
        core_root / "governance" / "__init__.py",
        "from core.market_data.domain.models import ETF\n"
        "from core.validation import gate\n",
    )

    report = format_inventory(check_repository(core_root))

    assert "2 violation(s) across 2 forbidden domain edge(s)" in report
    assert "governance -> etf" in report
    assert "governance -> validation" in report
    assert "core.market_data.domain.models.ETF" in report
    # The ETF footer names where the split has not been made yet.
    for module in ETF_SYMBOLS_BY_MODULE:
        assert module in report


def test_format_inventory_of_a_clean_tree_reports_success() -> None:
    assert "passed" in format_inventory([])


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
