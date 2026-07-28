"""Import-direction and dependency-purity boundary checker for ``core/``.

Two independent passes over ``core/`` each check one rule:

1. **Direction.** The cross-domain dependency table in
   docs/PLATFORM_ARCHITECTURE_V1.md Section 5 -- ``check_repository`` /
   ``format_inventory``. This is the "Import-direction lint" the
   architecture document itself specifies as one of the two enforcement
   mechanisms for domain boundaries (Section 5, "Enforcement", item 1).
2. **Purity.** A dependency-purity rule motivated by AD-005 and stated at
   ``core/``'s scope by AD-078 Section 3 -- ``check_dependency_purity`` /
   ``format_purity_inventory``. What this checker actually enforces is
   narrower than AD-005's own text: ``core/`` may import standard-library
   modules *or* ``core.*`` modules, not "standard library only" in the
   literal sense AD-005 states for the whole codebase. AD-005 is this
   rule's motivation, not a claim that this checker fully enforces AD-005
   as written -- dependency direction (rule 1, above) is a separate
   concern this rule does not fold in. Until 2026-07-28 even the
   narrower purity constraint was prose in a decision record and nothing
   else; every import whose top-level name was not ``core`` was simply
   not looked at, so ``import numpy`` inside ``core/statistics`` would
   have been invisible to this tool and to the suite. A same-day second
   change closed a narrower gap AD-078 Section 3 named directly: a
   repository-local sibling of ``core`` (``import adapters`` inside
   ``core/``) was accepted by this rule until then, checked only by a
   single test rather than by this checker (AD-078 Known Weakness 2).

The two rules are deliberately separate functions returning separate
types. A third-party import has no domain and therefore no ``edge``;
folding it into the direction inventory would have required inventing a
pseudo-domain for it, and would have made the pinned ETF coupling
inventory in ``tests/test_import_boundaries.py`` fail for a reason that
has nothing to do with ETF. ``main`` runs both and exits 1 if either
reports.

Both use stdlib ``ast`` only -- AD-005 applies to this checker as much as
to what it checks, and a purity checker that itself needed a package
would be self-refuting.

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
   ``core.market_data.domain.models`` and the ``*_etf`` repository
   functions. An import is attributed to the ``etf`` domain by the
   *symbol* it names, not by the module that currently happens to host
   it. This is what lets the checker report "governance -> etf" for a
   line whose module path says ``core.market_data``.

   The shared kernel was a third entry until 2026-07-27, when
   ``core.shared.ids`` declared ``ETFId``. That entry is gone because
   **the name is gone**: the alias was renamed to ``InstrumentId``
   (Engine Boundary cleanup item C1), which is the asset-class-neutral
   vocabulary docs/PLATFORM_ARCHITECTURE_V1.md Section 4.6 already uses
   for the same concept (``fetch(self, instrument_id: str, ...)``). It
   was **not** removed because the symbol was reclassified, exempted, or
   relocated -- the failure mode AD-068 decision 5 warns about -- and
   nothing about the kernel's rules changed.
   ``tests/test_import_boundaries.py::test_no_kernel_module_hosts_an_etf_symbol``
   now asserts that no kernel module may reappear in this mapping.

No domain may depend on ``etf``: an asset class is a plug-in above the
platform, never something the platform reaches down into. ``etf`` itself
may depend on ``data`` and ``statistics`` (and the kernel, like every
domain).

``store`` (boundary-hardening step 2, AD-069) is the substrate at the
opposite end of the table. ``core.store`` holds only the storage
primitives (``connect``, ``run_migrations``), so it may depend on
nothing. It is a domain rather than part of the kernel precisely so that
``kernel -> store`` stays checkable -- the kernel is a pure value
vocabulary and must not acquire I/O.

Unlike ``etf``, ``store`` is *reachable*, but only from the domains with
a demonstrated importer: ``data`` and ``governance``, and no others. The
grant list is **demand-driven** (AD-069) -- a domain is added when a real
importer appears, by recorded decision, in the commit that introduces it.
A granted-but-unused edge is invisible drift a future module can occupy
silently; in particular ``statistics -> store`` stays forbidden on
*purity* grounds, for the same reason the kernel is denied I/O.

**This check does not pass today, by design** (AD-068 decision 4). Step 1
is inventory, not repair: it makes the pre-existing coupling fail loudly
and enumerably so that a later step can discharge it deliberately.
``format_inventory`` renders that enumeration, and
``tests/test_import_boundaries.py`` carries the failure as a strict
``xfail`` so the rest of the suite keeps its pass/fail signal.

**Dependency purity (AD-005), added 2026-07-28.** Rule 2 classifies the
top-level name of every absolute import in every file under ``core/``
into exactly one of three buckets, and there is no fourth:

* **Standard library** -- the name is in ``sys.stdlib_module_names``.
  Allowed. That set is the interpreter's own answer to "is this
  stdlib", which is why it is used instead of a hand-kept list: a
  hand-kept list is a thing to forget to update, and forgetting would
  reject a legal import rather than admit an illegal one only by luck.
* **``core`` itself** -- the top-level name equals ``core_root``'s own
  name (``"core"`` on the real tree). Allowed *here*; whether a
  particular ``core.<domain>`` target is allowed is rule 1's question,
  and rule 1 answers it against AD-068/AD-069. Rule 2 deliberately does
  not re-litigate that.
* **Everything else** -- a violation, including a repository-local
  sibling of ``core`` (``adapters``, ``experiments``, a future
  ``workloads``, ...). This bucket is not "third-party packages we
  thought of"; it is the complement of the first two, so an unrecognized
  top-level name fails rather than falling through. No package name is
  hardcoded anywhere in this module, and adding one would be the bug:
  ``numpy``, ``scipy`` and ``pandas`` are rejected by the same clause
  that rejects a name nobody has heard of. This is AD-049 part 5's
  "resolved or rejected, never silently skipped" applied to the
  dependency axis. ``ForeignImport.repository_local`` records, for
  message purposes only, whether the rejected name is a real sibling
  package (found by the same repository-local discovery used to resolve
  rule 1's relative imports) or resolves to nothing in this repository
  at all -- both are rejected identically; AD-078 Section 3 draws no
  distinction between them.

  Until 2026-07-28 this bucket held only genuinely unresolvable names: a
  repository-local sibling of ``core`` was accepted here, on the
  reasoning above that rule 1 was the place to police it. AD-078 Section
  3 states the narrower rule directly -- "no repository-local package
  other than ``core`` itself" -- and until this change that half of the
  rule had exactly one enforcement mechanism, a single test
  (`tests/test_import_boundaries.py::
  test_real_repository_core_imports_no_non_core_repository_local_package`),
  with no checker rule behind it (AD-078 Known Weakness 2). This is the
  same purity flow, extended to answer rule 1's question after all for
  this one case, not a second mechanism: repository-local discovery and
  classification still happen in ``_repository_local_toplevel_names``,
  called once, from this function alone.

``ast.walk`` descends the entire module body, so a *guarded* import
(``try: import numpy / except ImportError:``), an ``if TYPE_CHECKING:``
import, and a function-local import are all reached and all reported. A
guarded import is still a declared dependency: the guard changes what
happens when the package is absent, not whether the code is written
against it.

Rule 2 does **not** consult ``DOMAIN_OF_TOPLEVEL``. Purity is orthogonal
to domain membership, so a package that has not yet been classified is
still checked -- an unmapped package is a rule-1 error, and it must not
also be a rule-2 blind spot.

Relative imports are out of rule 2's scope by construction: ``from .
import x`` and ``from ..shared import y`` can only name something inside
the repository, so they cannot introduce a third-party dependency. Rule
1 already resolves them for direction purposes.

Dynamic imports (``importlib.import_module(name)``, ``__import__``) are
invisible to any AST check, here as everywhere. This is a known and
unclosed limit, not an exemption.

Usage:
    python -m tools.check_import_boundaries [core_root]

Exits 0 with no output if the tree is clean under both rules, or 1 and a
grouped violation inventory if not -- suitable as a CI gate once the
direction inventory is discharged; run today via
``tests/test_import_boundaries.py``. Rule 2 is clean today and is
asserted directly, with no xfail: the purity milestone is enforcement of
a claim already true, not deferral of one that is not.
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORE_ROOT = REPO_ROOT / "core"

# The interpreter's own inventory of standard-library top-level names,
# not a hand-kept list (AD-005 purity rule; see the module docstring).
_STDLIB_TOPLEVEL_NAMES: frozenset[str] = frozenset(sys.stdlib_module_names)

ETF_DOMAIN = "etf"
STORE_DOMAIN = "store"

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
    "store": STORE_DOMAIN,
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
#
# ``store`` (AD-069) is the substrate, and its grant list is
# **demand-driven**: it appears only in the value sets of the domains
# that actually import it today -- ``data`` (the two permanent re-export
# shims at core/market_data/persistence/) and ``governance``
# (reconstruction_loader, reproduction_runner) -- and has an empty set of
# its own. A domain is added here when a real importer appears, by
# recorded decision, in the commit that introduces the importer; a
# granted-but-unused edge is invisible drift that a future module can
# occupy silently.
#
# Two of the omissions are not "no importer yet" but permanent:
# ``statistics -> store`` is refused on **purity** (Section 4.3 defines
# Statistics as a pure computational library; it is denied I/O for the
# same reason the kernel is), and ``kernel -> store`` must stay a
# violation so that ``core.shared`` cannot acquire sqlite3 unflagged --
# which is the whole reason ``store`` is a domain rather than part of the
# kernel exemption. Repository functions, which know table names, stay in
# their owning domain and are not part of ``store``.
ALLOWED_DEPENDENCIES: dict[str, frozenset[str]] = {
    "data": frozenset({STORE_DOMAIN}),
    "statistics": frozenset(),
    ETF_DOMAIN: frozenset({"data", "statistics"}),
    "governance": frozenset({"data", STORE_DOMAIN}),
    "validation": frozenset({"data", "statistics", "governance"}),
    "research": frozenset({"data", "statistics", "governance", "validation"}),
    "reporting": frozenset({"data", "statistics", "governance", "validation", "research"}),
    STORE_DOMAIN: frozenset(),
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


# --- Rule 2: dependency purity (AD-005) ----------------------------------


@dataclass(frozen=True)
class ForeignImport:
    """One import in ``core/`` whose top-level name is neither standard
    library nor ``core`` itself (AD-078 Section 3).

    Distinct from ``Violation`` on purpose: this has no ``from_domain``,
    no ``to_domain`` and no ``edge``, because a package outside the
    repository is not in the domain graph at all. Giving it a synthetic
    domain so it could share ``Violation`` would have put a name that is
    not a domain into ``format_inventory``'s edge grouping and into the
    ETF coupling inventory that ``tests/test_import_boundaries.py``
    pins.

    ``repository_local`` distinguishes the two ways a name can land in
    this bucket: a real sibling package under the repository root
    (``adapters``, ``experiments``, a future ``workloads``, ...) versus a
    name that resolves to nothing in this repository at all (a genuine
    third-party package, or a typo). Both are AD-078 Section 3
    violations for ``core/`` either way -- the flag only changes the
    message, it never changes the verdict."""

    file: Path
    lineno: int
    imported_module: str
    top_level: str
    repository_local: bool = False

    def __str__(self) -> str:
        if self.repository_local:
            return (
                f"{self.file}:{self.lineno}: '{self.imported_module}' imports the "
                f"repository-local package '{self.top_level}', not 'core' -- core/ imports "
                "only the standard library and core.* (AD-078 Section 3)"
            )
        return (
            f"{self.file}:{self.lineno}: '{self.imported_module}' is not importable from "
            f"the standard library or from 'core' itself -- top-level name "
            f"'{self.top_level}' is neither in sys.stdlib_module_names nor 'core'. "
            "core/ imports only standard-library or core.* modules (AD-078 Section 3)"
        )


def _repository_local_toplevel_names(local_root: Path) -> frozenset[str]:
    """Every top-level name an ``import X`` inside this repository could
    resolve to locally, read from `local_root` rather than declared.

    A directory counts when it is a regular package (``__init__.py``) or
    a PEP 420 namespace package that actually holds modules -- both are
    importable with the repository root on ``sys.path``, which
    ``pyproject.toml``'s ``pythonpath = ["."]`` puts there for the suite.
    A bare ``.py`` file at the root counts as a module. Directories
    holding no Python at all (``docs/``, ``migrations/``,
    ``research_archive/``) are not importable and are not listed, so
    naming one is a purity violation rather than a silent pass.

    Reading the tree rather than hardcoding the seven current names is
    what keeps a newly added top-level package from being reported as a
    third-party dependency the day it appears; it is also what makes the
    rule behave identically over a synthetic tree in ``tmp_path``, where
    `local_root` is the temporary directory, not this repository.

    Since 2026-07-28 (AD-078 Section 3) this set no longer gates
    ``check_dependency_purity``'s accept/reject decision for imports made
    from inside ``core/`` -- only the name ``"core"`` itself does that
    now. This function still runs and its result is still used, to mark
    a rejected sibling import as ``ForeignImport.repository_local=True``
    so the reported message can say "this is a real package next door,
    just not the one core/ may import" instead of treating it exactly
    like a typo or an uninstalled third-party name.

    Boundary, by design and not by oversight: only one level is examined.
    A directory qualifies as a package (``__init__.py``) or as a
    namespace package with at least one ``.py`` file as its *direct*
    child (``entry.glob``, not ``entry.rglob``). A directory whose only
    Python lives two or more levels down, with neither an ``__init__.py``
    nor a loose ``.py`` file directly inside it, is not discovered and is
    therefore treated as not locally importable. Recursive discovery of
    arbitrary nested Python directories is out of scope; extending this
    function to walk deeper is a semantics change, not a bug fix."""
    names: set[str] = set()
    for entry in sorted(local_root.iterdir()):
        if entry.name.startswith(".") or not entry.name.split(".")[0].isidentifier():
            continue
        if entry.is_dir():
            if (entry / "__init__.py").exists() or any(entry.glob("*.py")):
                names.add(entry.name)
        elif entry.suffix == ".py":
            names.add(entry.stem)
    return frozenset(names)


def _absolute_imported_modules(tree: ast.AST) -> Iterator[tuple[str, int]]:
    """Every absolute dotted module name named by an import in `tree`,
    with its line number.

    ``ast.walk`` visits the whole tree, so this reaches imports nested in
    ``try``/``except ImportError``, in ``if TYPE_CHECKING:``, and inside
    function and class bodies -- a guarded third-party import is still a
    third-party import. Relative imports (``node.level > 0``) are skipped
    because they can only name something inside the repository; rule 1
    resolves those for direction purposes."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                yield node.module, node.lineno


