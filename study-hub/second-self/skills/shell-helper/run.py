"""Shell Helper Skill — 执行入口"""
import os
import subprocess
import time
from pathlib import Path


def run(args: dict):
    """
    args: {
        "command": "要执行的命令",
        "cwd": "工作目录（可选）",
        "timeout": 30,
    }
    """
    cmd = args.get("command", "")
    cwd = args.get("cwd", os.getcwd())
    timeout = args.get("timeout", 30)

    if not cmd:
        return {"error": "缺少 command 参数"}

    # 常见别名
    aliases = {
        "ll": "ls -la",
        "la": "ls -a",
    }
    parts = cmd.split(None, 1)
    if parts and parts[0] in aliases:
        cmd = aliases[parts[0]] + (" " + parts[1] if len(parts) > 1 else "")

    start = time.time()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
        cwd=str(Path(cwd).expanduser()),
        encoding="utf-8",
        errors="replace",
    )
    stdout, stderr = proc.communicate(timeout=timeout)
    duration = (time.time() - start) * 1000

    return {
        "stdout": stdout[:5000],
        "stderr": stderr[:2000],
        "exit_code": proc.returncode,
        "duration_ms": round(duration, 2),
    }
