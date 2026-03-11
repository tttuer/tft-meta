from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    riot_api_key: str = ""
    database_url: str = "postgresql+asyncpg://tft_user:password@localhost:5432/tft_meta"
    redis_url: str = "redis://localhost:6379"
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    slack_webhook_url: str = ""

    # GitHub Copilot API (설정 시 OpenRouter 대신 사용)
    github_token: str = ""  # GitHub Personal Access Token (Copilot 구독 필요)
    github_copilot_model: str = "gpt-4o-mini"  # 쿼터 차감 없는 모델

    cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:53000",
        "http://127.0.0.1",
    ]
    cors_allow_all: bool = False  # 개발 편의용, True면 모든 origin 허용


settings = Settings()
