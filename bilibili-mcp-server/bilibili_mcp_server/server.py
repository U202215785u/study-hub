#!/usr/bin/env python3
"""
哔哩哔哩视频信息解析与文本提取 MCP 服务器

功能：
1. 解析B站分享链接获取视频信息（标题/封面/分P/UP主等）
2. 获取视频/音频下载链接
3. 从视频中提取文本内容（ASR语音识别）
4. 识别本地音频文件 / 在线音频URL
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
from .asr_module import QwenASR, create_asr_instance

import dashscope


mcp = FastMCP("Bilibili MCP Server",
              dependencies=["requests", "ffmpeg-python", "tqdm", "dashscope"])

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
}

DEFAULT_MODEL = "qwen3-asr-flash"


class BilibiliProcessor:
    """哔哩哔哩视频处理器"""

    def __init__(self, api_key: str = "", model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.temp_dir = Path(tempfile.mkdtemp())
        if api_key:
            dashscope.api_key = api_key
            self.asr = create_asr_instance(api_key, self.model)

    def __del__(self):
        import shutil
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _extract_bvid(self, share_text: str) -> str:
        """从分享文本中提取BV号"""
        # 支持多种格式:
        # https://b23.tv/xxxxx
        # https://www.bilibili.com/video/BV1xx411c7mD
        # https://bilibili.com/video/BV1xx411c7mD/?spm_id_from=...
        # BV1xx411c7mD (直接就是BV号)

        # 先尝试直接匹配BV号
        bv_match = re.search(r'BV[a-zA-Z0-9]{10}', share_text)
        if bv_match:
            return bv_match.group(0)

        # 提取URL
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', share_text)
        if not urls:
            raise ValueError("未找到有效的B站链接或BV号")

        share_url = urls[0]

        # 如果是b23.tv短链接，需要跟随重定向
        if 'b23.tv' in share_url:
            try:
                resp = requests.get(share_url, headers=HEADERS, allow_redirects=False, timeout=10)
                if resp.status_code in (301, 302):
                    share_url = resp.headers.get('Location', share_url)
                elif resp.status_code == 200:
                    # 有些短链接返回HTML页面
                    content = resp.text
                    bv_match = re.search(r'BV[a-zA-Z0-9]{10}', content)
                    if bv_match:
                        return bv_match.group(0)
                    raise ValueError("无法从短链接解析BV号，请直接提供BV号或完整视频链接")
            except requests.RequestException:
                pass

            # 尝试跟随重定向
            try:
                resp = requests.get(share_url, headers=HEADERS, allow_redirects=True, timeout=10)
                share_url = resp.url
            except requests.RequestException as e:
                raise ValueError(f"访问短链接失败: {e}")

        # 从完整URL提取BV号
        bv_match = re.search(r'BV[a-zA-Z0-9]{10}', share_url)
        if bv_match:
            return bv_match.group(0)

        raise ValueError("无法从链接中提取BV号")

    def parse_share_url(self, share_text: str) -> dict:
        """从分享链接/文本中解析视频信息"""
        bvid = self._extract_bvid(share_text)

        # 调用B站API获取视频信息
        api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        resp = requests.get(api_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise ValueError(f"B站API返回错误: {data.get('message', '未知错误')}")

        video_data = data["data"]

        # 获取分P信息（cid列表）
        pages = video_data.get("pages", [])
        cid_list = [{"page": p.get("page", 1), "part": p.get("part", ""), "cid": p.get("cid", 0)} for p in pages]

        return {
            "bvid": bvid,
            "title": video_data.get("title", ""),
            "description": video_data.get("desc", ""),
            "cover": video_data.get("pic", ""),
            "duration": video_data.get("duration", 0),
            "owner": {
                "name": video_data.get("owner", {}).get("name", ""),
                "mid": video_data.get("owner", {}).get("mid", 0),
                "face": video_data.get("owner", {}).get("face", ""),
            },
            "stat": {
                "view": video_data.get("stat", {}).get("view", 0),
                "danmaku": video_data.get("stat", {}).get("danmaku", 0),
                "reply": video_data.get("stat", {}).get("reply", 0),
                "favorite": video_data.get("stat", {}).get("favorite", 0),
                "coin": video_data.get("stat", {}).get("coin", 0),
                "share": video_data.get("stat", {}).get("share", 0),
                "like": video_data.get("stat", {}).get("like", 0),
            },
            "cid_list": cid_list,
            "aid": video_data.get("aid", 0),
            "tname": video_data.get("tname", ""),
            "pubdate": video_data.get("pubdate", 0),
            "ctime": video_data.get("ctime", 0),
        }

    def get_video_url(self, bvid: str, cid: int, quality: int = 80) -> dict:
        """获取视频播放URL"""
        api_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&fnval={quality}&fnver=0&fourk=1"
        resp = requests.get(api_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise ValueError(f"获取视频URL失败: {data.get('message', '未知错误')}")

        play_data = data["data"]

        result = {
            "quality": play_data.get("quality", 0),
            "format": play_data.get("format", ""),
            "timelength": play_data.get("timelength", 0),
            "accept_description": play_data.get("accept_description", []),
            "accept_quality": play_data.get("accept_quality", []),
        }

        # dash 流（音视频分离）
        dash = play_data.get("dash", {})
        if dash:
            result["dash"] = {
                "duration": dash.get("duration", 0),
                "video": [],
                "audio": []
            }
            for v in dash.get("video", []):
                result["dash"]["video"].append({
                    "id": v.get("id", 0),
                    "base_url": v.get("base_url", ""),
                    "backup_url": v.get("backup_url", []),
                    "width": v.get("width", 0),
                    "height": v.get("height", 0),
                    "frame_rate": v.get("frame_rate", ""),
                    "codecs": v.get("codecs", ""),
                    "bandwidth": v.get("bandwidth", 0),
                })
            for a in dash.get("audio", []):
                result["dash"]["audio"].append({
                    "id": a.get("id", 0),
                    "base_url": a.get("base_url", ""),
                    "backup_url": a.get("backup_url", []),
                    "codecs": a.get("codecs", ""),
                    "bandwidth": a.get("bandwidth", 0),
                })

        # durl 流（单一视频文件，含音频）
        durl = play_data.get("durl", [])
        if durl:
            result["durl"] = []
            for d in durl:
                result["durl"].append({
                    "url": d.get("url", ""),
                    "backup_url": d.get("backup_url", []),
                    "size": d.get("size", 0),
                    "length": d.get("length", 0),
                })

        return result

    def extract_text_from_audio_url(self, audio_url: str, context: Optional[str] = None) -> str:
        """从音频URL中提取文字（ASR）"""
        if not self.api_key:
            raise ValueError("未设置 DASHSCOPE_API_KEY")

        result = self.asr.recognize_url(
            audio_url=audio_url,
            context=context,
            language="zh",
            enable_lid=True,
            enable_itn=False
        )

        if result["success"]:
            return result["text"] or "未识别到文本内容"
        else:
            raise Exception(f"识别失败: {result['error']}")

    def extract_text_from_audio_file(self, file_path: Path, context: Optional[str] = None) -> str:
        """从本地音频文件中提取文字"""
        if not self.api_key:
            raise ValueError("未设置 DASHSCOPE_API_KEY")

        result = self.asr.recognize_file(
            file_path=file_path,
            context=context,
            language="zh",
            enable_lid=True,
            enable_itn=False
        )

        if result["success"]:
            return result["text"] or "未识别到文本内容"
        else:
            raise Exception(f"识别失败: {result['error']}")

    def extract_text_from_video_url(self, video_url: str, context: Optional[str] = None) -> str:
        """从视频URL中提取文字（使用阿里云百炼ASR）"""
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
def parse_bilibili_video_info(share_link: str) -> str:
    """
    解析B站分享链接，获取视频基本信息（标题、封面、UP主、播放量、分P列表等）

    参数:
    - share_link: B站分享链接（b23.tv短链接或bilibili.com/video/完整链接）或BV号

    返回:
    - 视频信息（JSON格式）
    """
    try:
        processor = BilibiliProcessor("")
        video_info = processor.parse_share_url(share_link)

        return json.dumps({
            "status": "success",
            **video_info
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"解析B站视频失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_bilibili_download_link(share_link: str, cid: Optional[int] = None, quality: Optional[int] = 80) -> str:
    """
    获取B站视频/音频的下载链接

    参数:
    - share_link: B站分享链接或BV号
    - cid: 分P的cid（可选，默认使用第一个分P）
    - quality: 清晰度级别，默认80（最高）。常用值: 16=360P, 32=480P, 64=720P, 80=1080P, 116=1080P60

    返回:
    - 包含视频/音频下载链接的JSON字符串
    """
    try:
        processor = BilibiliProcessor("")
        video_info = processor.parse_share_url(share_link)

        # 确定使用的cid
        if cid is None:
            if video_info.get("cid_list"):
                cid = video_info["cid_list"][0]["cid"]
            else:
                # 有些视频没有cid_list，使用aid
                api_url = f"https://api.bilibili.com/x/player/pagelist?bvid={video_info['bvid']}"
                resp = requests.get(api_url, headers=HEADERS, timeout=10)
                page_data = resp.json()
                if page_data.get("code") == 0 and page_data.get("data"):
                    cid = page_data["data"][0]["cid"]
                else:
                    raise ValueError("无法获取cid")

        play_url_data = processor.get_video_url(video_info["bvid"], cid, quality)

        return json.dumps({
            "status": "success",
            "bvid": video_info["bvid"],
            "title": video_info["title"],
            "cid": cid,
            "play_info": play_url_data,
            "usage_tip": "dash.video 为纯视频流（无声），dash.audio 为纯音频流。如需完整视频，下载后用 ffmpeg 合并。durl 为含音频的单一文件。"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"获取下载链接失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def extract_bilibili_text(
    share_link: str,
    cid: Optional[int] = None,
    model: Optional[str] = None,
    context: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    从B站视频中提取文本内容（AI语音识别）

    处理流程:
    1. 解析B站分享链接获取视频信息
    2. 获取视频的音频流URL
    3. 使用阿里云百炼 ASR 将音频转为文本

    参数:
    - share_link: B站分享链接或BV号
    - cid: 分P的cid（可选，默认第一个分P）
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

        processor = BilibiliProcessor(api_key, model)

        ctx.info("正在解析B站链接...")
        video_info = processor.parse_share_url(share_link)

        # 获取cid
        if cid is None:
            if video_info.get("cid_list"):
                cid = video_info["cid_list"][0]["cid"]
            else:
                api_url = f"https://api.bilibili.com/x/player/pagelist?bvid={video_info['bvid']}"
                resp = requests.get(api_url, headers=HEADERS, timeout=10)
                page_data = resp.json()
                if page_data.get("code") == 0 and page_data.get("data"):
                    cid = page_data["data"][0]["cid"]
                else:
                    raise ValueError("无法获取cid")

        ctx.info("正在获取音频流...")
        play_url_data = processor.get_video_url(video_info["bvid"], cid)

        # 优先使用dash音频流
        audio_url = None
        dash = play_url_data.get("dash", {})
        if dash and dash.get("audio"):
            # 选择最高码率的音频
            best_audio = max(dash["audio"], key=lambda a: a.get("bandwidth", 0))
            audio_url = best_audio.get("base_url", "") or best_audio.get("backup_url", [""])[0]

        if not audio_url:
            # fallback: 使用durl（含音频的视频流）
            durl = play_url_data.get("durl", [])
            if durl:
                audio_url = durl[0].get("url", "") or durl[0].get("backup_url", [""])[0]

        if not audio_url:
            raise ValueError("无法获取音频/视频流URL")

        ctx.info("正在从音频中提取文本...")
        text = processor.extract_text_from_video_url(audio_url, context)

        ctx.info("文本提取完成!")
        return f"# {video_info['title']}\n\n{text}"

    except Exception as e:
        ctx.error(f"处理错误: {str(e)}")
        raise Exception(f"提取B站视频文本失败: {str(e)}")


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

        asr = create_asr_instance(api_key, model or DEFAULT_MODEL)

        result = asr.recognize_file(
            file_path=file_path,
            context=context,
            language=language,
            enable_lid=True,
            enable_itn=False
        )

        if result["success"]:
            return json.dumps({
                "status": "success",
                "text": result["text"],
                "language": result.get("language"),
                "usage": result.get("usage"),
                "request_id": result.get("request_id")
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "error": result["error"]
            }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"识别音频文件失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


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

        asr = create_asr_instance(api_key, model or DEFAULT_MODEL)

        result = asr.recognize_url(
            audio_url=audio_url,
            context=context,
            language=language,
            enable_lid=True,
            enable_itn=False
        )

        if result["success"]:
            return json.dumps({
                "status": "success",
                "text": result["text"],
                "language": result.get("language"),
                "usage": result.get("usage"),
                "request_id": result.get("request_id")
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "error": result["error"]
            }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"识别音频URL失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.resource("bilibili://video/{bvid}")
def get_video_resource(bvid: str) -> str:
    """通过BV号获取视频详细信息"""
    try:
        processor = BilibiliProcessor("")
        video_info = processor.parse_share_url(bvid)
        return json.dumps(video_info, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取视频信息失败: {str(e)}"


@mcp.prompt()
def bilibili_usage_guide() -> str:
    """B站视频解析使用指南"""
    return """
