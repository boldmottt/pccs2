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
    # 로컬 단독 실행이 별도 설정 없이 바로 되도록 기본값은 SQLite다.
    # 운영(PostgreSQL)·CI·docker-compose는 DATABASE_URL 환경변수로 명시 설정한다.
    DATABASE_URL: str = "sqlite+aiosqlite:///./pccs2.db"

    # API
    API_URL: str = "http://localhost:8000"
    SECRET_KEY: str = "dev-secret-key-not-for-production"
    CORS_ORIGINS: str = "http://localhost:3000"

    # 로컬 rdp.db 자동 가져오기 경로 (비우면 기본 경로 시도)
    RDP_DB_PATH: str = ""

    # ML
    ML_MODEL_PATH: str = "models/"
    CLOUD_TRAINING_ENABLED: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
