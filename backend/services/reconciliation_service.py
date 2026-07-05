from decimal import Decimal
from sqlalchemy.orm import Session

from models.staging import StagingHeader
from models.settlement import Settlement
from common.constants import calculate_risk_score, assign_risk_tier
from common.enums import StagingStatus


class ReconciliationService:

    def reconcile_batch(self, batch_id: str, expected_count: int,
                        expected_amount: Decimal, db: Session) -> dict:
        actual_count = db.query(StagingHeader).filter(
            StagingHeader.batch_id == batch_id
        ).count()

        actual_amount = db.query(StagingHeader).filter(
            StagingHeader.batch_id == batch_id
        ).with_entities(
            StagingHeader.txn_amount
        ).all()
        actual_total = sum((r[0] or 0) for r in actual_amount)

        count_diff = expected_count - actual_count
        amount_diff = expected_amount - actual_total

        balanced = (count_diff == 0 and amount_diff == 0)

        return {
            "batch_id": batch_id,
            "expected_count": expected_count,
            "actual_count": actual_count,
            "count_difference": count_diff,
            "expected_amount": expected_amount,
            "actual_amount": actual_total,
            "amount_difference": amount_diff,
            "status": "BALANCED" if balanced else "UNBALANCED",
        }

    def generate_daily_report(self, report_date: str, db: Session) -> dict:
        staged = db.query(StagingHeader).filter(
            StagingHeader.created_at >= report_date
        ).count()

        posted = db.query(StagingHeader).filter(
            StagingHeader.stg_status == StagingStatus.POSTED,
            StagingHeader.created_at >= report_date,
        ).count()

        failed = db.query(StagingHeader).filter(
            StagingHeader.stg_status == StagingStatus.FAILED,
            StagingHeader.created_at >= report_date,
        ).count()

        return {
            "report_date": report_date,
            "staged_count": staged,
            "posted_count": posted,
            "failed_count": failed,
            "pending_count": staged - posted - failed,
        }
