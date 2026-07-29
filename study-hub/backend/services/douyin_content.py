import inspect
import re
from dataclasses import dataclass


FAILURE_MARKERS = (
    "语音提取失败",
    "解析失败",
    "从HTML中解析视频信息失败",
    "_placeholder",
)


class LocalFileRequired(RuntimeError):
    code = "local_file_required"


@dataclass(frozen=True)
class AcquiredContent:
    kind: str
    text: str
    source: str


async def _call(function, *args):
    result = function(*args)
    return await result if inspect.isawaitable(result) else result


async def acquire_content(item, *, subtitle_loader, transcriber):
    inline = [str(value).strip() for value in item.get("subtitle_texts", []) if str(value).strip()]
    if inline:
        return AcquiredContent("text", "\n".join(inline), "inline_subtitle")

    subtitle_urls = item.get("subtitle_urls") or []
    if subtitle_urls and subtitle_loader:
        text = str(await _call(subtitle_loader, subtitle_urls[0])).strip()
        if text:
            return AcquiredContent("text", text, "subtitle_url")

    audio_urls = item.get("audio_urls") or []
    if audio_urls and transcriber:
        text = str(await _call(transcriber, audio_urls[0], "audio")).strip()
        if text:
            return AcquiredContent("transcript", text, "audio")

    media_urls = item.get("media_urls") or []
    if item.get("download_permission") == "allowed" and media_urls and transcriber:
        text = str(await _call(transcriber, media_urls[0], "media")).strip()
        if text:
            return AcquiredContent("transcript", text, "media")

    local_path = str(item.get("local_file_path") or "").strip()
    if local_path and transcriber:
        text = str(await _call(transcriber, local_path, "local")).strip()
        if text:
            return AcquiredContent("transcript", text, "local_file")

    raise LocalFileRequired("需要上传本地视频才能继续识别")


def valid_document_content(content):
    if not isinstance(content, str):
        return False, "missing_content"
    if len(re.sub(r"\s+", "", content)) < 20:
        return False, "content_too_short"
    if any(marker.lower() in content.lower() for marker in FAILURE_MARKERS):
        return False, "failure_marker"
    return True, "quality_passed"


def finalize_replacement(conn, task_id, old_doc_id, new_doc_id):
    if not old_doc_id:
        return True
    row = conn.execute(
        "SELECT id, content FROM documents WHERE id = ?", (new_doc_id,)
    ).fetchone()
    valid, reason = valid_document_content(row["content"] if row else None)
    decision = "retained"
    if valid:
        cursor = conn.execute("DELETE FROM documents WHERE id = ?", (old_doc_id,))
        valid = cursor.rowcount == 1
        reason = "quality_passed" if valid else "old_document_missing"
        decision = "replaced" if valid else "retained"
    elif row:
        conn.execute("DELETE FROM documents WHERE id = ?", (new_doc_id,))
    conn.execute(
        """INSERT INTO document_replacement_audit
           (task_id, old_doc_id, new_doc_id, decision, reason)
           VALUES (?, ?, ?, ?, ?)""",
        (task_id, old_doc_id, new_doc_id if row else None, decision, reason),
    )
    conn.commit()
    return valid
