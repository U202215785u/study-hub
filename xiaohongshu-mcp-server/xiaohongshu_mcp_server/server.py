#!/usr/bin/env python3
"""
小红书笔记信息解析与文本提取 MCP 服务器

功能：
1. 解析小红书分享链接获取笔记信息（标题/正文/图片/视频/作者/互动数据等）
2. 提取小红书笔记中的文本内容
3. 获取笔记中的图片/视频链接
4. 对笔记中的视频进行AI语音识别提取文本
"""

import os
import re
import json
import requests
import tempfile
import asyncio
from pathlib import Path
from typing import Optional
from http import HTTPStatus

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context
import dashscope


mcp = FastMCP("Xiaohongshu MCP Server",
              dependencies=["requests", "ffmpeg-python", "tqdm", "dashscope"])

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Referer': 'https://www.xiaohongshu.com',
}

DEFAULT_MODEL = "qwen3-asr-flash"


class QwenASR:
    """Qwen-3-ASR-Flash 语音识别器（内联版）"""

    def __init__(self, api_key: Optional[str] = None, model: str = "qwen3-asr-flash"):
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("未设置 DASHSCOPE_API_KEY")
        self.model = model
        dashscope.api_key = self.api_key

    def recognize_audio(
        self,
        audio_input,
        context: Optional[str] = None,
        language: Optional[str] = None,
        enable_lid: bool = True,
        enable_itn: bool = False
    ) -> dict:
        try:
            if isinstance(audio_input, Path):
                audio_input = str(audio_input)

            if os.path.exists(str(audio_input)):
                audio_input = f"file://{os.path.abspath(str(audio_input))}"

            messages = [
                {"role": "system", "content": [{"text": context or ""}]},
                {"role": "user", "content": [{"audio": audio_input}]}
            ]

            asr_options = {"enable_lid": enable_lid, "enable_itn": enable_itn}
            if language:
                asr_options["language"] = language

            response = dashscope.MultiModalConversation.call(
                api_key=self.api_key,
                model=self.model,
                messages=messages,
                result_format="message",
                asr_options=asr_options
            )

            if response.status_code != 200:
                raise Exception(f"API调用失败: {response.message}")

            result = {
                "success": True, "text": "", "language": None,
                "usage": response.usage, "request_id": response.request_id
            }

            if response.output and response.output.choices:
                choice = response.output.choices[0]
                if choice.message and choice.message.content:
                    result["text"] = choice.message.content[0].get("text", "")
                if choice.message.annotations:
                    for annotation in choice.message.annotations:
                        if annotation.get("type") == "audio_info":
                            result["language"] = annotation.get("language")

            return result
        except Exception as e:
            return {"success": False, "error": str(e), "text": "", "language": None}

    def recognize_url(
        self, audio_url: str, context=None, language=None, enable_lid=True, enable_itn=False
    ) -> dict:
        return self.recognize_audio(audio_url, context, language, enable_lid, enable_itn)

    def recognize_file(
        self, file_path, context=None, language=None, enable_lid=True, enable_itn=False
    ) -> dict:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if not file_path.exists():
            return {"success": False, "error": f"文件不存在: {file_path}", "text": "", "language": None}
        return self.recognize_audio(file_path, context, language, enable_lid, enable_itn)


