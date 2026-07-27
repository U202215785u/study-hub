"""安全守卫 — 对标 OpenClaw Hardstop

对每一条 OS 操作指令进行风险分类：
  SAFE     → 自动执行（L2）
  RISKY    → 需要确认（L1）
  DANGEROUS→ 拦截或严格确认
"""
import os
import re
import shlex
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RiskLevel(Enum):
    SAFE = "safe"
    RISKY = "risky"
    DANGEROUS = "dangerous"


@dataclass
class SafetyCheck:
    risk: RiskLevel
    reason: str
    requires_confirmation: bool
    blocked: bool = False


# ── 危险命令黑名单（绝对禁止，除非显式 bypass）─────────────────
DANGEROUS_COMMANDS = {
    "rm", "rmdir", "del", "format", "mkfs", "fdisk", "dd",
    "shutdown", "reboot", "halt", "poweroff", "init", "systemctl",
    "kill", "killall", "pkill", "taskkill",
    "chmod", "chown", "chgrp", "setfacl",
    "curl", "wget", "fetch",  # 网络下载需确认
    "ssh", "scp", "sftp", "ftp", "telnet",
    "sudo", "su", "doas", "runas",
    "pip", "npm", "yarn", "pnpm", "gem", "composer",  # 包管理需确认
    "apt", "yum", "dnf", "pacman", "brew", "choco", "winget",
    "docker", "kubectl", "terraform", "ansible",
}

# 只读安全命令
SAFE_COMMANDS = {
    "ls", "dir", "cat", "type", "head", "tail", "less", "more",
    "find", "grep", "rg", "which", "where", "pwd", "cd",
    "echo", "printenv", "env", "date", "whoami", "uname",
    "git", "status", "log", "diff", "show", "branch",
    "wc", "sort", "uniq", "cut", "awk", "sed", "tr",
    "file", "stat", "du", "df", "free", "top", "htop", "ps",
    "python", "python3", "node", "ruby", "perl",
}

# 敏感路径（默认禁止访问）
SENSITIVE_PATHS = [
    ".ssh", ".gnupg", ".aws", ".azure", ".gcloud",
    ".env", ".env.", "id_rsa", "id_ed25519", ".pem", ".key",
    ".config", "credentials", "token", "secret", "password",
    ".gitconfig", ".netrc", ".npmrc", ".pypirc",
    "/etc/shadow", "/etc/passwd", "/etc/hosts",
]

# Windows 敏感路径
WINDOWS_SENSITIVE = [
    r"C:\\Windows", r"C:\\Program Files", r"C:\\ProgramData",
    r"System32", r"SysWOW64", r"Registry",
]

