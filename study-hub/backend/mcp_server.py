#!/usr/bin/env python3
"""
学习中枢 MCP Server
Claude Desktop 可以通过此 MCP Server 直接操作 study-hub 知识库。

所有操作通过 HTTP 调用后端 API，不重复业务逻辑。
"""

import os, sys, json, asyncio
import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions, ServerCapabilities
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 确保 backend 目录在导入路径中
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "backend"))
from social_parsers import (
    QwenASR, BilibiliParser, XiaohongshuParser, DEFAULT_ASR_MODEL,
)

API_BASE = os.getenv("STUDY_HUB_API_BASE", "http://localhost:8741").rstrip("/")

server = Server("study-hub")

async def api_get(path: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{API_BASE}{path}")
        resp.raise_for_status()
        return resp.json()

async def api_post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{API_BASE}{path}", json=body)
        resp.raise_for_status()
        return resp.json()

# ====== Tool Definitions ======

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_knowledge_base",
            description="在知识库中语义搜索。输入自然语言问题，返回基于你已上传文档的 AI 回答和相关来源。可指定分类名缩小搜索范围。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索问题，如：装饰器怎么用？"},
                    "category": {"type": "string", "description": "限定分类名，如 'Python'。不传则搜索全部。"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="list_categories",
            description="列出知识库的所有分类及其文档数量。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="list_documents",
            description="列出知识库中最近上传的文档列表。可按分类筛选。",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "返回文档数量，默认 10"},
                    "category": {"type": "string", "description": "按分类名筛选，如 'Python'。不传则显示全部。"},
                },
            },
        ),
        Tool(
            name="get_document",
            description="获取指定文档的完整内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "integer", "description": "文档 ID（从 list_documents 获取）"},
                },
                "required": ["doc_id"],
            },
        ),
        Tool(
            name="save_to_knowledge_base",
            description="将文本内容保存到知识库。适用于保存 Claude 对话总结、分析结果、或任何你想日后检索的内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "要保存的文本内容"},
                    "title": {"type": "string", "description": "文档标题，如：Claude对话 2026-05-01"},
                    "source": {"type": "string", "description": "来源标记，默认 claude-desktop"},
                    "category": {"type": "string", "description": "分类名，如 'Python'。不传则不分类。"},
                },
                "required": ["content", "title"],
            },
        ),
        Tool(
            name="polish_review",
            description="AI 润色学习笔记。输入原始笔记，返回润色后的总结 + 学习建议 + 知识库关联推荐。",
            inputSchema={
                "type": "object",
                "properties": {
                    "raw_text": {"type": "string", "description": "原始学习笔记，随意写即可"},
                    "date": {"type": "string", "description": "日期 (YYYY-MM-DD)，默认今天"},
                },
                "required": ["raw_text"],
            },
        ),
        Tool(
            name="get_review_list",
            description="获取历史每日复盘列表。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_weekly_report",
            description="生成本周学习周报。基于本周的每日复盘，AI 汇总生成。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # ===== B站 视频解析 =====
        Tool(
            name="parse_bilibili_video_info",
            description="解析B站分享链接，获取视频基本信息（标题、封面、UP主、播放量、分P列表等）。支持 b23.tv 短链接、bilibili.com/video/ 完整链接、或直接BV号。",
            inputSchema={
                "type": "object",
                "properties": {
                    "share_link": {"type": "string", "description": "B站分享链接或BV号"},
                },
                "required": ["share_link"],
            },
        ),
        Tool(
            name="get_bilibili_download_link",
            description="获取B站视频/音频的下载链接。返回 Dash 流（音视频分离）和 durl 流（含音频的单文件），可指定分P和清晰度。",
            inputSchema={
                "type": "object",
                "properties": {
                    "share_link": {"type": "string", "description": "B站分享链接或BV号"},
                    "cid": {"type": "integer", "description": "分P的cid，默认第一个分P"},
                    "quality": {"type": "integer", "description": "清晰度: 16=360P, 32=480P, 64=720P, 80=1080P, 116=1080P60。默认80"},
                },
                "required": ["share_link"],
            },
        ),
        Tool(
            name="extract_bilibili_text",
            description="从B站视频中提取语音文本（AI语音识别）。自动获取音频流并使用阿里云百炼 qwen3-asr-flash 模型转为文字。需要 DASHSCOPE_API_KEY。",
            inputSchema={
                "type": "object",
                "properties": {
                    "share_link": {"type": "string", "description": "B站分享链接或BV号"},
                    "cid": {"type": "integer", "description": "分P的cid，默认第一个分P"},
                    "context": {"type": "string", "description": "上下文文本，用于提高ASR识别准确率（可选）"},
                },
                "required": ["share_link"],
            },
        ),
        # ===== 小红书 笔记解析 =====
        Tool(
            name="parse_xiaohongshu_note_info",
            description="解析小红书分享链接，获取笔记基本信息（标题、正文、图片、视频、作者、互动数据等）。支持 xhslink.com 短链接和 xiaohongshu.com/explore/ 标准链接。",
            inputSchema={
                "type": "object",
                "properties": {
                    "share_link": {"type": "string", "description": "小红书分享链接"},
                },
                "required": ["share_link"],
            },
        ),
        Tool(
            name="extract_xiaohongshu_text",
            description="提取小红书笔记中的文字内容（标题 + 正文 + 标签 + 互动数据），返回Markdown格式。",
            inputSchema={
                "type": "object",
                "properties": {
                    "share_link": {"type": "string", "description": "小红书分享链接"},
                },
                "required": ["share_link"],
            },
        ),
        Tool(
            name="get_xiaohongshu_media",
            description="获取小红书笔记中的图片和视频链接。返回封面、所有图片URL、视频URL等信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "share_link": {"type": "string", "description": "小红书分享链接"},
                },
                "required": ["share_link"],
            },
        ),
        Tool(
            name="extract_xiaohongshu_video_text",
            description="从小红书视频笔记中提取语音文本（AI语音识别）。需要 DASHSCOPE_API_KEY。",
            inputSchema={
                "type": "object",
                "properties": {
                    "share_link": {"type": "string", "description": "小红书分享链接（必须是视频笔记）"},
                    "context": {"type": "string", "description": "上下文文本，用于提高ASR识别准确率（可选）"},
                },
                "required": ["share_link"],
            },
        ),
        # ===== 通用 ASR 语音识别 =====
        Tool(
            name="recognize_audio_file",
            description="识别本地音频文件中的文本。支持 aac/amr/avi/flac/flv/m4a/mkv/mp3/mp4/wav/webm 等格式。需要 DASHSCOPE_API_KEY。",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "本地音频文件路径"},
                    "context": {"type": "string", "description": "上下文文本，用于提高识别准确率（可选）"},
                    "language": {"type": "string", "description": "语言代码（如 zh / en），默认自动检测"},
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="recognize_audio_url",
            description="识别在线音频URL中的文本。直接传入音频链接即可转文字。需要 DASHSCOPE_API_KEY。",
            inputSchema={
                "type": "object",
                "properties": {
                    "audio_url": {"type": "string", "description": "音频URL链接"},
                    "context": {"type": "string", "description": "上下文文本，用于提高识别准确率（可选）"},
                    "language": {"type": "string", "description": "语言代码（如 zh / en），默认自动检测"},
                },
                "required": ["audio_url"],
            },
        ),
        # ===== Wiki 工具 =====
        Tool(
            name="compile_wiki",
            description="将知识库中的原始文档编译为结构化的 LLM Wiki 页面。AI 会自动提取知识点、建立交叉引用、检测矛盾。可指定文档 ID 列表编译特定文档，不指定则编译所有未编译过的文档。",
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "要编译的文档 ID 列表。不传则自动选择未编译的文档。",
                    },
                },
            },
        ),
        Tool(
            name="search_wiki",
            description="搜索 Wiki 页面。返回匹配的 Wiki 页面列表。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_wiki_page",
            description="获取指定 Wiki 页面的完整内容。包含页面正文、入链/出链、标签等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Wiki 页面 ID（数字）或 slug（字符串）"},
                },
                "required": ["page_id"],
            },
        ),
        Tool(
            name="list_wiki_pages",
            description="列出所有 Wiki 页面，可按分类筛选。",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "按分类名筛选，如 'Python'。不传则列出全部。"},
                },
            },
        ),
        Tool(
            name="get_wiki_graph",
            description="获取 Wiki 知识图谱数据。返回所有页面节点和交叉引用边，用于可视化知识网络。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="analyze_evolution",
            description="触发学习系统进化分析。基于最近学习的知识（Wiki页面、复盘内容），分析现有 Skills 可以如何改进，生成技能补丁。低风险补丁自动应用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "review_summary": {"type": "string", "description": "可选：复盘摘要文本"},
                },
            },
        ),
        Tool(
            name="list_evolution_patches",
            description="列出所有技能补丁。可按状态和风险级别筛选。",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "补丁状态: pending / applied / rejected"},
                    "risk_level": {"type": "string", "description": "风险级别: low / medium / high"},
                },
            },
        ),
        Tool(
            name="apply_evolution_patch",
            description="手动应用一个待处理的技能补丁。",
            inputSchema={
                "type": "object",
                "properties": {
                    "patch_id": {"type": "integer", "description": "补丁 ID"},
                },
                "required": ["patch_id"],
            },
        ),
        Tool(
            name="list_system_snapshots",
            description="列出系统快照。快照记录了 Skills、配置、Wiki 统计的每日状态。",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "返回数量，默认 10"},
                },
            },
        ),
        Tool(
            name="get_system_snapshot",
            description="获取指定系统快照的完整内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "snapshot_id": {"type": "integer", "description": "快照 ID"},
                },
                "required": ["snapshot_id"],
            },
        ),
        
    ]


