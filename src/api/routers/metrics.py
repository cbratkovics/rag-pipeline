"""Metrics API endpoints."""

import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, status

from src.core.models import SystemMetrics
from src.experiments.ab_testing import ab_test_manager
from src.infrastructure.cache import cache_manager
from src.infrastructure.logging import get_logger
from src.retrieval.vector_store import vector_store

logger = get_logger(__name__)
router = APIRouter()


@router.get("/metrics/system")
async def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics."""
    try:
        # Get query statistics from cache
        query_stats_key = cache_manager.make_key("query_stats", "24h")
        query_stats = await cache_manager.get(query_stats_key, default={})

        # Get vector store size
        try:
            vector_count = await vector_store.count_documents()
        except:
            vector_count = 0

        # Get system resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage_mb = (memory.total - memory.available) / (1024 * 1024)

        # Calculate metrics
        metrics = SystemMetrics(
            queries_per_second=query_stats.get("qps", 0.0),
            avg_latency_ms=query_stats.get("avg_latency", 0.0),
            p50_latency_ms=query_stats.get("p50_latency", 0.0),
            p95_latency_ms=query_stats.get("p95_latency", 0.0),
            p99_latency_ms=query_stats.get("p99_latency", 0.0),
            error_rate=query_stats.get("error_rate", 0.0),
            cache_hit_rate=query_stats.get("cache_hit_rate", 0.0),
            vector_store_size=vector_count,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_percent,
            active_experiments=len(ab_test_manager.active_experiments),
            total_queries_24h=query_stats.get("total_queries", 0),
            total_cost_24h_usd=query_stats.get("total_cost", 0.0),
        )

        return {
            "timestamp": metrics.timestamp.isoformat(),
            "performance": {
                "queries_per_second": metrics.queries_per_second,
                "avg_latency_ms": metrics.avg_latency_ms,
                "p50_latency_ms": metrics.p50_latency_ms,
                "p95_latency_ms": metrics.p95_latency_ms,
                "p99_latency_ms": metrics.p99_latency_ms,
                "error_rate": metrics.error_rate,
            },
            "resources": {
                "cpu_usage_percent": metrics.cpu_usage_percent,
                "memory_usage_mb": metrics.memory_usage_mb,
                "vector_store_size": metrics.vector_store_size,
                "cache_hit_rate": metrics.cache_hit_rate,
            },
            "business": {
                "active_experiments": metrics.active_experiments,
                "total_queries_24h": metrics.total_queries_24h,
                "total_cost_24h_usd": metrics.total_cost_24h_usd,
            },
        }

    except Exception as e:
        logger.error("Failed to get system metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}",
        )


@router.get("/metrics/queries")
async def get_query_metrics(hours: int = 24) -> Dict[str, Any]:
    """Get query metrics for the specified time period."""
    try:
        # Get query results from cache
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        pattern = cache_manager.make_key("experiment_results", "*")
        all_results = await cache_manager.get_pattern(pattern)

        # Filter by time range
        filtered_results = []
        for key, data in all_results.items():
            result_time = datetime.fromisoformat(data["timestamp"])
            if start_time <= result_time <= end_time:
                filtered_results.append(data)

        if not filtered_results:
            return {
                "period_hours": hours,
                "total_queries": 0,
                "metrics": {},
            }

        # Calculate aggregated metrics
        total_queries = len(filtered_results)
        successful_queries = sum(1 for r in filtered_results if r["success"])
        total_cost = sum(r["cost_usd"] for r in filtered_results)
        latencies = [r["latency_ms"] for r in filtered_results]
        ragas_scores = [r.get("ragas_score", 0.0) for r in filtered_results if "ragas_score" in r]

        # Calculate percentiles
        import numpy as np

        latencies_sorted = np.sort(latencies)
        p50 = np.percentile(latencies_sorted, 50) if latencies else 0
        p95 = np.percentile(latencies_sorted, 95) if latencies else 0
        p99 = np.percentile(latencies_sorted, 99) if latencies else 0

        return {
            "period_hours": hours,
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "success_rate": successful_queries / total_queries if total_queries > 0 else 0,
            "total_cost_usd": total_cost,
            "avg_cost_per_query": total_cost / total_queries if total_queries > 0 else 0,
            "latency": {
                "avg_ms": np.mean(latencies) if latencies else 0,
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
                "min_ms": min(latencies) if latencies else 0,
                "max_ms": max(latencies) if latencies else 0,
            },
            "ragas": {
                "avg_score": np.mean(ragas_scores) if ragas_scores else 0,
                "min_score": min(ragas_scores) if ragas_scores else 0,
                "max_score": max(ragas_scores) if ragas_scores else 0,
                "evaluated_count": len(ragas_scores),
            },
        }

    except Exception as e:
        logger.error("Failed to get query metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get query metrics: {str(e)}",
        )