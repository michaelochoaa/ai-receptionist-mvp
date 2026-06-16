from datetime import date, datetime

import pytest

from app.config import settings
from app.models import AppointmentRequest, LeadCapture
from app.services.calendar_service import CalendarSlotUnavailableError, GoogleCalendarService


class FakeGoogleCalendarClient:
    def __init__(self, busy=None) -> None:
        self.busy = busy or []
        self.inserted_event = None

    def freebusy(self):
        return _FakeFreeBusy(self.busy)

    def events(self):
        return _FakeEvents(self)


class _FakeFreeBusy:
    def __init__(self, busy) -> None:
        self.busy = busy

    def query(self, body):
        return _FakeExecute(
            {
                "calendars": {
                    body["items"][0]["id"]: {
                        "busy": self.busy,
                    }
                }
            }
        )


class _FakeEvents:
    def __init__(self, client: FakeGoogleCalendarClient) -> None:
        self.client = client

    def insert(self, calendarId, body):
        self.client.inserted_event = body
        return _FakeExecute({"id": "google-event-123", **body})


class _FakeExecute:
    def __init__(self, response) -> None:
        self.response = response

    def execute(self):
        return self.response


def test_available_slots_excludes_busy_calendar_events(monkeypatch) -> None:
    monkeypatch.setattr(settings, "google_calendar_id", "test-calendar")
    monkeypatch.setattr(settings, "business_timezone", "America/New_York")
    monkeypatch.setattr(settings, "business_start_hour", 9)
    monkeypatch.setattr(settings, "business_end_hour", 12)
    monkeypatch.setattr(settings, "estimate_duration_minutes", 60)
    client = FakeGoogleCalendarClient(
        busy=[
            {
                "start": "2026-06-18T10:00:00-04:00",
                "end": "2026-06-18T11:00:00-04:00",
            }
        ]
    )

    slots = GoogleCalendarService(calendar_client=client).available_slots(date(2026, 6, 18))

    assert [slot.start.hour for slot in slots] == [9, 11]


def test_create_estimate_appointment_prevents_double_booking(monkeypatch) -> None:
    monkeypatch.setattr(settings, "google_calendar_id", "test-calendar")
    monkeypatch.setattr(settings, "business_timezone", "America/New_York")
    client = FakeGoogleCalendarClient(
        busy=[
            {
                "start": "2026-06-18T14:00:00-04:00",
                "end": "2026-06-18T15:00:00-04:00",
            }
        ]
    )
    appointment = AppointmentRequest(
        lead=LeadCapture(
            caller_name="Maria Gomez",
            caller_phone="+15553217890",
            service_requested="exterior painting estimate",
            preferred_start=datetime(2026, 6, 18, 14, 0),
            preferred_end=datetime(2026, 6, 18, 15, 0),
        ),
        summary="Exterior painting estimate with Maria Gomez",
    )

    with pytest.raises(CalendarSlotUnavailableError):
        GoogleCalendarService(calendar_client=client).create_estimate_appointment(appointment)


def test_create_estimate_appointment_returns_event_id_when_available(monkeypatch) -> None:
    monkeypatch.setattr(settings, "google_calendar_id", "test-calendar")
    monkeypatch.setattr(settings, "business_timezone", "America/New_York")
    client = FakeGoogleCalendarClient()
    appointment = AppointmentRequest(
        lead=LeadCapture(
            caller_name="Maria Gomez",
            caller_phone="+15553217890",
            service_requested="exterior painting estimate",
            preferred_start=datetime(2026, 6, 18, 14, 0),
            preferred_end=datetime(2026, 6, 18, 15, 0),
            notes="Estimate request from phone call.",
        ),
        summary="Exterior painting estimate with Maria Gomez",
    )

    event = GoogleCalendarService(calendar_client=client).create_estimate_appointment(appointment)

    assert event["id"] == "google-event-123"
    assert client.inserted_event["summary"] == "Exterior painting estimate with Maria Gomez"
