from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from core.config import settings
from core.redis import redis_client
from models.consumer import Consumer
from common.exceptions import NotFoundError


class CreditService:

    async def get_limit(self, consumer_id: str, db: Session) -> dict:
        consumer = db.query(Consumer).filter(Consumer.consumer_id == consumer_id).first()
        if not consumer:
            raise NotFoundError(f"Consumer {consumer_id} not found")
        return {
            "consumer_id": consumer.consumer_id,
            "bnpl_limit_lak": consumer.bnpl_limit_lak,
            "available_limit_lak": consumer.available_limit_lak,
            "currency": "LAK",
            "limit_expiry": consumer.limit_expiry,
            "risk_tier": consumer.risk_tier,
        }

    async def refresh_limits_from_redis(self, db: Session):
        r = await redis_client
        cursor = 0
        pattern = f"{settings.REDIS_LIMIT_PREFIX}*"
        while True:
            cursor, keys = await r.scan(cursor=cursor, match=pattern, count=100)
            for key in keys:
                consumer_id = key.replace(settings.REDIS_LIMIT_PREFIX, "")
                data = await r.hgetall(key)
                if data:
                    consumer = db.query(Consumer).filter(Consumer.consumer_id == consumer_id).first()
                    if consumer:
                        consumer.available_limit_lak = Decimal(str(data.get("available_limit_lak", "0")))
            if cursor == 0:
                break
        db.commit()

    async def preload_limit_to_redis(self, consumer: Consumer):
        r = await redis_client
        key = f"{settings.REDIS_LIMIT_PREFIX}{consumer.consumer_id}"
        await r.hset(key, mapping={
            "consumer_id": consumer.consumer_id,
            "bnpl_limit_lak": str(consumer.bnpl_limit_lak),
            "available_limit_lak": str(consumer.available_limit_lak),
            "currency": "LAK",
            "risk_tier": consumer.risk_tier,
        })
        await r.expire(key, settings.REDIS_DEFAULT_TTL_SECONDS)

    def calculate_bnpl_limit(self, monthly_income: Decimal, existing_obligations: Decimal,
                             credit_score: int) -> Decimal:
        base = monthly_income * Decimal("0.3")
        debt_factor = Decimal("1") - (existing_obligations / max(monthly_income, Decimal("1")))
        score_factor = Decimal(str(min(credit_score, 850))) / Decimal("850")
        limit = base * debt_factor * score_factor
        return max(limit, Decimal("0")).quantize(Decimal("0.01"))
