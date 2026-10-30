"""Advanced RAG pipeline with safe fallbacks over existing hybrid retrieval."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.core.metrics import RAG_ADVANCED_OPERATIONS
from app.db.base import get_session_local
from app.schemas.ai import RAGQueryPlan, RerankResult
from app.services.client.ai_service import AIService
from app.services.common.rag import normalize_retrieval_scores, reciprocal_rank_fusion

logger = logging.getLogger(__name__)


class AdvancedRAGService:
    @staticmethod
    async def _plan(query: str) -> RAGQueryPlan:
        fallback = RAGQueryPlan(queries=[query], hypothetical_answer=query)
        if not settings.RAG_ADVANCED_ENABLED:
            return fallback
        plan = await AIService._chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是检索查询优化器。只返回 JSON："
                        "{\"queries\":[\"...\"],\"hypothetical_answer\":\"...\"}。"
                        "queries 只保留与原问题语义不同的 2 条中文检索式。"
                    ),
                },
                {"role": "user", "content": query},
            ],
            RAGQueryPlan,
            fallback.model_dump(),
            temperature=0.1,
        )
        unique = []
        for item in [query, *plan.queries[: settings.RAG_MULTI_QUERY_COUNT], plan.hypothetical_answer]:
            normalized = str(item).strip()
            if normalized and normalized not in unique:
                unique.append(normalized)
        RAG_ADVANCED_OPERATIONS.labels(operation="query_plan", status="success").inc()
        return RAGQueryPlan(queries=unique, hypothetical_answer=plan.hypothetical_answer)

    @staticmethod
    async def _rerank(query: str, candidates: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
        if not settings.RAG_RERANK_ENABLED or not candidates:
            return candidates[:k]
        payload = [
            {"id": item["id"], "text": item.get("question") or item.get("content", "")[:700]}
            for item in candidates[: settings.RAG_ADVANCED_CANDIDATE_K]
        ]
        fallback = RerankResult(items=[])
        ranked = await AIService._chat_json(
            [
                {
                    "role": "system",
                    "content": "只返回 JSON：{\"items\":[{\"id\":1,\"score\":9.2}]}。按与查询相关度降序排列，不能返回未知 id。",
                },
                {"role": "user", "content": f"查询：{query}\n候选：{json.dumps(payload, ensure_ascii=False)}"},
            ],
            RerankResult,
            fallback.model_dump(),
            temperature=0.0,
        )
        by_id = {item["id"]: item for item in candidates}
        ordered = []
        seen = set()
        for item in ranked.items:
            if item.id in by_id and item.id not in seen:
                value = dict(by_id[item.id])
                value["rerank_score"] = item.score
                ordered.append(value)
                seen.add(item.id)
        for item in candidates:
            if item["id"] not in seen:
                ordered.append(item)
        RAG_ADVANCED_OPERATIONS.labels(operation="rerank", status="success").inc()
        return ordered[:k]

    @classmethod
    async def retrieve_questions(
        cls,
        *,
        query: str,
        k: int,
        position_tag: str | None,
        difficulty: str | None,
        min_score: float,
    ) -> list[dict[str, Any]]:
        from app.services.backoffice.question_bank_service import QuestionBankService

        plan = await cls._plan(query)

        async def retrieve_one(item: str) -> list[dict[str, Any]]:
            async with get_session_local()() as session:
                return await QuestionBankService.retrieve_questions(
                    query=item,
                    db=session,
                    k=settings.RAG_ADVANCED_CANDIDATE_K,
                    position_tag=position_tag,
                    difficulty=difficulty,
                    min_score=min_score,
                    search_mode="hybrid",
                )

        try:
            results = await asyncio.gather(*(retrieve_one(item) for item in plan.queries))
            fused = reciprocal_rank_fusion(results, k=settings.RAG_RRF_K)
            normalize_retrieval_scores(fused, score_key="retrieval_score")
            for item in fused:
                item["retrieval_mode"] = "advanced"
            RAG_ADVANCED_OPERATIONS.labels(operation="retrieve_questions", status="success").inc()
            return await cls._rerank(query, fused, k)
        except Exception as exc:
            logger.warning("Advanced question retrieval failed; using hybrid: %s", exc)
            RAG_ADVANCED_OPERATIONS.labels(operation="retrieve_questions", status="fallback").inc()
            async with get_session_local()() as session:
                return await QuestionBankService.retrieve_questions(
                    query=query,
                    db=session,
                    k=k,
                    position_tag=position_tag,
                    difficulty=difficulty,
                    min_score=min_score,
                    search_mode="hybrid",
                )

    @classmethod
    async def retrieve_knowledge(
        cls,
        *,
        query: str,
        k: int,
        category: str | None,
        min_score: float,
        parent_session,
    ) -> list[dict[str, Any]]:
        from app.models.knowledge import KnowledgeChunk
        from app.services.backoffice.knowledge_service import KnowledgeService

        plan = await cls._plan(query)

        async def retrieve_one(item: str) -> list[dict[str, Any]]:
            async with get_session_local()() as session:
                return await KnowledgeService.retrieve_chunks(
                    query=item,
                    db=session,
                    k=settings.RAG_ADVANCED_CANDIDATE_K,
                    category=category,
                    min_score=min_score,
                    search_mode="hybrid",
                )

        try:
            results = await asyncio.gather(*(retrieve_one(item) for item in plan.queries))
            fused = reciprocal_rank_fusion(results, k=settings.RAG_RRF_K)
            normalize_retrieval_scores(fused, score_key="retrieval_score")
            reranked = await cls._rerank(query, fused, k)
            ids = [item["id"] for item in reranked]
            if not ids:
                return []
            rows = (
                await parent_session.execute(
                    select(KnowledgeChunk.id, KnowledgeChunk.document_id, KnowledgeChunk.chunk_index)
                    .where(KnowledgeChunk.id.in_(ids))
                )
            ).mappings().all()
            metadata = {row["id"]: row for row in rows}
            for item in reranked:
                row = metadata.get(item["id"])
                if not row:
                    continue
                adjacent = (
                    await parent_session.execute(
                        select(KnowledgeChunk.content)
                        .where(
                            KnowledgeChunk.document_id == row["document_id"],
                            KnowledgeChunk.chunk_index.between(
                                max(0, row["chunk_index"] - settings.RAG_PARENT_CONTEXT_WINDOW),
                                row["chunk_index"] + settings.RAG_PARENT_CONTEXT_WINDOW,
                            ),
                        )
                        .order_by(KnowledgeChunk.chunk_index)
                    )
                ).scalars().all()
                item["parent_context"] = "\n".join(adjacent)
                item["retrieval_mode"] = "advanced"
            RAG_ADVANCED_OPERATIONS.labels(operation="retrieve_knowledge", status="success").inc()
            return reranked
        except Exception as exc:
            logger.warning("Advanced knowledge retrieval failed; using hybrid: %s", exc)
            RAG_ADVANCED_OPERATIONS.labels(operation="retrieve_knowledge", status="fallback").inc()
            return await KnowledgeService.retrieve_chunks(
                query=query,
                db=parent_session,
                k=k,
                category=category,
                min_score=min_score,
                search_mode="hybrid",
            )
