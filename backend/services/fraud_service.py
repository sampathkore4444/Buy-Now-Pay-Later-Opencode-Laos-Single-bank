from decimal import Decimal
from sqlalchemy.orm import Session

from models.settlement import FraudRule
from models.transaction import AuthRequest
from models.consumer import Consumer
from models.merchant import Merchant
from common.enums import AuthStatus


class FraudService:

    def __init__(self):
        self.rules_cache: list[dict] | None = None

    async def evaluate(self, auth: AuthRequest, consumer: Consumer,
                       merchant: Merchant, db: Session) -> list[str]:
        flags: list[str] = []
        rules = self._load_rules(db)

        for rule in rules:
            if not rule.enabled:
                continue
            result = await self._evaluate_rule(rule, auth, consumer, merchant)
            if result:
                flags.append(result)
        return flags

    def _load_rules(self, db: Session) -> list[FraudRule]:
        return db.query(FraudRule).all()

    async def _evaluate_rule(self, rule: FraudRule, auth: AuthRequest,
                             consumer: Consumer, merchant: Merchant) -> str | None:
        param = rule.parameter
        threshold = rule.threshold

        if param == "txn_amount" and auth.amount_lak:
            try:
                limit = Decimal(threshold)
                if auth.amount_lak > limit:
                    return f"Amount {auth.amount_lak} exceeds threshold {limit}"
            except Exception:
                pass

        if param == "velocity_per_hour":
            return None

        if param == "new_merchant":
            if merchant.status and "PENDING" in merchant.status.name:
                return "Transaction from pending KYC merchant"

        if param == "round_amount":
            if auth.amount_lak and auth.amount_lak % Decimal("1000") == 0 and auth.amount_lak > Decimal("1000000"):
                return f"Round amount {auth.amount_lak} flagged for review"

        return None

    def check_refund_abuse(self, merchant_id: str, refund_count: int,
                           total_txns: int, threshold: float = 0.10) -> bool:
        if total_txns == 0:
            return False
        return (refund_count / total_txns) > threshold
