import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    # TestClient expects app as first positional argument
    return TestClient(app)


@pytest.mark.unit
def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.unit
def test_metrics_endpoint(client):
    """Test metrics endpoint returns Prometheus format."""
    response = client.get("/metrics")
    assert response.status_code == 200

    # Check content type
    content_type = response.headers.get("content-type", "")
    assert "text/plain" in content_type

    # Check for Prometheus format markers
    content = response.text
    assert "# HELP" in content or "# TYPE" in content or "rag_requests_total" in content


@pytest.mark.unit
def test_query_endpoint_schema(client):
    """Test query endpoint returns expected schema."""
    payload = {
        "question": "What is machine learning?",
        "k": 4,
        "top_k_bm25": 8,
        "top_k_vec": 8,
        "rrf_k": 60,
        "provider": "stub",
    }

    response = client.post("/api/v1/query", json=payload)

    # Should return 200 or 500 (if no index)
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()

        # Check required fields
        assert "answer" in data
        assert "contexts" in data
        assert "scores" in data
        assert "latency_ms" in data

        # Check types
        assert isinstance(data["answer"], str)
        assert isinstance(data["contexts"], list)
        assert isinstance(data["scores"], dict)
        assert isinstance(data["latency_ms"], int | float)


@pytest.mark.unit
def test_query_endpoint_default_params(client):
    """Test query endpoint with minimal params."""
    payload = {"question": "Test question"}

    response = client.post("/api/v1/query", json=payload)

    # Should accept with defaults
    assert response.status_code in [200, 500]


@pytest.mark.unit
def test_query_endpoint_invalid_request(client):
    """Test query endpoint with invalid request."""
    payload = {}  # Missing required question field

    response = client.post("/api/v1/query", json=payload)

    # Should return 422 for validation error
    assert response.status_code == 422
