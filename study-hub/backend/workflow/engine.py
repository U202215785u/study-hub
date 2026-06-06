"""
Workflow 执行引擎 —— 状态机驱动的步骤调度器。

每次运行有独立的 workspace 目录，工具产出的文件存这里。
状态流转：pending → running → done / error / paused
"""

import os
import uuid
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from .loader import WorkflowTemplate, StepDef, load, resolve_in
from .registry import execute as execute_tool

# ====== 任务队列 ======

MAX_WORKERS = 3
_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
_tasks: dict[str, dict] = {}
_lock = threading.Lock()

RUNS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "workflow-runs")
RUNS_DIR = os.path.abspath(RUNS_DIR)


# ====== 公开 API ======

def launch(yaml_path: str, params: dict | None = None) -> str:
    """启动一个 workflow，返回 task_id。"""
    template = load(yaml_path)
    task_id = str(uuid.uuid4())[:8]

    # 创建本次运行的 workspace
    workspace = os.path.join(RUNS_DIR, task_id)
    os.makedirs(workspace, exist_ok=True)

    steps_meta = [
        {"key": s.id, "label": _step_label(s), "status": "pending"}
        for s in template.steps
    ]

    with _lock:
        _tasks[task_id] = {
            "task_id": task_id,
            "type": "workflow",
            "status": "pending",
            "template_name": template.name,
            "template_path": yaml_path,
            "params": params or {},
            "workspace": workspace,
            "context": {"params": params or {}},
            "steps": steps_meta,
            "current_step": None,
            "current_step_index": -1,
            "progress": "排队中…",
            "error": "",
            "result": None,
            "outputs": [],       # 所有步骤的产出汇总
            "created_at": datetime.now().isoformat(),
        }

    _executor.submit(_run, template, task_id, params or {})
    return task_id


def status(task_id: str) -> dict | None:
    """查询任务状态。"""
    with _lock:
        task = _tasks.get(task_id)
    if not task:
        return None

    return {
        "task_id": task["task_id"],
        "status": task["status"],
        "template_name": task["template_name"],
        "progress": task.get("progress", ""),
        "current_step": task.get("current_step"),
        "steps": task.get("steps", []),
        "error": task.get("error", ""),
        "result": task.get("result"),
        "outputs": task.get("outputs", []),
        "workspace": task.get("workspace", ""),
        "created_at": task.get("created_at", ""),
        "archived": task.get("archived", False),
        "_pause_reason": task.get("_pause_reason"),
    }


def pause(task_id: str) -> bool:
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return False
        if task["status"] in ("pending", "running"):
            task["_pause_requested"] = True
            return True
    return False


def resume(task_id: str, user_input: dict | None = None) -> bool:
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return False
        if task["status"] != "paused":
            return False
        if user_input:
            task["context"]["_user_input"] = user_input
        task["status"] = "running"
        task["progress"] = "恢复执行…"
        task["_resume_signal"] = True

    template = load(task["template_path"])
    _executor.submit(_run, template, task_id, task["params"], resume_from=task["current_step_index"])
    return True


def list_recent(limit: int = 20, include_archived: bool = False) -> list[dict]:
    with _lock:
        all_tasks = _tasks.values()
        if not include_archived:
            all_tasks = [t for t in all_tasks if not t.get("archived")]
        all_tasks = sorted(all_tasks, key=lambda t: t.get("created_at", ""), reverse=True)[:limit]
    return [status(t["task_id"]) for t in all_tasks]


def archive(task_id: str) -> bool:
    """切换归档状态。"""
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return False
        task["archived"] = not task.get("archived")
        return True


def get_output_path(task_id: str, filename: str) -> str | None:
    """获取输出文件的完整路径（供下载）。"""
    with _lock:
        task = _tasks.get(task_id)
    if not task:
        return None
    filepath = os.path.join(task["workspace"], os.path.basename(filename))
    if os.path.isfile(filepath):
        return filepath
    return None


# ====== 内部执行逻辑 ======

