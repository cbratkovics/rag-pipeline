#!/usr/bin/env python3
"""Initialize vector store with comprehensive seed documents.

This script initializes ChromaDB with diverse documents about RAG, AI, and related topics.
Works both locally and in production (Render).
"""

import logging
import os
import sys
from pathlib import Path

# Set protobuf environment before importing ChromaDB
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Comprehensive seed documents about RAG, AI, and related topics
SEED_DOCUMENTS = [
    {
        "id": "rag_intro_1",
        "text": """Retrieval-Augmented Generation (RAG) is an advanced AI technique that combines the power of large language models with external knowledge retrieval. In a RAG system, when a user asks a question, the system first retrieves relevant documents from a knowledge base, then uses these documents as context for the language model to generate an informed response. This approach significantly reduces hallucinations and provides more accurate, factual answers grounded in real data.""",
        "metadata": {"topic": "RAG fundamentals", "category": "overview"},
    },
    {
        "id": "rag_architecture_2",
        "text": """A typical RAG architecture consists of three main components: the retriever, the vector store, and the generator. The retriever is responsible for finding relevant documents given a query. The vector store holds document embeddings that enable semantic search. The generator is usually a large language model that synthesizes information from retrieved documents to produce coherent answers. These components work together in a pipeline to deliver contextually relevant responses.""",
        "metadata": {"topic": "RAG architecture", "category": "technical"},
    },
    {
        "id": "vector_embeddings_3",
        "text": """Vector embeddings are numerical representations of text that capture semantic meaning in high-dimensional space. Modern embedding models like sentence-transformers convert text into dense vectors (typically 384 to 1536 dimensions) where semantically similar texts have similar vector representations. This enables semantic search, where queries can match documents based on meaning rather than just keyword overlap. The quality of embeddings directly impacts retrieval accuracy.""",
        "metadata": {"topic": "embeddings", "category": "technical"},
    },
    {
        "id": "hybrid_search_4",
        "text": """Hybrid search combines multiple retrieval methods to achieve better results than any single method alone. The most common approach combines BM25 (keyword-based) search with vector (semantic) search. BM25 is excellent at finding exact keyword matches and rare terms, while vector search captures semantic similarity. By fusing results using techniques like Reciprocal Rank Fusion (RRF), hybrid search leverages the strengths of both approaches.""",
        "metadata": {"topic": "hybrid search", "category": "retrieval"},
    },
    {
        "id": "bm25_algorithm_5",
        "text": """BM25 (Best Matching 25) is a probabilistic ranking function used in information retrieval. It ranks documents based on the query terms appearing in each document, taking into account term frequency, inverse document frequency, and document length normalization. BM25 has two key parameters: k1 (typically 1.2-2.0) controls term frequency saturation, and b (typically 0.75) controls length normalization. Despite being developed in the 1990s, BM25 remains highly effective for keyword-based search.""",
        "metadata": {"topic": "BM25", "category": "algorithms"},
    },
    {
        "id": "rrf_fusion_6",
        "text": """Reciprocal Rank Fusion (RRF) is an elegant method for combining ranked lists from multiple retrieval systems. For each document, RRF computes a score based on its rank positions across all result lists using the formula: score = sum(1/(k + rank)) where k is a constant (typically 60). This approach is simple, requires no training, and effectively handles scenarios where different retrieval methods produce incompatible scores. RRF often outperforms more complex fusion methods.""",
        "metadata": {"topic": "result fusion", "category": "algorithms"},
    },
    {
        "id": "chromadb_7",
        "text": """ChromaDB is an open-source embedding database designed specifically for AI applications. It provides a simple Python API for storing, searching, and managing vector embeddings. ChromaDB supports both in-memory and persistent storage, making it ideal for development and production. Key features include automatic embedding generation, metadata filtering, distance metrics (cosine, L2, IP), and integration with popular embedding models. ChromaDB's simplicity makes it an excellent choice for RAG applications.""",
        "metadata": {"topic": "ChromaDB", "category": "tools"},
    },
    {
        "id": "sentence_transformers_8",
        "text": """Sentence-transformers is a Python framework for creating state-of-the-art sentence and text embeddings. It provides pre-trained models that can encode text into dense vectors capturing semantic information. Popular models include all-MiniLM-L6-v2 (384 dimensions, fast), all-mpnet-base-v2 (768 dimensions, high quality), and multi-qa-mpnet-base-dot-v1 (optimized for question-answering). The framework supports fine-tuning models on custom datasets and offers utilities for semantic search and clustering.""",
        "metadata": {"topic": "embeddings", "category": "tools"},
    },
    {
        "id": "llm_prompting_9",
        "text": """Effective prompting is crucial for RAG systems. A well-designed prompt should include clear instructions, the retrieved context, and the user's question. Common patterns include: 'Based on the following context, answer the question' or 'Use only the provided context to answer'. Including phrases like 'If the answer is not in the context, say so' helps reduce hallucinations. The order and formatting of context documents can significantly impact response quality.""",
        "metadata": {"topic": "LLM prompting", "category": "best practices"},
    },
    {
        "id": "chunking_strategies_10",
        "text": """Document chunking is the process of splitting large documents into smaller, manageable pieces for embedding and retrieval. Common strategies include fixed-size chunking (e.g., 512 tokens with 50-token overlap), sentence-based chunking, paragraph-based chunking, and semantic chunking that respects natural boundaries. The optimal chunk size balances context preservation with retrieval precision. Overlap between chunks ensures that information spanning chunk boundaries is not lost.""",
        "metadata": {"topic": "chunking", "category": "preprocessing"},
    },
    {
        "id": "evaluation_metrics_11",
        "text": """RAG systems require specialized evaluation metrics. RAGAS (RAG Assessment) provides metrics like context relevancy (are retrieved docs relevant?), faithfulness (is the answer grounded in context?), answer relevancy (does it address the question?), and context recall (was all necessary context retrieved?). Traditional NLP metrics like BLEU and ROUGE are less suitable for RAG as they focus on exact text overlap rather than semantic correctness.""",
        "metadata": {"topic": "evaluation", "category": "metrics"},
    },
    {
        "id": "context_window_12",
        "text": """The context window is the maximum number of tokens an LLM can process in a single request, including both input and output. GPT-3.5-turbo has a 4,096 token context window, while GPT-4 offers up to 128k tokens. In RAG systems, the context window limits how many retrieved documents can be included in the prompt. This necessitates careful selection of top-k documents and efficient chunking strategies to maximize information density within the available window.""",
        "metadata": {"topic": "LLM constraints", "category": "technical"},
    },
    {
        "id": "reranking_13",
        "text": """Reranking improves retrieval quality by applying a more sophisticated model to re-order an initial set of retrieved documents. Cross-encoder models like ms-marco-MiniLM are specifically trained for this task. Unlike bi-encoders used for initial retrieval, cross-encoders process query-document pairs jointly, capturing fine-grained relevance signals. Reranking is applied to top-k results (typically 10-20) from initial retrieval, as cross-encoders are too slow for searching the entire corpus.""",
        "metadata": {"topic": "reranking", "category": "retrieval"},
    },
    {
        "id": "semantic_search_14",
        "text": """Semantic search goes beyond keyword matching to understand the intent and contextual meaning of queries. Using vector embeddings, semantic search can match queries like 'how to train a neural network' with documents about 'machine learning model training' even if they don't share exact words. Distance metrics like cosine similarity measure how close vectors are in embedding space. Modern RAG systems rely heavily on semantic search to find contextually relevant information.""",
        "metadata": {"topic": "semantic search", "category": "retrieval"},
    },
    {
        "id": "openai_embeddings_15",
        "text": """OpenAI provides powerful embedding models through their API. The text-embedding-ada-002 model produces 1,536-dimensional embeddings and is optimized for search, clustering, and classification tasks. These embeddings offer excellent semantic understanding but require API calls and have associated costs. For applications requiring offline or cost-effective solutions, open-source alternatives like sentence-transformers provide competitive performance with local execution.""",
        "metadata": {"topic": "embeddings", "category": "tools"},
    },
    {
        "id": "document_metadata_16",
        "text": """Metadata enriches documents with structured information that can improve retrieval and filtering. Common metadata includes source, author, date, document type, and topic tags. In RAG systems, metadata filtering allows queries like 'find documents from 2023 about machine learning' or 'retrieve only peer-reviewed papers'. Effective metadata design balances richness with maintainability, ensuring that metadata is accurate and consistently applied across the corpus.""",
        "metadata": {"topic": "metadata", "category": "best practices"},
    },
    {
        "id": "async_processing_17",
        "text": """Asynchronous processing is essential for building responsive RAG applications. Using async/await patterns in Python with libraries like asyncio allows concurrent handling of multiple queries, parallel document retrieval, and non-blocking API calls. FastAPI natively supports async endpoints, enabling high-throughput RAG services. Async processing is particularly important when dealing with slow operations like embedding generation or external API calls to LLM providers.""",
        "metadata": {"topic": "async programming", "category": "performance"},
    },
    {
        "id": "caching_strategies_18",
        "text": """Caching dramatically improves RAG system performance and reduces costs. Common caching layers include: embedding cache (store computed embeddings), retrieval cache (cache search results for common queries), and LLM response cache (reuse answers for identical queries). Redis is popular for distributed caching. Cache invalidation strategies must balance freshness with hit rates. Time-to-live (TTL) and least-recently-used (LRU) eviction policies are commonly used.""",
        "metadata": {"topic": "caching", "category": "performance"},
    },
    {
        "id": "prompt_engineering_19",
        "text": """Prompt engineering for RAG involves crafting templates that effectively combine retrieved context with user queries. Best practices include: clearly separating context from question, numbering context documents for reference, instructing the model to cite sources, and setting expectations about knowledge boundaries. System messages can establish the AI's role (e.g., 'helpful assistant that answers based only on provided context'). Iterative testing is essential to refine prompts for specific use cases.""",
        "metadata": {"topic": "prompt engineering", "category": "best practices"},
    },
    {
        "id": "scalability_20",
        "text": """Scaling RAG systems requires attention to multiple components. Vector stores like Qdrant and Weaviate offer distributed architectures for handling billions of vectors. Horizontal scaling of API servers behind load balancers distributes query traffic. Document ingestion pipelines benefit from batch processing and message queues. Monitoring tools like Prometheus and Grafana track latency, throughput, and error rates. As systems grow, specialized infrastructure for embeddings, retrieval, and generation may be warranted.""",
        "metadata": {"topic": "scalability", "category": "architecture"},
    },
    {
        "id": "ab_testing_21",
        "text": """A/B testing in RAG systems helps optimize retrieval and generation parameters. Common experiments include: comparing fusion methods (RRF vs weighted), testing different embedding models, varying top-k retrieval counts, and trying different LLM prompts. Metrics should align with business goals—user satisfaction, answer accuracy, or response time. Statistical significance testing ensures observed differences aren't due to chance. Feature flags enable safe experimentation in production.""",
        "metadata": {"topic": "A/B testing", "category": "optimization"},
    },
    {
        "id": "hallucination_mitigation_22",
        "text": """Hallucination occurs when LLMs generate plausible-sounding but incorrect information. RAG mitigates this by grounding responses in retrieved documents. Additional strategies include: instructing models to acknowledge uncertainty, implementing confidence scoring, requiring citation of source documents, and using faithfulness metrics during evaluation. Some systems use multiple models for verification or employ rule-based checks for obviously incorrect statements.""",
        "metadata": {"topic": "hallucination", "category": "reliability"},
    },
    {
        "id": "fastapi_framework_23",
        "text": """FastAPI is a modern Python web framework ideal for building RAG APIs. It offers automatic OpenAPI documentation, request validation via Pydantic, native async support, and excellent performance. FastAPI's dependency injection system cleanly manages resources like database connections and model instances. The framework's type hints enable better IDE support and catch errors early. For RAG applications, FastAPI simplifies building production-ready APIs with health checks, metrics, and proper error handling.""",
        "metadata": {"topic": "FastAPI", "category": "tools"},
    },
    {
        "id": "monitoring_observability_24",
        "text": """Observability is crucial for production RAG systems. Key metrics include query latency (p50, p95, p99), retrieval accuracy, LLM token usage, and error rates. Distributed tracing with OpenTelemetry tracks requests across components. Structured logging captures context for debugging. Dashboards visualize system health. Alerting on SLA violations enables rapid response. Cost tracking monitors API usage. User feedback loops identify quality issues. Together, these practices ensure reliable, efficient RAG services.""",
        "metadata": {"topic": "monitoring", "category": "operations"},
    },
    {
        "id": "cost_optimization_25",
        "text": """RAG systems incur costs from embeddings, vector storage, and LLM API calls. Optimization strategies include: using smaller, efficient embedding models (all-MiniLM-L6-v2 vs text-embedding-ada-002), caching common queries, batching embedding requests, implementing rate limiting, and choosing cost-effective LLM providers. Open-source models run locally eliminate API costs but require infrastructure. Monitoring token usage and setting budgets prevents unexpected expenses. The cost-quality tradeoff should align with business requirements.""",
        "metadata": {"topic": "cost optimization", "category": "optimization"},
    },
]


