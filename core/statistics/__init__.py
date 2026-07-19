"""Statistics domain (Layer 0, foundation).

Reserved package for the platform's future pure, stateless statistical
library -- Spearman/Pearson correlation, permutation nulls, block
bootstrap confidence intervals, Holm-Bonferroni correction, and related
functions, per docs/PLATFORM_ARCHITECTURE_V1.md Section 4.3.

Empty as of Phase 0 of docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md:
no function has been extracted or written here yet. The equivalent
logic exists today only as duplicated, inlined helpers inside four
``experiments/validate_*.py`` scripts, which remain unmodified and
authoritative for their own historical results.

Depends on nothing. Per the architecture document, Statistics may never
import from any other domain (``core.market_data``, ``core.analytics``,
or any future ``core.governance`` / ``core.validation`` / ``core.research``
/ ``core.reporting`` package) -- the one hard rule with no exception.
"""
