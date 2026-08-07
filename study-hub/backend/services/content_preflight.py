import re
from urllib.parse import urlsplit, urlunsplit


MAX_ITEMS = 10
MAX_INPUT_LENGTH = 20_000
PLATFORM_LABELS = {
    "douyin": "抖音",
    "bilibili": "B站",
    "xiaohongshu": "小红书",
}
PLATFORM_PATTERNS = {
    "douyin": re.compile(
        r"(?:(?:https?://)?(?:v\.)?douyin\.com/[A-Za-z0-9_/?=&.%+-]+|"
        r"(?:https?://)?(?:www\.)?iesdouyin\.com/share/(?:video|note)/\d+)",
        re.IGNORECASE,
    ),
    "bilibili": re.compile(
        r"(?:(?:https?://)?b23\.tv/[A-Za-z0-9_/?=&.%+-]+|"
        r"(?:https?://)?(?:www\.)?bilibili\.com/video/[A-Za-z0-9_/?=&.%+-]+)",
        re.IGNORECASE,
    ),
    "xiaohongshu": re.compile(
        r"(?:(?:https?://)?xhslink\.com/[A-Za-z0-9_/?=&.%+-]+|"
        r"(?:https?://)?(?:www\.)?xiaohongshu\.com/explore/[A-Za-z0-9_/?=&.%+-]+)",
        re.IGNORECASE,
    ),
}


class PreflightInputError(ValueError):
    pass


def build_preflight(raw_input: str, mode: str) -> dict:
    if mode not in ("auto", *PLATFORM_PATTERNS):
        raise PreflightInputError("请选择有效的平台")
    if not isinstance(raw_input, str) or not raw_input.strip() or len(raw_input) > MAX_INPUT_LENGTH:
        raise PreflightInputError("请输入不超过 20000 字的分享文本或链接")

    matches = _extract_links(raw_input)
    if not matches:
        raise PreflightInputError("没有找到支持的抖音、B站或小红书链接")
    if len(matches) > MAX_ITEMS:
        raise PreflightInputError("一次最多检查 10 个链接")

    return {
        "items": [_public_item(index, platform, url, mode) for index, (platform, url) in enumerate(matches, 1)],
        "total": len(matches),
    }


def _extract_links(raw_input: str) -> list[tuple[str, str]]:
    found = []
    for platform, pattern in PLATFORM_PATTERNS.items():
        for match in pattern.finditer(raw_input):
            found.append((match.start(), platform, _canonical_url(match.group(0))))
    found.sort(key=lambda item: item[0])

    unique = []
    seen = set()
    for _, platform, url in found:
        key = (platform, url)
        if key not in seen:
            seen.add(key)
            unique.append((platform, url))
    return unique


def _canonical_url(value: str) -> str:
    value = value.rstrip(".,，。!！?？;；)]}")
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    parsed = urlsplit(value)
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path, parsed.query, ""))


def _public_item(index: int, platform: str, url: str, mode: str) -> dict:
    mismatch = mode != "auto" and mode != platform
    label = PLATFORM_LABELS[platform]
    return {
        "item_id": f"item-{index}",
        "platform": platform,
        "input_url": url,
        "canonical_url": url,
        "title": "",
        "status": "failed" if mismatch else "ready",
        "error_code": "platform_mismatch" if mismatch else "",
        "error_message": (
            f"当前选择的是{PLATFORM_LABELS[mode]}，请切换为自动识别或 {label}"
            if mismatch else ""
        ),
        "available_actions": [] if mismatch else ["confirm"],
    }
