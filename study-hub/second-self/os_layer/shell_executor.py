"""Shell 执行器 — 安全地执行系统命令

对标 OpenClaw 的终端控制能力，集成 safety_guard 的风险检查。
"""
import os
import platform
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .safety_guard import check_shell_command, RiskLevel

# 工作目录白名单（默认允许操作的范围）
DEFAULT_ALLOWED_ROOTS = [
    Path(os.getcwd()).resolve(),
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Projects",
]

# 尝试加载用户自定义白名单
def _load_allowed_roots() -> list[Path]:
    roots = []
    for r in DEFAULT_ALLOWED_ROOTS:
        if r.exists():
            roots.append(r.resolve())
    # 检查是否有 ~/.second-self/allow-paths.txt
    config_file = Path.home() / ".second-self" / "allow-paths.txt"
    if config_file.exists():
        for line in config_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                p = Path(line).expanduser().resolve()
                if p.exists():
                    roots.append(p)
    return roots


ALLOWED_ROOTS = _load_allowed_roots()


@dataclass
class ShellResult:
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    command: str
    risk_level: str
    confirmed: bool


def execute(
    command: str,
    *,
    cwd: str = "",
    timeout: int = 30,
    user_confirmed: bool = False,
    bypass_safety: bool = False,
) -> ShellResult:
    """
    执行 Shell 命令，带安全检查。

    Args:
        command: 要执行的命令
        cwd: 工作目录
        timeout: 超时秒数
        user_confirmed: 用户是否已确认（用于 RISKY 命令）
        bypass_safety: 是否绕过安全检查（危险，仅用于用户显式要求）
    """
    start = time.time()

    # 1. 安全检查
    if not bypass_safety:
        check = check_shell_command(command, allow_risky=user_confirmed)
        if check.blocked:
            return ShellResult(
                stdout="",
                stderr=f"[BLOCKED] {check.reason}",
                exit_code=-1,
                duration_ms=0.0,
                command=command,
                risk_level=check.risk.value,
                confirmed=False,
            )
        if check.requires_confirmation and not user_confirmed:
            return ShellResult(
                stdout="",
                stderr=f"[NEEDS_CONFIRMATION] {check.reason}\n请显式确认后再执行此命令。",
                exit_code=-2,
                duration_ms=0.0,
                command=command,
                risk_level=check.risk.value,
                confirmed=False,
            )
    else:
        check = check_shell_command(command, allow_risky=True)
        check.risk = RiskLevel.RISKY if check.risk == RiskLevel.DANGEROUS else check.risk

    # 2. 确定工作目录
    work_dir = Path(cwd).resolve() if cwd else Path(os.getcwd()).resolve()

    # 3. 执行命令
    try:
        # Windows 需要 shell=True 来支持内置命令
        use_shell = platform.system() == "Windows"

        if use_shell:
            # Windows: 使用 cmd /c
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                cwd=str(work_dir),
                encoding="utf-8",
                errors="replace",
            )
        else:
            # Unix: 使用 bash -c
            proc = subprocess.Popen(
                ["bash", "-c", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(work_dir),
                encoding="utf-8",
                errors="replace",
            )

        stdout, stderr = proc.communicate(timeout=timeout)
        exit_code = proc.returncode

    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        return ShellResult(
            stdout=stdout or "",
            stderr=(stderr or "") + f"\n[TIMEOUT] 命令执行超过 {timeout} 秒，已终止。",
            exit_code=-3,
            duration_ms=(time.time() - start) * 1000,
            command=command,
            risk_level=check.risk.value,
            confirmed=user_confirmed or bypass_safety,
        )
    except Exception as e:
        return ShellResult(
            stdout="",
            stderr=f"[ERROR] 执行异常: {str(e)}",
            exit_code=-4,
            duration_ms=(time.time() - start) * 1000,
            command=command,
            risk_level=check.risk.value,
            confirmed=user_confirmed or bypass_safety,
        )

    duration_ms = (time.time() - start) * 1000

    # 4. 截断超长输出
    max_len = 10000
    if len(stdout) > max_len:
        stdout = stdout[:max_len] + f"\n... [截断，共 {len(stdout)} 字符]"
    if len(stderr) > max_len:
        stderr = stderr[:max_len] + f"\n... [截断，共 {len(stderr)} 字符]"

    return ShellResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        duration_ms=duration_ms,
        command=command,
        risk_level=check.risk.value,
        confirmed=user_confirmed or bypass_safety,
    )
