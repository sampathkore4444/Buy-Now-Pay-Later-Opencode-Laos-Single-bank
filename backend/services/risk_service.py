from decimal import Decimal
from sqlalchemy.orm import Session

from models.merchant import Merchant
from models.consumer import Consumer
from common.constants import calculate_risk_score, assign_risk_tier, RISK_WEIGHTS


class RiskService:

    def assess_merchant_risk(self, merchant: Merchant, db: Session) -> dict:
        metrics = {
            "business_tenure_months": 12,
            "chargeback_rate": 0.005,
            "settlement_on_time": True,
            "complaint_rate": 0.01,
        }
        score = calculate_risk_score(metrics)
        tier = assign_risk_tier(score)

        merchant.risk_score = score
        merchant.risk_tier = tier
        db.commit()

        return {
            "merchant_id": merchant.merchant_id,
            "risk_score": score,
            "risk_tier": tier,
        }

    def assess_consumer_risk(self, consumer: Consumer, db: Session) -> dict:
        score = 85
        tier = assign_risk_tier(score)

        consumer.risk_score = score
        consumer.risk_tier = tier
        db.commit()

        return {
            "consumer_id": consumer.consumer_id,
            "risk_score": score,
            "risk_tier": tier,
        }

    def get_mdr_adjustment(self, risk_tier: str) -> Decimal:
        adjustments = {
            "GREEN": Decimal("0.000"),
            "YELLOW": Decimal("0.010"),
            "ORANGE": Decimal("0.020"),
            "RED": Decimal("0.030"),
        }
        return adjustments.get(risk_tier, Decimal("0.000"))
