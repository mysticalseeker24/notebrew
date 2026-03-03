from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PARSING_PDF = "parsing_pdf"
    EXTRACTING_LATEX = "extracting_latex"
    GENERATING_CODE = "generating_code"
    CREATING_NOTEBOOK = "creating_notebook"
    COMPLETED = "completed"
    FAILED = "failed"

class ArxivRequest(BaseModel):
    arxiv_url: str = Field(..., description="arXiv paper URL or ID")
    model: Optional[str] = Field(None, description="Model to use: gemini-3-flash-preview or minimax-m2.5")

class NotebookSection(BaseModel):
    title: str
    content: str
    code_cells: List[str] = []
    markdown_cells: List[str] = []

class NotebookResponse(BaseModel):
    task_id: str
    status: ProcessingStatus
    notebook_url: Optional[str] = None
    colab_url: Optional[str] = None
    error: Optional[str] = None
    sections: List[NotebookSection] = []
    metadata: Dict[str, Any] = {}

class ProgressUpdate(BaseModel):
    task_id: str
    status: ProcessingStatus
    progress: float = Field(..., ge=0, le=100)
    message: str
    current_section: Optional[str] = None

class PaperMetadata(BaseModel):
    title: str
    authors: List[str] = []
    abstract: str = ""
    arxiv_id: Optional[str] = None
    published_date: Optional[str] = None
    equations: List[str] = []
    figures: List[str] = []
