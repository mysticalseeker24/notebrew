# NoteBrew — Project Context

> **Purpose**: Persistent project context for AI assistants. Read this first when working on the NoteBrew codebase.

## ⚠️ Agent Behavior Rules

> [!CAUTION]
> **Mandatory for ALL AI agents / models / sessions working on this project.**

1. **Always read this file first** — Before doing anything, read `.agent/context.md` in full to understand the project state, architecture, known issues, and current status.
2. **Always ask before proceeding** — Never make code changes, refactors, or file modifications without explicitly asking the user for approval first. Present your plan, get a "go ahead", then execute.
3. **Context review on every new session** — When starting a new conversation or window, summarize what you've read from this file and confirm with the user before taking any action.
4. **No assumptions** — If something is unclear or missing from this context, ask the user rather than guessing.
5. **Update this file** — After completing work, update the "Current Status" section at the bottom of this file to reflect what changed.
6. **Use latest stable versions** — Always use the latest stable, non-deprecated versions of all dependencies. Check for updates before adding new packages. Pin exact versions in requirements files.

## Overview

**NoteBrew** converts research papers (PDF/arXiv) into executable Jupyter notebooks using a custom AI agent with tool-calling.

- **Repo**: `https://github.com/mysticalseeker24/notebrew.git`
- **Branch**: `main`
- **Version**: Read from `./VERSION` file
- **License**: MIT
- **Author**: Saksham Mishra (@mysticalseeker24)

## Architecture

```
User → Frontend (Next.js 14) → FastAPI REST API → Agent Orchestrator
        │                                              │
        └── (port 8001) ──────────────────────────────┘
                                                       │
                                              ┌────────┴────────┐
                                              │  Tool Registry   │
                                              └────────┬────────┘
                                                       │
                          ┌──────────┬──────────┬──────┴───┬──────────┬──────────┐
                    parse_pdf  parse_arxiv  plan_notebook  generate_code  validate_code  assemble_notebook
                    (Gemini    (arxiv lib)  (LLM plan)     (LLM gen)      (ast.parse)    (nbformat)
                     Vision +
                     PyMuPDF
                     fallback)
```

- **Agent loop**: Orchestrator sends conversation + tool schemas to LLM → LLM returns tool calls → execute → append results → loop
- **No frameworks**: Custom agent, no LangChain/LangGraph
- **LLM access**: OpenRouter API (OpenAI SDK with custom `base_url`)

## Tech Stack

| Layer    | Technology |
|----------|-----------|
| Backend  | Python 3.11+, FastAPI, Uvicorn |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| PDF      | Gemini 3 Flash Vision (primary), PyMuPDF4LLM (fallback) |
| LLM      | Gemini 3 Flash Preview (primary), MiniMax M2.5 (fallback) |
| LLM API  | OpenRouter via OpenAI SDK v2+ |
| Notebook | nbformat |
| Port     | **8001** (both backend default and frontend API target) |

## File Map

```
├── VERSION                        # Centralized version string
├── CODING_CONVENTIONS.md          # Code style guide
├── CONTRIBUTING.md                # Contribution guide
├── README.md                      # Project readme
├── backend/
│   ├── .env                       # Secrets (git-ignored)
│   ├── .env.example               # Template
│   ├── requirements.txt           # Python deps (pymupdf4llm, openai>=2.0.0, fastapi, etc.)
│   └── app/
│       ├── main.py                # FastAPI app, routes, agent runner
│       ├── config.py              # Pydantic settings (SettingsConfigDict)
│       ├── models.py              # All Pydantic models (ConfigDict, Field defaults)
│       ├── llm_client.py          # Shared OpenAI client singleton
│       └── agent/
│           ├── orchestrator.py    # Custom tool-calling loop
│           ├── tool_registry.py   # Tool schema + execution registry
│           ├── tools/
│           │   ├── parse_pdf.py   # Hybrid PDF parser (Gemini Vision + PyMuPDF4LLM fallback)
│           │   ├── parse_arxiv.py # arXiv download + parse
│           │   ├── plan_notebook.py
│           │   ├── generate_code.py
│           │   ├── validate_code.py
│           │   └── assemble_notebook.py
│           └── prompts/
│               ├── system.py      # Agent system prompt
│               └── templates.py   # Prompt templates
└── frontend/
    └── src/
        ├── app/page.tsx           # Main UI
        ├── app/layout.tsx         # SEO metadata
        └── lib/api.ts             # API client (port 8001)
```

## Environment Variables

```env
OPENROUTER_API_KEY=sk-or-v1-...   # Required
PRIMARY_MODEL=gemini-3-flash-preview
FALLBACK_MODEL=minimax-m2.5
HOST=0.0.0.0
PORT=8001
DEBUG=True
AGENT_MAX_ITERATIONS=15
AGENT_MAX_RETRIES=3
PDF_PARSER_PRIMARY=gemini_vision    # "gemini_vision" or "pymupdf"
PDF_PARSER_TIMEOUT=60
PDF_MAX_SIZE_MB=20
PDF_VISION_MODEL=google/gemini-3-flash-preview
```

## Key Design Decisions

1. **Custom agent over LangGraph** — More control, no framework lock-in, lighter weight
2. **Gemini Vision over Docling** — Cloud-based vision parsing, zero GPU needed, best accuracy
3. **PyMuPDF4LLM fallback** — Lightweight offline fallback when API unavailable or PDF too large
4. **Shared LLM client** — Singleton `get_client()` in `llm_client.py` with connection pooling
5. **Base64 PDF passthrough** — PDFs sent to Gemini via OpenRouter multimodal API
6. **OpenRouter** — Unified API for multiple models (Gemini, MiniMax)

## Known Issues & Past Debugging

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| `proxies` TypeError | openai 1.54 + httpx 0.28 incompatibility | Upgraded to openai>=2.0.0 |
| 401 Missing Auth | Stale `OPENROUTER_API_KEY` env var overriding `.env` | Clear env var: `Remove-Item Env:OPENROUTER_API_KEY` |
| `finish_reason=length` loop | max_tokens=4096 too small for tool calls | Increased to 16384, added truncation recovery |
| Pydantic `class Config` deprecation | Old v1 syntax | Use `model_config = SettingsConfigDict(...)` |
| Docling slow + heavy | Deep learning models, GPU needed, Pydantic conflicts | Replaced with Gemini Vision + PyMuPDF4LLM hybrid |

## Current Status

- ✅ Backend runs on port 8001 (v2.2.0)
- ✅ All 6 agent tools registered
- ✅ Hybrid PDF parsing: Gemini Vision (structure) + PyMuPDF4LLM (full_text)
- ✅ Agent loop executes (tool calls, retries, fallback)
- ✅ Zero GPU requirements — all ML runs in the cloud
- ✅ All dependencies at latest versions (March 2026)
- ✅ Frontend redesigned v2.0.0 — Cream Codex + Immersive Editorial
- ✅ shadcn/ui + Framer Motion + Google Fonts (Inter, JetBrains Mono, Space Grotesk)
- ✅ Three pages: Landing (/), Features (/features), Brew (/brew/[id])
- ✅ Pushed to GitHub main branch
- ⚠️ Frontend not tested (npm install needed)
- ⚠️ End-to-end notebook generation needs testing with different papers
