import os
from pathlib import Path
from typing import Any

from app.case_repository import connect, create_case, initialize, list_cases

APP_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = APP_DIR / "case_schema.sql"
DEFAULT_DB = APP_DIR.parent / "data" / "cirt_cases.sqlite"
DB_PATH = Path(os.environ.get("CIRT_DFIR_DB_PATH", str(DEFAULT_DB)))


def ensure_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Initialize only a new/empty database; never reapply CREATE statements
    # to an existing database.
    needs_init = not DB_PATH.exists() or DB_PATH.stat().st_size == 0
    if needs_init:
        initialize(DB_PATH, SCHEMA_PATH)

    db = connect(DB_PATH)
    try:
        row = db.execute("SELECT COUNT(*) AS total FROM cases").fetchone()
        total = int(row["total"])
    finally:
        db.close()

    # Seed only empty databases, using synthetic demo records.
    if total == 0:
        timestamp = "2026-10-15T00:00:00Z"
        demo_records = [
            ("DEMO-2026-001", "Endpoint Alert Review", "High", "Investigating"),
            ("DEMO-2026-002", "Suspicious Login Review", "Medium", "Triage"),
            ("DEMO-2026-003", "Mailbox Rule Assessment", "Medium", "Evidence review"),
        ]

        db = connect(DB_PATH)
        try:
            for case_id, title, severity, status in demo_records:
                create_case(
                    db,
                    case_id=case_id,
                    title=title,
                    severity=severity,
                    status=status,
                    actor_id="DEMO-SYSTEM",
                    timestamp=timestamp,
                )
        finally:
            db.close()


def list_demo_cases() -> list[dict[str, Any]]:
    ensure_database()
    db = connect(DB_PATH)
    try:
        return list_cases(db)
    finally:
        db.close()