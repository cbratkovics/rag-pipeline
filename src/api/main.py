"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from prometheus_client import make_asgi_app

from src.api.middleware import (
    add_correlation_id,
    add_process_time,
    rate_limit_middleware,
)
from src.api.routers import admin, experiments, feedback, health, metrics, query, query_hybrid
from src.core.config import get_settings
from src.infrastructure.cache import cache_manager
from src.infrastructure.database import db_manager
from src.infrastructure.logging import get_logger, setup_logging
from src.retrieval.vector_store import vector_store

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting RAG Pipeline application")

    # Validate OpenAI configuration on startup
    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY not configured - shutting down")
        raise ValueError(
            "OPENAI_API_KEY is required for production. This system requires real LLM capabilities."
        )

    logger.info(f"✓ OpenAI configured with model: {settings.openai_model}")

    # Initialize components
    await db_manager.initialize()
    await cache_manager.initialize()
    await vector_store.initialize()

    # Check vector store and warn if empty
    try:
        count = await vector_store.count_documents()
        if count == 0:
            logger.warning(
                "⚠️  Vector store is EMPTY! The API will start but queries will fail. "
                "Please initialize with: POST /api/v1/admin/initialize"
            )
        else:
            logger.info(f"✓ Vector store contains {count} documents")
    except Exception as e:
        logger.error(f"Failed to check vector store status: {e}")

    # Import and initialize other components
    from src.experiments.ab_testing import ab_test_manager

    await ab_test_manager.initialize()

    logger.info("All components initialized successfully")

    yield

    # Cleanup
    logger.info("Shutting down RAG Pipeline application")
    await cache_manager.close()
    await db_manager.close()
    logger.info("Cleanup completed")


# Create FastAPI app
app = FastAPI(
    title="Production RAG Pipeline",
    description="Production-grade RAG system with A/B testing and continuous learning",
    version="0.1.0",
    lifespan=lifespan,
)

# Get settings
settings = get_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(add_correlation_id)
app.middleware("http")(add_process_time)
if settings.rate_limit_enabled:
    app.middleware("http")(rate_limit_middleware)

# Include routers
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(query_hybrid.router, prefix="/api/v1", tags=["Query"])
app.include_router(experiments.router, prefix="/api/v1", tags=["Experiments"])
app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])
app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])

