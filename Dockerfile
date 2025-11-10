# Multi-stage build for production RAG pipeline
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install uv
RUN pip install --no-cache-dir --no-compile uv==0.5.1

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev \
    && rm -rf /tmp/* /var/tmp/* \
    && find /usr/local -type f -name '*.pyc' -delete \
    && find /usr/local -type d -name '__pycache__' -delete

# Production stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code with specific patterns
COPY --chown=1000:1000 api/ ./api/
COPY --chown=1000:1000 src/ ./src/
COPY --chown=1000:1000 configs/ ./configs/
COPY --chown=1000:1000 scripts/ ./scripts/

# Create data directory
RUN mkdir -p /app/data

# Create non-root user
RUN useradd -m -u 1000 raguser
USER raguser

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]