from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from core.database import get_bnpl_db
from schemas.merchant import (
    MerchantOnboardRequest, MerchantOnboardResponse,
    MerchantDetailResponse, MerchantUpdateRequest,
)
from services.merchant_service import MerchantService
from common.utils import build_pagination_response
from routes.dependencies import get_current_admin
from models.merchant import MerchantDocument

router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.post("/onboard", response_model=MerchantOnboardResponse, status_code=201,
             summary="Onboard a new merchant")
def onboard_merchant(
    req: MerchantOnboardRequest,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    service = MerchantService()
    return service.onboard(req, db)


@router.get("/{merchant_id}", summary="Get merchant details")
def get_merchant(
    merchant_id: str,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    service = MerchantService()
    merchant = service.get_by_id(merchant_id, db)
    return MerchantDetailResponse(
        merchant_id=merchant.merchant_id,
        business_name=merchant.business_name,
        status=merchant.status,
        risk_tier=merchant.risk_tier,
        mdr_rate=merchant.mdr_rate,
        settlement_terms=merchant.settlement_terms,
        daily_limit_lak=merchant.daily_limit_lak,
        monthly_limit_lak=merchant.monthly_limit_lak,
        channels=merchant.channels.split(",") if merchant.channels else [],
        created_at=merchant.created_at,
    )


@router.get("", summary="List merchants")
def list_merchants(
    admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_bnpl_db),
):
    service = MerchantService()
    merchants, total = service.list_merchants(db, page, page_size, status)
    items = [
        MerchantDetailResponse(
            merchant_id=m.merchant_id,
            business_name=m.business_name,
            status=m.status,
            risk_tier=m.risk_tier,
            mdr_rate=m.mdr_rate,
            settlement_terms=m.settlement_terms,
            daily_limit_lak=m.daily_limit_lak,
            monthly_limit_lak=m.monthly_limit_lak,
            channels=m.channels.split(",") if m.channels else [],
            created_at=m.created_at,
        )
        for m in merchants
    ]
    return build_pagination_response(items, total, page, page_size)


@router.post("/{merchant_id}/documents", summary="Upload a merchant document")
def upload_document(
    merchant_id: str,
    file: UploadFile = File(...),
    document_type: str = Query(..., max_length=32),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    service = MerchantService()
    merchant = service.get_by_id(merchant_id, db)
    import uuid
    doc_url = f"/documents/{merchant_id}/{uuid.uuid4().hex}_{file.filename}"
    doc = MerchantDocument(
        merchant_id=merchant_id,
        document_type=document_type,
        document_url=doc_url,
        verified=False,
    )
    db.add(doc)
    db.commit()
    return {"document_id": doc.id, "document_url": doc_url, "document_type": document_type, "status": "uploaded"}


@router.get("/{merchant_id}/documents", summary="List merchant documents")
def list_documents(
    merchant_id: str,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    docs = db.query(MerchantDocument).filter(MerchantDocument.merchant_id == merchant_id).all()
    data = []
    for d in docs:
        data.append({
            "id": d.id,
            "document_type": d.document_type,
            "document_url": d.document_url,
            "verified": d.verified,
            "verified_at": d.verified_at.isoformat() if d.verified_at else None,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        })
    return {"data": data}


@router.patch("/{merchant_id}", summary="Update merchant details")
def update_merchant(
    merchant_id: str,
    req: MerchantUpdateRequest,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    service = MerchantService()
    updates = req.model_dump(exclude_none=True)
    merchant = service.update_merchant(merchant_id, updates, db)
    return MerchantDetailResponse(
        merchant_id=merchant.merchant_id,
        business_name=merchant.business_name,
        status=merchant.status,
        risk_tier=merchant.risk_tier,
        mdr_rate=merchant.mdr_rate,
        settlement_terms=merchant.settlement_terms,
        daily_limit_lak=merchant.daily_limit_lak,
        monthly_limit_lak=merchant.monthly_limit_lak,
        channels=merchant.channels.split(",") if merchant.channels else [],
        created_at=merchant.created_at,
    )
