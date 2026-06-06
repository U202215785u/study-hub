"""
社区 Skill 同步模块
从 awesome-claude-code 等仓库同步 Skill 目录到本地 SQLite 缓存
"""

import csv
import io
import sqlite3
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# awesome-claude-code 的 CSV 资源表
CSV_URL = "https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/main/THE_RESOURCES_TABLE.csv"
CSV_FALLBACK_URL = "https://raw.githubusercontent.com/alirezarezvani/claude-skills/main/README.md"

# 其他数据源
DATA_SOURCES = {
    "awesome_claude_code": CSV_URL,
}


def _fetch_csv(url: str, timeout: int = 15) -> Optional[str]:
    """从 URL 获取 CSV 内容"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Study-Hub-Skill-Sync/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"[skills_sync] 获取失败 {url}: {e}")
        return None


def _parse_stars(stars_str: str) -> int:
    """解析 stars 数字（处理 K/M 后缀）"""
    if not stars_str:
        return 0
    s = str(stars_str).strip().replace(",", "").lower()
    try:
        if s.endswith("k"):
            return int(float(s[:-1]) * 1000)
        elif s.endswith("m"):
            return int(float(s[:-1]) * 1000000)
        else:
            return int(float(s))
    except ValueError:
        return 0


def _parse_bool(val: str) -> int:
    """解析布尔值字符串"""
    if not val:
        return 1
    return 1 if val.strip().upper() in ("TRUE", "1", "YES", "Y") else 0


def sync_from_awesome_claude_code(db_path: str) -> Dict:
    """
    从 awesome-claude-code 同步 Skill 目录
    
    Returns:
        {"success": bool, "added": int, "updated": int, "total": int, "error": str}
    """
    csv_text = _fetch_csv(CSV_URL)
    if not csv_text:
        return {"success": False, "added": 0, "updated": 0, "total": 0, "error": "无法获取远程数据"}
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    added = 0
    updated = 0
    now = datetime.now().isoformat()
    
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        for row in reader:
            skill_id = row.get("ID", "").strip()
            if not skill_id:
                continue
            
            # 检查是否已存在
            existing = conn.execute(
                "SELECT id FROM community_skills WHERE id = ?", (skill_id,)
            ).fetchone()
            
            display_name = row.get("Display Name", "").strip()
            # 去除引号包裹
            if display_name.startswith('"') and display_name.endswith('"'):
                display_name = display_name[1:-1]
            
            data = {
                "id": skill_id,
                "display_name": display_name,
                "category": row.get("Category", "").strip(),
                "sub_category": row.get("Sub-Category", "").strip(),
                "primary_link": row.get("Primary Link", "").strip(),
                "secondary_link": row.get("Secondary Link", "").strip(),
                "author_name": row.get("Author Name", "").strip(),
                "author_link": row.get("Author Link", "").strip(),
                "license": row.get("License", "").strip(),
                "description": row.get("Description", "").strip(),
                "stars": _parse_stars(row.get("Repo Created", "")),  # CSV 可能没有 stars 列
                "active": _parse_bool(row.get("Active", "")),
                "date_added": row.get("Date Added", "").strip(),
                "last_modified": row.get("Last Modified", "").strip(),
                "last_checked": row.get("Last Checked", "").strip(),
                "repo_created": row.get("Repo Created", "").strip(),
                "latest_release": row.get("Latest Release", "").strip(),
                "release_version": row.get("Release Version", "").strip(),
                "release_source": row.get("Release Source", "").strip(),
                "synced_at": now,
            }
            
            if existing:
                # 更新
                conn.execute("""
                    UPDATE community_skills SET
                        display_name = :display_name,
                        category = :category,
                        sub_category = :sub_category,
                        primary_link = :primary_link,
                        secondary_link = :secondary_link,
                        author_name = :author_name,
                        author_link = :author_link,
                        license = :license,
                        description = :description,
                        stars = :stars,
                        active = :active,
                        date_added = :date_added,
                        last_modified = :last_modified,
                        last_checked = :last_checked,
                        repo_created = :repo_created,
                        latest_release = :latest_release,
                        release_version = :release_version,
                        release_source = :release_source,
                        synced_at = :synced_at
                    WHERE id = :id
                """, data)
                updated += 1
            else:
                # 插入
                conn.execute("""
                    INSERT INTO community_skills (
                        id, display_name, category, sub_category, primary_link,
                        secondary_link, author_name, author_link, license, description,
                        stars, active, date_added, last_modified, last_checked,
                        repo_created, latest_release, release_version, release_source, synced_at
                    ) VALUES (
                        :id, :display_name, :category, :sub_category, :primary_link,
                        :secondary_link, :author_name, :author_link, :license, :description,
                        :stars, :active, :date_added, :last_modified, :last_checked,
                        :repo_created, :latest_release, :release_version, :release_source, :synced_at
                    )
                """, data)
                added += 1
        
        conn.commit()
        
        # 统计总数
        total = conn.execute("SELECT COUNT(*) FROM community_skills").fetchone()[0]
        
        return {
            "success": True,
            "added": added,
            "updated": updated,
            "total": total,
            "error": "",
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "added": added, "updated": updated, "total": 0, "error": str(e)}
    finally:
        conn.close()


def get_community_skills(
    db_path: str,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "stars",
    limit: int = 50,
    offset: int = 0,
) -> List[Dict]:
    """查询社区 Skill 列表"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    where_clauses = ["active = 1"]
    params = []
    
    if category:
        where_clauses.append("category = ?")
        params.append(category)
    
    if search:
        where_clauses.append("(display_name LIKE ? OR description LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    
    where_sql = " AND ".join(where_clauses)
    
    # 排序
    sort_field = "stars" if sort == "stars" else "display_name"
    sort_dir = "DESC" if sort == "stars" else "ASC"
    
    query = f"""
        SELECT * FROM community_skills
        WHERE {where_sql}
        ORDER BY {sort_field} {sort_dir}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_skill_categories(db_path: str) -> List[str]:
    """获取所有分类列表"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT DISTINCT category FROM community_skills WHERE active = 1 ORDER BY category"
    ).fetchall()
    conn.close()
    return [r["category"] for r in rows if r["category"]]


def get_sync_stats(db_path: str) -> Dict:
    """获取同步统计信息"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    total = conn.execute("SELECT COUNT(*) as c FROM community_skills").fetchone()["c"]
    last_sync = conn.execute(
        "SELECT MAX(synced_at) as t FROM community_skills"
    ).fetchone()["t"]
    
    conn.close()
    return {"total": total, "last_sync": last_sync or "从未同步"}
