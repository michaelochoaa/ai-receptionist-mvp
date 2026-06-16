import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage

from app.config import settings
from app.models import LeadCapture, ReceptionistRequest, ReceptionistResponse

logger = logging.getLogger(__name__)


class OwnerEmailNotificationService:
    def is_configured(self) -> bool:
        return bool(
            settings.smtp_host
            and settings.smtp_from_email
            and settings.owner_email
        )

    def notify_lead_captured(
        self,
        request: ReceptionistRequest,
        response: ReceptionistResponse,
    ) -> None:
        subject, body = self.format_lead_summary(request, response)

        if not self.is_configured():
            logger.info("Owner notification not sent because SMTP is not configured:\n%s", body)
            return

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.smtp_from_email
        message["To"] = settings.owner_email
        message.set_content(body)

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                smtp.starttls()
                if settings.smtp_username and settings.smtp_password:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
        except Exception:
            logger.exception("Failed to send owner lead notification")

    def format_lead_summary(
        self,
        request: ReceptionistRequest,
        response: ReceptionistResponse,
    ) -> tuple[str, str]:
        lead = self._merge_request_context(request, response.lead)
        subject = f"New lead captured: {lead.caller_name or lead.caller_phone or 'Unknown caller'}"
        body = "\n".join(
            [
                f"New lead captured for {settings.business_name}",
                "",
                f"Caller name: {self._value(lead.caller_name)}",
                f"Caller phone: {self._value(lead.caller_phone)}",
                f"Service requested: {self._value(lead.service_requested)}",
                f"Preferred time: {self._format_time_range(lead)}",
                f"Intent: {response.intent.value}",
                f"Call ID: {request.call_id}",
                "",
                "Notes:",
                self._value(lead.notes),
            ]
        )
        return subject, body

    def _merge_request_context(
        self,
        request: ReceptionistRequest,
        lead: LeadCapture,
    ) -> LeadCapture:
        return lead.model_copy(
            update={
                "caller_phone": lead.caller_phone or request.caller_phone,
                "notes": lead.notes or request.latest_message,
            }
        )

    def _format_time_range(self, lead: LeadCapture) -> str:
        if lead.preferred_start and lead.preferred_end:
            start = self._format_datetime(lead.preferred_start)
            end = self._format_datetime(lead.preferred_end)
            return f"{start} - {end}"
        if lead.preferred_start:
            return self._format_datetime(lead.preferred_start)
        return "Not provided"

    def _format_datetime(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %I:%M %p")

    def _value(self, value: str | None) -> str:
        return value or "Not provided"
