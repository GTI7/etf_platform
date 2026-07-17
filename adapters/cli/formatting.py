from __future__ import annotations

from core.analytics.ranked_report import ETFAnalysisReport


def format_etf_analysis_report(report: ETFAnalysisReport) -> str:
    """Plain-text rendering of an ETFAnalysisReport.

    Every value printed comes directly from a field already on the report
    -- nothing here calculates, interprets, or summarizes anything.
    dimension_scores is sorted by dimension name only for deterministic
    display order; the values themselves are untouched.
    """
    lines = [
        f"Ticker: {report.ticker}",
        f"Name: {report.name}",
        f"Analysis date: {report.analysis_date.isoformat()}",
        f"Scoring profile id: {report.scoring_profile_id}",
        f"Overall score: {report.overall_score}",
        f"Rank: {report.rank} of {report.peer_count}",
    ]

    if report.dimension_scores:
        lines.append("Dimension scores:")
        for dimension in sorted(report.dimension_scores, key=lambda d: d.value):
            lines.append(f"  {dimension.value}: {report.dimension_scores[dimension]}")
    else:
        lines.append("Dimension scores: none")

    max_drawdown = report.max_drawdown if report.max_drawdown is not None else "N/A"
    lines.append(f"Max drawdown: {max_drawdown}")

    return "\n".join(lines)
