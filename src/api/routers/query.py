"""Query API endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.core.models import ExperimentVariant, Query
from src.evaluation.ragas_evaluator import ragas_evaluator
from src.experiments.ab_testing import ab_test_manager
from src.infrastructure.logging import get_logger
from src.retrieval.rag_pipeline import rag_pipeline

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    """Query request model."""

    query: str = Field(..., description="The query text")
    metadata_filters: dict[str, Any] | None = Field(
        default=None, description="Metadata filters for document retrieval"
    )
    experiment_variant: str | None = Field(
        default=None, description="Specific experiment variant to use"
    )
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of results")
    include_sources: bool = Field(default=True, description="Include source documents")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int | None = Field(
        default=None, ge=1, le=4000, description="Maximum tokens for response"
    )


class QueryResponse(BaseModel):
    """Query response model."""

    query_id: str
    answer: str
    sources: list | None = None
    experiment_variant: str
    confidence_score: float
    processing_time_ms: float
    token_count: int
    cost_usd: float
    evaluation_metrics: dict[str, float] | None = None


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, req: Request) -> QueryResponse:
    """Process a RAG query."""
    try:
        # Get user/session ID from headers or create one
        user_id = req.headers.get("X-User-ID")
        session_id = req.headers.get("X-Session-ID") or str(uuid.uuid4())

        # Create query model
        query = Query(
            text=request.query,
            user_id=user_id,
            session_id=session_id,
            metadata_filters=request.metadata_filters or {},
            max_results=request.max_results,
            include_sources=request.include_sources,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Assign experiment variant
        if request.experiment_variant:
            variant = ExperimentVariant(request.experiment_variant)
        else:
            variant = ab_test_manager.assign_variant(
                user_id=user_id,
                session_id=session_id,
                experiment_id="default",
            )
            query.experiment_variant = variant

        # Process query
        result = await rag_pipeline.process_query(query, variant)

        # Evaluate if enabled
        evaluation_metrics = None
        if settings.ragas_enabled:
            try:
                evaluation = await ragas_evaluator.evaluate(result)
                evaluation_metrics = {
                    "context_relevancy": evaluation.context_relevancy,
                    "answer_faithfulness": evaluation.answer_faithfulness,
                    "answer_relevancy": evaluation.answer_relevancy,
                    "context_recall": evaluation.context_recall,
                    "overall_score": evaluation.overall_score,
                }

                # Record experiment result with metrics
                await ab_test_manager.record_result(
                    experiment_id="default",
                    variant=variant,
                    result=result,
                    metrics=evaluation_metrics,
                )
            except Exception as e:
                logger.warning("RAGAS evaluation failed", error=str(e))
                # Record experiment result without metrics
                await ab_test_manager.record_result(
                    experiment_id="default",
                    variant=variant,
                    result=result,
                )
        else:
            # Record experiment result without evaluation
            await ab_test_manager.record_result(
                experiment_id="default",
                variant=variant,
                result=result,
            )

        # Prepare response
        response = QueryResponse(
            query_id=str(result.query_id),
            answer=result.answer,
            sources=[
                {
                    "document": {
                        "id": str(doc.document.id),
                        "content": doc.document.content[:500],  # Truncate for response
                        "title": doc.document.title,
                        "source": doc.document.source.value,
                        "url": doc.document.url,
                    },
                    "score": doc.score,
                    "rerank_score": doc.rerank_score,
                }
                for doc in result.sources
            ]
            if request.include_sources
            else None,
            experiment_variant=result.experiment_variant.value,
            confidence_score=result.confidence_score,
            processing_time_ms=result.processing_time_ms,
            token_count=result.token_count,
            cost_usd=result.cost_usd,
            evaluation_metrics=evaluation_metrics,
        )

        logger.info(
            "Query processed successfully",
            query_id=str(result.query_id),
            variant=variant.value,
        )

        return response

    except Exception as e:
        logger.error("Query processing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {e!s}",
        ) from e
