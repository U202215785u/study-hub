from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
import json, os, sys, asyncio
from datetime import datetime

# 确保 backend 目录在导入路径中（用于独立导入时）
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

from database import get_db
from processing.vector_store import get_vector_store
from ai_client import ai_client

router = APIRouter()

# ─── Pydantic Models ───────────────────────────────────────────

class MemoryCreate(BaseModel):
    content: str
    category: str = ""
    tags: List[str] = []
    source_tool: str = "manual"
    source_ref: str = ""
    importance: int = Field(default=3, ge=1, le=5)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    memory_layer: str = "session"  # role / project / workflow / session / world
    project_name: str = ""
    workflow_name: str = ""
    memory_type: str = "fact"  # fact / decision / preference / habit / action_item / lesson / snippet

class MemoryBatchCreate(BaseModel):
    items: List[MemoryCreate]

class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    importance: Optional[int] = Field(default=None, ge=1, le=5)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    status: Optional[str] = None
    memory_layer: Optional[str] = None
    project_name: Optional[str] = None
    workflow_name: Optional[str] = None
    memory_type: Optional[str] = None

class MemoryExtractRequest(BaseModel):
    text: str
    source_tool: str = "manual"
    source_ref: str = ""

class SummarizeExtractRequest(BaseModel):
    conversation: str
    source_tool: str = ""
    source_ref: str = ""
    detected_project: str = ""

class ContextInjectRequest(BaseModel):
    query: str
    tool: str = ""
    session_id: str = ""

class MemoryOut(BaseModel):
    id: int
    content: str
    category: str
    tags: List[str]
    source_tool: str
    source_ref: str
    importance: int
    confidence: float
    status: str
    memory_layer: str
    project_name: str
    workflow_name: str
    memory_type: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ─── Helpers ───────────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "content": row["content"],
        "category": row["category"] or "",
        "tags": json.loads(row["tags"] or "[]"),
        "source_tool": row["source_tool"] or "manual",
        "source_ref": row["source_ref"] or "",
        "importance": row["importance"],
        "confidence": row["confidence"],
        "status": row["status"],
        "memory_layer": row["memory_layer"] if "memory_layer" in row.keys() else "session",
        "project_name": row["project_name"] if "project_name" in row.keys() else "",
        "workflow_name": row["workflow_name"] if "workflow_name" in row.keys() else "",
        "memory_type": row["memory_type"] if "memory_type" in row.keys() else "fact",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _add_to_chroma(memory_id: int, content: str) -> str:
    """将记忆内容存入 ChromaDB，返回 embed_id"""
    vs = get_vector_store()
    embed_id = f"mem_{memory_id}"
    embedding = vs._get_embeddings([content])
    vs.memory_collection.add(
        ids=[embed_id],
        embeddings=embedding,
        documents=[content],
        metadatas={"memory_id": memory_id},
    )
    return embed_id


def _remove_from_chroma(memory_id: int):
    """从 ChromaDB 删除记忆"""
    vs = get_vector_store()
    embed_id = f"mem_{memory_id}"
    try:
        vs.memory_collection.delete(ids=[embed_id])
    except Exception:
        pass


def _update_chroma(memory_id: int, content: str):
    """更新 ChromaDB 中的记忆内容"""
    vs = get_vector_store()
    embed_id = f"mem_{memory_id}"
    embedding = vs._get_embeddings([content])
    try:
        vs.memory_collection.update(
            ids=[embed_id],
            embeddings=embedding,
            documents=[content],
        )
    except Exception:
        # 如果不存在则新增
        vs.memory_collection.add(
            ids=[embed_id],
            embeddings=embedding,
            documents=[content],
            metadatas={"memory_id": memory_id},
        )


# ─── CRUD Endpoints ────────────────────────────────────────────

