"""Feedback API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.core.models import FeedbackType, UserFeedback
from src.infrastructure.cache import cache_manager
from src.infrastructure.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()


class FeedbackRequest(BaseModel):
    """Feedback request model."""

    result_id: str = Field(..., description="ID of the query result")
    feedback_type: str = Field(..., description="Type of feedback")
    value: Any = Field(..., description="Feedback value")
    comment: str | None = Field(default=None, description="Optional comment")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class FeedbackResponse(BaseModel):
    """Feedback response model."""

    feedback_id: str
    message: str = "Feedback recorded successfully"


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest, req: Request) -> FeedbackResponse:
    """Submit user feedback for a query result."""
    try:
        # Get user ID from headers
        user_id = req.headers.get("X-User-ID")

        # Create feedback model
        feedback = UserFeedback(
            result_id=UUID(request.result_id),
            user_id=user_id,
            feedback_type=FeedbackType(request.feedback_type),
            value=request.value,
            comment=request.comment,
            metadata=request.metadata or {},
        )

        # Store feedback in cache (in production, this would go to database)
        feedback_key = cache_manager.make_key("feedback", str(feedback.id))
        await cache_manager.set(
            feedback_key,
            {
                "id": str(feedback.id),
                "result_id": str(feedback.result_id),
                "user_id": feedback.user_id,
                "feedback_type": feedback.feedback_type.value,
                "value": feedback.value,
                "comment": feedback.comment,
                "metadata": feedback.metadata,
                "created_at": feedback.created_at.isoformat(),
            },
            ttl=86400 * 30,  # Keep for 30 days
        )

        # Update feedback statistics
        stats_key = cache_manager.make_key("feedback_stats", request.feedback_type)
        await cache_manager.increment(stats_key)

        # Check if retraining threshold is reached
        if feedback.feedback_type == FeedbackType.RATING and feedback.value <= 2:
            negative_key = cache_manager.make_key("feedback_negative_count")
            negative_count = await cache_manager.increment(negative_key) or 0

            if negative_count >= settings.feedback_retraining_threshold:
                logger.info(
                    "Retraining threshold reached",
                    negative_count=negative_count,
                    threshold=settings.feedback_retraining_threshold,
                )
                # Trigger retraining (placeholder)
                # await trigger_retraining()

        logger.info(
            "Feedback recorded",
            feedback_id=str(feedback.id),
            result_id=request.result_id,
            feedback_type=request.feedback_type,
        )

        return FeedbackResponse(feedback_id=str(feedback.id))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feedback data: {e!s}",
        ) from e
    except Exception as e:
        logger.error("Failed to record feedback", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {e!s}",
        ) from e


@router.get("/feedback/stats")
async def get_feedback_stats() -> dict[str, Any]:
    """Get feedback statistics."""
    try:
        # Get feedback counts by type
        stats = {}
        for feedback_type in FeedbackType:
            stats_key = cache_manager.make_key("feedback_stats", feedback_type.value)
            count = await cache_manager.get(stats_key, default=0)
            stats[feedback_type.value] = count

        # Get negative feedback count
        negative_key = cache_manager.make_key("feedback_negative_count")
        negative_count = await cache_manager.get(negative_key, default=0)

        return {
            "feedback_by_type": stats,
            "negative_count": negative_count,
            "retraining_threshold": settings.feedback_retraining_threshold,
            "retraining_needed": negative_count >= settings.feedback_retraining_threshold,
        }

    except Exception as e:
        logger.error("Failed to get feedback stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback stats: {e!s}",
        ) from e
