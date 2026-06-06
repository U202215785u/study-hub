"""
运营流水线 API —— 6步集成：选题 → 矩阵号 → 口播稿 → 视频剪辑 → 封面图 → 多平台发布

每个步骤都是可直接调用的接口，前端运营工作台直接对接。
"""

import os, json, uuid, tempfile, subprocess, re
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

from database import get_db
from ai_client import ai_client

router = APIRouter(prefix="/operations", tags=["operations"])

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "operations")
os.makedirs(DATA_DIR, exist_ok=True)

# ============================================
# 数据模型
# ============================================

class TopicIdeaCreate(BaseModel):
    title: str
    source: str = "manual"
    tags: List[str] = []


class TopicIdeaOut(BaseModel):
    id: int
    title: str
    source: str
    trend_score: int
    tags: List[str]
    created_at: str


class ProjectCreate(BaseModel):
    title: str
    topic_id: Optional[int] = None
    platform: str = ""


class ProjectOut(BaseModel):
    id: int
    title: str
    topic_idea: str
    platform: str
    status: str
    tags: List[str]
    created_at: str
    updated_at: str


class ScriptGenerateRequest(BaseModel):
    project_id: int
    style: str = "口播"  # 口播 | 剧情 | 科普 | 带货
    duration: int = 60  # 秒
    reference_links: List[str] = []


class ScriptUpdateRequest(BaseModel):
    project_id: int
    script_content: str


class CoverGenerateRequest(BaseModel):
    project_id: int
    title: str = ""
    style: str = "default"  # default | xiaohongshu | douyin | bilibili
    prompt_override: str = ""


class PublishRequest(BaseModel):
    project_id: int
    platforms: List[str]  # douyin, xiaohongshu, bilibili, wechat
    scheduled_at: Optional[str] = None


class PlatformAccountCreate(BaseModel):
    platform: str
    account_name: str
    account_id: str = ""


# ============================================
# 步骤 1: 找选题
# ============================================

@router.post("/topics", response_model=dict)
async def create_topic(req: TopicIdeaCreate):
    """手动添加选题"""
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO topic_ideas (title, source, tags) VALUES (?, ?, ?)",
        (req.title, req.source, json.dumps(req.tags, ensure_ascii=False))
    )
    conn.commit()
    topic_id = cur.lastrowid
    conn.close()
    return {"id": topic_id, "title": req.title, "status": "created"}


