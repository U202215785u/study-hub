import json

import pytest
import database

from services.douyin_content import LocalFileRequired, acquire_content


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data, expected_kind, expected_value",
    [
        ({"subtitle_texts": ["inline"]}, "text", "inline"),
        ({"subtitle_urls": ["https://cdn.test/sub.vtt"]}, "text", "downloaded subtitle"),
        ({"audio_urls": ["https://cdn.test/audio.mp3"]}, "transcript", "audio"),
        ({"download_permission": "allowed", "media_urls": ["https://cdn.test/video.mp4"]}, "transcript", "media"),
        ({"local_file_path": "C:/temp/video.mp4"}, "transcript", "local"),
    ],
)
async def test_content_source_priority(data, expected_kind, expected_value):
    base = {
        "subtitle_texts": [], "subtitle_urls": [], "audio_urls": [],
        "media_urls": [], "download_permission": "unknown", "local_file_path": "",
    }
    base.update(data)

    async def subtitle(_url):
        return "downloaded subtitle"

    async def transcribe(source, kind):
        return {"audio": "audio", "media": "media", "local": "local"}[kind]

    result = await acquire_content(base, subtitle_loader=subtitle, transcriber=transcribe)
    assert result.kind == expected_kind
    assert result.text == expected_value


@pytest.mark.asyncio
async def test_unavailable_content_requires_local_file():
    with pytest.raises(LocalFileRequired) as caught:
        await acquire_content({}, subtitle_loader=None, transcriber=None)
    assert caught.value.code == "local_file_required"


def test_preflight_subtitle_enters_existing_raw_contract():
    from endpoints import automation

    conn = database.get_db()
    conn.execute(
        "INSERT OR IGNORE INTO douyin_preflight_batches (batch_id, raw_input, status) VALUES ('content-batch', 'x', 'ready')"
    )
    conn.execute(
        """INSERT OR REPLACE INTO douyin_preflight_items
           (item_id, batch_id, input_url, canonical_url, work_id, title, author,
            status, resolver_data)
           VALUES ('content-item', 'content-batch', 'https://v.douyin.com/x',
                   'https://www.douyin.com/video/88', '88', 'resolved title', 'author',
                   'confirmed', ?)""",
        (json.dumps({"subtitle_texts": ["recognized subtitle content"]}),),
    )
    conn.commit()
    conn.close()

    raw = automation._extract_preflight_douyin_raw("content-item")
    assert raw["video_id"] == "88"
    assert raw["title"] == "resolved title"
    assert raw["asr_text"] == "recognized subtitle content"
