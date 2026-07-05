from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.database import get_bnpl_db, get_cbs_staging_db
from services.consumer_service import ConsumerService
from schemas.consumer import ConsumerLimitResponse
from routes.dependencies import get_current_admin
from models.consumer import Consumer

router = APIRouter(prefix="/consumers", tags=["Consumers"])


class ConsumerEnrollRequest(BaseModel):
    bank_customer_id: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    phone: str = Field(..., max_length=20)
    email: str | None = Field(None, max_length=128)


class ConsumerEnrollResponse(BaseModel):
    consumer_id: str
    bnpl_limit_lak: float = 0
    message: str = "BNPL enrollment successful"


@router.post("/enroll", response_model=ConsumerEnrollResponse, status_code=201,
             summary="Enroll a consumer for BNPL (one-time signup)")
def enroll_consumer(
    req: ConsumerEnrollRequest,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    service = ConsumerService()
    consumer = service.create_consumer(
        bank_customer_id=req.bank_customer_id,
        name=req.name,
        phone=req.phone,
        email=req.email,
        db=db,
    )
    return ConsumerEnrollResponse(
        consumer_id=consumer.consumer_id,
        bnpl_limit_lak=float(consumer.bnpl_limit_lak or 0),
    )


@router.get("", summary="List consumers (paginated)")
def list_consumers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    query = db.query(Consumer)
    if search:
        query = query.filter(
            Consumer.name.ilike(f"%{search}%") | Consumer.phone.ilike(f"%{search}%") | Consumer.consumer_id.ilike(f"%{search}%")
        )
    total = query.count()
    consumers = query.order_by(desc(Consumer.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    data = []
    for c in consumers:
        data.append({
            "consumer_id": c.consumer_id,
            "bank_customer_id": c.bank_customer_id,
            "name": c.name,
            "phone": c.phone,
            "email": c.email,
            "bnpl_limit_lak": float(c.bnpl_limit_lak or 0),
            "available_limit_lak": float(c.available_limit_lak or 0),
            "risk_tier": c.risk_tier,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return {
        "data": data,
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": (total + page_size - 1) // page_size},
    }


@router.get("/{consumer_id}/limit", summary="Get consumer BNPL limit")
def get_consumer_limit(
    consumer_id: str,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    service = ConsumerService()
    consumer = service.get_by_id(consumer_id, db)
    return ConsumerLimitResponse(
        consumer_id=consumer.consumer_id,
        bnpl_limit_lak=consumer.bnpl_limit_lak,
        available_limit_lak=consumer.available_limit_lak,
        limit_expiry=consumer.limit_expiry,
        risk_tier=consumer.risk_tier,
    )
