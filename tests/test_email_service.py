from datetime import datetime

from app.models import (
    CallProvider,
    LeadCapture,
    ReceptionistIntent,
    ReceptionistRequest,
    ReceptionistResponse,
)
from app.services.email_service import OwnerEmailNotificationService


def test_formats_owner_notification_summary() -> None:
    request = ReceptionistRequest(
        provider=CallProvider.vapi,
        call_id="local-vapi-call-001",
        caller_phone="+15553217890",
        latest_message="Maria wants an exterior painting estimate.",
    )
    response = ReceptionistResponse(
        intent=ReceptionistIntent.book_appointment,
        message="Thanks. I have the details for your appointment request.",
        lead=LeadCapture(
            caller_name="Maria Gomez",
            caller_phone="+15553217890",
            service_requested="exterior painting estimate",
            preferred_start=datetime(2026, 6, 18, 14, 0),
            preferred_end=datetime(2026, 6, 18, 15, 0),
            notes="Maria wants an exterior painting estimate.",
        ),
        should_book=True,
    )

    subject, body = OwnerEmailNotificationService().format_lead_summary(request, response)

    assert subject == "New lead captured: Maria Gomez"
    assert "Caller name: Maria Gomez" in body
    assert "Caller phone: +15553217890" in body
    assert "Service requested: exterior painting estimate" in body
    assert "Preferred time: 2026-06-18 02:00 PM - 2026-06-18 03:00 PM" in body
    assert "Intent: book_appointment" in body
    assert "Call ID: local-vapi-call-001" in body
    assert "Maria wants an exterior painting estimate." in body
