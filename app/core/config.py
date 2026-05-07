from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str

    model_name: str = "gpt-4.1-mini"
    max_tokens: int = 50
    timeout: int = 10
    retries: int = 3
    delay: float = 0.1

    price_per_1k_tokens: float = 0.0005

    app_env: str = "local"
    log_level: str = "INFO"

    redis_url: str = "redis://localhost:6379/0"
    history_ttl: int = 3600
    history_max_len: int = 20

    database_url: str = "postgresql://postgres:postgres@localhost:5432/rag_db"

    class Config:
        env_file = ".env"


settings = Settings()