def get_persist_dir() -> str:
    """Get ChromaDB persistence directory, checking both local and Render paths."""
    # Try multiple possible locations
    paths = [
        os.getenv("CHROMA_PERSIST_DIR", ".chroma"),
        "/opt/render/project/.chroma",
        ".chroma",
    ]

    for path in paths:
        path_obj = Path(path)
        if path_obj.exists() or path_obj.parent.exists():
            logger.info(f"Using persist directory: {path}")
            return path

    # Default to first option
    logger.info(f"Using default persist directory: {paths[0]}")
    return paths[0]


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        chunks.append(chunk)
        start = start + chunk_size - overlap if end < text_length else text_length

    return chunks


def load_file_documents(data_dir: str) -> list[dict]:
    """Load documents from files in data directory."""
    documents = []
    data_path = Path(data_dir)

    if not data_path.exists():
        logger.warning(f"Data directory {data_dir} does not exist")
        return documents

    for file_path in data_path.glob("**/*"):
        if file_path.is_file() and file_path.suffix in [".txt", ".md"]:
            logger.info(f"Loading {file_path}")
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                chunks = chunk_text(content)
                for i, chunk in enumerate(chunks):
                    documents.append(
                        {
                            "id": f"{file_path.stem}_{i}",
                            "text": chunk,
                            "metadata": {
                                "source": str(file_path),
                                "chunk_index": i,
                                "filename": file_path.name,
                                "category": "file_based",
                            },
                        }
                    )
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")

    logger.info(f"Loaded {len(documents)} document chunks from files")
    return documents


