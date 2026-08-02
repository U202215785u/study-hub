#!/usr/bin/env python3
"""
抖音无水印视频下载并提取文本的 MCP 服务器

该服务器提供以下功能：
1. 解析抖音分享链接获取无水印视频链接
2. 下载视频并提取音频
3. 从音频中提取文本内容
4. 自动清理中间文件
"""

import os
import re
import json
import requests
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Tuple
import ffmpeg
from tqdm.asyncio import tqdm
from urllib import request
from http import HTTPStatus
import dashscope

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context
from .asr_module import QwenASR, create_asr_instance
from .errors import (
    DouyinError,
    DY_1001_MISSING_API_KEY,
    DY_2001_NO_SHARE_LINK,
    DY_2002_HTTP_REQUEST_FAILED,
    DY_2003_HTML_PARSE_FAILED,
    DY_2004_JSON_PARSE_FAILED,
    DY_2005_INVALID_VIDEO_INFO,
    DY_3001_VIDEO_DOWNLOAD_FAILED,
    DY_3002_AUDIO_EXTRACT_FAILED,
    DY_4002_ASR_RECOGNITION_FAILED,
    DY_4003_ASR_EMPTY_RESULT,
    setup_logger,
    log_error,
    classify_exception,
)

logger = setup_logger()


# 创建 MCP 服务器实例
mcp = FastMCP("Douyin MCP Server", 
              dependencies=["requests", "ffmpeg-python", "tqdm", "dashscope"])

# 请求头，模拟移动端访问
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 Version/17.0 Mobile/15E148 Safari/604.1'
}


# 默认 API 配置
DEFAULT_MODEL = "qwen3-asr-flash"

