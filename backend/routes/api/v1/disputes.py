from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_bnpl_db
from schemas.dispute import (
    DisputeInitiateRequest, DisputeInitiateResponse,
    CoolingOffCheckResponse, CoolingOffCancelResponse,
    DisputeResolveRequest, DisputeResponse,
)
from services.dispute_service import DisputeService
from routes.dependencies import get_current_admin

router = APIRouter(prefix="/disputes", tags=["Disputes"])


@router.post("/initiate", response_model=DisputeInitiateResponse, status_code=201, summary="Register a dispute")
def initiate_dispute(
    req: DisputeInitiateRequest,
    db: Session = Depends(get_bnpl_db),
):
    service = DisputeService()
    return service.initiate_dispute(req.consumer_id, req.auth_id, req.reason, req.description, db)


@router.get("/cooling-off/{consumer_id}/{auth_id}", response_model=CoolingOffCheckResponse,
            summary="Check cooling-off eligibility")
def check_cooling_off(
    consumer_id: str, auth_id: str,
    db: Session = Depends(get_bnpl_db),
):
    service = DisputeService()
    return service.check_cooling_off(auth_id, consumer_id, db)


@router.post("/cooling-off/cancel", response_model=CoolingOffCancelResponse, status_code=201,
             summary="Cancel transaction under cooling-off period")
def cancel_cooling_off(
    consumer_id: str, auth_id: str,
    db: Session = Depends(get_bnpl_db),
):
    service = DisputeService()
    return service.cancel_under_cooling_off(auth_id, consumer_id, db)


@router.post("/{dispute_id}/resolve", response_model=DisputeResponse, summary="Resolve a dispute (admin)")
def resolve_dispute(
    dispute_id: str,
    req: DisputeResolveRequest,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    service = DisputeService()
    return service.resolve_dispute(dispute_id, req.resolution, req.notes, db)


@router.get("/consumer/{consumer_id}", response_model=list[DisputeResponse],
            summary="List disputes for a consumer")
def list_consumer_disputes(
    consumer_id: str,
    db: Session = Depends(get_bnpl_db),
):
    service = DisputeService()
    return service.list_by_consumer(consumer_id, db)
