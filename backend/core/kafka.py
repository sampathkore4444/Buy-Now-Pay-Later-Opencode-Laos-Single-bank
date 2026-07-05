from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from core.config import settings

producer: AIOKafkaProducer | None = None


async def init_kafka():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        max_request_size=10485760,
    )
    await producer.start()


async def close_kafka():
    global producer
    if producer:
        await producer.stop()


async def get_producer() -> AIOKafkaProducer | None:
    return producer


async def send_event(topic: str, key: str, value: bytes):
    if producer is None:
        raise RuntimeError("Kafka producer not initialized")
    await producer.send(topic, key=key.encode(), value=value)
