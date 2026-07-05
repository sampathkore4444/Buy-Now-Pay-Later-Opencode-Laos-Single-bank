from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from core.database import get_bnpl_db
from models.settlement import CreditLimitRefreshLog
from schemas.common import PaginatedResponse
from common.utils import build_pagination_response, generate_uuid, safe_endpoint
from services.credit_service import CreditService
from routes.dependencies import get_current_admin

router = APIRouter(prefix="/credit", tags=["Credit Management"])


@router.post("/refresh", response_model=dict, summary="Trigger credit limit refresh from Redis")
@safe_endpoint
async def refresh_limits(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    log = CreditLimitRefreshLog(
        batch_id=f"CR-{generate_uuid()[:12]}",
        total_consumers=0,
        limits_updated=0,
        started_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()

    try:
        service = CreditService()
        await service.refresh_limits_from_redis(db)
        log.status = "COMPLETED"
        log.completed_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        log.status = "FAILED"
        log.error_message = str(e)
        db.commit()
        raise

    return {"status": "COMPLETED", "batch_id": log.batch_id}


@router.get("/refresh-logs", response_model=PaginatedResponse, summary="List credit limit refresh logs")
@safe_endpoint
def list_refresh_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    query = db.query(CreditLimitRefreshLog).order_by(desc(CreditLimitRefreshLog.started_at))
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    data = []
    for log in logs:
        data.append({
            "batch_id": log.batch_id,
            "total_consumers": log.total_consumers,
            "limits_updated": log.limits_updated,
            "status": log.status,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            "error_message": log.error_message,
        })
    return build_pagination_response(data, total, page, page_size)