# 破坏性参数模式
DESTRUCTIVE_PATTERNS = [
    re.compile(r"\brm\s+.*-r\s+.*[/\\]?\s*$"),
    re.compile(r"\brm\s+.*-f\s+.*[/\\]?\s*$"),
    re.compile(r"\brm\s+.*[/\\*]?\s*$"),
    re.compile(r">\s*[/\\]?\s*\b"),  # 重定向到根
    re.compile(r"\bdd\s+.*if=.*of="),
    re.compile(r"\bformat\s+.*[/\\]"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bdel\s+.*[/\\*]?\s*\.\*"),
]


def _extract_command(cmd: str) -> str:
    """提取命令主词。"""
    cmd = cmd.strip()
    # 处理管道和重定向，取第一个命令
    for delim in ["|", ">", "<", ";", "&&", "||"]:
        if delim in cmd:
            cmd = cmd.split(delim)[0]
            break
    # 去掉 sudo/runas 前缀
    prefixes = ["sudo", "doas", "runas", "/usr/bin/sudo"]
    parts = shlex.split(cmd)
    while parts and parts[0].lower().lstrip("/\\").replace("usr/bin/", "").replace("usr/local/bin/", "") in prefixes:
        parts = parts[1:]
    return parts[0].lower() if parts else ""


def _has_destructive_pattern(cmd: str) -> tuple[bool, str]:
    """检查命令是否匹配破坏性模式。"""
    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern.search(cmd):
            return True, f"命中破坏性模式: {pattern.pattern[:40]}..."
    # 检查是否重定向到空或根
    if re.search(r">\s*/\s*\b|>\s*C:\\\s*\b", cmd):
        return True, "检测到向根目录或系统盘重定向"
    return False, ""


def _has_sensitive_path(cmd: str) -> tuple[bool, str]:
    """检查命令是否涉及敏感路径。"""
    cmd_lower = cmd.lower()
    for sp in SENSITIVE_PATHS:
        if sp.lower() in cmd_lower:
            return True, f"涉及敏感路径/文件: {sp}"
    for wp in WINDOWS_SENSITIVE:
        if wp.lower().replace("\\\\", "\\") in cmd_lower.replace("/", "\\"):
            return True, f"涉及 Windows 系统目录: {wp}"
    return False, ""


def check_shell_command(cmd: str, allow_risky: bool = False) -> SafetyCheck:
    """
    检查 Shell 命令的安全等级。

    返回 SafetyCheck:
      - blocked=True → 绝对禁止，不给选项
      - requires_confirmation=True → 需要用户确认
    """
    if not cmd or not cmd.strip():
        return SafetyCheck(RiskLevel.SAFE, "空命令", False)

    cmd_stripped = cmd.strip()
    main_cmd = _extract_command(cmd_stripped)

    # 1. 先检查破坏性模式
    destructive, reason = _has_destructive_pattern(cmd_stripped)
    if destructive:
        return SafetyCheck(
            RiskLevel.DANGEROUS,
            reason,
            requires_confirmation=True,
            blocked=not allow_risky,
        )

    # 2. 检查敏感路径
    sensitive, reason = _has_sensitive_path(cmd_stripped)
    if sensitive:
        return SafetyCheck(
            RiskLevel.RISKY,
            reason,
            requires_confirmation=True,
            blocked=False,
        )

    # 3. 检查命令主词
    if main_cmd in DANGEROUS_COMMANDS:
        return SafetyCheck(
            RiskLevel.RISKY,
            f"命令 '{main_cmd}' 属于受控命令",
            requires_confirmation=True,
            blocked=False,
        )

    if main_cmd in SAFE_COMMANDS:
        return SafetyCheck(
            RiskLevel.SAFE,
            f"命令 '{main_cmd}' 在只读白名单中",
            requires_confirmation=False,
        )

    # 4. 未知命令 → 保守处理为 RISKY
    return SafetyCheck(
        RiskLevel.RISKY,
        f"未知命令 '{main_cmd}'，需要确认",
        requires_confirmation=True,
    )


def check_file_operation(operation: str, path: str, content: str = "") -> SafetyCheck:
    """
    检查文件操作的安全等级。
    operation: read / write / delete / list / search
    """
    path_obj = Path(path).resolve()
    path_str = str(path_obj).lower()

    # 检查敏感路径
    for sp in SENSITIVE_PATHS:
        if sp.lower() in path_str:
            return SafetyCheck(
                RiskLevel.DANGEROUS,
                f"目标路径涉及敏感文件: {sp}",
                requires_confirmation=True,
                blocked=True,
            )

    # 系统目录保护
    system_roots = ["/etc", "/usr", "/bin", "/sbin", "/lib", "/sys", "/proc", "/dev", "/boot"]
    for sr in system_roots:
        if path_str.startswith(sr):
            return SafetyCheck(
                RiskLevel.DANGEROUS,
                f"目标路径位于系统目录: {sr}",
                requires_confirmation=True,
                blocked=True,
            )

    # 写操作和删除操作需要确认
    if operation in ("write", "delete"):
        return SafetyCheck(
            RiskLevel.RISKY,
            f"{operation} 操作可能修改文件系统",
            requires_confirmation=True,
        )

    # 读操作自动放行
    if operation == "read":
        if not path_obj.exists():
            return SafetyCheck(
                RiskLevel.SAFE,
                "读取不存在的文件（将返回错误）",
                requires_confirmation=False,
            )
        return SafetyCheck(
            RiskLevel.SAFE,
            "只读操作",
            requires_confirmation=False,
        )

    # list / search 自动放行
    return SafetyCheck(
        RiskLevel.SAFE,
        f"{operation} 为只读操作",
        requires_confirmation=False,
    )


def check_browser_action(action: str, url: str = "") -> SafetyCheck:
    """检查浏览器操作的安全等级。"""
    if action in ("navigate", "click", "type", "submit"):
        # 检查 URL 是否可疑
        suspicious = ["login", "signin", "auth", "password", "credential", "bank", "pay"]
        url_lower = url.lower()
        for s in suspicious:
            if s in url_lower:
                return SafetyCheck(
                    RiskLevel.RISKY,
                    f"URL 可能涉及认证/支付页面: {s}",
                    requires_confirmation=True,
                )
        return SafetyCheck(
            RiskLevel.RISKY,
            f"浏览器交互操作 '{action}' 需要确认",
            requires_confirmation=True,
        )

    if action in ("screenshot", "extract", "read"):
        return SafetyCheck(
            RiskLevel.SAFE,
            f"浏览器只读操作 '{action}'",
            requires_confirmation=False,
        )

    return SafetyCheck(
        RiskLevel.RISKY,
        f"未知浏览器操作 '{action}'",
        requires_confirmation=True,
    )
