from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.agents.memory import AgentMemoryService
from app.agents.middleware import AgentContextPipeline
from app.agents.position_graph import build_position_graph
from app.schemas.ai import CareerAdviceResult, RerankItem, RerankResult
from app.schemas.client.position_agent import PositionMatchRequest
from app.services.common.advanced_rag import AdvancedRAGService


class FakeStore:
    def __init__(self):
        self.values = {}

    async def aget(self, namespace, key):
        value = self.values.get((namespace, key))
        return type("Item", (), {"value": value})() if value is not None else None

    async def aput(self, namespace, key, value, **kwargs):
        self.values[(namespace, key)] = value


@pytest.mark.unit
@pytest.mark.asyncio
async def test_long_term_memory_is_scoped_to_each_user():
    memory = AgentMemoryService(FakeStore())
    await memory.save_match(10, {"primary_stack": ["Python"]}, [{"position_tag": "python_backend"}])

    assert (await memory.get_profile(10))["preferred_positions"] == ["python_backend"]
    assert await memory.get_profile(11) == {}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_position_graph_merges_parallel_scouts():
    async def resume_data(_):
        return {"parsed_resume": {"skills": ["Python"]}}

    async def profile_data(_):
        return {"primary_stack": ["Python"], "position_hints": ["python_backend", "ai_application"]}

    async def scout_data(payload):
        category = (payload.get("categories") or ["backend"])[0]
        tag = "python_backend" if category == "backend" else "ai_application"
        return {"recommended_positions": [{"position_tag": tag, "title": tag, "match_score": 0.8}]}

    async def focus_data(_):
        return {"focus_topics": ["FastAPI"]}

    async def advice_data(*args, **kwargs):
        return CareerAdviceResult(next_actions=["完成专项练习", "复盘项目", "模拟面试"])

    memory = AgentMemoryService(FakeStore())
    graph = build_position_graph(
        memory_service=memory,
        context_pipeline=AgentContextPipeline(memory),
        checkpointer=MemorySaver(),
        store=None,
        operations={
            "get_resume": resume_data,
            "build_profile": profile_data,
            "match_positions": scout_data,
            "get_focus": focus_data,
            "career_advice": advice_data,
        },
    )
    state = await graph.ainvoke(
        {"user_id": 1, "resume_id": 1, "scout_results": [], "completed_steps": [], "errors": []},
        config={"configurable": {"thread_id": "test-run"}},
    )

    assert [item["position_tag"] for item in state["result"]["recommended_positions"]] == [
        "python_backend",
        "ai_application",
    ]
    assert "memory_writer" in state["completed_steps"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rerank_keeps_unknown_or_missing_ids_in_rrf_order(monkeypatch):
    async def rerank_data(*args, **kwargs):
        return RerankResult(items=[RerankItem(id=2, score=9), RerankItem(id=999, score=10)])

    monkeypatch.setattr("app.services.common.advanced_rag.AIService._chat_json", rerank_data)
    result = await AdvancedRAGService._rerank(
        "Python async",
        [{"id": 1, "question": "A"}, {"id": 2, "question": "B"}, {"id": 3, "question": "C"}],
        3,
    )

    assert [item["id"] for item in result] == [2, 1, 3]
    assert result[0]["rerank_score"] == 9


@pytest.mark.unit
def test_position_match_request_accepts_optional_run_id():
    request = PositionMatchRequest(resume_id=1, run_id="1d09c330-4037-45e7-8a32-16561a3c9df1")
    assert str(request.run_id) == "1d09c330-4037-45e7-8a32-16561a3c9df1"
