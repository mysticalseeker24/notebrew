# Contributing to NoteBrew

Thank you for your interest in contributing to NoteBrew! This guide will help you get started.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Adding a New Agent Tool](#adding-a-new-agent-tool)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Code Style](#code-style)
- [Reporting Issues](#reporting-issues)
- [Community](#community)

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/notebrew.git
   cd notebrew
   ```
3. **Create a branch** for your contribution:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Backend

```bash
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run the server
python -m app.main
```

The API runs at `http://localhost:8000`. Docs are available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

The frontend runs at `http://localhost:3000`.

---

## How to Contribute

### 🐛 Fix Bugs

1. Check [open issues](https://github.com/mysticalseeker24/notebrew/issues) for bugs
2. Comment on the issue to claim it
3. Submit a PR with the fix

### ✨ Add Features

1. Open an issue describing the feature
2. Wait for maintainer approval
3. Implement and submit a PR

### 📝 Improve Documentation

- Fix typos, improve explanations, add examples
- No issue needed — just submit a PR

### 🧪 Add Tests

- Open `tests/` directory and add test files
- Follow the naming convention: `test_<module>.py`

---

## Adding a New Agent Tool

NoteBrew's agent system is designed to be easily extensible. Here's how to add a new tool:

### Step 1: Create the tool file

Create a new file in `backend/app/agent/tools/`:

```python
# backend/app/agent/tools/my_new_tool.py

"""Tool: my_new_tool — Description of what it does."""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Tool schema (OpenAI function-calling format)
TOOL_SCHEMA = {
    "name": "my_new_tool",
    "description": "What this tool does (the LLM reads this to decide when to use it).",
    "parameters": {
        "type": "object",
        "properties": {
            "input_param": {
                "type": "string",
                "description": "Description of this parameter.",
            },
        },
        "required": ["input_param"],
    },
}


async def my_new_tool(input_param: str) -> dict[str, Any]:
    """Implement the tool logic here.

    Args:
        input_param: Description.

    Returns:
        Dict with results.
    """
    logger.info("Running my_new_tool with: %s", input_param)
    # ... your implementation ...
    return {"result": "success"}
```

### Step 2: Register the tool

In `backend/app/main.py`, import and register your tool in the `_build_tool_registry()` function:

```python
from app.agent.tools import my_new_tool

# Inside _build_tool_registry():
registry.register(
    name="my_new_tool",
    description=my_new_tool.TOOL_SCHEMA["description"],
    parameters=my_new_tool.TOOL_SCHEMA["parameters"],
    handler=my_new_tool.my_new_tool,
)
```

### Step 3: Update the system prompt (if needed)

If the agent should know about your tool's workflow, update `backend/app/agent/prompts/system.py`.

---

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows the project's [coding conventions](CODING_CONVENTIONS.md)
- [ ] All existing tests pass
- [ ] New code has appropriate tests
- [ ] Documentation is updated if needed
- [ ] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)

### PR Description Template

```markdown
## What

Brief description of the change.

## Why

Why is this change needed?

## How

How was this implemented? Key design decisions?

## Testing

How was this tested?
```

### Review Process

1. A maintainer will review your PR within 48 hours
2. Address any feedback and push updates
3. Once approved, the PR will be squash-merged

---

## Code Style

Please follow the conventions in [CODING_CONVENTIONS.md](CODING_CONVENTIONS.md). Key points:

- **Python**: Black formatting, Ruff linting, type hints required
- **TypeScript**: Prettier formatting, ESLint, strict mode
- **Commits**: Conventional Commits format (`feat:`, `fix:`, `docs:`, etc.)

---

## Reporting Issues

When reporting a bug, please include:

1. **What happened** — describe the unexpected behavior
2. **What you expected** — describe the expected behavior
3. **Steps to reproduce** — minimal steps to reproduce the issue
4. **Environment** — OS, Python version, Node version, browser
5. **Logs** — relevant error messages or stack traces

Use the issue templates when available.

---

## Community

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Requests**: Code contributions

### Code of Conduct

Be respectful, constructive, and inclusive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).

---

*Thank you for helping make NoteBrew better! ☕*
