import json
from pathlib import Path

from openai import AsyncOpenAI

from app.config import settings
from app.models import LeadCapture, ReceptionistIntent, ReceptionistRequest, ReceptionistResponse

PROMPT_PATH = Path(__file__).resolve().parents[1] / "receptionist" / "prompts" / "system.md"


class OpenAIReceptionistService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def is_configured(self) -> bool:
        return self.client is not None

    async def complete(
        self,
        request: ReceptionistRequest,
        baseline: ReceptionistResponse,
    ) -> ReceptionistResponse:
        if not self.client:
            return baseline

        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        transcript = "\n".join(f"{turn.role}: {turn.content}" for turn in request.transcript)
        user_content = (
            f"Caller phone: {request.caller_phone or 'unknown'}\n"
            f"Latest message: {request.latest_message or 'none'}\n"
            f"Transcript:\n{transcript or 'No transcript yet.'}"
        )

        completion = await self.client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        content = completion.choices[0].message.content or "{}"
        ai_response = ReceptionistResponse.model_validate(json.loads(content))
        return self._merge_responses(baseline, ai_response)

    def _merge_responses(
        self,
        baseline: ReceptionistResponse,
        ai_response: ReceptionistResponse,
    ) -> ReceptionistResponse:
        ai_lead = ai_response.lead
        base_lead = baseline.lead
        merged_lead = LeadCapture(
            caller_name=ai_lead.caller_name or base_lead.caller_name,
            caller_phone=ai_lead.caller_phone or base_lead.caller_phone,
            service_requested=ai_lead.service_requested or base_lead.service_requested,
            preferred_start=ai_lead.preferred_start or base_lead.preferred_start,
            preferred_end=ai_lead.preferred_end or base_lead.preferred_end,
            notes=ai_lead.notes or base_lead.notes,
        )
        intent = (
            baseline.intent
            if ai_response.intent == ReceptionistIntent.unknown and baseline.intent != ReceptionistIntent.unknown
            else ai_response.intent
        )
        return ai_response.model_copy(
            update={
                "intent": intent,
                "lead": merged_lead,
                "should_book": ai_response.should_book or baseline.should_book,
                "should_transfer": ai_response.should_transfer or baseline.should_transfer,
                "calendar_event_id": ai_response.calendar_event_id or baseline.calendar_event_id,
                "demo_mode": ai_response.demo_mode or baseline.demo_mode,
            }
        )
