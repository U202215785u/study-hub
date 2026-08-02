#!/usr/bin/env python3
"""MCP 工具错误响应结构测试（mock 网络，不实际调用抖音/API）"""

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import douyin_mcp_server.server as server_mod
from douyin_mcp_server.errors import (
    DY_1001_MISSING_API_KEY,
    DY_2001_NO_SHARE_LINK,
    DY_2002_HTTP_REQUEST_FAILED,
    DY_2003_HTML_PARSE_FAILED,
    DY_4002_ASR_RECOGNITION_FAILED,
    DouyinError,
)


class TestParseShareUrlErrorCodes:
    """parse_share_url 各失败场景的错误代号"""

    def test_no_link(self):
        with pytest.raises(DouyinError) as exc_info:
            server_mod.DouyinProcessor("").parse_share_url("没有链接的文本")
        assert exc_info.value.error_code == DY_2001_NO_SHARE_LINK

    def test_http_request_failed(self):
        import requests as req
        with mock.patch("requests.get", side_effect=req.ConnectionError("connection error")):
            with pytest.raises(DouyinError) as exc_info:
                server_mod.DouyinProcessor("").parse_share_url("https://v.douyin.com/abc123")
        assert exc_info.value.error_code == DY_2002_HTTP_REQUEST_FAILED

    def test_html_parse_failed(self):
        resp = mock.MagicMock()
        resp.raise_for_status.return_value = None
        resp.text = "<html>no router data</html>"
        # 第一次请求（分享短链）返回模拟，第二次（页面）也返回模拟
        with mock.patch("requests.get", return_value=resp):
            with pytest.raises(DouyinError) as exc_info:
                server_mod.DouyinProcessor("").parse_share_url("https://www.iesdouyin.com/share/video/123")
        assert exc_info.value.error_code == DY_2003_HTML_PARSE_FAILED


class TestToolsReturnErrorCode:
    """MCP 工具返回 JSON 中包含 error_code"""

    def test_get_douyin_download_link_no_link(self):
        result = server_mod.get_douyin_download_link("无链接文本")
        data = json.loads(result)
        assert data["status"] == "error"
        assert data["error_code"] == DY_2001_NO_SHARE_LINK

    def test_parse_douyin_video_info_no_link(self):
        result = server_mod.parse_douyin_video_info("无链接文本")
        data = json.loads(result)
        assert data["status"] == "error"
        assert data["error_code"] == DY_2001_NO_SHARE_LINK

    def test_recognize_audio_file_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        result = server_mod.recognize_audio_file("C:/不存在/1.wav")
        data = json.loads(result)
        assert data["status"] == "error"
        assert data["error_code"] == DY_1001_MISSING_API_KEY

    def test_recognize_audio_url_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        result = server_mod.recognize_audio_url("https://example.com/1.mp3")
        data = json.loads(result)
        assert data["status"] == "error"
        assert data["error_code"] == DY_1001_MISSING_API_KEY

    def test_extract_douyin_text_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

        class FakeCtx:
            def info(self, *a, **k):
                pass
            def error(self, *a, **k):
                pass

        import asyncio
        async def run():
            with pytest.raises(Exception) as exc_info:
                await server_mod.extract_douyin_text("https://v.douyin.com/abc", ctx=FakeCtx())
            return exc_info.value

        exc = asyncio.run(run())
        assert DY_1001_MISSING_API_KEY in str(exc)
