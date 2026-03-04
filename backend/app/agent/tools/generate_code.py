"""Tool: generate_code — Generate Python code for a notebook cell."""

from __future__ import annotations

import logging
import re
from typing import Any

from app.llm_client import get_client
from app.config import settings
from app.agent.prompts.templates import GENERATE_CODE_PROMPT, GENERATE_MARKDOWN_PROMPT

logger = logging.getLogger(__name__)

# Tool schema for the agent
TOOL_SCHEMA = {
    "name": "generate_code",
    "description": (
        "Generate Python code or markdown content for a single notebook cell. "
        "Uses the paper content, cell purpose, and previously generated code "
        "for context-aware generation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "cell_type": {
                "type": "string",
                "enum": ["code", "markdown"],
                "description": "Type of cell to generate ('code' or 'markdown').",
            },
            "cell_purpose": {
                "type": "string",
                "description": "What this cell should accomplish.",
            },
            "paper_title": {
                "type": "string",
                "description": "Title of the research paper.",
            },
            "section_title": {
                "type": "string",
                "description": "Title of the paper section this cell relates to.",
            },
            "section_content": {
                "type": "string",
                "description": "Content of the paper section.",
            },
            "equations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Relevant LaTeX equations.",
            },
            "previous_code_context": {
                "type": "string",
                "description": (
                    "Summary of previously generated code cells for coherence."
                ),
            },
        },
        "required": ["cell_type", "cell_purpose", "paper_title"],
    },
}


async def generate_code(
    cell_type: str,
    cell_purpose: str,
    paper_title: str,
    section_title: str = "",
    section_content: str = "",
    equations: list[str] | None = None,
    previous_code_context: str = "",
) -> dict[str, Any]:
    """Generate content for a single notebook cell.

    Args:
        cell_type: 'code' or 'markdown'.
        cell_purpose: What this cell should accomplish.
        paper_title: Title of the paper being implemented.
        section_title: Title of the relevant paper section.
        section_content: Content of the relevant section.
        equations: LaTeX equations relevant to this cell.
        previous_code_context: Summary of previously generated cells.

    Returns:
        Dict with cell_type, content, and dependencies.
    """
    equations_list = equations or []
    equations_str = (
        "\n".join(f"- ${eq}$" for eq in equations_list)
        if equations_list
        else "No specific equations for this cell."
    )

    # Choose the right prompt template
    if cell_type == "code":
        prompt = GENERATE_CODE_PROMPT.format(
            title=paper_title,
            section_title=section_title or "General",
            section_content=section_content[:3000] if section_content else "N/A",
            equations=equations_str,
            previous_code_context=previous_code_context[:2000] if previous_code_context else "This is the first code cell.",
            cell_purpose=cell_purpose,
        )
    else:
        prompt = GENERATE_MARKDOWN_PROMPT.format(
            title=paper_title,
            section_title=section_title or "General",
            section_content=section_content[:3000] if section_content else "N/A",
            equations=equations_str,
            cell_purpose=cell_purpose,
        )

    logger.info("Generating %s cell: %s", cell_type, cell_purpose[:60])

    client = get_client()

    system_msg = (
        "You are an expert ML researcher and PyTorch developer. "
        "Generate clean, production-quality, runnable code."
        if cell_type == "code"
        else "You are a technical writer creating clear Jupyter notebook markdown cells."
    )

    response = await client.chat.completions.create(
        model=settings.GEMINI_3_FLASH_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=4000,
    )

    content = response.choices[0].message.content or ""

    # Clean up code output (remove markdown code fences if present)
    if cell_type == "code":
        content = _strip_code_fences(content)

    # Extract dependencies from code cells
    dependencies = (
        _extract_dependencies(content) if cell_type == "code" else []
    )

    return {
        "cell_type": cell_type,
        "content": content.strip(),
        "purpose": cell_purpose,
        "section_ref": section_title,
        "dependencies": dependencies,
    }


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences from generated code."""
    text = text.strip()
    if text.startswith("```python"):
        text = text[len("```python") :]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _extract_dependencies(code: str) -> list[str]:
    """Extract third-party package names from import statements."""
    dependencies: set[str] = set()

    import_patterns = [
        r"^import (\w+)",
        r"^from (\w+) import",
    ]

    for line in code.split("\n"):
        line = line.strip()
        for pattern in import_patterns:
            match = re.match(pattern, line)
            if match:
                dependencies.add(match.group(1))

    # Remove standard library modules
    stdlib = {
        "os", "sys", "math", "random", "re", "json", "time", "datetime",
        "collections", "typing", "pathlib", "abc", "functools", "itertools",
        "copy", "io", "string", "textwrap", "warnings", "logging",
    }
    dependencies -= stdlib

    return sorted(dependencies)
