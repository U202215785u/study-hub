---
name: auto-readme
description: 为任意项目搭建自动更新 README 系统 —— 代码变更后 README 自动刷新，始终与代码同步。支持 Python / JS / TS / Go / Rust / Java 等多语言。
---

# auto-readme — 项目自动文档系统

一次配置，永久自动。代码变更 → README 中自动区立即刷新，永远与代码同步。

## 执行流程

### 第一步：探测项目

AI 先确认以下信息：

```
1. 项目语言/框架（Python FastAPI? React? Go Gin? Rust Actix?）
2. 主代码目录（src/? backend/? 还是根目录？）
3. Python 解释器路径（Windows: where python, Unix: which python3）
4. README 是否已存在（存在则嵌入 AUTO 标记，不存在则新建）
```

用 Read / Glob / Grep 快速探测，不要问用户（除非关键信息缺失）。

### 第二步：生成扫描脚本

#### 脚本必须包含的测试验证（TDD 模式）

如果用户明确要求“使用 TDD 让 AI 一次把代码写对”，则在生成扫描脚本后，立即生成对应的测试文件：
- 测试文件位置：`.Codex/scripts/test_generate_readme.py`
- 测试内容：
  1. 测试脚本能正确解析一个已知结构的示例项目
  2. 测试脚本能正确处理空目录（无代码文件）
  3. 测试脚本能正确处理混合语言项目
  4. 测试输出 Markdown 格式是否正确

执行测试并修复所有失败后再提交代码。

#### 脚本必须支持的语言模式（续）

| 语言 | 提取内容 |
|------|---------|
| **TypeScript/JavaScript** | `export function`/`export const`/`async function`/`interface`/`type` 定义 |
| **Go** | `func` 定义（含 receiver methods）、`type struct`/`type interface` |
| **Rust** | `fn` 定义、`pub fn`、`struct`/`enum`/`trait` 定义 |
| **Java** | `public class`/`public interface`/`@RequestMapping`/`@GetMapping` 等注解 |

> **提示**：对于未列出的语言，脚本应使用通用正则匹配函数/方法/类定义，并记录到日志中供后续扩展。

在 `.Codex/scripts/generate_readme.py` 生成一个完整的静态分析脚本。

#### 脚本必须支持的语言模式

| 语言 | 提取内容 |
|------|---------|
| **Python** | `def`/`async def` 函数签名 + docstring + `@router.get/post/...` 路由 + `class` 定义 + 关键 `from X import Y` |
| **JavaScript / TypeScript** | `function` / `const x = () =>` / `async function` + Express 路由 `router.get/post/...` + React 组件 + `import` |
| **Go** | `func` 函数签名 + `func (r *Receiver)` 方法 + `type struct/interface` + `mux.HandleFunc` / `gin.GET` 等路由 |
| **Rust** | `fn` 函数签名 + `pub fn` + `struct` / `enum` / `impl` / `trait` + `#[get("/")]` / `.route("/", ...)` 等路由 |
| **Java** | `public/private class` + `public/private ... method` + `@GetMapping/@PostMapping` 等 Spring 注解 |
| **HTML** | DOM `id` / `class` 列表 + `<script>` / `<style>` 块数量 + `fetch()` API 调用目标 |
| **CSS** | class 数量、关键选择器 |
| **配置** | `.env.example` 变量表 + `docker-compose.yml` 服务端口 + `package.json` scripts + `Cargo.toml` deps |

#### 脚本必须包含的通用能力

1. **文件指纹**：每个源文件记录 MD5（前 8 位）+ 行数，用于 `--check` 检测变更
2. **AUTO 标记**：`<!-- AUTO-GENERATED-START -->` / `<!-- AUTO-GENERATED-END -->` 之间内容由脚本覆写
3. **`--check` 模式**：对比指纹，有差异退出码 1，无差异退出码 0
4. **`--write` 模式**：先 check，stale 才写入（避免无意义覆写）
5. **UTF-8 输出**：`sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`

#### 脚本模板

