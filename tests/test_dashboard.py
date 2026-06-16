from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.models import CallProvider, LeadStatus, ReceptionistIntent
from app.services.lead_store import LeadStore


def test_dashboard_lists_leads_and_updates_status() -> None:
    database_path = Path("data") / f"test-dashboard-{uuid4().hex}.db"
    settings.database_path = str(database_path)
    store = LeadStore()
    try:
        store.initialize()
        with store._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO leads (
                    provider,
                    call_id,
                    caller_name,
                    caller_phone,
                    service_requested,
                    preferred_start,
                    preferred_end,
                    notes,
                    intent,
                    google_calendar_event_id,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    CallProvider.vapi.value,
                    "call-123",
                    "Maria Gomez",
                    "+15553217890",
                    "exterior painting estimate",
                    "2026-06-18T14:00:00",
                    "2026-06-18T15:00:00",
                    "Estimate request.",
                    ReceptionistIntent.book_appointment.value,
                    "demo-event-20260618T140000",
                    LeadStatus.new.value,
                    datetime.now(UTC).isoformat(),
                ),
            )
            lead_id = cursor.lastrowid

        with TestClient(app) as client:
            dashboard_response = client.get("/dashboard")
            update_response = client.post(
                f"/leads/{lead_id}/status",
                data={"status": LeadStatus.contacted.value},
            )
            leads_response = client.get("/leads")

        assert dashboard_response.status_code == 200
        assert "Maria Gomez" in dashboard_response.text
        assert "exterior painting estimate" in dashboard_response.text
        assert update_response.status_code == 200
        assert update_response.json() == {"id": lead_id, "status": LeadStatus.contacted.value}
        assert leads_response.json()[0]["status"] == LeadStatus.contacted.value
    finally:
        try:
            database_path.unlink(missing_ok=True)
        except PermissionError:
            pass
