from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.config import settings
from app.models import AppointmentRequest, AppointmentSlot, LeadCapture


class CalendarSlotUnavailableError(Exception):
    """Raised when a requested appointment overlaps an existing calendar event."""


class GoogleCalendarService:
    def __init__(self, calendar_client=None) -> None:
        self.calendar_id = settings.google_calendar_id
        self.credentials_path = settings.google_application_credentials
        self._calendar_client_override = calendar_client

    def is_configured(self) -> bool:
        return bool((self.calendar_id and self.credentials_path) or self._calendar_client_override)

    def available_slots(
        self,
        appointment_date: date,
        duration_minutes: int | None = None,
    ) -> list[AppointmentSlot]:
        self._ensure_configured()
        duration = timedelta(minutes=duration_minutes or settings.estimate_duration_minutes)
        timezone = ZoneInfo(settings.business_timezone)
        day_start = datetime.combine(
            appointment_date,
            time(hour=settings.business_start_hour),
            tzinfo=timezone,
        )
        day_end = datetime.combine(
            appointment_date,
            time(hour=settings.business_end_hour),
            tzinfo=timezone,
        )
        busy_ranges = self._busy_ranges(day_start, day_end)

        slots: list[AppointmentSlot] = []
        slot_start = day_start
        while slot_start + duration <= day_end:
            slot_end = slot_start + duration
            if self._slot_is_free(slot_start, slot_end, busy_ranges):
                slots.append(AppointmentSlot(start=slot_start, end=slot_end))
            slot_start += duration
        return slots

    def is_available(self, start: datetime, end: datetime) -> bool:
        self._ensure_configured()
        start = self._with_business_timezone(start)
        end = self._with_business_timezone(end)
        return self._slot_is_free(start, end, self._busy_ranges(start, end))

    def create_estimate_appointment(self, appointment: AppointmentRequest) -> dict:
        if not appointment.lead.preferred_start or not appointment.lead.preferred_end:
            raise ValueError("Appointment start and end are required")

        start = self._with_business_timezone(appointment.lead.preferred_start)
        end = self._with_business_timezone(appointment.lead.preferred_end)
        if not self.is_available(start, end):
            raise CalendarSlotUnavailableError("Requested appointment slot is already booked")

        service = self._calendar_client()
        event = {
            "summary": appointment.summary,
            "description": appointment.description or self._description_from_lead(appointment.lead),
            "start": self._event_time(start),
            "end": self._event_time(end),
            "attendees": [],
        }
        return service.events().insert(calendarId=self.calendar_id, body=event).execute()

    def _busy_ranges(self, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
        service = self._calendar_client()
        response = (
            service.freebusy()
            .query(
                body={
                    "timeMin": start.isoformat(),
                    "timeMax": end.isoformat(),
                    "timeZone": settings.business_timezone,
                    "items": [{"id": self.calendar_id}],
                }
            )
            .execute()
        )
        busy_items = response.get("calendars", {}).get(self.calendar_id, {}).get("busy", [])
        return [
            (self._parse_google_datetime(item["start"]), self._parse_google_datetime(item["end"]))
            for item in busy_items
        ]

    def _slot_is_free(
        self,
        start: datetime,
        end: datetime,
        busy_ranges: list[tuple[datetime, datetime]],
    ) -> bool:
        return not any(start < busy_end and end > busy_start for busy_start, busy_end in busy_ranges)

    def _calendar_client(self):
        if self._calendar_client_override:
            return self._calendar_client_override
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        return build("calendar", "v3", credentials=credentials)

    def _ensure_configured(self) -> None:
        if not self.is_configured():
            raise RuntimeError("Google Calendar is not configured")

    def _event_time(self, value: datetime) -> dict[str, str]:
        return {"dateTime": value.isoformat(), "timeZone": settings.business_timezone}

    def _with_business_timezone(self, value: datetime) -> datetime:
        timezone = ZoneInfo(settings.business_timezone)
        if value.tzinfo:
            return value.astimezone(timezone)
        return value.replace(tzinfo=timezone)

    def _parse_google_datetime(self, value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).astimezone(ZoneInfo(settings.business_timezone))

    def _description_from_lead(self, lead: LeadCapture) -> str:
        return "\n".join(
            [
                f"Caller: {lead.caller_name or 'Not provided'}",
                f"Phone: {lead.caller_phone or 'Not provided'}",
                f"Service: {lead.service_requested or 'Estimate request'}",
                "",
                "Notes:",
                lead.notes or "Not provided",
            ]
        )
