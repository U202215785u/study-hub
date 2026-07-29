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


def test_worker_output_ignores_f2_console_warnings():
    from services.douyin_resolver import _decode_worker_output

    payload = _decode_worker_output(
        b'WARNING request returned empty\r\n{"error_code":"network_error","error_message":"failed"}\r\n'
    )
    assert payload["error_code"] == "network_error"

    windows_output = '警告 请求为空\r\n{"error_code":"network_error","error_message":"抖音解析失败"}\r\n'.encode("gb18030")
    payload = _decode_worker_output(windows_output)
    assert payload["error_message"] == "抖音解析失败"


def test_empty_f2_response_is_classified_as_cookie_required():
    from services.douyin_f2_worker import _classify

    code, opens_circuit = _classify(RuntimeError("第 1 次请求响应内容为空"), False)
    assert (code, opens_circuit) == ("cookie_required", False)


def test_anonymous_worker_network_failure_requests_cookie():
    from services.douyin_resolver import _worker_error_code

    assert _worker_error_code("network_error", has_cookie=False) == "cookie_required"
    assert _worker_error_code("network_error", has_cookie=True) == "network_error"


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
