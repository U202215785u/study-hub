"""因果记忆系统 — 模拟人脑的因果推理与时序理解

核心概念：
- 因果链：A → B → C（因为 A 所以 B，进而 C）
- 时序链：A before B after C（事件先后顺序）
- 实体关联：同一个人/项目/技术的不同记忆

与向量记忆的区别：
- 向量记忆："A 和 B 意思相近"
- 因果记忆："A 导致 B 发生"

借鉴：
- Hindsight 的 memory_links（causes/caused_by/enables/prevents）
- Graphiti 的时序知识图谱（Episode → Entity → Edge）
"""

import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from memory_store import _get_db, get_entry, search_memory


# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

@dataclass
class CausalLink:
    """因果链接"""
    from_entry_id: str
    to_entry_id: str
    link_type: str
    confidence: float = 0.7
    extracted_from: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))


@dataclass
class TemporalLink:
    """时序链接"""
    from_entry_id: str
    to_entry_id: str
    relation: str
    confidence: float = 0.7
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))


@dataclass
class EntityNode:
    """实体节点"""
    id: str
    name: str
    entity_type: str
    first_seen: str
    last_seen: str
    mention_count: int = 1


# ═══════════════════════════════════════════════════════════════
# 因果模式库
# ═══════════════════════════════════════════════════════════════

CAUSAL_PATTERNS = {
    "causes": {
        "markers": ["导致", "造成", "引起", "使", "让", "使得", "引发", "诱发"],
        "direction": "forward",
    },
    "caused_by": {
        "markers": ["因为", "由于", "源于", "归咎于", "因", "基于"],
        "direction": "backward",
    },
    "enables": {
        "markers": ["让...能够", "使...可以", "为...提供", "赋予", "支持"],
        "direction": "forward",
    },
    "prevents": {
        "markers": ["阻止", "防止", "避免", "不让", "杜绝", "拦截"],
        "direction": "forward",
    },
    "leads_to": {
        "markers": ["进而", "从而", "最终", "结果是", "演变成", "发展为"],
        "direction": "forward",
    },
    "results_in": {
        "markers": ["结果是", "最终变成", "发展为", "演变为", "结局是"],
        "direction": "forward",
    },
}

TEMPORAL_PATTERNS = {
    "before": ["之前", "以前", "先前", "事先", "提前"],
    "after": ["之后", "后来", "随后", "接着", "然后", "继而"],
    "during": ["期间", "同时", "与此同时", "在...过程中"],
    "simultaneous": ["同时", "一起", "一并", "共同"],
}

ENTITY_TYPES = {
    "person": ["我", "你", "他", "她", "客户", "老板", "同事", "朋友", "用户"],
    "project": ["项目", "产品", "系统", "平台", "工具", "网站", "应用"],
    "tech": ["Python", "React", "AI", "LLM", "数据库", "API", "框架", "模型"],
    "place": ["公司", "家", "办公室", "会议室", "线上", "线下"],
    "concept": ["方法", "策略", "原则", "模式", "理论", "思路"],
}


# ═══════════════════════════════════════════════════════════════
# 数据库初始化
# ═══════════════════════════════════════════════════════════════

