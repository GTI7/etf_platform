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

**Status, 2026-07-27 (Engine Boundary cleanup).** The inventory is down
from five violations across two edges to **two across one**. The
``governance -> etf`` edge is empty -- the coupling AD-068 decision 4
named as the one the step was written to expose -- and the ``data ->
etf`` edge is all that remains: ``core.market_data`` still declares the
``ETF`` aggregate and its repository functions, and extracting that
aggregate is deliberately deferred until a second asset-class workload
exists to shape it. The xfail therefore still fails, correctly, and the
marker stays. Each removal is itemized above the baseline tuple with the
intent that authorized it; none was a test edit.

**Second rule, 2026-07-28 — dependency purity (AD-005).** The checker
now also enforces that every import under ``core/`` names either the
standard library or ``core`` itself. The tests for it are in the final
section of this file and **none of them is an xfail**: the direction
rule was inventoried before it was enforced because the tree violated
it, whereas ``core/`` has always satisfied AD-005 and the only thing
missing was a mechanism. ``test_real_repository_imports_no_
third_party_package`` asserts that directly and passes, which is what
turns a prose constraint into a blocking one. The two rules are checked
by separate functions returning separate types and neither test group
constrains the other -- ``test_the_two_rules_are_independent`` asserts
that separation rather than leaving it to be inferred.

**Same-day tightening — AD-078 Section 3, closing Known Weakness 2.**
``check_dependency_purity`` originally accepted *any* repository-local
top-level name, not just ``core``, on the reasoning that whether a
``core/`` import is allowed at all is the direction rule's question.
AD-078 Section 3 states a narrower rule directly for ``core/``: no
repository-local package other than ``core`` itself, full stop. Until
this change that half of the rule was enforced by exactly one test,
``test_real_repository_core_imports_no_non_core_repository_local_
package``, with no checker mechanism behind it. It now shares the same
mechanism as the third-party half: ``test_non_core_repository_local_
import_in_core_is_rejected`` is the new synthetic-tree test for it, and
**it too carries no xfail.**
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

from tools.check_import_boundaries import (
    DOMAIN_OF_TOPLEVEL,
    ETF_SYMBOLS_BY_MODULE,
    UnmappedPackageError,
    check_dependency_purity,
    check_repository,
    format_inventory,
    format_purity_inventory,
)

