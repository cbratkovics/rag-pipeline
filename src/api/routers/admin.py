"""Admin API endpoints for system management."""

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

# Set protobuf environment before importing ChromaDB
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/admin/initialize", status_code=status.HTTP_200_OK)
async def initialize_vector_store(
    reset: bool = False,
    data_dir: str = "data/seed",
) -> dict[str, Any]:
    """Initialize vector store with seed documents.

    This endpoint loads documents from the data directory into ChromaDB.
    It's useful for:
    - Initial setup
    - Resetting the vector store
    - Adding new documents after deployment

    Args:
        reset: Whether to reset the collection before adding documents
        data_dir: Directory containing documents to load

    Returns:
        Status and document count
    """
    try:
        # Import the initialization function
        import sys
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.initialize_vector_store import initialize_vector_store as init_fn

        logger.info("Starting vector store initialization", reset=reset, data_dir=data_dir)

        result = init_fn(
            data_dir=data_dir,
            reset=reset,
        )

        if result.get("status") == "success":
            logger.info(
                "Vector store initialized successfully",
                count=result.get("count"),
                seed_docs=result.get("seed_docs"),
                file_docs=result.get("file_docs"),
            )
            return {
                "status": "success",
                "message": "Vector store initialized successfully",
                "count": result.get("count", 0),
                "seed_docs": result.get("seed_docs", 0),
                "file_docs": result.get("file_docs", 0),
            }
        else:
            logger.error("Vector store initialization failed", result=result)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Initialization failed"),
            )

    except Exception as e:
        logger.error("Vector store initialization error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Initialization failed: {str(e)}",
        )


@router.get("/admin/vector-store/status", status_code=status.HTTP_200_OK)
async def vector_store_status() -> dict[str, Any]:
    """Get vector store status and document count.

    Returns:
        Vector store status including document count and health
    """
    try:
        from src.rag.retriever import HybridRetriever

        retriever = HybridRetriever()
        count = retriever.collection.count()

        # Test search to ensure it's working
        if count > 0:
            try:
                test_results = retriever.vector_search("test", top_k=1)
                search_working = len(test_results) > 0
            except Exception as e:
                logger.warning("Vector search test failed", error=str(e))
                search_working = False
        else:
            search_working = False

        health_status = "healthy" if count > 0 and search_working else "empty"

        return {
            "status": health_status,
            "document_count": count,
            "search_working": search_working,
            "collection_name": retriever.collection.name,
            "persist_dir": retriever.persist_dir,
        }

    except Exception as e:
        logger.error("Failed to get vector store status", error=str(e))
        return {
            "status": "error",
            "document_count": 0,
            "search_working": False,
            "error": str(e),
        }


@router.post("/admin/vector-store/verify", status_code=status.HTTP_200_OK)
async def verify_vector_store() -> dict[str, Any]:
    """Verify vector store health by running test queries.

    Returns:
        Verification results including test query results
    """
    try:
        import sys
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.initialize_vector_store import verify_vector_store as verify_fn

        logger.info("Running vector store verification")

        result = verify_fn()

        return {
            "status": result.get("status"),
            "document_count": result.get("count", 0),
            "search_results": result.get("search_results", 0),
            "sample_scores": result.get("sample_scores", []),
            "message": "Verification complete",
        }

    except Exception as e:
        logger.error("Vector store verification error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}",
        )
