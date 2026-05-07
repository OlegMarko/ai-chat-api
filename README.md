# Working with Python and LLMs

This project demonstrates how to build a Python API around Large Language Models
using FastAPI, Redis-backed conversation history, OpenAI chat completions,
embeddings, pgvector retrieval, and a small evaluation workflow.

## What this project shows

- Async Python service design with FastAPI.
- Configuration with Pydantic settings and environment variables.
- LLM chat responses through the OpenAI Python SDK.
- Streaming responses over server-sent events.
- Redis session history for multi-turn conversations.
- Token-aware history trimming before sending prompts to the model.
- Retrieval-augmented generation with embeddings and pgvector.
- Rate limiting, structured logging, request IDs, retries, and tests.

## Main Python pieces

| Area | Files | Purpose |
| --- | --- | --- |
| API entrypoint | `app/main.py` | Creates the FastAPI app, middleware, routers, and shared clients. |
| Chat endpoints | `app/api/chat.py` | Handles `/chat` and `/chat/stream`. |
| RAG endpoints | `app/api/rag.py` | Handles document ingestion and retrieval-backed answers. |
| LLM calls | `app/services/llm.py` | Builds messages, calls the model, tracks usage, and stores replies. |
| History | `app/services/history.py`, `app/services/history_builder.py` | Stores conversation turns and trims context to a token budget. |
| Retrieval | `app/services/retrieval.py`, `app/services/rag.py` | Finds relevant chunks and builds grounded prompts. |
| Embeddings | `app/services/embeddings.py` | Creates vectors for document chunks and queries. |
| Database | `app/db/*`, `app/repositories/vector_repository.py` | Stores chunks and vectors with PostgreSQL + pgvector. |
| Tests | `tests/` | Validates API behavior, history trimming, metrics, rate limits, and retry logic. |

## Requirements

- Python 3.12+
- Docker and Docker Compose
- An OpenAI API key
- `uv` or another Python package manager

Create a local `.env` file:

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://ollama:11434/v1
LLM_API_KEY=ollama
CHAT_MODEL_NAME=llama3.1:8b
EMBEDDING_MODEL_NAME=llama3.1:8b
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_db
REDIS_URL=redis://localhost:6379/0
```

## Install dependencies

Using `uv`:

```bash
uv sync --extra dev
```

Or with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the services

Start Postgres, Redis, and the API:

```bash
docker compose up -d --build
```

The API runs at:

```text
http://localhost:8000
```

Check health:

```bash
curl http://localhost:8000/health/live
```

## Basic LLM chat

Send a non-streaming chat request:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-session",
    "message": "Explain async Python in two short paragraphs."
  }'
```

What happens in Python:

1. `app/api/chat.py` receives the HTTP request.
2. `app/services/llm.py` loads previous session history from Redis.
3. `app/services/history_builder.py` trims the history to fit the prompt budget.
4. The OpenAI async client sends messages to the configured chat model.
5. The assistant reply is stored back in Redis and returned as JSON.

## Streaming LLM chat

Send a streaming chat request:

```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-stream",
    "message": "Give me five tips for writing reliable Python services."
  }'
```

The API emits server-sent events like:

```text
data: {"token": "Use"}
data: {"token": "typed"}
data: {"token": "configuration"}
data: [DONE]
```

This demonstrates how Python async iterators can bridge an LLM token stream into
an HTTP streaming response.

## Retrieval-augmented generation

First, ingest source text:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "source": "python-notes",
        "text": "FastAPI supports async request handlers. Async handlers are useful when waiting on network IO such as databases, Redis, and LLM APIs."
      },
      {
        "source": "llm-notes",
        "text": "RAG improves answer grounding by retrieving relevant chunks and placing them into the model context before generation."
      }
    ]
  }'
```

Then ask a grounded question:

```bash
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-rag",
    "question": "How do async Python and RAG help this service?"
  }'
```

RAG flow:

1. Documents are split into chunks.
2. Chunks are embedded with the configured embedding model.
3. Vectors are stored in PostgreSQL using pgvector.
4. A user question is embedded.
5. Similar chunks are retrieved and reranked.
6. The final prompt includes the retrieved context.
7. The LLM answers with more grounding than a plain chat request.

## Working directly with the LLM service

The core LLM call lives in `app/services/llm.py`:

```python
response = await client.chat.completions.create(
    model=model_to_use,
    messages=chat_messages,
    max_tokens=max_completion_tokens,
    timeout=settings.openai_chat_timeout_seconds,
    temperature=0.2 if rag_mode else 0.7,
)
```

Key ideas:

- `messages` contains a system message, trimmed history, and the latest user message.
- `temperature` is lower in RAG mode for more focused answers.
- `max_tokens` caps completion size.
- Retry behavior is centralized in `app/services/retry_policies.py`.
- Usage logging estimates request cost from prompt and completion tokens.

## Run tests

```bash
pytest
```

Useful focused test runs:

```bash
pytest tests/test_history_builder.py
pytest tests/test_retry_policies.py
pytest tests/test_api_validation.py
```

## Evaluation workflow

The `evaluation/` package contains a simple framework for testing answer quality
against a dataset:

```bash
python -m evaluation.report
```

Use this when changing prompts, chunking, retrieval limits, reranking, or model
settings so you can compare behavior before and after the change.

## Practical LLM development habits

- Keep prompts explicit and short enough to leave room for retrieved context.
- Trim chat history by tokens, not by message count alone.
- Use lower temperature for fact-grounded RAG answers.
- Log model name, token usage, latency, and failure types.
- Retry transient provider errors, but surface persistent failures clearly.
- Test validation, rate limits, empty responses, and streaming edge cases.
- Evaluate prompt and retrieval changes with a repeatable dataset.

## Suggested experiments

1. Change `CHAT_MODEL_NAME` and compare answer quality and cost.
2. Lower `CHAT_HISTORY_PROMPT_TOKEN_BUDGET` and observe history trimming.
3. Add more documents through `/ingest` and inspect RAG answer grounding.
4. Tune `RAG_CONTEXT_MAX_CHUNKS` and `RAG_CONTEXT_MAX_TOKENS`.
5. Add a new metric in `evaluation/metrics.py`.

This is a compact but realistic pattern for working with LLMs in Python: keep
the application async, make model calls observable, store conversation state
outside the process, ground answers with retrieval when needed, and protect the
API with validation, rate limits, retries, and tests.
