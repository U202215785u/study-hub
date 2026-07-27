#!/usr/bin/env python3
"""
Study-Hub 工具统一入口
自动检测可用的 Python 解释器，解决 Windows App Execution Alias 问题。

用法:
    py context/run.py indexer        # 运行代码地图生成器
    py context/run.py tool-scanner   # 运行工具扫描器
    py context/run.py update         # 一键顺序运行两者
"""

import subprocess
import sys
from pathlib import Path

# Windows 控制台 UTF-8 编码修复
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def find_python() -> str:
    """找到一个能正常工作的 Python 解释器。"""
    candidates = [
        "py",                           # Python Launcher (Windows 最可靠)
        "python3",
        "python",
        r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe",
    ]
    for cmd in candidates:
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                return cmd
        except Exception:
            continue
    print("错误：找不到可用的 Python 解释器。请安装 Python 或确保 'py' 命令可用。", file=sys.stderr)
    sys.exit(1)


def run_indexer(python: str):
    script = PROJECT_ROOT / "context" / "indexer.py"
    print(f"[run] 使用 {python} 运行 indexer.py ...")
    result = subprocess.run([python, str(script)], cwd=str(PROJECT_ROOT))
    return result.returncode


def run_tool_scanner(python: str):
    script = PROJECT_ROOT / "context" / "tool-scanner.py"
    print(f"[run] 使用 {python} 运行 tool-scanner.py ...")
    result = subprocess.run([python, str(script)], cwd=str(PROJECT_ROOT))
    return result.returncode


def main():
    if len(sys.argv) < 2:
        print("用法: py context/run.py [indexer | tool-scanner | update]")
        sys.exit(1)

    command = sys.argv[1]
    python = find_python()

    if command == "indexer":
        code = run_indexer(python)
        sys.exit(code)
    elif command == "tool-scanner":
        code = run_tool_scanner(python)
        sys.exit(code)
    elif command == "update":
        code1 = run_indexer(python)
        code2 = run_tool_scanner(python)
        if code1 != 0 or code2 != 0:
            print("[run] 部分任务失败，请检查上方输出。", file=sys.stderr)
            sys.exit(1)
        print("[run] 全部完成。")
        sys.exit(0)
    else:
        print(f"未知命令: {command}")
        print("用法: py context/run.py [indexer | tool-scanner | update]")
        sys.exit(1)


if __name__ == "__main__":
    main()
