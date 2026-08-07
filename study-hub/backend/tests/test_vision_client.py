import pytest

import ai_client as module
from ai_client import AIClient, RecoverableVisionError, VisionServiceError


def test_vision_messages_include_image_data_urls():
    assert AIClient()._vision_messages(["data:image/webp;base64,AA=="], "图集说明") == [{
        "role": "user",
        "content": [
            {"type": "text", "text": "图集说明"},
            {"type": "image_url", "image_url": {"url": "data:image/webp;base64,AA=="}},
        ],
    }]


@pytest.mark.asyncio
async def test_describe_images_uses_fallback_after_recoverable_primary_failure(monkeypatch):
    client = AIClient()
    calls = []

    async def fake_vision_chat(config, *_args):
        calls.append(config["model"])
        if config["model"] == "primary":
            raise RecoverableVisionError()
        return "图片分析"

    monkeypatch.setattr(module, "get_ai_config", lambda: {"model": "primary", "api_key": "a", "api_base": "https://a"})
    monkeypatch.setattr(module, "get_vision_fallback_config", lambda: {"model": "gpt-5.6-terra", "api_key": "b", "api_base": "https://b"})
    monkeypatch.setattr(client, "_vision_chat", fake_vision_chat)

    assert await client.describe_images(["data:image/jpeg;base64,AA=="], "图集说明") == "图片分析"
    assert calls == ["primary", "gpt-5.6-terra"]


@pytest.mark.asyncio
async def test_describe_images_hides_upstream_failure(monkeypatch):
    client = AIClient()

    async def fail(*_args):
        raise RecoverableVisionError()

    monkeypatch.setattr(client, "_vision_chat", fail)
    with pytest.raises(VisionServiceError, match="Image analysis is temporarily unavailable"):
        await client.describe_images(["data:image/jpeg;base64,AA=="], "图集说明")
