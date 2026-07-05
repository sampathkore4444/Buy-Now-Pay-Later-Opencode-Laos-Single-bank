from datetime import timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from services.staging_service import StagingService
from services.transaction_service import TransactionService
from services.settlement_service import SettlementService
from models.transaction import AuthRequest, Transaction
from models.merchant import Merchant
from models.consumer import Consumer
from common.enums import AuthStatus, TxnType, TxnCategory
from common.exceptions import NotFoundError, BadRequestError
from common.utils import generate_uuid, utcnow


REFUND_WINDOW_DAYS = 30


class RefundService:

    def initiate_refund(
        self, auth_id: str, merchant_id: str, amount: Decimal | None,
        bnpl_db: Session, cbs_db: Session,
    ) -> dict:
        auth = bnpl_db.query(AuthRequest).filter(
            AuthRequest.auth_id == auth_id,
            AuthRequest.merchant_id == merchant_id,
        ).first()

        if not auth:
            raise NotFoundError(f"Auth {auth_id} not found for merchant {merchant_id}")

        if auth.status != AuthStatus.SETTLED:
            raise BadRequestError(
                f"Auth {auth_id} is in state {auth.status.value}, must be SETTLED to refund"
            )

        refund_amount = amount or auth.approved_amount_lak
        if refund_amount <= 0:
            raise BadRequestError("Refund amount must be positive")

        if refund_amount > (auth.approved_amount_lak or 0):
            raise BadRequestError("Refund amount exceeds original transaction amount")

        days_since_settlement = (utcnow().date() - auth.auth_timestamp.date()).days if auth.auth_timestamp else 0
        if days_since_settlement > REFUND_WINDOW_DAYS:
            raise BadRequestError(
                f"Refund window of {REFUND_WINDOW_DAYS} days has passed "
                f"({days_since_settlement} days since transaction)"
            )

        mdr_rate = auth.mdr_rate or Decimal("0.045")
        mdr_reversal = (refund_amount * mdr_rate).quantize(Decimal("0.0001"))
        net_reversal = (refund_amount - mdr_reversal).quantize(Decimal("0.0001"))

        consumer = bnpl_db.query(Consumer).filter(
            Consumer.consumer_id == auth.consumer_id
        ).first()

        if consumer:
            consumer.available_limit_lak = (consumer.available_limit_lak or 0) + refund_amount

        refund_txn = Transaction(
            txn_id=f"RFND-{generate_uuid()[:16]}",
            correlation_id=None,
            auth_id=auth.auth_id,
            consumer_id=auth.consumer_id,
            merchant_id=auth.merchant_id,
            txn_type=TxnType.REVERSAL,
            txn_category=TxnCategory.BNPL_REFUND,
            amount_lak=refund_amount,
            mdr_rate=mdr_rate,
            mdr_amount=mdr_reversal,
            net_settlement_amount=net_reversal,
            status="REFUNDED",
        )
        bnpl_db.add(refund_txn)
        bnpl_db.commit()

        staging_service = StagingService()
        staging_req = {
            "batch_id": f"BNPL_{utcnow().strftime('%Y%m%d_%H')}",
            "source_ref_no": refund_txn.txn_id,
            "source_timestamp": utcnow(),
            "txn_type": "REVERSAL",
            "txn_category": "BNPL_REFUND",
            "txn_code": "BNPL-REFUND-001",
            "txn_amount": float(refund_amount),
            "debit_account_no": None,
            "credit_account_no": None,
            "bnpl_extensions": {
                "bnpl_txn_category": "REFUND",
                "bnpl_merchant_id": auth.merchant_id,
                "bnpl_consumer_id": auth.consumer_id,
                "bnpl_auth_id": auth.auth_id,
                "mdr_rate": float(mdr_rate),
                "mdr_amount": float(mdr_reversal),
                "net_settlement_amount": float(net_reversal),
            },
            "details": [
                {
                    "detail_type": "PRINCIPAL",
                    "detail_amount": float(net_reversal),
                    "narrative_line1": f"Refund for auth {auth_id}",
                },
                {
                    "detail_type": "MDR",
                    "detail_amount": float(mdr_reversal),
                    "narrative_line1": "MDR reversal for refund",
                },
            ],
        }
        result = staging_service.write_transaction(staging_req, cbs_db)
        return result
