from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr
from common.enums import MerchantStatus, RiskTier, ChannelType, BusinessType


class MerchantOwnerSchema(BaseModel):
    name: str = Field(..., max_length=128)
    id_card: str = Field(..., max_length=32)
    phone: str = Field(..., max_length=20)
    email: EmailStr = Field(...)


class SettlementAccountSchema(BaseModel):
    bank_code: str = Field(..., max_length=16)
    account_number: str = Field(..., max_length=34)
    account_name: str = Field(..., max_length=128)


class AddressSchema(BaseModel):
    street: str | None = Field(None, max_length=256)
    district: str | None = Field(None, max_length=64)
    province: str | None = Field(None, max_length=64)
    gps_coordinates: str | None = Field(None, max_length=32)


class MerchantOnboardRequest(BaseModel):
    application_id: str = Field(..., max_length=32)
    business_name: str = Field(..., max_length=256)
    business_name_lao: str | None = Field(None, max_length=256)
    registration_number: str | None = Field(None, max_length=64)
    tax_id: str | None = Field(None, max_length=64)
    business_type: BusinessType
    merchant_category: str = Field(..., max_length=64)
    owner: MerchantOwnerSchema
    settlement_account: SettlementAccountSchema
    business_address: AddressSchema
    channels: list[ChannelType]
    estimated_monthly_volume_lak: Decimal = Field(..., ge=0)
    average_ticket_size_lak: Decimal | None = Field(None, ge=0)
    referral_source: str | None = Field(None, max_length=64)


class IntegrationInfo(BaseModel):
    api_key: str
    api_secret: str
    webhook_url: str
    qr_code_url: str
    sandbox_url: str


class ComplianceInfo(BaseModel):
    kyc_status: str
    aml_check: str
    sanctions_screen: str
    next_review_date: date


class MerchantOnboardResponse(BaseModel):
    merchant_id: str
    status: MerchantStatus
    risk_tier: RiskTier
    mdr_rate: Decimal
    settlement_terms: str
    daily_limit_lak: Decimal | None
    monthly_limit_lak: Decimal | None
    integration: IntegrationInfo
    compliance: ComplianceInfo


class MerchantDetailResponse(BaseModel):
    merchant_id: str
    business_name: str
    status: MerchantStatus
    risk_tier: RiskTier
    mdr_rate: Decimal
    settlement_terms: str
    daily_limit_lak: Decimal | None
    monthly_limit_lak: Decimal | None
    channels: list[str]
    created_at: datetime


class MerchantListResponse(BaseModel):
    data: list[MerchantDetailResponse]
    pagination: dict


class MerchantUpdateRequest(BaseModel):
    business_name: str | None = None
    merchant_category: str | None = None
    mdr_rate: Decimal | None = None
    daily_limit_lak: Decimal | None = None
    monthly_limit_lak: Decimal | None = None
    webhook_url: str | None = None
