import asyncio
import sys

import httpx
import pytest

from services.douyin_resolver import (
    DouyinResolveError,
    ResolvedWork,
    classify_f2_exception,
    extract_douyin_urls,
    f2_available,
    normalize_f2_detail,
)


def test_f2_runtime_check_does_not_pollute_main_process_imports():
    before = list(sys.path)

    assert f2_available() is True
    assert sys.path == before


def test_extracts_and_deduplicates_links_from_complete_share_text():
    text = (
        "作品 A https://v.douyin.com/f5NZQ93-4aw/ 复制打开 "
        "重复 https://v.douyin.com/f5NZQ93-4aw/ "
        "作品 B www.douyin.com/video/7664111490818968832"
    )

    assert extract_douyin_urls(text) == [
        "https://v.douyin.com/f5NZQ93-4aw/",
        "https://www.douyin.com/video/7664111490818968832",
    ]


def test_extract_rejects_non_douyin_and_more_than_ten_links():
    with pytest.raises(DouyinResolveError) as invalid:
        extract_douyin_urls("https://example.com/video/1")
    assert invalid.value.code == "invalid_input"

    links = " ".join(f"https://www.douyin.com/video/{i}" for i in range(11))
    with pytest.raises(DouyinResolveError) as too_many:
        extract_douyin_urls(links)
    assert too_many.value.code == "invalid_input"


def test_normalizes_f2_detail_and_content_candidates():
    detail = {
        "aweme_id": "7664111490818968832",
        "desc": "卡片光束扫描交互",
        "nickname": "创作者",
        "duration": 46_000,
        "music_play_url": ["https://aweme.snssdk.com/audio.m4a"],
        "video_play_addr": ["https://v3-dy-o.zjcdn.com/video.mp4"],
        "cover": ["https://p3-pc-sign.douyinpic.com/cover.jpeg"],
        "_subtitle_texts": ["这是现成字幕"],
        "_subtitle_urls": ["https://v3-dy-o.zjcdn.com/subtitle.json"],
        "_download_permission": "allowed",
    }

    result = normalize_f2_detail(detail)

    assert result == ResolvedWork(
        work_id="7664111490818968832",
        canonical_url="https://www.douyin.com/video/7664111490818968832",
        title="卡片光束扫描交互",
        author="创作者",
        duration_seconds=46.0,
        cover_url="https://p3-pc-sign.douyinpic.com/cover.jpeg",
        download_permission="allowed",
        subtitle_texts=["这是现成字幕"],
        subtitle_urls=["https://v3-dy-o.zjcdn.com/subtitle.json"],
        audio_urls=["https://aweme.snssdk.com/audio.m4a"],
        media_urls=["https://v3-dy-o.zjcdn.com/video.mp4"],
    )


@pytest.mark.parametrize(
    ("exception", "has_cookie", "code", "opens_circuit"),
    [
        (httpx.TimeoutException("timed out"), False, "network_timeout", False),
        (httpx.HTTPStatusError("403", request=None, response=type("R", (), {"status_code": 403})()), True, "access_forbidden", True),
        (httpx.HTTPStatusError("429", request=None, response=type("R", (), {"status_code": 429})()), True, "rate_limited", True),
        (RuntimeError("captcha risk verify"), True, "risk_verification", True),
        (RuntimeError("login required"), False, "cookie_required", False),
        (KeyError("aweme_id"), True, "contract_changed", False),
    ],
)
def test_classifies_f2_failures(exception, has_cookie, code, opens_circuit):
    result = classify_f2_exception(exception, has_cookie=has_cookie)

    assert result.code == code
    assert result.opens_circuit is opens_circuit