@router.post("/memory/remember", response_model=MemoryOut)
async def memory_remember(payload: MemoryCreate):
    """存一条事实到记忆系统"""
    conn = get_db()
    now = datetime.now().isoformat()
    cursor = conn.execute(
        """
        INSERT INTO memories (content, category, tags, source_tool, source_ref, importance, confidence, status, embed_id, memory_layer, project_name, workflow_name, memory_type, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.content,
            payload.category,
            json.dumps(payload.tags, ensure_ascii=False),
            payload.source_tool,
            payload.source_ref,
            payload.importance,
            payload.confidence,
            "active",
            "",
            payload.memory_layer,
            payload.project_name,
            payload.workflow_name,
            payload.memory_type,
            now,
            now,
        ),
    )
    memory_id = cursor.lastrowid
    conn.commit()

    # 异步写入 ChromaDB（同步执行避免事件循环问题）
    try:
        embed_id = _add_to_chroma(memory_id, payload.content)
        conn.execute("UPDATE memories SET embed_id = ? WHERE id = ?", (embed_id, memory_id))
        conn.commit()
    except Exception as e:
        print(f"[memory] ChromaDB 写入失败: {e}")

    row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


@router.post("/memory/remember/batch")
async def memory_remember_batch(payload: MemoryBatchCreate):
    """批量存事实"""
    results = []
    for item in payload.items:
        result = await memory_remember(item)
        results.append(result)
    return {"added": len(results), "items": results}


@router.get("/memory/recall")
async def memory_recall(q: str, top_k: int = 5):
    """语义搜索记忆（走 ChromaDB）"""
    if not q.strip():
        return {"results": [], "query": q}

    vs = get_vector_store()
    if vs.memory_collection.count() == 0:
        return {"results": [], "query": q, "message": "记忆库为空"}

    q_embedding = vs._get_embeddings([q])
    results = vs.memory_collection.query(
        query_embeddings=q_embedding,
        n_results=top_k,
        where={"status": "active"},
    )

    out = []
    if results and results["ids"] and results["ids"][0]:
        conn = get_db()
        for i, embed_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            memory_id = meta.get("memory_id") if meta else None
            if memory_id:
                row = conn.execute(
                    "SELECT * FROM memories WHERE id = ? AND status = 'active'", (memory_id,)
                ).fetchone()
                if row:
                    out.append(_row_to_dict(row))
        conn.close()

    return {"results": out, "query": q, "count": len(out)}


@router.get("/memory/list")
async def memory_list(cat: str = "", status: str = "active", limit: int = 50, offset: int = 0):
    """列表查询记忆（走 SQLite）"""
    conn = get_db()
    where_clauses = ["status = ?"]
    params = [status]
    if cat:
        where_clauses.append("category = ?")
        params.append(cat)

    where_sql = " AND ".join(where_clauses)
    rows = conn.execute(
        f"SELECT * FROM memories WHERE {where_sql} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (*params, limit, offset),
    ).fetchall()

    total = conn.execute(
        f"SELECT COUNT(*) as c FROM memories WHERE {where_sql}", params
    ).fetchone()["c"]

    conn.close()
    return {"items": [_row_to_dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/memory/unified_search")
async def memory_unified_search(q: str, top_k: int = 5):
    """统一搜索：同时查 memories + documents + wiki_pages，RRF 融合排序"""
    if not q.strip():
        return {"results": [], "query": q}

    vs = get_vector_store()
    results = vs.unified_search(q, top_k=top_k)

    # 补充 memories 的完整字段
    conn = get_db()
    enriched = []
    for r in results:
        if r["source"] == "memory":
            memory_id = r["metadata"].get("memory_id") if r["metadata"] else None
            if memory_id:
                row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
                if row:
                    enriched.append({**r, "memory": _row_to_dict(row)})
                    continue
        enriched.append(r)
    conn.close()

    return {"results": enriched, "query": q, "count": len(enriched)}


@router.get("/memory/embedding_status")
async def memory_embedding_status():
    """返回各 collection 的 embedding 状态"""
    vs = get_vector_store()
    return vs.get_embedding_status()


@router.get("/memory/{memory_id}", response_model=MemoryOut)
async def memory_get(memory_id: int):
    """获取单条记忆"""
    conn = get_db()
    row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    conn.close()
    if not row:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "记忆不存在"})
    return _row_to_dict(row)


@router.put("/memory/{memory_id}", response_model=MemoryOut)
async def memory_update(memory_id: int, payload: MemoryUpdate):
    """修改记忆"""
    conn = get_db()
    row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if not row:
        conn.close()
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "记忆不存在"})

    updates = []
    params = []
    if payload.content is not None:
        updates.append("content = ?")
        params.append(payload.content)
    if payload.category is not None:
        updates.append("category = ?")
        params.append(payload.category)
    if payload.tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(payload.tags, ensure_ascii=False))
    if payload.importance is not None:
        updates.append("importance = ?")
        params.append(payload.importance)
    if payload.confidence is not None:
        updates.append("confidence = ?")
        params.append(payload.confidence)
    if payload.status is not None:
        updates.append("status = ?")
        params.append(payload.status)
    if payload.memory_layer is not None:
        updates.append("memory_layer = ?")
        params.append(payload.memory_layer)
    if payload.project_name is not None:
        updates.append("project_name = ?")
        params.append(payload.project_name)
    if payload.workflow_name is not None:
        updates.append("workflow_name = ?")
        params.append(payload.workflow_name)
    if payload.memory_type is not None:
        updates.append("memory_type = ?")
        params.append(payload.memory_type)

    if not updates:
        conn.close()
        return _row_to_dict(row)

    updates.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(memory_id)

    conn.execute(
        f"UPDATE memories SET {', '.join(updates)} WHERE id = ?",
        params,
    )
    conn.commit()

    # 更新 ChromaDB
    new_content = payload.content if payload.content is not None else row["content"]
    new_status = payload.status if payload.status is not None else row["status"]
    if payload.content is not None:
        _update_chroma(memory_id, new_content)
    if new_status != "active":
        _remove_from_chroma(memory_id)
    elif row["status"] != "active" and new_status == "active":
        _update_chroma(memory_id, new_content)

    row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


@router.delete("/memory/{memory_id}")
async def memory_delete(memory_id: int):
    """删除记忆"""
    conn = get_db()
    row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if not row:
        conn.close()
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "记忆不存在"})

    _remove_from_chroma(memory_id)
    conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()
    conn.close()
    return {"deleted": True, "id": memory_id}


# ─── 智能提取 ──────────────────────────────────────────────────

EXTRACT_SYSTEM_PROMPT = """你是一个事实提取专家。请从以下对话或文本中，提取所有关于用户的独立事实。

规则：
1. 每条事实必须是完整的、可独立理解的陈述句
2. 不要提取模糊表述（"可能"、"大概"），只提取确定的事实
3. 每条事实用 JSON 对象表示，包含 content（事实内容）、category（分类）、tags（标签数组）
4. 分类可选：preferences / health / travel / work / people / learning / habits / skills / goals / other
5. 返回 JSON 数组格式，不要其他内容

示例输出：
[
  {"content": "用户喜欢吃辣的食物", "category": "preferences", "tags": ["food", "spicy"]},
  {"content": "用户正在学习 Rust 编程语言", "category": "learning", "tags": ["rust", "programming"]}
]"""


@router.post("/memory/extract")
async def memory_extract(payload: MemoryExtractRequest):
    """喂一段文本，AI 自动提取事实并存入记忆系统"""
    text = payload.text.strip()
    if not text:
        return {"added": 0, "skipped": 0, "items": [], "message": "文本为空"}

    messages = [
        {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
        {"role": "user", "content": f"请从以下文本中提取事实：\n\n{text}"},
    ]

    try:
        result = await ai_client.chat(messages, temperature=0.3, max_tokens=2048)
    except Exception as e:
        return {"added": 0, "skipped": 0, "items": [], "error": f"AI 调用失败: {e}"}

    # 解析 JSON
    import re
    json_match = re.search(r'\[[\s\S]*\]', result)
    if not json_match:
        return {"added": 0, "skipped": 0, "items": [], "raw": result, "error": "无法解析 AI 返回的 JSON"}

    try:
        facts = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        return {"added": 0, "skipped": 0, "items": [], "raw": result, "error": f"JSON 解析失败: {e}"}

    if not isinstance(facts, list):
        return {"added": 0, "skipped": 0, "items": [], "raw": result, "error": "AI 返回的不是数组"}

    # 去重 + 矛盾检测
    conn = get_db()
    existing_rows = conn.execute(
        "SELECT id, content FROM memories WHERE status = 'active'"
    ).fetchall()
    existing_contents = [r["content"].strip().lower() for r in existing_rows]
    conn.close()

    added = []
    skipped = []
    contradictions = []

    for fact in facts:
        if not isinstance(fact, dict) or "content" not in fact:
            continue

        content = fact["content"].strip()
        if not content:
            continue

        # 简单去重：完全匹配（大小写不敏感）
        if content.lower() in existing_contents:
            skipped.append(content)
            continue

        # 矛盾检测：用 AI 判断新事实是否与现有记忆矛盾
        contradiction_id = await _detect_contradiction(content, existing_rows)
        if contradiction_id:
            # 标记旧记忆为 outdated，并建立矛盾关系
            conn = get_db()
            conn.execute(
                "UPDATE memories SET status = 'outdated', updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), contradiction_id),
            )
            conn.commit()
            conn.close()
            _remove_from_chroma(contradiction_id)
            contradictions.append({
                "new_fact": content,
                "old_memory_id": contradiction_id,
                "old_memory_content": next(r["content"] for r in existing_rows if r["id"] == contradiction_id),
            })

        # 存入记忆
        item = MemoryCreate(
            content=content,
            category=fact.get("category", "other"),
            tags=fact.get("tags", []),
            source_tool=payload.source_tool,
            source_ref=payload.source_ref,
            importance=fact.get("importance", 3),
            confidence=fact.get("confidence", 0.9),
        )
        result_item = await memory_remember(item)

        # 如果检测到矛盾，建立关系
        if contradiction_id:
            conn = get_db()
            conn.execute(
                "INSERT INTO memory_links (source_id, target_id, relation) VALUES (?, ?, ?)",
                (result_item["id"], contradiction_id, "矛盾"),
            )
            conn.commit()
            conn.close()

        added.append(result_item)
        existing_contents.append(content.lower())
        existing_rows.append({"id": result_item["id"], "content": content})

    return {
        "added": len(added),
        "skipped": len(skipped),
        "skipped_contents": skipped,
        "contradictions": contradictions,
        "contradictions_checked": len([c for c in contradictions if c]),
        "items": added,
    }


# 矛盾检测配置
CONTRADICTION_DISTANCE_THRESHOLD = float(os.getenv("CONTRADICTION_DISTANCE_THRESHOLD", "0.25"))
CONTRADICTION_KEYWORD_OVERLAP = float(os.getenv("CONTRADICTION_KEYWORD_OVERLAP", "0.3"))
CONTRADICTION_AI_ENABLED = os.getenv("CONTRADICTION_AI_ENABLED", "true").lower() == "true"


_jieba_loaded = False

def _ensure_jieba():
    """懒加载 jieba，首次调用时初始化"""
    global _jieba_loaded
    if _jieba_loaded:
        return
    try:
        import jieba
        jieba.initialize()
        _jieba_loaded = True
    except Exception:
        pass

def _jaccard_similarity(text1: str, text2: str) -> float:
    """计算两个文本的关键词 Jaccard 相似度"""
    _ensure_jieba()

    # 停用词：只过滤无意义虚词和标点，保留实词
    stopwords = {"，", "。", " ", "", "的", "是", "在", "了", "有", "和", "与", "或",
                 "一个", "一些", "这个", "那个", "什么", "怎么", "为什么"}

    try:
        import jieba
        words1 = set(jieba.lcut(text1.lower()))
        words2 = set(jieba.lcut(text2.lower()))
    except Exception:
        # jieba 不可用，降级为简单字符分词（效果差但能跑）
        words1 = set(text1.lower())
        words2 = set(text2.lower())

    words1 = {w for w in words1 if w not in stopwords and len(w) > 1}
    words2 = {w for w in words2 if w not in stopwords and len(w) > 1}
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union) if union else 0.0


async def _detect_contradiction(new_fact: str, existing_rows: list) -> int | None:
    """检测新事实是否与现有记忆矛盾。返回矛盾的记忆 ID，或 None。
    两层架构：粗筛（向量距离 + 关键词重叠）→ 精筛（AI 判断）
    """
    if not existing_rows or not CONTRADICTION_AI_ENABLED:
        return None

    # 先用语义搜索找最相关的几条记忆
    vs = get_vector_store()
    if vs.memory_collection.count() == 0:
        return None

    q_embedding = vs._get_embeddings([new_fact])
    results = vs.memory_collection.query(
        query_embeddings=q_embedding,
        n_results=min(5, len(existing_rows)),
        where={"status": "active"},
    )

    candidates = []
    if results and results["ids"] and results["ids"][0]:
        for i, embed_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            memory_id = meta.get("memory_id") if meta else None
            distance = results["distances"][0][i] if results.get("distances") else 999
            if memory_id:
                candidates.append({"id": memory_id, "distance": distance})

    if not candidates:
        return None

    # 粗筛：距离阈值 或 关键词重叠度
    candidate_texts = []
    for c in candidates:
        row = next((r for r in existing_rows if r["id"] == c["id"]), None)
        if not row:
            continue
        # 条件1：向量距离 < 阈值（cosine distance，越小越相似）
        passed_distance = c["distance"] is not None and c["distance"] < CONTRADICTION_DISTANCE_THRESHOLD
        # 条件2：关键词 Jaccard 重叠度 > 阈值
        jaccard = _jaccard_similarity(new_fact, row["content"])
        passed_keyword = jaccard > CONTRADICTION_KEYWORD_OVERLAP

        if passed_distance or passed_keyword:
            candidate_texts.append(f"ID {row['id']}: {row['content']}")

    if not candidate_texts:
        return None

    # 精筛：AI 判断
    prompt = f"""判断以下新事实是否与任何现有记忆矛盾。

新事实：{new_fact}

现有记忆：
{"\n".join(candidate_texts)}

规则：
1. 如果新事实与某条现有记忆直接矛盾（如"喜欢辣"vs"不吃辣"），返回该记忆的 ID
2. 如果是补充信息（如"喜欢川菜"和"喜欢辣"），不算矛盾，返回 null
3. 只返回一个整数 ID 或 null，不要其他内容

输出格式（纯 JSON）：{{"contradiction_id": null 或 整数}}"""

    try:
        result = await ai_client.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=128,
        )
        match = re.search(r'\{[\s\S]*?\}', result)
        if match:
            data = json.loads(match.group())
            cid = data.get("contradiction_id")
            if cid and any(r["id"] == cid for r in existing_rows):
                return cid
    except Exception as e:
        print(f"[memory] 矛盾检测失败: {e}")

    return None


# ─── 关系管理 ──────────────────────────────────────────────────

@router.post("/memory/forget")
async def memory_forget(payload: dict):
    """遗忘记忆：支持自然语言 query 或指定 memory_id"""
    memory_id = payload.get("memory_id")
    query = payload.get("query", "").strip()
    reason = payload.get("reason", "wrong")
    if reason not in ("outdated", "wrong"):
        reason = "wrong"

    conn = get_db()

    # 如果提供了 memory_id，直接标记
    if memory_id:
        row = conn.execute("SELECT id FROM memories WHERE id = ?", (memory_id,)).fetchone()
        if not row:
            conn.close()
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=404, content={"error": "记忆不存在"})
        conn.execute(
            "UPDATE memories SET status = ?, updated_at = ? WHERE id = ?",
            (reason, datetime.now().isoformat(), memory_id),
        )
        conn.commit()
        conn.close()
        _remove_from_chroma(memory_id)
        return {"forgotten": True, "id": memory_id, "reason": reason, "method": "direct"}

    # 否则用自然语言搜索匹配
    if not query:
        conn.close()
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"error": "请提供 memory_id 或 query"})

    # 语义搜索最相关的记忆
    vs = get_vector_store()
    if vs.memory_collection.count() == 0:
        conn.close()
        return {"forgotten": False, "message": "记忆库为空", "needs_confirmation": False}

    q_embedding = vs._get_embeddings([query])
    results = vs.memory_collection.query(
        query_embeddings=q_embedding,
        n_results=3,
        where={"status": "active"},
    )

    candidates = []
    if results and results["ids"] and results["ids"][0]:
        for i, embed_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results.get("distances") else 999
            memory_id = meta.get("memory_id") if meta else None
            if memory_id:
                row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
                if row:
                    candidates.append({"id": memory_id, "content": row["content"], "distance": distance})

    if not candidates:
        conn.close()
        return {"forgotten": False, "message": "未找到相关记忆", "needs_confirmation": False}

    # top-1 距离足够近（< 0.2）则自动标记，否则返回候选列表让用户确认
    top1 = candidates[0]
    auto_threshold = 0.20  # cosine distance，越小越相似
    if top1["distance"] is not None and top1["distance"] < auto_threshold:
        conn.execute(
            "UPDATE memories SET status = ?, updated_at = ? WHERE id = ?",
            (reason, datetime.now().isoformat(), top1["id"]),
        )
        conn.commit()
        conn.close()
        _remove_from_chroma(top1["id"])
        return {
            "forgotten": True,
            "id": top1["id"],
            "content": top1["content"],
            "reason": reason,
            "method": "auto_match",
            "confidence": f"distance={top1['distance']:.3f}",
        }

    conn.close()
    return {
        "forgotten": False,
        "message": "找到多个候选记忆，请确认",
        "needs_confirmation": True,
        "candidates": [{"id": c["id"], "content": c["content"]} for c in candidates],
    }


@router.post("/memory/{source_id}/link/{target_id}")
async def memory_link(source_id: int, target_id: int, relation: str = "相关"):
    """建立记忆之间的关系"""
    valid_relations = {"相关", "矛盾", "细化", "替代"}
    if relation not in valid_relations:
        relation = "相关"

    conn = get_db()
    # 检查双方存在
    s = conn.execute("SELECT id FROM memories WHERE id = ?", (source_id,)).fetchone()
    t = conn.execute("SELECT id FROM memories WHERE id = ?", (target_id,)).fetchone()
    if not s or not t:
        conn.close()
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "记忆不存在"})

    conn.execute(
        "INSERT INTO memory_links (source_id, target_id, relation) VALUES (?, ?, ?)",
        (source_id, target_id, relation),
    )
    conn.commit()
    conn.close()
    return {"linked": True, "source_id": source_id, "target_id": target_id, "relation": relation}


@router.get("/memory/{memory_id}/links")
async def memory_get_links(memory_id: int):
    """获取记忆的关系网络"""
    conn = get_db()
    outgoing = conn.execute(
        """
        SELECT ml.*, m.content as target_content
        FROM memory_links ml
        JOIN memories m ON ml.target_id = m.id
        WHERE ml.source_id = ?
        """,
        (memory_id,),
    ).fetchall()

    incoming = conn.execute(
        """
        SELECT ml.*, m.content as source_content
        FROM memory_links ml
        JOIN memories m ON ml.source_id = m.id
        WHERE ml.target_id = ?
        """,
        (memory_id,),
    ).fetchall()

    conn.close()
    return {
        "outgoing": [
            {"target_id": r["target_id"], "target_content": r["target_content"], "relation": r["relation"]}
            for r in outgoing
        ],
        "incoming": [
            {"source_id": r["source_id"], "source_content": r["source_content"], "relation": r["relation"]}
            for r in incoming
        ],
    }


# ─── 五层记忆系统：对话总结与分层提取 ───────────────────────────

SUMMARIZE_SYSTEM_PROMPT = """你是对话分析助手。请分析以下用户与 AI 的对话，提取五层记忆信息。

## 输出格式（严格 JSON）
{
  "role_memories": [
    {"content":"用户喜欢先写测试再实现代码","category":"habits","confidence":0.9,"memory_type":"habit"}
  ],
  "project_memories": [
    {"content":"博客项目路由已完成，使用文件系统路由","project_name":"个人博客","memory_type":"progress","confidence":0.95}
  ],
  "workflow_memories": [
    {"content":"使用 TDD 开发，先写测试再实现","workflow_name":"coding","memory_type":"preference","confidence":0.85}
  ],
  "session_memories": [
    {"content":"讨论了三种路由方案，最终选择文件系统路由","memory_type":"discussion","confidence":1.0}
  ],
  "projects_detected": ["个人博客"],
  "summary": "对话核心内容的简短总结"
}

## 分层规则

**role_memories**（角色记忆 — 关于"我是谁"）：
- 个人偏好：编码风格、沟通方式、技术倾向
- 能力边界：擅长什么、不擅长什么
- 工作习惯：作息、工作流偏好
- 只提取高置信度（>0.8）、长期稳定的信息

**project_memories**（项目记忆 — 关于"我在做什么"）：
- 项目进度：完成了什么、阻塞点、下一步
- 项目决策：选择了什么方案、放弃了什么
- 技术栈：用了什么技术
- 必须包含 project_name 字段

**workflow_memories**（工作流记忆 — 关于"我怎么做的"）：
- 开发流程：TDD、分支策略、代码审查习惯
- 工具偏好：IDE、快捷键、常用脚本
- 协作模式：如何与 AI 配合
- 必须包含 workflow_name 字段

**session_memories**（会话记忆 — 关于"刚才聊了什么"）：
- 本次讨论的核心内容
- 已做出的决定
- 待办事项

## 重要规则
1. 不要提取代码片段、技术细节（这些留在知识库）
2. 不要提取 AI 教的通用知识（只提取"用户相关的"）
3. content 必须是完整的陈述句，可独立理解
4. 如果某层没有信息，返回空数组
5. 置信度：1.0=确定事实，0.8-0.9=高度可能，<0.8=不确定（不提取）"""


@router.post("/memory/summarize_and_extract")
async def memory_summarize_and_extract(payload: SummarizeExtractRequest):
    """分析完整对话，分层提取记忆"""
    conversation = payload.conversation.strip()
    if not conversation:
        return {"error": "对话内容为空"}

    messages = [
        {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
        {"role": "user", "content": f"请分析以下对话，提取五层记忆：\n\n{conversation[:8000]}"},
    ]

    try:
        result = await ai_client.chat(messages, temperature=0.3, max_tokens=2048)
    except Exception as e:
        return {"error": f"AI 调用失败: {e}"}

    # 解析 JSON
    import re
    json_match = re.search(r'\{[\s\S]*\}', result)
    if not json_match:
        return {"error": "无法解析 AI 返回", "raw": result[:500]}

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失败: {e}", "raw": result[:500]}

    # 存储各层记忆
    added_counts = {"role": 0, "project": 0, "workflow": 0, "session": 0}
    stored_memories = []

    # 角色记忆
    for mem in data.get("role_memories", []):
        if not isinstance(mem, dict) or "content" not in mem:
            continue
        item = MemoryCreate(
            content=mem["content"],
            category=mem.get("category", "other"),
            tags=mem.get("tags", []),
            source_tool=payload.source_tool,
            source_ref=payload.source_ref,
            importance=mem.get("importance", 4),
            confidence=mem.get("confidence", 0.9),
            memory_layer="role",
            memory_type=mem.get("memory_type", "preference"),
        )
        stored = await memory_remember(item)
        stored_memories.append(stored)
        added_counts["role"] += 1

    # 项目记忆
    for mem in data.get("project_memories", []):
        if not isinstance(mem, dict) or "content" not in mem:
            continue
        project_name = mem.get("project_name", payload.detected_project)
        if project_name:
            # 自动创建/更新项目
            _ensure_project_exists(project_name)
        item = MemoryCreate(
            content=mem["content"],
            category="project",
            tags=mem.get("tags", []),
            source_tool=payload.source_tool,
            source_ref=payload.source_ref,
            importance=mem.get("importance", 4),
            confidence=mem.get("confidence", 0.9),
            memory_layer="project",
            project_name=project_name,
            memory_type=mem.get("memory_type", "fact"),
        )
        stored = await memory_remember(item)
        stored_memories.append(stored)
        added_counts["project"] += 1

    # 工作流记忆
    for mem in data.get("workflow_memories", []):
        if not isinstance(mem, dict) or "content" not in mem:
            continue
        workflow_name = mem.get("workflow_name", "")
        if workflow_name:
            _ensure_workflow_exists(workflow_name)
        item = MemoryCreate(
            content=mem["content"],
            category="workflow",
            tags=mem.get("tags", []),
            source_tool=payload.source_tool,
            source_ref=payload.source_ref,
            importance=mem.get("importance", 3),
            confidence=mem.get("confidence", 0.85),
            memory_layer="workflow",
            workflow_name=workflow_name,
            memory_type=mem.get("memory_type", "preference"),
        )
        stored = await memory_remember(item)
        stored_memories.append(stored)
        added_counts["workflow"] += 1

    # 会话记忆
    for mem in data.get("session_memories", []):
        if not isinstance(mem, dict) or "content" not in mem:
            continue
        item = MemoryCreate(
            content=mem["content"],
            category="session",
            tags=mem.get("tags", []),
            source_tool=payload.source_tool,
            source_ref=payload.source_ref,
            importance=mem.get("importance", 2),
            confidence=mem.get("confidence", 1.0),
            memory_layer="session",
            memory_type=mem.get("memory_type", "discussion"),
        )
        stored = await memory_remember(item)
        stored_memories.append(stored)
        added_counts["session"] += 1

    return {
        "added": sum(added_counts.values()),
        "added_by_layer": added_counts,
        "projects_detected": data.get("projects_detected", []),
        "summary": data.get("summary", ""),
        "memories": stored_memories,
    }


def _ensure_project_exists(name: str):
    """如果项目不存在则创建"""
    if not name:
        return
    conn = get_db()
    existing = conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO projects (name, status, last_active) VALUES (?, 'active', ?)",
            (name, datetime.now().isoformat()),
        )
        conn.commit()
    else:
        conn.execute(
            "UPDATE projects SET last_active = ? WHERE name = ?",
            (datetime.now().isoformat(), name),
        )
        conn.commit()
    conn.close()


def _ensure_workflow_exists(name: str):
    """如果工作流不存在则创建"""
    if not name:
        return
    conn = get_db()
    existing = conn.execute("SELECT id FROM workflows WHERE name = ?", (name,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO workflows (name, updated_at) VALUES (?, ?)",
            (name, datetime.now().isoformat()),
        )
        conn.commit()
    else:
        conn.execute(
            "UPDATE workflows SET updated_at = ? WHERE name = ?",
            (datetime.now().isoformat(), name),
        )
        conn.commit()
    conn.close()


# ─── 智能上下文注入 ─────────────────────────────────────────────

@router.get("/memory/context_inject")
async def memory_context_inject(q: str = "", tool: str = "", session_id: str = ""):
    """根据当前查询，生成要注入 AI 上下文的记忆摘要"""
    if not q.strip():
        q = "当前对话"

    conn = get_db()

    # 1. 角色记忆：取最近 10 条高置信度偏好/习惯
    role_rows = conn.execute(
        """SELECT content, category, confidence FROM memories
           WHERE memory_layer = 'role' AND status = 'active'
           ORDER BY confidence DESC, updated_at DESC LIMIT 10"""
    ).fetchall()

    # 2. 活跃项目：最近 30 天有更新的项目
    project_rows = conn.execute(
        """SELECT p.name, p.description, p.progress_note, p.tech_stack,
                  COUNT(m.id) as mem_count
           FROM projects p
           LEFT JOIN memories m ON m.project_name = p.name AND m.status = 'active'
           WHERE p.status = 'active' AND p.last_active > datetime('now', '-30 days')
           GROUP BY p.id
           ORDER BY p.last_active DESC LIMIT 5"""
    ).fetchall()

    # 3. 相关工作流：根据 query 关键词匹配
    workflow_rows = conn.execute(
        """SELECT name, trigger_keywords, preferences FROM workflows
           ORDER BY updated_at DESC LIMIT 10"""
    ).fetchall()

    # 4. 语义搜索相关记忆（所有层）
    vs = get_vector_store()
    relevant_memories = []
    if vs.memory_collection.count() > 0:
        q_embedding = vs._get_embeddings([q])
        results = vs.memory_collection.query(
            query_embeddings=q_embedding,
            n_results=5,
            where={"status": "active"},
        )
        if results and results["ids"] and results["ids"][0]:
            for i, embed_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                memory_id = meta.get("memory_id") if meta else None
                if memory_id:
                    row = conn.execute(
                        "SELECT content, memory_layer, project_name, workflow_name FROM memories WHERE id = ?",
                        (memory_id,),
                    ).fetchone()
                    if row:
                        relevant_memories.append(dict(row))
                        # 更新访问计数
                        conn.execute(
                            "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                            (datetime.now().isoformat(), memory_id),
                        )
            conn.commit()

    conn.close()

    # 构建注入内容
    parts = []

    # 角色画像
    if role_rows:
        role_lines = [f"- {r['content']} ({r['category']})" for r in role_rows]
        parts.append(f"【用户画像】\n" + "\n".join(role_lines))

    # 活跃项目
    if project_rows:
        proj_lines = []
        for r in project_rows:
            tech = json.loads(r["tech_stack"] or "[]")
            tech_str = f" 技术栈: {', '.join(tech)}" if tech else ""
            progress = f" 进度: {r['progress_note']}" if r["progress_note"] else ""
            proj_lines.append(f"- {r['name']}{tech_str}{progress}")
        parts.append(f"【活跃项目】\n" + "\n".join(proj_lines))

    # 相关工作流
    matched_workflows = []
    for r in workflow_rows:
        keywords = json.loads(r["trigger_keywords"] or "[]")
        if any(kw in q.lower() for kw in keywords):
            prefs = json.loads(r["preferences"] or "{}")
            pref_str = " ".join(f"{k}={v}" for k, v in prefs.items()) if prefs else ""
            matched_workflows.append(f"- {r['name']}: {pref_str}")
    if matched_workflows:
        parts.append(f"【工作流偏好】\n" + "\n".join(matched_workflows))

    # 相关记忆
    if relevant_memories:
        mem_lines = []
        for m in relevant_memories:
            layer_label = {"role": "[角色]", "project": "[项目]", "workflow": "[工作流]", "session": "[会话]", "world": "[知识]"}.get(m.get("memory_layer", ""), "")
            mem_lines.append(f"- {layer_label} {m['content']}")
        parts.append(f"【相关记忆】\n" + "\n".join(mem_lines))

    full_prompt = "\n\n".join(parts)

    return {
        "injection": {
            "role_profile": "\n".join([f"- {r['content']}" for r in role_rows]) if role_rows else "",
            "active_projects": [
                {"name": r["name"], "progress": r["progress_note"], "tech_stack": json.loads(r["tech_stack"] or "[]")}
                for r in project_rows
            ],
            "relevant_workflows": [{"name": r["name"], "preferences": json.loads(r["preferences"] or "{}")} for r in workflow_rows],
            "relevant_memories": relevant_memories,
        },
        "full_prompt": full_prompt,
        "query": q,
    }


# ─── Projects CRUD ──────────────────────────────────────────────

@router.get("/projects")
async def list_projects(status: str = ""):
    """列出所有项目"""
    conn = get_db()
    if status:
        rows = conn.execute(
            "SELECT * FROM projects WHERE status = ? ORDER BY last_active DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM projects ORDER BY last_active DESC").fetchall()
    conn.close()
    return [{
        "id": r["id"],
        "name": r["name"],
        "description": r["description"],
        "status": r["status"],
        "tech_stack": json.loads(r["tech_stack"] or "[]"),
        "start_date": r["start_date"],
        "last_active": r["last_active"],
        "progress_note": r["progress_note"],
    } for r in rows]


@router.post("/projects")
async def create_project(payload: dict):
    """创建项目"""
    name = (payload.get("name") or "").strip()
    if not name:
        return {"error": "项目名称不能为空"}

    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO projects (name, description, status, tech_stack, progress_note) VALUES (?, ?, ?, ?, ?)",
            (
                name,
                payload.get("description", ""),
                payload.get("status", "active"),
                json.dumps(payload.get("tech_stack", []), ensure_ascii=False),
                payload.get("progress_note", ""),
            ),
        )
        conn.commit()
        project_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return {"error": "项目已存在"}
    conn.close()
    return {"id": project_id, "name": name, "status": "created"}


@router.get("/projects/{project_name}/memories")
async def get_project_memories(project_name: str):
    """获取项目相关的所有记忆"""
    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM memories
           WHERE project_name = ? AND status = 'active'
           ORDER BY updated_at DESC""",
        (project_name,),
    ).fetchall()
    conn.close()
    return {"project": project_name, "memories": [_row_to_dict(r) for r in rows]}


