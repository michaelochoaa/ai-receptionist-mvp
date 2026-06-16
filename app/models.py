from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class CallProvider(StrEnum):
    vapi = "vapi"
    twilio = "twilio"


class ReceptionistIntent(StrEnum):
    book_appointment = "book_appointment"
    reschedule_appointment = "reschedule_appointment"
    cancel_appointment = "cancel_appointment"
    business_info = "business_info"
    transfer_or_callback = "transfer_or_callback"
    unknown = "unknown"


class LeadCapture(BaseModel):
    caller_name: str | None = None
    caller_phone: str | None = None
    service_requested: str | None = None
    preferred_start: datetime | None = None
    preferred_end: datetime | None = None
    notes: str | None = None


class ConversationTurn(BaseModel):
    role: str
    content: str


class ReceptionistRequest(BaseModel):
    provider: CallProvider
    call_id: str
    caller_phone: str | None = None
    transcript: list[ConversationTurn] = Field(default_factory=list)
    latest_message: str | None = None


class ReceptionistResponse(BaseModel):
    intent: ReceptionistIntent
    message: str
    lead: LeadCapture = Field(default_factory=LeadCapture)
    should_book: bool = False
    should_transfer: bool = False


class AppointmentRequest(BaseModel):
    lead: LeadCapture
    summary: str
    description: str | None = None


class LeadRecord(BaseModel):
    id: int
    provider: CallProvider
    call_id: str
    caller_name: str | None = None
    caller_phone: str | None = None
    service_requested: str | None = None
    preferred_start: datetime | None = None
    preferred_end: datetime | None = None
    notes: str | None = None
    intent: ReceptionistIntent
    created_at: datetime
