---
description: how to run the NoteBrew backend and frontend for development
---

# Dev Workflow — NoteBrew

## Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- OpenRouter API key

---

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
5. Start the backend server:
```
.\venv\Scripts\python.exe -m app.main
```

Backend runs at `http://localhost:8001` (API docs at `/docs`)

---

## Frontend Setup

// turbo
6. Open a new terminal and navigate to the frontend directory:
```
cd frontend
```

// turbo
7. Install dependencies:
```
npm install
```

// turbo
8. Start the dev server:
```
npm run dev
```

Frontend runs at `http://localhost:3000`

---

## Important Notes

- **Ports**: Backend = **8001**, Frontend = **3000**
- **Environment variables**: Shell env vars override `.env` file. If you get 401 errors, check for stale `OPENROUTER_API_KEY` env var:
  ```
  Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue
  ```
- **Pydantic config**: Old `.env` files with extra vars are safely ignored (`extra="ignore"` in settings)
- **Debug mode**: Set `DEBUG=True` in `.env` for auto-reload
- **Frontend design**: Uses Cream Codex color palette with shadcn/ui components
- **CSS lint warnings**: `@tailwind` and `@apply` warnings in globals.css are false positives — they work with PostCSS

## Quick Test

```bash
# Backend health check
curl http://localhost:8001/health

# Submit arXiv paper
curl -X POST http://localhost:8001/api/arxiv -H "Content-Type: application/json" -d '{"arxiv_url": "1706.03762"}'

# Check status (replace TASK_ID)
curl http://localhost:8001/api/status/TASK_ID

# Frontend — open in browser
# http://localhost:3000 (landing)
# http://localhost:3000/features (features)
# http://localhost:3000/brew/TASK_ID (brew progress)
```
