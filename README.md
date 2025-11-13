# RAG Pipeline — Production‑Ready, Observable, and Measurable

Retrieval‑Augmented Generation (RAG) service engineered like a real product: hybrid retrieval, streaming generation, evaluation (RAGAS), load testing, observability, and deployment artifacts. Built to demonstrate end‑to‑end AI engineering, not just a demo.

**Live Demo:** https://rag-pipeline-eta.vercel.app
**API Docs (Swagger):** https://rag-pipeline-api-hksb.onrender.com/docs
**Repo:** https://github.com/cbratkovics/rag-pipeline

---

## What This Project Demonstrates

- **Hybrid Retrieval with RRF:** BM25 + dense embeddings fused with Reciprocal Rank Fusion for robust ranking across query styles.
- **Production Observability:** `/metrics` for Prometheus, structured logging, and trace hooks via OpenTelemetry.
- **Evaluation you can trust:** RAGAS metrics (faithfulness, relevancy, answer correctness) and scripts to A/B retrieval strategies.
- **Real Ops Concerns:** Semantic caching (Redis), request budgets, retries/circuit breakers, typed configs, and health checks.
- **Deployable Anywhere:** Dockerfile, `docker-compose`, and Kubernetes manifests with staging/production env examples.

---

## Architecture at a glance

```mermaid
flowchart LR
    A[Client / Frontend] -- REST/WebSocket --> B[FastAPI Service]
    B -->|Query| C[Retriever]
    C -->|BM25| D[(BM25 Index)]
    C -->|Embeddings| E[(ChromaDB)]
    C -->|RRF fuse| F[Ranked Contexts]
    B -->|LLM prompt with contexts| G[Generator]
    G -->|Answer| A
    B <--> H[(Redis Cache)]
    B --> I[Metrics/Tracing]
````

**Request path (sequence):**

```mermaid
sequenceDiagram
    participant User
    participant API as FastAPI
    participant Cache as Redis
    participant Ret as Retriever
    participant LLM as LLM Provider

    User->>API: POST /api/v1/query
    API->>Cache: Check semantic cache
    alt Cache hit
        Cache-->>API: cached answer
        API-->>User: stream answer
    else Cache miss
        API->>Ret: hybrid search (BM25 + vector)
        Ret-->>API: top-k contexts (RRF)
        API->>LLM: generate with retrieved contexts
        LLM-->>API: streamed tokens
        API->>Cache: store result
        API-->>User: stream answer
    end
```

---

## Core Features

* **Hybrid search** using BM25 and vector search (sentence-transformers) with RRF fusion.
* **RAGAS evaluation** to quantify quality (faithfulness, relevancy, correctness).
* **A/B testing hooks** to compare retrieval strategies in real time.
* **Semantic cache (Redis)** with TTLs and invalidation to cut cost/latency.
* **Production guardrails**: retries, timeouts, circuit breakers, and request budgets.
* **Observability**: health checks, Prometheus metrics, structured logs, tracing hooks.
* **API design**: FastAPI with Pydantic models, OpenAPI docs, and optional streaming.

> See `api/`, `src/rag/`, `deployments/k8s/`, `benchmarks/locust/`, and `monitoring/` directories for full implementation.

---

## Quickstart (local)

> Requires Python 3.12+ and [uv](https://github.com/astral-sh/uv) **or** Docker.

### Option A — Python + uv

```bash
# 1) Clone
git clone https://github.com/cbratkovics/rag-pipeline.git
cd rag-pipeline

# 2) Install
uv sync

# 3) Environment
cp .env.example .env
# set OPENAI_API_KEY and any Redis/Chroma vars you need

# 4) Run tests (unit only)
uv run pytest tests/ -m "not integration"

# 5) Launch API
uv run uvicorn api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```

### Option B — Docker Compose (API + Redis + Chroma)

```bash
# Provide OPENAI_API_KEY in your shell or .env
docker compose up --build
# API: http://localhost:8000/docs
# Metrics: http://localhost:8000/metrics
```

---

## Ingest and Query

**Ingest documents**

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [{
      "content": "Your document text here",
      "metadata": {"source": "example","category":"technical"}
    }],
    "reset": false
  }'
```

**Query**

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is RAG?",
    "k": 4,
    "top_k_bm25": 8,
    "top_k_vec": 8,
    "rrf_k": 60,
    "provider": "openai"
  }'
```

---

## Evaluation & A/B testing

* **RAGAS** – generate a test set and score outputs (faithfulness, relevancy, answer correctness).
* **A/B hooks** – flip between retrieval configs (e.g., K values, fusion params) and compare RAGAS + latency.

Suggested workflow:

1. Create or synthesize a test set (e.g., ~100 Q/A with references).
2. Run the pipeline under Strategy A vs. Strategy B.
3. Compare RAGAS metrics and latency/throughput from load tests.
4. Promote the champion config; keep historical results for drift tracking.

---

## Load testing (Locust)

Spin up the API locally or in staging, then:

```bash
# From project root
uv run locust -f benchmarks/locust/locustfile.py --host http://localhost:8000
```

Track **p50/p95 latency**, **RPS/QPS**, and **error rates**; confirm semantic cache hit rates while ramping users.

---

## Configuration

Environment variables (see `.env.example`):

* `OPENAI_API_KEY` – default provider is OpenAI
* `OPENAI_MODEL` – e.g., `gpt-4o-mini` or similar
* `REDIS_URL` – `redis://localhost:6379/0`
* `CHROMADB_HOST` / `CHROMA_PERSIST_DIR` – for vector store
* `EMBEDDING_MODEL` – e.g., `all-MiniLM-L6-v2`

---

## Project Structure

```
rag-pipeline/
├── api/                    # FastAPI application
│   ├── main.py             # Application entry point
│   ├── routes/             # REST endpoints
│   └── dependencies.py     # Dependency injection / settings
├── src/
│   ├── rag/                # Retriever, generator, pipeline orchestration
│   ├── eval/               # RAGAS / eval utilities
│   └── monitoring/         # Instrumentation and metrics
├── benchmarks/locust/      # Load tests (Locust)
├── deployments/k8s/        # Kubernetes manifests
├── monitoring/             # Grafana/Prometheus assets
├── docs/                   # Quick start / local setup notes
├── tests/                  # Unit/integration tests
├── Dockerfile
├── docker-compose.yml
└── render.yaml
```

---

## Operations

* **Health:** `GET /healthz`
* **Docs:** `GET /docs` (OpenAPI)
* **Metrics:** `GET /metrics` (Prometheus format)
* **Tracing:** OpenTelemetry exporters pluggable (e.g., Jaeger)

---

## License

MIT — see `LICENSE`.
