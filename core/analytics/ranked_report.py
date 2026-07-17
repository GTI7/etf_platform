from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from core.analytics.domain.models import Dimension
from core.analytics.domain.ranking import rank_scores
from core.analytics.persistence.repository import (
    get_dimension_scores,
    get_indicator_values,
    get_scores_for_session,
)
from core.domain.exceptions import DomainError
from core.market_data.persistence.repository import get_etf
from core.shared.ids import ETFId


class MissingScoreError(DomainError):
    """Raised when generate_etf_analysis_report() is asked to analyse an
    ETF that has no Score for the given (scoring_profile_id,
    session_date). A Score is the one required precondition for a
    single-ETF analysis -- unlike max_drawdown (optional, resolves to
    None when absent), there is no meaningful analysis to return without
    it, so this fails loudly rather than returning None or a partial
    report."""


class InvalidScreeningCriteriaError(DomainError):
    """Raised when screen_etfs() is given criteria that cannot possibly be
    evaluated given the other supplied parameters -- a caller
    configuration error, not a valid "no matches" outcome. Currently:
    criteria.max_drawdown is set but risk_definition_id is None, so no
    candidate's max_drawdown could ever be resolved to check against it.
    Raised before any database work, unlike the per-ETF fail-closed
    exclusion screen_etfs() applies for individual candidates that lack
    the data a criterion needs."""


def _resolve_dimension_scores(conn: sqlite3.Connection, score_id: str) -> dict[Dimension, Decimal]:
    """The per-dimension breakdown behind one Score's overall_score."""
    return {
        dimension_score.dimension: dimension_score.value
        for dimension_score in get_dimension_scores(conn, score_id)
    }


def _resolve_max_drawdown(
    conn: sqlite3.Connection,
    risk_definition_id: str | None,
    etf_id: str,
    session_date: date,
) -> Decimal | None:
    """max_drawdown for one ETF/session, or None if risk_definition_id is
    omitted, or if supplied but no MAX_DRAWDOWN IndicatorValue exists yet
    -- never an error, since risk is an optional comparison metric."""
    if risk_definition_id is None:
        return None
    risk_values = get_indicator_values(
        conn, risk_definition_id, etf_id, start_date=session_date, end_date=session_date
    )
    return risk_values[0].value if risk_values else None


@dataclass(frozen=True, slots=True)
class RankedETFReportEntry:
    """One ranked ETF, resolved for display -- no persistence identity
    (no score_id, scoring_profile_id, session_date, or computed_at): just
    what a consumer of the report needs to see.

    dimension_scores exposes the same per-dimension values overall_score
    was already computed from (e.g. {MOMENTUM: ..., VALUE: ...}) -- the
    comparison-by-independent-method view, alongside the existing blended
    figure. No new scoring methodology: rank_scores() and overall_score
    are computed exactly as before.

    max_drawdown is a comparison metric only -- not a scoring dimension,
    not part of overall_score, and has no bearing on rank. None when
    generate_ranked_etf_report()'s risk_definition_id is omitted, or when
    supplied but no MAX_DRAWDOWN IndicatorValue exists yet for this
    ETF/session."""

    rank: int
    etf_id: ETFId
    ticker: str
    name: str
    overall_score: Decimal
    dimension_scores: dict[Dimension, Decimal]
    max_drawdown: Decimal | None


def generate_ranked_etf_report(
    conn: sqlite3.Connection,
    scoring_profile_id: str,
    session_date: date,
    risk_definition_id: str | None = None,
) -> list[RankedETFReportEntry]:
    """Compose the existing Phase 4 pieces into one usable ranked report:
    get_scores_for_session() -> rank_scores() -> get_etf(), resolving each
    ranked entry's ETF identity (ticker, name) for display.

    Read-only: no writes, no transaction boundary, no new tables. This is
    a composition/use-case function, not a pure domain function -- it
    takes a live connection and calls repository functions directly.

    Ordering is entirely rank_scores()'s: this function does not re-sort,
    re-rank, or apply any business rule of its own -- it only resolves
    identity for whatever order rank_scores() already produced.

    Returns an empty list if no Score exists yet for this
    (scoring_profile_id, session_date) -- a valid, expected outcome (e.g.
    scoring hasn't run for that day), not an error condition.

    Deterministic: for a fixed database state, the same
    (scoring_profile_id, session_date) always produces the same report in
    the same order, inherited from rank_scores()'s own determinism.

    dimension_scores is resolved via the original Score.score_id --
    rank_scores() deliberately drops it (RankedScore carries no
    persistence identity), so a score_id lookup keyed by etf_id is built
    from `scores` before ranking discards it.

    max_drawdown is resolved only when risk_definition_id is supplied --
    it is a comparison metric entirely independent of scoring: it plays no
    part in `scores`, rank_scores(), or overall_score, and has no bearing
    on ranking order. When omitted (the default), every entry's
    max_drawdown is None -- existing callers are unaffected. When
    supplied, it is resolved per ETF via the already-existing
    get_indicator_values(); an ETF with no MAX_DRAWDOWN IndicatorValue yet
    for this session gets None for that entry specifically, not an error.
    """
    scores = get_scores_for_session(conn, scoring_profile_id, session_date)
    score_id_by_etf = {score.etf_id: score.score_id for score in scores}
    ranked = rank_scores(scores)
    report: list[RankedETFReportEntry] = []
    for ranked_score in ranked:
        etf = get_etf(conn, ranked_score.etf_id)
        dimension_scores = _resolve_dimension_scores(conn, score_id_by_etf[ranked_score.etf_id])
        max_drawdown = _resolve_max_drawdown(conn, risk_definition_id, ranked_score.etf_id, session_date)
        report.append(
            RankedETFReportEntry(
                rank=ranked_score.rank,
                etf_id=ranked_score.etf_id,
                ticker=etf.ticker,
                name=etf.name,
                overall_score=ranked_score.overall_score,
                dimension_scores=dimension_scores,
                max_drawdown=max_drawdown,
            )
        )
    return report


