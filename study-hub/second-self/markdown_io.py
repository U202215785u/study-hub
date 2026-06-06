"""Markdown 文件读写 — 核心 Self 层文件操作

raw/ 目录内容不可变（只能通过 /api/file 读取，不能写入）。
"""
from pathlib import Path

from gateway_paths import ROOT


def read_markdown(rel_path: str) -> str:
    """读取 markdown 文件内容。"""
    path = ROOT / rel_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_markdown(rel_path: str, content: str) -> None:
    """写入 markdown 文件（raw/ 除外）。"""
    path = ROOT / rel_path
    if str(path).startswith(str(ROOT / "raw")):
        raise PermissionError("raw/ 目录不可变")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def list_markdown_files(rel_dir: str) -> list[str]:
    """列出目录下所有 .md 文件的相对路径。"""
    directory = ROOT / rel_dir
    if not directory.exists():
        return []
    return [
        str(p.relative_to(ROOT)).replace("\\", "/")
        for p in directory.rglob("*.md")
    ]
