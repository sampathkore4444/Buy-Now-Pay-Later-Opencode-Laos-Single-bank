from sqlalchemy import Column, BigInteger, String, DateTime, Text, Boolean, ForeignKey, func
from models.base import BaseModel


class Complaint(BaseModel):
    __tablename__ = "complaints"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    complaint_id = Column(String(64), unique=True, nullable=False, index=True)
    consumer_id = Column(String(32), ForeignKey("consumers.consumer_id"), nullable=False, index=True)
    auth_id = Column(String(64), ForeignKey("auth_requests.auth_id"), nullable=True)
    subject = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    channel = Column(String(16), nullable=False, default="PORTAL")
    status = Column(String(16), nullable=False, default="OPEN")
    assigned_to = Column(String(64), nullable=True)
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
