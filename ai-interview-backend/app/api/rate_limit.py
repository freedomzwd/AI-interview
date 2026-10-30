"""Redis-backed request throttling dependencies."""

import logging
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.services.common.redis import redis_client

logger = logging.getLogger(__name__)


def rate_limit(name: str, *, limit: int, window_seconds: int) -> Callable:
    """Create a FastAPI dependency for a fixed-window endpoint limit."""

    async def dependency(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        client_host = request.client.host if request.client else "unknown"
        key = f"rate-limit:{name}:{client_host}"
        try:
            allowed = await redis_client.allow_rate_limit(
                key,
                limit=limit,
                window_seconds=window_seconds,
            )
        except Exception as exc:
            logger.warning("Redis 限流不可用: %s", exc)
            if settings.RATE_LIMIT_FAIL_OPEN:
                return
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="请求保护服务暂不可用",
            ) from exc

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试",
                headers={"Retry-After": str(window_seconds)},
            )

    return dependency
