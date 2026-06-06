"""
Workflow API 路由 —— /workflow/

前端通过这组接口触发 workflow、查看进度、暂停/恢复。
支持白话文创建模板 + 模板增删改。
"""

import os
import re
import glob
import shutil
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from workflow.engine import launch, status, pause, resume, list_recent, archive as archive_task
from workflow.loader import load as load_template

router = APIRouter()

WORKFLOW_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "workflows"
)
WORKFLOW_DIR = os.path.abspath(WORKFLOW_DIR)


# ====== 请求模型 ======

class RunRequest(BaseModel):
    yaml_file: str
    params: dict = {}


class ResumeRequest(BaseModel):
    user_input: dict = {}


class CreateFromTextRequest(BaseModel):
    description: str      # 用户的白话文描述
    name: str = ""        # 可选模板名，不填则从描述中提取


class TemplateSaveRequest(BaseModel):
    content: str          # YAML 原始内容


# ====== 路由 ======

@router.post("/workflow/run")
def workflow_run(req: RunRequest):
    """启动一个 workflow。"""
    filename = os.path.basename(req.yaml_file)
    if not filename.endswith((".yml", ".yaml")):
        raise HTTPException(400, "模板文件名需以 .yml 或 .yaml 结尾")

    yaml_path = os.path.join(WORKFLOW_DIR, filename)
    if not os.path.isfile(yaml_path):
        raise HTTPException(404, f"模板不存在: {filename}")

    try:
        task_id = launch(yaml_path, req.params)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"task_id": task_id, "status": "started"}


@router.get("/workflow/status/{task_id}")
def workflow_status(task_id: str):
    """查询单个任务状态。"""
    result = status(task_id)
    if result is None:
        raise HTTPException(404, f"任务不存在: {task_id}")
    return result


@router.post("/workflow/pause/{task_id}")
def workflow_pause(task_id: str):
    """暂停一个运行中的 workflow。"""
    ok = pause(task_id)
    if not ok:
        raise HTTPException(400, "无法暂停（任务不存在或状态不允许）")
    return {"task_id": task_id, "status": "pausing"}


@router.post("/workflow/resume/{task_id}")
def workflow_resume(task_id: str, req: ResumeRequest = None):
    """恢复一个暂停的 workflow。"""
    user_input = req.user_input if req else {}
    ok = resume(task_id, user_input)
    if not ok:
        raise HTTPException(400, "无法恢复（任务不存在或未处于暂停状态）")
    return {"task_id": task_id, "status": "resumed"}


@router.get("/workflow/templates")
def workflow_templates():
    """列出所有可用的 YAML 模板。"""
    os.makedirs(WORKFLOW_DIR, exist_ok=True)

    templates = []
    for pattern in ("*.yml", "*.yaml"):
        for filepath in glob.glob(os.path.join(WORKFLOW_DIR, pattern)):
            filename = os.path.basename(filepath)
            try:
                tmpl = load_template(filepath)
                templates.append({
                    "file": filename,
                    "name": tmpl.name,
                    "desc": tmpl.desc,
                    "version": tmpl.version,
                    "params": [
                        {"name": p.name, "type": p.type, "ask": p.ask}
                        for p in tmpl.params
                    ],
                    "steps_count": len(tmpl.steps),
                    "steps": [
                        {"id": s.id, "type": s.step_type, "label": _step_summary(s)}
                        for s in tmpl.steps
                    ],
                })
            except Exception:
                templates.append({
                    "file": filename,
                    "name": filename,
                    "desc": "(模板解析失败)",
                    "version": "?",
                    "params": [],
                    "steps_count": 0,
                    "steps": [],
                })

    templates.sort(key=lambda t: t["name"])
    return {"templates": templates, "count": len(templates)}


