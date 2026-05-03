#!/usr/bin/env python3
"""
学习中枢 README 自动生成器

遍历项目所有源文件，提取每个函数、类、API 路由、数据模型、
配置项、HTML 结构、JS 函数，生成超详细 README。

用法: python generate_readme.py [--check] [--write]

  --check   仅检查 README 是否需要更新（退出码 0=最新, 1=过期）
  --write   写入 README.md（默认仅打印到 stdout）
  --stdout  输出到 stdout（默认行为，没有 --write 时）

设计原则：
  - 纯静态分析，不执行任何代码
  - 每个文件生成一个独立的文档区块
  - AUTO 标记之间的内容会被覆写，之外的手动内容保留
"""

import os, sys, re, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).resolve().parent  # .claude/scripts/
WORKSPACE_ROOT = SCRIPT_DIR.parent.parent  # study web/
# 项目代码在 study-hub/ 子目录下
PROJECT_ROOT = WORKSPACE_ROOT / "study-hub"
README_PATH = PROJECT_ROOT / "README.md"
AUTO_START = "<!-- AUTO-GENERATED-START -->"
AUTO_END = "<!-- AUTO-GENERATED-END -->"

# ============================================================
# 工具函数
# ============================================================

def rel(path: Path) -> str:
    """返回相对于 study-hub/ 的路径"""
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")

def safe_read(path: Path) -> str:
    """安全读取文件，出错返回空字符串"""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""

def hash_file(path: Path) -> str:
    """文件内容的 MD5 哈希"""
    content = safe_read(path)
    return hashlib.md5(content.encode()).hexdigest()[:8]

# ============================================================
# Python 文件解析
# ============================================================

def parse_python_functions(code: str, filepath: Path) -> list[dict]:
    """提取所有函数/方法签名及 docstring"""
    funcs = []
    # 匹配 def 函数名(参数)
    pattern = r'^\s*(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\S+))?\s*:'
    lines = code.split("\n")

    for i, line in enumerate(lines):
        m = re.match(pattern, line)
        if not m:
            continue

        # 跳过私有方法（_开头，但 __init__ 保留）
        name = m.group(1)
        if name.startswith("_") and name != "__init__":
            continue

        # 提取 docstring
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

        # 判断是函数还是方法
        indent = len(line) - len(line.lstrip())
        is_method = indent > 0

        # 提取装饰器
        decorators = []
        k = i - 1
        while k >= 0 and lines[k].strip().startswith("@"):
            decorators.append(lines[k].strip())
            k -= 1
        decorators.reverse()

        funcs.append({
            "name": name,
            "params": m.group(2).strip(),
            "return_type": m.group(3) or "",
            "doc": docstring[:200] if docstring else "",
            "decorators": decorators,
            "is_method": is_method,
            "line": i + 1,  # 1-indexed in output
        })

    return funcs


def parse_python_classes(code: str, filepath: Path) -> list[dict]:
    """提取所有类定义"""
    classes = []
    pattern = r'^\s*class\s+(\w+)\s*(?:\(([^)]*)\))?\s*:'
    lines = code.split("\n")

    for i, line in enumerate(lines):
        m = re.match(pattern, line)
        if not m:
            continue
        classes.append({
            "name": m.group(1),
            "bases": m.group(2) or "",
            "line": i + 1,
        })

    return classes


def parse_fastapi_routes(code: str, filepath: Path) -> list[dict]:
    """提取 FastAPI 路由定义"""
    routes = []
    # @router.get/post/put/delete/patch("/path")
    route_pattern = r'@(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
    lines = code.split("\n")

    for i, line in enumerate(lines):
        m = re.search(route_pattern, line)
        if not m:
            continue

        method = m.group(1).upper()
        path = m.group(2)

        # 找函数名（下一行或下几行的 def）
        func_name = ""
        params = ""
        for j in range(i + 1, min(i + 8, len(lines))):
            fm = re.match(r'^\s*(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)', lines[j])
            if fm:
                func_name = fm.group(1)
                params_raw = fm.group(2)
                # 提取关键参数（去掉类型注解和默认值）
                key_params = []
                for p in params_raw.split(","):
                    p = p.strip()
                    if p and p != "self":
                        # 取参数名（冒号前的部分）
                        pname = p.split(":")[0].strip()
                        key_params.append(pname)
                params = ", ".join(key_params)
                break

        routes.append({
            "method": method,
            "path": path,
            "handler": func_name,
            "params": params,
            "line": i + 1,
        })

    return routes


