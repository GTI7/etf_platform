"""Asset-class-neutral storage substrate.

``core.store`` owns the persistence *primitives* -- opening a connection
and applying schema migrations -- and nothing else. It holds no table
names, no row mappers, no aggregates, and no notion of what is being
stored. Repository functions (which do know table names) stay in their
owning domain: ``core.market_data.persistence.repository`` for market
data, ``core.analytics.persistence.repository`` for ETF scoring.

Its own domain, not the shared kernel: the kernel is a pure value
vocabulary (``Money``, ``Clock``, ids) with no I/O, and folding a module
that opens files and executes SQL into it would make ``core.shared``
importing sqlite3 unflaggable. See docs/ARCHITECTURE_DECISIONS.md AD-069.
"""
