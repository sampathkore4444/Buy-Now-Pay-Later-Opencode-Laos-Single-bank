from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field


class ConsumerLimitResponse(BaseModel):
    consumer_id: str
    bnpl_limit_lak: Decimal
    available_limit_lak: Decimal
    currency: str = "LAK"
    limit_expiry: date | None
    risk_tier: str


class ConsumerSignupResponse(BaseModel):
    consumer_id: str
    bnpl_limit_lak: Decimal
    message: str = "BNPL enrollment successful"