def parse_python_imports(code: str, filepath: Path) -> list[str]:
    """提取关键 imports（只保留项目内部和重要第三方）"""
    imports = []
    internal_prefixes = ["endpoints", "processing", "ai_client", "database", "watcher"]
    key_third_party = ["fastapi", "chromadb", "httpx", "watchdog", "pymupdf", "sentence_transformers", "uvicorn"]

    for line in code.split("\n"):
        line = line.strip()
        # from X import Y
        m = re.match(r'^from\s+(\S+)\s+import\s+(.+)$', line)
        if m:
            module = m.group(1)
            items = m.group(2)
            # 只保留项目内部或关键第三方
            if any(module.startswith(p) for p in internal_prefixes + key_third_party):
                imports.append(f"from {module} import {items}")
            continue

        # import X
        m = re.match(r'^import\s+(.+)$', line)
        if m:
            module = m.group(1)
            if any(module.startswith(p) for p in key_third_party):
                imports.append(f"import {module}")

    return imports


def parse_python_file(filepath: Path) -> dict:
    """完整解析单个 Python 文件"""
    code = safe_read(filepath)
    if not code:
        return None

    return {
        "path": rel(filepath),
        "hash": hash_file(filepath),
        "lines": len(code.split("\n")),
        "classes": parse_python_classes(code, filepath),
        "functions": parse_python_functions(code, filepath),
        "routes": parse_fastapi_routes(code, filepath),
        "imports": parse_python_imports(code, filepath),
    }


# ============================================================
# JavaScript / HTML 文件解析
# ============================================================

def parse_js_functions(code: str, filepath: Path) -> list[dict]:
    """提取 JS 函数定义"""
    funcs = []
    # function name() / async function name() / const name = () => / const name = async () =>
    patterns = [
        r'^\s*(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
        r'^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>',
    ]
    lines = code.split("\n")

    for i, line in enumerate(lines):
        for pat in patterns:
            m = re.match(pat, line)
            if m:
                funcs.append({
                    "name": m.group(1),
                    "params": m.group(2).strip(),
                    "line": i + 1,
                })
                break

    return funcs


def parse_html_structure(code: str, filepath: Path) -> dict:
    """提取 HTML 结构概要"""
    # 提取 id 属性
    ids = re.findall(r'id\s*=\s*["\']([^"\']+)["\']', code)
    # 提取 class 属性（去重）
    classes_raw = re.findall(r'class\s*=\s*["\']([^"\']+)["\']', code)
    classes_set = set()
    for c in classes_raw:
        for part in c.split():
            if part and not part.startswith("{") and not part.startswith("var("):
                classes_set.add(part)

    # 提取 <script> 块数量
    script_blocks = len(re.findall(r'<script[\s>]', code))
    # 提取 <style> 块数量
    style_blocks = len(re.findall(r'<style[\s>]', code))
    # 提取 API 调用 (fetch 目标)
    api_calls = re.findall(r'`\$\{API_BASE\}(/[^`\']+)`', code)
    api_calls += re.findall(r'["\']\$\{API_BASE\}(/[^"\']+)["\']', code)
    api_calls = list(set(api_calls))

    return {
        "ids": ids[:30],  # 最多 30 个 id
        "classes": sorted(classes_set)[:50],  # 最多 50 个 class
        "script_blocks": script_blocks,
        "style_blocks": style_blocks,
        "api_calls": api_calls,
    }


def parse_js_file(filepath: Path) -> dict:
    """解析单个 JS 文件"""
    code = safe_read(filepath)
    if not code:
        return None

    return {
        "path": rel(filepath),
        "hash": hash_file(filepath),
        "lines": len(code.split("\n")),
        "functions": parse_js_functions(code, filepath),
    }


def parse_html_file(filepath: Path) -> dict:
    """解析单个 HTML 文件"""
    code = safe_read(filepath)
    if not code:
        return None

    return {
        "path": rel(filepath),
        "hash": hash_file(filepath),
        "lines": len(code.split("\n")),
        "structure": parse_html_structure(code, filepath),
        "functions": parse_js_functions(code, filepath),
    }


# ============================================================
# 配置文件解析
# ============================================================

def parse_env_example(filepath: Path) -> list[dict]:
    """解析 .env.example 中的环境变量"""
    vars_list = []
    code = safe_read(filepath)
    for line in code.split("\n"):
        line = line.strip()
        if not line or line.startswith("# =="):
            continue
        # 提取注释
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
    """解析 Chrome 扩展 manifest.json"""
    code = safe_read(filepath)
    if not code:
        return {}
    try:
        return json.loads(code)
    except:
        return {}


