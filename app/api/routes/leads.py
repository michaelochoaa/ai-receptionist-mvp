from fastapi import APIRouter, Form, HTTPException, Query

from app.models import LeadRecord, LeadStatus
from app.services.lead_store import LeadStore

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("")
async def list_leads(limit: int = Query(default=50, ge=1, le=200)) -> list[LeadRecord]:
    return LeadStore().list_leads(limit=limit)


@router.post("/{lead_id}/status")
async def update_lead_status(
    lead_id: int,
    status: LeadStatus = Form(...),
) -> dict[str, object]:
    updated = LeadStore().update_status(lead_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"id": lead_id, "status": status.value}
