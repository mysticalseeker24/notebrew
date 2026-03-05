# NoteBrew ☕📓

**AI agent that brews research papers into executable Jupyter notebooks.**

NoteBrew uses a custom AI agent with tool-calling to intelligently parse research papers, plan notebook structure, generate PyTorch code, validate it, and assemble production-quality Jupyter notebooks.

![Version](https://img.shields.io/badge/version-2.2.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Node](https://img.shields.io/badge/node-18+-green)

---

## 🚀 Features

- **🤖 AI Agent Architecture** — Custom tool-calling agent that intelligently decides how to process each paper
- **📄 Hybrid PDF Parser** — Gemini 3 Flash Vision (primary) + PyMuPDF4LLM (fallback) for accurate extraction of text, equations, tables, figures, and references
- **🐍 PyTorch Code Generation** — Real ML implementations scaled for CPU execution
- **✅ Code Validation** — Validates generated code for syntax errors before assembly
- **🔗 arXiv Integration** — Direct support for arXiv papers via URL
- **📐 LaTeX Rendering** — Extracts and renders mathematical equations
- **☁️ Export Anywhere** — Download .ipynb, open in Google Colab, or launch in Kaggle
- **🔧 Extensible** — Easy to add new agent tools

## 🛠️ Tech Stack

### Backend
- **FastAPI** — High-performance Python web framework
- **Hybrid PDF Parser** — Gemini Vision (primary) + PyMuPDF4LLM (fallback)
- **Custom AI Agent** — Tool-calling loop with no framework dependency
- **Gemini 3 Flash Preview** — Frontier intelligence (1M context window)
- **MiniMax M2.5** — Cost-effective fallback model
- **OpenRouter** — Unified LLM API access
- **nbformat** — Jupyter notebook generation

### Frontend
- **Next.js 14** — React framework with App Router
- **TypeScript** — Type-safe development
- **shadcn/ui** — Accessible component library (Radix-based)
- **Framer Motion** — Scroll-reveal & spring animations
- **Tailwind CSS** — Utility-first styling (Cream Codex design system)
- **Google Fonts** — Inter, JetBrains Mono, Space Grotesk

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- OpenRouter API key ([Get one here](https://openrouter.ai))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/mysticalseeker24/notebrew.git
cd notebrew
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run server
python -m app.main
```

Backend runs at `http://localhost:8001` (API docs: `http://localhost:8001/docs`)

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs at `http://localhost:3000`

## 🤖 How It Works

NoteBrew uses a custom AI agent with tool-calling to process papers:

```
1. Upload PDF / arXiv URL
   ↓
2. Agent calls parse_pdf tool (Gemini Vision + PyMuPDF4LLM)
   → Extracts text, sections, equations, tables, figures, references
   ↓
3. Agent calls plan_notebook tool
   → Decides what to implement and how
   ↓
4. Agent calls generate_code tool (per cell)
   → Generates PyTorch code with context
   ↓
5. Agent calls validate_code tool
   → Checks for syntax errors, retries if needed
   ↓
6. Agent calls assemble_notebook tool
   → Creates structured .ipynb file
   ↓
7. Download notebook
```

### Agent Tools

| Tool | What It Does |
|------|-------------|
| `parse_pdf` | Parse PDF with Gemini Vision + PyMuPDF4LLM (text, equations, tables, figures, references) |
| `parse_arxiv` | Download from arXiv and parse |
| `plan_notebook` | Plan notebook structure based on paper content |
| `generate_code` | Generate Python/markdown cell content |
| `validate_code` | Validate code syntax and imports |
| `assemble_notebook` | Build the final .ipynb file |

## 📁 Project Structure

```
notebrew/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Settings & environment
│   │   ├── models.py                # Pydantic data models
│   │   └── agent/
│   │       ├── orchestrator.py      # Agent loop (tool-calling)
│   │       ├── tool_registry.py     # Tool management
│   │       ├── tools/
│   │       │   ├── parse_pdf.py     # Hybrid PDF parser (Gemini Vision + PyMuPDF4LLM)
│   │       │   ├── parse_arxiv.py   # arXiv downloader
│   │       │   ├── plan_notebook.py # Notebook planner
│   │       │   ├── generate_code.py # Code generator
│   │       │   ├── validate_code.py # Code validator
│   │       │   └── assemble_notebook.py # Notebook assembler
│   │       └── prompts/
│   │           ├── system.py        # Agent system prompt
│   │           └── templates.py     # Prompt templates
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # Landing page (hero + upload)
│   │   │   ├── layout.tsx            # Root layout + fonts
│   │   │   ├── globals.css           # Cream Codex design tokens
│   │   │   ├── features/page.tsx     # Features page
│   │   │   └── brew/[id]/page.tsx    # Brew progress + results page
│   │   ├── components/
│   │   │   ├── Navbar.tsx            # Fixed frosted-glass navbar
│   │   │   ├── Hero.tsx              # Animated hero section
│   │   │   ├── UploadCard.tsx        # PDF/arXiv tabbed upload
│   │   │   ├── HowItWorks.tsx        # 6-step feature cards
│   │   │   ├── ScrollReveal.tsx      # Scroll animation wrapper
│   │   │   ├── Footer.tsx            # Minimal footer
│   │   │   └── ui/                   # shadcn components
│   │   └── lib/                      # API client
│   └── package.json
├── CODING_CONVENTIONS.md
├── CONTRIBUTING.md
├── README.md
└── LICENSE
```

## 🔧 Configuration

### Environment Variables

```env
# OpenRouter API
OPENROUTER_API_KEY=your_key_here

# Models
PRIMARY_MODEL=gemini-3-flash-preview
FALLBACK_MODEL=minimax-m2.5

# Agent
AGENT_MAX_ITERATIONS=15
AGENT_MAX_RETRIES=3

# PDF Parser
PDF_PARSER_PRIMARY=gemini_vision
PDF_PARSER_TIMEOUT=120
PDF_MAX_SIZE_MB=20
PDF_VISION_MODEL=google/gemini-3-flash-preview
```

See [`.env.example`](backend/.env.example) for all options.

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Follow [CODING_CONVENTIONS.md](CODING_CONVENTIONS.md)
4. Submit a Pull Request

## 📝 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [Gemini 3 Flash Preview](https://deepmind.google/models/gemini/flash/) by Google DeepMind — PDF vision parsing + agent LLM
- [PyMuPDF4LLM](https://github.com/pymupdf/RAG) — Lightweight PDF text extraction
- [MiniMax M2.5](https://www.minimax.io/news/minimax-m25) by MiniMax AI
- [OpenRouter](https://openrouter.ai) — Unified LLM API access
- [FastAPI](https://fastapi.tiangolo.com/) — Backend framework
- [Next.js](https://nextjs.org/) — Frontend framework

---

**Built with ❤️ by [Saksham Mishra](https://github.com/mysticalseeker24) for the research community**