def parse_docker_compose(filepath: Path) -> dict:
    """解析 docker-compose.yml（简易版）"""
    code = safe_read(filepath)
    info = {"services": [], "volumes": []}
    for line in code.split("\n"):
        if "ports:" in line:
            info["ports"] = line.split(":")[-1].strip().split('"')[0] if ':' in line else ""
        if "image:" in line or "build:" in line:
            pass
    return info


# ============================================================
# 数据库模型提取
# ============================================================

def parse_database_schema(filepath: Path) -> dict:
    """从 database.py 提取表结构"""
    code = safe_read(filepath)
    tables = {}

    # 匹配 CREATE TABLE IF NOT EXISTS xxx (...)
    create_pattern = r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)\s*\((.*?)\);'
    for m in re.finditer(create_pattern, code, re.DOTALL | re.IGNORECASE):
        table_name = m.group(1)
        body = m.group(2)
        columns = []
        for col_line in body.split("\n"):
            col_line = col_line.strip().rstrip(",")
            if not col_line or col_line.startswith("--") or col_line.startswith("FOREIGN") or col_line.startswith("PRIMARY"):
                continue
            # 提取列名和类型
            parts = col_line.split(None, 1)
            if parts:
                col_name = parts[0]
                col_type = parts[1] if len(parts) > 1 else ""
                # 去掉约束关键字
                col_type_clean = re.sub(r'\b(PRIMARY\s+KEY|NOT\s+NULL|UNIQUE|AUTOINCREMENT|DEFAULT\s+\S+)\b', '', col_type, flags=re.IGNORECASE).strip()
                columns.append({"name": col_name, "type": col_type_clean})
        tables[table_name] = columns

    return tables


# ============================================================
# Markdown 生成
# ============================================================

def gen_python_section(parsed: dict) -> str:
    """生成单个 Python 文件的文档"""
    lines_out = []
    lines_out.append(f"#### `{parsed['path']}` ({parsed['lines']} 行)")
    lines_out.append("")

    # 路由
    if parsed["routes"]:
        lines_out.append("| 方法 | 路径 | 处理函数 | 参数 |")
        lines_out.append("|------|------|----------|------|")
        for r in parsed["routes"]:
            lines_out.append(f"| {r['method']} | `{r['path']}` | `{r['handler']}()` | {r['params']} |")
        lines_out.append("")

    # 类
    if parsed["classes"]:
        for cls in parsed["classes"]:
            base_info = f" (继承 `{cls['bases']}`)" if cls["bases"] else ""
            lines_out.append(f"**类 `{cls['name']}`**{base_info} — 行 {cls['line']}")
            lines_out.append("")

    # 函数
    if parsed["functions"]:
        lines_out.append("| 函数 | 签名 | 说明 |")
        lines_out.append("|------|------|------|")
        for fn in parsed["functions"]:
            sig = f"({fn['params']})"
            if fn["return_type"]:
                sig += f" -> {fn['return_type']}"
            doc_short = fn["doc"][:80].replace("\n", " ") if fn["doc"] else "-"
            prefix = "  ⮑ " if fn["is_method"] else ""
            lines_out.append(f"| {prefix}`{fn['name']}` | `{sig}` | {doc_short} |")
        lines_out.append("")

    # 关键 import
    if parsed["imports"]:
        lines_out.append("**关键依赖：**")
        for imp in parsed["imports"][:10]:
            lines_out.append(f"- `{imp}`")
        lines_out.append("")

    lines_out.append("---")
    return "\n".join(lines_out)


def gen_js_section(parsed: dict) -> str:
    """生成单个 JS 文件的文档"""
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
    """生成单个 HTML 文件的文档"""
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
            lines_out.append(f"  - `{fn['name']}({fn['params']})` → 行 {fn['line']}")

    lines_out.append("")
    lines_out.append("---")
    return "\n".join(lines_out)


def gen_env_section(vars_list: list[dict]) -> str:
    """生成环境变量文档"""
    lines_out = []
    lines_out.append("| 变量 | 默认值 | 说明 |")
    lines_out.append("|------|--------|------|")
    for v in vars_list:
        lines_out.append(f"| `{v['key']}` | `{v['default']}` | {v['desc']} |")
    return "\n".join(lines_out)


