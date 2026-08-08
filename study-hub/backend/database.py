import sqlite3, os

from butler.storage import initialize_butler_schema

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "study_hub.db")

def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def _migrate_ddl_tasks(conn):
    """为 ddl_tasks 表增加时间计划字段（兼容已有数据）"""
    cols = [row[1] for row in conn.execute("PRAGMA table_info(ddl_tasks)").fetchall()]
    if 'plan_type' not in cols:
        conn.execute("ALTER TABLE ddl_tasks ADD COLUMN plan_type TEXT DEFAULT 'todo'")
    if 'plan_date' not in cols:
        conn.execute("ALTER TABLE ddl_tasks ADD COLUMN plan_date TEXT DEFAULT NULL")
    if 'start_time' not in cols:
        conn.execute("ALTER TABLE ddl_tasks ADD COLUMN start_time TEXT DEFAULT NULL")
    if 'end_time' not in cols:
        conn.execute("ALTER TABLE ddl_tasks ADD COLUMN end_time TEXT DEFAULT NULL")
    if 'plan_date' in cols and 'idx_ddl_plan_date' not in [r[1] for r in conn.execute("SELECT * FROM sqlite_master WHERE type='index' AND tbl_name='ddl_tasks'").fetchall()]:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ddl_plan_date ON ddl_tasks(plan_date)")
    conn.commit()


