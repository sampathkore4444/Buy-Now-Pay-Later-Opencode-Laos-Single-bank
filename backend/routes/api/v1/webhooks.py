from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.database import get_bnpl_db
from services.merchant_service import MerchantService
from services.transaction_service import TransactionService
from services.notification_service import NotificationService
from routes.dependencies import get_api_merchant, get_current_admin
from models.merchant import Merchant
from models.settlement import WebhookLog

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/merchants/{merchant_id}", summary="Receive merchant webhook callbacks")
async def merchant_webhook(
    merchant_id: str,
    request: Request,
    merchant: Merchant = Depends(get_api_merchant),
    db: Session = Depends(get_bnpl_db),
):
    if merchant.merchant_id != merchant_id:
        raise HTTPException(status_code=403, detail="Merchant ID mismatch")
    payload = await request.json()
    event_type = payload.get("event", "unknown")
    log = WebhookLog(merchant_id=merchant_id, event_type=event_type, payload=str(payload), status="RECEIVED")
    db.add(log)
    db.commit()
    return {"status": "received", "merchant_id": merchant_id, "event": event_type}


@router.get("/logs", summary="List webhook logs (paginated)")
def list_webhook_logs(
    merchant_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    query = db.query(WebhookLog)
    if merchant_id:
        query = query.filter(WebhookLog.merchant_id == merchant_id)
    total = query.count()
    logs = query.order_by(desc(WebhookLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    data = []
    for log in logs:
        data.append({
            "id": log.id,
            "merchant_id": log.merchant_id,
            "event_type": log.event_type,
            "payload": log.payload,
            "status": log.status,
            "response_code": log.response_code,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })
    return {
        "data": data,
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": (total + page_size - 1) // page_size},
    }
