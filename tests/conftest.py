"""Test configuration and fixtures."""

import importlib.util
import os
import sys
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set protobuf workaround BEFORE any imports
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Set ALL required environment variables for testing
os.environ.setdefault("RAGAS_ENABLED", "false")
os.environ.setdefault("VECTOR_STORE_TYPE", "qdrant")
os.environ.setdefault("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("API_HOST", "127.0.0.1")
os.environ.setdefault("API_PORT", "8000")

# OpenAI configuration - REQUIRED for production (mocked in tests)
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing-only")
os.environ.setdefault("OPENAI_MODEL", "gpt-3.5-turbo")
os.environ.setdefault("CHROMA_PATH", "/tmp/test_chroma")
os.environ.setdefault("RERANKING_ENABLED", "false")
os.environ.setdefault("HYDE_ENABLED", "false")
os.environ.setdefault("ENABLE_METRICS", "false")
os.environ.setdefault("ENABLE_TRACING", "false")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("CACHE_TTL", "3600")
os.environ.setdefault("CACHE_TYPE", "redis")
os.environ.setdefault("MLFLOW_TRACKING_URI", "file:///tmp/mlflow")
os.environ.setdefault("PROMETHEUS_ENABLED", "false")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("CORS_ORIGINS", '["*"]')


@pytest.fixture(autouse=True)
def mock_openai_for_tests():
    """Always mock OpenAI in tests to avoid API costs."""
    # Mock ChatOpenAI from langchain_openai
    with patch("langchain_openai.ChatOpenAI") as mock_openai:
        mock_instance = MagicMock()

        # Mock ainvoke for async calls
        async def mock_ainvoke(messages, *args, **kwargs):
            if isinstance(messages, str):
                content = "Test response from mocked OpenAI"
            else:
                content = "Test response from mocked OpenAI"

            mock_response = MagicMock()
            mock_response.content = content
            return mock_response

        mock_instance.ainvoke = mock_ainvoke
        mock_instance.invoke = MagicMock(return_value=MagicMock(content="Test response"))
        mock_instance.predict = MagicMock(return_value="Test response")

        mock_openai.return_value = mock_instance
        yield mock_instance


@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock all external service connections for unit tests."""
    # Only mock services that are actually imported/used
    mocks = []

    # Mock ChromaDB if available
    if importlib.util.find_spec("chromadb"):
        mocks.append(patch("chromadb.PersistentClient", MagicMock()))

    # Mock Redis if available
    if importlib.util.find_spec("redis"):
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = None
        mock_redis_instance.set.return_value = True
        mock_redis_instance.expire.return_value = True
        mock_redis_instance.delete.return_value = True
        mocks.append(patch("redis.asyncio.Redis", return_value=mock_redis_instance))
        mocks.append(patch("redis.Redis", return_value=mock_redis_instance))

    # Mock PostgreSQL if available
    if importlib.util.find_spec("psycopg2"):
        mocks.append(patch("psycopg2.connect", MagicMock()))

    # Mock MLflow if available
    if importlib.util.find_spec("mlflow"):
        mocks.append(patch("mlflow.set_tracking_uri", return_value=None))

    # Enter all mocks
    for mock in mocks:
        mock.__enter__()

    yield

    # Exit all mocks
    for mock in reversed(mocks):
        mock.__exit__(None, None, None)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    mock_client = MagicMock()
    mock_client.generate.return_value = "Mocked LLM response"
    mock_client.embed.return_value = [0.1] * 768  # Mock embedding vector
    return mock_client


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    mock_store = MagicMock()
    mock_store.search.return_value = [
        {"id": "1", "text": "Test document 1", "score": 0.9},
        {"id": "2", "text": "Test document 2", "score": 0.8},
    ]
    mock_store.add.return_value = True
    mock_store.delete.return_value = True
    return mock_store


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "What is the meaning of life?"


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {"id": "1", "text": "The meaning of life is 42.", "metadata": {"source": "test1"}},
        {"id": "2", "text": "Life is about happiness.", "metadata": {"source": "test2"}},
        {"id": "3", "text": "To live is to learn.", "metadata": {"source": "test3"}},
    ]


@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing."""
    return {
        "1": [0.1] * 768,
        "2": [0.2] * 768,
        "3": [0.3] * 768,
    }


@pytest.fixture
def mock_rag_pipeline():
    """Mock the RAG pipeline for testing."""

    # Create a coroutine mock for answer_query
    async def mock_answer_query(*args, **kwargs):
        # Get the k parameter from kwargs, default to 3
        k = kwargs.get("final_k", kwargs.get("k", 3))

        # Create contexts based on k value
        all_contexts = [
            "Context 1: Machine learning is a subset of AI.",
            "Context 2: Deep learning uses neural networks.",
            "Context 3: Transformers revolutionized NLP.",
            "Context 4: Natural language processing is key.",
            "Context 5: RAG combines retrieval and generation.",
        ]

        contexts = all_contexts[: min(k, len(all_contexts))]

        return {
            "answer": "This is a test answer based on the retrieved context.",
            "contexts": contexts,
            "scores": {
                "hybrid": 0.85,
                "bm25": 0.75,
                "vector": 0.90,
            },
        }

    with patch("api.main.answer_query", mock_answer_query):
        yield mock_answer_query


@pytest.fixture
def test_app():
    """Create test FastAPI app for api/main.py."""
    # Import here to avoid circular imports
    from api.main import app

    # The app is already configured
    return app


@pytest.fixture
def test_client(test_app, mock_rag_pipeline) -> Generator[TestClient, None, None]:
    """Create test client for api/main.py."""
    with TestClient(test_app) as client:
        yield client


@pytest_asyncio.fixture
async def async_test_client(test_app, mock_rag_pipeline) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for api/main.py."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


# Remove the mock_src_infrastructure fixture as it's now integrated into test_src_app


@pytest.fixture
def test_src_app():
    """Create test FastAPI app for src/api/main.py."""
    # Mock vector store
    with patch("src.retrieval.vector_store.QdrantVectorStore") as mock_qdrant_class:
        mock_vector_instance = AsyncMock()
        mock_vector_instance.initialize = AsyncMock(return_value=None)
        mock_vector_instance.search = AsyncMock(return_value=[])
        mock_qdrant_class.return_value = mock_vector_instance

        # Mock the rag_pipeline instance after it's created
        with patch("src.retrieval.rag_pipeline.rag_pipeline") as mock_rag:
            mock_rag.process_query = AsyncMock(
                return_value={
                    "answer": "Test answer",
                    "sources": [],
                    "confidence_score": 0.9,
                    "processing_time_ms": 100,
                    "token_count": 50,
                    "cost_usd": 0.001,
                }
            )

            with patch("src.infrastructure.database.db_manager") as mock_db:
                mock_db.initialize = AsyncMock(return_value=None)
                mock_db.close = AsyncMock(return_value=None)

                with patch("src.infrastructure.cache.cache_manager") as mock_cache:
                    mock_cache.initialize = AsyncMock(return_value=None)
                    mock_cache.close = AsyncMock(return_value=None)

                    with patch("src.experiments.ab_testing.ab_test_manager") as mock_ab:
                        mock_ab.initialize = AsyncMock(return_value=None)

                        # Import app after all mocks are set up
                        from src.api.main import app

                        return app


@pytest.fixture
def test_src_client(test_src_app) -> Generator[TestClient, None, None]:
    """Create test client for src/api/main.py."""
    with TestClient(test_src_app) as client:
        yield client


@pytest_asyncio.fixture
async def async_test_src_client(test_src_app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for src/api/main.py."""
    async with AsyncClient(app=test_src_app, base_url="http://test") as client:
        yield client
