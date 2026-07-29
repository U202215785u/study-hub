import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from database import get_db
from endpoints import automation
from services.douyin_preflight import create_preflight, get_preflight, public_item
from services.douyin_resolver import DouyinResolveError, F2DouyinResolver
from services.secure_settings import (
    delete_secret, load_secret, save_secret, secret_status,
)


router = APIRouter(prefix="/automation/douyin", tags=["douyin"])
resolver = F2DouyinResolver()
COOKIE_NAME = "douyin_cookie"
UPLOAD_DIR = Path(tempfile.gettempdir()) / "StudyHub" / "douyin-uploads"


def _detail(code, message):
    return {"code": code, "message": message}


def enqueue_preflight_item(item):
    task_id = str(uuid.uuid4())[:8]
    task = {
        "task_id": task_id,
        "status": "pending",
        "module_id": "douyin-summary",
        "module_name": automation.MODULES["douyin-summary"]["name"],
        "input": item["canonical_url"] or item["input_url"],
        "progress": "排队中…",
        "created_at": automation.datetime.now().isoformat(),
        "replace_doc_id": item["replace_doc_id"],
        "preflight_item_id": item["item_id"],
    }
    with automation._lock:
        automation._tasks[task_id] = task
    automation._task_to_db(task)
    automation._executor.submit(automation._process_single_task, task_id)
    return task_id


@router.post("/preflight")
async def preflight(payload: dict):
    raw_input = payload.get("input") or ""
    conn = get_db()
    try:
        cookie = load_secret(conn, COOKIE_NAME) or ""
        return await create_preflight(conn, raw_input, resolver, cookie)
    except DouyinResolveError as exc:
        raise HTTPException(status_code=400, detail=_detail(exc.code, str(exc)))
    finally:
        conn.close()


@router.get("/preflight/{batch_id}")
def read_preflight(batch_id: str):
    conn = get_db()
    try:
        result = get_preflight(conn, batch_id)
        if not result:
            raise HTTPException(status_code=404, detail=_detail("batch_not_found", "预检批次不存在"))
        return result
    finally:
        conn.close()


@router.post("/confirm")
def confirm(payload: dict):
    batch_id = payload.get("batch_id") or ""
    item_ids = list(dict.fromkeys(payload.get("item_ids") or []))
    if not batch_id or not item_ids or len(item_ids) > 10:
        raise HTTPException(status_code=400, detail=_detail("invalid_items", "请选择 1 至 10 个项目"))
    conn = get_db()
    try:
        task_ids = []
        for item_id in item_ids:
            item = conn.execute(
                "SELECT * FROM douyin_preflight_items WHERE item_id = ? AND batch_id = ?",
                (item_id, batch_id),
            ).fetchone()
            if not item:
                raise HTTPException(status_code=404, detail=_detail("item_not_found", "预检项目不存在"))
            if item["status"] == "confirmed" and item["task_id"]:
                task_ids.append(item["task_id"])
                continue
            if item["status"] != "ready":
                raise HTTPException(status_code=409, detail=_detail("item_not_ready", "项目尚未达到可处理状态"))
            task_id = enqueue_preflight_item(item)
            conn.execute(
                "UPDATE douyin_preflight_items SET status='confirmed', task_id=?, updated_at=CURRENT_TIMESTAMP WHERE item_id=?",
                (task_id, item_id),
            )
            conn.commit()
            task_ids.append(task_id)
        return {"status": "queued", "task_ids": task_ids}
    finally:
        conn.close()


@router.put("/cookie")
def put_cookie(payload: dict):
    conn = get_db()
    try:
        save_secret(conn, COOKIE_NAME, payload.get("cookie") or "")
        return secret_status(conn, COOKIE_NAME)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=_detail("invalid_cookie", str(exc)))
    finally:
        conn.close()


@router.get("/cookie/status")
def cookie_status():
    conn = get_db()
    try:
        return secret_status(conn, COOKIE_NAME)
    finally:
        conn.close()


@router.delete("/cookie")
def clear_cookie():
    conn = get_db()
    try:
        delete_secret(conn, COOKIE_NAME)
        return secret_status(conn, COOKIE_NAME)
    finally:
        conn.close()


def _valid_video_header(header):
    return (len(header) >= 12 and header[4:8] == b"ftyp") or header.startswith(b"\x1aE\xdf\xa3")


@router.post("/items/{item_id}/local-file")
async def upload_local_file(item_id: str, file: UploadFile = File(...)):
    header = await file.read(16)
    if not _valid_video_header(header):
        raise HTTPException(status_code=400, detail=_detail("invalid_local_file", "文件不是受支持的视频"))
    conn = get_db()
    try:
        item = conn.execute(
            "SELECT * FROM douyin_preflight_items WHERE item_id = ?", (item_id,)
        ).fetchone()
        if not item:
            raise HTTPException(status_code=404, detail=_detail("item_not_found", "预检项目不存在"))
        if item["status"] not in ("needs_local_file", "blocked", "failed", "ready"):
            raise HTTPException(status_code=409, detail=_detail("item_not_uploadable", "当前项目不能上传本地视频"))
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        path = UPLOAD_DIR / f"{uuid.uuid4()}.video"
        size = len(header)
        with path.open("wb") as target:
            target.write(header)
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > 2 * 1024 * 1024 * 1024:
                    target.close()
                    path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail=_detail("local_file_too_large", "视频文件不能超过 2GB"))
                target.write(chunk)
        sources = list(dict.fromkeys(__import__("json").loads(item["content_sources"] or "[]") + ["local_file"]))
        conn.execute(
            """UPDATE douyin_preflight_items SET local_file_path=?, content_sources=?,
               status='ready', error_code='', error_message='', updated_at=CURRENT_TIMESTAMP
               WHERE item_id=?""",
            (str(path), __import__("json").dumps(sources), item_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM douyin_preflight_items WHERE item_id=?", (item_id,)).fetchone()
        return public_item(updated)
    finally:
        conn.close()
