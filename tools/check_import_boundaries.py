"""Import-direction boundary checker for ``core/``.

Enforces the cross-domain dependency table in
docs/PLATFORM_ARCHITECTURE_V1.md Section 5, using stdlib ``ast`` only
(AD-005: no third-party dependency for this or anything else). This is
the "Import-direction lint" the architecture document itself specifies
as one of the two enforcement mechanisms for domain boundaries (Section
5, "Enforcement", item 1).

Domain mapping. Each top-level package directly under ``core/`` is
assigned to one of the six architecture domains, or to the special
``"kernel"`` domain for the cross-cutting shared kernel (``core.shared``,
``core.domain``). The kernel is exempt from the dependency table only as
an import *target* -- every domain is allowed to depend on it, per
docs/ARCHITECTURE_DECISIONS.md AD-003/AD-007's existing "inject the
primitive, no domain owns it" pattern -- never as an import *source*: the
kernel may depend on nothing under ``core/`` (AD-049 part 5).

A top-level package under ``core/`` that is *not* in ``DOMAIN_OF_TOPLEVEL``
is a hard error (``UnmappedPackageError``), not a silent exemption
(AD-049 part 5): a new package must be classified before this checker can
run, so it cannot fall through unnoticed in either import direction.

ETF is its own domain, not part of Data (boundary-hardening step 1).
docs/PLATFORM_ARCHITECTURE_V1.md Section 1 states the goal directly:
"adding a new asset class (equities, crypto, bonds) never requires
touching Research, Validation, Statistics, Governance, or Reporting --
only a new Data-domain provider", and Section 3 requires Statistics to
have "no knowledge that 'ETF' or 'H3' exist". Both statements are only
meaningful if "ETF" names something distinct from generic market data.
Until this step, the checker collapsed the two: ``core.analytics`` (ETF
scoring/ranking product logic) was mapped to ``data``, and the
ETF-specific types living inside ``core.market_data`` were
indistinguishable from the asset-class-neutral ones beside them. Every
platform domain could therefore reach ETF concepts through an edge the
table blesses as "-> Data", and the coupling stayed invisible.

Two mechanisms make ETF visible without moving a single file:

1. ``core.analytics`` is mapped to the new ``etf`` domain rather than to
   ``data``. (Per docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md Section 1
   only ``core.analytics.persistence`` was ever formally Data-domain
   code; the rest is "not yet a domain; stays product logic". Under an
   ETF/Data split that persistence layer is ETF-scoring persistence, so
   the whole package moves together.)
2. ``ETF_SYMBOLS_BY_MODULE`` names the ETF-specific symbols that
   physically live in asset-class-neutral modules -- ``ETF`` in
   ``core.market_data.domain.models``, the ``*_etf`` repository
   functions, ``ETFId`` in the shared kernel. An import is attributed to
   the ``etf`` domain by the *symbol* it names, not by the module that
   currently happens to host it. This is what lets the checker report
   "governance -> etf" for a line whose module path says
   ``core.market_data``.

No domain may depend on ``etf``: an asset class is a plug-in above the
platform, never something the platform reaches down into. ``etf`` itself
may depend on ``data`` and ``statistics`` (and the kernel, like every
domain).

**This check does not pass today, by design** (AD-068 decision 4). Step 1
is inventory, not repair: it makes the pre-existing coupling fail loudly
and enumerably so that a later step can discharge it deliberately.
``format_inventory`` renders that enumeration, and
``tests/test_import_boundaries.py`` carries the failure as a strict
``xfail`` so the rest of the suite keeps its pass/fail signal.

Usage:
    python -m tools.check_import_boundaries [core_root]

Exits 0 with no output if the tree is clean, or 1 and a grouped
violation inventory if not -- suitable as a CI gate once the inventory
is discharged; run today via ``tests/test_import_boundaries.py``.
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORE_ROOT = REPO_ROOT / "core"

ETF_DOMAIN = "etf"

# Top-level package name under core/ -> domain name, or "kernel" for the
# shared kernel (exempt from the dependency table as an import target
# only -- see ALLOWED_DEPENDENCIES["kernel"] below).
DOMAIN_OF_TOPLEVEL: dict[str, str] = {
    "market_data": "data",
    "analytics": ETF_DOMAIN,
    "statistics": "statistics",
    "governance": "governance",
    "validation": "validation",
    "research": "research",
    "reporting": "reporting",
    "shared": "kernel",
    "domain": "kernel",
}

# ETF-specific symbols that currently live inside asset-class-neutral
# modules. Boundary-hardening step 1 does not move files, so the ETF
# domain cannot be identified by package path alone: an import of one of
# these names is attributed to the ``etf`` domain regardless of which
# module currently hosts the definition.
#
# This mapping is therefore also the inventory of *where the ETF/Data
# split has not been made yet* -- each entry is a generic module that
# still declares an asset-class-specific name. It shrinks to empty when
# the split is real; it is not an allow-list and nothing is exempted by
# appearing here.
ETF_SYMBOLS_BY_MODULE: dict[str, frozenset[str]] = {
    "core.shared.ids": frozenset({"ETFId"}),
    "core.market_data.domain.models": frozenset({"ETF"}),
    "core.market_data.persistence.repository": frozenset(
        {"insert_etf", "get_etf", "get_etf_by_ticker"}
    ),
}

# docs/PLATFORM_ARCHITECTURE_V1.md Section 5's allowed-dependency table,
# extended with the ETF domain. Same-domain imports are always allowed
# and are not listed here. The kernel is exempt as an import *target*
# for every domain (checked directly in check_repository, not via this
# table) but may itself depend on nothing under core/ -- AD-049 part 5.
#
# ``etf`` deliberately appears in no other domain's value set (AD-068
# decision 2). Section 1 of the architecture document requires that
# adding an asset class never touch Research, Validation, Statistics,
# Governance, or Reporting, so an edge *into* ETF from any of them is a
# boundary violation by construction -- including from Data, which
# "never calls upward".
ALLOWED_DEPENDENCIES: dict[str, frozenset[str]] = {
    "data": frozenset(),
    "statistics": frozenset(),
    ETF_DOMAIN: frozenset({"data", "statistics"}),
    "governance": frozenset({"data"}),
    "validation": frozenset({"data", "statistics", "governance"}),
    "research": frozenset({"data", "statistics", "governance", "validation"}),
    "reporting": frozenset({"data", "statistics", "governance", "validation", "research"}),
    "kernel": frozenset(),
}


class UnmappedPackageError(Exception):
    """Raised when a top-level package under ``core/`` is not present in
    ``DOMAIN_OF_TOPLEVEL``. AD-049 part 5: an unrecognized package must
    fail the check loudly rather than being silently exempted -- silent
    exemption was the escape hatch this tightening closes."""


@dataclass(frozen=True)
class ImportRef:
    """One name pulled in by one import statement. ``symbol`` is the
    bound name for ``from X import symbol`` and None for ``import X`` --
    the distinction matters because an ETF symbol can be reached through
    an otherwise asset-class-neutral module path."""

    module: str
    symbol: str | None
    lineno: int


@dataclass(frozen=True)
class Violation:
    file: Path
    lineno: int
    imported_module: str
    from_domain: str
    to_domain: str
    imported_symbol: str | None = None

    @property
    def imported_name(self) -> str:
        """The full dotted name actually pulled in -- module plus symbol
        when the symbol is what carries the domain attribution."""
        if self.imported_symbol is None:
            return self.imported_module
        return f"{self.imported_module}.{self.imported_symbol}"

    @property
    def edge(self) -> str:
        return f"{self.from_domain} -> {self.to_domain}"

    def __str__(self) -> str:
        via_symbol = ""
        if self.imported_symbol is not None and self.to_domain == ETF_DOMAIN:
            via_symbol = (
                f" -- '{self.imported_symbol}' is an ETF-domain name hosted by "
                f"'{self.imported_module}'"
            )
        return (
            f"{self.file}:{self.lineno}: domain '{self.from_domain}' may not import "
            f"'{self.imported_name}' (domain '{self.to_domain}'){via_symbol} -- forbidden per "
            "docs/PLATFORM_ARCHITECTURE_V1.md Section 5"
        )


def _iter_python_files(core_root: Path):
    for path in sorted(core_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _domain_of_file(path: Path, core_root: Path) -> str | None:
    relative_parts = path.relative_to(core_root).parts
    if len(relative_parts) < 2:
        return None  # core/__init__.py itself -- not inside any subpackage
    toplevel = relative_parts[0]
    if toplevel not in DOMAIN_OF_TOPLEVEL:
        raise UnmappedPackageError(
            f"core/{toplevel} is not in DOMAIN_OF_TOPLEVEL -- add it to the "
            "mapping (as a domain or as \"kernel\" for shared-kernel) before "
            "this checker can run"
        )
    return DOMAIN_OF_TOPLEVEL[toplevel]


def _domain_of_imported_module(dotted_module: str) -> str | None:
    parts = dotted_module.split(".")
    if len(parts) < 2 or parts[0] != "core":
        return None
    toplevel = parts[1]
    if toplevel not in DOMAIN_OF_TOPLEVEL:
        raise UnmappedPackageError(
            f"import target core.{toplevel} is not in DOMAIN_OF_TOPLEVEL -- "
            "add it to the mapping (as a domain or as \"kernel\") before "
            "this checker can run"
        )
    return DOMAIN_OF_TOPLEVEL[toplevel]


def _resolve_relative_import(file: Path, core_root: Path, node: ast.ImportFrom) -> str | None:
    """Resolve a relative ``ImportFrom`` (``node.level > 0``) found in
    `file` to its absolute dotted module string, e.g. ``'core.validation.
    gate'``. Returns None if the import climbs above ``core/`` itself
    (not resolvable to a core module; treated as out of scope rather than
    silently ignored, per AD-049 part 5's "resolved or rejected")."""
    relative_parts = list(file.relative_to(core_root).parts)
    # A module's own package is its parent directory; for `__init__.py`
    # that parent directory is also the package's own dotted name, so
    # dropping the filename gives the correct level=1 base in both cases.
    package_parts = relative_parts[:-1]

    base = ["core", *package_parts]
    climb = node.level - 1
    if climb:
        if climb >= len(base):
            return None
        base = base[: len(base) - climb]
    if node.module:
        base = base + node.module.split(".")
    return ".".join(base)


def _is_core_module(dotted_module: str) -> bool:
    return dotted_module == "core" or dotted_module.startswith("core.")


def _imported_core_references(tree: ast.AST, file: Path, core_root: Path) -> list[ImportRef]:
    """Every name of the form 'core...' referenced by an import in `tree`
    (absolute or relative), one ``ImportRef`` per bound name.

    ``from X import a, b`` yields one ref per alias rather than one per
    statement, because ``a`` and ``b`` can belong to different domains
    when an ETF symbol shares a module with asset-class-neutral ones.
    Relative imports are resolved to their absolute target rather than
    skipped -- AD-049 part 5: a relative import must not be invisible to
    the checker."""
    found: list[ImportRef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_core_module(alias.name):
                    found.append(ImportRef(module=alias.name, symbol=None, lineno=node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                module = node.module if node.module and _is_core_module(node.module) else None
            else:
                resolved = _resolve_relative_import(file, core_root, node)
                module = resolved if resolved and _is_core_module(resolved) else None
            if module is None:
                continue
            for alias in node.names:
                symbol = None if alias.name == "*" else alias.name
                found.append(ImportRef(module=module, symbol=symbol, lineno=node.lineno))
    return found


def _domain_of_reference(ref: ImportRef) -> str | None:
    """The domain an imported name belongs to. A symbol listed in
    ``ETF_SYMBOLS_BY_MODULE`` is ETF-domain no matter which module hosts
    it -- that reattribution is the whole point of step 1, since files do
    not move."""
    if ref.symbol is not None and ref.symbol in ETF_SYMBOLS_BY_MODULE.get(
        ref.module, frozenset()
    ):
        return ETF_DOMAIN
    return _domain_of_imported_module(ref.module)


def check_repository(core_root: Path = DEFAULT_CORE_ROOT) -> list[Violation]:
    """Scan every ``.py`` file under `core_root` and return every import
    that violates docs/PLATFORM_ARCHITECTURE_V1.md Section 5's
    dependency table. Empty list means the tree is clean."""
    violations: list[Violation] = []
    for file in _iter_python_files(core_root):
        from_domain = _domain_of_file(file, core_root)
        if from_domain is None:
            continue  # core/__init__.py itself -- not inside any subpackage
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        for ref in _imported_core_references(tree, file, core_root):
            to_domain = _domain_of_reference(ref)
            if to_domain is None or to_domain == from_domain:
                continue
            if to_domain == "kernel":
                continue  # kernel is exempt as an import target for every domain
            if to_domain not in ALLOWED_DEPENDENCIES.get(from_domain, frozenset()):
                violations.append(
                    Violation(
                        file=file.relative_to(REPO_ROOT) if file.is_relative_to(REPO_ROOT) else file,
                        lineno=ref.lineno,
                        imported_module=ref.module,
                        from_domain=from_domain,
                        to_domain=to_domain,
                        imported_symbol=ref.symbol,
                    )
                )
    return violations


def format_inventory(violations: list[Violation]) -> str:
    """Render `violations` as an explicit inventory grouped by domain
    edge, most-populated edge first. This is the artifact boundary-
    hardening step 1 produces: a named, countable list of the couplings
    a later step has to discharge, not a bare pass/fail."""
    if not violations:
        return "Import boundary check passed: no violations found."

    by_edge: dict[str, list[Violation]] = defaultdict(list)
    for violation in violations:
        by_edge[violation.edge].append(violation)

    lines = [
        f"Import boundary check FAILED: {len(violations)} violation(s) "
        f"across {len(by_edge)} forbidden domain edge(s).",
        "",
    ]
    for edge in sorted(by_edge, key=lambda e: (-len(by_edge[e]), e)):
        edge_violations = by_edge[edge]
        lines.append(f"{edge}  ({len(edge_violations)} violation(s))")
        for violation in sorted(edge_violations, key=lambda v: (str(v.file), v.lineno)):
            lines.append(f"    {violation.file}:{violation.lineno}  {violation.imported_name}")
        lines.append("")

    if any(v.to_domain == ETF_DOMAIN for v in violations):
        lines.append(
            "ETF-domain names still hosted by asset-class-neutral modules "
            "(ETF_SYMBOLS_BY_MODULE):"
        )
        for module in sorted(ETF_SYMBOLS_BY_MODULE):
            lines.append(f"    {module}: {', '.join(sorted(ETF_SYMBOLS_BY_MODULE[module]))}")
        lines.append("")

    return "\n".join(lines).rstrip()


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    core_root = Path(argv[0]).resolve() if argv else DEFAULT_CORE_ROOT
    violations = check_repository(core_root)
    if not violations:
        print(f"Import boundary check passed: no violations found under {core_root}")
        return 0
    print(f"Scanned {core_root}")
    print(format_inventory(violations))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
