import asyncio
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import httpx


STUDY_HUB_DIR = Path(__file__).resolve().parents[2]
F2_VENDOR_DIR = STUDY_HUB_DIR / ".vendor"
F2_WORKER = Path(__file__).with_name("douyin_f2_worker.py")
DOUYIN_HOSTS = {"douyin.com", "www.douyin.com", "v.douyin.com", "iesdouyin.com", "www.iesdouyin.com"}
MEDIA_SUFFIXES = (".douyin.com", ".douyinvod.com", ".douyinpic.com", ".zjcdn.com", ".snssdk.com")
ERROR_MESSAGES = {
    "invalid_input": "请输入有效的抖音分享文本或链接",
    "cookie_required": "匿名解析未取得作品，请更新可选 Cookie 后重试",
    "cookie_expired": "已保存的 Cookie 可能已失效，请更新后重试",
    "access_forbidden": "抖音拒绝了本次作品解析请求",
    "rate_limited": "抖音请求过于频繁，请等待暂停结束",
    "risk_verification": "抖音要求验证码或安全验证",
    "work_unavailable": "作品可能不存在、已删除、私密或权限不足",
    "contract_changed": "抖音返回结构已变化，当前解析器无法识别",
    "network_timeout": "访问抖音超时",
    "network_error": "无法连接抖音，请检查网络设置",
    "upstream_server_error": "抖音服务暂时异常",
    "daily_limit_exceeded": "今日抖音解析次数已达到上限",
}


class DouyinResolveError(RuntimeError):
    def __init__(self, code: str, message: str | None = None, *, opens_circuit=False):
        self.code = code
        self.opens_circuit = opens_circuit
        super().__init__(message or ERROR_MESSAGES.get(code, "抖音解析失败"))


@dataclass(eq=True)
class ResolvedWork:
    work_id: str
    canonical_url: str
    title: str
    author: str | None = None
    duration_seconds: float = 0
    cover_url: str | None = None
    download_permission: str = "unknown"
    subtitle_texts: list[str] = field(default_factory=list)
    subtitle_urls: list[str] = field(default_factory=list)
    audio_urls: list[str] = field(default_factory=list)
    media_urls: list[str] = field(default_factory=list)

    def content_sources(self):
        sources = []
        if self.subtitle_texts:
            sources.append("subtitle")
        if self.subtitle_urls:
            sources.append("subtitle_url")
        if self.audio_urls:
            sources.append("audio")
        if self.download_permission == "allowed" and self.media_urls:
            sources.append("media")
        return sources


def _allowed_page_url(value: str):
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and host in DOUYIN_HOSTS


def extract_douyin_urls(text: str):
    if not isinstance(text, str) or not text.strip() or len(text) > 20_000:
        raise DouyinResolveError("invalid_input")
    pattern = re.compile(
        r"(?:(?:https?://)?(?:v\.)?douyin\.com/[A-Za-z0-9_/?=&.%+-]+|"
        r"(?:https?://)?(?:www\.)?iesdouyin\.com/share/(?:video|note)/\d+)"
    )
    result = []
    for match in pattern.finditer(text):
        value = match.group(0).rstrip('.,，。!！?？;；)]}')
        if not value.startswith(("http://", "https://")):
            value = "https://" + value
        if value.startswith("http://"):
            value = "https://" + value[len("http://"):]
        if value.startswith("https://douyin.com/"):
            value = "https://www.douyin.com/" + value[len("https://douyin.com/"):]
        if not _allowed_page_url(value):
            continue
        if value not in result:
            result.append(value)
    if not result or len(result) > 10:
        raise DouyinResolveError("invalid_input")
    return result


def _strings(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values = []
        for key in ("url_list", "uri", "url"):
            values.extend(_strings(value.get(key)))
        return values
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_strings(item))
        return values
    return []


def _media_urls(value):
    result = []
    for url in _strings(value):
        host = (urlsplit(url).hostname or "").lower()
        if urlsplit(url).scheme == "https" and any(
            host == suffix[1:] or host.endswith(suffix) for suffix in MEDIA_SUFFIXES
        ):
            result.append(url)
    return list(dict.fromkeys(result))


def _first(value, default=""):
    values = _strings(value)
    return values[0] if values else default


