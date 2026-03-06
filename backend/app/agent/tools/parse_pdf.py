"""Tool: parse_pdf — Extract structured data from a PDF.

Primary:  Gemini 3 Flash Vision via OpenRouter (state-of-the-art, no local GPU).
Fallback: PyMuPDF4LLM (offline, lightweight, heuristic-based).

Hybrid strategy (Approach B):
  - Gemini Vision extracts STRUCTURED data: metadata, sections, equations
    (LaTeX), tables (markdown), figures (captions/descriptions), references.
  - PyMuPDF4LLM extracts the RAW full_text (fast, free, no token cost).
  - This avoids JSON truncation from asking Gemini to reproduce the full paper.
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
# Extraction prompt for Gemini Vision (structured data only — NO full_text)
# ---------------------------------------------------------------------------
EXTRACTION_PROMPT = """\
You are an expert research paper parser. Analyze this PDF and extract its \
complete structure as JSON.

Return a JSON object with EXACTLY this schema (no markdown fences, pure JSON):

{
  "metadata": {
    "title": "Full paper title",
    "authors": ["Author 1", "Author 2"],
    "abstract": "Full abstract text",
    "num_pages": 0,
    "published_date": "YYYY or YYYY-MM if visible",
    "doi": "DOI if visible, else null"
  },
  "sections": [
    {
      "title": "Section title (e.g., 1. Introduction)",
      "content_summary": "Brief 1-2 sentence summary of the section content",
      "equations": ["LaTeX string, e.g. E = mc^2"],
      "tables": [{"caption": "Table 1: ...", "content": "| col1 | col2 |\\n|---|---|\\n| ... |"}],
      "figures": [{"caption": "Figure 1: ...", "description": "Visual description of what the figure shows"}],
      "key_findings": ["Important result or claim from this section"]
    }
  ],
  "equations": ["Every LaTeX equation in the paper as a separate string"],
  "references": [
    {"id": "[1]", "text": "Author et al. Title. Journal, Year."}
  ],
  "key_contributions": ["Main contribution 1", "Main contribution 2"]
}

