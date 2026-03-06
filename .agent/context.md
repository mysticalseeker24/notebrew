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
- **Backend Version**: `2.2.0` (read from `./VERSION`)
- **Frontend Version**: `2.0.0` (read from `frontend/package.json`)
- **License**: MIT
- **Author**: Saksham Mishra (@mysticalseeker24)
- **Current AI Agent**: Gemini 3.1 Pro

## Architecture

```
User → Frontend (Next.js 14, port 3000) → FastAPI REST API (port 8001) → Agent Orchestrator
        │                                                                    │
        └── 3 pages: /, /features, /brew/[id]                               │
                                                                    ┌────────┴────────┐
                                                                    │  Tool Registry   │
                                                                    └────────┬────────┘
                                                                             │
                      ┌──────────┬──────────┬──────────┬──────────┬──────────┐
                parse_pdf  parse_arxiv  plan_notebook  generate_code  validate_code  assemble_notebook
                (Gemini    (arxiv lib)  (LLM plan)     (LLM gen)      (ast.parse)    (nbformat)
                 Vision +
                 PyMuPDF
                 fallback)
```

- **Agent loop**: Orchestrator sends conversation + tool schemas to LLM → LLM returns tool calls → execute → append results → loop
- **No frameworks**: Custom agent, no LangChain/LangGraph
- **LLM access**: OpenRouter API (OpenAI SDK with custom `base_url`)

## Backend Architecture

### API Routes (`main.py`, port 8001)

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Root — returns welcome message + version |
| `GET` | `/health` | Health check — returns `{"status": "healthy"}` |
| `POST` | `/api/upload-pdf` | Upload PDF → creates background task → returns `task_id` |
| `POST` | `/api/arxiv` | Submit arXiv URL/ID → creates background task → returns `task_id` |
| `GET` | `/api/status/{task_id}` | Poll task progress (`status`, `progress`, `message`, `current_tool`) |
| `GET` | `/api/download/{task_id}` | Download generated `.ipynb` file |

Docs: `http://localhost:8001/docs` (Swagger UI)

### Agent Orchestrator (`orchestrator.py`)

The `AgentOrchestrator` class implements the core tool-calling loop:

```
1. Build system prompt + user task description
2. Send messages + tool schemas to LLM (Gemini 3 Flash Preview via OpenRouter)
3. If LLM returns tool_calls:
   a. Execute each tool via ToolRegistry
   b. Append tool results to message history
   c. Emit progress callback (status, progress %, message)
   d. Loop back to step 2
4. If LLM returns text (no tool_calls): agent is done
5. Max iterations: 15 (configurable AGENT_MAX_ITERATIONS)
```

**Retry & fallback logic** (`_call_llm`):
- On API error → retry up to `AGENT_MAX_RETRIES` (default: 3)
- If primary model fails all retries → fall back to `FALLBACK_MODEL` (MiniMax M2.5)
- `finish_reason=length` handling → truncation recovery with increased `max_tokens` (16384)

**Key methods**:
- `run(task_description, state)` → main loop
- `_call_llm(messages, tools)` → single LLM call with retry
- `_update_state_from_tool(state, result)` → mutates `AgentState` based on tool output
- `_assistant_msg_to_dict(msg)` → serializes OpenAI response objects

### Agent Tools (6 tools)

| Tool | File | What It Does | LLM/API Used |
|------|------|-------------|-------------|
| `parse_pdf` | `tools/parse_pdf.py` | Hybrid PDF parsing (see below) | Gemini Vision + PyMuPDF4LLM |
| `parse_arxiv` | `tools/parse_arxiv.py` | Downloads paper from arXiv, then calls `parse_pdf` | `arxiv` library |
| `plan_notebook` | `tools/plan_notebook.py` | Plans notebook structure (cells, sections, framework) | Primary LLM |
| `generate_code` | `tools/generate_code.py` | Generates PyTorch code for a specific cell | Primary LLM |
| `validate_code` | `tools/validate_code.py` | `ast.parse()` syntax check + import validation | Local (no LLM) |
| `assemble_notebook` | `tools/assemble_notebook.py` | Builds `.ipynb` with nbformat | Local (no LLM) |

