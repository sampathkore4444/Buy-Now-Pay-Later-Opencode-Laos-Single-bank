from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "BNPL Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "development"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "bnpl_user"
    POSTGRES_PASSWORD: str = "bnpl_pass"
    POSTGRES_DB: str = "bnpl_platform"
    DATABASE_URL: Optional[str] = None

    CBS_STAGING_HOST: str = "localhost"
    CBS_STAGING_PORT: int = 5432
    CBS_STAGING_USER: str = "bnpl_stg_writer"
    CBS_STAGING_PASSWORD: str = "stg_pass"
    CBS_STAGING_DB: str = "cbs_staging"
    CBS_STAGING_SCHEMA: str = "INT_STG"
    CBS_STAGING_URL: Optional[str] = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP: str = "bnpl-consumer-group"
    KAFKA_AUTH_TOPIC: str = "bnpl-auth"
    KAFKA_STAGING_TOPIC: str = "bnpl-staging"
    KAFKA_SETTLEMENT_TOPIC: str = "bnpl-settlement"
    KAFKA_NOTIFICATION_TOPIC: str = "bnpl-notification"

    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    API_KEY_EXPIRATION_DAYS: int = 365

    REDIS_LIMIT_PREFIX: str = "bnpl:limit:"
    REDIS_MERCHANT_PREFIX: str = "bnpl:merchant:"
    REDIS_AUTH_PREFIX: str = "bnpl:auth:"
    REDIS_DEFAULT_TTL_SECONDS: int = 3600

    AUTH_TIMEOUT_MINUTES: int = 30
    EOD_BATCH_HOUR: int = 22
    EOD_BATCH_TIMEZONE: str = "Asia/Vientiane"
    MAX_RETRIES_STAGING: int = 3
    DEFAULT_MDR_RATE: float = 0.045

    SMS_API_URL: Optional[str] = None
    SMS_API_KEY: Optional[str] = None

    BCEL_API_BASE_URL: str = "https://api.bcel.com.la/v1"
    BCEL_API_KEY: Optional[str] = None
    LDB_API_BASE_URL: str = "https://api.ldb.com.la/v1"
    LDB_API_KEY: Optional[str] = None

    PROMETHEUS_ENABLED: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