生成脚本时，根据项目语言选择对应的解析器。下面是 Python 项目模板的核心结构（生成时按语言替换解析逻辑）：

```python
#!/usr/bin/env python3
"""
{AUTO_README_TITLE}
遍历项目源文件，提取每个函数、API 路由、数据模型、配置项，生成超详细 README。
用法: python generate_readme.py [--check] [--write]
"""
import os, sys, re, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # 根据实际路径调整
README_PATH = PROJECT_ROOT / "README.md"
AUTO_START = "<!-- AUTO-GENERATED-START -->"
AUTO_END = "<!-- AUTO-GENERATED-END -->"

# ... 语言特定的解析函数 ...

def collect_all_files() -> dict:
    """遍历项目，按类型分类收集文件"""
    # 跳过: venv, __pycache__, .git, node_modules, target, dist, build, data
    pass

def check_stale() -> bool:
    """对比 README 中的文件指纹和当前实际指纹"""
    pass

def generate_auto_readme() -> str:
    """生成完整的自动文档 Markdown"""
    pass

def update_readme(auto_content: str) -> bool:
    """将 AUTO 标记之间的内容替换为 auto_content"""
    pass

if __name__ == "__main__":
    # CLI: --check / --write / --stdout
    pass
```

### 第三步：配置 Hook

在 `.Codex/settings.json` 中配置 PostToolUse hook。

#### 关键约定

1. **使用 `&&` 链式调用**：先 `python -c "..."` 检查 `CLAUDE_TOOL_INPUT` 环境变量中的 `file_path` 是否包含项目目录，通过才执行生成脚本
2. **Python 路径必须用绝对路径**（Windows 上从 `where python` 获得）
3. **Edit 和 Write 工具都要挂 hook**
4. **如果已有 settings.json**，合并而非覆盖（保留已有配置）

#### Hook 配置模板

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [{
          "type": "command",
          "command": "{PYTHON_PATH} -c \"import os,json,sys; inp=json.loads(os.getenv('CLAUDE_TOOL_INPUT','{}')); fp=inp.get('file_path',''); sys.exit(0 if '{PROJECT_DIR}' in fp else 1)\" && {PYTHON_PATH} \"{SCRIPT_PATH}\" --write"
        }]
      },
      {
        "matcher": "Write",
        "hooks": [{
          "type": "command",
          "command": "{PYTHON_PATH} -c \"import os,json,sys; inp=json.loads(os.getenv('CLAUDE_TOOL_INPUT','{}')); fp=inp.get('file_path',''); sys.exit(0 if '{PROJECT_DIR}' in fp else 1)\" && {PYTHON_PATH} \"{SCRIPT_PATH}\" --write"
        }]
      }
    ]
  }
}
```

### 第四步：种子 README

1. 如果 README 已存在：在合适位置插入 `<!-- AUTO-GENERATED-START -->` / `<!-- AUTO-GENERATED-END -->` 标记对，保留现有手动内容
2. 如果 README 不存在：创建基础结构（项目名 + 一句话 + AUTO 标记）
3. 运行 `python .Codex/scripts/generate_readme.py --write` 填充自动区
4. 运行 `--check` 验证一切正常

### 第五步：交付说明

完成后，告诉用户：

```
自动文档系统已就绪。

工作方式：
  你改代码 → Hook 检测到 study-hub/ 下文件变更
  → 自动跑 generate_readme.py --write
  → 对比文件指纹，有差异才更新 README 自动区
  → 无差异跳过

手动触发：
  python .Codex/scripts/generate_readme.py --write   # 强制刷新
  python .Codex/scripts/generate_readme.py --check   # 仅检查

README 结构：
  手动区（你写的）→ AUTO 标记 → 自动区（脚本维护）→ AUTO 标记 → 手动区继续
  脚本只覆写 AUTO 之间的内容，之外的内容永远不动。
