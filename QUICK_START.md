# Paper2Notebook - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Get OpenRouter API Key
1. Go to [OpenRouter.ai](https://openrouter.ai)
2. Sign up for a free account
3. Navigate to API Keys
4. Create new key and copy it

### Step 2: Clone & Setup

```bash
# Clone repository (after you create it)
git clone https://github.com/YOUR_USERNAME/Paper2Notebook.git
cd Paper2Notebook

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and paste your OpenRouter API key

# Run backend
python -m app.main
# Backend running at http://localhost:8000

# In new terminal - Frontend setup
cd frontend
npm install
npm run dev
# Frontend running at http://localhost:3000
```

### Step 3: Test It Out

1. Open http://localhost:3000
2. Click "arXiv URL" tab
3. Paste: `https://arxiv.org/abs/1706.03762` (Attention paper)
4. Click "Generate Notebook"
5. Wait ~30 seconds
6. Download your notebook!

## 💻 Using Antigravity IDE

Since you mentioned using Antigravity IDE, here's how to set it up:

### 1. Create New Project
```bash
# In Antigravity IDE terminal
git clone YOUR_REPO_URL
cd Paper2Notebook
```

### 2. Install Dependencies

**Backend**:
```bash
cd backend
pip install -r requirements.txt
```

**Frontend**:
```bash
cd frontend
npm install
```

### 3. Configure Environment

Create `.env` file in `backend/`:
```env
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
PRIMARY_MODEL=gemini-3-flash-preview
FALLBACK_MODEL=minimax-m2.5
DEBUG=True
```

### 4. Run Development Servers

**Option A: Two Terminals**

Terminal 1 (Backend):
```bash
cd backend
python -m app.main
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

**Option B: Docker**
```bash
docker-compose up
```

## 🎯 First Test

### Test 1: Health Check
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Test 2: Simple Paper

Visit http://localhost:3000 and try:
- URL: `https://arxiv.org/abs/2103.14030`
- Title: "Learning Transferable Visual Models From Natural Language Supervision" (CLIP)

Expected result: Notebook with CLIP implementation in ~60 seconds

## 🐛 Common Issues & Fixes

### Issue 1: "Module not found"
**Fix**: 
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue 2: "OpenRouter API error"
**Fix**: 
- Check API key is correct in `.env`
- Verify key has credits
- Try with FALLBACK_MODEL

### Issue 3: "Port already in use"
**Fix**:
```bash
# Backend (change port)
PORT=8001 python -m app.main

# Frontend
PORT=3001 npm run dev
```

### Issue 4: PDF parsing fails
**Fix**:
- Ensure PDF is text-based (not scanned)
- Try simpler paper first
- Check PDF file size < 50MB

## 📱 Usage Examples

### Example 1: Generate from PDF

```python
import requests

# Upload PDF
with open('paper.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/api/upload-pdf', files=files)
    task_id = response.json()['task_id']

# Check status
status = requests.get(f'http://localhost:8000/api/status/{task_id}')
print(status.json())

# Download when ready
notebook = requests.get(f'http://localhost:8000/api/download/{task_id}')
with open('notebook.ipynb', 'wb') as f:
    f.write(notebook.content)
```

### Example 2: Generate from arXiv

```python
import requests

# Submit arXiv URL
response = requests.post('http://localhost:8000/api/arxiv', json={
    'arxiv_url': 'https://arxiv.org/abs/1706.03762',
    'model': 'gemini-3-flash-preview'
})

task_id = response.json()['task_id']
print(f"Processing task: {task_id}")
```

## 🎨 Customization

### Change Models

Edit `backend/.env`:
```env
# Use MiniMax as primary (cheaper, faster)
PRIMARY_MODEL=minimax-m2.5
FALLBACK_MODEL=gemini-3-flash-preview
```

### Adjust Timeout

Edit `backend/app/config.py`:
```python
NOTEBOOK_TIMEOUT: int = 600  # 10 minutes instead of 5
```

### Custom Branding

Edit `frontend/src/app/page.tsx`:
```tsx
<h1 className="text-5xl font-bold">
  YourName's Paper2Notebook 📄→📓
</h1>
```

## 🚢 Deploy to Production

### Option 1: Railway
```bash
# Install Railway CLI
npm install -g railway

# Login
railway login

# Deploy
railway up
```

### Option 2: Vercel (Frontend) + Railway (Backend)

**Frontend** (Vercel):
```bash
cd frontend
vercel
```

**Backend** (Railway):
```bash
cd backend
railway init
railway up
```

Update frontend `.env.production`:
```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### Option 3: DigitalOcean App Platform

```yaml
# app.yaml
name: paper2notebook
services:
  - name: backend
    github:
      repo: your-username/Paper2Notebook
      branch: main
    dockerfile_path: backend/Dockerfile
    
  - name: frontend
    github:
      repo: your-username/Paper2Notebook
      branch: main
    dockerfile_path: frontend/Dockerfile
```

## 📊 Monitoring

### View Logs

**Docker**:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Local**:
Backend logs appear in terminal
Frontend logs in browser console

### Check API Stats
```bash
curl http://localhost:8000/docs
# Opens FastAPI Swagger UI
```

## 🎓 Next Steps

1. **Try different papers**: Test with various ML papers
2. **Customize prompts**: Edit code_generator.py
3. **Add features**: Check FEATURES_ROADMAP.md
4. **Contribute**: Submit PRs to improve the tool
5. **Share**: Star the repo and share with community

## 💬 Get Help

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/Paper2Notebook/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/Paper2Notebook/discussions)
- **Discord**: [Join our Discord](#)
- **Twitter**: [@yourusername](#)

---

**Ready to build? Let's go! 🚀**
