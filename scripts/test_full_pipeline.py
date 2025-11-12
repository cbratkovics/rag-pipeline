#!/usr/bin/env python3
"""Test the full RAG pipeline end-to-end.

This script tests the entire pipeline locally to ensure everything works correctly.
"""

import logging
import os
import sys
from pathlib import Path

# Set protobuf environment before importing ChromaDB
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.retriever import HybridRetriever

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_vector_store_health():
    """Test 1: Verify vector store has documents."""
    logger.info("=" * 80)
    logger.info("TEST 1: Vector Store Health Check")
    logger.info("=" * 80)

    try:
        retriever = HybridRetriever()

        # Get collection info
        count = retriever.collection.count()
        logger.info(f"✓ Vector store contains {count} documents")

        if count == 0:
            logger.error("✗ FAIL: Vector store is empty!")
            return False

        logger.info("✓ PASS: Vector store has documents")
        return True

    except Exception as e:
        logger.error(f"✗ FAIL: Vector store health check failed: {e}")
        return False


def test_bm25_search():
    """Test 2: Test BM25 search returns non-zero scores."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 2: BM25 Search")
    logger.info("=" * 80)

    try:
        retriever = HybridRetriever()
        query = "What is retrieval-augmented generation?"

        results = retriever.bm25_search(query, top_k=5)

        logger.info(f"✓ BM25 search returned {len(results)} results")

        if not results:
            logger.error("✗ FAIL: BM25 search returned no results")
            return False

        # Check scores
        non_zero_scores = [r for r in results if r[2] > 0]
        logger.info(f"✓ {len(non_zero_scores)}/{len(results)} results have non-zero scores")

        # Display sample results
        for i, (_, text, score, _) in enumerate(results[:3], 1):
            logger.info(f"  Result {i}:")
            logger.info(f"    Score: {score:.4f}")
            logger.info(f"    Text: {text[:100]}...")

        if len(non_zero_scores) > 0:
            logger.info("✓ PASS: BM25 search working")
            return True
        else:
            logger.error("✗ FAIL: All BM25 scores are zero")
            return False

    except Exception as e:
        logger.error(f"✗ FAIL: BM25 search failed: {e}")
        return False


def test_vector_search():
    """Test 3: Test vector search returns non-zero scores."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 3: Vector Search")
    logger.info("=" * 80)

    try:
        retriever = HybridRetriever()
        query = "What is retrieval-augmented generation?"

        results = retriever.vector_search(query, top_k=5)

        logger.info(f"✓ Vector search returned {len(results)} results")

        if not results:
            logger.error("✗ FAIL: Vector search returned no results")
            return False

        # Check scores
        non_zero_scores = [r for r in results if r[2] > 0]
        logger.info(f"✓ {len(non_zero_scores)}/{len(results)} results have non-zero scores")

        # Display sample results
        for i, (_, text, score, _) in enumerate(results[:3], 1):
            logger.info(f"  Result {i}:")
            logger.info(f"    Score: {score:.4f}")
            logger.info(f"    Text: {text[:100]}...")

        if len(non_zero_scores) > 0:
            logger.info("✓ PASS: Vector search working")
            return True
        else:
            logger.error("✗ FAIL: All vector scores are zero")
            return False

    except Exception as e:
        logger.error(f"✗ FAIL: Vector search failed: {e}")
        return False


