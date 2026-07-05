import functools
import inspect
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    return str(uuid.uuid4())


def generate_correlation_id() -> str:
    return str(uuid.uuid4())


def generate_batch_id() -> str:
    now = datetime.now(timezone.utc)
    return f"BNPL_{now.strftime('%Y%m%d_%H')}"


def generate_auth_code() -> str:
    return f"AUTH-{uuid.uuid4().hex[:8].upper()}"


def generate_merchant_id() -> str:
    from datetime import datetime
    suffix = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"M-{suffix}"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def pagination_params(page: int = 1, page_size: int = 20) -> tuple[int, int]:
    from common.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    return page, page_size


def build_pagination_response(
    items: list[dict[str, Any]],
    total: int,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    from schemas.common import PaginationInfo
    pagination = PaginationInfo(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=(total + page_size - 1) // page_size,
    )
    return {
        "data": items,
        "pagination": pagination.model_dump(),
    }


def safe_endpoint(func):
    """Decorator that wraps route handlers with try-catch + logging.

    Catches unhandled exceptions, logs them with the function name,
    then re-raises so FastAPI's global exception handler can format the response.
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception:
                logger.exception("Unhandled error in %s", func.__qualname__)
                raise
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception:
                logger.exception("Unhandled error in %s", func.__qualname__)
                raise
        return sync_wrapper
