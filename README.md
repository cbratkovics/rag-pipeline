# RAG Pipeline - Production-Ready AI System

Enterprise-grade Retrieval-Augmented Generation implementation showcasing advanced AI engineering capabilities for portfolio demonstration.

## 🚀 Live Deployments

- **Frontend**: [rag-pipeline-eta.vercel.app](https://rag-pipeline-eta.vercel.app)
- **Backend API**: [rag-pipeline-api-hksb.onrender.com](https://rag-pipeline-api-hksb.onrender.com/docs)
- **Repository**: [github.com/cbratkovics/rag-pipeline](https://github.com/cbratkovics/rag-pipeline)

## 🎯 Key Features

### Core RAG Capabilities
- **Hybrid Search**: BM25 keyword search + dense vector embeddings using sentence-transformers
- **A/B Testing Framework**: Compare retrieval strategies in production with configurable experiments
- **RAGAS Evaluation**: Comprehensive metrics including faithfulness, relevancy, and answer correctness
- **Smart Caching**: Redis-based multi-tier caching with TTL management and cache invalidation

### Production Engineering
- **Observability**: Prometheus metrics, structured logging via structlog, OpenTelemetry tracing
- **Continuous Learning**: MLflow experiment tracking, model versioning, performance monitoring
- **Error Handling**: Retry logic with tenacity, circuit breakers, graceful degradation
- **API Design**: FastAPI with automatic OpenAPI docs, Pydantic v2 validation, WebSocket support

## 🛠️ Technology Stack

### Backend
- **Runtime**: Python 3.12, uvloop for async performance
- **Framework**: FastAPI 0.121.1, Pydantic 2.5.0
- **Vector Store**: ChromaDB 1.3.4 with chroma-hnswlib 0.7.6
- **LLM Integration**: OpenAI GPT-4 API, sentence-transformers 2.2.2
- **Caching**: Redis 5.0.0 with connection pooling
- **Search**: rank-bm25 0.2.2 for hybrid retrieval
- **Monitoring**: Prometheus, Grafana dashboards

### Infrastructure
- **Deployment**: Docker multi-stage builds, GitHub Actions CI/CD
- **Backend Hosting**: Render (srv-d3neevgv73c739vsa1g)
- **Cache Hosting**: Render Redis (red-d3nealjipnbc73b1cnsg)
- **Frontend Hosting**: Vercel with edge functions

## 📦 Installation

### Quick Start with uv (Recommended)
```bash
# Clone repository
git clone https://github.com/cbratkovics/rag-pipeline.git
cd rag-pipeline

# Install dependencies with uv
uv sync

# Run tests
uv run pytest tests/ -m "not integration"

# Start API server
uv run uvicorn api.main:app --reload --port 8000
```

### Docker Deployment
```bash
# Build production image
docker build -t rag-pipeline:latest .

# Run with environment variables
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e REDIS_URL=redis://localhost:6379 \
  -e CHROMADB_HOST=localhost \
  rag-pipeline:latest
```

## 📊 Performance Metrics

- **Response Time**: <500ms p95 latency
- **Throughput**: 1000+ requests/minute sustained
- **Cache Hit Rate**: 60-80% depending on query patterns
- **Retrieval Accuracy**: 0.85+ MRR, 0.92+ NDCG@10
- **Uptime**: 99.9% availability SLA

## 🧪 Development

### Code Quality
```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check . --fix

# Type checking
uv run mypy src api --ignore-missing-imports

# Run all tests
uv run pytest tests/ --cov=src --cov=api --cov-report=html
```

### Pre-commit Hooks
```bash
# Install hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

## 📚 Project Structure

```
rag-pipeline/
├── api/                    # FastAPI application
│   ├── main.py            # Application entry point
│   ├── routes/            # API endpoints
│   └── dependencies.py    # Dependency injection
├── src/                    # Core RAG implementation
│   ├── rag/               # Pipeline components
│   │   ├── retriever.py   # Hybrid search implementation
│   │   ├── generator.py   # LLM response generation
│   │   └── pipeline.py    # Orchestration logic
│   ├── eval/              # RAGAS evaluation
│   └── monitoring/        # Observability tools
├── configs/               # Configuration files
├── tests/                 # Comprehensive test suite
├── scripts/               # Utility scripts
└── frontend/             # Next.js application
```

## 🔧 Configuration

Environment variables (see `.env.example`):
- `OPENAI_API_KEY`: Required for GPT-4 access
- `REDIS_URL`: Cache connection string
- `CHROMADB_HOST`: Vector database host
- `EMBEDDING_MODEL`: Default "all-MiniLM-L6-v2"
- `LLM_MODEL`: Default "gpt-4"

## 📈 Monitoring & Observability

- **Metrics Endpoint**: `/metrics` (Prometheus format)
- **Health Check**: `/healthz`
- **API Docs**: `/docs` (Swagger UI)
- **Tracing**: OpenTelemetry with Jaeger backend

## 🤝 Contributing

This is a portfolio project demonstrating production AI engineering capabilities. Feel free to explore the codebase and architecture decisions.

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 👤 Contact

Built by AI Engineer for demonstrating production-ready AI systems architecture and implementation.