@router.get("/workflow/templates/{filename}")
def workflow_template_get(filename: str):
    """获取单个模板的 YAML 原始内容（用于编辑）。"""
    filename = os.path.basename(filename)
    filepath = os.path.join(WORKFLOW_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(404, f"模板不存在: {filename}")

    with open(filepath, "r", encoding="utf-8") as fh:
        content = fh.read()

    tmpl = load_template(filepath)
    return {
        "file": filename,
        "name": tmpl.name,
        "desc": tmpl.desc,
        "content": content,
        "parsed": {
            "version": tmpl.version,
            "params": [{"name": p.name, "type": p.type, "ask": p.ask} for p in tmpl.params],
            "steps": [{"id": s.id, "type": s.step_type, "config": s.config} for s in tmpl.steps],
        },
    }


@router.put("/workflow/templates/{filename}")
def workflow_template_save(filename: str, req: TemplateSaveRequest):
    """保存/更新 YAML 模板。"""
    filename = os.path.basename(filename)
    if not filename.endswith((".yml", ".yaml")):
        raise HTTPException(400, "模板文件名需以 .yml 或 .yaml 结尾")

    os.makedirs(WORKFLOW_DIR, exist_ok=True)
    filepath = os.path.join(WORKFLOW_DIR, filename)

    # 基本校验：能成功加载才保存
    try:
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(req.content)
        load_template(filepath)  # 校验
    except Exception as e:
        raise HTTPException(400, f"YAML 格式无效: {e}")

    return {"file": filename, "status": "saved"}


@router.delete("/workflow/templates/{filename}")
def workflow_template_delete(filename: str):
    """删除一个 YAML 模板。"""
    filename = os.path.basename(filename)
    filepath = os.path.join(WORKFLOW_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(404, f"模板不存在: {filename}")
    os.remove(filepath)
    return {"file": filename, "status": "deleted"}


@router.post("/workflow/templates/{filename}/copy")
def workflow_template_copy(filename: str):
    """复制一个模板。"""
    filename = os.path.basename(filename)
    src = os.path.join(WORKFLOW_DIR, filename)
    if not os.path.isfile(src):
        raise HTTPException(404, f"模板不存在: {filename}")

    base, ext = os.path.splitext(filename)
    copy_name = f"{base}-副本{ext}"
    dst = os.path.join(WORKFLOW_DIR, copy_name)

    n = 1
    while os.path.exists(dst):
        copy_name = f"{base}-副本{n}{ext}"
        dst = os.path.join(WORKFLOW_DIR, copy_name)
        n += 1

    shutil.copy2(src, dst)
    return {"file": copy_name, "status": "copied"}


@router.post("/workflow/create-from-text")
def workflow_create_from_text(req: CreateFromTextRequest):
    """用大白话描述创建 workflow 模板——AI 自动转译为 YAML。

    示例输入：
      "打开百度搜猫的图片，截图保存，然后AI分析图片里什么品种"

    系统会用 AI 生成合法的 YAML 模板并保存到 workflows/ 目录。
    """
    if not req.description.strip():
        raise HTTPException(400, "请描述你想让工作流做什么")

    os.makedirs(WORKFLOW_DIR, exist_ok=True)

    yaml_content = _generate_yaml(req.description)

    # 从内容中提取 name，生成文件名
    name_match = re.search(r"^name:\s*(.+)", yaml_content, re.MULTILINE)
    raw_name = name_match.group(1).strip().strip("\"'") if name_match else "自定义工作流"
    slug = re.sub(r"[^\w一-鿿\-]", "", raw_name.replace(" ", "-"))[:30]
    filename = f"{slug}.yml" if slug else "custom-workflow.yml"

    filepath = os.path.join(WORKFLOW_DIR, filename)
    n = 1
    while os.path.exists(filepath):
        filename = f"{slug}-{n}.yml"
        filepath = os.path.join(WORKFLOW_DIR, filename)
        n += 1

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write(yaml_content)

    # 校验
    try:
        tmpl = load_template(filepath)
    except Exception as e:
        os.remove(filepath)
        raise HTTPException(400, f"AI 生成的 YAML 格式有误: {e}\n\n生成内容：\n{yaml_content[:500]}")

    return {
        "file": filename,
        "name": tmpl.name,
        "desc": tmpl.desc,
        "steps_count": len(tmpl.steps),
        "content": yaml_content,
    }


@router.get("/workflow/queue/status")
def workflow_queue_status(show_archived: bool = False):
    """获取所有 workflow 任务状态（最近 20 个）。"""
    tasks = list_recent(20, include_archived=show_archived)
    archived_tasks = list_recent(100, include_archived=True)
    archived_tasks = [t for t in archived_tasks if t.get("archived")]
    stats = {
        "total": len(tasks),
        "pending": sum(1 for t in tasks if t["status"] == "pending"),
        "running": sum(1 for t in tasks if t["status"] == "running"),
        "paused": sum(1 for t in tasks if t["status"] == "paused"),
        "done": sum(1 for t in tasks if t["status"] == "done"),
        "error": sum(1 for t in tasks if t["status"] == "error"),
        "archived": len(archived_tasks),
        "max_workers": 3,
    }
    return {"stats": stats, "tasks": tasks, "archived": archived_tasks[:50]}


@router.post("/workflow/archive/{task_id}")
def workflow_archive(task_id: str):
    """切换任务的归档状态。"""
    ok = archive_task(task_id)
    if not ok:
        raise HTTPException(404, f"任务不存在: {task_id}")
    return {"task_id": task_id, "status": "toggled"}


@router.get("/workflow/tools")
def workflow_tools():
    """列出所有已注册的工具。"""
    from workflow.registry import list_tools
    return {"tools": list_tools()}


@router.get("/workflow/output/{task_id}/{filename}")
def workflow_download(task_id: str, filename: str):
    """下载 workflow 输出文件（截图、报告等）。"""
    from fastapi.responses import FileResponse
    from workflow.engine import get_output_path

    path = get_output_path(task_id, filename)
    if not path:
        raise HTTPException(404, f"文件不存在: {filename}")
    return FileResponse(path, filename=filename)


# ====== AI 转译 ======

YAML_SCHEMA_PROMPT = """你是一个工作流模板生成器。用户描述一个流程，你输出合法的 YAML。

## YAML 格式（重要！每个步骤必须有 input 和 output 定义）

```yaml
name: 流程名称（简短中文）
desc: 流程描述（一句话）
version: "1.0"

params:
  - name: keyword
    type: string
    ask: "需要用户提供什么？"

steps:
  - id: step_1
    type: tool
    tool: browser
    input:
      action: search
      search: "{{.params.keyword}}"
    output:
      label: "搜索结果"

  - id: step_2
    type: tool
    tool: ai
    input:
      prompt: "分析上面的内容，总结要点"
      format: report
    output:
      label: "分析报告"
```

## 三种步骤类型

| type | 说明 |
|------|------|
| tool | 自动调用工具，必须有 tool + input + output |
| ask | 暂停等用户输入，用 ask 字段写问题 |
| human | 暂停等用户手动操作，用 human 字段写说明 |

## 可用工具及 input 字段

### browser（浏览器操作）
- action: navigate | search | screenshot | click | fill
- url: 网页地址（navigate 时）
- search: 搜索词（search 时）
- output.label: 描述产出（如 "搜索结果截图"）

### ai（AI 分析）
- prompt: 提示词（告诉 AI 分析什么）
- format: text | report（report 会保存为可下载的 Markdown 文件）
- output.label: 描述产出（如 "配色分析报告"）

### api（HTTP 请求）
- url: 请求地址
- method: GET | POST
- output.label: 描述产出

## 规则
1. 只输出 YAML，不要解释，不要 ``` 包裹
2. name 用中文，10 字以内
3. 每个 tool 步骤必须有 input 和 output 块
4. output.label 是给人看的产出描述（如"配色分析报告"、"页面截图"）
5. AI 分析类步骤 format 用 report（用户可下载）
6. 变量引用用 {{.步骤id.字段}} 语法"""



def _generate_yaml(description: str) -> str:
    """调 AI 把用户描述转成 YAML——复用项目已有的 ai_client。"""
    from workflow.executors import _sync_ai_chat

    try:
        content = _sync_ai_chat(
            messages=[
                {"role": "system", "content": YAML_SCHEMA_PROMPT},
                {"role": "user", "content": f"创建这个工作流：{description}"},
            ],
            temperature=0.7,
            max_tokens=2048,
        )

        if isinstance(content, str) and content.startswith("AI API 错误"):
            raise HTTPException(500, f"AI 调用失败: {content}")

        content = content.strip()

        # 清理可能包裹的 ```yaml ```
        content = re.sub(r"^```ya?ml\s*\n?", "", content)
        content = re.sub(r"\n?```\s*$", "", content)

        if not content.startswith("name:"):
            raise HTTPException(500, f"AI 生成格式异常，未以 name: 开头:\n{content[:300]}")

        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"AI 生成失败: {e}")


def _step_summary(step) -> str:
    """给模板列表用的步骤摘要。"""
    from workflow.loader import StepDef
    if isinstance(step, StepDef):
        # 优先用 output label
        label = step.output_spec.get("label", "") if step.output_spec else ""
        if label:
            return f"📤 {label}"

        if step.step_type == "tool":
            tool = step.tool or step.config.get("tool", "?")
            action = step.input_spec.get("action", step.input_spec.get("search", "")) if step.input_spec else ""
            if not action:
                action = step.config.get("action", "")[:20]
            return f"🔧 {tool}: {action}" if action else f"🔧 {tool}"
        if step.step_type == "ask":
            return f"💬 {step.config.get('ask', '确认')[:20]}"
        if step.step_type == "human":
            return f"👤 {step.config.get('human', '手动操作')[:20]}"
    return str(step)
