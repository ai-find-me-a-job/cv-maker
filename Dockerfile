FROM python:3.12-slim-trixie

# Copy UV package manager
COPY --from=ghcr.io/astral-sh/uv:0.6.8 /uv /uvx /bin/

# Install system dependencies and TeX Live
RUN apt-get update && apt-get install -y --no-install-recommends \
    # TeX Live for PDF generation
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    lmodern \
    texlive-lang-portuguese \
    # Playwright dependencies for web scraping
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    libwayland-client0 \
    # General utilities
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app ./app

# Create necessary directories
RUN mkdir -p /app/output

# Install Python dependencies using UV
RUN uv sync --frozen --no-dev

# Install Playwright browsers
RUN uv run python -m playwright install chromium

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--port", "8000", "--workers", "4"]