def check_dependency_purity(core_root: Path = DEFAULT_CORE_ROOT) -> list[ForeignImport]:
    """Scan every ``.py`` file under `core_root` and return every import
    that AD-078 Section 3 forbids: one whose top-level name is neither
    standard library nor `core_root`'s own name (``"core"`` on the real
    tree). Empty list means ``core/`` depends on nothing but Python
    itself and ``core.*``.

    The repository root is taken to be `core_root`'s parent, which is
    true of the real tree and of any synthetic one. A repository-local
    sibling package (``adapters``, ``experiments``, ...) is *not*
    accepted here even though ``_repository_local_toplevel_names`` finds
    it -- that discovery is still used, but only to mark a violation as
    ``repository_local`` for an accurate message, not to admit it.
    AD-078 Section 3: "No repository-local package other than `core`
    itself." Before 2026-07-28 this function accepted any repository-
    local name, which left that half of the rule enforced by a single
    test (`tests/test_import_boundaries.py::
    test_real_repository_core_imports_no_non_core_repository_local_package`)
    with no checker mechanism behind it -- AD-078 Known Weakness 2.

    Unlike ``check_repository`` this does not consult
    ``DOMAIN_OF_TOPLEVEL`` and so never raises ``UnmappedPackageError``:
    an unclassified package is a direction-rule error, and it must not
    also escape the purity rule while it stays unclassified."""
    local_names = _repository_local_toplevel_names(core_root.parent)
    core_name = core_root.name
    foreign: list[ForeignImport] = []
    for file in _iter_python_files(core_root):
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        for module, lineno in _absolute_imported_modules(tree):
            top_level = module.split(".")[0]
            if top_level in _STDLIB_TOPLEVEL_NAMES or top_level == core_name:
                continue
            foreign.append(
                ForeignImport(
                    file=file.relative_to(REPO_ROOT) if file.is_relative_to(REPO_ROOT) else file,
                    lineno=lineno,
                    imported_module=module,
                    top_level=top_level,
                    repository_local=top_level in local_names,
                )
            )
    return foreign