@router.put("/projects/{project_name}/progress")
async def update_project_progress(project_name: str, payload: dict):
    """更新项目进度"""
    conn = get_db()
    existing = conn.execute("SELECT id FROM projects WHERE name = ?", (project_name,)).fetchone()
    if not existing:
        conn.close()
        return {"error": "项目不存在"}

    updates = []
    params = []
    if "progress_note" in payload:
        updates.append("progress_note = ?")
        params.append(payload["progress_note"])
    if "status" in payload:
        updates.append("status = ?")
        params.append(payload["status"])
    if "tech_stack" in payload:
        updates.append("tech_stack = ?")
        params.append(json.dumps(payload["tech_stack"], ensure_ascii=False))
    if "description" in payload:
        updates.append("description = ?")
        params.append(payload["description"])

    if updates:
        updates.append("last_active = ?")
        params.append(datetime.now().isoformat())
        params.append(project_name)
        conn.execute(
            f"UPDATE projects SET {', '.join(updates)} WHERE name = ?",
            params,
        )
        conn.commit()
    conn.close()
    return {"updated": True, "project": project_name}


# ─── Workflows CRUD ─────────────────────────────────────────────

@router.get("/workflows")
async def list_workflows():
    """列出所有工作流"""
    conn = get_db()
    rows = conn.execute("SELECT * FROM workflows ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [{
        "id": r["id"],
        "name": r["name"],
        "description": r["description"],
        "trigger_keywords": json.loads(r["trigger_keywords"] or "[]"),
        "preferences": json.loads(r["preferences"] or "{}"),
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    } for r in rows]


