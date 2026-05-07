import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.rag import router as rag_router
from app.core.config import settings
from app.core.exceptions import LLMServiceError
from app.core.logging import setup_logging
from app.db.database import async_engine
from app.infrastructure.openai_clients import create_shared_llm_client
from app.infrastructure.redis_pool import create_connection_pool, disconnect_pool
from app.middleware.request_context import RequestCorrelationMiddleware

setup_logging(settings.log_level, json_logs=settings.log_json)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.redis_pool = create_connection_pool()
    app.state.shared_openai = create_shared_llm_client()

    try:
        yield
    finally:
        await disconnect_pool(app.state.redis_pool)
        await async_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        title="AI Chat + RAG API",
        version="0.2.0",
    )

    app.add_middleware(RequestCorrelationMiddleware)

    if settings.cors_origin_list():
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list(),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(LLMServiceError)
    async def llm_error(_request: Request, exc: LLMServiceError) -> JSONResponse:
        logger.exception("LLM operation failed", exc_info=exc)

        return JSONResponse(
            status_code=503,
            content={"detail": "ai_backend_unavailable"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_error(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)

        return JSONResponse(
            status_code=500, content={"detail": "internal_server_error"}
        )

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(rag_router)

    return app


app = create_app()
