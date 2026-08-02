"""SQLite schema migrations for the workbench version history."""


def migrate(conn):
    """Create the version history schema; safe to call on every startup."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS workbench_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workbench_id TEXT NOT NULL,
            version_type TEXT NOT NULL CHECK(version_type IN ('formal', 'test')),
            version TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            commit_sha TEXT NOT NULL DEFAULT '',
            base_formal_version_id INTEGER,
            status TEXT NOT NULL DEFAULT 'recorded',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (base_formal_version_id) REFERENCES workbench_versions(id),
            UNIQUE(workbench_id, version_type, version)
        );

        CREATE INDEX IF NOT EXISTS idx_workbench_versions_scope
            ON workbench_versions(workbench_id, version_type, created_at DESC, id DESC);
        CREATE INDEX IF NOT EXISTS idx_workbench_versions_base_formal
            ON workbench_versions(base_formal_version_id);

        CREATE TABLE IF NOT EXISTS workbench_version_tickets (
            version_id INTEGER NOT NULL,
            ticket_id TEXT NOT NULL,
            ticket_title TEXT NOT NULL DEFAULT '',
            ticket_status TEXT NOT NULL DEFAULT '',
            PRIMARY KEY(version_id, ticket_id),
            FOREIGN KEY (version_id) REFERENCES workbench_versions(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_workbench_version_tickets_ticket
            ON workbench_version_tickets(ticket_id);
        """
    )
    conn.commit()


def run_migrations(conn):
    """Compatibility entry point for callers that use a generic name."""
    migrate(conn)
