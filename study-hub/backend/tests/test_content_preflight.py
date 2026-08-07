import pytest

from services.content_preflight import PreflightInputError, build_preflight


def test_auto_mode_detects_three_platforms_and_deduplicates():
    result = build_preflight(
        "https://v.douyin.com/abc https://b23.tv/xyz https://xhslink.com/foo https://b23.tv/xyz",
        "auto",
    )

    assert [item["platform"] for item in result["items"]] == [
        "douyin", "bilibili", "xiaohongshu",
    ]
    assert all(item["status"] == "ready" for item in result["items"])


def test_manual_mode_marks_other_platform_as_mismatch():
    result = build_preflight("https://b23.tv/xyz", "douyin")

    assert result["items"] == [{
        "item_id": "item-1",
        "platform": "bilibili",
        "input_url": "https://b23.tv/xyz",
        "canonical_url": "https://b23.tv/xyz",
        "title": "",
        "status": "failed",
        "error_code": "platform_mismatch",
        "error_message": "当前选择的是抖音，请切换为自动识别或 B站",
        "available_actions": [],
    }]


@pytest.mark.parametrize("raw_input", ["", "https://example.com/a"])
def test_rejects_empty_or_unsupported_input(raw_input):
    with pytest.raises(PreflightInputError):
        build_preflight(raw_input, "auto")


def test_rejects_more_than_ten_unique_links():
    links = " ".join(f"https://b23.tv/{index}" for index in range(11))

    with pytest.raises(PreflightInputError):
        build_preflight(links, "auto")
