"""Tool: validate_code — Validate generated Python code for correctness."""

from __future__ import annotations

import ast
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Tool schema for the agent
TOOL_SCHEMA = {
    "name": "validate_code",
    "description": (
        "Validate a Python code block for syntax errors and import issues. "
        "Returns validation results so the agent can fix errors before "
        "assembling the notebook."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to validate.",
            },
            "cell_index": {
                "type": "integer",
                "description": "Index of the cell in the notebook plan (for reference).",
            },
        },
        "required": ["code"],
    },
}


async def validate_code(code: str, cell_index: int = -1) -> dict[str, Any]:
    """Validate Python code for syntax and basic correctness.

    Performs:
    1. Syntax check via ast.parse
    2. Import statement analysis
    3. Basic structural checks

    Args:
        code: Python code string to validate.
        cell_index: Index of the cell for reference.

    Returns:
        Dict with is_valid, errors, warnings, and analysis info.
    """
    result: dict[str, Any] = {
        "cell_index": cell_index,
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "imports": [],
        "defined_names": [],
    }

    if not code or not code.strip():
        result["is_valid"] = False
        result["errors"].append("Empty code block.")
        return result

    # --- 1. Syntax Check ---
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        result["is_valid"] = False
        result["errors"].append(
            f"Syntax error at line {exc.lineno}: {exc.msg}"
        )
        return result

    # --- 2. Analyze imports ---
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    result["imports"] = imports

    # --- 3. Extract defined names (functions, classes, variables) ---
    defined_names: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            defined_names.append(f"function:{node.name}")
        elif isinstance(node, ast.ClassDef):
            defined_names.append(f"class:{node.name}")
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.append(f"var:{target.id}")
    result["defined_names"] = defined_names

    # --- 4. Basic quality checks ---
    # Warn about common issues
    if "import *" in code:
        result["warnings"].append(
            "Wildcard import detected — may cause namespace pollution."
        )

    if len(code.split("\n")) > 200:
        result["warnings"].append(
            "Code cell is very long (>200 lines). Consider splitting."
        )

    # Check for print statements vs proper logging
    lines = code.split("\n")
    print_count = sum(1 for line in lines if "print(" in line)
    if print_count > 10:
        result["warnings"].append(
            f"Many print statements ({print_count}). Consider using logging "
            "or reducing debug output."
        )

    logger.info(
        "Validated cell %d: valid=%s, %d errors, %d warnings",
        cell_index,
        result["is_valid"],
        len(result["errors"]),
        len(result["warnings"]),
    )

    return result
