import json
import logging
from decimal import Decimal

from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session

from core.config import settings
from core.database import BnplSessionLocal as SessionLocal
from services.transaction_service import TransactionService
from services.staging_service import StagingService
from services.webhook_service import WebhookDeliveryService
from services.notification_service import NotificationService
from models.transaction import AuthRequest, Transaction
from models.merchant import Merchant
from models.consumer import Consumer
from common.enums import AuthStatus

logger = logging.getLogger(__name__)


class AuthEventConsumer:

    async def consume(self):
        consumer = AIOKafkaConsumer(
            settings.KAFKA_AUTH_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP,
            value_deserializer=lambda v: json.loads(v.decode()),
        )
        await consumer.start()
        logger.info("Auth event consumer started")
        try:
            async for msg in consumer:
                event = msg.value
                auth_id = event.get("auth_id")
                status = event.get("status")
                try:
                    await self._process_event(auth_id, status, event)
                except Exception as e:
                    logger.error("Failed to process auth event for %s: %s", auth_id, e)
        finally:
            await consumer.stop()

    async def _process_event(self, auth_id: str, status: str, event: dict):
        db: Session = SessionLocal()
        try:
            if status == "CONFIRMED":
                await self._handle_confirmed(auth_id, db)
            elif status == "AUTHED":
                logger.info("Auth %s authorized, awaiting confirm", auth_id)
            elif status == "DECLINED":
                await self._handle_declined(auth_id, event, db)
            elif status == "CANCELLED":
                logger.info("Auth %s was cancelled", auth_id)
        finally:
            db.close()

    async def _handle_confirmed(self, auth_id: str, db: Session):
        txn_service = TransactionService()
        staging_service = StagingService()
        webhook_service = WebhookDeliveryService()

        auth = db.query(AuthRequest).filter(AuthRequest.auth_id == auth_id).first()
        if not auth:
            logger.warning("Auth %s not found for confirm processing", auth_id)
            return

        txn = txn_service.create_from_auth(auth, db)
        logger.info("Transaction %s created from auth %s", txn.txn_id, auth_id)

        staging_header = txn_service.create_staging_header(txn, db)
        logger.info("Staging header %s created for txn %s", staging_header.id, txn.txn_id)

        merchant = db.query(Merchant).filter(Merchant.merchant_id == auth.merchant_id).first()
        if merchant and merchant.webhook_url:
            details = {
                "txn_id": txn.txn_id,
                "amount_lak": float(auth.approved_amount_lak),
                "correlation_id": txn.correlation_id,
            }
            await webhook_service.deliver_auth_result(
                merchant.webhook_url, auth_id, "CONFIRMED", details
            )

        consumer = db.query(Consumer).filter(Consumer.consumer_id == auth.consumer_id).first()
        if consumer:
            notif_service = NotificationService()
            await notif_service.notify_purchase_confirmed(
                consumer.phone,
                float(auth.approved_amount_lak),
                auth.repayment_date.strftime("%Y-%m-%d") if auth.repayment_date else "TBD",
            )

    async def _handle_declined(self, auth_id: str, event: dict, db: Session):
        reason = event.get("reason_code", "UNKNOWN")
        auth = db.query(AuthRequest).filter(AuthRequest.auth_id == auth_id).first()
        if auth:
            consumer = db.query(Consumer).filter(Consumer.consumer_id == auth.consumer_id).first()
            if consumer:
                notif_service = NotificationService()
                await notif_service.notify_declined(
                    consumer.phone, float(auth.amount_lak), reason
                )
