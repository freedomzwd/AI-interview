"""Initialize LangGraph Postgres checkpoint and store tables idempotently."""

import asyncio

from app.agents.runtime import agent_runtime


async def main() -> None:
    await agent_runtime.start()
    await agent_runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())
