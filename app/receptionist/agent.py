import logging

from app.models import AppointmentRequest, ReceptionistIntent, ReceptionistRequest, ReceptionistResponse
from app.services.calendar_service import CalendarSlotUnavailableError, GoogleCalendarService
from app.services.email_service import OwnerEmailNotificationService
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
        self.notifications = OwnerEmailNotificationService()

    async def handle(self, request: ReceptionistRequest) -> ReceptionistResponse:
        baseline = self.extractor.extract(request)
        response = await self.openai.complete(request, baseline)
        lead_id = self.leads.save_from_receptionist(request, response)

        if lead_id is not None and response.should_book and response.intent == ReceptionistIntent.book_appointment:
            await self._try_booking(lead_id, response)

        if lead_id is not None:
            self.notifications.notify_lead_captured(request, response)

        return response

    async def _try_booking(self, lead_id: int, response: ReceptionistResponse) -> None:
        if not self.calendar.is_configured():
            logger.info("Skipping calendar booking because Google Calendar is not configured")
            return

        appointment = AppointmentRequest(
            lead=response.lead,
            summary=self._appointment_summary(response),
            description=self._appointment_description(response),
        )
        try:
            event = self.calendar.create_estimate_appointment(appointment)
        except CalendarSlotUnavailableError:
            logger.info("Skipping calendar booking because requested slot is unavailable")
            return

        event_id = event.get("id")
        if event_id:
            self.leads.update_calendar_event_id(lead_id, event_id)

    def _appointment_summary(self, response: ReceptionistResponse) -> str:
        service = response.lead.service_requested or "Estimate"
        caller = response.lead.caller_name or "new caller"
        return f"{service.title()} with {caller}"

    def _appointment_description(self, response: ReceptionistResponse) -> str:
        lead = response.lead
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
