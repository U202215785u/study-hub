"""Isolated F2 process. Reads one JSON request from stdin and emits one JSON result."""

import asyncio
import json
import sys


def _strings(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values = []
        for key in ("url", "url_list", "text", "content", "subtitle_text"):
            values.extend(_strings(value.get(key)))
        return values
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_strings(item))
        return values
    return []


def _media_policy(payload):
    aweme = payload.get("aweme_detail") if isinstance(payload, dict) else None
    aweme = aweme if isinstance(aweme, dict) else {}
    control = aweme.get("video_control")
    control = control if isinstance(control, dict) else {}
    allow = control.get("allow_download")
    if isinstance(allow, bool):
        permission = "allowed" if allow else "denied"
    elif isinstance(aweme.get("prevent_download"), bool):
        permission = "denied" if aweme["prevent_download"] else "allowed"
    else:
        permission = "unknown"

    subtitle_texts = []
    subtitle_urls = []
    containers = [
        aweme.get("subtitle_infos"),
        aweme.get("video_subtitle"),
        (aweme.get("video") or {}).get("subtitleInfos")
        if isinstance(aweme.get("video"), dict) else None,
    ]

    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = str(key).lower()
                if lowered in {"url", "subtitle_url"}:
                    subtitle_urls.extend(_strings(child))
                elif lowered in {"text", "content", "subtitle_text"}:
                    subtitle_texts.extend(_strings(child))
                elif isinstance(child, (dict, list, tuple)):
                    visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)

    for container in containers:
        visit(container)
    return permission, list(dict.fromkeys(subtitle_texts)), list(dict.fromkeys(subtitle_urls))


def _classify(exc, has_cookie):
    message = str(exc).lower()
    name = exc.__class__.__name__.lower()
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if "timeout" in name or "timed out" in message:
        return "network_timeout", False
    if status == 429 or "429" in message:
        return "rate_limited", True
    if status == 403 or "403" in message or "forbidden" in message:
        return "access_forbidden", True
    if any(token in message for token in ("captcha", "verify", "risk")):
        return "risk_verification", True
    if any(token in message for token in ("cookie", "login", "unauthorized")):
        return ("cookie_expired" if has_cookie else "cookie_required"), False
    if status == 404:
        return "work_unavailable", False
    if isinstance(exc, (KeyError, AttributeError, ValueError)):
        return "contract_changed", False
    return "network_error", False


async def main():
    request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    work_id = str(request.get("work_id") or "")
    cookie = str(request.get("cookie") or "")
    try:
        from f2.apps.douyin.crawler import DouyinCrawler
        from f2.apps.douyin.filter import PostDetailFilter
        from f2.apps.douyin.model import PostDetail

        kwargs = {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
                "Referer": "https://www.douyin.com/",
            },
            "proxies": {"http://": None, "https://": None},
            "timeout": 20,
            "max_retries": 1,
            "cookie": cookie.strip(),
        }
        async with DouyinCrawler(kwargs) as crawler:
            payload = await crawler.fetch_post_detail(PostDetail(aweme_id=work_id))
        if not isinstance(payload, dict) or not payload:
            code = "cookie_expired" if cookie else "cookie_required"
            print(json.dumps({"error_code": code}, ensure_ascii=False))
            return
        detail = PostDetailFilter(payload)._to_dict()
        permission, subtitle_texts, subtitle_urls = _media_policy(payload)
        detail["_download_permission"] = permission
        detail["_subtitle_texts"] = subtitle_texts
        detail["_subtitle_urls"] = subtitle_urls
        print(json.dumps({"detail": detail}, ensure_ascii=False))
    except Exception as exc:
        code, opens_circuit = _classify(exc, bool(cookie.strip()))
        print(json.dumps({
            "error_code": code,
            "error_message": "抖音解析失败",
            "opens_circuit": opens_circuit,
        }, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
