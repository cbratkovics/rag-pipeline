"""Text chunking strategies for document processing."""

import re
from typing import List, Optional, Tuple

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

from src.core.config import get_settings
from src.infrastructure.logging import LoggerMixin


class ChunkingStrategy(LoggerMixin):
    """Base class for chunking strategies."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        """Initialize chunking strategy."""
        self.settings = get_settings()
        self.chunk_size = chunk_size or self.settings.chunk_size
        self.chunk_overlap = chunk_overlap or self.settings.chunk_overlap
        self._ensure_nltk_data()

    def _ensure_nltk_data(self) -> None:
        """Download required NLTK data if not present."""
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            self.logger.info("Downloading NLTK punkt tokenizer")
            nltk.download("punkt", quiet=True)

    def chunk_text(self, text: str) -> List[str]:
        """Chunk text into smaller pieces."""
        raise NotImplementedError


class FixedSizeChunker(ChunkingStrategy):
    """Fixed-size chunking with character count."""

    def chunk_text(self, text: str) -> List[str]:
        """Chunk text into fixed-size pieces."""
        if not text:
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                sentence_end = text.rfind(".", start, end)
                if sentence_end == -1:
                    sentence_end = text.rfind("!", start, end)
                if sentence_end == -1:
                    sentence_end = text.rfind("?", start, end)

                if sentence_end != -1 and sentence_end > start:
                    end = sentence_end + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap if end < len(text) else end

        return chunks


class SentenceChunker(ChunkingStrategy):
    """Sentence-based chunking."""

    def chunk_text(self, text: str) -> List[str]:
        """Chunk text by sentences."""
        if not text:
            return []

        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(" ".join(current_chunk))
                # Start new chunk with overlap
                if self.chunk_overlap > 0:
                    # Keep last few sentences for overlap
                    overlap_sentences = []
                    overlap_size = 0
                    for sent in reversed(current_chunk):
                        overlap_size += len(sent)
                        if overlap_size >= self.chunk_overlap:
                            break
                        overlap_sentences.insert(0, sent)
                    current_chunk = overlap_sentences
                    current_size = sum(len(s) for s in current_chunk)
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_size

        # Add remaining chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks


class SemanticChunker(ChunkingStrategy):
    """Semantic chunking based on content structure."""

    def chunk_text(self, text: str) -> List[str]:
        """Chunk text based on semantic boundaries."""
        if not text:
            return []

        # Split by paragraphs first
        paragraphs = re.split(r"\n\n+", text)
        chunks = []
        current_chunk = []
        current_size = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            paragraph_size = len(paragraph)

            # If paragraph is too large, use sentence chunking
            if paragraph_size > self.chunk_size:
                sub_chunker = SentenceChunker(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                )
                sub_chunks = sub_chunker.chunk_text(paragraph)
                chunks.extend(sub_chunks)
            elif current_size + paragraph_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append("\n\n".join(current_chunk))
                # Start new chunk with overlap if needed
                current_chunk = [paragraph]
                current_size = paragraph_size
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size

        # Add remaining chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks


class DynamicChunker(ChunkingStrategy):
    """Dynamic chunking based on query complexity."""

    def __init__(
        self,
        min_chunk_size: int = 256,
        max_chunk_size: int = 1024,
        chunk_overlap: Optional[int] = None,
    ):
        """Initialize dynamic chunker."""
        super().__init__(chunk_overlap=chunk_overlap)
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def determine_chunk_size(self, query_complexity: float) -> int:
        """Determine chunk size based on query complexity."""
        # Scale chunk size based on complexity (0.0 to 1.0)
        chunk_range = self.max_chunk_size - self.min_chunk_size
        chunk_size = int(self.min_chunk_size + (chunk_range * query_complexity))
        return chunk_size

    def chunk_text(
        self,
        text: str,
        query_complexity: float = 0.5,
    ) -> List[str]:
        """Chunk text with dynamic size based on query."""
        if not text:
            return []

        chunk_size = self.determine_chunk_size(query_complexity)
        chunker = SemanticChunker(
            chunk_size=chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        return chunker.chunk_text(text)


class ChunkerFactory:
    """Factory for creating chunking strategies."""

    @staticmethod
    def create(
        strategy: str = "semantic",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> ChunkingStrategy:
        """Create a chunking strategy."""
        if strategy == "fixed":
            return FixedSizeChunker(chunk_size, chunk_overlap)
        elif strategy == "sentence":
            return SentenceChunker(chunk_size, chunk_overlap)
        elif strategy == "semantic":
            return SemanticChunker(chunk_size, chunk_overlap)
        elif strategy == "dynamic":
            return DynamicChunker(chunk_overlap=chunk_overlap)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")