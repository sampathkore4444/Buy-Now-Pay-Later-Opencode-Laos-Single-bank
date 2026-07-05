from sqlalchemy import (
    Column, BigInteger, String, DateTime, Date, Numeric, ForeignKey,
    Enum as SqlEnum, func, Text
)
from models.base import BaseModel
from common.enums import AuthStatus


class OverdueTracker(BaseModel):
    __tablename__ = "overdue_tracker"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consumer_id = Column(String(32), ForeignKey("consumers.consumer_id"), nullable=False, index=True)
    auth_id = Column(String(64), ForeignKey("auth_requests.auth_id"), nullable=True)
    overdue_date = Column(Date, nullable=False)
    days_overdue = Column(BigInteger, nullable=False, default=0)
    overdue_amount_lak = Column(Numeric(19, 4), nullable=False, default=0)

    late_fee_charged = Column(Numeric(19, 4), nullable=False, default=0)
    interest_charged = Column(Numeric(19, 4), nullable=False, default=0)
    late_fee_count = Column(BigInteger, nullable=False, default=0)
    last_fee_assessment = Column(Date, nullable=True)
    last_interest_assessment = Column(Date, nullable=True)

    status = Column(String(16), nullable=False, default="ACTIVE")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
