"""Health check API endpoints."""

from typing import Dict

from fastapi import APIRouter, status

from src.infrastructure.cache import cache_manager
from src.infrastructure.database import db_manager
from src.infrastructure.logging import get_logger
from src.retrieval.vector_store import vector_store

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """Basic health check."""
    return {"status": "healthy", "service": "rag-pipeline"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, any]:
    """Readiness check for all components."""
    checks = {
        "database": False,
        "cache": False,
        "vector_store": False,
    }

    # Check database
    try:
        async with db_manager.get_session() as session:
            await session.execute("SELECT 1")
            checks["database"] = True
    except Exception as e:
        logger.warning("Database health check failed", error=str(e))

    # Check cache
    try:
        test_key = cache_manager.make_key("health_check")
        await cache_manager.set(test_key, "test", ttl=10)
        value = await cache_manager.get(test_key)
        if value == "test":
            checks["cache"] = True
            await cache_manager.delete(test_key)
    except Exception as e:
        logger.warning("Cache health check failed", error=str(e))

    # Check vector store
    try:
        count = await vector_store.count_documents()
        checks["vector_store"] = True
        checks["vector_store_count"] = count
    except Exception as e:
        logger.warning("Vector store health check failed", error=str(e))

    # Determine overall status
    all_healthy = all(v for k, v in checks.items() if k != "vector_store_count")

    if not all_healthy:
        return {
            "status": "degraded",
            "checks": checks,
        }

    return {
        "status": "ready",
        "checks": checks,
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """Liveness check for Kubernetes."""
    return {"status": "alive"}