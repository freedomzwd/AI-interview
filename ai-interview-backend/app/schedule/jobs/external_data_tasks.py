"""Celery tasks for approved external job and problem sources."""

import asyncio

from app.core.celery_app import celery_app
from app.db.base import create_scheduler_engine, create_scheduler_session_factory
from app.services.common.external_data import ExternalDataService


async def _sync_jobs(providers: list[str] | None) -> dict:
    engine = create_scheduler_engine()
    session_factory = create_scheduler_session_factory(engine)
    try:
        async with session_factory() as db:
            return await ExternalDataService.sync_jobs(db, providers)
    finally:
        await engine.dispose()


async def _sync_codeforces(tag: str, limit: int | None) -> dict:
    engine = create_scheduler_engine()
    session_factory = create_scheduler_session_factory(engine)
    try:
        async with session_factory() as db:
            return await ExternalDataService.sync_codeforces(db, tag, limit)
    finally:
        await engine.dispose()


@celery_app.task(bind=True, max_retries=2, time_limit=600)
def sync_external_jobs_task(self, providers: list[str] | None = None) -> dict:
    try:
        return asyncio.run(_sync_jobs(providers))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1)) from exc


@celery_app.task(bind=True, max_retries=2, time_limit=600)
def sync_codeforces_problems_task(self, tag: str = "dp", limit: int | None = None) -> dict:
    try:
        return asyncio.run(_sync_codeforces(tag, limit))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1)) from exc
