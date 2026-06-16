import logging

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings
from app.receptionist.agent import ReceptionistAgent
from app.services.vapi_service import VapiWebhookParser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/vapi", tags=["vapi"])


@router.post("")
async def receive_vapi_webhook(
    request: Request,
    x_vapi_secret: str | None = Header(default=None),
) -> dict[str, object]:
    if settings.vapi_webhook_secret and x_vapi_secret != settings.vapi_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid Vapi webhook secret")

    payload = await request.json()
    receptionist_request = VapiWebhookParser().parse(payload)
    response = await ReceptionistAgent().handle(receptionist_request)

    logger.info("Handled Vapi call event call_id=%s intent=%s", receptionist_request.call_id, response.intent)
    return {
        "message": response.message,
        "intent": response.intent,
        "shouldBook": response.should_book,
        "shouldTransfer": response.should_transfer,
    }
