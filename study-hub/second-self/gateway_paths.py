"""路径常量 — 所有文件操作的根入口

防止路径遍历：所有路径必须在 ROOT 之下。
"""
from pathlib import Path

# 项目根目录（second-self/ 的父目录是 study-hub/）
ROOT = Path(__file__).parent.resolve()


def safe_path(relative: str) -> Path:
    """将相对路径转为安全绝对路径。

    如果解析后超出 ROOT，抛出 ValueError。
    """
    target = (ROOT / relative).resolve()
    if not str(target).startswith(str(ROOT)):
        raise ValueError(f"路径遍历风险: {relative}")
    return target
