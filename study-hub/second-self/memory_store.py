"""记忆存储 — SQLite 语义记忆 + 文件搜索双轨

SQLite schema 见 docs/gateway/contracts/memory-schema-v0.md
文件搜索作为补充：覆盖尚未录入 SQLite 的 wiki/*.md 历史内容。
"""
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from gateway_paths import ROOT

# ── 数据库路径 ──────────────────────────────────────────────

MEMORY_DIR = ROOT / ".memory"
DB_PATH = MEMORY_DIR / "entries.db"
INDEX_PATH = MEMORY_DIR / "index.json"

# ── 懒初始化 ─────────────────────────────────────────────────

_db: sqlite3.Connection | None = None


def _get_db() -> sqlite3.Connection:
    """获取数据库连接，首次调用时自动初始化。"""
    global _db
    if _db is None:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        _db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _db.row_factory = sqlite3.Row
        _db.execute("PRAGMA journal_mode=WAL")
        _db.execute("PRAGMA foreign_keys=ON")
        _init_tables(_db)
    return _db


def _init_tables(db: sqlite3.Connection) -> None:
    """创建表（如果不存在）。"""
    db.executescript("""
        CREATE TABLE IF NOT EXISTS entries (
            id              TEXT PRIMARY KEY,
            source          TEXT NOT NULL,
            type            TEXT NOT NULL,
            content         TEXT NOT NULL,
            context_json    TEXT DEFAULT '{}',
            significance    TEXT NOT NULL DEFAULT 'auto',
            status          TEXT NOT NULL DEFAULT 'active',
            embedding_dim   INTEGER DEFAULT NULL,
            created_at      TEXT NOT NULL,
            last_hit_at     TEXT DEFAULT NULL,
            hit_count       INTEGER NOT NULL DEFAULT 0,
            dormant_at      TEXT DEFAULT NULL,
            -- 神经式记忆系统新增字段
            field           TEXT DEFAULT 'knowledge',
            emotional_tag   TEXT DEFAULT NULL,
            scene_binding   TEXT DEFAULT '[]',
            depth           TEXT DEFAULT 'surface',
            conflict_with   TEXT DEFAULT '[]'
        );

        CREATE INDEX IF NOT EXISTS idx_entries_source     ON entries(source);
        CREATE INDEX IF NOT EXISTS idx_entries_type       ON entries(type);
        CREATE INDEX IF NOT EXISTS idx_entries_status     ON entries(status);
        CREATE INDEX IF NOT EXISTS idx_entries_created    ON entries(created_at);
        CREATE INDEX IF NOT EXISTS idx_entries_last_hit   ON entries(last_hit_at);
        CREATE INDEX IF NOT EXISTS idx_entries_hit_count  ON entries(hit_count);
        -- 神经式记忆系统新增索引
        CREATE INDEX IF NOT EXISTS idx_entries_field      ON entries(field);
        CREATE INDEX IF NOT EXISTS idx_entries_depth      ON entries(depth);
        CREATE INDEX IF NOT EXISTS idx_entries_emotional  ON entries(emotional_tag);

        CREATE TABLE IF NOT EXISTS links (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id          TEXT NOT NULL,
            related_entry_id  TEXT NOT NULL,
            relation_type     TEXT NOT NULL DEFAULT 'related',
            created_at        TEXT NOT NULL,
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (related_entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            UNIQUE(entry_id, related_entry_id, relation_type)
        );

        CREATE INDEX IF NOT EXISTS idx_links_entry      ON links(entry_id);
        CREATE INDEX IF NOT EXISTS idx_links_related    ON links(related_entry_id);

        CREATE TABLE IF NOT EXISTS retrieval_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text      TEXT NOT NULL,
            query_source    TEXT NOT NULL,
            entry_id        TEXT NOT NULL,
            score           REAL NOT NULL,
            rank            INTEGER NOT NULL,
            k_value         INTEGER NOT NULL,
            searched_at     TEXT NOT NULL,
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_retrieval_log_entry   ON retrieval_log(entry_id);
        CREATE INDEX IF NOT EXISTS idx_retrieval_log_time    ON retrieval_log(searched_at);
        
        -- ═══════════════════════════════════════════════════════
        -- 因果记忆系统表（Phase 4）
        -- ═══════════════════════════════════════════════════════
        
        -- 实体表
        CREATE TABLE IF NOT EXISTS entities (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            entity_type     TEXT DEFAULT 'concept',
            first_seen      TEXT NOT NULL,
            last_seen       TEXT NOT NULL,
            mention_count   INTEGER DEFAULT 1
        );
        
        CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
        
        -- 记忆-实体关联
        CREATE TABLE IF NOT EXISTS entry_entities (
            entry_id        TEXT NOT NULL,
            entity_id       TEXT NOT NULL,
            PRIMARY KEY (entry_id, entity_id),
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_entry_entities_entry ON entry_entities(entry_id);
        CREATE INDEX IF NOT EXISTS idx_entry_entities_entity ON entry_entities(entity_id);
        
        -- 因果链接（核心）
        CREATE TABLE IF NOT EXISTS causal_links (
            from_entry_id   TEXT NOT NULL,
            to_entry_id     TEXT NOT NULL,
            link_type       TEXT NOT NULL CHECK(link_type IN ('causes','caused_by','enables','prevents','leads_to','results_in')),
            confidence      REAL DEFAULT 0.7,
            extracted_from  TEXT,
            created_at      TEXT NOT NULL,
            PRIMARY KEY (from_entry_id, to_entry_id, link_type),
            FOREIGN KEY (from_entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (to_entry_id) REFERENCES entries(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_causal_from ON causal_links(from_entry_id);
        CREATE INDEX IF NOT EXISTS idx_causal_to ON causal_links(to_entry_id);
        CREATE INDEX IF NOT EXISTS idx_causal_type ON causal_links(link_type);
        
        -- 时序链接
        CREATE TABLE IF NOT EXISTS temporal_links (
            from_entry_id   TEXT NOT NULL,
            to_entry_id     TEXT NOT NULL,
            relation        TEXT NOT NULL CHECK(relation IN ('before','after','during','simultaneous')),
            confidence      REAL DEFAULT 0.7,
            created_at      TEXT NOT NULL,
            PRIMARY KEY (from_entry_id, to_entry_id, relation),
            FOREIGN KEY (from_entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (to_entry_id) REFERENCES entries(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_temporal_from ON temporal_links(from_entry_id);
        CREATE INDEX IF NOT EXISTS idx_temporal_to ON temporal_links(to_entry_id);
        CREATE INDEX IF NOT EXISTS idx_temporal_relation ON temporal_links(relation);
    """)