# The complete ETF coupling present in core/ as of boundary-hardening
# step 1, as (domain edge, "repo/relative/path.py:lineno", imported name).
#
# Every entry is an import that was legal only because "ETF" and
# "generic market data" used to be the same domain to this checker:
#
#   data -> etf         core/market_data is not asset-class-neutral: the
#                       generic ingestion and persistence layers name ETF
#                       directly.
#
# This is a baseline to shrink, never to extend. A new line here needs a
# recorded decision, not a test edit -- and so does a *removed* line. The
# ledger below is what makes a shrink auditable: it is not enough that
# the count went down, it must be visible *how*, because the cheapest way
# to empty this tuple is to stop attributing the symbols rather than to
# stop importing them (AD-068 decision 5's false-success mode).
#
# Removals so far, each with its recorded intent. All three are from the
# Engine Boundary cleanup of 2026-07-27; its record, including the
# prepared AD-068 amendment note, is
# docs/ENGINE_BOUNDARY_CLEANUP_2026-07-27.md.
#
#   item C1 -- kernel identity cleanup:
#       ("data -> etf", "core/market_data/domain/models.py:7",
#        "core.shared.ids.ETFId")
#   discharged by renaming the kernel alias ``ETFId`` -> ``InstrumentId``.
#   The kernel may hold neutral identity primitives; it may not hold an
#   asset class's vocabulary. Nothing was exempted, relocated, or
#   reclassified: the ETF-named symbol ceased to exist, which is the only
#   way an ETF_SYMBOLS_BY_MODULE entry is allowed to disappear. AD-068
#   decision 3 names ``ETFId`` explicitly, which is why this reduction
#   needed an amendment note rather than a test edit.
#
#   item C4 -- governance/workload separation:
#       ("governance -> etf", "core/governance/dataset_snapshots.py:26",
#        "core.market_data.domain.models.ETF")
#       ("governance -> etf", "core/governance/dataset_snapshots.py:27",
#        "core.market_data.persistence.repository.insert_etf")
#   discharged by deleting ``core.governance.dataset_snapshots``. Its row
#   /object conversion moved to the workload
#   (``core.analytics.persistence.etf_snapshot`` for ETF,
#   ``core.market_data.persistence.snapshot_rows`` for the two neutral
#   tables); Governance kept canonical serialization, hashing, integrity
#   verification, and byte comparison, and now receives ``parse_row`` and
#   ``load_rows`` as caller-supplied callables. The `governance -> etf`
#   edge is **empty**, which was the coupling AD-068 decision 4 was
#   written to expose and explicitly deferred to a later step.
#   `test_governance_does_not_reach_the_etf_domain` below asserts that
#   emptiness directly, so it cannot regress unnoticed.
EXPECTED_ETF_COUPLING: tuple[tuple[str, str, str], ...] = (
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


def test_governance_does_not_reach_the_etf_domain() -> None:
    """The inverse of the test this replaces, and the reason it is a test
    of its own rather than a line in the inventory tuple above.

    Boundary-hardening step 1 could only *expose* Governance's reach into
    the ETF aggregate; AD-068 decision 4 deferred discharging it. Cleanup
    item C4 discharged it on 2026-07-27 by deleting
    ``core.governance.dataset_snapshots`` and moving row/object
    conversion to workload-owned modules.

    Asserting emptiness explicitly matters because the inventory tuple
    cannot: a tuple with no ``governance -> etf`` entry reads identically
    whether the edge is genuinely gone or the checker merely stopped
    seeing it. This assertion names the domain rather than any file, so
    a *new* Governance module reaching into ETF fails here even though it
    would appear in the inventory as a line nobody recognizes as a
    regression.

    Governance's warrant for this is not a preference. Section 4.4 of
    docs/PLATFORM_ARCHITECTURE_V1.md defines Governance as auditing by
    re-deriving from Data and plain artifacts; an auditor that constructs
    the asset class it audits cannot audit a second one."""
    governance_reaching_etf = [
        v for v in check_repository() if v.from_domain == "governance" and v.to_domain == "etf"
    ]

    assert governance_reaching_etf == [], (
        "Governance must not depend on the ETF domain (AD-068 decision 2): "
        + format_inventory(governance_reaching_etf)
    )


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


def test_etf_symbol_hosted_by_the_shared_kernel_is_not_exempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The kernel is exempt as an import target because the kernel is
    asset-class-neutral. An asset-class-specific name is not, so hosting
    one in ``core.shared.ids`` must not launder an ETF dependency through
    the kernel exemption.

    The kernel hosted exactly such a name -- ``ETFId`` -- until the
    2026-07-27 rename to ``InstrumentId`` (cleanup item C1) removed it,
    so the entry is injected here rather than read from the real mapping.
    The mechanism is what this test is about and the mechanism is
    unchanged; deleting the test along with the symbol would have
    discarded the proof that the kernel exemption is still not a hole.
    ``test_no_kernel_module_hosts_an_etf_symbol`` below asserts the
    complementary fact -- that the real mapping has no kernel entry --
    and neither test substitutes for the other."""
    monkeypatch.setitem(ETF_SYMBOLS_BY_MODULE, "core.shared.ids", frozenset({"ETFId"}))
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


def test_no_kernel_module_hosts_an_etf_symbol() -> None:
    """The state cleanup item C1 established, asserted against the real
    mapping: no shared-kernel module declares an ETF-domain name.

    The kernel is the one package the checker exempts as an import target
    for every domain, so an ETF name living there is uniquely damaging --
    it is reachable from Statistics, which docs/PLATFORM_ARCHITECTURE_V1.md
    Section 4.3 requires to have "no knowledge that 'ETF' or 'H3' exist".
    Re-adding a kernel entry to ``ETF_SYMBOLS_BY_MODULE`` fails here,
    which is deliberately harder to do by accident than noticing that the
    inventory grew by one line."""
    kernel_toplevels = {
        f"core.{toplevel}"
        for toplevel, domain in DOMAIN_OF_TOPLEVEL.items()
        if domain == "kernel"
    }
    offenders = {
        module: sorted(symbols)
        for module, symbols in ETF_SYMBOLS_BY_MODULE.items()
        if any(module == root or module.startswith(f"{root}.") for root in kernel_toplevels)
    }

    assert offenders == {}, (
        f"the shared kernel hosts ETF-domain name(s): {offenders}. The kernel is exempt as "
        "an import target for every domain, including Statistics, so an asset class's "
        "vocabulary may not live in it."
    )


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


# --- Dependency purity: core/ is standard-library-only (AD-005) ----------
#
# AD-005 states the constraint -- "the entire codebase is Python standard
# library only" -- and until 2026-07-28 nothing checked it. The direction
# checker walked the same ASTs and discarded every import whose top-level
# name was not ``core``, so a third-party import was not merely
# unenforced, it was structurally invisible: no test could have caught
# it, because the tool never produced a fact about it.
#
# These tests are the mechanism. Note what they do *not* do: no test here
# names ``numpy``, ``scipy`` or ``pandas`` as a special case, and neither
# does the checker. The rule is the complement of two allow-sets (stdlib,
# repository-local), so a package nobody anticipated fails for the same
# reason a famous one does. ``test_no_third_party_package_name_is_
# hardcoded`` asserts that property directly, because an allow-list-
# shaped implementation would pass every other test in this section while
# admitting the first dependency nobody thought to name.

_FAKE_THIRD_PARTY = "quantlib_fictional"


def test_third_party_import_in_core_is_rejected(tmp_path: Path) -> None:
    """The base case the rule exists for: a module under ``core/``
    importing a package that is neither stdlib nor in this repository."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(
        core_root / "statistics" / "__init__.py",
        f"import {_FAKE_THIRD_PARTY}\n",
    )

    foreign = check_dependency_purity(core_root)

    assert len(foreign) == 1
    item = foreign[0]
    assert item.top_level == _FAKE_THIRD_PARTY
    assert item.imported_module == _FAKE_THIRD_PARTY
    assert item.lineno == 1