def gen_db_section(tables: dict) -> str:
    """生成数据库表文档"""
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
    """生成 MCP 工具清单"""
    code = safe_read(filepath)
    tools = []
    # 匹配 Tool(name="xxx", description="xxx")
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
    """遍历项目，分类收集所有文件"""
    categories = {
        "backend_python": [],  # backend/*.py
        "backend_processing": [],  # backend/processing/*.py
        "backend_endpoints": [],  # backend/endpoints/*.py
        "frontend": [],  # frontend/*.html
        "extension": [],  # extension/*.js
        "config": [],  # .env.example, docker-compose.yml, etc.
        "root_python": [],  # mcp_server.py
        "other": [],
    }

    for filepath in sorted(PROJECT_ROOT.rglob("*")):
        if filepath.is_dir():
            # 跳过虚拟环境和缓存
            if any(skip in filepath.parts for skip in ["venv", "__pycache__", ".git", "node_modules", "data"]):
                continue
            continue

        rel_path = rel(filepath)

        if filepath.suffix == ".py":
            if "backend/endpoints" in rel_path:
                categories["backend_endpoints"].append(filepath)
            elif "backend/processing" in rel_path:
                categories["backend_processing"].append(filepath)
            elif "backend" in rel_path:
                categories["backend_python"].append(filepath)
            elif filepath.parent == PROJECT_ROOT:
                categories["root_python"].append(filepath)

        elif filepath.suffix in (".html",):
            categories["frontend"].append(filepath)

        elif filepath.suffix == ".js" and "extension" in rel_path:
            categories["extension"].append(filepath)

        elif filepath.name in (".env.example", "docker-compose.yml", "Dockerfile", "requirements.txt", "requirements-mcp.txt", "manifest.json"):
            categories["config"].append(filepath)

        else:
            categories["other"].append(filepath)

    return categories


