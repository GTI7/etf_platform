from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date
from typing import Iterator

from core.market_data.domain.models import IngestionRun, IngestionStatus
from core.market_data.persistence.repository import (
    advance_pipeline_watermark,
    complete_ingestion_run,
    start_ingestion_run,
)
from core.shared.clock import Clock


@contextmanager
def run_pipeline(
    conn: sqlite3.Connection,
    clock: Clock,
    pipeline_name: str,
    pipeline_date: date,
) -> Iterator[str]:
    """Record a pipeline execution attempt.

    The watermark (last_successful_pipeline_date) only advances once the
    block inside the `with` statement completes without raising. A failed
    run is recorded but never advances it, and re-running the same
    pipeline_date is safe to repeat.
    """
    ingestion_run_id = uuid.uuid4().hex
    run = IngestionRun(
        ingestion_run_id=ingestion_run_id,
        pipeline_name=pipeline_name,
        pipeline_date=pipeline_date,
        status=IngestionStatus.RUNNING,
        started_at=clock.now(),
        completed_at=None,
        error_message=None,
    )
    # Committed on its own: a crash during the pipeline body should leave a
    # visible orphaned 'running' row rather than erase the attempt.
    with conn:
        start_ingestion_run(conn, run)
    try:
        yield ingestion_run_id
    except Exception as exc:
        # Single transaction: if this fails partway, the run stays exactly
        # as it was before this block (still 'running'), never half-updated.
        with conn:
            complete_ingestion_run(
                conn, ingestion_run_id, IngestionStatus.FAILED, clock.now(), error_message=str(exc)
            )
        raise
    else:
        completed_at = clock.now()
        # Single transaction: the run can only ever be observed as 'success'
        # together with the watermark having advanced, never one without
        # the other.
        with conn:
            complete_ingestion_run(conn, ingestion_run_id, IngestionStatus.SUCCESS, completed_at)
            advance_pipeline_watermark(conn, pipeline_name, pipeline_date, completed_at)
