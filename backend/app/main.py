"""NoteBrew API — FastAPI application with AI agent-powered paper-to-notebook conversion."""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uuid
import logging
from pathlib import Path
import shutil
from typing import Optional

from app.config import settings
from app.models import (
    ArxivRequest,
    NotebookResponse,
    ProcessingStatus,
    ProgressUpdate,
    AgentState,
)
from app.agent.orchestrator import AgentOrchestrator
from app.agent.tool_registry import ToolRegistry
from app.agent.tools import parse_pdf, parse_arxiv, plan_notebook
from app.agent.tools import generate_code, validate_code, assemble_notebook

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Read version from VERSION file
_VERSION_FILE = Path(__file__).resolve().parent.parent.parent / "VERSION"
__version__ = _VERSION_FILE.read_text().strip() if _VERSION_FILE.exists() else "2.1.0"

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="NoteBrew API",
    description="AI agent that converts research papers into executable Jupyter notebooks",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
Path(settings.OUTPUT_DIR).mkdir(exist_ok=True)

# Task storage (use Redis / database in production)
tasks: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Tool Registry Setup
# ---------------------------------------------------------------------------

def _build_tool_registry() -> ToolRegistry:
    """Create and populate the tool registry with all agent tools."""
    registry = ToolRegistry()

    registry.register(
        name="parse_pdf",
        description=parse_pdf.TOOL_SCHEMA["description"],
        parameters=parse_pdf.TOOL_SCHEMA["parameters"],
        handler=parse_pdf.parse_pdf,
    )
    registry.register(
        name="parse_arxiv",
        description=parse_arxiv.TOOL_SCHEMA["description"],
        parameters=parse_arxiv.TOOL_SCHEMA["parameters"],
        handler=parse_arxiv.parse_arxiv_paper,
    )
    registry.register(
        name="plan_notebook",
        description=plan_notebook.TOOL_SCHEMA["description"],
        parameters=plan_notebook.TOOL_SCHEMA["parameters"],
        handler=plan_notebook.plan_notebook,
    )
    registry.register(
        name="generate_code",
        description=generate_code.TOOL_SCHEMA["description"],
        parameters=generate_code.TOOL_SCHEMA["parameters"],
        handler=generate_code.generate_code,
    )
    registry.register(
        name="validate_code",
        description=validate_code.TOOL_SCHEMA["description"],
        parameters=validate_code.TOOL_SCHEMA["parameters"],
        handler=validate_code.validate_code,
    )
    registry.register(
        name="assemble_notebook",
        description=assemble_notebook.TOOL_SCHEMA["description"],
        parameters=assemble_notebook.TOOL_SCHEMA["parameters"],
        handler=assemble_notebook.assemble_notebook,
    )

    return registry


tool_registry = _build_tool_registry()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "name": "NoteBrew API",
        "version": __version__,
        "description": "AI agent that converts research papers into Jupyter notebooks",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent_tools": tool_registry.tool_names}


@app.post("/api/upload-pdf", response_model=NotebookResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model: Optional[str] = None,
):
    """Upload a PDF paper and convert to notebook using the AI agent."""

    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    task_id = str(uuid.uuid4())
    file_path = Path(settings.UPLOAD_DIR) / f"{task_id}.pdf"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {exc}")

    tasks[task_id] = {
        "status": ProcessingStatus.PENDING,
        "progress": 0,
        "message": "Processing started",
    }

    background_tasks.add_task(
        _run_agent,
        task_id=task_id,
        task_description=(
            f"Parse the PDF at '{file_path}' using the parse_pdf tool, then "
            f"plan and generate a Jupyter notebook from it."
        ),
        model=model,
    )

    return NotebookResponse(task_id=task_id, status=ProcessingStatus.PENDING)


@app.post("/api/arxiv", response_model=NotebookResponse)
async def process_arxiv(
    request: ArxivRequest,
    background_tasks: BackgroundTasks,
):
    """Process a paper from arXiv URL using the AI agent."""

    task_id = str(uuid.uuid4())

    tasks[task_id] = {
        "status": ProcessingStatus.PENDING,
        "progress": 0,
        "message": "Downloading from arXiv",
    }

    background_tasks.add_task(
        _run_agent,
        task_id=task_id,
        task_description=(
            f"Download and parse the arXiv paper at '{request.arxiv_url}' using "
            f"the parse_arxiv tool, then plan and generate a Jupyter notebook."
        ),
        model=request.model,
    )

    return NotebookResponse(task_id=task_id, status=ProcessingStatus.PENDING)


@app.get("/api/status/{task_id}", response_model=ProgressUpdate)
async def get_status(task_id: str):
    """Get processing status for a task."""

    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]
    return ProgressUpdate(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        message=task["message"],
        current_tool=task.get("current_tool"),
    )


@app.get("/api/download/{task_id}")
async def download_notebook(task_id: str):
    """Download generated notebook."""

    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]
    if task["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not completed yet")

    notebook_path = task.get("notebook_path")
    if not notebook_path or not Path(notebook_path).exists():
        raise HTTPException(status_code=404, detail="Notebook file not found")

    return FileResponse(
        path=notebook_path,
        filename=f"notebrew_{task_id}.ipynb",
        media_type="application/x-ipynb+json",
    )


# ---------------------------------------------------------------------------
# Agent Execution
# ---------------------------------------------------------------------------

async def _run_agent(task_id: str, task_description: str, model: Optional[str]):
    """Run the AI agent to process a paper and generate a notebook."""

    def on_progress(status: str, progress: float, message: str):
        tasks[task_id].update(
            {"status": status, "progress": progress, "message": message}
        )

    try:
        orchestrator = AgentOrchestrator(
            tool_registry=tool_registry,
            model=model,
            on_progress=on_progress,
        )

        state = AgentState(task_id=task_id)
        final_state = await orchestrator.run(task_description, state)

        if final_state.status == ProcessingStatus.COMPLETED and final_state.notebook_path:
            tasks[task_id].update({
                "status": ProcessingStatus.COMPLETED,
                "progress": 100,
                "message": "Notebook generated successfully",
                "notebook_path": final_state.notebook_path,
                "metadata": (
                    final_state.paper_structure.metadata.model_dump()
                    if final_state.paper_structure
                    else {}
                ),
            })
        else:
            tasks[task_id].update({
                "status": ProcessingStatus.FAILED,
                "progress": 0,
                "message": final_state.error or "Agent failed to complete",
            })

    except Exception as exc:
        logger.exception("Agent execution failed for task %s", task_id)
        tasks[task_id].update({
            "status": ProcessingStatus.FAILED,
            "progress": 0,
            "message": f"Error: {exc}",
        })


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
