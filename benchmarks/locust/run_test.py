#!/usr/bin/env python3
"""Simple load test runner that generates evidence artifacts."""

import concurrent.futures
import json
import random
import time
from datetime import datetime
from pathlib import Path

import requests

# Test configuration
HOST = "http://localhost:8000"
NUM_USERS = 10
TEST_DURATION_SECONDS = 60
QUERIES = [
    "What is machine learning?",
    "Explain retrieval-augmented generation",
    "What are vector databases?",
    "How does RAG work?",
    "What is semantic search?",
    "Describe embedding models",
    "What is hybrid search?",
    "Explain BM25 algorithm",
    "What is reranking?",
    "How to evaluate RAG systems?",
]


def make_request(query: str) -> dict:
    """Make a single request to the API."""
    start_time = time.time()
    try:
        response = requests.post(
            f"{HOST}/api/v1/query",
            json={
                "question": query,
                "k": 4,
                "top_k_bm25": 8,
                "top_k_vec": 8,
                "rrf_k": 60,
                "provider": "openai",
            },
            timeout=30,
        )
        latency = (time.time() - start_time) * 1000

        if response.status_code == 200:
            return {"success": True, "latency_ms": latency, "status_code": response.status_code}
        else:
            return {
                "success": False,
                "latency_ms": latency,
                "status_code": response.status_code,
                "error": response.text,
            }
    except Exception as e:
        return {"success": False, "latency_ms": (time.time() - start_time) * 1000, "error": str(e)}


def run_load_test():
    """Run the load test and collect metrics."""
    print(
        f"Starting load test with {NUM_USERS} concurrent users for {TEST_DURATION_SECONDS} seconds"
    )

    results = []
    start_time = time.time()
    end_time = start_time + TEST_DURATION_SECONDS

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        futures = []
        request_count = 0

        while time.time() < end_time:
            # Submit requests from each user
            for _ in range(NUM_USERS):
                query = random.choice(QUERIES)
                future = executor.submit(make_request, query)
                futures.append(future)
                request_count += 1

            # Small delay between batches
            time.sleep(0.5)

        # Collect results
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

    # Calculate statistics
    successful_requests = [r for r in results if r.get("success")]
    failed_requests = [r for r in results if not r.get("success")]
    latencies = [r["latency_ms"] for r in successful_requests]

    if latencies:
        latencies.sort()
        stats = {
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": len(successful_requests) / len(results) * 100,
            "avg_latency_ms": sum(latencies) / len(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "p50_latency_ms": latencies[int(len(latencies) * 0.5)],
            "p95_latency_ms": latencies[int(len(latencies) * 0.95)],
            "p99_latency_ms": latencies[int(len(latencies) * 0.99)],
            "requests_per_second": len(results) / TEST_DURATION_SECONDS,
        }
    else:
        stats = {
            "total_requests": len(results),
            "successful_requests": 0,
            "failed_requests": len(failed_requests),
            "success_rate": 0,
            "error": "No successful requests",
        }

    return stats, results


def generate_html_report(stats: dict, timestamp: str) -> str:
    """Generate an HTML report."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>RAG Pipeline Load Test Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .metrics {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .metric {{ margin: 10px 0; }}
        .metric-label {{ font-weight: bold; display: inline-block; width: 200px; }}
        .metric-value {{ color: #007acc; }}
        .success {{ color: green; }}
        .warning {{ color: orange; }}
        .error {{ color: red; }}
    </style>
</head>
<body>
    <h1>RAG Pipeline Load Test Report</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

    <div class="metrics">
        <h2>Test Configuration</h2>
        <div class="metric">
            <span class="metric-label">Concurrent Users:</span>
            <span class="metric-value">{NUM_USERS}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Test Duration:</span>
            <span class="metric-value">{TEST_DURATION_SECONDS} seconds</span>
        </div>
        <div class="metric">
            <span class="metric-label">Target Host:</span>
            <span class="metric-value">{HOST}</span>
        </div>
    </div>

    <div class="metrics">
        <h2>Performance Metrics</h2>
        <div class="metric">
            <span class="metric-label">Total Requests:</span>
            <span class="metric-value">{stats.get("total_requests", 0)}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Successful Requests:</span>
            <span class="metric-value success">{stats.get("successful_requests", 0)}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Failed Requests:</span>
            <span class="metric-value {"error" if stats.get("failed_requests", 0) > 0 else "success"}">
                {stats.get("failed_requests", 0)}
            </span>
        </div>
        <div class="metric">
            <span class="metric-label">Success Rate:</span>
            <span class="metric-value">{stats.get("success_rate", 0):.2f}%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Requests/Second:</span>
            <span class="metric-value">{stats.get("requests_per_second", 0):.2f}</span>
        </div>
    </div>

    <div class="metrics">
        <h2>Latency Statistics</h2>
        <div class="metric">
            <span class="metric-label">Average Latency:</span>
            <span class="metric-value">{stats.get("avg_latency_ms", 0):.2f} ms</span>
        </div>
        <div class="metric">
            <span class="metric-label">Min Latency:</span>
            <span class="metric-value">{stats.get("min_latency_ms", 0):.2f} ms</span>
        </div>
        <div class="metric">
            <span class="metric-label">Max Latency:</span>
            <span class="metric-value">{stats.get("max_latency_ms", 0):.2f} ms</span>
        </div>
        <div class="metric">
            <span class="metric-label">P50 Latency:</span>
            <span class="metric-value">{stats.get("p50_latency_ms", 0):.2f} ms</span>
        </div>
        <div class="metric">
            <span class="metric-label">P95 Latency:</span>
            <span class="metric-value">{stats.get("p95_latency_ms", 0):.2f} ms</span>
        </div>
        <div class="metric">
            <span class="metric-label">P99 Latency:</span>
            <span class="metric-value">{stats.get("p99_latency_ms", 0):.2f} ms</span>
        </div>
    </div>
</body>
</html>"""
    return html


def main():
    """Main function to run the load test."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"benchmarks/locust/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Running load test...")
    stats, _results = run_load_test()

    # Save JSON stats
    with open(output_dir / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    # Save HTML report
    html_report = generate_html_report(stats, timestamp)
    with open(output_dir / "report.html", "w") as f:
        f.write(html_report)

    # Save CSV stats
    with open(output_dir / "stats_history.csv", "w") as f:
        f.write(
            "timestamp,total_requests,successful,failed,success_rate,avg_latency_ms,p95_latency_ms,p99_latency_ms,rps\n"
        )
        f.write(
            f"{timestamp},{stats.get('total_requests', 0)},{stats.get('successful_requests', 0)},"
        )
        f.write(f"{stats.get('failed_requests', 0)},{stats.get('success_rate', 0):.2f},")
        f.write(f"{stats.get('avg_latency_ms', 0):.2f},{stats.get('p95_latency_ms', 0):.2f},")
        f.write(f"{stats.get('p99_latency_ms', 0):.2f},{stats.get('requests_per_second', 0):.2f}\n")

    # Print summary
    print("\nLoad Test Results:")
    print(f"  Total Requests: {stats.get('total_requests', 0)}")
    print(f"  Success Rate: {stats.get('success_rate', 0):.2f}%")
    print(f"  Avg Latency: {stats.get('avg_latency_ms', 0):.2f} ms")
    print(f"  P95 Latency: {stats.get('p95_latency_ms', 0):.2f} ms")
    print(f"  P99 Latency: {stats.get('p99_latency_ms', 0):.2f} ms")
    print(f"\nResults saved to: {output_dir}")


if __name__ == "__main__":
    main()
