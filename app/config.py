"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings loaded from .env file or environment variables."""

    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "adaptive_testing"
    GEMINI_API_KEY: str = "[ENCRYPTION_KEY]"
    QUESTIONS_PER_TEST: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
