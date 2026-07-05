from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_cbs_staging_db
from schemas.reconciliation import ReconcileBatchRequest, ReconcileBatchResponse, DailyReconcileReportResponse
from routes.dependencies import get_current_admin
from services.reconciliation_service import ReconciliationService
from common.utils import safe_endpoint

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


@router.post("/batch", response_model=ReconcileBatchResponse, summary="Reconcile a staging batch")
@safe_endpoint
def reconcile_batch(
    req: ReconcileBatchRequest,
    admin: dict = Depends(get_current_admin),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    srv = ReconciliationService()
    result = srv.reconcile_batch(req.batch_id, req.expected_count, req.expected_amount, cbs_db)
    return ReconcileBatchResponse(**result)


@router.get("/daily-report", response_model=DailyReconcileReportResponse, summary="Generate daily reconciliation report")
@safe_endpoint
def daily_report(
    report_date: str | None = None,
    admin: dict = Depends(get_current_admin),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    srv = ReconciliationService()
    result = srv.generate_daily_report(report_date or str(date.today()), cbs_db)
    return DailyReconcileReportResponse(**result)
