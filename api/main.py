import os

# Set protobuf environment variable before any chromadb imports
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import time
import warnings
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

import chromadb
import structlog
import uvicorn
from chromadb.config import Settings as ChromaSettings
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field

from src.rag.pipeline import answer_query
from src.retrieval.embeddings import embedding_manager
from src.retrieval.vector_store import vector_store

warnings.filterwarnings("ignore", category=DeprecationWarning, module="opentelemetry")

load_dotenv()

logger = structlog.get_logger()


def _get_chroma_collection():
    """Get or create ChromaDB collection."""
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", ".chroma")
    name = os.getenv("CHROMADB_COLLECTION", "rag_documents")
    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    return client, client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


async def _seed_if_empty():
    """Seed the vector store with initial documents if empty."""
    _, coll = _get_chroma_collection()
    if coll.count() == 0:
        logger.info("ChromaDB collection is empty, seeding with initial documents")
        docs = [
            {
                "content": "Retrieval-Augmented Generation (RAG) combines retrieval systems with generative models to produce more accurate and grounded responses by fetching relevant context from a knowledge base.",
                "metadata": {"source": "intro", "category": "overview"},
            },
            {
                "content": "Semantic search uses vector embeddings to find documents based on meaning rather than exact keyword matches, enabling more nuanced information retrieval.",
                "metadata": {"source": "concepts", "category": "fundamentals"},
            },
            {
                "content": "BM25 is a probabilistic ranking function used in information retrieval that scores documents based on term frequency and inverse document frequency with saturation.",
                "metadata": {"source": "algorithms", "category": "technical"},
            },
            {
                "content": "Hybrid search combines keyword-based methods like BM25 with semantic vector search, using techniques like Reciprocal Rank Fusion to merge results from both approaches for improved retrieval quality.",
                "metadata": {"source": "techniques", "category": "advanced"},
            },
        ]
        contents = [d["content"] for d in docs]
        ids = [str(uuid4()) for _ in contents]
        metadatas = [d["metadata"] for d in docs]
        embeddings = embedding_manager.embed_batch(contents)
        coll.add(ids=ids, documents=contents, embeddings=embeddings, metadatas=metadatas)
        logger.info(f"Seeded ChromaDB with {len(docs)} initial documents")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    # Startup
    logger.info("Starting RAG Pipeline application")
    try:
        await vector_store.initialize()
        logger.info("✓ Qdrant vector store initialized")
    except Exception as e:
        logger.warning(
            "⚠ Failed to initialize vector store - running in degraded mode",
            error=str(e),
        )

    # Seed ChromaDB if empty
    try:
        await _seed_if_empty()
    except Exception as e:
        logger.warning(
            "⚠ Failed to seed ChromaDB - you may need to add documents manually",
            error=str(e),
        )

    logger.info("Application startup complete")
    yield
    # Shutdown
    logger.info("Application shutdown complete")


app = FastAPI(title="RAG Pipeline API", version="0.1.0", lifespan=lifespan)

_raw = os.getenv("FRONTEND_CORS_ORIGINS", "")
_allowed = [o.strip() for o in _raw.split(",") if o.strip()]
_origin_regex = os.getenv("FRONTEND_CORS_ORIGIN_REGEX")

app.add_middleware(
    CORSMiddleware,
    allow_origins=([] if _origin_regex else _allowed or ["*"]),
    allow_origin_regex=_origin_regex,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUEST_COUNT = Counter(
    "rag_requests_total",
    "Total requests",
    ["endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "rag_request_duration_seconds",
    "Request latency",
    ["endpoint"],
)
ERROR_COUNT = Counter(
    "rag_errors_total",
    "Total errors",
    ["endpoint", "error_type"],
)


tracer_provider = TracerProvider()
trace.set_tracer_provider(tracer_provider)
span_processor = BatchSpanProcessor(ConsoleSpanExporter())
tracer_provider.add_span_processor(span_processor)
FastAPIInstrumentor.instrument_app(app)


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        description="The question to answer",
    )
    k: int = Field(
        4,
        description="Number of final documents to retrieve",
    )
    top_k_bm25: int = Field(
        8,
        description="Number of BM25 results to retrieve",
    )
    top_k_vec: int = Field(
        8,
        description="Number of vector search results to retrieve",
    )
    rrf_k: int = Field(
        60,
        description="RRF K parameter for fusion",
    )
    provider: str = Field(
        "openai",
        description="LLM provider (OpenAI only)",
    )


class QueryResponse(BaseModel):
    answer: str
    contexts: list[str]
    scores: dict
    latency_ms: float


class IngestDoc(BaseModel):
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    documents: list[IngestDoc]
    reset: bool = False


@app.get("/api/health")
def api_health() -> dict:
    REQUEST_COUNT.labels(
        endpoint="/api/health",
        status="success",
    ).inc()
    return {"ok": True, "service": "rag-pipeline-api"}


@app.get("/healthz")
def healthz() -> dict:
    REQUEST_COUNT.labels(
        endpoint="/healthz",
        status="success",
    ).inc()
    return {"status": "ok"}


@app.get("/health")
def health() -> dict:
    REQUEST_COUNT.labels(
        endpoint="/health",
        status="success",
    ).inc()
    return {"status": "healthy", "service": "rag-pipeline"}


@app.get("/metrics")
def metrics():
    REQUEST_COUNT.labels(
        endpoint="/metrics",
        status="success",
    ).inc()
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    with REQUEST_LATENCY.labels(
        endpoint="/api/v1/query",
    ).time():
        start_time = time.time()
        try:
            result = await answer_query(
                question=request.question,
                top_k_vec=request.top_k_vec,
                top_k_bm25=request.top_k_bm25,
                rrf_k=request.rrf_k,
                final_k=request.k,
                provider=request.provider,
            )
            latency_ms = (time.time() - start_time) * 1000.0
            REQUEST_COUNT.labels(
                endpoint="/api/v1/query",
                status="success",
            ).inc()
            return QueryResponse(
                answer=result["answer"],
                contexts=result["contexts"],
                scores=result["scores"],
                latency_ms=latency_ms,
            )
        except Exception as e:
            ERROR_COUNT.labels(
                endpoint="/api/v1/query",
                error_type=type(e).__name__,
            ).inc()
            REQUEST_COUNT.labels(
                endpoint="/api/v1/query",
                status="error",
            ).inc()
            raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/ingest")
async def ingest(req: IngestRequest):
    """Ingest documents into the vector store."""
    try:
        client, coll = _get_chroma_collection()

        if req.reset:
            name = os.getenv("CHROMADB_COLLECTION", "rag_documents")
            client.delete_collection(name)
            _, coll = _get_chroma_collection()

        contents = [d.content for d in req.documents]
        ids = [str(uuid4()) for _ in contents]
        metadatas = [d.metadata for d in req.documents]
        embeddings = embedding_manager.embed_batch(contents)

        coll.add(ids=ids, documents=contents, embeddings=embeddings, metadatas=metadatas)

        REQUEST_COUNT.labels(
            endpoint="/api/v1/ingest",
            status="success",
        ).inc()

        logger.info(f"Ingested {len(ids)} documents into ChromaDB")
        return {"ok": True, "inserted": len(ids)}
    except Exception as e:
        ERROR_COUNT.labels(
            endpoint="/api/v1/ingest",
            error_type=type(e).__name__,
        ).inc()
        REQUEST_COUNT.labels(
            endpoint="/api/v1/ingest",
            status="error",
        ).inc()
        logger.error(f"Failed to ingest documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
