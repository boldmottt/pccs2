from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "PCCS2"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pccs2"

    # API
    API_URL: str = "http://localhost:8000"
    SECRET_KEY: str = "dev-secret-key-not-for-production"

    # ML
    ML_MODEL_PATH: str = "models/"
    CLOUD_TRAINING_ENABLED: bool = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
