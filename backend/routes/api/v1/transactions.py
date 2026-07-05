from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_bnpl_db
from services.transaction_service import TransactionService
from schemas.transaction import TransactionResponse
from schemas.common import PaginatedResponse
from common.utils import build_pagination_response, safe_endpoint
from routes.dependencies import get_current_admin

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _to_response(txn) -> TransactionResponse:
    return TransactionResponse(
        txn_id=txn.txn_id,
        correlation_id=txn.correlation_id,
        auth_id=txn.auth_id,
        consumer_id=txn.consumer_id,
        merchant_id=txn.merchant_id,
        txn_type=txn.txn_type.value if hasattr(txn.txn_type, "value") else txn.txn_type,
        txn_category=txn.txn_category.value if hasattr(txn.txn_category, "value") else txn.txn_category,
        amount_lak=txn.amount_lak,
        currency=txn.currency,
        mdr_rate=txn.mdr_rate,
        mdr_amount=txn.mdr_amount,
        net_settlement_amount=txn.net_settlement_amount,
        status=txn.status,
        staging_status=txn.staging_status,
        created_at=txn.created_at,
    )


@router.get("/{txn_id}", response_model=TransactionResponse, summary="Get transaction details")
@safe_endpoint
def get_transaction(
    txn_id: str,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    service = TransactionService()
    txn = service.get_by_id(txn_id, db)
    return _to_response(txn)


@router.get("", response_model=PaginatedResponse, summary="List transactions")
@safe_endpoint
def list_transactions(
    admin: dict = Depends(get_current_admin),
    merchant_id: str | None = Query(None),
    consumer_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_bnpl_db),
):
    service = TransactionService()
    if merchant_id:
        txns, total = service.list_by_merchant(merchant_id, db, page, page_size)
    elif consumer_id:
        txns, total = service.list_by_consumer(consumer_id, db, page, page_size)
    else:
        return {"data": [], "pagination": {"page": page, "page_size": page_size, "total": 0, "total_pages": 0}}
    items = [_to_response(t).model_dump() for t in txns]
    return build_pagination_response(items, total, page, page_size)
