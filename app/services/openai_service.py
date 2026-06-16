import json
from pathlib import Path

from openai import AsyncOpenAI

from app.config import settings
from app.models import ReceptionistIntent, ReceptionistRequest, ReceptionistResponse

PROMPT_PATH = Path(__file__).resolve().parents[1] / "receptionist" / "prompts" / "system.md"


class OpenAIReceptionistService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def complete(self, request: ReceptionistRequest) -> ReceptionistResponse:
        if not self.client:
            return ReceptionistResponse(
                intent=ReceptionistIntent.unknown,
                message="Thanks for calling. I can help collect your details for an appointment.",
            )

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
        return ReceptionistResponse.model_validate(json.loads(content))