class DouyinProcessor:
    """抖音视频处理器"""
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.temp_dir = Path(tempfile.mkdtemp())
        self._asr = None  # ASR 实例懒加载，解析/下载无需 API 密钥
    
    def _get_asr(self) -> QwenASR:
        """懒创建 ASR 实例（仅识别时需要），未配置密钥时给出明确错误代号。"""
        if self._asr is None:
            if not self.api_key:
                raise DouyinError(DY_1001_MISSING_API_KEY, detail="请在配置中添加阿里云百炼API密钥")
            dashscope.api_key = self.api_key
            self._asr = create_asr_instance(self.api_key, self.model)
        return self._asr
    
    def __del__(self):
        """清理临时目录"""
        import shutil
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def parse_share_url(self, share_text: str) -> dict:
        """从分享文本中提取无水印视频链接"""
        # 提取分享链接
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', share_text)
        if not urls:
            log_error(logger, DY_2001_NO_SHARE_LINK, "未找到有效的分享链接", context=f"share_text={share_text[:120]}")
            raise DouyinError(DY_2001_NO_SHARE_LINK)

        share_url = urls[0]
        try:
            share_response = requests.get(share_url, headers=HEADERS)
            share_response.raise_for_status()
        except requests.RequestException as e:
            log_error(logger, DY_2002_HTTP_REQUEST_FAILED, f"请求分享链接失败: {share_url}", exc=e)
            raise DouyinError(DY_2002_HTTP_REQUEST_FAILED, detail=f"{share_url}: {e}") from e
        video_id = share_response.url.split("?")[0].strip("/").split("/")[-1]
        share_url = f'https://www.iesdouyin.com/share/video/{video_id}'

        # 获取视频页面内容
        try:
            response = requests.get(share_url, headers=HEADERS)
            response.raise_for_status()
        except requests.RequestException as e:
            log_error(logger, DY_2002_HTTP_REQUEST_FAILED, f"请求视频页面失败: {share_url}", exc=e)
            raise DouyinError(DY_2002_HTTP_REQUEST_FAILED, detail=f"{share_url}: {e}") from e

        pattern = re.compile(
            pattern=r"window\._ROUTER_DATA\s*=\s*(.*?)</script>",
            flags=re.DOTALL,
        )
        find_res = pattern.search(response.text)

        if not find_res or not find_res.group(1):
            log_error(logger, DY_2003_HTML_PARSE_FAILED, "从HTML中解析视频信息失败", context=f"url={share_url}")
            raise DouyinError(DY_2003_HTML_PARSE_FAILED)

        # 解析JSON数据
        try:
            json_data = json.loads(find_res.group(1).strip())
        except json.JSONDecodeError as e:
            log_error(logger, DY_2004_JSON_PARSE_FAILED, "JSON 数据解析失败", exc=e, context=f"url={share_url}")
            raise DouyinError(DY_2004_JSON_PARSE_FAILED, detail=str(e)) from e
        VIDEO_ID_PAGE_KEY = "video_(id)/page"
        NOTE_ID_PAGE_KEY = "note_(id)/page"

        loader_data = json_data.get("loaderData", {})
        if VIDEO_ID_PAGE_KEY in loader_data:
            original_video_info = loader_data[VIDEO_ID_PAGE_KEY].get("videoInfoRes")
        elif NOTE_ID_PAGE_KEY in loader_data:
            original_video_info = loader_data[NOTE_ID_PAGE_KEY].get("videoInfoRes")
        else:
            log_error(logger, DY_2004_JSON_PARSE_FAILED, "无法从JSON中解析视频或图集信息", context=f"url={share_url}")
            raise DouyinError(DY_2004_JSON_PARSE_FAILED, detail="loaderData 中未找到 video/note 页面键")

        if not original_video_info or not original_video_info.get("item_list"):
            log_error(logger, DY_2005_INVALID_VIDEO_INFO, "视频信息缺失或格式异常", context=f"url={share_url}")
            raise DouyinError(DY_2005_INVALID_VIDEO_INFO)

        data = original_video_info["item_list"][0]

        # 获取视频信息
        try:
            video_url = data["video"]["play_addr"]["url_list"][0].replace("playwm", "play")
        except (KeyError, IndexError, TypeError) as e:
            log_error(logger, DY_2005_INVALID_VIDEO_INFO, "视频播放地址缺失", exc=e, context=f"url={share_url}")
            raise DouyinError(DY_2005_INVALID_VIDEO_INFO, detail="video.play_addr.url_list 缺失") from e
        desc = data.get("desc", "").strip() or f"douyin_{video_id}"
        
        # 替换文件名中的非法字符
        desc = re.sub(r'[\\/:*?"<>|]', '_', desc)
        
        return {
            "url": video_url,
            "title": desc,
            "video_id": video_id
        }
    
    async def download_video(self, video_info: dict, ctx: Context) -> Path:
        """异步下载视频到临时目录"""
        filename = f"{video_info['video_id']}.mp4"
        filepath = self.temp_dir / filename
        
        ctx.info(f"正在下载视频: {video_info['title']}")
        logger.info("开始下载视频: id=%s title=%s", video_info['video_id'], video_info['title'])
        
        try:
            response = requests.get(video_info['url'], headers=HEADERS, stream=True)
            response.raise_for_status()
        except requests.RequestException as e:
            log_error(logger, DY_3001_VIDEO_DOWNLOAD_FAILED, f"视频下载请求失败: {video_info['url']}", exc=e)
            raise DouyinError(DY_3001_VIDEO_DOWNLOAD_FAILED, detail=str(e)) from e
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        
        # 异步下载文件，显示进度
        try:
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = downloaded / total_size
                            await ctx.report_progress(downloaded, total_size)
        except OSError as e:
            log_error(logger, DY_3001_VIDEO_DOWNLOAD_FAILED, f"视频写入磁盘失败: {filepath}", exc=e)
            raise DouyinError(DY_3001_VIDEO_DOWNLOAD_FAILED, detail=str(e)) from e
        
        ctx.info(f"视频下载完成: {filepath}")
        logger.info("视频下载完成: %s", filepath)
        return filepath
    
    def extract_text_from_audio_file(self, audio_path: Path, context: Optional[str] = None) -> str:
        """从本地音频文件中提取文字"""
        try:
            result = self._get_asr().recognize_file(
                file_path=audio_path,
                context=context,
                language="zh",
                enable_lid=True,
                enable_itn=False
            )
            
            if result["success"]:
                text = result.get("text") or ""
                if not text.strip():
                    raise DouyinError(DY_4003_ASR_EMPTY_RESULT)
                return text
            else:
                raise DouyinError(
                    result.get("error_code", DY_4002_ASR_RECOGNITION_FAILED),
                    detail=result.get("error", result.get("detail", "")),
                )
                
        except DouyinError:
            raise
        except Exception as e:
            log_error(logger, DY_4002_ASR_RECOGNITION_FAILED, "从音频文件提取文字时出错", exc=e, context=f"file={audio_path}")
            raise DouyinError(DY_4002_ASR_RECOGNITION_FAILED, detail=str(e)) from e
    
    def extract_audio(self, video_path: Path) -> Path:
        """从视频文件中提取音频"""
        audio_path = video_path.with_suffix('.wav')
        
        try:
            (
                ffmpeg
                .input(str(video_path))
                .output(str(audio_path), acodec='pcm_s16le', ac=1, ar=16000)
                .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
            )
            return audio_path
        except Exception as e:
            log_error(logger, DY_3002_AUDIO_EXTRACT_FAILED, f"提取音频失败: {video_path}", exc=e)
            raise DouyinError(DY_3002_AUDIO_EXTRACT_FAILED, detail=str(e)) from e
    
    def extract_text_from_video_url(self, video_url: str, context: Optional[str] = None) -> str:
        """从视频URL中提取文字（使用Qwen-3-ASR-Flash模型）"""
        try:
            # 使用新的ASR模块进行识别
            result = self._get_asr().recognize_url(
                audio_url=video_url,
                context=context,
                language="zh",  # 默认中文，也支持自动检测
                enable_lid=True,  # 启用语种识别
                enable_itn=False  # 不启用逆文本规范化
            )
            
            if result["success"]:
                text = result.get("text") or ""
                if not text.strip():
                    raise DouyinError(DY_4003_ASR_EMPTY_RESULT)
                return text
            else:
                raise DouyinError(
                    result.get("error_code", DY_4002_ASR_RECOGNITION_FAILED),
                    detail=result.get("error", result.get("detail", "")),
                )
                
        except DouyinError:
            raise
        except Exception as e:
            log_error(logger, DY_4002_ASR_RECOGNITION_FAILED, "提取文字时出错", exc=e, context=f"url={video_url[:120]}")
            raise DouyinError(DY_4002_ASR_RECOGNITION_FAILED, detail=str(e)) from e
    
    def cleanup_files(self, *file_paths: Path):
        """清理指定的文件"""
        for file_path in file_paths:
            if file_path.exists():
                file_path.unlink()


