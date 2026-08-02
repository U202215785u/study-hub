"""
内置工具执行器 —— 每个工具有明确的输入/输出定义。

输出分为两类：
- text 型：直接展示在页面上（AI 分析结果等）
- file 型：保存到 workspace 目录，前端提供下载链接（截图、报告等）
"""

import os
import json
import httpx
from datetime import datetime

from .registry import register

WEB_BRIDGE_URL = "http://127.0.0.1:10086/command"


def _sync_ai_chat(messages: list, temperature: float = 0.7, max_tokens: int = 2048) -> str:
    """同步调用 AI —— 直接用 requests 库（避免 httpx 在线程中的 SSL 问题）。"""
    import requests
    from ai_client import get_ai_config

    config = get_ai_config()
    api_base = config["api_base"]
    api_key = config["api_key"]
    model = config["model"]

    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # 重试 3 次
    last_error = None
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=120)
            if resp.status_code != 200:
                return f"AI API 错误 ({resp.status_code}): {resp.text[:300]}"
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.SSLError as e:
            last_error = e
            # SSL 失败后尝试 verify=False
            try:
                resp = requests.post(url, headers=headers, json=body, timeout=120, verify=False)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                return f"AI API 错误 ({resp.status_code}): {resp.text[:300]}"
            except Exception as e2:
                last_error = e2
        except Exception as e:
            last_error = e

    return f"AI 服务不可用（重试3次后失败）: {last_error}"


# ====== Browser 执行器 ======

def _browser_run(input_data: dict, context: dict, workspace: str) -> dict:
    """浏览器操作。

    输入：
        action: navigate | search | screenshot | click | fill
        url:    网页地址（navigate 时必填）
        search: 搜索词（search 时必填）
        click:  CSS 选择器（click 时必填）
        fill:   输入内容（fill 时必填）
        selector: 目标元素选择器

    输出：
        type: screenshot（PNG 文件）| snapshot（页面文字快照）| status（操作状态）
    """
    action = input_data.get("action", "navigate")
    session = input_data.get("session", "workflow")
    outputs = []

    if action == "navigate":
        url = input_data.get("url", "")
        if not url:
            return {"error": "navigate 需要 url 参数"}
        resp = _bridge("navigate", {"url": url, "newTab": True}, session)
        outputs.append({"type": "status", "label": "打开网页", "data": resp})

    elif action == "search":
        query = input_data.get("search", input_data.get("query", ""))
        if not query:
            return {"error": "search 需要 search 参数"}
        search_url = f"https://www.bing.com/search?q={query}"
        resp = _bridge("navigate", {"url": search_url, "newTab": True}, session)
        outputs.append({"type": "status", "label": f"搜索: {query}", "data": resp})

    elif action == "screenshot":
        resp = _bridge("screenshot", {"format": "png", "quality": 80}, session)
        if resp.get("ok") and resp.get("data", {}).get("path"):
            # 截图已由 WebBridge 保存，复制到 workspace
            src_path = resp["data"]["path"]
            dst_name = f"screenshot_{datetime.now().strftime('%H%M%S')}.png"
            dst_path = os.path.join(workspace, dst_name)
            os.makedirs(workspace, exist_ok=True)
            try:
                import shutil
                shutil.copy2(src_path, dst_path)
                outputs.append({
                    "type": "file",
                    "label": "截图",
                    "filename": dst_name,
                    "path": dst_path,
                    "mime": "image/png",
                })
            except Exception as e:
                outputs.append({"error": f"复制截图失败: {e}"})
        else:
            outputs.append({"error": "截图失败", "detail": resp})

    elif action == "click":
        selector = input_data.get("click", input_data.get("selector", ""))
        if not selector:
            return {"error": "click 需要 selector 参数"}
        resp = _bridge("click", {"selector": selector}, session)
        outputs.append({"type": "status", "label": f"点击: {selector}", "data": resp})

    elif action == "fill":
        selector = input_data.get("selector", "")
        value = input_data.get("fill", input_data.get("value", ""))
        if not selector or not value:
            return {"error": "fill 需要 selector 和 fill 参数"}
        resp = _bridge("fill", {"selector": selector, "value": value}, session)
        outputs.append({"type": "status", "label": f"输入: {value[:30]}", "data": resp})

    # 操作后默认截一个页面快照
    if action in ("navigate", "search"):
        import time; time.sleep(1.5)  # 等页面加载
        snap = _bridge("snapshot", {}, session)
        if snap.get("ok"):
            # 保存快照文字
            snap_path = os.path.join(workspace, f"page_snapshot_{datetime.now().strftime('%H%M%S')}.txt")
            os.makedirs(workspace, exist_ok=True)
            try:
                tree_text = json.dumps(snap.get("data", {}).get("tree", ""), ensure_ascii=False)
                with open(snap_path, "w", encoding="utf-8") as f:
                    f.write(tree_text)
                outputs.append({
                    "type": "file",
                    "label": "页面快照",
                    "filename": os.path.basename(snap_path),
                    "path": snap_path,
                    "mime": "text/plain",
                })
            except Exception:
                pass

    return {"outputs": outputs}


def _bridge(action: str, args: dict, session: str = "workflow") -> dict:
    try:
        resp = httpx.post(WEB_BRIDGE_URL, json={"action": action, "args": args, "session": session}, timeout=30)
        return resp.json() if resp.status_code == 200 else {"error": f"WebBridge {resp.status_code}"}
    except Exception as e:
        return {"error": f"WebBridge 不可用: {e}"}


# ====== AI 执行器 ======

