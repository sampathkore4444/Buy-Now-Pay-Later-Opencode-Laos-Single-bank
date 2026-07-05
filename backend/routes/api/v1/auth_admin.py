from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_bnpl_db
from core.security import create_access_token, verify_password
from models.merchant import MerchantUser
from models.consumer import Consumer
from common.exceptions import UnauthorizedError

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=128)
    password: str = Field(..., min_length=8, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    role: str


class ConsumerLoginRequest(BaseModel):
    consumer_id: str = Field(..., max_length=32)
    phone: str = Field(..., max_length=20)


@router.post("/consumer-login", response_model=dict, summary="Consumer-facing login for limit self-service")
def consumer_login(
    req: ConsumerLoginRequest,
    db: Session = Depends(get_bnpl_db),
):
    consumer = db.query(Consumer).filter(
        Consumer.consumer_id == req.consumer_id,
        Consumer.phone == req.phone,
    ).first()
    if not consumer:
        raise UnauthorizedError("Invalid consumer credentials")
    token_data = {
        "sub": consumer.consumer_id,
        "role": "consumer",
        "name": consumer.name,
    }
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer", "consumer_id": consumer.consumer_id}


@router.post("/login", response_model=LoginResponse, summary="Admin/Merchant user login")
def login(
    req: LoginRequest,
    db: Session = Depends(get_bnpl_db),
):
    user = db.query(MerchantUser).filter(MerchantUser.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        from common.exceptions import UnauthorizedError as AuthError
        raise AuthError("Invalid email or password")
    if not user.is_active:
        from common.exceptions import ForbiddenError
        raise ForbiddenError("Account is disabled")

    token_data = {
        "sub": user.email,
        "user_id": str(user.id),
        "role": "admin" if user.role == "ADMIN" else "merchant",
        "name": user.name,
    }
    access_token = create_access_token(token_data)

    return LoginResponse(
        access_token=access_token,
        user_id=str(user.id),
        name=user.name,
        role=user.role,
    )
