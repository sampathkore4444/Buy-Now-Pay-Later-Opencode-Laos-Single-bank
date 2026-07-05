from datetime import date, timedelta
from core.database import BnplSessionLocal, CbsStagingSessionLocal
from services.auto_debit_service import AutoDebitService


class RepaymentBatchProcessor:

    def process(self) -> dict:
        bnpl_db = BnplSessionLocal()
        cbs_db = CbsStagingSessionLocal()
        try:
            service = AutoDebitService()
            result = service.process_daily_repayments(bnpl_db, cbs_db)
            return result
        finally:
            bnpl_db.close()
            cbs_db.close()