# ====== Tool Handlers ======

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "search_knowledge_base":
            return await handle_search(arguments)
        elif name == "list_categories":
            return await handle_list_categories(arguments)
        elif name == "list_documents":
            return await handle_list_docs(arguments)
        elif name == "get_document":
            return await handle_get_doc(arguments)
        elif name == "save_to_knowledge_base":
            return await handle_save(arguments)
        elif name == "polish_review":
            return await handle_polish(arguments)
        elif name == "get_review_list":
            return await handle_review_list(arguments)
        elif name == "get_weekly_report":
            return await handle_weekly(arguments)
        elif name == "compile_wiki":
            return await handle_compile_wiki(arguments)
        elif name == "search_wiki":
            return await handle_search_wiki(arguments)
        elif name == "get_wiki_page":
            return await handle_get_wiki_page(arguments)
        elif name == "list_wiki_pages":
            return await handle_list_wiki_pages(arguments)
        elif name == "get_wiki_graph":
            return await handle_wiki_graph(arguments)
        elif name == "analyze_evolution":
            return await handle_analyze_evolution(arguments)
        elif name == "list_evolution_patches":
            return await handle_list_evolution_patches(arguments)
        elif name == "apply_evolution_patch":
            return await handle_apply_evolution_patch(arguments)
        elif name == "list_system_snapshots":
            return await handle_list_system_snapshots(arguments)
        elif name == "get_system_snapshot":
            return await handle_get_system_snapshot(arguments)
        # ===== 社媒解析 =====
        elif name == "parse_bilibili_video_info":
            return await handle_parse_bilibili(arguments)
        elif name == "get_bilibili_download_link":
            return await handle_bilibili_download(arguments)
        elif name == "extract_bilibili_text":
            return await handle_extract_bilibili_text(arguments)
        elif name == "parse_xiaohongshu_note_info":
            return await handle_parse_xhs(arguments)
        elif name == "extract_xiaohongshu_text":
            return await handle_extract_xhs_text(arguments)
        elif name == "get_xiaohongshu_media":
            return await handle_xhs_media(arguments)
        elif name == "extract_xiaohongshu_video_text":
            return await handle_extract_xhs_video_text(arguments)
        elif name == "recognize_audio_file":
            return await handle_recognize_audio_file(arguments)
        elif name == "recognize_audio_url":
            return await handle_recognize_audio_url(arguments)
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
    except httpx.ConnectError:
        return [TextContent(type="text", text="错误：无法连接到 study-hub 后端。请确保后端已启动 (docker compose up -d 或 python main.py)")]
    except Exception as e:
        return [TextContent(type="text", text=f"错误：{e}")]


