from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class AuthRequestSchema(BaseModel):
    auth_id: str = Field(..., max_length=64)
    consumer_id: str = Field(..., max_length=32)
    merchant_id: str = Field(..., max_length=32)
    amount_lak: Decimal = Field(..., gt=0)
    currency: str = Field(default="LAK", max_length=3)
    txn_type: str = Field(default="PURCHASE", max_length=16)
    channel: str = Field(..., max_length=16)
    device_fingerprint: str | None = Field(None, max_length=128)
    gps_location: str | None = Field(None, max_length=32)


class AuthApprovedResponse(BaseModel):
    auth_id: str
    status: str = "AUTHED"
    auth_code: str
    approved_amount_lak: Decimal
    remaining_limit_lak: Decimal
    settlement_date: datetime
    repayment_date: datetime
    mdr_rate: Decimal
    merchant_settlement_lak: Decimal
    timestamp: datetime


class AuthDeclinedResponse(BaseModel):
    auth_id: str
    status: str = "DECLINED"
    reason_code: str
    message: str


class AuthConfirmRequest(BaseModel):
    auth_id: str = Field(..., max_length=64)


class AuthStatusResponse(BaseModel):
    auth_id: str
    status: str
    auth_code: str | None = None
    timeout_at: datetime | None = None
