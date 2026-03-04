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
                    (Docling)  (arxiv lib)  (LLM plan)     (LLM gen)      (ast.parse)    (nbformat)
```

- **Agent loop**: Orchestrator sends conversation + tool schemas to LLM → LLM returns tool calls → execute → append results → loop
- **No frameworks**: Custom agent, no LangChain/LangGraph
- **LLM access**: OpenRouter API (OpenAI SDK with custom `base_url`)

## Tech Stack

| Layer    | Technology |
|----------|-----------|
| Backend  | Python 3.11+, FastAPI, Uvicorn |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| PDF      | Docling (IBM) — deep learning PDF parser |
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
│   ├── requirements.txt           # Python deps (docling, openai>=2.0.0, fastapi, etc.)
│   └── app/
│       ├── main.py                # FastAPI app, routes, agent runner
│       ├── config.py              # Pydantic settings (SettingsConfigDict)
│       ├── models.py              # All Pydantic models (ConfigDict, Field defaults)
│       ├── llm_client.py          # Shared OpenAI client singleton
│       └── agent/
│           ├── orchestrator.py    # Custom tool-calling loop
│           ├── tool_registry.py   # Tool schema + execution registry
│           ├── tools/
│           │   ├── parse_pdf.py   # Docling PDF parser (thread pool, batch)
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
DOCLING_OCR_ENABLED=True
DOCLING_EXTRACT_TABLES=True
```

## Key Design Decisions

1. **Custom agent over LangGraph** — More control, no framework lock-in, lighter weight
2. **Docling over PyMuPDF** — Deep learning parser handles complex layouts, tables, equations
3. **Shared LLM client** — Singleton `get_client()` in `llm_client.py` with connection pooling
4. **Thread pool for Docling** — `asyncio.to_thread()` prevents blocking the event loop
5. **Batch processing** — `ocr_batch_size=4`, `layout_batch_size=4`, `table_batch_size=4`
6. **OpenRouter** — Unified API for multiple models (Gemini, MiniMax)

## Known Issues & Past Debugging

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| `proxies` TypeError | openai 1.54 + httpx 0.28 incompatibility | Upgraded to openai>=2.0.0 |
| 401 Missing Auth | Stale `OPENROUTER_API_KEY` env var overriding `.env` | Clear env var: `Remove-Item Env:OPENROUTER_API_KEY` |
| `PdfPipelineOptions no attr backend` | Wrong Docling API: need `PdfFormatOption` wrapper | `format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=...)}` |
| `finish_reason=length` loop | max_tokens=4096 too small for tool calls | Increased to 16384, added truncation recovery |
| Pydantic `model_` warnings | Docling models use `model_spec` field name | `model_config = ConfigDict(protected_namespaces=())` |
| Pydantic `class Config` deprecation | Old v1 syntax | Use `model_config = SettingsConfigDict(...)` |

## Current Status

- ✅ Backend runs on port 8001
- ✅ All 6 agent tools registered
- ✅ Docling PDF parsing works (thread pool + batch)
- ✅ Agent loop executes (tool calls, retries, fallback)
- ⚠️ Frontend not tested (npm install needed)
- ⚠️ End-to-end notebook generation needs more testing with different papers
