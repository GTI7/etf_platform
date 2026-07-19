"""Reporting domain (Layer 3, leaf).

Reserved package for the platform's future rendering capability --
``ReportBuilder``, ``Renderer``, and ``ReportRegistry`` -- per
docs/PLATFORM_ARCHITECTURE_V1.md Section 4.5.

Empty as of Phase 0 of docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md: no
builder or renderer has been written here yet. Every research report to
date has been hand-written Markdown, transcribing figures that already
exist in a machine-readable JSON artifact -- see
docs/RESEARCH_PLATFORM_RETROSPECTIVE.md Section 3, item 7.

Depends on every other domain's structured output, read-only. A true
leaf: nothing may depend on Reporting, and no domain's correctness may
ever depend on a report having been generated.
"""
