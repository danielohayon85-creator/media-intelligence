from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://media:media@localhost:5432/media_intelligence"
    ai_provider: str = "mock"  # mock | anthropic
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5-5"
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
