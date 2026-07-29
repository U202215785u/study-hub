import json

import pytest
from httpx import ASGITransport, AsyncClient

import database
from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_preflight_creates_no_document_and_returns_ready_item(monkeypatch):
    from endpoints import douyin
    from services.douyin_resolver import ResolvedWork

    async def resolve(_url, *, cookie=""):
        return ResolvedWork(
            work_id="123456789",
            canonical_url="https://www.douyin.com/video/123456789",
            title="test work",
            subtitle_texts=["enough transcript text"],
        )

    monkeypatch.setattr(douyin.resolver, "resolve", resolve)
    conn = database.get_db()
    before = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    conn.close()

    async with await _client() as client:
        response = await client.post(
            "/automation/douyin/preflight",
            json={"input": "https://www.douyin.com/video/123456789"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["items"][0]["status"] == "ready"
    assert "resolver_data" not in body["items"][0]
    conn = database.get_db()
    assert conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == before
    conn.close()


@pytest.mark.asyncio
async def test_confirmation_is_idempotent_and_rejects_non_ready(monkeypatch):
    from endpoints import douyin

    queued = []
    monkeypatch.setattr(douyin, "enqueue_preflight_item", lambda item: queued.append(item) or "task-one")
    conn = database.get_db()
    conn.execute(
        "INSERT INTO douyin_preflight_batches (batch_id, raw_input, status) VALUES ('batch-confirm', 'x', 'ready')"
    )
    for item_id, status in (("ready-item", "ready"), ("failed-item", "failed")):
        conn.execute(
            """INSERT INTO douyin_preflight_items
               (item_id, batch_id, input_url, work_id, title, status, resolver_data)
               VALUES (?, 'batch-confirm', 'https://www.douyin.com/video/1', ?, 'title', ?, '{}')""",
            (item_id, item_id, status),
        )
    conn.commit()
    conn.close()

    async with await _client() as client:
        payload = {"batch_id": "batch-confirm", "item_ids": ["ready-item"]}
        first = await client.post("/automation/douyin/confirm", json=payload)
        second = await client.post("/automation/douyin/confirm", json=payload)
        failed = await client.post(
            "/automation/douyin/confirm",
            json={"batch_id": "batch-confirm", "item_ids": ["failed-item"]},
        )

    assert first.json()["task_ids"] == ["task-one"]
    assert second.json()["task_ids"] == ["task-one"]
    assert len(queued) == 1
    assert failed.status_code == 409


@pytest.mark.asyncio
async def test_cookie_routes_never_return_plaintext():
    secret = "sessionid=never-return-this-value"
    async with await _client() as client:
        saved = await client.put("/automation/douyin/cookie", json={"cookie": secret})
        status = await client.get("/automation/douyin/cookie/status")
        deleted = await client.delete("/automation/douyin/cookie")

    for response in (saved, status, deleted):
        assert response.status_code == 200
        assert secret not in response.text
    assert saved.json()["configured"] is True
    assert status.json()["configured"] is True
    assert deleted.json()["configured"] is False


@pytest.mark.asyncio
async def test_confirmation_rejects_item_from_another_batch(monkeypatch):
    from endpoints import douyin

    monkeypatch.setattr(douyin, "enqueue_preflight_item", lambda item: "must-not-run")
    async with await _client() as client:
        response = await client.post(
            "/automation/douyin/confirm",
            json={"batch_id": "another-batch", "item_ids": ["ready-item"]},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_local_file_accepts_mp4_signature_without_exposing_path():
    conn = database.get_db()
    conn.execute(
        "INSERT OR IGNORE INTO douyin_preflight_batches (batch_id, raw_input, status) VALUES ('batch-valid-file', 'x', 'blocked')"
    )
    conn.execute(
        """INSERT OR REPLACE INTO douyin_preflight_items
           (item_id, batch_id, input_url, work_id, title, status)
           VALUES ('valid-file', 'batch-valid-file', 'https://www.douyin.com/video/3', '3', 'title', 'needs_local_file')"""
    )
    conn.commit()
    conn.close()
    async with await _client() as client:
        response = await client.post(
            "/automation/douyin/items/valid-file/local-file",
            files={"file": ("real.mp4", b"\x00\x00\x00\x18ftypmp42payload", "video/mp4")},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert "local_file_path" not in response.json()


@pytest.mark.asyncio
async def test_local_file_recovers_a_blocked_item():
    conn = database.get_db()
    conn.execute(
        "INSERT OR IGNORE INTO douyin_preflight_batches (batch_id, raw_input, status) VALUES ('batch-blocked-file', 'x', 'blocked')"
    )
    conn.execute(
        """INSERT OR REPLACE INTO douyin_preflight_items
           (item_id, batch_id, input_url, title, status, error_code)
           VALUES ('blocked-file', 'batch-blocked-file', 'https://v.douyin.com/x', 'title', 'blocked', 'cookie_required')"""
    )
    conn.commit()
    conn.close()
    async with await _client() as client:
        response = await client.post(
            "/automation/douyin/items/blocked-file/local-file",
            files={"file": ("real.mp4", b"\x00\x00\x00\x18ftypmp42payload", "video/mp4")},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_local_file_rejects_invalid_signature():
    conn = database.get_db()
    conn.execute(
        "INSERT INTO douyin_preflight_batches (batch_id, raw_input, status) VALUES ('batch-file', 'x', 'blocked')"
    )
    conn.execute(
        """INSERT INTO douyin_preflight_items
           (item_id, batch_id, input_url, work_id, title, status)
           VALUES ('needs-file', 'batch-file', 'https://www.douyin.com/video/2', '2', 'title', 'needs_local_file')"""
    )
    conn.commit()
    conn.close()

    async with await _client() as client:
        response = await client.post(
            "/automation/douyin/items/needs-file/local-file",
            files={"file": ("fake.mp4", b"this is not an mp4", "video/mp4")},
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_local_file"
