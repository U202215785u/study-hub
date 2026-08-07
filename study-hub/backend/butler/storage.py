"""SQLite schema and persistence helpers owned by the Butler runtime."""

import json


def initialize_butler_schema(conn) -> None:
    """Create Butler tables without changing existing project data."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS butler_tasks (
            id TEXT PRIMARY KEY,
            task_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            feature_code TEXT DEFAULT '',
            status TEXT NOT NULL,
            mode TEXT NOT NULL DEFAULT 'simple',
            risk_level TEXT NOT NULL DEFAULT 'normal',
            attempt_count INTEGER NOT NULL DEFAULT 0,
            current_role TEXT DEFAULT '',
            current_expert TEXT DEFAULT '',
            context_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_butler_tasks_status
            ON butler_tasks(status, updated_at DESC);

        CREATE TABLE IF NOT EXISTS butler_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor TEXT NOT NULL DEFAULT 'butler',
            summary TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(task_id) REFERENCES butler_tasks(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_butler_events_task_time
            ON butler_events(task_id, created_at, id);

        CREATE TABLE IF NOT EXISTS butler_approvals (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            risk_kind TEXT NOT NULL,
            summary TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            response TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            decided_at TIMESTAMP,
            FOREIGN KEY(task_id) REFERENCES butler_tasks(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_butler_approvals_pending
            ON butler_approvals(status, task_id);

        CREATE TABLE IF NOT EXISTS butler_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            summary TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(task_id) REFERENCES butler_tasks(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_butler_evidence_task
            ON butler_evidence(task_id, created_at, id);

        CREATE TABLE IF NOT EXISTS butler_memory_drafts (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            target_path TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            response TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            decided_at TIMESTAMP,
            FOREIGN KEY(task_id) REFERENCES butler_tasks(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_butler_memory_drafts_status
            ON butler_memory_drafts(status, task_id);
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(butler_tasks)").fetchall()}
    if "mode" not in columns:
        # Existing tasks retain the old full-flow behavior during migration.
        conn.execute("ALTER TABLE butler_tasks ADD COLUMN mode TEXT NOT NULL DEFAULT 'complex'")
    conn.execute("UPDATE butler_tasks SET mode = 'complex' WHERE mode IS NULL OR mode = ''")
    conn.commit()


def encode(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def decode(value: str, default):
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return default


def task_from_row(row) -> dict | None:
    if row is None:
        return None
    task = dict(row)
    task.setdefault("mode", "complex")
    task["context"] = decode(task.pop("context_json"), {})
    task["experts"] = tuple(filter(None, task.pop("current_expert").split(",")))
    return task


def event_from_row(row) -> dict:
    event = dict(row)
    event["type"] = event.pop("event_type")
    event["payload"] = decode(event.pop("payload_json"), {})
    return event


def create_task(conn, task: dict) -> dict:
    conn.execute(
        """
        INSERT INTO butler_tasks (
            id, task_type, title, description, feature_code, status, mode, risk_level,
            attempt_count, current_role, current_expert, context_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task["id"], task["task_type"], task["title"], task["description"],
            task["feature_code"], task["status"], task["mode"], task["risk_level"],
            task["attempt_count"], task["current_role"], task["current_expert"],
            encode(task["context"]),
        ),
    )
    return read_task(conn, task["id"])


def read_task(conn, task_id: str) -> dict | None:
    return task_from_row(
        conn.execute("SELECT * FROM butler_tasks WHERE id = ?", (task_id,)).fetchone()
    )


def list_tasks(conn, *, include_archived=False) -> list[dict]:
    query = "SELECT * FROM butler_tasks"
    values = []
    if not include_archived:
        query += " WHERE status != ?"
        values.append("archived")
    query += " ORDER BY updated_at DESC, id DESC"
    return [task_from_row(row) for row in conn.execute(query, values).fetchall()]


def update_task(conn, task_id: str, **changes) -> dict | None:
    if not changes:
        return read_task(conn, task_id)
    values = dict(changes)
    if "context" in values:
        values["context_json"] = encode(values.pop("context"))
    columns = list(values)
    assignments = ", ".join(f"{column} = ?" for column in columns)
    conn.execute(
        f"UPDATE butler_tasks SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [values[column] for column in columns] + [task_id],
    )
    return read_task(conn, task_id)


