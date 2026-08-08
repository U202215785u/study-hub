import json
from fastapi import APIRouter
from database import get_db

router = APIRouter()


def _categories(conn):
    return [dict(row) for row in conn.execute("SELECT id, name, sort_order, is_system FROM ddl_categories ORDER BY sort_order, id").fetchall()]


@router.get("/ddl/categories")
def list_categories():
    conn = get_db()
    try:
        return _categories(conn)
    finally:
        conn.close()


@router.post("/ddl/categories")
def create_category(payload: dict):
    name = (payload.get("name") or "").strip()
    if not name:
        return {"error": "分类名称不能为空"}
    conn = get_db()
    try:
        order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM ddl_categories").fetchone()[0]
        cursor = conn.execute("INSERT INTO ddl_categories (name, sort_order) VALUES (?, ?)", (name, order))
        conn.commit()
        return dict(conn.execute("SELECT id, name, sort_order, is_system FROM ddl_categories WHERE id = ?", (cursor.lastrowid,)).fetchone())
    except Exception:
        return {"error": "分类名称已存在"}
    finally:
        conn.close()


@router.put("/ddl/categories/reorder")
def reorder_categories(payload: dict):
    ids = payload.get("category_ids") or []
    conn = get_db()
    try:
        if not ids or len(set(ids)) != len(ids) or len(ids) != conn.execute("SELECT COUNT(*) FROM ddl_categories WHERE id IN ({})".format(",".join("?" for _ in ids)), ids).fetchone()[0]:
            return {"error": "分类列表无效"}
        for order, category_id in enumerate(ids):
            conn.execute("UPDATE ddl_categories SET sort_order = ? WHERE id = ?", (order, category_id))
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


@router.put("/ddl/categories/{category_id}")
def update_category(category_id: int, payload: dict):
    name = (payload.get("name") or "").strip()
    conn = get_db()
    try:
        row = conn.execute("SELECT is_system FROM ddl_categories WHERE id = ?", (category_id,)).fetchone()
        if not row or row["is_system"] or not name:
            return {"error": "该分类不能重命名"}
        conn.execute("UPDATE ddl_categories SET name = ? WHERE id = ?", (name, category_id))
        conn.commit()
        return {"status": "ok", "id": category_id}
    except Exception:
        return {"error": "分类名称已存在"}
    finally:
        conn.close()


@router.delete("/ddl/categories/{category_id}")
def delete_category(category_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT is_system FROM ddl_categories WHERE id = ?", (category_id,)).fetchone()
        fallback = conn.execute("SELECT id FROM ddl_categories WHERE is_system = 1 LIMIT 1").fetchone()
        if not row or row["is_system"]:
            return {"error": "该分类不能删除"}
        conn.execute("UPDATE ddl_tasks SET category_id = ? WHERE category_id = ?", (fallback["id"], category_id))
        conn.execute("DELETE FROM ddl_categories WHERE id = ?", (category_id,))
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


@router.get("/ddl/tasks")
def list_tasks(status: str = "", task_type: str = "", project_id: int = 0, plan_date: str = "", plan_type: str = "", category_id: int = 0):
    """列出 DDL 任务，支持按状态、类型、项目、计划日期筛选"""
    conn = get_db()
    sql = "SELECT * FROM ddl_tasks WHERE 1=1"
    params = []

    if status:
        sql += " AND status = ?"
        params.append(status)
    if task_type:
        sql += " AND task_type = ?"
        params.append(task_type)
    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)
    if plan_date:
        sql += " AND plan_date = ?"
        params.append(plan_date)
    if plan_type:
        sql += " AND plan_type = ?"
        params.append(plan_type)
    if category_id:
        sql += " AND category_id = ?"
        params.append(category_id)

    sql += " ORDER BY sort_order, plan_date, start_time, due_date, created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    tasks = [dict(r) for r in rows]
    # 确保 sort_order 和 project_id 是整数
    for t in tasks:
        t["sort_order"] = t.get("sort_order", 0) or 0
        t["project_id"] = t.get("project_id") or None
        # 计算剩余天数
        if t.get("due_date"):
            from datetime import date
            try:
                due = date.fromisoformat(t["due_date"])
                delta = (due - date.today()).days
                t["days_left"] = delta
            except (ValueError, TypeError):
                t["days_left"] = None
        else:
            t["days_left"] = None
    return tasks


