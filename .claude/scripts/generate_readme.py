#!/usr/bin/env python3
"""
学习中枢 README 自动生成器 — 全项目覆盖版

遍历所有子项目源文件，提取函数、类、API 路由、数据模型、
配置项、HTML 结构、JS 函数，生成超详细 README。

用法: python generate_readme.py [--check] [--write]

  --check   仅检查 README 是否需要更新（退出码 0=最新, 1=过期）
  --write   写入 README.md（默认仅打印到 stdout）
  --stdout  输出到 stdout（默认行为，没有 --write 时）

覆盖子项目:
  - study-hub/ (FastAPI 后端 + 前端 + 扩展 + MCP)
  - bilibili-mcp-server/ (B站 MCP)
  - xiaohongshu-mcp-server/ (小红书 MCP)
  - mods/ (工具百宝箱)
"""

import os, sys, re, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).resolve().parent  # .claude/scripts/
WORKSPACE_ROOT = SCRIPT_DIR.parent.parent  # study web/
PROJECT_ROOT = WORKSPACE_ROOT / "study-hub"
MODS_ROOT = WORKSPACE_ROOT / "mods"
BILIBILI_ROOT = WORKSPACE_ROOT / "bilibili-mcp-server"
XHS_ROOT = WORKSPACE_ROOT / "xiaohongshu-mcp-server"
README_PATH = PROJECT_ROOT / "README.md"
AUTO_START = "<!-- AUTO-GENERATED-START -->"
AUTO_END = "<!-- AUTO-GENERATED-END -->"

# 根目录 README 微型自动区
ROOT_README_PATH = WORKSPACE_ROOT / "README.md"
ROOT_AUTO_START = "<!-- AUTO-STATS-START -->"
ROOT_AUTO_END = "<!-- AUTO-STATS-END -->"

# ============================================================
# 工具函数
# ============================================================

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")

def safe_read(path: Path) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""

def hash_file(path: Path) -> str:
    return hashlib.md5(safe_read(path).encode()).hexdigest()[:8]

# ============================================================
# Python 解析
# ============================================================

def parse_python_functions(code: str, filepath: Path) -> list[dict]:
    funcs = []
    pattern = r'^\s*(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\S+))?\s*:'
    lines = code.split("\n")
    for i, line in enumerate(lines):
        m = re.match(pattern, line)
        if not m:
            continue
        name = m.group(1)
        if name.startswith("_") and name != "__init__":
            continue
        docstring = ""
        j = i + 1
        in_doc = False
        doc_lines = []
        while j < len(lines):
            stripped = lines[j].strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_doc:
                    in_doc = True
                    doc_lines.append(stripped)
                    if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                        docstring = stripped.strip('"""').strip("'''").strip()
                        break
                else:
                    doc_lines.append(stripped)
                    docstring = "\n".join(doc_lines).strip('"""').strip("'''").strip()
                    break
            elif in_doc:
                doc_lines.append(stripped)
            else:
                break
            j += 1
        indent = len(line) - len(line.lstrip())
        is_method = indent > 0
        decorators = []
        k = i - 1
        while k >= 0 and lines[k].strip().startswith("@"):
            decorators.append(lines[k].strip())
            k -= 1
        decorators.reverse()
        funcs.append({
            "name": name, "params": m.group(2).strip(),
            "return_type": m.group(3) or "",
            "doc": docstring[:200] if docstring else "",
            "decorators": decorators, "is_method": is_method,
            "line": i + 1,
        })
    return funcs

def parse_python_classes(code: str, filepath: Path) -> list[dict]:
    classes = []
    pattern = r'^\s*class\s+(\w+)\s*(?:\(([^)]*)\))?\s*:'
    lines = code.split("\n")
    for i, line in enumerate(lines):
        m = re.match(pattern, line)
        if not m:
            continue
        classes.append({"name": m.group(1), "bases": m.group(2) or "", "line": i + 1})
    return classes

def parse_fastapi_routes(code: str, filepath: Path) -> list[dict]:
    routes = []
    route_pattern = r'@(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
    lines = code.split("\n")
    for i, line in enumerate(lines):
        m = re.search(route_pattern, line)
        if not m:
            continue
        method = m.group(1).upper()
        path = m.group(2)
        func_name = ""; params = ""
        for j in range(i + 1, min(i + 8, len(lines))):
            fm = re.match(r'^\s*(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)', lines[j])
            if fm:
                func_name = fm.group(1)
                params_raw = fm.group(2)
                key_params = []
                for p in params_raw.split(","):
                    p = p.strip()
                    if p and p != "self":
                        key_params.append(p.split(":")[0].strip())
                params = ", ".join(key_params)
                break
        routes.append({"method": method, "path": path, "handler": func_name, "params": params, "line": i + 1})
    return routes