def format_purity_inventory(foreign: list[ForeignImport]) -> str:
    """Render `foreign` grouped by offending top-level package, most-
    populated first -- the same shape ``format_inventory`` uses, because
    the useful unit of a purity failure is "which dependency crept in",
    not "which line"."""
    if not foreign:
        return (
            "Dependency purity check passed: core/ imports only the standard "
            "library and core.* modules."
        )

    by_package: dict[str, list[ForeignImport]] = defaultdict(list)
    for item in foreign:
        by_package[item.top_level].append(item)

    lines = [
        f"Dependency purity check FAILED: {len(foreign)} import(s) of "
        f"{len(by_package)} non-standard-library, non-'core' package(s) -- "
        "core/ imports only standard-library or core.* modules (AD-078 Section 3).",
        "",
    ]
    for package in sorted(by_package, key=lambda p: (-len(by_package[p]), p)):
        package_imports = by_package[package]
        lines.append(f"{package}  ({len(package_imports)} import(s))")
        for item in sorted(package_imports, key=lambda i: (str(i.file), i.lineno)):
            lines.append(f"    {item.file}:{item.lineno}  {item.imported_module}")
        lines.append("")

    return "\n".join(lines).rstrip()


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    core_root = Path(argv[0]).resolve() if argv else DEFAULT_CORE_ROOT
    violations = check_repository(core_root)
    foreign = check_dependency_purity(core_root)
    if not violations and not foreign:
        print(f"Import boundary check passed: no violations found under {core_root}")
        return 0
    print(f"Scanned {core_root}")
    if violations:
        print(format_inventory(violations))
    if foreign:
        if violations:
            print()
        print(format_purity_inventory(foreign))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
