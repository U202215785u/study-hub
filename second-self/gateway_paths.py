"""路径常量与安全检查。"""
from pathlib import Path

ROOT = Path(__file__).parent.resolve()


def safe_resolve(path: str) -> Path:
    """解析路径，阻止目录穿越。"""
    target = ROOT / path
    target = target.resolve()
    if not str(target).startswith(str(ROOT)):
        raise ValueError("path traversal blocked")
    return target


def is_immutable(path: Path) -> bool:
    """检查路径是否在 raw/ 目录下（不可变）。"""
    return "raw" in str(path).lower()


def is_core_self_file(path: Path) -> bool:
    """检查是否是核心 Self 文件。"""
    core_names = {"ME.md", "DASHBOARD.md", "PRINCIPLES.md", "PREFERENCES.md", "AUTONOMY.md", "DECISIONS.md", "TASKS.md"}
    return path.name in core_names
