# Paper2Notebook Development Guide

## 🎯 Project Overview

Paper2Notebook is an open-source tool that converts research papers into executable Jupyter notebooks using AI. Built with FastAPI and Next.js, powered by Gemini 3 Flash Preview and MiniMax M2.5.

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/app/
├── main.py              # Entry point, API routes
├── config.py            # Settings and configuration
├── models.py            # Pydantic schemas
├── pdf_parser.py        # PDF extraction (PyMuPDF)
├── code_generator.py    # LLM code generation
└── notebook_generator.py # Jupyter notebook creation
```

### Frontend (Next.js 14)
```
frontend/src/
├── app/
│   ├── page.tsx        # Main UI
│   ├── layout.tsx      # Root layout
│   └── globals.css     # Global styles
├── components/         # React components
└── lib/
    └── api.ts          # API client
```

## 🔑 Key Features Implementation

### 1. PDF Parsing
**File**: `backend/app/pdf_parser.py`

- Uses PyMuPDF (fitz) for text extraction
- pdfplumber for table detection
- Regex patterns for LaTeX equations
- Section detection (Abstract, Methods, etc.)

```python
# Extract equations
equations = parser.extract_latex_equations()

# Extract sections
sections = parser.extract_sections()
```

### 2. Code Generation
**File**: `backend/app/code_generator.py`

Uses OpenRouter API to access:
- **Primary**: Gemini 3 Flash Preview (1M context, frontier reasoning)
- **Fallback**: MiniMax M2.5 (100 tokens/sec, cost-effective)

```python
# Generate code for section
code_result = generator.generate_code_from_section(
    section_title="Methodology",
    section_content=content,
    equations=equations,
    paper_context=context
)
```

### 3. Notebook Generation
**File**: `backend/app/notebook_generator.py`

Creates structured Jupyter notebooks:
- Header cell with metadata
- Setup cell with dependencies
- Section cells (Markdown + Code)
- Colab button
- Conclusion with next steps

```python
# Generate complete notebook
notebook = nb_gen.generate_from_paper_data(paper_data)
nb_gen.save('output.ipynb')
```

### 4. arXiv Integration
**File**: `backend/app/main.py`

```python
# Download from arXiv
search = arxiv.Search(id_list=[arxiv_id])
paper = next(search.results())
paper.download_pdf(filename=pdf_path)
```

## 🚀 Development Workflow

### Local Development

1. **Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Access at: http://localhost:8000
Docs at: http://localhost:8000/docs

2. **Frontend**
```bash
cd frontend
npm install
npm run dev
```

Access at: http://localhost:3000

### Testing

```bash
# Backend
cd backend
pytest tests/

# Frontend
cd frontend
npm test
```

## 🔧 Configuration

### Environment Variables

**Backend** (`.env`)
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxx
PRIMARY_MODEL=gemini-3-flash-preview
FALLBACK_MODEL=minimax-m2.5
MAX_FILE_SIZE_MB=50
```

**Frontend** (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📊 Model Comparison

| Feature | Gemini 3 Flash Preview | MiniMax M2.5 |
|---------|------------------------|--------------|
| Context Window | 1M tokens | 204K tokens |
| Speed | Medium | 100 tokens/sec |
| Cost | Low | Very Low (1/10th) |
| Reasoning | Frontier-level | Strong |
| Best For | Complex papers | Simple papers |

## 🎨 UI Components

### Main Page (`page.tsx`)
- Tab switching (PDF/arXiv)
- File upload with drag-and-drop
- Progress indicator
- Download button

### Key States
```typescript
const [processing, setProcessing] = useState(false)
const [taskId, setTaskId] = useState<string | null>(null)
const [progress, setProgress] = useState(0)
```

## 🔍 API Endpoints

### POST `/api/upload-pdf`
Upload PDF and start processing

**Request**: multipart/form-data
- `file`: PDF file
- `model`: (optional) Model to use

**Response**:
```json
{
  "task_id": "uuid",
  "status": "pending"
}
```

### POST `/api/arxiv`
Process arXiv paper

**Request**:
```json
{
  "arxiv_url": "https://arxiv.org/abs/2301.00001",
  "model": "gemini-3-flash-preview"
}
```

### GET `/api/status/{task_id}`
Check processing status

**Response**:
```json
{
  "task_id": "uuid",
  "status": "generating_code",
  "progress": 60,
  "message": "Generating PyTorch code"
}
```

### GET `/api/download/{task_id}`
Download generated notebook

Returns `.ipynb` file

## 🐛 Debugging

### Backend Logs
```bash
# Verbose logging
DEBUG=True python -m app.main
```

### Common Issues

1. **PDF parsing fails**
   - Check file is valid PDF
   - Try different PDF library (PyPDF2)

2. **Code generation timeout**
   - Increase `NOTEBOOK_TIMEOUT` in config
   - Use shorter paper sections

3. **Model API errors**
   - Verify OpenRouter API key
   - Check model availability
   - Try fallback model

## 🚢 Deployment

### Docker
```bash
# Build and run
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Considerations
- Use Redis for task queue (replace in-memory dict)
- Add rate limiting
- Implement proper error handling
- Set up monitoring (Sentry, etc.)
- Use environment-specific configs
- Enable CORS properly
- Add authentication if needed

## 📈 Future Enhancements

### Planned Features
- [ ] Multi-language support
- [ ] Custom model fine-tuning
- [ ] Batch processing
- [ ] GitHub integration
- [ ] Code execution validation
- [ ] Automatic hyperparameter tuning
- [ ] Dataset integration
- [ ] Collaborative editing

### Architecture Improvements
- [ ] Websocket for real-time progress
- [ ] Celery for async task processing
- [ ] PostgreSQL for task persistence
- [ ] S3 for file storage
- [ ] Docker Swarm/Kubernetes deployment

## 🤝 Contributing Guidelines

1. **Fork & Clone**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes**
4. **Test thoroughly**
5. **Commit**: `git commit -m 'Add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Create Pull Request**

### Code Style
- Python: Follow PEP 8
- TypeScript: Follow Airbnb style guide
- Use meaningful variable names
- Add comments for complex logic
- Write docstrings for functions

## 📚 Resources

- [Gemini 3 Flash Docs](https://ai.google.dev/gemini-api/docs/models/gemini-3-flash-preview)
- [MiniMax M2.5 Docs](https://www.minimax.io/news/minimax-m25)
- [OpenRouter Docs](https://openrouter.ai/docs)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Next.js 14 Docs](https://nextjs.org/docs)

## 💡 Tips & Tricks

### Optimizing Code Generation
- Keep prompts focused and specific
- Include paper context in prompts
- Use lower temperature (0.2-0.4) for code
- Implement retry logic for API failures

### Performance
- Cache parsed PDFs
- Implement request deduplication
- Use connection pooling
- Optimize image processing

### Cost Optimization
- Use MiniMax M2.5 for simple papers
- Implement token counting
- Cache LLM responses
- Set reasonable rate limits

---

**Happy Coding! 🚀**