class XiaohongshuProcessor:
    """小红书笔记处理器"""

    def __init__(self, api_key: str = "", model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.temp_dir = Path(tempfile.mkdtemp())
        if api_key:
            dashscope.api_key = api_key
            self.asr = QwenASR(api_key, self.model)
        self._session = requests.Session()

    def __del__(self):
        import shutil
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _resolve_short_link(self, share_url: str) -> str:
        """解析xhslink.com短链接，获取真实URL和note_id"""
        resp = requests.get(share_url, headers=HEADERS, allow_redirects=True, timeout=15)

        # 从最终URL中提取note_id
        note_match = re.search(r'/explore/([a-zA-Z0-9]+)', resp.url)
        if note_match:
            return note_match.group(1)

        # 从页面内容中尝试提取
        note_match = re.search(r'/explore/([a-zA-Z0-9]+)', resp.text)
        if note_match:
            return note_match.group(1)

        raise ValueError("无法解析小红书短链接")

    def _extract_note_id(self, share_text: str) -> str:
        """从分享文本中提取笔记ID"""
        # 直接匹配 explore/note_id 格式
        note_match = re.search(r'/explore/([a-zA-Z0-9]+)', share_text)
        if note_match:
            return note_match.group(1)

        # 提取URL
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', share_text)
        if not urls:
            raise ValueError("未找到有效的小红书链接")

        share_url = urls[0]

        # xhslink.com 短链接
        if 'xhslink.com' in share_url:
            return self._resolve_short_link(share_url)

        # 标准链接
        note_match = re.search(r'/explore/([a-zA-Z0-9]+)', share_url)
        if note_match:
            return note_match.group(1)

        # 从页面中提取
        resp = requests.get(share_url, headers=HEADERS, timeout=15)
        note_match = re.search(r'/explore/([a-zA-Z0-9]+)', resp.url)
        if note_match:
            return note_match.group(1)

        raise ValueError("无法从链接中提取笔记ID")

    def parse_note_info(self, share_text: str) -> dict:
        """解析小红书分享链接获取笔记信息"""
        note_id = self._extract_note_id(share_text)

        # 使用小红书网页API获取笔记详情
        api_url = f"https://www.xiaohongshu.com/explore/{note_id}"

        headers = {
            **HEADERS,
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
        }

        resp = requests.get(api_url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # 尝试从 __INITIAL_STATE__ 提取数据
        note_data = {}

        # 方法1: 从 window.__INITIAL_STATE__ 提取
        init_state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>', html, re.DOTALL)
        if init_state_match:
            try:
                init_state = json.loads(init_state_match.group(1))
                note_detail = init_state.get("note", {}).get("noteDetailMap", {}).get(note_id, {})

                if note_detail:
                    note = note_detail.get("note", {})
                    note_data = {
                        "note_id": note_detail.get("noteId", note_id),
                        "title": note.get("title", ""),
                        "description": note.get("desc", ""),
                        "type": note.get("type", ""),  # "normal" or "video"
                        "cover": "",
                        "images": [],
                        "video_url": "",
                        "author": {
                            "name": note.get("user", {}).get("nickname", ""),
                            "id": note.get("user", {}).get("userId", ""),
                            "avatar": note.get("user", {}).get("avatar", ""),
                        },
                        "stat": {
                            "liked": note.get("interactInfo", {}).get("likedCount", 0),
                            "collected": note.get("interactInfo", {}).get("collectedCount", 0),
                            "comment": note.get("interactInfo", {}).get("commentCount", 0),
                            "shared": note.get("interactInfo", {}).get("shareCount", 0),
                        },
                        "tags": [t.get("name", "") for t in note.get("tagList", [])],
                        "create_time": note.get("time", 0),
                        "ip_location": note.get("ipLocation", ""),
                    }

                    # 提取封面
                    image_list = note.get("imageList", [])
                    if image_list:
                        for img in image_list:
                            url = img.get("urlDefault", "") or img.get("url", "") or img.get("infoList", [{}])[0].get("url", "")
                            if url and not url.startswith("http"):
                                url = "https:" + url
                            if url:
                                note_data["images"].append(url)
                            if not note_data["cover"]:
                                note_data["cover"] = url

                    # 提取视频
                    video_info = note.get("video", {})
                    if video_info:
                        media = video_info.get("media", {})
                        note_data["video_url"] = media.get("stream", {}).get("h264", [{}])[0].get("masterUrl", "")
                        if not note_data["video_url"]:
                            note_data["video_url"] = media.get("stream", {}).get("h265", [{}])[0].get("masterUrl", "")
                        note_data["video_duration"] = media.get("videoDuration", 0)
                        note_data["cover"] = video_info.get("image", {}).get("firstFrameFileid", "")
                        if note_data["cover"] and not note_data["cover"].startswith("http"):
                            note_data["cover"] = "https:" + note_data["cover"]

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                pass

        # 方法2: 如果 __INITIAL_STATE__ 提取失败，从HTML meta标签提取基础信息
        if not note_data:
            title_match = re.search(r'<meta[^>]*name="og:title"[^>]*content="([^"]*)"', html)
            desc_match = re.search(r'<meta[^>]*name="og:description"[^>]*content="([^"]*)"', html)
            image_match = re.search(r'<meta[^>]*name="og:image"[^>]*content="([^"]*)"', html)
            video_match = re.search(r'<meta[^>]*name="og:video"[^>]*content="([^"]*)"', html)

            note_data = {
                "note_id": note_id,
                "title": title_match.group(1) if title_match else "",
                "description": desc_match.group(1) if desc_match else "",
                "cover": image_match.group(1) if image_match else "",
                "images": [],
                "video_url": video_match.group(1) if video_match else "",
                "author": {},
                "stat": {},
                "tags": [],
            }

        if not note_data:
            raise ValueError("无法解析笔记信息，可能需要登录Cookie")

        return note_data

    def extract_text_from_video(self, video_url: str, context: Optional[str] = None) -> str:
        """从小红书视频中提取文字"""
        if not self.api_key:
            raise ValueError("未设置 DASHSCOPE_API_KEY")

        result = self.asr.recognize_url(
            audio_url=video_url,
            context=context,
            language="zh",
            enable_lid=True,
            enable_itn=False
        )

        if result["success"]:
            return result["text"] or "未识别到文本内容"
        else:
            raise Exception(f"识别失败: {result['error']}")


# ====== MCP Tools ======

@mcp.tool()
def parse_xiaohongshu_note_info(share_link: str) -> str:
    """
    解析小红书分享链接，获取笔记基本信息（标题、正文、图片、视频、作者、互动数据等）

    参数:
    - share_link: 小红书分享链接（xhslink.com短链接 或 xiaohongshu.com/explore/标准链接）

    返回:
    - 笔记信息（JSON格式）
    """
    try:
        processor = XiaohongshuProcessor("")
        note_info = processor.parse_note_info(share_link)

        return json.dumps({
            "status": "success",
            **note_info
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"解析小红书笔记失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def extract_xiaohongshu_text(share_link: str) -> str:
    """
    提取小红书笔记中的文字内容（标题 + 正文 + 标签）

    参数:
    - share_link: 小红书分享链接

    返回:
    - 笔记的文字内容（Markdown格式）
    """
    try:
        processor = XiaohongshuProcessor("")
        note_info = processor.parse_note_info(share_link)

        text_parts = []
        if note_info.get("title"):
            text_parts.append(f"# {note_info['title']}\n")
        if note_info.get("author", {}).get("name"):
            text_parts.append(f"**作者**: {note_info['author']['name']}")
            if note_info.get("ip_location"):
                text_parts[-1] += f" | 📍{note_info['ip_location']}"
            text_parts.append("")
        if note_info.get("description"):
            text_parts.append(f"\n{note_info['description']}\n")
        if note_info.get("tags"):
            text_parts.append(f"**标签**: {' '.join('#' + t for t in note_info['tags'])}")
        if note_info.get("stat"):
            stat = note_info["stat"]
            text_parts.append(f"\n❤️{stat.get('liked', 0)} ⭐{stat.get('collected', 0)} 💬{stat.get('comment', 0)} 🔄{stat.get('shared', 0)}")

        if note_info.get("video_url"):
            text_parts.append(f"\n> 📹 该笔记包含视频，可使用 extract_xiaohongshu_video_text 提取视频语音文本")

        return "\n".join(text_parts) if text_parts else "未提取到文字内容"

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"提取文本失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_xiaohongshu_media(share_link: str) -> str:
    """
    获取小红书笔记中的图片和视频链接

    参数:
    - share_link: 小红书分享链接

    返回:
    - 包含图片URL列表和视频URL的JSON
    """
    try:
        processor = XiaohongshuProcessor("")
        note_info = processor.parse_note_info(share_link)

        return json.dumps({
            "status": "success",
            "note_id": note_info["note_id"],
            "title": note_info.get("title", ""),
            "type": note_info.get("type", ""),
            "cover": note_info.get("cover", ""),
            "images": note_info.get("images", []),
            "video_url": note_info.get("video_url", ""),
            "video_duration": note_info.get("video_duration", 0),
            "image_count": len(note_info.get("images", [])),
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"获取媒体失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def extract_xiaohongshu_video_text(
    share_link: str,
    model: Optional[str] = None,
    context: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    从小红书笔记的视频中提取语音文本（AI语音识别）

    处理流程:
    1. 解析小红书分享链接
    2. 获取笔记中的视频URL
    3. 使用阿里云百炼 ASR 将视频语音转为文本

    参数:
    - share_link: 小红书分享链接
    - model: 语音识别模型（可选，默认qwen3-asr-flash）
    - context: 上下文文本，用于提高识别准确率（可选）

    返回:
    - 提取的文本内容

    注意: 需要设置环境变量 DASHSCOPE_API_KEY
    """
    try:
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            raise ValueError("未设置环境变量 DASHSCOPE_API_KEY")

        processor = XiaohongshuProcessor(api_key, model)

        ctx.info("正在解析小红书链接...")
        note_info = processor.parse_note_info(share_link)

        video_url = note_info.get("video_url", "")
        if not video_url:
            raise ValueError("该笔记没有视频内容")

        ctx.info(f"正在从视频中提取文本: {note_info.get('title', '')}")
        text = processor.extract_text_from_video(video_url, context)

        ctx.info("文本提取完成!")
        return f"# {note_info.get('title', '无标题')}\n\n{text}"

    except Exception as e:
        ctx.error(f"处理错误: {str(e)}")
        raise Exception(f"提取小红书视频文本失败: {str(e)}")


@mcp.tool()
def recognize_audio_file(
    file_path: str,
    context: Optional[str] = None,
    language: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """
    识别本地音频文件中的文本

    参数:
    - file_path: 本地音频文件路径
    - context: 上下文文本，用于提高识别准确率（可选）
    - language: 指定语言代码（如 'zh', 'en'），可选，默认自动检测
    - model: 语音识别模型（可选，默认使用qwen3-asr-flash）

    返回:
    - 识别的文本内容

    注意: 需要设置环境变量 DASHSCOPE_API_KEY
    """
    try:
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            raise ValueError("未设置环境变量 DASHSCOPE_API_KEY")

        asr = QwenASR(api_key, model or DEFAULT_MODEL)

        result = asr.recognize_file(
            file_path=file_path, context=context, language=language,
            enable_lid=True, enable_itn=False
        )

        if result["success"]:
            return json.dumps({
                "status": "success", "text": result["text"],
                "language": result.get("language"),
                "usage": result.get("usage"),
                "request_id": result.get("request_id")
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({"status": "error", "error": result["error"]}, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": f"识别失败: {str(e)}"}, ensure_ascii=False, indent=2)


@mcp.tool()
def recognize_audio_url(
    audio_url: str,
    context: Optional[str] = None,
    language: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """
    识别在线音频URL中的文本

    参数:
    - audio_url: 音频URL链接
    - context: 上下文文本，用于提高识别准确率（可选）
    - language: 指定语言代码（如 'zh', 'en'），可选，默认自动检测
    - model: 语音识别模型（可选，默认使用qwen3-asr-flash）

    返回:
    - 识别的文本内容

    注意: 需要设置环境变量 DASHSCOPE_API_KEY
    """
    try:
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            raise ValueError("未设置环境变量 DASHSCOPE_API_KEY")

        asr = QwenASR(api_key, model or DEFAULT_MODEL)

        result = asr.recognize_url(
            audio_url=audio_url, context=context, language=language,
            enable_lid=True, enable_itn=False
        )

        if result["success"]:
            return json.dumps({
                "status": "success", "text": result["text"],
                "language": result.get("language"),
                "usage": result.get("usage"),
                "request_id": result.get("request_id")
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({"status": "error", "error": result["error"]}, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": f"识别失败: {str(e)}"}, ensure_ascii=False, indent=2)


@mcp.resource("xiaohongshu://note/{note_id}")
def get_note_resource(note_id: str) -> str:
    """通过笔记ID获取笔记信息"""
    try:
        processor = XiaohongshuProcessor("")
        note_info = processor.parse_note_info(f"https://www.xiaohongshu.com/explore/{note_id}")
        return json.dumps(note_info, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取笔记信息失败: {str(e)}"


@mcp.prompt()
def xiaohongshu_usage_guide() -> str:
    """小红书笔记解析使用指南"""
    return """
# 小红书笔记解析使用指南

## 功能说明
这个MCP服务器提供小红书笔记的解析和文本提取功能：
1. 解析小红书分享链接获取笔记元数据（标题、正文、图片、视频、作者等）
2. 提取笔记的文字内容
3. 获取笔记中的图片和视频链接
4. 对视频笔记进行AI语音识别提取文本

## 支持的链接格式
- **短链接**: `https://xhslink.com/xxxxx`
- **标准链接**: `https://www.xiaohongshu.com/explore/{note_id}`
- **APP分享链接**: `小红书分享的文本中包含的链接`

## 环境变量
- `DASHSCOPE_API_KEY`: 阿里云百炼API密钥（视频文本提取功能必需）

## 工具说明
- `parse_xiaohongshu_note_info`: 解析笔记完整信息（无需API密钥）
- `extract_xiaohongshu_text`: 提取笔记文字内容（无需API密钥）
- `get_xiaohongshu_media`: 获取图片/视频链接（无需API密钥）
- `extract_xiaohongshu_video_text`: 从视频中提取语音文本（需要API密钥）
- `recognize_audio_file`: 识别本地音频文件
- `recognize_audio_url`: 识别在线音频URL

## 注意事项
- 小红书部分接口可能需要Cookie才能正常访问
- 视频文本提取需要阿里云百炼API密钥
- 支持的音频格式: aac, amr, avi, aiff, flac, flv, m4a, mkv, mp3, mp4, mpeg, ogg, wav, webm, wma, wmv
"""


def main():
    """启动MCP服务器"""
    mcp.run()


if __name__ == "__main__":
    main()