def parse_python_imports(code: str, filepath: Path) -> list[str]:
    imports = []
    internal_prefixes = ["endpoints", "processing", "ai_client", "database", "watcher", "bilibili_mcp_server", "xiaohongshu_mcp_server"]
    key_third_party = ["fastapi", "chromadb", "httpx", "watchdog", "pymupdf", "sentence_transformers", "uvicorn", "mcp"]
    for line in code.split("\n"):
        line = line.strip()
        m = re.match(r'^from\s+(\S+)\s+import\s+(.+)$', line)
        if m:
            module = m.group(1); items = m.group(2)
            if any(module.startswith(p) for p in internal_prefixes + key_third_party):
                imports.append(f"from {module} import {items}")
            continue
        m = re.match(r'^import\s+(.+)$', line)
        if m:
            module = m.group(1)
            if any(module.startswith(p) for p in key_third_party):
                imports.append(f"import {module}")
    return imports

def parse_python_file(filepath: Path) -> dict:
    code = safe_read(filepath)
    if not code:
        return None
    return {
        "path": rel(filepath), "hash": hash_file(filepath),
        "lines": len(code.split("\n")),
        "classes": parse_python_classes(code, filepath),
        "functions": parse_python_functions(code, filepath),
        "routes": parse_fastapi_routes(code, filepath),
        "imports": parse_python_imports(code, filepath),
    }

# ============================================================
# JS / HTML 解析
# ============================================================

def parse_js_functions(code: str, filepath: Path) -> list[dict]:
    funcs = []
    patterns = [
        r'^\s*(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
        r'^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>',
    ]
    lines = code.split("\n")
    for i, line in enumerate(lines):
        for pat in patterns:
            m = re.match(pat, line)
            if m:
                funcs.append({"name": m.group(1), "params": m.group(2).strip(), "line": i + 1})
                break
    return funcs

def parse_html_structure(code: str, filepath: Path) -> dict:
    ids = re.findall(r'id\s*=\s*["\']([^"\']+)["\']', code)
    classes_raw = re.findall(r'class\s*=\s*["\']([^"\']+)["\']', code)
    classes_set = set()
    for c in classes_raw:
        for part in c.split():
            if part and not part.startswith("{") and not part.startswith("var("):
                classes_set.add(part)
    script_blocks = len(re.findall(r'<script[\s>]', code))
    style_blocks = len(re.findall(r'<style[\s>]', code))
    api_calls = re.findall(r'`\$\{API_BASE\}(/[^`\']+)`', code)
    api_calls += re.findall(r'["\']\$\{API_BASE\}(/[^"\']+)["\']', code)
    api_calls = list(set(api_calls))
    return {"ids": ids[:30], "classes": sorted(classes_set)[:50], "script_blocks": script_blocks, "style_blocks": style_blocks, "api_calls": api_calls}

def parse_js_file(filepath: Path) -> dict:
    code = safe_read(filepath)
    if not code:
        return None
    return {"path": rel(filepath), "hash": hash_file(filepath), "lines": len(code.split("\n")), "functions": parse_js_functions(code, filepath)}

def parse_html_file(filepath: Path) -> dict:
    code = safe_read(filepath)
    if not code:
        return None
    return {"path": rel(filepath), "hash": hash_file(filepath), "lines": len(code.split("\n")), "structure": parse_html_structure(code, filepath), "functions": parse_js_functions(code, filepath)}

# ============================================================
# 配置解析
# ============================================================

def parse_env_example(filepath: Path) -> list[dict]:
    vars_list = []
    code = safe_read(filepath)
    for line in code.split("\n"):
        line = line.strip()
        if not line or line.startswith("# =="):
            continue
        comment = ""
        if "#" in line:
            comment = line[line.index("#") + 1:].strip()
            line = line[:line.index("#")].strip()
        if "=" in line:
            key = line.split("=")[0].strip()
            val = line.split("=")[1].strip() if len(line.split("=")) > 1 else ""
            vars_list.append({"key": key, "default": val, "desc": comment})
    return vars_list

