"""Application configuration"""
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "AI will API"
    APP_VERSION: str = "1.3.0"
    DEBUG: bool = True  # Set to False in production

    # API
    API_V1_PREFIX: str = "/v1"

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database (SQLite for development, PostgreSQL for production)
    DATABASE_URL: str = "sqlite:///./aiwill.db"

    # Redis (for rate limiting, caching, idempotency)
    REDIS_URL: str = "redis://localhost:6379/0"

    # External Services
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_TIMEOUT_SECONDS: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
