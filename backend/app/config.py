from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "PCCS2"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pccs2"

    # API
    API_URL: str = "http://localhost:8000"
    SECRET_KEY: str = "dev-secret-key-not-for-production"
    CORS_ORIGINS: str = "http://localhost:3000"

    # ML
    ML_MODEL_PATH: str = "models/"
    CLOUD_TRAINING_ENABLED: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
