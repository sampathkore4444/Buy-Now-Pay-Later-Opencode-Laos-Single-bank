from sqlalchemy import (
    Column, BigInteger, Integer, String, DateTime, Date, Numeric, ForeignKey,
    Boolean, Enum as SqlEnum, func, Text
)
from sqlalchemy.orm import relationship
from models.base import BaseModel
from common.enums import AuthStatus


class Consumer(BaseModel):
    __tablename__ = "consumers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consumer_id = Column(String(32), unique=True, nullable=False, index=True)
    bank_customer_id = Column(String(32), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(128), nullable=True)
    id_card = Column(String(32), nullable=True)
    date_of_birth = Column(Date, nullable=True)

    bnpl_limit_lak = Column(Numeric(19, 4), nullable=False, default=0)
    available_limit_lak = Column(Numeric(19, 4), nullable=False, default=0)
    limit_expiry = Column(Date, nullable=True)
    risk_tier = Column(String(16), nullable=False, default="GREEN")
    risk_score = Column(Integer, nullable=True)

    kyc_status = Column(String(16), nullable=False, default="VERIFIED")
    aml_status = Column(String(16), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    auth_requests = relationship("AuthRequest", back_populates="consumer")
    transactions = relationship("Transaction", back_populates="consumer")


class ConsumerDevice(BaseModel):
    __tablename__ = "consumer_devices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consumer_id = Column(String(32), ForeignKey("consumers.consumer_id"), nullable=False)
    device_fingerprint = Column(String(128), nullable=False)
    device_type = Column(String(32), nullable=True)
    last_ip_address = Column(String(45), nullable=True)
    last_gps_location = Column(String(32), nullable=True)
    trusted = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
