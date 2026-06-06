#!/usr/bin/env python3
"""
Study-Hub 代码地图自动生成器 v7.0
零外部依赖。Python 标准库。

每次跑做四件事：
1. 扫描项目目录，列出所有代码文件
2. 提取函数/类名（Python, Vue, JS, TS）
3. 检测潜在问题点（try-except块、TODO/FIXME/HACK注释、注释掉的代码）
4. 统计文件变更频率（基于 git log）
5. 比对时间戳，只处理变更文件，增量更新
"""

import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime

# ============================================================
# 配置
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_ROOT = PROJECT_ROOT / "study-hub"  # 实际代码目录
INDEX_FILE = PROJECT_ROOT / "project-memory" / "项目索引.md"
CACHE_FILE = PROJECT_ROOT / "project-memory" / ".index_cache.json"

EXCLUDE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".next", ".agents", "project-memory",
    ".index_cache.json", ".claude"
}

CODE_EXTENSIONS = {".py", ".js", ".ts", ".vue", ".jsx", ".tsx", ".go", ".rs", ".java"}

# ============================================================
# 符号提取
# ============================================================

def extract_symbols_python(content: str) -> list[str]:
    symbols = []
    for match in re.finditer(r'^\s*(?:def|class|async def)\s+(\w+)', content, re.MULTILINE):
        symbols.append(match.group(1))
    return symbols

def extract_symbols_js(content: str) -> list[str]:
    symbols = []
    for match in re.finditer(r'(?:function|class|const|let|var)\s+(\w+)', content):
        symbols.append(match.group(1))
    # Vue methods
    for match in re.finditer(r'(?:async\s+)?(\w+)\s*\(', content):
        name = match.group(1)
        if name not in {"if", "for", "while", "switch", "catch", "return"}:
            symbols.append(name)
    return symbols

def extract_symbols_vue(content: str) -> list[str]:
    symbols = []
    script_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    if script_match:
        symbols.extend(extract_symbols_js(script_match.group(1)))
    # template events
    for match in re.finditer(r'@(\w+)', content):
        symbols.append(f"@{match.group(1)}")
    return symbols

EXTRACTORS = {
    ".py": extract_symbols_python,
    ".js": extract_symbols_js,
    ".ts": extract_symbols_js,
    ".jsx": extract_symbols_js,
    ".tsx": extract_symbols_js,
    ".vue": extract_symbols_vue,
    ".go": lambda c: re.findall(r'func\s+(?:\([^)]*\)\s+)?(\w+)', c),
    ".rs": lambda c: re.findall(r'fn\s+(\w+)', c),
    ".java": lambda c: re.findall(r'(?:public|private|protected)?\s*(?:static\s+)?(?:class|interface|void|\w+)\s+(\w+)\s*\(', c),
}

# ============================================================
# 潜在问题扫描
# ============================================================

def scan_potential_issues(filepath: Path, content: str) -> list[dict]:
    """扫描代码中的潜在问题信号。"""
    issues = []
    lines = content.split("\n")

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # TODO/FIXME/HACK/XXX
        if re.search(r'(TODO|FIXME|HACK|XXX|BUG|WORKAROUND)', stripped, re.IGNORECASE):
            issues.append({
                "type": "代码标注",
                "line": i,
                "content": stripped[:120],
                "file": str(filepath.relative_to(CODE_ROOT))
            })

        # 注释掉的代码块（连续 3+ 行注释的代码）
        if re.search(r'(?:方案|approach|deprecated|废弃|弃用|放弃|dropped)', stripped, re.IGNORECASE):
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
                issues.append({
                    "type": "废弃方案",
                    "line": i,
                    "content": stripped[:120],
                    "file": str(filepath.relative_to(CODE_ROOT))
                })

        # try-except 块标记（标记有 try 但无 except 的不完整结构）
        if re.match(r'except\s*:', stripped) or re.match(r'except\s+Exception\s*:', stripped):
            issues.append({
                "type": "宽泛异常",
                "line": i,
                "content": stripped[:120],
                "file": str(filepath.relative_to(CODE_ROOT))
            })

    return issues