# Mount Prometheus metrics endpoint
if settings.prometheus_enabled:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/healthz")
async def healthz():
    """Simple health check endpoint for frontend compatibility."""
    return {"status": "ok", "service": "rag-pipeline"}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API documentation links."""
    return """
    <html>
        <head>
            <title>RAG Pipeline API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .links { margin-top: 20px; }
                .links a {
                    display: inline-block;
                    margin: 10px 20px 10px 0;
                    padding: 10px 20px;
                    background: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                }
                .links a:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <h1>Production RAG Pipeline API</h1>
            <p>A production-grade Retrieval-Augmented Generation system with A/B testing and continuous learning.</p>
            <div class="links">
                <a href="/docs">API Documentation</a>
                <a href="/redoc">Alternative Docs</a>
                <a href="/demo">Interactive Demo</a>
                <a href="/metrics">Prometheus Metrics</a>
            </div>
        </body>
    </html>
    """


@app.get("/demo", response_class=HTMLResponse)
async def demo():
    """Interactive demo interface."""
    return """
    <html>
        <head>
            <title>RAG Pipeline Demo</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { color: #333; margin-bottom: 10px; }
                .subtitle { color: #666; margin-bottom: 30px; }
                .query-section {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }
                textarea {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                    resize: vertical;
                }
                select, button {
                    padding: 10px 20px;
                    margin: 10px 10px 10px 0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                }
                button {
                    background: #007bff;
                    color: white;
                    border: none;
                    cursor: pointer;
                }
                button:hover { background: #0056b3; }
                button:disabled {
                    background: #ccc;
                    cursor: not-allowed;
                }
                .results {
                    margin-top: 20px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                }
                .metrics {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-top: 20px;
                }
                .metric-card {
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
                .metric-label {
                    color: #666;
                    font-size: 12px;
                    margin-bottom: 5px;
                }
                .metric-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                }
                .source {
                    background: white;
                    padding: 10px;
                    margin: 10px 0;
                    border-left: 3px solid #007bff;
                    border-radius: 4px;
                }
                .loading {
                    text-align: center;
                    padding: 20px;
                    color: #666;
                }
                .error {
                    background: #f8d7da;
                    color: #721c24;
                    padding: 10px;
                    border-radius: 4px;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>RAG Pipeline Interactive Demo</h1>
                <p class="subtitle">Test the production RAG system with real-time A/B testing and RAGAS evaluation</p>

                <div class="query-section">
                    <h3>Query Input</h3>
                    <textarea id="query" rows="3" placeholder="Enter your question here...">What are the latest advances in transformer architectures?</textarea>

                    <div style="margin-top: 15px;">
                        <label>Experiment Variant:</label>
                        <select id="variant">
                            <option value="auto">Auto (A/B Test)</option>
                            <option value="baseline">Baseline</option>
                            <option value="reranked">Reranked</option>
                            <option value="hybrid">Hybrid</option>
                            <option value="finetuned">Fine-tuned</option>
                        </select>

                        <label>Data Sources:</label>
                        <select id="source" multiple size="3">
                            <option value="arxiv" selected>ArXiv</option>
                            <option value="wikipedia" selected>Wikipedia</option>
                            <option value="pubmed">PubMed</option>
                        </select>
                    </div>

                    <button id="submitBtn" onclick="submitQuery()">Submit Query</button>
                    <button onclick="clearResults()">Clear</button>
                </div>

                <div id="results" style="display:none;">
                    <h3>Results</h3>
                    <div id="answer"></div>

                    <div class="metrics" id="metrics"></div>

                    <div id="sources"></div>

                    <div id="evaluation"></div>
                </div>
            </div>

            <script>
                async function submitQuery() {
                    const query = document.getElementById('query').value;
                    const variant = document.getElementById('variant').value;
                    const sourceSelect = document.getElementById('source');
                    const sources = Array.from(sourceSelect.selectedOptions).map(opt => opt.value);

                    if (!query.trim()) {
                        alert('Please enter a query');
                        return;
                    }

                    const submitBtn = document.getElementById('submitBtn');
                    const resultsDiv = document.getElementById('results');
                    const answerDiv = document.getElementById('answer');

                    submitBtn.disabled = true;
                    resultsDiv.style.display = 'block';
                    answerDiv.innerHTML = '<div class="loading">Processing query...</div>';

                    try {
                        const response = await fetch('/api/v1/query', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                query: query,
                                experiment_variant: variant === 'auto' ? null : variant,
                                metadata_filters: sources.length > 0 ? { source: sources } : {}
                            })
                        });

                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }

                        const data = await response.json();
                        displayResults(data);

                    } catch (error) {
                        answerDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
                    } finally {
                        submitBtn.disabled = false;
                    }
                }

                function displayResults(data) {
                    // Display answer
                    document.getElementById('answer').innerHTML = `
                        <h4>Answer:</h4>
                        <p>${data.answer}</p>
                    `;

                    // Display metrics
                    const metricsHtml = `
                        <div class="metric-card">
                            <div class="metric-label">Experiment Variant</div>
                            <div class="metric-value">${data.experiment_variant}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Confidence Score</div>
                            <div class="metric-value">${(data.confidence_score * 100).toFixed(1)}%</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Processing Time</div>
                            <div class="metric-value">${data.processing_time_ms.toFixed(0)}ms</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Token Count</div>
                            <div class="metric-value">${data.token_count}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Cost (USD)</div>
                            <div class="metric-value">$${data.cost_usd.toFixed(4)}</div>
                        </div>
                    `;
                    document.getElementById('metrics').innerHTML = metricsHtml;

                    // Display sources
                    if (data.sources && data.sources.length > 0) {
                        let sourcesHtml = '<h4>Sources:</h4>';
                        data.sources.forEach((source, i) => {
                            sourcesHtml += `
                                <div class="source">
                                    <strong>Source ${i + 1}:</strong> ${source.document.title || 'Untitled'}<br>
                                    <small>Score: ${(source.score * 100).toFixed(1)}% | ${source.document.source}</small><br>
                                    <p>${source.document.content.substring(0, 200)}...</p>
                                </div>
                            `;
                        });
                        document.getElementById('sources').innerHTML = sourcesHtml;
                    }

                    // Display evaluation metrics if available
                    if (data.evaluation_metrics) {
                        const evalHtml = `
                            <h4>RAGAS Evaluation:</h4>
                            <div class="metrics">
                                <div class="metric-card">
                                    <div class="metric-label">Context Relevancy</div>
                                    <div class="metric-value">${(data.evaluation_metrics.context_relevancy * 100).toFixed(1)}%</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-label">Answer Faithfulness</div>
                                    <div class="metric-value">${(data.evaluation_metrics.answer_faithfulness * 100).toFixed(1)}%</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-label">Answer Relevancy</div>
                                    <div class="metric-value">${(data.evaluation_metrics.answer_relevancy * 100).toFixed(1)}%</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-label">Overall Score</div>
                                    <div class="metric-value">${(data.evaluation_metrics.overall_score * 100).toFixed(1)}%</div>
                                </div>
                            </div>
                        `;
                        document.getElementById('evaluation').innerHTML = evalHtml;
                    }
                }

                function clearResults() {
                    document.getElementById('results').style.display = 'none';
                    document.getElementById('query').value = '';
                }
            </script>
        </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
