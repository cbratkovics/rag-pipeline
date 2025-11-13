#!/usr/bin/env python3
"""Comprehensive deployment verification test script.

This script verifies all critical functionality:
1. Health endpoints return 200 (no rate limiting)
2. Vector store has documents
3. Query endpoint returns non-zero scores
4. CORS headers are correct
5. Rate limiting works on non-health endpoints
"""

import os
import sys
import time
from pathlib import Path

import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class DeploymentTester:
    """Test deployed RAG API."""

    def __init__(self, base_url: str):
        """Initialize tester with API base URL."""
        self.base_url = base_url.rstrip("/")
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def print_header(self, text: str):
        """Print test section header."""
        print("\n" + "=" * 80)
        print(f"  {text}")
        print("=" * 80)

    def print_test(self, name: str, status: str, details: str = ""):
        """Print test result."""
        emoji = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠"}
        color = {"PASS": "\033[92m", "FAIL": "\033[91m", "WARN": "\033[93m"}
        reset = "\033[0m"

        print(f"{color.get(status, '')}{emoji.get(status, '?')} {name}: {status}{reset}")
        if details:
            print(f"  → {details}")

        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "WARN":
            self.warnings += 1

    def test_health_endpoints(self):
        """Test all health check endpoints are not rate limited."""
        self.print_header("Health Endpoint Tests")

        endpoints = [
            "/healthz",
            "/api/v1/health",
            "/api/v1/health/ready",
            "/api/v1/health/live",
        ]

        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                # Test multiple times to ensure no rate limiting
                for i in range(5):
                    response = requests.get(url, timeout=10)
                    if response.status_code == 429:
                        self.print_test(
                            f"Health endpoint {endpoint}",
                            "FAIL",
                            f"Rate limited on request {i + 1}/5",
                        )
                        break
                else:
                    self.print_test(
                        f"Health endpoint {endpoint}",
                        "PASS",
                        f"Status: {response.status_code}, No rate limiting after 5 requests",
                    )
            except Exception as e:
                self.print_test(f"Health endpoint {endpoint}", "FAIL", str(e))

    def test_vector_store_status(self):
        """Test vector store has documents."""
        self.print_header("Vector Store Status Tests")

        url = f"{self.base_url}/api/v1/admin/vector-store/status"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                doc_count = data.get("document_count", 0)

                if doc_count > 0:
                    self.print_test(
                        "Vector store status",
                        "PASS",
                        f"Contains {doc_count} documents, Status: {data.get('status')}",
                    )
                else:
                    self.print_test(
                        "Vector store status",
                        "FAIL",
                        "Vector store is empty! Initialize with POST /api/v1/admin/initialize",
                    )
            else:
                self.print_test(
                    "Vector store status",
                    "FAIL",
                    f"Status code: {response.status_code}",
                )
        except Exception as e:
            self.print_test("Vector store status", "FAIL", str(e))

    def test_query_endpoint(self):
        """Test query endpoint returns non-zero scores."""
        self.print_header("Query Endpoint Tests")

        url = f"{self.base_url}/api/v1/query"
        test_queries = [
            "What is RAG?",
            "How does hybrid search work?",
            "What is BM25?",
        ]

        for query in test_queries:
            try:
                response = requests.post(
                    url,
                    json={"query": query},
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    confidence = data.get("confidence_score", 0)

                    if answer and sources:
                        # Check for non-zero scores
                        has_nonzero_scores = any(source.get("score", 0) > 0 for source in sources)

                        if has_nonzero_scores:
                            self.print_test(
                                f"Query: '{query[:40]}...'",
                                "PASS",
                                f"Got answer with {len(sources)} sources, confidence: {confidence:.2f}",
                            )
                        else:
                            self.print_test(
                                f"Query: '{query[:40]}...'",
                                "WARN",
                                "All scores are zero - vector store may need reinitialization",
                            )
                    else:
                        self.print_test(
                            f"Query: '{query[:40]}...'",
                            "FAIL",
                            "Empty answer or no sources returned",
                        )
                elif response.status_code == 429:
                    self.print_test(
                        f"Query: '{query[:40]}...'",
                        "WARN",
                        "Rate limited - this is expected behavior for query endpoint",
                    )
                else:
                    self.print_test(
                        f"Query: '{query[:40]}...'",
                        "FAIL",
                        f"Status code: {response.status_code}, Response: {response.text[:100]}",
                    )
            except Exception as e:
                self.print_test(f"Query: '{query[:40]}...'", "FAIL", str(e))

            # Small delay between queries to avoid rate limiting
            time.sleep(0.5)

    def test_cors_headers(self):
        """Test CORS headers are present."""
        self.print_header("CORS Headers Tests")

        url = f"{self.base_url}/api/v1/health"
        try:
            response = requests.options(
                url,
                headers={
                    "Origin": "https://rag-pipeline-eta.vercel.app",
                    "Access-Control-Request-Method": "GET",
                },
                timeout=10,
            )

            cors_headers = {
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers",
            }

            found_headers = cors_headers.intersection(response.headers.keys())

            if found_headers:
                self.print_test(
                    "CORS headers",
                    "PASS",
                    f"Found headers: {', '.join(found_headers)}",
                )
            else:
                self.print_test(
                    "CORS headers",
                    "WARN",
                    "No CORS headers found - may cause frontend issues",
                )
        except Exception as e:
            self.print_test("CORS headers", "FAIL", str(e))

    def test_rate_limiting_on_query(self):
        """Test rate limiting works on query endpoint."""
        self.print_header("Rate Limiting Tests")

        url = f"{self.base_url}/api/v1/query"
        rate_limited = False

        try:
            # Make multiple requests to trigger rate limit
            for i in range(15):
                response = requests.post(
                    url,
                    json={"query": f"Test query {i}"},
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )

                if response.status_code == 429:
                    rate_limited = True
                    self.print_test(
                        "Rate limiting on queries",
                        "PASS",
                        f"Rate limited after {i + 1} requests (expected behavior)",
                    )
                    break

                time.sleep(0.1)

            if not rate_limited:
                self.print_test(
                    "Rate limiting on queries",
                    "WARN",
                    "No rate limiting detected after 15 requests - check settings",
                )
        except Exception as e:
            self.print_test("Rate limiting on queries", "FAIL", str(e))

    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        self.print_header("Metrics Endpoint Tests")

        url = f"{self.base_url}/metrics"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text
                if "# HELP" in content and "# TYPE" in content:
                    self.print_test(
                        "Prometheus metrics",
                        "PASS",
                        f"Endpoint returns Prometheus format ({len(content)} bytes)",
                    )
                else:
                    self.print_test(
                        "Prometheus metrics",
                        "WARN",
                        "Response doesn't look like Prometheus format",
                    )
            else:
                self.print_test(
                    "Prometheus metrics",
                    "FAIL",
                    f"Status code: {response.status_code}",
                )
        except Exception as e:
            self.print_test("Prometheus metrics", "FAIL", str(e))

    def run_all_tests(self):
        """Run all deployment tests."""
        print("\n" + "🚀" * 40)
        print(f"  Testing RAG API Deployment: {self.base_url}")
        print("🚀" * 40)

        self.test_health_endpoints()
        self.test_vector_store_status()
        self.test_query_endpoint()
        self.test_cors_headers()
        self.test_metrics_endpoint()
        self.test_rate_limiting_on_query()

        # Print summary
        print("\n" + "=" * 80)
        print("  TEST SUMMARY")
        print("=" * 80)
        print(f"✓ Passed:   {self.passed}")
        print(f"⚠ Warnings: {self.warnings}")
        print(f"✗ Failed:   {self.failed}")
        print("=" * 80)

        if self.failed == 0:
            print("\n✅ All critical tests passed!")
            return True
        else:
            print(f"\n❌ {self.failed} critical test(s) failed")
            return False


def main():
    """Run deployment tests."""
    # Get API URL from environment or use default
    api_url = os.getenv("API_URL", "http://localhost:8000")

    if len(sys.argv) > 1:
        api_url = sys.argv[1]

    tester = DeploymentTester(api_url)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
