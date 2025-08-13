"""Hybrid search combining semantic and keyword-based retrieval."""

import math
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from rank_bm25 import BM25Okapi

from src.core.config import get_settings
from src.core.models import Document, RetrievedDocument
from src.infrastructure.logging import LoggerMixin
from src.retrieval.embeddings import embedding_manager
from src.retrieval.vector_store import vector_store


class BM25Searcher(LoggerMixin):
    """BM25 keyword search implementation."""

    def __init__(self, k1: Optional[float] = None, b: Optional[float] = None):
        """Initialize BM25 searcher."""
        self.settings = get_settings()
        self.k1 = k1 or self.settings.bm25_k1
        self.b = b or self.settings.bm25_b
        self.documents: List[Document] = []
        self.tokenized_docs: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25."""
        # Simple tokenization - can be improved with NLTK or spaCy
        tokens = text.lower().split()
        # Remove punctuation
        tokens = [token.strip(".,!?;:\"'") for token in tokens]
        # Filter empty tokens
        tokens = [token for token in tokens if token]
        return tokens

    def index_documents(self, documents: List[Document]) -> None:
        """Index documents for BM25 search."""
        self.documents = documents
        self.tokenized_docs = [self.tokenize(doc.content) for doc in documents]
        self.bm25 = BM25Okapi(
            self.tokenized_docs,
            k1=self.k1,
            b=self.b,
        )
        self.logger.info("Indexed documents for BM25", count=len(documents))

    def search(
        self,
        query: str,
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Document, float]]:
        """Search documents using BM25."""
        if not self.bm25:
            self.logger.warning("BM25 index not initialized")
            return []

        tokenized_query = self.tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        # Apply metadata filter if provided
        filtered_indices = []
        for i, doc in enumerate(self.documents):
            if metadata_filter:
                match = True
                for key, value in metadata_filter.items():
                    doc_value = doc.metadata.get(key)
                    if isinstance(value, list):
                        if doc_value not in value:
                            match = False
                            break
                    elif doc_value != value:
                        match = False
                        break
                if not match:
                    continue
            filtered_indices.append(i)

        # Get top-k documents
        if filtered_indices:
            filtered_scores = [(i, scores[i]) for i in filtered_indices]
        else:
            filtered_scores = list(enumerate(scores))

        filtered_scores.sort(key=lambda x: x[1], reverse=True)
        top_results = filtered_scores[:top_k]

        results = []
        for idx, score in top_results:
            if score > 0:  # Only include documents with positive scores
                results.append((self.documents[idx], float(score)))

        return results


class HybridSearcher(LoggerMixin):
    """Hybrid search combining semantic and BM25 retrieval."""

    def __init__(self):
        """Initialize hybrid searcher."""
        self.settings = get_settings()
        self.bm25_searcher = BM25Searcher()
        self.alpha = self.settings.hybrid_search_alpha

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        alpha: Optional[float] = None,
    ) -> List[RetrievedDocument]:
        """Perform hybrid search combining semantic and keyword search."""
        top_k = top_k or self.settings.search_top_k
        alpha = alpha if alpha is not None else self.alpha

        # Generate query embedding
        query_embedding = embedding_manager.embed_text(query)

        # Perform semantic search
        semantic_results = await vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more results for merging
            metadata_filter=metadata_filter,
        )

        # Perform BM25 search if documents are indexed
        bm25_results = []
        if self.bm25_searcher.bm25:
            bm25_raw = self.bm25_searcher.search(
                query=query,
                top_k=top_k * 2,
                metadata_filter=metadata_filter,
            )
            bm25_results = [
                RetrievedDocument(
                    document=doc,
                    score=0.0,  # Will be computed later
                    bm25_score=score,
                )
                for doc, score in bm25_raw
            ]

        # Merge results using reciprocal rank fusion
        merged_results = self._reciprocal_rank_fusion(
            semantic_results=semantic_results,
            bm25_results=bm25_results,
            alpha=alpha,
        )

        # Return top-k results
        return merged_results[:top_k]

    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[RetrievedDocument],
        bm25_results: List[RetrievedDocument],
        alpha: float,
    ) -> List[RetrievedDocument]:
        """Merge results using reciprocal rank fusion."""
        # Create score dictionaries
        semantic_scores = {}
        bm25_scores = {}

        # Process semantic results
        for i, result in enumerate(semantic_results):
            doc_id = str(result.document.id)
            # Reciprocal rank: 1 / (rank + k), where k=60 is a constant
            semantic_scores[doc_id] = 1.0 / (i + 60)

        # Process BM25 results
        for i, result in enumerate(bm25_results):
            doc_id = str(result.document.id)
            bm25_scores[doc_id] = 1.0 / (i + 60)

        # Combine scores
        all_doc_ids = set(semantic_scores.keys()) | set(bm25_scores.keys())
        combined_scores = {}

        for doc_id in all_doc_ids:
            semantic_score = semantic_scores.get(doc_id, 0.0)
            bm25_score = bm25_scores.get(doc_id, 0.0)
            # Weighted combination
            combined_scores[doc_id] = alpha * semantic_score + (1 - alpha) * bm25_score

        # Create result documents
        doc_map = {}
        for result in semantic_results:
            doc_id = str(result.document.id)
            doc_map[doc_id] = result

        for result in bm25_results:
            doc_id = str(result.document.id)
            if doc_id not in doc_map:
                doc_map[doc_id] = result

        # Sort by combined score
        sorted_ids = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)

        # Create final results
        final_results = []
        for doc_id in sorted_ids:
            result = doc_map[doc_id]
            result.score = combined_scores[doc_id]
            final_results.append(result)

        return final_results

    async def index_for_bm25(self, documents: List[Document]) -> None:
        """Index documents for BM25 search."""
        self.bm25_searcher.index_documents(documents)


class QueryExpander(LoggerMixin):
    """Query expansion for improved retrieval."""

    def __init__(self):
        """Initialize query expander."""
        self.settings = get_settings()

    def expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms."""
        expanded_queries = [query]

        # Simple expansion strategies
        # 1. Add question variations
        if not query.endswith("?"):
            expanded_queries.append(f"What is {query}?")
            expanded_queries.append(f"How does {query} work?")

        # 2. Extract key terms and create variations
        tokens = query.lower().split()
        if len(tokens) > 3:
            # Create sub-queries from important terms
            important_tokens = [t for t in tokens if len(t) > 3]
            if len(important_tokens) >= 2:
                expanded_queries.append(" ".join(important_tokens))

        return expanded_queries

    def reformulate_query(self, query: str, context: Optional[str] = None) -> str:
        """Reformulate query based on context."""
        if context:
            # If we have context from previous interactions, use it
            reformulated = f"{context} {query}"
            return reformulated
        return query


# Global instances
hybrid_searcher = HybridSearcher()
query_expander = QueryExpander()