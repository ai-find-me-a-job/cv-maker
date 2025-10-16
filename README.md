# CV Maker 🤖📄

An AI-powered application that generates tailored CVs/resumes based on job descriptions using agentic workflows. The system combines web scraping, vector search, LaTeX document generation, and PDF compilation to create professional resumes that match specific job requirements.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118+-green.svg)](https://fastapi.tiangolo.com/)
[![LlamaIndex](https://img.shields.io/badge/LlamaIndex-Workflows-orange.svg)](https://docs.llamaindex.ai/en/stable/module_guides/workflow/)
[![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)

## 🌟 Features

- **🔄 Human-in-the-Loop**: Interactive workflow with candidate experiences and resume review
- **🧠 Intelligent Job Analysis**: Automatically extracts job requirements from URLs or descriptions
- **🌍 Multi-Language Support**: Generate resumes in English or Portuguese (Brazilian)
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

### Using Docker (Recommended)

The easiest way to run CV Maker is with Docker Compose, which handles all dependencies automatically.

1. **Clone and configure**:
   ```bash
   git clone https://github.com/ai-find-me-a-job/cv-maker.git
   cd cv-maker
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start the application**:
   ```bash
   # Development mode (hot reload)
   docker-compose -f docker-compose.dev.yml up -d
   
   # OR Production mode (4 workers)
   docker-compose up -d
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - Redis: localhost:6379

**That's it!** Docker handles Python, LaTeX, Playwright, and all dependencies.

### Local Development (Advanced)

For development without Docker, you'll need to install dependencies manually.

**Prerequisites**:
- Python 3.12+
- UV package manager
- LaTeX distribution (MiKTeX/TeX Live/MacTeX)
- Redis server
- Google API key

**Setup**:
```bash
# 1. Clone repository
git clone https://github.com/ai-find-me-a-job/cv-maker.git
cd cv-maker

# 2. Install Python dependencies
uv sync

# 3. Install Playwright browsers
uv run python scripts/setup_playwright.py

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Start Redis
redis-server  # or: docker run -d -p 6379:6379 redis:latest

# 6. Run application
uv run fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

## 📝 Configuration

### Environment Variables

Create a `.env` file in the project root:

```properties
# Required
GOOGLE_API_KEY="your-gemini-api-key"
LLAMA_PARSE_API_KEY="your-llama-parse-key"

# Optional (with defaults)
GEMINI_MODEL="gemini-2.0-flash"
GEMINI_TEMPERATURE="0.1"
REDIS_URL="redis://localhost:6379/0"  # Use "redis://redis:6379/0" in Docker
```

### LaTeX Setup (Local Only)

**Docker users can skip this** - LaTeX is included in the image.

For local development, install a LaTeX distribution:

<details>
<summary><b>Windows (MiKTeX)</b></summary>

```bash
# Download from: https://miktex.org/download
# Or using Chocolatey:
choco install miktex
```
</details>

<details>
<summary><b>macOS (MacTeX)</b></summary>

```bash
# Download from: http://www.tug.org/mactex/
# Or using Homebrew:
brew install --cask mactex
```
</details>

<details>
<summary><b>Linux (TeX Live)</b></summary>

```bash
# Ubuntu/Debian
sudo apt-get install texlive-full

# CentOS/RHEL
sudo yum install texlive-scheme-full
```
</details>

## 🐳 Docker

### Docker Compose Files

| File | Use Case | Features |
|------|----------|----------|
| `docker-compose.yml` | Production | 4 workers, optimized |
| `docker-compose.dev.yml` | Development | Hot reload, code mounting |

### Common Commands

```bash
# Start services
docker-compose up -d                              # Production
docker-compose -f docker-compose.dev.yml up -d    # Development

# View logs
docker-compose logs -f cv-maker

# Restart
docker-compose restart

# Stop
docker-compose down

# Rebuild (after Dockerfile changes)
docker-compose build

# Status
docker-compose ps
```


### Useful Commands

```bash
# View logs in real-time
docker-compose logs -f cv-maker

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Rebuild after Dockerfile changes
docker-compose build

# Check service status
docker-compose ps
```


## 📖 API Usage

### Get Supported Languages

```bash
curl -X GET "http://localhost:8000/cv/languages"
```

### Generate CV from Job URL

```bash
curl -X POST "http://localhost:8000/cv/run/from-url/en" \
     -H "Content-Type: application/json" \
     -d '{"job_url": "https://example.com/job-posting"}'
```

### Generate CV from Job Description

```bash
curl -X POST "http://localhost:8000/cv/run/from-description/pt" \
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
├── app/                      # Application code
│   ├── main.py              # FastAPI entry point
│   ├── api/v1/              # API endpoints
│   │   ├── cv.py            # CV generation
│   │   └── index.py         # File indexing
│   ├── services/workflow/   # CV workflow engine
│   │   ├── __init__.py      # Workflow steps
│   │   ├── extraction_models.py  # Data models
│   │   ├── prompts.py       # LLM prompts
│   │   └── latex_generator.py    # PDF generation
│   └── core/                # Utilities
│       ├── config.py        # Configuration
│       ├── index_manager.py # Vector search
│       └── web_scraper.py   # Job scraping
├── data/                    # Persistent data
│   ├── files/              # Uploaded resumes
│   └── .storage/           # Vector index
├── output/                 # Generated PDFs
├── docs/                   # Documentation
├── scripts/                # Setup scripts
└── docker-compose.yml      # Docker configs
```

## 🔧 Advanced Topics

### Vector Index

The application uses LlamaIndex to store and search resume information. Data is persisted in `data/.storage/`. To reset:
```bash
rm -rf data/.storage
```

### Production Deployment

For production environments:
- Use `docker-compose.yml` (includes 4 workers)
- Set proper CORS origins in `app/main.py`
- Use Docker secrets or vault for API keys
- Deploy behind nginx/Traefik reverse proxy
- Enable HTTPS with SSL certificates

See [Docker Deployment Guide](docs/docker-deployment.md) for details.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 📝 License

This project is licensed under the GPL v3 - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ai-find-me-a-job/cv-maker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ai-find-me-a-job/cv-maker/discussions)
- **Documentation**: Check the `docs/` folder for detailed guides

## 🗺️ Roadmap

- [x] Human-in-the-loop interactive resume creation
- [x] Multi-language support (English, Portuguese)
- [x] Docker deployment with hot reload
- [ ] Web interface for non-technical users
- [ ] Resume templates and styling options
- [ ] Additional output formats (Word, HTML)
- [ ] Batch processing capabilities
- [ ] Integration with job boards and LinkedIn
- [ ] Mobile app support

---

**Made with ❤️ for job seekers everywhere**
