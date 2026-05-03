"""
Evolution system file I/O.
Reads SKILL.md files, writes skill-patch files and daily snapshots.
"""
import os
import json
import re
import hashlib
from datetime import date
from typing import Optional

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
CLAUDE_DIR = os.path.join(PROJECT_ROOT, ".claude")
SKILLS_DIR = os.path.join(CLAUDE_DIR, "skills")
PATCHES_DIR = os.path.join(CLAUDE_DIR, "skill-patches")
SNAPSHOTS_DIR = os.path.join(CLAUDE_DIR, "daily-snapshots")

for d in [PATCHES_DIR, SNAPSHOTS_DIR]:
    os.makedirs(d, exist_ok=True)


def list_skills() -> list[dict]:
    """Return [{skill_name, file_path, frontmatter, body}] for every installed skill."""
    skills = []
    if not os.path.isdir(SKILLS_DIR):
        return skills
    for name in os.listdir(SKILLS_DIR):
        skill_dir = os.path.join(SKILLS_DIR, name)
        if not os.path.isdir(skill_dir):
            continue
        md_path = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(md_path):
            md_alt = os.path.join(skill_dir, f"{name}.md")
            if os.path.isfile(md_alt):
                md_path = md_alt
            else:
                continue
        fm, body = parse_skill_file(md_path)
        skills.append({
            "skill_name": name,
            "file_path": md_path,
            "frontmatter": fm,
            "body": body,
        })
    return skills


def read_skill_file(skill_name: str) -> Optional[dict]:
    """Read one SKILL.md, returning {skill_name, file_path, frontmatter, body} or None."""
    skill_dir = os.path.join(SKILLS_DIR, skill_name)
    if not os.path.isdir(skill_dir):
        return None
    md_path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(md_path):
        md_path = os.path.join(skill_dir, f"{skill_name}.md")
    if not os.path.isfile(md_path):
        return None
    fm, body = parse_skill_file(md_path)
    return {"skill_name": skill_name, "file_path": md_path, "frontmatter": fm, "body": body}


def parse_skill_file(file_path: str) -> tuple[dict, str]:
    """Parse a SKILL.md file into (frontmatter_dict, body_text)."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    fm = {}
    body = text
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', text, re.DOTALL)
    if m:
        frontmatter_text = m.group(1)
        body = m.group(2).strip()
        for line in frontmatter_text.split("\n"):
            line = line.strip()
            if ":" in line:
                key, _, val = line.partition(":")
                fm[key.strip()] = val.strip()
    return fm, body


def write_patch_file(patch_id: int, skill_name: str, patch_type: str, content: str) -> str:
    """Write a skill-patch file to .claude/skill-patches/. Returns the file path."""
    os.makedirs(PATCHES_DIR, exist_ok=True)
    filename = f"{skill_name}-{patch_type}-{patch_id}.md"
    file_path = os.path.join(PATCHES_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# Skill Patch: {skill_name}\n")
        f.write(f"# Type: {patch_type}\n")
        f.write(f"# Patch ID: {patch_id}\n\n")
        f.write(content)
    return file_path


def apply_patch_to_skill(skill_name: str, patch_type: str, target_section: str, patch_content: str) -> bool:
    """Actually modify the SKILL.md file on disk. Returns True on success."""
    skill = read_skill_file(skill_name)
    if not skill:
        return False

    with open(skill["file_path"], "r", encoding="utf-8") as f:
        original = f.read()

    if patch_type in ("add", "append"):
        new_content = original.rstrip() + "\n\n" + patch_content.strip() + "\n"
    elif patch_type == "replace":
        if target_section and target_section in original:
            new_content = original.replace(target_section, patch_content)
        else:
            new_content = original + "\n\n" + patch_content.strip() + "\n"
    elif patch_type == "insert_after":
        if target_section and target_section in original:
            idx = original.find(target_section) + len(target_section)
            new_content = original[:idx] + "\n\n" + patch_content.strip() + "\n" + original[idx:]
        else:
            new_content = original + "\n\n" + patch_content.strip() + "\n"
    elif patch_type == "insert_before":
        if target_section and target_section in original:
            idx = original.find(target_section)
            new_content = original[:idx] + patch_content.strip() + "\n\n" + original[idx:]
        else:
            new_content = patch_content.strip() + "\n\n" + original
    else:
        new_content = original + "\n\n" + patch_content.strip() + "\n"

    with open(skill["file_path"], "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def write_daily_snapshot(snapshot_id: int, snapshot_date: str, skills_json: str,
                         config_json: str, wiki_stats_json: str,
                         review_summary: str, evolution_notes: str) -> str:
    """Write a daily snapshot markdown file. Returns the file path."""
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    filename = f"snapshot-{snapshot_date}-{snapshot_id}.md"
    file_path = os.path.join(SNAPSHOTS_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# System Snapshot: {snapshot_date}\n\n")
        f.write(f"## Skills State\n\n```json\n{skills_json}\n```\n\n")
        f.write(f"## Configuration\n\n```json\n{config_json}\n```\n\n")
        f.write(f"## Wiki Statistics\n\n```json\n{wiki_stats_json}\n```\n\n")
        if review_summary:
            f.write(f"## Review Summary\n\n{review_summary}\n\n")
        if evolution_notes:
            f.write(f"## Evolution Notes\n\n{evolution_notes}\n\n")
    return file_path


def compute_skill_fingerprint(skill_name: str) -> str:
    """MD5 hash of the SKILL.md file content."""
    skill = read_skill_file(skill_name)
    if not skill:
        return ""
    with open(skill["file_path"], "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def read_config_files() -> dict:
    """Read settings.json and .mcp.json, return as dict."""
    config = {}
    settings_path = os.path.join(CLAUDE_DIR, "settings.json")
    if os.path.isfile(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            config["settings"] = json.load(f)
    mcp_path = os.path.join(PROJECT_ROOT, ".mcp.json")
    if os.path.isfile(mcp_path):
        with open(mcp_path, "r", encoding="utf-8") as f:
            config["mcp"] = json.load(f)
    return config
