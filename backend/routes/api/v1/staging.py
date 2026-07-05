from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_cbs_staging_db
from services.staging_service import StagingService
from schemas.staging import StagingTransactionRequest, StagingTransactionResponse
from routes.dependencies import get_current_admin

router = APIRouter(prefix="/staging", tags=["Staging"])


@router.post("/transactions", response_model=StagingTransactionResponse, status_code=201,
             summary="Write a transaction to CBS INT_STG staging tables")
def write_staging_transaction(
    req: StagingTransactionRequest,
    admin: dict = Depends(get_current_admin),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    service = StagingService()
    result = service.write_transaction(req.model_dump(), cbs_db)
    return StagingTransactionResponse(**result)


@router.get("/transactions/{correlation_id}", summary="Get staging transaction status")
def get_staging_status(
    correlation_id: str,
    admin: dict = Depends(get_current_admin),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    service = StagingService()
    return service.get_status(correlation_id, cbs_db)
