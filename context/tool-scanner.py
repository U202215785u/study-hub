#!/usr/bin/env python3
"""
Study-Hub 已装工具扫描器 v7.0
扫描用户已安装的 Skill 文件，提取触发域声明，生成触发域索引。

扫描路径：
- .agents/skills/          # 项目本地
- ~/.agents/skills/        # 用户全局（如果可访问）

输出：触发域索引 JSON
"""

import os
import re
import json
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "project-memory" / ".tool-index.json"

def extract_frontmatter(content: str) -> dict:
    """提取 Markdown frontmatter。"""
    fm = {}
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if match:
        for line in match.group(1).split("\n"):
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val.startswith("[") and val.endswith("]"):
                    val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
                fm[key] = val
    return fm

def extract_trigger_domain(content: str) -> Optional[list[str]]:
    """从内容中提取触发域声明。"""
    # 尝试 frontmatter
    fm = extract_frontmatter(content)
    if "触发域" in fm:
        return fm["触发域"]

    # 尝试正文中的触发域声明
    match = re.search(r'触发域:\s*\[([^\]]+)\]', content)
    if match:
        return [v.strip() for v in match.group(1).split(",")]

    # 从 h2 标题推断
    match = re.search(r'领域[：:](.*?)(?:\n|$)', content)
    if match:
        return [match.group(1).strip()]

    return None

def extract_skill_name(content: str, filename: str) -> str:
    """提取 Skill 名称。"""
    fm = extract_frontmatter(content)
    if "name" in fm:
        return fm["name"]

    # 从文件名推断
    name = filename.replace(".md", "").replace("-", " ").replace("_", " ")
    return name

def scan_skills_dir(directory: Path) -> list[dict]:
    """扫描一个 Skill 目录。"""
    skills = []
    if not directory.exists():
        return skills

    for filepath in directory.rglob("*.md"):
        if filepath.name == "SKILL.md" or filepath.suffix == ".md":
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                name = extract_skill_name(content, filepath.stem)
                trigger_domain = extract_trigger_domain(content)

                # 如果没有触发域，从描述中提取关键词作为降级方案
                if not trigger_domain:
                    title_match = re.search(r'^#\s+(.*?)$', content, re.MULTILINE)
                    desc = title_match.group(1) if title_match else name
                    trigger_domain = [desc.lower()]

                skills.append({
                    "name": name,
                    "file": str(filepath.relative_to(directory)),
                    "trigger_domain": trigger_domain,
                    "is_builtin": "butler" in filepath.stem.lower()
                })
            except Exception:
                pass

    return skills

def build_trigger_index(skills: list[dict]) -> dict:
    """构建触发域 → Skill 的反向索引。"""
    index = {}
    for skill in skills:
        for domain in skill.get("trigger_domain", []):
            domain_key = domain.lower().strip()
            if domain_key not in index:
                index[domain_key] = []
            index[domain_key].append(skill["name"])
    return index

def main():
    local_skills = PROJECT_ROOT / ".agents" / "skills"
    global_skills = Path.home() / ".agents" / "skills"

    all_skills = []
    all_skills.extend(scan_skills_dir(local_skills))
    all_skills.extend(scan_skills_dir(global_skills))

    # 过滤掉管家文件
    tools = [s for s in all_skills if not s.get("is_builtin")]

    trigger_index = build_trigger_index(tools)

    output = {
        "scan_time": __import__("datetime").datetime.now().isoformat(),
        "total_tools": len(tools),
        "tools": tools,
        "trigger_index": trigger_index
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2))

    print(f"扫描完成：{len(tools)} 个工具")
    print(f"触发域索引：{len(trigger_index)} 个关键词")
    print(f"输出：{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
