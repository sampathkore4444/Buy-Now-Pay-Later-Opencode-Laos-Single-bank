from datetime import timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from models.dispute import Dispute
from models.transaction import AuthRequest, Transaction
from models.consumer import Consumer
from common.enums import AuthStatus, TxnType, TxnCategory
from common.exceptions import NotFoundError, BadRequestError
from common.utils import generate_uuid, utcnow

COOLING_OFF_DAYS = 3
COOLING_OFF_THRESHOLD_LAK = Decimal("1000000")


class DisputeService:

    def initiate_dispute(
        self, consumer_id: str, auth_id: str, reason: str,
        description: str | None, db: Session,
    ) -> dict:
        auth = db.query(AuthRequest).filter(
            AuthRequest.auth_id == auth_id,
            AuthRequest.consumer_id == consumer_id,
        ).first()
        if not auth:
            raise NotFoundError(f"Auth {auth_id} not found for consumer {consumer_id}")
        if auth.status not in (AuthStatus.CONFIRMED, AuthStatus.SETTLED):
            raise BadRequestError(f"Auth {auth_id} is in state {auth.status.value}, cannot dispute")

        dispute = Dispute(
            dispute_id=f"DSP-{generate_uuid()[:16]}",
            consumer_id=consumer_id,
            auth_id=auth_id,
            reason=reason,
            description=description,
            amount_lak=auth.approved_amount_lak or 0,
            status="OPEN",
            is_cooling_off=False,
        )
        db.add(dispute)
        db.commit()
        db.refresh(dispute)

        return {
            "dispute_id": dispute.dispute_id,
            "status": dispute.status,
            "message": "Dispute registered. Investigation will be completed within 7 days.",
        }

    def check_cooling_off(self, auth_id: str, consumer_id: str, db: Session) -> dict:
        auth = db.query(AuthRequest).filter(
            AuthRequest.auth_id == auth_id,
            AuthRequest.consumer_id == consumer_id,
        ).first()
        if not auth:
            raise NotFoundError(f"Auth {auth_id} not found")

        amount = auth.approved_amount_lak or 0
        if amount < COOLING_OFF_THRESHOLD_LAK:
            return {"eligible": False, "reason": "Transaction below cooling-off threshold (1,000,000 LAK)"}

        if auth.status != AuthStatus.CONFIRMED:
            return {"eligible": False, "reason": f"Auth is in state {auth.status.value}, must be CONFIRMED"}

        days_since = (utcnow() - auth.confirm_timestamp).days if auth.confirm_timestamp else 0
        if days_since > COOLING_OFF_DAYS:
            return {"eligible": False, "reason": f"Cooling-off period of {COOLING_OFF_DAYS} days has expired"}

        expiry = auth.confirm_timestamp + timedelta(days=COOLING_OFF_DAYS) if auth.confirm_timestamp else utcnow()

        return {
            "eligible": True,
            "cooling_off_expiry": expiry.isoformat() if expiry else None,
            "days_remaining": max(0, COOLING_OFF_DAYS - days_since),
            "amount_lak": float(amount),
        }

    def cancel_under_cooling_off(
        self, auth_id: str, consumer_id: str, db: Session,
    ) -> dict:
        result = self.check_cooling_off(auth_id, consumer_id, db)
        if not result["eligible"]:
            raise BadRequestError(result["reason"])

        auth = db.query(AuthRequest).filter(
            AuthRequest.auth_id == auth_id,
            AuthRequest.consumer_id == consumer_id,
        ).first()

        auth.status = AuthStatus.CANCELLED
        consumer = db.query(Consumer).filter(Consumer.consumer_id == consumer_id).first()
        if consumer and auth.approved_amount_lak:
            consumer.available_limit_lak = (consumer.available_limit_lak or 0) + auth.approved_amount_lak

        dispute = Dispute(
            dispute_id=f"DSP-{generate_uuid()[:16]}",
            consumer_id=consumer_id,
            auth_id=auth_id,
            reason="COOLING_OFF_CANCELLATION",
            description="Consumer-initiated cancellation under 3-day cooling-off period",
            amount_lak=auth.approved_amount_lak or 0,
            status="RESOLVED",
            resolution="REFUNDED",
            resolved_at=utcnow(),
            is_cooling_off=True,
            cooling_off_expiry=auth.confirm_timestamp + timedelta(days=COOLING_OFF_DAYS) if auth.confirm_timestamp else None,
        )
        db.add(dispute)
        db.commit()

        return {
            "auth_id": auth_id,
            "status": "CANCELLED",
            "message": "Transaction cancelled under cooling-off period. Limit restored.",
        }

    def resolve_dispute(self, dispute_id: str, resolution: str, notes: str | None, db: Session) -> dict:
        dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
        if not dispute:
            raise NotFoundError(f"Dispute {dispute_id} not found")

        dispute.status = "RESOLVED"
        dispute.resolution = resolution
        dispute.resolved_at = utcnow()
        if notes:
            dispute.investigation_notes = notes
        db.commit()

        return {
            "dispute_id": dispute_id,
            "status": "RESOLVED",
            "resolution": resolution,
        }

    def list_by_consumer(self, consumer_id: str, db: Session) -> list[dict]:
        disputes = db.query(Dispute).filter(
            Dispute.consumer_id == consumer_id,
        ).order_by(Dispute.created_at.desc()).all()
        return [
            {
                "dispute_id": d.dispute_id,
                "auth_id": d.auth_id,
                "reason": d.reason,
                "status": d.status,
                "resolution": d.resolution,
                "created_at": d.created_at.isoformat(),
            }
            for d in disputes
        ]

    def get_open_count(self, db: Session) -> int:
        return db.query(Dispute).filter(Dispute.status == "OPEN").count()
