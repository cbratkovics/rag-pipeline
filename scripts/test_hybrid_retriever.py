#!/usr/bin/env python3
"""Test script to verify HybridRetriever functionality."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set protobuf environment before importing ChromaDB
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from src.rag.retriever import HybridRetriever


def test_hybrid_retriever():
    """Test that HybridRetriever can retrieve documents with non-zero scores."""
    print("=" * 80)
    print("Testing HybridRetriever Functionality")
    print("=" * 80)

    # Initialize retriever
    print("\n1. Initializing HybridRetriever...")
    retriever = HybridRetriever()

    # Check document count
    doc_count = retriever.collection.count()
    print("   ✓ HybridRetriever initialized")
    print(f"   ✓ Document count: {doc_count}")

    if doc_count == 0:
        print("\n   ❌ ERROR: Vector store is empty!")
        print("   Please run: POST /api/v1/admin/initialize")
        return False

    # Test queries
    test_queries = [
        "What is RAG?",
        "Explain transformer architecture",
        "How does retrieval work?",
    ]

    print("\n2. Testing retrieval with sample queries...")
    all_tests_passed = True

    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: '{query}'")

        # Perform retrieval
        result = retriever.retrieve(
            query=query,
            top_k_bm25=10,
            top_k_vec=10,
            final_k=4,
            fusion_method="rrf",
            rrf_k=60,
        )

        contexts = result["contexts"]
        scores = result["scores"]

        # Check results
        if not contexts:
            print("      ❌ No contexts retrieved")
            all_tests_passed = False
            continue

        print(f"      ✓ Retrieved {len(contexts)} contexts")

        # Check for non-zero scores
        hybrid_scores = scores.get("hybrid", [])
        bm25_scores = scores.get("bm25", [])
        vector_scores = scores.get("vector", [])

        if not hybrid_scores or all(s == 0 for s in hybrid_scores):
            print("      ❌ All hybrid scores are zero!")
            all_tests_passed = False
        else:
            avg_hybrid = sum(hybrid_scores) / len(hybrid_scores)
            max_hybrid = max(hybrid_scores)
            print(f"      ✓ Hybrid scores: avg={avg_hybrid:.4f}, max={max_hybrid:.4f}")

        if bm25_scores:
            avg_bm25 = sum(bm25_scores) / len(bm25_scores)
            print(f"      ✓ BM25 scores: avg={avg_bm25:.4f}")

        if vector_scores:
            avg_vector = sum(vector_scores) / len(vector_scores)
            print(f"      ✓ Vector scores: avg={avg_vector:.4f}")

        # Show first context snippet
        if contexts:
            print(f"      ✓ First context preview: {contexts[0][:100]}...")

    # Summary
    print("\n" + "=" * 80)
    if all_tests_passed and doc_count > 0:
        print("✅ SUCCESS: HybridRetriever is working correctly!")
        print(f"   - Document count: {doc_count}")
        print("   - All queries returned non-zero scores")
        print("   - Retrieval system is operational")
        return True
    else:
        print("❌ FAILURE: Some tests failed")
        return False


if __name__ == "__main__":
    success = test_hybrid_retriever()
    sys.exit(0 if success else 1)
