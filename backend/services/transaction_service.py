import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from core.config import settings
from core.kafka import send_event
from models.transaction import Transaction, AuthRequest
from models.staging import StagingHeader
from common.enums import TxnType, TxnCategory, AuthStatus
from common.exceptions import NotFoundError, BadRequestError
from common.utils import generate_uuid, generate_correlation_id, utcnow


class TransactionService:

    def create_from_auth(self, auth: AuthRequest, db: Session) -> Transaction:
        correlation_id = generate_correlation_id()
        mdr_amount = (auth.approved_amount_lak * (auth.mdr_rate or Decimal("0"))).quantize(Decimal("0.0001"))
        net_amount = (auth.approved_amount_lak - mdr_amount).quantize(Decimal("0.0001"))

        txn = Transaction(
            txn_id=f"TXN-{generate_uuid()[:16]}",
            correlation_id=correlation_id,
            auth_id=auth.auth_id,
            consumer_id=auth.consumer_id,
            merchant_id=auth.merchant_id,
            txn_type=TxnType.TRANSFER,
            txn_category=TxnCategory.BNPL_PURCHASE,
            amount_lak=auth.approved_amount_lak,
            mdr_rate=auth.mdr_rate,
            mdr_amount=mdr_amount,
            net_settlement_amount=net_amount,
            status="CONFIRMED",
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)
        return txn

    def get_by_id(self, txn_id: str, db: Session) -> Transaction:
        txn = db.query(Transaction).filter(Transaction.txn_id == txn_id).first()
        if not txn:
            raise NotFoundError(f"Transaction {txn_id} not found")
        return txn

    def list_by_merchant(self, merchant_id: str, db: Session,
                         page: int = 1, page_size: int = 20) -> tuple[list[Transaction], int]:
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        total = query.count()
        txns = query.order_by(Transaction.created_at.desc()) \
                    .offset((page - 1) * page_size) \
                    .limit(page_size) \
                    .all()
        return txns, total

    def list_by_consumer(self, consumer_id: str, db: Session,
                         page: int = 1, page_size: int = 20) -> tuple[list[Transaction], int]:
        query = db.query(Transaction).filter(Transaction.consumer_id == consumer_id)
        total = query.count()
        txns = query.order_by(Transaction.created_at.desc()) \
                    .offset((page - 1) * page_size) \
                    .limit(page_size) \
                    .all()
        return txns, total

    def create_staging_header(self, txn: Transaction, db: Session) -> StagingHeader:
        batch_id = f"BNPL_{utcnow().strftime('%Y%m%d_%H')}"

        header = StagingHeader(
            correlation_id=txn.correlation_id,
            batch_id=batch_id,
            source_ref_no=txn.txn_id,
            source_timestamp=utcnow(),
            txn_type=txn.txn_type.value,
            txn_category=txn.txn_category.value,
            txn_amount=txn.amount_lak,
            txn_code="BNPL-PURCHASE-001",
            bnpl_txn_category=txn.txn_category.value,
            bnpl_merchant_id=txn.merchant_id,
            bnpl_consumer_id=txn.consumer_id,
            bnpl_auth_id=txn.auth_id,
            mdr_rate=txn.mdr_rate,
            mdr_amount=txn.mdr_amount,
            net_settlement_amount=txn.net_settlement_amount,
        )
        db.add(header)
        db.commit()
        db.refresh(header)
        return header
