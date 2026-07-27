"""OS 能力网关 — 统一入口

接收自然语言意图，路由到具体执行器：
  - shell → shell_executor
  - fs    → fs_operator
  - browser → browser_controller
  - skill → skill_registry

同时记录审计日志到 ACTION_LOG.md
"""
import json
import time
import re
from dataclasses import asdict
from pathlib import Path

from gateway_paths import ROOT
from . import shell_executor
from . import fs_operator
from . import browser_controller
from . import skill_registry


ACTION_LOG = ROOT / "ACTION_LOG.md"


def _append_action_log(entry: dict):
    """追加操作到 ACTION_LOG。"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"\n## OS 操作 | {timestamp}",
        f"- 动作: {entry.get('action', 'unknown')}",
        f"- 目标: {entry.get('target', '')}",
        f"- 结果: {'成功' if entry.get('success') else '失败'}",
    ]
    if entry.get('error'):
        lines.append(f"- 错误: {entry['error']}")
    if entry.get('risk_level'):
        lines.append(f"- 风险等级: {entry['risk_level']}")
    if entry.get('confirmed') is not None:
        lines.append(f"- 用户确认: {'是' if entry['confirmed'] else '否'}")
    lines.append("")

    try:
        with open(ACTION_LOG, "a", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception:
        pass


def execute(
    action: str,
    params: dict,
    *,
    user_confirmed: bool = False,
) -> dict:
    """
    统一执行入口。

    action 类型:
      shell.execute    — 执行 Shell 命令
      fs.read          — 读文件
      fs.write         — 写文件
      fs.list          — 列出目录
      fs.search        — 搜索内容
      fs.delete        — 删除文件/目录
      browser.navigate — 导航到 URL
      browser.extract  — 提取网页内容
      browser.screenshot — 网页截图
      skill.execute    — 执行技能
      skill.list       — 列出技能
    """
    result = {"success": False, "action": action, "error": "未知动作"}

    # ── Shell ───────────────────────────────────────────────
    if action == "shell.execute":
        cmd = params.get("command", "")
        cwd = params.get("cwd", "")
        timeout = params.get("timeout", 30)
        r = shell_executor.execute(
            cmd, cwd=cwd, timeout=timeout,
            user_confirmed=user_confirmed,
            bypass_safety=params.get("bypass_safety", False),
        )
        result = {
            "success": r.exit_code == 0,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "exit_code": r.exit_code,
            "duration_ms": r.duration_ms,
            "risk_level": r.risk_level,
            "confirmed": r.confirmed,
        }
        _append_action_log({
            "action": "shell.execute",
            "target": cmd,
            "success": r.exit_code == 0,
            "error": r.stderr if r.exit_code != 0 else "",
            "risk_level": r.risk_level,
            "confirmed": r.confirmed,
        })

    # ── File System ─────────────────────────────────────────
    elif action == "fs.read":
        r = fs_operator.read_file(params.get("path", ""), max_bytes=params.get("max_bytes", 500_000))
        result = {"success": r.success, "content": r.content, "error": r.error, "risk_level": r.risk_level}
        _append_action_log({"action": "fs.read", "target": params.get("path"), **result})

    elif action == "fs.write":
        r = fs_operator.write_file(
            params.get("path", ""),
            params.get("content", ""),
            user_confirmed=user_confirmed,
            append=params.get("append", False),
        )
        result = {"success": r.success, "error": r.error, "risk_level": r.risk_level}
        _append_action_log({"action": "fs.write", "target": params.get("path"), **result})

    elif action == "fs.list":
        r = fs_operator.list_directory(params.get("path", "."))
        result = {"success": r.success, "content": r.content, "error": r.error, "risk_level": r.risk_level}
        _append_action_log({"action": "fs.list", "target": params.get("path", "."), **result})

    elif action == "fs.search":
        r = fs_operator.search_in_files(
            params.get("pattern", ""),
            params.get("path", "."),
            params.get("glob", "*"),
        )
        result = {"success": r.success, "content": r.content, "error": r.error, "risk_level": r.risk_level}
        _append_action_log({"action": "fs.search", "target": params.get("path", "."), **result})

    elif action == "fs.delete":
        r = fs_operator.delete_path(params.get("path", ""), user_confirmed=user_confirmed)
        result = {"success": r.success, "error": r.error, "risk_level": r.risk_level}
        _append_action_log({"action": "fs.delete", "target": params.get("path"), **result})

    # ── Browser ─────────────────────────────────────────────
    elif action == "browser.navigate":
        r = browser_controller.navigate(params.get("url", ""), user_confirmed=user_confirmed)
        result = {"success": r.success, "content": r.content, "error": r.error, "risk_level": r.risk_level}
        _append_action_log({"action": "browser.navigate", "target": params.get("url"), **result})

    elif action == "browser.extract":
        r = browser_controller.extract(params.get("url", ""), params.get("selector", ""))
        result = {"success": r.success, "content": r.content, "error": r.error, "risk_level": r.risk_level}
        _append_action_log({"action": "browser.extract", "target": params.get("url"), **result})

    elif action == "browser.screenshot":
        r = browser_controller.screenshot(params.get("url", ""), user_confirmed=user_confirmed)
        result = {"success": r.success, "content": r.content, "error": r.error, "risk_level": r.risk_level}
        _append_action_log({"action": "browser.screenshot", "target": params.get("url"), **result})

    # ── Skills ──────────────────────────────────────────────
    elif action == "skill.list":
        skills = skill_registry.list_skills()
        result = {"success": True, "skills": skills}

    elif action == "skill.execute":
        skill_name = params.get("name", "")
        skill_args = params.get("args", {})
        skills = skill_registry.discover_skills()
        skill = next((s for s in skills if s.name == skill_name), None)
        if skill is None:
            result = {"success": False, "error": f"技能 '{skill_name}' 未找到"}
        else:
            r = skill_registry.execute_skill(skill, skill_args, user_confirmed=user_confirmed)
            result = r
            _append_action_log({"action": "skill.execute", "target": skill_name, **result})

    return result


def detect_intent(text: str) -> str | None:
    """
    简单意图检测：从自然语言中提取可能的 OS 操作意图。
    返回 action 字符串或 None。
    """
    text_lower = text.lower()

    # Shell 意图
    shell_patterns = [
        r"运行\s*命令",
        r"执行\s*shell",
        r"执行\s*命令",
        r"跑一下\s*",
        r"运行\s*脚本",
        r"执行\s*脚本",
    ]
    for p in shell_patterns:
        if re.search(p, text_lower):
            return "shell.execute"

    # 文件读取（包含直接读某个文件路径的情况）
    if re.search(r"读(取|一下|一下这个)?\s*文件|看(一下)?\s*文件|打开\s*文件|cat\s|读\s+\S+\.(md|txt|py|js|json|csv|yaml|yml|html|css)", text_lower):
        return "fs.read"

    # 文件写入
    if re.search(r"写(入)?\s*文件|创建\s*文件|新建\s*文件|保存\s*到|写入\s+\S+\.(md|txt|py|js|json)", text_lower):
        return "fs.write"

    # 列出目录
    if re.search(r"列出\s*目录|看(一下)?\s*文件夹|ls\s|dir\s|有(什么|哪些)\s*文件", text_lower):
        return "fs.list"

    # 搜索
    if re.search(r"搜索\s*文件|查找\s*内容|grep\s|找(一下)?\s*文件", text_lower):
        return "fs.search"

    # 删除
    if re.search(r"删除\s*文件|删掉|移除\s*文件|rm\s", text_lower):
        return "fs.delete"

    # 浏览器
    if re.search(r"打开\s*(网页|网站|url)|浏览\s|访问\s|navigate\s|goto\s|打开\s+https?://", text_lower):
        return "browser.navigate"
    if re.search(r"截图\s*网页|screenshot\s|截(个)?图", text_lower):
        return "browser.screenshot"
    if re.search(r"提取\s*网页|抓取\s*(网页|内容)|scrape\s", text_lower):
        return "browser.extract"

    # 技能
    if re.search(r"执行\s*技能|运行\s*skill|skill\s*execute", text_lower):
        return "skill.execute"
    if re.search(r"列出\s*技能|有什么\s*技能|list\s*skill", text_lower):
        return "skill.list"

    return None
