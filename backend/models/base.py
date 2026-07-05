import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, String, DateTime, func
from core.database import Base


class BaseModel(Base):
    __abstract__ = True

    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
