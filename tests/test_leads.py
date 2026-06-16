import json

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.models import ReceptionistIntent


def test_leads_endpoint_returns_list() -> None:
    client = TestClient(app)
    response = client.get("/leads")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_vapi_webhook_captures_painting_lead(tmp_path) -> None:
    settings.database_path = str(tmp_path / "leads.db")
    settings.openai_api_key = None
    settings.google_calendar_id = None
    settings.google_application_credentials = None
    client = TestClient(app)

    with open("samples/vapi_webhook.json", encoding="utf-8") as payload_file:
        payload = json.load(payload_file)

    webhook_response = client.post("/webhooks/vapi", json=payload)
    leads_response = client.get("/leads")

    assert webhook_response.status_code == 200
    assert leads_response.status_code == 200

    leads = leads_response.json()
    assert len(leads) == 1
    lead = leads[0]
    assert lead["caller_name"] == "Maria Gomez"
    assert lead["caller_phone"] == "+15553217890"
    assert lead["service_requested"] == "exterior painting estimate"
    assert lead["preferred_start"] == "2026-06-18T14:00:00"
    assert lead["preferred_end"] == "2026-06-18T15:00:00"
    assert lead["intent"] == ReceptionistIntent.book_appointment.value
