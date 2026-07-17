from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from core.analytics.domain.models import Dimension, DimensionScore, Score, ScoringProfile, serialize_parameters
from core.analytics.persistence.repository import (
    get_dimension_scores,
    get_score,
    get_scores_for_etf,
    get_scores_for_session,
    get_scoring_profile,
    insert_dimension_score,
    insert_score,
    insert_scoring_profile,
)
from core.market_data.domain.models import ETF, Calendar
from core.market_data.persistence.repository import insert_calendar, insert_etf

CALENDAR_ID = "XNYS"


def _make_etf(conn: sqlite3.Connection) -> ETF:
    insert_calendar(
        conn,
        Calendar(
            calendar_id=CALENDAR_ID,
            name="New York Stock Exchange",
            exchange="NYSE",
            timezone="America/New_York",
        ),
    )
    etf = ETF(
        etf_id=uuid.uuid4().hex,
        ticker="SPY",
        name="SPDR S&P 500",
        currency="USD",
        calendar_id=CALENDAR_ID,
        created_at=datetime.now(timezone.utc),
    )
    insert_etf(conn, etf)
    return etf


def _make_second_etf(conn: sqlite3.Connection, ticker: str = "QQQ") -> ETF:
    """A second ETF on the already-populated CALENDAR_ID calendar (does not
    re-insert the Calendar row -- use only after _make_etf has already been
    called once in the same test)."""
    etf = ETF(
        etf_id=uuid.uuid4().hex,
        ticker=ticker,
        name="Invesco QQQ",
        currency="USD",
        calendar_id=CALENDAR_ID,
        created_at=datetime.now(timezone.utc),
    )
    insert_etf(conn, etf)
    return etf


def _make_profile(name: str = "REFERENCE", version: int = 1) -> ScoringProfile:
    return ScoringProfile(
        scoring_profile_id=uuid.uuid4().hex,
        name=name,
        version=version,
        parameters=serialize_parameters(
            {"dimensions": {"MOMENTUM": {"indicator_name": "SMA", "indicator_version": 1}}}
        ),
        created_at=datetime.now(timezone.utc),
    )


def test_insert_and_get_scoring_profile(conn: sqlite3.Connection) -> None:
    profile = _make_profile()
    insert_scoring_profile(conn, profile)

    assert get_scoring_profile(conn, "REFERENCE", 1) == profile


def test_get_scoring_profile_returns_none_when_missing(conn: sqlite3.Connection) -> None:
    assert get_scoring_profile(conn, "REFERENCE", 99) is None


def test_scoring_profile_duplicate_rejected(conn: sqlite3.Connection) -> None:
    insert_scoring_profile(conn, _make_profile())

    with pytest.raises(sqlite3.IntegrityError):
        insert_scoring_profile(conn, _make_profile())


def test_scoring_profile_different_version_is_independent(conn: sqlite3.Connection) -> None:
    insert_scoring_profile(conn, _make_profile(version=1))
    insert_scoring_profile(conn, _make_profile(version=2))  # does not raise

    assert get_scoring_profile(conn, "REFERENCE", 1) is not None
    assert get_scoring_profile(conn, "REFERENCE", 2) is not None


