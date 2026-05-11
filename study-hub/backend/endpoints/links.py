"""双向链接 API：解析 [[wiki-link]]，出链 / 反链查询。"""
import re
from fastapi import APIRouter
from database import get_db

router = APIRouter()

# [[Page Title]] 或 [[Page Title|display text]]
LINK_RE = re.compile(r'\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]')


def parse_wiki_links(content: str) -> list[dict]:
    """从文本中提取所有 [[...]] 链接，返回 [{target_title, link_text}]."""
    links = []
    for m in LINK_RE.finditer(content):
        target = m.group(1).strip()
        display = (m.group(2) or target).strip()
        if target:
            links.append({"target_title": target, "link_text": display})
    return links


def sync_document_links(doc_id: int, content: str):
    """解析文档内容中的 [[...]] 并同步到 document_links 表。"""
    conn = get_db()
    conn.execute("DELETE FROM document_links WHERE source_doc_id = ?", (doc_id,))
    links = parse_wiki_links(content)
    for link in links:
        # 尝试解析目标文档 ID（按标题精确匹配）
        target_row = conn.execute(
            "SELECT id FROM documents WHERE title = ? LIMIT 1",
            (link["target_title"],),
        ).fetchone()
        target_doc_id = target_row["id"] if target_row else None
        conn.execute(
            "INSERT INTO document_links (source_doc_id, target_title, target_doc_id, link_text) VALUES (?, ?, ?, ?)",
            (doc_id, link["target_title"], target_doc_id, link["link_text"]),
        )
    conn.commit()
    conn.close()


@router.get("/documents/{doc_id}/links")
def get_document_links(doc_id: int):
    """获取文档的出链（它指向了哪些文档）。"""
    conn = get_db()
    doc = conn.execute("SELECT id, title FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not doc:
        conn.close()
        return {"error": "文档不存在"}

    rows = conn.execute(
        """SELECT dl.*, d.title AS target_doc_title
           FROM document_links dl
           LEFT JOIN documents d ON dl.target_doc_id = d.id
           WHERE dl.source_doc_id = ?
           ORDER BY dl.id""",
        (doc_id,),
    ).fetchall()
    conn.close()
    return {
        "doc_id": doc_id,
        "doc_title": doc["title"],
        "links": [dict(r) for r in rows],
    }


@router.get("/documents/{doc_id}/backlinks")
def get_document_backlinks(doc_id: int):
    """获取文档的反链（哪些文档指向了它）。"""
    conn = get_db()
    doc = conn.execute("SELECT id, title FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not doc:
        conn.close()
        return {"error": "文档不存在"}

    rows = conn.execute(
        """SELECT d.id AS source_doc_id, d.title AS source_doc_title,
                  dl.target_title, dl.link_text, dl.id AS link_id
           FROM document_links dl
           JOIN documents d ON dl.source_doc_id = d.id
           WHERE dl.target_title = ? OR dl.target_doc_id = ?
           ORDER BY d.title""",
        (doc["title"], doc_id),
    ).fetchall()
    conn.close()
    return {
        "doc_id": doc_id,
        "doc_title": doc["title"],
        "backlinks": [dict(r) for r in rows],
    }
