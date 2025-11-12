"""Integration tests for the complete RAG pipeline."""

import concurrent.futures
import time

import pytest


@pytest.mark.integration
class TestFullPipeline:
    """Test the complete RAG pipeline flow."""

    def test_health_endpoint(self, test_client):
        """Test that the health endpoint is accessible."""
        response = test_client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_metrics_endpoint(self, test_client):
        """Test that the metrics endpoint returns Prometheus format."""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        assert "# HELP" in response.text or "# TYPE" in response.text

    def test_query_baseline(self, test_client):
        """Test querying with baseline variant."""
        payload = {
            "question": "What is machine learning?",
            "k": 4,
            "top_k_bm25": 8,
            "top_k_vec": 8,
            "rrf_k": 60,
            "provider": "openai",
        }

        response = test_client.post("/api/v1/query", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "answer" in data
        assert "contexts" in data
        assert "scores" in data
        assert "latency_ms" in data

        # Verify response structure
        assert isinstance(data["answer"], str)
        assert isinstance(data["contexts"], list)
        assert isinstance(data["scores"], dict)
        assert isinstance(data["latency_ms"], int | float)

        # Verify contexts were retrieved
        assert len(data["contexts"]) > 0
        assert len(data["contexts"]) <= payload["k"]

    def test_query_with_different_parameters(self, test_client):
        """Test querying with different retrieval parameters."""
        test_cases = [
            {"k": 2, "top_k_bm25": 5, "top_k_vec": 5},
            {"k": 5, "top_k_bm25": 10, "top_k_vec": 10},
            {"k": 3, "top_k_bm25": 6, "top_k_vec": 8, "rrf_k": 30},
        ]

        for params in test_cases:
            payload = {
                "question": "What is Natural Language Processing?",
                "provider": "openai",
                **params,
            }

            response = test_client.post("/api/v1/query", json=payload)
            assert response.status_code == 200

            data = response.json()
            assert len(data["contexts"]) <= params["k"]

    def test_query_different_questions(self, test_client):
        """Test the system with various question types."""
        questions = [
            "What is machine learning?",
            "Explain RAG systems",
            "What are vector databases?",
            "How does semantic search work?",
            "What is BM25?",
        ]

        for question in questions:
            payload = {"question": question, "k": 3, "provider": "openai"}

            response = test_client.post("/api/v1/query", json=payload)
            assert response.status_code == 200

            data = response.json()
            assert data["answer"]
            assert data["contexts"]

    def test_concurrent_requests(self, test_client):
        """Test handling concurrent requests."""

        def make_request(question):
            payload = {"question": question, "k": 3, "provider": "openai"}
            response = test_client.post("/api/v1/query", json=payload)
            return response.status_code, response.json()

        questions = ["What is ML?", "What is NLP?", "What is RAG?"] * 3

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, q) for q in questions]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(status == 200 for status, _ in results)
        assert all("answer" in data for _, data in results)

    def test_empty_query_handling(self, test_client):
        """Test handling of empty or invalid queries."""
        # Empty question
        payload = {"question": "", "k": 3, "provider": "openai"}

        response = test_client.post("/api/v1/query", json=payload)
        # Should either handle gracefully or return 422
        assert response.status_code in [200, 422]

    def test_response_scores(self, test_client):
        """Verify that scoring metrics are properly calculated."""
        payload = {
            "question": "What is retrieval-augmented generation?",
            "k": 4,
            "provider": "openai",
        }

        response = test_client.post("/api/v1/query", json=payload)
        assert response.status_code == 200

        data = response.json()
        scores = data["scores"]

        # Check that all expected score types are present
        assert "hybrid" in scores
        assert "bm25" in scores
        assert "vector" in scores

        # Scores should be numeric
        assert isinstance(scores["hybrid"], int | float)
        assert isinstance(scores["bm25"], int | float)
        assert isinstance(scores["vector"], int | float)

    def test_latency_measurement(self, test_client):
        """Verify that latency is properly measured."""
        payload = {"question": "What is machine learning?", "k": 3, "provider": "openai"}

        start_time = time.time()
        response = test_client.post("/api/v1/query", json=payload)
        request_time = (time.time() - start_time) * 1000

        assert response.status_code == 200

        data = response.json()
        reported_latency = data["latency_ms"]

        # Reported latency should be positive and less than total request time
        assert reported_latency > 0
        assert reported_latency <= request_time + 100  # Add buffer for timing variations

    def test_openai_provider(self, test_client):
        """Test that OpenAI provider works correctly."""
        payload = {"question": "Test question for OpenAI", "k": 2, "provider": "openai"}

        response = test_client.post("/api/v1/query", json=payload)
        assert response.status_code == 200

        data = response.json()
        # OpenAI should return an answer
        assert data["answer"]
        # The mock returns a fixed answer
        assert (
            "test answer" in data["answer"].lower() or "retrieved context" in data["answer"].lower()
        )


@pytest.mark.integration
class TestABTesting:
    """Test A/B testing functionality."""

    def test_variant_selection(self, test_client):
        """Test that different variants can be selected."""
        # This would require A/B testing implementation
        # For now, just verify the basic query works
        payload = {"question": "What is A/B testing?", "k": 3, "provider": "openai"}

        response = test_client.post("/api/v1/query", json=payload)
        assert response.status_code == 200


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_json(self, test_client):
        """Test handling of invalid JSON payload."""
        response = test_client.post(
            "/api/v1/query",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]

    def test_missing_required_field(self, test_client):
        """Test handling of missing required fields."""
        payload = {
            # Missing 'question' field
            "k": 3
        }

        response = test_client.post("/api/v1/query", json=payload)
        assert response.status_code == 422

    def test_invalid_parameter_values(self, test_client):
        """Test handling of invalid parameter values."""
        test_cases = [
            {"question": "Test", "k": -1},  # Negative k
            {"question": "Test", "k": 1000},  # Very large k
            {"question": "Test", "top_k_bm25": -5},  # Negative top_k
        ]

        for payload in test_cases:
            response = test_client.post("/api/v1/query", json=payload)
            # Should either handle gracefully or return validation error
            assert response.status_code in [200, 422]


@pytest.mark.integration
@pytest.mark.skip(reason="src/api/main.py has complex initialization dependencies")
class TestSrcAPIEndpoints:
    """Test endpoints for src/api/main.py if available."""

    def test_src_health_endpoint(self, test_src_client):
        """Test that the src API health endpoint is accessible."""
        # Try different possible health endpoints
        for endpoint in ["/healthz", "/api/v1/health"]:
            response = test_src_client.get(endpoint)
            if response.status_code == 200:
                break
        # At least one should work
        assert response.status_code == 200

    def test_src_root_endpoint(self, test_src_client):
        """Test that the src API root endpoint returns HTML."""
        response = test_src_client.get("/")
        assert response.status_code == 200
        assert "RAG Pipeline" in response.text