# B站视频解析使用指南

## 功能说明
这个MCP服务器提供B站视频的解析和文本提取功能：
1. 解析B站分享链接获取视频元数据（标题、封面、UP主、播放量等）
2. 获取视频/音频的下载链接（支持Dash流）
3. 使用AI语音识别从视频中提取文本内容
4. 支持本地音频文件和在线音频URL的识别

## 支持的链接格式
- **短链接**: `https://b23.tv/xxxxx`
- **完整链接**: `https://www.bilibili.com/video/BV1xx411c7mD`
- **直接BV号**: `BV1xx411c7mD`

## 环境变量
- `DASHSCOPE_API_KEY`: 阿里云百炼API密钥（文本提取功能必需）

## 工具说明
- `parse_bilibili_video_info`: 解析视频基本信息（无需API密钥）
- `get_bilibili_download_link`: 获取视频/音频下载链接（无需API密钥）
- `extract_bilibili_text`: 完整文本提取流程（需要API密钥）
- `recognize_audio_file`: 识别本地音频文件
- `recognize_audio_url`: 识别在线音频URL

## 语音识别
- 模型: qwen3-asr-flash
- 支持: 多语种、上下文增强、语种检测
- 格式: aac, amr, avi, aiff, flac, flv, m4a, mkv, mp3, mp4, mpeg, ogg, wav, webm, wma, wmv
"""


def main():
    """启动MCP服务器"""
    mcp.run()


if __name__ == "__main__":
    main()