@router.post("/workflows")
async def create_workflow(payload: dict):
    """创建工作流"""
    name = (payload.get("name") or "").strip()
    if not name:
        return {"error": "工作流名称不能为空"}

    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO workflows (name, description, trigger_keywords, preferences) VALUES (?, ?, ?, ?)",
            (
                name,
                payload.get("description", ""),
                json.dumps(payload.get("trigger_keywords", []), ensure_ascii=False),
                json.dumps(payload.get("preferences", {}), ensure_ascii=False),
            ),
        )
        conn.commit()
        workflow_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return {"error": "工作流已存在"}
    conn.close()
    return {"id": workflow_id, "name": name, "status": "created"}


@router.get("/workflows/{workflow_name}")
async def get_workflow(workflow_name: str):
    """获取工作流详情"""
    conn = get_db()
    row = conn.execute("SELECT * FROM workflows WHERE name = ?", (workflow_name,)).fetchone()
    conn.close()
    if not row:
        return {"error": "工作流不存在"}
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "trigger_keywords": json.loads(row["trigger_keywords"] or "[]"),
        "preferences": json.loads(row["preferences"] or "{}"),
    }


@router.put("/workflows/{workflow_name}/preferences")
async def update_workflow_preferences(workflow_name: str, payload: dict):
    """更新工作流偏好"""
    conn = get_db()
    existing = conn.execute("SELECT id FROM workflows WHERE name = ?", (workflow_name,)).fetchone()
    if not existing:
        conn.close()
        return {"error": "工作流不存在"}

    updates = []
    params = []
    if "preferences" in payload:
        updates.append("preferences = ?")
        params.append(json.dumps(payload["preferences"], ensure_ascii=False))
    if "trigger_keywords" in payload:
        updates.append("trigger_keywords = ?")
        params.append(json.dumps(payload["trigger_keywords"], ensure_ascii=False))
    if "description" in payload:
        updates.append("description = ?")
        params.append(payload["description"])

    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(workflow_name)
        conn.execute(
            f"UPDATE workflows SET {', '.join(updates)} WHERE name = ?",
            params,
        )
        conn.commit()
    conn.close()
    return {"updated": True, "workflow": workflow_name}


# ─── 记忆列表支持按层过滤 ───────────────────────────────────────

@router.get("/memory/list")
async def memory_list(cat: str = "", status: str = "", layer: str = "", project: str = "", workflow: str = "", limit: int = 50, offset: int = 0):
    """列表查询记忆（支持分层过滤）"""
    conn = get_db()
    where_clauses = ["1=1"]
    params = []

    if status:
        where_clauses.append("status = ?")
        params.append(status)
    if cat:
        where_clauses.append("category = ?")
        params.append(cat)
    if layer:
        where_clauses.append("memory_layer = ?")
        params.append(layer)
    if project:
        where_clauses.append("project_name = ?")
        params.append(project)
    if workflow:
        where_clauses.append("workflow_name = ?")
        params.append(workflow)

    where_sql = " AND ".join(where_clauses)
    rows = conn.execute(
        f"SELECT * FROM memories WHERE {where_sql} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (*params, limit, offset),
    ).fetchall()

    total = conn.execute(
        f"SELECT COUNT(*) as c FROM memories WHERE {where_sql}", params
    ).fetchone()["c"]

    conn.close()
    return {"items": [_row_to_dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}
