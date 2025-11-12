import os
import time
import warnings
from contextlib import asynccontextmanager

import structlog
import uvicorn
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
from src.retrieval.vector_store import vector_store

warnings.filterwarnings("ignore", category=DeprecationWarning, module="opentelemetry")

load_dotenv()

logger = structlog.get_logger()


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
        "stub",
        description="LLM provider: 'stub' or 'openai'",
    )


class QueryResponse(BaseModel):
    answer: str
    contexts: list[str]
    scores: dict
    latency_ms: float


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


if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
