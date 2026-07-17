from __future__ import annotations

from datetime import date

from core.analytics.ranked_report import ETFAnalysisReport, RankedETFReportEntry, ScoreHistoryEntry
from core.analytics.write_pipeline import WritePipelineResult
from core.market_data.domain.models import IngestionRun


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


def format_update_result(ticker: str, session_date: date, result: WritePipelineResult) -> str:
    """Plain-text rendering of a WritePipelineResult.

    Every value printed comes directly from the result -- nothing here
    calculates, interprets, or summarizes anything. price_ingestion_run_id
    is displayed as a factual skip note when None (ingestion was skipped
    because a PriceBar already existed for this exact ETF/session), never
    as a success/failure judgement.
    """
    price_ingestion = (
        result.price_ingestion_run_id
        if result.price_ingestion_run_id is not None
        else "skipped (price data already present)"
    )
    lines = [
        "ETF update completed",
        f"Ticker: {ticker}",
        f"Session date: {session_date.isoformat()}",
        f"Price ingestion run: {price_ingestion}",
        f"SMA run: {result.sma_run_id}",
        f"RSI run: {result.rsi_run_id}",
        f"Score run: {result.score_run_id}",
    ]
    return "\n".join(lines)


def _format_run(run: IngestionRun | None) -> list[str]:
    """One pipeline stage's most recent run, indented under its own label
    -- every value comes directly from the IngestionRun already resolved
    by the caller; nothing here calculates or interprets anything."""
    if run is None:
        return ["  No run recorded"]
    completed_at = run.completed_at.isoformat() if run.completed_at is not None else "N/A"
    error_message = run.error_message if run.error_message is not None else "none"
    return [
        f"  Status: {run.status.value}",
        f"  Pipeline date: {run.pipeline_date.isoformat()}",
        f"  Started at: {run.started_at.isoformat()}",
        f"  Completed at: {completed_at}",
        f"  Error: {error_message}",
    ]


def format_ranked_report(header: str, session_date: date, entries: list[RankedETFReportEntry]) -> str:
    """Plain-text rendering of a list of RankedETFReportEntry.

    Shared by `etf rank` (the full ranking, from generate_ranked_etf_report())
    and `etf compare` (a named subset, from compare_etfs()) -- both return
    the same entry type, so `header` is the only thing distinguishing the
    two callers' output; nothing else here differs by caller.

    Every value printed comes directly from a field already on each entry
    -- nothing here calculates, interprets, or summarizes anything,
    including which entry is first. `rank` is printed because it is
    already a field on the entry (screen_etfs()/compare_etfs() rank
    locally among survivors, not within the full universe -- this
    formatter does not know or care which; it prints whatever rank the
    entry already carries).

    An empty `entries` list is a valid, expected outcome (no Score yet for
    this profile/session, or no candidate survived) -- printed as an
    explicit factual line, never silently producing empty output.
    """
    lines = [header, f"Session date: {session_date.isoformat()}"]

    if not entries:
        lines.append("")
        lines.append("No ranked scores found for this profile and session date.")
        return "\n".join(lines)

    for entry in entries:
        lines.append("")
        lines.append(f"Rank {entry.rank}: {entry.ticker} ({entry.name})")
        lines.append(f"  Overall score: {entry.overall_score}")
        if entry.dimension_scores:
            lines.append("  Dimension scores:")
            for dimension in sorted(entry.dimension_scores, key=lambda d: d.value):
                lines.append(f"    {dimension.value}: {entry.dimension_scores[dimension]}")
        else:
            lines.append("  Dimension scores: none")
        max_drawdown = entry.max_drawdown if entry.max_drawdown is not None else "N/A"
        lines.append(f"  Max drawdown: {max_drawdown}")

    return "\n".join(lines)


def format_score_history(ticker: str, entries: list[ScoreHistoryEntry]) -> str:
    """Plain-text rendering of one ETF's own score history under one
    scoring profile, from get_score_history().

    No rank, no peer comparison -- ScoreHistoryEntry carries neither (this
    is one ETF's own scores over time, not a comparison against others).
    Every value printed comes directly from a field already on each entry
    -- nothing here calculates, interprets, or summarizes anything,
    including any trend across dates.

    An empty `entries` list is a valid, expected outcome (no Score yet for
    this ETF/profile, or none in the requested date range) -- printed as
    an explicit factual line, never silently producing empty output.
    """
    lines = [f"Ticker: {ticker}"]

    if not entries:
        lines.append("")
        lines.append("No score history found for this ticker and profile.")
        return "\n".join(lines)

    for entry in entries:
        lines.append("")
        lines.append(f"Session date: {entry.session_date.isoformat()}")
        lines.append(f"  Overall score: {entry.overall_score}")
        if entry.dimension_scores:
            lines.append("  Dimension scores:")
            for dimension in sorted(entry.dimension_scores, key=lambda d: d.value):
                lines.append(f"    {dimension.value}: {entry.dimension_scores[dimension]}")
        else:
            lines.append("  Dimension scores: none")

    return "\n".join(lines)


def format_status(
    ticker: str,
    price_ingestion_run: IngestionRun | None,
    sma_run: IngestionRun | None,
    rsi_run: IngestionRun | None,
    score_run: IngestionRun | None,
) -> str:
    """Plain-text rendering of the four write-pipeline stages' most recent
    runs for one ETF. Every value printed comes directly from the
    IngestionRun the caller already resolved for each stage -- nothing
    here calculates, interprets, or summarizes anything, including
    whether the reported states are 'good' or 'bad'."""
    lines = [f"Ticker: {ticker}"]
    for label, run in [
        ("Price ingestion", price_ingestion_run),
        ("SMA", sma_run),
        ("RSI", rsi_run),
        ("Score", score_run),
    ]:
        lines.append(f"{label}:")
        lines.extend(_format_run(run))
    return "\n".join(lines)
