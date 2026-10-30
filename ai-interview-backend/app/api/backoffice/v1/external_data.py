"""Admin controls and audit history for approved external data sources."""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.backoffice.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.models.external_sync_run import ExternalSyncRun
from app.schemas.response import ApiResponse
from app.schedule.jobs.external_data_tasks import sync_codeforces_problems_task, sync_external_jobs_task

router = APIRouter()


@router.post("/jobs/sync")
async def sync_jobs(
    providers: list[Literal["remotive", "greenhouse"]] | None = None,
    current_admin: Admin = Depends(get_current_admin),
):
    """Queue synchronization from public, approved job-board APIs."""
    task = sync_external_jobs_task.delay(providers)
    return ApiResponse.success({"task_id": task.id}, message="职位同步任务已提交")


@router.post("/codeforces/sync")
async def sync_codeforces(
    tag: str = Query("dp", min_length=1, max_length=50),
    limit: int = Query(30, ge=1, le=100),
    current_admin: Admin = Depends(get_current_admin),
):
    """Queue a bounded import from the Codeforces public API."""
    task = sync_codeforces_problems_task.delay(tag, limit)
    return ApiResponse.success({"task_id": task.id}, message="算法题同步任务已提交")


@router.get("/runs")
async def list_sync_runs(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    rows = (await db.execute(
        select(ExternalSyncRun).order_by(ExternalSyncRun.started_at.desc()).limit(limit)
    )).scalars().all()
    return ApiResponse.success({"items": [
        {
            "id": row.id, "provider": row.provider, "resource": row.resource, "status": row.status,
            "received_count": row.received_count, "created_count": row.created_count,
            "updated_count": row.updated_count, "error_message": row.error_message,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        }
        for row in rows
    ]})
