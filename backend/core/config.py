"""
Core configuration settings for Blueprint Eye application.
Loaded from environment variables or .env file.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and environment variables."""

    PROJECT_NAME: str = "Blueprint Eye"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Upload Settings
    MAX_UPLOAD_SIZE_MB: int = 50
    MANUAL_STORAGE_PATH: str = "storage/manuals"

    # PDF Processing Settings
    PAGE_IMAGE_FORMAT: str = "png"
    PAGE_IMAGE_DPI: int = 150
    PAGE_IMAGE_STORAGE_PATH: str = "storage/page_images"
    METADATA_STORAGE_PATH: str = "storage/metadata"

    # Chunking Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    CHUNK_STORAGE_PATH: str = "storage/chunks"

    # Embedding & Vector Database Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_COLLECTION: str = "manual_chunks"
    CHROMA_PATH: str = "storage/chromadb"

    # Search Settings
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 20





    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
