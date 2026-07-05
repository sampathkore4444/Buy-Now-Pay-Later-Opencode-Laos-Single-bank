from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import settings

bnpl_engine = create_engine(
    settings.DATABASE_URL or
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

cbs_staging_engine = create_engine(
    settings.CBS_STAGING_URL or
    f"postgresql://{settings.CBS_STAGING_USER}:{settings.CBS_STAGING_PASSWORD}"
    f"@{settings.CBS_STAGING_HOST}:{settings.CBS_STAGING_PORT}/{settings.CBS_STAGING_DB}",
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
)

BnplSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=bnpl_engine)
CbsStagingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cbs_staging_engine)

Base = declarative_base()


def get_bnpl_db():
    db = BnplSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cbs_staging_db():
    db = CbsStagingSessionLocal()
    try:
        yield db
    finally:
        db.close()
