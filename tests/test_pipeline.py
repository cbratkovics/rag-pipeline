"""Tests for the RAG pipeline."""

import os

# Set protobuf workaround FIRST
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from uuid import uuid4

import pytest

from src.core.models import (
    Document,
    DocumentSource,
    EvaluationMetrics,
    ExperimentVariant,
    Query,
    RetrievedDocument,
)
from src.experiments.ab_testing import ABTestManager
from src.retrieval.chunking import SemanticChunker
from src.retrieval.embeddings import EmbeddingManager


@pytest.mark.unit
class TestEmbeddingManager:
    """Test embedding manager functionality."""

    def test_embedding_generation(self):
        """Test that embeddings are generated correctly."""
        manager = EmbeddingManager()
        manager.initialize()

        text = "This is a test document."
        embedding = manager.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_batch_embedding(self):
        """Test batch embedding generation."""
        manager = EmbeddingManager()
        manager.initialize()

        texts = ["First document", "Second document", "Third document"]
        embeddings = manager.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(isinstance(e, list) for e in embeddings)

    def test_similarity_calculation(self):
        """Test cosine similarity calculation."""
        manager = EmbeddingManager()

        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [1.0, 0.0, 0.0]
        embedding3 = [0.0, 1.0, 0.0]

        similarity1 = manager.compute_similarity(embedding1, embedding2)
        similarity2 = manager.compute_similarity(embedding1, embedding3)

        assert similarity1 == pytest.approx(1.0, rel=1e-5)
        assert similarity2 == pytest.approx(0.0, rel=1e-5)


@pytest.mark.unit
class TestChunking:
    """Test document chunking strategies."""

    def test_semantic_chunking(self):
        """Test semantic chunking strategy."""
        chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)

        text = """
        This is the first paragraph of text. It contains some information.

        This is the second paragraph. It has different content than the first.

        And here is the third paragraph with even more information.
        """

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) <= 200 for chunk in chunks)  # Allow some flexibility

    def test_empty_text_chunking(self):
        """Test chunking with empty text."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_text("")
        assert chunks == []


@pytest.mark.unit
class TestABTesting:
    """Test A/B testing functionality."""

    def test_variant_assignment(self):
        """Test that variant assignment is deterministic."""
        manager = ABTestManager()

        # Same user should get same variant
        user_id = "test_user_123"
        variant1 = manager.assign_variant(user_id=user_id, experiment_id="test")
        variant2 = manager.assign_variant(user_id=user_id, experiment_id="test")

        assert variant1 == variant2
        assert isinstance(variant1, ExperimentVariant)

    def test_traffic_split(self):
        """Test that traffic split distributes users correctly."""
        manager = ABTestManager()

        # Assign many users and check distribution
        assignments = {}
        for i in range(1000):
            user_id = f"user_{i}"
            variant = manager.assign_variant(user_id=user_id, experiment_id="test")
            variant_name = variant.value
            assignments[variant_name] = assignments.get(variant_name, 0) + 1

        # Check that all variants got some traffic
        assert len(assignments) > 1
        # Check that no variant got more than 40% (for 4 variants with 25% each)
        for count in assignments.values():
            assert count < 400  # 40% of 1000


@pytest.mark.asyncio
class TestQueryProcessing:
    """Test query processing pipeline."""

    async def test_query_creation(self):
        """Test query model creation."""
        query = Query(
            text="What is machine learning?",
            user_id="test_user",
            max_results=5,
        )

        assert query.text == "What is machine learning?"
        assert query.user_id == "test_user"
        assert query.max_results == 5
        assert query.id is not None

    async def test_document_retrieval(self):
        """Test document retrieval structure."""
        doc = Document(
            content="Machine learning is a subset of AI.",
            source=DocumentSource.WIKIPEDIA,
            title="Machine Learning",
        )

        retrieved = RetrievedDocument(
            document=doc,
            score=0.95,
        )

        assert retrieved.score == 0.95
        assert retrieved.document.content == "Machine learning is a subset of AI."
        assert retrieved.document.source == DocumentSource.WIKIPEDIA


@pytest.mark.asyncio
class TestRAGASEvaluation:
    """Test RAGAS evaluation metrics."""

    async def test_evaluation_metrics_calculation(self):
        """Test that evaluation metrics are calculated correctly."""
        metrics = EvaluationMetrics(
            result_id=uuid4(),
            context_relevancy=0.85,
            answer_faithfulness=0.90,
            answer_relevancy=0.88,
            context_recall=0.75,
            overall_score=0.0,
            evaluation_time_ms=100.0,
        )

        overall = metrics.calculate_overall_score()

        # Check that overall score is weighted average
        expected = 0.85 * 0.25 + 0.90 * 0.30 + 0.88 * 0.30 + 0.75 * 0.15
        assert overall == pytest.approx(expected, rel=1e-3)

    async def test_threshold_checking(self):
        """Test threshold checking for metrics."""
        from src.core.models import EvaluationMetrics
        from src.evaluation.ragas_evaluator import RAGASEvaluator

        evaluator = RAGASEvaluator()

        metrics = EvaluationMetrics(
            result_id=uuid4(),
            context_relevancy=0.85,
            answer_faithfulness=0.85,
            answer_relevancy=0.85,
            context_recall=0.75,
            overall_score=0.83,
            evaluation_time_ms=100.0,
        )

        thresholds = evaluator.check_thresholds(metrics)

        assert thresholds["context_relevancy"]
        assert thresholds["answer_faithfulness"]
        assert thresholds["answer_relevancy"]
        assert thresholds["context_recall"]


@pytest.mark.unit
class TestCostCalculation:
    """Test cost calculation functionality."""

    def test_cost_calculation(self):
        """Test that costs are calculated correctly."""
        from src.retrieval.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline()

        cost = pipeline._calculate_cost(
            retrieval_count=10,
            token_count=500,
            variant=ExperimentVariant.HYBRID,
        )

        assert isinstance(cost, float)
        assert cost > 0
        # Check that cost includes all components
        assert cost >= pipeline.settings.cost_per_embedding_request
