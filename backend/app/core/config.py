import os
from typing import ClassVar

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


def _normalize_database_url(url: str) -> str:
    """
    Render/Heroku-style managed Postgres URLs use the 'postgres://' scheme,
    but SQLAlchemy with psycopg2 requires 'postgresql://'.
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Settings:
    """
    Configuration class to load environment variables.
    """

    DATABASE_URL: str = _normalize_database_url(os.getenv("DATABASE_URL", ""))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_ENABLED: bool = os.getenv("WEBHOOK_ENABLED", "false").lower() == "true"
    ALLOWED_ORIGINS: ClassVar[list[str]] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200"
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