@dataclass(frozen=True, slots=True)
class ETFAnalysisReport:
    """A complete, single-ETF analysis for one (scoring_profile_id,
    session_date) pair.

    Deliberately context-carrying, not a permanent property of the ETF:
    analysis_date and scoring_profile_id are included because the same
    etf_id analysed under a different profile, or on a different session,
    can produce a different report -- a score is only meaningful together
    with the methodology and date that produced it.

    dimension_scores and max_drawdown follow the exact same resolution
    and None-handling as RankedETFReportEntry (see
    generate_ranked_etf_report() for the shared behaviour -- both are
    built on the same underlying helpers).

    rank/peer_count describe this ETF's position among every other ETF
    with a Score for the same (scoring_profile_id, session_date),
    computed via the same rank_scores() the multi-ETF report uses -- not
    a separate ranking rule."""

    etf_id: ETFId
    ticker: str
    name: str
    analysis_date: date
    scoring_profile_id: str
    overall_score: Decimal
    dimension_scores: dict[Dimension, Decimal]
    max_drawdown: Decimal | None
    rank: int
    peer_count: int


def generate_etf_analysis_report(
    conn: sqlite3.Connection,
    etf_id: str,
    scoring_profile_id: str,
    session_date: date,
    risk_definition_id: str | None = None,
) -> ETFAnalysisReport:
    """A complete analysis of exactly one ETF for one (scoring_profile_id,
    session_date) pair: identity, overall_score, the per-dimension
    breakdown behind it, an optional risk metric, and this ETF's position
    among its peers for the same profile/session.

    Read-only, additive: does not modify generate_ranked_etf_report()'s
    behaviour, reuses the same private helpers it uses, and reuses
    get_scores_for_session()/rank_scores() for the peer-ranking context
    rather than introducing a new repository query -- the same data
    get_scores_for_session() already fetches also answers "does this ETF
    have a Score at all" for the required-Score check below.

    Raises MissingScoreError if no Score exists for this
    (etf_id, scoring_profile_id, session_date) -- a Score is the one
    required precondition for a single-ETF analysis; this fails loudly
    rather than returning None or a partial report, the same discipline
    InsufficientPriceHistoryError/MissingIndicatorValueError already use
    elsewhere for a missing required precondition. This is unlike
    max_drawdown, which is optional and resolves to None when absent.
    """
    peer_scores = get_scores_for_session(conn, scoring_profile_id, session_date)
    own_score = next((score for score in peer_scores if score.etf_id == etf_id), None)
    if own_score is None:
        raise MissingScoreError(
            f"No Score for etf_id={etf_id!r}, scoring_profile_id={scoring_profile_id!r}, "
            f"session_date={session_date}"
        )

    etf = get_etf(conn, etf_id)
    dimension_scores = _resolve_dimension_scores(conn, own_score.score_id)
    max_drawdown = _resolve_max_drawdown(conn, risk_definition_id, etf_id, session_date)

    ranked_peers = rank_scores(peer_scores)
    rank = next(ranked.rank for ranked in ranked_peers if ranked.etf_id == etf_id)

    return ETFAnalysisReport(
        etf_id=etf.etf_id,
        ticker=etf.ticker,
        name=etf.name,
        analysis_date=session_date,
        scoring_profile_id=scoring_profile_id,
        overall_score=own_score.overall_score,
        dimension_scores=dimension_scores,
        max_drawdown=max_drawdown,
        rank=rank,
        peer_count=len(ranked_peers),
    )


