import uuid
from collections.abc import Awaitable, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.context import request_id_var


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming = request.headers.get("x-request-id") or str(uuid.uuid4())
        correlation_reset_token_identifier = request_id_var.set(incoming)

        try:
            response = await call_next(request)
            response.headers.setdefault("x-request-id", incoming)
            return response
        finally:
            request_id_var.reset(correlation_reset_token_identifier)