async def handle_search(args: dict) -> list[TextContent]:
    body = {"question": args["query"]}
    if args.get("category"):
        # 将分类名转换为 category_id
        cats = await api_get("/categories")
        for cat in cats:
            if cat["name"] == args["category"]:
                body["category_id"] = cat["id"]
                break
    data = await api_post("/rag/query", body)
    answer = data.get("answer", "")
    sources = data.get("sources", [])
    cat_filter = data.get("category_filter", "")
    text = answer
    if cat_filter:
        text = f"[分类: {cat_filter}]\n{text}"
    if sources:
        text += f"\n\n来源：{', '.join(sources)}"
    return [TextContent(type="text", text=text)]


async def handle_list_categories(args: dict) -> list[TextContent]:
    cats = await api_get("/categories")
    if not cats:
        return [TextContent(type="text", text="暂无分类。")]
    lines = [f"- {c['icon']} {c['name']} ({c['doc_count']}篇文档)" for c in cats]
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_list_docs(args: dict) -> list[TextContent]:
    limit = args.get("limit", 10)
    category_name = args.get("category", "")
    url = "/documents"
    if category_name:
        cats = await api_get("/categories")
        for cat in cats:
            if cat["name"] == category_name:
                url += f"?category_id={cat['id']}"
                break
    docs = await api_get(url)
    docs = docs[:limit]
    if not docs:
        return [TextContent(type="text", text="知识库为空。")]
    lines = []
    for d in docs:
        cat_info = f" [{d.get('category_name', '')}]" if d.get("category_name") else ""
        lines.append(f"ID {d['id']}: {d['title']}{cat_info} ({d['char_count']}字)")
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_get_doc(args: dict) -> list[TextContent]:
    doc = await api_get(f"/documents/{args['doc_id']}")
    if "error" in doc:
        return [TextContent(type="text", text=doc["error"])]
    content = doc.get("content", "")
    # 截断过长内容
    if len(content) > 8000:
        content = content[:8000] + "\n\n…(内容过长，已截断。完整内容请在浏览器中查看)"
    return [TextContent(type="text", text=f"# {doc['title']}\n\n{content}")]