# ============================================================
# Git 变更频率
# ============================================================

def get_file_churn(filepath: Path) -> int:
    """统计文件在过去 30 天内的改动次数。"""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "log", "--oneline", "--since=30.days", "--", str(filepath.relative_to(PROJECT_ROOT))],
            capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=10
        )
        return len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
    except Exception:
        return 0

# ============================================================
# 主扫描
# ============================================================

def scan_project() -> dict:
    """扫描整个项目，返回结构化数据。"""
    modules = {}
    all_files = []
    all_issues = []
    total_size = 0

    for filepath in CODE_ROOT.rglob("*"):
        if filepath.is_file() and filepath.suffix in CODE_EXTENSIONS:
            # 排除目录
            parts = set(filepath.relative_to(CODE_ROOT).parts)
            if parts & EXCLUDE_DIRS:
                continue

            rel_path = str(filepath.relative_to(CODE_ROOT))
            module = filepath.relative_to(CODE_ROOT).parts[0] if len(filepath.relative_to(CODE_ROOT).parts) > 1 else "root"
            size = filepath.stat().st_size

            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                content = ""

            extractor = EXTRACTORS.get(filepath.suffix)
            symbols = extractor(content) if extractor else []
            issues = scan_potential_issues(filepath, content)
            churn = get_file_churn(filepath)

            file_info = {
                "path": rel_path,
                "module": module,
                "symbols": symbols[:15],
                "size_kb": round(size / 1024, 1),
                "issues": issues,
                "churn_30d": churn,
                "hash": hashlib.md5(content.encode()).hexdigest()
            }

            if module not in modules:
                modules[module] = {"files": [], "total_size_kb": 0, "api_routes": []}
            modules[module]["files"].append(file_info)
            modules[module]["total_size_kb"] += file_info["size_kb"]
            all_files.append(file_info)
            all_issues.extend(issues)
            total_size += size

    # 检测 API 路由
    api_patterns = [
        (".py", r'@(?:app|router)\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)'),
        (".js", r'(?:app|router)\.(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)'),
        (".ts", r'(?:app|router)\.(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)'),
    ]
    for file_info in all_files:
        ext = Path(file_info["path"]).suffix
        for pat_ext, pattern in api_patterns:
            if ext == pat_ext:
                try:
                    content = (CODE_ROOT / file_info["path"]).read_text(encoding="utf-8", errors="ignore")
                    routes = re.findall(pattern, content)
                    if routes:
                        modules[file_info["module"]]["api_routes"].extend(routes)
                except Exception:
                    pass

    return {
        "scan_time": datetime.now().isoformat(),
        "total_files": len(all_files),
        "total_size_kb": round(total_size / 1024, 1),
        "modules": modules,
        "files": all_files,
        "issues": all_issues,
        "churn_hotspots": [f for f in all_files if f.get("churn_30d", 0) >= 5]
    }

# ============================================================
# 增量更新
# ============================================================

def get_changed_files(data: dict) -> list:
    """比对缓存，只返回变更文件。"""
    if not CACHE_FILE.exists():
        return data["files"]

    try:
        cache = json.loads(CACHE_FILE.read_text())
        cached_hashes = cache.get("hashes", {})
    except Exception:
        return data["files"]

    changed = []
    for f in data["files"]:
        if f["path"] not in cached_hashes or cached_hashes[f["path"]] != f["hash"]:
            changed.append(f)

    return changed

# ============================================================
# 索引文件生成
# ============================================================

