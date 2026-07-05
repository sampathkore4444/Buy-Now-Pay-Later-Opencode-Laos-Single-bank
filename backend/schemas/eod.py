from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class EODBatchStatusResponse(BaseModel):
    batch_id: str
    control_status: str
    eod_batch_run_id: str | None = None
    eod_start_timestamp: datetime | None = None
    eod_end_timestamp: datetime | None = None
    expected_record_count: int = 0
    actual_record_count: int = 0
    expected_total_amount: Decimal = 0
    actual_total_amount: Decimal = 0
    control_status_timestamp: datetime | None = None


class EODRunResponse(BaseModel):
    status: str
    eod_batch_run_id: str
    batches_found: int = 0
    batches_processed: list[dict] = []
    timestamp: str | None = None
    reason: str | None = None


class EODListResponse(BaseModel):
    data: list[EODBatchStatusResponse]
    pagination: dict
