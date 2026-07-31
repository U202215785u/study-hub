"""SQLite schema owned by the Butler runtime."""


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
    conn.commit()
