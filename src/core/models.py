"""Core domain models for the RAG pipeline."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class DocumentSource(str, Enum):
    """Supported document sources."""

    ARXIV = "arxiv"
    WIKIPEDIA = "wikipedia"
    COMMON_CRAWL = "common_crawl"
    SEC_EDGAR = "sec_edgar"
    PUBMED = "pubmed"
    CUSTOM = "custom"


class ExperimentVariant(str, Enum):
    """A/B test experiment variants."""

    BASELINE = "baseline"
    RERANKED = "reranked"
    HYBRID = "hybrid"
    FINETUNED = "finetuned"


class FeedbackType(str, Enum):
    """Types of user feedback."""

    THUMBS = "thumbs"
    RATING = "rating"
    CORRECTION = "correction"
    IMPLICIT = "implicit"


class QueryStatus(str, Enum):
    """Query processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    """Document model for storage and retrieval."""

    id: UUID = Field(default_factory=uuid4)
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: DocumentSource
    source_id: str | None = None
    title: str | None = None
    author: str | None = None
    published_date: datetime | None = None
    url: str | None = None
    license: str | None = None
    embedding: list[float] | None = None
    chunk_id: int | None = None
    parent_id: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure metadata is JSON-serializable."""
        import json

        try:
            json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Metadata must be JSON-serializable: {e}") from e
        return v


class Query(BaseModel):
    """Query model for RAG requests."""

    id: UUID = Field(default_factory=uuid4)
    text: str
    user_id: str | None = None
    session_id: str | None = None
    metadata_filters: dict[str, Any] = Field(default_factory=dict)
    experiment_variant: ExperimentVariant | None = None
    max_results: int = Field(default=5, ge=1, le=20)
    include_sources: bool = Field(default=True)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=4000)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RetrievedDocument(BaseModel):
    """Retrieved document with relevance score."""

    document: Document
    score: float = Field(ge=0.0, le=1.0)
    rerank_score: float | None = Field(default=None, ge=0.0, le=1.0)
    bm25_score: float | None = Field(default=None, ge=0.0)
    semantic_score: float | None = Field(default=None, ge=0.0, le=1.0)


class QueryResult(BaseModel):
    """Result of a RAG query."""

    id: UUID = Field(default_factory=uuid4)
    query_id: UUID
    query_text: str
    answer: str
    sources: list[RetrievedDocument] = Field(default_factory=list)
    experiment_variant: ExperimentVariant
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float
    token_count: int
    cost_usd: float
    status: QueryStatus = QueryStatus.COMPLETED
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluationMetrics(BaseModel):
    """RAGAS evaluation metrics for a query result."""

    result_id: UUID
    context_relevancy: float = Field(ge=0.0, le=1.0)
    answer_faithfulness: float = Field(ge=0.0, le=1.0)
    answer_relevancy: float = Field(ge=0.0, le=1.0)
    context_recall: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)
    evaluation_time_ms: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def calculate_overall_score(self) -> float:
        """Calculate weighted overall score."""
        weights = {
            "context_relevancy": 0.25,
            "answer_faithfulness": 0.30,
            "answer_relevancy": 0.30,
            "context_recall": 0.15,
        }
        score = (
            self.context_relevancy * weights["context_relevancy"]
            + self.answer_faithfulness * weights["answer_faithfulness"]
            + self.answer_relevancy * weights["answer_relevancy"]
            + self.context_recall * weights["context_recall"]
        )
        return round(score, 3)


class UserFeedback(BaseModel):
    """User feedback for query results."""

    id: UUID = Field(default_factory=uuid4)
    result_id: UUID
    user_id: str | None = None
    feedback_type: FeedbackType
    value: Any  # Can be bool (thumbs), int (rating), str (correction)
    comment: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any, info: Any) -> Any:
        """Validate feedback value based on type."""
        feedback_type = info.data.get("feedback_type")
        if feedback_type == FeedbackType.THUMBS:
            if not isinstance(v, bool):
                raise ValueError("Thumbs feedback must be boolean")
        elif feedback_type == FeedbackType.RATING:
            if not isinstance(v, int | float) or v < 1 or v > 5:
                raise ValueError("Rating must be between 1 and 5")
        elif feedback_type == FeedbackType.CORRECTION and not isinstance(v, str):
            raise ValueError("Correction must be a string")
        return v


class ExperimentResult(BaseModel):
    """A/B test experiment results."""

    experiment_id: str
    variant: ExperimentVariant
    sample_size: int
    success_count: int
    success_rate: float = Field(ge=0.0, le=1.0)
    avg_latency_ms: float
    avg_cost_usd: float
    avg_ragas_score: float = Field(ge=0.0, le=1.0)
    confidence_interval_lower: float = Field(ge=0.0, le=1.0)
    confidence_interval_upper: float = Field(ge=0.0, le=1.0)
    is_significant: bool
    p_value: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemMetrics(BaseModel):
    """System performance metrics."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    queries_per_second: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float = Field(ge=0.0, le=1.0)
    cache_hit_rate: float = Field(ge=0.0, le=1.0)
    vector_store_size: int
    memory_usage_mb: float
    cpu_usage_percent: float = Field(ge=0.0, le=100.0)
    active_experiments: int
    total_queries_24h: int
    total_cost_24h_usd: float
