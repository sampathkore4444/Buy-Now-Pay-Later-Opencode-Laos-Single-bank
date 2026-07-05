from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from core.database import get_bnpl_db
from models.complaint import Complaint
from schemas.common import PaginatedResponse
from common.utils import build_pagination_response, generate_uuid
from common.exceptions import NotFoundError
from routes.dependencies import get_current_admin

router = APIRouter(prefix="/complaints", tags=["Consumer Complaints"])


class ComplaintCreateRequest(BaseModel):
    consumer_id: str = Field(..., max_length=32)
    auth_id: str | None = Field(None, max_length=64)
    subject: str = Field(..., max_length=128)
    description: str = Field(..., max_length=2000)
    channel: str = Field(default="PORTAL", max_length=16)


class ComplaintResolveRequest(BaseModel):
    resolution: str = Field(..., max_length=2000)


@router.post("", response_model=dict, status_code=201, summary="Submit a consumer complaint")
def create_complaint(
    req: ComplaintCreateRequest,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    complaint_id = f"CMP-{generate_uuid()[:16]}"
    complaint = Complaint(
        complaint_id=complaint_id,
        consumer_id=req.consumer_id,
        auth_id=req.auth_id,
        subject=req.subject,
        description=req.description,
        channel=req.channel,
    )
    db.add(complaint)
    db.commit()
    return {
        "complaint_id": complaint_id,
        "status": "OPEN",
        "message": "Complaint registered successfully",
    }


@router.get("", response_model=PaginatedResponse, summary="List complaints (paginated)")
def list_complaints(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    consumer_id: str | None = Query(None),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    query = db.query(Complaint)
    if status:
        query = query.filter(Complaint.status == status)
    if consumer_id:
        query = query.filter(Complaint.consumer_id == consumer_id)
    total = query.count()
    complaints = query.order_by(desc(Complaint.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    data = []
    for c in complaints:
        data.append({
            "complaint_id": c.complaint_id,
            "consumer_id": c.consumer_id,
            "auth_id": c.auth_id,
            "subject": c.subject,
            "description": c.description[:200],
            "channel": c.channel,
            "status": c.status,
            "assigned_to": c.assigned_to,
            "resolution": c.resolution,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return build_pagination_response(data, total, page, page_size)


@router.post("/{complaint_id}/resolve", response_model=dict, summary="Resolve a complaint")
def resolve_complaint(
    complaint_id: str,
    req: ComplaintResolveRequest,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_bnpl_db),
):
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise NotFoundError("Complaint not found")
    complaint.status = "RESOLVED"
    complaint.resolution = req.resolution
    complaint.resolved_at = datetime.utcnow()
    db.commit()
    return {"complaint_id": complaint_id, "status": "RESOLVED"}
