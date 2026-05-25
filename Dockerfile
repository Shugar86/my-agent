# Multi-stage Dockerfile for production optimization
FROM node:20-slim AS frontend-builder

WORKDIR /app
COPY web/frontend/package*.json ./web/frontend/
WORKDIR /app/web/frontend
RUN npm ci 2>/dev/null || npm install
COPY web/frontend/ ./
RUN npm run build

FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir build && \
    pip install --no-cache-dir -e .[dev] || true

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Install runtime dependencies + Playwright browser deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tesseract-ocr \
    poppler-utils \
    nodejs \
    git \
    libnss3 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install Playwright Chromium for browser automation
RUN python -m playwright install chromium || true

# Copy application code
COPY . .

# Copy built frontend from node stage
COPY --from=frontend-builder /app/web/static/app ./web/static/app

# Create data directory with proper permissions
RUN mkdir -p data && chown -R appuser:appuser data

USER appuser

EXPOSE 8020

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

CMD ["python", "-m", "uvicorn", "web.server:app", "--host", "0.0.0.0", "--port", "8020"]
