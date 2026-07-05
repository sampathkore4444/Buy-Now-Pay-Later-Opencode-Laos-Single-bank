from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from decimal import Decimal
from sqlalchemy.orm import Session

from core.database import get_bnpl_db, get_cbs_staging_db
from models.merchant import Merchant
from services.refund_service import RefundService
from routes.dependencies import get_api_merchant
from common.utils import safe_endpoint

router = APIRouter(prefix="/refunds", tags=["Refunds"])


class RefundRequest(BaseModel):
    auth_id: str = Field(..., max_length=64)
    amount_lak: Decimal | None = Field(None, gt=0)


class RefundResponse(BaseModel):
    correlation_id: str
    stg_header_id: int
    status: str = "PENDING"


@router.post("", response_model=RefundResponse, status_code=201,
             summary="Initiate a refund for a settled BNPL transaction")
@safe_endpoint
def initiate_refund(
    req: RefundRequest,
    merchant: Merchant = Depends(get_api_merchant),
    bnpl_db: Session = Depends(get_bnpl_db),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    service = RefundService()
    result = service.initiate_refund(
        auth_id=req.auth_id,
        merchant_id=merchant.merchant_id,
        amount=req.amount_lak,
        bnpl_db=bnpl_db,
        cbs_db=cbs_db,
    )
    return RefundResponse(
        correlation_id=result["correlation_id"],
        stg_header_id=result["stg_header_id"],
        status=result["status"],
    )
