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
2. **Gemini Vision over Docling** — Cloud-based vision parsing, zero GPU needed, best accuracy
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
| Docling slow + heavy | Deep learning models, GPU needed, Pydantic conflicts | Replaced with Gemini Vision + PyMuPDF4LLM hybrid |
| shadcn init failed | No `next.config.mjs` for framework detection | Created `next.config.mjs` |
| `@tailwind` lint warnings | IDE CSS validator doesn't understand Tailwind directives | False positives — works at build time with PostCSS |

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
- ⚠️ End-to-end notebook generation needs testing with different papers
- ⚠️ Colab/Kaggle deep-links need backend endpoint for file hosting
