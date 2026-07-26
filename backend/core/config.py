"""
Core configuration settings for Blueprint Eye application.
Loaded from environment variables or .env file.
"""

from typing import Any, List, Optional, Union
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file automatically into environment
load_dotenv()


class Settings(BaseSettings):
    """Application settings and environment variables."""

    PROJECT_NAME: str = "Blueprint Eye"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    import json
                    return json.loads(v_str)
                except Exception:
                    pass
            return [item.strip() for item in v_str.split(",") if item.strip()]
        return v

    # Upload Settings
    MAX_UPLOAD_SIZE_MB: int = 50
    MANUAL_STORAGE_PATH: str = "storage/manuals"

    # PDF Processing Settings
    PAGE_IMAGE_FORMAT: str = "png"
    PAGE_IMAGE_DPI: int = 150
    PAGE_IMAGE_STORAGE_PATH: str = "storage/page_images"
    METADATA_STORAGE_PATH: str = "storage/metadata"

    # Gemini Image/Diagram Analysis Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    ENABLE_IMAGE_ANALYSIS: bool = True

    # Chunking Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    CHUNK_STORAGE_PATH: str = "storage/chunks"

    # Embedding & Vector Database Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_COLLECTION: str = "manual_chunks"
    CHROMA_PATH: str = "storage/chromadb"

    # Search Settings
    DEFAULT_TOP_K: int = 3
    MAX_TOP_K: int = 20

    # Groq API Settings for RAG Answer Generation
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TIMEOUT: float = 60.0
    GROQ_TEMPERATURE: float = 0.0
    GROQ_TOP_P: float = 0.9
    GROQ_MAX_OUTPUT_TOKENS: int = 512

    # Gemini Image/Diagram Analysis Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    ENABLE_IMAGE_ANALYSIS: bool = True
    GEMINI_TIMEOUT: float = 60.0
    GEMINI_TEMPERATURE: float = 0.0
    GEMINI_TOP_P: float = 0.9
    GEMINI_MAX_OUTPUT_TOKENS: int = 512
    MAX_GENERATION_RETRIES: int = 1

    RAG_TOP_K: int = 3
    RAG_SIMILARITY_THRESHOLD: float = 0.45

    RAG_MAX_CONTEXT_CHARS: int = 12000

    # Answer Generation & Soft Threshold Settings (Sprint 6.5)
    RAG_ENABLE_SOFT_THRESHOLD: bool = True
    RAG_SOFT_THRESHOLD_MARGIN: float = 0.05
    RAG_INCLUDE_PAGE_HEADERS: bool = True
    RAG_MAX_PREVIEW_CHARS: int = 250

    # Debug & Observability Settings
    DEBUG_RAG_PIPELINE: bool = False

    # Evidence & Context Selection Settings (Sprint 7.2)
    EVIDENCE_TOP1_THRESHOLD: float = 0.90
    EVIDENCE_TOP2_THRESHOLD: float = 0.82
    EVIDENCE_TOP3_THRESHOLD: float = 0.75







    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
