"""NoteBrew configuration — settings and environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    # API Keys
    OPENROUTER_API_KEY: str

    # Model Configuration
    PRIMARY_MODEL: Literal[
        "gemini-3-flash-preview", "minimax-m2.5"
    ] = "gemini-3-flash-preview"
    FALLBACK_MODEL: Literal[
        "gemini-3-flash-preview", "minimax-m2.5"
    ] = "minimax-m2.5"

    # OpenRouter Configuration
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    GEMINI_3_FLASH_MODEL: str = "google/gemini-3-flash-preview"
    MINIMAX_M25_MODEL: str = "minimaxai/minimax-m2.5"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False

    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"

    # Notebook Configuration
    NOTEBOOK_TIMEOUT: int = 300  # seconds
    MAX_CONTEXT_TOKENS: int = 100000  # for Gemini 3 Flash's 1M context

    # Agent Configuration
    AGENT_MAX_ITERATIONS: int = 15
    AGENT_MAX_RETRIES: int = 3
    AGENT_TOOL_TIMEOUT: int = 120  # seconds per tool execution

    # Docling Configuration
    DOCLING_OCR_ENABLED: bool = True
    DOCLING_EXTRACT_FIGURES: bool = True
    DOCLING_EXTRACT_TABLES: bool = True


settings = Settings()
