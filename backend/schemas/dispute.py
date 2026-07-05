from pydantic import BaseModel, Field
from datetime import datetime


class DisputeInitiateRequest(BaseModel):
    consumer_id: str = Field(..., max_length=32)
    auth_id: str = Field(..., max_length=64)
    reason: str = Field(..., max_length=32)
    description: str | None = Field(None, max_length=1000)


class DisputeInitiateResponse(BaseModel):
    dispute_id: str
    status: str
    message: str


class CoolingOffCheckResponse(BaseModel):
    eligible: bool
    cooling_off_expiry: str | None = None
    days_remaining: int | None = None
    amount_lak: float | None = None
    reason: str | None = None


class CoolingOffCancelResponse(BaseModel):
    auth_id: str
    status: str
    message: str


class DisputeResolveRequest(BaseModel):
    resolution: str = Field(..., max_length=32)
    notes: str | None = Field(None, max_length=2000)


class DisputeResponse(BaseModel):
    dispute_id: str
    auth_id: str
    reason: str
    status: str
    resolution: str | None = None
    created_at: str