async def handle_save(args: dict) -> list[TextContent]:
    body = {
        "content": args["content"],
        "title": args["title"],
        "source": args.get("source", "claude-desktop"),
    }
    if args.get("category"):
        cats = await api_get("/categories")
        for cat in cats:
            if cat["name"] == args["category"]:
                body["category_id"] = cat["id"]
                break
    data = await api_post("/upload/text", body)
    if "error" in data:
        return [TextContent(type="text", text=f"保存失败: {data['error']}")]
    cat_info = f", 分类: {data.get('category_name', '未分类')}" if data.get("category_name") else ""
    return [TextContent(type="text", text=f"已保存。文档 ID: {data['id']}, 标题: {data['title']}, 字数: {data['char_count']}{cat_info}")]


async def handle_polish(args: dict) -> list[TextContent]:
    body = {"raw_text": args["raw_text"]}
    if "date" in args and args["date"]:
        body["date"] = args["date"]
    data = await api_post("/review/polish", body)
    if "error" in data:
        return [TextContent(type="text", text=f"润色失败: {data['error']}")]

    text = f"## 润色总结\n\n{data.get('polished', '')}"
    suggestions = data.get("suggestions", [])
    if suggestions:
        text += "\n\n## 学习建议\n\n" + "\n".join(f"- {s}" for s in suggestions)
    related = data.get("related_docs", [])
    if related:
        text += "\n\n## 关联推荐\n\n" + "\n".join(f"- {r}" for r in related)
    return [TextContent(type="text", text=text)]


async def handle_review_list(args: dict) -> list[TextContent]:
    data = await api_get("/review/list")
    if not data:
        return [TextContent(type="text", text="暂无复盘记录。")]
    lines = []
    for r in data[:10]:
        date = r.get("date", "")
        raw = (r.get("raw_text") or "")[:60]
        lines.append(f"- {date}: {raw}…")
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_weekly(args: dict) -> list[TextContent]:
    data = await api_get("/review/weekly")
    report = data.get("report", "暂无数据")
    return [TextContent(type="text", text=report)]


# ====== 社媒解析 Handlers ======

def _parse_sync(fn):
    """将同步解析函数包装为异步执行（避免阻塞事件循环）"""
    return asyncio.get_event_loop().run_in_executor(None, fn)