def _migrate_ddl_categories(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS ddl_categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, sort_order INTEGER NOT NULL DEFAULT 0, is_system INTEGER NOT NULL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    columns = {row[1] for row in conn.execute("PRAGMA table_info(ddl_tasks)").fetchall()}
    if "category_id" not in columns:
        conn.execute("ALTER TABLE ddl_tasks ADD COLUMN category_id INTEGER DEFAULT NULL")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ddl_category_id ON ddl_tasks(category_id)")
    for name, order, system in (("待办", 0, 0), ("学习任务", 1, 0), ("里程碑", 2, 0), ("未分类", 3, 1)):
        conn.execute("INSERT OR IGNORE INTO ddl_categories (name, sort_order, is_system) VALUES (?, ?, ?)", (name, order, system))
    for legacy, name in (("todo", "待办"), ("learning", "学习任务"), ("milestone", "里程碑")):
        conn.execute("UPDATE ddl_tasks SET category_id = (SELECT id FROM ddl_categories WHERE name = ?) WHERE category_id IS NULL AND task_type = ?", (name, legacy))
    conn.execute("UPDATE ddl_tasks SET category_id = (SELECT id FROM ddl_categories WHERE is_system = 1 LIMIT 1) WHERE category_id IS NULL")
    conn.commit()


def init_db():
    # 防重置：如果数据库文件已存在且有数据，不再执行 CREATE TABLE（DEC-023）
    db_exists = os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS secure_settings (
            name TEXT PRIMARY KEY,
            encrypted_value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 热力图偏好必须每次启动幂等建表，不能放入 DEC-023 的首次建库分支。
    conn.execute("""
        CREATE TABLE IF NOT EXISTS heatmap_preferences (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            style_id TEXT NOT NULL DEFAULT 'grid',
            settings_json TEXT NOT NULL DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
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
                tutorial_markdown TEXT DEFAULT '',
                tutorial_status TEXT DEFAULT 'not_requested',
                tutorial_reason TEXT DEFAULT '',
                parse_options TEXT DEFAULT '{}',
                source_key TEXT DEFAULT '',
                source_url TEXT DEFAULT '',
                document_status TEXT NOT NULL DEFAULT 'active',
                duplicate_of_document_id INTEGER DEFAULT NULL,
                asr_status TEXT NOT NULL DEFAULT 'not_applicable',
                asr_error TEXT DEFAULT '',
                char_count INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS document_source_claims (
                source TEXT NOT NULL,
                source_key TEXT NOT NULL,
                document_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source, source_key),
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
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
        ("tutorial_markdown", "ALTER TABLE documents ADD COLUMN tutorial_markdown TEXT DEFAULT ''"),
        ("tutorial_status", "ALTER TABLE documents ADD COLUMN tutorial_status TEXT DEFAULT 'not_requested'"),
        ("tutorial_reason", "ALTER TABLE documents ADD COLUMN tutorial_reason TEXT DEFAULT ''"),
        ("parse_options", "ALTER TABLE documents ADD COLUMN parse_options TEXT DEFAULT '{}'"),
        ("source_key", "ALTER TABLE documents ADD COLUMN source_key TEXT DEFAULT ''"),
        ("source_url", "ALTER TABLE documents ADD COLUMN source_url TEXT DEFAULT ''"),
        ("document_status", "ALTER TABLE documents ADD COLUMN document_status TEXT NOT NULL DEFAULT 'active'"),
        ("duplicate_of_document_id", "ALTER TABLE documents ADD COLUMN duplicate_of_document_id INTEGER DEFAULT NULL"),
        ("asr_status", "ALTER TABLE documents ADD COLUMN asr_status TEXT NOT NULL DEFAULT 'not_applicable'"),
        ("asr_error", "ALTER TABLE documents ADD COLUMN asr_error TEXT DEFAULT ''"),
        # SQLite ALTER TABLE only permits constant defaults. Backfill below retains stable pagination ordering.
        ("updated_at", "ALTER TABLE documents ADD COLUMN updated_at TEXT DEFAULT ''"),
    ]:
        try:
            conn.execute(f"SELECT {col} FROM documents LIMIT 1")
        except:
            conn.execute(sql)
    conn.commit()
    conn.execute("UPDATE documents SET updated_at = created_at WHERE updated_at IS NULL OR updated_at = ''")
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

    # DDL 任务面板
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ddl_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            due_date TEXT,
            task_type TEXT DEFAULT 'todo' CHECK(task_type IN ('milestone','todo','learning')),
            project_id INTEGER DEFAULT NULL,
            status TEXT DEFAULT 'todo' CHECK(status IN ('todo','in_progress','done')),
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_ddl_status ON ddl_tasks(status);
        CREATE INDEX IF NOT EXISTS idx_ddl_due_date ON ddl_tasks(due_date);
        CREATE INDEX IF NOT EXISTS idx_ddl_type ON ddl_tasks(task_type);
    """)
    # 迁移：为已有 ddl_tasks 表增加时间计划字段（plan_type, plan_date, start_time, end_time）
    _migrate_ddl_tasks(conn)
    _migrate_ddl_categories(conn)
    conn.commit()

    # 任务队列持久化（防止重启丢失解析任务）
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS task_queue (
            task_id TEXT PRIMARY KEY,
            module_id TEXT NOT NULL,
            module_name TEXT DEFAULT '',
            input_text TEXT NOT NULL,
            input_hash TEXT DEFAULT '',
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending','extracting','summarizing','importing','done','error')),
            progress TEXT DEFAULT '',
            error TEXT DEFAULT '',
            result_doc_id INTEGER DEFAULT NULL,
            result_title TEXT DEFAULT '',
            steps_json TEXT DEFAULT '[]',
            current_step TEXT DEFAULT '',
            api_key_error INTEGER DEFAULT 0,
            api_key_error_msg TEXT DEFAULT '',
            replace_doc_id INTEGER DEFAULT NULL,
            include_tutorial INTEGER DEFAULT 0,
            document_id INTEGER DEFAULT NULL,
            reparse_mode TEXT DEFAULT '',
            asr_status TEXT DEFAULT '',
            asr_error TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_task_status ON task_queue(status);
        CREATE INDEX IF NOT EXISTS idx_task_input_hash ON task_queue(input_hash);
        CREATE INDEX IF NOT EXISTS idx_task_created ON task_queue(created_at);
    """)
    conn.commit()

    _add_column_if_missing(conn, "task_queue", "include_tutorial", "INTEGER DEFAULT 0")
    _add_column_if_missing(conn, "task_queue", "document_id", "INTEGER DEFAULT NULL")
    _add_column_if_missing(conn, "task_queue", "reparse_mode", "TEXT DEFAULT ''")
    _add_column_if_missing(conn, "task_queue", "asr_status", "TEXT DEFAULT ''")
    _add_column_if_missing(conn, "task_queue", "asr_error", "TEXT DEFAULT ''")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS document_source_claims (
            source TEXT NOT NULL,
            source_key TEXT NOT NULL,
            document_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source, source_key),
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_active_source_key ON documents(source, source_key, document_status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_active_created_id ON documents(document_status, created_at DESC, id DESC)")
    conn.commit()

    # SOP 规范化模块
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sop_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            content TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            source_wiki_page_id INTEGER DEFAULT NULL,
            source_type TEXT DEFAULT 'manual' CHECK(source_type IN ('manual','wiki')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_wiki_page_id) REFERENCES wiki_pages(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS sop_chains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sop_chain_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_id INTEGER NOT NULL,
            block_id INTEGER NOT NULL,
            sort_order INTEGER DEFAULT 0,
            parent_id INTEGER DEFAULT NULL,
            branch_label TEXT DEFAULT '',
            FOREIGN KEY (chain_id) REFERENCES sop_chains(id) ON DELETE CASCADE,
            FOREIGN KEY (block_id) REFERENCES sop_blocks(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES sop_chain_blocks(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_sop_cb_chain ON sop_chain_blocks(chain_id);
        CREATE INDEX IF NOT EXISTS idx_sop_cb_sort ON sop_chain_blocks(chain_id, sort_order);
        CREATE TABLE IF NOT EXISTS sop_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            suggestion_type TEXT NOT NULL,
            wiki_page_id INTEGER DEFAULT NULL,
            block_id INTEGER DEFAULT NULL,
            chain_id INTEGER DEFAULT NULL,
            suggested_title TEXT DEFAULT '',
            suggested_content TEXT DEFAULT '',
            rationale TEXT DEFAULT '',
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending','confirmed','rejected')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (wiki_page_id) REFERENCES wiki_pages(id) ON DELETE SET NULL,
            FOREIGN KEY (block_id) REFERENCES sop_blocks(id) ON DELETE SET NULL,
            FOREIGN KEY (chain_id) REFERENCES sop_chains(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_sop_sug_status ON sop_suggestions(status);
    """)
    conn.commit()

    # Skill 市场：社区 Skill 缓存表
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS community_skills (
            id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            category TEXT DEFAULT '',
            sub_category TEXT DEFAULT '',
            primary_link TEXT NOT NULL,
            secondary_link TEXT DEFAULT '',
            author_name TEXT DEFAULT '',
            author_link TEXT DEFAULT '',
            license TEXT DEFAULT '',
            description TEXT DEFAULT '',
            stars INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            date_added TEXT DEFAULT '',
            last_modified TEXT DEFAULT '',
            last_checked TEXT DEFAULT '',
            repo_created TEXT DEFAULT '',
            latest_release TEXT DEFAULT '',
            release_version TEXT DEFAULT '',
            release_source TEXT DEFAULT '',
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_cs_category ON community_skills(category);
        CREATE INDEX IF NOT EXISTS idx_cs_stars ON community_skills(stars);
        CREATE INDEX IF NOT EXISTS idx_cs_active ON community_skills(active);
        CREATE INDEX IF NOT EXISTS idx_cs_synced ON community_skills(synced_at);
    """)
    conn.commit()

    # Skill 市场：本地已安装 Skill 记录
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS local_skills (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            source TEXT DEFAULT 'claude' CHECK(source IN ('claude','agents','kimi')),
            install_path TEXT NOT NULL,
            github_url TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1,
            config_json TEXT DEFAULT '{}',
            installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_ls_source ON local_skills(source);
        CREATE INDEX IF NOT EXISTS idx_ls_enabled ON local_skills(enabled);
    """)
    conn.commit()

    # 手账日记表
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL DEFAULT '',
            mood TEXT DEFAULT 'neutral' CHECK(mood IN ('happy','excited','calm','neutral','tired','sad','angry','loved')),
            tags TEXT DEFAULT '[]',
            weather TEXT DEFAULT '',
            location TEXT DEFAULT '',
            sticker TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(date);
        CREATE INDEX IF NOT EXISTS idx_journal_mood ON journal_entries(mood);
    """)
    conn.commit()

    # 运营流水线：内容项目表（选题→发布全生命周期）
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS content_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            topic_idea TEXT DEFAULT '',
            platform TEXT DEFAULT '',
            status TEXT DEFAULT 'idea' CHECK(status IN ('idea','script','recording','editing','cover','ready','published','archived')),
            script_content TEXT DEFAULT '',
            script_audio_url TEXT DEFAULT '',
            video_path TEXT DEFAULT '',
            cover_image_url TEXT DEFAULT '',
            published_urls TEXT DEFAULT '{}',
            tags TEXT DEFAULT '[]',
            scheduled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_cp_status ON content_projects(status);
        CREATE INDEX IF NOT EXISTS idx_cp_platform ON content_projects(platform);
        CREATE INDEX IF NOT EXISTS idx_cp_created ON content_projects(created_at);

        CREATE TABLE IF NOT EXISTS topic_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT DEFAULT '',
            trend_score INTEGER DEFAULT 0,
            used_in_project_id INTEGER DEFAULT NULL,
            tags TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (used_in_project_id) REFERENCES content_projects(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ti_used ON topic_ideas(used_in_project_id);

        CREATE TABLE IF NOT EXISTS platform_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            account_name TEXT NOT NULL,
            account_id TEXT DEFAULT '',
            avatar_url TEXT DEFAULT '',
            followers_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            config_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_pa_platform ON platform_accounts(platform);

        CREATE TABLE IF NOT EXISTS monitored_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            title TEXT DEFAULT '',
            last_content_hash TEXT DEFAULT '',
            last_content TEXT DEFAULT '',
            last_checked TIMESTAMP,
            change_detected INTEGER DEFAULT 0,
            change_count INTEGER DEFAULT 0,
            notify_enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_mu_checked ON monitored_urls(last_checked);
    """)
    conn.commit()
    initialize_butler_schema(conn)
    import importlib.util
    migration_path = os.path.join(os.path.dirname(__file__), "workbench", "migrations.py")
    migration_spec = importlib.util.spec_from_file_location(
        "study_hub_workbench_migrations", migration_path
    )
    migration_module = importlib.util.module_from_spec(migration_spec)
    migration_spec.loader.exec_module(migration_module)
    migration_module.migrate(conn)

    conn.close()


def _add_column_if_missing(conn, table, column, definition):
    """兼容添加列：如果列不存在则添加"""
    try:
        conn.execute(f"SELECT {column} FROM {table} LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        conn.commit()
        print(f"[db] 已添加列 {table}.{column}")
