# AI Receptionist MVP

AI receptionist for small businesses that captures leads and schedules appointments.

This repository is scaffolded as a Python FastAPI service that can receive voice-call events from Vapi and Twilio, reason over caller intent with OpenAI, and create appointments in Google Calendar.

## MVP scope

- Answer inbound calls through Vapi or Twilio webhooks
- Capture caller name, phone number, requested service, preferred appointment time, and notes
- Use OpenAI to classify intent and produce receptionist responses
- Check Google Calendar availability and create appointment events
- Provide health checks and simple integration seams for deployment

## Project structure

```text
app/
  api/
    routes/
      health.py          # service health endpoint
      vapi.py            # Vapi webhook endpoint
      twilio.py          # Twilio voice webhook endpoint
  core/
    logging.py           # logging setup
  receptionist/
    agent.py             # conversation orchestration
    prompts/
      system.md          # receptionist behavior prompt
  services/
    calendar_service.py  # Google Calendar integration
    openai_service.py    # OpenAI integration
    twilio_service.py    # Twilio response helpers
    vapi_service.py      # Vapi event parsing helpers
  config.py              # environment-based settings
  main.py                # FastAPI application factory
  models.py              # shared Pydantic models
tests/
  test_health.py
```

## Quick start

1. Create a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -e ".[dev]"
   ```

3. Copy environment defaults:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Fill in provider credentials in `.env`.

5. Run the API:

   ```powershell
   uvicorn app.main:app --reload
   ```

6. Visit:

   ```text
   http://127.0.0.1:8000/health
   ```

## Provider setup checklist

- Vapi: point assistant or server webhooks to `/webhooks/vapi`
- Twilio: point the phone number voice webhook to `/webhooks/twilio/voice`
- OpenAI: set `OPENAI_API_KEY`
- Google Calendar: set `GOOGLE_APPLICATION_CREDENTIALS` and `GOOGLE_CALENDAR_ID`

For local webhook testing, expose the server with a tunnel such as ngrok and configure provider webhooks to the public tunnel URL.

## Environment

See `.env.example` for all configuration values.

## Tests

```powershell
pytest
```
