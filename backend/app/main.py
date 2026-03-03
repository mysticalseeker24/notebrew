from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import arxiv
import uuid
import os
from pathlib import Path
import shutil
from typing import Optional

from app.config import settings
from app.models import (
    ArxivRequest, NotebookResponse, ProcessingStatus, 
    ProgressUpdate, PaperMetadata
)
from app.pdf_parser import PDFParser
from app.code_generator import CodeGenerator
from app.notebook_generator import NotebookGenerator

app = FastAPI(
    title="Paper2Notebook API",
    description="Convert research papers to runnable Jupyter notebooks",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
Path(settings.OUTPUT_DIR).mkdir(exist_ok=True)

# Task storage (use Redis/database in production)
tasks = {}

@app.get("/")
async def root():
    return {
        "message": "Paper2Notebook API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/upload-pdf", response_model=NotebookResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model: Optional[str] = None
):
    """Upload a PDF paper and convert to notebook"""
    
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Create task
    task_id = str(uuid.uuid4())
    file_path = Path(settings.UPLOAD_DIR) / f"{task_id}.pdf"
    
    # Save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Initialize task
    tasks[task_id] = {
        "status": ProcessingStatus.PENDING,
        "progress": 0,
        "message": "Processing started"
    }
    
    # Process in background
    background_tasks.add_task(
        process_paper,
        task_id=task_id,
        pdf_path=str(file_path),
        model=model
    )
    
    return NotebookResponse(
        task_id=task_id,
        status=ProcessingStatus.PENDING,
    )

@app.post("/api/arxiv", response_model=NotebookResponse)
async def process_arxiv(
    request: ArxivRequest,
    background_tasks: BackgroundTasks
):
    """Process a paper from arXiv URL or ID"""
    
    task_id = str(uuid.uuid4())
    
    # Initialize task
    tasks[task_id] = {
        "status": ProcessingStatus.PENDING,
        "progress": 0,
        "message": "Downloading from arXiv"
    }
    
    # Process in background
    background_tasks.add_task(
        process_arxiv_paper,
        task_id=task_id,
        arxiv_url=request.arxiv_url,
        model=request.model
    )
    
    return NotebookResponse(
        task_id=task_id,
        status=ProcessingStatus.PENDING,
    )

@app.get("/api/status/{task_id}", response_model=ProgressUpdate)
async def get_status(task_id: str):
    """Get processing status for a task"""
    
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    return ProgressUpdate(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        message=task["message"],
        current_section=task.get("current_section")
    )

@app.get("/api/download/{task_id}")
async def download_notebook(task_id: str):
    """Download generated notebook"""
    
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
        filename=f"paper_notebook_{task_id}.ipynb",
        media_type="application/x-ipynb+json"
    )

async def process_arxiv_paper(task_id: str, arxiv_url: str, model: Optional[str]):
    """Download and process arXiv paper"""
    
    try:
        # Update status
        update_task(task_id, ProcessingStatus.PARSING_PDF, 10, "Downloading from arXiv")
        
        # Extract arXiv ID
        arxiv_id = arxiv_url.split('/')[-1].replace('.pdf', '')
        
        # Download paper
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())
        
        # Download PDF
        pdf_path = Path(settings.UPLOAD_DIR) / f"{task_id}.pdf"
        paper.download_pdf(filename=str(pdf_path))
        
        # Process the PDF
        await process_paper(task_id, str(pdf_path), model)
        
    except Exception as e:
        update_task(task_id, ProcessingStatus.FAILED, 0, f"Error: {str(e)}")
        raise

async def process_paper(task_id: str, pdf_path: str, model: Optional[str]):
    """Main paper processing pipeline"""
    
    try:
        # 1. Parse PDF
        update_task(task_id, ProcessingStatus.PARSING_PDF, 20, "Parsing PDF structure")
        
        parser = PDFParser(pdf_path)
        paper_structure = parser.get_complete_structure()
        
        # 2. Extract LaTeX
        update_task(task_id, ProcessingStatus.EXTRACTING_LATEX, 40, "Extracting equations")
        
        # Already done in get_complete_structure()
        
        # 3. Generate Code
        update_task(task_id, ProcessingStatus.GENERATING_CODE, 60, "Generating PyTorch code")
        
        code_gen = CodeGenerator(model=model)
        notebook_data = code_gen.generate_complete_notebook(paper_structure)
        
        # 4. Create Notebook
        update_task(task_id, ProcessingStatus.CREATING_NOTEBOOK, 80, "Creating Jupyter notebook")
        
        nb_gen = NotebookGenerator()
        notebook = nb_gen.generate_from_paper_data(notebook_data)
        
        # Save notebook
        output_path = Path(settings.OUTPUT_DIR) / f"{task_id}.ipynb"
        nb_gen.save(str(output_path))
        
        # 5. Complete
        tasks[task_id].update({
            "status": ProcessingStatus.COMPLETED,
            "progress": 100,
            "message": "Notebook generated successfully",
            "notebook_path": str(output_path),
            "metadata": paper_structure['metadata']
        })
        
    except Exception as e:
        update_task(task_id, ProcessingStatus.FAILED, 0, f"Error: {str(e)}")
        raise

def update_task(task_id: str, status: ProcessingStatus, progress: float, message: str):
    """Update task status"""
    if task_id in tasks:
        tasks[task_id].update({
            "status": status,
            "progress": progress,
            "message": message
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
