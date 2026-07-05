from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy import desc
from sqlalchemy.orm import Session

from core.database import get_cbs_staging_db
from cbs_staging.models import STG_TXN_CONTROL
from schemas.eod import EODBatchStatusResponse, EODRunResponse, EODListResponse
from common.exceptions import NotFoundError
from routes.dependencies import get_current_admin
from tasks.eod_batch import EODBatchProcessor

router = APIRouter(prefix="/eod", tags=["EOD Batch"])


@router.get("/batches", response_model=EODListResponse, summary="List EOD batch runs")
def list_eod_batches(
    page: int = 1,
    page_size: int = 20,
    admin: dict = Depends(get_current_admin),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    query = cbs_db.query(STG_TXN_CONTROL).order_by(desc(STG_TXN_CONTROL.CONTROL_STATUS_TIMESTAMP))
    total = query.count()
    batches = query.offset((page - 1) * page_size).limit(page_size).all()
    data = []
    for b in batches:
        data.append(EODBatchStatusResponse(
            batch_id=b.BATCH_ID,
            control_status=b.CONTROL_STATUS,
            eod_batch_run_id=b.EOD_BATCH_RUN_ID,
            eod_start_timestamp=b.EOD_START_TIMESTAMP,
            eod_end_timestamp=b.EOD_END_TIMESTAMP,
            expected_record_count=b.EXPECTED_RECORD_COUNT or 0,
            actual_record_count=b.ACTUAL_RECORD_COUNT or 0,
            expected_total_amount=b.EXPECTED_TOTAL_AMOUNT or 0,
            actual_total_amount=b.ACTUAL_TOTAL_AMOUNT or 0,
            control_status_timestamp=b.CONTROL_STATUS_TIMESTAMP,
        ))
    return EODListResponse(
        data=data,
        pagination={"page": page, "page_size": page_size, "total": total, "total_pages": (total + page_size - 1) // page_size},
    )


@router.get("/batches/{batch_id}", response_model=EODBatchStatusResponse, summary="Get EOD batch details")
def get_eod_batch(
    batch_id: str,
    admin: dict = Depends(get_current_admin),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    b = cbs_db.query(STG_TXN_CONTROL).filter(STG_TXN_CONTROL.BATCH_ID == batch_id).first()
    if not b:
        raise NotFoundError("Batch not found")
    return EODBatchStatusResponse(
        batch_id=b.BATCH_ID,
        control_status=b.CONTROL_STATUS,
        eod_batch_run_id=b.EOD_BATCH_RUN_ID,
        eod_start_timestamp=b.EOD_START_TIMESTAMP,
        eod_end_timestamp=b.EOD_END_TIMESTAMP,
        expected_record_count=b.EXPECTED_RECORD_COUNT or 0,
        actual_record_count=b.ACTUAL_RECORD_COUNT or 0,
        expected_total_amount=b.EXPECTED_TOTAL_AMOUNT or 0,
        actual_total_amount=b.ACTUAL_TOTAL_AMOUNT or 0,
        control_status_timestamp=b.CONTROL_STATUS_TIMESTAMP,
    )


@router.post("/run", response_model=dict, summary="Trigger EOD batch processing")
def trigger_eod(
    background_tasks: BackgroundTasks,
    admin: dict = Depends(get_current_admin),
):
    processor = EODBatchProcessor()
    background_tasks.add_task(processor.process)
    return {"message": "EOD batch processing triggered", "status": "PENDING"}


@router.get("/status", response_model=dict, summary="Get EOD system status")
def eod_system_status(
    admin: dict = Depends(get_current_admin),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    in_progress = cbs_db.query(STG_TXN_CONTROL).filter(STG_TXN_CONTROL.CONTROL_STATUS == "IN_PROGRESS").count()
    pending = cbs_db.query(STG_TXN_CONTROL).filter(STG_TXN_CONTROL.CONTROL_STATUS == "READY_FOR_PICKUP").count()
    completed = cbs_db.query(STG_TXN_CONTROL).filter(STG_TXN_CONTROL.CONTROL_STATUS == "COMPLETED").count()
    failed = cbs_db.query(STG_TXN_CONTROL).filter(STG_TXN_CONTROL.CONTROL_STATUS == "FAILED").count()
    partial = cbs_db.query(STG_TXN_CONTROL).filter(STG_TXN_CONTROL.CONTROL_STATUS == "PARTIAL").count()
    return {
        "in_progress": in_progress,
        "pending": pending,
        "completed": completed,
        "failed": failed,
        "partial": partial,
    }
