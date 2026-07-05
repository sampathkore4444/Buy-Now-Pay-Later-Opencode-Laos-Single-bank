from sqlalchemy import (
    Column, BigInteger, Integer, String, DateTime, Date, Numeric, ForeignKey,
    Boolean, Text, Enum as SqlEnum, func
)
from sqlalchemy.orm import relationship
from models.base import BaseModel
from common.enums import (
    MerchantStatus, RiskTier, ChannelType, BusinessType,
)


class Merchant(BaseModel):
    __tablename__ = "merchants"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    merchant_id = Column(String(32), unique=True, nullable=False, index=True)
    application_id = Column(String(32), unique=True, nullable=False)
    business_name = Column(String(256), nullable=False)
    business_name_lao = Column(String(256), nullable=True)
    registration_number = Column(String(64), nullable=True)
    tax_id = Column(String(64), nullable=True)
    business_type = Column(SqlEnum(BusinessType), nullable=False)
    merchant_category = Column(String(64), nullable=False)
    mcc_code = Column(String(8), nullable=True)

    owner_name = Column(String(128), nullable=False)
    owner_id_card = Column(String(32), nullable=False)
    owner_phone = Column(String(20), nullable=False)
    owner_email = Column(String(128), nullable=False)

    settlement_bank_code = Column(String(16), nullable=False)
    settlement_account_no = Column(String(34), nullable=False)
    settlement_account_name = Column(String(128), nullable=False)

    address_street = Column(String(256), nullable=True)
    address_district = Column(String(64), nullable=True)
    address_province = Column(String(64), nullable=True)
    address_gps = Column(String(32), nullable=True)

    channels = Column(String(256), nullable=True)
    estimated_monthly_volume_lak = Column(Numeric(19, 4), nullable=True)
    average_ticket_size_lak = Column(Numeric(19, 4), nullable=True)
    referral_source = Column(String(64), nullable=True)

    status = Column(SqlEnum(MerchantStatus), nullable=False, default=MerchantStatus.PENDING_KYC)
    risk_tier = Column(SqlEnum(RiskTier), nullable=False, default=RiskTier.GREEN)
    risk_score = Column(Integer, nullable=True, default=100)
    mdr_rate = Column(Numeric(5, 4), nullable=False)
    settlement_terms = Column(String(8), nullable=False, default="T+1")
    daily_limit_lak = Column(Numeric(19, 4), nullable=True)
    monthly_limit_lak = Column(Numeric(19, 4), nullable=True)

    api_key = Column(String(128), unique=True, nullable=True)
    api_secret_hash = Column(String(256), nullable=True)
    webhook_url = Column(String(512), nullable=True)
    qr_code_url = Column(String(512), nullable=True)

    kyc_status = Column(String(16), nullable=True)
    aml_check = Column(String(16), nullable=True)
    sanctions_screen = Column(String(16), nullable=True)
    next_review_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(32), nullable=False, default="SYSTEM")

    transactions = relationship("Transaction", back_populates="merchant")


class MerchantDocument(BaseModel):
    __tablename__ = "merchant_documents"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    merchant_id = Column(String(32), ForeignKey("merchants.merchant_id"), nullable=False)
    document_type = Column(String(32), nullable=False)
    document_url = Column(String(512), nullable=False)
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MerchantUser(BaseModel):
    __tablename__ = "merchant_users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    merchant_id = Column(String(32), ForeignKey("merchants.merchant_id"), nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    name = Column(String(128), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(String(16), nullable=False, default="ADMIN")
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)



