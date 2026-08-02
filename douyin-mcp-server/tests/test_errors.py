#!/usr/bin/env python3
"""错误代号与日志模块测试"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from douyin_mcp_server.errors import (
    DouyinError,
    ERROR_CODE_MESSAGES,
    DY_1001_MISSING_API_KEY,
    DY_2001_NO_SHARE_LINK,
    DY_2002_HTTP_REQUEST_FAILED,
    DY_2003_HTML_PARSE_FAILED,
    DY_2004_JSON_PARSE_FAILED,
    DY_2005_INVALID_VIDEO_INFO,
    DY_3001_VIDEO_DOWNLOAD_FAILED,
    DY_3002_AUDIO_EXTRACT_FAILED,
    DY_3003_FILE_NOT_FOUND,
    DY_4001_ASR_CALL_FAILED,
    DY_4002_ASR_RECOGNITION_FAILED,
    DY_4003_ASR_EMPTY_RESULT,
    DY_4004_INVALID_AUDIO_URL,
    DY_9001_UNKNOWN,
    setup_logger,
    get_log_file_path,
    log_error,
    classify_exception,
)


class TestErrorCodes:
    """错误代号定义完整性测试"""

    def test_all_codes_have_messages(self):
        """所有错误代号都应有可读说明"""
        codes = [
            DY_1001_MISSING_API_KEY, DY_2001_NO_SHARE_LINK,
            DY_2002_HTTP_REQUEST_FAILED, DY_2003_HTML_PARSE_FAILED,
            DY_2004_JSON_PARSE_FAILED, DY_2005_INVALID_VIDEO_INFO,
            DY_3001_VIDEO_DOWNLOAD_FAILED, DY_3002_AUDIO_EXTRACT_FAILED,
            DY_3003_FILE_NOT_FOUND, DY_4001_ASR_CALL_FAILED,
            DY_4002_ASR_RECOGNITION_FAILED, DY_4003_ASR_EMPTY_RESULT,
            DY_4004_INVALID_AUDIO_URL, DY_9001_UNKNOWN,
        ]
        assert len(codes) == len(set(codes)), "错误代号必须唯一"
        for code in codes:
            assert code in ERROR_CODE_MESSAGES, f"缺少说明: {code}"
            assert ERROR_CODE_MESSAGES[code].strip(), f"说明为空: {code}"

    def test_code_format(self):
        """错误代号格式为 DY-XXXX"""
        for code in ERROR_CODE_MESSAGES:
            assert code.startswith("DY-"), f"代号格式错误: {code}"


class TestDouyinError:
    """DouyinError 异常类测试"""

    def test_default_message(self):
        err = DouyinError(DY_2001_NO_SHARE_LINK)
        assert err.error_code == DY_2001_NO_SHARE_LINK
        assert err.message == ERROR_CODE_MESSAGES[DY_2001_NO_SHARE_LINK]

    def test_custom_message_and_detail(self):
        err = DouyinError(DY_2002_HTTP_REQUEST_FAILED, message="自定义", detail="https://x.com: 404")
        assert err.message == "自定义"
        assert err.detail == "https://x.com: 404"

    def test_to_dict(self):
        err = DouyinError(DY_4002_ASR_RECOGNITION_FAILED, detail="boom")
        d = err.to_dict()
        assert d["error_code"] == DY_4002_ASR_RECOGNITION_FAILED
        assert d["error"] == ERROR_CODE_MESSAGES[DY_4002_ASR_RECOGNITION_FAILED]
        assert d["detail"] == "boom"

    def test_str_contains_code(self):
        err = DouyinError(DY_2001_NO_SHARE_LINK)
        assert "[DY-2001]" in str(err)


class TestClassifyException:
    """异常分类测试"""

    def test_passthrough_douyin_error(self):
        original = DouyinError(DY_2001_NO_SHARE_LINK)
        classified = classify_exception(original)
        assert classified is original

    def test_unknown_exception_fallback(self):
        classified = classify_exception(ValueError("random"))
        assert classified.error_code == DY_9001_UNKNOWN
        assert "random" in (classified.detail or "")


class TestLogging:
    """日志记录测试"""

    def test_log_file_created_and_contains_error_code(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DOUYIN_MCP_LOG_DIR", str(tmp_path))
        import douyin_mcp_server.errors as errors_mod

        logger = errors_mod.setup_logger("test-douyin")
        errors_mod.log_error(logger, DY_3002_AUDIO_EXTRACT_FAILED, "提取音频失败", context="file=1.mp4")

        log_file = tmp_path / "douyin-mcp-server.log"
        assert log_file.exists(), "日志文件应被创建"
        content = log_file.read_text(encoding="utf-8")
        assert "DY-3002" in content, "日志中应包含错误代号"
        assert "提取音频失败" in content, "日志中应包含错误消息"
        assert "file=1.mp4" in content, "日志中应包含上下文"

    def test_log_error_with_exception_has_traceback(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DOUYIN_MCP_LOG_DIR", str(tmp_path))
        import douyin_mcp_server.errors as errors_mod

        logger = errors_mod.setup_logger("test-douyin-exc")
        try:
            raise RuntimeError("模拟异常")
        except RuntimeError as e:
            errors_mod.log_error(logger, DY_4002_ASR_RECOGNITION_FAILED, "识别失败", exc=e)

        content = (tmp_path / "douyin-mcp-server.log").read_text(encoding="utf-8")
        assert "DY-4002" in content
        assert "RuntimeError" in content
        assert "模拟异常" in content
