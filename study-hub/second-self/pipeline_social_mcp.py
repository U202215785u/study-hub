"""社交媒体 MCP 导入 — 从 Bilibili、小红书等平台导入内容。"""
import re
import urllib.request
from typing import Any

from memory_store import insert_entry


def ingest_social(url: str, user_note: str = "") -> dict:
    """从社交媒体 URL 导入内容。"""
    platform = _detect_platform(url)
    
    try:
        if platform == "bilibili":
            content = _fetch_bilibili(url)
        elif platform == "xiaohongshu":
            content = _fetch_xiaohongshu(url)
        else:
            return {"error": f"unsupported platform: {platform}"}
        
        full_content = f"来源：{url}\n\n{content}"
        if user_note:
            full_content += f"\n\n用户备注：{user_note}"
        
        entry_id = insert_entry(
            source="social_ingest",
            type="capture",
            content=full_content,
            context={"platform": platform, "url": url, "user_note": user_note},
            significance="B",
            field="knowledge",
        )
        return {"ok": True, "entry_id": entry_id, "platform": platform}
    except Exception as e:
        return {"error": str(e)}


def _detect_platform(url: str) -> str:
    if "bilibili" in url or "b23.tv" in url:
        return "bilibili"
    if "xiaohongshu" in url or "xhs.link" in url:
        return "xiaohongshu"
    return "unknown"


def _fetch_bilibili(url: str) -> str:
    """获取 Bilibili 视频信息。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            title = re.search(r'<title>(.*?)</title>', html)
            desc = re.search(r'description" content="(.*?)"', html)
            return f"标题：{title.group(1) if title else '未知'}\n描述：{desc.group(1) if desc else '无'}"
    except Exception as e:
        return f"[获取失败: {str(e)}]"


def _fetch_xiaohongshu(url: str) -> str:
    """获取小红书笔记信息。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            title = re.search(r'<title>(.*?)</title>', html)
            return f"标题：{title.group(1) if title else '未知'}"
    except Exception as e:
        return f"[获取失败: {str(e)}]"
