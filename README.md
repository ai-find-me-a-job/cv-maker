# CV Maker 🤖📄

An AI-powered application that generates tailored CVs/resumes based on job descriptions using agentic workflows. The system combines web scraping, vector search, LaTeX document generation, and PDF compilation to create professional resumes that match specific job requirements.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118+-green.svg)](https://fastapi.tiangolo.com/)
[![LlamaIndex](https://img.shields.io/badge/LlamaIndex-Workflows-orange.svg)](https://docs.llamaindex.ai/en/stable/module_guides/workflow/)
[![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)

## 🌟 Features

- **🔄 Human-in-the-Loop**: Interactive workflow with candidate experiences and resume review
- **🧠 Intelligent Job Analysis**: Automatically extracts job requirements from URLs or descriptions
- **🤖 AI-Powered Resume Generation**: Creates tailored resumes using Google Gemini LLM
- **📄 Professional PDF Output**: Generates LaTeX-formatted PDFs with proper styling
- **🎯 Strategic Optimization**: Matches keywords and requirements for ATS compatibility
- **🚀 RESTful API**: FastAPI-based endpoints for easy integration
- **⚡ Async Workflows**: Event-driven architecture for optimal performance

## 🏗️ Architecture

The application uses an event-driven workflow architecture powered by LlamaIndex with human interaction:

```
Job URL/Description → Web Scraping → Interactive Candidate Queries → Resume Generation → Human Review → PDF Export
```

### Core Components

- **Interactive Workflow Engine**: LlamaIndex workflows with human-in-the-loop interactions
- **Web Scraper**: Playwright-based job posting extraction
- **Vector Search**: Intelligent candidate information retrieval
- **LLM Integration**: Google Gemini for text generation and analysis
- **Document Generation**: PyLaTeX for professional PDF creation
- **API Layer**: FastAPI with automatic documentation and interactive endpoints

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- UV package manager (recommended) or pip
- LaTeX distribution (MiKTeX or TeX Live) for PDF generation
- Google API key for Gemini LLM

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ai-find-me-a-job/cv-maker.git
   cd cv-maker
   ```

2. **Install dependencies**:
   ```bash
   # Using UV (recommended)
   uv sync
   
   # Or using pip
   pip install -e .
   ```

3. **Set up Playwright** (for web scraping):
   ```bash
   uv run python scripts/setup_playwright.py
   # Or manually: uv run python -m playwright install chromium
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Environment Configuration

Create a `.env` file in the project root:

```properties
# Required
GOOGLE_API_KEY="your-gemini-api-key"
LLAMA_PARSE_API_KEY="your-llama-parse-key"

# Optional
GEMINI_MODEL="gemini-2.0-flash"  # Default model
GEMINI_TEMPERATURE="0.1"        # Default temperature
```

### Running the Application

#### Development Server
```bash
# Option 1: FastAPI development server
uv run fastapi dev main.py --host 0.0.0.0 --port 8000

# Option 2: Direct Python execution
uv run python main.py
```

#### Production Server
```bash
# Single worker
uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Multiple workers
uv run gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📖 API Usage

### Generate CV from Job URL

```bash
curl -X POST "http://localhost:8000/cv/run/from-url" \
     -H "Content-Type: application/json" \
     -d '{"job_url": "https://example.com/job-posting"}'
```

### Generate CV from Job Description

```bash
curl -X POST "http://localhost:8000/cv/run/from-description" \
     -H "Content-Type: text/plain" \
     -d "We are seeking a Senior Python Developer..."
```

### Continue CV Workflow

```bash
curl -X POST "http://localhost:8000/cv/continue/{workflow_id}" \
     -H "Content-Type: application/json" \
     -d '{"approve": true, "feedback": "Looks good, please proceed"}'
```

### Add Resume Files to Index

```bash
curl -X POST "http://localhost:8000/cv/index/add-files" \
     -F "files=@resume.pdf" \
     -F "files=@cover_letter.docx"
```

### Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

## 📂 Project Structure

```
cv-maker/
├── main.py                    # FastAPI application entry point
├── pyproject.toml            # Project dependencies and metadata
├── .env                      # Environment variables (not in git)
├── src/
│   ├── api/v1/              # REST API endpoints
│   │   ├── cv.py            # CV generation endpoints
│   │   └── index.py         # File upload/indexing endpoints
│   ├── cv_maker/            # Core CV generation logic
│   │   └── workflow/        # Agentic workflow implementation
│   │       ├── __init__.py  # CVWorkflow class and step functions
│   │       ├── models.py    # Resume, Experience, Skills data models
│   │       ├── prompts.py   # LLM prompts and guidelines
│   │       └── latex_generator.py # PyLaTeX document generation
│   ├── core/                # Shared utilities
│   │   ├── index_manager.py # Vector index management
│   │   └── web_scraper.py   # Playwright web scraping
│   └── config.py            # Environment configuration
├── data/                    # User data and storage
│   ├── files/              # User uploaded resumes (not in git)
│   └── .storage/           # Vector index storage (not in git)
├── output/                 # Generated LaTeX/PDF files (not in git)
├── scripts/                # Setup and utility scripts
├── tests/                  # Test suite
└── docs/                   # Documentation
```

## 🔧 Configuration

### LaTeX Setup

The application requires a LaTeX distribution for PDF generation:

**Windows (MiKTeX)**:
```bash
# Download and install from: https://miktex.org/download
# Or using Chocolatey:
choco install miktex
```

**macOS (MacTeX)**:
```bash
# Download from: http://www.tug.org/mactex/
# Or using Homebrew:
brew install --cask mactex
```

**Linux (TeX Live)**:
```bash
# Ubuntu/Debian:
sudo apt-get install texlive-full

# CentOS/RHEL:
sudo yum install texlive-scheme-full
```

### Vector Index Storage

The application stores vector indices in `data/.storage/`. This directory is created automatically and excluded from git. To reset the index, simply delete this directory.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Install pre-commit hooks (if available)
pre-commit install

# Run tests before committing
uv run pytest
```

## 📝 License

This project is licensed under the GPL v3 - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ai-find-me-a-job/cv-maker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ai-find-me-a-job/cv-maker/discussions)
- **Documentation**: Check the `docs/` folder for detailed guides

## 🗺️ Roadmap

- [x] **Human-in-the-loop for interactive resume creation** ✅
- [ ] Web interface for non-technical users
- [ ] Resume templates and styling options
- [ ] Multi-language support
- [ ] Additional output formats (Word, HTML)
- [ ] Resume templates and styling options
- [ ] Batch processing capabilities
- [ ] Web interface for non-technical users
- [ ] Integration with job boards and LinkedIn
- [ ] Mobile app for on-the-go resume generation

---

**Made with ❤️ for job seekers everywhere**
