# 🩺 Study Hub 排障手册

> 不懂代码也能定位问题。出问题时按「症状 → 原因 → 解法」三步走。

---

## 快速诊断流程图

```
页面打不开？
  ├── 看管理控制台 http://localhost:8741/admin.html
  │     ├── 绿灯亮着 → 页面缓存问题，按 Ctrl+F5 刷新
  │     └── 红灯/打不开 → 服务没启动，往下读「服务启动失败」
  └──

功能不正常？
  ├── 看「状态看板」数字对不对
  ├── 看「日志」有没有红色报错
  └── 对照下面表格找症状
```

---

## 服务启动失败

### 症状 1：运行启动脚本后窗口一闪就关
**原因**：Python 环境异常（如 GamePP 注入的 `HD_python.exe`）

**解法**：
```powershell
# 用 PowerShell 运行，能看到报错
powershell -ExecutionPolicy Bypass -File start.ps1
```
如果看到 `HD_python.exe` 相关报错，说明第三方软件篡改了 venv。请：
1. 卸载或退出 GamePP / 游戏加加 等性能监控软件
2. 删除 `venv` 文件夹重新创建：`python -m venv venv`
3. 使用系统原始 Python 启动（脚本已自动处理）

### 症状 2：卡在「启动服务…」很久没反应
**原因**：`sentence-transformers` + PyTorch 首次加载较慢（正常 5-30 秒）

**解法**：耐心等待。启动日志会打印进度，如果超过 2 分钟：
1. 结束进程
2. 检查网络（需要下载 HuggingFace 模型，国内已配置镜像）
3. 检查 `HF_ENDPOINT=https://hf-mirror.com` 是否在 `.env` 中

### 症状 3：`ModuleNotFoundError: No module named 'dashscope'`
**原因**：`requirements.txt` 未安装完整（旧版本缺失 dashscope）

**解法**：
```bash
cd backend
pip install -r requirements.txt
# 或直接用 venv 的 pip
../venv/Scripts/pip.exe install -r requirements.txt
```

---

## 功能异常

### 症状 4：上传文件后知识库没增加
**检查点**：
1. 管理控制台「知识库文档」数字是否 +1
2. 日志中是否有红色报错
3. 文件类型是否支持（txt / md / pdf）

**常见原因**：
- 文件名有特殊符号（`#`、`%`、`&`）→ 重命名后重新上传
- PDF 是扫描件（图片）→ 无法提取文字，需 OCR 后上传
- 文件超过 50MB → 分段上传或压缩

### 症状 5：RAG 搜索答非所问
**检查点**：
1. 「数据大小」是否为 0 → 向量库为空
2. 日志中是否有 `Embedding: 使用本地模型 xxx` 字样

**常见原因**：
- **向量库为空**：没有上传过文档，或文档上传失败
- **Embedding 模型加载失败**：看日志，如果显示模型加载失败，可能是网络问题导致模型下载中断
- **中文模型 vs 英文模型混用**：如果日志显示 `all-MiniLM-L6-v2`（英文模型），中文搜索效果会很差。应确保使用 `bge-small-zh-v1.5` 或 `bge-large-zh-v1.5`

### 症状 6：Chrome 扩展不采集对话
**检查点**：
1. 打开 `chrome://extensions` → 看 Study Hub 扩展图标是否变红
2. 点扩展图标 → 看后端地址是否为 `http://localhost:8741`
3. 在 Claude/ChatGPT 页面按 F12 → Console → 看是否有红色报错

**常见原因**：
- 扩展后端地址填错 → 修改为正确端口
- 扩展权限不足 → 在 `chrome://extensions` 中打开「允许访问文件网址」
- 后端服务重启过 → 扩展需要重新连接，刷新页面即可

### 症状 7：Inbox 拖入文件没反应
**检查点**：
1. 管理控制台「数据大小」是否变化
2. 看日志是否有 `InboxHandler` 相关记录

**常见原因**：
- Watcher 没启动（极少见，通常是服务启动时初始化失败）
- 文件正在被其他程序占用（如 Word 打开中）→ 关闭后重试

---

## 数据相关

### 症状 8：数据丢了 / 想恢复
**解法**：
1. 数据实际存在 `backend/data/` 文件夹：
   - `study_hub.db` —— SQLite 数据库
   - `chroma/` —— 向量库
   - `inbox/` —— 原始文件
2. 备份：直接复制整个 `data/` 文件夹
3. 恢复：把备份的 `data/` 覆盖回来，重启服务即可

### 症状 9：想清空所有数据重来
**解法**：
1. 停止服务
2. 删除 `backend/data/` 下的所有文件（保留空文件夹）
3. 重新启动服务（会自动重建数据库）

---

## 环境相关

### 症状 10：端口被占用（`Address already in use`）
**解法**：
```powershell
# 查看谁占用了 8741
netstat -ano | findstr :8741
# 记下最后一列 PID，然后结束进程
taskkill /F /PID <PID>
```

### 症状 11：Docker 启动失败
**解法**：
1. 确认 Docker Desktop 已运行
2. 首次构建需要 5-10 分钟下载模型
3. 如果卡住，检查 `.env` 是否已配置 API Key

---

## 前端构建问题

### 症状 12：`npm run build` 无任何输出直接退出 / `Error: The service was stopped`
**原因**：360 安全卫士将 `node_modules/@esbuild/win32-x64/esbuild.exe` 替换为 `RuntimeBroker` 代理程序，破坏了 esbuild 与 Node.js 的 IPC 通信。

**验证**：
```powershell
Get-Item "node_modules\@esbuild\win32-x64\esbuild.exe" | Select-Object VersionInfo
# 如果 ProductName 显示为 RuntimeBroker，说明已被替换
```

**解法**：
1. `frontend/package.json` 已配置 `overrides: { esbuild: "npm:esbuild-wasm@0.21.5" }`
2. 删除 `frontend/node_modules` 和 `frontend/package-lock.json`（若 360 锁定导致删不掉，需临时退出 360 防护）
3. 重新安装：`cd frontend && npm install`
4. 再次构建：`npm run build`

---

## 后台运行问题

### 症状 13：后端服务在 Kimi CLI 后台任务中 60s 后被 kill
**原因**：Kimi CLI `Shell(run_in_background=true)` 默认 60s 超时。`启动.bat` 是阻塞式前台脚本，不适合后台运行。

**解法**：使用项目根目录新增的专用后台启动脚本：
```powershell
# 在项目根目录执行
.\后台启动.bat    # 双击也行
```
- 服务会在**无窗口**的后台独立运行，不受 CLI 超时影响
- PID 自动写入 `backend/data/server.pid`

**停止**：
```powershell
.\后台停止.bat
```

---

## 如何获取帮助

1. **打开管理控制台** → `http://localhost:8741/admin.html`
2. **复制日志最后 20 行**（从 `backend/data/app.log` 或控制台输出）
3. **说明症状**：做了什么操作 → 预期什么结果 → 实际发生什么
