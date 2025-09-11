"""Experiments API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.experiments.ab_testing import ab_test_manager
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ExperimentStatsResponse(BaseModel):
    """Experiment statistics response."""

    experiment_id: str
    results: list[dict[str, Any]]
    winning_variant: str | None


@router.get("/experiments/{experiment_id}/stats", response_model=ExperimentStatsResponse)
async def get_experiment_stats(
    experiment_id: str,
    min_samples: int | None = None,
) -> ExperimentStatsResponse:
    """Get experiment statistics."""
    try:
        # Calculate statistics
        results = await ab_test_manager.calculate_statistics(experiment_id, min_samples)

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No results found for experiment {experiment_id}",
            )

        # Get winning variant
        winning_variant = await ab_test_manager.get_winning_variant(experiment_id)

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "variant": result.variant.value,
                    "sample_size": result.sample_size,
                    "success_rate": result.success_rate,
                    "avg_latency_ms": result.avg_latency_ms,
                    "avg_cost_usd": result.avg_cost_usd,
                    "avg_ragas_score": result.avg_ragas_score,
                    "confidence_interval": [
                        result.confidence_interval_lower,
                        result.confidence_interval_upper,
                    ],
                    "is_significant": result.is_significant,
                    "p_value": result.p_value,
                }
            )

        response = ExperimentStatsResponse(
            experiment_id=experiment_id,
            results=formatted_results,
            winning_variant=winning_variant.value if winning_variant else None,
        )

        logger.info(
            "Experiment stats retrieved",
            experiment_id=experiment_id,
            variants=len(results),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get experiment stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get experiment stats: {e!s}",
        ) from e


@router.get("/experiments", response_model=list[str])
async def list_experiments() -> list[str]:
    """List all active experiments."""
    try:
        experiment_ids = list(ab_test_manager.active_experiments.keys())
        return experiment_ids

    except Exception as e:
        logger.error("Failed to list experiments", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list experiments: {e!s}",
        ) from e
