import json
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from core.config import settings
from core.kafka import send_event
from cbs_staging.models import (
    STG_TXN_HEADER,
    STG_TXN_DETAIL,
    STG_TXN_CONTROL,
    STG_ERROR_LOG,
    STG_AUDIT_TRAIL,
)
from common.exceptions import ConflictError, BadRequestError
from common.utils import generate_correlation_id, utcnow


class CircuitBreaker:
    _open_until: datetime | None = None
    _failure_count: int = 0
    _threshold: int = 5
    _timeout_minutes: int = 10

    def is_open(self) -> bool:
        if self._open_until and utcnow() < self._open_until:
            return True
        if self._open_until:
            self._open_until = None
            self._failure_count = 0
        return False

    def record_failure(self):
        self._failure_count += 1
        if self._failure_count >= self._threshold:
            self._open_until = utcnow() + timedelta(minutes=self._timeout_minutes)

    def record_success(self):
        if self._failure_count > 0:
            self._failure_count -= 1


staging_circuit_breaker = CircuitBreaker()


class StagingService:

    def write_transaction(self, req: dict, cbs_db: Session) -> dict:
        if staging_circuit_breaker.is_open():
            from common.exceptions import ServiceUnavailableError
            raise ServiceUnavailableError(
                "CBS staging circuit breaker is open. Retry after 10 minutes."
            )

        source_ref_no = req.get("source_ref_no")
        existing = cbs_db.query(STG_TXN_HEADER).filter(
            STG_TXN_HEADER.SOURCE_REF_NO == source_ref_no
        ).first()

        if existing:
            if existing.STG_STATUS in ("POSTED", "PICKED"):
                return self._build_response(existing)
            if existing.STG_STATUS in ("PENDING", "HELD"):
                raise ConflictError(
                    f"Record {source_ref_no} already exists with status {existing.STG_STATUS}"
                )
            if existing.RETRY_COUNT < existing.MAX_RETRIES:
                existing.RETRY_COUNT += 1
                existing.STG_STATUS = "PENDING"
                cbs_db.commit()
            else:
                raise BadRequestError(
                    f"Record {source_ref_no} has exceeded max retries"
                )

        if req.get("txn_amount", 0) <= 0:
            raise BadRequestError("ERR-ZERO-001: Zero-amount transactions not allowed")

        correlation_id = generate_correlation_id()
        batch_id = req.get("batch_id") or f"BNPL_{utcnow().strftime('%Y%m%d_%H')}"
        ext = req.get("bnpl_extensions") or {}
        details = req.get("details") or []

        try:
            header = STG_TXN_HEADER(
                CORRELATION_ID=correlation_id,
                BATCH_ID=batch_id,
                SOURCE_REF_NO=source_ref_no,
                SOURCE_TIMESTAMP=req.get("source_timestamp", utcnow()),
                TXN_TYPE=req.get("txn_type"),
                TXN_CATEGORY=req.get("txn_category"),
                TXN_CODE=req.get("txn_code"),
                TXN_CURRENCY=req.get("txn_currency", "LAK"),
                TXN_AMOUNT=Decimal(str(req.get("txn_amount", 0))),
                DEBIT_ACCOUNT_NO=req.get("debit_account_no"),
                CREDIT_ACCOUNT_NO=req.get("credit_account_no"),
                BNPL_TXN_CATEGORY=ext.get("bnpl_txn_category"),
                BNPL_MERCHANT_ID=ext.get("bnpl_merchant_id"),
                BNPL_CONSUMER_ID=ext.get("bnpl_consumer_id"),
                BNPL_AUTH_ID=ext.get("bnpl_auth_id"),
                MDR_RATE=Decimal(str(ext.get("mdr_rate", 0))) if ext.get("mdr_rate") else None,
                MDR_AMOUNT=Decimal(str(ext.get("mdr_amount", 0))) if ext.get("mdr_amount") else None,
                NET_SETTLEMENT_AMOUNT=Decimal(str(ext.get("net_settlement_amount", 0)))
                if ext.get("net_settlement_amount") else None,
            )
            cbs_db.add(header)
            cbs_db.flush()

            for i, d in enumerate(details):
                detail = STG_TXN_DETAIL(
                    STG_HEADER_ID=header.STG_HEADER_ID,
                    LINE_NO=i + 1,
                    DETAIL_TYPE=d.get("detail_type"),
                    DETAIL_AMOUNT=Decimal(str(d.get("detail_amount", 0))),
                    NARRATIVE_LINE1=d.get("narrative_line1"),
                    GL_ACCOUNT_CODE=d.get("gl_account_code"),
                )
                cbs_db.add(detail)

            self._upsert_control(batch_id, req, cbs_db)

            audit = STG_AUDIT_TRAIL(
                OPERATION="INSERT",
                TABLE_NAME="STG_TXN_HEADER",
                RECORD_ID=header.STG_HEADER_ID,
                USER_ID="BNPL_INTEGRATION",
                TIMESTAMP=utcnow(),
            )
            cbs_db.add(audit)
            cbs_db.commit()

            staging_circuit_breaker.record_success()

            return {
                "correlation_id": correlation_id,
                "stg_header_id": header.STG_HEADER_ID,
                "status": "PENDING",
                "staging_timestamp": utcnow(),
                "estimated_eod_window": self._next_eod_window(),
            }

        except Exception as e:
            cbs_db.rollback()
            staging_circuit_breaker.record_failure()
            raise

    def _upsert_control(self, batch_id: str, req: dict, cbs_db: Session):
        control = cbs_db.query(STG_TXN_CONTROL).filter(
            STG_TXN_CONTROL.BATCH_ID == batch_id
        ).with_for_update().first()

        if not control:
            total_amount = Decimal(str(req.get("txn_amount", 0)))
            control = STG_TXN_CONTROL(
                BATCH_ID=batch_id,
                EXPECTED_RECORD_COUNT=1,
                EXPECTED_TOTAL_AMOUNT=total_amount,
                CONTROL_STATUS="READY_FOR_PICKUP",
            )
            cbs_db.add(control)
        else:
            control.EXPECTED_RECORD_COUNT = (control.EXPECTED_RECORD_COUNT or 0) + 1
            control.EXPECTED_TOTAL_AMOUNT = (
                control.EXPECTED_TOTAL_AMOUNT or Decimal("0")
            ) + Decimal(str(req.get("txn_amount", 0)))
            control.CONTROL_STATUS = "READY_FOR_PICKUP"
            control.CONTROL_STATUS_TIMESTAMP = utcnow()

    def finalize_batch(self, batch_id: str, cbs_db: Session):
        control = cbs_db.query(STG_TXN_CONTROL).filter(
            STG_TXN_CONTROL.BATCH_ID == batch_id
        ).first()
        if control:
            control.CONTROL_STATUS = "READY_FOR_PICKUP"
            control.CONTROL_STATUS_TIMESTAMP = utcnow()
            cbs_db.commit()

    def get_status(self, correlation_id: str, cbs_db: Session) -> dict:
        header = cbs_db.query(STG_TXN_HEADER).filter(
            STG_TXN_HEADER.CORRELATION_ID == correlation_id
        ).first()
        if not header:
            from common.exceptions import NotFoundError
            raise NotFoundError(f"Staging record {correlation_id} not found")
        return {
            "correlation_id": header.CORRELATION_ID,
            "status": header.STG_STATUS,
            "retry_count": header.RETRY_COUNT,
            "eod_batch_run_id": header.EOD_BATCH_RUN_ID,
            "eod_posting_timestamp": header.EOD_POSTING_TIMESTAMP,
            "eod_failure_reason": header.EOD_FAILURE_REASON,
        }

    def retry_failed(self, correlation_id: str, cbs_db: Session):
        header = cbs_db.query(STG_TXN_HEADER).filter(
            STG_TXN_HEADER.CORRELATION_ID == correlation_id
        ).first()
        if not header:
            return
        if header.RETRY_COUNT < header.MAX_RETRIES:
            header.RETRY_COUNT = (header.RETRY_COUNT or 0) + 1
            header.STG_STATUS = "PENDING"
            cbs_db.commit()

    def _build_response(self, header: STG_TXN_HEADER) -> dict:
        return {
            "correlation_id": header.CORRELATION_ID,
            "stg_header_id": header.STG_HEADER_ID,
            "status": header.STG_STATUS,
            "staging_timestamp": header.CREATED_TIMESTAMP,
            "estimated_eod_window": self._next_eod_window(),
        }

    def _next_eod_window(self) -> datetime:
        now = utcnow()
        eod_time = now.replace(hour=22, minute=0, second=0, microsecond=0)
        if now >= eod_time:
            eod_time += timedelta(days=1)
        return eod_time
