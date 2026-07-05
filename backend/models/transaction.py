from sqlalchemy import (
    Column, BigInteger, String, DateTime, Numeric, ForeignKey,
    Enum as SqlEnum, func, Text
)
from sqlalchemy.orm import relationship
from models.base import BaseModel
from common.enums import AuthStatus, TxnType, TxnCategory


class AuthRequest(BaseModel):
    __tablename__ = "auth_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    auth_id = Column(String(64), unique=True, nullable=False, index=True)
    auth_code = Column(String(32), unique=True, nullable=True)
    consumer_id = Column(String(32), ForeignKey("consumers.consumer_id"), nullable=False, index=True)
    merchant_id = Column(String(32), ForeignKey("merchants.merchant_id"), nullable=False, index=True)
    amount_lak = Column(Numeric(19, 4), nullable=False)
    currency = Column(String(3), nullable=False, default="LAK")
    txn_type = Column(String(16), nullable=False, default="PURCHASE")
    channel = Column(String(16), nullable=False)
    device_fingerprint = Column(String(128), nullable=True)
    gps_location = Column(String(32), nullable=True)

    status = Column(SqlEnum(AuthStatus), nullable=False, default=AuthStatus.INITIATED)
    approved_amount_lak = Column(Numeric(19, 4), nullable=True)
    remaining_limit_lak = Column(Numeric(19, 4), nullable=True)
    settlement_date = Column(DateTime(timezone=True), nullable=True)
    repayment_date = Column(DateTime(timezone=True), nullable=True)
    mdr_rate = Column(Numeric(5, 4), nullable=True)
    merchant_settlement_lak = Column(Numeric(19, 4), nullable=True)

    initiated_at = Column(DateTime(timezone=True), nullable=True)
    pending_at = Column(DateTime(timezone=True), nullable=True)
    reason_code = Column(String(32), nullable=True)
    decline_reason = Column(Text, nullable=True)

    auth_timestamp = Column(DateTime(timezone=True), nullable=True)
    confirm_timestamp = Column(DateTime(timezone=True), nullable=True)
    timeout_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    consumer = relationship("Consumer", back_populates="auth_requests")
    merchant = relationship("Merchant")
    transactions = relationship("Transaction", back_populates="auth_request")


class Transaction(BaseModel):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    txn_id = Column(String(64), unique=True, nullable=False, index=True)
    correlation_id = Column(String(64), unique=True, nullable=True)
    auth_id = Column(String(64), ForeignKey("auth_requests.auth_id"), nullable=True, index=True)
    consumer_id = Column(String(32), ForeignKey("consumers.consumer_id"), nullable=False, index=True)
    merchant_id = Column(String(32), ForeignKey("merchants.merchant_id"), nullable=False, index=True)
    txn_type = Column(SqlEnum(TxnType), nullable=False)
    txn_category = Column(SqlEnum(TxnCategory), nullable=False)
    amount_lak = Column(Numeric(19, 4), nullable=False)
    currency = Column(String(3), nullable=False, default="LAK")
    mdr_rate = Column(Numeric(5, 4), nullable=True)
    mdr_amount = Column(Numeric(19, 4), nullable=True)
    net_settlement_amount = Column(Numeric(19, 4), nullable=True)
    status = Column(String(16), nullable=False, default="PENDING")
    staging_status = Column(String(16), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    merchant = relationship("Merchant", back_populates="transactions")
    consumer = relationship("Consumer", back_populates="transactions")
    auth_request = relationship("AuthRequest", back_populates="transactions")