async def handle_parse_bilibili(args: dict) -> list[TextContent]:
    try:
        info = await _parse_sync(lambda: BilibiliParser.get_video_info(args["share_link"]))
        return [TextContent(type="text", text=json.dumps({"status": "success", **info}, ensure_ascii=False, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2))]

async def handle_bilibili_download(args: dict) -> list[TextContent]:
    try:
        info = BilibiliParser.get_video_info(args["share_link"])
        cid = args.get("cid")
        if cid is None:
            cids = info.get("cid_list", [])
            if cids:
                cid = cids[0]["cid"]
        if cid is None:
            return [TextContent(type="text", text=json.dumps({"status": "error", "error": "无法获取cid"}, ensure_ascii=False))]
        quality = args.get("quality", 80)
        play = await _parse_sync(lambda: BilibiliParser.get_play_url(info["bvid"], cid, quality))
        return [TextContent(type="text", text=json.dumps({
            "status": "success", "bvid": info["bvid"], "title": info["title"],
            "cid": cid, "play_info": play,
            "usage_tip": "dash.video为纯视频流(无声)，dash.audio为纯音频流。durl为含音频的单一文件。"
        }, ensure_ascii=False, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2))]

async def handle_extract_bilibili_text(args: dict) -> list[TextContent]:
    try:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return [TextContent(type="text", text="错误：未设置 DASHSCOPE_API_KEY 环境变量")]
        audio_url, info = await _parse_sync(lambda: BilibiliParser.get_audio_url(args["share_link"], args.get("cid")))
        asr = QwenASR(api_key)
        result = await _parse_sync(lambda: asr.recognize(audio_url, args.get("context"), "zh"))
        if result["success"]:
            return [TextContent(type="text", text=f"# {info['title']}\n\n{result['text']}")]
        return [TextContent(type="text", text=f"ASR识别失败: {result.get('error', '未知错误')}")]
    except Exception as e:
        return [TextContent(type="text", text=f"错误：{e}")]

async def handle_parse_xhs(args: dict) -> list[TextContent]:
    try:
        info = await _parse_sync(lambda: XiaohongshuParser.get_note_info(args["share_link"]))
        return [TextContent(type="text", text=json.dumps({"status": "success", **info}, ensure_ascii=False, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2))]

async def handle_extract_xhs_text(args: dict) -> list[TextContent]:
    try:
        info = await _parse_sync(lambda: XiaohongshuParser.get_note_info(args["share_link"]))
        parts = []
        if info.get("title"):
            parts.append(f"# {info['title']}\n")
        author = info.get("author", {})
        if author.get("name"):
            loc = f" | 📍{info['ip_location']}" if info.get("ip_location") else ""
            parts.append(f"**作者**: {author['name']}{loc}\n")
        if info.get("description"):
            parts.append(f"{info['description']}\n")
        if info.get("tags"):
            parts.append(f"**标签**: {' '.join('#' + t for t in info['tags'])}")
        stat = info.get("stat", {})
        if stat:
            parts.append(f"\n❤️{stat.get('liked',0)} ⭐{stat.get('collected',0)} 💬{stat.get('comment',0)} 🔄{stat.get('shared',0)}")
        if info.get("video_url"):
            parts.append(f"\n> 📹 该笔记包含视频，可使用 extract_xiaohongshu_video_text 提取视频语音文本")
        return [TextContent(type="text", text="\n".join(parts) if parts else "未提取到文字内容")]
    except Exception as e:
        return [TextContent(type="text", text=f"错误：{e}")]

async def handle_xhs_media(args: dict) -> list[TextContent]:
    try:
        info = await _parse_sync(lambda: XiaohongshuParser.get_note_info(args["share_link"]))
        return [TextContent(type="text", text=json.dumps({
            "status": "success", "note_id": info["note_id"], "title": info.get("title", ""),
            "type": info.get("type", ""), "cover": info.get("cover", ""),
            "images": info.get("images", []), "video_url": info.get("video_url", ""),
            "video_duration": info.get("video_duration", 0),
            "image_count": len(info.get("images", [])),
        }, ensure_ascii=False, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2))]

