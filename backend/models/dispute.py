from sqlalchemy import (
    Column, BigInteger, String, DateTime, Date, Numeric, Text, Boolean, ForeignKey, func
)
from models.base import BaseModel


class Dispute(BaseModel):
    __tablename__ = "disputes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dispute_id = Column(String(64), unique=True, nullable=False, index=True)
    consumer_id = Column(String(32), ForeignKey("consumers.consumer_id"), nullable=False, index=True)
    auth_id = Column(String(64), ForeignKey("auth_requests.auth_id"), nullable=False)
    txn_id = Column(String(64), ForeignKey("transactions.txn_id"), nullable=True)

    reason = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    amount_lak = Column(Numeric(19, 4), nullable=False)

    status = Column(String(16), nullable=False, default="OPEN")
    assigned_to = Column(String(64), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    resolution = Column(String(32), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    cooling_off_expiry = Column(DateTime(timezone=True), nullable=True)
    is_cooling_off = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