def _init_causal_tables(db: sqlite3.Connection) -> None:
    """创建因果记忆相关表（如果不存在）。"""
    db.executescript("""
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
    db.commit()


def ensure_causal_tables() -> None:
    """确保因果记忆表已创建。"""
    db = _get_db()
    _init_causal_tables(db)


# ═══════════════════════════════════════════════════════════════
# 因果提取器
# ═══════════════════════════════════════════════════════════════

def extract_causal_links(text: str, entry_id: str) -> list[CausalLink]:
    """从记忆文本中提取因果关系。"""
    links = []
    sentences = re.split(r'[。！？\n]', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 5:
            continue
            
        for link_type, config in CAUSAL_PATTERNS.items():
            sorted_markers = sorted(config["markers"], key=len, reverse=True)
            matched = False
            for marker in sorted_markers:
                if matched:
                    break
                if marker in sentence:
                    parts = _split_causal_sentence(sentence, marker, config["direction"])
                    if parts:
                        cause_text, effect_text = parts
                        cause_entry = _find_or_create_stub_entry(cause_text, entry_id)
                        effect_entry = _find_or_create_stub_entry(effect_text, entry_id)
                        
                        if cause_entry and effect_entry and cause_entry != effect_entry:
                            links.append(CausalLink(
                                from_entry_id=cause_entry,
                                to_entry_id=effect_entry,
                                link_type=link_type,
                                confidence=_calculate_confidence(sentence, marker),
                                extracted_from=entry_id,
                            ))
                            matched = True
    
    return links


def _split_causal_sentence(sentence: str, marker: str, direction: str) -> tuple[str, str] | None:
    """拆分因果句为原因和结果。"""
    idx = sentence.find(marker)
    if idx == -1:
        return None
    
    before = sentence[:idx].strip()
    after = sentence[idx + len(marker):].strip()
    
    if not after or len(after) < 2:
        return None
    
    if direction == "forward":
        if not before or len(before) < 2:
            return None
        for sep in ['，', ',', '。', '；', ';']:
            if sep in after:
                after = after.split(sep)[0].strip()
                break
        return before, after
    else:
        cause = after
        effect = before
        
        for sep in ['，', ',', '；', ';']:
            if sep in cause:
                cause = cause.split(sep)[0].strip()
                break
        
        if effect:
            for sep in ['，', ',', '；', ';']:
                if sep in effect:
                    parts = [p.strip() for p in effect.split(sep) if p.strip()]
                    if parts:
                        effect = parts[-1]
                    break
        
        if len(cause) < 2:
            return None
        
        return cause, effect


def _calculate_confidence(sentence: str, marker: str) -> float:
    """计算因果关系的置信度。"""
    base = 0.7
    if len(sentence) > 20:
        base += 0.05
    if len(sentence) > 40:
        base += 0.05
    strong_markers = ["导致", "因为", "结果是", "最终变成"]
    if marker in strong_markers:
        base += 0.1
    return min(0.95, base)


def _find_or_create_stub_entry(text: str, source_entry_id: str) -> str | None:
    """查找或创建占位记忆条目。"""
    if not text or len(text.strip()) < 3:
        return None
    
    db = _get_db()
    text_clean = text.strip()
    
    cursor = db.execute(
        "SELECT id, content FROM entries WHERE content = ? AND status = 'active' LIMIT 1",
        (text_clean,)
    )
    row = cursor.fetchone()
    if row:
        return row["id"]
    
    cursor = db.execute(
        """SELECT id, content FROM entries 
           WHERE content LIKE ? 
             AND status = 'active'
             AND LENGTH(content) BETWEEN ? AND ?
           LIMIT 1""",
        (f"%{text_clean[:20]}%", int(len(text_clean) * 0.5), int(len(text_clean) * 2))
    )
    row = cursor.fetchone()
    if row:
        return row["id"]
    
    from memory_store import _next_id
    stub_id = _next_id()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    db.execute(
        """INSERT INTO entries (id, source, type, content, significance, status, created_at, field, depth)
           VALUES (?, 'causal_extraction', 'causal_stub', ?, 'auto', 'active', ?, 'knowledge', 'surface')""",
        (stub_id, text_clean, now)
    )
    db.commit()
    
    return stub_id


# ═══════════════════════════════════════════════════════════════
# 时序提取器
# ═══════════════════════════════════════════════════════════════

def extract_temporal_links(text: str, entry_id: str, entries_in_session: list[str] | None = None) -> list[TemporalLink]:
    """从记忆文本中提取时序关系。"""
    links = []
    
    if entries_in_session and len(entries_in_session) > 1:
        idx = entries_in_session.index(entry_id) if entry_id in entries_in_session else -1
        if idx > 0:
            links.append(TemporalLink(
                from_entry_id=entries_in_session[idx - 1],
                to_entry_id=entry_id,
                relation="before",
                confidence=0.8,
            ))
    
    sentences = re.split(r'[。！？\n]', text)
    for i, sentence in enumerate(sentences):
        for relation, markers in TEMPORAL_PATTERNS.items():
            for marker in markers:
                if marker in sentence and i > 0:
                    prev_text = sentences[i - 1]
                    prev_entry = _find_or_create_stub_entry(prev_text, entry_id)
                    curr_entry = _find_or_create_stub_entry(sentence, entry_id)
                    
                    if prev_entry and curr_entry:
                        links.append(TemporalLink(
                            from_entry_id=prev_entry,
                            to_entry_id=curr_entry,
                            relation=relation,
                            confidence=0.6,
                        ))
    
    return links


# ═══════════════════════════════════════════════════════════════
# 实体提取器
# ═══════════════════════════════════════════════════════════════

def extract_entities(text: str, entry_id: str) -> list[EntityNode]:
    """从记忆文本中提取实体。"""
    entities = []
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    db = _get_db()
    
    for entity_type, keywords in ENTITY_TYPES.items():
        for keyword in keywords:
            if keyword in text:
                cursor = db.execute(
                    "SELECT id, mention_count FROM entities WHERE name = ? AND entity_type = ?",
                    (keyword, entity_type)
                )
                row = cursor.fetchone()
                
                if row:
                    entity_id = row["id"]
                    db.execute(
                        "UPDATE entities SET last_seen = ?, mention_count = ? WHERE id = ?",
                        (now, row["mention_count"] + 1, entity_id)
                    )
                else:
                    entity_id = f"ent-{entity_type}-{keyword}-{now.replace(':', '').replace('-', '')}"
                    db.execute(
                        "INSERT INTO entities (id, name, entity_type, first_seen, last_seen, mention_count) VALUES (?, ?, ?, ?, ?, 1)",
                        (entity_id, keyword, entity_type, now, now)
                    )
                    entities.append(EntityNode(
                        id=entity_id,
                        name=keyword,
                        entity_type=entity_type,
                        first_seen=now,
                        last_seen=now,
                    ))
                
                db.execute(
                    "INSERT OR IGNORE INTO entry_entities (entry_id, entity_id) VALUES (?, ?)",
                    (entry_id, entity_id)
                )
    
    db.commit()
    return entities


# ═══════════════════════════════════════════════════════════════
# 保存链接
# ═══════════════════════════════════════════════════════════════

def save_causal_links(links: list[CausalLink]) -> int:
    """保存因果链接到数据库。"""
    if not links:
        return 0
    
    ensure_causal_tables()
    db = _get_db()
    count = 0
    
    for link in links:
        try:
            db.execute(
                """INSERT OR IGNORE INTO causal_links 
                   (from_entry_id, to_entry_id, link_type, confidence, extracted_from, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (link.from_entry_id, link.to_entry_id, link.link_type,
                 link.confidence, link.extracted_from, link.created_at)
            )
            count += 1
        except sqlite3.IntegrityError:
            pass
    
    db.commit()
    return count


def save_temporal_links(links: list[TemporalLink]) -> int:
    """保存时序链接到数据库。"""
    if not links:
        return 0
    
    ensure_causal_tables()
    db = _get_db()
    count = 0
    
    for link in links:
        try:
            db.execute(
                """INSERT OR IGNORE INTO temporal_links 
                   (from_entry_id, to_entry_id, relation, confidence, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (link.from_entry_id, link.to_entry_id, link.relation,
                 link.confidence, link.created_at)
            )
            count += 1
        except sqlite3.IntegrityError:
            pass
    
    db.commit()
    return count


# ═══════════════════════════════════════════════════════════════
# 主入口：处理记忆条目
# ═══════════════════════════════════════════════════════════════

def process_entry(entry_id: str, entries_in_session: list[str] | None = None) -> dict:
    """处理单条记忆，提取因果、时序、实体。"""
    entry = get_entry(entry_id)
    if not entry:
        return {"causal_links": 0, "temporal_links": 0, "entities": 0}
    
    text = entry.get("content", "")
    if len(text) < 10:
        return {"causal_links": 0, "temporal_links": 0, "entities": 0}
    
    ensure_causal_tables()
    
    causal = extract_causal_links(text, entry_id)
    causal_count = save_causal_links(causal)
    
    temporal = extract_temporal_links(text, entry_id, entries_in_session)
    temporal_count = save_temporal_links(temporal)
    
    entities = extract_entities(text, entry_id)
    
    return {
        "causal_links": causal_count,
        "temporal_links": temporal_count,
        "entities": len(entities),
    }


# ═══════════════════════════════════════════════════════════════
# 因果检索（核心！）
# ═══════════════════════════════════════════════════════════════

def causal_search(query: str, k: int = 5) -> dict:
    """因果记忆检索 — 真正的逻辑推理。"""
    ensure_causal_tables()
    
    seed_results = search_memory(query, k=10, use_causal=False)
    seeds = seed_results.get("results", [])
    
    if not seeds:
        return {"query": query, "results": [], "chains": [], "stats": {}}
    
    seed_ids = [r.get("entry_id") for r in seeds if r.get("entry_id")]
    
    causal_results = _expand_causal_chain(seed_ids, depth=2)
    temporal_results = _expand_temporal(seed_ids)
    
    entity_results = []
    if len(seed_ids) <= 3:
        entity_results = _expand_by_entities(seed_ids)
    
    merged = _merge_results(seeds, causal_results, temporal_results, entity_results)
    chains = _build_causal_chains(merged[:k])
    
    return {
        "query": query,
        "results": merged[:k],
        "chains": chains,
        "stats": {
            "seeds": len(seeds),
            "causal_expanded": len(causal_results),
            "temporal_expanded": len(temporal_results),
            "entity_expanded": len(entity_results),
        }
    }


def _expand_causal_chain(seed_ids: list[str], depth: int = 2) -> list[dict]:
    """因果链扩展：找到原因和结果。"""
    db = _get_db()
    results = []
    visited = set(seed_ids)
    queue = [(sid, 0) for sid in seed_ids]
    
    while queue:
        current_id, current_depth = queue.pop(0)
        if current_depth >= depth:
            continue
        
        rows = db.execute(
            """SELECT cl.*, e.content, e.type
               FROM causal_links cl
               JOIN entries e ON cl.from_entry_id = e.id
               WHERE cl.to_entry_id = ? AND e.status = 'active'
               ORDER BY cl.confidence DESC
               LIMIT 5""",
            (current_id,)
        ).fetchall()
        
        for row in rows:
            if row["from_entry_id"] not in visited:
                visited.add(row["from_entry_id"])
                results.append({
                    "entry_id": row["from_entry_id"],
                    "content": row["content"],
                    "type": row["type"],
                    "link_type": row["link_type"],
                    "confidence": row["confidence"],
                    "direction": "cause",
                    "source_seed": current_id,
                })
                queue.append((row["from_entry_id"], current_depth + 1))
        
        rows = db.execute(
            """SELECT cl.*, e.content, e.type
               FROM causal_links cl
               JOIN entries e ON cl.to_entry_id = e.id
               WHERE cl.from_entry_id = ? AND e.status = 'active'
               ORDER BY cl.confidence DESC
               LIMIT 5""",
            (current_id,)
        ).fetchall()
        
        for row in rows:
            if row["to_entry_id"] not in visited:
                visited.add(row["to_entry_id"])
                results.append({
                    "entry_id": row["to_entry_id"],
                    "content": row["content"],
                    "type": row["type"],
                    "link_type": row["link_type"],
                    "confidence": row["confidence"],
                    "direction": "effect",
                    "source_seed": current_id,
                })
                queue.append((row["to_entry_id"], current_depth + 1))
    
    return results


def _expand_temporal(seed_ids: list[str]) -> list[dict]:
    """时序扩展。"""
    db = _get_db()
    results = []
    
    for sid in seed_ids:
        rows = db.execute(
            """SELECT tl.*, e.content, e.type
               FROM temporal_links tl
               JOIN entries e ON tl.from_entry_id = e.id
               WHERE tl.to_entry_id = ? AND tl.relation = 'before' AND e.status = 'active'
               ORDER BY tl.confidence DESC
               LIMIT 3""",
            (sid,)
        ).fetchall()
        
        for row in rows:
            results.append({
                "entry_id": row["from_entry_id"],
                "content": row["content"],
                "type": row["type"],
                "relation": "before",
                "confidence": row["confidence"],
            })
        
        rows = db.execute(
            """SELECT tl.*, e.content, e.type
               FROM temporal_links tl
               JOIN entries e ON tl.to_entry_id = e.id
               WHERE tl.from_entry_id = ? AND tl.relation = 'before' AND e.status = 'active'
               ORDER BY tl.confidence DESC
               LIMIT 3""",
            (sid,)
        ).fetchall()
        
        for row in rows:
            results.append({
                "entry_id": row["to_entry_id"],
                "content": row["content"],
                "type": row["type"],
                "relation": "after",
                "confidence": row["confidence"],
            })
    
    return results


def _expand_by_entities(seed_ids: list[str]) -> list[dict]:
    """实体扩展。"""
    db = _get_db()
    results = []
    
    for sid in seed_ids:
        entity_rows = db.execute(
            "SELECT entity_id FROM entry_entities WHERE entry_id = ?",
            (sid,)
        ).fetchall()
        
        entity_ids = [r["entity_id"] for r in entity_rows]
        if not entity_ids:
            continue
        
        placeholders = ",".join("?" * len(entity_ids))
        rows = db.execute(
            f"""SELECT ee.entry_id, e.content, e.type, COUNT(DISTINCT ee.entity_id) as shared_count
                FROM entry_entities ee
                JOIN entries e ON ee.entry_id = e.id
                WHERE ee.entity_id IN ({placeholders})
                  AND ee.entry_id != ?
                  AND e.status = 'active'
                GROUP BY ee.entry_id
                ORDER BY shared_count DESC
                LIMIT 5""",
            (*entity_ids, sid)
        ).fetchall()
        
        for row in rows:
            results.append({
                "entry_id": row["entry_id"],
                "content": row["content"],
                "type": row["type"],
                "shared_entities": row["shared_count"],
                "confidence": min(0.9, 0.5 + row["shared_count"] * 0.1),
            })
    
    return results


def _merge_results(seeds, causal, temporal, entity):
    """融合多路检索结果。"""
    scored = {}
    
    for r in seeds:
        eid = r.get("entry_id") or r.get("source", "")
        if eid:
            scored[eid] = {**r, "score": 1.0, "source_type": "seed"}
    
    for r in causal:
        eid = r["entry_id"]
        score = 0.9 * r.get("confidence", 0.7)
        if eid in scored:
            scored[eid]["score"] = max(scored[eid]["score"], score)
            scored[eid]["source_type"] = "causal+seed"
        else:
            scored[eid] = {**r, "score": score, "source_type": "causal"}
    
    for r in temporal:
        eid = r["entry_id"]
        score = 0.7 * r.get("confidence", 0.7)
        if eid in scored:
            scored[eid]["score"] = max(scored[eid]["score"], score)
        else:
            scored[eid] = {**r, "score": score, "source_type": "temporal"}
    
    for r in entity:
        eid = r["entry_id"]
        score = 0.6 * r.get("confidence", 0.7)
        if eid in scored:
            scored[eid]["score"] = max(scored[eid]["score"], score)
        else:
            scored[eid] = {**r, "score": score, "source_type": "entity"}
    
    return sorted(scored.values(), key=lambda x: x["score"], reverse=True)


def _build_causal_chains(results):
    """构建因果链用于展示。"""
    chains = []
    
    for r in results:
        eid = r.get("entry_id")
        if not eid:
            continue
        
        causes = []
        effects = []
        
        if r.get("direction") == "cause":
            causes.append({"content": r.get("content", "")[:80], "type": r.get("link_type", "causes")})
        elif r.get("direction") == "effect":
            effects.append({"content": r.get("content", "")[:80], "type": r.get("link_type", "causes")})
        
        if causes or effects:
            chains.append({
                "entry_id": eid,
                "content": r.get("content", "")[:100],
                "causes": causes,
                "effects": effects,
            })
    
    return chains


# ═══════════════════════════════════════════════════════════════
# 调试工具
# ═══════════════════════════════════════════════════════════════

def print_causal_report(limit: int = 20):
    """打印因果记忆报告。"""
    ensure_causal_tables()
    db = _get_db()
    
    print("=== 因果记忆报告 ===\n")
    
    causal_count = db.execute("SELECT COUNT(*) as c FROM causal_links").fetchone()["c"]
    temporal_count = db.execute("SELECT COUNT(*) as c FROM temporal_links").fetchone()["c"]
    entity_count = db.execute("SELECT COUNT(*) as c FROM entities").fetchone()["c"]
    
    print(f"因果链接: {causal_count}")
    print(f"时序链接: {temporal_count}")
    print(f"实体节点: {entity_count}\n")
    
    print("--- 最近因果链接 ---")
    rows = db.execute(
        """SELECT cl.*, e1.content as from_content, e2.content as to_content
           FROM causal_links cl
           JOIN entries e1 ON cl.from_entry_id = e1.id
           JOIN entries e2 ON cl.to_entry_id = e2.id
           ORDER BY cl.created_at DESC
           LIMIT ?""",
        (limit,)
    ).fetchall()
    
    for row in rows:
        print(f"[{row['link_type']}] (置信度: {row['confidence']:.2f})")
        print(f"  因: {row['from_content'][:60]}...")
        print(f"  果: {row['to_content'][:60]}...")
        print()


if __name__ == "__main__":
    print_causal_report()
