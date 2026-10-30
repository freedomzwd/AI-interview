"""Small context pipeline for graph nodes on the LangChain 0.3 stack."""

from __future__ import annotations

from typing import Any


class AgentContextPipeline:
    def __init__(self, memory_service: Any) -> None:
        self._memory_service = memory_service

    async def load(self, user_id: int) -> dict[str, Any]:
        return await self._memory_service.get_profile(user_id)

    @staticmethod
    def prompt_context(memory: dict[str, Any], target_direction: str | None) -> str:
        parts = []
        if target_direction:
            parts.append(f"用户意向方向：{target_direction}")
        if memory.get("preferred_positions"):
            parts.append(f"历史岗位偏好：{', '.join(memory['preferred_positions'][:3])}")
        if memory.get("recent_interview", {}).get("weaknesses"):
            parts.append("近期待提升项：" + "；".join(memory["recent_interview"]["weaknesses"][:3]))
        return "\n".join(parts)