def _ai_run(input_data: dict, context: dict, workspace: str) -> dict:
    """AI 分析/生成。

    输入：
        prompt:  提示词（必填）
        context: 上下文引用（可选，从 context 中取之前步骤的输出）
        format:  text | markdown | report（输出格式，默认 text）

    输出：
        text 型：直接展示的分析结果
        file 型（format=report 时）：保存为 Markdown 文件
    """
    prompt = input_data.get("prompt", "")
    if not prompt:
        return {"error": "AI 需要 prompt 参数"}

    # 如果指定了上下文引用，从 context 中读取文件内容拼到 prompt 后面
    context_ref = input_data.get("context", "")
    if context_ref and context_ref in context:
        ref_data = context[context_ref]
        if isinstance(ref_data, dict):
            # 取上一步的文本快照
            for output_item in ref_data.get("outputs", []):
                if output_item.get("type") == "file" and output_item.get("path"):
                    try:
                        with open(output_item["path"], "r", encoding="utf-8") as f:
                            content = f.read()[:5000]
                        prompt += f"\n\n--- 上下文内容 ---\n{content}"
                    except Exception:
                        pass

    output_format = input_data.get("format", "text")

    try:
        content = _sync_ai_chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
        )

        if isinstance(content, str) and content.startswith("AI API 错误"):
            return {"error": content}

        if output_format == "report":
            # 保存为 Markdown 文件
            filename = f"report_{datetime.now().strftime('%H%M%S')}.md"
            filepath = os.path.join(workspace, filename)
            os.makedirs(workspace, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "outputs": [{
                    "type": "file",
                    "label": "分析报告",
                    "filename": filename,
                    "path": filepath,
                    "mime": "text/markdown",
                }, {
                    "type": "text",
                    "label": "分析结果",
                    "text": content[:2000],
                }]
            }
        else:
            return {
                "outputs": [{
                    "type": "text",
                    "label": "AI 回复",
                    "text": content,
                }]
            }
    except Exception as e:
        return {"error": f"AI 调用失败: {e}"}


# ====== API 执行器 ======

def _api_run(input_data: dict, context: dict, workspace: str) -> dict:
    """通用 HTTP 请求。

    输入：
        url:     请求地址（必填）
        method:  GET | POST（默认 GET）
        body:    请求体（POST 时）
        headers: 额外请求头

    输出：
        json 型：结构化的 API 返回数据
        file 型：保存为 JSON 文件
    """
    url = input_data.get("url", "")
    method = input_data.get("method", "GET").upper()
    body = input_data.get("body", None)
    headers = input_data.get("headers", {})

    if not url:
        return {"error": "API 需要 url 参数"}

    try:
        if method == "POST":
            resp = httpx.post(url, json=body, headers=headers, timeout=30)
        else:
            resp = httpx.get(url, headers=headers, timeout=30)

        try:
            data = resp.json()
        except Exception:
            data = {"text": resp.text[:3000]}

        # 同时保存为 JSON 文件
        filename = f"api_response_{datetime.now().strftime('%H%M%S')}.json"
        filepath = os.path.join(workspace, filename)
        os.makedirs(workspace, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {
            "outputs": [{
                "type": "file",
                "label": f"API 响应 ({method} {url[:50]})",
                "filename": filename,
                "path": filepath,
                "mime": "application/json",
            }, {
                "type": "text",
                "label": "响应预览",
                "text": json.dumps(data, ensure_ascii=False, indent=2)[:2000],
            }]
        }
    except Exception as e:
        return {"error": f"HTTP 请求失败: {e}"}


# ====== 自动注册 ======

def setup_builtin_tools():
    register(
        "browser", "浏览器操作：打开网页、搜索、截图、点击、输入",
        inputs={
            "action": {"type": "select", "label": "操作", "required": True,
                       "options": ["navigate", "search", "screenshot", "click", "fill"]},
            "url": {"type": "url", "label": "网页地址", "placeholder": "https://..."},
            "search": {"type": "text", "label": "搜索词", "placeholder": "输入搜索内容"},
            "click": {"type": "text", "label": "点击目标", "placeholder": "CSS 选择器或元素描述"},
            "fill": {"type": "text", "label": "输入内容"},
            "selector": {"type": "text", "label": "目标选择器"},
        },
        outputs={
            "screenshot": {"type": "file", "label": "页面截图", "mime": "image/png"},
            "snapshot": {"type": "file", "label": "页面快照", "mime": "text/plain"},
            "status": {"type": "text", "label": "操作状态"},
        },
        executor=_browser_run,
    )

    register(
        "ai", "AI 分析/生成：总结、分类、翻译、生成报告",
        inputs={
            "prompt": {"type": "textarea", "label": "提示词", "required": True,
                       "placeholder": "告诉 AI 要做什么…"},
            "context": {"type": "ref", "label": "引用上一步输出", "placeholder": "步骤 id"},
            "format": {"type": "select", "label": "输出格式", "options": ["text", "report"]},
        },
        outputs={
            "text": {"type": "text", "label": "分析结果"},
            "report": {"type": "file", "label": "分析报告", "mime": "text/markdown"},
        },
        executor=_ai_run,
    )

    register(
        "api", "HTTP 请求：调用任意 API 接口",
        inputs={
            "url": {"type": "url", "label": "请求地址", "required": True,
                    "placeholder": "https://api.example.com/..."},
            "method": {"type": "select", "label": "请求方式", "options": ["GET", "POST"]},
            "body": {"type": "json", "label": "请求体（JSON）"},
            "headers": {"type": "json", "label": "请求头"},
        },
        outputs={
            "response": {"type": "file", "label": "API 响应", "mime": "application/json"},
            "preview": {"type": "text", "label": "响应预览"},
        },
        executor=_api_run,
    )


setup_builtin_tools()
