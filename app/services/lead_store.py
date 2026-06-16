import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.config import settings
from app.models import LeadCapture, LeadRecord, ReceptionistRequest, ReceptionistResponse


class LeadStore:
    def __init__(self, database_path: str | None = None) -> None:
        self.database_path = Path(database_path or settings.database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    call_id TEXT NOT NULL,
                    caller_name TEXT,
                    caller_phone TEXT,
                    service_requested TEXT,
                    preferred_start TEXT,
                    preferred_end TEXT,
                    notes TEXT,
                    intent TEXT NOT NULL,
                    google_calendar_event_id TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._add_column_if_missing(connection, "google_calendar_event_id", "TEXT")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC)"
            )

    def save_from_receptionist(
        self,
        request: ReceptionistRequest,
        response: ReceptionistResponse,
    ) -> int | None:
        lead = self._merge_request_context(request, response.lead)
        if not self._has_lead_data(lead):
            return None

        self.initialize()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO leads (
                    provider,
                    call_id,
                    caller_name,
                    caller_phone,
                    service_requested,
                    preferred_start,
                    preferred_end,
                    notes,
                    intent,
                    google_calendar_event_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.provider.value,
                    request.call_id,
                    lead.caller_name,
                    lead.caller_phone,
                    lead.service_requested,
                    self._datetime_to_text(lead.preferred_start),
                    self._datetime_to_text(lead.preferred_end),
                    lead.notes,
                    response.intent.value,
                    None,
                    datetime.now(UTC).isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def update_calendar_event_id(self, lead_id: int, event_id: str) -> None:
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                "UPDATE leads SET google_calendar_event_id = ? WHERE id = ?",
                (event_id, lead_id),
            )

    def list_leads(self, limit: int = 50) -> list[LeadRecord]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    provider,
                    call_id,
                    caller_name,
                    caller_phone,
                    service_requested,
                    preferred_start,
                    preferred_end,
                    notes,
                    intent,
                    google_calendar_event_id,
                    created_at
                FROM leads
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _merge_request_context(
        self,
        request: ReceptionistRequest,
        lead: LeadCapture,
    ) -> LeadCapture:
        return lead.model_copy(
            update={
                "caller_phone": lead.caller_phone or request.caller_phone,
                "notes": lead.notes or request.latest_message,
            }
        )

    def _has_lead_data(self, lead: LeadCapture) -> bool:
        return any(
            [
                lead.caller_name,
                lead.caller_phone,
                lead.service_requested,
                lead.preferred_start,
                lead.preferred_end,
                lead.notes,
            ]
        )

    def _row_to_record(self, row: sqlite3.Row) -> LeadRecord:
        return LeadRecord(
            id=row["id"],
            provider=row["provider"],
            call_id=row["call_id"],
            caller_name=row["caller_name"],
            caller_phone=row["caller_phone"],
            service_requested=row["service_requested"],
            preferred_start=self._text_to_datetime(row["preferred_start"]),
            preferred_end=self._text_to_datetime(row["preferred_end"]),
            notes=row["notes"],
            intent=row["intent"],
            google_calendar_event_id=row["google_calendar_event_id"],
            created_at=self._text_to_datetime(row["created_at"]) or datetime.now(UTC),
        )

    def _add_column_if_missing(
        self,
        connection: sqlite3.Connection,
        column_name: str,
        column_type: str,
    ) -> None:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(leads)").fetchall()
        }
        if column_name not in columns:
            connection.execute(f"ALTER TABLE leads ADD COLUMN {column_name} {column_type}")

    def _datetime_to_text(self, value: datetime | None) -> str | None:
        return value.isoformat() if value else None

    def _text_to_datetime(self, value: str | None) -> datetime | None:
        return datetime.fromisoformat(value) if value else None
