"""Cross-encoder reranking for improved precision."""

import torch
from sentence_transformers import CrossEncoder

from src.core.config import get_settings
from src.core.models import RetrievedDocument
from src.infrastructure.logging import LoggerMixin


class Reranker(LoggerMixin):
    """Cross-encoder reranker for document reordering."""

    def __init__(self, model_name: str | None = None):
        """Initialize reranker."""
        self.settings = get_settings()
        self.model_name = model_name or self.settings.reranker_model
        self.model: CrossEncoder | None = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def initialize(self) -> None:
        """Load the reranking model."""
        if self.model is None:
            self.logger.info("Loading reranker model", model=self.model_name)
            self.model = CrossEncoder(
                self.model_name,
                max_length=512,
                device=self.device,
            )
            self.logger.info(
                "Reranker model loaded",
                model=self.model_name,
                device=self.device,
            )

    def rerank(
        self,
        query: str,
        documents: list[RetrievedDocument],
        top_k: int | None = None,
    ) -> list[RetrievedDocument]:
        """Rerank documents using cross-encoder."""
        if not documents:
            return []

        if self.model is None:
            self.initialize()

        top_k = top_k or self.settings.reranker_top_k
        top_k = min(top_k, len(documents))

        # Prepare query-document pairs
        pairs = [[query, doc.document.content] for doc in documents]

        # Get reranking scores
        try:
            if self.model is None:
                return documents[:top_k]
            scores = self.model.predict(pairs, show_progress_bar=False)
        except Exception as e:
            self.logger.error("Reranking failed", error=str(e))
            # Return original order if reranking fails
            return documents[:top_k]

        # Update documents with rerank scores
        for doc, score in zip(documents, scores, strict=False):
            doc.rerank_score = float(score)

        # Sort by rerank score
        reranked = sorted(
            documents,
            key=lambda x: x.rerank_score or 0.0,
            reverse=True,
        )

        # Update final scores to be rerank scores
        for doc in reranked[:top_k]:
            if doc.rerank_score is not None:
                doc.score = doc.rerank_score

        self.logger.debug(
            "Documents reranked",
            original_count=len(documents),
            returned_count=min(top_k, len(documents)),
        )

        return reranked[:top_k]

    def batch_rerank(
        self,
        queries: list[str],
        document_sets: list[list[RetrievedDocument]],
        top_k: int | None = None,
    ) -> list[list[RetrievedDocument]]:
        """Rerank multiple query-document sets."""
        if self.model is None:
            self.initialize()

        results = []
        for query, documents in zip(queries, document_sets, strict=False):
            reranked = self.rerank(query, documents, top_k)
            results.append(reranked)

        return results


# Global reranker instance
reranker = Reranker()
