"""Tool: parse_arxiv — Download a paper from arXiv and parse it."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import arxiv

from app.config import settings
from app.agent.tools.parse_pdf import parse_pdf

logger = logging.getLogger(__name__)

# Tool schema for the agent
TOOL_SCHEMA = {
    "name": "parse_arxiv",
    "description": (
        "Download a research paper from arXiv by URL or ID, then parse it. "
        "Returns the same structured representation as parse_pdf, plus arXiv metadata."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "arxiv_url": {
                "type": "string",
                "description": (
                    "arXiv paper URL (e.g., 'https://arxiv.org/abs/1706.03762') "
                    "or just the ID (e.g., '1706.03762')."
                ),
            },
            "save_dir": {
                "type": "string",
                "description": "Directory to save the downloaded PDF. Defaults to uploads dir.",
            },
        },
        "required": ["arxiv_url"],
    },
}


async def parse_arxiv_paper(
    arxiv_url: str, save_dir: str | None = None
) -> dict[str, Any]:
    """Download an arXiv paper and parse it with Gemini Vision / PyMuPDF4LLM.

    Args:
        arxiv_url: arXiv URL or paper ID.
        save_dir: Directory to save the downloaded PDF.

    Returns:
        Structured paper data with arXiv-specific metadata.
    """
    # Extract arXiv ID from URL
    arxiv_id = arxiv_url.strip().split("/")[-1].replace(".pdf", "")
    logger.info("Downloading arXiv paper: %s", arxiv_id)

    # Download the paper
    search = arxiv.Search(id_list=[arxiv_id])
    paper = next(search.results())

    save_path = Path(save_dir or settings.UPLOAD_DIR)
    save_path.mkdir(parents=True, exist_ok=True)
    pdf_filename = save_path / f"arxiv_{arxiv_id.replace('.', '_')}.pdf"

    paper.download_pdf(filename=str(pdf_filename))
    logger.info("Downloaded PDF to: %s", pdf_filename)

    # Parse the downloaded PDF
    result = await parse_pdf(file_path=str(pdf_filename))

    # Enrich metadata with arXiv info
    result["metadata"]["title"] = paper.title or result["metadata"]["title"]
    result["metadata"]["authors"] = [a.name for a in paper.authors]
    result["metadata"]["abstract"] = paper.summary or ""
    result["metadata"]["arxiv_id"] = arxiv_id
    result["metadata"]["published_date"] = (
        paper.published.isoformat() if paper.published else None
    )
    result["metadata"]["doi"] = paper.doi
    result["metadata"]["source"] = "arxiv"

    return result
