"""Hybrid query endpoint using HybridRetriever directly."""

import os
import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Set protobuf environment before importing ChromaDB
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from src.infrastructure.logging import get_logger
from src.rag.generator import get_llm
from src.rag.retriever import HybridRetriever

logger = get_logger(__name__)
router = APIRouter()

# Global retriever and LLM instances
_retriever = None
_llm = None


def get_retriever() -> HybridRetriever:
    """Get or create retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


def get_llm_instance():
    """Get or create LLM instance."""
    global _llm
    if _llm is None:
        try:
            _llm = get_llm()
        except ValueError:
            logger.warning("OpenAI API key not available")
            _llm = None
    return _llm


class HybridQueryRequest(BaseModel):
    """Hybrid query request model."""

    question: str = Field(..., description="The question to answer")
    k: int = Field(default=4, ge=1, le=20, description="Number of results to return")
    top_k_bm25: int = Field(default=10, ge=1, le=50, description="Number of BM25 results")
    top_k_vec: int = Field(default=10, ge=1, le=50, description="Number of vector results")
    rrf_k: int = Field(default=60, ge=1, le=100, description="RRF k parameter")
    fusion_method: str = Field(default="rrf", description="Fusion method: rrf or weighted")


class HybridQueryResponse(BaseModel):
    """Hybrid query response model."""

    query_id: str
    answer: str
    contexts: list[str]
    scores: dict[str, list[float]]
    metadata: list[dict[str, Any]]
    latency_ms: float
    document_count: int


@router.post("/query-hybrid", response_model=HybridQueryResponse)
async def query_hybrid(request: HybridQueryRequest) -> HybridQueryResponse:
    """Process query using HybridRetriever.

    This endpoint directly uses the HybridRetriever that contains the documents
    populated by the admin initialization endpoint.

    Args:
        request: Query request with question and retrieval parameters

    Returns:
        Query response with answer, contexts, and scores
    """
    start_time = time.time()
    query_id = str(uuid4())

    try:
        # Get retriever
        retriever = get_retriever()

        # Check document count
        doc_count = retriever.collection.count()
        logger.info(
            "Processing hybrid query",
            query_id=query_id,
            document_count=doc_count,
            question=request.question[:100],
        )

        if doc_count == 0:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vector store is empty. Please initialize it first via /admin/initialize",
            )

        # Perform retrieval
        retrieval_result = retriever.retrieve(
            query=request.question,
            top_k_bm25=request.top_k_bm25,
            top_k_vec=request.top_k_vec,
            final_k=request.k,
            fusion_method=request.fusion_method,
            rrf_k=request.rrf_k,
        )

        contexts = retrieval_result["contexts"]
        scores = retrieval_result["scores"]
        metadata_list = retrieval_result["metadata"]

        logger.info(
            "Retrieval complete",
            query_id=query_id,
            contexts_count=len(contexts),
            avg_hybrid_score=sum(scores["hybrid"]) / len(scores["hybrid"])
            if scores["hybrid"]
            else 0,
        )

        # Generate answer
        llm = get_llm_instance()
        if llm and contexts:
            try:
                answer = llm.generate(request.question, contexts)
                logger.info("Answer generated successfully", query_id=query_id)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}", query_id=query_id)
                answer = f"Retrieved {len(contexts)} contexts but answer generation failed: {e!s}"
        elif not contexts:
            answer = "I couldn't find relevant information to answer your question."
        else:
            answer = "LLM not available. Please set OPENAI_API_KEY environment variable."

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        response = HybridQueryResponse(
            query_id=query_id,
            answer=answer,
            contexts=contexts,
            scores=scores,
            metadata=metadata_list,
            latency_ms=latency_ms,
            document_count=doc_count,
        )

        logger.info(
            "Query processed successfully",
            query_id=query_id,
            latency_ms=latency_ms,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Query processing failed",
            query_id=query_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {e!s}",
        ) from e


@router.get("/query-hybrid/status", status_code=status.HTTP_200_OK)
async def hybrid_query_status() -> dict[str, Any]:
    """Get hybrid query system status.

    Returns:
        Status information including document count and health
    """
    try:
        retriever = get_retriever()
        doc_count = retriever.collection.count()
        llm = get_llm_instance()

        return {
            "status": "healthy" if doc_count > 0 else "empty",
            "document_count": doc_count,
            "llm_available": llm is not None,
            "collection_name": retriever.collection.name,
            "persist_dir": retriever.persist_dir,
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "status": "error",
            "document_count": 0,
            "llm_available": False,
            "error": str(e),
        }
