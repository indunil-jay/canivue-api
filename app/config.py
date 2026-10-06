from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App Info
    APP_NAME: str = "Canivue API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"
    DB_ECHO: bool = False

    # Security
    SECRET_KEY: str = "default_dev_secret_key_change_in_production"
    ALLOWED_ORIGINS: List[str] = ["*"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # AI / ML
    # Root directory for versioned trained-model artifacts (see model_registry/README.md).
    # Per-model settings (e.g. <X>_MODEL_BACKEND, <X>_MODEL_WEIGHTS_PATH) belong here too,
    # added alongside each AI feature as it's built -- see .agents/skills/ml-feature/SKILL.md.
    MODEL_REGISTRY_DIR: str = "./model_registry"
    USE_REAL_ML_MODELS: bool = False
    NLP_MODEL_CHECKPOINT: str = "nlp/symptom_distilbert_v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
