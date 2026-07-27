# 通用陷阱（跨项目）

> 不限于当前项目的高频陷阱。

## 环境类

| 陷阱 | 说明 |
|------|------|
| Python 多版本混用 | 系统可能装了多个 Python。装包前先确认当前环境。 |
| 端口占用 | 启动服务前检查端口是否已被占用。 |
| 路径空格 | Windows 路径带空格导致命令解析错误。用引号包裹路径。 |
| **Windows GBK 编码崩溃** | Python 在 Windows 终端（GBK 编码）下 print 特殊字符（如 ✓、🚀、📋）会导致 `UnicodeEncodeError`，服务启动直接崩溃。解决方法：(1) 用 ASCII 字符替代 emoji，如 `[OK]` 代替 `✓`；(2) 或在入口文件强制 `sys.stdout` 使用 UTF-8 wrapper。 |
| **Windows venv python.exe GUI 子系统** | 在 Windows 上创建 venv 时，`python.exe` 可能被编译为 GUI 子系统（`PE32 executable ... (GUI)`），终端下无任何 stdout/stderr 输出。即使 Python 脚本报错也完全静默，排查极其困难。验证方法：`file venv/Scripts/python.exe`。解决：(1) 用系统 Python（console 子系统）启动，`PYTHONPATH` 指向 venv site-packages；(2) 或重建 venv 时确保 python.exe 是 console 子系统。 |
| **Windows Python Store 重定向器（exit code 49）** | Windows 将 `python`/`python3` 命令关联到 Microsoft Store 重定向器（`WindowsApps/python.exe`），执行任何脚本都返回 exit code 49，完全不运行。Git Bash 下尤其隐蔽。解决：用 PowerShell 或完整路径调用真实 Python（如 `C:\Users\...\Python312\python.exe`），或从 Microsoft Store 安装 Python 后首次通过 GUI 启动完成初始化。 |
| **SQLite WAL 并发锁** | WAL 模式下多进程/多线程同时写 SQLite 会出现 `database is locked`。解决：连接时设置 `PRAGMA busy_timeout=10000`（10秒），并给 `sqlite3.connect()` 传 `timeout=30.0`。 |
| **SQLite ALTER TABLE 不支持 CHECK** | `ALTER TABLE ... ADD COLUMN ... CHECK(...)` 在 SQLite 中会报错 `Cannot add a column with non-constant default`。迁移时应先加无约束的列，再用 `UPDATE` 修正数据，或在应用层做校验。 |
| **SQLite 文件锁导致目录无法删除** | 当 Python 进程持有 SQLite 数据库连接（尤其是 WAL 模式的 `entries.db` + `db-shm` + `db-wal`）时，`rm -rf` 会报 "Device or resource busy"。解决：先终止持有数据库连接的 Python 进程（可用 PowerShell `Get-Process python | Stop-Process -Force`），再删除目录。 |
| **Python 模块缓存不感知文件替换** | Python 进程启动后会将导入的模块缓存到 `sys.modules`，即使源 `.py` 文件被替换/删除，运行中的进程仍使用内存中的旧版本。迁移代码后必须重启服务，否则 API 可能返回旧数据或 `ImportError`。 |

## Git 类

| 陷阱 | 原因 | 修复 |
|------|------|------|
| 大文件提交 | 超过 100MB 的文件不要提交。用 .gitignore 排除。 |
| 合并冲突忽视 | 不要用 --force 覆盖远程分支。 |

## 通用

| 陷阱 | 说明 |
|------|------|
| 硬编码路径 | 绝对路径在另一台机器跑不了。用相对路径或配置文件。 |
| 密钥泄露 | API Key / Token 永远不要写进代码。用环境变量。 |

## 前端组件选型

| 陷阱 | 说明 |
|------|------|
| 甘特图/日历组件过重 | 对个人项目/DDL 面板，完整日历库（如 FullCalendar）或甘特图库过于庞大。日/周/月视图可用 `date-fns` + CSS Grid/Flex 自建，几百行代码即可，比引入几千 KB 的第三方库更可控。只在需要复杂功能（拖拽调整、资源视图、iCal 导出）时才引入完整库。 |

