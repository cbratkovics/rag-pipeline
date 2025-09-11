import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

from src.rag.pipeline import answer_query

load_dotenv()

app = FastAPI(title="RAG Pipeline API", version="0.1.0")

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:8000"]')
app.add_middleware(
    CORSMiddleware,
    allow_origins=eval(cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter("rag_requests_total", "Total requests", ["endpoint", "status"])
REQUEST_LATENCY = Histogram("rag_request_duration_seconds", "Request latency", ["endpoint"])
ERROR_COUNT = Counter("rag_errors_total", "Total errors", ["endpoint", "error_type"])

# OpenTelemetry setup
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

span_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)  # type: ignore[attr-defined]

FastAPIInstrumentor.instrument_app(app)


class QueryRequest(BaseModel):
    question: str = Field(..., description="The question to answer")
    k: int = Field(4, description="Number of final documents to retrieve")
    top_k_bm25: int = Field(8, description="Number of BM25 results to retrieve")
    top_k_vec: int = Field(8, description="Number of vector search results to retrieve")
    rrf_k: int = Field(60, description="RRF K parameter for fusion")
    provider: str = Field("stub", description="LLM provider: 'stub' or 'openai'")


class QueryResponse(BaseModel):
    answer: str
    contexts: list[str]
    scores: dict
    latency_ms: float


@app.get("/healthz")
async def health_check():
    REQUEST_COUNT.labels(endpoint="/healthz", status="success").inc()
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    REQUEST_COUNT.labels(endpoint="/metrics", status="success").inc()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    with REQUEST_LATENCY.labels(endpoint="/api/v1/query").time():
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

            latency_ms = (time.time() - start_time) * 1000

            REQUEST_COUNT.labels(endpoint="/api/v1/query", status="success").inc()

            return QueryResponse(
                answer=result["answer"],
                contexts=result["contexts"],
                scores=result["scores"],
                latency_ms=latency_ms,
            )

        except Exception as e:
            ERROR_COUNT.labels(endpoint="/api/v1/query", error_type=type(e).__name__).inc()
            REQUEST_COUNT.labels(endpoint="/api/v1/query", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
