from datetime import datetime, timedelta

from app.models import CallProvider, ConversationTurn, ReceptionistIntent, ReceptionistRequest
from app.services.lead_extractor import DeterministicLeadExtractor


def test_extracts_painting_company_lead_fields() -> None:
    request = ReceptionistRequest(
        provider=CallProvider.vapi,
        call_id="test-call-001",
        caller_phone="+15553217890",
        transcript=[
            ConversationTurn(role="assistant", content="Thanks for calling. How can I help?"),
            ConversationTurn(
                role="user",
                content=(
                    "Hi, this is Maria Gomez. I need an estimate for exterior painting "
                    "on June 18, 2026 at 2 PM. My number is 555-321-7890."
                ),
            ),
        ],
    )

    response = DeterministicLeadExtractor().extract(request)

    assert response.intent == ReceptionistIntent.book_appointment
    assert response.lead.caller_name == "Maria Gomez"
    assert response.lead.caller_phone == "+15553217890"
    assert response.lead.service_requested == "exterior painting estimate"
    assert response.lead.preferred_start == datetime(2026, 6, 18, 14, 0)
    assert response.lead.preferred_end == datetime(2026, 6, 18, 14, 0) + timedelta(hours=1)
