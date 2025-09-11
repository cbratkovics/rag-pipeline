import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.rag.retriever import HybridRetriever


def test_rrf_combine():
    """Test Reciprocal Rank Fusion combination."""
    retriever = HybridRetriever()

    # Mock BM25 results: (id, text, score, metadata)
    bm25_results = [
        ("doc1", "Text 1", 10.0, {"source": "file1"}),
        ("doc2", "Text 2", 8.0, {"source": "file2"}),
        ("doc3", "Text 3", 6.0, {"source": "file3"}),
    ]

    # Mock vector results with some overlap
    vector_results = [
        ("doc2", "Text 2", 0.9, {"source": "file2"}),
        ("doc4", "Text 4", 0.85, {"source": "file4"}),
        ("doc1", "Text 1", 0.8, {"source": "file1"}),
    ]

    # Test RRF combination
    results = retriever.rrf_combine(bm25_results, vector_results, k=60)

    # Check results structure
    assert len(results) == 4  # Should have 4 unique documents
    assert all(len(r) == 4 for r in results)  # Each result should have 4 elements

    # Check first result structure
    doc_id, text, scores, metadata = results[0]
    assert isinstance(doc_id, str)
    assert isinstance(text, str)
    assert isinstance(scores, dict)
    assert "hybrid" in scores
    assert "bm25" in scores
    assert "vector" in scores
    assert isinstance(metadata, dict)

    # Check that doc2 should rank high (appears in both lists)
    doc_ids = [r[0] for r in results]
    assert "doc2" in doc_ids[:2]  # Should be in top 2


def test_weighted_combine():
    """Test weighted combination of results."""
    retriever = HybridRetriever()

    # Mock BM25 results
    bm25_results = [
        ("doc1", "Text 1", 10.0, {}),
        ("doc2", "Text 2", 5.0, {}),
    ]

    # Mock vector results
    vector_results = [
        ("doc3", "Text 3", 0.9, {}),
        ("doc1", "Text 1", 0.7, {}),
    ]

    # Test with equal weights
    results = retriever.weighted_combine(
        bm25_results, vector_results, bm25_weight=0.5, vector_weight=0.5
    )

    # Check results
    assert len(results) == 3  # Should have 3 unique documents

    # Check scores are normalized and weighted
    for _doc_id, _text, scores, _metadata in results:
        assert 0 <= scores["hybrid"] <= 1.0
        assert scores["bm25"] >= 0
        assert scores["vector"] >= 0

    # Test with different weights
    results_bm25_heavy = retriever.weighted_combine(
        bm25_results, vector_results, bm25_weight=0.8, vector_weight=0.2
    )

    # BM25-heavy weighting should favor doc1 and doc2
    doc_ids = [r[0] for r in results_bm25_heavy]
    assert doc_ids[0] in ["doc1", "doc2"]


def test_empty_results_handling():
    """Test handling of empty result sets."""
    retriever = HybridRetriever()

    # Test with empty BM25 results
    results = retriever.rrf_combine([], [("doc1", "Text", 0.9, {})], k=60)
    assert len(results) == 1
    assert results[0][0] == "doc1"

    # Test with empty vector results
    results = retriever.rrf_combine([("doc2", "Text", 5.0, {})], [], k=60)
    assert len(results) == 1
    assert results[0][0] == "doc2"

    # Test with both empty
    results = retriever.rrf_combine([], [], k=60)
    assert len(results) == 0


def test_rrf_k_parameter():
    """Test the effect of different k values in RRF."""
    retriever = HybridRetriever()

    bm25_results = [
        ("doc1", "Text 1", 10.0, {}),
        ("doc2", "Text 2", 8.0, {}),
    ]

    vector_results = [
        ("doc2", "Text 2", 0.9, {}),
        ("doc1", "Text 1", 0.8, {}),
    ]

    # Test with different k values
    results_k10 = retriever.rrf_combine(bm25_results, vector_results, k=10)
    results_k60 = retriever.rrf_combine(bm25_results, vector_results, k=60)
    results_k100 = retriever.rrf_combine(bm25_results, vector_results, k=100)

    # All should return same documents
    assert len(results_k10) == len(results_k60) == len(results_k100) == 2

    # But scores should differ
    scores_k10 = results_k10[0][2]["hybrid"]
    scores_k60 = results_k60[0][2]["hybrid"]
    scores_k100 = results_k100[0][2]["hybrid"]

    assert scores_k10 != scores_k60
    assert scores_k60 != scores_k100