def initialize_vector_store(
    data_dir: str = "data/seed",
    persist_dir: str | None = None,
    embedding_model: str = "all-MiniLM-L6-v2",
    reset: bool = False,
    collection_name: str = "rag_documents",
) -> dict:
    """Initialize ChromaDB vector store with seed documents.

    Args:
        data_dir: Directory containing additional documents to load
        persist_dir: ChromaDB persistence directory
        embedding_model: Sentence transformer model name
        reset: Whether to reset the collection before adding documents
        collection_name: Name of the ChromaDB collection

    Returns:
        Dictionary with status and document count
    """
    # Get configuration
    persist_dir = persist_dir or get_persist_dir()

    logger.info("=" * 80)
    logger.info("INITIALIZING VECTOR STORE")
    logger.info("=" * 80)
    logger.info(f"Persist directory: {persist_dir}")
    logger.info(f"Embedding model: {embedding_model}")
    logger.info(f"Collection name: {collection_name}")
    logger.info(f"Reset: {reset}")

    # Initialize ChromaDB client
    try:
        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info("✓ ChromaDB client initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize ChromaDB client: {e}")
        return {"status": "error", "message": str(e)}

    # Reset collection if requested
    if reset:
        try:
            client.delete_collection(collection_name)
            logger.info(f"✓ Deleted existing collection: {collection_name}")
        except Exception as e:
            logger.info(f"No existing collection to delete: {e}")

    # Get or create collection
    try:
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"✓ Collection ready: {collection_name}")
    except Exception as e:
        logger.error(f"✗ Failed to get/create collection: {e}")
        return {"status": "error", "message": str(e)}

    # Prepare all documents (seed + file-based)
    all_documents = SEED_DOCUMENTS.copy()

    # Load additional documents from files if directory exists
    file_documents = load_file_documents(data_dir)
    all_documents.extend(file_documents)

    logger.info(f"Total documents to process: {len(all_documents)}")
    logger.info(f"  - Seed documents: {len(SEED_DOCUMENTS)}")
    logger.info(f"  - File documents: {len(file_documents)}")

    if not all_documents:
        logger.warning("No documents to ingest")
        return {"status": "warning", "message": "No documents found", "count": 0}

    # Initialize embedding model
    try:
        logger.info(f"Loading embedding model: {embedding_model}")
        model = SentenceTransformer(embedding_model)
        logger.info("✓ Embedding model loaded")
    except Exception as e:
        logger.error(f"✗ Failed to load embedding model: {e}")
        return {"status": "error", "message": str(e)}

    # Create embeddings
    try:
        logger.info("Creating embeddings...")
        texts = [doc["text"] for doc in all_documents]
        embeddings = model.encode(texts, show_progress_bar=True)
        embeddings_list = [emb.tolist() for emb in embeddings]
        logger.info(f"✓ Created {len(embeddings_list)} embeddings")
    except Exception as e:
        logger.error(f"✗ Failed to create embeddings: {e}")
        return {"status": "error", "message": str(e)}

    # Store in ChromaDB
    try:
        logger.info("Storing documents in ChromaDB...")
        ids = [doc["id"] for doc in all_documents]
        texts = [doc["text"] for doc in all_documents]
        metadatas = [doc["metadata"] for doc in all_documents]

        collection.add(
            ids=ids,
            embeddings=embeddings_list,
            documents=texts,
            metadatas=metadatas,
        )

        final_count = collection.count()
        logger.info("✓ Successfully stored documents")
        logger.info(f"✓ Collection now contains {final_count} documents")

        logger.info("=" * 80)
        logger.info("VECTOR STORE INITIALIZATION COMPLETE")
        logger.info("=" * 80)

        return {
            "status": "success",
            "count": final_count,
            "seed_docs": len(SEED_DOCUMENTS),
            "file_docs": len(file_documents),
        }

    except Exception as e:
        logger.error(f"✗ Failed to store documents: {e}")
        return {"status": "error", "message": str(e)}


