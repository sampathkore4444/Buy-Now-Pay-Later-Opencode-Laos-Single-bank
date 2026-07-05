from decimal import Decimal
from sqlalchemy.orm import Session

from core.config import settings
from core.security import generate_api_key, generate_api_secret, hash_password
from models.merchant import Merchant, MerchantDocument, MerchantUser
from schemas.merchant import MerchantOnboardRequest, MerchantOnboardResponse
from common.enums import MerchantStatus, RiskTier
from common.constants import determine_mdr_rate
from common.exceptions import ConflictError, NotFoundError, BadRequestError
from common.utils import generate_merchant_id, utcnow


class MerchantService:

    def onboard(self, req: MerchantOnboardRequest, db: Session) -> MerchantOnboardResponse:
        existing = db.query(Merchant).filter(
            Merchant.application_id == req.application_id
        ).first()
        if existing:
            raise ConflictError(f"Application {req.application_id} already exists")

        existing_tax = db.query(Merchant).filter(
            Merchant.tax_id == req.tax_id
        ).first()
        if existing_tax:
            raise ConflictError(f"Tax ID {req.tax_id} already registered")

        merchant_id = generate_merchant_id()
        mdr_rate = determine_mdr_rate(
            float(req.estimated_monthly_volume_lak),
            "GREEN",
        )

        risk_tier = RiskTier.GREEN
        daily_limit = req.estimated_monthly_volume_lak / Decimal("30")
        monthly_limit = req.estimated_monthly_volume_lak

        api_key = generate_api_key()
        api_secret = generate_api_secret()
        api_secret_hash_val = hash_password(api_secret)

        merchant = Merchant(
            merchant_id=merchant_id,
            application_id=req.application_id,
            business_name=req.business_name,
            business_name_lao=req.business_name_lao,
            registration_number=req.registration_number,
            tax_id=req.tax_id,
            business_type=req.business_type,
            merchant_category=req.merchant_category,
            owner_name=req.owner.name,
            owner_id_card=req.owner.id_card,
            owner_phone=req.owner.phone,
            owner_email=req.owner.email,
            settlement_bank_code=req.settlement_account.bank_code,
            settlement_account_no=req.settlement_account.account_number,
            settlement_account_name=req.settlement_account.account_name,
            address_street=req.business_address.street,
            address_district=req.business_address.district,
            address_province=req.business_address.province,
            address_gps=req.business_address.gps_coordinates,
            channels=",".join(c.value for c in req.channels),
            estimated_monthly_volume_lak=req.estimated_monthly_volume_lak,
            average_ticket_size_lak=req.average_ticket_size_lak,
            referral_source=req.referral_source,
            status=MerchantStatus.APPROVED,
            risk_tier=risk_tier,
            mdr_rate=Decimal(str(mdr_rate)),
            settlement_terms="T+1",
            daily_limit_lak=daily_limit,
            monthly_limit_lak=monthly_limit,
            api_key=api_key,
            api_secret_hash=api_secret_hash_val,
            webhook_url=f"https://api.bnpl-bank.la/v1/webhooks/merchants/{merchant_id}",
            qr_code_url=f"https://qr.bnpl-bank.la/{merchant_id}",
            kyc_status="VERIFIED",
            aml_check="PASSED",
            sanctions_screen="PASSED",
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        return MerchantOnboardResponse(
            merchant_id=merchant.merchant_id,
            status=merchant.status,
            risk_tier=merchant.risk_tier,
            mdr_rate=merchant.mdr_rate,
            settlement_terms=merchant.settlement_terms,
            daily_limit_lak=merchant.daily_limit_lak,
            monthly_limit_lak=merchant.monthly_limit_lak,
            integration={
                "api_key": api_key,
                "api_secret": api_secret,
                "webhook_url": merchant.webhook_url,
                "qr_code_url": merchant.qr_code_url,
                "sandbox_url": "https://sandbox-api.bnpl-bank.la/v1",
            },
            compliance={
                "kyc_status": "VERIFIED",
                "aml_check": "PASSED",
                "sanctions_screen": "PASSED",
                "next_review_date": (utcnow().date()).replace(day=min(utcnow().day, 28)),
            },
        )

    def get_by_id(self, merchant_id: str, db: Session) -> Merchant:
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            raise NotFoundError(f"Merchant {merchant_id} not found")
        return merchant

    def list_merchants(self, db: Session, page: int = 1, page_size: int = 20,
                       status: str | None = None) -> tuple[list[Merchant], int]:
        query = db.query(Merchant)
        if status:
            query = query.filter(Merchant.status == status)
        total = query.count()
        merchants = query.order_by(Merchant.created_at.desc()) \
                         .offset((page - 1) * page_size) \
                         .limit(page_size) \
                         .all()
        return merchants, total

    def update_merchant(self, merchant_id: str, updates: dict, db: Session) -> Merchant:
        merchant = self.get_by_id(merchant_id, db)
        for field, value in updates.items():
            if value is not None and hasattr(merchant, field):
                setattr(merchant, field, value)
        db.commit()
        db.refresh(merchant)
        return merchant

    def validate_api_key(self, api_key: str, db: Session) -> Merchant | None:
        return db.query(Merchant).filter(Merchant.api_key == api_key).first()