def parse_manifest_json(filepath: Path) -> dict:
    code = safe_read(filepath)
    if not code:
        return {}
    try:
        return json.loads(code)
    except:
        return {}

# ============================================================
# 数据库模型提取
# ============================================================

def parse_database_schema(filepath: Path) -> dict:
    code = safe_read(filepath)
    tables = {}
    create_pattern = r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)\s*\((.*?)\);'
    for m in re.finditer(create_pattern, code, re.DOTALL | re.IGNORECASE):
        table_name = m.group(1)
        body = m.group(2)
        columns = []
        for col_line in body.split("\n"):
            col_line = col_line.strip().rstrip(",")
            if not col_line or col_line.startswith("--") or col_line.startswith("FOREIGN") or col_line.startswith("PRIMARY"):
                continue
            parts = col_line.split(None, 1)
            if parts:
                col_name = parts[0]
                col_type = parts[1] if len(parts) > 1 else ""
                col_type_clean = re.sub(r'\b(PRIMARY\s+KEY|NOT\s+NULL|UNIQUE|AUTOINCREMENT|DEFAULT\s+\S+)\b', '', col_type, flags=re.IGNORECASE).strip()
                columns.append({"name": col_name, "type": col_type_clean})
        tables[table_name] = columns
    return tables

# ============================================================
# Markdown 生成
# ============================================================

def gen_python_section(parsed: dict) -> str:
    lines_out = []
    lines_out.append(f"#### `{parsed['path']}` ({parsed['lines']} 行)")
    lines_out.append("")
    if parsed["routes"]:
        lines_out.append("| 方法 | 路径 | 处理函数 | 参数 |")
        lines_out.append("|------|------|----------|------|")
        for r in parsed["routes"]:
            lines_out.append(f"| {r['method']} | `{r['path']}` | `{r['handler']}()` | {r['params']} |")
        lines_out.append("")
    if parsed["classes"]:
        for cls in parsed["classes"]:
            base_info = f" (继承 `{cls['bases']}`)" if cls["bases"] else ""
            lines_out.append(f"**类 `{cls['name']}`**{base_info} — 行 {cls['line']}")
            lines_out.append("")
    if parsed["functions"]:
        lines_out.append("| 函数 | 签名 | 说明 |")
        lines_out.append("|------|------|------|")
        for fn in parsed["functions"]:
            sig = f"({fn['params']})"
            if fn["return_type"]:
                sig += f" -> {fn['return_type']}"
            doc_short = fn["doc"][:80].replace("\n", " ") if fn["doc"] else "-"
            prefix = "  \\u2b91 " if fn["is_method"] else ""
            lines_out.append(f"| {prefix}`{fn['name']}` | `{sig}` | {doc_short} |")
        lines_out.append("")
    if parsed["imports"]:
        lines_out.append("**关键依赖：**")
        for imp in parsed["imports"][:10]:
            lines_out.append(f"- `{imp}`")
        lines_out.append("")
    lines_out.append("---")
    return "\n".join(lines_out)

def gen_js_section(parsed: dict) -> str:
    lines_out = []
    lines_out.append(f"#### `{parsed['path']}` ({parsed['lines']} 行)")
    lines_out.append("")
    if parsed["functions"]:
        lines_out.append("| 函数 | 参数 | 行号 |")
        lines_out.append("|------|------|------|")
        for fn in parsed["functions"]:
            lines_out.append(f"| `{fn['name']}()` | {fn['params']} | {fn['line']} |")
        lines_out.append("")
    lines_out.append("---")
    return "\n".join(lines_out)

def gen_html_section(parsed: dict) -> str:
    lines_out = []
    lines_out.append(f"#### `{parsed['path']}` ({parsed['lines']} 行)")
    lines_out.append("")
    s = parsed["structure"]
    lines_out.append(f"- {s['script_blocks']} 个 `<script>` 块, {s['style_blocks']} 个 `<style>` 块")
    if s["api_calls"]:
        lines_out.append("- **调用的 API：**")
        for api in sorted(s["api_calls"]):
            lines_out.append(f"  - `{api}`")
    if s["ids"]:
        lines_out.append(f"- **关键 DOM ID：** {', '.join(f'`{i}`' for i in s['ids'][:20])}")
    if parsed["functions"]:
        lines_out.append("- **JS 函数：**")
        for fn in parsed["functions"][:20]:
            lines_out.append(f"  - `{fn['name']}({fn['params']})` -> 行 {fn['line']}")
    lines_out.append("")
    lines_out.append("---")
    return "\n".join(lines_out)

