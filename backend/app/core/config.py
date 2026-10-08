"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./sasti_dawai.db"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # OCR
    TESSERACT_CMD: str = "tesseract"
    OCR_DPI: int = 300
    OCR_LANG: str = "eng"

    # Upload
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}

    # Safety
    MIN_CONFIDENCE_THRESHOLD: float = 0.6

    class Config:
        env_file = ".env"


settings = Settings()
