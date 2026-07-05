from datetime import date
from core.database import BnplSessionLocal, CbsStagingSessionLocal
from services.fee_service import FeeService


class FeeBatchProcessor:

    def process_daily_fees(self) -> dict:
        bnpl_db = BnplSessionLocal()
        cbs_db = CbsStagingSessionLocal()
        try:
            service = FeeService()
            result = service.assess_late_fees(bnpl_db, cbs_db)
            return result
        finally:
            bnpl_db.close()
            cbs_db.close()

    def process_monthly_interest(self) -> dict:
        bnpl_db = BnplSessionLocal()
        cbs_db = CbsStagingSessionLocal()
        try:
            service = FeeService()
            result = service.assess_interest(bnpl_db, cbs_db)
            return result
        finally:
            bnpl_db.close()
            cbs_db.close()
