"""Tool: assemble_notebook — Combine generated cells into a .ipynb file."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

from app.config import settings

logger = logging.getLogger(__name__)

# Tool schema for the agent
TOOL_SCHEMA = {
    "name": "assemble_notebook",
    "description": (
        "Assemble all generated cells (markdown and code) into a final "
        "Jupyter notebook (.ipynb) file. Adds a header, setup cell, Colab "
        "button, and conclusion. Saves to disk and returns the file path."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Notebook title (paper title).",
            },
            "authors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of paper authors.",
            },
            "cells": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "cell_type": {"type": "string"},
                        "content": {"type": "string"},
                    },
                },
                "description": "List of cells with cell_type and content.",
            },
            "dependencies": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of pip packages to install.",
            },
            "output_path": {
                "type": "string",
                "description": "Path to save the notebook. Auto-generated if not provided.",
            },
        },
        "required": ["title", "cells"],
    },
}


async def assemble_notebook(
    title: str,
    cells: list[dict[str, Any]],
    authors: list[str] | None = None,
    dependencies: list[str] | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Assemble generated cells into a Jupyter notebook.

    Creates a structured notebook with:
    - Header cell (title, authors, metadata)
    - Colab button
    - Setup cell (pip install + imports)
    - All generated cells
    - Conclusion cell

    Args:
        title: Paper/notebook title.
        cells: List of dicts with 'cell_type' and 'content'.
        authors: Paper author names.
        dependencies: pip packages to install.
        output_path: Where to save the .ipynb file.

    Returns:
        Dict with notebook_path, num_cells, and file_size.
    """
    nb = new_notebook()
    authors_list = authors or []
    deps = dependencies or ["torch", "numpy", "matplotlib"]

    # --- Header cell ---
    nb.cells.append(new_markdown_cell(_header_markdown(title, authors_list)))

    # --- Colab button ---
    nb.cells.append(new_markdown_cell(_colab_markdown()))

    # --- Setup cell ---
    nb.cells.append(new_code_cell(_setup_code(deps)))

    # --- Learning usage guide ---
    nb.cells.append(new_markdown_cell(_learning_guide_markdown()))

    # --- Generated cells ---
    for cell_data in cells:
        cell_type = cell_data.get("cell_type", "code")
        content = cell_data.get("content", "")

        if not content.strip():
            continue

        if cell_type == "markdown":
            nb.cells.append(new_markdown_cell(content))
        else:
            nb.cells.append(new_code_cell(content))

    # --- Conclusion cell ---
    nb.cells.append(new_markdown_cell(_conclusion_markdown()))

    # --- Save ---
    if output_path:
        save_path = Path(output_path)
    else:
        save_path = Path(settings.OUTPUT_DIR) / f"notebook_{datetime.now():%Y%m%d_%H%M%S}.ipynb"

    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    file_size = save_path.stat().st_size
    logger.info(
        "Assembled notebook: %s (%d cells, %.1f KB)",
        save_path.name,
        len(nb.cells),
        file_size / 1024,
    )

    return {
        "notebook_path": str(save_path),
        "num_cells": len(nb.cells),
        "file_size_bytes": file_size,
    }


def _header_markdown(title: str, authors: list[str]) -> str:
    """Generate the notebook header cell."""
    authors_str = ", ".join(authors) if authors else "Unknown Authors"
    return f"""# {title}

**Authors:** {authors_str}
**Generated:** {datetime.now():%Y-%m-%d %H:%M:%S}
**Tool:** [NoteBrew](https://github.com/mysticalseeker24/notebrew) — AI-powered paper-to-notebook conversion

---

## 📚 About This Notebook

This notebook was automatically generated from a research paper using NoteBrew's AI agent.
It contains:
- Paper overview and key concepts
- Runnable PyTorch implementations (scaled for CPU)
- Visualizations and analysis code

⚠️ **Note:** Model dimensions have been reduced for CPU execution. Scale up for production use.

---
"""


def _colab_markdown() -> str:
    """Generate the Colab button cell."""
    return """---

## 🚀 Open in Google Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/)

> Upload this notebook to Colab for GPU-accelerated execution.

---
"""


def _setup_code(dependencies: list[str]) -> str:
    """Generate the setup/installation code cell."""
    deps_str = " ".join(dependencies)
    return f"""# ═══════════════════════════════════════════════════
# Setup — Run this cell first!
# ═══════════════════════════════════════════════════

!pip install -q {deps_str}

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt

try:
    import ipywidgets as widgets
except Exception:
    widgets = None

from typing import List, Tuple, Optional

# Reproducibility
torch.manual_seed(42)
np.random.seed(42)

# Device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Using device: {{device}}')
print(f'PyTorch version: {{torch.__version__}}')

# Interactive defaults learners can tweak quickly in later cells
interactive_config = {
    "batch_size": 8,
    "learning_rate": 1e-3,
    "hidden_dim": 64,
    "epochs": 3,
}
print("Interactive config:", interactive_config)

if widgets is not None:
    print("ipywidgets available: sliders/interact can be used in this notebook.")
else:
    print("ipywidgets not installed: interactive cells can still run with manual config edits.")
"""


def _learning_guide_markdown() -> str:
    """Generate an onboarding cell to improve notebook learnability."""
    return """## How to Learn With This Notebook

Use this notebook as an interactive walkthrough, not just a script dump.

1. Run cells top-to-bottom once to establish baseline behavior.
2. Change values in `interactive_config` and rerun experiment cells.
3. Compare metrics/plots after each change and note what shifted.
4. Use the markdown checkpoint questions to verify understanding.

### Suggested First Experiments
- Halve and double `learning_rate`.
- Increase `hidden_dim` from 64 to 128.
- Increase `epochs` from 3 to 10 and observe overfitting signals.
"""


def _conclusion_markdown() -> str:
    """Generate the conclusion cell."""
    return """---

## 📝 Conclusion

This notebook implemented the key components from the research paper.

### Next Steps
1. 🔧 **Scale Up** — Increase model dimensions for better performance
2. 📊 **Full Dataset** — Replace synthetic data with real datasets
3. 🎯 **Hyperparameter Tuning** — Optimize learning rate, batch size, etc.
4. 🚀 **GPU Training** — Move to GPU for faster training
5. 📈 **Advanced Metrics** — Add more evaluation metrics

### References
- Original Paper: [Add link here]
- PyTorch Documentation: https://pytorch.org/docs/

---

**Generated by [NoteBrew](https://github.com/mysticalseeker24/notebrew)** | Made with ❤️ for the research community
"""
