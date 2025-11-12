"""Vector store interfaces and implementations."""

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, cast
from uuid import UUID

import chromadb
from chromadb.config import Settings as ChromaSettings
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from src.core.config import get_settings
from src.core.models import Document, DocumentSource, RetrievedDocument
from src.infrastructure.logging import LoggerMixin
from src.retrieval.embeddings import embedding_manager


class VectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store."""
        pass

    @abstractmethod
    async def add_documents(self, documents: list[Document]) -> list[str]:
        """Add documents to the vector store."""
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[RetrievedDocument]:
        """Search for similar documents."""
        pass

    @abstractmethod
    async def delete_documents(self, ids: list[str]) -> bool:
        """Delete documents by IDs."""
        pass

    @abstractmethod
    async def get_document(self, doc_id: str) -> Document | None:
        """Get a document by ID."""
        pass

    @abstractmethod
    async def update_document(self, document: Document) -> bool:
        """Update a document."""
        pass

    @abstractmethod
    async def count_documents(self) -> int:
        """Count total documents in the store."""
        pass


class QdrantVectorStore(VectorStore, LoggerMixin):
    """Qdrant vector store implementation."""

    def __init__(self):
        """Initialize Qdrant vector store."""
        self.settings = get_settings()
        self.client: QdrantClient | None = None
        self.collection_name = self.settings.qdrant_collection
        self.dimension = self.settings.embedding_dimension

    async def initialize(self) -> None:
        """Initialize Qdrant connection and collection (optional service)."""
        try:
            self.client = QdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port,
                api_key=self.settings.qdrant_api_key,
            )

            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.dimension,
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )
                self.logger.info("✓ Created Qdrant collection", collection=self.collection_name)
            else:
                self.logger.info(
                    "✓ Using existing Qdrant collection", collection=self.collection_name
                )

        except Exception as e:
            self.logger.warning(
                "⚠ Qdrant unavailable - running in degraded mode (vector search disabled)",
                error=str(e),
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port,
            )
            self.client = None

    def is_available(self) -> bool:
        """Check if Qdrant is available and connected."""
        return self.client is not None

    async def add_documents(self, documents: list[Document]) -> list[str]:
        """Add documents to Qdrant."""
        if not self.client:
            await self.initialize()

        if not self.is_available():
            self.logger.warning("Cannot add documents - Qdrant unavailable")
            return []

        if not documents:
            return []

        try:
            # Generate embeddings if not present
            for doc in documents:
                if doc.embedding is None:
                    doc.embedding = embedding_manager.embed_text(doc.content)

            # Prepare points for Qdrant
            points = []
            for doc in documents:
                if doc.embedding is None:
                    raise ValueError(f"Document {doc.id} has no embedding")
                point = qdrant_models.PointStruct(
                    id=str(doc.id),
                    vector=doc.embedding,
                    payload={
                        "content": doc.content,
                        "metadata": doc.metadata,
                        "source": doc.source.value,
                        "source_id": doc.source_id,
                        "title": doc.title,
                        "author": doc.author,
                        "published_date": doc.published_date.isoformat()
                        if doc.published_date
                        else None,
                        "url": doc.url,
                        "license": doc.license,
                        "chunk_id": doc.chunk_id,
                        "parent_id": str(doc.parent_id) if doc.parent_id else None,
                    },
                )
                points.append(point)

            # Upload to Qdrant
            if self.client is None:
                raise RuntimeError("Qdrant client not initialized")
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

            self.logger.info("Added documents to Qdrant", count=len(documents))
            return [str(doc.id) for doc in documents]

        except Exception as e:
            self.logger.error("Failed to add documents to Qdrant", error=str(e))
            raise

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[RetrievedDocument]:
        """Search for similar documents in Qdrant."""
        if not self.client:
            await self.initialize()

        if not self.is_available():
            self.logger.debug("Cannot search - Qdrant unavailable, returning empty results")
            return []

        try:
            # Build filter if provided
            search_filter = None
            if metadata_filter:
                must_conditions = []
                for key, value in metadata_filter.items():
                    if isinstance(value, list):
                        must_conditions.append(
                            qdrant_models.FieldCondition(
                                key=key,
                                match=qdrant_models.MatchAny(any=value),
                            )
                        )
                    else:
                        must_conditions.append(
                            qdrant_models.FieldCondition(
                                key=key,
                                match=qdrant_models.MatchValue(value=value),
                            )
                        )
                if must_conditions:
                    search_filter = qdrant_models.Filter(must=cast(Any, must_conditions))

            # Search
            if self.client is None:
                raise RuntimeError("Qdrant client not initialized")
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=search_filter,
            )

            # Convert to RetrievedDocument
            retrieved_docs = []
            for result in results:
                if result.payload is None:
                    continue
                doc = Document(
                    id=UUID(str(result.id)),
                    content=result.payload["content"],
                    metadata=result.payload.get("metadata", {}),
                    source=result.payload["source"],
                    source_id=result.payload.get("source_id"),
                    title=result.payload.get("title"),
                    author=result.payload.get("author"),
                    url=result.payload.get("url"),
                    license=result.payload.get("license"),
                    chunk_id=result.payload.get("chunk_id"),
                    parent_id=UUID(result.payload["parent_id"])
                    if result.payload.get("parent_id")
                    else None,
                )
                retrieved = RetrievedDocument(
                    document=doc,
                    score=result.score,
                    semantic_score=result.score,
                )
                retrieved_docs.append(retrieved)

            self.logger.debug("Search completed", results=len(retrieved_docs))
            return retrieved_docs

        except Exception as e:
            self.logger.error("Failed to search in Qdrant", error=str(e))
            raise

    async def delete_documents(self, ids: list[str]) -> bool:
        """Delete documents from Qdrant."""
        if not self.client:
            await self.initialize()

        if not self.is_available():
            self.logger.warning("Cannot delete documents - Qdrant unavailable")
            return False

        try:
            if self.client is None:
                raise RuntimeError("Qdrant client not initialized")
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.PointIdsList(
                    points=cast(Any, ids),
                ),
            )
            self.logger.info("Deleted documents from Qdrant", count=len(ids))
            return True

        except Exception as e:
            self.logger.error("Failed to delete documents from Qdrant", error=str(e))
            return False

    async def get_document(self, doc_id: str) -> Document | None:
        """Get a document by ID from Qdrant."""
        if not self.client:
            await self.initialize()

        if not self.is_available():
            self.logger.debug("Cannot get document - Qdrant unavailable")
            return None

        try:
            if self.client is None:
                raise RuntimeError("Qdrant client not initialized")
            results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[doc_id],
            )

            if not results:
                return None

            result = results[0]
            if result.payload is None:
                return None
            doc = Document(
                id=UUID(str(result.id)),
                content=result.payload["content"],
                metadata=result.payload.get("metadata", {}),
                source=result.payload["source"],
                source_id=result.payload.get("source_id"),
                title=result.payload.get("title"),
                author=result.payload.get("author"),
                url=result.payload.get("url"),
                license=result.payload.get("license"),
                chunk_id=result.payload.get("chunk_id"),
                parent_id=UUID(result.payload["parent_id"])
                if result.payload.get("parent_id")
                else None,
            )
            return doc

        except Exception as e:
            self.logger.error("Failed to get document from Qdrant", error=str(e), doc_id=doc_id)
            return None

    async def update_document(self, document: Document) -> bool:
        """Update a document in Qdrant."""
        # In Qdrant, update is the same as upsert
        result = await self.add_documents([document])
        return len(result) > 0

    async def count_documents(self) -> int:
        """Count total documents in Qdrant."""
        if not self.client:
            await self.initialize()

        if not self.is_available():
            self.logger.debug("Cannot count documents - Qdrant unavailable")
            return 0

        try:
            if self.client is None:
                raise RuntimeError("Qdrant client not initialized")
            info = self.client.get_collection(self.collection_name)
            if info.points_count is None:
                return 0
            return int(info.points_count)

        except Exception as e:
            self.logger.error("Failed to count documents in Qdrant", error=str(e))
            return 0


class ChromaDBVectorStore(VectorStore, LoggerMixin):
    """ChromaDB vector store implementation."""

    def __init__(self):
        """Initialize ChromaDB vector store."""
        self.settings = get_settings()
        self.collection_name = self.settings.chromadb_collection
        self.persist_dir = ".chroma"  # Default ChromaDB persist directory
        self.client: chromadb.ClientAPI | None = None
        self.collection: chromadb.Collection | None = None
        self.dimension = self.settings.embedding_dimension

    async def initialize(self) -> None:
        """Initialize ChromaDB connection and collection."""
        try:
            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            # Check document count
            count = self.collection.count()

            self.logger.info(
                "✓ ChromaDB initialized",
                collection=self.collection_name,
                persist_dir=self.persist_dir,
                document_count=count,
            )

        except Exception as e:
            self.logger.warning(
                "⚠ ChromaDB unavailable - running in degraded mode (vector search disabled)",
                error=str(e),
                persist_dir=self.persist_dir,
            )
            self.client = None
            self.collection = None

    def is_available(self) -> bool:
        """Check if ChromaDB is available and connected."""
        return self.client is not None and self.collection is not None

    async def add_documents(self, documents: list[Document]) -> list[str]:
        """Add documents to ChromaDB."""
        if not self.client or not self.collection:
            await self.initialize()

        if not self.is_available():
            self.logger.debug("Cannot add documents - ChromaDB unavailable")
            return []

        try:
            # Generate embeddings
            contents = [doc.content for doc in documents]
            embeddings = embedding_manager.embed_batch(contents)

            # Prepare data for ChromaDB
            ids = [str(doc.id) for doc in documents]
            metadatas = []

            for doc in documents:
                metadata: dict[str, Any] = {
                    "source": doc.source.value if doc.source else "unknown",
                    "title": doc.title or "",
                    "author": doc.author or "",
                    "url": doc.url or "",
                    "license": doc.license or "",
                }
                # Add custom metadata fields
                if doc.metadata:
                    metadata.update(doc.metadata)
                metadatas.append(metadata)

            # Add to collection
            if self.collection is None:
                raise RuntimeError("ChromaDB collection not initialized")

            # Cast embeddings and metadatas to satisfy type checker
            embeddings_list = cast(list[Sequence[float]], embeddings)
            metadatas_list = cast(list[Mapping[str, Any]], metadatas)

            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                documents=contents,
                metadatas=metadatas_list,
            )

            self.logger.info(
                "Added documents to ChromaDB",
                count=len(documents),
                collection=self.collection_name,
            )

            return ids

        except Exception as e:
            self.logger.error("Failed to add documents to ChromaDB", error=str(e))
            return []

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[RetrievedDocument]:
        """Search for similar documents in ChromaDB."""
        if not self.client or not self.collection:
            await self.initialize()

        if not self.is_available():
            self.logger.debug("Cannot search - ChromaDB unavailable")
            return []

        try:
            if self.collection is None:
                raise RuntimeError("ChromaDB collection not initialized")

            # Build where filter if metadata_filter provided
            where = metadata_filter if metadata_filter else None

            # Cast query embedding to satisfy type checker
            query_embeddings_list = cast(list[Sequence[float]], [query_embedding])

            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=query_embeddings_list,
                n_results=top_k,
                where=where,
            )

            # Convert to RetrievedDocument objects
            retrieved_docs = []

            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    doc_id = results["ids"][0][i]
                    content = results["documents"][0][i] if results["documents"] else ""
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0.0

                    # Convert distance to similarity score (cosine distance -> similarity)
                    # ChromaDB returns L2 distance, but we configured cosine space
                    # Cosine distance ranges from 0 (identical) to 2 (opposite)
                    # Convert to similarity: 1 - (distance / 2)
                    score = 1.0 - (distance / 2.0) if distance <= 2.0 else 0.0

                    # Create Document object with proper type casting
                    # Convert ChromaDB metadata to dict[str, Any]
                    doc_metadata = dict(metadata) if metadata else {}

                    # Convert source string to DocumentSource enum
                    source_str = str(metadata.get("source", "custom"))
                    try:
                        doc_source = DocumentSource(source_str)
                    except ValueError:
                        doc_source = DocumentSource.CUSTOM

                    doc = Document(
                        id=UUID(doc_id),
                        content=content,
                        metadata=doc_metadata,
                        source=doc_source,
                        title=str(metadata.get("title")) if metadata.get("title") else None,
                        author=str(metadata.get("author")) if metadata.get("author") else None,
                        url=str(metadata.get("url")) if metadata.get("url") else None,
                        license=str(metadata.get("license")) if metadata.get("license") else None,
                    )

                    retrieved_docs.append(
                        RetrievedDocument(
                            document=doc,
                            score=float(score),
                            semantic_score=float(score),
                        )
                    )

            return retrieved_docs

        except Exception as e:
            self.logger.error("Failed to search ChromaDB", error=str(e))
            return []

    async def delete_documents(self, ids: list[str]) -> bool:
        """Delete documents from ChromaDB by IDs."""
        if not self.client or not self.collection:
            await self.initialize()

        if not self.is_available():
            self.logger.debug("Cannot delete documents - ChromaDB unavailable")
            return False

        try:
            if self.collection is None:
                raise RuntimeError("ChromaDB collection not initialized")

            self.collection.delete(ids=ids)

            self.logger.info("Deleted documents from ChromaDB", count=len(ids))
            return True

        except Exception as e:
            self.logger.error("Failed to delete documents from ChromaDB", error=str(e))
            return False

    async def get_document(self, doc_id: str) -> Document | None:
        """Get a document from ChromaDB by ID."""
        if not self.client or not self.collection:
            await self.initialize()

        if not self.is_available():
            self.logger.debug("Cannot get document - ChromaDB unavailable")
            return None

        try:
            if self.collection is None:
                raise RuntimeError("ChromaDB collection not initialized")

            results = self.collection.get(ids=[doc_id], include=["documents", "metadatas"])

            if not results["ids"] or len(results["ids"]) == 0:
                return None

            content = results["documents"][0] if results["documents"] else ""
            metadata = results["metadatas"][0] if results["metadatas"] else {}

            # Convert ChromaDB metadata to dict[str, Any]
            doc_metadata = dict(metadata) if metadata else {}

            # Convert source string to DocumentSource enum
            source_str = str(metadata.get("source", "custom"))
            try:
                doc_source = DocumentSource(source_str)
            except ValueError:
                doc_source = DocumentSource.CUSTOM

            doc = Document(
                id=UUID(doc_id),
                content=content,
                metadata=doc_metadata,
                source=doc_source,
                title=str(metadata.get("title")) if metadata.get("title") else None,
                author=str(metadata.get("author")) if metadata.get("author") else None,
                url=str(metadata.get("url")) if metadata.get("url") else None,
                license=str(metadata.get("license")) if metadata.get("license") else None,
            )

            return doc

        except Exception as e:
            self.logger.error("Failed to get document from ChromaDB", error=str(e), doc_id=doc_id)
            return None

    async def update_document(self, document: Document) -> bool:
        """Update a document in ChromaDB."""
        # ChromaDB doesn't have a native update - use upsert by re-adding
        result = await self.add_documents([document])
        return len(result) > 0

    async def count_documents(self) -> int:
        """Count total documents in ChromaDB."""
        if not self.client or not self.collection:
            await self.initialize()

        if not self.is_available():
            self.logger.debug("Cannot count documents - ChromaDB unavailable")
            return 0

        try:
            if self.collection is None:
                raise RuntimeError("ChromaDB collection not initialized")

            count = self.collection.count()
            return count

        except Exception as e:
            self.logger.error("Failed to count documents in ChromaDB", error=str(e))
            return 0


class VectorStoreFactory:
    """Factory for creating vector store instances."""

    @staticmethod
    def create(store_type: str | None = None) -> VectorStore:
        """Create a vector store instance."""
        settings = get_settings()
        store_type = store_type or settings.vector_store_type

        if store_type == "qdrant":
            return QdrantVectorStore()
        elif store_type == "chromadb":
            return ChromaDBVectorStore()
        else:
            raise ValueError(f"Unknown vector store type: {store_type}")


# Global vector store instance
vector_store = VectorStoreFactory.create()
