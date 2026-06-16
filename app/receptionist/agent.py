import logging

from app.models import AppointmentRequest, ReceptionistIntent, ReceptionistRequest, ReceptionistResponse
from app.services.calendar_service import GoogleCalendarService
from app.services.lead_extractor import DeterministicLeadExtractor
from app.services.lead_store import LeadStore
from app.services.openai_service import OpenAIReceptionistService

logger = logging.getLogger(__name__)


class ReceptionistAgent:
    def __init__(self) -> None:
        self.extractor = DeterministicLeadExtractor()
        self.openai = OpenAIReceptionistService()
        self.calendar = GoogleCalendarService()
        self.leads = LeadStore()

    async def handle(self, request: ReceptionistRequest) -> ReceptionistResponse:
        baseline = self.extractor.extract(request)
        response = await self.openai.complete(request, baseline)
        self.leads.save_from_receptionist(request, response)

        if response.should_book and response.intent == ReceptionistIntent.book_appointment:
            await self._try_booking(response)

        return response

    async def _try_booking(self, response: ReceptionistResponse) -> None:
        if not self.calendar.is_configured():
            logger.info("Skipping calendar booking because Google Calendar is not configured")
            return

        appointment = AppointmentRequest(
            lead=response.lead,
            summary=f"Appointment with {response.lead.caller_name or 'new caller'}",
            description=response.lead.notes,
        )
        self.calendar.create_appointment(appointment)
