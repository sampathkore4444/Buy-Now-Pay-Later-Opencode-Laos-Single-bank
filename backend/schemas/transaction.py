from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class BnplExtensionSchema(BaseModel):
    bnpl_txn_category: str = Field(..., max_length=32)
    bnpl_merchant_id: str | None = Field(None, max_length=32)
    bnpl_consumer_id: str | None = Field(None, max_length=32)
    bnpl_auth_id: str | None = Field(None, max_length=64)
    mdr_rate: Decimal | None = Field(None, ge=0)
    mdr_amount: Decimal | None = Field(None, ge=0)
    net_settlement_amount: Decimal | None = Field(None, ge=0)


class DetailLineSchema(BaseModel):
    line_no: int = Field(..., ge=1)
    detail_type: str = Field(..., max_length=16)
    detail_amount: Decimal = Field(..., ge=0)
    detail_currency: str = Field(default="LAK", max_length=3)
    gl_account_code: str | None = Field(None, max_length=16)
    narrative_line1: str | None = Field(None, max_length=140)


class StagingWriteRequest(BaseModel):
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
    bnpl_extensions: BnplExtensionSchema | None = None
    details: list[DetailLineSchema] = Field(default_factory=list)


class StagingWriteResponse(BaseModel):
    correlation_id: str
    stg_header_id: int
    status: str = "PENDING"
    staging_timestamp: datetime
    estimated_eod_window: datetime


class TransactionResponse(BaseModel):
    txn_id: str
    correlation_id: str | None = None
    auth_id: str | None = None
    consumer_id: str
    merchant_id: str
    txn_type: str
    txn_category: str
    amount_lak: Decimal
    currency: str = "LAK"
    mdr_rate: Decimal | None = None
    mdr_amount: Decimal | None = None
    net_settlement_amount: Decimal | None = None
    status: str
    staging_status: str | None = None
    created_at: datetime | None = None
