from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_bnpl_db
from core.redis import get_redis
from models.consumer import Consumer
from models.merchant import Merchant
from schemas.auth import (
    AuthRequestSchema, AuthApprovedResponse, AuthDeclinedResponse,
    AuthConfirmRequest, AuthStatusResponse,
)
from services.auth_service import AuthService
from services.merchant_service import MerchantService
from services.consumer_service import ConsumerService
from common.exceptions import InsufficientLimitError
from routes.dependencies import get_api_merchant

router = APIRouter(prefix="/bnpl", tags=["Authorization"])


@router.post(
    "/auth",
    response_model=AuthApprovedResponse | AuthDeclinedResponse,
    summary="Real-time BNPL authorization",
    description="Authorize a BNPL transaction. Checks consumer limit, merchant status, and fraud rules.",
)
async def authorize(
    req: AuthRequestSchema,
    merchant: Merchant = Depends(get_api_merchant),
    db: Session = Depends(get_bnpl_db),
):
    consumer_service = ConsumerService()
    auth_service = AuthService()

    consumer = consumer_service.get_by_id(req.consumer_id, db)

    result = await auth_service.authorize(req, merchant, consumer, db)
    return result


@router.post("/auth/confirm", summary="Confirm an authorized transaction")
async def confirm_auth(
    req: AuthConfirmRequest,
    merchant: Merchant = Depends(get_api_merchant),
    db: Session = Depends(get_bnpl_db),
):
    auth_service = AuthService()
    result = await auth_service.confirm(req.auth_id, db)
    return result


@router.post("/auth/cancel", summary="Cancel an authorized transaction")
async def cancel_auth(
    req: AuthConfirmRequest,
    merchant: Merchant = Depends(get_api_merchant),
    db: Session = Depends(get_bnpl_db),
):
    auth_service = AuthService()
    result = await auth_service.cancel(req.auth_id, db)
    return result


@router.get("/auth/{auth_id}", summary="Get authorization status")
async def get_auth_status(
    auth_id: str,
    db: Session = Depends(get_bnpl_db),
):
    auth_service = AuthService()
    result = await auth_service.get_status(auth_id, db)
    return result
