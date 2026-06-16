from xml.sax.saxutils import escape


class TwilioVoiceResponder:
    def voice_response(self, message: str) -> str:
        escaped_message = escape(message)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f"<Say>{escaped_message}</Say>"
            '<Gather input="speech" action="/webhooks/twilio/voice" method="POST" speechTimeout="auto">'
            "<Say>How else can I help?</Say>"
            "</Gather>"
            "</Response>"
        )