## 浏览器扩展开发

| 陷阱 | 说明 |
|------|------|
| **拖拽与固定状态耦合** | 侧边栏面板的拖拽功能不要和「固定/取消固定」按钮强绑定。固定状态只控制「松手后是否回到默认位置」，不应该阻止拖拽事件的触发。如果 `startDrag` 里判断 `if (isPinned) return`，用户必须先取消固定才能拖拽，体验极差。 |
| **收起/展开布局逻辑反了** | 面板收起时应该恢复页面原始布局（`marginRight = ''`），展开时才需要给面板留空间（`marginRight = '360px'`）。如果逻辑写反，收起后页面反而被挤压，展开后布局又不对。 |
| **事件委托优于逐个绑定** | 动态内容（如场景切换后重新渲染的 tabs）如果用 `addEventListener` 逐个绑定，切换后事件会丢失。改用事件委托（在父容器上监听 `click`，通过 `e.target.closest()` 分发），动态内容不需要重新绑定。 |
| **history API 拦截** | SPA（如 Bing 搜索）用 `history.pushState` 做无刷新跳转，只监听 `popstate` 会漏掉。需要同时拦截 `pushState` 和 `replaceState`，并在调用后触发检查。 |
| **Shadow DOM CSS 隔离** | 扩展面板用 Shadow DOM 注入样式时，外部页面的 CSS 不会影响内部，但内部的 `!important` 规则如果和页面冲突仍可能出问题。尽量用独特的类名前缀（如 `sh-*`）避免命名冲突。 |

## 前端渲染

| 陷阱 | 说明 |
|------|------|
| **Markdown + HTML escape 顺序** | 如果先 `esc()` 再 `simpleMarkdown()`，`**粗体**` 会被转义成 `&#42;&#42;粗体&#42;&#42;`，正则匹配失败。正确顺序：先对原始文本做 HTML escape（防 XSS），再解析 Markdown 语法生成 `<strong>` 标签。 |
| **流式 DOM 全量替换卡顿** | 每收到一个 token 就用 `innerHTML = ...` 全量替换，长文本时浏览器频繁重排。优化：用 `textContent` 增量更新，或 50ms 批量缓冲刷新。 |

## LLM / Prompt 工程

| 陷阱 | 说明 |
|------|------|
| **System Prompt 没有长度约束** | 不控制长度时，LLM 对简单问题也会给出冗长回复。应根据场景动态约束：HIGH 80-150字，MEDIUM 40-80字，LOW 20-40字。 |
| **System Prompt 语气不明确** | 只说"像朋友一样"不够，要给出具体可执行的风格指令：禁止"首先/其次/最后"、禁止"综上所述"、允许说"得了吧""别想了"。 |

## AI 文件操作安全

| 陷阱 | 说明 |
|------|------|
| **复合命令中的 `;` 与 `&&` 混淆** | `cmd1; cmd2` 表示无论 cmd1 成败都执行 cmd2。文件移动后接删除时，必须用 `&&`（`mv ... && rm ...`），否则 mv 失败后 rm 会把源目录直接扬了。 |
| **`2>/dev/null` 掩盖关键错误** | 把 stderr 重定向到 /dev/null 会隐藏文件被占用、路径不存在等错误，导致误判操作成功。涉及 `rm -rf` 的命令绝不应该搭配 `2>/dev/null`。 |
| **`.*` 展开包含 `.` 和 `..`** | Bash 的 `.*` 会匹配当前目录 `.` 和父目录 `..`，`mv` 遇到它们会报错或行为异常。移动文件时应明确列出隐藏文件，或使用 `find`/`rsync`。 |
| **删除前无验证** | 安全的文件迁移流程：(1) 复制到目标 → (2) 验证目标文件完整 → (3) 重命名源为 `.bak` → (4) 确认无误后删除。绝不应在验证前使用 `rm -rf`。 |
| **Git Bash `rm -rf` 不进回收站** | Windows Git Bash 的 `rm -rf` 是直删，不经过回收站。重要操作前应手动备份到 `.trash/` 或使用 `mv` 替代 `rm`。 |
