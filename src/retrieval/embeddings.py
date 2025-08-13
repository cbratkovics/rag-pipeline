"""Embedding generation and management."""

from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.infrastructure.cache import CacheDecorator, cache_manager
from src.infrastructure.logging import LoggerMixin


class EmbeddingManager(LoggerMixin):
    """Manages embedding generation for documents and queries."""

    def __init__(self, model_name: Optional[str] = None):
        """Initialize embedding manager."""
        self.settings = get_settings()
        self.model_name = model_name or self.settings.embedding_model
        self.model: Optional[SentenceTransformer] = None
        self.dimension = self.settings.embedding_dimension

    def initialize(self) -> None:
        """Load the embedding model."""
        if self.model is None:
            self.logger.info("Loading embedding model", model=self.model_name)
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            self.logger.info(
                "Embedding model loaded",
                model=self.model_name,
                dimension=self.dimension,
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def embed_text(self, text: str, normalize: bool = True) -> List[float]:
        """Generate embedding for a single text."""
        if self.model is None:
            self.initialize()

        embedding = self.model.encode(
            text,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        return embedding.tolist()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def embed_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        normalize: bool = True,
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if self.model is None:
            self.initialize()

        if not texts:
            return []

        batch_size = batch_size or self.settings.embedding_batch_size

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=len(texts) > 100,
        )

        return embeddings.tolist()

    @CacheDecorator(key_prefix="embedding", ttl=86400)  # Cache for 24 hours
    async def embed_with_cache(self, text: str, normalize: bool = True) -> List[float]:
        """Generate embedding with caching."""
        return self.embed_text(text, normalize)

    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """Compute cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Normalize if not already normalized
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2)

        similarity = np.dot(vec1_norm, vec2_norm)
        return float(similarity)

    def compute_similarities(
        self,
        query_embedding: List[float],
        document_embeddings: List[List[float]],
    ) -> List[float]:
        """Compute similarities between query and multiple documents."""
        if not document_embeddings:
            return []

        query_vec = np.array(query_embedding)
        doc_vecs = np.array(document_embeddings)

        # Normalize
        query_norm = query_vec / np.linalg.norm(query_vec)
        doc_norms = doc_vecs / np.linalg.norm(doc_vecs, axis=1, keepdims=True)

        # Compute similarities
        similarities = np.dot(doc_norms, query_norm)
        return similarities.tolist()


# Global embedding manager instance
embedding_manager = EmbeddingManager()