def gen_env_section(vars_list: list[dict]) -> str:
    lines_out = []
    lines_out.append("| 变量 | 默认值 | 说明 |")
    lines_out.append("|------|--------|------|")
    for v in vars_list:
        lines_out.append(f"| `{v['key']}` | `{v['default']}` | {v['desc']} |")
    return "\n".join(lines_out)

def gen_db_section(tables: dict) -> str:
    lines_out = []
    for table_name, columns in tables.items():
        lines_out.append(f"### `{table_name}` 表")
        lines_out.append("")
        lines_out.append("| 列名 | 类型 |")
        lines_out.append("|------|------|")
        for col in columns:
            lines_out.append(f"| `{col['name']}` | {col['type']} |")
        lines_out.append("")
    return "\n".join(lines_out)

def gen_mcp_tools_section(filepath: Path) -> str:
    code = safe_read(filepath)
    tools = []
    pattern = r'Tool\(\s*name\s*=\s*["\']([^"\']+)["\'].*?description\s*=\s*["\']([^"\']+)["\']'
    for m in re.finditer(pattern, code, re.DOTALL):
        tools.append((m.group(1), m.group(2)))
    if not tools:
        return ""
    lines_out = []
    lines_out.append("| 工具名 | 用途 |")
    lines_out.append("|--------|------|")
    for name, desc in tools:
        lines_out.append(f"| `{name}` | {desc} |")
    lines_out.append("")
    return "\n".join(lines_out)

# ============================================================
# 主流程
# ============================================================

def collect_all_files() -> dict:
    """遍历所有子项目，分类收集文件"""
    categories = {
        "backend_python": [], "backend_processing": [], "backend_endpoints": [],
        "frontend": [], "extension": [], "config": [], "root_python": [],
        "bilibili_python": [], "xiaohongshu_python": [],
        "bilibili_config": [], "xiaohongshu_config": [],
        "other": [],
    }
    # study-hub
    for fp in sorted(PROJECT_ROOT.rglob("*")):
        if fp.is_dir():
            if any(skip in fp.parts for skip in ["venv", "__pycache__", ".git", "node_modules", "data"]):
                continue
            continue
        rp = rel(fp)
        if fp.suffix == ".py":
            if "backend/endpoints" in rp:
                categories["backend_endpoints"].append(fp)
            elif "backend/processing" in rp:
                categories["backend_processing"].append(fp)
            elif "backend" in rp:
                categories["backend_python"].append(fp)
            elif fp.parent == PROJECT_ROOT:
                categories["root_python"].append(fp)
        elif fp.suffix in (".html",):
            categories["frontend"].append(fp)
        elif fp.suffix == ".js" and "extension" in rp:
            categories["extension"].append(fp)
        elif fp.name in (".env.example", "docker-compose.yml", "Dockerfile", "requirements.txt", "requirements-mcp.txt", "manifest.json"):
            categories["config"].append(fp)
        else:
            categories["other"].append(fp)

    # bilibili-mcp-server
    if BILIBILI_ROOT.exists():
        for fp in sorted(BILIBILI_ROOT.rglob("*")):
            if fp.is_dir():
                if any(skip in fp.parts for skip in ["__pycache__", ".git", "dist", ".egg-info"]):
                    continue
                continue
            if fp.suffix == ".py":
                categories["bilibili_python"].append(fp)
            elif fp.name in ("pyproject.toml", "requirements.txt", "README.md"):
                categories["bilibili_config"].append(fp)

    # xiaohongshu-mcp-server
    if XHS_ROOT.exists():
        for fp in sorted(XHS_ROOT.rglob("*")):
            if fp.is_dir():
                if any(skip in fp.parts for skip in ["__pycache__", ".git", "dist", ".egg-info"]):
                    continue
                continue
            if fp.suffix == ".py":
                categories["xiaohongshu_python"].append(fp)
            elif fp.name in ("pyproject.toml", "requirements.txt", "README.md"):
                categories["xiaohongshu_config"].append(fp)

    return categories