def test_hybrid_retrieval_rrf():
    """Test 4: Test hybrid retrieval with RRF."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 4: Hybrid Retrieval (RRF)")
    logger.info("=" * 80)

    try:
        retriever = HybridRetriever()
        query = "What is retrieval-augmented generation?"

        result = retriever.retrieve(
            query=query,
            top_k_bm25=8,
            top_k_vec=8,
            final_k=4,
            fusion_method="rrf",
        )

        contexts = result["contexts"]
        scores = result["scores"]

        logger.info(f"✓ Hybrid retrieval returned {len(contexts)} contexts")

        # Check scores
        hybrid_scores = scores["hybrid"]
        bm25_scores = scores["bm25"]
        vector_scores = scores["vector"]

        logger.info(f"✓ Hybrid scores: {[f'{s:.4f}' for s in hybrid_scores]}")
        logger.info(f"✓ BM25 scores: {[f'{s:.4f}' for s in bm25_scores]}")
        logger.info(f"✓ Vector scores: {[f'{s:.4f}' for s in vector_scores]}")

        non_zero_hybrid = sum(1 for s in hybrid_scores if s > 0)
        logger.info(f"✓ {non_zero_hybrid}/{len(hybrid_scores)} hybrid scores are non-zero")

        # Display sample contexts
        for i, ctx in enumerate(contexts[:2], 1):
            logger.info(f"  Context {i}: {ctx[:100]}...")

        if non_zero_hybrid > 0:
            logger.info("✓ PASS: Hybrid retrieval (RRF) working")
            return True
        else:
            logger.error("✗ FAIL: All hybrid scores are zero")
            return False

    except Exception as e:
        logger.error(f"✗ FAIL: Hybrid retrieval (RRF) failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_hybrid_retrieval_weighted():
    """Test 5: Test hybrid retrieval with weighted fusion."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 5: Hybrid Retrieval (Weighted)")
    logger.info("=" * 80)

    try:
        retriever = HybridRetriever()
        query = "What is retrieval-augmented generation?"

        result = retriever.retrieve(
            query=query,
            top_k_bm25=8,
            top_k_vec=8,
            final_k=4,
            fusion_method="weighted",
            bm25_weight=0.5,
            vector_weight=0.5,
        )

        contexts = result["contexts"]
        scores = result["scores"]

        logger.info(f"✓ Hybrid retrieval returned {len(contexts)} contexts")

        # Check scores
        hybrid_scores = scores["hybrid"]
        non_zero_hybrid = sum(1 for s in hybrid_scores if s > 0)
        logger.info(f"✓ {non_zero_hybrid}/{len(hybrid_scores)} hybrid scores are non-zero")

        if non_zero_hybrid > 0:
            logger.info("✓ PASS: Hybrid retrieval (Weighted) working")
            return True
        else:
            logger.error("✗ FAIL: All hybrid scores are zero")
            return False

    except Exception as e:
        logger.error(f"✗ FAIL: Hybrid retrieval (Weighted) failed: {e}")
        return False


def test_multiple_queries():
    """Test 6: Test multiple different queries."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 6: Multiple Queries")
    logger.info("=" * 80)

    queries = [
        "What is RAG?",
        "How does vector search work?",
        "Explain hybrid search",
        "What are embeddings?",
    ]

    try:
        retriever = HybridRetriever()
        all_passed = True

        for i, query in enumerate(queries, 1):
            logger.info(f"\n  Query {i}: {query}")

            result = retriever.retrieve(
                query=query,
                top_k_bm25=5,
                top_k_vec=5,
                final_k=3,
            )

            contexts = result["contexts"]
            scores = result["scores"]
            hybrid_scores = scores["hybrid"]

            non_zero = sum(1 for s in hybrid_scores if s > 0)
            logger.info(f"    ✓ {len(contexts)} contexts, {non_zero} non-zero scores")

            if non_zero == 0:
                logger.error(f"    ✗ Query {i} returned all zero scores")
                all_passed = False

        if all_passed:
            logger.info("\n✓ PASS: All queries returned non-zero scores")
            return True
        else:
            logger.error("\n✗ FAIL: Some queries returned zero scores")
            return False

    except Exception as e:
        logger.error(f"✗ FAIL: Multiple queries test failed: {e}")
        return False


def main():
    """Run all tests and report results."""
    logger.info("")
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + " " * 20 + "FULL PIPELINE TEST SUITE" + " " * 34 + "║")
    logger.info("╚" + "═" * 78 + "╝")
    logger.info("")

    tests = [
        test_vector_store_health,
        test_bm25_search,
        test_vector_search,
        test_hybrid_retrieval_rrf,
        test_hybrid_retrieval_weighted,
        test_multiple_queries,
    ]

    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append((test_func.__name__, passed))
        except Exception as e:
            logger.error(f"Test {test_func.__name__} crashed: {e}")
            results.append((test_func.__name__, False))

    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info("")
    logger.info(f"Total: {passed_count}/{total_count} tests passed")
    logger.info("=" * 80)

    if passed_count == total_count:
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"❌ {total_count - passed_count} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
