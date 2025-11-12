import json
import random
from pathlib import Path

from dotenv import load_dotenv
from locust import HttpUser, between, task

load_dotenv()


class RAGPipelineUser(HttpUser):
    """Locust user for load testing the RAG pipeline."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Initialize the user with test data."""
        # Load test queries
        self.queries = self._load_queries()
        if not self.queries:
            # Default queries if file not found
            self.queries = [
                "What is machine learning?",
                "Explain natural language processing",
                "What are the types of machine learning?",
                "How does supervised learning work?",
                "What is tokenization in NLP?",
                "Describe reinforcement learning",
                "What are NLP applications?",
                "What is sentiment analysis?",
                "Explain unsupervised learning",
                "What challenges does NLP face?",
            ]

    def _load_queries(self):
        """Load queries from file."""
        queries = []

        # Try loading from queries.txt
        queries_file = Path("benchmarks/locust/queries.txt")
        if queries_file.exists():
            with open(queries_file) as f:
                queries = [line.strip() for line in f if line.strip()]

        # Try loading from eval dataset
        if not queries:
            eval_file = Path("data/eval/eval_dataset.json")
            if eval_file.exists():
                with open(eval_file) as f:
                    data = json.load(f)
                    queries = [item["question"] for item in data.get("questions", [])]

        return queries

    @task(1)
    def health_check(self):
        """Test the health endpoint."""
        with self.client.get("/healthz", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(10)
    def query_rag(self):
        """Test the main RAG query endpoint."""
        # Select a random query
        question = random.choice(self.queries)

        # Prepare request payload
        payload = {
            "question": question,
            "k": 4,
            "top_k_bm25": 8,
            "top_k_vec": 8,
            "rrf_k": 60,
            "provider": "openai",
        }

        # Make request
        with self.client.post("/api/v1/query", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Validate response structure
                    if all(key in data for key in ["answer", "contexts", "scores", "latency_ms"]):
                        response.success()
                    else:
                        response.failure("Invalid response structure")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Query failed: {response.status_code}")

    @task(2)
    def check_metrics(self):
        """Test the metrics endpoint."""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                # Verify it returns Prometheus format
                if "# HELP" in response.text or "# TYPE" in response.text:
                    response.success()
                else:
                    response.failure("Invalid metrics format")
            else:
                response.failure(f"Metrics check failed: {response.status_code}")
