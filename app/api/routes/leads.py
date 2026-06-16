from fastapi import APIRouter, Query

from app.models import LeadRecord
from app.services.lead_store import LeadStore

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("")
async def list_leads(limit: int = Query(default=50, ge=1, le=200)) -> list[LeadRecord]:
    return LeadStore().list_leads(limit=limit)