def test_from_import_of_a_third_party_submodule_is_rejected(tmp_path: Path) -> None:
    """Attribution is by *top-level* name, so a deep ``from`` import is
    caught and is reported against the package a requirements file would
    have to name, not against the submodule."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(
        core_root / "statistics" / "__init__.py",
        f"from {_FAKE_THIRD_PARTY}.linalg.decomp import svd\n",
    )

    foreign = check_dependency_purity(core_root)

    assert len(foreign) == 1
    assert foreign[0].top_level == _FAKE_THIRD_PARTY
    assert foreign[0].imported_module == f"{_FAKE_THIRD_PARTY}.linalg.decomp"


@pytest.mark.parametrize(
    ("label", "source"),
    [
        (
            "try/except ImportError",
            f"try:\n    import {_FAKE_THIRD_PARTY}\nexcept ImportError:\n"
            f"    {_FAKE_THIRD_PARTY} = None\n",
        ),
        (
            "if TYPE_CHECKING",
            "from typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n"
            f"    from {_FAKE_THIRD_PARTY} import Array\n",
        ),
        (
            "function-local",
            f"def compute():\n    import {_FAKE_THIRD_PARTY}\n"
            f"    return {_FAKE_THIRD_PARTY}\n",
        ),
    ],
)
def test_guarded_third_party_import_is_rejected(
    tmp_path: Path, label: str, source: str
) -> None:
    """A guard is not an exemption, and this is the failure mode most
    likely to be argued as one.

    ``try: import numpy / except ImportError:`` is the standard way to
    make a dependency *optional*, and the standard argument for it is
    that the code still runs without the package. That argument does not
    apply here. AD-005's rationale is reproducibility -- "there are no
    third-party numerical library versions that could silently change
    calculation behavior between releases" -- and an optional dependency
    makes that worse, not better: the calculation then depends on
    whether the package happened to be installed, which is exactly the
    silent behavioural difference the decision forbids. The same holds
    for a deferred function-local import and for an ``if TYPE_CHECKING:``
    import, which declares that the repository's types are written
    against a package it does not have.

    Mechanically this needs no special handling -- ``ast.walk`` descends
    the whole tree -- which is why it is tested rather than coded around:
    a future rewrite that walked only ``tree.body`` would pass every
    other test in this section and silently reopen all three holes."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "statistics" / "__init__.py", source)

    foreign = check_dependency_purity(core_root)

    assert [item.top_level for item in foreign] == [_FAKE_THIRD_PARTY], label


