from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from core.database import get_bnpl_db
from models.settlement import NotificationLog
from schemas.common import PaginatedResponse
from common.utils import build_pagination_response, safe_endpoint
from routes.dependencies import get_current_admin

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PaginatedResponse, summary="List notification logs (paginated)")
@safe_endpoint
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    channel: str | None = Query(None),
    status: str | None = Query(None),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    query = db.query(NotificationLog)
    if channel:
        query = query.filter(NotificationLog.channel == channel)
    if status:
        query = query.filter(NotificationLog.status == status)
    total = query.count()
    logs = query.order_by(desc(NotificationLog.sent_at)).offset((page - 1) * page_size).limit(page_size).all()
    data = []
    for log in logs:
        data.append({
            "notification_id": log.notification_id,
            "recipient": log.recipient,
            "channel": log.channel,
            "template": log.template,
            "message": log.message[:200],
            "status": log.status,
            "reference_type": log.reference_type,
            "reference_id": log.reference_id,
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
        })
    return build_pagination_response(data, total, page, page_size)
