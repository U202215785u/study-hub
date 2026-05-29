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
    # 防重置：如果数据库文件已存在且有数据，不再执行 CREATE TABLE（DEC-023）
    db_exists = os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0
    conn = get_db()
    if not db_exists:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                icon TEXT DEFAULT '📁',
                color TEXT DEFAULT '#7c8aff',
                sort_order INTEGER DEFAULT 0,
                tag_rules TEXT DEFAULT '[]',
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
                cover_image TEXT DEFAULT '',
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

    # 兼容旧表：categories 新增 tag_rules 字段
    try:
        conn.execute("SELECT tag_rules FROM categories LIMIT 1")
    except:
        conn.execute("ALTER TABLE categories ADD COLUMN tag_rules TEXT DEFAULT '[]'")
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
        ("cover_image", "ALTER TABLE wiki_pages ADD COLUMN cover_image TEXT DEFAULT ''"),
    ]:
        try:
            conn.execute(f"SELECT {col} FROM wiki_pages LIMIT 1")
        except:
            conn.execute(sql)
    conn.commit()

    # 防止 automation 摘要文档重复入库：source + content_hash 联合唯一（仅对非空 content_hash 生效）
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_doc_source_hash
        ON documents(source, content_hash)
        WHERE content_hash != ''
    """)
    conn.commit()

    # 兼容旧表：memories 记忆系统
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            source_tool TEXT DEFAULT 'manual',
            source_ref TEXT DEFAULT '',
            importance INTEGER DEFAULT 3 CHECK(importance BETWEEN 1 AND 5),
            confidence REAL DEFAULT 1.0 CHECK(confidence BETWEEN 0.0 AND 1.0),
            status TEXT DEFAULT 'active' CHECK(status IN ('active','outdated','wrong')),
            embed_id TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
        CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status);
        CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source_tool);
        CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
        CREATE TABLE IF NOT EXISTS memory_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            relation TEXT DEFAULT '相关' CHECK(relation IN ('相关','矛盾','细化','替代')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES memories(id) ON DELETE CASCADE,
            FOREIGN KEY (target_id) REFERENCES memories(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_mem_links_source ON memory_links(source_id);
        CREATE INDEX IF NOT EXISTS idx_mem_links_target ON memory_links(target_id);
    """)
    conn.commit()

    # === 五层记忆系统升级 ===
    # 1. 扩展 memories 表（兼容旧数据）
    _add_column_if_missing(conn, "memories", "memory_layer", "TEXT DEFAULT 'session'")
    _add_column_if_missing(conn, "memories", "project_name", "TEXT DEFAULT ''")
    _add_column_if_missing(conn, "memories", "workflow_name", "TEXT DEFAULT ''")
    _add_column_if_missing(conn, "memories", "memory_type", "TEXT DEFAULT 'fact'")
    _add_column_if_missing(conn, "memories", "access_count", "INTEGER DEFAULT 0")
    _add_column_if_missing(conn, "memories", "last_accessed", "TIMESTAMP")

    # 2. 创建 projects 表
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'paused', 'completed', 'archived')),
            tech_stack TEXT DEFAULT '[]',
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            progress_note TEXT DEFAULT '',
            related_memories TEXT DEFAULT '[]'
        );
        CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
        CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
    """)
    conn.commit()

    # 3. 创建 workflows 表
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            trigger_keywords TEXT DEFAULT '[]',
            preferences TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name);
    """)
    conn.commit()

    # 4. 创建 sessions 表（会话记忆）
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            source_tool TEXT DEFAULT '',
            source_ref TEXT DEFAULT '',
            summary TEXT DEFAULT '',
            raw_dialogue TEXT DEFAULT '',
            extracted_memories TEXT DEFAULT '[]',
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'archived')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_tool ON sessions(source_tool);
        CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);
    """)
    conn.commit()

    conn.close()


def _add_column_if_missing(conn, table, column, definition):
    """兼容添加列：如果列不存在则添加"""
    try:
        conn.execute(f"SELECT {column} FROM {table} LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        conn.commit()
        print(f"[db] 已添加列 {table}.{column}")
