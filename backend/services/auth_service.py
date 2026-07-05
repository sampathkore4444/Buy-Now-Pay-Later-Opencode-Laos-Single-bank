import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from core.config import settings
from core.redis import redis_client
from core.kafka import send_event
from models.transaction import AuthRequest
from models.merchant import Merchant
from models.consumer import Consumer
from schemas.auth import AuthRequestSchema, AuthApprovedResponse, AuthDeclinedResponse
from common.enums import AuthStatus, RiskTier, TxnCategory
from common.exceptions import InsufficientLimitError, NotFoundError, BadRequestError
from common.utils import generate_auth_code, utcnow


INITIATED_TIMEOUT_MINUTES = 5
PENDING_TIMEOUT_SECONDS = 10
AUTHED_TIMEOUT_MINUTES = 30


class AuthService:

    async def authorize(
        self, req: AuthRequestSchema, merchant: Merchant, consumer: Consumer, db: Session
    ) -> AuthApprovedResponse | AuthDeclinedResponse:
        now = utcnow()

        existing = db.query(AuthRequest).filter(AuthRequest.auth_id == req.auth_id).first()
        if existing:
            if existing.status in (AuthStatus.AUTHED, AuthStatus.CONFIRMED, AuthStatus.SETTLED):
                return self._result_from_existing(existing)
            if existing.status == AuthStatus.CANCELLED:
                raise BadRequestError(f"Auth {req.auth_id} was already cancelled")
            if existing.status == AuthStatus.FAILED:
                raise BadRequestError(f"Auth {req.auth_id} was already failed")
            if existing.status == AuthStatus.INITIATED:
                if now > existing.timeout_at:
                    existing.status = AuthStatus.CANCELLED
                    db.commit()
                    raise BadRequestError("INITIATED session expired (>5 min)")
                return await self._continue_from_initiated(existing, merchant, consumer, db)
            if existing.status == AuthStatus.PENDING:
                if now > existing.timeout_at:
                    existing.status = AuthStatus.FAILED
                    existing.reason_code = "PENDING_TIMEOUT"
                    db.commit()
                    raise BadRequestError("PENDING validation timed out (>10 sec)")
                return await self._continue_from_pending(existing, merchant, consumer, db)

        auth_code = generate_auth_code()
        settlement_date = (now + timedelta(days=1)).replace(hour=22, minute=0, second=0, microsecond=0)
        repayment_date = (now + timedelta(days=30)).replace(hour=6, minute=0, second=0, microsecond=0)

        auth_record = AuthRequest(
            auth_id=req.auth_id,
            auth_code=auth_code,
            consumer_id=req.consumer_id,
            merchant_id=req.merchant_id,
            amount_lak=req.amount_lak,
            currency=req.currency,
            txn_type=req.txn_type,
            channel=req.channel,
            device_fingerprint=req.device_fingerprint,
            gps_location=req.gps_location,
            status=AuthStatus.INITIATED,
            initiated_at=now,
            timeout_at=now + timedelta(minutes=INITIATED_TIMEOUT_MINUTES),
        )
        db.add(auth_record)
        db.commit()

        return await self._continue_from_initiated(auth_record, merchant, consumer, db)

    async def _continue_from_initiated(
        self, auth: AuthRequest, merchant: Merchant, consumer: Consumer, db: Session
    ) -> AuthApprovedResponse | AuthDeclinedResponse:
        now = utcnow()
        auth.status = AuthStatus.PENDING
        auth.pending_at = now
        auth.timeout_at = now + timedelta(seconds=PENDING_TIMEOUT_SECONDS)
        db.commit()

        return await self._continue_from_pending(auth, merchant, consumer, db)

    async def _continue_from_pending(
        self, auth: AuthRequest, merchant: Merchant, consumer: Consumer, db: Session
    ) -> AuthApprovedResponse | AuthDeclinedResponse:
        mdr_rate = merchant.mdr_rate or Decimal(str(settings.DEFAULT_MDR_RATE))
        merchant_settlement = auth.amount_lak * (Decimal("1") - mdr_rate)
        current_limit = consumer.available_limit_lak

        if current_limit < auth.amount_lak:
            return await self._decline(auth, "INSUFFICIENT_LIMIT",
                f"Available BNPL limit ({current_limit:,.0f} LAK) is less than "
                f"transaction amount ({auth.amount_lak:,.0f} LAK).", db)

        if merchant.status.name != "APPROVED":
            return await self._decline(auth, "MERCHANT_UNAVAILABLE",
                "Merchant is not active for BNPL transactions.", db)

        if not consumer.is_active:
            return await self._decline(auth, "CONSUMER_BLOCKED",
                "Consumer account is not active.", db)

        now = utcnow()
        auth.status = AuthStatus.AUTHED
        auth.approved_amount_lak = auth.amount_lak
        auth.remaining_limit_lak = current_limit - auth.amount_lak
        settlement_date = (now + timedelta(days=1)).replace(hour=22, minute=0, second=0, microsecond=0)
        repayment_date = (now + timedelta(days=30)).replace(hour=6, minute=0, second=0, microsecond=0)
        auth.settlement_date = settlement_date
        auth.repayment_date = repayment_date
        auth.mdr_rate = mdr_rate
        auth.merchant_settlement_lak = merchant_settlement
        auth.auth_timestamp = now
        auth.timeout_at = now + timedelta(minutes=AUTHED_TIMEOUT_MINUTES)
        db.commit()

        new_available = current_limit - auth.amount_lak
        consumer.available_limit_lak = new_available
        db.commit()

        await self._update_redis_limit(auth.consumer_id, new_available)
        await self._publish_event(auth.auth_id, "AUTHED", None)

        from common.constants import LATE_FEE_FLAT_LAK
        return AuthApprovedResponse(
            auth_id=auth.auth_id,
            status="AUTHED",
            auth_code=auth.auth_code,
            approved_amount_lak=auth.amount_lak,
            remaining_limit_lak=new_available,
            settlement_date=settlement_date,
            repayment_date=repayment_date,
            mdr_rate=mdr_rate,
            merchant_settlement_lak=merchant_settlement,
            timestamp=now,
            total_cost_due=auth.amount_lak,
            due_date_display=repayment_date.strftime("%d %b %Y") if repayment_date else "",
        )

    async def _decline(
        self, auth: AuthRequest, reason_code: str, message: str, db: Session
    ) -> AuthDeclinedResponse:
        auth.status = AuthStatus.FAILED
        auth.reason_code = reason_code
        auth.decline_reason = message
        db.commit()
        await self._publish_event(auth.auth_id, "DECLINED", reason_code)
        return AuthDeclinedResponse(
            auth_id=auth.auth_id,
            status="DECLINED",
            reason_code=reason_code,
            message=message,
        )

    def _result_from_existing(self, auth: AuthRequest) -> AuthApprovedResponse:
        now = utcnow()
        return AuthApprovedResponse(
            auth_id=auth.auth_id,
            status=auth.status.value,
            auth_code=auth.auth_code,
            approved_amount_lak=auth.approved_amount_lak,
            remaining_limit_lak=auth.remaining_limit_lak,
            settlement_date=auth.settlement_date,
            repayment_date=auth.repayment_date,
            mdr_rate=auth.mdr_rate,
            merchant_settlement_lak=auth.merchant_settlement_lak,
            timestamp=now,
            total_cost_due=auth.approved_amount_lak or 0,
            due_date_display=auth.repayment_date.strftime("%d %b %Y") if auth.repayment_date else "",
        )

    async def confirm(self, auth_id: str, db: Session) -> dict:
        auth = db.query(AuthRequest).filter(AuthRequest.auth_id == auth_id).first()
        if not auth:
            raise NotFoundError(f"Auth {auth_id} not found")

        if auth.status != AuthStatus.AUTHED:
            raise BadRequestError(f"Auth {auth_id} is in state {auth.status.value}, cannot confirm")

        if utcnow() > auth.timeout_at:
            auth.status = AuthStatus.CANCELLED
            db.commit()
            await self._release_limit(auth.consumer_id, auth.approved_amount_lak, db)
            raise BadRequestError("Auth session expired (30-min AUTHED timeout)")

        auth.status = AuthStatus.CONFIRMED
        auth.confirm_timestamp = utcnow()
        db.commit()

        await self._publish_event(auth_id, "CONFIRMED", None)
        return {"auth_id": auth_id, "status": "CONFIRMED"}

    async def cancel(self, auth_id: str, db: Session) -> dict:
        auth = db.query(AuthRequest).filter(AuthRequest.auth_id == auth_id).first()
        if not auth:
            raise NotFoundError(f"Auth {auth_id} not found")

        if auth.status not in (AuthStatus.AUTHED, AuthStatus.INITIATED, AuthStatus.PENDING):
            raise BadRequestError(f"Auth {auth_id} is in state {auth.status.value}, cannot cancel")

        auth.status = AuthStatus.CANCELLED
        db.commit()
        if auth.approved_amount_lak:
            await self._release_limit(auth.consumer_id, auth.approved_amount_lak, db)
        await self._publish_event(auth_id, "CANCELLED", None)
        return {"auth_id": auth_id, "status": "CANCELLED"}

    async def get_status(self, auth_id: str, db: Session) -> dict:
        auth = db.query(AuthRequest).filter(AuthRequest.auth_id == auth_id).first()
        if not auth:
            raise NotFoundError(f"Auth {auth_id} not found")
        return {
            "auth_id": auth.auth_id,
            "status": auth.status.value,
            "auth_code": auth.auth_code,
            "initiated_at": auth.initiated_at,
            "pending_at": auth.pending_at,
            "auth_timestamp": auth.auth_timestamp,
            "timeout_at": auth.timeout_at,
        }

    async def _record_auth(
        self, req: AuthRequestSchema, merchant: Merchant,
        consumer: Consumer, status: AuthStatus, db: Session
    ):
        now = utcnow()
        record = AuthRequest(
            auth_id=req.auth_id,
            consumer_id=req.consumer_id,
            merchant_id=req.merchant_id,
            amount_lak=req.amount_lak,
            currency=req.currency,
            txn_type=req.txn_type,
            channel=req.channel,
            device_fingerprint=req.device_fingerprint,
            gps_location=req.gps_location,
            status=status,
            initiated_at=now,
            auth_timestamp=now,
            timeout_at=now + timedelta(minutes=AUTHED_TIMEOUT_MINUTES),
        )
        db.add(record)
        db.commit()

    async def _release_limit(self, consumer_id: str, amount: Decimal, db: Session):
        consumer = db.query(Consumer).filter(Consumer.consumer_id == consumer_id).first()
        if consumer:
            consumer.available_limit_lak = (consumer.available_limit_lak or 0) + amount
            db.commit()
            await self._update_redis_limit(consumer_id, consumer.available_limit_lak)

    async def _update_redis_limit(self, consumer_id: str, available: Decimal):
        r = await redis_client
        key = f"{settings.REDIS_LIMIT_PREFIX}{consumer_id}"
        await r.hset(key, "available_limit_lak", str(available))

    async def _publish_event(self, auth_id: str, status: str, reason: str | None):
        event = {"auth_id": auth_id, "status": status, "timestamp": utcnow().isoformat()}
        if reason:
            event["reason_code"] = reason
        await send_event(
            settings.KAFKA_AUTH_TOPIC,
            key=auth_id,
            value=json.dumps(event).encode(),
        )
