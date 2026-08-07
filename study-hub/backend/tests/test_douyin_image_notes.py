import pytest

from endpoints import automation


class ImageNoteProcessor:
    def __init__(self, _key):
        pass

    def parse_share_url(self, _input):
        return {
            "content_type": "image_note", "canonical_url": "https://www.iesdouyin.com/share/note/1",
            "title": "图集标题", "video_id": "1", "description": "图集文案", "author": "作者",
            "stats": {}, "image_urls": ["https://cdn.example/1.webp"],
        }


def test_image_note_uses_visual_analysis_and_skips_asr(monkeypatch):
    async def describe(data_urls, context):
        assert data_urls == ["https://cdn.example/1.webp"]
        assert "图集标题" in context
        return "可见的图文步骤"

    monkeypatch.setattr(automation, "DouyinProcessor", ImageNoteProcessor)
    monkeypatch.setattr(automation, "_download_douyin_images", lambda _urls: (["https://cdn.example/1.webp"], 0))
    monkeypatch.setattr(automation.ai_client, "describe_images", describe)

    raw = automation._extract_douyin_raw("https://v.douyin.com/note")

    assert raw["type"] == "图文"
    assert raw["visual_analysis"] == "可见的图文步骤"
    assert "asr_text" not in raw


def test_image_note_fails_when_images_cannot_be_downloaded(monkeypatch):
    monkeypatch.setattr(automation, "DouyinProcessor", ImageNoteProcessor)
    monkeypatch.setattr(automation, "_download_douyin_images", lambda _urls: ([], 1))

    with pytest.raises(RuntimeError, match="未能下载可供视觉分析的抖音图集图片"):
        automation._extract_douyin_raw("https://v.douyin.com/note")


def test_image_downloader_returns_validated_source_url_for_vision(monkeypatch):
    class Response:
        headers = {"Content-Type": "image/webp", "Content-Length": "2"}

        def raise_for_status(self):
            pass

        def iter_content(self, _chunk_size):
            yield b"ok"

    monkeypatch.setattr(automation.requests, "get", lambda *_args, **_kwargs: Response())

    image_urls, failures = automation._download_douyin_images(["https://cdn.example/1.webp"])

    assert image_urls == ["https://cdn.example/1.webp"]
    assert failures == 0