def test_score_round_trip_preserves_decimal_precision(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    score = Score(
        score_id=uuid.uuid4().hex,
        etf_id=etf.etf_id,
        scoring_profile_id=profile.scoring_profile_id,
        session_date=date(2026, 7, 14),
        overall_score=Decimal("60.123456789"),
        computed_at=datetime.now(timezone.utc),
    )

    insert_score(conn, score)

    assert get_score(conn, etf.etf_id, profile.scoring_profile_id, date(2026, 7, 14)) == score


def test_get_score_returns_none_when_missing(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)

    assert get_score(conn, etf.etf_id, profile.scoring_profile_id, date(2026, 7, 14)) is None


def test_score_duplicate_insert_is_idempotent(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    session_date = date(2026, 7, 14)

    for _ in range(3):
        insert_score(
            conn,
            Score(
                score_id=uuid.uuid4().hex,
                etf_id=etf.etf_id,
                scoring_profile_id=profile.scoring_profile_id,
                session_date=session_date,
                overall_score=Decimal("60"),
                computed_at=datetime.now(timezone.utc),
            ),
        )

    row = conn.execute(
        "SELECT COUNT(*) AS n FROM Score WHERE etf_id = ? AND scoring_profile_id = ? AND session_date = ?",
        (etf.etf_id, profile.scoring_profile_id, session_date.isoformat()),
    ).fetchone()
    assert row["n"] == 1


def test_score_rejects_update(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    score_id = uuid.uuid4().hex
    insert_score(
        conn,
        Score(
            score_id=score_id,
            etf_id=etf.etf_id,
            scoring_profile_id=profile.scoring_profile_id,
            session_date=date(2026, 7, 14),
            overall_score=Decimal("60"),
            computed_at=datetime.now(timezone.utc),
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE Score SET overall_score = ? WHERE score_id = ?", ("99", score_id))


def test_score_rejects_delete(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    score_id = uuid.uuid4().hex
    insert_score(
        conn,
        Score(
            score_id=score_id,
            etf_id=etf.etf_id,
            scoring_profile_id=profile.scoring_profile_id,
            session_date=date(2026, 7, 14),
            overall_score=Decimal("60"),
            computed_at=datetime.now(timezone.utc),
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM Score WHERE score_id = ?", (score_id,))


def test_dimension_score_round_trip_and_get(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    score = Score(
        score_id=uuid.uuid4().hex,
        etf_id=etf.etf_id,
        scoring_profile_id=profile.scoring_profile_id,
        session_date=date(2026, 7, 14),
        overall_score=Decimal("50"),
        computed_at=datetime.now(timezone.utc),
    )
    insert_score(conn, score)
    momentum = DimensionScore(
        score_id=score.score_id,
        dimension=Dimension.MOMENTUM,
        value=Decimal("70.123456789"),
        computed_at=datetime.now(timezone.utc),
    )
    value_dim = DimensionScore(
        score_id=score.score_id,
        dimension=Dimension.VALUE,
        value=Decimal("30"),
        computed_at=datetime.now(timezone.utc),
    )
    insert_dimension_score(conn, momentum)
    insert_dimension_score(conn, value_dim)

    fetched = get_dimension_scores(conn, score.score_id)

    assert {d.dimension: d for d in fetched} == {
        Dimension.MOMENTUM: momentum,
        Dimension.VALUE: value_dim,
    }


def test_dimension_score_rejects_unknown_dimension(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    score = Score(
        score_id=uuid.uuid4().hex,
        etf_id=etf.etf_id,
        scoring_profile_id=profile.scoring_profile_id,
        session_date=date(2026, 7, 14),
        overall_score=Decimal("50"),
        computed_at=datetime.now(timezone.utc),
    )
    insert_score(conn, score)

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO DimensionScore (score_id, dimension, value, computed_at) VALUES (?, ?, ?, ?)",
            (score.score_id, "NOT_A_REAL_DIMENSION", "1", datetime.now(timezone.utc).isoformat()),
        )


def test_dimension_score_rejects_update(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    score = Score(
        score_id=uuid.uuid4().hex,
        etf_id=etf.etf_id,
        scoring_profile_id=profile.scoring_profile_id,
        session_date=date(2026, 7, 14),
        overall_score=Decimal("50"),
        computed_at=datetime.now(timezone.utc),
    )
    insert_score(conn, score)
    insert_dimension_score(
        conn,
        DimensionScore(
            score_id=score.score_id,
            dimension=Dimension.MOMENTUM,
            value=Decimal("70"),
            computed_at=datetime.now(timezone.utc),
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE DimensionScore SET value = ? WHERE score_id = ? AND dimension = ?",
            ("99", score.score_id, "MOMENTUM"),
        )


def test_dimension_score_rejects_delete(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    score = Score(
        score_id=uuid.uuid4().hex,
        etf_id=etf.etf_id,
        scoring_profile_id=profile.scoring_profile_id,
        session_date=date(2026, 7, 14),
        overall_score=Decimal("50"),
        computed_at=datetime.now(timezone.utc),
    )
    insert_score(conn, score)
    insert_dimension_score(
        conn,
        DimensionScore(
            score_id=score.score_id,
            dimension=Dimension.MOMENTUM,
            value=Decimal("70"),
            computed_at=datetime.now(timezone.utc),
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "DELETE FROM DimensionScore WHERE score_id = ? AND dimension = ?",
            (score.score_id, "MOMENTUM"),
        )


def test_get_scores_for_session_returns_scores_for_requested_profile_and_date(
    conn: sqlite3.Connection,
) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    session_date = date(2026, 7, 14)
    score = Score(
        score_id=uuid.uuid4().hex,
        etf_id=etf.etf_id,
        scoring_profile_id=profile.scoring_profile_id,
        session_date=session_date,
        overall_score=Decimal("70"),
        computed_at=datetime.now(timezone.utc),
    )
    insert_score(conn, score)

    results = get_scores_for_session(conn, profile.scoring_profile_id, session_date)

    assert results == [score]


def test_get_scores_for_session_excludes_other_profiles(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile_a = _make_profile(version=1)
    profile_b = _make_profile(version=2)
    insert_scoring_profile(conn, profile_a)
    insert_scoring_profile(conn, profile_b)
    session_date = date(2026, 7, 14)
    insert_score(
        conn,
        Score(
            score_id=uuid.uuid4().hex,
            etf_id=etf.etf_id,
            scoring_profile_id=profile_a.scoring_profile_id,
            session_date=session_date,
            overall_score=Decimal("70"),
            computed_at=datetime.now(timezone.utc),
        ),
    )
    insert_score(
        conn,
        Score(
            score_id=uuid.uuid4().hex,
            etf_id=etf.etf_id,
            scoring_profile_id=profile_b.scoring_profile_id,
            session_date=session_date,
            overall_score=Decimal("40"),
            computed_at=datetime.now(timezone.utc),
        ),
    )

    results = get_scores_for_session(conn, profile_a.scoring_profile_id, session_date)

    assert [r.scoring_profile_id for r in results] == [profile_a.scoring_profile_id]


def test_get_scores_for_session_excludes_other_dates(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    insert_score(
        conn,
        Score(
            score_id=uuid.uuid4().hex,
            etf_id=etf.etf_id,
            scoring_profile_id=profile.scoring_profile_id,
            session_date=date(2026, 7, 13),
            overall_score=Decimal("70"),
            computed_at=datetime.now(timezone.utc),
        ),
    )
    insert_score(
        conn,
        Score(
            score_id=uuid.uuid4().hex,
            etf_id=etf.etf_id,
            scoring_profile_id=profile.scoring_profile_id,
            session_date=date(2026, 7, 14),
            overall_score=Decimal("40"),
            computed_at=datetime.now(timezone.utc),
        ),
    )

    results = get_scores_for_session(conn, profile.scoring_profile_id, date(2026, 7, 14))

    assert [r.session_date for r in results] == [date(2026, 7, 14)]


def test_get_scores_for_session_supports_multiple_etfs(conn: sqlite3.Connection) -> None:
    etf_a = _make_etf(conn)
    etf_b = _make_second_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    session_date = date(2026, 7, 14)
    insert_score(
        conn,
        Score(
            score_id=uuid.uuid4().hex,
            etf_id=etf_a.etf_id,
            scoring_profile_id=profile.scoring_profile_id,
            session_date=session_date,
            overall_score=Decimal("70"),
            computed_at=datetime.now(timezone.utc),
        ),
    )
    insert_score(
        conn,
        Score(
            score_id=uuid.uuid4().hex,
            etf_id=etf_b.etf_id,
            scoring_profile_id=profile.scoring_profile_id,
            session_date=session_date,
            overall_score=Decimal("40"),
            computed_at=datetime.now(timezone.utc),
        ),
    )

    results = get_scores_for_session(conn, profile.scoring_profile_id, session_date)

    assert {r.etf_id for r in results} == {etf_a.etf_id, etf_b.etf_id}


def test_get_scores_for_etf_returns_multiple_historical_sessions(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    for session_date, overall_score in [
        (date(2026, 7, 13), Decimal("70")),
        (date(2026, 7, 14), Decimal("75")),
        (date(2026, 7, 15), Decimal("80")),
    ]:
        insert_score(
            conn,
            Score(
                score_id=uuid.uuid4().hex,
                etf_id=etf.etf_id,
                scoring_profile_id=profile.scoring_profile_id,
                session_date=session_date,
                overall_score=overall_score,
                computed_at=datetime.now(timezone.utc),
            ),
        )

    results = get_scores_for_etf(conn, etf.etf_id, profile.scoring_profile_id)

    assert len(results) == 3


def test_get_scores_for_etf_ordered_by_session_date(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    # Inserted deliberately out of date order, to prove the result's order
    # comes from the query's ORDER BY, not insertion order.
    for session_date in [date(2026, 7, 15), date(2026, 7, 13), date(2026, 7, 14)]:
        insert_score(
            conn,
            Score(
                score_id=uuid.uuid4().hex,
                etf_id=etf.etf_id,
                scoring_profile_id=profile.scoring_profile_id,
                session_date=session_date,
                overall_score=Decimal("70"),
                computed_at=datetime.now(timezone.utc),
            ),
        )

    results = get_scores_for_etf(conn, etf.etf_id, profile.scoring_profile_id)

    assert [r.session_date for r in results] == [
        date(2026, 7, 13),
        date(2026, 7, 14),
        date(2026, 7, 15),
    ]


def test_get_scores_for_etf_filters_by_start_date(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    for session_date in [date(2026, 7, 13), date(2026, 7, 14), date(2026, 7, 15)]:
        insert_score(
            conn,
            Score(
                score_id=uuid.uuid4().hex,
                etf_id=etf.etf_id,
                scoring_profile_id=profile.scoring_profile_id,
                session_date=session_date,
                overall_score=Decimal("70"),
                computed_at=datetime.now(timezone.utc),
            ),
        )

    results = get_scores_for_etf(
        conn, etf.etf_id, profile.scoring_profile_id, start_date=date(2026, 7, 14)
    )

    assert [r.session_date for r in results] == [date(2026, 7, 14), date(2026, 7, 15)]


def test_get_scores_for_etf_filters_by_end_date(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    for session_date in [date(2026, 7, 13), date(2026, 7, 14), date(2026, 7, 15)]:
        insert_score(
            conn,
            Score(
                score_id=uuid.uuid4().hex,
                etf_id=etf.etf_id,
                scoring_profile_id=profile.scoring_profile_id,
                session_date=session_date,
                overall_score=Decimal("70"),
                computed_at=datetime.now(timezone.utc),
            ),
        )

    results = get_scores_for_etf(
        conn, etf.etf_id, profile.scoring_profile_id, end_date=date(2026, 7, 14)
    )

    assert [r.session_date for r in results] == [date(2026, 7, 13), date(2026, 7, 14)]


def test_get_scores_for_etf_isolates_by_etf(conn: sqlite3.Connection) -> None:
    etf_a = _make_etf(conn)
    etf_b = _make_second_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    session_date = date(2026, 7, 14)
    insert_score(
        conn,
        Score(
            score_id=uuid.uuid4().hex,
            etf_id=etf_a.etf_id,
            scoring_profile_id=profile.scoring_profile_id,
            session_date=session_date,
            overall_score=Decimal("70"),
            computed_at=datetime.now(timezone.utc),
        ),
    )
    insert_score(
        conn,
        Score(
            score_id=uuid.uuid4().hex,
            etf_id=etf_b.etf_id,
            scoring_profile_id=profile.scoring_profile_id,
            session_date=session_date,
            overall_score=Decimal("40"),
            computed_at=datetime.now(timezone.utc),
        ),
    )

    results = get_scores_for_etf(conn, etf_a.etf_id, profile.scoring_profile_id)

    assert [r.etf_id for r in results] == [etf_a.etf_id]


def test_get_scores_for_etf_isolates_by_scoring_profile(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile_a = _make_profile(version=1)
    profile_b = _make_profile(version=2)
    insert_scoring_profile(conn, profile_a)
    insert_scoring_profile(conn, profile_b)
    session_date = date(2026, 7, 14)
    insert_score(
        conn,
        Score(
            score_id=uuid.uuid4().hex,
            etf_id=etf.etf_id,
            scoring_profile_id=profile_a.scoring_profile_id,
            session_date=session_date,
            overall_score=Decimal("70"),
            computed_at=datetime.now(timezone.utc),
        ),
    )
    insert_score(
        conn,
        Score(
            score_id=uuid.uuid4().hex,
            etf_id=etf.etf_id,
            scoring_profile_id=profile_b.scoring_profile_id,
            session_date=session_date,
            overall_score=Decimal("40"),
            computed_at=datetime.now(timezone.utc),
        ),
    )

    results = get_scores_for_etf(conn, etf.etf_id, profile_a.scoring_profile_id)

    assert [r.scoring_profile_id for r in results] == [profile_a.scoring_profile_id]


def test_get_scores_for_etf_returns_empty_list_when_no_history(conn: sqlite3.Connection) -> None:
    etf = _make_etf(conn)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)

    results = get_scores_for_etf(conn, etf.etf_id, profile.scoring_profile_id)

    assert results == []