Each tool exports: `TOOL_SCHEMA` (OpenAI function format) + `execute(**kwargs)` async function.

### Hybrid PDF Parser (`parse_pdf.py`, Approach B)

```
PDF File
  ├── Gemini 3 Flash Vision (primary)
  │   ├── Sends base64 PDF pages as images via OpenRouter multimodal API
  │   ├── Structured JSON prompt extracts:
  │   │   ├── metadata (title, authors, abstract)
  │   │   ├── sections[] (title, content, equations, tables, figures)
  │   │   ├── equations[] (all LaTeX)
  │   │   └── references[]
  │   ├── max_tokens=32768, timeout=120s
  │   └── Falls back to PyMuPDF4LLM on failure
  │
  └── PyMuPDF4LLM (always runs)
      ├── Extracts full_text (markdown format)
      ├── Zero cost, offline, fast
      ├── Uses pymupdf-layout for enhanced layout analysis
      └── Result merged into PaperStructure.full_text
```

### Pydantic Data Models (`models.py`)

| Model | Purpose |
|-------|---------|
| `ProcessingStatus` | Enum: pending → parsing_pdf → planning → generating_code → validating_code → assembling_notebook → completed/failed |
| `ArxivRequest` | API input: `arxiv_url`, optional `model` |
| `NotebookResponse` | API output: `task_id`, `status`, `notebook_url`, `colab_url`, `error` |
| `ProgressUpdate` | Polling response: `progress` (0-100), `message`, `current_tool` |
| `PaperSection` | Extracted section: `title`, `content`, `equations[]`, `tables[]`, `figures[]` |
| `PaperMetadata` | Paper info: `title`, `authors`, `abstract`, `arxiv_id`, `num_pages` |
| `PaperStructure` | Complete paper: `metadata`, `full_text`, `sections[]`, `equations[]` |
| `NotebookCellPlan` | Planned cell: `cell_type` (markdown/code), `purpose`, `section_ref` |
| `NotebookPlan` | Full plan: `title`, `summary`, `framework`, `cells[]`, `dependencies[]` |
| `ToolCall` | LLM tool request: `id`, `name`, `arguments` |
| `ToolResult` | Tool response: `tool_call_id`, `name`, `success`, `result`, `error` |
| `AgentMessage` | Conversation message: `role`, `content`, `tool_calls[]` |
| `AgentState` | Agent runtime: `paper_structure`, `notebook_plan`, `generated_cells[]`, `notebook_path`, `status` |

All models use `ConfigDict(protected_namespaces=())` for Pydantic v2 compatibility.

### Configuration (`config.py`)

Settings loaded via `pydantic-settings` from `.env` file (with `extra="ignore"` for forward-compat).

Key settings groups:
- **API Keys**: `OPENROUTER_API_KEY` (required)
- **Models**: `PRIMARY_MODEL`, `FALLBACK_MODEL`, `GEMINI_3_FLASH_MODEL`, `MINIMAX_M25_MODEL`
- **Server**: `HOST`, `PORT` (8001), `DEBUG`
- **Upload**: `MAX_FILE_SIZE_MB` (50), `UPLOAD_DIR`, `OUTPUT_DIR`
- **Agent**: `AGENT_MAX_ITERATIONS` (15), `AGENT_MAX_RETRIES` (3), `AGENT_TOOL_TIMEOUT` (120s)
- **PDF Parser**: `PDF_PARSER_PRIMARY` (gemini_vision), `PDF_PARSER_TIMEOUT` (120s), `PDF_MAX_SIZE_MB` (20)
- **Notebook**: `NOTEBOOK_TIMEOUT` (300s), `MAX_CONTEXT_TOKENS` (100000)

