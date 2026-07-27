"""Markdown 文件读写。"""
from pathlib import Path

from gateway_paths import ROOT, safe_resolve, is_immutable


def read_file(path: str) -> dict:
    """读取文件内容。"""
    target = safe_resolve(path)
    if not target.exists():
        raise FileNotFoundError(path)
    return {
        "path": path,
        "content": target.read_text(encoding="utf-8"),
    }


def write_file(path: str, content: str) -> None:
    """写入文件内容。"""
    target = safe_resolve(path)
    if is_immutable(target):
        raise PermissionError("raw is immutable")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def list_core_files() -> list[dict]:
    """列出核心 Self 文件。"""
    core_files = ["ME.md", "DASHBOARD.md", "PRINCIPLES.md", "PREFERENCES.md", "AUTONOMY.md", "DECISIONS.md", "TASKS.md"]
    result = []
    for name in core_files:
        path = ROOT / name
        if path.exists():
            result.append({
                "name": name,
                "size": path.stat().st_size,
                "modified": path.stat().st_mtime,
            })
    return result


def append_to_log(path: str, content: str) -> None:
    """追加内容到日志文件。"""
    target = safe_resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as f:
        f.write(content + "\n")
