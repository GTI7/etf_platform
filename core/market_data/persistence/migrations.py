"""Compatibility re-export. ``run_migrations`` moved to
``core.store.migrations`` (AD-069); it is a storage primitive with no
market-data content and had no business living in the Data domain.

**PERMANENT, not a transitional alias.** Its primary reason is not hash
protection but pinned-commit module resolution: a pinned experiment
script's legacy import resolves through HEAD's ``core.__path__`` and
binds *this* file, so deleting it turns every archived cycle's
reproduction into an uncaught runner crash rather than a governed
failure status. See ``core/market_data/persistence/database.py`` for the
full mechanism and for the two-clause retirement condition (AD-069),
whose binding clause is about **pinned commits**, not about the current
working tree. **No new code may import from here.**
"""

from __future__ import annotations

from core.store.migrations import run_migrations

__all__ = ["run_migrations"]