# ── 记忆 ID 生成 ────────────────────────────────────────────

_counter: int | None = None


def _next_id() -> str:
    """生成下一个记忆 ID：mem-{YYYYMMDD}-{序号}"""
    global _counter
    db = _get_db()
    today = datetime.now().strftime("%Y%m%d")
    if _counter is None:
        row = db.execute(
            "SELECT id FROM entries WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
            (f"mem-{today}-%",)
        ).fetchone()
        if row:
            last_num = int(row["id"].rsplit("-", 1)[-1])
            _counter = last_num
        else:
            _counter = 0
    _counter += 1
    return f"mem-{today}-{_counter:04d}"


# ── 条目 CRUD ───────────────────────────────────────────────

def insert_entry(
    source: str,
    type: str,
    content: str,
    context: dict | None = None,
    significance: str = "auto",
    field: str = "knowledge",
    emotional_tag: str | None = None,
    scene_binding: list | None = None,
    depth: str = "surface",
    conflict_with: list | None = None,
) -> str:
    """插入一条记忆条目，返回生成的 ID。"""
    db = _get_db()
    entry_id = _next_id()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    ctx_json = json.dumps(context or {}, ensure_ascii=False)
    scene_json = json.dumps(scene_binding or [], ensure_ascii=False)
    conflict_json = json.dumps(conflict_with or [], ensure_ascii=False)

    db.execute(
        """INSERT INTO entries (id, source, type, content, context_json,
           significance, status, created_at, field, emotional_tag, scene_binding, depth, conflict_with)
           VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)""",
        (entry_id, source, type, content, ctx_json, significance, now,
         field, emotional_tag, scene_json, depth, conflict_json),
    )
    db.commit()
    _update_index_for_entry(entry_id, source, type, content, ctx_json, field=field)
    
    # 自动提取因果、时序、实体（Phase 4：因果记忆）
    try:
        from memory_causal import process_entry
        process_entry(entry_id)
    except Exception:
        pass  # 因果提取失败不影响主流程
    
    return entry_id


def get_entry(entry_id: str) -> dict | None:
    """读取单条记忆。"""
    db = _get_db()
    row = db.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


def update_hit(entry_id: str) -> None:
    """更新记忆的命中时间和计数。"""
    db = _get_db()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    db.execute(
        "UPDATE entries SET last_hit_at = ?, hit_count = hit_count + 1 WHERE id = ?",
        (now, entry_id),
    )
    db.commit()


def get_stats() -> dict:
    """获取记忆存储统计信息。"""
    db = _get_db()
    total = db.execute("SELECT COUNT(*) as n FROM entries").fetchone()["n"]
    active = db.execute("SELECT COUNT(*) as n FROM entries WHERE status='active'").fetchone()["n"]
    dormant = db.execute("SELECT COUNT(*) as n FROM entries WHERE status='dormant'").fetchone()["n"]
    return {"total": total, "active": active, "dormant": dormant}


# ── 搜索 ─────────────────────────────────────────────────────