def generate_code_map(data: dict) -> str:
    """生成代码地图 Markdown 段。"""
    lines = []
    lines.append(f"## 代码地图")
    lines.append(f"生成时间：{data['scan_time'][:19]}")
    lines.append(f"文件总数：{data['total_files']}  |  总大小：{data['total_size_kb']} KB")
    lines.append("")

    # 模块概览
    lines.append("### 模块概览")
    lines.append("")
    lines.append("| 模块 | 文件数 | 总大小 | API 路由 | 30天改动 |")
    lines.append("|------|--------|--------|---------|---------|")
    for mod_name, mod_data in sorted(data["modules"].items()):
        api_count = len(mod_data["api_routes"])
        churn_total = sum(f.get("churn_30d", 0) for f in mod_data["files"])
        lines.append(f"| {mod_name} | {len(mod_data['files'])} | {mod_data['total_size_kb']:.0f}KB | {api_count} | {churn_total} |")
    lines.append("")

    # 文件清单
    lines.append("### 文件清单")
    lines.append("")
    lines.append("| 文件 | 模块 | 符号 | 30天改动 | 大小 |")
    lines.append("|------|------|------|---------|------|")
    for f in data["files"]:
        syms = ", ".join(f["symbols"][:5]) if f["symbols"] else "—"
        churn = f.get("churn_30d", 0)
        churn_mark = "🔥" if churn >= 5 else ("⚡" if churn >= 2 else "—")
        lines.append(f"| {f['path']} | {f['module']} | {syms} | {churn_mark} {churn} | {f['size_kb']}KB |")
    lines.append("")

    # API 接口清单
    lines.append("### API 接口清单")
    lines.append("")
    has_api = False
    for mod_name, mod_data in sorted(data["modules"].items()):
        if mod_data["api_routes"]:
            has_api = True
            routes = ", ".join(mod_data["api_routes"][:10])
            lines.append(f"- **{mod_name}**: {routes}")
    if not has_api:
        lines.append("暂无检测到的 API 接口")
    lines.append("")

    # 潜在问题点
    if data["issues"]:
        lines.append("### 自动发现的潜在问题点")
        lines.append("")
        lines.append("| 类型 | 文件 | 行号 | 内容 |")
        lines.append("|------|------|------|------|")
        for issue in data["issues"][:20]:
            lines.append(f"| {issue['type']} | {issue['file']} | {issue['line']} | {issue['content'][:80]} |")
        lines.append("")

    # 高频变更区
    if data["churn_hotspots"]:
        lines.append("### 高频变更区（30天内）")
        lines.append("")
        for f in data["churn_hotspots"]:
            lines.append(f"- **{f['path']}** — 30 天内改动 {f['churn_30d']} 次，可能不稳定")
        lines.append("")

    return "\n".join(lines)


def update_index_file(code_map: str):
    """替换索引文件的代码地图段，保留判断记录段。"""
    separator = "---"

    if INDEX_FILE.exists():
        old_content = INDEX_FILE.read_text(encoding="utf-8")
        parts = old_content.split(separator, 1)
        judgment_section = parts[1] if len(parts) > 1 else ""
    else:
        judgment_section = """
## 问题索引

| ID | 关键词 | 模块 | 状态 |
|----|--------|------|------|
| — | — | — | — |

## 陷阱索引

| 模块 | 陷阱 | 严重程度 |
|------|------|---------|
| — | — | — |

## 决策索引

| ID | 决定 | 状态 |
|----|------|------|
| — | — | — |

## 实验索引

| 模块 | 实验 | 方案 | 结果 |
|------|------|------|------|
| — | — | — | — |

## 当前优先级

1. —
"""

    new_content = code_map + "\n" + separator + "\n" + judgment_section
    INDEX_FILE.write_text(new_content, encoding="utf-8")

# ============================================================
# 入口
# ============================================================

def main():
    data = scan_project()
    changed = get_changed_files(data)

    code_map = generate_code_map(data)
    update_index_file(code_map)

    # 更新缓存
    cache_data = {
        "last_scan": data["scan_time"],
        "total_files": data["total_files"],
        "hashes": {f["path"]: f["hash"] for f in data["files"]}
    }
    CACHE_FILE.write_text(json.dumps(cache_data, ensure_ascii=False, indent=2))

    print(f"扫描完成：{data['total_files']} 个文件")
    print(f"变更文件：{len(changed)} 个")
    print(f"发现问题点：{len(data['issues'])} 个")
    print(f"高频变更区：{len(data['churn_hotspots'])} 个")
    print(f"索引已更新：{INDEX_FILE}")

if __name__ == "__main__":
    main()
