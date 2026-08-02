#!/usr/bin/env python3
"""
抖音 MCP 服务器错误代号与日志模块

统一错误代号（error_code）与日志记录，便于排查识别失败问题。

错误代号格式：DY-XXXX（DY = DouYin）
- DY-1000 系列：环境/配置类错误
- DY-2000 系列：链接解析类错误
- DY-3000 系列：下载/音频提取类错误
- DY-4000 系列：语音识别（ASR）类错误
- DY-9000 系列：未知/兜底错误
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, Type

# ---------- 错误代号定义 ----------

# 环境/配置类
DY_1001_MISSING_API_KEY = "DY-1001"      # 未设置 DASHSCOPE_API_KEY
DY_1002_INVALID_MODEL = "DY-1002"        # 指定的模型名无效

# 链接解析类
DY_2001_NO_SHARE_LINK = "DY-2001"        # 分享文本中未找到有效链接
DY_2002_HTTP_REQUEST_FAILED = "DY-2002"  # 请求分享/视频页面失败（网络或状态码错误）
DY_2003_HTML_PARSE_FAILED = "DY-2003"    # 从 HTML 中解析 _ROUTER_DATA 失败
DY_2004_JSON_PARSE_FAILED = "DY-2004"    # 从 JSON 中解析视频信息失败
DY_2005_INVALID_VIDEO_INFO = "DY-2005"   # 视频信息字段缺失/格式异常

# 下载/音频提取类
DY_3001_VIDEO_DOWNLOAD_FAILED = "DY-3001"  # 视频下载失败
DY_3002_AUDIO_EXTRACT_FAILED = "DY-3002"   # ffmpeg 提取音频失败
DY_3003_FILE_NOT_FOUND = "DY-3003"         # 音频/视频文件不存在

# ASR 识别类
DY_4001_ASR_CALL_FAILED = "DY-4001"    # 调用 DashScope ASR API 失败（非 200）
DY_4002_ASR_RECOGNITION_FAILED = "DY-4002"  # 识别过程异常/识别结果为空
DY_4003_ASR_EMPTY_RESULT = "DY-4003"    # 识别成功但无文本内容
DY_4004_INVALID_AUDIO_URL = "DY-4004"   # 音频 URL 无效（本地文件不存在或非法路径）

# 兜底
DY_9001_UNKNOWN = "DY-9001"  # 未知/未分类错误

# 错误代号 -> 人类可读说明（供日志与返回信息使用）
ERROR_CODE_MESSAGES = {
    DY_1001_MISSING_API_KEY: "未设置环境变量 DASHSCOPE_API_KEY",
    DY_1002_INVALID_MODEL: "指定的语音识别模型无效",
    DY_2001_NO_SHARE_LINK: "分享文本中未找到有效的抖音链接",
    DY_2002_HTTP_REQUEST_FAILED: "请求抖音页面失败（网络错误或 HTTP 状态码异常）",
    DY_2003_HTML_PARSE_FAILED: "从 HTML 中解析视频信息失败（链接可能已过期或抖音限制访问）",
    DY_2004_JSON_PARSE_FAILED: "从 JSON 数据中解析视频/图集信息失败",
    DY_2005_INVALID_VIDEO_INFO: "视频信息字段缺失或格式异常",
    DY_3001_VIDEO_DOWNLOAD_FAILED: "视频下载失败",
    DY_3002_AUDIO_EXTRACT_FAILED: "使用 ffmpeg 提取音频失败",
    DY_3003_FILE_NOT_FOUND: "音频/视频文件不存在",
    DY_4001_ASR_CALL_FAILED: "调用语音识别 API 失败",
    DY_4002_ASR_RECOGNITION_FAILED: "语音识别过程出现异常",
    DY_4003_ASR_EMPTY_RESULT: "语音识别完成但未识别到文本内容",
    DY_4004_INVALID_AUDIO_URL: "音频 URL 无效（本地文件不存在或路径非法）",
    DY_9001_UNKNOWN: "未知错误",
}


class DouyinError(Exception):
    """携带错误代号的抖音工具异常。

    属性:
        error_code: 错误代号，如 "DY-2001"
        message: 可读错误说明
        detail: 原始异常/详细上下文（可选）
    """

    def __init__(self, error_code: str, message: Optional[str] = None, detail: Optional[str] = None):
        self.error_code = error_code
        self.message = message or ERROR_CODE_MESSAGES.get(error_code, "未知错误")
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """转换为结构化错误字典（含代号与说明）。"""
        result = {
            "error_code": self.error_code,
            "error": self.message,
        }
        if self.detail:
            result["detail"] = self.detail
        return result

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}" + (f"（{self.detail}）" if self.detail else "")


# ---------- 日志配置 ----------

_DEFAULT_LOG_DIR_ENV = "DOUYIN_MCP_LOG_DIR"  # 可通过环境变量指定日志目录


def default_log_dir() -> Path:
    """返回默认日志目录：优先环境变量，否则系统临时目录下的 douyin-mcp-server。"""
    env_dir = os.getenv(_DEFAULT_LOG_DIR_ENV)
    if env_dir:
        return Path(env_dir)
    return Path(tempfile.gettempdir()) / "douyin-mcp-server"


def get_log_dir() -> Path:
    """获取并确保日志目录存在。"""
    log_dir = default_log_dir()
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # 目录创建失败时回退到系统临时目录根，保证日志不丢
        log_dir = Path(tempfile.gettempdir())
    return log_dir


def get_log_file_path() -> Path:
    """日志文件路径：<log_dir>/douyin-mcp-server.log"""
    return get_log_dir() / "douyin-mcp-server.log"


def setup_logger(name: str = "douyin-mcp-server") -> logging.Logger:
    """配置并返回日志器：同时输出到控制台(stderr)与日志文件。

    日志文件默认位置: <DOUYIN_MCP_LOG_DIR 或 系统临时目录>/douyin-mcp-server/douyin-mcp-server.log
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # 已初始化

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出（stderr）
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    # 文件输出
    try:
        file_handler = logging.FileHandler(str(get_log_file_path()), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
        logger.debug("日志文件: %s", get_log_file_path())
    except OSError as e:
        logger.warning("无法创建日志文件 %s: %s", get_log_file_path(), e)

    return logger


def log_error(logger: logging.Logger, error_code: str, message: str,
              exc: Optional[BaseException] = None, context: Optional[str] = None):
    """记录带错误代号与上下文（含堆栈）的错误日志。"""
    detail = f" | context={context}" if context else ""
    if exc is not None:
        logger.error("[%s] %s%s | cause=%s: %s", error_code, message, detail,
                     type(exc).__name__, exc, exc_info=exc)
    else:
        logger.error("[%s] %s%s", error_code, message, detail)


def classify_exception(e: BaseException) -> "DouyinError":
    """将任意异常归类为携带错误代号的 DouyinError（未识别类型时使用 DY-9001 兜底）。

    若 e 本身就是 DouyinError，直接返回。
    """
    if isinstance(e, DouyinError):
        return e
    if isinstance(e, ValueError):
        # ValueError 无法区分具体场景，交由调用方捕获时补充上下文；
        # 此处兜底为未知错误，调用方可覆盖。
        return DouyinError(DY_9001_UNKNOWN, detail=str(e))
    return DouyinError(DY_9001_UNKNOWN, detail=str(e))


__all__ = [
    "DouyinError",
    "ERROR_CODE_MESSAGES",
    "DY_1001_MISSING_API_KEY",
    "DY_1002_INVALID_MODEL",
    "DY_2001_NO_SHARE_LINK",
    "DY_2002_HTTP_REQUEST_FAILED",
    "DY_2003_HTML_PARSE_FAILED",
    "DY_2004_JSON_PARSE_FAILED",
    "DY_2005_INVALID_VIDEO_INFO",
    "DY_3001_VIDEO_DOWNLOAD_FAILED",
    "DY_3002_AUDIO_EXTRACT_FAILED",
    "DY_3003_FILE_NOT_FOUND",
    "DY_4001_ASR_CALL_FAILED",
    "DY_4002_ASR_RECOGNITION_FAILED",
    "DY_4003_ASR_EMPTY_RESULT",
    "DY_4004_INVALID_AUDIO_URL",
    "DY_9001_UNKNOWN",
    "setup_logger",
    "get_log_dir",
    "get_log_file_path",
    "log_error",
    "classify_exception",
]
