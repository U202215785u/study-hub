"""管理控制台 API —— 给非技术用户看的系统状态和数据管理"""

import os
import glob
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def admin_stats():
    """返回系统核心统计数字"""
    db = get_db()
    stats = {}

    # 数据库统计
    stats["documents"] = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    stats["categories"] = db.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    stats["reviews"] = db.execute("SELECT COUNT(*) FROM daily_reviews").fetchone()[0]
    stats["wiki_pages"] = db.execute("SELECT COUNT(*) FROM wiki_pages").fetchone()[0]
    stats["patches"] = db.execute("SELECT COUNT(*) FROM skill_patches").fetchone()[0]
    stats["snapshots"] = db.execute("SELECT COUNT(*) FROM system_snapshots").fetchone()[0]

    # 数据目录大小
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_size += os.path.getsize(fp)
                file_count += 1
            except Exception:
                pass

    stats["data_size_mb"] = round(total_size / 1024 / 1024, 2)
    stats["data_files"] = file_count

    # 最近活动
    latest_doc = db.execute(
        "SELECT title, created_at FROM documents ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    latest_review = db.execute(
        "SELECT date, created_at FROM daily_reviews ORDER BY created_at DESC LIMIT 1"
    ).fetchone()

    stats["latest_doc"] = dict(latest_doc) if latest_doc else None
    stats["latest_review"] = dict(latest_review) if latest_review else None
    stats["server_time"] = datetime.now().isoformat()

    return stats


@router.get("/logs")
def admin_logs(lines: int = 100):
    """返回后端日志最后 N 行"""
    log_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "studyhub2.log"),
        os.path.join(os.path.dirname(__file__), "..", "..", "studyhub.log"),
        os.path.join(os.path.dirname(__file__), "..", "data", "app.log"),
    ]
    for path in log_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    all_lines = f.readlines()
                return {"source": os.path.basename(path), "lines": all_lines[-lines:]}
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})
    return {"source": None, "lines": [], "note": "未找到日志文件"}


@router.get("/documents/recent")
def recent_documents(limit: int = 20):
    """返回最近上传的文档列表（带预览）"""
    db = get_db()
    rows = db.execute(
        """
        SELECT d.id, d.title, d.content_type, d.source, d.created_at,
               c.name as category_name
        FROM documents d
        LEFT JOIN categories c ON d.category_id = c.id
        ORDER BY d.created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/system/info")
def system_info():
    """返回运行环境信息"""
    import sys
    import platform
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "working_directory": os.getcwd(),
        "data_directory": os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "data")
        ),
        "inbox_directory": os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "data", "inbox")
        ),
    }


# ========== 网页变更监控 (changedetection.io 风格) ==========

import hashlib
import requests

@router.get("/monitored-urls")
def list_monitored_urls():
    """列出所有监控的 URL"""
    db = get_db()
    rows = db.execute(
        "SELECT id, url, title, last_checked, change_detected, change_count, notify_enabled, created_at FROM monitored_urls ORDER BY created_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("/monitored-urls")
def add_monitored_url(payload: dict):
    """添加监控 URL"""
    url = payload.get("url", "").strip()
    title = payload.get("title", "").strip()
    if not url:
        return {"error": "缺少 url 参数"}
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    db = get_db()
    try:
        db.execute(
            "INSERT INTO monitored_urls (url, title) VALUES (?, ?)",
            (url, title),
        )
        db.commit()
        return {"success": True, "url": url}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@router.delete("/monitored-urls/{url_id}")
def delete_monitored_url(url_id: int):
    """删除监控 URL"""
    db = get_db()
    db.execute("DELETE FROM monitored_urls WHERE id = ?", (url_id,))
    db.commit()
    db.close()
    return {"success": True}


@router.post("/monitored-urls/check")
def check_monitored_urls():
    """
    手动触发所有 URL 的变更检查。
    生产环境应在 main.py lifespan 中设置定时任务每 6 小时调用一次。
    """
    db = get_db()
    rows = db.execute(
        "SELECT id, url, last_content_hash FROM monitored_urls WHERE notify_enabled = 1"
    ).fetchall()

    changed = []
    for r in rows:
        url_id = r["id"]
        url = r["url"]
        old_hash = r["last_content_hash"] or ""

        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            if resp.status_code == 200:
                content = resp.text[:50000]  # 限制 50KB
                new_hash = hashlib.sha256(content.encode()).hexdigest()

                if old_hash and old_hash != new_hash:
                    # 检测到变更
                    db.execute(
                        "UPDATE monitored_urls SET last_content_hash = ?, last_content = ?, last_checked = datetime('now'), change_detected = 1, change_count = change_count + 1 WHERE id = ?",
                        (new_hash, content, url_id),
                    )
                    changed.append({"id": url_id, "url": url, "status": "changed"})
                else:
                    db.execute(
                        "UPDATE monitored_urls SET last_content_hash = ?, last_content = ?, last_checked = datetime('now'), change_detected = 0 WHERE id = ?",
                        (new_hash, content, url_id),
                    )
                db.commit()
            else:
                changed.append({"id": url_id, "url": url, "status": f"http_{resp.status_code}"})
        except Exception as e:
            changed.append({"id": url_id, "url": url, "status": "error", "error": str(e)})

    db.close()
    return {"checked": len(rows), "changed": len([c for c in changed if c.get("status") == "changed"]), "details": changed}


@router.get("/monitored-urls/changes")
def get_url_changes():
    """获取有变更的 URL 列表"""
    db = get_db()
    rows = db.execute(
        "SELECT id, url, title, change_count, last_checked FROM monitored_urls WHERE change_detected = 1 ORDER BY last_checked DESC"
    ).fetchall()
    return [dict(r) for r in rows]
