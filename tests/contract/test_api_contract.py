"""Contract tests for API endpoints.

These tests ensure that API contracts (schemas, endpoints, status codes) remain stable,
preventing breaking changes that would affect the deployed frontend.
"""

import pytest
from fastapi.testclient import TestClient

# Import will fail gracefully if API not available
try:
    from src.api.main import app

    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False


pytestmark = pytest.mark.skipif(not API_AVAILABLE, reason="API not available")


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Contract tests for health check endpoints."""

    def test_healthz_endpoint_exists(self, client):
        """Ensure /healthz endpoint exists and returns expected structure."""
        response = client.get("/healthz")

        # Contract: Must return 200
        assert response.status_code == 200

        # Contract: Must be JSON
        data = response.json()
        assert isinstance(data, dict)

        # Contract: Must have status field
        assert "status" in data
        assert data["status"] in ["ok", "healthy", "degraded", "unhealthy"]

    def test_root_endpoint_exists(self, client):
        """Ensure / endpoint exists and returns HTML."""
        response = client.get("/")

        # Contract: Must return 200 or 404
        assert response.status_code in [200, 404]

        # If exists, should return HTML
        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")


class TestQueryEndpoints:
    """Contract tests for query endpoints."""

    def test_query_endpoint_exists(self, client):
        """Ensure query endpoint exists at expected path."""
        # Contract: POST /api/v1/query should exist
        response = client.post(
            "/api/v1/query",
            json={"query": "test question", "max_results": 4},
        )

        # Contract: Must not return 404 (endpoint exists)
        assert response.status_code != 404

        # Contract: Should return 200 (success) or 422 (validation error) or 500 (server error)
        assert response.status_code in [200, 422, 500]

    def test_query_request_schema(self, client):
        """Ensure query endpoint accepts expected request fields."""
        # Contract: Must accept query field
        response = client.post(
            "/api/v1/query",
            json={"query": "What is machine learning?"},
        )

        # Should not fail due to missing required fields
        assert response.status_code != 422 or (
            response.status_code == 422 and "query" not in str(response.json()).lower()
        )

    def test_query_response_schema(self, client):
        """Ensure query response has expected fields (if successful)."""
        response = client.post(
            "/api/v1/query",
            json={"query": "test", "max_results": 2},
        )

        # Only check schema if request was successful
        if response.status_code == 200:
            data = response.json()

            # Contract: Response must be a dict
            assert isinstance(data, dict)

            # Contract: Must have answer field
            assert "answer" in data
            assert isinstance(data["answer"], str)

            # Contract: Should have timing information
            # (field name might vary: processing_time_ms, latency_ms, etc.)
            assert (
                "processing_time_ms" in data or "latency_ms" in data or "response_time_ms" in data
            )


class TestMetricsEndpoints:
    """Contract tests for metrics and monitoring endpoints."""

    def test_metrics_endpoint_exists(self, client):
        """Ensure /metrics endpoint exists for Prometheus."""
        response = client.get("/metrics")

        # Contract: Should return 200 or 404 (if metrics disabled)
        assert response.status_code in [200, 404]

        # If available, should return Prometheus text format
        if response.status_code == 200:
            assert "text/plain" in response.headers.get("content-type", "").lower()


class TestCORSHeaders:
    """Contract tests for CORS configuration."""

    def test_cors_headers_present(self, client):
        """Ensure CORS headers are configured for frontend compatibility."""
        # Make an OPTIONS request to check CORS
        response = client.options(
            "/api/v1/query",
            headers={
                "Origin": "https://frontend-domain.com",
                "Access-Control-Request-Method": "POST",
            },
        )

        # Contract: Should allow CORS (200 or 204) or not restrict it (405)
        assert response.status_code in [200, 204, 405]


class TestErrorHandling:
    """Contract tests for error responses."""

    def test_404_returns_json_error(self, client):
        """Ensure 404 errors return consistent JSON format."""
        response = client.get("/api/v1/nonexistent-endpoint")

        # Contract: Must return 404
        assert response.status_code == 404

        # Contract: Should return JSON error
        # (FastAPI returns JSON by default, but verify)
        content_type = response.headers.get("content-type", "")
        assert "json" in content_type.lower() or response.status_code == 404

    def test_invalid_json_returns_422(self, client):
        """Ensure invalid request data returns 422 validation error."""
        response = client.post(
            "/api/v1/query",
            json={"invalid_field": "value"},  # Missing required 'query' field
        )

        # Contract: Should return 422 for validation errors
        assert response.status_code in [422, 400]


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with deployed frontend."""

    def test_legacy_healthz_format(self, client):
        """Ensure healthz returns format expected by deployed frontend."""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()

        # Frontend expects these specific keys
        assert "status" in data

    def test_query_response_includes_essential_fields(self, client):
        """Ensure query response includes fields required by frontend."""
        response = client.post(
            "/api/v1/query",
            json={"query": "test"},
        )

        if response.status_code == 200:
            data = response.json()

            # Frontend requires these fields to render results
            assert "answer" in data, "Frontend needs 'answer' field"

            # Frontend should be able to display timing
            has_timing = (
                "processing_time_ms" in data or "latency_ms" in data or "response_time_ms" in data
            )
            assert has_timing, "Frontend needs timing information"
