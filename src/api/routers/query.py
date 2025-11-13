"""Query API endpoints."""

import os
import time
import uuid
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import AliasChoices, BaseModel, Field

# Set protobuf environment before importing ChromaDB
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from src.core.config import get_settings
from src.core.models import (
    Document,
    DocumentSource,
    ExperimentVariant,
    Query,
    QueryResult,
    QueryStatus,
    RetrievedDocument,
)
from src.evaluation.ragas_evaluator import ragas_evaluator
from src.experiments.ab_testing import ab_test_manager
from src.infrastructure.logging import get_logger
from src.rag.generator import get_llm
from src.rag.retriever import HybridRetriever
from src.retrieval.rag_pipeline import rag_pipeline

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()

# Initialize retriever and LLM
_hybrid_retriever = None
_llm = None


def get_hybrid_retriever() -> HybridRetriever:
    """Get or create hybrid retriever instance."""
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()
    return _hybrid_retriever


def get_llm_instance():
    """Get or create LLM instance."""
    global _llm
    if _llm is None:
        try:
            _llm = get_llm()
        except ValueError:
            logger.warning("OpenAI API key not available, will fall back to rag_pipeline")
            _llm = None
    return _llm


async def process_query_with_hybrid_retriever(
    query: Query, variant: ExperimentVariant
) -> QueryResult:
    """Process query using HybridRetriever and OpenAI LLM.

    This is the preferred method as it uses the populated ChromaDB collection.
    """
    start_time = time.time()

    try:
        # Get retriever and LLM
        retriever = get_hybrid_retriever()
        llm = get_llm_instance()

        # Check if retriever has documents
        doc_count = retriever.collection.count()
        logger.info(f"HybridRetriever has {doc_count} documents")

        if doc_count == 0:
            logger.warning("HybridRetriever is empty, cannot process query")
            raise ValueError("Vector store is empty")

        # Perform retrieval
        retrieval_result = retriever.retrieve(
            query=query.text,
            top_k_bm25=10,
            top_k_vec=10,
            final_k=query.max_results,
            fusion_method="rrf",
            rrf_k=60,
        )

        contexts = retrieval_result["contexts"]
        scores = retrieval_result["scores"]
        metadata_list = retrieval_result["metadata"]

        logger.info(
            f"Retrieved {len(contexts)} contexts",
            hybrid_scores=scores["hybrid"][:3] if scores["hybrid"] else [],
        )

        # Generate answer using LLM
        if llm and contexts:
            answer = llm.generate(query.text, contexts)
            # Estimate token count
            token_count = (
                len(query.text.split())
                + sum(len(c.split()) for c in contexts)
                + len(answer.split())
            )
        else:
            if not contexts:
                answer = "I couldn't find relevant information to answer your question."
            else:
                answer = "LLM not available. Retrieved contexts but cannot generate answer."
            token_count = 0

        # Convert to RetrievedDocument objects
        retrieved_docs = []
        for i, (context, metadata_dict) in enumerate(zip(contexts, metadata_list, strict=False)):
            # Extract scores for this document
            hybrid_score = scores["hybrid"][i] if i < len(scores["hybrid"]) else 0.0
            bm25_score = scores["bm25"][i] if i < len(scores["bm25"]) else 0.0
            vector_score = scores["vector"][i] if i < len(scores["vector"]) else 0.0

            # Create Document object
            doc = Document(
                id=uuid4(),
                content=context,
                metadata=metadata_dict or {},
                source=DocumentSource.CUSTOM,
                title=metadata_dict.get("title") if metadata_dict else None,
                url=metadata_dict.get("url") if metadata_dict else None,
            )

            # Create RetrievedDocument
            retrieved_doc = RetrievedDocument(
                document=doc,
                score=float(hybrid_score),
                bm25_score=float(bm25_score),
                semantic_score=float(vector_score),
            )
            retrieved_docs.append(retrieved_doc)

        # Calculate metrics
        processing_time = (time.time() - start_time) * 1000
        confidence_score = float(scores["hybrid"][0]) if scores["hybrid"] else 0.0

        # Estimate cost (simplified)
        cost_usd = token_count * 0.000002 if token_count > 0 else 0.0

        # Create QueryResult
        result = QueryResult(
            query_id=query.id,
            query_text=query.text,
            answer=answer,
            sources=retrieved_docs if query.include_sources else [],
            experiment_variant=variant,
            confidence_score=min(confidence_score, 1.0),
            processing_time_ms=processing_time,
            token_count=token_count,
            cost_usd=cost_usd,
            status=QueryStatus.COMPLETED,
        )

        logger.info(
            "Query processed with HybridRetriever",
            query_id=str(query.id),
            contexts_count=len(contexts),
            processing_time_ms=processing_time,
        )

        return result

    except Exception as e:
        logger.error(f"HybridRetriever processing failed: {e}", exc_info=True)
        raise


class QueryRequest(BaseModel):
    """Query request model (accepts 'query' or legacy 'question')."""

    query: str = Field(
        ...,
        description="The query text",
        validation_alias=AliasChoices("query", "question"),
    )
    metadata_filters: dict[str, Any] | None = Field(
        default=None, description="Metadata filters for document retrieval"
    )
    experiment_variant: str | None = Field(
        default=None, description="Specific experiment variant to use"
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results",
        validation_alias=AliasChoices("max_results", "k"),
    )
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

        # Process query - try HybridRetriever first, fallback to rag_pipeline
        result = None
        try:
            logger.info("Attempting to process query with HybridRetriever")
            result = await process_query_with_hybrid_retriever(query, variant)
            logger.info("Successfully processed query with HybridRetriever")
        except Exception as e:
            logger.warning(
                f"HybridRetriever failed, falling back to rag_pipeline: {e}", exc_info=True
            )
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
