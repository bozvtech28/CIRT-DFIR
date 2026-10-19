PRAGMA foreign_keys = ON;

CREATE TABLE cases (
    case_id TEXT PRIMARY KEY NOT NULL,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    severity TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    status TEXT NOT NULL CHECK (
        status IN ('Triage', 'Investigating', 'Evidence review', 'Contained', 'Closed')
    ),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1)
);

CREATE TABLE audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (length(trim(event_type)) > 0),
    actor_id TEXT NOT NULL CHECK (length(trim(actor_id)) > 0),
    event_time TEXT NOT NULL,
    details_json TEXT NOT NULL CHECK (json_valid(details_json)),
    previous_hash TEXT,
    event_hash TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE RESTRICT
);

CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_severity ON cases(severity);
CREATE INDEX idx_audit_case_time ON audit_events(case_id, event_time);

-- Basic database-level protection against ordinary audit-event edits/deletes.
-- This does not protect against a database administrator or direct file tampering.
CREATE TRIGGER audit_events_no_update
BEFORE UPDATE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'Audit events are append-only');
END;

CREATE TRIGGER audit_events_no_delete
BEFORE DELETE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'Audit events are append-only');
END;