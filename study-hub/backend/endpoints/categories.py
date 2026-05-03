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

    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO categories (name, icon, color, sort_order) VALUES (?, ?, ?, ?)",
            (name, icon, color, sort_order),
        )
        conn.commit()
        cat_id = cur.lastrowid
        return {"id": cat_id, "name": name, "icon": icon, "color": color, "sort_order": sort_order, "doc_count": 0}
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

    conn.execute(
        "UPDATE categories SET name = ?, icon = ?, color = ?, sort_order = ? WHERE id = ?",
        (name, icon, color, sort_order, cat_id),
    )
    conn.commit()
    conn.close()
    return {"id": cat_id, "name": name, "icon": icon, "color": color, "sort_order": sort_order}


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
