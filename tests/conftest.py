"""Test configuration and fixtures."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set protobuf workaround BEFORE any imports
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Set ALL required environment variables for testing
os.environ.setdefault("LLM_PROVIDER", "stub")
os.environ.setdefault("RAGAS_ENABLED", "false")
os.environ.setdefault("VECTOR_STORE_TYPE", "chromadb")
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

# Additional environment variables for complete configuration
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("CHROMA_PATH", "/tmp/test_chroma")
os.environ.setdefault("RERANKING_ENABLED", "false")
os.environ.setdefault("HYDE_ENABLED", "false")
os.environ.setdefault("ENABLE_METRICS", "false")
os.environ.setdefault("ENABLE_TRACING", "false")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("CACHE_TTL", "3600")
os.environ.setdefault("CACHE_TYPE", "redis")
os.environ.setdefault("MLFLOW_TRACKING_URI", "file:///tmp/mlflow")


@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock all external service connections for unit tests."""
    # Only mock services that are actually imported/used
    mocks = []
    
    # Try to mock each service conditionally
    try:
        import chromadb
        mocks.append(patch('chromadb.PersistentClient', MagicMock()))
    except ImportError:
        pass
    
    try:
        import redis
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = None
        mock_redis_instance.set.return_value = True
        mock_redis_instance.expire.return_value = True
        mock_redis_instance.delete.return_value = True
        mocks.append(patch('redis.asyncio.Redis', return_value=mock_redis_instance))
        mocks.append(patch('redis.Redis', return_value=mock_redis_instance))
    except ImportError:
        pass
    
    try:
        import psycopg2
        mocks.append(patch('psycopg2.connect', MagicMock()))
    except ImportError:
        pass
    
    try:
        import mlflow
        mocks.append(patch('mlflow.set_tracking_uri', return_value=None))
    except ImportError:
        pass
    
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