def generate_auto_readme() -> str:
    """生成完整的自动文档内容"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    files = collect_all_files()
    out = []
    out.append(f"<!-- 自动生成于 {now}，请勿手动编辑此区块 -->")
    out.append("")

    # === API 路由 ===
    out.append("## API 路由全览")
    out.append("")
    out.append("### 端点 (endpoints/)")
    out.append("")
    all_routes = []
    for fp in files["backend_endpoints"]:
        parsed = parse_python_file(fp)
        if parsed and parsed["routes"]:
            all_routes.extend(parsed["routes"])
    if all_routes:
        out.append("| 方法 | 路径 | 处理函数 | 关键参数 | 文件 |")
        out.append("|------|------|----------|----------|------|")
        for r in all_routes:
            out.append(f"| {r['method']} | `{r['path']}` | `{r['handler']}()` | {r['params']} | `{r['line']}` |")
        out.append("")

    # === MCP 工具 ===
    mp = PROJECT_ROOT / "mcp_server.py"
    if mp.exists():
        out.append("### MCP Server 工具（供 Claude Desktop 调用）")
        out.append("")
        tools_text = gen_mcp_tools_section(mp)
        out.append(tools_text)

    # === 数据库 ===
    db_file = PROJECT_ROOT / "backend" / "database.py"
    if db_file.exists():
        out.append("## 数据库表结构")
        out.append("")
        tables = parse_database_schema(db_file)
        out.append(gen_db_section(tables))

    # === 环境变量 ===
    env_file = PROJECT_ROOT / ".env.example"
    if env_file.exists():
        out.append("## 环境变量 (.env)")
        out.append("")
        vars_list = parse_env_example(env_file)
        out.append(gen_env_section(vars_list))
        out.append("")

    # === 后端核心 ===
    out.append("## 后端核心文件")
    out.append("")
    core_order = ["backend/main.py", "backend/ai_client.py", "backend/database.py", "backend/watcher.py"]
    for rp in core_order:
        fp = PROJECT_ROOT / rp
        if fp.exists():
            parsed = parse_python_file(fp)
            if parsed:
                out.append(gen_python_section(parsed))
    for fp in files["backend_python"]:
        if rel(fp) not in core_order:
            parsed = parse_python_file(fp)
            if parsed:
                out.append(gen_python_section(parsed))

    out.append("## 后端处理层 (processing/)")
    out.append("")
    for fp in files["backend_processing"]:
        parsed = parse_python_file(fp)
        if parsed:
            out.append(gen_python_section(parsed))

    out.append("## 后端端点层 (endpoints/)")
    out.append("")
    for fp in files["backend_endpoints"]:
        parsed = parse_python_file(fp)
        if parsed:
            out.append(gen_python_section(parsed))

    out.append("## MCP Server")
    out.append("")
    for fp in files["root_python"]:
        parsed = parse_python_file(fp)
        if parsed:
            out.append(gen_python_section(parsed))

    # === 前端 ===
    out.append("## 前端页面")
    out.append("")
    for fp in files["frontend"]:
        parsed = parse_html_file(fp)
        if parsed:
            out.append(gen_html_section(parsed))

    # === Chrome 扩展 ===
    out.append("## Chrome 扩展")
    out.append("")
    man_file = PROJECT_ROOT / "extension" / "manifest.json"
    if man_file.exists():
        manifest = parse_manifest_json(man_file)
        if manifest:
            out.append(f"### 扩展配置")
            out.append(f"- **名称**: {manifest.get('name', '')}")
            out.append(f"- **版本**: {manifest.get('version', '')}")
            out.append(f"- **权限**: {', '.join(f'`{p}`' for p in manifest.get('permissions', []))}")
            hosts = manifest.get('host_permissions', [])
            if hosts:
                out.append(f"- **Host 权限**: {', '.join(f'`{h}`' for h in hosts)}")
            out.append("")
    for fp in files["extension"]:
        parsed = parse_js_file(fp)
        if parsed:
            out.append(gen_js_section(parsed))

    # === 配置文件 ===
    out.append("## 配置文件")
    out.append("")
    for fp in files["config"]:
        if fp.name in (".env.example", "manifest.json"):
            continue
        content = safe_read(fp)
        fh = hash_file(fp)
        out.append(f"### `{rel(fp)}` ({len(content.split(chr(10)))} 行, hash: `{fh}`)")
        out.append("")
        out.append("```")
        out.append(content[:1500])
        if len(content) > 1500:
            out.append(f"\n... (截断，完整文件 {len(content)} 字符)")
        out.append("```")
        out.append("")

    # === mods/ ===
    if MODS_ROOT.exists():
        out.append("## 工具百宝箱 (mods/)")
        out.append("")
        mod_dirs = sorted([d for d in MODS_ROOT.iterdir() if d.is_dir() and not d.name.startswith(".")])
        for mod_dir in mod_dirs:
            mod_name = mod_dir.name
            mod_files = []
            for mf in sorted(mod_dir.rglob("*")):
                if mf.is_file() and not any(skip in mf.parts for skip in ["node_modules", ".git", "__pycache__", "dist", "build", ".superpowers", ".claude"]):
                    mod_files.append(mf)
            if not mod_files:
                continue
            out.append(f"### {mod_name}")
            out.append("")
            out.append("| 文件 | 行数 |")
            out.append("|------|------|")
            for mf in mod_files[:50]:
                rp = str(mf.relative_to(mod_dir)).replace("\\", "/")
                lines = len(safe_read(mf).split("\n"))
                out.append(f"| `{rp}` | {lines} |")
            if len(mod_files) > 50:
                out.append(f"| ... | 还有 {len(mod_files) - 50} 个文件 |")
            out.append("")

    # === B站 MCP Server ===
    if BILIBILI_ROOT.exists():
        out.append("## B站 MCP Server (bilibili-mcp-server/)")
        out.append("")
        for fp in files["bilibili_config"]:
            if fp.name == "pyproject.toml":
                content = safe_read(fp)
                out.append(f"### `{fp.relative_to(WORKSPACE_ROOT)}`")
                out.append("")
                out.append("```toml")
                out.append(content[:1000])
                out.append("```")
                out.append("")
        for fp in files["bilibili_python"]:
            parsed = parse_python_file(fp)
            if parsed:
                out.append(gen_python_section(parsed))

    # === 小红书 MCP Server ===
    if XHS_ROOT.exists():
        out.append("## 小红书 MCP Server (xiaohongshu-mcp-server/)")
        out.append("")
        for fp in files["xiaohongshu_config"]:
            if fp.name == "pyproject.toml":
                content = safe_read(fp)
                out.append(f"### `{fp.relative_to(WORKSPACE_ROOT)}`")
                out.append("")
                out.append("```toml")
                out.append(content[:1000])
                out.append("```")
                out.append("")
        for fp in files["xiaohongshu_python"]:
            parsed = parse_python_file(fp)
            if parsed:
                out.append(gen_python_section(parsed))

    # === 文件指纹 ===
    out.append("## 文件完整性指纹")
    out.append("")
    out.append("| 文件 | MD5 (前8位) | 行数 |")
    out.append("|------|-------------|------|")
    all_source_files = (
        files["backend_python"] + files["backend_processing"] + files["backend_endpoints"] +
        files["root_python"] + files["frontend"] + files["extension"] +
        files["bilibili_python"] + files["xiaohongshu_python"]
    )
    for fp in sorted(all_source_files, key=lambda x: str(x)):
        rp = rel(fp) if PROJECT_ROOT in fp.parents else str(fp.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
        fhash = hash_file(fp)
        flines = len(safe_read(fp).split("\n"))
        out.append(f"| `{rp}` | `{fhash}` | {flines} |")
    out.append("")
    out.append(f"<!-- 文件总数: {len(all_source_files)}, 生成时间: {now} -->")
    return "\n".join(out)


def update_readme(auto_content: str) -> bool:
    if not README_PATH.exists():
        print(f"[ERROR] README.md 不存在: {README_PATH}")
        return False
    current = safe_read(README_PATH)
    if AUTO_START in current and AUTO_END in current:
        before = current[:current.index(AUTO_START)]
        after = current[current.index(AUTO_END) + len(AUTO_END):]
        new_content = before + AUTO_START + "\n\n" + auto_content + "\n" + AUTO_END + after
    else:
        new_content = current + "\n\n" + AUTO_START + "\n\n" + auto_content + "\n" + AUTO_END + "\n"
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def generate_root_stats() -> str:
    """生成根目录 README 微型统计摘要"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    files = collect_all_files()

    # 统计后端端点
    ep_count = len(files["backend_endpoints"])
    # MCP 工具（从 mcp_server.py 提取）
    mcp_file = PROJECT_ROOT / "mcp_server.py"
    mcp_tools = 0
    if mcp_file.exists():
        mcp_content = safe_read(mcp_file)
        # 匹配 list_tools() 中返回的 Tool(...) 数量
        mcp_tools = len(re.findall(r'Tool\(', mcp_content))
    # 前端页面
    fe_count = sum(1 for f in files["frontend"] if f.name.endswith(".html"))
    # 代码总行数
    all_py = files["backend_python"] + files["backend_processing"] + files["backend_endpoints"] + files["root_python"]
    total_lines = sum(len(safe_read(f).splitlines()) for f in all_py)
    # mods 模块数
    mod_count = 0
    if MODS_ROOT.exists():
        mod_count = sum(1 for d in MODS_ROOT.iterdir() if d.is_dir() and not d.name.startswith("."))

    lines = [
        f"<!-- 自动生成于 {now}，请勿手动编辑此区块 -->",
        "",
        "## 项目实时概况",
        "",
        "| 指标 | 数值 |",
        "|:---|:---|",
        f"| 后端 API 端点 | `{ep_count}` 个 |",
        f"| MCP Server 工具 | `{mcp_tools}` 个 |",
        f"| 前端页面 | `{fe_count}` 个 |",
        f"| 工具百宝箱模块 | `{mod_count}` 个 |",
        f"| Python 代码总行数 | `{total_lines:,}` 行 |",
        f"| 自动文档更新 | `{now}` |",
        "",
        "📖 [查看完整 API 文档 →](study-hub/README.md)",
    ]
    return "\n".join(lines)


