# syntax=docker/dockerfile:1.4
# Multi-stage build for production RAG pipeline

FROM python:3.12-slim as builder

WORKDIR /app

# Install essential build dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv==0.5.1

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code (after dependencies for better caching)
COPY api/ ./api/
COPY src/ ./src/
COPY configs/ ./configs/

# Create non-root user
RUN useradd -m -u 1000 raguser && \
    chown -R raguser:raguser /app

USER raguser

# Environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
