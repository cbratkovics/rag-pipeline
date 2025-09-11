"""Integration tests for the complete RAG pipeline."""

import time

import pytest
import requests

BASE_URL = "http://localhost:8000"


class TestFullPipeline:
    """Test the complete RAG pipeline flow."""

    def test_health_endpoint(self):
        """Test that the health endpoint is accessible."""
        response = requests.get(f"{BASE_URL}/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_metrics_endpoint(self):
        """Test that the metrics endpoint returns Prometheus format."""
        response = requests.get(f"{BASE_URL}/metrics")
        assert response.status_code == 200
        assert "# HELP" in response.text or "# TYPE" in response.text

    def test_query_baseline(self):
        """Test querying with baseline variant."""
        payload = {
            "question": "What is machine learning?",
            "k": 4,
            "top_k_bm25": 8,
            "top_k_vec": 8,
            "rrf_k": 60,
            "provider": "stub",
        }

        response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
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
        assert isinstance(data["latency_ms"], (int, float))

        # Verify contexts were retrieved
        assert len(data["contexts"]) > 0
        assert len(data["contexts"]) <= payload["k"]

    def test_query_with_different_parameters(self):
        """Test querying with different retrieval parameters."""
        test_cases = [
            {"k": 2, "top_k_bm25": 5, "top_k_vec": 5},
            {"k": 5, "top_k_bm25": 10, "top_k_vec": 10},
            {"k": 3, "top_k_bm25": 6, "top_k_vec": 8, "rrf_k": 30},
        ]

        for params in test_cases:
            payload = {
                "question": "What is Natural Language Processing?",
                "provider": "stub",
                **params,
            }

            response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
            assert response.status_code == 200

            data = response.json()
            assert len(data["contexts"]) <= params["k"]

    def test_query_different_questions(self):
        """Test the system with various question types."""
        questions = [
            "What is machine learning?",
            "Explain RAG systems",
            "What are vector databases?",
            "How does semantic search work?",
            "What is BM25?",
        ]

        for question in questions:
            payload = {"question": question, "k": 3, "provider": "stub"}

            response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
            assert response.status_code == 200

            data = response.json()
            assert data["answer"]
            assert data["contexts"]

    def test_concurrent_requests(self):
        """Test handling concurrent requests."""
        import concurrent.futures

        def make_request(question):
            payload = {"question": question, "k": 3, "provider": "stub"}
            response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
            return response.status_code, response.json()

        questions = ["What is ML?", "What is NLP?", "What is RAG?"] * 3

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, q) for q in questions]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(status == 200 for status, _ in results)
        assert all("answer" in data for _, data in results)

    def test_empty_query_handling(self):
        """Test handling of empty or invalid queries."""
        # Empty question
        payload = {"question": "", "k": 3, "provider": "stub"}

        response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
        # Should either handle gracefully or return 422
        assert response.status_code in [200, 422]

    def test_response_scores(self):
        """Verify that scoring metrics are properly calculated."""
        payload = {
            "question": "What is retrieval-augmented generation?",
            "k": 4,
            "provider": "stub",
        }

        response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
        assert response.status_code == 200

        data = response.json()
        scores = data["scores"]

        # Check that all expected score types are present
        assert "hybrid" in scores
        assert "bm25" in scores
        assert "vector" in scores

        # Scores should be numeric
        assert isinstance(scores["hybrid"], (int, float))
        assert isinstance(scores["bm25"], (int, float))
        assert isinstance(scores["vector"], (int, float))

    def test_latency_measurement(self):
        """Verify that latency is properly measured."""
        payload = {"question": "What is machine learning?", "k": 3, "provider": "stub"}

        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
        request_time = (time.time() - start_time) * 1000

        assert response.status_code == 200

        data = response.json()
        reported_latency = data["latency_ms"]

        # Reported latency should be positive and less than total request time
        assert reported_latency > 0
        assert reported_latency <= request_time

    def test_stub_provider(self):
        """Test that stub provider works correctly."""
        payload = {"question": "Test question for stub", "k": 2, "provider": "stub"}

        response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Stub should return an answer
        assert data["answer"]
        assert "Based on" in data["answer"] or "cannot find" in data["answer"]


class TestABTesting:
    """Test A/B testing functionality."""

    def test_variant_selection(self):
        """Test that different variants can be selected."""
        # This would require A/B testing implementation
        # For now, just verify the basic query works
        payload = {"question": "What is A/B testing?", "k": 3, "provider": "stub"}

        response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_json(self):
        """Test handling of invalid JSON payload."""
        response = requests.post(
            f"{BASE_URL}/api/v1/query",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]

    def test_missing_required_field(self):
        """Test handling of missing required fields."""
        payload = {
            # Missing 'question' field
            "k": 3
        }

        response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
        assert response.status_code == 422

    def test_invalid_parameter_values(self):
        """Test handling of invalid parameter values."""
        test_cases = [
            {"question": "Test", "k": -1},  # Negative k
            {"question": "Test", "k": 1000},  # Very large k
            {"question": "Test", "top_k_bm25": -5},  # Negative top_k
        ]

        for payload in test_cases:
            response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
            # Should either handle gracefully or return validation error
            assert response.status_code in [200, 422]


def test_api_availability():
    """Quick test to verify API is running."""
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        return response.status_code == 200
    except:
        return False


if __name__ == "__main__":
    # Check if API is running
    if not test_api_availability():
        print("ERROR: API is not running at http://localhost:8000")
        print("Please start the API with: make run")
        exit(1)

    # Run tests
    pytest.main([__file__, "-v"])