@dataclass(frozen=True, slots=True)
class ETFScreeningCriteria:
    """Explicit, inspectable screening criteria -- every field maps to a
    metric the system already computes and exposes on RankedETFReportEntry
    (overall_score, dimension_scores, max_drawdown). No weighting, no
    presets: an ETF either satisfies every supplied criterion or it
    doesn't -- criteria are independent AND conditions, never combined
    into a new score. This is not composite scoring.

    All criteria are inclusive floors:
    - min_overall_score: entry.overall_score >= minimum passes.
    - min_dimension_scores: entry.dimension_scores[dimension] >= minimum
      passes, per dimension. A dict, not one field per Dimension member,
      so it generalizes over whatever Dimension currently has (or later
      gains) without requiring a new field per dimension.
    - max_drawdown: entry.max_drawdown >= criteria.max_drawdown passes.
      E.g. criteria.max_drawdown = Decimal("-0.20") allows -0.10, -0.15,
      -0.20, and rejects -0.25 (a worse decline). Requires
      risk_definition_id to be supplied to screen_etfs() -- see
      InvalidScreeningCriteriaError.

    An unset field (None, or an empty dict) applies no constraint at all;
    ETFScreeningCriteria() with every field left at its default matches
    every candidate.
    """

    min_overall_score: Decimal | None = None
    min_dimension_scores: dict[Dimension, Decimal] = field(default_factory=dict)
    max_drawdown: Decimal | None = None


def _satisfies_screening_criteria(
    criteria: ETFScreeningCriteria,
    overall_score: Decimal,
    dimension_scores: dict[Dimension, Decimal],
    max_drawdown: Decimal | None,
) -> bool:
    """Fail-closed: a criterion that references data this candidate
    doesn't have (a missing dimension, an unresolved max_drawdown)
    excludes the candidate -- an unverified criterion is never treated as
    satisfied."""
    if criteria.min_overall_score is not None and overall_score < criteria.min_overall_score:
        return False
    for dimension, minimum in criteria.min_dimension_scores.items():
        if dimension not in dimension_scores or dimension_scores[dimension] < minimum:
            return False
    if criteria.max_drawdown is not None:
        if max_drawdown is None or max_drawdown < criteria.max_drawdown:
            return False
    return True


def screen_etfs(
    conn: sqlite3.Connection,
    scoring_profile_id: str,
    session_date: date,
    candidate_etf_ids: list[str] | None = None,
    criteria: ETFScreeningCriteria | None = None,
    risk_definition_id: str | None = None,
) -> list[RankedETFReportEntry]:
    """Rank the candidates (or every ETF with a Score for this profile
    and session, if candidate_etf_ids is omitted) that satisfy `criteria`,
    ranked locally among just the survivors -- not the full universe.

    screen_etfs(conn, profile_id, date) with every other parameter
    omitted is behaviourally equivalent to
    generate_ranked_etf_report(conn, profile_id, date): no candidate
    restriction, no filtering, same ranking.

    A screening tool, not a recommendation engine: criteria are always
    supplied by the caller. Omitting criteria means "no filtering," never
    "apply built-in default criteria" -- the system never substitutes its
    own opinion of what's interesting.

    candidate_etf_ids restricts the pool before anything else runs. An id
    with no Score for this profile/session (whether never scored, or not
    a real ETF) is simply absent from the result -- not an error.

    Each remaining candidate's dimension_scores/max_drawdown are resolved
    exactly once via the same _resolve_dimension_scores()/
    _resolve_max_drawdown() helpers generate_ranked_etf_report() and
    generate_etf_analysis_report() already use, then reused both for
    filtering and for building the final entry -- no duplicate
    resolution.

    Filtering happens strictly before ranking: rank_scores() is called
    only on the surviving Score objects, so ranks are always local and
    gapless (1..N among survivors) -- never the candidates' rank within
    the full universe. Fail-closed per candidate: a criterion referencing
    data a candidate doesn't have (a missing dimension, an unresolved
    max_drawdown) excludes that candidate rather than passing it
    unverified.

    Raises InvalidScreeningCriteriaError if criteria.max_drawdown is set
    but risk_definition_id is None -- a structurally impossible request
    (no candidate's max_drawdown could ever be resolved to check against
    it), checked before any database work, distinct from the per-ETF
    fail-closed exclusion above.

    Returns an empty list if no candidate satisfies criteria -- a valid,
    expected screening outcome, not an error, same as
    generate_ranked_etf_report()'s empty-result precedent.
    """
    if criteria is not None and criteria.max_drawdown is not None and risk_definition_id is None:
        raise InvalidScreeningCriteriaError(
            "criteria.max_drawdown is set but risk_definition_id is None -- "
            "no candidate's max_drawdown could be resolved to check against it"
        )

    scores = get_scores_for_session(conn, scoring_profile_id, session_date)
    if candidate_etf_ids is not None:
        candidate_ids = set(candidate_etf_ids)
        scores = [score for score in scores if score.etf_id in candidate_ids]

    resolved_by_etf: dict[str, tuple[dict[Dimension, Decimal], Decimal | None]] = {}
    surviving_scores = []
    for score in scores:
        dimension_scores = _resolve_dimension_scores(conn, score.score_id)
        max_drawdown = _resolve_max_drawdown(conn, risk_definition_id, score.etf_id, session_date)
        if criteria is not None and not _satisfies_screening_criteria(
            criteria, score.overall_score, dimension_scores, max_drawdown
        ):
            continue
        resolved_by_etf[score.etf_id] = (dimension_scores, max_drawdown)
        surviving_scores.append(score)

    ranked = rank_scores(surviving_scores)
    report: list[RankedETFReportEntry] = []
    for ranked_score in ranked:
        etf = get_etf(conn, ranked_score.etf_id)
        dimension_scores, max_drawdown = resolved_by_etf[ranked_score.etf_id]
        report.append(
            RankedETFReportEntry(
                rank=ranked_score.rank,
                etf_id=ranked_score.etf_id,
                ticker=etf.ticker,
                name=etf.name,
                overall_score=ranked_score.overall_score,
                dimension_scores=dimension_scores,
                max_drawdown=max_drawdown,
            )
        )
    return report