def search_memory(query: str, k: int = 5, use_causal: bool = True) -> dict:
    """混合搜索：SQLite 关键词 + 因果检索 + 文件扫描。"""
    q = query.lower().strip()
    if not q:
        return {"query": query, "results": [], "stats": get_stats(), "causal_chains": []}

    results = []
    causal_chains = []

    # ① 因果记忆检索（Phase 4）
    if use_causal:
        try:
            from memory_causal import causal_search
            causal_result = causal_search(query, k=k)
            for r in causal_result.get("results", []):
                results.append({
                    "source": f"memory://{r.get('entry_id', '')}",
                    "type": r.get("type", "causal"),
                    "preview": r.get("content", "")[:200],
                    "score": r.get("score", 0.8),
                    "entry_id": r.get("entry_id", ""),
                    "source_type": r.get("source_type", "causal"),
                })
            causal_chains = causal_result.get("chains", [])
        except Exception:
            pass

    # ② SQLite 关键词搜索
    results.extend(_search_sql(q))

    # ③ 文件扫描
    results.extend(_search_files(q))

    # 去重
    seen = set()
    deduped = []
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        if r["source"] not in seen:
            seen.add(r["source"])
            deduped.append(r)

    top_k = deduped[:k]

    # ④ 记录检索日志
    _log_retrieval(query, top_k, k)

    return {"query": q, "results": top_k, "stats": get_stats(), "causal_chains": causal_chains}


def _search_sql(q: str) -> list[dict]:
    """SQLite LIKE 关键词搜索。"""
    db = _get_db()
    results = []

    keywords = [kw.strip() for kw in q.split() if len(kw.strip()) >= 1]
    if not keywords:
        keywords = [q]

    rows = db.execute(
        "SELECT * FROM entries WHERE status = 'active' ORDER BY hit_count DESC"
    ).fetchall()

    for row in rows:
        content_lower = row["content"].lower()
        match_count = sum(content_lower.count(kw) for kw in keywords)
        if match_count > 0:
            context = json.loads(row["context_json"] or "{}")
            results.append({
                "source": f"memory://{row['id']}",
                "type": row["type"],
                "preview": row["content"][:200],
                "score": match_count,
                "entry_id": row["id"],
                "domain": context.get("domain") if isinstance(context, dict) else None,
                "project": context.get("project") if isinstance(context, dict) else None,
            })

    if results:
        max_score = max(r["score"] for r in results)
        if max_score > 0:
            for r in results:
                r["score"] = round(r["score"] / max_score, 2)

    return results


def _search_files(q: str) -> list[dict]:
    """文件扫描：wiki/*.md + DECISIONS.md + DASHBOARD.md。"""
    results = []

    wiki_dir = ROOT / "wiki"
    if wiki_dir.exists():
        for md in wiki_dir.rglob("*.md"):
            if md.name in ("index.md", "log.md"):
                continue
            try:
                text = md.read_text(encoding="utf-8").lower()
                if q in text:
                    relative_path = str(md.relative_to(ROOT))
                    results.append({
                        "source": relative_path,
                        "type": "wiki",
                        "preview": text[:200],
                        "score": 0.3,
                    })
            except Exception:
                pass

    for special in ("DECISIONS.md", "DASHBOARD.md"):
        path = ROOT / special
        if path.exists():
            text = path.read_text(encoding="utf-8").lower()
            if q in text:
                results.append({
                    "source": special,
                    "type": "self",
                    "preview": text[:200],
                    "score": 0.5,
                })

    return results


def _log_retrieval(query: str, results: list[dict], k: int) -> None:
    """记录检索日志。"""
    db = _get_db()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    for rank, r in enumerate(results, 1):
        entry_id = r.get("entry_id", "")
        if not entry_id:
            continue
        db.execute(
            """INSERT INTO retrieval_log
               (query_text, query_source, entry_id, score, rank, k_value, searched_at)
               VALUES (?, 'manual_search', ?, ?, ?, ?, ?)""",
            (query, entry_id, r.get("score", 0), rank, k, now),
        )
    db.commit()


# ── 索引维护 ─────────────────────────────────────────────────

def _update_index_for_entry(
    entry_id: str, source: str, mem_type: str,
    content: str, context_json: str, field: str = "knowledge",
) -> None:
    """更新 index.json 的轻量索引。"""
    index = _load_index()

    words = set()
    for w in re.findall(r"[\u4e00-\u9fff]{2,}", content):
        words.add(w)
    for w in re.findall(r"[a-zA-Z_]{3,}", content):
        words.add(w.lower())

    for word in words:
        if word not in index["keywords"]:
            index["keywords"][word] = []
        if entry_id not in index["keywords"][word]:
            index["keywords"][word].append(entry_id)

    try:
        context = json.loads(context_json or "{}") if isinstance(context_json, str) else (context_json or {})
    except json.JSONDecodeError:
        context = {}
    index["entries_summary"][entry_id] = {
        "source": source,
        "type": mem_type,
        "domain": context.get("domain") if isinstance(context, dict) else None,
        "project": context.get("project") if isinstance(context, dict) else None,
        "content_preview": content[:200],
        "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "active",
        "significance": "auto",
        "field": field,
    }

    index["total_entries"] = len(index["entries_summary"])
    index["built_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    _save_index(index)


def _load_index() -> dict:
    """加载 index.json，如果不存在则创建空索引。"""
    if INDEX_PATH.exists():
        try:
            return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "version": 1,
        "keywords": {},
        "entries_summary": {},
        "total_entries": 0,
        "built_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


def _save_index(index: dict) -> None:
    """保存 index.json。"""
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 工具函数 ─────────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict:
    """将 sqlite3.Row 转为普通 dict。"""
    return {key: row[key] for key in row.keys()}
