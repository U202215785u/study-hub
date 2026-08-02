#!/usr/bin/env python3
"""
douyin-mcp-server 错误代号与日志功能测试

覆盖:
1. errors.py 错误代号体系（DouyinError、分类、日志初始化）
2. asr_module.py 失败路径返回 error_code
3. server.py 各工具函数失败时返回 error_code 且写入日志文件
"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# 确保被测包可导入（tests 在项目根下）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from douyin_mcp_server import errors
from douyin_mcp_server.errors import (
    DouyinError,
    DY_1001_MISSING_API_KEY,
    DY_2001_NO_SHARE_LINK,
    DY_2002_HTTP_REQUEST_FAILED,
    DY_2003_HTML_PARSE_FAILED,
    DY_2004_JSON_PARSE_FAILED,
    DY_2005_INVALID_VIDEO_INFO,
    DY_3001_VIDEO_DOWNLOAD_FAILED,
    DY_3003_FILE_NOT_FOUND,
    DY_4001_ASR_CALL_FAILED,
    DY_4002_ASR_RECOGNITION_FAILED,
    DY_4003_ASR_EMPTY_RESULT,
    DY_9001_UNKNOWN,
    setup_logger,
    log_error,
    classify_exception,
)
from douyin_mcp_server import asr_module, server as server_module


# ---------- errors.py ----------

class TestErrors:
    def test_error_code_constants(self):
        assert DY_1001_MISSING_API_KEY.startswith("DY-")
        assert DY_9001_UNKNOWN == "DY-9001"
        # 所有已定义代号在消息表中有说明
        for code in [
            DY_1001_MISSING_API_KEY, DY_2001_NO_SHARE_LINK, DY_2002_HTTP_REQUEST_FAILED,
            DY_2003_HTML_PARSE_FAILED, DY_2004_JSON_PARSE_FAILED, DY_2005_INVALID_VIDEO_INFO,
            DY_3001_VIDEO_DOWNLOAD_FAILED, DY_3003_FILE_NOT_FOUND, DY_4001_ASR_CALL_FAILED,
            DY_4002_ASR_RECOGNITION_FAILED, DY_4003_ASR_EMPTY_RESULT, DY_9001_UNKNOWN,
        ]:
            assert code in errors.ERROR_CODE_MESSAGES, f"缺少 {code} 的说明"

    def test_douyin_error_str_and_dict(self):
        err = DouyinError(DY_2001_NO_SHARE_LINK, detail="test")
        assert str(err) == "[DY-2001] 分享文本中未找到有效的抖音链接（test）"
        d = err.to_dict()
        assert d["error_code"] == "DY-2001"
        assert d["error"]
        assert d["detail"] == "test"

    def test_classify_exception_passthrough(self):
        err = DouyinError(DY_2003_HTML_PARSE_FAILED)
        assert classify_exception(err) is err

    def test_classify_exception_unknown(self):
        wrapped = classify_exception(RuntimeError("boom"))
        assert wrapped.error_code == DY_9001_UNKNOWN

    def test_setup_logger_creates_file(self, tmp_path, monkeypatch):
        log_dir = tmp_path / "logs"
        monkeypatch.setenv("DOUYIN_MCP_LOG_DIR", str(log_dir))
        # 使用独立 logger 名称避免污染全局
        lg = setup_logger("test-logger-errors")
        assert lg is not None
        log_file = log_dir / "douyin-mcp-server.log"
        assert log_file.exists(), f"日志文件未创建: {log_file}"
        # 清理 handler，避免重复添加
        for h in lg.handlers:
            lg.removeHandler(h)

    def test_log_error_writes_entry(self, tmp_path, monkeypatch):
        log_dir = tmp_path / "logs"
        monkeypatch.setenv("DOUYIN_MCP_LOG_DIR", str(log_dir))
        lg = setup_logger("test-logger-entry")
        log_error(lg, DY_2002_HTTP_REQUEST_FAILED, "请求失败", exc=None, context="url=xxx")
        lg.handlers[0].flush() if lg.handlers else None
        content = (log_dir / "douyin-mcp-server.log").read_text(encoding="utf-8")
        assert "DY-2002" in content
        assert "请求失败" in content
        for h in lg.handlers:
            lg.removeHandler(h)


# ---------- asr_module.py ----------

class TestAsrModule:
    def test_recognize_file_not_found_has_error_code(self):
        asr = asr_module.QwenASR(api_key="test-key")
        result = asr.recognize_file(file_path="/no/such/file.mp3")
        assert result["success"] is False
        assert result["error_code"] == DY_3003_FILE_NOT_FOUND
        assert result["error"]

    @mock.patch("dashscope.MultiModalConversation.call")
    def test_recognize_api_error_has_error_code(self, mock_call):
        class FakeResponse:
            status_code = 401
            message = "InvalidApiKey"
        mock_call.return_value = FakeResponse()
        asr = asr_module.QwenASR(api_key="test-key")
        result = asr.recognize_audio("https://example.com/a.mp3")
        assert result["success"] is False
        assert result["error_code"] == DY_4001_ASR_CALL_FAILED

    @mock.patch("dashscope.MultiModalConversation.call")
    def test_recognize_exception_has_error_code(self, mock_call):
        mock_call.side_effect = ConnectionError("network down")
        asr = asr_module.QwenASR(api_key="test-key")
        result = asr.recognize_audio("https://example.com/a.mp3")
        assert result["success"] is False
        assert result["error_code"] == DY_4002_ASR_RECOGNITION_FAILED


# ---------- server.py ----------

class TestServerTools:
    def _call(self, fn, *args, **kwargs):
        """调用工具函数并把 MCP Context 替换为 stub。"""
        ctx = mock.MagicMock()
        if "ctx" in kwargs:
            kwargs["ctx"] = ctx
        return fn(*args, **kwargs), ctx

    def test_get_download_link_no_link_has_error_code(self):
        out, _ = self._call(server_module.get_douyin_download_link, "没有链接的文本")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == DY_2001_NO_SHARE_LINK

    @mock.patch("requests.get")
    def test_get_download_link_http_fail_has_error_code(self, mock_get):
        import requests as req
        mock_get.side_effect = req.ConnectionError("timeout")
        out, _ = self._call(server_module.get_douyin_download_link, "https://v.douyin.com/abc123/")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == DY_2002_HTTP_REQUEST_FAILED

    def test_parse_info_no_link_has_error_code(self):
        out, _ = self._call(server_module.parse_douyin_video_info, "随便一句话")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == DY_2001_NO_SHARE_LINK

    def test_extract_text_missing_api_key_has_error_code(self, monkeypatch):
        import asyncio
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        async def _run():
            with pytest.raises(Exception) as exc_info:
                await server_module.extract_douyin_text(
                    share_link="https://v.douyin.com/abc/", ctx=mock.MagicMock()
                )
            return exc_info.value
        exc = asyncio.run(_run())
        assert DY_1001_MISSING_API_KEY in str(exc)

    def test_recognize_audio_file_missing_api_key_has_error_code(self, monkeypatch):
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        out, _ = self._call(server_module.recognize_audio_file, file_path="x.mp3")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == DY_1001_MISSING_API_KEY

    def test_recognize_audio_url_missing_api_key_has_error_code(self, monkeypatch):
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        out, _ = self._call(server_module.recognize_audio_url, audio_url="https://x.com/a.mp3")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == DY_1001_MISSING_API_KEY

    @mock.patch("douyin_mcp_server.server.os.getenv", return_value="test-key")
    @mock.patch("douyin_mcp_server.server.create_asr_instance")
    def test_recognize_audio_file_not_found_has_error_code(self, mock_asr, mock_env):
        fake_asr = mock.MagicMock()
        fake_asr.recognize_file.return_value = {
            "success": False,
            "error_code": DY_3003_FILE_NOT_FOUND,
            "error": "音频/视频文件不存在",
            "detail": "/no/such.mp3",
        }
        mock_asr.return_value = fake_asr
        out, _ = self._call(server_module.recognize_audio_file, file_path="/no/such.mp3")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == DY_3003_FILE_NOT_FOUND

    @mock.patch("douyin_mcp_server.server.os.getenv", return_value="test-key")
    @mock.patch("douyin_mcp_server.server.create_asr_instance")
    def test_recognize_audio_url_asr_fail_has_error_code(self, mock_asr, mock_env):
        fake_asr = mock.MagicMock()
        fake_asr.recognize_url.return_value = {
            "success": False,
            "error_code": DY_4001_ASR_CALL_FAILED,
            "error": "调用语音识别 API 失败",
            "detail": "HTTP 500",
        }
        mock_asr.return_value = fake_asr
        out, _ = self._call(server_module.recognize_audio_url, audio_url="https://x.com/a.mp3")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == DY_4001_ASR_CALL_FAILED

    def test_douyin_processor_no_link_raises_code(self):
        proc = server_module.DouyinProcessor("")
        with pytest.raises(DouyinError) as exc_info:
            proc.parse_share_url("无链接文本")
        assert exc_info.value.error_code == DY_2001_NO_SHARE_LINK


# ---------- 日志文件集成验证 ----------

class TestLogFileIntegration:
    def test_tool_error_writes_log_file(self, tmp_path, monkeypatch):
        log_dir = tmp_path / "logs"
        monkeypatch.setenv("DOUYIN_MCP_LOG_DIR", str(log_dir))
        # 重新初始化测试专用 logger（独立名称），避免与全局 logger 混淆
        lg = setup_logger("test-logger-integration")
        log_error(lg, DY_2002_HTTP_REQUEST_FAILED, "请求分享链接失败", exc=ConnectionError("boom"), context="share_text=https://x")
        log_file = log_dir / "douyin-mcp-server.log"
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "DY-2002" in content
        assert "ConnectionError" in content
        assert "boom" in content
        for h in lg.handlers:
            lg.removeHandler(h)
