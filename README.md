# Paper2Notebook 📄→📓

Transform research papers into executable Jupyter notebooks in seconds. Powered by Gemini 3 Flash Preview & MiniMax M2.5.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🚀 Features

- **📄 PDF to Notebook Conversion**: Upload research papers and get runnable PyTorch notebooks
- **🔗 arXiv Integration**: Direct support for arXiv papers - just paste the URL
- **📐 LaTeX Extraction**: Automatically extracts and renders mathematical equations
- **🐍 PyTorch Implementation**: Real ML implementations at reduced scale for CPU execution
- **☁️ Google Colab Ready**: One-click "Open in Colab" functionality
- **🔧 Auto Dependencies**: Automatically detects and installs required libraries
- **🎯 Structured Output**: Organized into Abstract, Methodology, Experiments, and Conclusion sections

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Gemini 3 Flash Preview**: Frontier intelligence at speed (1M context window)
- **MiniMax M2.5**: Cost-effective agentic coding model
- **PyMuPDF**: PDF processing and text extraction
- **nbformat**: Jupyter notebook generation

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Smooth animations

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- OpenRouter API key ([Get one here](https://openrouter.ai))

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/Paper2Notebook.git
cd Paper2Notebook
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run server
python -m app.main
```

Backend will be running at `http://localhost:8000`

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be running at `http://localhost:3000`

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

Access at `http://localhost:3000`

## 📖 Usage

### Upload PDF
1. Click on "Upload PDF" tab
2. Drag and drop your research paper
3. Click "Generate Notebook"
4. Wait for processing (20-60 seconds)
5. Download the generated notebook

### arXiv Integration
1. Click on "arXiv URL" tab
2. Paste arXiv URL (e.g., `https://arxiv.org/abs/2301.00001`)
3. Click "Generate Notebook"
4. Download when ready

## 🎯 Model Selection

The tool uses two powerful models:

1. **Gemini 3 Flash Preview** (Primary)
   - 1M token context window
   - Frontier-level reasoning
   - Excellent for complex papers

2. **MiniMax M2.5** (Fallback)
   - 100 tokens/second speed
   - Extremely cost-effective
   - Great for simpler papers

## 📁 Project Structure

```
Paper2Notebook/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── models.py            # Pydantic models
│   │   ├── pdf_parser.py        # PDF parsing logic
│   │   ├── code_generator.py    # LLM code generation
│   │   └── notebook_generator.py # Jupyter notebook creation
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js app directory
│   │   ├── components/          # React components
│   │   └── lib/                 # API client
│   ├── package.json
│   └── tailwind.config.ts
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

### Environment Variables

```env
# OpenRouter API
OPENROUTER_API_KEY=your_key_here

# Model Configuration
PRIMARY_MODEL=gemini-3-flash-preview
FALLBACK_MODEL=minimax-m2.5

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Limits
MAX_FILE_SIZE_MB=50
NOTEBOOK_TIMEOUT=300
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Gemini 3 Flash Preview](https://deepmind.google/models/gemini/flash/) by Google DeepMind
- [MiniMax M2.5](https://www.minimax.io/news/minimax-m25) by MiniMax AI
- [OpenRouter](https://openrouter.ai) for unified LLM API access
- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF processing
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Next.js](https://nextjs.org/) for the frontend framework

## 📧 Contact

Your Name - [@yourusername](https://twitter.com/yourusername)

Project Link: [https://github.com/yourusername/Paper2Notebook](https://github.com/yourusername/Paper2Notebook)

---

**Built with ❤️ for the research community**
