from pydantic import BaseModel, Field
from typing import Any, Generic, TypeVar
from datetime import datetime


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel):
    data: list[dict[str, Any]]
    pagination: PaginationInfo


DataT = TypeVar("DataT")


class ErrorResponse(BaseModel):
    detail: str | dict[str, Any]


class MessageResponse(BaseModel):
    message: str
    status: str = "success"


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
