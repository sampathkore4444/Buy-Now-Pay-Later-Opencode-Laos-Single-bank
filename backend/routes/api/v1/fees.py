from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy import desc
from sqlalchemy.orm import Session

from core.database import get_bnpl_db, get_cbs_staging_db
from models.overdue import OverdueTracker
from services.fee_service import FeeService
from routes.dependencies import get_current_admin

router = APIRouter(prefix="/fees", tags=["Fees & Overdue"])


@router.get("/overdue", summary="List overdue trackers (paginated)")
def list_overdue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    query = db.query(OverdueTracker)
    if status:
        query = query.filter(OverdueTracker.status == status)
    total = query.count()
    trackers = query.order_by(desc(OverdueTracker.days_overdue)).offset((page - 1) * page_size).limit(page_size).all()
    data = []
    for t in trackers:
        data.append({
            "consumer_id": t.consumer_id,
            "auth_id": t.auth_id,
            "overdue_date": t.overdue_date.isoformat() if t.overdue_date else None,
            "days_overdue": t.days_overdue,
            "overdue_amount_lak": float(t.overdue_amount_lak or 0),
            "late_fee_charged": float(t.late_fee_charged or 0),
            "interest_charged": float(t.interest_charged or 0),
            "late_fee_count": t.late_fee_count,
            "status": t.status,
            "last_fee_assessment": t.last_fee_assessment.isoformat() if t.last_fee_assessment else None,
            "last_interest_assessment": t.last_interest_assessment.isoformat() if t.last_interest_assessment else None,
        })
    return {
        "data": data,
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": (total + page_size - 1) // page_size},
    }


@router.get("/overdue/{consumer_id}", summary="Get consumer overdue details")
def get_consumer_overdue(
    consumer_id: str,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    service = FeeService()
    result = service.get_consumer_overdue(consumer_id, db)
    if not result:
        return {"consumer_id": consumer_id, "overdue": False, "message": "No active overdue record"}
    result["overdue"] = True
    return result


@router.post("/assess-late-fees", summary="Trigger late fee assessment batch")
def assess_late_fees(
    background_tasks: BackgroundTasks,
    admin: dict = Depends(get_current_admin),
    bnpl_db: Session = Depends(get_bnpl_db),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    service = FeeService()
    result = service.assess_late_fees(bnpl_db, cbs_db)
    return {"status": "COMPLETED", **result}


@router.post("/assess-interest", summary="Trigger interest assessment batch")
def assess_interest(
    background_tasks: BackgroundTasks,
    admin: dict = Depends(get_current_admin),
    bnpl_db: Session = Depends(get_bnpl_db),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    service = FeeService()
    result = service.assess_interest(bnpl_db, cbs_db)
    return {"status": "COMPLETED", **result}