### Dependencies (`requirements.txt`)

```
fastapi==0.135.1, uvicorn==0.41.0, pydantic==2.12.5, pydantic-settings==2.13.1
pymupdf4llm==0.3.4, pymupdf-layout==1.27.1
openai==2.24.0
nbformat==5.10.4, nbconvert==7.17.0
arxiv==2.4.0, requests==2.32.5
python-dotenv==1.2.2, aiofiles==25.1.0, python-multipart==0.0.22
```

### LLM Client (`llm_client.py`)

Singleton `get_client()` returns a shared `openai.OpenAI` instance configured with:
- `base_url`: `https://openrouter.ai/api/v1`
- `api_key`: from `OPENROUTER_API_KEY` env var
- Connection pooling for concurrent requests
## Tech Stack

| Layer    | Technology |
|----------|-----------|
| Backend  | Python 3.11+, FastAPI 0.135.1, Uvicorn 0.41.0, Pydantic 2.12.5 |
| Frontend | Next.js 14.2.0, TypeScript, Tailwind CSS 3.4, shadcn/ui, Framer Motion |
| Fonts    | Inter (sans), JetBrains Mono (mono), Space Grotesk (labels/buttons) |
| Design   | Cream Codex palette — warm cream (#FCEED1), apricot (#F7882F), blue (#1561AD) |
| PDF      | Gemini 3 Flash Vision (primary), PyMuPDF4LLM 0.3.4 (fallback) |
| LLM      | Gemini 3 Flash Preview (primary), MiniMax M2.5 (fallback) |
| LLM API  | OpenRouter via OpenAI SDK v2.24.0+ |
| Notebook | nbformat |
| Port     | Backend: **8001**, Frontend: **3000** |

## File Map

```
├── VERSION                        # Centralized backend version string
├── CODING_CONVENTIONS.md          # Code style guide
├── CONTRIBUTING.md                # Contribution guide
├── README.md                      # Project readme
├── backend/
│   ├── .env                       # Secrets (git-ignored)
│   ├── .env.example               # Template
│   ├── requirements.txt           # Python deps (pymupdf4llm, openai>=2.0.0, fastapi, etc.)
│   └── app/
│       ├── main.py                # FastAPI app, routes, agent runner
│       ├── config.py              # Pydantic settings (SettingsConfigDict, extra="ignore")
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
├── frontend/
│   ├── package.json               # v2.0.0 — shadcn, framer-motion, lucide-react, axios
│   ├── components.json            # shadcn configuration (new-york style, Radix-based)
│   ├── tailwind.config.ts         # Cream Codex colors via CSS vars, font families
│   ├── postcss.config.js          # Tailwind + Autoprefixer
│   ├── next.config.mjs            # Next.js config
│   └── src/
│       ├── app/
│       │   ├── page.tsx           # Landing page (Hero + UploadCard)
│       │   ├── layout.tsx         # Root layout — 3 Google Fonts, SEO metadata
│       │   ├── globals.css        # Cream Codex CSS variables + custom animations
│       │   ├── features/page.tsx  # Features page (HowItWorks + AI Stack + Output detail cards)
│       │   └── brew/[id]/page.tsx # Brew page — progress timeline → results → error states
│       ├── components/
│       │   ├── Navbar.tsx         # Fixed frosted-glass navbar, "NoteBrew ☕" branding
│       │   ├── Hero.tsx           # Full-viewport animated hero with blue accent title
│       │   ├── UploadCard.tsx     # Tabbed (PDF upload / arXiv URL) with drag-and-drop
│       │   ├── HowItWorks.tsx     # 6 step cards in responsive 3-col grid
│       │   ├── ScrollReveal.tsx   # Reusable Framer Motion scroll-reveal wrapper
│       │   ├── Footer.tsx         # Minimal footer (version, author, GitHub)
│       │   └── ui/               # shadcn components (tabs, card, progress, button)
│       └── lib/
│           ├── api.ts             # API client (port 8001, upload, status, download)
│           └── utils.ts           # shadcn utility (cn function)
└── .agent/
    ├── context.md                 # This file — project memory
    ├── notes.md                   # Personal agent notes (git-ignored)
    └── workflows/
        └── dev.md                 # Dev workflow (/dev command)
```

## Frontend Architecture

### Pages & Routing

| Route | Page | Description |
|-------|------|-------------|
| `/` | Landing | Hero section + tabbed UploadCard (PDF/arXiv) |
| `/features` | Features | HowItWorks (6 steps) + AI Stack + Notebook Output cards |
| `/brew/[id]` | Brew | Progress → Completed → Failed (state-driven, same URL) |

### Design System — Cream Codex

```css
--background: #FCEED1    /* warm cream page */
--card: #F0E2C8          /* card surfaces */
--accent-primary: #1561AD /* trustworthy blue (CTAs) */
--accent-warm: #F7882F    /* apricot (brew theme, highlights) */
--success: #7EBC59        /* eco green */
--border: #D4C9B5         /* warm gray borders */
--text-heading: #202020   /* rich black */
--text-body: #3F3F3F      /* dark gray */
--text-muted: #707070     /* secondary */
```

### Component Library

Uses **shadcn/ui** (Radix-based, Tailwind-native, copy-paste components):
- `tabs.tsx`, `card.tsx`, `progress.tsx`, `button.tsx`
- Themed with CSS variables to match Cream Codex palette

### Animations (Framer Motion)

- Hero: fade-up + scale spring (0.8s)
- ScrollReveal: fade-up on scroll-into-view (0.6s, staggered)
- Brew button: spinning ☕ during loading
- Progress: apricot shimmer sweep
- Step timeline: checked/spinning/pending states
- Completion: scale bounce + 🎉

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
PDF_PARSER_TIMEOUT=120
PDF_MAX_SIZE_MB=20
PDF_VISION_MODEL=google/gemini-3-flash-preview
```

## Key Design Decisions

1. **Custom agent over LangGraph** — More control, no framework lock-in, lighter weight
2. **Gemini Vision** — Cloud-based vision parsing, zero GPU needed, best accuracy
3. **PyMuPDF4LLM fallback** — Lightweight offline fallback when API unavailable or PDF too large
4. **Shared LLM client** — Singleton `get_client()` in `llm_client.py` with connection pooling
5. **Base64 PDF passthrough** — PDFs sent to Gemini via OpenRouter multimodal API
6. **OpenRouter** — Unified API for multiple models (Gemini, MiniMax)
7. **shadcn/ui over custom components** — Accessible, Radix-based, Tailwind-native, zero vendor lock
8. **Cream Codex palette** — Research-appropriate warm cream tones, not dark mode for readability
9. **Framer Motion** — Lightweight animation lib, already bundled with Next.js
10. **Multi-page over SPA** — Separate routes for landing, features, brew for clean URL structure

## Known Issues & Past Debugging

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| `proxies` TypeError | openai 1.54 + httpx 0.28 incompatibility | Upgraded to openai>=2.0.0 |
| 401 Missing Auth | Stale `OPENROUTER_API_KEY` env var overriding `.env` | Clear env var: `Remove-Item Env:OPENROUTER_API_KEY` |
| `finish_reason=length` loop | max_tokens=4096 too small for tool calls | Increased to 16384, added truncation recovery |
| Pydantic `class Config` deprecation | Old v1 syntax | Use `model_config = SettingsConfigDict(...)` |

| shadcn init failed | No `next.config.mjs` for framework detection | Created `next.config.mjs` |
| `@tailwind` lint warnings | IDE CSS validator doesn't understand Tailwind directives | False positives — works at build time with PostCSS |
| Brew timeline showed weak step accuracy | Backend status callback did not include active `current_tool` | Added tool-aware telemetry in orchestrator + status response |
| arXiv tasks could lose parser state context | Orchestrator only mapped `parse_pdf` to `paper_structure` | Added `parse_arxiv` state propagation in orchestrator |
| Colab/Kaggle actions were generic links | Frontend hardcoded home URLs without generated artifact context | Backend now returns link metadata and frontend consumes it |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| Backend 2.2.0 | Mar 2026 | Hybrid PDF parser (Gemini Vision + PyMuPDF4LLM), all deps latest |
| Frontend 2.0.0 | Mar 2026 | Complete redesign: Cream Codex, shadcn/ui, 3 pages, Framer Motion |
| Backend 2.1.0 | Mar 2026 | Batch PDF processing, parallel analysis |
| Backend 2.0.0 | Mar 2026 | Pydantic v2 migration, config overhaul |

## Current Status

- ✅ Backend runs on port 8001 (v2.2.0)
- ✅ All 6 agent tools registered and tested
- ✅ Hybrid PDF parsing: Gemini Vision (structure) + PyMuPDF4LLM (full_text)
- ✅ Agent loop executes (tool calls, retries, fallback)
- ✅ Zero GPU requirements — all ML runs in the cloud
- ✅ All dependencies at latest stable versions (March 2026)
- ✅ Frontend v2.0.0 — Cream Codex + Immersive Editorial + shadcn/ui
- ✅ Three pages: Landing (/), Features (/features), Brew (/brew/[id])
- ✅ shadcn components: tabs, card, progress, button
- ✅ Google Fonts: Inter, JetBrains Mono, Space Grotesk
- ✅ Framer Motion animations: scroll-reveal, spring, shimmer
- ✅ All pushed to GitHub main branch
- ✅ Brew timeline telemetry now includes `current_tool` and `current_section`
- ✅ `parse_arxiv` now updates agent `paper_structure` state
- ✅ Metadata model expanded (`doi`, `references`, `key_contributions`, section `key_findings`)
- ✅ Reusable `FileDropzone` extracted and wired into `UploadCard`
- ✅ Frontend API error handling improved with backend detail passthrough
- ✅ Backend now emits launch-link metadata (`notebook_url`, `colab_url`, `kaggle_url`, `links_ready`)
- ⚠️ True direct Colab/Kaggle deep links require `PUBLIC_NOTEBOOK_BASE_URL` pointing to a public notebook host
- ✅ Backend validation should be run with `backend/venv` Python (`.\\venv\\Scripts\\python.exe` on Windows)
- ✅ Runtime check: backend launched from venv and `/health` returned registered tool list
- ✅ Phase 1 Step 1: model routing defaults updated to MiniMax 2.5 for orchestration, planning, and code generation (`ORCHESTRATION_MODEL`, `PLANNING_MODEL`, `CODEGEN_MODEL`)
- ✅ Phase 1 Step 2: notebook complexity caps added (`MAX_NOTEBOOK_CELLS`, `MAX_NOTEBOOK_CODE_CELLS`) with merged summary markdown cell for overflow low-priority sections
- ✅ Phase 1 Step 3: orchestrator budget guards added (`MAX_LLM_CALLS_PER_TASK`, `MAX_GENERATE_CODE_CALLS`, `MAX_RUNTIME_SECONDS`, `MAX_RETRY_PER_TOOL`) with explicit fail-fast status messages
- ✅ Phase 1 Step 4: deterministic orchestrator fanout added after planning (`generate_code` in parallel, bounded retries, code validation, then direct notebook assembly)
- ✅ Phase 1 Step 5: chunked PDF processing added for long documents (concurrent Gemini chunk extraction with merged sections/equations/references)
- ✅ Phase 1 Step 6: notebook quality prompts upgraded for interactivity and learning effectiveness (interactive experiment cells, learner checkpoints, compact tweakable config patterns)
