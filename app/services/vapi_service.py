from app.models import CallProvider, ConversationTurn, ReceptionistRequest


class VapiWebhookParser:
    """Extracts normalized call details from Vapi webhook payloads."""

    def parse(self, payload: dict) -> ReceptionistRequest:
        message = payload.get("message", payload)
        call = message.get("call") or payload.get("call") or {}
        transcript = self._parse_transcript(message)

        return ReceptionistRequest(
            provider=CallProvider.vapi,
            call_id=str(call.get("id") or message.get("callId") or payload.get("id") or "unknown"),
            caller_phone=(
                call.get("customer", {}).get("number")
                or call.get("phoneNumber", {}).get("number")
                or payload.get("from")
            ),
            transcript=transcript,
            latest_message=self._latest_user_message(transcript),
        )

    def _parse_transcript(self, message: dict) -> list[ConversationTurn]:
        raw_messages = message.get("messages") or message.get("transcript") or []
        turns: list[ConversationTurn] = []

        if isinstance(raw_messages, str):
            return [ConversationTurn(role="user", content=raw_messages)]

        for item in raw_messages:
            if not isinstance(item, dict):
                continue
            content = item.get("message") or item.get("content") or item.get("text")
            if content:
                turns.append(ConversationTurn(role=item.get("role", "user"), content=content))
        return turns

    def _latest_user_message(self, transcript: list[ConversationTurn]) -> str | None:
        for turn in reversed(transcript):
            if turn.role == "user":
                return turn.content
        return transcript[-1].content if transcript else None
