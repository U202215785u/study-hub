import json
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from douyin_mcp_server.errors import DY_2005_INVALID_VIDEO_INFO, DouyinError
from douyin_mcp_server.server import DouyinProcessor


def _response(url="", text=""):
    response = mock.MagicMock()
    response.url = url
    response.text = text
    response.raise_for_status.return_value = None
    return response


def _router_page(page_key, item):
    data = {"loaderData": {page_key: {"videoInfoRes": {"item_list": [item]}}}}
    return f"<script>window._ROUTER_DATA = {json.dumps(data)}</script>"


def test_parse_share_url_returns_image_note_without_video_address():
    item = {
        "desc": "图集标题",
        "images": [{"url_list": ["https://cdn.example/1.webp"]}],
        "author": {"nickname": "作者"},
    }
    responses = [
        _response("https://www.iesdouyin.com/share/note/123456"),
        _response(text=_router_page("note_(id)/page", item)),
    ]

    with mock.patch("requests.get", side_effect=responses):
        info = DouyinProcessor("").parse_share_url("https://v.douyin.com/example")

    assert info["content_type"] == "image_note"
    assert info["image_urls"] == ["https://cdn.example/1.webp"]
    assert info["canonical_url"] == "https://www.iesdouyin.com/share/note/123456"
    assert "video_url" not in info


def test_parse_share_url_keeps_video_playback_for_video_posts():
    item = {
        "desc": "视频标题",
        "video": {"play_addr": {"url_list": ["https://cdn.example/video.mp4"]}},
    }
    responses = [
        _response("https://www.iesdouyin.com/share/video/123456"),
        _response(text=_router_page("video_(id)/page", item)),
    ]

    with mock.patch("requests.get", side_effect=responses):
        info = DouyinProcessor("").parse_share_url("https://v.douyin.com/example")

    assert info["content_type"] == "video"
    assert info["video_url"] == "https://cdn.example/video.mp4"
    assert info["url"] == "https://cdn.example/video.mp4"


def test_parse_share_url_rejects_posts_without_supported_media():
    item = {"desc": "无媒体内容"}
    responses = [
        _response("https://www.iesdouyin.com/share/note/123456"),
        _response(text=_router_page("note_(id)/page", item)),
    ]

    with mock.patch("requests.get", side_effect=responses):
        with pytest.raises(DouyinError) as error:
            DouyinProcessor("").parse_share_url("https://v.douyin.com/example")

    assert error.value.error_code == DY_2005_INVALID_VIDEO_INFO
