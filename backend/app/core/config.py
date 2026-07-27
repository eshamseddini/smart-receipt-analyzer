import os

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Settings:
    """
    Configuration class to load environment variables.
    """
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_ENABLED: bool = os.getenv("WEBHOOK_ENABLED", "false").lower() == "true"

settings = Settings()