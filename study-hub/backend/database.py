import sqlite3, os

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "study_hub.db")

def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT DEFAULT '📁',
            color TEXT DEFAULT '#7c8aff',
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            content_type TEXT DEFAULT 'text',
            source TEXT DEFAULT 'upload',
            category_id INTEGER DEFAULT NULL,
            tags TEXT DEFAULT '[]',
            content_hash TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0,
            chunk_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS daily_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            polished TEXT,
            suggestions TEXT,
            related_docs TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS wiki_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            summary TEXT DEFAULT '',
            source_doc_ids TEXT DEFAULT '[]',
            cross_refs TEXT DEFAULT '[]',
            contradictions TEXT DEFAULT '[]',
            tags TEXT DEFAULT '[]',
            category TEXT DEFAULT '',
            version INTEGER DEFAULT 1,
            char_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS wiki_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_page_id INTEGER NOT NULL,
            target_page_slug TEXT NOT NULL,
            link_type TEXT DEFAULT 'reference',
            context TEXT DEFAULT '',
            FOREIGN KEY (source_page_id) REFERENCES wiki_pages(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS skill_patches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL,
            patch_type TEXT NOT NULL CHECK(patch_type IN ('add','replace','insert_after','insert_before','append')),
            target_section TEXT DEFAULT '',
            patch_content TEXT NOT NULL,
            rationale TEXT DEFAULT '',
            source_event_type TEXT DEFAULT '' CHECK(source_event_type IN ('wiki_compile','review_polish','manual','')),
            source_event_id INTEGER DEFAULT 0,
            risk_level TEXT NOT NULL CHECK(risk_level IN ('low','medium','high')),
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','applied','rejected','superseded')),
            file_path TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            applied_at TIMESTAMP,
            rejected_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS document_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_doc_id INTEGER NOT NULL,
            target_title TEXT NOT NULL,
            target_doc_id INTEGER,
            link_text TEXT DEFAULT '',
            FOREIGN KEY (source_doc_id) REFERENCES documents(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_doc_links_source ON document_links(source_doc_id);
        CREATE INDEX IF NOT EXISTS idx_doc_links_target ON document_links(target_title);
        CREATE TABLE IF NOT EXISTS system_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_type TEXT NOT NULL CHECK(snapshot_type IN ('daily','weekly','manual')),
            snapshot_date TEXT NOT NULL,
            skills_json TEXT NOT NULL DEFAULT '[]',
            config_json TEXT NOT NULL DEFAULT '{}',
            wiki_stats_json TEXT NOT NULL DEFAULT '{}',
            review_summary TEXT DEFAULT '',
            evolution_notes TEXT DEFAULT '',
            patch_ids_applied TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    # 兼容旧表：如果 documents 缺少新增列则补充
    for col, sql in [
        ("category_id", "ALTER TABLE documents ADD COLUMN category_id INTEGER DEFAULT NULL"),
        ("tags", "ALTER TABLE documents ADD COLUMN tags TEXT DEFAULT '[]'"),
        ("content_hash", "ALTER TABLE documents ADD COLUMN content_hash TEXT DEFAULT ''"),
    ]:
        try:
            conn.execute(f"SELECT {col} FROM documents LIMIT 1")
        except:
            conn.execute(sql)
    conn.commit()

    # 兼容旧表：wiki_pages 新增框架字段
    for col, sql in [
        ("content_type", "ALTER TABLE wiki_pages ADD COLUMN content_type TEXT DEFAULT ''"),
        ("difficulty", "ALTER TABLE wiki_pages ADD COLUMN difficulty TEXT DEFAULT ''"),
        ("external_links", "ALTER TABLE wiki_pages ADD COLUMN external_links TEXT DEFAULT '[]'"),
        ("prerequisites", "ALTER TABLE wiki_pages ADD COLUMN prerequisites TEXT DEFAULT '[]'"),
        ("next_steps", "ALTER TABLE wiki_pages ADD COLUMN next_steps TEXT DEFAULT '[]'"),
    ]:
        try:
            conn.execute(f"SELECT {col} FROM wiki_pages LIMIT 1")
        except:
            conn.execute(sql)
    conn.commit()

    conn.close()
