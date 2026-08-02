import os, sys, tempfile, json, re
from fastapi import APIRouter, UploadFile, File, Form
from database import get_db
from processing.processors import can_handle, process_bytes, sha256, is_duplicate
from endpoints.links import sync_document_links, parse_wiki_links

router = APIRouter()


def _auto_tag_sync(title: str, content: str) -> list:
    """同步调用 AI 识别文档标签"""
    import httpx
    analysis_text = (content or "")[:2000]
    api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    api_key = "sk-d703daaf15d343b88dce53a1dd4d32e4"
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

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
        resp = httpx.post(
            f"{api_base.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 256},
            timeout=30
        )
        if resp.status_code != 200:
            print(f"[auto-tag] API error: {resp.status_code} {resp.text[:200]}")
            return []
        data = resp.json()
        raw = data["choices"][0]["message"]["content"]
        print(f"[auto-tag] AI raw response: {raw[:200]}")
        match = re.search(r'\[[\s\S]*?\]', raw)
        if match:
            tags = json.loads(match.group())
            print(f"[auto-tag] parsed tags: {tags}")
            if isinstance(tags, list):
                tags = [str(t).strip() for t in tags if t][:8]
                tags = list(dict.fromkeys(tags))
                print(f"[auto-tag] final tags: {tags}")
                return tags
        print(f"[auto-tag] no JSON array found in response")
        return []
    except Exception as e:
        print(f"[auto-tag] error: {e}")
        import traceback
        traceback.print_exc()
        return []


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

    # 解析并存储 [[wiki-link]]
    try:
        sync_document_links(doc_id, text)
    except Exception as e:
        print(f"链接解析失败 (文档 {doc_id}): {e}")

    conn.close()

    # AI 标签识别（同步调用）
    try:
        tags = _auto_tag_sync(title, text)
        if tags:
            tags_json = json.dumps(tags, ensure_ascii=False)
            conn2 = get_db()
            conn2.execute("UPDATE documents SET tags = ? WHERE id = ?", (tags_json, doc_id))
            conn2.commit()
            conn2.close()
            # 同步向量库 tags
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
    except Exception as e:
        print(f"[auto-tag] doc_id={doc_id} failed: {e}")

    wiki_links = parse_wiki_links(text)
    return {"id": doc_id, "title": file.filename, "char_count": len(text), "category_name": category_name, "wiki_links": len(wiki_links)}


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

    try:
        sync_document_links(doc_id, text)
    except Exception as e:
        print(f"链接解析失败 (文档 {doc_id}): {e}")

    conn.close()

    # AI 标签识别（同步调用）
    try:
        tags = _auto_tag_sync(title, text)
        if tags:
            tags_json = json.dumps(tags, ensure_ascii=False)
            conn2 = get_db()
            conn2.execute("UPDATE documents SET tags = ? WHERE id = ?", (tags_json, doc_id))
            conn2.commit()
            conn2.close()
            # 同步向量库 tags
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
    except Exception as e:
        print(f"[auto-tag] doc_id={doc_id} failed: {e}")

    wiki_links = parse_wiki_links(text)
    return {"id": doc_id, "title": title, "char_count": len(text), "category_name": category_name, "wiki_links": len(wiki_links)}


@router.get("/documents")
def list_documents(category_id: int = None, search: str = None, tag: str = None,
                   date_from: str = None, date_to: str = None, limit: int = 50,
                   sort_by: str = 'created_at', sort_order: str = 'desc'):
    conn = get_db()
    conditions = []
    params = []

    if category_id:
        conditions.append("d.category_id = ?")
        params.append(category_id)

    if search:
        conditions.append("(d.title LIKE ? OR d.content LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])

    if tag:
        # 标签以 JSON 数组存储，用 LIKE 模糊匹配
        conditions.append("d.tags LIKE ?")
        params.append(f"%{tag}%")

    if date_from:
        conditions.append("d.created_at >= ?")
        params.append(date_from)

    if date_to:
        conditions.append("d.created_at <= ?")
        params.append(date_to + " 23:59:59")

    # 排序字段白名单
    allowed_sort_by = {'created_at', 'title', 'char_count'}
    allowed_sort_order = {'asc', 'desc'}
    sort_by = sort_by if sort_by in allowed_sort_by else 'created_at'
    sort_order = sort_order.lower() if sort_order.lower() in allowed_sort_order else 'desc'

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    query = f"""SELECT d.*, c.name AS category_name, c.icon AS category_icon, c.color AS category_color
               FROM documents d
               LEFT JOIN categories c ON d.category_id = c.id
               {where}
               ORDER BY d.{sort_by} {sort_order} LIMIT ?"""
    params.append(limit)

    rows = conn.execute(query, params).fetchall()

    # 检测 ASR 失败文档（摘要类文档且内容中包含 ASR 错误标记）
    result = []
    for r in rows:
        doc = dict(r)
        if doc.get("source") in ("douyin-summary", "bilibili-summary", "xiaohongshu-summary"):
            content = doc.get("content", "") or ""
            # 检测 ASR 失败的各种标记
            content_preview = content[:1200]
            doc["asr_failed"] = (
                "asr_error" in content or
                "ASR" in content and "提取失败" in content or
                "语音识别" in content and "提取失败" in content or
                "语音提取失败" in content or
                "⚠️ 语音提取失败" in content or
                "ASR 失败" in content or
                "识别失败" in content or
                "API调用失败" in content_preview or
                "Invalid API-key" in content_preview or
                ("API" in content_preview and ("不可用" in content_preview or "欠费" in content_preview or "API Key 无效" in content_preview)) or
                ("Level 3" in content[:1000] and "基于视频标题" in content[:1000])
            )
        else:
            doc["asr_failed"] = False
        result.append(doc)

    conn.close()
    return result


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
