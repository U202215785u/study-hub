import uuid

from fastapi import APIRouter, HTTPException

from database import get_db
from endpoints import automation
from services.content_preflight import PreflightInputError, build_preflight


router = APIRouter(prefix="/content-parser", tags=["content-parser"])
_batches: dict[str, dict] = {}
SOURCE_BY_PLATFORM = {
    "douyin": "douyin-summary",
    "bilibili": "bilibili-summary",
    "xiaohongshu": "xiaohongshu-summary",
}


@router.post("/preflight")
def preflight(payload: dict):
    try:
        batch = build_preflight(payload.get("input", ""), payload.get("mode", "auto"))
    except PreflightInputError as exc:
        raise HTTPException(status_code=400, detail={"code": "invalid_input", "message": str(exc)}) from exc
    batch_id = str(uuid.uuid4())
    batch["batch_id"] = batch_id
    _batches[batch_id] = batch
    return batch


@router.post("/confirm")
def confirm(payload: dict):
    batch = _batches.get(payload.get("batch_id", ""))
    item_ids = set(payload.get("item_ids") or [])
    if not batch or not item_ids:
        raise HTTPException(status_code=400, detail={"code": "invalid_items", "message": "请选择检查结果中的可处理项目"})
    groups = {}
    for item in batch["items"]:
        if item["item_id"] in item_ids and item["status"] == "ready":
            groups.setdefault(item["platform"], []).append(item["canonical_url"])
    if not groups:
        raise HTTPException(status_code=409, detail={"code": "item_not_ready", "message": "所选项目当前不能提交"})
    task_ids = []
    for platform, inputs in groups.items():
        result = automation.queue_tasks({"module_id": SOURCE_BY_PLATFORM[platform], "inputs": inputs})
        task_ids.extend(result.get("task_ids", []))
    return {"status": "queued", "task_ids": task_ids}


@router.get("/documents")
def documents(platform: str = "all", state: str = "completed", search: str = ""):
    if platform != "all" and platform not in SOURCE_BY_PLATFORM:
        raise HTTPException(status_code=400, detail={"code": "invalid_platform", "message": "平台筛选无效"})
    if state not in ("completed", "pending", "error"):
        raise HTTPException(status_code=400, detail={"code": "invalid_state", "message": "状态筛选无效"})
    sources = [SOURCE_BY_PLATFORM[platform]] if platform != "all" else list(SOURCE_BY_PLATFORM.values())
    with automation._lock:
        tasks = list(automation._tasks.values())
    parser_tasks = [task for task in tasks if task.get("module_id") in SOURCE_BY_PLATFORM.values()]
    task_state = {"pending": ("pending", "extracting", "summarizing", "importing"), "error": ("error",)}
    counts = {
        "pending": sum(task.get("status") in task_state["pending"] for task in parser_tasks),
        "completed": 0,
        "error": sum(task.get("status") in task_state["error"] for task in parser_tasks),
    }
    if state in task_state:
        selected = [task for task in parser_tasks if task.get("status") in task_state[state]]
        if platform != "all":
            selected = [task for task in selected if task.get("module_id") == SOURCE_BY_PLATFORM[platform]]
        return {"items": [{
            "id": f"task:{task['task_id']}", "task_id": task["task_id"], "title": task.get("title") or task.get("input", "未命名任务"),
            "source": task.get("module_id"), "char_count": 0, "created_at": task.get("created_at", ""),
            "progress": task.get("progress", ""), "error": task.get("error", ""),
        } for task in selected], "counts": counts}
    placeholders = ",".join("?" for _ in sources)
    conditions = [f"source IN ({placeholders})", "content NOT LIKE '%\"_placeholder\"%'"]
    params = list(sources)
    if search.strip():
        conditions.append("(title LIKE ? OR content LIKE ?)")
        term = f"%{search.strip()}%"
        params.extend([term, term])
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, source, char_count, created_at FROM documents WHERE " + " AND ".join(conditions)
        + " ORDER BY created_at DESC LIMIT 200", params,
    ).fetchall()
    count_rows = conn.execute(
        f"SELECT COUNT(*) AS count FROM documents WHERE source IN ({placeholders}) "
        "AND content NOT LIKE '%\"_placeholder\"%'", sources,
    ).fetchone()
    conn.close()
    counts["completed"] = count_rows["count"]
    return {"items": [dict(row) for row in rows], "counts": counts}
