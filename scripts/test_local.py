#!/usr/bin/env python3
"""Local test runner for API verification.

This script:
1. Starts the API server locally
2. Initializes vector store (if empty)
3. Runs all health checks
4. Tests a sample query
5. Verifies scores are non-zero
6. Prints detailed diagnostics
"""

import os
import sys
import time
from pathlib import Path

import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class LocalTester:
    """Test local API deployment."""

    def __init__(self, port: int = 8000):
        """Initialize tester with local port."""
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.api_process = None

    def print_step(self, step: str, status: str = "INFO"):
        """Print test step."""
        emoji = {"INFO": "ℹ️", "SUCCESS": "✓", "ERROR": "✗", "WARN": "⚠"}
        print(f"\n{emoji.get(status, 'ℹ️')} {step}")

    def check_api_running(self) -> bool:
        """Check if API is already running."""
        try:
            response = requests.get(f"{self.base_url}/healthz", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def wait_for_api(self, timeout: int = 30) -> bool:
        """Wait for API to become ready."""
        self.print_step(f"Waiting for API to start (timeout: {timeout}s)...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/healthz", timeout=2)
                if response.status_code == 200:
                    self.print_step(
                        f"API is ready! Took {time.time() - start_time:.1f}s",
                        "SUCCESS",
                    )
                    return True
            except Exception:
                pass

            time.sleep(1)
            print(".", end="", flush=True)

        self.print_step(f"API failed to start within {timeout}s", "ERROR")
        return False

    def initialize_vector_store(self) -> bool:
        """Initialize vector store if empty."""
        self.print_step("Checking vector store status...")

        try:
            # Check status
            response = requests.get(f"{self.base_url}/api/v1/admin/vector-store/status", timeout=10)

            if response.status_code == 200:
                data = response.json()
                doc_count = data.get("document_count", 0)

                if doc_count > 0:
                    self.print_step(
                        f"Vector store already has {doc_count} documents",
                        "SUCCESS",
                    )
                    return True
                else:
                    self.print_step("Vector store is empty, initializing...", "WARN")

                    # Initialize
                    init_response = requests.post(
                        f"{self.base_url}/api/v1/admin/initialize",
                        json={"reset": False},
                        timeout=60,
                    )

                    if init_response.status_code == 200:
                        result = init_response.json()
                        self.print_step(
                            f"Vector store initialized with {result.get('count', 0)} documents",
                            "SUCCESS",
                        )
                        return True
                    else:
                        self.print_step(
                            f"Failed to initialize: {init_response.status_code}",
                            "ERROR",
                        )
                        return False
            else:
                self.print_step(f"Failed to check status: {response.status_code}", "ERROR")
                return False

        except Exception as e:
            self.print_step(f"Error initializing vector store: {e}", "ERROR")
            return False

    def test_health_endpoints(self) -> bool:
        """Test health endpoints."""
        self.print_step("Testing health endpoints...")

        endpoints = ["/healthz", "/api/v1/health", "/api/v1/health/ready"]
        all_passed = True

        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"  ✓ {endpoint}: {response.status_code}")
                else:
                    print(f"  ✗ {endpoint}: {response.status_code}")
                    all_passed = False
            except Exception as e:
                print(f"  ✗ {endpoint}: {e}")
                all_passed = False

        return all_passed

    def test_query(self) -> bool:
        """Test query endpoint with a sample query."""
        self.print_step("Testing query endpoint...")

        test_query = "What is Retrieval-Augmented Generation?"

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/query",
                json={"query": test_query},
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                confidence = data.get("confidence_score", 0)

                print(f"\n  Query: {test_query}")
                print(f"  Answer length: {len(answer)} chars")
                print(f"  Sources: {len(sources)}")
                print(f"  Confidence: {confidence:.3f}")

                # Check for non-zero scores
                if sources:
                    print("\n  Source scores:")
                    for i, source in enumerate(sources[:3], 1):
                        score = source.get("score", 0)
                        print(f"    {i}. Score: {score:.4f}")

                    has_nonzero = any(s.get("score", 0) > 0 for s in sources)
                    if has_nonzero:
                        self.print_step("Query test passed!", "SUCCESS")
                        return True
                    else:
                        self.print_step("All scores are zero!", "WARN")
                        return False
                else:
                    self.print_step("No sources returned!", "ERROR")
                    return False
            else:
                self.print_step(f"Query failed with status {response.status_code}", "ERROR")
                print(f"  Response: {response.text[:200]}")
                return False

        except Exception as e:
            self.print_step(f"Query test error: {e}", "ERROR")
            return False

    def run_diagnostics(self):
        """Run diagnostic checks."""
        self.print_step("Running diagnostics...")

        # Check environment
        print("\n  Environment:")
        print(f"    OPENAI_API_KEY: {'✓ Set' if os.getenv('OPENAI_API_KEY') else '✗ Not set'}")
        print(f"    CHROMA_PERSIST_DIR: {os.getenv('CHROMA_PERSIST_DIR', '.chroma (default)')}")
        print(f"    RATE_LIMIT_ENABLED: {os.getenv('RATE_LIMIT_ENABLED', 'true (default)')}")

        # Check vector store status
        try:
            response = requests.get(f"{self.base_url}/api/v1/admin/vector-store/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("\n  Vector Store:")
                print(f"    Status: {data.get('status')}")
                print(f"    Documents: {data.get('document_count')}")
                print(f"    Search working: {data.get('search_working')}")
        except Exception as e:
            print(f"\n  Vector Store: Error - {e}")

    def run_all_tests(self) -> bool:
        """Run all local tests."""
        print("\n" + "=" * 80)
        print("  LOCAL API TEST SUITE")
        print("=" * 80)

        # Check if API is already running
        already_running = self.check_api_running()

        if not already_running:
            self.print_step("API not running. Please start it manually with:")
            print(f"\n    $HOME/.local/bin/uv run uvicorn src.api.main:app --port {self.port}")
            print("\n  Or in development mode:")
            print(
                f"\n    $HOME/.local/bin/uv run uvicorn src.api.main:app --reload --port {self.port}"
            )
            return False

        self.print_step(f"API is running on port {self.port}", "SUCCESS")

        # Initialize vector store
        if not self.initialize_vector_store():
            return False

        # Test health endpoints
        if not self.test_health_endpoints():
            self.print_step("Health endpoint tests failed", "ERROR")
            return False

        # Test query
        if not self.test_query():
            self.print_step("Query test failed", "ERROR")
            return False

        # Run diagnostics
        self.run_diagnostics()

        # Success
        print("\n" + "=" * 80)
        print("  ✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\n  Next steps:")
        print("    1. Run deployment test: python scripts/test_deployment.py")
        print("    2. Deploy to Render")
        print("    3. Initialize production: python scripts/init_deployed_store.py")
        print("=" * 80 + "\n")

        return True


def main():
    """Run local tests."""
    port = int(os.getenv("PORT", "8000"))
    tester = LocalTester(port)
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
