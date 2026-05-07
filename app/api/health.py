import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.deps import RedisDepAnnotated
from app.db.database import async_engine

router = APIRouter(prefix="/health", tags=["health"])

logger = logging.getLogger(__name__)


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "live"}


@router.get("/ready")
async def ready(redis: RedisDepAnnotated) -> dict[str, str]:
    try:
        if await redis.ping() is not True:
            raise RuntimeError("unexpected redis ping reply")
    except Exception as exc:
        logger.warning("redis_readiness_failure err=%s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="redis_unavailable") from exc

    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    except Exception as exc:
        logger.warning("postgres_readiness_failure err=%s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="postgres_unavailable") from exc

    return {"status": "ready"}
