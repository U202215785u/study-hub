import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app


@pytest.mark.asyncio
async def test_list_categories_returns_seeded_categories_in_display_order():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.get('/ddl/categories')

    assert response.status_code == 200
    assert [category['name'] for category in response.json()] == ['待办', '学习任务', '里程碑', '未分类']


@pytest.mark.asyncio
async def test_task_persists_selected_category_and_deletion_moves_it_to_uncategorized():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        category = (await client.post('/ddl/categories', json={'name': '深度工作'})).json()
        task = (await client.post('/ddl/tasks', json={'title': '完成设计', 'category_id': category['id']})).json()
        assert (await client.delete(f"/ddl/categories/{category['id']}")).json()['status'] == 'ok'
        categories = (await client.get('/ddl/categories')).json()
        tasks = (await client.get('/ddl/tasks')).json()

    uncategorized = next(item for item in categories if item['name'] == '未分类')
    assert next(item for item in tasks if item['id'] == task['id'])['category_id'] == uncategorized['id']


@pytest.mark.asyncio
async def test_a_custom_category_can_be_renamed_and_reordered():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        first = (await client.post('/ddl/categories', json={'name': '阅读'})).json()
        second = (await client.post('/ddl/categories', json={'name': '写作'})).json()
        renamed = await client.put(f"/ddl/categories/{first['id']}", json={'name': '精读'})
        reordered = await client.put('/ddl/categories/reorder', json={'category_ids': [second['id'], first['id']]})

    assert renamed.json()['status'] == 'ok'
    assert reordered.json()['status'] == 'ok'
