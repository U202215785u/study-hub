"""文件系统操作器 — 安全的文件读写

支持：读文件、写文件、列出目录、搜索内容、复制、移动、删除
"""
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .safety_guard import check_file_operation, RiskLevel


@dataclass
class FSResult:
    success: bool
    content: str = ""
    error: str = ""
    path: str = ""
    operation: str = ""
    risk_level: str = "safe"


def read_file(path: str, max_bytes: int = 500_000) -> FSResult:
    """安全读取文件内容。"""
    check = check_file_operation("read", path)
    if check.blocked:
        return FSResult(False, error=f"[BLOCKED] {check.reason}", path=path, operation="read", risk_level=check.risk.value)

    try:
        target = Path(path).expanduser().resolve()
        if not target.exists():
            return FSResult(False, error=f"文件不存在: {path}", path=str(target), operation="read")
        if target.is_dir():
            return FSResult(False, error=f"路径是目录，不是文件: {path}", path=str(target), operation="read")

        size = target.stat().st_size
        if size > max_bytes:
            # 读取前 max_bytes
            content = target.read_bytes()[:max_bytes].decode("utf-8", errors="replace")
            content += f"\n\n[文件过大，已截断。实际大小: {size} bytes]"
        else:
            content = target.read_text(encoding="utf-8", errors="replace")

        return FSResult(True, content=content, path=str(target), operation="read", risk_level=check.risk.value)
    except Exception as e:
        return FSResult(False, error=f"读取失败: {str(e)}", path=path, operation="read")


def write_file(path: str, content: str, *, user_confirmed: bool = False, append: bool = False) -> FSResult:
    """安全写入文件。"""
    check = check_file_operation("write", path)
    if check.blocked:
        return FSResult(False, error=f"[BLOCKED] {check.reason}", path=path, operation="write", risk_level=check.risk.value)
    if check.requires_confirmation and not user_confirmed:
        return FSResult(
            False,
            error=f"[NEEDS_CONFIRMATION] {check.reason}\n请显式确认后再执行写操作。",
            path=path,
            operation="write",
            risk_level=check.risk.value,
        )

    try:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if append else "w"
        with open(target, mode, encoding="utf-8") as f:
            f.write(content)

        return FSResult(True, path=str(target), operation="write", risk_level=check.risk.value)
    except Exception as e:
        return FSResult(False, error=f"写入失败: {str(e)}", path=path, operation="write")


def list_directory(path: str = ".") -> FSResult:
    """列出目录内容。"""
    check = check_file_operation("list", path)
    if check.blocked:
        return FSResult(False, error=f"[BLOCKED] {check.reason}", path=path, operation="list", risk_level=check.risk.value)

    try:
        target = Path(path).expanduser().resolve()
        if not target.exists():
            return FSResult(False, error=f"目录不存在: {path}", path=str(target), operation="list")
        if not target.is_dir():
            return FSResult(False, error=f"路径不是目录: {path}", path=str(target), operation="list")

        items = []
        for entry in sorted(target.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            prefix = "[DIR] " if entry.is_dir() else "[FILE]"
            size = ""
            if entry.is_file():
                size = f" ({entry.stat().st_size:,} bytes)"
            items.append(f"{prefix} {entry.name}{size}")

        return FSResult(
            True,
            content="\n".join(items) or "(空目录)",
            path=str(target),
            operation="list",
            risk_level=check.risk.value,
        )
    except PermissionError:
        return FSResult(False, error=f"权限不足，无法访问: {path}", path=path, operation="list")
    except Exception as e:
        return FSResult(False, error=f"列出目录失败: {str(e)}", path=path, operation="list")


def search_in_files(pattern: str, path: str = ".", glob_pattern: str = "*") -> FSResult:
    """在目录中搜索文件内容。"""
    import fnmatch

    check = check_file_operation("search", path)
    if check.blocked:
        return FSResult(False, error=f"[BLOCKED] {check.reason}", path=path, operation="search", risk_level=check.risk.value)

    try:
        target = Path(path).expanduser().resolve()
        if not target.exists() or not target.is_dir():
            return FSResult(False, error=f"目录不存在: {path}", path=str(target), operation="search")

        matches = []
        max_matches = 50
        max_line_len = 200

        for root, dirs, files in os.walk(target):
            # 跳过隐藏目录和敏感目录
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git", "venv", ".venv")]

            for filename in files:
                if not fnmatch.fnmatch(filename.lower(), glob_pattern.lower()):
                    continue
                file_path = Path(root) / filename
                try:
                    text = file_path.read_text(encoding="utf-8", errors="replace")
                    lines = text.splitlines()
                    for i, line in enumerate(lines, 1):
                        if pattern.lower() in line.lower():
                            snippet = line.strip()
                            if len(snippet) > max_line_len:
                                snippet = snippet[:max_line_len] + "..."
                            matches.append(f"{file_path.relative_to(target)}:{i}: {snippet}")
                            if len(matches) >= max_matches:
                                break
                    if len(matches) >= max_matches:
                        break
                except (PermissionError, UnicodeDecodeError, OSError):
                    continue
            if len(matches) >= max_matches:
                break

        content = f"找到 {len(matches)} 条匹配:\n" + "\n".join(matches) if matches else "未找到匹配内容。"
        return FSResult(True, content=content, path=str(target), operation="search", risk_level=check.risk.value)
    except Exception as e:
        return FSResult(False, error=f"搜索失败: {str(e)}", path=path, operation="search")


def delete_path(path: str, *, user_confirmed: bool = False) -> FSResult:
    """删除文件或目录。"""
    check = check_file_operation("delete", path)
    if check.blocked:
        return FSResult(False, error=f"[BLOCKED] {check.reason}", path=path, operation="delete", risk_level=check.risk.value)
    if check.requires_confirmation and not user_confirmed:
        return FSResult(
            False,
            error=f"[NEEDS_CONFIRMATION] {check.reason}\n请显式确认后再执行删除操作。",
            path=path,
            operation="delete",
            risk_level=check.risk.value,
        )

    try:
        target = Path(path).expanduser().resolve()
        if not target.exists():
            return FSResult(False, error=f"路径不存在: {path}", path=str(target), operation="delete")

        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

        return FSResult(True, path=str(target), operation="delete", risk_level=check.risk.value)
    except Exception as e:
        return FSResult(False, error=f"删除失败: {str(e)}", path=path, operation="delete")