def get_top_candidates(
    conn: sqlite3.Connection,
    scoring_profile_id: str,
    session_date: date,
    limit: int,
    candidate_etf_ids: list[str] | None = None,
    criteria: ETFScreeningCriteria | None = None,
    risk_definition_id: str | None = None,
) -> list[RankedETFReportEntry]:
    """The first `limit` entries of screen_etfs()'s result, in the exact
    order screen_etfs() already produced -- a bounded-size convenience over
    screening, not a new ranking or scoring method.

    limit is required and has no default: the caller decides how many
    candidates they want to see. The system never substitutes a preferred
    shortlist size (e.g. 10) -- omitting this parameter would mean "apply a
    built-in opinion", which this system never does, the same discipline
    screen_etfs() already applies to criteria.

    All filtering and ranking is exactly screen_etfs()'s: candidate_etf_ids,
    criteria, and risk_definition_id are passed through unchanged, and this
    function performs no additional sorting, re-ranking, or scoring of its
    own. Truncating to the first `limit` entries never changes an entry's
    rank value -- rank still reflects its position among all survivors, not
    its position within the returned shortlist.

    Raises ValueError if limit <= 0 -- a caller configuration error, checked
    before calling screen_etfs() (and therefore before any database work).

    Returns fewer than `limit` entries if fewer candidates survive
    screening -- not an error, and never padded: the same
    fewer-than-expected-is-valid discipline screen_etfs() already applies to
    an empty result.
    """
    if limit <= 0:
        raise ValueError(f"limit must be positive, got {limit}")

    screened = screen_etfs(
        conn,
        scoring_profile_id,
        session_date,
        candidate_etf_ids=candidate_etf_ids,
        criteria=criteria,
        risk_definition_id=risk_definition_id,
    )
    return screened[:limit]


def compare_etfs(
    conn: sqlite3.Connection,
    scoring_profile_id: str,
    session_date: date,
    etf_ids: list[str],
    risk_definition_id: str | None = None,
) -> list[RankedETFReportEntry]:
    """The given etf_ids, ranked locally among just themselves -- a named
    comparison view over screen_etfs(), not a new ranking or scoring
    method. Equivalent to
    screen_etfs(conn, scoring_profile_id, session_date,
    candidate_etf_ids=etf_ids), with no criteria: comparison means "show me
    these specific ETFs," not "filter a pool," so filtering is deliberately
    not exposed here -- a caller wanting a filtered comparison already has
    screen_etfs() directly.

    No length validation: a single etf_id is a valid comparison of one
    (degenerates to rank 1 of 1, the same precedent
    generate_etf_analysis_report() already establishes for a lone ETF), and
    an empty etf_ids list is a valid "compare nothing" request that
    resolves to [] via screen_etfs()'s existing empty-candidate handling --
    neither is a structurally invalid input the way get_top_candidates()'s
    limit <= 0 is, so unlike that function this is pure delegation with no
    guard clause.

    An etf_id with no Score for this (scoring_profile_id, session_date) is
    silently excluded -- the same fail-closed-per-candidate behaviour
    screen_etfs() already applies to candidate_etf_ids, not a new rule.
    This function does not track or report which requested etf_ids were
    dropped; a richer response can be considered later if a real consumer
    needs it.
    """
    return screen_etfs(
        conn,
        scoring_profile_id,
        session_date,
        candidate_etf_ids=etf_ids,
        risk_definition_id=risk_definition_id,
    )