async def handle_extract_xhs_video_text(args: dict) -> list[TextContent]:
    try:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return [TextContent(type="text", text="错误：未设置 DASHSCOPE_API_KEY 环境变量")]
        video_url, info = await _parse_sync(lambda: XiaohongshuParser.get_video_url(args["share_link"]))
        asr = QwenASR(api_key)
        result = await _parse_sync(lambda: asr.recognize(video_url, args.get("context"), "zh"))
        if result["success"]:
            return [TextContent(type="text", text=f"# {info.get('title', '无标题')}\n\n{result['text']}")]
        return [TextContent(type="text", text=f"ASR识别失败: {result.get('error', '未知错误')}")]
    except Exception as e:
        return [TextContent(type="text", text=f"错误：{e}")]

async def handle_recognize_audio_file(args: dict) -> list[TextContent]:
    try:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return [TextContent(type="text", text="错误：未设置 DASHSCOPE_API_KEY 环境变量")]
        asr = QwenASR(api_key)
        result = await _parse_sync(lambda: asr.recognize(args["file_path"], args.get("context"), args.get("language")))
        return [TextContent(type="text", text=json.dumps({
            "status": "success" if result["success"] else "error",
            "text": result.get("text", ""), "language": result.get("language"),
            "request_id": result.get("request_id"),
        } if result["success"] else {"status": "error", "error": result.get("error")}, ensure_ascii=False, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2))]

async def handle_recognize_audio_url(args: dict) -> list[TextContent]:
    try:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return [TextContent(type="text", text="错误：未设置 DASHSCOPE_API_KEY 环境变量")]
        asr = QwenASR(api_key)
        result = await _parse_sync(lambda: asr.recognize(args["audio_url"], args.get("context"), args.get("language")))
        return [TextContent(type="text", text=json.dumps({
            "status": "success" if result["success"] else "error",
            "text": result.get("text", ""), "language": result.get("language"),
            "request_id": result.get("request_id"),
        } if result["success"] else {"status": "error", "error": result.get("error")}, ensure_ascii=False, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2))]


# ====== Wiki Handlers ======

async def handle_compile_wiki(args: dict) -> list[TextContent]:
    body = {}
    if args.get("doc_ids"):
        body["doc_ids"] = args["doc_ids"]
    data = await api_post("/wiki/compile", body)
    if data.get("status") == "no_docs":
        return [TextContent(type="text", text=data.get("message", "没有待编译的文档"))]
    results = data.get("results", [])
    lines = []
    for r in results:
        if r.get("error"):
            lines.append(f"❌ [{r['doc_title']}] {r['error']}")
        else:
            lines.append(f"✅ {r['doc_title']} → 新建 {r['new_pages']} 页, 更新 {r['updated_pages']} 页" +
                        (f", ⚠️ {r['contradictions']} 处矛盾" if r.get('contradictions') else ""))
    return [TextContent(type="text", text="\n".join(lines) if lines else "编译完成，无新页面。")]


async def handle_search_wiki(args: dict) -> list[TextContent]:
    data = await api_get(f"/wiki/pages?search={args['query']}")
    if not data:
        return [TextContent(type="text", text=f"未找到与「{args['query']}」相关的 Wiki 页面。")]
    lines = []
    for p in data[:10]:
        tags = p.get("tags", "[]")
        cat = f" [{p['category']}]" if p.get("category") else ""
        lines.append(f"- **{p['title']}**{cat} — {p.get('summary', '无摘要')} (v{p['version']}, id={p['id']})")
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_get_wiki_page(args: dict) -> list[TextContent]:
    data = await api_get(f"/wiki/pages/{args['page_id']}")
    if "error" in data:
        return [TextContent(type="text", text=data["error"])]
    content = data.get("content", "")
    if len(content) > 6000:
        content = content[:6000] + "\n\n…(内容过长，已截断。请在浏览器中查看完整页面)"
    text = f"# {data['title']}\n\n{content}\n\n---\n版本: v{data.get('version',1)} | 分类: {data.get('category','无')} | 字数: {data.get('char_count',0)}"
    return [TextContent(type="text", text=text)]


