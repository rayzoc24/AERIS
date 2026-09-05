"""AERIS backend configuration.

Loads environment variables and validates that every required variable
is present at startup. The application refuses to boot if a critical
variable is missing.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---------------------------------------------------------
    APP_NAME: str = "AERIS"
    APP_ENV: str = Field(default="development")
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False)
    API_V1_PREFIX: str = "/api/v1"
    PUBLIC_BASE_URL: str = Field(default="http://localhost:5173")
    BACKEND_BASE_URL: str = Field(default="http://localhost:8000")

    # --- Security ------------------------------------------------------------
    SECRET_KEY: str = Field(default="")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    # Stored as a comma-separated string in the env, parsed to list below.
    CORS_ALLOWED_ORIGINS_STR: str = Field(default="", validation_alias="CORS_ALLOWED_ORIGINS")
    CSRF_SECRET: str = Field(default="")
    COOKIE_DOMAIN: str = Field(default="localhost")
    SECURE_COOKIES: bool = Field(default=False)

    # --- Database ------------------------------------------------------------
    MONGO_URI: str = Field(default="")
    MONGO_DB_NAME: str = Field(default="aeris")

    # --- External APIs -------------------------------------------------------
    MAPPLS_API_KEY: str = Field(default="")
    MAPPLS_CLIENT_ID: str = Field(default="")
    MAPPLS_CLIENT_SECRET: str = Field(default="")
    FIREBASE_CREDENTIALS_PATH: str = Field(default="")
    FCM_SERVER_KEY: str = Field(default="")

    # --- Rate limiting -------------------------------------------------------
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_REPORTS: str = "20/minute"

    # --- File uploads --------------------------------------------------------
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_UPLOAD_MIMES_STR: str = Field(
        default="image/jpeg,image/png,image/webp",
        validation_alias="ALLOWED_UPLOAD_MIMES",
    )

    # --- Documentation -------------------------------------------------------
    ENABLE_SWAGGER: bool = Field(default=True)

    @property
    def CORS_ALLOWED_ORIGINS(self) -> List[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS_STR.split(",") if o.strip()]

    @property
    def ALLOWED_UPLOAD_MIMES(self) -> List[str]:
        return [m.strip() for m in self.ALLOWED_UPLOAD_MIMES_STR.split(",") if m.strip()]


REQUIRED_FOR_PROD = [
    "SECRET_KEY",
    "CSRF_SECRET",
    "MONGO_URI",
    "MAPPLS_API_KEY",
    "CORS_ALLOWED_ORIGINS",
]

REQUIRED_FOR_DEV = [
    "SECRET_KEY",
    "MONGO_URI",
]


def _validate_required(settings: Settings) -> List[str]:
    missing: List[str] = []
    required = REQUIRED_FOR_PROD if settings.APP_ENV == "production" else REQUIRED_FOR_DEV
    for key in required:
        value = getattr(settings, key)
        if isinstance(value, list) and not value:
            missing.append(key)
        elif isinstance(value, str) and not value:
            missing.append(key)
    return missing


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    missing = _validate_required(settings)
    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill in the values."
        )
    if settings.APP_ENV == "production":
        if settings.DEBUG:
            raise RuntimeError("DEBUG must be False in production.")
        if settings.ENABLE_SWAGGER:
            raise RuntimeError("ENABLE_SWAGGER must be False in production.")
        if not settings.SECURE_COOKIES:
            raise RuntimeError("SECURE_COOKIES must be True in production.")
    return settings
