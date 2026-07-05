import json
import logging

from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_cbs_staging_db
from services.staging_service import StagingService
from common.enums import StagingStatus

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class StagingEventConsumer:

    async def consume(self):
        consumer = AIOKafkaConsumer(
            settings.KAFKA_STAGING_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP,
            value_deserializer=lambda v: json.loads(v.decode()),
        )
        await consumer.start()
        logger.info("Staging event consumer started")
        try:
            async for msg in consumer:
                event = msg.value
                correlation_id = event.get("correlation_id")
                status = event.get("status")
                try:
                    await self._process_event(correlation_id, status, event)
                except Exception as e:
                    logger.error("Failed to process staging event for %s: %s", correlation_id, e)
        finally:
            await consumer.stop()

    async def _process_event(self, correlation_id: str, status: str, event: dict):
        if status == "WRITTEN":
            logger.info("Staging record %s written successfully", correlation_id)
        elif status == "FAILED":
            attempt = event.get("attempt", 1)
            if attempt < MAX_RETRIES:
                logger.info("Retrying staging write for %s (attempt %d)", correlation_id, attempt + 1)
                db = next(get_cbs_staging_db())
                try:
                    service = StagingService()
                    service.retry_failed(correlation_id, db)
                finally:
                    db.close()
            else:
                logger.error("Staging write for %s failed after %d attempts", correlation_id, MAX_RETRIES)
        elif status == "POSTED":
            logger.info("Staging record %s posted to CBS", correlation_id)
        elif status == "HELD":
            logger.warning("Staging record %s held for manual review", correlation_id)