async def handle_list_wiki_pages(args: dict) -> list[TextContent]:
    category = args.get("category", "")
    path = f"/wiki/pages?category={category}" if category else "/wiki/pages"
    data = await api_get(path)
    if not data:
        return [TextContent(type="text", text="Wiki 知识库为空，请先编译文档。")]
    lines = [f"共 {len(data)} 个 Wiki 页面："]
    for p in data[:20]:
        cat = f" [{p['category']}]" if p.get("category") else ""
        lines.append(f"- (ID {p['id']}) {p['title']}{cat} — v{p['version']}")
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_wiki_graph(args: dict) -> list[TextContent]:
    data = await api_get("/wiki/graph")
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    text = f"知识图谱：{len(nodes)} 个节点，{len(edges)} 条边\n\n"
    text += "主要节点：\n"
    for n in nodes[:15]:
        text += f"- [{n.get('category','无分类')}] {n['label']}\n"
    if len(edges) > 0:
        text += f"\n部分关联：\n"
        for e in edges[:10]:
            text += f"- {e['source']} → {e['target']}\n"
    return [TextContent(type="text", text=text)]


# ====== 进化系统 ======

async def handle_analyze_evolution(args: dict) -> list[TextContent]:
    body = {
        "source_event_type": "manual",
        "new_pages": [], "updated_pages": [], "contradictions": [],
        "review_summary": args.get("review_summary", ""),
    }
    data = await api_post("/evolution/analyze", body)
    text = "分析完成。\n"
    text += f"- 低风险自动应用: {data.get('low_risk_applied', 0)} 个\n"
    text += f"- 中风险待审核: {data.get('medium_risk_pending', 0)} 个\n"
    text += f"- 高风险仅记录: {data.get('high_risk_logged', 0)} 个\n"
    text += f"- 快照 ID: {data.get('snapshot_id', 'N/A')}"
    patches = data.get("patches", [])
    if patches:
        text += "\n\n补丁详情：\n"
        for p in patches:
            text += f"\n- [{p['risk_level']}] {p['skill_name']}: {p.get('rationale', '')[:80]} (状态: {p['status']})"
    return [TextContent(type="text", text=text)]

async def handle_list_evolution_patches(args: dict) -> list[TextContent]:
    params = []
    if args.get("status"):
        params.append(f"status={args['status']}")
    if args.get("risk_level"):
        params.append(f"risk_level={args['risk_level']}")
    qs = "&".join(params)
    path = f"/evolution/patches?{qs}" if qs else "/evolution/patches"
    data = await api_get(path)
    if not data:
        return [TextContent(type="text", text="暂无技能补丁。")]
    lines = [f"共 {len(data)} 个补丁："]
    for p in data:
        lines.append(f"- [{p['risk_level']}风险] #{p['id']} {p['skill_name']}: {p.get('rationale', '无说明')[:80]} ({p['status']})")
    return [TextContent(type="text", text="\n".join(lines))]

async def handle_apply_evolution_patch(args: dict) -> list[TextContent]:
    data = await api_post(f"/evolution/patches/{args['patch_id']}/apply", {})
    if data.get("applied"):
        return [TextContent(type="text", text=f"补丁 #{args['patch_id']} 已应用。")]
    return [TextContent(type="text", text=f"应用失败: {data.get('error', '未知错误')}")]

async def handle_list_system_snapshots(args: dict) -> list[TextContent]:
    limit = args.get("limit", 10)
    data = await api_get(f"/evolution/snapshots?limit={limit}")
    if not data:
        return [TextContent(type="text", text="暂无系统快照。")]
    lines = [f"最近 {len(data)} 个快照："]
    for s in data:
        lines.append(f"- #{s['id']} {s['snapshot_date']} ({s['snapshot_type']}) — {s.get('evolution_notes', '')}")
    return [TextContent(type="text", text="\n".join(lines))]

async def handle_get_system_snapshot(args: dict) -> list[TextContent]:
    data = await api_get(f"/evolution/snapshots/{args['snapshot_id']}")
    if "error" in data:
        return [TextContent(type="text", text=data["error"])]
    text = f"# 系统快照 #{data['id']}\n\n"
    text += f"日期: {data.get('snapshot_date', '')}\n"
    text += f"类型: {data.get('snapshot_type', '')}\n"
    text += f"笔记: {data.get('evolution_notes', '无')}\n"
    return [TextContent(type="text", text=text)]


# ====== Entry Point ======

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="study-hub",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    experimental=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
