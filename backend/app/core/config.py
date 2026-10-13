import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Campus Safety & Response Grid (SCS-RG)"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "scs-rg-super-secret-jwt-key-for-robo-fusion-competition"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite+aiosqlite:///./scs_rg.db"
    SYNC_DATABASE_URL: str = "sqlite:///./scs_rg.db"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Feature Flags
    BONUS_TREND_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
