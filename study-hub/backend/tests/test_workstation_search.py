from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
import pytest

from database import get_db
from endpoints.workstation_search import router
import endpoints.workstation_search as workstation_search


def seed_search_records():
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO documents (title, content, tags) VALUES (?, ?, ?)",
            ("设计系统笔记", "这是一篇关于搜索交互和设计系统的内部文章。", '["设计"]'),
        )
        conn.execute(
            "INSERT INTO wiki_pages (title, slug, content, summary, tags) VALUES (?, ?, ?, ?, ?)",
            ("搜索架构", "search-architecture", "工作站搜索使用受控导航。", "搜索架构说明", '["搜索"]'),
        )
        conn.execute(
            "INSERT INTO ddl_tasks (title, description) VALUES (?, ?)",
            ("设计搜索面板", "完成首页内部搜索"),
        )
        conn.execute(
            "INSERT INTO journal_entries (date, content, tags) VALUES (?, ?, ?)",
            ("2026-08-08", "今天整理了搜索设计。", '["设计"]'),
        )
        conn.execute(
            "INSERT INTO workflows (name, description, trigger_keywords) VALUES (?, ?, ?)",
            ("设计工作流", "搜索设计的工作流", '["设计"]'),
        )
        conn.execute(
            "INSERT INTO butler_tasks (id, task_type, title, description, status) VALUES (?, ?, ?, ?, ?)",
            ("search-case", "change", "设计搜索", "工作站搜索改造", "implementing"),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_search_returns_internal_groups_with_safe_navigation():
    seed_search_records()
    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/workstation/search", params={"q": "搜索"})

    assert response.status_code == 200
    payload = response.json()
    groups = {group["id"]: group for group in payload["groups"]}
    assert set(groups) == {"features", "knowledge", "records"}
    assert all(group["status"] == "ready" for group in groups.values())

    document = next(item for item in groups["knowledge"]["items"] if item["kind"] == "document")
    assert document["navigation"] == {"kind": "document", "document_id": document["navigation"]["document_id"]}

    wiki = next(item for item in groups["knowledge"]["items"] if item["kind"] == "wiki")
    assert wiki["navigation"] == {"kind": "route", "path": "/wiki/search-architecture", "query": {}}

    assert groups["records"]["items"]
    assert {item["navigation"]["path"] for item in groups["records"]["items"]} <= {"/workbench", "/ddl", "/journal", "/workflow"}
    assert payload["assistant"] == {"enabled": False, "label": "问一问 AI 助手", "status": "暂未开放"}


@pytest.mark.asyncio
async def test_search_marks_only_the_failed_group_unavailable(monkeypatch):
    app = FastAPI()
    app.include_router(router)
    monkeypatch.setattr(workstation_search, "search_knowledge", lambda _query: (_ for _ in ()).throw(RuntimeError("database offline")))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/workstation/search", params={"q": "设计"})

    assert response.status_code == 200
    groups = {group["id"]: group for group in response.json()["groups"]}
    assert groups["knowledge"] == {
        "id": "knowledge",
        "label": "文章与知识",
        "status": "unavailable",
        "message": "文章与知识暂时不可用",
        "items": [],
    }
    assert groups["features"]["status"] == "ready"
    assert groups["records"]["status"] == "ready"


@pytest.mark.asyncio
async def test_search_rejects_blank_queries():
    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/workstation/search", params={"q": "   "})

    assert response.status_code == 422
