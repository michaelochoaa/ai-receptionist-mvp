from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.config import settings
from app.models import AppointmentRequest


class GoogleCalendarService:
    def __init__(self) -> None:
        self.calendar_id = settings.google_calendar_id
        self.credentials_path = settings.google_application_credentials

    def is_configured(self) -> bool:
        return bool(self.calendar_id and self.credentials_path)

    def create_appointment(self, appointment: AppointmentRequest) -> dict:
        if not self.is_configured():
            raise RuntimeError("Google Calendar is not configured")
        if not appointment.lead.preferred_start or not appointment.lead.preferred_end:
            raise ValueError("Appointment start and end are required")

        service = self._calendar_client()
        event = {
            "summary": appointment.summary,
            "description": appointment.description or appointment.lead.notes,
            "start": self._event_time(appointment.lead.preferred_start),
            "end": self._event_time(appointment.lead.preferred_end),
            "attendees": [],
        }
        return service.events().insert(calendarId=self.calendar_id, body=event).execute()

    def _calendar_client(self):
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        return build("calendar", "v3", credentials=credentials)

    def _event_time(self, value: datetime) -> dict[str, str]:
        return {"dateTime": value.isoformat(), "timeZone": settings.business_timezone}