def test_no_third_party_package_name_is_hardcoded(tmp_path: Path) -> None:
    """The rule is a complement, not an allow-list of known offenders.

    Three real packages this repository has a standing reason to refuse
    and three invented names are treated identically. An implementation
    that blocked only the named ones would satisfy every other test here
    and would admit the seventh package anyone reached for -- which is
    the same silent-exemption shape AD-049 part 5 closes on the direction
    axis."""
    suspects = ["numpy", "scipy", "pandas", "not_a_real_package", "zzz_unknown", "yfinance"]
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    for index, package in enumerate(suspects):
        _write(core_root / "statistics" / f"m{index}.py", f"import {package}\n")

    foreign = check_dependency_purity(core_root)

    assert sorted(item.top_level for item in foreign) == sorted(suspects)


def test_stdlib_imports_are_allowed(tmp_path: Path) -> None:
    """Everything AD-005 names as permitted, plus the ``__future__``
    import every module in this repository starts with, must pass. A
    purity rule that rejected ``sqlite3`` would be discovered instantly;
    one that rejected ``__future__`` would be discovered on the first
    real file and is the likelier slip."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(
        core_root / "statistics" / "__init__.py",
        "from __future__ import annotations\n"
        "import sqlite3\n"
        "import json\n"
        "import uuid\n"
        "import os.path\n"
        "from decimal import Decimal\n"
        "from datetime import date, datetime\n"
        "from urllib.request import urlopen\n"
        "from typing import Protocol\n"
        "from collections.abc import Iterator\n",
    )

    assert check_dependency_purity(core_root) == []


def test_core_dotted_imports_are_not_purity_violations(tmp_path: Path) -> None:
    """``core.*`` is the one repository-local namespace ``core/`` may
    import (AD-078 Section 3), so a dotted ``core`` import at any depth
    is not a purity failure. Whether a *particular* ``core.<domain>``
    target is allowed is the direction rule's question, and this rule
    does not answer it -- see ``test_the_two_rules_are_independent``."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(
        core_root / "statistics" / "__init__.py",
        "import core.shared.clock\nfrom core.shared import clock\n",
    )

    assert check_dependency_purity(core_root) == []


