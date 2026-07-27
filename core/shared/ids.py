"""Shared-kernel identifier vocabulary (AD-003): a `NewType` over `str`
per identity, so an identifier cannot be passed where a different
identifier is expected, with no runtime cost.

**Only names with a live caller live here.** Five names originally
reserved ahead of any caller -- `UniverseId`, `PortfolioId`, `HoldingId`
(AD-003) and `ArtifactRef` (AD-031) -- were withdrawn on 2026-07-27
during the Engine Boundary cleanup, having gone unused since Phase 0. A
`NewType` alias costs one line to introduce whenever its first real
caller appears, and until then it is indistinguishable from a domain
this platform actually has: a reader encountering `PortfolioId` here has
no way to tell that no portfolio concept exists anywhere in the
repository. `ProjectId` is kept because `core.research` uses it
throughout, and `ScoreId` because `core.analytics.domain.models` does.

The activation triggers those names were reserved against are unchanged
and are still recorded in docs/BASELINE_STATUS.md; withdrawing the alias
withdraws no decision about whether a Portfolio or Universe domain
should one day exist.
"""

from __future__ import annotations

from typing import NewType

# The identity of a tradeable instrument. Named for what the kernel is
# allowed to know -- `docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.6
# already writes the Data-domain provider contract as
# `fetch(self, instrument_id: str, ...)`, so this is the document's own
# vocabulary, not a coined one. It was called `ETFId` from Phase 0 until
# 2026-07-27; see the Engine Boundary cleanup record for why a kernel
# type may not carry an asset class in its name. Fields typed by it are
# still spelled `etf_id`, because the *aggregates* holding them (`ETF`,
# `PriceBar`, `Score`) are genuinely ETF-workload objects and their
# extraction is a separate, deferred piece of work.
InstrumentId = NewType("InstrumentId", str)
ScoreId = NewType("ScoreId", str)

# The Research domain's project-registry key (AD-031). Constructed only
# through `core.research.project_id.create_project_id`, never directly.
ProjectId = NewType("ProjectId", str)
