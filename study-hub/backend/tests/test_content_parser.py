import hashlib

import pytest
from httpx import ASGITransport, AsyncClient

import database
from main import app


def _insert_document(source, title):
    content = f"# {title}\n\nhttps://example.com/{title}"
    conn = database.get_db()
    cursor = conn.execute(
        """INSERT INTO documents (title, content, content_type, source, char_count, content_hash)
           VALUES (?, ?, 'text', ?, ?, ?)""",
        (title, content, source, len(content), hashlib.sha256(content.encode()).hexdigest()),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


@pytest.mark.asyncio
async def test_preflight_accepts_mixed_links():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/content-parser/preflight", json={
            "input": "https://b23.tv/xyz\nhttps://xhslink.com/foo", "mode": "auto",
        })

    assert response.status_code == 200
    body = response.json()
    assert {item["platform"] for item in body["items"]} == {"bilibili", "xiaohongshu"}
    assert body["batch_id"]


@pytest.mark.asyncio
async def test_library_only_returns_requested_platform_documents():
    bilibili_id = _insert_document("bilibili-summary", "Bilibili item")
    _insert_document("xiaohongshu-summary", "Xiaohongshu item")
    _insert_document("upload", "Ordinary item")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/content-parser/documents?platform=bilibili&state=completed")

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["items"] if item["id"] in {bilibili_id}] == [bilibili_id]
    assert all(item["source"] == "bilibili-summary" for item in body["items"])
