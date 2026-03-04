# NoteBrew — Coding Conventions

Consistent coding conventions are essential for maintaining code quality and enabling collaboration. This guide defines the coding standards for the NoteBrew project.

---

## Table of Contents

- [General Principles](#general-principles)
- [Python Backend Conventions](#python-backend-conventions)
- [TypeScript Frontend Conventions](#typescript-frontend-conventions)
- [Project Structure](#project-structure)
- [API Design](#api-design)
- [Documentation Standards](#documentation-standards)
- [Testing Conventions](#testing-conventions)
- [Git Workflow](#git-workflow)

---

## General Principles

### Code Quality First

- **Readability over cleverness**: Write code that others can understand
- **Explicit is better than implicit**: Make intentions clear
- **Consistency**: Follow existing patterns in the codebase
- **DRY (Don't Repeat Yourself)**: Extract reusable logic
- **YAGNI (You Aren't Gonna Need It)**: Don't add unnecessary features

### Performance Considerations

- Optimize only when necessary (measure first)
- Consider memory usage for large PDFs
- Use `async`/`await` for I/O operations
- Cache expensive operations when appropriate

### Error Handling

- Never silently swallow exceptions
- Provide meaningful error messages with context
- Use custom exception classes for domain errors
- Log errors with enough detail to debug

### Dependency Management

- **Always use the latest stable versions** of all dependencies — no deprecated or outdated packages
- **Pin exact versions** in `requirements.txt` and `package.json` for reproducibility
- **Periodically audit** dependencies for newer releases and compatibility
- **No legacy systems** — if a library is deprecated, replace it with the modern alternative
- Before adding a new dependency, check: is it actively maintained? When was the last release?

---

## Python Backend Conventions

### Style & Formatting

- **Formatter**: [Black](https://github.com/psf/black) with default settings (line length 88)
- **Linter**: [Ruff](https://github.com/astral-sh/ruff) for fast, comprehensive linting
- **Type Hints**: Required for all function signatures

```python
# ✅ Good
def parse_pdf(file_path: Path, max_pages: int = 50) -> PaperStructure:
    """Parse a PDF file and return structured paper data."""
    ...

# ❌ Bad
def parse_pdf(file_path, max_pages=50):
    ...
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Variables & functions | `snake_case` | `extract_equations()` |
| Classes | `PascalCase` | `CodeGenerator` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_FILE_SIZE_MB` |
| Private methods | `_leading_underscore` | `_create_prompt()` |
| Modules | `snake_case` | `pdf_parser.py` |

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def generate_code(section: PaperSection, context: str) -> GeneratedCode:
    """Generate PyTorch code for a paper section.

    Args:
        section: The parsed paper section to generate code for.
        context: Full paper context for coherent generation.

    Returns:
        GeneratedCode object containing code blocks and metadata.

    Raises:
        LLMError: If the language model fails after all retries.
        ValidationError: If generated code fails syntax checks.
    """
```

### Imports

Order imports in three groups separated by blank lines:

```python
# 1. Standard library
import os
from pathlib import Path

# 2. Third-party
from fastapi import FastAPI
from pydantic import BaseModel

# 3. Local
from app.config import settings
from app.models import PaperStructure
```

### Async Patterns

- Use `async def` for I/O-bound operations (API calls, file I/O)
- Use synchronous functions for CPU-bound work
- Never block the event loop with synchronous calls in async contexts

```python
# ✅ Good - async for I/O
async def call_llm(prompt: str) -> str:
    response = await client.chat.completions.create(...)
    return response.choices[0].message.content

# ✅ Good - sync for CPU-bound
def extract_equations(text: str) -> list[str]:
    return re.findall(EQUATION_PATTERN, text)
```

### Pydantic Models

- Use `BaseModel` for all data transfer objects
- Add `Field()` descriptions for API-facing models
- Use validators for complex validation logic

```python
class PaperSection(BaseModel):
    """A section extracted from a research paper."""

    title: str = Field(..., description="Section title (e.g., 'Abstract')")
    content: str = Field(..., description="Full section text content")
    equations: list[str] = Field(default_factory=list, description="LaTeX equations found")
```

---

## TypeScript Frontend Conventions

### Style & Formatting

- **Formatter**: [Prettier](https://prettier.io/) with single quotes, no semicolons, 2-space indent
- **Linter**: [ESLint](https://eslint.org/) with Next.js recommended rules
- **Strict mode**: `"strict": true` in `tsconfig.json`

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Variables & functions | `camelCase` | `handleUpload()` |
| Components | `PascalCase` | `UploadPanel` |
| Constants | `UPPER_SNAKE_CASE` | `API_BASE_URL` |
| Types & interfaces | `PascalCase` | `NotebookResponse` |
| Files (components) | `PascalCase.tsx` | `UploadPanel.tsx` |
| Files (utilities) | `camelCase.ts` | `apiClient.ts` |

### Component Structure

```tsx
// 1. Imports
import { useState } from 'react'
import { Upload } from 'lucide-react'

// 2. Types
interface UploadPanelProps {
  onUpload: (file: File) => Promise<void>
  disabled?: boolean
}

// 3. Component
export function UploadPanel({ onUpload, disabled = false }: UploadPanelProps) {
  // Hooks first
  const [file, setFile] = useState<File | null>(null)

  // Handlers
  const handleSubmit = async () => { ... }

  // Render
  return (...)
}
```

### State Management

- Use React hooks (`useState`, `useReducer`) for local state
- Lift state up only when needed
- Extract complex logic into custom hooks (`useNotebookGeneration`, `usePolling`)

---

## Project Structure

```
notebrew/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI entry point
│   │   ├── config.py          # Settings & environment
│   │   ├── models.py          # Pydantic data models
│   │   ├── agent/             # AI Agent system
│   │   │   ├── orchestrator.py
│   │   │   ├── tools/         # Agent tools (Gemini Vision PDF, code gen, etc.)
│   │   │   └── prompts/       # Prompt templates
│   │   ├── parsers/           # PDF parsing (Gemini Vision + PyMuPDF4LLM)
│   │   └── generators/        # Notebook generation
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js pages
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom hooks
│   │   └── lib/               # Utilities & API
│   └── package.json
├── docs/                       # Extended documentation
├── CODING_CONVENTIONS.md
├── CONTRIBUTING.md
├── README.md
└── LICENSE
```

### File Organization Rules

- **One class per file** in the backend (except small related classes)
- **One component per file** in the frontend
- **Co-locate tests** with source in `tests/` directory mirroring `app/` structure
- **Keep files under 300 lines** — split if exceeding

---

## API Design

### REST Endpoints

- Use **kebab-case** for URL paths: `/api/upload-pdf`
- Use **HTTP methods** semantically: `GET` (read), `POST` (create), `DELETE` (remove)
- Return consistent response shapes

### Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

Error responses:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "PARSING_FAILED",
    "message": "Failed to parse PDF: file is password protected"
  }
}
```

### Status Codes

| Code | Usage |
|------|-------|
| `200` | Successful response |
| `201` | Resource created (e.g., task started) |
| `400` | Client error (bad input) |
| `404` | Resource not found |
| `422` | Validation error |
| `500` | Internal server error |

---

## Documentation Standards

### Code Documentation

- All public functions MUST have docstrings
- Complex logic SHOULD have inline comments explaining *why*, not *what*
- Module-level docstrings for files with non-obvious purpose

### README Updates

- Update README when adding new features or changing setup steps
- Include screenshots/GIFs for UI changes
- Keep the Quick Start section current

### Changelog

- Follow [Keep a Changelog](https://keepachangelog.com/) format
- Update with every PR that changes user-facing behavior

---

## Testing Conventions

### Backend (pytest)

- Test file naming: `test_<module>.py`
- Use fixtures for shared setup
- Aim for ≥80% coverage on core logic (agent, parsers, generators)

```python
# tests/test_pdf_parser.py

def test_extract_equations_finds_inline_latex():
    parser = PDFParser("fixtures/sample_paper.pdf")
    equations = parser.extract_latex_equations()
    assert len(equations) > 0
    assert any("\\frac" in eq for eq in equations)
```

### Frontend (Jest + Testing Library)

- Test file naming: `ComponentName.test.tsx`
- Test user interactions, not implementation details
- Mock API calls in component tests

### What to Test

| Priority | What | Example |
|----------|------|---------|
| **Must** | Agent tool execution | Code generation, PDF parsing |
| **Must** | API endpoints | Upload, status, download |
| **Should** | Component interactions | File upload, progress display |
| **Nice** | Edge cases | Corrupt PDFs, timeout handling |

---

## Git Workflow

### Branch Naming

```
feature/<description>     # New features
fix/<description>         # Bug fixes
docs/<description>        # Documentation only
refactor/<description>    # Code refactoring
test/<description>        # Adding tests
```

Examples: `feature/docling-parser`, `fix/arxiv-download-timeout`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

<optional body>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

```bash
# ✅ Good
feat(agent): add code validation tool with syntax checking
fix(parser): handle multi-column PDF layouts correctly
docs(readme): update quick start with setup instructions

# ❌ Bad
fixed stuff
update
WIP
```

### Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Write a clear description of *what* and *why*
- Reference related issues
- Ensure all tests pass before requesting review
- Squash commits when merging

---

*Last updated: March 2026*
