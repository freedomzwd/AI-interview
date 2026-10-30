import logging
import time
from sqlalchemy import select, delete, update, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.metrics import RAG_LATENCY, RAG_REQUESTS
from app.models.question_bank import QuestionBank
from app.services.common.embedding import embed_text, embed_texts
from app.services.common.rag import normalize_retrieval_scores, reciprocal_rank_fusion

logger = logging.getLogger(__name__)


def _build_embedding_text(question: str, reference_answer: str | None) -> str:
    """构造用于向量化的文本：题面 + 参考答案"""
    parts = [question.strip()]
    if reference_answer and reference_answer.strip():
        parts.append(f"参考答案：{reference_answer.strip()}")
    return "\n\n".join(parts)


class QuestionBankService:

    # ── CRUD ────────────────────────────────────────────────────────────

    @staticmethod
    async def create(db: AsyncSession, data: dict) -> QuestionBank:
        """新增题目，保存后自动向量化"""
        emb_text = _build_embedding_text(data["question"], data.get("reference_answer"))
        embedding = await embed_text(emb_text)

        q = QuestionBank(
            category=data["category"],
            position_tag=data["position_tag"],
            difficulty=data["difficulty"],
            question=data["question"],
            reference_answer=data.get("reference_answer"),
            key_points=data.get("key_points"),
            tags=data.get("tags"),
            source=data.get("source", "manual"),
            created_by=data.get("created_by"),
            embedding=embedding,
            embedding_text=emb_text,
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        logger.info(f"题目 {q.id} 已创建并向量化")
        return q

    @staticmethod
    async def get_by_id(db: AsyncSession, question_id: int) -> QuestionBank | None:
        """按主键获取单道题目，不存在时返回 None。"""
        return await db.get(QuestionBank, question_id)

    @staticmethod
    async def update(db: AsyncSession, question_id: int, data: dict) -> QuestionBank | None:
        """更新题目，若修改了题面或答案则重新向量化"""
        q = await db.get(QuestionBank, question_id)
        if not q:
            return None

        need_reembed = False
        for field in ("question", "reference_answer"):
            if field in data and data[field] != getattr(q, field):
                need_reembed = True

        for field, val in data.items():
            if hasattr(q, field):
                setattr(q, field, val)

        if need_reembed:
            emb_text = _build_embedding_text(q.question, q.reference_answer)
            q.embedding = await embed_text(emb_text)
            q.embedding_text = emb_text

        await db.commit()
        await db.refresh(q)
        return q

    @staticmethod
    async def delete(db: AsyncSession, question_id: int) -> bool:
        """删除单道题目，返回是否删除成功。"""
        result = await db.execute(
            delete(QuestionBank).where(QuestionBank.id == question_id)
        )
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def toggle(db: AsyncSession, question_id: int, is_active: bool) -> bool:
        """启用或禁用题目，返回是否更新成功。"""
        result = await db.execute(
            update(QuestionBank)
            .where(QuestionBank.id == question_id)
            .values(is_active=is_active)
        )
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def get_list(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        category: str | None = None,
        position_tag: str | None = None,
        difficulty: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> dict:
        """按条件分页查询题库列表，供后台管理页展示和筛选。"""
        stmt = select(QuestionBank)
        if category:
            stmt = stmt.where(QuestionBank.category == category)
        if position_tag:
            stmt = stmt.where(QuestionBank.position_tag.contains(position_tag))
        if difficulty:
            stmt = stmt.where(QuestionBank.difficulty == difficulty)
        if is_active is not None:
            stmt = stmt.where(QuestionBank.is_active == is_active)
        if search:
            stmt = stmt.where(
                or_(
                    QuestionBank.question.ilike(f"%{search}%"),
                    QuestionBank.reference_answer.ilike(f"%{search}%"),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(QuestionBank.created_at.desc()).offset((page - 1) * size).limit(size)
        items = (await db.execute(stmt)).scalars().all()
        return {"items": items, "total": total, "page": page, "size": size}

    # ── 向量化 ──────────────────────────────────────────────────────────

    @staticmethod
    async def embed_question(db: AsyncSession, question_id: int) -> bool:
        """单题重新向量化"""
        q = await db.get(QuestionBank, question_id)
        if not q:
            return False
        emb_text = _build_embedding_text(q.question, q.reference_answer)
        q.embedding = await embed_text(emb_text)
        q.embedding_text = emb_text
        await db.commit()
        return True

    @staticmethod
    def batch_embed_sync(question_ids: list[int]) -> dict:
        """
        同步批量向量化（供 Celery 任务调用）。
        因 Celery 无事件循环，这里直接操作数据库。
        """
        import asyncio
        from app.db.base import get_session_local

        async def _run():
            """在独立会话中批量生成 embedding 并回写数据库。"""
            async with get_session_local()() as db:
                stmt = select(QuestionBank).where(QuestionBank.id.in_(question_ids))
                rows = (await db.execute(stmt)).scalars().all()

                texts = [_build_embedding_text(q.question, q.reference_answer) for q in rows]
                embeddings = await embed_texts(texts)  # async batch

                for q, emb, txt in zip(rows, embeddings, texts):
                    q.embedding = emb
                    q.embedding_text = txt

                await db.commit()
                return len(rows)

        count = asyncio.run(_run())
        logger.info(f"批量向量化完成：{count} 题")
        return {"embedded": count}

    @staticmethod
    def reindex_all_sync() -> dict:
        """全量重建 embedding（升级模型时使用）"""
        import asyncio
        from app.db.base import get_session_local

        async def _run():
            """遍历全量题目 ID，并按批次调用批量向量化逻辑。"""
            async with get_session_local()() as db:
                stmt = select(QuestionBank)
                rows = (await db.execute(stmt)).scalars().all()
                ids = [q.id for q in rows]

            # 分批处理
            batch_size = 50
            total = 0
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i: i + batch_size]
                result = QuestionBankService.batch_embed_sync(batch_ids)
                total += result["embedded"]
            return total

        total = asyncio.run(_run())
        return {"total_reindexed": total}

    # ── 检索 ─────────────────────────────────────────────────────────────

    @staticmethod
    async def retrieve_questions(
        query: str,
        db: AsyncSession,
        k: int = 20,
        position_tag: str | None = None,
        difficulty: str | None = None,
        min_score: float = 0.7,
        search_mode: str | None = None,
    ) -> list[dict]:
        """
        混合检索：pgvector 语义召回 + PostgreSQL FTS 关键词召回。
        ``search_mode`` 支持 semantic、keyword、hybrid、advanced，默认读取配置。
        """
        mode = (search_mode or settings.RAG_SEARCH_MODE).lower()
        if mode not in {"semantic", "keyword", "hybrid", "advanced"}:
            mode = "hybrid"
        started = time.perf_counter()
        try:
            if mode == "advanced":
                from app.services.common.advanced_rag import AdvancedRAGService

                return await AdvancedRAGService.retrieve_questions(
                    query=query,
                    k=k,
                    position_tag=position_tag,
                    difficulty=difficulty,
                    min_score=min_score,
                )
            semantic = []
            keyword = []
            if mode in {"semantic", "hybrid"}:
                semantic = await QuestionBankService._semantic_search(
                    query, db, k, position_tag, difficulty, min_score
                )
            if mode in {"keyword", "hybrid"}:
                keyword = await QuestionBankService._keyword_search(
                    query, db, k, position_tag, difficulty
                )
            if mode == "semantic":
                results = semantic
            elif mode == "keyword":
                results = keyword
            else:
                results = reciprocal_rank_fusion(
                    [semantic, keyword],
                    k=settings.RAG_RRF_K,
                )[:k]
                normalize_retrieval_scores(results, score_key="retrieval_score")
                for item in results:
                    item["retrieval_mode"] = "hybrid"
            return results
        finally:
            RAG_REQUESTS.labels(retriever="question_bank", mode=mode).inc()
            RAG_LATENCY.labels(retriever="question_bank", mode=mode).observe(
                time.perf_counter() - started
            )

    @staticmethod
    async def _semantic_search(
        query: str,
        db: AsyncSession,
        k: int,
        position_tag: str | None,
        difficulty: str | None,
        min_score: float,
    ) -> list[dict]:
        query_vec = await embed_text(query)
        distance = QuestionBank.embedding.cosine_distance(query_vec)
        stmt = (
            select(
                QuestionBank.id,
                QuestionBank.category,
                QuestionBank.position_tag,
                QuestionBank.difficulty,
                QuestionBank.question,
                QuestionBank.reference_answer,
                QuestionBank.key_points,
                distance.label("distance"),
            )
            .where(
                QuestionBank.is_active.is_(True),
                QuestionBank.embedding.is_not(None),
                distance <= 1.0 - min_score,
            )
            .order_by(distance)
            .limit(k)
        )
        if position_tag:
            stmt = stmt.where(QuestionBank.position_tag.contains(position_tag))
        if difficulty:
            stmt = stmt.where(QuestionBank.difficulty == difficulty)

        rows = (await db.execute(stmt)).mappings().all()
        results = [
            {
                "id": row["id"],
                "category": row["category"],
                "position_tag": row["position_tag"],
                "difficulty": row["difficulty"],
                "question": row["question"],
                "reference_answer": row["reference_answer"],
                "key_points": row["key_points"],
                "similarity": round(1.0 - float(row["distance"]), 4),
                "source": "from_bank",
                "retrieval_mode": "semantic",
            }
            for row in rows
        ]
        return results

    @staticmethod
    async def _keyword_search(
        query: str,
        db: AsyncSession,
        k: int,
        position_tag: str | None,
        difficulty: str | None,
    ) -> list[dict]:
        document = func.to_tsvector(
            "simple",
            func.concat(
                func.coalesce(QuestionBank.question, ""),
                " ",
                func.coalesce(QuestionBank.reference_answer, ""),
            ),
        )
        query_vector = func.websearch_to_tsquery("simple", query)
        rank = func.ts_rank_cd(document, query_vector)
        stmt = (
            select(
                QuestionBank.id,
                QuestionBank.category,
                QuestionBank.position_tag,
                QuestionBank.difficulty,
                QuestionBank.question,
                QuestionBank.reference_answer,
                QuestionBank.key_points,
                rank.label("keyword_score"),
            )
            .where(
                QuestionBank.is_active.is_(True),
                document.op("@@")(query_vector),
            )
            .order_by(rank.desc())
            .limit(k)
        )
        if position_tag:
            stmt = stmt.where(QuestionBank.position_tag.contains(position_tag))
        if difficulty:
            stmt = stmt.where(QuestionBank.difficulty == difficulty)

        rows = (await db.execute(stmt)).mappings().all()
        results = [
            {
                "id": row["id"],
                "category": row["category"],
                "position_tag": row["position_tag"],
                "difficulty": row["difficulty"],
                "question": row["question"],
                "reference_answer": row["reference_answer"],
                "key_points": row["key_points"],
                "similarity": 0.0,
                "source": "from_bank",
                "retrieval_mode": "keyword",
                "keyword_score": round(float(row["keyword_score"]), 6),
            }
            for row in rows
        ]
        return normalize_retrieval_scores(results, score_key="keyword_score")

    @staticmethod
    async def increment_use_count(db: AsyncSession, question_ids: list[int]) -> None:
        """面试选题后增加使用次数"""
        if not question_ids:
            return
        await db.execute(
            update(QuestionBank)
            .where(QuestionBank.id.in_(question_ids))
            .values(use_count=QuestionBank.use_count + 1)
        )
        await db.commit()

    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        """题库统计：按分类、难度的分布 + 使用率排行"""
        by_category = (
            await db.execute(
                select(QuestionBank.category, func.count().label("cnt"))
                .group_by(QuestionBank.category)
            )
        ).all()

        by_difficulty = (
            await db.execute(
                select(QuestionBank.difficulty, func.count().label("cnt"))
                .group_by(QuestionBank.difficulty)
            )
        ).all()

        top_used = (
            await db.execute(
                select(QuestionBank.id, QuestionBank.question, QuestionBank.use_count)
                .order_by(QuestionBank.use_count.desc())
                .limit(10)
            )
        ).all()

        total = (await db.execute(select(func.count()).select_from(QuestionBank))).scalar_one()
        embedded = (
            await db.execute(
                select(func.count()).select_from(QuestionBank).where(QuestionBank.embedding.is_not(None))
            )
        ).scalar_one()

        return {
            "total": total,
            "embedded": embedded,
            "by_category": {row[0]: row[1] for row in by_category},
            "by_difficulty": {row[0]: row[1] for row in by_difficulty},
            "top_used": [{"id": r[0], "question": r[1][:50], "use_count": r[2]} for r in top_used],
        }
