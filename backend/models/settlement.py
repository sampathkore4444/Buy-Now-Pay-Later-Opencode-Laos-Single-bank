from sqlalchemy import Column, BigInteger, Integer, Boolean, String, DateTime, Numeric, Enum as SqlEnum, func, Date, Text
from models.base import BaseModel


class Settlement(BaseModel):
    __tablename__ = "settlements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    settlement_id = Column(String(64), unique=True, nullable=False, index=True)
    merchant_id = Column(String(32), nullable=False, index=True)
    batch_id = Column(String(64), nullable=False)
    settlement_date = Column(Date, nullable=False)
    total_txn_count = Column(Integer, nullable=False, default=0)
    total_gross_amount = Column(Numeric(19, 4), nullable=False, default=0)
    total_mdr_amount = Column(Numeric(19, 4), nullable=False, default=0)
    total_net_amount = Column(Numeric(19, 4), nullable=False, default=0)
    status = Column(String(16), nullable=False, default="PENDING")
    staged_at = Column(DateTime(timezone=True), nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class NotificationLog(BaseModel):
    __tablename__ = "notification_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    notification_id = Column(String(64), unique=True, nullable=False)
    recipient = Column(String(128), nullable=False)
    channel = Column(String(16), nullable=False)
    template = Column(String(64), nullable=False)
    message = Column(String(2000), nullable=False)
    status = Column(String(16), nullable=False, default="SENT")
    reference_type = Column(String(32), nullable=True)
    reference_id = Column(String(64), nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WebhookLog(BaseModel):
    __tablename__ = "webhook_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    merchant_id = Column(String(32), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    payload = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="RECEIVED")
    response_code = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FraudRule(BaseModel):
    __tablename__ = "fraud_rules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    rule_name = Column(String(64), unique=True, nullable=False)
    rule_type = Column(String(32), nullable=False)
    parameter = Column(String(128), nullable=False)
    threshold = Column(String(64), nullable=False)
    action = Column(String(16), nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CreditLimitRefreshLog(BaseModel):
    __tablename__ = "credit_limit_refresh_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    batch_id = Column(String(64), nullable=False)
    total_consumers = Column(Integer, nullable=False, default=0)
    limits_updated = Column(Integer, nullable=False, default=0)
    status = Column(String(16), nullable=False, default="RUNNING")
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