@router.get("/topics")
async def list_topics(limit: int = 50, unused_only: bool = False):
    """列出选题库"""
    conn = get_db()
    sql = "SELECT * FROM topic_ideas"
    params = []
    if unused_only:
        sql += " WHERE used_in_project_id IS NULL"
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return {
        "topics": [
            {
                "id": r["id"],
                "title": r["title"],
                "source": r["source"],
                "trend_score": r["trend_score"],
                "tags": json.loads(r["tags"] or "[]"),
                "used": r["used_in_project_id"] is not None,
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    }


@router.post("/topics/ai-discover")
async def ai_discover_topics(keyword: str = "", count: int = 5):
    """AI 自动发现选题"""
    prompt = f"""请基于当前热点和趋势，生成 {count} 个适合短视频/自媒体的内容选题。
{"关键词方向：" + keyword if keyword else ""}

要求：
1. 选题要具体、有争议性或实用性
2. 每个选题包含：标题 + 一句话说明为什么火 + 建议平台（抖音/小红书/B站/公众号）
3. 输出 JSON 数组格式

示例：
[
  {{"title": "为什么年轻人突然不爱换手机了", "reason": "消费降级话题，共鸣强", "platform": "抖音/小红书"}},
  ...
]
"""
    content = await ai_client.chat([{"role": "user", "content": prompt}], temperature=0.8, max_tokens=2048)
    
    # 尝试提取 JSON
    try:
        # 找方括号包裹的内容
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            topics = json.loads(match.group())
        else:
            topics = []
    except Exception:
        topics = []

    # 存入数据库
    conn = get_db()
    saved = []
    for t in topics:
        title = t.get("title", "")
        if not title:
            continue
        reason = t.get("reason", "")
        platform = t.get("platform", "")
        cur = conn.execute(
            "INSERT INTO topic_ideas (title, source, tags) VALUES (?, ?, ?)",
            (title, "ai-discover", json.dumps([reason, platform], ensure_ascii=False))
        )
        saved.append({"id": cur.lastrowid, "title": title, "reason": reason, "platform": platform})
    conn.commit()
    conn.close()

    return {"topics": saved, "raw": content}


# ============================================
# 步骤 2: 矩阵号管理
# ============================================

@router.post("/accounts")
async def add_account(req: PlatformAccountCreate):
    """添加平台账号"""
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO platform_accounts (platform, account_name, account_id) VALUES (?, ?, ?)",
        (req.platform, req.account_name, req.account_id)
    )
    conn.commit()
    account_id = cur.lastrowid
    conn.close()
    return {"id": account_id, "platform": req.platform, "name": req.account_name}


@router.get("/accounts")
async def list_accounts(platform: str = ""):
    """列出所有账号"""
    conn = get_db()
    if platform:
        rows = conn.execute("SELECT * FROM platform_accounts WHERE platform = ? ORDER BY created_at DESC", (platform,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM platform_accounts ORDER BY created_at DESC").fetchall()
    conn.close()
    return {
        "accounts": [
            {
                "id": r["id"],
                "platform": r["platform"],
                "name": r["account_name"],
                "account_id": r["account_id"],
                "followers": r["followers_count"],
                "active": bool(r["is_active"]),
            }
            for r in rows
        ]
    }


# ============================================
# 内容项目管理（贯穿 6 步）
# ============================================

@router.post("/projects")
async def create_project(req: ProjectCreate):
    """创建内容项目"""
    conn = get_db()
    
    # 如果有选题，标记为已使用
    topic_idea = ""
    if req.topic_id:
        topic = conn.execute("SELECT title FROM topic_ideas WHERE id = ?", (req.topic_id,)).fetchone()
        if topic:
            topic_idea = topic["title"]
            conn.execute("UPDATE topic_ideas SET used_in_project_id = ? WHERE id = ?", (req.topic_id, req.topic_id))
    
    cur = conn.execute(
        "INSERT INTO content_projects (title, topic_idea, platform, status) VALUES (?, ?, ?, ?)",
        (req.title, topic_idea, req.platform, "idea")
    )
    project_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"id": project_id, "title": req.title, "status": "idea"}


@router.get("/projects")
async def list_projects(status: str = "", platform: str = "", limit: int = 50):
    """列出内容项目"""
    conn = get_db()
    sql = "SELECT * FROM content_projects WHERE 1=1"
    params = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if platform:
        sql += " AND platform = ?"
        params.append(platform)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return {
        "projects": [
            {
                "id": r["id"],
                "title": r["title"],
                "topic_idea": r["topic_idea"],
                "platform": r["platform"],
                "status": r["status"],
                "tags": json.loads(r["tags"] or "[]"),
                "cover_url": r["cover_image_url"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]
    }


@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    """获取项目详情"""
    conn = get_db()
    row = conn.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "项目不存在")
    return {
        "id": row["id"],
        "title": row["title"],
        "topic_idea": row["topic_idea"],
        "platform": row["platform"],
        "status": row["status"],
        "script_content": row["script_content"],
        "script_audio_url": row["script_audio_url"],
        "video_path": row["video_path"],
        "cover_image_url": row["cover_image_url"],
        "published_urls": json.loads(row["published_urls"] or "{}"),
        "tags": json.loads(row["tags"] or "[]"),
        "scheduled_at": row["scheduled_at"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.post("/projects/{project_id}/status")
async def update_project_status(project_id: int, status: str):
    """更新项目状态"""
    valid_statuses = ["idea", "script", "recording", "editing", "cover", "ready", "published", "archived"]
    if status not in valid_statuses:
        raise HTTPException(400, f"无效状态，可选: {', '.join(valid_statuses)}")
    conn = get_db()
    conn.execute("UPDATE content_projects SET status = ?, updated_at = datetime('now') WHERE id = ?", (status, project_id))
    conn.commit()
    conn.close()
    return {"project_id": project_id, "status": status}


# ============================================
# 步骤 3: 口播稿生成
# ============================================

@router.post("/projects/{project_id}/script/generate")
async def generate_script(project_id: int, req: ScriptGenerateRequest = None):
    """AI 生成口播稿"""
    conn = get_db()
    project = conn.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(404, "项目不存在")
    
    style = req.style if req else "口播"
    duration = req.duration if req else 60
    refs = req.reference_links if req else []
    
    title = project["title"]
    topic = project["topic_idea"] or title
    
    ref_text = ""
    if refs:
        ref_text = "\n参考链接内容：\n" + "\n".join(refs)
    
    prompt = f"""请为以下选题生成一段{style}风格的口播稿。

选题：{title}
主题：{topic}
时长：约{duration}秒
{ref_text}

要求：
1. 开头3秒必须有钩子（悬念/痛点/反常识）
2. 语言口语化，适合对着镜头直接念
3. 每30秒左右有一个节奏点（转折/金句/互动提问）
4. 结尾有明确的行动号召（关注/点赞/评论引导）
5. 总字数控制在 {duration * 3} 字左右（按每秒3字估算）
6. 标注【停顿】【重音】【表情】等表演提示

直接输出口播稿全文，不要解释。"""

    content = await ai_client.chat([{"role": "user", "content": prompt}], temperature=0.8, max_tokens=3000)
    
    # 保存到项目
    conn.execute(
        "UPDATE content_projects SET script_content = ?, status = 'script', updated_at = datetime('now') WHERE id = ?",
        (content, project_id)
    )
    conn.commit()
    conn.close()
    
    return {"project_id": project_id, "script": content, "status": "script"}


@router.post("/projects/{project_id}/script/update")
async def update_script(project_id: int, req: ScriptUpdateRequest):
    """更新口播稿（人工编辑后保存）"""
    conn = get_db()
    conn.execute(
        "UPDATE content_projects SET script_content = ?, updated_at = datetime('now') WHERE id = ?",
        (req.script_content, project_id)
    )
    conn.commit()
    conn.close()
    return {"project_id": project_id, "status": "updated"}


@router.post("/projects/{project_id}/script/polish")
async def polish_script(project_id: int, style: str = "更口语化"):
    """AI 润色口播稿"""
    conn = get_db()
    project = conn.execute("SELECT script_content FROM content_projects WHERE id = ?", (project_id,)).fetchone()
    if not project or not project["script_content"]:
        conn.close()
        raise HTTPException(400, "项目没有口播稿，请先生成")
    
    script = project["script_content"]
    prompt = f"""请对以下口播稿进行润色，要求：{style}。

原文：
{script}

要求：
1. 保持原意和结构
2. 让语言更自然、更像真人说话
3. 增强节奏感和记忆点
4. 保留【停顿】【重音】等表演提示

直接输出润色后的全文。"""

    content = await ai_client.chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=3000)
    
    conn.execute(
        "UPDATE content_projects SET script_content = ?, updated_at = datetime('now') WHERE id = ?",
        (content, project_id)
    )
    conn.commit()
    conn.close()
    
    return {"project_id": project_id, "script": content}


# ============================================
# 步骤 4: 视频剪辑（简化版——生成剪辑指令）
# ============================================

@router.post("/projects/{project_id}/video/editing-plan")
async def generate_editing_plan(project_id: int):
    """生成视频剪辑方案"""
    conn = get_db()
    project = conn.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(404, "项目不存在")
    
    script = project["script_content"]
    if not script:
        conn.close()
        raise HTTPException(400, "项目没有口播稿")
    
    prompt = f"""请为以下口播稿生成详细的视频剪辑方案。

口播稿：
{script[:2000]}

请输出：
1. 镜头分段建议（每段时长、画面内容、景别）
2. B-roll 素材需求清单
3. 字幕样式建议
4. 转场和特效建议
5. 背景音乐风格建议
6. 导出参数建议（分辨率、帧率、码率）

格式清晰，方便直接交给剪辑师执行。"""

    content = await ai_client.chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=3000)
    
    # 更新状态
    conn.execute(
        "UPDATE content_projects SET status = 'editing', updated_at = datetime('now') WHERE id = ?",
        (project_id,)
    )
    conn.commit()
    conn.close()
    
    return {"project_id": project_id, "editing_plan": content, "status": "editing"}


@router.post("/projects/{project_id}/video/upload")
async def upload_video_path(project_id: int, video_path: str):
    """记录视频文件路径（实际文件由用户上传到指定目录）"""
    conn = get_db()
    conn.execute(
        "UPDATE content_projects SET video_path = ?, status = 'editing', updated_at = datetime('now') WHERE id = ?",
        (video_path, project_id)
    )
    conn.commit()
    conn.close()
    return {"project_id": project_id, "video_path": video_path}


# ============================================
# 步骤 5: 封面图生成
# ============================================

@router.post("/projects/{project_id}/cover/generate")
async def generate_cover_for_project(project_id: int, req: CoverGenerateRequest = None):
    """为项目生成封面图"""
    conn = get_db()
    project = conn.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(404, "项目不存在")
    
    title = project["title"]
    if req and req.title:
        title = req.title
    
    style = req.style if req else "default"
    
    # 平台-specific 尺寸和风格
    platform_config = {
        "default": {"ratio": "16:9", "desc": "通用横版封面"},
        "xiaohongshu": {"ratio": "3:4", "desc": "小红书竖版封面，明亮清新风格"},
        "douyin": {"ratio": "9:16", "desc": "抖音竖版封面，大字标题风格"},
        "bilibili": {"ratio": "16:9", "desc": "B站横版封面，二次元或知识区风格"},
    }
    config = platform_config.get(style, platform_config["default"])
    
    if req and req.prompt_override:
        prompt = req.prompt_override
    else:
        prompt = (
            f'Create a modern, eye-catching cover image for a video titled "{title}". '
            f'Style: {config["desc"]}. '
            f'Use bold colors, clear visual hierarchy, suitable for social media thumbnail. '
            f'No text in the image.'
        )
    
    # 调用 GrsAI 生图
    GRSAI_BASE = os.getenv("GRSAI_BASE", "https://grsai.dakka.com.cn")
    GRSAI_API_KEY = os.getenv("GRSAI_API_KEY", "")
    
    if not GRSAI_API_KEY:
        conn.close()
        return {"error": "GrsAi API Key 未配置，请在 .env 中设置 GRSAI_API_KEY"}
    
    submit_url = f"{GRSAI_BASE.rstrip('/')}/v1/draw/nano-banana"
    headers = {
        "Authorization": f"Bearer {GRSAI_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": os.getenv("GRSAI_MODEL", "nano-banana-2"),
        "prompt": prompt,
        "aspectRatio": config["ratio"],
        "urls": [],
        "webHook": "-1"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(submit_url, headers=headers, json=body)
        if resp.status_code != 200:
            conn.close()
            return {"error": f"提交生图任务失败 ({resp.status_code}): {resp.text[:500]}"}
        task_data = resp.json()
    
    task_id = task_data.get("data", {}).get("id") or task_data.get("id")
    if not task_id:
        conn.close()
        return {"error": f"未获取到任务 ID: {task_data}"}
    
    # 轮询结果
    result_url = f"{GRSAI_BASE.rstrip('/')}/v1/draw/result"
    image_url = None
    for _ in range(30):
        async with httpx.AsyncClient(timeout=10) as qclient:
            qresp = await qclient.post(result_url, headers=headers, json={"id": task_id})
            if qresp.status_code == 200:
                qdata = qresp.json()
                d = qdata.get("data", {})
                if d.get("progress") == 100 or d.get("status", "").lower() == "succeeded":
                    results = d.get("results", [])
                    if results:
                        image_url = results[0].get("url")
                    break
                elif d.get("status", "").lower() == "failed":
                    conn.close()
                    return {"error": f"生图任务失败: {d.get('failure_reason', '未知错误')}"}
        await __import__("asyncio").sleep(2)
    
    if not image_url:
        conn.close()
        return {"error": "生图任务超时，请稍后重试"}
    
    # 下载图片
    async with httpx.AsyncClient(timeout=30) as dclient:
        dresp = await dclient.get(image_url)
        if dresp.status_code != 200:
            conn.close()
            return {"error": f"下载图片失败 ({dresp.status_code})"}
        img_bytes = dresp.content
    
    filename = f"cover_{project_id}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(img_bytes)
    
    local_url = f"/operations/images/{filename}"
    
    # 更新项目
    conn.execute(
        "UPDATE content_projects SET cover_image_url = ?, status = 'cover', updated_at = datetime('now') WHERE id = ?",
        (local_url, project_id)
    )
    conn.commit()
    conn.close()
    
    return {"project_id": project_id, "cover_url": local_url, "prompt": prompt}


@router.get("/images/{filename}")
async def serve_cover_image(filename: str):
    """提供封面图文件"""
    from fastapi.responses import FileResponse
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(404, "图片不存在")
    return FileResponse(filepath)


# ============================================
# 步骤 6: 多平台发布
# ============================================

@router.post("/projects/{project_id}/publish")
async def publish_project(project_id: int, req: PublishRequest = None):
    """发布到多平台（当前为模拟/记录，实际发布需对接各平台 API）"""
    conn = get_db()
    project = conn.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(404, "项目不存在")
    
    platforms = req.platforms if req else ["douyin", "xiaohongshu"]
    
    # 生成各平台适配内容
    script = project["script_content"] or ""
    title = project["title"]
    
    platform_contents = {}
    for pf in platforms:
        if pf == "xiaohongshu":
            prompt = f"""请将以下内容改写为小红书风格的笔记文案：

标题：{title}
内容：{script[:1000]}

要求：
1. 标题要有 emoji 和情绪词
2. 正文分段清晰，多用短句
3. 结尾加 3-5 个相关标签
4. 语气亲切像朋友分享

直接输出生成的小红书文案。"""
        elif pf == "douyin":
            prompt = f"""请将以下内容改写为抖音视频文案（用于视频描述区）：

标题：{title}
内容：{script[:1000]}

要求：
1. 前20字必须有钩子
2. 加 3-5 个热门话题标签 #话题#
3. 引导互动（评论/点赞/关注）
4. 可以 @相关账号

直接输出生成的抖音文案。"""
        elif pf == "bilibili":
            prompt = f"""请将以下内容改写为B站视频简介：

标题：{title}
内容：{script[:1000]}

要求：
1. 简介包含视频内容概述
2. 加时间轴（如有重点内容）
3. 加相关标签和分区
4. 可以提及使用的工具/素材来源

直接输出生成的B站简介。"""
        elif pf == "wechat":
            prompt = f"""请将以下内容改写为公众号文章：

标题：{title}
内容：{script[:1500]}

要求：
1. 有吸引人的开头故事/案例
2. 分段清晰，有小标题
3. 适当加粗重点
4. 结尾有总结和行动号召
5. 总字数 800-1500

直接输出生成的公众号文章。"""
        else:
            continue
        
        content = await ai_client.chat([{"role": "user", "content": prompt}], temperature=0.8, max_tokens=2500)
        platform_contents[pf] = content
    
    # 更新项目状态
    published_urls = json.loads(project["published_urls"] or "{}")
    for pf in platforms:
        published_urls[pf] = {"status": "ready", "content": platform_contents.get(pf, "")}
    
    scheduled = req.scheduled_at if req else None
    conn.execute(
        "UPDATE content_projects SET published_urls = ?, status = 'ready', scheduled_at = ?, updated_at = datetime('now') WHERE id = ?",
        (json.dumps(published_urls, ensure_ascii=False), scheduled, project_id)
    )
    conn.commit()
    conn.close()
    
    return {
        "project_id": project_id,
        "status": "ready",
        "platforms": platform_contents,
        "message": "内容已适配各平台，请复制到对应平台发布。自动发布功能开发中。"
    }


@router.post("/projects/{project_id}/publish/confirm")
async def confirm_published(project_id: int, platform: str, url: str = ""):
    """确认已发布（用户手动发布后回填链接）"""
    conn = get_db()
    project = conn.execute("SELECT published_urls FROM content_projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(404, "项目不存在")
    
    published_urls = json.loads(project["published_urls"] or "{}")
    if platform in published_urls:
        published_urls[platform]["status"] = "published"
        published_urls[platform]["url"] = url
        published_urls[platform]["published_at"] = datetime.now().isoformat()
    
    # 检查是否所有平台都已发布
    all_published = all(v.get("status") == "published" for v in published_urls.values())
    new_status = "published" if all_published else "ready"
    
    conn.execute(
        "UPDATE content_projects SET published_urls = ?, status = ?, updated_at = datetime('now') WHERE id = ?",
        (json.dumps(published_urls, ensure_ascii=False), new_status, project_id)
    )
    conn.commit()
    conn.close()
    
    return {"project_id": project_id, "platform": platform, "status": "published"}


# ============================================
# 剪映/CapCut 自动剪辑（通过剪映脚本 + FFmpeg 实现）
# ============================================

# 剪映配置（通过剪映桌面版的导出功能 + 自动化脚本）
JIYING_EXPORT_DIR = os.getenv("JIYING_EXPORT_DIR", "")
CAPCUT_API_KEY = os.getenv("CAPCUT_API_KEY", "")


class AutoEditRequest(BaseModel):
    project_id: int
    media_files: List[str] = []  # 素材文件路径列表
    use_tts_audio: bool = True  # 是否使用 TTS 音频
    add_subtitles: bool = True  # 是否自动加字幕
    subtitle_style: str = "default"  # 字幕样式
    output_format: str = "mp4"  # 输出格式
    resolution: str = "1080p"  # 分辨率 720p/1080p/4k


@router.post("/projects/{project_id}/auto-edit")
async def auto_edit_video(project_id: int, req: AutoEditRequest = None):
    """自动剪辑视频（基于 FFmpeg + 口播稿时间轴）"""
    conn = get_db()
    project = conn.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(404, "项目不存在")
    
    script = project["script_content"] or ""
    audio_url = project["script_audio_url"] or ""
    
    use_tts = req.use_tts_audio if req else True
    add_subtitles = req.add_subtitles if req else True
    resolution = req.resolution if req else "1080p"
    
    # 分辨率映射
    res_map = {"720p": (1280, 720), "1080p": (1920, 1080), "4k": (3840, 2160)}
    width, height = res_map.get(resolution, (1920, 1080))
    
    # 构建 FFmpeg 命令
    # 方案：TTS 音频 + 纯色/渐变背景 + 字幕 = 基础口播视频
    output_filename = f"video_{project_id}_{uuid.uuid4().hex[:8]}.mp4"
    output_path = os.path.join(DATA_DIR, output_filename)
    
    # 查找 TTS 音频文件
    audio_path = None
    if use_tts and audio_url:
        audio_filename = os.path.basename(audio_url)
        audio_path = os.path.join(DATA_DIR, audio_filename)
        if not os.path.isfile(audio_path):
            audio_path = None
    
    if not audio_path:
        conn.close()
        return {
            "error": "没有找到 TTS 音频，请先生成语音",
            "solution": "先调用 POST /operations/projects/{id}/tts/generate 生成音频"
        }
    
    # 使用 FFmpeg 生成视频
    # 1. 创建带字幕的滤镜脚本
    # 2. 音频 + 视频背景 + 字幕叠加
    
    try:
        # 获取音频时长
        ffprobe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                       "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, timeout=30)
        audio_duration = float(result.stdout.strip()) if result.returncode == 0 else 60.0
        
        # 生成字幕文件（SRT）
        subtitle_path = os.path.join(tempfile.gettempdir(), f"subtitles_{project_id}.srt")
        _generate_srt_from_script(script, subtitle_path, audio_duration)
        
        # FFmpeg 命令：纯色背景 + 音频 + 字幕
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:d={audio_duration}",
            "-i", audio_path,
            "-vf", f"subtitles={subtitle_path}:force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=50'",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            output_path
        ]
        
        proc = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)
        
        if proc.returncode != 0:
            conn.close()
            return {"error": f"FFmpeg 剪辑失败: {proc.stderr[:500]}"}
        
        video_url = f"/operations/video/{output_filename}"
        
        # 更新项目
        conn.execute(
            "UPDATE content_projects SET video_path = ?, status = 'editing', updated_at = datetime('now') WHERE id = ?",
            (video_url, project_id)
        )
        conn.commit()
        conn.close()
        
        # 清理临时字幕文件
        try:
            os.remove(subtitle_path)
        except:
            pass
        
        return {
            "project_id": project_id,
            "video_url": video_url,
            "duration": round(audio_duration, 1),
            "resolution": f"{width}x{height}",
            "features": ["TTS音频", "自动字幕"] if add_subtitles else ["TTS音频"],
            "status": "editing",
            "message": "基础口播视频已生成。如需更复杂的剪辑，请下载后导入剪映继续编辑。"
        }
    
    except Exception as e:
        conn.close()
        return {"error": f"自动剪辑失败: {str(e)}"}


def _generate_srt_from_script(script: str, output_path: str, total_duration: float):
    """从口播稿生成 SRT 字幕文件"""
    # 清理脚本，按句分割
    clean = re.sub(r'[【\[].*?[】\]]', '', script)
    sentences = re.split(r'[。！？\n]', clean)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        sentences = [clean[:100]]
    
    # 平均分配时间
    avg_duration = total_duration / len(sentences)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for i, sentence in enumerate(sentences):
            start = i * avg_duration
            end = min((i + 1) * avg_duration, total_duration)
            
            start_time = _seconds_to_srt_time(start)
            end_time = _seconds_to_srt_time(end)
            
            f.write(f"{i + 1}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{sentence}\n\n")


def _seconds_to_srt_time(seconds: float) -> str:
    """将秒数转为 SRT 时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


@router.get("/video/{filename}")
async def serve_video(filename: str):
    """提供视频文件"""
    from fastapi.responses import FileResponse
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(404, "视频不存在")
    return FileResponse(filepath, media_type="video/mp4")


@router.post("/projects/{project_id}/video/capcut-export")
async def capcut_export_guide(project_id: int):
    """生成剪映导入指南（剪映目前没有开放 API，提供自动化脚本）"""
    conn = get_db()
    project = conn.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(404, "项目不存在")
    
    script = project["script_content"] or ""
    audio_url = project["script_audio_url"] or ""
    cover_url = project["cover_image_url"] or ""
    
    # 生成剪映导入脚本（PowerShell/Batch）
    guide = f"""# 剪映自动导入指南

## 项目：{project['title']}

### 步骤 1: 准备素材
1. 音频文件：{audio_url}
2. 封面图片：{cover_url}
3. 口播稿已保存到项目

### 步骤 2: 剪映操作
1. 打开剪映专业版
2. 点击「开始创作」
3. 导入音频文件
4. 添加封面图片作为视频背景（或添加纯色背景）
5. 使用「图文成片」功能导入口播稿自动生成字幕
6. 调整字幕样式、位置
7. 添加 B-roll 素材（可选）
8. 导出视频

### 步骤 3: 导出设置
- 分辨率：1080p
- 帧率：30fps
- 码率：推荐
- 格式：MP4

### 自动化脚本（Windows）
将以下文件放入剪映导入目录：
- 音频：{audio_url.split('/')[-1] if audio_url else '未生成'}
- 封面：{cover_url.split('/')[-1] if cover_url else '未生成'}

剪映导入目录通常位于：
`C:\\Users\\[用户名]\\AppData\\Local\\JianyingPro\\User Data\\Projects`
"""
    
    conn.close()
    return {
        "project_id": project_id,
        "guide": guide,
        "files": {
            "audio": audio_url,
            "cover": cover_url,
        },
        "message": "剪映暂未开放 API，已生成导入指南。请按步骤手动导入或使用上面的 FFmpeg 自动剪辑。"
    }


# ============================================
# Postiz / n8n 一键发布
# ============================================

POSTIZ_BASE = os.getenv("POSTIZ_BASE", "http://localhost:4200")
POSTIZ_API_KEY = os.getenv("POSTIZ_API_KEY", "")
N8N_BASE = os.getenv("N8N_BASE", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")


class AutoPublishRequest(BaseModel):
    project_id: int
    platforms: List[str]  # douyin, xiaohongshu, bilibili, wechat
    schedule_time: Optional[str] = None  # ISO 格式时间


@router.post("/projects/{project_id}/auto-publish")
async def auto_publish(project_id: int, req: AutoPublishRequest = None):
    """一键发布到多平台（通过 Postiz 或 n8n）"""
    conn = get_db()
    project = conn.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(404, "项目不存在")
    
    platforms = req.platforms if req else ["douyin", "xiaohongshu"]
    
    # 先生成各平台文案
    script = project["script_content"] or ""
    title = project["title"]
    cover_url = project["cover_image_url"] or ""
    video_url = project["video_path"] or ""
    
    results = {}
    
    for pf in platforms:
        # 生成平台适配文案
        if pf == "xiaohongshu":
            prompt = f"""请将以下内容改写为小红书风格的笔记文案：

标题：{title}
内容：{script[:1000]}

要求：
1. 标题要有 emoji 和情绪词
2. 正文分段清晰，多用短句
3. 结尾加 3-5 个相关标签
4. 语气亲切像朋友分享

直接输出生成的小红书文案。"""
        elif pf == "douyin":
            prompt = f"""请将以下内容改写为抖音视频文案（用于视频描述区）：

标题：{title}
内容：{script[:1000]}

要求：
1. 前20字必须有钩子
2. 加 3-5 个热门话题标签 #话题#
3. 引导互动（评论/点赞/关注）
4. 可以 @相关账号

直接输出生成的抖音文案。"""
        elif pf == "bilibili":
            prompt = f"""请将以下内容改写为B站视频简介：

标题：{title}
内容：{script[:1000]}

要求：
1. 简介包含视频内容概述
2. 加时间轴（如有重点内容）
3. 加相关标签和分区
4. 可以提及使用的工具/素材来源

直接输出生成的B站简介。"""
        elif pf == "wechat":
            prompt = f"""请将以下内容改写为公众号文章：

标题：{title}
内容：{script[:1500]}

要求：
1. 有吸引人的开头故事/案例
2. 分段清晰，有小标题
3. 适当加粗重点
4. 结尾有总结和行动号召
5. 总字数 800-1500

直接输出生成的公众号文章。"""
        else:
            continue
        
        content = await ai_client.chat([{"role": "user", "content": prompt}], temperature=0.8, max_tokens=2500)
        
        # 尝试通过 Postiz 发布（如果配置了）
        postiz_result = None
        if POSTIZ_API_KEY:
            postiz_result = await _postiz_publish(pf, title, content, cover_url, video_url, req.schedule_time if req else None)
        
        # 尝试通过 n8n 触发（如果配置了）
        n8n_result = None
        if N8N_API_KEY:
            n8n_result = await _n8n_trigger(pf, title, content, cover_url, video_url)
        
        results[pf] = {
            "content": content,
            "postiz": postiz_result,
            "n8n": n8n_result,
            "status": "published" if (postiz_result and postiz_result.get("success")) else "ready",
        }
    
    # 更新项目状态
    published_urls = json.loads(project["published_urls"] or "{}")
    for pf, r in results.items():
        published_urls[pf] = {
            "status": r["status"],
            "content": r["content"],
            "postiz_result": r.get("postiz"),
            "n8n_result": r.get("n8n"),
        }
    
    all_published = all(v.get("status") == "published" for v in published_urls.values())
    new_status = "published" if all_published else "ready"
    
    conn.execute(
        "UPDATE content_projects SET published_urls = ?, status = ?, updated_at = datetime('now') WHERE id = ?",
        (json.dumps(published_urls, ensure_ascii=False), new_status, project_id)
    )
    conn.commit()
    conn.close()
    
    return {
        "project_id": project_id,
        "status": new_status,
        "results": results,
        "message": "各平台文案已生成" + ("并尝试自动发布" if POSTIZ_API_KEY or N8N_API_KEY else "，请手动复制发布")
    }


async def _postiz_publish(platform: str, title: str, content: str, cover_url: str, video_url: str, schedule_time: str = None):
    """通过 Postiz API 发布"""
    if not POSTIZ_API_KEY:
        return {"success": False, "error": "Postiz API Key 未配置"}
    
    try:
        # Postiz API 格式（根据实际文档调整）
        headers = {"Authorization": f"Bearer {POSTIZ_API_KEY}"}
        body = {
            "platform": platform,
            "title": title,
            "content": content,
            "image_url": cover_url,
            "video_url": video_url,
        }
        if schedule_time:
            body["schedule_time"] = schedule_time
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{POSTIZ_BASE}/api/posts", headers=headers, json=body)
            if resp.status_code in (200, 201):
                return {"success": True, "post_id": resp.json().get("id")}
            return {"success": False, "error": f"Postiz API 错误 ({resp.status_code}): {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _n8n_trigger(platform: str, title: str, content: str, cover_url: str, video_url: str):
    """通过 n8n Webhook 触发发布工作流"""
    if not N8N_API_KEY:
        return {"success": False, "error": "n8n API Key 未配置"}
    
    try:
        headers = {"X-N8N-API-KEY": N8N_API_KEY}
        body = {
            "platform": platform,
            "title": title,
            "content": content,
            "cover_url": cover_url,
            "video_url": video_url,
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            # 调用 n8n webhook（需要用户配置对应的工作流）
            resp = await client.post(f"{N8N_BASE}/webhook/publish", headers=headers, json=body)
            if resp.status_code in (200, 201):
                return {"success": True, "response": resp.json()}
            return {"success": False, "error": f"n8n 错误 ({resp.status_code}): {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/publish/config")
async def get_publish_config():
    """获取发布配置状态"""
    return {
        "postiz": {
            "configured": bool(POSTIZ_API_KEY),
            "base_url": POSTIZ_BASE,
        },
        "n8n": {
            "configured": bool(N8N_API_KEY),
            "base_url": N8N_BASE,
        },
        "manual_fallback": True,
        "message": "Postiz 和 n8n 都未配置时，系统会生成各平台文案供手动复制发布"
    }


# ============================================
# 火山引擎 TTS 语音合成
# ============================================

# 火山引擎 TTS 配置
VOLC_TTS_APP_ID = os.getenv("VOLC_APP_KEY", "")
VOLC_TTS_ACCESS_TOKEN = os.getenv("VOLC_ACCESS_KEY", "")
VOLC_TTS_ENDPOINT = "https://openspeech.bytedance.com/api/v1/tts"

# 音色映射
TTS_VOICES = {
    "zh_female": {"voice_type": "BV001_streaming", "desc": "中文女声"},
    "zh_male": {"voice_type": "BV002_streaming", "desc": "中文男声"},
    "zh_news_female": {"voice_type": "BV503_streaming", "desc": "新闻女声"},
    "zh_dubbing_female": {"voice_type": "BV506_streaming", "desc": "配音女声"},
    "zh_dubbing_male": {"voice_type": "BV507_streaming", "desc": "配音男声"},
}


class TTSRequest(BaseModel):
    project_id: int
    voice: str = "zh_dubbing_female"  # 默认配音女声
    speed: float = 1.0  # 语速 0.5-2.0
    pitch: float = 0.0  # 音调 -12 到 12


@router.post("/projects/{project_id}/tts/generate")
async def generate_tts(project_id: int, req: TTSRequest = None):
    """将口播稿转为语音（火山引擎 TTS）"""
    conn = get_db()
    project = conn.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(404, "项目不存在")
    
    script = project["script_content"]
    if not script:
        conn.close()
        raise HTTPException(400, "项目没有口播稿，请先生成")
    
    voice_key = req.voice if req else "zh_dubbing_female"
    voice_config = TTS_VOICES.get(voice_key, TTS_VOICES["zh_dubbing_female"])
    speed = req.speed if req else 1.0
    pitch = req.pitch if req else 0.0
    
    if not VOLC_TTS_APP_ID or not VOLC_TTS_ACCESS_TOKEN:
        conn.close()
        return {"error": "火山引擎 TTS 未配置，请在 .env 中设置 VOLC_APP_KEY 和 VOLC_ACCESS_KEY"}
    
    # 清理口播稿中的表演提示（【停顿】【重音】等）
    clean_script = re.sub(r'[【\[].*?[】\]]', '', script)
    clean_script = clean_script.strip()
    
    if len(clean_script) > 5000:
        clean_script = clean_script[:5000]
    
    # 火山引擎 TTS API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer;{VOLC_TTS_ACCESS_TOKEN}",
    }
    body = {
        "app": {
            "appid": VOLC_TTS_APP_ID,
            "token": "access_token",
            "cluster": "volcano_tts",
        },
        "user": {
            "uid": VOLC_TTS_APP_ID,
        },
        "audio": {
            "voice_type": voice_config["voice_type"],
            "encoding": "mp3",
            "speed_ratio": speed,
            "pitch_ratio": pitch,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": clean_script,
            "operation": "query",
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(VOLC_TTS_ENDPOINT, headers=headers, json=body)
            
            if resp.status_code != 200:
                conn.close()
                return {"error": f"TTS 请求失败 ({resp.status_code}): {resp.text[:500]}"}
            
            data = resp.json()
            
            # 检查响应码
            if data.get("code") != 3000:
                conn.close()
                return {"error": f"TTS 合成失败: {data.get('message', '未知错误')}"}
            
            # 解码音频数据
            import base64
            audio_data = base64.b64decode(data["data"])
            
            # 保存音频文件
            filename = f"tts_{project_id}_{uuid.uuid4().hex[:8]}.mp3"
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(audio_data)
            
            audio_url = f"/operations/audio/{filename}"
            
            # 更新项目
            conn.execute(
                "UPDATE content_projects SET script_audio_url = ?, status = 'recording', updated_at = datetime('now') WHERE id = ?",
                (audio_url, project_id)
            )
            conn.commit()
            conn.close()
            
            return {
                "project_id": project_id,
                "audio_url": audio_url,
                "voice": voice_config["desc"],
                "duration_estimate": len(clean_script) * 0.3,  # 粗略估算秒数
                "status": "recording"
            }
    
    except Exception as e:
        conn.close()
        return {"error": f"TTS 处理失败: {str(e)}"}


@router.get("/audio/{filename}")
async def serve_audio(filename: str):
    """提供音频文件"""
    from fastapi.responses import FileResponse
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(404, "音频不存在")
    return FileResponse(filepath, media_type="audio/mpeg")


@router.get("/tts/voices")
async def list_tts_voices():
    """列出可用音色"""
    return {
        "voices": [
            {"key": k, "name": v["desc"], "voice_type": v["voice_type"]}
            for k, v in TTS_VOICES.items()
        ]
    }


# ============================================
# 仪表盘统计
# ============================================

@router.get("/dashboard")
async def operations_dashboard():
    """运营仪表盘"""
    conn = get_db()
    
    # 项目统计
    status_counts = conn.execute("""
        SELECT status, COUNT(*) as cnt FROM content_projects GROUP BY status
    """).fetchall()
    
    # 本月项目
    month_count = conn.execute("""
        SELECT COUNT(*) as cnt FROM content_projects 
        WHERE created_at >= datetime('now', 'start of month')
    """).fetchone()["cnt"]
    
    # 已发布
    published_count = conn.execute("""
        SELECT COUNT(*) as cnt FROM content_projects WHERE status = 'published'
    """).fetchone()["cnt"]
    
    # 选题库
    topic_count = conn.execute("SELECT COUNT(*) as cnt FROM topic_ideas").fetchone()["cnt"]
    unused_topic_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM topic_ideas WHERE used_in_project_id IS NULL"
    ).fetchone()["cnt"]
    
    # 账号数
    account_count = conn.execute("SELECT COUNT(*) as cnt FROM platform_accounts").fetchone()["cnt"]
    
    conn.close()
    
    return {
        "projects": {
            "total": sum(r["cnt"] for r in status_counts),
            "by_status": {r["status"]: r["cnt"] for r in status_counts},
            "this_month": month_count,
            "published": published_count,
        },
        "topics": {
            "total": topic_count,
            "unused": unused_topic_count,
        },
        "accounts": account_count,
    }
