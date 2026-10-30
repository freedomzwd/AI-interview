"""Authenticated listing of externally synchronized, attributed job postings."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.client.deps import get_current_user
from app.db.session import get_db
from app.models.job_posting import JobPosting
from app.models.user import User
from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("")
async def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    provider: str | None = Query(None),
    search: str | None = Query(None, max_length=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(JobPosting).where(JobPosting.is_active.is_(True))
    if provider:
        stmt = stmt.where(JobPosting.provider == provider)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(or_(JobPosting.title.ilike(pattern), JobPosting.company.ilike(pattern), JobPosting.location.ilike(pattern)))
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (await db.execute(
        stmt.order_by(JobPosting.published_at.desc().nullslast(), JobPosting.id.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )).scalars().all()
    return ApiResponse.success({
        "items": [
            {
                "id": row.id, "provider": row.provider, "company": row.company, "title": row.title,
                "location": row.location, "employment_type": row.employment_type, "work_type": row.work_type,
                "description": row.description, "tags": row.tags or [], "apply_url": row.apply_url,
                "source_url": row.source_url, "published_at": row.published_at.isoformat() if row.published_at else None,
                "last_seen_at": row.last_seen_at.isoformat(),
            }
            for row in rows
        ],
        "total": total, "page": page, "per_page": per_page,
    })
