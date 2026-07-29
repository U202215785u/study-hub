import asyncio
import time

import pytest
from httpx import AsyncClient, ASGITransport

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import main
from main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_startup_recovery_does_not_block_the_event_loop(monkeypatch):
    from endpoints import automation

    def slow_recovery():
        time.sleep(0.5)

    monkeypatch.setattr(automation, "recover_tasks_on_startup", slow_recovery)
    recovery = asyncio.create_task(main._async_recover_automation_state())

    await asyncio.sleep(3.1)
    assert not recovery.done()
    await recovery


@pytest.mark.asyncio
async def test_list_modules():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/automation/modules")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(m["id"] == "douyin-summary" for m in data)


@pytest.mark.asyncio
async def test_list_documents():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/documents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_categories():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/categories")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_automation_invalid_module():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/automation/run", json={
            "module_id": "nonexistent",
            "input": "test",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_automation_empty_input():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/automation/run", json={
            "module_id": "douyin-summary",
            "input": "",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"] == "请输入内容"


@pytest.mark.asyncio
async def test_rag_empty_query():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/rag/query", json={"query": ""})
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"answer": "请输入问题", "sources": []}
