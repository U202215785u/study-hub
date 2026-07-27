# 部署专家 Skill

领域：服务启动、进程管理、环境配置、端口冲突、后台运行、Windows 脚本。

触发域: [部署, 启动, 端口, 进程, 环境, 后台服务, powershell, bat, 脚本, 后台, 停止, 重启, 上线, 发布]

## 你被激活后的标准动作

1. **读领域记忆**：`project-memory/deploy/问题.md`、`project-memory/deploy/决策.md`、`project-memory/deploy/状态.md`
2. **查现场**：
   - 检查目标端口是否被占用（区分 LISTEN 和 TIME_WAIT）
   - 检查现有进程和 PID 文件
   - 确认 Python 环境（venv 是否被污染、python 命令是否可用）
   - 读启动脚本和日志
3. **结合陷阱做诊断**
4. **向管家汇报**：问题根因 + 建议方案 + 风险
5. **管家确认后执行**

## 硬约束
- **禁止手动启动**：所有启动必须通过 `后台启动.bat` → `start-background.ps1`
- 启动前必须先 stop（清理野进程和僵尸 PID）
- Windows 下必须用完整路径调用 Python，不依赖 `python` 命令
- 启动后必须验证端口真的在监听，不能只看脚本输出

## 通用陷阱

| 陷阱 | 严重度 | 说明 |
|------|--------|------|
| 野进程 | 高 | 绕过启动脚本手动启动的服务无 PID 文件，`stop-background.ps1` 找不到它，端口一直被占用。 |
| PID 僵尸化 | 高 | `data/server.pid` 记录的是已死进程的 PID，新启动时误判服务在跑。启动前必须校验端口 + 进程存在性。 |
| venv 被污染 | 高 | `venv\Scripts\python.exe` 可能被替换成 `HD_python.exe` 或 GUI 子系统，终端无输出、启动失败静默。优先用系统 Python312。 |
| Windows python 重定向器 | 高 | Windows 默认将 `python` 命令关联到 Microsoft Store 重定向器，返回 exit code 49，完全不执行。 |
| Kimi Bash 超时杀进程 | 高 | Kimi CLI 的 Shell 后台任务有超时（默认 15s），持续运行的后端进程会被强制终止。必须用项目提供的后台启动脚本。 |
| TIME_WAIT 误判 | 中 | 停止服务后端口上的 TIME_WAIT 残留连接不应阻止新服务启动。端口检查必须过滤 `State -eq 'Listen'`。 |
| localhost IPv6 误判 | 中 | Windows 上 `localhost` 可能解析为 `::1`，但服务只监听 IPv4。端口检测必须用 `127.0.0.1`。 |
| Git Bash 后台不可靠 | 高 | Git Bash 的 `nohup &` 在 Windows 下启动的 Python 进程网络绑定异常，表现为 netstat 显示监听但实际连不上。 |