Rules:
- Extract ALL sections: Abstract, Introduction, Related Work, Methodology, \
Experiments, Results, Discussion, Conclusion, Appendix, etc.
- Convert ALL math to LaTeX (\\nabla, \\sum, \\int, \\frac{}{}, etc.)
- Preserve table structure using markdown table syntax
- For figures: describe what the figure visually shows (charts, diagrams, \
architecture, plots, etc.)
- Extract all numbered references from the References/Bibliography section
- Do NOT include full section text — use content_summary instead
- Be thorough — extract EVERY equation, table, figure, and reference
- Return ONLY valid JSON, no markdown fences or extra text"""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
async def parse_pdf(file_path: str) -> dict[str, Any]:
    """Parse a PDF file and return structured paper data.

    Hybrid strategy:
        1. PyMuPDF4LLM extracts raw full_text (fast, offline, free).
        2. Gemini Vision extracts structured data (metadata, sections,
           equations, tables, figures, references).
        3. Results are merged into a single unified response.

    Falls back to PyMuPDF-only if Gemini Vision fails.
    """
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    pdf_bytes = pdf_path.read_bytes()
    file_size_mb = len(pdf_bytes) / (1024 * 1024)

    logger.info(
        "Parsing PDF: %s (%.1f MB)", pdf_path.name, file_size_mb,
    )

    # Step 1: Always extract full_text with PyMuPDF4LLM (instant, free)
    full_text = await _extract_full_text_pymupdf(pdf_path)
    logger.info("PyMuPDF4LLM extracted %d chars of full text", len(full_text))

    # Step 2: Try Gemini Vision for structured extraction
    use_gemini = (
        settings.PDF_PARSER_PRIMARY == "gemini_vision"
        and file_size_mb <= settings.PDF_MAX_SIZE_MB
    )

    if use_gemini:
        try:
            page_count = _count_pdf_pages(pdf_bytes)
            use_chunking = (
                settings.PDF_CHUNK_ENABLED
                and page_count >= settings.PDF_CHUNK_MIN_PAGES
                and settings.PDF_CHUNK_PAGE_SIZE > 0
            )

            if use_chunking:
                structured = await _parse_with_gemini_chunks(
                    pdf_bytes=pdf_bytes,
                    filename=pdf_path.name,
                    page_count=page_count,
                )
            else:
                structured = await _parse_with_gemini_vision(pdf_bytes, pdf_path.name)

            logger.info(
                "Gemini Vision: %d sections, %d equations, %d references",
                len(structured.get("sections", [])),
                len(structured.get("equations", [])),
                len(structured.get("references", [])),
            )
            # Merge: Gemini structured data + PyMuPDF full_text
            structured["full_text"] = full_text
            return structured
        except Exception as exc:
            logger.warning(
                "Gemini Vision failed, using PyMuPDF-only fallback: %s", exc,
            )

    # Fallback: structure from PyMuPDF heuristics
    result = _build_structure_from_text(full_text, pdf_path.name)
    logger.info(
        "PyMuPDF fallback: %d sections, %d equations",
        len(result.get("sections", [])),
        len(result.get("equations", [])),
    )
    return result


def _count_pdf_pages(pdf_bytes: bytes) -> int:
    """Return page count from raw PDF bytes."""
    import pymupdf

    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return int(doc.page_count)


def _split_pdf_chunks(pdf_bytes: bytes, page_size: int) -> list[tuple[int, int, bytes]]:
    """Split PDF bytes into page-based chunk bytes (start_page, end_page, bytes)."""
    import pymupdf

    chunks: list[tuple[int, int, bytes]] = []
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as src:
        total_pages = src.page_count
        for start in range(0, total_pages, page_size):
            end = min(start + page_size, total_pages)
            out = pymupdf.open()
            out.insert_pdf(src, from_page=start, to_page=end - 1)
            chunk_bytes = out.tobytes()
            out.close()
            chunks.append((start + 1, end, chunk_bytes))
    return chunks


async def _parse_with_gemini_chunks(
    pdf_bytes: bytes,
    filename: str,
    page_count: int,
) -> dict[str, Any]:
    """Parse long PDFs in concurrent page chunks and merge structured outputs."""
    chunk_size = max(1, settings.PDF_CHUNK_PAGE_SIZE)
    chunks = _split_pdf_chunks(pdf_bytes, chunk_size)
    if len(chunks) <= 1:
        return await _parse_with_gemini_vision(pdf_bytes, filename)

    logger.info(
        "Chunked Gemini parse enabled: %d pages split into %d chunks (size=%d)",
        page_count,
        len(chunks),
        chunk_size,
    )

    semaphore = asyncio.Semaphore(max(1, settings.PDF_CHUNK_MAX_CONCURRENCY))

    async def _run_chunk(
        index: int,
        start_page: int,
        end_page: int,
        chunk_pdf_bytes: bytes,
    ) -> tuple[int, dict[str, Any]]:
        async with semaphore:
            result = await _parse_with_gemini_vision(
                chunk_pdf_bytes,
                f"{filename} [pages {start_page}-{end_page}]",
                chunk_hint=(start_page, end_page, page_count),
            )
            return index, result

    tasks = [
        _run_chunk(i, start, end, chunk_bytes)
        for i, (start, end, chunk_bytes) in enumerate(chunks)
    ]
    results = await asyncio.gather(*tasks)
    ordered = [r for _, r in sorted(results, key=lambda item: item[0])]
    return _merge_chunk_results(ordered, filename, page_count)


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    """De-duplicate non-empty strings preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = (value or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _merge_chunk_results(
    chunk_results: list[dict[str, Any]],
    filename: str,
    page_count: int,
) -> dict[str, Any]:
    """Merge chunk-level Gemini structures into one normalized paper structure."""
    if not chunk_results:
        return _normalize_gemini_response({}, filename)

    metadata = {
        "title": "",
        "authors": [],
        "abstract": "",
        "num_pages": page_count,
        "published_date": None,
        "doi": None,
        "source": "pdf_upload",
    }

    section_signatures: set[str] = set()
    sections: list[dict[str, Any]] = []
    all_equations: list[str] = []
    all_references: list[dict[str, Any]] = []
    all_contributions: list[str] = []

    for item in chunk_results:
        md = item.get("metadata", {}) or {}
        if not metadata["title"] and md.get("title"):
            metadata["title"] = md.get("title")
        if not metadata["abstract"] and md.get("abstract"):
            metadata["abstract"] = md.get("abstract")
        if not metadata["doi"] and md.get("doi"):
            metadata["doi"] = md.get("doi")
        if not metadata["published_date"] and md.get("published_date"):
            metadata["published_date"] = md.get("published_date")

        metadata["authors"] = _dedupe_preserve_order(
            list(metadata.get("authors", [])) + list(md.get("authors", []))
        )

        for section in item.get("sections", []) or []:
            title = str(section.get("title", "")).strip()
            content = str(section.get("content", "")).strip()
            signature = f"{title.lower()}::{content[:200].lower()}"
            if signature in section_signatures:
                continue
            section_signatures.add(signature)
            sections.append(section)

        all_equations.extend(item.get("equations", []) or [])
        all_references.extend(item.get("references", []) or [])
        all_contributions.extend(item.get("key_contributions", []) or [])

    if not metadata["title"]:
        metadata["title"] = Path(filename).stem

    # Deduplicate references by serialized identity.
    unique_refs: list[dict[str, Any]] = []
    seen_ref_keys: set[str] = set()
    for ref in all_references:
        if not isinstance(ref, dict):
            continue
        key = json.dumps(ref, sort_keys=True, ensure_ascii=True)
        if key in seen_ref_keys:
            continue
        seen_ref_keys.add(key)
        unique_refs.append(ref)

    return {
        "metadata": metadata,
        "full_text": "",
        "sections": sections,
        "equations": _dedupe_preserve_order(all_equations),
        "references": unique_refs,
        "key_contributions": _dedupe_preserve_order(all_contributions),
    }


# ---------------------------------------------------------------------------
# PyMuPDF4LLM: fast full-text extraction (always runs)
# ---------------------------------------------------------------------------
async def _extract_full_text_pymupdf(pdf_path: Path) -> str:
    """Extract raw markdown text from PDF using PyMuPDF4LLM.

    This is CPU-bound, so it runs in a thread pool. It's instant and
    provides the complete paper text that Gemini Vision doesn't need
    to reproduce in its JSON output.
    """
    import pymupdf4llm

    return await asyncio.to_thread(
        pymupdf4llm.to_markdown, str(pdf_path),
    )


# ---------------------------------------------------------------------------
# Primary parser: Gemini 3 Flash Vision via OpenRouter
# ---------------------------------------------------------------------------
async def _parse_with_gemini_vision(
    pdf_bytes: bytes, filename: str,
    chunk_hint: tuple[int, int, int] | None = None,
) -> dict[str, Any]:
    """Send the PDF to Gemini 3 Flash for structured extraction.

    Extracts metadata, sections (with summaries), equations (LaTeX),
    tables (markdown), figures (descriptions), and references.
    Does NOT extract full_text — that comes from PyMuPDF4LLM.
    """
    b64_data = base64.b64encode(pdf_bytes).decode("utf-8")
    client = get_client()

    logger.info("Sending PDF to Gemini Vision (%s)...", settings.PDF_VISION_MODEL)

    prompt = EXTRACTION_PROMPT
    if chunk_hint:
        start_page, end_page, total_pages = chunk_hint
        prompt = (
            f"This document is pages {start_page}-{end_page} of {total_pages}. "
            "Extract JSON for only the visible chunk content.\n\n"
            f"{EXTRACTION_PROMPT}"
        )

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
                            "text": prompt,
                        },
                    ],
                }
            ],
            temperature=0.1,  # Low for extraction accuracy
            max_tokens=32768,  # Structured data fits well within this
        ),
        timeout=settings.PDF_PARSER_TIMEOUT,
    )

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("Gemini returned empty response")

    # Parse JSON from response (strip markdown fences if present)
    json_str = _extract_json(raw_content)
    data = json.loads(json_str)

    return _normalize_gemini_response(data, filename)


