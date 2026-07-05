import asyncio
import json
import logging
from typing import Any

import httpx

from core.config import settings
from core.kafka import send_event
from common.utils import generate_uuid, utcnow

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_DELAY_SECONDS = 2.0
TIMEOUT_SECONDS = 10.0


class WebhookDeliveryService:

    async def deliver(self, webhook_url: str, event_type: str, payload: dict) -> dict:
        delivery_id = f"WH-{generate_uuid()[:16]}"
        body = {
            "event": event_type,
            "delivery_id": delivery_id,
            "timestamp": utcnow().isoformat(),
            "data": payload,
        }

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                    response = await client.post(webhook_url, json=body)
                    response.raise_for_status()
                logger.info("Webhook %s delivered to %s on attempt %d", delivery_id, webhook_url, attempt)
                await self._publish_event(delivery_id, event_type, "DELIVERED", attempt)
                return {"delivery_id": delivery_id, "status": "DELIVERED", "attempt": attempt}

            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_error = str(e)
                logger.warning("Webhook %s attempt %d/%d failed: %s", delivery_id, attempt, MAX_RETRIES, last_error)
                if attempt < MAX_RETRIES:
                    delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)

        logger.error("Webhook %s failed after %d attempts: %s", delivery_id, MAX_RETRIES, last_error)
        await self._publish_event(delivery_id, event_type, "FAILED", MAX_RETRIES)
        return {"delivery_id": delivery_id, "status": "FAILED", "attempt": MAX_RETRIES, "error": last_error}

    async def deliver_auth_result(self, webhook_url: str, auth_id: str, status: str, details: dict):
        return await self.deliver(webhook_url, "auth.result", {
            "auth_id": auth_id,
            "status": status,
            **details,
        })

    async def deliver_settlement(self, webhook_url: str, batch_id: str, amount: float, txn_count: int):
        return await self.deliver(webhook_url, "settlement.completed", {
            "batch_id": batch_id,
            "amount_lak": amount,
            "transaction_count": txn_count,
        })

    async def _publish_event(self, delivery_id: str, event_type: str, status: str, attempt: int):
        event = {
            "delivery_id": delivery_id,
            "event_type": event_type,
            "status": status,
            "attempt": attempt,
            "timestamp": utcnow().isoformat(),
        }
        try:
            await send_event(
                "bnpl-webhook-delivery",
                key=delivery_id,
                value=json.dumps(event).encode(),
            )
        except Exception as e:
            logger.warning("Failed to publish webhook delivery event: %s", e)
