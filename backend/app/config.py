"""NoteBrew configuration — settings and environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignore unknown env vars (e.g., old DOCLING_* vars)
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
    ORCHESTRATION_MODEL: Literal[
        "gemini-3-flash-preview", "minimax-m2.5"
    ] = "minimax-m2.5"
    PLANNING_MODEL: Literal[
        "gemini-3-flash-preview", "minimax-m2.5"
    ] = "minimax-m2.5"
    CODEGEN_MODEL: Literal[
        "gemini-3-flash-preview", "minimax-m2.5"
    ] = "minimax-m2.5"

    # OpenRouter Configuration
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    GEMINI_3_FLASH_MODEL: str = "google/gemini-3-flash-preview"
    MINIMAX_M25_MODEL: str = "minimax/minimax-m2.5"

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
    MAX_LLM_CALLS_PER_TASK: int = 20
    MAX_GENERATE_CODE_CALLS: int = 8
    MAX_RUNTIME_SECONDS: int = 120
    MAX_RETRY_PER_TOOL: int = 2

    # PDF Parser Configuration
    PDF_PARSER_PRIMARY: str = "gemini_vision"     # "gemini_vision" or "pymupdf"
    PDF_PARSER_TIMEOUT: int = 120                 # seconds for Gemini API call
    PDF_MAX_SIZE_MB: int = 20                     # max PDF size for Gemini vision
    PDF_VISION_MODEL: str = "google/gemini-3-flash-preview"  # model for PDF parsing
    PDF_CHUNK_ENABLED: bool = True
    PDF_CHUNK_PAGE_SIZE: int = 5
    PDF_CHUNK_MIN_PAGES: int = 10
    PDF_CHUNK_MAX_CONCURRENCY: int = 3

    # Notebook planning limits (Phase 1 speed controls)
    MAX_NOTEBOOK_CELLS: int = 8
    MAX_NOTEBOOK_CODE_CELLS: int = 3

    # Notebook launch links and hosting
    PUBLIC_NOTEBOOK_BASE_URL: str = ""
    COLAB_URL_TEMPLATE: str = "https://colab.research.google.com/#fileId={notebook_url}"
    KAGGLE_URL_TEMPLATE: str = "https://www.kaggle.com/code?url={notebook_url}"


settings = Settings()
