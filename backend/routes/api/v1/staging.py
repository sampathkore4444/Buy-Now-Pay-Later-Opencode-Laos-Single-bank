from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_cbs_staging_db
from cbs_staging.models import STG_TXN_CONTROL
from services.staging_service import StagingService
from schemas.staging import StagingTransactionRequest, StagingTransactionResponse
from common.exceptions import NotFoundError
from common.utils import safe_endpoint
from routes.dependencies import get_current_admin

router = APIRouter(prefix="/staging", tags=["Staging"])


@router.post("/transactions", response_model=StagingTransactionResponse, status_code=201,
             summary="Write a transaction to CBS INT_STG staging tables")
@safe_endpoint
def write_staging_transaction(
    req: StagingTransactionRequest,
    admin: dict = Depends(get_current_admin),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    service = StagingService()
    result = service.write_transaction(req.model_dump(), cbs_db)
    return StagingTransactionResponse(**result)


@router.get("/transactions/{correlation_id}", response_model=dict, summary="Get staging transaction status")
@safe_endpoint
def get_staging_status(
    correlation_id: str,
    admin: dict = Depends(get_current_admin),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    service = StagingService()
    return service.get_status(correlation_id, cbs_db)


class FinalizeBatchRequest(BaseModel):
    batch_id: str = Field(..., max_length=64)


@router.post("/batches/{batch_id}/finalize", response_model=dict, summary="Finalize a staging batch (OPEN\u2192READY_FOR_PICKUP)")
@safe_endpoint
def finalize_batch(
    batch_id: str,
    admin: dict = Depends(get_current_admin),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    service = StagingService()
    control = cbs_db.query(STG_TXN_CONTROL).filter(STG_TXN_CONTROL.BATCH_ID == batch_id).first()
    if not control:
        raise NotFoundError(f"Batch {batch_id} not found")
    service.finalize_batch(batch_id, cbs_db)
    return {
        "batch_id": batch_id,
        "control_status": "READY_FOR_PICKUP",
        "expected_record_count": control.EXPECTED_RECORD_COUNT,
        "expected_total_amount": float(control.EXPECTED_TOTAL_AMOUNT or 0),
        "message": "Batch finalized and ready for EOD pickup",
    }
