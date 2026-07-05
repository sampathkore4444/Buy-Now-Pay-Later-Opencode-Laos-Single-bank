from decimal import Decimal
from pydantic import BaseModel, Field


class ReconcileBatchRequest(BaseModel):
    batch_id: str = Field(..., max_length=64)
    expected_count: int = Field(..., ge=0)
    expected_amount: Decimal = Field(..., ge=0)


class ReconcileBatchResponse(BaseModel):
    batch_id: str
    expected_count: int
    actual_count: int
    count_difference: int
    expected_amount: Decimal
    actual_amount: Decimal
    amount_difference: Decimal
    status: str


class DailyReconcileReportResponse(BaseModel):
    report_date: str
    staged_count: int = 0
    posted_count: int = 0
    failed_count: int = 0
    pending_count: int = 0
