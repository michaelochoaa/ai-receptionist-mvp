# AI Receptionist MVP

AI receptionist for small businesses that captures leads and schedules appointments.

This repository is scaffolded as a Python FastAPI service that can receive voice-call events from Vapi and Twilio, reason over caller intent with OpenAI, and create appointments in Google Calendar.

## MVP scope

- Answer inbound calls through Vapi or Twilio webhooks
- Capture caller name, phone number, requested service, preferred appointment time, and notes
- Use OpenAI to classify intent and produce receptionist responses
- Check Google Calendar availability and create appointment events
- Store captured leads in a local SQLite database
- View captured leads in a simple local dashboard
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
      dashboard.py       # simple HTML lead dashboard
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
- Dashboard: `http://127.0.0.1:8000/dashboard`
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

4. Open the demo dashboard:

   ```text
   http://127.0.0.1:8000/dashboard
   ```

   The dashboard shows all leads in a table with name, phone, service, appointment time, status, and created date. Status values are `New`, `Contacted`, `Scheduled`, and `Closed`.

5. Update a lead status from PowerShell:

   ```powershell
   Invoke-RestMethod `
     -Method Post `
     -Uri http://127.0.0.1:8000/leads/1/status `
     -ContentType "application/x-www-form-urlencoded" `
     -Body @{ status = "Contacted" }
   ```

6. View available estimate slots:

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

## Vapi live demo setup

Use this flow when you are ready to test the MVP with a real phone call through Vapi.

1. Start the local API:

   ```powershell
   .\scripts\run_local.ps1
   ```

2. Expose the local server with a public HTTPS tunnel:

   ```powershell
   ngrok http 8000
   ```

3. Copy the HTTPS forwarding URL from ngrok. It will look like:

   ```text
   https://abc123.ngrok-free.app
   ```

4. In Vapi, set the assistant server/webhook URL to:

   ```text
   https://abc123.ngrok-free.app/webhooks/vapi
   ```

5. If `VAPI_WEBHOOK_SECRET` is set in `.env`, configure Vapi to send the same value in the `x-vapi-secret` header. For the simplest demo, leave `VAPI_WEBHOOK_SECRET` blank.

6. In Vapi, connect the assistant to a phone number and place a test call.

During the demo, leave Google Calendar credentials blank if you want demo mode. The app will still create demo event IDs and show leads in the dashboard.

## Vapi webhook URL format

Local URL:

```text
http://127.0.0.1:8000/webhooks/vapi
```

Public demo URL through ngrok:

```text
https://YOUR-NGROK-SUBDOMAIN.ngrok-free.app/webhooks/vapi
```

Production URL:

```text
https://YOUR-DOMAIN.com/webhooks/vapi
```

The endpoint accepts Vapi call/transcript webhook payloads and returns a JSON response with the receptionist message, intent, booking flags, calendar event ID, and demo mode flag.

## Sample Vapi assistant prompt

Use this as the assistant system prompt for an Ochoa Painting demo:

```text
You are the friendly phone receptionist for Ochoa Painting.

Your job is to help callers request painting estimates. Keep responses short, warm, and natural for a phone call.

Collect these details:
- Caller name
- Best phone number
- Service requested, such as interior painting, exterior painting, cabinet painting, drywall repair, or a painting estimate
- Preferred day and time for an estimate
- Brief notes about the project

If the caller asks for an estimate, ask one question at a time until you have the name, phone number, service, and preferred time.

Do not promise that the appointment is confirmed. Say that you will pass the request to the owner for follow-up.

Example closing:
"Thanks, I have your estimate request. Someone from Ochoa Painting will follow up to confirm the appointment."
```

## Phone call demo script

Use this simple script when calling the Vapi number:

```text
Assistant: Thanks for calling Ochoa Painting. How can I help today?

Caller: Hi, this is Maria Gomez. I need an estimate for exterior painting.

Assistant: I can help with that. What is the best phone number for you?

Caller: 555-321-7890.

Assistant: What day and time would you prefer for the estimate?

Caller: June 18, 2026 at 2 PM.

Assistant: Great. Any quick notes about the project?

Caller: It is a two-story house and the trim needs repainting.

Assistant: Thanks, I have your estimate request. Someone from Ochoa Painting will follow up to confirm the appointment.
```

After the call:

1. Open the dashboard:

   ```text
   http://127.0.0.1:8000/dashboard
   ```

2. Confirm the lead appears with the caller name, phone, service, appointment time, status, and created date.

3. If SMTP is configured, confirm the owner received the lead summary email.

## Vapi webhook troubleshooting

- If Vapi shows webhook failures, confirm the API is running at `http://127.0.0.1:8000/health`.
- If Vapi cannot reach the webhook, confirm ngrok is still running and that the Vapi webhook URL uses the current HTTPS ngrok URL.
- If the app returns `401`, either remove `VAPI_WEBHOOK_SECRET` from `.env` for the demo or configure Vapi to send the matching `x-vapi-secret` header.
- If no lead appears in `/dashboard`, check the app terminal logs and confirm Vapi is sending transcript messages in the webhook payload.
- If the call works but calendar booking looks fake, that is expected in demo mode when Google Calendar credentials are blank.
- If ngrok says the tunnel is offline, restart `ngrok http 8000` and update the webhook URL in Vapi.
- If you changed `.env`, restart the local API so the new environment values are loaded.

## Environment

See `.env.example` for all configuration values.

## Tests

```powershell
pytest
```
