from fastapi import Header, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.database import get_bnpl_db
from core.security import decode_access_token
from models.merchant import Merchant
from common.exceptions import UnauthorizedError, ForbiddenError

bearer_scheme = HTTPBearer()


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedError("Invalid or expired token")
    role = payload.get("role", "")
    if role != "admin":
        raise ForbiddenError("Admin access required")
    return payload


def get_current_merchant_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_bnpl_db),
):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedError("Invalid or expired token")
    return payload


def get_current_consumer(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_bnpl_db),
):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedError("Invalid or expired token")
    role = payload.get("role", "")
    if role != "consumer":
        raise ForbiddenError("Consumer access required")
    from models.consumer import Consumer
    consumer = db.query(Consumer).filter(
        Consumer.consumer_id == payload.get("sub")
    ).first()
    if not consumer:
        raise UnauthorizedError("Consumer not found")
    return consumer


def get_api_merchant(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_bnpl_db),
) -> Merchant:
    merchant = db.query(Merchant).filter(Merchant.api_key == x_api_key).first()
    if not merchant:
        raise UnauthorizedError("Invalid API key")
    if merchant.status.name != "APPROVED":
        raise ForbiddenError("Merchant account is not active")
    return merchant
