"""Tool: plan_notebook — Create a structured plan for the notebook."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.llm_client import get_client
from app.config import settings
from app.agent.prompts.templates import PLAN_NOTEBOOK_PROMPT

logger = logging.getLogger(__name__)


def _resolve_model_name(model_name: str) -> str:
    """Resolve short model names to full OpenRouter paths."""
    mapping = {
        "gemini-3-flash-preview": settings.GEMINI_3_FLASH_MODEL,
        "minimax-m2.5": settings.MINIMAX_M25_MODEL,
    }
    return mapping.get(model_name, model_name)

# Tool schema for the agent
TOOL_SCHEMA = {
    "name": "plan_notebook",
    "description": (
        "Analyze the parsed paper structure and create a plan for the Jupyter "
        "notebook. Decides which sections to implement as code, which to "
        "describe in markdown, what dependencies are needed, and the overall "
        "notebook structure."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "paper_data": {
                "type": "object",
                "description": (
                    "The parsed paper data from parse_pdf or parse_arxiv, "
                    "containing metadata, sections, and equations."
                ),
            },
        },
        "required": ["paper_data"],
    },
}


async def plan_notebook(paper_data: dict[str, Any]) -> dict[str, Any]:
    """Create a notebook plan by analyzing the paper structure.

    Uses the LLM to decide what to implement and how to structure the notebook.

    Args:
        paper_data: Parsed paper data with metadata, sections, equations.

    Returns:
        NotebookPlan as a dict with title, summary, framework, dependencies, cells.
    """
    metadata = paper_data.get("metadata", {})
    sections = paper_data.get("sections", [])
    equations = paper_data.get("equations", [])

    # Build sections summary
    sections_summary = "\n".join(
        f"- **{s['title']}**: {s['content'][:200]}..."
        for s in sections
    )

    # Build equations summary
    equations_summary = (
        "\n".join(f"- ${eq}$" for eq in equations[:15])
        if equations
        else "No equations found."
    )

    prompt = PLAN_NOTEBOOK_PROMPT.format(
        title=metadata.get("title", "Unknown Paper"),
        abstract=metadata.get("abstract", "No abstract available."),
        sections_summary=sections_summary or "No sections extracted.",
        equations_summary=equations_summary,
    )

    logger.info("Planning notebook for: %s", metadata.get("title", "Unknown"))

    client = get_client()

    response = await client.chat.completions.create(
        model=_resolve_model_name(settings.PLANNING_MODEL),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a notebook planning assistant. Analyze the paper "
                    "and return a JSON plan. Return ONLY valid JSON, no markdown."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=2000,
    )

    content = response.choices[0].message.content or "{}"

    # Parse JSON from response (handle potential markdown wrapping)
    content = content.strip()
    if content.startswith("```"):
        # Strip markdown code block
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])

    try:
        plan = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse notebook plan JSON, using fallback")
        plan = _fallback_plan(metadata, sections)

    plan = _apply_plan_limits(plan)

    logger.info("Notebook plan: %d cells", len(plan.get("cells", [])))
    return plan


def _is_low_value_section(section_ref: str, purpose: str) -> bool:
    """Heuristic for sections that can be merged into summaries."""
    text = f"{section_ref} {purpose}".lower()
    low_value_tokens = (
        "related work",
        "background",
        "appendix",
        "supplementary",
        "limitations",
        "future work",
    )
    return any(token in text for token in low_value_tokens)


def _apply_plan_limits(plan: dict[str, Any]) -> dict[str, Any]:
    """Cap notebook size and merge overflow into one markdown summary."""
    cells = plan.get("cells") or []
    if not isinstance(cells, list):
        plan["cells"] = []
        return plan

    max_cells = max(4, settings.MAX_NOTEBOOK_CELLS)
    max_code_cells = max(2, settings.MAX_NOTEBOOK_CODE_CELLS)

    limited: list[dict[str, Any]] = []
    dropped_sections: list[str] = []
    code_count = 0

    for cell in cells:
        if not isinstance(cell, dict):
            continue

        cell_type = str(cell.get("cell_type", "markdown")).lower()
        purpose = str(cell.get("purpose", "")).strip()
        section_ref = str(cell.get("section_ref") or "").strip()

        if cell_type == "code":
            if code_count >= max_code_cells:
                if section_ref:
                    dropped_sections.append(section_ref)
                continue
            code_count += 1

        if len(limited) >= max_cells:
            if section_ref:
                dropped_sections.append(section_ref)
            continue

        limited.append(cell)

    if len(limited) < len(cells):
        for cell in cells:
            if not isinstance(cell, dict):
                continue
            if cell in limited:
                continue
            section_ref = str(cell.get("section_ref") or "").strip()
            purpose = str(cell.get("purpose", "")).strip()
            if section_ref and _is_low_value_section(section_ref, purpose):
                dropped_sections.append(section_ref)

    unique_dropped: list[str] = []
    for section in dropped_sections:
        if section and section not in unique_dropped:
            unique_dropped.append(section)

    if unique_dropped:
        summary_cell = {
            "cell_type": "markdown",
            "purpose": (
                "Condensed summary for lower-priority sections merged to keep the "
                f"notebook concise: {', '.join(unique_dropped[:8])}"
            ),
            "section_ref": None,
        }

        if len(limited) < max_cells:
            limited.append(summary_cell)
        else:
            replace_idx = next(
                (i for i in range(len(limited) - 1, -1, -1)
                 if str(limited[i].get("cell_type", "markdown")).lower() == "markdown"),
                len(limited) - 1,
            )
            limited[replace_idx] = summary_cell

    if not limited:
        limited = _fallback_plan({}, []).get("cells", [])[:max_cells]

    plan["cells"] = limited
    return plan


def _fallback_plan(
    metadata: dict[str, Any], sections: list[dict[str, Any]]
) -> dict[str, Any]:
    """Generate a basic fallback plan if LLM response parsing fails."""
    cells = [
        {
            "cell_type": "markdown",
            "purpose": "Header with paper title, authors, and metadata",
            "section_ref": None,
        },
        {
            "cell_type": "code",
            "purpose": "Setup: install dependencies, imports, random seeds, device config",
            "section_ref": None,
        },
    ]

    for section in sections:
        title = section.get("title", "").lower()
        # Markdown for abstract/intro/conclusion, code for methodology/experiments
        if any(kw in title for kw in ("abstract", "introduction", "conclusion", "related")):
            cells.append({
                "cell_type": "markdown",
                "purpose": f"Overview of {section['title']}",
                "section_ref": section["title"],
            })
        else:
            cells.append({
                "cell_type": "markdown",
                "purpose": f"Description of {section['title']}",
                "section_ref": section["title"],
            })
            cells.append({
                "cell_type": "code",
                "purpose": f"Implementation of {section['title']}",
                "section_ref": section["title"],
            })

    cells.append({
        "cell_type": "markdown",
        "purpose": "Conclusion and next steps",
        "section_ref": None,
    })

    return {
        "title": metadata.get("title", "Paper Implementation"),
        "summary": "Jupyter notebook implementing key components from the paper.",
        "framework": "pytorch",
        "dependencies": ["torch", "numpy", "matplotlib", "seaborn"],
        "cells": cells,
    }
