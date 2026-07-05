from sqlalchemy.orm import Session

from models.consumer import Consumer
from common.exceptions import NotFoundError, ConflictError
from common.utils import generate_uuid


class ConsumerService:

    def get_by_id(self, consumer_id: str, db: Session) -> Consumer:
        consumer = db.query(Consumer).filter(Consumer.consumer_id == consumer_id).first()
        if not consumer:
            raise NotFoundError(f"Consumer {consumer_id} not found")
        return consumer

    def get_by_bank_customer_id(self, bank_customer_id: str, db: Session) -> Consumer | None:
        return db.query(Consumer).filter(
            Consumer.bank_customer_id == bank_customer_id
        ).first()

    def create_consumer(self, bank_customer_id: str, name: str, phone: str,
                        email: str | None, db: Session) -> Consumer:
        existing = self.get_by_bank_customer_id(bank_customer_id, db)
        if existing:
            raise ConflictError(f"Consumer with bank customer ID {bank_customer_id} already exists")

        consumer_id = f"C-{bank_customer_id[-6:]}" if len(bank_customer_id) >= 6 else f"C-{generate_uuid()[:8]}"

        consumer = Consumer(
            consumer_id=consumer_id,
            bank_customer_id=bank_customer_id,
            name=name,
            phone=phone,
            email=email,
            bnpl_limit_lak=0,
            available_limit_lak=0,
            risk_tier="GREEN",
            kyc_status="VERIFIED",
        )
        db.add(consumer)
        db.commit()
        db.refresh(consumer)
        return consumer

    def update_limit(self, consumer_id: str, bnpl_limit: float,
                     available_limit: float, db: Session) -> Consumer:
        consumer = self.get_by_id(consumer_id, db)
        consumer.bnpl_limit_lak = bnpl_limit
        consumer.available_limit_lak = available_limit
        db.commit()
        db.refresh(consumer)
        return consumer
