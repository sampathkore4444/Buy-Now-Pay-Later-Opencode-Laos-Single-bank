from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    data: list[dict[str, Any]]
    pagination: dict[str, Any]


class ErrorResponse(BaseModel):
    detail: str | dict[str, Any]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
