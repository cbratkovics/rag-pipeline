# syntax=docker/dockerfile:1.4
# Multi-stage build for production RAG pipeline

FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Install minimal build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv with cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir uv==0.5.1

# Copy ONLY dependency files first (maximize cache hit rate)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies with aggressive caching
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    uv sync --frozen --no-dev

# Copy application code LAST (changes most frequently)
COPY api/ ./api/
COPY src/ ./src/
COPY configs/ ./configs/

# Production stage
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install ONLY runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code from builder
COPY --from=builder /app/api ./api
COPY --from=builder /app/src ./src
COPY --from=builder /app/configs ./configs

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
