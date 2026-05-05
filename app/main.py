import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import chat_router
from app.core import LLMServiceError, settings
from app.core.logging import setup_logging

setup_logging(settings.log_level)

logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(chat_router)


@app.exception_handler(LLMServiceError)
async def llm_exception_handler(request: Request, exc: LLMServiceError):
    logger.exception(f"LLM error on {request.url.path}")

    return JSONResponse(
        status_code=500,
        content={"detail": "AI service temporarily unavailable"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url.path}")

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