def append_event(conn, task_id: str, event_type: str, summary: str, *, actor="butler", payload=None) -> dict:
    cursor = conn.execute(
        """
        INSERT INTO butler_events (task_id, event_type, actor, summary, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (task_id, event_type, actor, summary, encode(payload or {})),
    )
    row = conn.execute("SELECT * FROM butler_events WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return event_from_row(row)


def list_events(conn, task_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM butler_events WHERE task_id = ? ORDER BY id", (task_id,)
    ).fetchall()
    return [event_from_row(row) for row in rows]


def evidence_from_row(row) -> dict | None:
    if row is None:
        return None
    evidence = dict(row)
    evidence["payload"] = decode(evidence.pop("payload_json"), {})
    return evidence


def create_evidence(conn, evidence: dict) -> dict:
    cursor = conn.execute(
        """
        INSERT INTO butler_evidence (task_id, evidence_type, summary, location, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            evidence["task_id"], evidence["evidence_type"], evidence["summary"],
            evidence.get("location", ""), encode(evidence.get("payload", {})),
        ),
    )
    row = conn.execute(
        "SELECT * FROM butler_evidence WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return evidence_from_row(row)


def list_evidence(conn, task_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM butler_evidence WHERE task_id = ? ORDER BY id", (task_id,)
    ).fetchall()
    return [evidence_from_row(row) for row in rows]


def approval_from_row(row) -> dict | None:
    return dict(row) if row is not None else None


def create_approval(conn, approval: dict) -> dict:
    conn.execute(
        """
        INSERT INTO butler_approvals (id, task_id, risk_kind, summary, status, response)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            approval["id"], approval["task_id"], approval["risk_kind"],
            approval["summary"], approval["status"], approval.get("response", ""),
        ),
    )
    return read_approval(conn, approval["id"])


def read_approval(conn, approval_id: str) -> dict | None:
    return approval_from_row(
        conn.execute("SELECT * FROM butler_approvals WHERE id = ?", (approval_id,)).fetchone()
    )


def pending_approvals(conn, task_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM butler_approvals WHERE task_id = ? AND status = 'pending' ORDER BY created_at, id",
        (task_id,),
    ).fetchall()
    return [approval_from_row(row) for row in rows]


def resolve_approval(conn, approval_id: str, *, approved: bool, response: str) -> dict | None:
    status = "approved" if approved else "rejected"
    conn.execute(
        """
        UPDATE butler_approvals
        SET status = ?, response = ?, decided_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = 'pending'
        """,
        (status, response, approval_id),
    )
    return read_approval(conn, approval_id)


def memory_draft_from_row(row) -> dict | None:
    return dict(row) if row is not None else None


def create_memory_draft(conn, draft: dict) -> dict:
    conn.execute(
        """
        INSERT INTO butler_memory_drafts (id, task_id, target_path, content, status, response)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            draft["id"], draft["task_id"], draft["target_path"], draft["content"],
            draft["status"], draft.get("response", ""),
        ),
    )
    return read_memory_draft(conn, draft["id"])


def read_memory_draft(conn, draft_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM butler_memory_drafts WHERE id = ?", (draft_id,)
    ).fetchone()
    return memory_draft_from_row(row)


def list_memory_drafts(conn, *, task_id: str | None = None) -> list[dict]:
    query = "SELECT * FROM butler_memory_drafts"
    values = []
    if task_id is not None:
        query += " WHERE task_id = ?"
        values.append(task_id)
    query += " ORDER BY created_at, id"
    return [memory_draft_from_row(row) for row in conn.execute(query, values).fetchall()]


def resolve_memory_draft(conn, draft_id: str, *, approved: bool, response: str) -> dict | None:
    status = "approved" if approved else "rejected"
    conn.execute(
        """
        UPDATE butler_memory_drafts
        SET status = ?, response = ?, decided_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = 'pending'
        """,
        (status, response, draft_id),
    )
    return read_memory_draft(conn, draft_id)
