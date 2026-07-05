import json
import logging

import httpx
from aiokafka import AIOKafkaConsumer

from core.config import settings

logger = logging.getLogger(__name__)

SMS_API_TIMEOUT = 10.0


class NotificationConsumer:

    async def consume(self):
        consumer = AIOKafkaConsumer(
            settings.KAFKA_NOTIFICATION_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP,
            value_deserializer=lambda v: json.loads(v.decode()),
        )
        await consumer.start()
        logger.info("Notification consumer started")
        try:
            async for msg in consumer:
                event = msg.value
                try:
                    await self._send_notification(event)
                except Exception as e:
                    logger.error("Failed to send notification %s: %s", event.get("notification_id"), e)
        finally:
            await consumer.stop()

    async def _send_notification(self, event: dict):
        notification_id = event.get("notification_id")
        recipient = event.get("recipient")
        message = event.get("message")
        channel = event.get("channel", "SMS")

        if not recipient or not message:
            logger.warning("Notification %s missing recipient or message", notification_id)
            return

        if channel == "SMS":
            await self._send_sms(notification_id, recipient, message)
        else:
            logger.warning("Unknown notification channel: %s", channel)

    async def _send_sms(self, notification_id: str, phone: str, message: str):
        api_url = settings.SMS_API_URL
        api_key = settings.SMS_API_KEY

        if not api_url:
            logger.info("[MOCK SMS] To: %s | Message: %s", phone, message)
            return

        payload = {
            "to": phone,
            "message": message,
            "sender": "BNPL-Bank",
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=SMS_API_TIMEOUT) as client:
                response = await client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
            logger.info("SMS %s sent to %s successfully", notification_id, phone)
        except httpx.RequestError as e:
            logger.error("SMS API request failed for %s: %s", notification_id, e)
            raise
        except httpx.HTTPStatusError as e:
            logger.error("SMS API returned error for %s: %d %s", notification_id, e.response.status_code, e.response.text)
            raise
