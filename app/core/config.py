from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    llm_api_key: str
    llm_base_url: str = "http://ollama:11434/v1"

    chat_model_name: str = "gpt-4.1-mini"
    rag_model_name: str | None = Field(
        default=None,
        description="If set, RAG completions use this model; otherwise chat_model_name.",
    )

    embedding_model_name: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    tiktoken_budget_model_override: str | None = Field(
        default=None,
        description="Fallback encoding model name when tiktoken lacks direct coverage.",
    )
    chat_history_system_margin_tokens: int = 128
    chat_history_reply_reserve_tokens: int = 4096
    chat_history_prompt_token_budget: int = 4000

    chat_max_completion_tokens: int = 1024
    rag_max_completion_tokens: int = 1024

    openai_chat_timeout_seconds: float = 60.0
    openai_embedding_timeout_seconds: float = 30.0
    openai_max_retries: int = 3
    openai_retry_min_wait_seconds: float = 0.5
    openai_retry_max_wait_seconds: float = 30.0

    price_per_1k_prompt_tokens_usd: float = 0.00015
    price_per_1k_completion_tokens_usd: float = 0.0006

    app_env: str = "local"
    log_level: str = "INFO"
    log_json: bool = Field(
        default=True,
        description="Emit JSON-shaped lines when True (recommended for centralized logging).",
    )

    redis_url: str = "redis://localhost:6379/0"
    redis_pool_max_connections: int = 50

    history_ttl_seconds: int = Field(3600, validation_alias="history_ttl")
    history_max_messages: int = Field(20, validation_alias="history_max_len")
    history_message_byte_cap: int = 50_000

    database_url: str = "postgresql://postgres:postgres@localhost:5432/rag_db"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    retrieval_ann_limit: int = 100
    retrieval_rerank_top_k: int = 24
    rag_context_max_chunks: int = 12
    rag_context_max_tokens: int = 3000
    rag_max_per_source: int = 3

    hnsw_ef_search: int = 80

    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    cors_origins_raw: str = Field(default="", alias="cors_origins")

    api_rate_limit_chat_per_minute: int = 120
    api_rate_limit_rag_per_minute: int = 60

    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins_raw.strip():
            return []
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    def effective_rag_chat_model(self) -> str:
        return self.rag_model_name or self.chat_model_name


settings = Settings()
