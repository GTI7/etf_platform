"""Compatibility re-export. ``connect`` moved to ``core.store.connection``
(AD-069); it is a storage primitive with no market-data content and had
no business living in the Data domain.

**This module is PERMANENT. It is not a transitional alias, and deleting
it is a prohibited act unless the condition at the bottom of this
docstring is satisfied in full.** It exists for two reasons, in priority
order.

**PRIMARY -- pinned-commit module resolution.**
``core/governance/reproduction_runner.py`` reproduces archived research
cycles by prepending a pinned worktree to ``sys.path`` and
``exec_module``-ing the pinned experiment script. But
``sys.modules['core']`` is *already populated with HEAD's package* -- the
runner itself is ``core.governance.reproduction_runner``. Python
therefore resolves ``core.market_data.persistence.database`` through
**HEAD's** ``core.__path__``, not through ``sys.path``, so a pinned
script's legacy import binds **this file**, never the worktree's own
copy. There is no ``sys.modules`` isolation anywhere in ``core/``. All
three archived cycles pin resolvable commits (``07f0da3``, ``19771d4``,
``8831d54``) and all three pin ``daily_etf_universe_update.py``, which
imports both legacy paths. This module is therefore live runtime
infrastructure for reproduction, and would remain so even if every
hash-protected file were retired tomorrow.

**SECONDARY -- hash-protected evidence.** The eight ``experiments/*.py``
scripts and ``maintenance/remediate_h3_invalid_pricebar_rows.py`` are
hash-protected Phase-0 evidence (tests/fixtures/protected_file_hashes.json,
tests/test_repository_integrity_snapshot.py) and may not be edited to
change their import lines.

**If this module is deleted, reproduction does not degrade -- it
crashes.** The resulting ``ImportError`` is not mapped to ``DRIFTED`` or
``UNVERIFIABLE``: in ``reproduction_runner``,
``_load_expected_tickers_from_worktree`` catches ``OSError`` only, its
caller catches ``ReproductionRunnerError`` only, and the failure is
raised before the ``reconstruct_database`` block whose broad handler
would have governed it. It propagates out of ``run_reproduction``
uncaught, with no status and no evidence record.

**No new code may import from here.** Import ``core.store.connection``
instead; ``tests/test_store_extraction.py`` fails if any importer outside
the frozen set appears.

**Retirement condition (AD-069) -- both clauses must hold:**

(a) no file in the working tree imports either legacy path; **and**
(b) **no reproducible commit imports either legacy path** -- for every
    cycle under ``research_archive/*/`` with a ``COMMIT.txt``, that
    pinned commit's own tree contains no import of
    ``core.market_data.persistence.database`` or
    ``core.market_data.persistence.migrations``.

(b) is strictly stronger than (a) and is the binding clause. Satisfying
(a) alone and deleting this module destroys the reproducibility of every
archived cycle **silently, with a fully green test suite**. (b) is not
satisfiable today and cannot become so while those three commits exist,
because pinned history is immutable. If it ever does, retirement is a
governance act requiring a new ADR that records which archived cycles
were re-verified after deletion and by whom -- a green suite is
necessary and not sufficient.
"""

from __future__ import annotations

from core.store.connection import connect

__all__ = ["connect"]
