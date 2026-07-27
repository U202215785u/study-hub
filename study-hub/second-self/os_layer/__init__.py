"""OS Layer — Second Self 的操作系统能力扩展

提供：
  - safety_guard    安全检查（对标 OpenClaw Hardstop）
  - shell_executor  Shell 命令执行
  - fs_operator     文件系统操作
  - browser_controller 浏览器控制
  - skill_registry  技能注册与执行
  - gateway         统一执行入口

使用：
  from os_layer import gateway
  result = gateway.execute("shell.execute", {"command": "ls -la"})
"""
from . import gateway
from . import safety_guard
from . import shell_executor
from . import fs_operator
from . import browser_controller
from . import skill_registry

__all__ = ["gateway", "safety_guard", "shell_executor", "fs_operator", "browser_controller", "skill_registry"]