def update_root_readme() -> bool:
    """更新根目录 README 的微型统计区"""
    if not ROOT_README_PATH.exists():
        print(f"[WARN] 根目录 README 不存在: {ROOT_README_PATH}")
        return False
    current = safe_read(ROOT_README_PATH)
    stats = generate_root_stats()
    if ROOT_AUTO_START in current and ROOT_AUTO_END in current:
        before = current[:current.index(ROOT_AUTO_START)]
        after = current[current.index(ROOT_AUTO_END) + len(ROOT_AUTO_END):]
        new_content = before + ROOT_AUTO_START + "\n\n" + stats + "\n" + ROOT_AUTO_END + after
    else:
        # 默认追加到文件末尾
        new_content = current + "\n\n" + ROOT_AUTO_START + "\n\n" + stats + "\n" + ROOT_AUTO_END + "\n"
    with open(ROOT_README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def check_stale() -> bool:
    if not README_PATH.exists():
        return True
    current = safe_read(README_PATH)
    if AUTO_START not in current or AUTO_END not in current:
        return True
    auto_section = current[current.index(AUTO_START):current.index(AUTO_END)]
    files = collect_all_files()
    all_source_files = (
        files["backend_python"] + files["backend_processing"] + files["backend_endpoints"] +
        files["root_python"] + files["frontend"] + files["extension"] +
        files["bilibili_python"] + files["xiaohongshu_python"]
    )
    for fp in all_source_files:
        rp = rel(fp) if PROJECT_ROOT in fp.parents else str(fp.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
        current_hash = hash_file(fp)
        pattern = re.compile(rf'\|\s*`{re.escape(rp)}`\s*\|\s*`([a-f0-9]+)`\s*\|')
        m = pattern.search(auto_section)
        if m:
            old_hash = m.group(1)
            if old_hash != current_hash:
                return True
        else:
            return True
    if ROOT_README_PATH.exists():
        root_current = safe_read(ROOT_README_PATH)
        if ROOT_AUTO_START not in root_current or ROOT_AUTO_END not in root_current:
            return True
    return False


if __name__ == "__main__":
    import argparse, io
    parser = argparse.ArgumentParser(description="学习中枢 README 自动生成器")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if args.check:
        is_stale = check_stale()
        print("STALE: README 需要更新" if is_stale else "OK: README 是最新的")
        sys.exit(0 if not is_stale else 1)
    if args.write:
        if not check_stale():
            print("SKIP: README 已是最新, 无需更新")
            sys.exit(0)
        auto_content = generate_auto_readme()
        ok = update_readme(auto_content)
        if ok:
            root_ok = update_root_readme()
            if root_ok:
                print("OK: study-hub/README.md + 根目录 README.md 已同步更新")
            else:
                print("OK: study-hub/README.md 已更新 (根目录 README 更新失败)")
        else:
            print("ERROR: study-hub/README.md 更新失败")
        sys.exit(0 if ok else 1)
    else:
        print(generate_auto_readme())
