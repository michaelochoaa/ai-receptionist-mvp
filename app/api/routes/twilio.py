import logging

from fastapi import APIRouter, Form, Request, Response

from app.models import CallProvider, ReceptionistRequest
from app.receptionist.agent import ReceptionistAgent
from app.services.twilio_service import TwilioVoiceResponder

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/twilio", tags=["twilio"])


@router.post("/voice")
async def receive_twilio_voice(
    request: Request,
    CallSid: str = Form(...),
    From: str | None = Form(default=None),
    SpeechResult: str | None = Form(default=None),
) -> Response:
    receptionist_request = ReceptionistRequest(
        provider=CallProvider.twilio,
        call_id=CallSid,
        caller_phone=From,
        latest_message=SpeechResult,
    )
    response = await ReceptionistAgent().handle(receptionist_request)
    twiml = TwilioVoiceResponder().voice_response(response.message)

    logger.info("Handled Twilio call event call_id=%s intent=%s", CallSid, response.intent)
    return Response(content=twiml, media_type="application/xml")