def _run(template: WorkflowTemplate, task_id: str, params: dict, resume_from: int = -1):
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return
        task["status"] = "running"
        task["progress"] = "开始执行…"

    workspace = task["workspace"]
    context = {"params": params}
    start_index = resume_from + 1 if resume_from >= 0 else 0

    try:
        for idx in range(start_index, len(template.steps)):
            step = template.steps[idx]

            with _lock:
                if task.get("_pause_requested"):
                    task["_pause_requested"] = False
                    task["status"] = "paused"
                    task["progress"] = f"已暂停（步骤: {step.id}）"
                    task["current_step"] = step.id
                    task["current_step_index"] = idx
                    return

            _update_step(task_id, step, "running")
            _update_progress(task_id, f"执行中: {_step_label(step)}")

            # 解析模板变量
            resolved_input = resolve_in(step.input_spec, context) if step.input_spec else {}
            resolved_config = resolve_in(step.config, context)

            # before gate
            for gate in step.gates:
                if gate.position == "before":
                    gate_result = _execute_gate(gate, resolved_config, context, task_id)
                    if gate_result.get("action") == "pause":
                        _do_pause(task_id, step, idx, gate_result)
                        return
                    if gate_result.get("action") == "reject":
                        raise RuntimeError(f"步骤 [{step.id}] before gate 未通过: {gate_result.get('reason')}")

            # 主步骤
            step_result = _execute_step(step, resolved_input, resolved_config, context, workspace, task_id)

            if step_result:
                context[step.id] = step_result
                # 收集文件产出
                outputs = step_result.get("outputs", [])
                with _lock:
                    task["context"] = dict(context)
                    for o in outputs:
                        o["_step_id"] = step.id
                        task["outputs"].append(o)

            # after gate
            for gate in step.gates:
                if gate.position == "after":
                    gate_result = _execute_gate(gate, {**resolved_config, "result": step_result}, context, task_id)
                    if gate_result.get("action") == "pause":
                        _do_pause(task_id, step, idx, gate_result)
                        return
                    if gate_result.get("action") == "retry":
                        _update_progress(task_id, f"重试: {_step_label(step)}")
                        idx -= 1
                        continue
                    if gate_result.get("action") == "reject":
                        raise RuntimeError(f"步骤 [{step.id}] after gate 未通过: {gate_result.get('reason')}")

            _update_step(task_id, step, "done")

        # 完成
        with _lock:
            task["status"] = "done"
            task["progress"] = "完成"
            task["result"] = context

    except Exception as exc:
        with _lock:
            task["status"] = "error"
            task["error"] = str(exc)
            task["progress"] = "失败"


def _execute_step(step: StepDef, input_data: dict, config: dict, context: dict, workspace: str, task_id: str) -> dict | None:
    """执行单个步骤。"""
    if step.step_type == "tool":
        tool_name = step.tool or config.get("tool", "")
        if not tool_name:
            raise ValueError(f"步骤 [{step.id}] 未指定 tool")

        # 兼容旧格式：没有 input_spec 时从 config/action 构造
        merged_input = dict(input_data)
        if not merged_input and config:
            # 旧格式：action + tool 字段
            action = config.get("action", "")
            if tool_name == "browser":
                if "搜索" in action:
                    merged_input["action"] = "search"
                    merged_input["search"] = action.replace("搜索", "").strip().strip("「」""''")
                elif "截图" in action or "截屏" in action:
                    merged_input["action"] = "screenshot"
                elif "打开" in action:
                    merged_input["action"] = "navigate"
                    import re
                    urls = re.findall(r"https?://[^\s]+", action)
                    merged_input["url"] = urls[0] if urls else ""
                else:
                    merged_input["action"] = "navigate"
                    merged_input["url"] = action
            elif tool_name == "ai":
                merged_input["prompt"] = action
                merged_input["format"] = "text"
            else:
                merged_input["url"] = config.get("url", config.get("endpoint", ""))

        return execute_tool(tool_name, merged_input, context, workspace)

    elif step.step_type == "ask":
        _do_pause(task_id, step, step.index, {
            "type": "ask",
            "prompt": config.get("ask", config.get("prompt", input_data.get("ask", "请确认"))),
        })
        return None

    elif step.step_type == "human":
        _do_pause(task_id, step, step.index, {
            "type": "human",
            "prompt": config.get("human", config.get("prompt", input_data.get("human", "请完成操作后继续"))),
        })
        return None


def _execute_gate(gate, config: dict, context: dict, task_id: str) -> dict:
    gate_config = gate.config
    if "ask" in gate_config:
        return {"action": "pause", "type": "ask", "prompt": resolve_in(gate_config["ask"], context)}
    if "check" in gate_config:
        return {"action": "pass"}
    return {"action": "pass"}


def _do_pause(task_id: str, step: StepDef, step_index: int, reason: dict):
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return
        task["status"] = "paused"
        task["current_step"] = step.id
        task["current_step_index"] = step_index
        task["progress"] = reason.get("prompt", f"等待操作: {step.id}")
        task["_pause_reason"] = reason


def _update_step(task_id: str, step: StepDef, status: str):
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return
        task["current_step"] = step.id
        for s in task.get("steps", []):
            if s["key"] == step.id:
                s["status"] = status


def _update_progress(task_id: str, message: str):
    with _lock:
        task = _tasks.get(task_id)
        if task:
            task["progress"] = message


def _step_label(step: StepDef) -> str:
    """人类可读的步骤标签。优先用 output label，其次 input action。"""
    output_label = step.output_spec.get("label", "") if step.output_spec else ""
    if output_label:
        return output_label

    if step.step_type == "tool":
        tool = step.tool or step.config.get("tool", "?")
        action = step.input_spec.get("action", step.input_spec.get("search", "")) if step.input_spec else ""
        if not action:
            action = step.config.get("action", "")[:30]
        return f"[{tool}] {action}" if action else f"[{tool}]"
    if step.step_type == "ask":
        return step.config.get("ask", "确认")[:40]
    if step.step_type == "human":
        return step.config.get("human", "手动操作")[:40]
    return step.id
