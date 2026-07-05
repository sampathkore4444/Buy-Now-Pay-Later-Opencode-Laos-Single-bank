from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.config import settings
from core.database import BnplSessionLocal, CbsStagingSessionLocal
from cbs_staging.models import (
    STG_TXN_HEADER,
    STG_TXN_CONTROL,
    STG_ERROR_LOG,
    STG_RECONCILE,
)
from models.transaction import AuthRequest
from services.transaction_service import TransactionService
from services.staging_service import StagingService
from common.enums import AuthStatus
from common.utils import utcnow

EOD_LOCK_KEY = 12345
MAX_EOD_DURATION_HOURS = 6


class EODBatchProcessor:

    def process(self, eod_batch_run_id: str | None = None) -> dict:
        if eod_batch_run_id is None:
            eod_batch_run_id = f"EOD_{utcnow().strftime('%Y%m%d_%H%M%S')}_{utcnow().microsecond}"

        bnpl_db = BnplSessionLocal()
        cbs_db = CbsStagingSessionLocal()

        try:
            lock_acquired = self._acquire_advisory_lock(cbs_db)
            if not lock_acquired:
                return {
                    "status": "SKIPPED",
                    "reason": "Another EOD instance is running",
                    "eod_batch_run_id": eod_batch_run_id,
                }

            self._detect_and_recover_crashed_runs(cbs_db)

            ready_batches = cbs_db.query(STG_TXN_CONTROL).filter(
                STG_TXN_CONTROL.CONTROL_STATUS == "READY_FOR_PICKUP",
                STG_TXN_CONTROL.CONTROL_STATUS_TIMESTAMP < utcnow() - timedelta(minutes=15),
            ).with_for_update(skip_locked=True).all()

            results = []
            for control in ready_batches:
                batch_result = self._process_batch(
                    control, eod_batch_run_id, bnpl_db, cbs_db
                )
                results.append(batch_result)

            self._release_advisory_lock(cbs_db)

            return {
                "status": "COMPLETED",
                "batches_found": len(ready_batches),
                "batches_processed": results,
                "eod_batch_run_id": eod_batch_run_id,
                "timestamp": utcnow().isoformat(),
            }

        finally:
            bnpl_db.close()
            cbs_db.close()

    def _acquire_advisory_lock(self, cbs_db: Session) -> bool:
        result = cbs_db.execute(
            text("SELECT pg_try_advisory_lock(:lock_key)"),
            {"lock_key": EOD_LOCK_KEY},
        ).scalar()
        return bool(result)

    def _release_advisory_lock(self, cbs_db: Session):
        cbs_db.execute(
            text("SELECT pg_advisory_unlock(:lock_key)"),
            {"lock_key": EOD_LOCK_KEY},
        )

    def _detect_and_recover_crashed_runs(self, cbs_db: Session):
        cutoff = utcnow() - timedelta(hours=MAX_EOD_DURATION_HOURS)
        stalled = cbs_db.query(STG_TXN_CONTROL).filter(
            STG_TXN_CONTROL.CONTROL_STATUS == "IN_PROGRESS",
            STG_TXN_CONTROL.EOD_START_TIMESTAMP < cutoff,
        ).all()

        for control in stalled:
            batch_id = control.BATCH_ID

            picked = cbs_db.query(STG_TXN_HEADER).filter(
                STG_TXN_HEADER.BATCH_ID == batch_id,
                STG_TXN_HEADER.STG_STATUS == "PICKED",
            ).all()

            for header in picked:
                header.STG_STATUS = "PENDING"
                header.EOD_BATCH_RUN_ID = None
                header.EOD_PICKUP_TIMESTAMP = None

            control.CONTROL_STATUS = "READY_FOR_PICKUP"
            control.EOD_BATCH_RUN_ID = None
            control.EOD_START_TIMESTAMP = None
            control.CONTROL_STATUS_TIMESTAMP = utcnow()

        if stalled:
            cbs_db.commit()

    def _process_batch(
        self,
        control: STG_TXN_CONTROL,
        eod_batch_run_id: str,
        bnpl_db,
        cbs_db,
    ) -> dict:
        batch_id = control.BATCH_ID

        control.CONTROL_STATUS = "IN_PROGRESS"
        control.EOD_BATCH_RUN_ID = eod_batch_run_id
        control.EOD_START_TIMESTAMP = utcnow()
        control.CONTROL_STATUS_TIMESTAMP = utcnow()

        cbs_db.query(STG_TXN_HEADER).filter(
            STG_TXN_HEADER.BATCH_ID == batch_id,
            STG_TXN_HEADER.STG_STATUS == "PENDING",
        ).update({
            STG_TXN_HEADER.STG_STATUS: "PICKED",
            STG_TXN_HEADER.EOD_BATCH_RUN_ID: eod_batch_run_id,
            STG_TXN_HEADER.EOD_PICKUP_TIMESTAMP: utcnow(),
        })
        cbs_db.flush()

        picked = cbs_db.query(STG_TXN_HEADER).filter(
            STG_TXN_HEADER.BATCH_ID == batch_id,
            STG_TXN_HEADER.STG_STATUS == "PICKED",
        ).all()

        posted_count = 0
        posted_amount = Decimal("0")
        failed_count = 0
        failed_amount = Decimal("0")
        held_count = 0
        held_amount = Decimal("0")

        for header in picked:
            try:
                if not self._validate_staging_record(header):
                    raise ValueError(f"Validation failed for header {header.STG_HEADER_ID}")

                self._post_to_live_gl(header, bnpl_db)

                header.STG_STATUS = "POSTED"
                header.EOD_POSTING_TIMESTAMP = utcnow()
                posted_count += 1
                posted_amount += (header.TXN_AMOUNT or Decimal("0"))

            except Exception as e:
                header.STG_STATUS = "FAILED"
                header.EOD_FAILURE_REASON = str(e)[:512]
                header.RETRY_COUNT += 1
                failed_count += 1
                failed_amount += (header.TXN_AMOUNT or Decimal("0"))

                error_log = STG_ERROR_LOG(
                    STG_HEADER_ID=header.STG_HEADER_ID,
                    BATCH_ID=batch_id,
                    ERROR_PHASE="EOD_POSTING",
                    ERROR_CODE="EOD-POST-001",
                    ERROR_SEVERITY="ERROR",
                    ERROR_MESSAGE=str(e)[:2000],
                    ERROR_TIMESTAMP=utcnow(),
                )
                cbs_db.add(error_log)

        control.ACTUAL_RECORD_COUNT = posted_count
        control.ACTUAL_TOTAL_AMOUNT = posted_amount
        control.EOD_END_TIMESTAMP = utcnow()
        control.CONTROL_STATUS_TIMESTAMP = utcnow()

        if failed_count == 0:
            control.CONTROL_STATUS = "COMPLETED"
        elif posted_count > 0:
            control.CONTROL_STATUS = "PARTIAL"
        else:
            control.CONTROL_STATUS = "FAILED"

        cbs_db.commit()

        reconcile = STG_RECONCILE(
            RECONCILE_DATE=utcnow().date(),
            SOURCE_SYSTEM="BNPL_PLATFORM",
            BATCH_ID=batch_id,
            STAGED_COUNT=len(picked),
            STAGED_AMOUNT=posted_amount + failed_amount,
            POSTED_COUNT=posted_count,
            POSTED_AMOUNT=posted_amount,
            FAILED_COUNT=failed_count,
            FAILED_AMOUNT=failed_amount,
            HELD_COUNT=held_count,
            HELD_AMOUNT=held_amount,
            DIFFERENCE_COUNT=0,
            DIFFERENCE_AMOUNT=Decimal("0"),
            STATUS="BALANCED" if failed_count == 0 else "UNBALANCED",
        )
        cbs_db.add(reconcile)
        cbs_db.commit()

        return {
            "batch_id": batch_id,
            "status": control.CONTROL_STATUS,
            "posted": posted_count,
            "failed": failed_count,
        }

    def _validate_staging_record(self, header: STG_TXN_HEADER) -> bool:
        if not header.DEBIT_ACCOUNT_NO and not header.CREDIT_ACCOUNT_NO:
            return False
        if header.TXN_AMOUNT is None or header.TXN_AMOUNT <= 0:
            return False
        return True

    def _post_to_live_gl(self, header: STG_TXN_HEADER, bnpl_db):
        if header.BNPL_AUTH_ID:
            auth = bnpl_db.query(AuthRequest).filter(
                AuthRequest.auth_id == header.BNPL_AUTH_ID
            ).first()
            if auth and auth.status == AuthStatus.CONFIRMED:
                auth.status = AuthStatus.SETTLED
