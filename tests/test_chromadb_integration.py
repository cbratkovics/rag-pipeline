"""Integration tests for ChromaDB-based RAG pipeline."""

import os

import pytest

# Set protobuf environment before importing ChromaDB
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from src.rag.retriever import HybridRetriever


@pytest.mark.integration
class TestChromaDBIntegration:
    """Test ChromaDB-based retrieval system."""

    @pytest.fixture
    def retriever(self):
        """Create a retriever instance."""
        return HybridRetriever()

    def test_vector_store_has_documents(self, retriever):
        """Test that vector store contains documents."""
        count = retriever.collection.count()
        assert count > 0, "Vector store should contain documents"

    def test_bm25_search_returns_results(self, retriever):
        """Test BM25 search returns results with non-zero scores."""
        query = "What is RAG?"
        results = retriever.bm25_search(query, top_k=5)

        assert len(results) > 0, "BM25 search should return results"
        assert all(score > 0 for _, _, score, _ in results), "All BM25 scores should be non-zero"

    def test_vector_search_returns_results(self, retriever):
        """Test vector search returns results with non-zero scores."""
        query = "What is RAG?"
        results = retriever.vector_search(query, top_k=5)

        assert len(results) > 0, "Vector search should return results"
        assert all(score > 0 for _, _, score, _ in results), "All vector scores should be non-zero"

    def test_hybrid_retrieval_rrf(self, retriever):
        """Test hybrid retrieval with RRF fusion."""
        query = "What is RAG?"
        result = retriever.retrieve(
            query=query,
            top_k_bm25=8,
            top_k_vec=8,
            final_k=4,
            fusion_method="rrf",
        )

        assert len(result["contexts"]) == 4, "Should return 4 contexts"
        assert all(s > 0 for s in result["scores"]["hybrid"]), (
            "All hybrid scores should be non-zero"
        )

    def test_hybrid_retrieval_weighted(self, retriever):
        """Test hybrid retrieval with weighted fusion."""
        query = "What is RAG?"
        result = retriever.retrieve(
            query=query,
            top_k_bm25=8,
            top_k_vec=8,
            final_k=4,
            fusion_method="weighted",
            bm25_weight=0.5,
            vector_weight=0.5,
        )

        assert len(result["contexts"]) == 4, "Should return 4 contexts"
        assert all(s > 0 for s in result["scores"]["hybrid"]), (
            "All hybrid scores should be non-zero"
        )

    def test_multiple_queries(self, retriever):
        """Test multiple different queries all return non-zero scores."""
        queries = [
            "What is RAG?",
            "How does vector search work?",
            "Explain hybrid search",
            "What are embeddings?",
        ]

        for query in queries:
            result = retriever.retrieve(
                query=query,
                top_k_bm25=5,
                top_k_vec=5,
                final_k=3,
            )

            assert len(result["contexts"]) > 0, f"Query '{query}' should return contexts"
            assert any(s > 0 for s in result["scores"]["hybrid"]), (
                f"Query '{query}' should have non-zero scores"
            )

    def test_retrieval_with_different_k_values(self, retriever):
        """Test retrieval with different k values."""
        query = "What is RAG?"

        for final_k in [1, 3, 5, 10]:
            result = retriever.retrieve(
                query=query,
                top_k_bm25=10,
                top_k_vec=10,
                final_k=final_k,
            )

            assert len(result["contexts"]) <= final_k, f"Should return at most {final_k} contexts"
            assert len(result["scores"]["hybrid"]) == len(result["contexts"]), (
                "Should have matching number of scores and contexts"
            )


@pytest.mark.integration
class TestVectorStoreInitialization:
    """Test vector store initialization functionality."""

    def test_initialization_script_exists(self):
        """Test that initialization script exists and is importable."""
        from scripts.initialize_vector_store import initialize_vector_store

        assert callable(initialize_vector_store), "Initialization function should be callable"

    def test_verification_script_exists(self):
        """Test that verification script exists and is importable."""
        from scripts.initialize_vector_store import verify_vector_store

        assert callable(verify_vector_store), "Verification function should be callable"

    def test_full_pipeline_test_script_exists(self):
        """Test that full pipeline test script exists."""
        import scripts.test_full_pipeline

        assert hasattr(scripts.test_full_pipeline, "main"), "Test script should have main function"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
