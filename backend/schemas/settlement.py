from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class SettlementResponse(BaseModel):
    settlement_id: str
    merchant_id: str
    batch_id: str
    settlement_date: date
    total_txn_count: int
    total_gross_amount: Decimal
    total_mdr_amount: Decimal
    total_net_amount: Decimal
    status: str
    staged_at: datetime | None = None
    posted_at: datetime | None = None
    created_at: datetime | None = None


class SettlementListResponse(BaseModel):
    data: list[SettlementResponse]
    pagination: dict
