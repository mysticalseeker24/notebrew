---
description: how to run the NoteBrew backend for development
---

# Dev Workflow — NoteBrew Backend

## Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- OpenRouter API key

## Backend Setup

// turbo
1. Navigate to the backend directory:
```
cd backend
```

// turbo
2. Create and activate virtual environment:
```
python -m venv venv
.\venv\Scripts\activate   # Windows
```

// turbo
3. Install dependencies:
```
.\venv\Scripts\pip.exe install -r requirements.txt
```

4. Create `.env` from template:
```
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

// turbo
5. Start the server:
```
.\venv\Scripts\python.exe -m app.main
```

Server runs at `http://localhost:8001` (API docs at `/docs`)

## Important Notes

- **Port**: Always use **8001** (not 8000)
- **Environment variables**: Shell env vars override `.env` file. If you get 401 errors, check for stale `OPENROUTER_API_KEY` env var:
  ```
  Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue
  ```
- **Pydantic warnings**: Docling's `model_spec` warnings are cosmetic (from Docling's own models, not ours)
- **Debug mode**: Set `DEBUG=True` in `.env` for auto-reload

## Quick Test

```bash
# Health check
curl http://localhost:8001/health

# Submit arXiv paper
curl -X POST http://localhost:8001/api/arxiv -H "Content-Type: application/json" -d '{"arxiv_url": "1706.03762"}'

# Check status (replace TASK_ID)
curl http://localhost:8001/api/status/TASK_ID
```
