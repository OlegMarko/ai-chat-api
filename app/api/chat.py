import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.deps import OpenAIDepAnnotated, RedisDepAnnotated
from app.schemas import ChatRequest, ChatResponse, ChatStreamRequest
from app.security.ratelimit import gate_chat_burst
from app.services.llm import generate_response, generate_response_stream

router = APIRouter(tags=["chat"])


def _client_label(request: Request) -> str:
    if request.client is None:
        return "anon"
    return request.client.host


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    body: ChatRequest,
    request: Request,
    redis: RedisDepAnnotated,
    openai_client: OpenAIDepAnnotated,
) -> ChatResponse:
    await gate_chat_burst(redis, _client_label(request))

    reply = await generate_response(
        redis=redis,
        client=openai_client,
        session_id=body.session_id,
        message=body.message,
        rag_mode=False,
    )

    return ChatResponse(response=reply)


@router.post("/chat/stream")
async def chat_stream_endpoint(
    body: ChatStreamRequest,
    request: Request,
    redis: RedisDepAnnotated,
    openai_client: OpenAIDepAnnotated,
) -> StreamingResponse:
    await gate_chat_burst(redis, _client_label(request))

    async def token_iterator() -> AsyncIterator[bytes]:
        async for chunk_text in generate_response_stream(
            redis=redis,
            client=openai_client,
            session_id=body.session_id,
            message=body.message,
            rag_mode=False,
        ):
            payload = json.dumps({"token": chunk_text}, ensure_ascii=False)
            yield f"data: {payload}\n\n".encode("utf-8")

        yield b"data: [DONE]\n\n"

    return StreamingResponse(token_iterator(), media_type="text/event-stream")
