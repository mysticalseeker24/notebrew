"""Tool: parse_pdf — Extract structured data from a PDF.

Primary:  Gemini 3 Flash Vision via OpenRouter (state-of-the-art, no local GPU).
Fallback: PyMuPDF4LLM (offline, lightweight, heuristic-based).
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from pathlib import Path
from typing import Any

from app.config import settings
from app.llm_client import get_client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool schema for the agent (OpenAI function-calling format)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Extraction prompt for Gemini Vision
# ---------------------------------------------------------------------------
EXTRACTION_PROMPT = """You are a research paper parser. Analyze this PDF document and extract its complete structure.

Return a JSON object with EXACTLY this schema (no markdown fences, pure JSON):

{
  "metadata": {
    "title": "Paper title",
    "authors": ["Author 1", "Author 2"],
    "abstract": "Full abstract text",
    "num_pages": 0
  },
  "sections": [
    {
      "title": "Section title (e.g., Introduction, Methodology)",
      "content": "Full section text content in markdown format",
      "equations": ["LaTeX equation strings found in this section, e.g., E = mc^2"],
      "tables": [{"caption": "Table caption", "content": "Table in markdown format"}],
      "figures": [{"caption": "Figure caption", "description": "Brief description"}]
    }
  ],
  "equations": ["All LaTeX equations found in the paper, each as a separate string"],
  "full_text": "Complete paper content as clean markdown, preserving structure with ## headers for sections"
}

Rules:
- Extract ALL sections, including Abstract, Introduction, Related Work, Methodology, Experiments, Results, Conclusion, References, etc.
- Convert ALL mathematical equations to LaTeX notation (e.g., \\nabla, \\sum, \\int, etc.)
- Preserve table structure using markdown table syntax
- The full_text should be a clean markdown representation of the entire paper
- Be thorough — do NOT skip or summarize any content
- Return ONLY valid JSON, no markdown code fences or extra text"""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
async def parse_pdf(file_path: str) -> dict[str, Any]:
    """Parse a PDF file and return structured paper data.

    Strategy:
        1. Try Gemini 3 Flash Vision via OpenRouter (state-of-the-art accuracy).
        2. Fall back to PyMuPDF4LLM if Gemini fails or file is too large.
    """
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    pdf_bytes = pdf_path.read_bytes()
    file_size_mb = len(pdf_bytes) / (1024 * 1024)

    logger.info(
        "Parsing PDF: %s (%.1f MB)", pdf_path.name, file_size_mb,
    )

    # Decide parser based on config and file size
    use_gemini = (
        settings.PDF_PARSER_PRIMARY == "gemini_vision"
        and file_size_mb <= settings.PDF_MAX_SIZE_MB
    )

    if use_gemini:
        try:
            result = await _parse_with_gemini_vision(pdf_bytes, pdf_path.name)
            logger.info(
                "Gemini Vision parsed PDF: %d sections, %d equations",
                len(result.get("sections", [])),
                len(result.get("equations", [])),
            )
            return result
        except Exception as exc:
            logger.warning(
                "Gemini Vision parsing failed, falling back to PyMuPDF4LLM: %s",
                exc,
            )

    # Fallback: PyMuPDF4LLM (lightweight, offline)
    result = await _parse_with_pymupdf(pdf_path)
    logger.info(
        "PyMuPDF4LLM parsed PDF: %d sections, %d equations",
        len(result.get("sections", [])),
        len(result.get("equations", [])),
    )
    return result


# ---------------------------------------------------------------------------
# Primary parser: Gemini 3 Flash Vision via OpenRouter
# ---------------------------------------------------------------------------
async def _parse_with_gemini_vision(
    pdf_bytes: bytes, filename: str,
) -> dict[str, Any]:
    """Send the PDF to Gemini 3 Flash via OpenRouter for vision-based parsing.

    The PDF is base64-encoded and sent as a multimodal message. Gemini
    natively understands PDF layout, equations, tables, and figures.
    """
    b64_data = base64.b64encode(pdf_bytes).decode("utf-8")
    client = get_client()

    logger.info("Sending PDF to Gemini Vision (%s)...", settings.PDF_VISION_MODEL)

    response = await asyncio.wait_for(
        client.chat.completions.create(
            model=settings.PDF_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{b64_data}",
                            },
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
            temperature=0.1,  # Low temperature for extraction accuracy
            max_tokens=16384,
        ),
        timeout=settings.PDF_PARSER_TIMEOUT,
    )

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("Gemini returned empty response")

    # Parse the JSON from the response (strip any markdown fences if present)
    json_str = _extract_json(raw_content)
    data = json.loads(json_str)

    # Normalize the response to match our expected format
    return _normalize_gemini_response(data, filename)


def _extract_json(text: str) -> str:
    """Extract JSON from LLM response, stripping markdown fences if present."""
    # Try to find JSON in markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try to find raw JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text.strip()


def _normalize_gemini_response(
    data: dict[str, Any], filename: str,
) -> dict[str, Any]:
    """Normalize Gemini's response to match the expected PaperStructure format."""
    metadata = data.get("metadata", {})
    metadata.setdefault("title", Path(filename).stem)
    metadata.setdefault("authors", [])
    metadata.setdefault("abstract", "")
    metadata.setdefault("num_pages", 0)
    metadata.setdefault("source", "pdf_upload")

    sections = []
    for s in data.get("sections", []):
        sections.append({
            "title": s.get("title", "Untitled"),
            "content": s.get("content", ""),
            "equations": s.get("equations", []),
            "tables": s.get("tables", []),
            "figures": s.get("figures", []),
        })

    # Try to extract abstract from sections if not in metadata
    if not metadata["abstract"]:
        for section in sections:
            if section["title"].lower().strip() in ("abstract",):
                metadata["abstract"] = section["content"][:500]
                break

    return {
        "metadata": metadata,
        "full_text": data.get("full_text", ""),
        "sections": sections,
        "equations": data.get("equations", []),
    }


# ---------------------------------------------------------------------------
# Fallback parser: PyMuPDF4LLM (offline, no ML)
# ---------------------------------------------------------------------------
async def _parse_with_pymupdf(pdf_path: Path) -> dict[str, Any]:
    """Parse a PDF using PyMuPDF4LLM as a lightweight offline fallback.

    This is heuristic-based — good for text extraction but weaker on
    equations and complex tables compared to Gemini Vision.
    """
    import pymupdf4llm  # Lazy import to avoid loading if Gemini succeeds

    logger.info("Parsing PDF with PyMuPDF4LLM (fallback): %s", pdf_path.name)

    # PyMuPDF4LLM is CPU-bound, offload to thread pool
    md_text = await asyncio.to_thread(
        pymupdf4llm.to_markdown, str(pdf_path),
    )

    # Extract structure from markdown
    sections = _extract_sections(md_text)
    equations = _extract_equations(md_text)

    # Build metadata
    metadata = {
        "title": pdf_path.stem,
        "authors": [],
        "abstract": "",
        "num_pages": 0,
        "source": "pdf_upload",
    }

    # Try to get abstract from sections
    for section in sections:
        if section["title"].lower().strip() in ("abstract",):
            metadata["abstract"] = section["content"][:500]
            break

    return {
        "metadata": metadata,
        "full_text": md_text,
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


# ---------------------------------------------------------------------------
# Shared helpers (used by PyMuPDF4LLM fallback)
# ---------------------------------------------------------------------------
def _extract_sections(md_text: str) -> list[dict[str, Any]]:
    """Extract sections from markdown text."""
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
