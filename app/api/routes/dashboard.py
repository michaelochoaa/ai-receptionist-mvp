from html import escape

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.models import LeadRecord, LeadStatus
from app.services.lead_store import LeadStore

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    leads = LeadStore().list_leads(limit=200)
    rows = "\n".join(_lead_row(lead) for lead in leads)
    if not rows:
        rows = '<tr><td colspan="6">No leads captured yet.</td></tr>'

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>AI Receptionist Leads</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background: #f3f3f3; }}
    select, button {{ font: inherit; }}
  </style>
</head>
<body>
  <h1>Leads</h1>
  <table>
    <thead>
      <tr>
        <th>Name</th>
        <th>Phone</th>
        <th>Service</th>
        <th>Appointment Time</th>
        <th>Status</th>
        <th>Created Date</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>"""
    return HTMLResponse(html)


def _lead_row(lead: LeadRecord) -> str:
    return f"""<tr>
  <td>{_value(lead.caller_name)}</td>
  <td>{_value(lead.caller_phone)}</td>
  <td>{_value(lead.service_requested)}</td>
  <td>{_datetime(lead.preferred_start)}</td>
  <td>{_status_form(lead)}</td>
  <td>{_datetime(lead.created_at)}</td>
</tr>"""


def _status_form(lead: LeadRecord) -> str:
    options = "\n".join(
        f'<option value="{status.value}"{" selected" if status == lead.status else ""}>'
        f"{status.value}</option>"
        for status in LeadStatus
    )
    return f"""<form method="post" action="/leads/{lead.id}/status">
  <select name="status">{options}</select>
  <button type="submit">Save</button>
</form>"""


def _value(value: str | None) -> str:
    return escape(value or "Not provided")


def _datetime(value) -> str:
    if not value:
        return "Not provided"
    return escape(value.strftime("%Y-%m-%d %I:%M %p"))