# ---------------------------------------------------------------------------
# JSON extraction and normalization
# ---------------------------------------------------------------------------
def _extract_json(text: str) -> str:
    """Extract JSON from LLM response, stripping markdown fences if present."""
    # Try markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try raw JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text.strip()


def _normalize_gemini_response(
    data: dict[str, Any], filename: str,
) -> dict[str, Any]:
    """Normalize Gemini's response to the expected PaperStructure format."""
    # Metadata
    metadata = data.get("metadata", {})
    metadata.setdefault("title", Path(filename).stem)
    metadata.setdefault("authors", [])
    metadata.setdefault("abstract", "")
    metadata.setdefault("num_pages", 0)
    metadata.setdefault("published_date", None)
    metadata.setdefault("doi", None)
    metadata.setdefault("source", "pdf_upload")

    # Sections
    sections = []
    for s in data.get("sections", []):
        sections.append({
            "title": s.get("title", "Untitled"),
            "content": s.get("content_summary", s.get("content", "")),
            "equations": s.get("equations", []),
            "tables": s.get("tables", []),
            "figures": s.get("figures", []),
            "key_findings": s.get("key_findings", []),
        })

    # Extract abstract from sections if not in metadata
    if not metadata["abstract"]:
        for section in sections:
            if section["title"].lower().strip() in ("abstract",):
                metadata["abstract"] = section["content"][:1000]
                break

    # References
    references = data.get("references", [])

    return {
        "metadata": metadata,
        "full_text": "",  # Filled by caller with PyMuPDF4LLM output
        "sections": sections,
        "equations": data.get("equations", []),
        "references": references,
        "key_contributions": data.get("key_contributions", []),
    }


# ---------------------------------------------------------------------------
# Fallback: build structure from PyMuPDF raw text only
# ---------------------------------------------------------------------------
def _build_structure_from_text(
    md_text: str, filename: str,
) -> dict[str, Any]:
    """Build a structured response from PyMuPDF4LLM markdown text.

    This is the pure-offline fallback — heuristic-based, weaker on
    equations/tables/figures, but always works.
    """
    sections = _extract_sections(md_text)
    equations = _extract_equations(md_text)

    metadata = {
        "title": filename.replace(".pdf", "").replace("_", " "),
        "authors": [],
        "abstract": "",
        "num_pages": 0,
        "source": "pdf_upload",
    }

    # Try to get abstract from sections
    for section in sections:
        if section["title"].lower().strip() in ("abstract",):
            metadata["abstract"] = section["content"][:1000]
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
                "key_findings": [],
            }
            for s in sections
        ],
        "equations": equations,
        "references": [],
        "key_contributions": [],
    }


# ---------------------------------------------------------------------------
# Heuristic helpers (used by PyMuPDF fallback)
# ---------------------------------------------------------------------------
def _extract_sections(md_text: str) -> list[dict[str, Any]]:
    """Extract sections from markdown text using heading patterns."""
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

            # Detect equations
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
