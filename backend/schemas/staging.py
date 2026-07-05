from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class StagingTransactionRequest(BaseModel):
    batch_id: str = Field(..., max_length=64)
    source_ref_no: str = Field(..., max_length=128)
    source_timestamp: datetime
    txn_type: str = Field(..., max_length=16)
    txn_category: str = Field(..., max_length=32)
    txn_code: str | None = Field(None, max_length=16)
    txn_currency: str = Field(default="LAK", max_length=3)
    txn_amount: Decimal = Field(..., ge=0)
    debit_account_no: str | None = Field(None, max_length=34)
    credit_account_no: str | None = Field(None, max_length=34)
    narrative: str | None = Field(None, max_length=256)

    bnpl_extensions: dict | None = None
    details: list[dict] = Field(default_factory=list)


class StagingTransactionResponse(BaseModel):
    correlation_id: str
    stg_header_id: int
    status: str
    staging_timestamp: datetime
    estimated_eod_window: datetime


class StagingStatusResponse(BaseModel):
    correlation_id: str
    status: str
    retry_count: int
    eod_batch_run_id: str | None
    eod_posting_timestamp: datetime | None
    eod_failure_reason: str | None
