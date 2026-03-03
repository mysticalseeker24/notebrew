"""NoteBrew data models — Pydantic models for the API and agent system."""

from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


# ---------------------------------------------------------------------------
# Processing Status
# ---------------------------------------------------------------------------

class ProcessingStatus(str, Enum):
    """Status stages for notebook generation pipeline."""

    PENDING = "pending"
    PARSING_PDF = "parsing_pdf"
    PLANNING = "planning"
    GENERATING_CODE = "generating_code"
    VALIDATING_CODE = "validating_code"
    ASSEMBLING_NOTEBOOK = "assembling_notebook"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# API Request / Response Models
# ---------------------------------------------------------------------------

class ArxivRequest(BaseModel):
    """Request to process a paper from arXiv."""

    arxiv_url: str = Field(..., description="arXiv paper URL or ID")
    model: Optional[str] = Field(
        None, description="Model to use: gemini-3-flash-preview or minimax-m2.5"
    )


class NotebookResponse(BaseModel):
    """Response returned when a notebook generation task is created."""

    task_id: str
    status: ProcessingStatus
    notebook_url: Optional[str] = None
    colab_url: Optional[str] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = {}


class ProgressUpdate(BaseModel):
    """Real-time progress update for a running task."""

    task_id: str
    status: ProcessingStatus
    progress: float = Field(..., ge=0, le=100)
    message: str
    current_tool: Optional[str] = None
    current_section: Optional[str] = None


# ---------------------------------------------------------------------------
# Paper Structure Models
# ---------------------------------------------------------------------------

class PaperSection(BaseModel):
    """A single section extracted from a research paper."""

    title: str = Field(..., description="Section title (e.g., 'Abstract')")
    content: str = Field(..., description="Full section text content")
    equations: list[str] = Field(
        default_factory=list, description="LaTeX equations found in this section"
    )
    tables: list[dict[str, Any]] = Field(
        default_factory=list, description="Tables extracted from this section"
    )
    figures: list[dict[str, Any]] = Field(
        default_factory=list, description="Figure references in this section"
    )


class PaperMetadata(BaseModel):
    """Metadata extracted from a research paper."""

    title: str = ""
    authors: list[str] = []
    abstract: str = ""
    arxiv_id: Optional[str] = None
    published_date: Optional[str] = None
    num_pages: int = 0
    source: str = ""  # "pdf_upload" or "arxiv"


class PaperStructure(BaseModel):
    """Complete structured representation of a research paper."""

    metadata: PaperMetadata = Field(default_factory=PaperMetadata)
    full_text: str = ""
    sections: list[PaperSection] = []
    equations: list[str] = Field(
        default_factory=list, description="All LaTeX equations in the paper"
    )


# ---------------------------------------------------------------------------
# Notebook Planning Models
# ---------------------------------------------------------------------------

class NotebookCellPlan(BaseModel):
    """Plan for a single notebook cell."""

    cell_type: str = Field(..., description="'markdown' or 'code'")
    purpose: str = Field(..., description="What this cell should contain/accomplish")
    section_ref: Optional[str] = Field(
        None, description="Which paper section this cell relates to"
    )


class NotebookPlan(BaseModel):
    """Agent's plan for the notebook structure."""

    title: str = Field(..., description="Notebook title")
    summary: str = Field(..., description="Brief description of what the notebook implements")
    framework: str = Field(default="pytorch", description="ML framework to use")
    cells: list[NotebookCellPlan] = []
    dependencies: list[str] = Field(
        default_factory=list, description="Required pip packages"
    )


# ---------------------------------------------------------------------------
# Agent Models
# ---------------------------------------------------------------------------

class ToolCall(BaseModel):
    """A tool call requested by the agent LLM."""

    id: str = Field(..., description="Unique ID for this tool call")
    name: str = Field(..., description="Name of the tool to invoke")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments to pass to the tool"
    )


class ToolResult(BaseModel):
    """Result returned from a tool execution."""

    tool_call_id: str = Field(..., description="ID of the tool call this result is for")
    name: str = Field(..., description="Name of the tool that was executed")
    success: bool = True
    result: Any = None
    error: Optional[str] = None


class AgentMessage(BaseModel):
    """A message in the agent's conversation history."""

    role: str = Field(..., description="'system', 'user', 'assistant', or 'tool'")
    content: Optional[str] = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class AgentState(BaseModel):
    """Current state of the agent during execution."""

    task_id: str
    iteration: int = 0
    messages: list[AgentMessage] = []
    paper_structure: Optional[PaperStructure] = None
    notebook_plan: Optional[NotebookPlan] = None
    generated_cells: list[dict[str, Any]] = Field(default_factory=list)
    notebook_path: Optional[str] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    error: Optional[str] = None