@mcp.tool()
def get_douyin_download_link(share_link: str) -> str:
    """
    获取抖音视频的无水印下载链接
    
    参数:
    - share_link: 抖音分享链接或包含链接的文本
    
    返回:
    - 包含下载链接和视频信息的JSON字符串
    """
    try:
        processor = DouyinProcessor("")  # 获取下载链接不需要API密钥
        video_info = processor.parse_share_url(share_link)
        
        logger.info("获取下载链接成功: video_id=%s", video_info["video_id"])
        return json.dumps({
            "status": "success",
            "video_id": video_info["video_id"],
            "title": video_info["title"],
            "download_url": video_info["url"],
            "description": f"视频标题: {video_info['title']}",
            "usage_tip": "可以直接使用此链接下载无水印视频"
        }, ensure_ascii=False, indent=2)
        
    except DouyinError as e:
        log_error(logger, e.error_code, e.message, exc=e, context=f"share_link={share_link[:120]}")
        return json.dumps({
            "status": "error",
            "error_code": e.error_code,
            "error": e.message,
            "detail": e.detail,
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        err = classify_exception(e)
        log_error(logger, err.error_code, err.message, exc=e, context=f"share_link={share_link[:120]}")
        return json.dumps({
            "status": "error",
            "error_code": err.error_code,
            "error": f"获取下载链接失败: {err.message}",
            "detail": err.detail,
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def extract_douyin_text(
    share_link: str,
    model: Optional[str] = None,
    context: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    从抖音分享链接提取视频中的文本内容
    
    参数:
    - share_link: 抖音分享链接或包含链接的文本
    - model: 语音识别模型（可选，默认使用qwen3-asr-flash）
    - context: 上下文文本，用于提高识别准确率（可选）
    
    返回:
    - 提取的文本内容
    
    注意: 需要设置环境变量 DASHSCOPE_API_KEY
    """
    try:
        # 从环境变量获取API密钥
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            log_error(logger, DY_1001_MISSING_API_KEY, "未设置环境变量 DASHSCOPE_API_KEY")
            raise DouyinError(DY_1001_MISSING_API_KEY, detail="请在配置中添加阿里云百炼API密钥")
        
        processor = DouyinProcessor(api_key, model)
        
        # 解析视频链接
        ctx.info("正在解析抖音分享链接...")
        video_info = processor.parse_share_url(share_link)
        
        # 直接使用视频URL进行文本提取，支持上下文增强
        ctx.info("正在从视频中提取文本...")
        text_content = processor.extract_text_from_video_url(video_info['url'], context)
        
        ctx.info("文本提取完成!")
        logger.info("抖音文本提取成功: video_id=%s chars=%d", video_info["video_id"], len(text_content))
        return text_content
        
    except DouyinError as e:
        log_error(logger, e.error_code, e.message, exc=e, context=f"share_link={share_link[:120]}")
        ctx.error(f"[{e.error_code}] 处理过程中出现错误: {e.message}")
        raise Exception(f"[{e.error_code}] 提取抖音视频文本失败: {e.message}" + (f"（{e.detail}）" if e.detail else ""))
    except Exception as e:
        err = classify_exception(e)
        log_error(logger, err.error_code, err.message, exc=e, context=f"share_link={share_link[:120]}")
        ctx.error(f"[{err.error_code}] 处理过程中出现错误: {err.message}")
        raise Exception(f"[{err.error_code}] 提取抖音视频文本失败: {err.message}")


@mcp.tool()
def parse_douyin_video_info(share_link: str) -> str:
    """
    解析抖音分享链接，获取视频基本信息
    
    参数:
    - share_link: 抖音分享链接或包含链接的文本
    
    返回:
    - 视频信息（JSON格式字符串）
    """
    try:
        processor = DouyinProcessor("")  # 不需要API密钥来解析链接
        video_info = processor.parse_share_url(share_link)
        
        logger.info("解析视频信息成功: video_id=%s", video_info["video_id"])
        return json.dumps({
            "video_id": video_info["video_id"],
            "title": video_info["title"],
            "download_url": video_info["url"],
            "status": "success"
        }, ensure_ascii=False, indent=2)
        
    except DouyinError as e:
        log_error(logger, e.error_code, e.message, exc=e, context=f"share_link={share_link[:120]}")
        return json.dumps({
            "status": "error",
            "error_code": e.error_code,
            "error": e.message,
            "detail": e.detail,
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        err = classify_exception(e)
        log_error(logger, err.error_code, err.message, exc=e, context=f"share_link={share_link[:120]}")
        return json.dumps({
            "status": "error",
            "error_code": err.error_code,
            "error": err.message,
            "detail": err.detail,
        }, ensure_ascii=False, indent=2)


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
        # 从环境变量获取API密钥
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            log_error(logger, DY_1001_MISSING_API_KEY, "未设置环境变量 DASHSCOPE_API_KEY")
            raise DouyinError(DY_1001_MISSING_API_KEY, detail="请在配置中添加阿里云百炼API密钥")
        
        # 创建ASR实例
        asr = create_asr_instance(api_key, model or DEFAULT_MODEL)
        
        # 识别音频文件
        result = asr.recognize_file(
            file_path=file_path,
            context=context,
            language=language,
            enable_lid=True,
            enable_itn=False
        )
        
        if result["success"]:
            logger.info("音频文件识别成功: file=%s chars=%d", file_path, len(result.get("text") or ""))
            return json.dumps({
                "status": "success",
                "text": result["text"],
                "language": result.get("language"),
                "usage": result.get("usage"),
                "request_id": result.get("request_id")
            }, ensure_ascii=False, indent=2)
        else:
            err = DouyinError(
                result.get("error_code", DY_4002_ASR_RECOGNITION_FAILED),
                detail=result.get("error", result.get("detail", "")),
            )
            log_error(logger, err.error_code, err.message, context=f"file={file_path}")
            return json.dumps({
                "status": "error",
                "error_code": err.error_code,
                "error": err.message,
                "detail": err.detail,
            }, ensure_ascii=False, indent=2)
            
    except DouyinError as e:
        log_error(logger, e.error_code, e.message, exc=e, context=f"file={file_path}")
        return json.dumps({
            "status": "error",
            "error_code": e.error_code,
            "error": f"识别音频文件失败: {e.message}",
            "detail": e.detail,
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        err = classify_exception(e)
        log_error(logger, err.error_code, err.message, exc=e, context=f"file={file_path}")
        return json.dumps({
            "status": "error",
            "error_code": err.error_code,
            "error": f"识别音频文件失败: {err.message}",
            "detail": err.detail,
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
        # 从环境变量获取API密钥
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            log_error(logger, DY_1001_MISSING_API_KEY, "未设置环境变量 DASHSCOPE_API_KEY")
            raise DouyinError(DY_1001_MISSING_API_KEY, detail="请在配置中添加阿里云百炼API密钥")
        
        # 创建ASR实例
        asr = create_asr_instance(api_key, model or DEFAULT_MODEL)
        
        # 识别音频URL
        result = asr.recognize_url(
            audio_url=audio_url,
            context=context,
            language=language,
            enable_lid=True,
            enable_itn=False
        )
        
        if result["success"]:
            logger.info("音频URL识别成功: url=%s chars=%d", audio_url[:120], len(result.get("text") or ""))
            return json.dumps({
                "status": "success",
                "text": result["text"],
                "language": result.get("language"),
                "usage": result.get("usage"),
                "request_id": result.get("request_id")
            }, ensure_ascii=False, indent=2)
        else:
            err = DouyinError(
                result.get("error_code", DY_4002_ASR_RECOGNITION_FAILED),
                detail=result.get("error", result.get("detail", "")),
            )
            log_error(logger, err.error_code, err.message, context=f"url={audio_url[:120]}")
            return json.dumps({
                "status": "error",
                "error_code": err.error_code,
                "error": err.message,
                "detail": err.detail,
            }, ensure_ascii=False, indent=2)
            
    except DouyinError as e:
        log_error(logger, e.error_code, e.message, exc=e, context=f"url={audio_url[:120]}")
        return json.dumps({
            "status": "error",
            "error_code": e.error_code,
            "error": f"识别音频URL失败: {e.message}",
            "detail": e.detail,
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        err = classify_exception(e)
        log_error(logger, err.error_code, err.message, exc=e, context=f"url={audio_url[:120]}")
        return json.dumps({
            "status": "error",
            "error_code": err.error_code,
            "error": f"识别音频URL失败: {err.message}",
            "detail": err.detail,
        }, ensure_ascii=False, indent=2)


@mcp.resource("douyin://video/{video_id}")
def get_video_info(video_id: str) -> str:
    """
    获取指定视频ID的详细信息
    
    参数:
    - video_id: 抖音视频ID
    
    返回:
    - 视频详细信息
    """
    share_url = f"https://www.iesdouyin.com/share/video/{video_id}"
    try:
        processor = DouyinProcessor("")
        video_info = processor.parse_share_url(share_url)
        return json.dumps(video_info, ensure_ascii=False, indent=2)
    except DouyinError as e:
        log_error(logger, e.error_code, e.message, exc=e, context=f"video_id={video_id}")
        return f"获取视频信息失败: [{e.error_code}] {e.message}"
    except Exception as e:
        err = classify_exception(e)
        log_error(logger, err.error_code, err.message, exc=e, context=f"video_id={video_id}")
        return f"获取视频信息失败: [{err.error_code}] {err.message}"


@mcp.prompt()
def douyin_text_extraction_guide() -> str:
    """抖音视频文本提取使用指南"""
    return """
# 抖音视频文本提取使用指南

## 功能说明
这个MCP服务器提供强大的语音识别功能，支持：
1. 从抖音分享链接中提取视频的文本内容
2. 识别本地音频文件中的文本
3. 识别在线音频URL中的文本
4. 获取无水印视频下载链接
5. 上下文增强功能提高识别准确率

## 环境变量配置
请确保设置了以下环境变量：
- `DASHSCOPE_API_KEY`: 阿里云百炼API密钥

## 语音识别模型
- **默认模型**: qwen3-asr-flash（Qwen-3-ASR-Flash）
- **功能特性**: 
  - 多语种高精度识别（普通话及多种方言，如粤语、四川话等）
  - 复杂环境适应，支持自动语种检测与智能非人声过滤
  - 高精度歌唱识别，即使在伴随背景音乐的情况下也能准确转写
  - 上下文增强功能，通过配置上下文提高识别准确率

## 使用步骤
1. 复制抖音视频的分享链接或准备音频文件/URL
2. 在Claude Desktop配置中设置环境变量 DASHSCOPE_API_KEY
3. 使用相应的工具进行操作

## 工具说明
### 抖音视频处理
- `extract_douyin_text`: 完整的文本提取流程，支持上下文增强（需要API密钥）
- `get_douyin_download_link`: 获取无水印视频下载链接（无需API密钥）
- `parse_douyin_video_info`: 仅解析视频基本信息

### 音频识别
- `recognize_audio_file`: 识别本地音频文件中的文本，支持上下文增强
- `recognize_audio_url`: 识别在线音频URL中的文本，支持上下文增强

### 资源
- `douyin://video/{video_id}`: 获取指定视频的详细信息

## 上下文增强使用技巧
通过提供相关的上下文文本，可以显著提高识别准确率，特别是对于：
- 专有名词、人名、地名
- 特定领域术语
- 品牌名称、产品名称

### 上下文格式示例：
- 词表格式: "苹果、华为、小米、vivo"
- 自然语言: "这是一段关于手机品牌的介绍，主要涉及苹果iPhone、华为Mate系列等产品"

## Claude Desktop 配置示例
```json
{
  "mcpServers": {
    "douyin-mcp": {
      "command": "uvx",
      "args": ["douyin-mcp-server"],
      "env": {
        "DASHSCOPE_API_KEY": "your-dashscope-api-key-here"
      }
    }
  }
}
```

## 支持的音频格式
aac、amr、avi、aiff、flac、flv、m4a、mkv、mp3、mp4、mpeg、ogg、opus、wav、webm、wma、wmv

## 注意事项
- 需要提供有效的阿里云百炼API密钥（通过环境变量）
- 使用阿里云百炼的qwen3-asr-flash模型进行语音识别
- 音频文件大小不超过10MB，且时长不超过3分钟
- 音频采样率要求16kHz，单声道
- 获取下载链接无需API密钥
"""


def main():
    """启动MCP服务器"""
    mcp.run()


if __name__ == "__main__":
    main()