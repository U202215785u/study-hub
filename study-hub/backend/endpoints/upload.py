import os, sys, tempfile, json
from fastapi import APIRouter, UploadFile, File, Form
from database import get_db
from processing.processors import can_handle, process_bytes, sha256, is_duplicate

router = APIRouter()


def _get_category_name(category_id) -> str:
    if category_id is None:
        return ""
    conn = get_db()
    row = conn.execute("SELECT name FROM categories WHERE id = ?", (category_id,)).fetchone()
    conn.close()
    return row["name"] if row else ""


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), category_id: int = Form(None)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if not can_handle(ext):
        return {"error": f"不支持的文件格式: {ext}"}

    data = await file.read()
    try:
        text = process_bytes(data, ext)
    except Exception as e:
        return {"error": str(e)}

    if not text.strip():
        return {"error": "文件内容为空或无法提取文本"}

    content_hash = sha256(text)
    if is_duplicate(content_hash):
        return {"error": "内容重复，该文档已存在"}

    category_name = _get_category_name(category_id)

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO documents (title, content, content_type, source, category_id, content_hash, char_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (file.filename, text, ext.lstrip("."), "upload", category_id, content_hash, len(text))
    )
    doc_id = cur.lastrowid
    conn.commit()

    try:
        from processing.chunker import chunk_text
        from processing.vector_store import get_vector_store
        chunks = chunk_text(text)
        vs = get_vector_store()
        vs.add_document(doc_id, file.filename, chunks, category=category_name)
        conn.execute("UPDATE documents SET chunk_count = ? WHERE id = ?", (len(chunks), doc_id))
        conn.commit()
    except Exception as e:
        print(f"向量化失败 (文档 {doc_id}): {e}")

    conn.close()
    return {"id": doc_id, "title": file.filename, "char_count": len(text), "category_name": category_name}


@router.post("/upload/text")
async def upload_text(payload: dict):
    text = (payload.get("content") or payload.get("text") or "").strip()
    title = payload.get("title", "AI对话记录")
    source = payload.get("source", "extension")
    category_id = payload.get("category_id")
    tags = payload.get("tags", [])

    if not text:
        return {"error": "内容为空"}

    content_hash = sha256(text)
    if is_duplicate(content_hash):
        return {"error": "内容重复，该文档已存在"}

    category_name = _get_category_name(category_id)
    tags_json = json.dumps(tags, ensure_ascii=False)

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO documents (title, content, content_type, source, category_id, tags, content_hash, char_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (title, text, "text", source, category_id, tags_json, content_hash, len(text))
    )
    doc_id = cur.lastrowid
    conn.commit()

    try:
        from processing.chunker import chunk_text
        from processing.vector_store import get_vector_store
        chunks = chunk_text(text)
        vs = get_vector_store()
        tags_str = ",".join(tags) if tags else ""
        vs.add_document(doc_id, title, chunks, category=category_name, tags=tags_str)
        conn.execute("UPDATE documents SET chunk_count = ? WHERE id = ?", (len(chunks), doc_id))
        conn.commit()
    except Exception as e:
        print(f"向量化失败 (文档 {doc_id}): {e}")

    conn.close()
    return {"id": doc_id, "title": title, "char_count": len(text), "category_name": category_name}


@router.get("/documents")
def list_documents(category_id: int = None):
    conn = get_db()
    if category_id:
        rows = conn.execute(
            """SELECT d.*, c.name AS category_name, c.icon AS category_icon, c.color AS category_color
               FROM documents d
               LEFT JOIN categories c ON d.category_id = c.id
               WHERE d.category_id = ?
               ORDER BY d.created_at DESC LIMIT 50""",
            (category_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT d.*, c.name AS category_name, c.icon AS category_icon, c.color AS category_color
               FROM documents d
               LEFT JOIN categories c ON d.category_id = c.id
               ORDER BY d.created_at DESC LIMIT 50"""
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/documents/{doc_id}")
def get_document(doc_id: int):
    conn = get_db()
    row = conn.execute(
        """SELECT d.*, c.name AS category_name, c.icon AS category_icon, c.color AS category_color
           FROM documents d
           LEFT JOIN categories c ON d.category_id = c.id
           WHERE d.id = ?""",
        (doc_id,),
    ).fetchone()
    conn.close()
    if not row:
        return {"error": "文档不存在"}
    return dict(row)


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int):
    conn = get_db()
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not doc:
        conn.close()
        return {"error": "文档不存在"}

    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

    # 删除向量库数据
    try:
        from processing.vector_store import get_vector_store
        vs = get_vector_store()
        existing = vs.collection.get(where={"doc_id": doc_id})
        if existing and existing["ids"]:
            vs.collection.delete(ids=existing["ids"])
    except Exception:
        pass

    return {"status": "ok"}


@router.post("/documents/batch-delete")
def batch_delete_documents(payload: dict):
    doc_ids = payload.get("doc_ids", [])
    if not doc_ids:
        return {"error": "请选择文档"}

    conn = get_db()
    placeholders = ",".join("?" for _ in doc_ids)
    conn.execute(f"DELETE FROM documents WHERE id IN ({placeholders})", doc_ids)
    conn.commit()
    conn.close()

    try:
        from processing.vector_store import get_vector_store
        vs = get_vector_store()
        for doc_id in doc_ids:
            existing = vs.collection.get(where={"doc_id": doc_id})
            if existing and existing["ids"]:
                vs.collection.delete(ids=existing["ids"])
    except Exception:
        pass

    return {"status": "ok", "count": len(doc_ids)}
