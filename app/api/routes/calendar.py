from datetime import date

from fastapi import APIRouter, Query

from app.config import settings
from app.models import CalendarAvailabilityResponse
from app.services.calendar_service import GoogleCalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/available-slots")
async def available_slots(
    appointment_date: date = Query(..., description="Date to check in YYYY-MM-DD format."),
    duration_minutes: int = Query(default=settings.estimate_duration_minutes, ge=15, le=240),
) -> CalendarAvailabilityResponse:
    calendar = GoogleCalendarService()
    return CalendarAvailabilityResponse(
        demo_mode=calendar.demo_mode,
        slots=calendar.available_slots(appointment_date, duration_minutes=duration_minutes),
    )
