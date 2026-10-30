"""Privacy-scoped long-term memory backed by LangGraph Postgres Store."""

from __future__ import annotations

import logging
from typing import Any

from app.core.metrics import AGENT_MEMORY_OPERATIONS

logger = logging.getLogger(__name__)


class AgentMemoryService:
    def __init__(self, store: Any | None) -> None:
        self._store = store

    @staticmethod
    def _namespace(user_id: int) -> tuple[str, str]:
        return ("users", str(user_id), "career")

    async def get_profile(self, user_id: int) -> dict[str, Any]:
        if self._store is None:
            return {}
        try:
            item = await self._store.aget(self._namespace(user_id), "profile")
            AGENT_MEMORY_OPERATIONS.labels(operation="get", status="success").inc()
            return dict(item.value) if item else {}
        except Exception as exc:
            AGENT_MEMORY_OPERATIONS.labels(operation="get", status="error").inc()
            logger.warning("Unable to load agent memory: %s", exc)
            return {}

    async def save_match(self, user_id: int, profile: dict[str, Any], positions: list[dict[str, Any]]) -> None:
        if self._store is None:
            return
        value = {
            "experience_level": profile.get("experience_level", ""),
            "primary_stack": list(profile.get("primary_stack", []))[:8],
            "strong_points": list(profile.get("strong_points", []))[:5],
            "weak_points": list(profile.get("weak_points", []))[:5],
            "preferred_positions": [item.get("position_tag", "") for item in positions[:3]],
        }
        try:
            await self._store.aput(self._namespace(user_id), "profile", value, index=False)
            AGENT_MEMORY_OPERATIONS.labels(operation="put", status="success").inc()
        except Exception as exc:
            AGENT_MEMORY_OPERATIONS.labels(operation="put", status="error").inc()
            logger.warning("Unable to save agent memory: %s", exc)

    async def save_interview_report(self, user_id: int, report: dict[str, Any], score: float | None) -> None:
        if self._store is None:
            return
        current = await self.get_profile(user_id)
        current["recent_interview"] = {
            "score": score,
            "strengths": list(report.get("strengths", []))[:5],
            "weaknesses": list(report.get("weaknesses", []))[:5],
        }
        try:
            await self._store.aput(self._namespace(user_id), "profile", current, index=False)
            AGENT_MEMORY_OPERATIONS.labels(operation="report", status="success").inc()
        except Exception as exc:
            AGENT_MEMORY_OPERATIONS.labels(operation="report", status="error").inc()
            logger.warning("Unable to save interview memory: %s", exc)
