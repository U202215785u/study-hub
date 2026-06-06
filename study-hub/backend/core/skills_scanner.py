"""
本地 Skill 扫描器
扫描 .claude/skills/ 和 .agents/skills/ 目录，提取 Skill 元数据
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


def _parse_skill_md_frontmatter(content: str) -> Dict:
    """解析 SKILL.md 的 YAML frontmatter"""
    meta = {}
    
    # 匹配 --- ... --- 格式的 frontmatter
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        for line in fm_text.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                meta[key] = val
    
    # 提取第一个 # 标题作为名称后备
    if not meta.get('name'):
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            meta['name'] = title_match.group(1).strip()
    
    # 提取 description（frontmatter 或第一段文字）
    if not meta.get('description'):
        desc_match = re.search(r'^##?\s*.*?\n\n(.{10,200})', content, re.MULTILINE | re.DOTALL)
        if desc_match:
            meta['description'] = desc_match.group(1).strip().replace('\n', ' ')[:200]
    
    return meta


def scan_claude_skills(project_root: str) -> List[Dict]:
    """扫描 .claude/skills/ 目录下的 Skill"""
    skills = []
    skills_dir = Path(project_root) / ".claude" / "skills"
    
    if not skills_dir.exists():
        return skills
    
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            meta = _parse_skill_md_frontmatter(content)
            
            skills.append({
                "id": f"claude_{skill_dir.name}",
                "name": skill_dir.name,
                "display_name": meta.get("name", skill_dir.name),
                "description": meta.get("description", meta.get("desc", "")),
                "source": "claude",
                "path": str(skill_dir.relative_to(project_root)).replace("\\", "/"),
                "has_scripts": any((skill_dir / "scripts").glob("*")) if (skill_dir / "scripts").exists() else False,
            })
    
    return skills


def scan_agents_skills(project_root: str) -> List[Dict]:
    """扫描 .agents/skills/ 目录下的 Skill"""
    skills = []
    skills_dir = Path(project_root) / ".agents" / "skills"
    
    if not skills_dir.exists():
        return skills
    
    for skill_file in skills_dir.glob("*.md"):
        content = skill_file.read_text(encoding="utf-8")
        meta = _parse_skill_md_frontmatter(content)
        
        # 从文件名提取 ID
        skill_id = skill_file.stem
        
        skills.append({
            "id": f"agents_{skill_id}",
            "name": skill_id,
            "display_name": meta.get("name", skill_id),
            "description": meta.get("description", meta.get("desc", "")),
            "source": "agents",
            "path": str(skill_file.relative_to(project_root)).replace("\\", "/"),
            "has_scripts": False,
        })
    
    return skills


def scan_all_local_skills(project_root: str) -> List[Dict]:
    """扫描所有本地 Skill"""
    return scan_claude_skills(project_root) + scan_agents_skills(project_root)


def sync_local_skills_to_db(db_path: str, project_root: str) -> Dict:
    """将本地 Skill 扫描结果同步到数据库"""
    conn = sqlite3.connect(db_path)
    
    local_skills = scan_all_local_skills(project_root)
    now = datetime.now().isoformat()
    
    added = 0
    updated = 0
    
    try:
        for skill in local_skills:
            existing = conn.execute(
                "SELECT id FROM local_skills WHERE id = ?", (skill["id"],)
            ).fetchone()
            
            if existing:
                conn.execute("""
                    UPDATE local_skills SET
                        display_name = ?,
                        source = ?,
                        install_path = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (skill["display_name"], skill["source"], skill["path"], now, skill["id"]))
                updated += 1
            else:
                conn.execute("""
                    INSERT INTO local_skills (id, name, display_name, source, install_path, enabled, installed_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """, (skill["id"], skill["name"], skill["display_name"], skill["source"], skill["path"], now, now))
                added += 1
        
        conn.commit()
        
        total = conn.execute("SELECT COUNT(*) FROM local_skills").fetchone()[0]
        return {"success": True, "added": added, "updated": updated, "total": total}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def get_local_skills_from_db(db_path: str) -> List[Dict]:
    """从数据库获取本地 Skill 列表"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM local_skills ORDER BY source, display_name"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def toggle_skill(db_path: str, skill_id: str, enabled: bool) -> Dict:
    """启用/禁用 Skill"""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE local_skills SET enabled = ?, updated_at = ? WHERE id = ?",
            (1 if enabled else 0, datetime.now().isoformat(), skill_id)
        )
        conn.commit()
        return {"success": True, "skill_id": skill_id, "enabled": enabled}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def uninstall_skill(db_path: str, skill_id: str, project_root: str) -> Dict:
    """卸载 Skill：删除文件 + 删除数据库记录"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        row = conn.execute(
            "SELECT install_path FROM local_skills WHERE id = ?", (skill_id,)
        ).fetchone()
        
        if not row:
            return {"success": False, "error": "Skill 不存在"}
        
        install_path = row["install_path"]
        full_path = Path(project_root) / install_path
        
        # 删除文件/目录
        if full_path.exists():
            if full_path.is_dir():
                import shutil
                shutil.rmtree(full_path)
            else:
                full_path.unlink()
        
        # 删除数据库记录
        conn.execute("DELETE FROM local_skills WHERE id = ?", (skill_id,))
        conn.commit()
        
        return {"success": True, "skill_id": skill_id}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
