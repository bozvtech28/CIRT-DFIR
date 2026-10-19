import json
import sqlite3
from pathlib import Path
from typing import Any


def connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(database_path: str | Path, schema_path: str | Path) -> None:
    schema = Path(schema_path).read_text(encoding="utf-8")
    db = connect(database_path)
    try:
        db.executescript(schema)
        db.commit()
    finally:
        db.close()


def create_case(
    db: sqlite3.Connection,
    *,
    case_id: str,
    title: str,
    severity: str,
    status: str,
    actor_id: str,
    timestamp: str,
) -> dict[str, Any]:
    if not all(isinstance(value, str) and value.strip() for value in (
        case_id, title, severity, status, actor_id, timestamp
    )):
        raise ValueError("Case fields, actor, and timestamp must be non-empty strings.")

    details = json.dumps(
        {"synthetic": True, "action": "case_created"},
        sort_keys=True,
        separators=(",", ":"),
    )

    with db:
        db.execute(
            """INSERT INTO cases
               (case_id, title, severity, status, created_at, updated_at, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (case_id, title, severity, status, timestamp, timestamp, actor_id),
        )
        db.execute(
            """INSERT INTO audit_events
               (case_id, event_type, actor_id, event_time, details_json)
               VALUES (?, ?, ?, ?, ?)""",
            (case_id, "CASE_CREATED", actor_id, timestamp, details),
        )

    return get_case(db, case_id)




def update_case(
    db: sqlite3.Connection,
    *,
    case_id: str,
    actor_id: str,
    timestamp: str,
    status: str | None = None,
    severity: str | None = None,
) -> dict[str, Any] | None:
    """Update case status/severity and append an audit event atomically."""
    import json

    if not isinstance(actor_id, str) or not actor_id.strip():
        raise ValueError("actor_id must be a non-empty string.")
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("timestamp must be a non-empty string.")
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("case_id must be a non-empty string.")

    allowed_statuses = {
        "Triage", "Investigating", "Evidence review", "Contained", "Closed"
    }
    allowed_severities = {"Low", "Medium", "High", "Critical"}

    if status is not None and status not in allowed_statuses:
        raise ValueError("Unsupported case status.")
    if severity is not None and severity not in allowed_severities:
        raise ValueError("Unsupported case severity.")
    if status is None and severity is None:
        raise ValueError("Provide status, severity, or both.")

    before_row = db.execute(
        """SELECT case_id, title, severity, status, created_at,
                  updated_at, created_by
           FROM cases WHERE case_id = ?""",
        (case_id,),
    ).fetchone()

    if before_row is None:
        return None

    before = dict(before_row)
    new_status = status if status is not None else before["status"]
    new_severity = severity if severity is not None else before["severity"]

    if new_status == before["status"] and new_severity == before["severity"]:
        raise ValueError("Update contains no case changes.")

    details = json.dumps(
        {
            "synthetic": True,
            "before": {
                "status": before["status"],
                "severity": before["severity"],
            },
            "after": {
                "status": new_status,
                "severity": new_severity,
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    try:
        db.execute(
            """UPDATE cases
               SET status = ?, severity = ?, updated_at = ?
               WHERE case_id = ?""",
            (new_status, new_severity, timestamp, case_id),
        )
        db.execute(
            """INSERT INTO audit_events
               (case_id, event_type, actor_id, event_time, details_json)
               VALUES (?, ?, ?, ?, ?)""",
            (case_id, "CASE_UPDATED", actor_id.strip(), timestamp, details),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    updated = db.execute(
        """SELECT case_id, title, severity, status, created_at,
                  updated_at, created_by
           FROM cases WHERE case_id = ?""",
        (case_id,),
    ).fetchone()
    return dict(updated) if updated is not None else None


def get_case(db: sqlite3.Connection, case_id: str) -> dict[str, Any] | None:
    row = db.execute(
        """SELECT case_id, title, severity, status, created_at,
                  updated_at, created_by, version
           FROM cases WHERE case_id = ?""",
        (case_id,),
    ).fetchone()
    return dict(row) if row else None


def list_cases(db: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = db.execute(
        """SELECT case_id, title, severity, status, created_at,
                  updated_at, created_by, version
           FROM cases ORDER BY created_at, case_id"""
    ).fetchall()
    return [dict(row) for row in rows]


def list_audit_events(
    db: sqlite3.Connection, case_id: str
) -> list[dict[str, Any]]:
    rows = db.execute(
        """SELECT event_id, case_id, event_type, actor_id,
                  event_time, details_json, previous_hash, event_hash
           FROM audit_events
           WHERE case_id = ?
           ORDER BY event_id""",
        (case_id,),
    ).fetchall()
    return [dict(row) for row in rows]