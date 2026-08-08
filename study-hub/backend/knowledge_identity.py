import re
import sqlite3
from urllib.parse import urlparse


_URL_PATTERN = re.compile(r"https?://[^\s)\]}>,]+", re.IGNORECASE)


def extract_source_url(content: str) -> str | None:
    match = _URL_PATTERN.search(content or "")
    return match.group(0).rstrip(".。，,") if match else None


def source_identity(source: str, url: str) -> str | None:
    parsed = urlparse(url or "")
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    if source == "douyin-summary":
        if host == "v.douyin.com" and path:
            return f"douyin:short:{path.split('/')[0]}"
        match = re.search(r"(?:^|/)video/(\d+)(?:/|$)", path)
        if host.endswith("douyin.com") and match:
            return f"douyin:{match.group(1)}"
        return None

    if source == "bilibili-summary":
        if host == "b23.tv" and path:
            return f"bilibili:short:{path.split('/')[0]}"
        match = re.search(r"(?:^|/)video/(BV[\w]+)(?:/|$)", path, re.IGNORECASE)
        if host.endswith("bilibili.com") and match:
            return f"bilibili:{match.group(1).upper()}"
        return None

    if source == "xiaohongshu-summary":
        if host == "xhslink.com" and path:
            return f"xiaohongshu:short:{path.split('/')[0]}"
        match = re.search(r"(?:^|/)explore/([\w-]+)(?:/|$)", path)
        if host.endswith("xiaohongshu.com") and match:
            return f"xiaohongshu:{match.group(1)}"

    return None


def claim_source_identity(conn: sqlite3.Connection, source: str, source_key: str | None, document_id: int) -> int:
    """Claim an import identity or return the document that already owns it."""
    if not source_key:
        return document_id
    conn.execute(
        "INSERT OR IGNORE INTO document_source_claims (source, source_key, document_id) VALUES (?, ?, ?)",
        (source, source_key, document_id),
    )
    row = conn.execute(
        "SELECT document_id FROM document_source_claims WHERE source = ? AND source_key = ?",
        (source, source_key),
    ).fetchone()
    return int(row[0])