def normalize_f2_detail(detail: dict):
    if not isinstance(detail, dict):
        raise DouyinResolveError("contract_changed")
    work_id = str(detail.get("aweme_id") or "")
    if not re.fullmatch(r"\d{1,64}", work_id):
        raise DouyinResolveError("contract_changed")
    try:
        duration = float(detail.get("duration") or 0) / 1000
    except (TypeError, ValueError):
        duration = 0
    permission = str(detail.get("_download_permission") or "unknown")
    if permission not in {"allowed", "denied", "unknown"}:
        permission = "unknown"
    return ResolvedWork(
        work_id=work_id,
        canonical_url=f"https://www.douyin.com/video/{work_id}",
        title=str(detail.get("desc_raw") or detail.get("desc") or f"抖音作品 {work_id}").strip()[:180],
        author=str(detail.get("nickname_raw") or detail.get("nickname") or "").strip() or None,
        duration_seconds=duration,
        cover_url=_first(detail.get("cover")) or None,
        download_permission=permission,
        subtitle_texts=[str(v).strip() for v in detail.get("_subtitle_texts", []) if str(v).strip()],
        subtitle_urls=_media_urls(detail.get("_subtitle_urls")),
        audio_urls=_media_urls(detail.get("music_play_url")),
        media_urls=_media_urls(detail.get("video_play_addr")) if permission == "allowed" else [],
    )


def classify_f2_exception(exc: Exception, *, has_cookie: bool):
    if isinstance(exc, DouyinResolveError):
        return exc
    message = str(exc)
    lowered = message.lower()
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if isinstance(exc, (httpx.TimeoutException, TimeoutError)) or "timed out" in lowered:
        return DouyinResolveError("network_timeout")
    if status == 429 or "429" in lowered:
        return DouyinResolveError("rate_limited", opens_circuit=True)
    if status == 403 or "403" in lowered or "forbidden" in lowered:
        return DouyinResolveError("access_forbidden", opens_circuit=True)
    if any(token in lowered for token in ("captcha", "verify", "risk")):
        return DouyinResolveError("risk_verification", opens_circuit=True)
    if any(token in lowered for token in ("cookie", "login required", "unauthorized")):
        return DouyinResolveError("cookie_expired" if has_cookie else "cookie_required")
    if status == 404:
        return DouyinResolveError("work_unavailable")
    if isinstance(exc, (KeyError, AttributeError, ValueError)):
        return DouyinResolveError("contract_changed")
    if isinstance(status, int) and status >= 500:
        return DouyinResolveError("upstream_server_error")
    return DouyinResolveError("network_error")


def f2_available():
    if not (F2_VENDOR_DIR / "f2").is_dir():
        return False
    env = os.environ.copy()
    env["PYTHONPATH"] = str(F2_VENDOR_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-c", "import f2.apps.douyin.crawler"],
        env=env,
        capture_output=True,
        timeout=15,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return result.returncode == 0


async def _fetch_with_f2_worker(work_id: str, cookie: str, timeout: float):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(F2_VENDOR_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(F2_WORKER),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    request = json.dumps({"work_id": work_id, "cookie": cookie}).encode("utf-8")
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(request), timeout=timeout + 10
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise DouyinResolveError("network_timeout")
    if process.returncode != 0:
        raise DouyinResolveError("network_error")
    try:
        payload = _decode_worker_output(stdout)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DouyinResolveError("contract_changed") from exc
    if payload.get("error_code"):
        code = _worker_error_code(payload["error_code"], has_cookie=bool(cookie.strip()))
        raise DouyinResolveError(
            code, None if code != payload["error_code"] else payload.get("error_message"),
            opens_circuit=bool(payload.get("opens_circuit")),
        )
    return payload.get("detail")


def _decode_worker_output(stdout: bytes):
    try:
        text = stdout.decode("utf-8")
    except UnicodeDecodeError:
        text = stdout.decode("gb18030")
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            payload = json.loads(line)
            if isinstance(payload, dict):
                return payload
    raise ValueError("worker returned no structured result")


def _worker_error_code(code: str, *, has_cookie: bool):
    if code == "network_error" and not has_cookie:
        return "cookie_required"
    return code


class F2DouyinResolver:
    def __init__(self, timeout=20.0):
        self.timeout = timeout

    async def _work_id(self, url: str):
        match = re.search(r"/(?:video|note)/(\d+)", url)
        if match:
            return match.group(1)
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=self.timeout,
                trust_env=False,
                headers={"User-Agent": "Mozilla/5.0 StudyHub/1.0"},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
            match = re.search(r"/(?:video|note)/(\d+)", str(response.url))
            if not match:
                raise DouyinResolveError("work_unavailable")
            return match.group(1)
        except Exception as exc:
            raise classify_f2_exception(exc, has_cookie=False) from exc

    async def resolve(self, url: str, *, cookie=""):
        if not f2_available():
            raise DouyinResolveError("contract_changed", "F2 0.0.1.7 未安装")
        work_id = await self._work_id(url)
        try:
            detail = await _fetch_with_f2_worker(work_id, cookie.strip(), self.timeout)
            if not isinstance(detail, dict) or not detail:
                raise DouyinResolveError("cookie_expired" if cookie else "cookie_required")
            return normalize_f2_detail(detail)
        except Exception as exc:
            raise classify_f2_exception(exc, has_cookie=bool(cookie.strip())) from exc
