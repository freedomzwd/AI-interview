"""Approved upstream integrations for live jobs and programming problems.

The module intentionally calls documented/public board endpoints only. It does
not scrape consumer recruitment sites or bypass authentication controls.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import bleach
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.external_sync_run import ExternalSyncRun
from app.models.job_posting import JobPosting
from app.models.question_bank import QuestionBank
from app.services.common.embedding import embed_texts

logger = logging.getLogger(__name__)


def _as_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _plain_text(value: str | None, limit: int = 6000) -> str:
    return " ".join(bleach.clean(value or "", tags=[], strip=True).split())[:limit]


def _difficulty(rating: int | None) -> str:
    if rating is None or rating <= 1300:
        return "easy"
    if rating <= 1900:
        return "medium"
    return "hard"


def _problem_embedding_text(question: str, tags: list[str]) -> str:
    """Keep the title and official problem tags searchable by the RAG retriever."""
    return f"{question}\n\n算法标签：{'、'.join(tags)}"


class ExternalDataService:
    @staticmethod
    async def _start_run(db: AsyncSession, provider: str, resource: str, details: dict[str, Any]) -> ExternalSyncRun:
        run = ExternalSyncRun(provider=provider, resource=resource, details=details)
        db.add(run)
        await db.commit()
        await db.refresh(run)
        return run

    @staticmethod
    async def _finish_run(
        db: AsyncSession,
        run: ExternalSyncRun,
        *,
        received: int = 0,
        created: int = 0,
        updated: int = 0,
        error: str | None = None,
    ) -> None:
        run.status = "failed" if error else "completed"
        run.received_count = received
        run.created_count = created
        run.updated_count = updated
        run.error_message = error[:1000] if error else None
        run.finished_at = datetime.now(UTC)
        await db.commit()

    @staticmethod
    async def sync_codeforces(db: AsyncSession, tag: str = "dp", limit: int | None = None) -> dict[str, int]:
        """Import a bounded, attributed set of real Codeforces problems."""
        if not settings.EXTERNAL_SYNC_ENABLED:
            raise RuntimeError("外部数据同步已禁用")
        limit = min(limit or settings.CODEFORCES_IMPORT_LIMIT, 100)
        run = await ExternalDataService._start_run(db, "codeforces", "problems", {"tag": tag, "limit": limit})
        try:
            async with httpx.AsyncClient(timeout=settings.EXTERNAL_SYNC_TIMEOUT_SECONDS) as client:
                response = await client.get("https://codeforces.com/api/problemset.problems")
                response.raise_for_status()
                payload = response.json()
            if payload.get("status") != "OK":
                raise RuntimeError("Codeforces API returned a non-OK response")

            candidates = [
                item for item in payload.get("result", {}).get("problems", [])
                if item.get("contestId") and item.get("index") and tag.lower() in [value.lower() for value in item.get("tags", [])]
            ]
            candidates.sort(key=lambda item: (item.get("rating") is None, item.get("rating", 0), item["contestId"], item["index"]))
            candidates = candidates[:limit]
            created = updated = 0
            rows_to_embed: list[QuestionBank] = []
            for item in candidates:
                external_id = f"{item['contestId']}{item['index']}"
                row = (await db.execute(select(QuestionBank).where(
                    QuestionBank.source == "codeforces", QuestionBank.external_id == external_id
                ))).scalar_one_or_none()
                values = {
                    "category": "technical",
                    "position_tag": "algorithm",
                    "difficulty": _difficulty(item.get("rating")),
                    "question": f"Codeforces {external_id}: {item['name']}",
                    "reference_answer": None,
                    "key_points": item.get("tags", []),
                    "tags": ["codeforces", *item.get("tags", [])],
                    "source": "codeforces",
                    "external_id": external_id,
                    "source_url": f"https://codeforces.com/problemset/problem/{item['contestId']}/{item['index']}",
                }
                if row:
                    for field, value in values.items():
                        setattr(row, field, value)
                    updated += 1
                else:
                    row = QuestionBank(**values)
                    db.add(row)
                    created += 1
                rows_to_embed.append(row)

            # Do not mark an imported problem as ready until it participates in
            # semantic/hybrid retrieval. Existing source rows are also rebuilt.
            embedding_texts = [
                _problem_embedding_text(row.question, row.tags or [])
                for row in rows_to_embed
            ]
            embeddings = await embed_texts(embedding_texts)
            for row, embedding_text, embedding in zip(rows_to_embed, embedding_texts, embeddings):
                row.embedding_text = embedding_text
                row.embedding = embedding
            await db.commit()
            await ExternalDataService._finish_run(db, run, received=len(candidates), created=created, updated=updated)
            return {"received": len(candidates), "created": created, "updated": updated, "embedded": len(rows_to_embed)}
        except Exception as exc:
            await db.rollback()
            await ExternalDataService._finish_run(db, run, error=str(exc))
            logger.exception("Codeforces synchronization failed")
            raise

    @staticmethod
    async def _upsert_job(db: AsyncSession, values: dict[str, Any]) -> tuple[bool, bool]:
        row = (await db.execute(select(JobPosting).where(
            JobPosting.provider == values["provider"], JobPosting.external_id == values["external_id"]
        ))).scalar_one_or_none()
        if row:
            for field, value in values.items():
                setattr(row, field, value)
            return False, True
        db.add(JobPosting(**values))
        return True, False

    @staticmethod
    async def _sync_remotive(db: AsyncSession) -> dict[str, int]:
        run = await ExternalDataService._start_run(db, "remotive", "jobs", {"category": "software-dev"})
        try:
            async with httpx.AsyncClient(timeout=settings.EXTERNAL_SYNC_TIMEOUT_SECONDS) as client:
                response = await client.get("https://remotive.com/api/remote-jobs", params={"category": "software-dev"})
                response.raise_for_status()
                jobs = response.json().get("jobs", [])[: settings.EXTERNAL_JOB_SYNC_LIMIT]
            created = updated = 0
            now = datetime.now(UTC)
            for job in jobs:
                is_created, is_updated = await ExternalDataService._upsert_job(db, {
                    "provider": "remotive",
                    "external_id": str(job["id"]),
                    "company": job.get("company_name") or "Unknown company",
                    "title": job.get("title") or "Untitled position",
                    "location": job.get("candidate_required_location") or "Remote",
                    "employment_type": job.get("job_type"),
                    "work_type": "remote",
                    "description": _plain_text(job.get("description")),
                    "tags": job.get("tags", []),
                    "apply_url": job.get("url"),
                    "source_url": job.get("url"),
                    "published_at": _as_datetime(job.get("publication_date")),
                    "last_seen_at": now,
                    "raw_payload": {"id": job.get("id"), "url": job.get("url"), "category": job.get("category")},
                    "is_active": True,
                })
                created += int(is_created)
                updated += int(is_updated)
            await db.commit()
            await ExternalDataService._finish_run(db, run, received=len(jobs), created=created, updated=updated)
            return {"received": len(jobs), "created": created, "updated": updated}
        except Exception as exc:
            await ExternalDataService._finish_run(db, run, error=str(exc))
            logger.exception("Remotive synchronization failed")
            raise

    @staticmethod
    async def _sync_greenhouse_board(db: AsyncSession, board: str) -> dict[str, int]:
        run = await ExternalDataService._start_run(db, "greenhouse", "jobs", {"board": board})
        try:
            async with httpx.AsyncClient(timeout=settings.EXTERNAL_SYNC_TIMEOUT_SECONDS) as client:
                response = await client.get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", params={"content": "true"})
                response.raise_for_status()
                jobs = response.json().get("jobs", [])[: settings.EXTERNAL_JOB_SYNC_LIMIT]
            created = updated = 0
            now = datetime.now(UTC)
            for job in jobs:
                is_created, is_updated = await ExternalDataService._upsert_job(db, {
                    "provider": "greenhouse",
                    "external_id": f"{board}:{job['id']}",
                    "company": board,
                    "title": job.get("title") or "Untitled position",
                    "location": (job.get("location") or {}).get("name"),
                    "employment_type": None,
                    "work_type": None,
                    "description": _plain_text(job.get("content")),
                    "tags": [item.get("name") for item in job.get("departments", []) if item.get("name")],
                    "apply_url": job.get("absolute_url"),
                    "source_url": job.get("absolute_url"),
                    "published_at": _as_datetime(job.get("updated_at")),
                    "last_seen_at": now,
                    "raw_payload": {"id": job.get("id"), "board": board, "updated_at": job.get("updated_at")},
                    "is_active": True,
                })
                created += int(is_created)
                updated += int(is_updated)
            await db.commit()
            await ExternalDataService._finish_run(db, run, received=len(jobs), created=created, updated=updated)
            return {"received": len(jobs), "created": created, "updated": updated}
        except Exception as exc:
            await ExternalDataService._finish_run(db, run, error=str(exc))
            logger.exception("Greenhouse synchronization failed for board %s", board)
            raise

    @staticmethod
    async def sync_jobs(db: AsyncSession, providers: list[str] | None = None) -> dict[str, dict[str, int]]:
        """Synchronize supported job sources; Greenhouse boards are allowlisted by config."""
        if not settings.EXTERNAL_SYNC_ENABLED:
            raise RuntimeError("外部数据同步已禁用")
        requested = set(providers or ["remotive", "greenhouse"])
        result: dict[str, dict[str, int]] = {}
        if "remotive" in requested:
            result["remotive"] = await ExternalDataService._sync_remotive(db)
        if "greenhouse" in requested:
            boards = [item.strip() for item in settings.JOB_GREENHOUSE_BOARDS.split(",") if item.strip()]
            for board in boards:
                result[f"greenhouse:{board}"] = await ExternalDataService._sync_greenhouse_board(db, board)
        return result
