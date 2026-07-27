"""浏览器控制器 — 利用 Playwright 控制浏览器

对标 OpenClaw Browser Skill 的 CDP 控制能力。
由于环境中已有 Playwright MCP，我们复用其能力。
"""
import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Any

from .safety_guard import check_browser_action, RiskLevel


@dataclass
class BrowserResult:
    success: bool
    content: str = ""
    error: str = ""
    action: str = ""
    url: str = ""
    risk_level: str = "safe"


def _fetch_page_text(url: str, timeout: int = 10) -> tuple[bool, str, str]:
    """纯 HTTP 获取页面文本（无浏览器开销）。"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            # 简单提取文本
            text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", "", text)
            text = re.sub(r"\s+", " ", text).strip()
            return True, text[:8000], ""
    except Exception as e:
        return False, "", str(e)


def navigate(url: str, *, user_confirmed: bool = False) -> BrowserResult:
    """导航到指定 URL。"""
    check = check_browser_action("navigate", url)
    if check.blocked:
        return BrowserResult(False, error=f"[BLOCKED] {check.reason}", action="navigate", url=url, risk_level=check.risk.value)
    if check.requires_confirmation and not user_confirmed:
        return BrowserResult(
            False,
            error=f"[NEEDS_CONFIRMATION] {check.reason}\n请显式确认后再导航。",
            action="navigate",
            url=url,
            risk_level=check.risk.value,
        )

    ok, text, err = _fetch_page_text(url)
    if ok:
        preview = text[:2000]
        return BrowserResult(
            True,
            content=f"页面已加载。内容预览:\n{preview}\n\n[完整内容 {len(text)} 字符]",
            action="navigate",
            url=url,
            risk_level=check.risk.value,
        )
    else:
        return BrowserResult(False, error=f"加载失败: {err}", action="navigate", url=url)


def extract(url: str, selector: str = "") -> BrowserResult:
    """提取网页内容。"""
    check = check_browser_action("extract", url)
    if check.blocked:
        return BrowserResult(False, error=f"[BLOCKED] {check.reason}", action="extract", url=url, risk_level=check.risk.value)

    ok, text, err = _fetch_page_text(url)
    if not ok:
        return BrowserResult(False, error=f"提取失败: {err}", action="extract", url=url)

    # 如果指定了选择器，做简单过滤
    if selector:
        lines = [l for l in text.splitlines() if selector.lower() in l.lower()]
        content = "\n".join(lines[:50]) or "(未找到匹配选择器的内容)"
    else:
        content = text[:5000]

    return BrowserResult(True, content=content, action="extract", url=url, risk_level=check.risk.value)


def screenshot(url: str, *, user_confirmed: bool = False) -> BrowserResult:
    """
    截图指定网页。
    如果环境中有 Playwright，使用它；否则返回提示。
    """
    check = check_browser_action("screenshot", url)
    if check.blocked:
        return BrowserResult(False, error=f"[BLOCKED] {check.reason}", action="screenshot", url=url, risk_level=check.risk.value)

    # 尝试使用 Playwright
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url, wait_until="networkidle", timeout=15000)
            # 保存到 second-self 目录下的 screenshots/
            import os
            from pathlib import Path
            ss_dir = Path(__file__).parent.parent / "screenshots"
            ss_dir.mkdir(exist_ok=True)
            filename = f"ss_{__import__('time').time():.0f}.png"
            path = ss_dir / filename
            page.screenshot(path=str(path))
            browser.close()

            return BrowserResult(
                True,
                content=f"截图已保存: {path}",
                action="screenshot",
                url=url,
                risk_level=check.risk.value,
            )
    except ImportError:
        return BrowserResult(
            False,
            error="Playwright 未安装。请运行: pip install playwright && playwright install chromium",
            action="screenshot",
            url=url,
        )
    except Exception as e:
        return BrowserResult(False, error=f"截图失败: {str(e)}", action="screenshot", url=url)