@router.post("/ddl/tasks")
def create_task(payload: dict):
    """创建 DDL 任务"""
    title = (payload.get("title") or "").strip()
    if not title:
        return {"error": "任务标题不能为空"}

    description = payload.get("description", "")
    due_date = payload.get("due_date") or None
    task_type = payload.get("task_type", "todo")
    category_id = payload.get("category_id")
    project_id = payload.get("project_id") or None
    status = payload.get("status", "todo")
    plan_type = payload.get("plan_type", "todo")
    plan_date = payload.get("plan_date") or None
    start_time = payload.get("start_time") or None
    end_time = payload.get("end_time") or None

    # 获取最大 sort_order
    conn = get_db()
    if category_id is None:
        category_id = conn.execute("SELECT id FROM ddl_categories WHERE name = ?", ({"todo": "待办", "learning": "学习任务", "milestone": "里程碑"}.get(task_type, "未分类"),)).fetchone()[0]
    elif not conn.execute("SELECT 1 FROM ddl_categories WHERE id = ?", (category_id,)).fetchone():
        conn.close()
        return {"error": "任务分类不存在"}
    max_sort = conn.execute("SELECT COALESCE(MAX(sort_order), -1) FROM ddl_tasks").fetchone()[0]

    try:
        cur = conn.execute(
            """INSERT INTO ddl_tasks (title, description, due_date, task_type, category_id, project_id, status, sort_order, plan_type, plan_date, start_time, end_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, description, due_date, task_type, category_id, project_id, status, max_sort + 1, plan_type, plan_date, start_time, end_time),
        )
        conn.commit()
        task_id = cur.lastrowid
        row = conn.execute("SELECT * FROM ddl_tasks WHERE id = ?", (task_id,)).fetchone()
        result = dict(row) if row else {"id": task_id, "title": title}
        result["sort_order"] = result.get("sort_order", 0) or 0
        result["project_id"] = result.get("project_id") or None
        # 计算剩余天数
        if result.get("due_date"):
            from datetime import date
            try:
                due = date.fromisoformat(result["due_date"])
                result["days_left"] = (due - date.today()).days
            except (ValueError, TypeError):
                result["days_left"] = None
        else:
            result["days_left"] = None
        return result
    except Exception as e:
        return {"error": f"创建失败: {e}"}
    finally:
        conn.close()


@router.put("/ddl/tasks/{task_id}")
def update_task(task_id: int, payload: dict):
    """更新 DDL 任务"""
    conn = get_db()
    existing = conn.execute("SELECT * FROM ddl_tasks WHERE id = ?", (task_id,)).fetchone()
    if not existing:
        conn.close()
        return {"error": "任务不存在"}
    existing = dict(existing)

    title = payload.get("title", existing["title"])
    description = payload.get("description", existing["description"])
    due_date = payload.get("due_date", existing["due_date"])
    task_type = payload.get("task_type", existing["task_type"])
    category_id = payload.get("category_id", existing.get("category_id"))
    project_id = payload.get("project_id", existing["project_id"])
    status = payload.get("status", existing["status"])
    sort_order = payload.get("sort_order", existing["sort_order"])
    plan_type = payload.get("plan_type", existing.get("plan_type", "todo"))
    plan_date = payload.get("plan_date", existing.get("plan_date"))
    start_time = payload.get("start_time", existing.get("start_time"))
    end_time = payload.get("end_time", existing.get("end_time"))
    if category_id is not None and not conn.execute("SELECT 1 FROM ddl_categories WHERE id = ?", (category_id,)).fetchone():
        conn.close()
        return {"error": "任务分类不存在"}

    conn.execute(
        """UPDATE ddl_tasks
           SET title = ?, description = ?, due_date = ?, task_type = ?, category_id = ?,
               project_id = ?, status = ?, sort_order = ?, plan_type = ?, plan_date = ?, start_time = ?, end_time = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (title, description, due_date, task_type, category_id, project_id, status, sort_order, plan_type, plan_date, start_time, end_time, task_id),
    )
    conn.commit()
    conn.close()
    return {"id": task_id, "status": "ok"}


@router.delete("/ddl/tasks/{task_id}")
def delete_task(task_id: int):
    """删除 DDL 任务"""
    conn = get_db()
    existing = conn.execute("SELECT * FROM ddl_tasks WHERE id = ?", (task_id,)).fetchone()
    if not existing:
        conn.close()
        return {"error": "任务不存在"}

    conn.execute("DELETE FROM ddl_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.put("/ddl/tasks/reorder")
def reorder_tasks(payload: dict):
    """批量更新排序 (拖拽后的顺序)"""
    task_ids = payload.get("task_ids", [])
    if not task_ids:
        return {"error": "task_ids 不能为空"}

    conn = get_db()
    for i, tid in enumerate(task_ids):
        conn.execute("UPDATE ddl_tasks SET sort_order = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (i, tid))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.get("/ddl/stats")
def ddl_stats():
    """DDL 统计信息"""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM ddl_tasks").fetchone()[0]
    todo = conn.execute("SELECT COUNT(*) FROM ddl_tasks WHERE status = 'todo'").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM ddl_tasks WHERE status = 'in_progress'").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM ddl_tasks WHERE status = 'done'").fetchone()[0]

    # 即将到期 (3天内) 且未完成的任务数
    from datetime import date, timedelta
    today = date.today().isoformat()
    deadline = (date.today() + timedelta(days=3)).isoformat()
    urgent = conn.execute(
        "SELECT COUNT(*) FROM ddl_tasks WHERE due_date IS NOT NULL AND due_date <= ? AND status != 'done'",
        (deadline,)
    ).fetchone()[0]

    # 已超期的任务数
    overdue = conn.execute(
        "SELECT COUNT(*) FROM ddl_tasks WHERE due_date IS NOT NULL AND due_date < ? AND status != 'done'",
        (today,)
    ).fetchone()[0]

    conn.close()
    return {
        "total": total,
        "todo": todo,
        "in_progress": in_progress,
        "done": done,
        "urgent": urgent,
        "overdue": overdue,
    }