def test_non_core_repository_local_import_in_core_is_rejected(tmp_path: Path) -> None:
    """AD-078 Section 3: ``core/`` may import no repository-local package
    other than ``core`` itself. A sibling package -- ``adapters``,
    ``experiments``, a bare top-level module -- is a real, importable
    package in this repository, but it is not ``core``, so it is now
    rejected by the checker itself rather than only by
    ``test_real_repository_core_imports_no_non_core_repository_local_package``'s
    tripwire (AD-078 Known Weakness 2, closed 2026-07-28). Each is
    reported with ``repository_local=True``, distinguishing it from a
    genuinely unresolvable name."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(tmp_path / "adapters" / "__init__.py", "")
    _write(tmp_path / "experiments" / "run_thing.py", "")  # namespace package, no __init__
    _write(tmp_path / "top_level_module.py", "")
    _write(
        core_root / "statistics" / "__init__.py",
        "import core.shared.clock\n"
        "from adapters import sink\n"
        "from experiments.run_thing import main\n"
        "import top_level_module\n",
    )

    foreign = check_dependency_purity(core_root)

    assert sorted(item.top_level for item in foreign) == [
        "adapters",
        "experiments",
        "top_level_module",
    ]
    assert all(item.repository_local for item in foreign)


def test_a_directory_holding_no_python_is_not_repository_local(tmp_path: Path) -> None:
    """``docs/``, ``migrations/`` and ``research_archive/`` are real
    directories at this repository's root and none is importable. Being
    a directory is not the test -- holding Python is -- otherwise any
    name that happened to match a data folder would launder an unknown
    import through the local bucket."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    (tmp_path / "migrations").mkdir()
    (tmp_path / "migrations" / "0001_init.sql").write_text("", encoding="utf-8")
    _write(core_root / "statistics" / "__init__.py", "import migrations\n")

    foreign = check_dependency_purity(core_root)

    assert [item.top_level for item in foreign] == ["migrations"]


def test_relative_imports_are_never_a_purity_failure(tmp_path: Path) -> None:
    """A relative import can only name something inside the repository,
    so it is out of this rule's scope by construction rather than by
    exemption -- including one that climbs above ``core/``."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "statistics" / "__init__.py", "")
    _write(core_root / "statistics" / "helpers.py", "")
    _write(
        core_root / "statistics" / "significance.py",
        "from . import helpers\nfrom .. import shared\nfrom ...adapters import sink\n",
    )

    assert check_dependency_purity(core_root) == []


def test_purity_is_checked_in_an_unclassified_package(tmp_path: Path) -> None:
    """Purity does not depend on the domain map. A package missing from
    ``DOMAIN_OF_TOPLEVEL`` makes ``check_repository`` raise, and if the
    purity scan shared that gate an unclassified package would be a blind
    spot for as long as it stayed unclassified -- which is precisely when
    a new dependency is most likely to arrive with it."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "mystery_package" / "__init__.py", f"import {_FAKE_THIRD_PARTY}\n")

    with pytest.raises(UnmappedPackageError):
        check_repository(core_root)

    foreign = check_dependency_purity(core_root)

    assert [item.top_level for item in foreign] == [_FAKE_THIRD_PARTY]


