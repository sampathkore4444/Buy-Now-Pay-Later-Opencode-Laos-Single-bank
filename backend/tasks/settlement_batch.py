from datetime import date, timedelta
from core.database import BnplSessionLocal
from services.settlement_service import SettlementService
from services.merchant_service import MerchantService


class SettlementBatchProcessor:

    def process(self, settlement_date: date | None = None):
        if settlement_date is None:
            settlement_date = date.today() - timedelta(days=1)
        db = BnplSessionLocal()
        try:
            merchant_service = MerchantService()
            settlement_service = SettlementService()
            merchants, total = merchant_service.list_merchants(db, page=1, page_size=1000)
            results = []
            for merchant in merchants:
                try:
                    settlement = settlement_service.create_daily_settlement(
                        merchant.merchant_id, settlement_date, db
                    )
                    results.append({
                        "merchant_id": merchant.merchant_id,
                        "settlement_id": settlement.settlement_id,
                        "amount": float(settlement.total_net_amount),
                    })
                except Exception:
                    continue
            return {"settlement_date": settlement_date.isoformat(), "settlements": results}
        finally:
            db.close()
