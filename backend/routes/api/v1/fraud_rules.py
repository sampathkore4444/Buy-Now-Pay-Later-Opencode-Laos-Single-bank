from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_bnpl_db
from models.settlement import FraudRule
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


@router.get("", summary="List all fraud rules")
def list_rules(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    rules = db.query(FraudRule).order_by(FraudRule.rule_name).all()
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
    return {"data": data, "total": len(data)}


@router.post("", summary="Create a fraud rule")
def create_rule(
    req: FraudRuleCreate,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    existing = db.query(FraudRule).filter(FraudRule.rule_name == req.rule_name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Rule '{req.rule_name}' already exists")
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


@router.put("/{rule_id}", summary="Update a fraud rule")
def update_rule(
    rule_id: int,
    req: FraudRuleUpdate,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    rule = db.query(FraudRule).filter(FraudRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    updates = req.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(rule, field, value)
    db.commit()
    return {"id": rule.id, "rule_name": rule.rule_name, "status": "updated"}


@router.delete("/{rule_id}", summary="Delete a fraud rule")
def delete_rule(
    rule_id: int,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    rule = db.query(FraudRule).filter(FraudRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"status": "deleted"}
