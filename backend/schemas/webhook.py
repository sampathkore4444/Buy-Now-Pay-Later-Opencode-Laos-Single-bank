from datetime import datetime
from pydantic import BaseModel, Field


class WebhookLogResponse(BaseModel):
    id: int
    merchant_id: str
    event_type: str
    payload: dict = {}
    status: str
    response_code: int | None = None
    created_at: datetime | None = None


class WebhookLogListResponse(BaseModel):
    data: list[WebhookLogResponse]
    pagination: dict