def generate_auto_readme() -> str:
    """生成完整的自动文档内容"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    files = collect_all_files()

    out = []
    out.append(f"<!-- 自动生成于 {now}，请勿手动编辑此区块 -->")
    out.append("")

    # ==================== 后端 API 路由 ====================
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

    # ==================== MCP 工具 ====================
    mp = PROJECT_ROOT / "mcp_server.py"
    if mp.exists():
        out.append("### MCP Server 工具（供 Claude Desktop 调用）")
        out.append("")
        tools_text = gen_mcp_tools_section(mp)
        out.append(tools_text)

    # ==================== 数据库 ====================
    db_file = PROJECT_ROOT / "backend" / "database.py"
    if db_file.exists():
        out.append("## 数据库表结构")
        out.append("")
        tables = parse_database_schema(db_file)
        out.append(gen_db_section(tables))

    # ==================== 环境变量 ====================
    env_file = PROJECT_ROOT / ".env.example"
    if env_file.exists():
        out.append("## 环境变量 (.env)")
        out.append("")
        vars_list = parse_env_example(env_file)
        out.append(gen_env_section(vars_list))
        out.append("")

    # ==================== 后端核心文件 ====================
    out.append("## 后端核心文件")
    out.append("")

    core_order = ["backend/main.py", "backend/ai_client.py", "backend/database.py", "backend/watcher.py"]
    for rel_path in core_order:
        fp = PROJECT_ROOT / rel_path
        if not fp.exists():
            continue
        parsed = parse_python_file(fp)
        if parsed:
            out.append(gen_python_section(parsed))

    # 其余后端文件
    for fp in files["backend_python"]:
        if rel(fp) not in core_order:
            parsed = parse_python_file(fp)
            if parsed:
                out.append(gen_python_section(parsed))

    # ==================== 处理层 ====================
    out.append("## 后端处理层 (processing/)")
    out.append("")
    for fp in files["backend_processing"]:
        parsed = parse_python_file(fp)
        if parsed:
            out.append(gen_python_section(parsed))

    # ==================== 端点层 ====================
    out.append("## 后端端点层 (endpoints/)")
    out.append("")
    for fp in files["backend_endpoints"]:
        parsed = parse_python_file(fp)
        if parsed:
            out.append(gen_python_section(parsed))

    # ==================== MCP Server ====================
    out.append("## MCP Server")
    out.append("")
    for fp in files["root_python"]:
        parsed = parse_python_file(fp)
        if parsed:
            out.append(gen_python_section(parsed))

    # ==================== 前端页面 ====================
    out.append("## 前端页面")
    out.append("")
    for fp in files["frontend"]:
        parsed = parse_html_file(fp)
        if parsed:
            out.append(gen_html_section(parsed))

    # ==================== Chrome 扩展 ====================
    out.append("## Chrome 扩展")
    out.append("")

    # manifest.json
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

    # ==================== 配置文件 ====================
    out.append("## 配置文件")
    out.append("")
    for fp in files["config"]:
        if fp.name == ".env.example":
            continue  # 已在上方环境变量章节处理
        if fp.name == "manifest.json":
            continue  # 已在扩展章节处理

        content = safe_read(fp)
        file_hash = hash_file(fp)
        out.append(f"### `{rel(fp)}` ({len(content.split(chr(10)))} 行, hash: `{file_hash}`)")
        out.append("")
        out.append("```")
        out.append(content[:1500])  # 最多 1500 字符
        if len(content) > 1500:
            out.append(f"\n... (截断，完整文件 {len(content)} 字符)")
        out.append("```")
        out.append("")

    # ==================== 文件指纹（用于检测变更） ====================
    out.append("## 文件完整性指纹")
    out.append("")
    out.append("| 文件 | MD5 (前8位) | 行数 |")
    out.append("|------|-------------|------|")

    all_source_files = (
        files["backend_python"] + files["backend_processing"] + files["backend_endpoints"] +
        files["root_python"] + files["frontend"] + files["extension"]
    )
    for fp in sorted(all_source_files, key=lambda x: rel(x)):
        rp = rel(fp)
        fhash = hash_file(fp)
        flines = len(safe_read(fp).split("\n"))
        out.append(f"| `{rp}` | `{fhash}` | {flines} |")

    out.append("")
    out.append(f"<!-- 文件总数: {len(all_source_files)}, 生成时间: {now} -->")

    return "\n".join(out)


def update_readme(auto_content: str) -> bool:
    """将自动内容写入 README.md 的 AUTO 标记区域"""
    if not README_PATH.exists():
        print(f"[ERROR] README.md 不存在: {README_PATH}")
        return False

    current = safe_read(README_PATH)

    if AUTO_START in current and AUTO_END in current:
        # 替换 AUTO 区域
        before = current[:current.index(AUTO_START)]
        after = current[current.index(AUTO_END) + len(AUTO_END):]
        new_content = before + AUTO_START + "\n\n" + auto_content + "\n" + AUTO_END + after
    else:
        # 追加 AUTO 区域
        new_content = current + "\n\n" + AUTO_START + "\n\n" + auto_content + "\n" + AUTO_END + "\n"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def check_stale() -> bool:
    """检查 README 是否过期（AUTO 区域是否存在且 hash 匹配）"""
    if not README_PATH.exists():
        return True

    current = safe_read(README_PATH)
    if AUTO_START not in current or AUTO_END not in current:
        return True

    # 检查是否有文件变更：对比 AUTO 区域中的文件指纹和当前实际指纹
    auto_section = current[current.index(AUTO_START):current.index(AUTO_END)]

    # 收集当前所有源文件的 hash
    files = collect_all_files()
    all_source_files = (
        files["backend_python"] + files["backend_processing"] + files["backend_endpoints"] +
        files["root_python"] + files["frontend"] + files["extension"]
    )

    for fp in all_source_files:
        rp = rel(fp)
        current_hash = hash_file(fp)
        # 在 AUTO 区域中查找这个文件的 hash
        pattern = re.compile(rf'\|\s*`{re.escape(rp)}`\s*\|\s*`([a-f0-9]+)`\s*\|')
        m = pattern.search(auto_section)
        if m:
            old_hash = m.group(1)
            if old_hash != current_hash:
                return True
        else:
            # 新文件，不在旧 README 中
            return True

    return False


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="学习中枢 README 自动生成器")
    parser.add_argument("--check", action="store_true", help="检查 README 是否过期")
    parser.add_argument("--write", action="store_true", help="写入 README.md")
    parser.add_argument("--stdout", action="store_true", help="输出到 stdout")
    args = parser.parse_args()

    # 解决 Windows GBK 编码问题
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    if args.check:
        is_stale = check_stale()
        if is_stale:
            print("STALE: README 需要更新")
        else:
            print("OK: README 是最新的")
        sys.exit(0 if not is_stale else 1)

    if args.write:
        if not check_stale():
            print("SKIP: README 已是最新, 无需更新")
            sys.exit(0)
        auto_content = generate_auto_readme()
        ok = update_readme(auto_content)
        if ok:
            print("OK: README.md 已更新")
        else:
            print("ERROR: 更新失败")
            sys.exit(1)
    else:
        auto_content = generate_auto_readme()
        print(auto_content)
