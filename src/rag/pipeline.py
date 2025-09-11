import logging
import os
import time
from typing import Any

from dotenv import load_dotenv

from .generator import get_llm
from .retriever import HybridRetriever

load_dotenv()

logger = logging.getLogger(__name__)


async def answer_query(
    question: str,
    top_k_vec: int = 8,
    top_k_bm25: int = 8,
    rrf_k: int = 60,
    final_k: int = 4,
    provider: str = "stub",
    fusion_method: str = "rrf",
    bm25_weight: float | None = None,
    vector_weight: float | None = None,
) -> dict[str, Any]:
    """
    Execute the RAG pipeline to answer a question.

    Args:
        question: The question to answer
        top_k_vec: Number of vector search results
        top_k_bm25: Number of BM25 results
        rrf_k: K parameter for RRF fusion
        final_k: Final number of contexts to use
        provider: LLM provider ("stub" or "openai")
        fusion_method: "rrf" or "weighted"
        bm25_weight: Weight for BM25 (for weighted fusion)
        vector_weight: Weight for vector search (for weighted fusion)

    Returns:
        Dictionary containing answer, contexts, scores, and metadata
    """
    start_time = time.time()

    # Get weights from environment if not provided
    if bm25_weight is None:
        bm25_weight = float(os.getenv("HYBRID_WEIGHT_BM25", "0.5"))
    if vector_weight is None:
        vector_weight = float(os.getenv("HYBRID_WEIGHT_VECTOR", "0.5"))

    # Initialize retriever
    logger.info(f"Retrieving documents for: {question}")
    retriever = HybridRetriever()

    # Retrieve documents
    retrieval_start = time.time()
    retrieval_results = retriever.retrieve(
        query=question,
        top_k_bm25=top_k_bm25,
        top_k_vec=top_k_vec,
        final_k=final_k,
        fusion_method=fusion_method,
        rrf_k=rrf_k,
        bm25_weight=bm25_weight,
        vector_weight=vector_weight,
    )
    retrieval_time = time.time() - retrieval_start
    logger.info(f"Retrieved {len(retrieval_results['contexts'])} contexts in {retrieval_time:.2f}s")

    # Generate answer
    logger.info(f"Generating answer using {provider} provider")
    generation_start = time.time()
    llm = get_llm(provider)
    answer = llm.generate(question, retrieval_results["contexts"])
    generation_time = time.time() - generation_start
    logger.info(f"Generated answer in {generation_time:.2f}s")

    # Calculate aggregate scores
    aggregate_scores = {}
    for score_type in ["hybrid", "bm25", "vector"]:
        scores = retrieval_results["scores"].get(score_type, [])
        if scores:
            aggregate_scores[score_type] = sum(scores) / len(scores)
        else:
            aggregate_scores[score_type] = 0.0

    total_time = time.time() - start_time
    logger.info(f"Pipeline completed in {total_time:.2f}s")

    return {
        "answer": answer,
        "contexts": retrieval_results["contexts"],
        "scores": aggregate_scores,
        "metadata": retrieval_results.get("metadata", []),
        "timing": {
            "retrieval_ms": retrieval_time * 1000,
            "generation_ms": generation_time * 1000,
            "total_ms": total_time * 1000,
        },
    }
