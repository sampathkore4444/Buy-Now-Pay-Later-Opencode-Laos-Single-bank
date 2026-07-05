from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from core.config import settings
from common.constants import (
    LATE_FEE_FLAT_LAK, LATE_FEE_GRACE_DAYS, LATE_FEE_MAX_PER_CONSUMER,
    INTEREST_MONTHLY_RATE, INTEREST_COMPOUND_DAYS,
)
from common.enums import TxnType, TxnCategory
from common.utils import generate_uuid, utcnow
from models.consumer import Consumer
from models.transaction import Transaction, AuthRequest
from models.overdue import OverdueTracker
from services.staging_service import StagingService


class FeeService:

    def assess_late_fees(self, bnpl_db: Session, cbs_db: Session) -> dict:
        today = date.today()
        overdue_consumers = bnpl_db.query(Consumer).filter(
            Consumer.is_active == True,
            Consumer.available_limit_lak < Consumer.bnpl_limit_lak,
        ).all()

        staging_service = StagingService()
        assessed = 0
        skipped = 0
        errors = 0

        for consumer in overdue_consumers:
            try:
                used_amount = (consumer.bnpl_limit_lak or 0) - (consumer.available_limit_lak or 0)
                if used_amount <= 0:
                    continue

                tracker = bnpl_db.query(OverdueTracker).filter(
                    OverdueTracker.consumer_id == consumer.consumer_id,
                    OverdueTracker.status == "ACTIVE",
                ).first()

                if not tracker:
                    last_repayment = bnpl_db.query(Transaction).filter(
                        Transaction.consumer_id == consumer.consumer_id,
                        Transaction.txn_category == TxnCategory.BNPL_REPAYMENT,
                        Transaction.status == "REPAID",
                    ).order_by(Transaction.created_at.desc()).first()

                    overdue_start = today - timedelta(days=LATE_FEE_GRACE_DAYS)
                    if last_repayment and last_repayment.created_at.date() > overdue_start:
                        skipped += 1
                        continue

                    tracker = OverdueTracker(
                        consumer_id=consumer.consumer_id,
                        overdue_date=overdue_start,
                        days_overdue=(today - overdue_start).days,
                        overdue_amount_lak=used_amount,
                        status="ACTIVE",
                    )
                    bnpl_db.add(tracker)
                    bnpl_db.flush()

                if tracker.last_fee_assessment and tracker.last_fee_assessment == today:
                    skipped += 1
                    continue

                if tracker.late_fee_count >= LATE_FEE_MAX_PER_CONSUMER:
                    skipped += 1
                    continue

                if tracker.last_fee_assessment:
                    days_since_last = (today - tracker.last_fee_assessment).days
                    if days_since_last < LATE_FEE_GRACE_DAYS:
                        skipped += 1
                        continue

                self._apply_late_fee(consumer, tracker, used_amount, staging_service, bnpl_db, cbs_db)
                assessed += 1

            except Exception:
                bnpl_db.rollback()
                cbs_db.rollback()
                errors += 1
                continue

        bnpl_db.commit()
        cbs_db.commit()
        return {
            "assessed": assessed,
            "skipped": skipped,
            "errors": errors,
            "status": "COMPLETED",
        }

    def assess_interest(self, bnpl_db: Session, cbs_db: Session) -> dict:
        today = date.today()
        trackers = bnpl_db.query(OverdueTracker).filter(
            OverdueTracker.status == "ACTIVE",
        ).all()

        staging_service = StagingService()
        assessed = 0
        skipped = 0
        errors = 0

        for tracker in trackers:
            try:
                if tracker.last_interest_assessment:
                    days_since = (today - tracker.last_interest_assessment).days
                    if days_since < INTEREST_COMPOUND_DAYS:
                        skipped += 1
                        continue
                elif tracker.days_overdue < LATE_FEE_GRACE_DAYS:
                    skipped += 1
                    continue

                consumer = bnpl_db.query(Consumer).filter(
                    Consumer.consumer_id == tracker.consumer_id,
                    Consumer.is_active == True,
                ).first()
                if not consumer:
                    skipped += 1
                    continue

                used_amount = (consumer.bnpl_limit_lak or 0) - (consumer.available_limit_lak or 0)
                if used_amount <= 0:
                    skipped += 1
                    continue

                self._apply_interest(consumer, tracker, used_amount, staging_service, bnpl_db, cbs_db)
                assessed += 1

            except Exception:
                bnpl_db.rollback()
                cbs_db.rollback()
                errors += 1
                continue

        bnpl_db.commit()
        cbs_db.commit()
        return {
            "assessed": assessed,
            "skipped": skipped,
            "errors": errors,
            "status": "COMPLETED",
        }

    def _apply_late_fee(
        self,
        consumer: Consumer,
        tracker: OverdueTracker,
        used_amount: Decimal,
        staging_service: StagingService,
        bnpl_db: Session,
        cbs_db: Session,
    ):
        today = date.today()
        fee_amount = Decimal(str(LATE_FEE_FLAT_LAK))

        txn_id = f"LATEFEE-{generate_uuid()[:16]}"
        txn = Transaction(
            txn_id=txn_id,
            consumer_id=consumer.consumer_id,
            merchant_id=None,
            txn_type=TxnType.DEBIT,
            txn_category=TxnCategory.BNPL_LATE_FEE,
            amount_lak=fee_amount,
            status="ASSESSED",
        )
        bnpl_db.add(txn)

        staging_req = {
            "batch_id": f"BNPL_{utcnow().strftime('%Y%m%d_%H')}",
            "source_ref_no": txn_id,
            "source_timestamp": utcnow(),
            "txn_type": "DEBIT",
            "txn_category": "BNPL_LATE_FEE",
            "txn_code": "BNPL-FEE-001",
            "txn_amount": float(fee_amount),
            "debit_account_no": None,
            "credit_account_no": None,
            "bnpl_extensions": {
                "bnpl_txn_category": "LATE_FEE",
                "bnpl_consumer_id": consumer.consumer_id,
            },
            "details": [
                {
                    "detail_type": "LATE_FEE",
                    "detail_amount": float(fee_amount),
                    "narrative_line1": f"Late fee {today.isoformat()} for {consumer.consumer_id}",
                },
            ],
        }
        staging_service.write_transaction(staging_req, cbs_db)

        consumer.available_limit_lak = (consumer.available_limit_lak or 0) - fee_amount
        tracker.late_fee_charged = (tracker.late_fee_charged or 0) + fee_amount
        tracker.late_fee_count = (tracker.late_fee_count or 0) + 1
        tracker.last_fee_assessment = today
        tracker.days_overdue = (today - tracker.overdue_date).days
        tracker.overdue_amount_lak = used_amount + fee_amount

        bnpl_db.flush()

    def _apply_interest(
        self,
        consumer: Consumer,
        tracker: OverdueTracker,
        used_amount: Decimal,
        staging_service: StagingService,
        bnpl_db: Session,
        cbs_db: Session,
    ):
        today = date.today()
        overdue_principal = used_amount
        interest_amount = (overdue_principal * Decimal(str(INTEREST_MONTHLY_RATE))).quantize(Decimal("0.0001"))

        if interest_amount <= 0:
            return

        txn_id = f"INT-{generate_uuid()[:16]}"
        txn = Transaction(
            txn_id=txn_id,
            consumer_id=consumer.consumer_id,
            merchant_id=None,
            txn_type=TxnType.DEBIT,
            txn_category=TxnCategory.BNPL_INTEREST,
            amount_lak=interest_amount,
            status="ASSESSED",
        )
        bnpl_db.add(txn)

        staging_req = {
            "batch_id": f"BNPL_{utcnow().strftime('%Y%m%d_%H')}",
            "source_ref_no": txn_id,
            "source_timestamp": utcnow(),
            "txn_type": "DEBIT",
            "txn_category": "BNPL_INTEREST",
            "txn_code": "BNPL-INT-001",
            "txn_amount": float(interest_amount),
            "debit_account_no": None,
            "credit_account_no": None,
            "bnpl_extensions": {
                "bnpl_txn_category": "INTEREST",
                "bnpl_consumer_id": consumer.consumer_id,
            },
            "details": [
                {
                    "detail_type": "INTEREST",
                    "detail_amount": float(interest_amount),
                    "narrative_line1": f"Monthly interest {today.isoformat()} for {consumer.consumer_id}",
                },
            ],
        }
        staging_service.write_transaction(staging_req, cbs_db)

        consumer.available_limit_lak = (consumer.available_limit_lak or 0) - interest_amount
        tracker.interest_charged = (tracker.interest_charged or 0) + interest_amount
        tracker.last_interest_assessment = today
        tracker.days_overdue = (today - tracker.overdue_date).days
        tracker.overdue_amount_lak = used_amount + interest_amount

        bnpl_db.flush()

    def mark_repaid(self, consumer_id: str, bnpl_db: Session):
        trackers = bnpl_db.query(OverdueTracker).filter(
            OverdueTracker.consumer_id == consumer_id,
            OverdueTracker.status == "ACTIVE",
        ).all()
        for t in trackers:
            t.status = "PAID"
        bnpl_db.commit()

    def get_consumer_overdue(self, consumer_id: str, bnpl_db: Session) -> dict | None:
        tracker = bnpl_db.query(OverdueTracker).filter(
            OverdueTracker.consumer_id == consumer_id,
            OverdueTracker.status == "ACTIVE",
        ).first()
        if not tracker:
            return None
        return {
            "consumer_id": tracker.consumer_id,
            "days_overdue": tracker.days_overdue,
            "overdue_amount_lak": float(tracker.overdue_amount_lak or 0),
            "late_fee_charged": float(tracker.late_fee_charged or 0),
            "interest_charged": float(tracker.interest_charged or 0),
            "last_fee_assessment": tracker.last_fee_assessment.isoformat() if tracker.last_fee_assessment else None,
            "last_interest_assessment": tracker.last_interest_assessment.isoformat() if tracker.last_interest_assessment else None,
        }
