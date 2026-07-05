from sqlalchemy import (
    Column, BigInteger, Integer, String, DateTime, Numeric, Enum as SqlEnum, func, Text
)
from models.base import BaseModel
from common.enums import StagingStatus, DetailType


class StagingHeader(BaseModel):
    __tablename__ = "staging_headers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stg_header_id = Column(BigInteger, nullable=True)
    correlation_id = Column(String(64), unique=True, nullable=False)
    batch_id = Column(String(64), nullable=False, index=True)
    source_system = Column(String(32), nullable=False, default="BNPL_PLATFORM")
    source_ref_no = Column(String(128), nullable=False)
    source_timestamp = Column(DateTime(timezone=True), nullable=False)

    txn_type = Column(String(16), nullable=False)
    txn_category = Column(String(32), nullable=False)
    txn_code = Column(String(16), nullable=True)
    txn_currency = Column(String(3), nullable=False, default="LAK")
    txn_amount = Column(Numeric(19, 4), nullable=False)

    debit_account_no = Column(String(34), nullable=True)
    credit_account_no = Column(String(34), nullable=True)
    debit_account_branch = Column(String(8), nullable=True)
    credit_account_branch = Column(String(8), nullable=True)

    bnpl_txn_category = Column(String(32), nullable=True)
    bnpl_merchant_id = Column(String(32), nullable=True)
    bnpl_consumer_id = Column(String(32), nullable=True)
    bnpl_auth_id = Column(String(64), nullable=True)
    mdr_rate = Column(Numeric(5, 4), nullable=True)
    mdr_amount = Column(Numeric(19, 4), nullable=True)
    net_settlement_amount = Column(Numeric(19, 4), nullable=True)

    stg_status = Column(String(16), nullable=False, default="PENDING")
    eod_batch_run_id = Column(String(64), nullable=True)
    eod_pickup_timestamp = Column(DateTime(timezone=True), nullable=True)
    eod_posting_timestamp = Column(DateTime(timezone=True), nullable=True)
    eod_failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    hold_reason = Column(String(128), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
