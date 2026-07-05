from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_bnpl_db
from models.settlement import FraudRule
from schemas.common import PaginatedResponse
from common.utils import build_pagination_response, safe_endpoint
from common.exceptions import ConflictError, NotFoundError
from routes.dependencies import get_current_admin

router = APIRouter(prefix="/fraud-rules", tags=["Fraud Rules"])


class FraudRuleCreate(BaseModel):
    rule_name: str = Field(..., max_length=64)
    rule_type: str = Field(..., max_length=32)
    parameter: str = Field(..., max_length=128)
    threshold: str = Field(..., max_length=64)
    action: str = Field(..., max_length=16)
    enabled: bool = True


class FraudRuleUpdate(BaseModel):
    rule_name: str | None = None
    rule_type: str | None = None
    parameter: str | None = None
    threshold: str | None = None
    action: str | None = None
    enabled: bool | None = None


@router.get("", response_model=PaginatedResponse, summary="List all fraud rules")
@safe_endpoint
def list_rules(
    admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_bnpl_db),
):
    query = db.query(FraudRule).order_by(FraudRule.rule_name)
    total = query.count()
    rules = query.offset((page - 1) * page_size).limit(page_size).all()
    data = []
    for r in rules:
        data.append({
            "id": r.id,
            "rule_name": r.rule_name,
            "rule_type": r.rule_type,
            "parameter": r.parameter,
            "threshold": r.threshold,
            "action": r.action,
            "enabled": r.enabled,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return build_pagination_response(data, total, page, page_size)


@router.post("", response_model=dict, status_code=201, summary="Create a fraud rule")
@safe_endpoint
def create_rule(
    req: FraudRuleCreate,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    existing = db.query(FraudRule).filter(FraudRule.rule_name == req.rule_name).first()
    if existing:
        raise ConflictError(f"Rule '{req.rule_name}' already exists")
    rule = FraudRule(
        rule_name=req.rule_name,
        rule_type=req.rule_type,
        parameter=req.parameter,
        threshold=req.threshold,
        action=req.action,
        enabled=req.enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"id": rule.id, "rule_name": rule.rule_name, "status": "created"}


@router.put("/{rule_id}", response_model=dict, summary="Update a fraud rule")
@safe_endpoint
def update_rule(
    rule_id: int,
    req: FraudRuleUpdate,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    rule = db.query(FraudRule).filter(FraudRule.id == rule_id).first()
    if not rule:
        raise NotFoundError("Rule not found")
    updates = req.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(rule, field, value)
    db.commit()
    return {"id": rule.id, "rule_name": rule.rule_name, "status": "updated"}


@router.delete("/{rule_id}", status_code=204, summary="Delete a fraud rule")
@safe_endpoint
def delete_rule(
    rule_id: int,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    rule = db.query(FraudRule).filter(FraudRule.id == rule_id).first()
    if not rule:
        raise NotFoundError("Rule not found")
    db.delete(rule)
    db.commit()
