from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from decimal import Decimal
from sqlalchemy.orm import Session

from core.database import get_bnpl_db, get_cbs_staging_db
from services.auto_debit_service import AutoDebitService
from services.fee_service import FeeService
from models.consumer import Consumer
from models.transaction import Transaction
from common.enums import TxnType, TxnCategory
from common.utils import generate_uuid
from common.exceptions import NotFoundError, BadRequestError
from routes.dependencies import get_current_admin

router = APIRouter(prefix="/repayments", tags=["Repayments"])


class ManualRepaymentRequest(BaseModel):
    consumer_id: str = Field(..., max_length=32)
    amount_lak: Decimal = Field(..., gt=0)


@router.post("/trigger-auto-debit", summary="Trigger auto-debit repayment batch")
def trigger_auto_debit(
    background_tasks: BackgroundTasks,
    admin: dict = Depends(get_current_admin),
    bnpl_db: Session = Depends(get_bnpl_db),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    service = AutoDebitService()
    result = service.process_daily_repayments(bnpl_db, cbs_db)
    return {"status": "COMPLETED", **result}


@router.post("/manual", summary="Record a manual consumer repayment")
def manual_repayment(
    req: ManualRepaymentRequest,
    admin: dict = Depends(get_current_admin),
    bnpl_db: Session = Depends(get_bnpl_db),
    cbs_db: Session = Depends(get_cbs_staging_db),
):
    consumer = bnpl_db.query(Consumer).filter(Consumer.consumer_id == req.consumer_id).first()
    if not consumer:
        raise NotFoundError(f"Consumer {req.consumer_id} not found")

    used_amount = (consumer.bnpl_limit_lak or 0) - (consumer.available_limit_lak or 0)
    if used_amount <= 0:
        raise BadRequestError("Consumer has no outstanding BNPL balance")

    repay_amount = min(req.amount_lak, used_amount)
    txn_id = f"MANREPAY-{generate_uuid()[:16]}"

    txn = Transaction(
        txn_id=txn_id,
        consumer_id=consumer.consumer_id,
        merchant_id=None,
        txn_type=TxnType.DEBIT,
        txn_category=TxnCategory.BNPL_REPAYMENT,
        amount_lak=repay_amount,
        status="REPAID",
    )
    bnpl_db.add(txn)

    from services.staging_service import StagingService
    staging_service = StagingService()
    staging_req = {
        "batch_id": datetime.utcnow().strftime("BNPL_%Y%m%d_%H"),
        "source_ref_no": txn_id,
        "source_timestamp": datetime.utcnow(),
        "txn_type": "DEBIT",
        "txn_category": "BNPL_REPAYMENT",
        "txn_code": "BNPL-REPAY-001",
        "txn_amount": float(repay_amount),
        "bnpl_extensions": {
            "bnpl_txn_category": "REPAYMENT",
            "bnpl_consumer_id": consumer.consumer_id,
        },
        "details": [
            {
                "detail_type": "PRINCIPAL",
                "detail_amount": float(repay_amount),
                "narrative_line1": f"Manual repayment for {consumer.consumer_id}",
            },
        ],
    }
    staging_service.write_transaction(staging_req, cbs_db)

    consumer.available_limit_lak = (consumer.available_limit_lak or 0) + repay_amount
    if consumer.available_limit_lak >= consumer.bnpl_limit_lak:
        FeeService().mark_repaid(consumer.consumer_id, bnpl_db)

    bnpl_db.commit()
    return {
        "txn_id": txn_id,
        "consumer_id": consumer.consumer_id,
        "amount_lak": float(repay_amount),
        "remaining_outstanding": float((consumer.bnpl_limit_lak or 0) - (consumer.available_limit_lak or 0)),
        "status": "REPAID",
    }
