"""Prompt templates for code generation and notebook planning."""

PLAN_NOTEBOOK_PROMPT = """\
You are analyzing a research paper to plan a Jupyter notebook implementation.

## Paper Information
**Title**: {title}
**Abstract**: {abstract}

## Extracted Sections
{sections_summary}

## Extracted Equations
{equations_summary}

## Instructions
Create a structured notebook plan. Decide:
1. Which sections to implement as code (focus on methodology, algorithms, experiments)
2. Which sections to describe in markdown (abstract, introduction, conclusion)
3. What dependencies are needed
4. What ML framework to use (default: PyTorch)
5. How to make the notebook interactive and pedagogical for learning

Plan requirements:
- Keep the notebook concise and high-signal.
- Include at least one interactive exploration cell (parameter sweep, comparison, or ablation).
- Include at least one visualization-heavy analysis cell.
- Include at least one "Try This" experiment cell for learners.
- Prefer compact, runnable examples over full-scale training pipelines.

Return a JSON object with this structure:
{{
    "title": "notebook title",
    "summary": "brief description",
    "framework": "pytorch",
    "dependencies": ["torch", "numpy", ...],
    "cells": [
        {{"cell_type": "markdown", "purpose": "Header with paper title and metadata", "section_ref": null}},
        {{"cell_type": "code", "purpose": "Setup: imports and random seeds", "section_ref": null}},
        {{"cell_type": "markdown", "purpose": "Abstract and paper overview", "section_ref": "abstract"}},
        {{"cell_type": "code", "purpose": "Implement core model architecture", "section_ref": "methodology"}},
        {{"cell_type": "code", "purpose": "Interactive experiment: modify key hyperparameters and compare outcomes", "section_ref": "experiments"}},
        {{"cell_type": "markdown", "purpose": "Learning recap and key takeaways", "section_ref": null}},
        ...
    ]
}}
"""

GENERATE_CODE_PROMPT = """\
You are implementing a section of a research paper in PyTorch.

## Paper Title
{title}

## Section: {section_title}
{section_content}

## Relevant Equations
{equations}

## Previously Generated Code Context
{previous_code_context}

## Cell Purpose
{cell_purpose}

## Requirements
1. Generate clean, runnable PyTorch code
2. Scale down model dimensions for CPU execution (e.g., 64 hidden dims instead of 512)
3. Include all necessary imports at the top of the cell
4. Add clear comments explaining the implementation
5. Implement equations from the paper accurately
6. Use modern PyTorch conventions (nn.Module, etc.)
7. Make code self-contained and executable in Jupyter
8. Include sample data generation if needed
9. Add matplotlib/seaborn visualizations where appropriate
10. Add a compact `config` dict for key hyperparameters so users can tweak behavior quickly
11. Include a short "Try this" section in comments with 2-3 learner-friendly parameter changes
12. Keep heavy training loops short by default (few epochs / tiny synthetic data)

## Output
Return ONLY the Python code. No markdown formatting, no triple backticks. \
Just pure Python code that can be directly placed in a Jupyter code cell.
"""

GENERATE_MARKDOWN_PROMPT = """\
You are creating a markdown cell for a Jupyter notebook implementing a research paper.

## Paper Title
{title}

## Section: {section_title}
{section_content}

## Relevant Equations
{equations}

## Cell Purpose
{cell_purpose}

## Requirements
1. Write clear, well-formatted markdown
2. Include relevant LaTeX equations using $...$ for inline and $$...$$ for display
3. Keep it concise but informative
4. Use headers (##, ###) for structure
5. Reference the paper's key contributions in this section
6. Add a short "What to observe" subsection to guide learner attention
7. End with a one-line checkpoint question when suitable

## Output
Return ONLY the markdown content. No code blocks wrapping it.
"""
