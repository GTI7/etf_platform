"""Reporting domain (Layer 3, leaf).

Step 8 v0.1 (docs/ARCHITECTURE_DECISIONS.md AD-046,
docs/STEP_8_REPORTING_DESIGN.md): ``report_model.ReportModel``,
``report_builder.build_report``, ``json_renderer.render_json``, and
``markdown_renderer.render_markdown``. Callers import each submodule
explicitly -- this package itself re-exports nothing, the same
convention ``core.statistics``/``core.governance``/``core.research``/
``core.validation`` already follow.

Depends on every other domain's structured output, read-only. A true
leaf: nothing may depend on Reporting, and no domain's correctness may
ever depend on a report having been generated. ``report_builder.py`` is
the only module in this package permitted to import
``core.validation``; both renderers take ``ReportModel`` only.
"""