def verify_vector_store(
    persist_dir: str | None = None,
    collection_name: str = "rag_documents",
) -> dict:
    """Verify vector store has documents and can perform searches.

    Args:
        persist_dir: ChromaDB persistence directory
        collection_name: Name of the ChromaDB collection

    Returns:
        Dictionary with verification results
    """
    persist_dir = persist_dir or get_persist_dir()

    logger.info("=" * 80)
    logger.info("VERIFYING VECTOR STORE")
    logger.info("=" * 80)

    try:
        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_collection(collection_name)

        count = collection.count()
        logger.info(f"✓ Collection contains {count} documents")

        if count == 0:
            logger.warning("✗ Collection is empty!")
            return {"status": "empty", "count": 0}

        # Test search
        model = SentenceTransformer("all-MiniLM-L6-v2")
        test_query = "What is RAG?"
        query_embedding = model.encode([test_query])[0].tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
        )

        if results and results.get("documents"):
            logger.info("✓ Search test successful")
            logger.info(f"  Found {len(results['documents'][0])} results")

            # Check scores
            distances = results.get("distances", [[]])[0]
            scores = [1.0 - d for d in distances]

            logger.info(f"  Sample scores: {[f'{s:.4f}' for s in scores]}")

            if all(s > 0 for s in scores):
                logger.info("✓ All scores are non-zero")
                status = "healthy"
            else:
                logger.warning("✗ Some scores are zero")
                status = "degraded"
        else:
            logger.warning("✗ Search returned no results")
            status = "degraded"

        logger.info("=" * 80)
        logger.info(f"VERIFICATION COMPLETE: {status.upper()}")
        logger.info("=" * 80)

        return {
            "status": status,
            "count": count,
            "search_results": len(results["documents"][0]) if results else 0,
            "sample_scores": scores if results else [],
        }

    except Exception as e:
        logger.error(f"✗ Verification failed: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize RAG vector store")
    parser.add_argument(
        "--data-dir",
        default="data/seed",
        help="Directory containing documents to ingest",
    )
    parser.add_argument(
        "--persist-dir",
        default=None,
        help="ChromaDB persistence directory",
    )
    parser.add_argument(
        "--embedding-model",
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model name",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset collection before adding documents",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify vector store, don't initialize",
    )

    args = parser.parse_args()

    if args.verify_only:
        result = verify_vector_store(
            persist_dir=args.persist_dir,
        )
    else:
        result = initialize_vector_store(
            data_dir=args.data_dir,
            persist_dir=args.persist_dir,
            embedding_model=args.embedding_model,
            reset=args.reset,
        )

        # Verify after initialization
        if result.get("status") == "success":
            verify_vector_store(persist_dir=args.persist_dir)

    # Exit with appropriate code
    if result.get("status") in ["success", "healthy"]:
        sys.exit(0)
    else:
        sys.exit(1)
