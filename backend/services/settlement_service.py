import json
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from core.config import settings
from core.kafka import send_event
from models.transaction import Transaction
from models.merchant import Merchant
from models.settlement import Settlement
from common.enums import TxnCategory, StagingStatus
from common.exceptions import NotFoundError
from common.utils import generate_uuid, utcnow


class SettlementService:

    def calculate_settlement(self, amount: Decimal, mdr_rate: Decimal) -> dict:
        mdr_amount = (amount * mdr_rate).quantize(Decimal("0.0001"))
        net_amount = (amount - mdr_amount).quantize(Decimal("0.0001"))
        return {
            "mdr_amount": mdr_amount,
            "net_amount": net_amount,
        }

    def create_daily_settlement(self, merchant_id: str, settlement_date: date, db: Session) -> Settlement:
        txns = db.query(Transaction).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.txn_category == TxnCategory.BNPL_PURCHASE,
            Transaction.created_at >= settlement_date,
            Transaction.created_at < settlement_date.replace(day=settlement_date.day + 1),
            Transaction.status == "CONFIRMED",
        ).all()

        if not txns:
            raise NotFoundError(f"No transactions found for merchant {merchant_id} on {settlement_date}")

        total_gross = sum((t.amount_lak or 0) for t in txns)
        total_mdr = sum((t.mdr_amount or 0) for t in txns)
        total_net = sum((t.net_settlement_amount or 0) for t in txns)

        settlement = Settlement(
            settlement_id=f"STL-{generate_uuid()[:16]}",
            merchant_id=merchant_id,
            batch_id=f"BNPL_{settlement_date.strftime('%Y%m%d')}_STL",
            settlement_date=settlement_date,
            total_txn_count=len(txns),
            total_gross_amount=total_gross,
            total_mdr_amount=total_mdr,
            total_net_amount=total_net,
            status="PENDING",
        )
        db.add(settlement)
        db.commit()
        db.refresh(settlement)
        return settlement

    def process_merchant_payout(self, settlement: Settlement, merchant: Merchant, db: Session):
        settlement.status = "PROCESSING"
        db.commit()

        settlement.staged_at = utcnow()
        settlement.status = "STAGED"
        db.commit()

    def get_settlement_history(self, merchant_id: str, db: Session,
                               page: int = 1, page_size: int = 20) -> tuple[list[Settlement], int]:
        query = db.query(Settlement).filter(Settlement.merchant_id == merchant_id)
        total = query.count()
        settlements = query.order_by(Settlement.settlement_date.desc()) \
                           .offset((page - 1) * page_size) \
                           .limit(page_size) \
                           .all()
        return settlements, total
