from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.database import get_bnpl_db
from models.settlement import Settlement
from schemas.settlement import SettlementResponse, SettlementListResponse
from routes.dependencies import get_current_admin
from services.settlement_service import SettlementService

router = APIRouter(prefix="/settlements", tags=["Settlements"])


@router.get("", summary="List settlements (paginated)")
def list_settlements(
    merchant_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    query = db.query(Settlement)
    if merchant_id:
        query = query.filter(Settlement.merchant_id == merchant_id)
    total = query.count()
    settlements = query.order_by(desc(Settlement.settlement_date)).offset((page - 1) * page_size).limit(page_size).all()
    return SettlementListResponse(
        data=[SettlementResponse.model_validate(s) for s in settlements],
        pagination={"page": page, "page_size": page_size, "total": total, "total_pages": (total + page_size - 1) // page_size},
    )


@router.get("/{settlement_id}", summary="Get settlement details")
def get_settlement(
    settlement_id: str,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    settlement = db.query(Settlement).filter(Settlement.settlement_id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    return SettlementResponse.model_validate(settlement)


@router.post("/{merchant_id}/create-daily", summary="Create daily settlement for a merchant")
def create_daily_settlement(
    merchant_id: str,
    settlement_date: str | None = None,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    from datetime import date
    srv = SettlementService()
    s = srv.create_daily_settlement(
        merchant_id=merchant_id,
        settlement_date=date.fromisoformat(settlement_date) if settlement_date else date.today(),
        db=db,
    )
    return SettlementResponse.model_validate(s)
