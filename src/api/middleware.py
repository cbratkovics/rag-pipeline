"""API middleware for request processing."""

import time
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import get_settings
from src.infrastructure.cache import cache_manager
from src.infrastructure.logging import get_logger, set_correlation_id

logger = get_logger(__name__)
settings = get_settings()


async def add_correlation_id(request: Request, call_next: Callable) -> Response:
    """Add correlation ID to requests."""
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        import uuid

        correlation_id = str(uuid.uuid4())

    set_correlation_id(correlation_id)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


async def add_process_time(request: Request, call_next: Callable) -> Response:
    """Add request processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-MS"] = str(process_time)
    return response


async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """Rate limiting middleware."""
    if not settings.rate_limit_enabled:
        return await call_next(request)

    # Get client identifier (IP or API key)
    client_id = request.headers.get(settings.api_key_header)
    if not client_id:
        client_id = request.client.host if request.client else "unknown"

    # Check rate limits
    minute_key = cache_manager.make_key("rate_limit", "minute", client_id)
    hour_key = cache_manager.make_key("rate_limit", "hour", client_id)
    day_key = cache_manager.make_key("rate_limit", "day", client_id)

    # Increment counters
    minute_count = await cache_manager.increment(minute_key) or 0
    hour_count = await cache_manager.increment(hour_key) or 0
    day_count = await cache_manager.increment(day_key) or 0

    # Set TTLs if first request
    if minute_count == 1:
        await cache_manager.set(minute_key, 1, ttl=60)
    if hour_count == 1:
        await cache_manager.set(hour_key, 1, ttl=3600)
    if day_count == 1:
        await cache_manager.set(day_key, 1, ttl=86400)

    # Check limits
    if minute_count > settings.rate_limit_requests_per_minute:
        logger.warning("Rate limit exceeded (minute)", client_id=client_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

    if hour_count > settings.rate_limit_requests_per_hour:
        logger.warning("Rate limit exceeded (hour)", client_id=client_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Hourly rate limit exceeded. Please try again later.",
        )

    if day_count > settings.rate_limit_requests_per_day:
        logger.warning("Rate limit exceeded (day)", client_id=client_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily rate limit exceeded. Please try again tomorrow.",
        )

    response = await call_next(request)

    # Add rate limit headers
    response.headers["X-RateLimit-Limit-Minute"] = str(
        settings.rate_limit_requests_per_minute
    )
    response.headers["X-RateLimit-Remaining-Minute"] = str(
        settings.rate_limit_requests_per_minute - minute_count
    )
    response.headers["X-RateLimit-Limit-Hour"] = str(settings.rate_limit_requests_per_hour)
    response.headers["X-RateLimit-Remaining-Hour"] = str(
        settings.rate_limit_requests_per_hour - hour_count
    )

    return response