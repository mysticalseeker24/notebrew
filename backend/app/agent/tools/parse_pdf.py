"""Tool: parse_pdf — Extract structured data from a PDF using Docling."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    AcceleratorOptions,
    PdfPipelineOptions,
)

from app.config import settings

logger = logging.getLogger(__name__)

# Tool schema for the agent (OpenAI function-calling format)
TOOL_SCHEMA = {
    "name": "parse_pdf",
    "description": (
        "Parse a PDF research paper and extract its structure: sections, "
        "equations, tables, figures, and metadata. Returns a structured "
        "representation of the paper."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the PDF file to parse.",
            },
        },
        "required": ["file_path"],
    },
}


def _run_docling_sync(pdf_path: Path) -> Any:
    """Run Docling conversion synchronously (called from thread pool).

    This is the CPU-bound work that must NOT run on the asyncio event loop.
    """
    num_threads = max(1, (os.cpu_count() or 4) // 2)

    pipeline_options = PdfPipelineOptions(
        do_ocr=settings.DOCLING_OCR_ENABLED,
        do_table_structure=settings.DOCLING_EXTRACT_TABLES,
        # Batch sizes for parallel processing of pages
        ocr_batch_size=4,
        layout_batch_size=4,
        table_batch_size=4,
        # Multi-threaded deep learning stages
        accelerator_options=AcceleratorOptions(
            num_threads=num_threads,
        ),
    )

    converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
            ),
        },
    )

    return converter.convert(str(pdf_path))


async def parse_pdf(file_path: str) -> dict[str, Any]:
    """Parse a PDF file using Docling and return structured paper data.

    Offloads the CPU-bound Docling conversion to a thread pool so the
    asyncio event loop is never blocked.
    """
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    logger.info("Parsing PDF with Docling: %s", pdf_path.name)

    # Offload CPU-bound Docling to thread pool
    result = await asyncio.to_thread(_run_docling_sync, pdf_path)
    doc = result.document

    # Extract metadata
    metadata = {
        "title": doc.name or pdf_path.stem,
        "authors": [],
        "abstract": "",
        "num_pages": 0,
        "source": "pdf_upload",
    }

    # Extract full text as markdown
    full_text = doc.export_to_markdown()

    # Extract sections
    sections = _extract_sections(full_text)

    # Extract equations from the document
    equations = _extract_equations(full_text)

    # Try to get the abstract from sections
    for section in sections:
        if section["title"].lower().strip() in ("abstract",):
            metadata["abstract"] = section["content"][:500]
            break

    logger.info(
        "Parsed PDF: %d sections, %d equations",
        len(sections),
        len(equations),
    )

    return {
        "metadata": metadata,
        "full_text": full_text,
        "sections": [
            {
                "title": s["title"],
                "content": s["content"],
                "equations": s.get("equations", []),
                "tables": s.get("tables", []),
                "figures": s.get("figures", []),
            }
            for s in sections
        ],
        "equations": equations,
    }


def _extract_sections(md_text: str) -> list[dict[str, Any]]:
    """Extract sections from the markdown text produced by Docling."""
    sections: list[dict[str, Any]] = []
    current_section: dict[str, Any] | None = None

    for line in md_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# ") or stripped.startswith("## "):
            if current_section and current_section["content"].strip():
                sections.append(current_section)

            title = stripped.lstrip("#").strip()
            current_section = {
                "title": title,
                "content": "",
                "equations": [],
                "tables": [],
                "figures": [],
            }
        elif current_section is not None:
            current_section["content"] += line + "\n"

            if "$" in line or "\\begin{" in line:
                current_section["equations"].append(line.strip())

    if current_section and current_section["content"].strip():
        sections.append(current_section)

    return sections


def _extract_equations(text: str) -> list[str]:
    """Extract LaTeX equations from markdown text."""
    import re

    equations: list[str] = []

    # Display equations: $$...$$
    display_matches = re.findall(r"\$\$(.+?)\$\$", text, re.DOTALL)
    equations.extend(eq.strip() for eq in display_matches)

    # Inline equations: $...$ (but not $$)
    inline_matches = re.findall(r"(?<!\$)\$([^\$]+?)\$(?!\$)", text)
    equations.extend(eq.strip() for eq in inline_matches if len(eq.strip()) > 2)

    # LaTeX environments
    env_patterns = [
        r"\\begin\{equation\}(.+?)\\end\{equation\}",
        r"\\begin\{align\}(.+?)\\end\{align\}",
        r"\\begin\{gather\}(.+?)\\end\{gather\}",
    ]
    for pattern in env_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        equations.extend(eq.strip() for eq in matches)

    return equations
