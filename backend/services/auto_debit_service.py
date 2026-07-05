from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from core.config import settings
from services.staging_service import StagingService
from services.fee_service import FeeService
from models.consumer import Consumer
from models.transaction import Transaction
from common.enums import TxnType, TxnCategory
from common.utils import generate_uuid, utcnow


class AutoDebitService:

    def process_daily_repayments(self, bnpl_db: Session, cbs_db: Session) -> dict:
        due_date = date.today() - timedelta(days=30)
        consumers = bnpl_db.query(Consumer).filter(
            Consumer.is_active == True,
            Consumer.available_limit_lak < Consumer.bnpl_limit_lak,
        ).all()

        staging_service = StagingService()
        processed = 0
        errors = 0

        for consumer in consumers:
            used_amount = (consumer.bnpl_limit_lak or 0) - (consumer.available_limit_lak or 0)
            if used_amount <= 0:
                continue

            try:
                txn_id = f"REPAY-{generate_uuid()[:16]}"
                txn = Transaction(
                    txn_id=txn_id,
                    consumer_id=consumer.consumer_id,
                    merchant_id=None,
                    txn_type=TxnType.DEBIT,
                    txn_category=TxnCategory.BNPL_REPAYMENT,
                    amount_lak=used_amount,
                    status="REPAID",
                )
                bnpl_db.add(txn)

                staging_req = {
                    "batch_id": f"BNPL_{utcnow().strftime('%Y%m%d_%H')}",
                    "source_ref_no": txn_id,
                    "source_timestamp": utcnow(),
                    "txn_type": "DEBIT",
                    "txn_category": "BNPL_REPAYMENT",
                    "txn_code": "BNPL-REPAY-001",
                    "txn_amount": float(used_amount),
                    "debit_account_no": None,
                    "credit_account_no": None,
                    "bnpl_extensions": {
                        "bnpl_txn_category": "REPAYMENT",
                        "bnpl_consumer_id": consumer.consumer_id,
                    },
                    "details": [
                        {
                            "detail_type": "PRINCIPAL",
                            "detail_amount": float(used_amount),
                            "narrative_line1": f"Auto-debit repayment for {consumer.consumer_id}",
                        },
                    ],
                }
                staging_service.write_transaction(staging_req, cbs_db)

                consumer.available_limit_lak = consumer.bnpl_limit_lak
                FeeService().mark_repaid(consumer.consumer_id, bnpl_db)
                bnpl_db.commit()
                processed += 1

            except Exception:
                bnpl_db.rollback()
                errors += 1
                continue

        bnpl_db.commit()
        return {
            "processed": processed,
            "errors": errors,
            "total": len(consumers),
            "status": "COMPLETED",
        }
