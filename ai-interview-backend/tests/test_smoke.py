import httpx
import pytest

from app.route.route import create_app
from app.schemas.ai import AnswerEvaluation
from app.services.client.ai_service import AIService
from app.services.common.rag import normalize_retrieval_scores, reciprocal_rank_fusion


@pytest.mark.unit
def test_extract_json_accepts_markdown_wrapped_output():
    payload = AIService._extract_json(
        '说明文字\n```json\n{"score": 8.5, "feedback": "回答清晰"}\n```'
    )
    result = AnswerEvaluation.model_validate(payload)
    assert result.score == 8.5
    assert result.feedback == "回答清晰"


@pytest.mark.unit
def test_rrf_merges_duplicate_results_and_preserves_payload():
    result = reciprocal_rank_fusion(
        [
            [{"id": 1, "question": "A"}, {"id": 2, "question": "B"}],
            [{"id": 2, "question": "B keyword"}, {"id": 3, "question": "C"}],
        ],
        k=60,
    )
    assert [item["id"] for item in result] == [2, 1, 3]
    assert result[0]["question"] == "B"
    assert result[0]["retrieval_score"] > result[1]["retrieval_score"]


@pytest.mark.unit
def test_normalized_retrieval_scores_preserve_order_and_scale_to_one():
    result = normalize_retrieval_scores(
        [{"id": 1, "keyword_score": 0.2}, {"id": 2, "keyword_score": 0.1}],
        score_key="keyword_score",
    )
    assert [item["similarity"] for item in result] == [1.0, 0.5]


@pytest.mark.smoke
def test_create_app_registers_metrics_endpoint():
    app = create_app()
    paths = {route.path for route in app.routes}
    assert "/metrics" in paths
    assert any(path.endswith("/config/health") for path in paths)


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_payload():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/")
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert "ai_interview_api_requests_total" in response.text


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limit_dependency_fail_open_when_redis_is_down(monkeypatch):
    from app.api.rate_limit import rate_limit
    from app.core.config import settings
    from app.services.common.redis import redis_client

    async def failing_allow(*args, **kwargs):
        raise ConnectionError("redis unavailable")

    monkeypatch.setattr(redis_client, "allow_rate_limit", failing_allow)
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_FAIL_OPEN", True)

    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "client": ("127.0.0.1", 1234),
        "scheme": "http",
        "server": ("test", 80),
        "query_string": b"",
    }
    await rate_limit("test", limit=1, window_seconds=60)(Request(scope))
