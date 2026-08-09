from endpoints import automation
import pytest


def test_verify_external_deps_reports_legacy_douyin_parser_as_incompatible(monkeypatch):
    monkeypatch.setattr(automation, "_douyin_mcp_version", lambda: "1.2.1", raising=False)

    report = automation.verify_external_deps()

    assert report["douyin_mcp"]["compatible"] is False
    assert "1.3.0" in report["douyin_mcp"]["warning"]


def test_verify_external_deps_reports_current_douyin_parser_as_compatible(monkeypatch):
    monkeypatch.setattr(automation, "_douyin_mcp_version", lambda: "1.3.0", raising=False)

    report = automation.verify_external_deps()

    assert report["douyin_mcp"]["compatible"] is True
    assert report["douyin_mcp"]["warning"] is None
    assert report["douyin_mcp"]["path"].endswith("server.py")


def test_extract_douyin_raw_explains_legacy_parser_contract_mismatch(monkeypatch):
    class LegacyProcessor:
        def __init__(self, _key):
            pass

        def parse_share_url(self, _input):
            return {"url": "https://cdn.example/video.mp4", "title": "Video", "video_id": "1"}

    monkeypatch.setattr(automation, "DouyinProcessor", LegacyProcessor)

    with pytest.raises(RuntimeError, match="抖音解析组件版本过旧"):
        automation._extract_douyin_raw("https://v.douyin.com/example")
