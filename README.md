# AI Receptionist MVP

AI receptionist for small businesses that captures leads and schedules appointments.

This repository is scaffolded as a Python FastAPI service that can receive voice-call events from Vapi and Twilio, reason over caller intent with OpenAI, and create appointments in Google Calendar.

## MVP scope

- Answer inbound calls through Vapi or Twilio webhooks
- Capture caller name, phone number, requested service, preferred appointment time, and notes
- Use OpenAI to classify intent and produce receptionist responses
- Check Google Calendar availability and create appointment events
- Store captured leads in a local SQLite database
- Notify the business owner by email when a lead is captured
- Create Google Calendar events for estimate appointments, with demo mode before credentials are connected
- Provide health checks and simple integration seams for deployment

## Project structure

```text
app/
  api/
    routes/
      health.py          # service health endpoint
      calendar.py        # Google Calendar availability endpoint
      leads.py           # captured lead listing endpoint
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
    email_service.py     # SMTP owner notifications
    lead_store.py        # SQLite lead persistence
    openai_service.py    # OpenAI integration
    twilio_service.py    # Twilio response helpers
    vapi_service.py      # Vapi event parsing helpers
  config.py              # environment-based settings
  main.py                # FastAPI application factory
  models.py              # shared Pydantic models
samples/
  vapi_webhook.json      # local Vapi webhook test payload
scripts/
  setup_env.ps1          # creates .env from .env.example
  run_local.ps1          # runs the local FastAPI server
tests/
  test_health.py
```

## Local setup

1. Create a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -e ".[dev]"
   ```

3. Create your local `.env` file:

   ```powershell
   .\scripts\setup_env.ps1
   ```

4. For a local smoke test, you can leave provider keys blank. The app will still accept the sample webhook and store a basic lead record.

5. To test real OpenAI responses, set this in `.env`:

   ```text
   OPENAI_API_KEY=your_api_key_here
   ```

6. Google Calendar can run in demo mode or real mode.

   Demo mode is automatic when `GOOGLE_CALENDAR_ID` or `GOOGLE_APPLICATION_CREDENTIALS` is blank. In demo mode:

   - `/calendar/available-slots` returns sample slots from your configured business hours.
   - Captured estimate requests receive a fake event ID like `demo-event-20260618T140000`.
   - Responses clearly include `demo_mode: true` where calendar availability is returned.
   - No Google API calls are made.

   To use real Google Calendar mode, set:

   ```text
   GOOGLE_CALENDAR_ID=your_calendar_id_here
   GOOGLE_APPLICATION_CREDENTIALS=C:\absolute\path\to\service-account.json
   ESTIMATE_DURATION_MINUTES=60
   BUSINESS_START_HOUR=9
   BUSINESS_END_HOUR=17
   ```

   Google Calendar setup:

   - Create or choose a Google Cloud project.
   - Enable the Google Calendar API.
   - Create a service account and download its JSON key.
   - Share the target Google Calendar with the service account email.
   - Give the service account permission to make changes to events.
   - Put the calendar ID in `GOOGLE_CALENDAR_ID`.
   - Put the absolute path to the JSON key in `GOOGLE_APPLICATION_CREDENTIALS`.

7. To send real owner email notifications, set:

   ```text
   SMTP_HOST=smtp.example.com
   SMTP_PORT=587
   SMTP_USERNAME=your_smtp_username
   SMTP_PASSWORD=your_smtp_password
   SMTP_FROM_EMAIL=receptionist@example.com
   OWNER_EMAIL=owner@example.com
   ```

   If these values are blank, the app logs the formatted owner notification instead of sending email.

## Run locally

Start the API:

   ```powershell
   .\scripts\run_local.ps1
   ```

The local run command starts:

   ```text
   http://127.0.0.1:8000
   ```

Useful local URLs:

- Health check: `http://127.0.0.1:8000/health`
- Leads: `http://127.0.0.1:8000/leads`
- Available slots: `http://127.0.0.1:8000/calendar/available-slots?appointment_date=2026-06-18`
- API docs: `http://127.0.0.1:8000/docs`

## Test locally

Run these commands in a second PowerShell window while the API is running.

1. Confirm the server is healthy:

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/health
   ```

2. Send the sample Vapi webhook payload:

   ```powershell
   Invoke-RestMethod `
     -Method Post `
     -Uri http://127.0.0.1:8000/webhooks/vapi `
     -ContentType "application/json" `
     -InFile .\samples\vapi_webhook.json
   ```

3. View captured leads:

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/leads
   ```

4. View available estimate slots:

   ```powershell
   Invoke-RestMethod "http://127.0.0.1:8000/calendar/available-slots?appointment_date=2026-06-18"
   ```

   Without Google credentials, this returns demo slots and `demo_mode: true`. With Google credentials, this returns real open slots after checking Google Calendar free/busy data.

The sample payload represents a painting company estimate request from Maria Gomez. The app should capture her name, phone number, exterior painting estimate service, June 18, 2026 at 2:00 PM preferred start time, June 18, 2026 at 3:00 PM preferred end time, and `book_appointment` intent.

In demo mode, the app stores a fake event ID on the lead as `google_calendar_event_id`, and the Vapi webhook response includes `demoMode: true` plus `calendarEventId`. In real Google Calendar mode, if the requested time is free, the app creates an estimate appointment event and stores the returned Google event ID. If the requested time overlaps an existing calendar event, the app logs that the slot is unavailable and does not create a duplicate event.

When that lead is captured, the app also prepares an owner email summary with caller name, phone, service requested, preferred time, notes, and call ID. Without SMTP settings, the summary appears in the app logs.

The SQLite database is created automatically at `data/leads.db`. The `data/` directory is ignored by Git so local test data stays local.

## Provider setup checklist

- Vapi: point assistant or server webhooks to `/webhooks/vapi`
- Twilio: point the phone number voice webhook to `/webhooks/twilio/voice`
- OpenAI: set `OPENAI_API_KEY`
- Google Calendar: set `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_CALENDAR_ID`, business hours, and estimate duration
- SMTP: set `SMTP_HOST`, `SMTP_FROM_EMAIL`, and `OWNER_EMAIL` to enable owner notifications

For local webhook testing, expose the server with a tunnel such as ngrok and configure provider webhooks to the public tunnel URL.

## Environment

See `.env.example` for all configuration values.

## Tests

```powershell
pytest
```
