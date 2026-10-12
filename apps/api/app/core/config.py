from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "OVERCLOCK API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://overclock:overclock_dev_password@localhost:5432/overclock"
    )
    DATABASE_ADMIN_URL: str | None = None

    # Security & Tokens
    SECRET_KEY: str = "development-secret-key-at-least-32-chars-long-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # S3 / MinIO Storage
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_PUBLIC_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "overclock-documents"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False

    # AI Provider & Models
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    MODEL_EXTRACT_PRIMARY: str = "gpt-4o-mini"
    MODEL_EXTRACT_ESCALATION: str = "gpt-4o"
    MODEL_EXPLAIN: str = "gpt-4o-mini"

    # AI Budget Guards
    DEFAULT_MONTHLY_AI_BUDGET_INR: float = 500.00
    GLOBAL_DAILY_AI_CAP_INR: float = 50.00

    # Standards
    TIMEZONE: str = "Asia/Kolkata"
    DEFAULT_CURRENCY: str = "INR"
    DATE_FORMAT: str = "DD-MM-YYYY"


@lru_cache
def get_settings() -> Settings:
    return Settings()
