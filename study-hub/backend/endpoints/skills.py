"""
Skill 市场/管理器 API
提供社区 Skill 浏览、同步、本地管理功能
"""

import os
from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from database import get_db, DB_PATH
from core.skills_sync import (
    sync_from_awesome_claude_code,
    get_community_skills,
    get_skill_categories,
    get_sync_stats,
)
from core.skills_scanner import (
    scan_all_local_skills,
    sync_local_skills_to_db,
    get_local_skills_from_db,
    toggle_skill,
    uninstall_skill,
)

router = APIRouter(prefix="/skills", tags=["skills"])

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


# ============================================
# 数据模型
# ============================================
class CommunitySkillOut(BaseModel):
    id: str
    display_name: str
    category: str
    sub_category: str
    primary_link: str
    author_name: str
    license: str
    description: str
    stars: int
    installed: bool = False


class LocalSkillOut(BaseModel):
    id: str
    name: str
    display_name: str
    source: str
    install_path: str
    github_url: str
    enabled: bool
    installed_at: str


class SyncResult(BaseModel):
    success: bool
    added: int
    updated: int
    total: int
    error: str = ""


class ToggleRequest(BaseModel):
    enabled: bool


class ToggleResult(BaseModel):
    success: bool
    skill_id: str = ""
    enabled: bool = False
    error: str = ""


class DeleteResult(BaseModel):
    success: bool
    skill_id: str = ""
    error: str = ""


class InstallRequest(BaseModel):
    skill_id: str
    install_type: str = "light"  # light | full


class InstallResult(BaseModel):
    success: bool
    skill_id: str = ""
    message: str = ""
    error: str = ""


# ============================================
# 社区 Skill API
# ============================================
@router.get("/community", response_model=List[CommunitySkillOut])
async def list_community_skills(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: str = Query("stars"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    获取社区 Skill 列表（从本地缓存）
    
    参数:
        category: 按分类筛选
        search: 关键词搜索（名称/描述）
        sort: 排序方式（stars | name）
        limit: 返回数量
        offset: 分页偏移
    """
    skills = get_community_skills(DB_PATH, category, search, sort, limit, offset)
    
    # 检查哪些已安装
    conn = get_db()
    installed_ids = set()
    try:
        rows = conn.execute("SELECT id FROM local_skills").fetchall()
        installed_ids = {r[0] for r in rows}
    finally:
        conn.close()
    
    result = []
    for s in skills:
        skill_id = s.get("id", "")
        result.append({
            "id": skill_id,
            "display_name": s.get("display_name", ""),
            "category": s.get("category", ""),
            "sub_category": s.get("sub_category", ""),
            "primary_link": s.get("primary_link", ""),
            "author_name": s.get("author_name", ""),
            "license": s.get("license", ""),
            "description": s.get("description", ""),
            "stars": s.get("stars", 0),
            "installed": skill_id in installed_ids,
        })
    
    return result


@router.get("/community/categories")
async def list_categories():
    """获取所有 Skill 分类"""
    return get_skill_categories(DB_PATH)


@router.post("/community/sync", response_model=SyncResult)
async def sync_community():
    """手动触发从 GitHub 同步社区 Skill 目录"""
    result = sync_from_awesome_claude_code(DB_PATH)
    return SyncResult(**result)


@router.get("/community/stats")
async def community_stats():
    """获取同步统计信息"""
    return get_sync_stats(DB_PATH)


# ============================================
# 本地 Skill API
# ============================================
@router.get("/local", response_model=List[LocalSkillOut])
async def list_local_skills():
    """获取已安装的本地 Skill 列表"""
    # 先扫描同步
    sync_local_skills_to_db(DB_PATH, PROJECT_ROOT)
    return get_local_skills_from_db(DB_PATH)


@router.post("/local/scan")
async def scan_local():
    """重新扫描本地 Skill 文件"""
    result = sync_local_skills_to_db(DB_PATH, PROJECT_ROOT)
    return result


@router.post("/local/{skill_id}/toggle", response_model=ToggleResult)
async def toggle_local_skill(skill_id: str, req: ToggleRequest):
    """启用/禁用本地 Skill"""
    result = toggle_skill(DB_PATH, skill_id, req.enabled)
    return ToggleResult(**result)


@router.delete("/local/{skill_id}", response_model=DeleteResult)
async def delete_local_skill(skill_id: str):
    """卸载本地 Skill"""
    result = uninstall_skill(DB_PATH, skill_id, PROJECT_ROOT)
    return DeleteResult(**result)


@router.post("/local/install", response_model=InstallResult)
async def install_skill(req: InstallRequest):
    """
    安装社区 Skill 到本地
    
    当前实现：标记为已安装（实际文件操作需要 git clone，后续扩展）
    """
    # 查找社区 Skill 信息
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM community_skills WHERE id = ?", (req.skill_id,)
        ).fetchone()
        
        if not row:
            return InstallResult(success=False, error="Skill 不存在")
        
        skill = dict(row)
        
        # 检查是否已安装
        existing = conn.execute(
            "SELECT id FROM local_skills WHERE id = ?", (req.skill_id,)
        ).fetchone()
        
        if existing:
            return InstallResult(success=False, error="Skill 已安装")
        
        # 记录到本地 Skill 表（实际文件安装后续扩展）
        from datetime import datetime
        now = datetime.now().isoformat()
        conn.execute("""
            INSERT INTO local_skills (id, name, display_name, source, install_path, github_url, enabled, installed_at, updated_at)
            VALUES (?, ?, ?, 'claude', ?, ?, 1, ?, ?)
        """, (
            req.skill_id,
            skill.get("display_name", req.skill_id),
            skill.get("display_name", req.skill_id),
            f".claude/skills/{req.skill_id}",
            skill.get("primary_link", ""),
            now, now
        ))
        conn.commit()
        
        return InstallResult(
            success=True,
            skill_id=req.skill_id,
            message=f"Skill '{skill.get('display_name', req.skill_id)}' 已标记为安装。实际文件将在后续版本中自动下载。"
        )
    except Exception as e:
        conn.rollback()
        return InstallResult(success=False, error=str(e))
    finally:
        conn.close()
