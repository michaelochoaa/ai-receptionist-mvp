import re
from datetime import datetime, timedelta

from app.models import LeadCapture, ReceptionistIntent, ReceptionistRequest, ReceptionistResponse

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


class DeterministicLeadExtractor:
    def extract(self, request: ReceptionistRequest) -> ReceptionistResponse:
        text = self._conversation_text(request)
        lead = LeadCapture(
            caller_name=self._extract_name(text),
            caller_phone=self._extract_phone(text) or request.caller_phone,
            service_requested=self._extract_service(text),
            notes=request.latest_message,
        )
        lead.preferred_start = self._extract_preferred_start(text)
        lead.preferred_end = lead.preferred_start + timedelta(hours=1) if lead.preferred_start else None
        intent = self._extract_intent(text)

        return ReceptionistResponse(
            intent=intent,
            message=self._message_for(lead, intent),
            lead=lead,
            should_book=intent == ReceptionistIntent.book_appointment and lead.preferred_start is not None,
        )

    def _conversation_text(self, request: ReceptionistRequest) -> str:
        parts = [turn.content for turn in request.transcript]
        if request.latest_message and request.latest_message not in parts:
            parts.append(request.latest_message)
        return " ".join(parts)

    def _extract_name(self, text: str) -> str | None:
        patterns = [
            r"\b(?:this is|my name is|i am|i'm)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
            r"\bname is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_phone(self, text: str) -> str | None:
        match = re.search(
            r"(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}",
            text,
        )
        if not match:
            return None

        digits = re.sub(r"\D", "", match.group(0))
        if len(digits) == 10:
            return f"+1{digits}"
        if len(digits) == 11 and digits.startswith("1"):
            return f"+{digits}"
        return match.group(0)

    def _extract_service(self, text: str) -> str | None:
        lower_text = text.lower()
        service_patterns = [
            r"\b(?:estimate|quote)\s+for\s+([a-z ]+?)(?:\s+(?:on|at|for|next|this|tomorrow|today)\b|[.!?]|$)",
            r"\b(?:need|want|looking for|calling about)\s+(?:an?\s+)?([a-z ]*painting[a-z ]*?)(?:\s+(?:on|at|for|next|this|tomorrow|today)\b|[.!?]|$)",
        ]
        for pattern in service_patterns:
            match = re.search(pattern, lower_text)
            if match:
                return self._clean_service(match.group(1))

        if "painting" in lower_text and ("estimate" in lower_text or "quote" in lower_text):
            return "painting estimate"
        if "painting" in lower_text:
            return "painting"
        return None

    def _extract_preferred_start(self, text: str) -> datetime | None:
        date_match = re.search(
            r"\b("
            + "|".join(MONTHS)
            + r")\s+(\d{1,2})(?:st|nd|rd|th)?(?:,\s*(\d{4}))?",
            text,
            flags=re.IGNORECASE,
        )
        time_match = re.search(
            r"\b(?:at|around)?\s*(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b",
            text,
            flags=re.IGNORECASE,
        )
        if not date_match or not time_match:
            return None

        month = MONTHS[date_match.group(1).lower()]
        day = int(date_match.group(2))
        year = int(date_match.group(3) or datetime.now().year)
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        meridiem = time_match.group(3).lower().replace(".", "")

        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0

        return datetime(year, month, day, hour, minute)

    def _extract_intent(self, text: str) -> ReceptionistIntent:
        lower_text = text.lower()
        if any(word in lower_text for word in ["reschedule", "move my appointment"]):
            return ReceptionistIntent.reschedule_appointment
        if any(word in lower_text for word in ["cancel", "call off"]):
            return ReceptionistIntent.cancel_appointment
        if any(word in lower_text for word in ["appointment", "estimate", "quote", "book", "schedule"]):
            return ReceptionistIntent.book_appointment
        if any(word in lower_text for word in ["hours", "address", "location", "open"]):
            return ReceptionistIntent.business_info
        return ReceptionistIntent.unknown

    def _clean_service(self, service: str) -> str:
        service = re.sub(r"\b(?:an?|the|some)\b", "", service)
        service = re.sub(r"\s+", " ", service).strip(" .")
        if "painting" in service and "estimate" not in service:
            return f"{service} estimate"
        return service or "painting estimate"

    def _message_for(self, lead: LeadCapture, intent: ReceptionistIntent) -> str:
        if intent == ReceptionistIntent.book_appointment and lead.preferred_start:
            return "Thanks. I have the details for your appointment request."
        if intent == ReceptionistIntent.book_appointment:
            return "Thanks. What day and time would you prefer?"
        return "Thanks for calling. I can help collect your details."
