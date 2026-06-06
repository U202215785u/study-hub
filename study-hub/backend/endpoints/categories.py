import json
from fastapi import APIRouter
from database import get_db

router = APIRouter()


@router.get("/categories")
def list_categories():
    conn = get_db()
    rows = conn.execute(
        """SELECT c.*, COUNT(d.id) AS doc_count
           FROM categories c
           LEFT JOIN documents d ON d.category_id = c.id
           GROUP BY c.id
           ORDER BY c.sort_order, c.name"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/categories")
def create_category(payload: dict):
    name = (payload.get("name") or "").strip()
    if not name:
        return {"error": "分类名称不能为空"}

    icon = payload.get("icon", "📁")
    color = payload.get("color", "#7c8aff")
    sort_order = payload.get("sort_order", 0)
    tag_rules = json.dumps(payload.get("tag_rules", []), ensure_ascii=False)

    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO categories (name, icon, color, sort_order, tag_rules) VALUES (?, ?, ?, ?, ?)",
            (name, icon, color, sort_order, tag_rules),
        )
        conn.commit()
        cat_id = cur.lastrowid
        return {"id": cat_id, "name": name, "icon": icon, "color": color, "sort_order": sort_order, "tag_rules": json.loads(tag_rules), "doc_count": 0}
    except Exception as e:
        return {"error": f"创建失败: {e}"}
    finally:
        conn.close()


@router.put("/categories/{cat_id}")
def update_category(cat_id: int, payload: dict):
    conn = get_db()
    existing = conn.execute("SELECT * FROM categories WHERE id = ?", (cat_id,)).fetchone()
    if not existing:
        conn.close()
        return {"error": "分类不存在"}

    name = payload.get("name", existing["name"])
    icon = payload.get("icon", existing["icon"])
    color = payload.get("color", existing["color"])
    sort_order = payload.get("sort_order", existing["sort_order"])
    tag_rules = json.dumps(payload.get("tag_rules", json.loads(existing["tag_rules"] or "[]")), ensure_ascii=False)

    conn.execute(
        "UPDATE categories SET name = ?, icon = ?, color = ?, sort_order = ?, tag_rules = ? WHERE id = ?",
        (name, icon, color, sort_order, tag_rules, cat_id),
    )
    conn.commit()
    conn.close()
    return {"id": cat_id, "name": name, "icon": icon, "color": color, "sort_order": sort_order, "tag_rules": json.loads(tag_rules)}


@router.delete("/categories/{cat_id}")
def delete_category(cat_id: int):
    conn = get_db()
    existing = conn.execute("SELECT * FROM categories WHERE id = ?", (cat_id,)).fetchone()
    if not existing:
        conn.close()
        return {"error": "分类不存在"}

    conn.execute("UPDATE documents SET category_id = NULL WHERE category_id = ?", (cat_id,))
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.put("/documents/{doc_id}/move")
def move_document(doc_id: int, payload: dict):
    """移动文档到指定分类，同时更新向量库 metadata"""
    category_id = payload.get("category_id")  # None 或 null 表示移除分类

    conn = get_db()
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not doc:
        conn.close()
        return {"error": "文档不存在"}

    # 获取分类名
    category_name = ""
    if category_id is not None:
        cat = conn.execute("SELECT name FROM categories WHERE id = ?", (category_id,)).fetchone()
        if cat:
            category_name = cat["name"]
        else:
            conn.close()
            return {"error": "目标分类不存在"}

    conn.execute("UPDATE documents SET category_id = ? WHERE id = ?", (category_id, doc_id))
    conn.commit()
    conn.close()

    # 同步更新向量库 metadata
    try:
        from processing.vector_store import get_vector_store
        vs = get_vector_store()
        existing = vs.collection.get(where={"doc_id": doc_id})
        if existing and existing["ids"]:
            for meta in existing["metadatas"]:
                meta["category"] = category_name
            vs.collection.update(ids=existing["ids"], metadatas=existing["metadatas"])
    except Exception:
        pass

    return {"status": "ok", "doc_id": doc_id, "category_id": category_id, "category_name": category_name}


@router.put("/documents/batch-move")
def batch_move_documents(payload: dict):
    """批量移动文档到指定分类"""
    doc_ids = payload.get("doc_ids", [])
    category_id = payload.get("category_id")

    if not doc_ids:
        return {"error": "请选择文档"}

    conn = get_db()
    category_name = ""
    if category_id is not None:
        cat = conn.execute("SELECT name FROM categories WHERE id = ?", (category_id,)).fetchone()
        if cat:
            category_name = cat["name"]
        else:
            conn.close()
            return {"error": "目标分类不存在"}

    placeholders = ",".join("?" for _ in doc_ids)
    conn.execute(
        f"UPDATE documents SET category_id = ? WHERE id IN ({placeholders})",
        [category_id] + doc_ids,
    )
    conn.commit()
    conn.close()

    # 同步更新向量库 metadata
    try:
        from processing.vector_store import get_vector_store
        vs = get_vector_store()
        for doc_id in doc_ids:
            existing = vs.collection.get(where={"doc_id": doc_id})
            if existing and existing["ids"]:
                for meta in existing["metadatas"]:
                    meta["category"] = category_name
                vs.collection.update(ids=existing["ids"], metadatas=existing["metadatas"])
    except Exception:
        pass

    return {"status": "ok", "count": len(doc_ids)}


@router.put("/documents/{doc_id}/tags")
def update_document_tags(doc_id: int, payload: dict):
    """更新文档标签"""
    tags = payload.get("tags", [])

    conn = get_db()
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not doc:
        conn.close()
        return {"error": "文档不存在"}

    tags_json = json.dumps(tags, ensure_ascii=False)
    conn.execute("UPDATE documents SET tags = ? WHERE id = ?", (tags_json, doc_id))
    conn.commit()
    conn.close()

    # 同步向量库
    try:
        from processing.vector_store import get_vector_store
        vs = get_vector_store()
        existing = vs.collection.get(where={"doc_id": doc_id})
        if existing and existing["ids"]:
            tags_str = ",".join(tags)
            for meta in existing["metadatas"]:
                meta["tags"] = tags_str
            vs.collection.update(ids=existing["ids"], metadatas=existing["metadatas"])
    except Exception:
        pass

    return {"status": "ok", "doc_id": doc_id, "tags": tags}


@router.post("/documents/{doc_id}/auto-tags")
async def auto_tag_document(doc_id: int):
    """AI 自动识别文档标签"""
    conn = get_db()
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not doc:
        conn.close()
        return {"error": "文档不存在"}

    content = doc["content"] or ""
    title = doc["title"] or ""
    conn.close()

    # 取前 2000 字作为分析内容
    analysis_text = content[:2000]

    from ai_client import ai_client
    prompt = f"""请分析以下文档，提取 3-8 个精准标签。
要求：
1. 标签应概括文档的核心主题、技术栈、领域
2. 每个标签 2-6 个中文字符，或 1-3 个英文单词
3. 输出格式必须是 JSON 数组，不要其他内容
4. 不要输出解释，只输出 JSON

文档标题：{title}

文档内容（前 2000 字）：
{analysis_text}

请输出标签数组："""

    try:
        raw = await ai_client.chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=256)
        # 尝试提取 JSON 数组
        import re
        match = re.search(r'\[[\s\S]*?\]', raw)
        if match:
            tags = json.loads(match.group())
            if isinstance(tags, list):
                # 过滤非字符串项，去重，限制最多 8 个
                tags = [str(t).strip() for t in tags if t][:8]
                tags = list(dict.fromkeys(tags))  # 去重保持顺序
                return {"tags": tags}
        return {"error": "AI 返回格式不正确", "raw": raw[:200]}
    except Exception as e:
        return {"error": f"识别失败: {e}"}
