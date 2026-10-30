"""Process-local runtime for LangGraph PostgreSQL persistence."""

from __future__ import annotations

from urllib.parse import quote_plus

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.agents.memory import AgentMemoryService
from app.agents.middleware import AgentContextPipeline
from app.core.config import settings


class AgentRuntime:
    def __init__(self) -> None:
        self._pool: AsyncConnectionPool | None = None
        self._checkpointer: AsyncPostgresSaver | None = None
        self._store: AsyncPostgresStore | None = None
        self._memory: AgentMemoryService | None = None
        self._graph = None

    @staticmethod
    def _connection_string() -> str:
        return (
            "postgresql://"
            f"{quote_plus(settings.POSTGRES_USER)}:{quote_plus(settings.POSTGRES_PASSWORD)}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{quote_plus(settings.POSTGRES_DB)}"
        )

    async def start(self) -> None:
        if self._graph is not None:
            return
        self._pool = AsyncConnectionPool(
            self._connection_string(),
            min_size=1,
            max_size=settings.AGENT_POSTGRES_POOL_MAX_SIZE,
            open=False,
            kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        )
        await self._pool.open()
        self._checkpointer = AsyncPostgresSaver(self._pool)
        self._store = AsyncPostgresStore(self._pool)
        await self._checkpointer.setup()
        await self._store.setup()

        from app.agents.position_graph import build_position_graph

        memory = AgentMemoryService(self._store if settings.AGENT_MEMORY_ENABLED else None)
        self._memory = memory
        self._graph = build_position_graph(
            memory_service=memory,
            context_pipeline=AgentContextPipeline(memory),
            checkpointer=self._checkpointer,
            store=self._store,
        )

    async def stop(self) -> None:
        if self._pool is not None:
            await self._pool.close()
        self._pool = None
        self._checkpointer = None
        self._store = None
        self._memory = None
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            raise RuntimeError("Agent runtime has not been started")
        return self._graph

    @property
    def memory(self) -> AgentMemoryService:
        if self._memory is None:
            raise RuntimeError("Agent runtime has not been started")
        return self._memory


agent_runtime = AgentRuntime()
