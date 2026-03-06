from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    riot_api_key: str = ""
    database_url: str = "postgresql+asyncpg://tft_user:password@localhost:5432/tft_meta"
    redis_url: str = "redis://localhost:6379"
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    slack_webhook_url: str = ""

    cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:3000",
    ]


settings = Settings()