def test_the_two_rules_are_independent(tmp_path: Path) -> None:
    """Neither rule may absorb the other's signal.

    The tree below is clean on direction (``validation -> statistics`` is
    allowed) and dirty on purity. The direction check must still report
    nothing -- if a third-party import leaked into ``check_repository``'s
    output it would break the pinned ETF coupling inventory at the top of
    this file with a message about ETF that had nothing to do with ETF --
    and the purity check must report the dependency."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "statistics" / "__init__.py", "")
    _write(
        core_root / "validation" / "__init__.py",
        f"from core.statistics import significance\nimport {_FAKE_THIRD_PARTY}\n",
    )

    assert check_repository(core_root) == []
    assert [item.top_level for item in check_dependency_purity(core_root)] == [_FAKE_THIRD_PARTY]


def test_existing_direction_violations_are_unaffected_by_purity(tmp_path: Path) -> None:
    """The mirror of the previous test: a forbidden domain edge is still
    reported exactly as before when a third-party import sits beside it,
    and it is reported by ``check_repository``, not swallowed."""
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "validation" / "__init__.py", "")
    _write(core_root / "validation" / "gate.py", "")
    _write(
        core_root / "governance" / "__init__.py",
        f"import {_FAKE_THIRD_PARTY}\nfrom core.validation import gate\n",
    )

    violations = check_repository(core_root)

    assert len(violations) == 1
    assert violations[0].from_domain == "governance"
    assert violations[0].to_domain == "validation"
    assert len(check_dependency_purity(core_root)) == 1


def test_real_repository_imports_no_third_party_package() -> None:
    """The actual tree, and the point of the whole milestone.

    This is **not** an xfail and must never become one. The direction
    rule was inventoried before it was enforced because ``core/``
    genuinely violated it (AD-068 decision 4); AD-005 has held since
    Phase 0 and the only thing missing was a check. A failure here is a
    new dependency, not inherited debt, and the response is to remove the
    import -- not to add an exception, a baseline tuple, or a marker."""
    foreign = check_dependency_purity()

    assert foreign == [], "\n" + format_purity_inventory(foreign)


def test_real_repository_core_imports_no_non_core_repository_local_package() -> None:
    """Regression tripwire for a gap that used to sit between the two
    rules rather than inside either one -- AD-078 Known Weakness 2,
    closed 2026-07-28.

    Before that date, ``check_dependency_purity`` allowed *any*
    repository-local top-level name, and ``check_repository`` only
    resolved a domain for names starting with ``core.``; a sibling
    top-level package was simply not something either rule looked at.
    ``import tools.something`` or ``from experiments import x`` written
    inside ``core/`` would have passed *both* rules silently -- a
    core -> non-core coupling neither rule was positioned to catch,
    including core -> tools, core -> tests, core -> experiments, core ->
    maintenance, core -> research_artifacts, or a future core ->
    workloads. This test was the only mechanism that caught it, by
    replicating rule 2's own AST walk independently and refusing to let
    a repository-local name other than ``core`` through.

    ``check_dependency_purity`` now enforces this directly (see the
    module docstring and ``ForeignImport``), so the first assertion below
    is no longer merely a sanity check for the *third-party* half of rule
    2 -- it is the mechanized form of this test's own rule. The manual
    walk that follows is kept as an independent cross-check using a
    different code path than the production checker
    (``test_real_tree_statistics_and_kernel_import_no_store`` uses the
    same direct-AST-walk approach for ``core.store``), not because a gap
    remains. Today's tree has no such import, so this test passes now and
    only starts failing the day one is added -- through either
    assertion."""
    core_root = Path(__file__).resolve().parent.parent / "core"

    assert check_dependency_purity(core_root) == []

    top_level_importers: dict[str, list[str]] = {}
    for path in sorted(core_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level_importers.setdefault(alias.name.split(".")[0], []).append(
                        str(path)
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    top_level_importers.setdefault(node.module.split(".")[0], []).append(
                        str(path)
                    )

    stdlib_names = set(sys.stdlib_module_names)
    offenders = {
        name: sorted(set(files))
        for name, files in top_level_importers.items()
        if name != "core" and name not in stdlib_names
    }

    assert offenders == {}, (
        f"core/ imports repository-local package(s) outside core/ itself: {offenders}. "
        "check_dependency_purity should already have failed the assertion above; if this "
        "line is what caught it instead, that regressed."
    )


def test_format_purity_inventory_groups_by_package(tmp_path: Path) -> None:
    core_root = tmp_path / "core"
    _write(core_root / "__init__.py", "")
    _write(core_root / "statistics" / "__init__.py", f"import {_FAKE_THIRD_PARTY}\n")
    _write(
        core_root / "statistics" / "significance.py",
        f"from {_FAKE_THIRD_PARTY} import mean\nimport other_fictional_pkg\n",
    )

    report = format_purity_inventory(check_dependency_purity(core_root))

    assert "3 import(s) of 2 non-standard-library, non-'core' package(s)" in report
    assert f"{_FAKE_THIRD_PARTY}  (2 import(s))" in report
    assert "other_fictional_pkg  (1 import(s))" in report
    assert "AD-078" in report


def test_format_purity_inventory_of_a_pure_tree_reports_success() -> None:
    assert "passed" in format_purity_inventory([])
