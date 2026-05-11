"""一键导出知识库为 Markdown 文件（ZIP 下载）。"""
import io, zipfile, json, re
from urllib.parse import quote
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from database import get_db

router = APIRouter()

# 安全文件名：替换非法字符
_SAFE_RE = re.compile(r'[\\/:*?"<>|]')


def _safe_filename(name: str) -> str:
    return _SAFE_RE.sub('_', name).strip()


def _doc_to_markdown(doc: dict) -> str:
    """将文档转为带 frontmatter 的 Markdown。"""
    tags = []
    try:
        tags = json.loads(doc.get("tags") or "[]")
    except (json.JSONDecodeError, TypeError):
        pass

    frontmatter = f"""---
title: "{doc['title']}"
created_at: {doc.get('created_at', '')}
char_count: {doc.get('char_count', 0)}
source: {doc.get('source', '')}
"""
    if doc.get("category_name"):
        frontmatter += f"category: \"{doc['category_name']}\"\n"
    if tags:
        frontmatter += f"tags: [{', '.join(repr(t) for t in tags)}]\n"
    frontmatter += "---\n\n"

    return frontmatter + (doc.get("content") or "")


@router.get("/export/all")
def export_all():
    """导出所有文档为 ZIP 文件，按分类组织文件夹。"""
    conn = get_db()
    rows = conn.execute(
        """SELECT d.*, c.name AS category_name
           FROM documents d
           LEFT JOIN categories c ON d.category_id = c.id
           ORDER BY c.name, d.title"""
    ).fetchall()
    conn.close()

    if not rows:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("知识库为空.txt", "知识库中暂无文档。请先上传文档。")
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=study-hub-export.zip"},
        )

    buf = io.BytesIO()
    used_names = {}  # category -> set of filenames used

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in rows:
            doc = dict(doc)
            cat = doc.get("category_name") or "未分类"
            safe_cat = _safe_filename(cat) or "_未分类"
            safe_title = _safe_filename(doc["title"]) or "untitled"

            # 去重文件名
            if safe_cat not in used_names:
                used_names[safe_cat] = set()
            base_name = safe_title
            counter = 1
            while safe_title + ".md" in used_names[safe_cat]:
                safe_title = f"{base_name}_{counter}"
                counter += 1
            used_names[safe_cat].add(safe_title + ".md")

            path = f"{safe_cat}/{safe_title}.md"
            zf.writestr(path, _doc_to_markdown(doc))

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=study-hub-export.zip"},
    )


@router.get("/export/document/{doc_id}")
def export_document(doc_id: int):
    """导出单个文档为 Markdown 文件。"""
    conn = get_db()
    row = conn.execute(
        """SELECT d.*, c.name AS category_name
           FROM documents d
           LEFT JOIN categories c ON d.category_id = c.id
           WHERE d.id = ?""",
        (doc_id,),
    ).fetchone()
    conn.close()

    if not row:
        return {"error": "文档不存在"}

    doc = dict(row)
    content = _doc_to_markdown(doc)
    safe_title = _safe_filename(doc["title"]) or "untitled"
    encoded_filename = quote(f"{safe_title}.md")

    return Response(
        content=content.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )
