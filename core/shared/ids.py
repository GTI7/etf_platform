from __future__ import annotations

from typing import NewType

ETFId = NewType("ETFId", str)
UniverseId = NewType("UniverseId", str)
ScoreId = NewType("ScoreId", str)
PortfolioId = NewType("PortfolioId", str)
HoldingId = NewType("HoldingId", str)

# Reserved for the future platform (docs/PLATFORM_ARCHITECTURE_V1.md,
# docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md Phase 0, task 4). Not
# used by any code today, and no existing identifier is migrated to use
# them -- these exist only so the Research domain's ProjectId and a
# future Governance/Reporting ArtifactRef have a stable name to
# converge on, following the same NewType-over-str convention as the
# identifiers above (AD-003), rather than each future domain inventing
# its own ad hoc string-id type.
ProjectId = NewType("ProjectId", str)
ArtifactRef = NewType("ArtifactRef", str)
