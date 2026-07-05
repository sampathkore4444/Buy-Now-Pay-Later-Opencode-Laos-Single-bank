from datetime import datetime
from decimal import Decimal
from core.database import BnplSessionLocal
from models.consumer import Consumer
from services.credit_service import CreditService


class CreditLimitRefreshTask:

    def refresh_all(self):
        db = BnplSessionLocal()
        try:
            credit_service = CreditService()
            consumers = db.query(Consumer).filter(Consumer.is_active == True).all()
            updated = 0
            for consumer in consumers:
                try:
                    credit_service.preload_limit_to_redis(consumer)
                    updated += 1
                except Exception:
                    continue
            return {"total": len(consumers), "updated": updated, "status": "COMPLETED"}
        finally:
            db.close()