```

---

## 项目类型适配指南

### Python 项目（FastAPI / Flask / Django）

- 扫描 `backend/` `src/` `app/` 目录
- 提取 `@router.get/post/put/delete` (FastAPI) 或 `@app.route` (Flask)
- 提取 SQLAlchemy / Django ORM 模型
- 提取 `Pydantic BaseModel` 定义
- 检测 `requirements.txt` `pyproject.toml`

### Node.js 项目（Express / Next.js / React）

- 扫描 `src/` `pages/` `api/` 目录
- 提取 `router.get/post/put/delete` (Express)
- 提取 `export default function` / `export const` (React 组件)
- 提取 `app/api/` 路由 (Next.js App Router)
- 检测 `package.json` scripts 和 dependencies

### Go 项目

- 扫描 `cmd/` `internal/` `pkg/` 目录
- 提取 `func (s *Server) HandleXxx` 方法
- 提取 `mux.HandleFunc("/path", handler)` 路由注册
- 提取 `type Xxx struct` 数据模型
- 检测 `go.mod` module 和 dependencies

### Rust 项目

- 扫描 `src/` 目录
- 提取 `pub fn` / `pub async fn` 函数
- 提取 `#[get("/")]` / `.route("/", ...)` (Actix / Axum)
- 提取 `struct` / `enum` / `impl` / `trait`
- 检测 `Cargo.toml` dependencies

### 通用回退

如果项目语言不在上述列表中，至少：
- 列出所有文件的路径、行数、MD5 指纹
- 提取 `.env.example` 和 `docker-compose.yml` 的配置信息
- 提取 `package.json` / `requirements.txt` / `go.mod` / `Cargo.toml` 的依赖清单

---

## 脚本通用模板（完整版）

以下是 `generate_readme.py` 的通用模板。生成时，`{LANG_PARSERS}` 替换为语言特定的解析函数，`{LANG_SECTIONS}` 替换为语言特定的文档章节。

完整模板内嵌在 skill 中，生成时根据项目类型裁剪。关键结构：

```
1. 工具函数（safe_read, hash_file, rel）
2. {LANG_PARSERS} — 语言特定的 parse_* 函数
3. parse_env_example() — 通用
4. parse_docker_compose() — 通用
5. parse_package_json() — 如有 Node.js
6. collect_all_files() — 通用
7. {LANG_SECTIONS} — 语言特定的 gen_*_section 函数
8. generate_auto_readme() — 编排所有章节
9. update_readme() — 写入 AUTO 标记区
10. check_stale() — 对比文件指纹
11. CLI 入口 (--check, --write, --stdout)
```

---

## 注意事项

1. **脚本不导入项目依赖**：纯静态正则分析，不 `import` 项目模块，避免依赖缺失报错
2. **路径用正斜杠**：Windows 上也用 `/`，保证跨平台一致
3. **跳过生成文件**：`venv/` `__pycache__/` `.git/` `node_modules/` `target/` `dist/` `build/` `data/` `.next/`
4. **跳过二进制文件**：`.pyc` `.o` `.exe` `.dll` `.so` `.wasm` `.bin` `.db` `.sqlite3`
5. **合并已有 settings.json**：如果 `.Codex/settings.json` 已有其他配置（如 permissions），只追加 hooks 部分
6. **Hook 命令中的路径用绝对路径**：避免 working directory 问题

---

## 示例：完整执行

```
用户：帮这个项目搭自动文档

Codex：
  （第一步：探测）
  检测到 Python FastAPI 项目，主目录 study-hub/
  Python: C:/.../Python312/python.exe

  （第二步：生成脚本）
  正在生成 .Codex/scripts/generate_readme.py ...
  [包含 Python 解析器 + FastAPI 路由提取 + SQLite schema 提取]

  （第三步：配置 Hook）
  正在配置 .Codex/settings.json ...
  [Edit + Write → 检查路径含 study-hub → 执行 --write]

  （第四步：种子 README）
  README 已存在，嵌入 AUTO 标记...
  首次生成自动文档...
  OK: README.md 已更新

  完成！以后每次改代码，README 自动刷新。
```
