# Multi-stage build for production RAG pipeline
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv==0.5.1

# Copy dependency files and README (required by hatchling build backend)
COPY pyproject.toml uv.lock ./
COPY README.md ./

# Install dependencies using uv (frozen lockfile, production only)
RUN uv sync --frozen --no-dev --compile-bytecode || \
    (echo "uv sync failed, attempting pip fallback..." && \
     uv export --format requirements-txt --no-hashes > requirements.txt && \
     pip install --no-cache-dir -r requirements.txt)

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python and uv from builder
COPY --from=builder /usr/local /usr/local

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy app code
COPY api/ ./api/
COPY src/ ./src/
COPY configs/ ./configs/

# Create non-root user
RUN useradd -m -u 1000 raguser && \
    chown -R raguser:raguser /app

USER raguser

# Use virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/app/.venv

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
