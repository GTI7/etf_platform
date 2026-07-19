"""Repository-level, stdlib-only tooling.

Not part of the ``etf`` CLI, not installed, not a domain package under
``core/``. Scripts here check or generate structure across the
repository -- they never contain scoring, statistical, or research
business logic (that lives in ``core/`` or ``experiments/``).
"""

from __future__ import annotations
